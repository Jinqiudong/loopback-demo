"""
Knowledge Vault — storage and verification layer for LoopBack.

Exposes exactly three functions to mira-app (via vault_client.py):
  search_vault        — semantic search, returns best matching entry
  upsert_vault_entry  — write or update an entry, applies three-signal logic
  update_status       — update a task card's status field

Install in the mira-app environment with:
  pip install -e ../vault-service
"""

import os
import uuid
from datetime import datetime, timezone

import openai
from supabase import create_client

# ── clients (initialised once at import time) ─────────────────────────────────

_supabase = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_SERVICE_KEY"],
)
_openai = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# ── confidence constants (see DESIGN.md § Confidence accumulation) ────────────

_HIGH_MATCH = 0.85   # return answer immediately above this similarity
_LOW_MATCH  = 0.70   # below this → treat as no match

_INITIAL_SCORES = {
    "signal_1":           0.90,  # clear confirmation from requester
    "signal_2_ambiguous": 0.55,  # requester replied but wasn't clear (weak positive)
    "signal_2_silence":   0.30,  # two rounds of silence (zero information)
    "signal_3":           0.40,  # denial + new answer (reset after escalation)
}
_USAGE_INCREMENT      = 0.05   # each independent hit without denial raises confidence
_AUTO_VERIFY_THRESHOLD = 0.85  # unconfirmed flips to verified automatically at this score

VALID_STATUSES = frozenset({
    "draft", "ai_searching", "human_working",
    "pending_confirm", "verified", "unconfirmed", "escalate",
})

# ── internal helpers ──────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _embed(text: str) -> list[float]:
    """1536-dim embedding via OpenAI text-embedding-3-small."""
    response = _openai.embeddings.create(input=text, model="text-embedding-3-small")
    return response.data[0].embedding


def _initial_score(signal: str, ambiguous: bool = False) -> float:
    if signal == "signal_1":
        return _INITIAL_SCORES["signal_1"]
    if signal == "signal_2":
        return _INITIAL_SCORES["signal_2_ambiguous" if ambiguous else "signal_2_silence"]
    if signal == "signal_3":
        return _INITIAL_SCORES["signal_3"]
    return 0.0


# ── public API ────────────────────────────────────────────────────────────────

def search_vault(query_text: str) -> dict:
    """
    Semantic search against vault_entries.

    Confidence thresholds (caller's responsibility to act on, per DESIGN.md):
      > 0.85   return answer immediately
      0.7–0.85 ask a clarifying question before surfacing the answer
      < 0.7    treat as no match, fall through to Slack history search

    Each match increments usage_count and raises confidence by _USAGE_INCREMENT.
    If confidence crosses _AUTO_VERIFY_THRESHOLD, status flips to 'verified'
    automatically — no single person needed to confirm.
    """
    embedding = _embed(query_text)

    result = _supabase.rpc(
        "match_vault_entries",
        {"query_embedding": embedding, "match_count": 1},
    ).execute()

    if not result.data:
        return _no_match()

    top = result.data[0]
    similarity = float(top.get("similarity", 0.0))

    if similarity < _LOW_MATCH:
        return _no_match()

    # Passive confidence accumulation: this user found the answer useful (no denial yet).
    new_score = min(float(top["confidence_score"]) + _USAGE_INCREMENT, 1.0)
    patch: dict = {"usage_count": top["usage_count"] + 1, "confidence_score": new_score}
    if new_score >= _AUTO_VERIFY_THRESHOLD and top["status"] == "unconfirmed":
        patch["status"] = "verified"
        patch["last_confirmed_at"] = _now()

    _supabase.table("vault_entries").update(patch).eq("id", top["id"]).execute()

    return {
        "match_found": True,
        "entry_id": top["id"],
        "answer": top["current_answer"],
        "owner_id": top["owner_id"],
        "confidence": similarity,
        "last_confirmed_at": top.get("last_confirmed_at"),
    }


def _no_match() -> dict:
    return {
        "match_found": False,
        "entry_id": None,
        "answer": None,
        "owner_id": None,
        "confidence": 0.0,
        "last_confirmed_at": None,
    }


