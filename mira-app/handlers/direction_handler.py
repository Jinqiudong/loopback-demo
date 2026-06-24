"""
Pre-escalation direction check.

When Mira finds relevant context in Tier 2 search (GitHub MCP / Slack history),
she posts her findings and asks the requester to confirm the direction before
looping in the resolver. This prevents unnecessary escalations and ensures the
resolver gets useful context.

State: {thread_ts → task context + findings}
Positive reply from requester → transition to human_working with enriched card.
Timeout (5 min) → auto-escalate with findings anyway.
"""

import re

from services.task_card import build_task_card
from services.vault_client import VaultClient

_vault = VaultClient()

# {thread_ts → {card_ts, channel, question, asker_id, task_card_id, context_summary}}
_direction_threads: dict = {}

_POSITIVE_PATTERNS = re.compile(
    r"\b(yes|yeah|yep|correct|right|exactly|confirm|go ahead|proceed|looks right|that'?s? it)\b",
    re.IGNORECASE,
)


def register_direction_check(
    thread_ts: str,
    card_ts: str,
    channel: str,
    question_text: str,
    asker_id: str,
    task_card_id: str,
    context_summary: str,
) -> None:
    _direction_threads[thread_ts] = {
        "card_ts": card_ts,
        "channel": channel,
        "question_text": question_text,
        "asker_id": asker_id,
        "task_card_id": task_card_id,
        "context_summary": context_summary,
    }


def register_direction_handler(app, bot_user_id: str) -> None:
    from handlers.resolution_handler import register_active_thread

    @app.event("message", matchers=[_is_direction_reply])
    def handle_direction_reply(event, client, logger):
        thread_ts = event.get("thread_ts")
        user = event.get("user", "")
        text = event.get("text", "")

        if not thread_ts or thread_ts not in _direction_threads:
            return
        if user == bot_user_id or event.get("subtype"):
            return

        task = _direction_threads[thread_ts]

        # Only the original requester's reply counts for direction confirmation
        if user != task["asker_id"]:
            return

        if not _POSITIVE_PATTERNS.search(text):
            # Not a clear confirmation — let them keep talking
            return

        # Confirmed direction — escalate to resolver with context
        task_data = _direction_threads.pop(thread_ts)
        _escalate_with_context(client, logger, task_data, thread_ts)

    def _escalate_with_context(client, logger, task, thread_ts):
        try:
            _vault.update_status(task["task_card_id"], "human_working")
        except Exception:
            logger.exception("Failed to update status after direction confirmed")

        client.chat_update(
            channel=task["channel"],
            ts=task["card_ts"],
            blocks=build_task_card(
                task["question_text"],
                status="human_working",
                thread_ts=thread_ts,
                asker_id=task["asker_id"],
                context_summary=task["context_summary"],
            ),
            text=f"[human_working] {task['question_text']}",
        )

        # Register for resolution detection
        from handlers.resolution_handler import register_active_thread
        register_active_thread(
            thread_ts=thread_ts,
            card_ts=task["card_ts"],
            channel=task["channel"],
            question_text=task["question_text"],
            asker_id=task["asker_id"],
            task_card_id=task["task_card_id"],
        )

        logger.info(f"Direction confirmed for thread {thread_ts}, escalating to resolver")


def _is_direction_reply(event) -> bool:
    return (
        event.get("thread_ts") in _direction_threads
        and not event.get("subtype")
    )
