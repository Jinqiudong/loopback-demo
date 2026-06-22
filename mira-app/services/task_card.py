"""
Builds the Block Kit representation of a task card.

Two distinct visual experiences:
  Cold start  → "🆕 First time this has been asked" — human resolver steps in
  Vault hit   → "⚡ Answered from Knowledge Vault"  — instant answer + confirm button

The card mutates in place through every state. No new messages, just one card
that shows the full resolution story as it unfolds.
"""

import json
import time
from typing import Any, Optional

_ANSWER_PREVIEW_LIMIT = 280


def build_task_card(
    question_text: str,
    status: str = "draft",
    results: Optional[list[dict[str, Any]]] = None,
    thread_ts: Optional[str] = None,
    asker_id: Optional[str] = None,
    vault_hit: bool = False,
) -> list[dict]:
    task_id = _task_id(thread_ts)
    time_ago = _relative_time(thread_ts)

    blocks: list[dict] = [
        {
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": f"*{task_id}*"}],
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*{question_text}*"},
        },
        {"type": "divider"},
    ]

    if status == "draft":
        blocks.append(_headline("🔍", "Checking Knowledge Vault..."))

    elif status == "ai_searching":
        blocks.append(_headline("🔍", "Searching Knowledge Vault + Slack history..."))

    elif status == "human_working":
        blocks.append(_headline("🆕", "First time this question has been asked"))
        blocks.append({
            "type": "context",
            "elements": [{"type": "mrkdwn",
                          "text": "A teammate will answer directly in this thread — Mira is listening, not relaying"}],
        })

    elif status == "pending_confirm":
        if vault_hit and results:
            blocks.extend(_vault_hit_blocks(results[0], thread_ts, asker_id))
        elif results:
            blocks.extend(_resolver_answer_blocks(results[0], thread_ts, asker_id))
        else:
            blocks.append(_headline("⏳", "Waiting for your confirmation"))

    elif status == "verified":
        if results:
            blocks.extend(_verified_blocks(results[0]))
        else:
            blocks.append(_headline("✅", "Verified — saved to Knowledge Vault"))
            blocks.append({
                "type": "context",
                "elements": [{"type": "mrkdwn",
                              "text": "Next time anyone asks, Mira answers instantly"}],
            })

    elif status == "unconfirmed":
        if results:
            blocks.extend(_unconfirmed_blocks(results[0]))
        else:
            blocks.append(_headline("💡", "Suggested answer — not yet verified"))

    elif status == "escalate":
        blocks.append(_headline("↩️", "Answer wasn't helpful — a teammate will try again"))
        blocks.append({
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": "Previous answer preserved in history"}],
        })

    blocks.append({"type": "divider"})
    blocks.append({
        "type": "context",
        "elements": [{"type": "mrkdwn",
                      "text": f"Owner: {_owner(status, asker_id)}  ·  {time_ago}"}],
    })

    return blocks


# ── state-specific block groups ───────────────────────────────────────────────

def _vault_hit_blocks(result: dict[str, Any],
                      thread_ts: Optional[str],
                      asker_id: Optional[str]) -> list[dict]:
    answer = _truncate(result.get("answer", ""))
    confidence = result.get("confidence", 0)
    usage = result.get("usage_count", 0)

    meta = f"{int(confidence * 100)}% confidence"
    if usage > 0:
        meta += f"  ·  verified by {usage} teammate{'s' if usage > 1 else ''}"

    value = _button_value(result, answer, thread_ts, asker_id, vault_hit=True)

    return [
        _headline("⚡", "Answered from Knowledge Vault"),
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": answer},
        },
        {
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": meta}],
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "This helped ✓"},
                    "style": "primary",
                    "action_id": "vault_confirm",
                    "value": value,
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Outdated?"},
                    "action_id": "vault_not_helpful",
                    "value": value,
                },
            ],
        },
    ]


def _resolver_answer_blocks(result: dict[str, Any],
                             thread_ts: Optional[str],
                             asker_id: Optional[str]) -> list[dict]:
    answer = _truncate(result.get("answer", ""))
    value = _button_value(result, answer, thread_ts, asker_id, vault_hit=False)

    return [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": answer},
        },
        {
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": "Did this resolve your issue?"}],
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Yes, resolved ✓"},
                    "style": "primary",
                    "action_id": "vault_confirm",
                    "value": value,
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Not quite"},
                    "action_id": "vault_not_helpful",
                    "value": value,
                },
            ],
        },
    ]


def _verified_blocks(result: dict[str, Any]) -> list[dict]:
    answer = _truncate(result.get("answer", ""))
    owner = result.get("owner_id", "")
    usage = result.get("usage_count", 1)

    meta = f"answered by <@{owner}>" if owner else "confirmed"
    if usage > 1:
        meta += f"  ·  helped {usage} teammates"
    meta += "  ·  next time this is asked, Mira answers instantly"

    return [
        _headline("✅", "Verified — saved to Knowledge Vault"),
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": answer},
        },
        {
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": meta}],
        },
    ]


def _unconfirmed_blocks(result: dict[str, Any]) -> list[dict]:
    answer = _truncate(result.get("answer", ""))
    return [
        _headline("💡", "Suggested answer — not yet verified"),
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": answer},
        },
        {
            "type": "context",
            "elements": [{"type": "mrkdwn",
                          "text": "Be the first to confirm this · confidence will rise with each verification"}],
        },
    ]


# ── helpers ───────────────────────────────────────────────────────────────────

def _headline(emoji: str, text: str) -> dict:
    return {
        "type": "section",
        "text": {"type": "mrkdwn", "text": f"{emoji}  *{text}*"},
    }


def _owner(status: str, asker_id: Optional[str]) -> str:
    if status == "pending_confirm":
        return f"<@{asker_id}>" if asker_id else "Requester"
    return {
        "draft": "—",
        "ai_searching": "Mira AI",
        "human_working": "Resolver",
        "verified": "—",
        "unconfirmed": "—",
        "escalate": "Resolver",
    }.get(status, "—")


def _button_value(result: dict[str, Any], answer: str,
                  thread_ts: Optional[str], asker_id: Optional[str],
                  vault_hit: bool = False) -> str:
    return json.dumps({
        "task_card_id": result.get("task_card_id", ""),
        "entry_id": result.get("entry_id", ""),
        "answer": answer,
        "owner_id": result.get("owner_id", ""),
        "thread_ts": thread_ts or "",
        "asker_id": asker_id or "",
        "vault_hit": vault_hit,
    })


def _task_id(thread_ts: Optional[str]) -> str:
    if not thread_ts:
        return "#----"
    return f"#{thread_ts.split('.')[0][-4:]}"


def _relative_time(thread_ts: Optional[str]) -> str:
    if not thread_ts:
        return "just now"
    try:
        elapsed = time.time() - float(thread_ts)
        if elapsed < 60:
            return "just now"
        if elapsed < 3600:
            return f"{int(elapsed / 60)} min ago"
        if elapsed < 86400:
            return f"{int(elapsed / 3600)} hr ago"
        return f"{int(elapsed / 86400)} days ago"
    except (ValueError, TypeError):
        return "just now"


def _truncate(answer: str) -> str:
    if len(answer) > _ANSWER_PREVIEW_LIMIT:
        return answer[:_ANSWER_PREVIEW_LIMIT].rstrip() + "…"
    return answer
