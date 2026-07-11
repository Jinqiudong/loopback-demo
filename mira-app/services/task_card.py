"""
Builds the Block Kit representation of a task card.

Design principles:
  - Question is NOT repeated (it's already visible as the user's original message)
  - Status is shown prominently via header block at the top
  - Source thread link shown when answer comes from vault or Slack history
  - Status + timestamp shown clearly at the bottom
"""

import json
import time
from typing import Any, Optional

_ANSWER_PREVIEW_LIMIT = 280

_STATUS_HEADERS = {
    "draft":          ("🔍", "Checking Knowledge Vault..."),
    "ai_searching":   ("🔍", "Searching Knowledge Vault + Slack history + codebase..."),
    "direction_check":("🔎", "Direction Check — does this look right?"),
    "human_working":  ("🆕", "First time this has been asked"),
    "pending_confirm":("💬", "Answer found — does this help?"),
    "verified":       ("✅", "Verified Answer"),
    "unconfirmed":    ("💡", "Suggested Answer — not yet verified"),
    "escalate":       ("↩️", "Answer wasn't helpful — a teammate will try again"),
}


def build_task_card(
    question_text: str,
    status: str = "draft",
    results: Optional[list[dict[str, Any]]] = None,
    thread_ts: Optional[str] = None,
    asker_id: Optional[str] = None,
    vault_hit: bool = False,
    context_summary: Optional[str] = None,
) -> list[dict]:
    emoji, header_text = _STATUS_HEADERS.get(status, ("•", status))
    # Vault hits get a distinct header so the source is immediately clear
    if status == "pending_confirm" and vault_hit:
        emoji, header_text = "⚡", "Answered from Knowledge Vault"
    time_ago = _relative_time(thread_ts)

    blocks: list[dict] = [
        # Status as header — larger, clearly the first thing you see
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"{emoji} {header_text}", "emoji": True},
        },
        {"type": "divider"},
    ]

    if status in ("draft", "ai_searching"):
        pass  # header is enough for transient states

    elif status == "direction_check":
        if context_summary:
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*What Mira found:*\n{context_summary}"},
            })
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn",
                     "text": "Reply *yes* to confirm this direction and loop in a resolver · or clarify what's different"},
        })

    elif status == "human_working":
        if context_summary:
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Mira's investigation findings:*\n{context_summary}"},
            })
        blocks.append({
            "type": "context",
            "elements": [{"type": "mrkdwn",
                          "text": "A teammate will answer directly in this thread — Mira is listening, not relaying"}],
        })

    elif status == "pending_confirm":
        if vault_hit and results:
            blocks.extend(_vault_hit_blocks(results[0], thread_ts, asker_id, question_text))
        elif results:
            blocks.extend(_resolver_answer_blocks(results[0], thread_ts, asker_id, question_text))

    elif status == "verified" and results:
        blocks.extend(_verified_blocks(results[0]))

    elif status == "unconfirmed" and results:
        blocks.extend(_unconfirmed_blocks(results[0]))

    elif status == "escalate":
        blocks.append({
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": "Previous answer preserved in history"}],
        })

    blocks.append({"type": "divider"})
    blocks.append({
        "type": "context",
        "elements": [{"type": "mrkdwn",
                      "text": f"Status: *{emoji} {header_text}*  ·  {_asked_by(asker_id)}  ·  {time_ago}"}],
    })

    return blocks


# ── state-specific block groups ───────────────────────────────────────────────

def _vault_hit_blocks(result: dict[str, Any],
                      thread_ts: Optional[str],
                      asker_id: Optional[str],
                      question_text: str = "") -> list[dict]:
    answer = _truncate(result.get("answer", ""))
    confidence = result.get("confidence", 0)
    usage = result.get("usage_count", 0)
    owner_id = result.get("owner_id") or ""
    source_thread = result.get("source_thread") or ""

    blocks = [
        {
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": "💡 *A similar question was already answered* — see details below"}],
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": answer},
        },
    ]

    meta_parts = [f"*{int(confidence * 100)}% confidence*"]
    if owner_id:
        meta_parts.append(f"answered by <@{owner_id}>")
    if usage > 0:
        meta_parts.append(f"helped {usage} teammate{'s' if usage > 1 else ''}")
    if source_thread:
        meta_parts.append(f"<{source_thread}|View original thread>")

    blocks.append({
        "type": "context",
        "elements": [{"type": "mrkdwn", "text": "  ·  ".join(meta_parts)}],
    })

    value = _button_value(result, answer, thread_ts, asker_id, vault_hit=True, question=question_text)
    blocks.append({
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
    })
    return blocks


def _resolver_answer_blocks(result: dict[str, Any],
                             thread_ts: Optional[str],
                             asker_id: Optional[str],
                             question_text: str = "") -> list[dict]:
    answer = _truncate(result.get("answer", ""))
    source_thread = result.get("permalink") or result.get("source_thread")
    value = _button_value(result, answer, thread_ts, asker_id, vault_hit=False, question=question_text)

    blocks = [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": answer},
        },
    ]

    if source_thread:
        blocks.append({
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": f"📎 <{source_thread}|View source thread>"}],
        })

    blocks.append({
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
    })
    return blocks


def _verified_blocks(result: dict[str, Any]) -> list[dict]:
    answer = _truncate(result.get("answer", ""))
    owner = result.get("owner_id") or ""
    confidence = result.get("confidence", 0)
    usage = result.get("usage_count", 1)
    source_thread = result.get("source_thread") or ""

    blocks = [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": answer},
        },
    ]

    meta_parts = []
    if owner:
        meta_parts.append(f"answered by <@{owner}>")
    if confidence:
        meta_parts.append(f"*{int(confidence * 100)}% confidence*")
    if usage > 1:
        meta_parts.append(f"helped {usage} teammates")
    if source_thread:
        meta_parts.append(f"<{source_thread}|View original thread>")
    if not meta_parts or not source_thread:
        meta_parts.append("next time this is asked, Mira answers instantly")

    blocks.append({
        "type": "context",
        "elements": [{"type": "mrkdwn", "text": "  ·  ".join(meta_parts)}],
    })
    return blocks


def _unconfirmed_blocks(result: dict[str, Any]) -> list[dict]:
    answer = _truncate(result.get("answer", ""))
    source_thread = result.get("source_thread")

    blocks = [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": answer},
        },
    ]

    meta_parts = ["Be the first to confirm this"]
    if source_thread:
        meta_parts.append(f"<{source_thread}|View original thread>")

    blocks.append({
        "type": "context",
        "elements": [{"type": "mrkdwn", "text": "  ·  ".join(meta_parts)}],
    })
    return blocks


# ── helpers ───────────────────────────────────────────────────────────────────

def _asked_by(asker_id: Optional[str]) -> str:
    return f"Asked by <@{asker_id}>" if asker_id else "Asked by teammate"


def _button_value(result: dict[str, Any], answer: str,
                  thread_ts: Optional[str], asker_id: Optional[str],
                  vault_hit: bool = False, question: str = "") -> str:
    return json.dumps({
        "task_card_id": result.get("task_card_id", ""),
        "entry_id": result.get("entry_id", ""),
        "answer": answer,
        "owner_id": result.get("owner_id", ""),
        "thread_ts": thread_ts or "",
        "asker_id": asker_id or "",
        "vault_hit": vault_hit,
        "question": question,
    })


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
