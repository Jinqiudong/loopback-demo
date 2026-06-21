"""
Handles Block Kit button actions from task cards.

vault_confirm     — user clicked "Confirm ✓": the suggested answer worked
vault_not_helpful — user clicked "Not Helpful": the answer didn't work, escalate

Both handlers ack() immediately (Slack requires < 3s), then update the card
in place via chat_update so the user sees the state change without a new message.
"""

import json

from services.task_card import build_task_card
from services.vault_client import VaultClient

_vault = VaultClient()


def register_action_handlers(app):
    @app.action("vault_confirm")
    def handle_confirm(ack, body, client, logger):
        ack()
        value = _parse_value(body)
        task_card_id = value.get("task_card_id", "")
        entry_id = value.get("entry_id", "")
        answer = value.get("answer", "")
        owner_id = value.get("owner_id", "")
        channel = body["channel"]["id"]
        message_ts = body["message"]["ts"]
        question_text = _extract_question(body)

        try:
            _vault.upsert_entry(
                task_card_id=task_card_id,
                question_canonical=question_text,
                answer=answer,
                owner_id=owner_id,
                signal="signal_1",
            )
        except Exception:
            logger.exception("Vault upsert_entry failed on confirm")

        client.chat_update(
            channel=channel,
            ts=message_ts,
            blocks=build_task_card(
                question_text,
                status="verified",
                results=[{"entry_id": entry_id, "answer": answer, "confidence": 0.95, "verified": True, "owner_id": owner_id}],
            ),
            text=f"[verified] {question_text}",
        )

    @app.action("vault_not_helpful")
    def handle_not_helpful(ack, body, client, logger):
        ack()
        value = _parse_value(body)
        task_card_id = value.get("task_card_id", "")
        channel = body["channel"]["id"]
        message_ts = body["message"]["ts"]
        question_text = _extract_question(body)

        try:
            _vault.update_status(task_card_id, "escalate")
        except Exception:
            logger.exception("Vault update_status failed on not_helpful")

        client.chat_update(
            channel=channel,
            ts=message_ts,
            blocks=build_task_card(question_text, status="escalate"),
            text=f"[escalate] {question_text}",
        )


def _parse_value(body: dict) -> dict:
    try:
        return json.loads(body["actions"][0]["value"])
    except (KeyError, IndexError, json.JSONDecodeError):
        return {}


def _extract_question(body: dict) -> str:
    """Pull question text back out of the card's first block."""
    try:
        raw = body["message"]["blocks"][0]["text"]["text"]
        return raw.replace("*Question:*\n", "").strip()
    except (KeyError, IndexError):
        return ""
