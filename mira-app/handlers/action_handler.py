"""
Handles Block Kit button actions from task cards.

vault_confirm     — "This helped ✓" / "Yes, resolved ✓"
                    Calls upsert_entry (signal_1) to write the verified answer to the Vault.
vault_not_helpful — "Outdated?" / "Not quite"
                    Updates status to escalate so a teammate tries again.
"""

import json
from typing import Optional

from services.reactions import update_status_reaction
from services.task_card import build_task_card
from services.vault_client import VaultClient
from handlers.resolution_handler import register_active_thread
from dashboard.channel_canvas import (
    update_canvas, build_period_selector,
    period_since, period_label,
)

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
        thread_ts = value.get("thread_ts") or body["message"].get("thread_ts")
        asker_id = value.get("asker_id")
        vault_hit = value.get("vault_hit", False)
        question_text = value.get("question", "")
        channel = body["channel"]["id"]
        message_ts = body["message"]["ts"]
        source_thread = _thread_permalink(channel, thread_ts)

        try:
            if vault_hit and entry_id:
                # Answer already in Vault — just record the usage, don't create a duplicate entry.
                # source_thread must stay pointing to the ORIGINAL thread, not this one.
                _vault.update_status(task_card_id, "verified", vault_entry_id=entry_id)
            else:
                _vault.upsert_entry(
                    task_card_id=task_card_id,
                    question_canonical=question_text,
                    answer=answer,
                    owner_id=owner_id,
                    signal="signal_1",
                    source_thread=source_thread,
                )
            update_status_reaction(client, channel, thread_ts, "verified")
        except Exception:
            logger.exception("Vault confirm failed")

        # Silently refresh Channel Insights Canvas so it stays current after each resolution
        try:
            from dashboard.channel_canvas import update_canvas, period_since, period_label
            cards = _vault.get_channel_insights(channel, since=period_since("month"))
            ch_name = body.get("channel", {}).get("name") or channel
            update_canvas(client, channel, cards, ch_name, period_label("month"))
        except Exception:
            pass  # canvas refresh is best-effort, never block the confirm flow

        # For vault hits, keep the original source_thread from the existing entry
        display_source_thread = source_thread if not vault_hit else value.get("source_thread", source_thread)

        client.chat_update(
            channel=channel,
            ts=message_ts,
            blocks=build_task_card(
                question_text,
                status="verified",
                results=[{"task_card_id": task_card_id, "entry_id": entry_id,
                          "answer": answer, "confidence": 0.95,
                          "owner_id": owner_id, "source_thread": display_source_thread}],
                thread_ts=thread_ts,
                asker_id=asker_id,
                vault_hit=vault_hit,
            ),
            text=f"[verified] {question_text}",
        )

    @app.action("vault_not_helpful")
    def handle_not_helpful(ack, body, client, logger):
        ack()
        value = _parse_value(body)
        task_card_id = value.get("task_card_id", "")
        thread_ts = value.get("thread_ts") or body["message"].get("thread_ts")
        asker_id = value.get("asker_id")
        vault_hit = value.get("vault_hit", False)
        channel = body["channel"]["id"]
        message_ts = body["message"]["ts"]
        question_text = value.get("question", "")

        try:
            _vault.update_status(task_card_id, "escalate")
            update_status_reaction(client, channel, thread_ts, "escalate")
        except Exception:
            logger.exception("Vault update_status failed on not_helpful")

        client.chat_update(
            channel=channel,
            ts=message_ts,
            blocks=build_task_card(question_text, status="escalate",
                                   thread_ts=thread_ts, asker_id=asker_id,
                                   vault_hit=vault_hit),
            text=f"[escalate] {question_text}",
        )

        # Re-register thread so Mira keeps listening for a second resolver attempt
        if thread_ts:
            register_active_thread(
                thread_ts=thread_ts,
                card_ts=message_ts,
                channel=channel,
                question_text=question_text,
                asker_id=asker_id or "",
                task_card_id=task_card_id,
            )


    def _handle_insights(period: str, ack, body, client, logger):
        ack()
        channel_id = body["actions"][0].get("value", body["channel"]["id"])
        # Use name from body if available, fall back to channel_id (avoids channels:read scope)
        channel_name = body.get("channel", {}).get("name") or channel_id

        cards = _vault.get_channel_insights(channel_id, since=period_since(period))
        label = period_label(period)

        ok = update_canvas(client, channel_id, cards, channel_name, label)

        if ok:
            client.chat_update(
                channel=body["channel"]["id"],
                ts=body["message"]["ts"],
                blocks=build_period_selector(channel_id, updated_label=label),
                text=f"Channel Insights canvas updated — {label}",
            )
        else:
            logger.warning("Canvas update failed for channel %s — check CANVAS_ID_%s env var", channel_id, channel_id)
            client.chat_postMessage(
                channel=channel_id,
                text=f"⚠️ Canvas update failed. Set env var `CANVAS_ID_{channel_id}` in Railway with the canvas ID.",
            )

    @app.action("insights_this_month")
    def handle_insights_month(ack, body, client, logger):
        _handle_insights("month", ack, body, client, logger)

    @app.action("insights_this_quarter")
    def handle_insights_quarter(ack, body, client, logger):
        _handle_insights("quarter", ack, body, client, logger)

    @app.action("insights_this_year")
    def handle_insights_year(ack, body, client, logger):
        _handle_insights("year", ack, body, client, logger)

    @app.action("proposal_approve")
    def handle_proposal_approve(ack, body, say, logger):
        ack()
        say(channel=body["channel"]["id"],
            thread_ts=body["message"].get("thread_ts", body["message"]["ts"]),
            text="Approved. Adding to the product backlog.")

    @app.action("proposal_defer")
    def handle_proposal_defer(ack, body, say, logger):
        ack()
        say(channel=body["channel"]["id"],
            thread_ts=body["message"].get("thread_ts", body["message"]["ts"]),
            text="Deferred. Mira will resurface this when more data accumulates.")

    @app.action("proposal_reject")
    def handle_proposal_reject(ack, body, say, logger):
        ack()
        say(channel=body["channel"]["id"],
            thread_ts=body["message"].get("thread_ts", body["message"]["ts"]),
            text="Noted. Proposal rejected.")

    @app.action("ambient_save_yes")
    def handle_ambient_save_yes(ack, body, client, logger):
        ack()
        value = _parse_value(body)
        question = value.get("question", "")
        answer = value.get("answer", "")
        asker_id = value.get("asker_id", "")
        resolver_id = value.get("resolver_id", "")
        thread_ts = value.get("thread_ts", "")
        channel = value.get("channel") or body["channel"]["id"]
        source_thread = _thread_permalink(channel, thread_ts)

        try:
            task_card_id = _vault.create_task_card(
                requester_id=asker_id,
                channel_id=channel,
                thread_ts=thread_ts,
                question_raw=question,
            )
            _vault.upsert_entry(
                task_card_id=task_card_id,
                question_canonical=question,
                answer=answer,
                owner_id=resolver_id,
                signal="signal_1",
                source_thread=source_thread,
            )
            # Update task card status so Channel Insights counts it correctly
            _vault.update_status(task_card_id, "verified")
            update_status_reaction(client, channel, thread_ts, "verified")
        except Exception:
            logger.exception("Ambient vault save failed")

        client.chat_update(
            channel=body["channel"]["id"],
            ts=body["message"]["ts"],
            blocks=[{"type": "section", "text": {"type": "mrkdwn", "text": "Saved to the Knowledge Vault ✓"}}],
            text="Saved to the Knowledge Vault ✓",
        )

    @app.action("ambient_save_no")
    def handle_ambient_save_no(ack, body, client, logger):
        ack()
        client.chat_update(
            channel=body["channel"]["id"],
            ts=body["message"]["ts"],
            blocks=[{"type": "section", "text": {"type": "mrkdwn", "text": "Got it, I'll leave this one."}}],
            text="Got it, I'll leave this one.",
        )



def _parse_value(body: dict) -> dict:
    try:
        return json.loads(body["actions"][0]["value"])
    except (KeyError, IndexError, json.JSONDecodeError):
        return {}


def _thread_permalink(channel: str, thread_ts: Optional[str]) -> str:
    if not thread_ts:
        return ""
    ts_compact = thread_ts.replace(".", "")
    return f"https://slack.com/archives/{channel}/p{ts_compact}"
