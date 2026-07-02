"""
Handles @Mira mentions.

Three-tier resolution flow:
  Tier 1: Knowledge Vault (semantic search)
  Tier 2: Slack history + GitHub MCP + Data Dictionary (parallel)
  Tier 3: Escalate to resolver

v2 addition: if Tier 2 finds something, Mira enriches the task card with findings
and asks the requester to confirm direction before looping in the resolver.

Special trigger: if the message contains "analyze" → run Enhancement Proposal engine.
"""

import re

from services.intent import classify_intent
from services.investigator import investigate
from services.task_card import build_task_card
from services.vault_client import VaultClient
from handlers.resolution_handler import register_active_thread, register_direction_thread

_MENTION_PATTERN = re.compile(r"<@[A-Z0-9]+>")
_vault = VaultClient()

_VAULT_HIGH_CONFIDENCE = 0.85
_VAULT_LOW_CONFIDENCE = 0.70


def _strip_mention(raw_text: str) -> str:
    return _MENTION_PATTERN.sub("", raw_text).strip()


def _update_card(client, channel, ts, question, status,
                 results=None, thread_ts=None, asker_id=None,
                 vault_hit=False, context_summary=None):
    client.chat_update(
        channel=channel,
        ts=ts,
        blocks=build_task_card(question, status=status, results=results,
                                thread_ts=thread_ts, asker_id=asker_id,
                                vault_hit=vault_hit, context_summary=context_summary),
        text=f"[{status}] {question}",
    )



def register_mention_handler(app):
    @app.event("app_mention")
    def handle_mention(event, say, client, logger):
        question_text = _strip_mention(event.get("text", ""))

        if not question_text:
            return

        # Special trigger: @Mira insights → Channel Insights Canvas period selector
        if re.search(r"\binsights?\b", question_text, re.IGNORECASE):
            from dashboard.channel_canvas import build_period_selector
            say(
                channel=event["channel"],
                blocks=build_period_selector(event["channel"]),
                text="Which time period would you like to see?",
            )
            return

        # Special trigger: @Mira analyze → Enhancement Proposal engine
        if re.search(r"\banalyze\b", question_text, re.IGNORECASE):
            from pm.proposal_engine import generate_opportunities
            cards = _vault.get_channel_insights(event["channel"], since="month")
            opportunities = generate_opportunities(cards, "This Month")
            if opportunities:
                opp = opportunities[0]
                bullets = "\n".join(f"• {b}" for b in opp.get("bullets", []))
                say(
                    channel=event["channel"],
                    blocks=[
                        {"type": "header", "text": {"type": "plain_text", "text": "Enhancement Opportunity"}},
                        {"type": "context", "elements": [{"type": "mrkdwn", "text": f"AI-generated from {opp.get('related_count', 0)} related questions"}]},
                        {"type": "divider"},
                        {"type": "section", "text": {"type": "mrkdwn", "text": f"*{opp.get('title', '')}*\n{bullets}"}},
                        {"type": "divider"},
                        {"type": "actions", "elements": [
                            {"type": "button", "text": {"type": "plain_text", "text": "Approve"}, "style": "primary", "action_id": "proposal_approve"},
                            {"type": "button", "text": {"type": "plain_text", "text": "Defer"}, "action_id": "proposal_defer"},
                            {"type": "button", "text": {"type": "plain_text", "text": "Reject"}, "style": "danger", "action_id": "proposal_reject"},
                        ]},
                    ],
                    text="Enhancement Opportunity from Mira",
                )
            else:
                say(channel=event["channel"],
                    text="Not enough resolved questions yet to identify patterns.")
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

        # ── Tier 1: Vault hit ─────────────────────────────────────────────
        if vault_result["match_found"]:
            confidence = vault_result.get("confidence", 0)
            result_payload = [{**vault_result, "task_card_id": task_card_id}]

            _vault.update_status(task_card_id, "pending_confirm")

            if confidence >= _VAULT_HIGH_CONFIDENCE:
                _update_card(client, channel, card_ts, question_text, "pending_confirm",
                             results=result_payload,
                             thread_ts=thread_ts, asker_id=asker_id, vault_hit=True)
            else:
                # Medium confidence: show answer but post clarifying question
                _update_card(client, channel, card_ts, question_text, "pending_confirm",
                             results=result_payload,
                             thread_ts=thread_ts, asker_id=asker_id, vault_hit=False)
                say(channel=channel, thread_ts=thread_ts,
                    text=f"I found something that might be related — is this the same as what you're asking? ({int(confidence * 100)}% match)")
            return

        # ── Tier 2: Agentic investigation (Claude tool use) ──────────────
        # Claude autonomously decides what to search — this is the MCP pattern.
        context_summary = investigate(question_text)

        if context_summary:
            # Don't update DB status yet — wait for requester to confirm direction
            _update_card(client, channel, card_ts, question_text, "direction_check",
                         thread_ts=thread_ts, asker_id=asker_id,
                         context_summary=context_summary)

            say(channel=channel, thread_ts=thread_ts,
                text="Based on what I found, does this look like the right direction? Reply *yes* to loop in your team.")

            register_direction_thread(
                thread_ts=thread_ts,
                card_ts=card_ts,
                channel=channel,
                question_text=question_text,
                asker_id=asker_id,
                task_card_id=task_card_id,
                context_summary=context_summary,
            )

        else:
            # ── Tier 3: Escalate ─────────────────────────────────────────
            _vault.update_status(task_card_id, "human_working")
            _update_card(client, channel, card_ts, question_text, "human_working",
                         thread_ts=thread_ts, asker_id=asker_id)
            register_active_thread(
                thread_ts=thread_ts,
                card_ts=card_ts,
                channel=channel,
                question_text=question_text,
                asker_id=asker_id,
                task_card_id=task_card_id,
            )
