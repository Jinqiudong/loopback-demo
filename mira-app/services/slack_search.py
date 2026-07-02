"""
Slack Real-Time Search API integration.

Searches workspace message history for existing answers to a question.
Used as the middle tier: Vault miss → Slack history → human escalation.

Requires a user token (SLACK_USER_TOKEN) with search:read scope.
Bot tokens cannot call search.messages — this is a Slack API constraint.
Add SLACK_USER_TOKEN to .env to enable; if absent, search is skipped silently.
"""

import logging
import os
import re
from typing import Any

from slack_sdk import WebClient

logger = logging.getLogger(__name__)

_SLACK_USER_TOKEN = os.environ.get("SLACK_USER_TOKEN", "")
_MIN_ANSWER_LENGTH = 40
_BOT_MENTION_PATTERN = r"<@[A-Z0-9]+>"


def _is_valid_answer(text: str) -> bool:
    if len(text) < _MIN_ANSWER_LENGTH:
        return False
    if re.search(_BOT_MENTION_PATTERN, text):
        return False
    if text.strip().endswith("?"):
        return False
    return True


def search_slack_history(query: str, count: int = 3) -> list[dict[str, Any]]:
    """
    Search Slack message history for messages related to the query.
    Returns candidates sorted by relevance, empty list if search unavailable.
    """
    if not _SLACK_USER_TOKEN:
        logger.debug("SLACK_USER_TOKEN not set — skipping Slack history search")
        return []

    try:
        user_client = WebClient(token=_SLACK_USER_TOKEN)
        result = user_client.search_messages(query=query, count=count, sort="score")
        matches = result.get("messages", {}).get("matches", [])

        return [
            {
                "text": m.get("text", ""),
                "permalink": m.get("permalink", ""),
                "username": m.get("username", ""),
                "user": m.get("user", ""),
                "channel_name": m.get("channel", {}).get("name", ""),
            }
            for m in matches
            if _is_valid_answer(m.get("text", ""))
        ]
    except Exception:
        logger.warning("Slack history search failed", exc_info=True)
        return []
