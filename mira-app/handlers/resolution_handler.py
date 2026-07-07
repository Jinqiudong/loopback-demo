"""
Unified message handler for two thread states:

1. direction_check — requester's "yes" confirms Mira's findings → escalate to resolver
2. human_working   — resolver's reply → update card to pending_confirm

Also handles passive ambient detection: threads Mira was never @-mentioned in.
When a reply arrives in a thread whose parent looks like a question, Mira offers
to save the Q&A to the Vault without requiring an @-mention.

Single handler avoids Slack Bolt multi-handler conflicts.
"""

import json
import re

from services.intent import classify_resolution
from services.task_card import build_task_card
from services.vault_client import VaultClient

_vault = VaultClient()

# human_working threads: {thread_ts → task context}
_active_threads: dict = {}

# direction_check threads: {thread_ts → task context + context_summary}
_direction_threads: dict = {}

# threads where Mira already sent (or decided not to send) an ambient nudge
_seen_ambient_threads: set = set()

_POSITIVE_PATTERNS = re.compile(
    r"\b(yes|yeah|yep|correct|right|exactly|confirm|go ahead|proceed|looks right|that'?s? it)\b",
    re.IGNORECASE,
)

# Answers that redirect rather than resolve — not worth saving
_DEFLECTION_PATTERNS = re.compile(
    r"\b(create|open|submit|file|raise|log)\s+a?\s*(ticket|jira|issue|bug report|pr)\b",
    re.IGNORECASE,
)


def register_active_thread(thread_ts, card_ts, channel, question_text, asker_id, task_card_id):
    _active_threads[thread_ts] = {
        "card_ts": card_ts,
        "channel": channel,
        "question_text": question_text,
        "asker_id": asker_id,
        "task_card_id": task_card_id,
    }


def register_direction_thread(thread_ts, card_ts, channel, question_text, asker_id, task_card_id, context_summary):
    _direction_threads[thread_ts] = {
        "card_ts": card_ts,
        "channel": channel,
        "question_text": question_text,
        "asker_id": asker_id,
        "task_card_id": task_card_id,
        "context_summary": context_summary,
    }


def register_resolution_handler(app, bot_user_id: str) -> None:
    @app.event("message")
    def handle_message(event, client, logger):
        thread_ts = event.get("thread_ts")
        user = event.get("user", "")
        text = event.get("text", "").strip()
        channel = event.get("channel", "")

        if not thread_ts or not user or user == bot_user_id or event.get("subtype"):
            return

        # ── Direction check: requester confirms Mira's findings ──────────
        if thread_ts in _direction_threads:
            task = _direction_threads[thread_ts]
            if user == task["asker_id"] and _POSITIVE_PATTERNS.search(text):
                task_data = _direction_threads.pop(thread_ts)
                logger.info(f"Direction confirmed in {thread_ts}, escalating to resolver")

                try:
                    _vault.update_status(task_data["task_card_id"], "human_working")
                except Exception:
                    logger.exception("Failed to update status after direction confirmed")

                client.chat_update(
                    channel=task_data["channel"],
                    ts=task_data["card_ts"],
                    blocks=build_task_card(
                        task_data["question_text"],
                        status="human_working",
                        thread_ts=thread_ts,
                        asker_id=task_data["asker_id"],
                        context_summary=task_data["context_summary"],
                    ),
                    text=f"[human_working] {task_data['question_text']}",
                )

                # Now listen for the resolver's reply
                register_active_thread(
                    thread_ts=thread_ts,
                    card_ts=task_data["card_ts"],
                    channel=task_data["channel"],
                    question_text=task_data["question_text"],
                    asker_id=task_data["asker_id"],
                    task_card_id=task_data["task_card_id"],
                )
            return

        # ── Resolution detection: resolver answers in human_working thread ─
        if thread_ts not in _active_threads:
            # Mira wasn't invoked — check if this looks like an ambient Q&A
            _maybe_nudge_ambient(thread_ts, user, text, channel, client, logger)
            return

        if not text:
            return

        task = _active_threads.pop(thread_ts)
        resolver_id = user

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
                    "answer": text,
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

        logger.info(f"Resolution detected in {thread_ts} by {resolver_id}")

    def _maybe_nudge_ambient(thread_ts, user, text, channel, client, logger):
        """Nudge to save when the original asker signals the question was resolved."""
        if thread_ts in _seen_ambient_threads:
            return

        try:
            replies = client.conversations_replies(channel=channel, ts=thread_ts, limit=20)
            messages = replies.get("messages", [])
            if len(messages) < 2:
                return

            parent = messages[0]
            asker_id = parent.get("user", "")
            parent_text = parent.get("text", "")

            # Only care when the original asker is replying
            if user != asker_id:
                return

            # Claude decides if this signals resolution — works in any language/phrasing
            if not classify_resolution(text):
                return

            # Mark seen now so further messages in this thread don't re-trigger
            _seen_ambient_threads.add(thread_ts)

            # Find the most recent substantive answer (from someone other than the asker)
            answer_msg = None
            for msg in reversed(messages[1:]):
                msg_user = msg.get("user", "")
                if msg_user and msg_user != asker_id:
                    answer_msg = msg
                    break

            if not answer_msg:
                return

            answer_text = answer_msg.get("text", "")

            # Skip deflections ("please create a ticket", etc.)
            if _DEFLECTION_PATTERNS.search(answer_text):
                return

            ctx = json.dumps({
                "question": parent_text[:500],
                "answer": answer_text[:500],
                "asker_id": asker_id,
                "resolver_id": answer_msg.get("user", ""),
                "thread_ts": thread_ts,
                "channel": channel,
            })
            client.chat_postMessage(
                channel=channel,
                thread_ts=thread_ts,
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "Looks like this was resolved! Want me to save it to the Knowledge Vault?",
                        },
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {"type": "plain_text", "text": "Save it ✓"},
                                "style": "primary",
                                "action_id": "ambient_save_yes",
                                "value": ctx,
                            },
                            {
                                "type": "button",
                                "text": {"type": "plain_text", "text": "No thanks"},
                                "action_id": "ambient_save_no",
                                "value": ctx,
                            },
                        ],
                    },
                ],
                text="Looks like this was resolved! Want me to save it to the Knowledge Vault?",
            )
        except Exception:
            logger.exception("Ambient Q&A nudge failed for thread %s", thread_ts)
