"""
Thin wrapper around the Knowledge Vault Python API (teammate's package).

Set VAULT_STUB=true in .env to run without the real package during local dev.
Stubs return plausible shapes so the rest of the app is exercisable end-to-end.
"""

import os
import uuid
from typing import Any

_STUB = os.environ.get("VAULT_STUB", "").lower() in ("1", "true", "yes")


class VaultClient:
    def search(self, query: str) -> list[dict[str, Any]]:
        if _STUB:
            return _stub_search(query)
        from knowledge_vault import search_vault
        return search_vault(query)

    def upsert_entry(self, question: str, channel: str, thread_ts: str) -> str:
        if _STUB:
            return _stub_upsert()
        from knowledge_vault import upsert_vault_entry
        return upsert_vault_entry(question, channel, thread_ts)

    def update_status(self, entry_id: str, status: str) -> None:
        if _STUB:
            return
        from knowledge_vault import update_status
        update_status(entry_id, status)


def _stub_search(query: str) -> list[dict[str, Any]]:
    # Non-empty so the pending_confirm path is reachable during local testing.
    return [
        {
            "entry_id": "stub-001",
            "question": "How do I request PTO?",
            "answer": "Submit a request via Workday at least 3 business days in advance.",
            "confidence": 0.91,
            "verified": True,
        }
    ]


def _stub_upsert() -> str:
    return f"stub-{uuid.uuid4().hex[:8]}"
