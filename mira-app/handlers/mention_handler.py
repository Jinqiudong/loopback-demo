"""
Handles the `app_mention` event — whenever someone @-mentions Mira.

Full flow:
  1. Classify intent. Noise → ignore.
  2. Post draft card immediately.
  3. Create task card record in Vault, then search for an existing answer.

  Vault hit (confidence > 0.85):
    → pending_confirm with ⚡ Answered from Knowledge Vault

  Vault low-confidence (0.7–0.85):
    → pending_confirm with clarifying message ("Found something related...")

  Vault miss:
    → Search Slack history (Real-Time Search API)
    → History hit  → pending_confirm with history result
    → History miss → human_working, register thread for resolution detection
"""

import re

from services.intent import classify_intent
from services.slack_search import search_slack_history
from services.task_card import build_task_card
from services.vault_client import VaultClient
from handlers.resolution_handler import register_active_thread

_MENTION_PATTERN = re.compile(r"<@[A-Z0-9]+>")
_vault = VaultClient()

_VAULT_HIGH_CONFIDENCE = 0.85
_VAULT_LOW_CONFIDENCE = 0.70


def _strip_mention(raw_text: str) -> str:
    return _MENTION_PATTERN.sub("", raw_text).strip()


def _update_card(client, channel: str, ts: str, question: str, status: str,
                 results=None, thread_ts=None, asker_id=None, vault_hit=False):
    client.chat_update(
        channel=channel,
        ts=ts,
        blocks=build_task_card(question, status=status, results=results,
                                thread_ts=thread_ts, asker_id=asker_id,
                                vault_hit=vault_hit),
        text=f"[{status}] {question}",
    )


def register_mention_handler(app):
    @app.event("app_mention")
    def handle_mention(event, say, client, logger):
        question_text = _strip_mention(event.get("text", ""))

        if not question_text:
            logger.info("Mention had no text after stripping; ignoring.")
            return

        result = classify_intent(question_text)
        logger.info(f"Intent: {result.raw_label} — {question_text!r}")

        if not result.is_question:
            return

        channel = event["channel"]
        thread_ts = event.get("thread_ts", event.get("ts"))
        asker_id = event.get("user", "")

        resp = say(
            channel=channel,
            thread_ts=thread_ts,
            blocks=build_task_card(question_text, status="draft",
                                   thread_ts=thread_ts, asker_id=asker_id),
            text=f"[draft] {question_text}",
        )
        card_ts = resp["ts"]

        _update_card(client, channel, card_ts, question_text, "ai_searching",
                     thread_ts=thread_ts, asker_id=asker_id)

        try:
            task_card_id = _vault.create_task_card(
                requester_id=asker_id,
                channel_id=channel,
                thread_ts=thread_ts,
                question_raw=question_text,
                question_intent=result.raw_label,
            )
            vault_result = _vault.search(question_text)
        except Exception:
            logger.exception("Vault call failed; falling back to human_working.")
            _update_card(client, channel, card_ts, question_text, "human_working",
                         thread_ts=thread_ts, asker_id=asker_id)
            return

        if vault_result["match_found"]:
            confidence = vault_result.get("confidence", 0)
            result_payload = [{**vault_result, "task_card_id": task_card_id}]

            if confidence >= _VAULT_HIGH_CONFIDENCE:
                # High confidence: surface answer directly
                _vault.update_status(task_card_id, "pending_confirm")
                _update_card(
                    client, channel, card_ts, question_text, "pending_confirm",
                    results=result_payload,
                    thread_ts=thread_ts, asker_id=asker_id, vault_hit=True,
                )
            else:
                # Low confidence (0.70–0.85): ask clarifying question first
                _vault.update_status(task_card_id, "pending_confirm")
                _update_card(
                    client, channel, card_ts, question_text, "pending_confirm",
                    results=result_payload,
                    thread_ts=thread_ts, asker_id=asker_id, vault_hit=False,
                )
                say(
                    channel=channel,
                    thread_ts=thread_ts,
                    text=(
                        f"I found something that might be related — "
                        f"is this the same as what you're asking about? "
                        f"({int(confidence * 100)}% match)"
                    ),
                )

        else:
            # Vault miss: try Slack history before escalating to a human
            history = search_slack_history(question_text)

            if history:
                best = history[0]
                _vault.update_status(task_card_id, "pending_confirm")
                _update_card(
                    client, channel, card_ts, question_text, "pending_confirm",
                    results=[{
                        "task_card_id": task_card_id,
                        "entry_id": None,
                        "answer": best["text"],
                        "owner_id": best.get("user", ""),
                        "confidence": 0.75,
                        "usage_count": 0,
                        "verified": False,
                    }],
                    thread_ts=thread_ts, asker_id=asker_id, vault_hit=False,
                )
                if best.get("permalink"):
                    say(
                        channel=channel,
                        thread_ts=thread_ts,
                        text=f"Found something related in Slack history: {best['permalink']}",
                    )
            else:
                # No match anywhere — escalate to a human
                _vault.update_status(task_card_id, "human_working")
                _update_card(
                    client, channel, card_ts, question_text, "human_working",
                    thread_ts=thread_ts, asker_id=asker_id, vault_hit=False,
                )
                register_active_thread(
                    thread_ts=thread_ts,
                    card_ts=card_ts,
                    channel=channel,
                    question_text=question_text,
                    asker_id=asker_id,
                    task_card_id=task_card_id,
                )
