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

import anthropic

from config import ANTHROPIC_API_KEY
from services.intent import classify_intent
from services.mcp_github import gather_context
from services.slack_search import search_slack_history
from services.task_card import build_task_card
from services.vault_client import VaultClient
from handlers.resolution_handler import register_active_thread, register_direction_thread

_MENTION_PATTERN = re.compile(r"<@[A-Z0-9]+>")
_vault = VaultClient()
_claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

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


def _summarise_findings(question: str, findings: dict) -> str:
    """Use Claude to synthesise Tier 2 findings into a concise summary."""
    if not findings:
        return ""

    parts = []
    if "code_files" in findings:
        for f in findings["code_files"]:
            parts.append(f"**{f['filename']}**:\n```\n{f['excerpt']}\n```")
    if "known_issues" in findings:
        parts.append(f"**Known issues doc:**\n{findings['known_issues'][:1200]}")
    if "data_dictionary" in findings and not parts:
        parts.append(f"**Data dictionary:**\n{findings['data_dictionary'][:600]}")

    if not parts:
        return ""

    raw_context = "\n\n".join(parts)

    try:
        response = _claude.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=200,
            system=(
                "You are Mira, an AI assistant. Summarise the following findings "
                "in 2-3 bullet points that are directly relevant to the user's question. "
                "Be specific. Use plain text, no markdown headers."
            ),
            messages=[{
                "role": "user",
                "content": f"Question: {question}\n\nFindings:\n{raw_context}"
            }],
        )
        return response.content[0].text.strip()
    except Exception:
        return raw_context[:300]


def register_mention_handler(app):
    @app.event("app_mention")
    def handle_mention(event, say, client, logger):
        question_text = _strip_mention(event.get("text", ""))

        if not question_text:
            return

        # Special trigger: @Mira analyze → run Enhancement Proposal engine
        if re.search(r"\banalyze\b", question_text, re.IGNORECASE):
            from pm.proposal_engine import run_proposal_engine
            run_proposal_engine(say, channel=event["channel"])
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

        # ── Tier 2: Parallel search ───────────────────────────────────────
        history_results = search_slack_history(question_text)
        github_findings = gather_context(question_text)

        has_findings = bool(history_results or github_findings)

        if has_findings:
            context_summary = _summarise_findings(question_text, github_findings)
            if not context_summary and history_results:
                context_summary = f"• Found related message: {history_results[0].get('permalink', '')}"

            # Update card to direction_check state
            _vault.update_status(task_card_id, "pending_confirm")
            _update_card(client, channel, card_ts, question_text, "direction_check",
                         thread_ts=thread_ts, asker_id=asker_id,
                         context_summary=context_summary)

            # Ask requester to confirm direction
            say(channel=channel, thread_ts=thread_ts,
                text=f"Based on what I found, does this look like the right direction? Reply *yes* to loop in your team.")

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
