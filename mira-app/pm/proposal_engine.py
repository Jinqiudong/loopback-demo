"""
Enhancement Proposal engine — Mira's PM identity.

Claude reads accumulated task cards and identifies patterns worth surfacing
as product/workflow improvement proposals. No templates — Claude decides
what matters and how to phrase it.

Entry points:
  generate_opportunities(cards, period_label) → list of {title, related_count, bullets}
"""

import json
import logging
from typing import Any

from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL

logger = logging.getLogger(__name__)

import anthropic
_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

_OPPORTUNITIES_PROMPT = """You are Mira, an AI analyst. Read the questions from this Slack channel
and identify 1-3 patterns that suggest a product, documentation, or process improvement.

Return ONLY a JSON array. Each item must have:
- "title": a 5-8 word phrase naming the pattern (e.g. "Leave policy not clearly documented")
- "category": one of "documentation", "code", "ux", "process", "product"
- "related_count": number of questions that relate to this pattern
- "bullets": array of 2-3 strings — first bullet(s) describe what you observed, last bullet starts with "Suggested:"

Category guide:
  documentation — missing or unclear docs, runbooks, FAQs
  code          — bug, data pipeline issue, schema/query problem
  ux            — confusing UI, poor discoverability
  process       — unclear workflow, missing ownership, manual steps that should be automated
  product       — missing feature or capability gap

If there are no meaningful patterns, return an empty array [].
Do not include any text outside the JSON array."""


def generate_opportunities(cards: list[dict[str, Any]], period_label: str) -> list[dict]:
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
            model=ANTHROPIC_MODEL,
            max_tokens=600,
            system=_OPPORTUNITIES_PROMPT,
            messages=[{
                "role": "user",
                "content": f"Period: {period_label}\n\nQuestions:\n\n{cards_text}",
            }],
        )
        text = response.content[0].text.strip()
        # Strip markdown code fences if present
        if "```" in text:
            parts = text.split("```")
            text = parts[1].lstrip("json").strip() if len(parts) > 1 else text
        if not text:
            return []
        return json.loads(text)
    except Exception:
        logger.exception("Claude opportunity generation failed")
        return []
