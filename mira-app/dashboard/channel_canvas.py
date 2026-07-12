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
    """Return canvas_id for this channel, creating one if needed.

    Lookup order:
    1. In-memory cache (canvas_ids.json on local dev)
    2. Environment variable CANVAS_ID_<CHANNEL_ID> — set this in Railway Variables
       when the canvas already exists and can't be recreated (free plan limit)
    3. Create a new canvas via Slack API
    """
    if channel_id in _channel_canvas_ids:
        return _channel_canvas_ids[channel_id]

    # Railway / persistent env-var fallback — avoids filesystem dependency
    env_key = f"CANVAS_ID_{channel_id}"
    env_canvas_id = os.environ.get(env_key)
    if env_canvas_id:
        _channel_canvas_ids[channel_id] = env_canvas_id
        logger.info("Using canvas %s from env var %s", env_canvas_id, env_key)
        return env_canvas_id

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
    except Exception as e:
        logger.warning("Failed to create canvas for %s: %s", channel_id, e)
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


def build_period_selector(channel_id: str, updated_label: Optional[str] = None) -> list[dict]:
    """Block Kit selector posted in the channel when user types @Mira insights."""
    blocks: list[dict] = [
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
    if updated_label:
        blocks.append({
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": f"✅ Canvas updated — {updated_label}"}],
        })
    return blocks


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

_STATUS_PROGRESS = {
    "pending_confirm": "💬 Suggested answer → ⏳ Awaiting confirmation",
    "unconfirmed":     "💬 Suggested answer → ⏳ Awaiting confirmation",
    "human_working":   "🔍 Investigated → ✓ Direction confirmed → ⏳ Resolver notified",
    "escalate":        "🔍 Investigated → ✓ Confirmed → 👤 Escalated — needs follow-up",
}

_CATEGORY_EMOJI = {
    "documentation": "📖",
    "code":          "🔧",
    "ux":            "🎨",
    "process":       "📋",
    "product":       "🚀",
}


def _build_markdown(cards: list[dict], channel_name: str, label: str) -> str:
    from pm.proposal_engine import generate_opportunities

    now_str = datetime.now(timezone.utc).strftime("%b %d, %Y %H:%M UTC")

    verified   = [c for c in cards if c["status"] == "verified"]
    unanswered = [c for c in cards if c["status"] in ("unconfirmed", "pending_confirm")]
    open_q     = [c for c in cards if c["status"] in ("human_working", "escalate")]
    total      = len(cards)

    lines = [
        f"# Channel Insights — #{channel_name}",
        f"📅 {label}  ·  Updated {now_str}",
        "",
        "---",
        "",
    ]

    # ── Section 1: Impact ────────────────────────────────────────────────────
    lines += ["## 📊 Impact", ""]
    lines.append(f"**{total} question{'s' if total != 1 else ''}** received this period.")
    lines.append("")

    if verified:
        lines.append(f"→ **{len(verified)} resolved** — answers ready to reuse, no resolver needed next time")
    if unanswered:
        lines.append(f"→ **{len(unanswered)} suggested** — has a candidate answer, awaiting confirmation")
    if open_q:
        lines.append(f"→ **{len(open_q)} open** — a teammate is being looped in")

    lines.append("")
    if verified:
        lines.append(
            f"Mira can now auto-serve **{len(verified)} topic{'s' if len(verified) != 1 else ''}** instantly. "
            f"Every verified answer means one less interruption next time around."
        )
    lines += ["", "---", ""]

    # ── Section 2: Knowledge Vault ───────────────────────────────────────────
    lines += ["## 🧠 Knowledge Vault", ""]

    if verified:
        clusters = _cluster_by_topic(verified)
        for cluster in clusters:
            best = max(cluster, key=lambda c: c.get("confidence_score", 0))
            conf = int(best.get("confidence_score", 0) * 100)
            owner = best.get("owner_id", "")
            thread = best.get("source_thread", "")

            # Compact topic title (≤70 chars)
            topic = _topic_title(cluster)
            owner_str = f" · answered by <@{owner}>" if owner else ""
            thread_str = f" · [View original thread ↗]({thread})" if thread else ""

            lines.append(f"**{topic}**")
            lines.append(f"✅ {conf}% confidence{owner_str}{thread_str}")
            lines.append("")

            # Indent similar questions that were answered by this same entry
            if len(cluster) > 1:
                for card in cluster:
                    q = card["question"]
                    q_short = q if len(q) <= 80 else q[:77] + "..."
                    t = card.get("source_thread", "")
                    t_str = f" [↗]({t})" if t else ""
                    lines.append(f"  - {q_short}{t_str}")
                lines.append("")
            else:
                q = best["question"]
                q_short = q if len(q) <= 80 else q[:77] + "..."
                t = best.get("source_thread", "")
                t_str = f" [↗]({t})" if t else ""
                lines.append(f"  - {q_short}{t_str}")
                lines.append("")
    else:
        lines += ["_No verified knowledge yet this period._", ""]

    if unanswered:
        lines += [
            "### 🔔 Unanswered — needs confirmation",
            "_Has a suggested answer but not yet confirmed. Tag the resolver to follow up._",
            "",
        ]
        for card in unanswered:
            q = card["question"]
            q_short = q if len(q) <= 80 else q[:77] + "..."
            t = card.get("source_thread", "")
            t_str = f" [View thread ↗]({t})" if t else ""
            lines.append(f"- {q_short}{t_str}")
        lines.append("")

    if open_q:
        lines += ["### ❓ Open — no answer yet", ""]
        for card in open_q:
            q = card["question"]
            q_short = q if len(q) <= 80 else q[:77] + "..."
            t = card.get("source_thread", "")
            t_str = f"  [View thread ↗]({t})" if t else ""
            status_label = _STATUS_PROGRESS.get(card["status"], f"Status: {card['status']}")
            lines.append(f"**{q_short}**")
            lines.append(f"{status_label}{t_str}")
            lines.append("")

    lines += ["---", ""]

    # ── Section 3: Enhancement Opportunities ─────────────────────────────────
    opportunities = generate_opportunities(cards, label)
    lines += _opportunity_section(opportunities, label)

    return "\n".join(lines)


def _opportunity_section(opportunities: list[dict], label: str) -> list[str]:
    if not opportunities:
        return [
            "## 🌱 Enhancement Opportunities",
            "",
            "_Not enough data yet to surface patterns. Come back after more questions are resolved._",
            "",
        ]
    lines = [
        "## 🌱 Enhancement Opportunities",
        f"*AI-generated from resolved questions · {label}*",
        "",
    ]
    for i, opp in enumerate(opportunities, 1):
        title = opp.get("title", "Untitled pattern")
        count = opp.get("related_count", 0)
        category = opp.get("category", "")
        emoji = _CATEGORY_EMOJI.get(category, "💡")
        bullets = opp.get("bullets", [])
        lines.append(f"**{i}. {emoji} {title}**  ·  {count} related question{'s' if count != 1 else ''}")
        for b in bullets:
            lines.append(f"- {b}")
        lines.append("")
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
