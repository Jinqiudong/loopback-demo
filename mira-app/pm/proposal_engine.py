"""
Enhancement Proposal engine — Mira's PM identity.

When triggered (via @Mira analyze or after enough task cards accumulate),
Claude reads the resolved task cards and generates an AI-written Enhancement
Proposal. No predefined templates — Claude decides what patterns are worth
surfacing and what they might mean.

Triggered by: @Mira analyze [in any channel]
Posts proposal to: the channel where it was triggered
"""

import anthropic
import json
import logging
from typing import Any

from config import ANTHROPIC_API_KEY
from services.vault_client import VaultClient

logger = logging.getLogger(__name__)

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
_vault = VaultClient()

_MODEL = "claude-sonnet-4-6"

_ANALYSIS_PROMPT = """You are Mira, an AI analyst embedded in a team's Slack workspace.
You have access to a Knowledge Vault — a collection of resolved support questions, each with:
- The original question
- The answer that was given
- Who answered it
- How many times similar questions have been asked
- Whether the answer was verified or is still suggested

Your job: read these task cards and identify patterns that suggest a product or system improvement.
Don't look for the most common question — look for what the pattern of questions *reveals* about
the underlying product, data, or process.

Write one Enhancement Proposal. Be specific about what you observed. Keep it concise.
Structure your response as:

**What Mira observed:**
[2-3 sentences about the pattern you noticed in the task cards]

**What this might mean:**
[1-2 sentences about the underlying product/system issue this suggests]

**Suggested next step:**
[One concrete, actionable suggestion]

**Source questions:**
[List the question_canonical values that informed this proposal]

Do not make up data. Only reference what is in the task cards provided.
If there is no meaningful pattern, say so honestly."""


def generate_proposal(task_cards: list[dict[str, Any]]) -> str:
    """
    Send task cards to Claude and get back an AI-generated Enhancement Proposal.
    Returns the proposal as a markdown string.
    """
    if not task_cards:
        return "Not enough resolved questions yet to identify patterns. Come back after a few more questions have been resolved."

    cards_text = "\n\n".join([
        f"Q: {card.get('question_canonical', 'Unknown')}\n"
        f"A: {card.get('current_answer', 'No answer recorded')}\n"
        f"Status: {card.get('status', 'unknown')} | "
        f"Confidence: {card.get('confidence_score', 0):.0%} | "
        f"Used: {card.get('usage_count', 0)} times"
        for card in task_cards
    ])

    try:
        response = _client.messages.create(
            model=_MODEL,
            max_tokens=600,
            system=_ANALYSIS_PROMPT,
            messages=[{
                "role": "user",
                "content": f"Here are the resolved task cards from the Knowledge Vault:\n\n{cards_text}"
            }],
        )
        return response.content[0].text.strip()
    except Exception:
        logger.exception("Claude proposal generation failed")
        return "Unable to generate proposal at this time."


_OPPORTUNITIES_PROMPT = """You are Mira, an AI analyst. Read the questions from this Slack channel
and identify 1-3 patterns that suggest a product, documentation, or process improvement.

Return ONLY a JSON array. Each item must have:
- "title": a 5-8 word phrase naming the pattern (e.g. "Leave policy not clearly documented")
- "related_count": number of questions that relate to this pattern
- "bullets": array of 2-3 strings — first bullet(s) describe what you observed, last bullet starts with "Suggested:"

If there are no meaningful patterns, return an empty array [].
Do not include any text outside the JSON array."""


def generate_opportunities(cards: list[dict], period_label: str) -> list[dict]:
    """
    Analyse channel task cards and return structured Enhancement Opportunities.
    Returns a list of dicts: {title, related_count, bullets}
    """
    if not cards:
        return []

    cards_text = "\n\n".join([
        f"Q: {card.get('question', 'Unknown')} (status: {card.get('status', '?')})"
        for card in cards
    ])

    try:
        response = _client.messages.create(
            model=_MODEL,
            max_tokens=600,
            system=_OPPORTUNITIES_PROMPT,
            messages=[{
                "role": "user",
                "content": f"Period: {period_label}\n\nQuestions:\n\n{cards_text}",
            }],
        )
        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()
        if not text:
            return []
        return json.loads(text)
    except Exception:
        logger.exception("Claude opportunity generation failed")
        return []


