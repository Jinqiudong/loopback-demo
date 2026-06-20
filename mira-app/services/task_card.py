"""
Builds the Block Kit representation of a task card.
"""

from typing import Any

STATUS_LABELS = {
    "draft": "Draft",
    "ai_searching": "Searching",
    "human_working": "Waiting on a teammate",
    "pending_confirm": "Waiting on you to confirm",
    "verified": "Verified",
    "unconfirmed": "Suggested, not yet verified",
    "escalate": "Escalated",
}

_ANSWER_PREVIEW_LIMIT = 280


def build_task_card(
    question_text: str,
    status: str = "draft",
    results: list[dict[str, Any]] | None = None,
) -> list[dict]:
    status_label = STATUS_LABELS.get(status, status)

    blocks: list[dict] = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Question:*\n{question_text}",
            },
        },
    ]

    if status == "pending_confirm" and results:
        blocks.append({"type": "divider"})
        blocks.extend(_result_blocks(results[0]))

    if status == "human_working":
        blocks.append(
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": ":mag: No existing answer found — a teammate will follow up.",
                    }
                ],
            }
        )

    blocks.append(
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Status: *{status_label}*",
                }
            ],
        }
    )

    return blocks


def _result_blocks(result: dict[str, Any]) -> list[dict]:
    answer = result.get("answer", "")
    if len(answer) > _ANSWER_PREVIEW_LIMIT:
        answer = answer[:_ANSWER_PREVIEW_LIMIT].rstrip() + "…"

    confidence = result.get("confidence", 0)
    verified = result.get("verified", False)
    confidence_text = f"{int(confidence * 100)}% confidence"
    if verified:
        confidence_text += " · :white_check_mark: Verified"

    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Suggested answer:*\n{answer}",
            },
        },
        {
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": confidence_text}],
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Confirm ✓"},
                    "style": "primary",
                    "action_id": "vault_confirm",
                    "value": result.get("entry_id", ""),
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Not Helpful"},
                    "action_id": "vault_not_helpful",
                    "value": result.get("entry_id", ""),
                },
            ],
        },
    ]
