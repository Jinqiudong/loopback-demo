"""
Thin wrapper around the Knowledge Vault Python API (knowledge_vault package).

Set VAULT_STUB=true in .env to run without the real package during local dev.
Stubs return plausible shapes so the rest of the app is exercisable end-to-end.
"""

import os
import uuid
from typing import Any, Optional

_STUB = os.environ.get("VAULT_STUB", "").lower() in ("1", "true", "yes")


class VaultClient:
    def create_task_card(
        self,
        requester_id: str,
        channel_id: str,
        thread_ts: str,
        question_raw: str,
        question_intent: Optional[str] = None,
    ) -> str:
        if _STUB:
            return f"stub-card-{uuid.uuid4().hex[:8]}"
        from knowledge_vault import create_task_card
        return create_task_card(requester_id, channel_id, thread_ts, question_raw, question_intent)

    def search(self, query: str) -> dict[str, Any]:
        if _STUB:
            return _stub_search(query)
        from knowledge_vault import search_vault
        return search_vault(query)

    def upsert_entry(
        self,
        task_card_id: str,
        question_canonical: str,
        answer: str,
        owner_id: str,
        signal: str,
        ambiguous: bool = False,
        source_thread: Optional[str] = None,
    ) -> dict[str, Any]:
        if _STUB:
            return {"entry_id": f"stub-entry-{uuid.uuid4().hex[:8]}", "status": "verified", "confidence_score": 0.90}
        from knowledge_vault import upsert_vault_entry
        return upsert_vault_entry(task_card_id, question_canonical, answer, owner_id, signal, ambiguous, source_thread)

    def update_status(self, task_card_id: str, new_status: str, vault_entry_id: str = None) -> dict[str, Any]:
        if _STUB:
            return {"success": True, "updated_at": ""}
        from knowledge_vault import update_status
        return update_status(task_card_id, new_status, vault_entry_id=vault_entry_id)

    def list_entries(self, limit: int = 20) -> list[dict[str, Any]]:
        if _STUB:
            return _stub_entries()
        from knowledge_vault import list_vault_entries
        return list_vault_entries(limit=limit)

    def get_channel_insights(self, channel_id: str, since: str) -> list[dict[str, Any]]:
        if _STUB:
            return _stub_channel_cards(channel_id)
        from knowledge_vault import get_channel_task_cards
        return get_channel_task_cards(channel_id, since)


def _stub_entries() -> list[dict[str, Any]]:
    return [
        {
            "entry_id": "stub-001",
            "question_canonical": "How do I request PTO?",
            "current_answer": "Submit your request via Workday at least 3 business days in advance. Your manager will be notified automatically.",
            "status": "verified",
            "confidence_score": 0.94,
            "usage_count": 5,
            "owner_id": "U_STUB_USER_1",
            "last_confirmed_at": "2026-06-20T10:30:00Z",
        },
        {
            "entry_id": "stub-002",
            "question_canonical": "How do I log overtime hours?",
            "current_answer": "Log overtime in Workday under Time & Absence. Submit by end of the pay period.",
            "status": "unconfirmed",
            "confidence_score": 0.61,
            "usage_count": 1,
            "owner_id": "U_STUB_USER_2",
            "last_confirmed_at": None,
        },
        {
            "entry_id": "stub-003",
            "question_canonical": "Where do I find the Q4 OKRs?",
            "current_answer": "Q4 OKRs are in Notion under Company > Strategy > 2026 OKRs.",
            "status": "verified",
            "confidence_score": 0.88,
            "usage_count": 3,
            "owner_id": "U_STUB_USER_1",
            "last_confirmed_at": "2026-06-19T14:00:00Z",
        },
    ]


def _stub_channel_cards(channel_id: str) -> list[dict[str, Any]]:
    return [
        {"task_card_id": "tc-001", "question": "Why did approval rate spike last week?",
         "status": "verified", "source_thread": None, "confidence_score": 0.90, "embedding": None},
        {"task_card_id": "tc-002", "question": "da_approval_metrics underreporting since March",
         "status": "verified", "source_thread": None, "confidence_score": 0.85, "embedding": None},
        {"task_card_id": "tc-003", "question": "How do I backfill NULL product_type values?",
         "status": "unconfirmed", "source_thread": None, "confidence_score": 0.55, "embedding": None},
        {"task_card_id": "tc-004", "question": "What counts as a completed approval?",
         "status": "human_working", "source_thread": None, "confidence_score": 0.0, "embedding": None},
    ]


def _stub_search(query: str) -> dict[str, Any]:
    return {
        "match_found": False,
        "entry_id": None,
        "answer": None,
        "owner_id": None,
        "confidence": 0.0,
        "last_confirmed_at": None,
    }