def generate_proposal_from_cards(cards: list[dict], channel_name: str, period_label: str) -> list[dict]:
    """
    Generate an Enhancement Proposal from channel task cards (insights data).
    Scoped to a specific channel and time period — more focused than global vault analysis.
    """
    if not cards:
        return [{
            "type": "section",
            "text": {"type": "mrkdwn",
                     "text": f"No resolved questions in #{channel_name} for {period_label} yet."},
        }]

    cards_text = "\n\n".join([
        f"Q: {card.get('question', 'Unknown')}\n"
        f"Status: {card.get('status', 'unknown')} | "
        f"Confidence: {card.get('confidence_score', 0):.0%}"
        for card in cards
    ])

    try:
        response = _client.messages.create(
            model=_MODEL,
            max_tokens=500,
            system=_ANALYSIS_PROMPT,
            messages=[{
                "role": "user",
                "content": (
                    f"Channel: #{channel_name} | Period: {period_label}\n\n"
                    f"Questions from this channel:\n\n{cards_text}"
                ),
            }],
        )
        proposal_text = response.content[0].text.strip()
    except Exception:
        logger.exception("Claude proposal generation failed")
        proposal_text = "Unable to generate proposal at this time."

    return [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "Enhancement Proposal"},
        },
        {
            "type": "context",
            "elements": [{"type": "mrkdwn",
                          "text": f"AI-generated from #{channel_name} · {period_label}"}],
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": proposal_text},
        },
        {"type": "divider"},
        {
            "type": "actions",
            "elements": [
                {"type": "button", "text": {"type": "plain_text", "text": "Approve"},
                 "style": "primary", "action_id": "proposal_approve"},
                {"type": "button", "text": {"type": "plain_text", "text": "Defer"},
                 "action_id": "proposal_defer"},
                {"type": "button", "text": {"type": "plain_text", "text": "Reject"},
                 "style": "danger", "action_id": "proposal_reject"},
            ],
        },
        {
            "type": "context",
            "elements": [{"type": "mrkdwn",
                          "text": "Powered by Mira · Analysis based on this channel's questions only"}],
        },
    ]


def run_proposal_engine(say, channel: str) -> None:
    """
    Fetch vault entries, run Claude analysis, post result as a structured
    Block Kit card in the channel.
    """
    entries = _vault.list_entries(limit=20)

    if not entries:
        say(
            channel=channel,
            text="The Knowledge Vault doesn't have enough entries yet to analyze patterns. "
                 "Resolve a few more questions first.",
        )
        return

    proposal_text = generate_proposal(entries)

    say(
        channel=channel,
        blocks=_build_proposal_card(proposal_text, len(entries)),
        text="Enhancement Proposal from Mira",
    )


def _build_proposal_card(proposal_text: str, entry_count: int) -> list[dict]:
    return [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "Enhancement Proposal"},
        },
        {
            "type": "context",
            "elements": [{"type": "mrkdwn",
                          "text": f"AI-generated from {entry_count} resolved questions in the Knowledge Vault"}],
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": proposal_text},
        },
        {"type": "divider"},
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Approve"},
                    "style": "primary",
                    "action_id": "proposal_approve",
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Defer"},
                    "action_id": "proposal_defer",
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Reject"},
                    "style": "danger",
                    "action_id": "proposal_reject",
                },
            ],
        },
        {
            "type": "context",
            "elements": [{"type": "mrkdwn",
                          "text": "Powered by Mira · Analysis based on Knowledge Vault data only"}],
        },
    ]
