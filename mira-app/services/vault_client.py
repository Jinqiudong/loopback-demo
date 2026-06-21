"""
Thin wrapper around the Knowledge Vault Python API (knowledge_vault package).

Set VAULT_STUB=true in .env to run without the real package during local dev.
Stubs return plausible shapes so the rest of the app is exercisable end-to-end.
"""

import os
import uuid
from typing import Any

_STUB = os.environ.get("VAULT_STUB", "").lower() in ("1", "true", "yes")


class VaultClient:
    def create_task_card(
        self,
        requester_id: str,
        channel_id: str,
        thread_ts: str,
        question_raw: str,
        question_intent: str = None,
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
    ) -> dict[str, Any]:
        if _STUB:
            return {"entry_id": f"stub-entry-{uuid.uuid4().hex[:8]}", "status": "verified", "confidence_score": 0.90}
        from knowledge_vault import upsert_vault_entry
        return upsert_vault_entry(task_card_id, question_canonical, answer, owner_id, signal, ambiguous)

    def update_status(self, task_card_id: str, new_status: str) -> dict[str, Any]:
        if _STUB:
            return {"success": True, "updated_at": ""}
        from knowledge_vault import update_status
        return update_status(task_card_id, new_status)


def _stub_search(query: str) -> dict[str, Any]:
    # Returns no match by default → triggers human_working path.
    # To test pending_confirm path, comment the first return and uncomment the second.
    return {
        "match_found": False,
        "entry_id": None,
        "answer": None,
        "owner_id": None,
        "confidence": 0.0,
        "last_confirmed_at": None,
    }
    # return {
    #     "match_found": True,
    #     "entry_id": "stub-001",
    #     "answer": f"[STUB] Placeholder answer for: {query!r}",
    #     "owner_id": "U_STUB_OWNER",
    #     "confidence": 0.91,
    #     "last_confirmed_at": None,
    # }
