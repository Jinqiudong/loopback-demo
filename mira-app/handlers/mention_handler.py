"""
Handles the `app_mention` event — whenever someone @-mentions Mira.

Flow:
  1. Strip mention, classify intent. Noise → ignore.
  2. Post draft card immediately (instant feedback).
  3. Create task card record in the Vault, then search for an existing answer.
  4a. Match found  → pending_confirm with suggested answer + buttons.
  4b. No match     → human_working, resolver answers directly in thread.
"""

import re

from services.intent import classify_intent
from services.task_card import build_task_card
from services.vault_client import VaultClient

_MENTION_PATTERN = re.compile(r"<@[A-Z0-9]+>")
_vault = VaultClient()


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
            logger.info("Mention had no text content after stripping; ignoring.")
            return

        result = classify_intent(question_text)
        logger.info(f"Intent classified as {result.raw_label}: {question_text!r}")

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
            _vault.update_status(task_card_id, "pending_confirm")
            _update_card(
                client, channel, card_ts, question_text, "pending_confirm",
                results=[{**vault_result, "task_card_id": task_card_id}],
                thread_ts=thread_ts, asker_id=asker_id, vault_hit=True,
            )
        else:
            _vault.update_status(task_card_id, "human_working")
            _update_card(client, channel, card_ts, question_text, "human_working",
                         thread_ts=thread_ts, asker_id=asker_id, vault_hit=False)