def upsert_vault_entry(
    task_card_id: str,
    question_canonical: str,
    answer: str,
    owner_id: str,
    signal: str,              # 'signal_1' | 'signal_2' | 'signal_3'
    ambiguous: bool = False,  # signal_2 only: True = ambiguous reply, False = silence
) -> dict:
    """
    Write or update a Knowledge Vault entry based on a confirmation signal.

    signal_1 → status: verified (requester confirmed it worked)
    signal_2 → status: unconfirmed (silence or ambiguous — stored for future accumulation)
    signal_3 → push current answer to version_history, accept new answer as unconfirmed,
               set task card to 'escalate'

    Old answers are never silently deleted — signal_3 pushes them to version_history.

    Returns: { entry_id, status, confidence_score }
    """
    card = (
        _supabase.table("task_cards")
        .select("vault_entry_id")
        .eq("id", task_card_id)
        .maybe_single()
        .execute()
    )
    existing_entry_id = (card.data or {}).get("vault_entry_id")

    if signal == "signal_3" and existing_entry_id:
        return _apply_signal_3(existing_entry_id, answer, owner_id, task_card_id)

    score = _initial_score(signal, ambiguous=ambiguous)
    status = "verified" if signal == "signal_1" else "unconfirmed"
    now = _now()

    if existing_entry_id:
        patch = {
            "current_answer": answer,
            "owner_id": owner_id,
            "status": status,
            "confidence_score": score,
            "updated_at": now,
        }
        if status == "verified":
            patch["last_confirmed_at"] = now
        _supabase.table("vault_entries").update(patch).eq("id", existing_entry_id).execute()
        _supabase.table("task_cards").update({"confidence_signal": signal}).eq("id", task_card_id).execute()
        return {"entry_id": existing_entry_id, "status": status, "confidence_score": score}

    # New entry — generate embedding for canonical question text
    embedding = _embed(question_canonical)
    entry_id = str(uuid.uuid4())

    _supabase.table("vault_entries").insert({
        "id": entry_id,
        "question_canonical": question_canonical,
        "embedding": embedding,
        "current_answer": answer,
        "owner_id": owner_id,
        "status": status,
        "confidence_score": score,
        "usage_count": 0,
        "version_history": [],
        "last_confirmed_at": now if status == "verified" else None,
        "created_at": now,
        "updated_at": now,
    }).execute()

    _supabase.table("task_cards").update({
        "vault_entry_id": entry_id,
        "confidence_signal": signal,
    }).eq("id", task_card_id).execute()

    return {"entry_id": entry_id, "status": status, "confidence_score": score}


def _apply_signal_3(entry_id: str, new_answer: str, owner_id: str, task_card_id: str) -> dict:
    """Push current answer to version_history; accept new answer as unconfirmed."""
    existing = (
        _supabase.table("vault_entries")
        .select("*")
        .eq("id", entry_id)
        .single()
        .execute()
        .data
    )
    now = _now()

    archive = {
        "answer": existing["current_answer"],
        "valid_from": existing.get("created_at"),
        "valid_until": now,
        "changed_by": owner_id,
        "reason": "denied_by_requester",
    }
    history = list(existing.get("version_history") or [])
    history.append(archive)
    score = _INITIAL_SCORES["signal_3"]

    _supabase.table("vault_entries").update({
        "current_answer": new_answer,
        "owner_id": owner_id,
        "status": "unconfirmed",
        "confidence_score": score,
        "version_history": history,
        "updated_at": now,
    }).eq("id", entry_id).execute()

    _supabase.table("task_cards").update({
        "status": "escalate",
        "confidence_signal": "signal_3",
        "updated_at": now,
    }).eq("id", task_card_id).execute()

    return {"entry_id": entry_id, "status": "unconfirmed", "confidence_score": score}


def update_status(task_card_id: str, new_status: str) -> dict:
    """
    Update a task card's status field.

    Returns: { success: bool, updated_at: str }
    """
    if new_status not in VALID_STATUSES:
        raise ValueError(f"Invalid status {new_status!r}. Valid: {sorted(VALID_STATUSES)}")

    now = _now()
    _supabase.table("task_cards").update({
        "status": new_status,
        "updated_at": now,
    }).eq("id", task_card_id).execute()

    return {"success": True, "updated_at": now}


def create_task_card(
    requester_id: str,
    channel_id: str,
    thread_ts: str,
    question_raw: str,
    question_intent: str = None,
) -> str:
    """Insert a new task card row and return its UUID."""
    card_id = str(uuid.uuid4())
    now = _now()
    _supabase.table("task_cards").insert({
        "id": card_id,
        "requester_id": requester_id,
        "channel_id": channel_id,
        "thread_ts": thread_ts,
        "question_raw": question_raw,
        "question_intent": question_intent,
        "status": "draft",
        "created_at": now,
        "updated_at": now,
    }).execute()
    return card_id


def list_vault_entries(limit: int = 20) -> list:
    """
    Fetch vault entries for the Dashboard, ordered by most recently updated.
    Returns a flat list of dicts — schema matches what home_view.py expects.
    Dashboard will expand this (filtering, pagination) in a later sprint.
    """
    rows = (
        _supabase.table("vault_entries")
        .select("id, question_canonical, current_answer, owner_id, status, confidence_score, usage_count, last_confirmed_at, updated_at")
        .order("updated_at", desc=True)
        .limit(limit)
        .execute()
        .data
    )
    return [
        {
            "entry_id": r["id"],
            "question_canonical": r["question_canonical"],
            "current_answer": r["current_answer"],
            "owner_id": r["owner_id"],
            "status": r["status"],
            "confidence_score": r["confidence_score"],
            "usage_count": r["usage_count"],
            "last_confirmed_at": r["last_confirmed_at"],
        }
        for r in (rows or [])
    ]


__all__ = ["create_task_card", "search_vault", "upsert_vault_entry", "update_status", "list_vault_entries"]
