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
            logger.exception("Vault upsert_entry failed on confirm")

        client.chat_update(
            channel=channel,
            ts=message_ts,
            blocks=build_task_card(
                question_text,
                status="verified",
                results=[{"task_card_id": task_card_id, "entry_id": entry_id,
                          "answer": answer, "confidence": 0.95,
                          "owner_id": owner_id, "source_thread": source_thread}],
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
            logger.warning("Canvas update failed for channel %s", channel_id)

        # Post compact action card — full content is in the Canvas, buttons stay in chat
        from pm.proposal_engine import generate_opportunities
        opportunities = generate_opportunities(cards, label)
        if opportunities:
            opp = opportunities[0]
            client.chat_postMessage(
                channel=body["channel"]["id"],
                blocks=[
                    {"type": "section", "text": {"type": "mrkdwn",
                        "text": f"🌱 *Enhancement Opportunity identified* — see Canvas for full analysis\n*{opp.get('title', '')}*  ·  {opp.get('related_count', 0)} related questions"}},
                    {"type": "actions", "elements": [
                        {"type": "button", "text": {"type": "plain_text", "text": "Approve"}, "style": "primary", "action_id": "proposal_approve"},
                        {"type": "button", "text": {"type": "plain_text", "text": "Defer"}, "action_id": "proposal_defer"},
                        {"type": "button", "text": {"type": "plain_text", "text": "Reject"}, "style": "danger", "action_id": "proposal_reject"},
                    ]},
                ],
                text="Enhancement Opportunity identified — see Canvas for details",
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
