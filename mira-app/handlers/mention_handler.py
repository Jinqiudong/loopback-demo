"""
Handles the `app_mention` event -- i.e. whenever someone @-mentions Mira
in a Slack channel or thread.

Week 1 Day 3-5 flow:
  1. Strip the bot mention out of the message text.
  2. Classify it: question or noise. If noise, do nothing.
  3. Post a draft card immediately (instant feedback to the user).
  4. Update the card to ai_searching, then call the Knowledge Vault.
  5a. Results found → update card to pending_confirm with suggested answer + buttons.
  5b. No results   → update card to human_working.

What's intentionally NOT here yet:
  - Resolution detection / three-signal confirmation logic
  - Escalating to a named resolver
  - Handling the Confirm / Not Helpful button actions (wired in a later week)
"""

import re

from services.intent import classify_intent
from services.task_card import build_task_card
from services.vault_client import VaultClient

_MENTION_PATTERN = re.compile(r"<@[A-Z0-9]+>")
_vault = VaultClient()


def _strip_mention(raw_text: str) -> str:
    return _MENTION_PATTERN.sub("", raw_text).strip()


def _update_card(client, channel: str, ts: str, question: str, status: str, results=None):
    client.chat_update(
        channel=channel,
        ts=ts,
        blocks=build_task_card(question, status=status, results=results),
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
        requester_id = event.get("user", "")

        # Post immediately so the user sees something right away.
        resp = say(
            channel=channel,
            thread_ts=thread_ts,
            blocks=build_task_card(question_text, status="draft"),
            text=f"[draft] {question_text}",
        )
        card_ts = resp["ts"]

        _update_card(client, channel, card_ts, question_text, "ai_searching")

        try:
            task_card_id = _vault.create_task_card(
                requester_id=requester_id,
                channel_id=channel,
                thread_ts=thread_ts,
                question_raw=question_text,
                question_intent=result.raw_label,
            )
            vault_result = _vault.search(question_text)
        except Exception:
            logger.exception("Vault call failed; falling back to human_working.")
            _update_card(client, channel, card_ts, question_text, "human_working")
            return

        if vault_result["match_found"]:
            _vault.update_status(task_card_id, "pending_confirm")
            _update_card(
                client, channel, card_ts, question_text, "pending_confirm",
                results=[{**vault_result, "task_card_id": task_card_id}],
            )
        else:
            _vault.update_status(task_card_id, "human_working")
            _update_card(client, channel, card_ts, question_text, "human_working")
