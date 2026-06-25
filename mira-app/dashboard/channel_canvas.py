"""
Channel Insights Canvas — builds and updates a Slack Canvas for a channel.

Triggered by: @Mira insights → posts time period selector in the channel
Updated by:   [This Month] / [This Quarter] / [This Year] button clicks

Three sections in the canvas:
  ✅ Knowledge        — verified task cards
  💡 Answered Pending — unconfirmed task cards
  ❓ Open Questions   — human_working / escalate task cards

Within each section, questions are grouped by semantic topic using cosine
similarity on stored embeddings. The question with the highest confidence
score becomes the topic title (no extra API call needed).
"""

import json
import math
import logging
import os
from datetime import datetime, timezone, date
from typing import Any, Optional

logger = logging.getLogger(__name__)

_CANVAS_IDS_FILE = os.path.join(os.path.dirname(__file__), "canvas_ids.json")


def _load_canvas_ids() -> dict:
    try:
        with open(_CANVAS_IDS_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_canvas_ids(ids: dict) -> None:
    with open(_CANVAS_IDS_FILE, "w") as f:
        json.dump(ids, f)


_channel_canvas_ids: dict[str, str] = _load_canvas_ids()

_CLUSTER_THRESHOLD = 0.75  # cosine similarity to be grouped in the same topic


# ── public API ────────────────────────────────────────────────────────────────

def get_or_create_canvas(client, channel_id: str) -> Optional[str]:
    """Return canvas_id for this channel, creating one if needed."""
    if channel_id in _channel_canvas_ids:
        return _channel_canvas_ids[channel_id]
    try:
        resp = client.conversations_canvases_create(
            channel_id=channel_id,
            title="Channel Insights",
            document_content={
                "type": "markdown",
                "markdown": "# Channel Insights\n\nLoading...",
            },
        )
        canvas_id = resp["canvas_id"]
        _channel_canvas_ids[channel_id] = canvas_id
        _save_canvas_ids(_channel_canvas_ids)
        logger.info("Created canvas %s for channel %s", canvas_id, channel_id)
        return canvas_id
    except Exception:
        logger.warning("Failed to create canvas for %s", channel_id, exc_info=True)
        return None


def update_canvas(client, channel_id: str, cards: list[dict[str, Any]],
                  channel_name: str, period_label: str) -> bool:
    """Rebuild canvas content for the given cards and time period."""
    canvas_id = get_or_create_canvas(client, channel_id)
    if not canvas_id:
        return False

    markdown = _build_markdown(cards, channel_name, period_label)
    try:
        client.canvases_edit(
            canvas_id=canvas_id,
            changes=[{
                "operation": "replace",
                "document_content": {"type": "markdown", "markdown": markdown},
            }],
        )
        return True
    except Exception:
        logger.warning("Failed to update canvas %s", canvas_id, exc_info=True)
        return False


def build_period_selector(channel_id: str) -> list[dict]:
    """Block Kit selector posted in the channel when user types @Mira insights."""
    return [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": "Which time period would you like to see?\nResults will appear in the *Channel Insights* canvas in this channel."},
        },
        {
            "type": "actions",
            "block_id": f"insights_period_{channel_id}",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "This Month"},
                    "action_id": "insights_this_month",
                    "value": channel_id,
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "This Quarter"},
                    "action_id": "insights_this_quarter",
                    "value": channel_id,
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "This Year"},
                    "action_id": "insights_this_year",
                    "value": channel_id,
                },
            ],
        },
    ]


def period_since(period: str) -> str:
    """ISO timestamp for the start of the requested period."""
    today = date.today()
    if period == "month":
        start = date(today.year, today.month, 1)
    elif period == "quarter":
        q_start_month = ((today.month - 1) // 3) * 3 + 1
        start = date(today.year, q_start_month, 1)
    else:  # year
        start = date(today.year, 1, 1)
    return datetime(start.year, start.month, start.day, tzinfo=timezone.utc).isoformat()


def period_label(period: str) -> str:
    today = date.today()
    if period == "month":
        return f"This Month ({today.strftime('%B %Y')})"
    elif period == "quarter":
        q = (today.month - 1) // 3 + 1
        return f"This Quarter (Q{q} {today.year})"
    else:
        return f"This Year ({today.year})"


# ── canvas markdown builder ───────────────────────────────────────────────────

def _build_markdown(cards: list[dict], channel_name: str, label: str) -> str:
    now_str = datetime.now(timezone.utc).strftime("%b %d, %Y %H:%M UTC")

    verified = [c for c in cards if c["status"] == "verified"]
    pending  = [c for c in cards if c["status"] == "unconfirmed"]
    open_q   = [c for c in cards if c["status"] in ("human_working", "escalate")]

    total = len(cards)
    summary = (
        f"**{total} question{'s' if total != 1 else ''}**  ·  "
        f"{len(verified)} verified  ·  "
        f"{len(pending)} pending  ·  "
        f"{len(open_q)} open"
    )

    lines = [
        f"# Channel Insights — #{channel_name}",
        f"📅 {label}  ·  Updated {now_str}",
        "",
        summary,
        "",
        "---",
        "",
    ]

    lines += _section("✅ Knowledge", verified)
    lines += _section("💡 Answered Pending", pending)
    lines += _section("❓ Open Questions", open_q)

    return "\n".join(lines)


def _section(title: str, cards: list[dict]) -> list[str]:
    if not cards:
        return [f"## {title}", "", "_None this period._", "", "---", ""]

    clusters = _cluster_by_topic(cards)
    topic_count = len(clusters)
    lines = [
        f"## {title}  ({topic_count} topic{'s' if topic_count != 1 else ''})",
        "",
    ]

    for cluster in clusters:
        topic_name = _topic_title(cluster)
        q_count = len(cluster)
        lines.append(f"**{topic_name}**  ·  {q_count} question{'s' if q_count != 1 else ''}")
        for card in cluster:
            if card.get("source_thread"):
                lines.append(f"- {card['question']} — [View thread]({card['source_thread']})")
            else:
                lines.append(f"- {card['question']}")
        lines.append("")

    lines += ["---", ""]
    return lines


# ── topic clustering ──────────────────────────────────────────────────────────

def _cluster_by_topic(cards: list[dict]) -> list[list[dict]]:
    """
    Greedy cosine-similarity clustering on stored embeddings.
    Cards without embeddings each get their own single-card cluster.
    """
    clusters: list[list[dict]] = []
    for card in cards:
        emb = card.get("embedding")
        placed = False
        if emb:
            for cluster in clusters:
                rep_emb = cluster[0].get("embedding")
                if rep_emb and _cosine_sim(emb, rep_emb) >= _CLUSTER_THRESHOLD:
                    cluster.append(card)
                    placed = True
                    break
        if not placed:
            clusters.append([card])
    return clusters


def _topic_title(cluster: list[dict]) -> str:
    """Question with the highest confidence score becomes the topic title."""
    best = max(cluster, key=lambda c: c.get("confidence_score", 0.0))
    q = best["question"]
    return q if len(q) <= 60 else q[:57].rstrip() + "..."


def _cosine_sim(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
