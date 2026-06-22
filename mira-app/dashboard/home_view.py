"""
App Home Dashboard — the Knowledge Vault UI inside Slack.

Renders all vault entries as cards: question, answer preview, confidence,
owner, usage count, and status badge. Lives in Mira's App Home tab so
it's always one click away without leaving Slack.
"""

from typing import Any

from services.vault_client import VaultClient

_vault = VaultClient()

_STATUS_EMOJI = {
    "verified": "✅",
    "unconfirmed": "💡",
    "outdated": "⚠️",
}

_ANSWER_PREVIEW = 120


def build_home_view() -> dict:
    entries = _vault.list_entries()

    blocks: list[dict] = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "Knowledge Vault"},
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": (
                        f"{len(entries)} entr{'y' if len(entries) == 1 else 'ies'}  ·  "
                        f"{sum(1 for e in entries if e['status'] == 'verified')} verified  ·  "
                        f"{sum(e.get('usage_count', 0) for e in entries)} total uses"
                    ),
                }
            ],
        },
        {"type": "divider"},
    ]

    if not entries:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    "*No entries yet.*\n"
                    "The Vault fills automatically as questions get resolved in Slack. "
                    "Ask Mira something to get started."
                ),
            },
        })
    else:
        for entry in entries:
            blocks.extend(_entry_blocks(entry))
            blocks.append({"type": "divider"})

    return {"type": "home", "blocks": blocks}


def _entry_blocks(entry: dict[str, Any]) -> list[dict]:
    status = entry.get("status", "unconfirmed")
    emoji = _STATUS_EMOJI.get(status, "❓")
    confidence = entry.get("confidence_score", 0)
    usage = entry.get("usage_count", 0)
    owner = entry.get("owner_id", "")
    answer = entry.get("current_answer", "")

    if len(answer) > _ANSWER_PREVIEW:
        answer = answer[:_ANSWER_PREVIEW].rstrip() + "…"

    meta_parts = [f"{int(confidence * 100)}% confidence"]
    if owner:
        meta_parts.append(f"answered by <@{owner}>")
    if usage:
        meta_parts.append(f"used {usage} time{'s' if usage > 1 else ''}")

    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"{emoji}  *{entry.get('question_canonical', '')}*\n{answer}",
            },
        },
        {
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": "  ·  ".join(meta_parts)}],
        },
    ]


def register_home_handler(app) -> None:
    @app.event("app_home_opened")
    def handle_home_opened(event, client, logger):
        try:
            client.views_publish(
                user_id=event["user"],
                view=build_home_view(),
            )
        except Exception:
            logger.exception("Failed to publish App Home view")
