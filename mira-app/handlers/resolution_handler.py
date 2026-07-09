"""
Unified message handler covering four cases:

1. Proactive detection  — top-level question, no @Mira → Mira investigates automatically
2. direction_check      — requester's "yes" confirms Mira's findings → escalate to resolver
3. human_working        — resolver's reply → update card to pending_confirm
4. Ambient detection    — untracked thread resolves → Mira offers to save the Q&A

This is the zero-@mention flow: teams work normally, Mira handles everything.
"""

import json
import re

from config import VAULT_HIGH_CONFIDENCE_THRESHOLD
from services.intent import classify_intent, classify_resolution, classify_direction_response, classify_is_deflection
from services.reactions import update_status_reaction
from services.task_card import build_task_card
from services.vault_client import VaultClient

# Structural pattern only — detects Slack bot mention format <@U...>, not semantic
_BOT_MENTION_RE = re.compile(r"<@[A-Z0-9]+>")

# Minimum message length for proactive question detection (filters out reactions, single words)
_MIN_PROACTIVE_LENGTH = 15

_vault = VaultClient()

# human_working threads: {thread_ts → task context}
_active_threads: dict = {}

# direction_check threads: {thread_ts → task context + context_summary}
_direction_threads: dict = {}

# pending_confirm threads where user may type instead of clicking button
_pending_threads: dict = {}

# threads where Mira already sent (or decided not to send) an ambient nudge
_seen_ambient_threads: set = set()


