"""
Resolution detection: listens for any reply in a thread where Mira posted
a human_working card, treats the first non-bot reply as the resolver's answer,
and updates the card to pending_confirm.

State is in-memory — survives only as long as the process runs, which is fine
for a hackathon demo. Production would persist this in task_cards table.
"""

from services.task_card import build_task_card
from services.vault_client import VaultClient

_vault = VaultClient()

# {thread_ts: {card_ts, channel, question_text, asker_id, task_card_id}}
_active_threads: dict = {}


def register_active_thread(
    thread_ts: str,
    card_ts: str,
    channel: str,
    question_text: str,
    asker_id: str,
    task_card_id: str,
) -> None:
    _active_threads[thread_ts] = {
        "card_ts": card_ts,
        "channel": channel,
        "question_text": question_text,
        "asker_id": asker_id,
        "task_card_id": task_card_id,
    }


def register_resolution_handler(app, bot_user_id: str) -> None:
    @app.event("message")
    def handle_message(event, client, logger):
        thread_ts = event.get("thread_ts")

        # Only care about thread replies in active human_working threads
        if not thread_ts or thread_ts not in _active_threads:
            return

        # Skip bot messages and Slack system subtypes
        if event.get("user") == bot_user_id or event.get("subtype"):
            return

        answer_text = event.get("text", "").strip()
        if not answer_text:
            return

        task = _active_threads.pop(thread_ts)
        resolver_id = event.get("user", "")

        try:
            _vault.update_status(task["task_card_id"], "pending_confirm")
        except Exception:
            logger.exception("Failed to update vault status on resolution detection")

        client.chat_update(
            channel=task["channel"],
            ts=task["card_ts"],
            blocks=build_task_card(
                task["question_text"],
                status="pending_confirm",
                results=[{
                    "task_card_id": task["task_card_id"],
                    "entry_id": None,
                    "answer": answer_text,
                    "owner_id": resolver_id,
                    "confidence": 1.0,
                    "usage_count": 0,
                    "verified": False,
                }],
                thread_ts=thread_ts,
                asker_id=task["asker_id"],
                vault_hit=False,
            ),
            text=f"[pending_confirm] {task['question_text']}",
        )

        logger.info(f"Resolution detected in thread {thread_ts} by {resolver_id}")
