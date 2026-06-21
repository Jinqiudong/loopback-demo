"""
Builds the Block Kit representation of a task card.
Every status in the Resolution Cycle has a distinct visual treatment —
the card updates in place as it moves through states, not as separate messages.
"""

import json
from typing import Any, Optional

STATUS_LABELS = {
    "draft": "Draft",
    "ai_searching": "Searching",
    "human_working": "Waiting on a teammate",
    "pending_confirm": "Waiting on you to confirm",
    "verified": "Verified ✓",
    "unconfirmed": "Suggested, not yet verified",
    "escalate": "Escalated",
}

_ANSWER_PREVIEW_LIMIT = 280


def build_task_card(
    question_text: str,
    status: str = "draft",
    results: Optional[list[dict[str, Any]]] = None,
) -> list[dict]:
    status_label = STATUS_LABELS.get(status, status)

    blocks: list[dict] = [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Question:*\n{question_text}"},
        },
    ]

    if status == "ai_searching":
        blocks.append({
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": ":mag: Checking the Knowledge Vault and Slack history..."}],
        })

    elif status == "pending_confirm" and results:
        blocks.append({"type": "divider"})
        blocks.extend(_pending_confirm_blocks(results[0]))

    elif status == "verified" and results:
        blocks.append({"type": "divider"})
        blocks.extend(_verified_blocks(results[0]))

    elif status == "unconfirmed" and results:
        blocks.append({"type": "divider"})
        blocks.extend(_unconfirmed_blocks(results[0]))

    elif status == "human_working":
        blocks.append({
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": ":speech_balloon: No existing answer found — a teammate will follow up directly in this thread."}],
        })

    elif status == "escalate":
        blocks.append({
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": ":arrows_counterclockwise: Answer marked as not helpful — a teammate will take another look."}],
        })

    blocks.append({
        "type": "context",
        "elements": [{"type": "mrkdwn", "text": f"Status: *{status_label}*"}],
    })

    return blocks


def _truncate(answer: str) -> str:
    if len(answer) > _ANSWER_PREVIEW_LIMIT:
        return answer[:_ANSWER_PREVIEW_LIMIT].rstrip() + "…"
    return answer


def _button_value(result: dict[str, Any], answer: str) -> str:
    # Encode all fields action handlers need to call upsert_entry without a second Vault lookup.
    return json.dumps({
        "task_card_id": result.get("task_card_id", ""),
        "entry_id": result.get("entry_id", ""),
        "answer": answer,
        "owner_id": result.get("owner_id", ""),
    })


def _pending_confirm_blocks(result: dict[str, Any]) -> list[dict]:
    answer = _truncate(result.get("answer", ""))
    confidence = result.get("confidence", 0)
    confidence_text = f"{int(confidence * 100)}% confidence"
    if result.get("verified"):
        confidence_text += " · :white_check_mark: previously verified"

    value = _button_value(result, answer)

    return [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Suggested answer:*\n{answer}"},
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
                    "value": value,
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Not Helpful"},
                    "action_id": "vault_not_helpful",
                    "value": value,
                },
            ],
        },
    ]


def _verified_blocks(result: dict[str, Any]) -> list[dict]:
    answer = _truncate(result.get("answer", ""))
    owner = result.get("owner_id", "")
    meta = f"{int(result.get('confidence', 0) * 100)}% confidence"
    if owner:
        meta += f" · answered by <@{owner}>"

    return [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f":white_check_mark: *Verified answer:*\n{answer}"},
        },
        {
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": meta}],
        },
    ]


def _unconfirmed_blocks(result: dict[str, Any]) -> list[dict]:
    answer = _truncate(result.get("answer", ""))

    return [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Suggested answer:*\n{answer}"},
        },
        {
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": ":grey_question: Suggested, not yet verified — be the first to confirm it."}],
        },
    ]