def register_pending_thread(thread_ts, card_ts, channel, question_text, asker_id, task_card_id, answer, vault_hit):
    """Track pending_confirm threads so text replies are handled."""
    _pending_threads[thread_ts] = {
        "card_ts": card_ts,
        "channel": channel,
        "question_text": question_text,
        "asker_id": asker_id,
        "task_card_id": task_card_id,
        "answer": answer,
        "vault_hit": vault_hit,
    }


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

        if not user or user == bot_user_id or event.get("subtype"):
            return

        # ── Proactive detection: top-level question, no @Mira ────────────
        if not thread_ts:
            # Skip if message already mentions Mira (handle_mention will cover it)
            if text and len(text) >= _MIN_PROACTIVE_LENGTH and not _BOT_MENTION_RE.search(text):
                _investigate_proactively(text, channel, event.get("ts", ""),
                                         user, client, logger)
            return

        # ── Direction check: requester responds to Mira's findings ──────────
        if thread_ts in _direction_threads:
            task = _direction_threads[thread_ts]
            if user != task["asker_id"]:
                return

            direction = classify_direction_response(text)

            if direction == "ESCALATE":
                task_data = _direction_threads.pop(thread_ts)
                logger.info(f"Direction confirmed in {thread_ts}, escalating to resolver")

                try:
                    _vault.update_status(task_data["task_card_id"], "human_working")
                    update_status_reaction(client, task_data["channel"], thread_ts, "human_working")
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

                # Status reaction on the original message signals the team visually
                update_status_reaction(client, task_data["channel"], thread_ts, "human_working")

                # Now listen for the resolver's reply
                register_active_thread(
                    thread_ts=thread_ts,
                    card_ts=task_data["card_ts"],
                    channel=task_data["channel"],
                    question_text=task_data["question_text"],
                    asker_id=task_data["asker_id"],
                    task_card_id=task_data["task_card_id"],
                )

            elif direction == "RESOLVED":
                task_data = _direction_threads.pop(thread_ts)
                _seen_ambient_threads.add(thread_ts)
                ctx = json.dumps({
                    "question": task_data["question_text"],
                    "answer": task_data.get("context_summary", ""),
                    "asker_id": task_data["asker_id"],
                    "resolver_id": "",
                    "thread_ts": thread_ts,
                    "channel": task_data["channel"],
                })
                client.chat_postMessage(
                    channel=task_data["channel"],
                    thread_ts=thread_ts,
                    blocks=[
                        {"type": "section", "text": {"type": "mrkdwn",
                            "text": "Glad that helped! Want me to save this to the Knowledge Vault so the next person gets an instant answer?"}},
                        {"type": "actions", "elements": [
                            {"type": "button", "text": {"type": "plain_text", "text": "Save it ✓"},
                             "style": "primary", "action_id": "ambient_save_yes", "value": ctx},
                            {"type": "button", "text": {"type": "plain_text", "text": "No thanks"},
                             "action_id": "ambient_save_no", "value": ctx},
                        ]},
                    ],
                    text="Want me to save this to the Knowledge Vault?",
                )
            return

        # ── Pending confirm: user typed instead of clicking button ────────────
        if thread_ts in _pending_threads:
            task = _pending_threads[thread_ts]
            if user == task["asker_id"]:
                direction = classify_direction_response(text)
                if direction == "RESOLVED":
                    _pending_threads.pop(thread_ts)
                    # treat same as button click "This helped"
                    client.chat_update(
                        channel=task["channel"],
                        ts=task["card_ts"],
                        blocks=build_task_card(
                            task["question_text"], status="verified",
                            results=[{"task_card_id": task["task_card_id"],
                                      "answer": task["answer"], "confidence": 0.95,
                                      "verified": True, "owner_id": ""}],
                            thread_ts=thread_ts, asker_id=task["asker_id"],
                            vault_hit=task["vault_hit"],
                        ),
                        text=f"[verified] {task['question_text']}",
                    )
                elif direction == "ESCALATE":
                    _pending_threads.pop(thread_ts)
                    _vault.update_status(task["task_card_id"], "escalate")
                    client.chat_update(
                        channel=task["channel"],
                        ts=task["card_ts"],
                        blocks=build_task_card(
                            task["question_text"], status="escalate",
                            thread_ts=thread_ts, asker_id=task["asker_id"],
                        ),
                        text=f"[escalate] {task['question_text']}",
                    )
                    register_active_thread(
                        thread_ts, task["card_ts"], task["channel"],
                        task["question_text"], task["asker_id"], task["task_card_id"],
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
            update_status_reaction(client, task["channel"], thread_ts, "pending_confirm")
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
            if classify_is_deflection(answer_text):
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
        except Exception as e:
            if "thread_not_found" not in str(e):
                logger.exception("Ambient Q&A nudge failed for thread %s", thread_ts)


# ── Proactive investigation (called for top-level questions) ──────────────────

# Tracks messages already being investigated to avoid duplicates on edits
_proactive_seen: set = set()


def _investigate_proactively(text: str, channel: str, message_ts: str,
                              asker_id: str, client, logger) -> None:
    """
    Mira proactively investigates a question posted without @mention.
    Same full flow as @Mira: Vault search → Claude investigation → direction check.
    """
    if message_ts in _proactive_seen:
        return
    _proactive_seen.add(message_ts)
    _seen_ambient_threads.add(message_ts)  # prevent ambient nudge on same thread

    intent = classify_intent(text)
    if not intent.is_question:
        _proactive_seen.discard(message_ts)
        return

    logger.info(f"Proactive investigation triggered for: {text!r}")

    from services.investigator import investigate

    # Post draft card as a reply (creates a thread under the original message)
    try:
        resp = client.chat_postMessage(
            channel=channel,
            thread_ts=message_ts,
            blocks=build_task_card(text, status="draft",
                                   thread_ts=message_ts, asker_id=asker_id),
            text=f"[draft] {text}",
        )
        card_ts = resp["ts"]
    except Exception:
        logger.exception("Proactive: failed to post draft card")
        return

    client.chat_update(
        channel=channel, ts=card_ts,
        blocks=build_task_card(text, status="ai_searching",
                               thread_ts=message_ts, asker_id=asker_id),
        text=f"[ai_searching] {text}",
    )

    # Vault search
    try:
        task_card_id = _vault.create_task_card(
            requester_id=asker_id, channel_id=channel,
            thread_ts=message_ts, question_raw=text, question_intent=intent.raw_label,
        )
        vault_result = _vault.search(text)
    except Exception:
        logger.exception("Proactive: Vault call failed")
        client.chat_update(
            channel=channel, ts=card_ts,
            blocks=build_task_card(text, status="human_working",
                                   thread_ts=message_ts, asker_id=asker_id),
            text=f"[human_working] {text}",
        )
        register_active_thread(message_ts, card_ts, channel, text, asker_id, task_card_id)
        return

    if vault_result["match_found"]:
        confidence = vault_result.get("confidence", 0)
        vault_hit = confidence >= VAULT_HIGH_CONFIDENCE_THRESHOLD
        _vault.update_status(task_card_id, "pending_confirm")
        update_status_reaction(client, channel, message_ts, "pending_confirm")
        client.chat_update(
            channel=channel, ts=card_ts,
            blocks=build_task_card(text, status="pending_confirm",
                                   results=[{**vault_result, "task_card_id": task_card_id}],
                                   thread_ts=message_ts, asker_id=asker_id,
                                   vault_hit=vault_hit),
            text=f"[pending_confirm] {text}",
        )
        register_pending_thread(
            thread_ts=message_ts, card_ts=card_ts, channel=channel,
            question_text=text, asker_id=asker_id, task_card_id=task_card_id,
            answer=vault_result.get("answer", ""), vault_hit=vault_hit,
        )
        return

    # Tier 2: Claude agentic investigation
    context_summary = investigate(text)

    if context_summary:
        update_status_reaction(client, channel, message_ts, "human_working")
        client.chat_update(
            channel=channel, ts=card_ts,
            blocks=build_task_card(text, status="direction_check",
                                   thread_ts=message_ts, asker_id=asker_id,
                                   context_summary=context_summary),
            text=f"[direction_check] {text}",
        )
        register_direction_thread(message_ts, card_ts, channel, text,
                                  asker_id, task_card_id, context_summary)
    else:
        _vault.update_status(task_card_id, "human_working")
        update_status_reaction(client, channel, message_ts, "human_working")
        client.chat_update(
            channel=channel, ts=card_ts,
            blocks=build_task_card(text, status="human_working",
                                   thread_ts=message_ts, asker_id=asker_id),
            text=f"[human_working] {text}",
        )
        register_active_thread(message_ts, card_ts, channel, text, asker_id, task_card_id)
