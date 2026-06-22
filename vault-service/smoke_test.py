"""
vault-service smoke test — run from vault-service/ directory:

    cd vault-service
    pip install -e . python-dotenv
    python smoke_test.py

Exits 0 on success, 1 on any failure.
"""

import os
import sys
import uuid
from dotenv import load_dotenv

load_dotenv()

# ── 1. import after env is loaded ─────────────────────────────────────────────
try:
    from knowledge_vault import search_vault, upsert_vault_entry, update_status
    from supabase import create_client
    print("[1/5] imports OK")
except Exception as e:
    print(f"[1/5] FAIL — import error: {e}")
    sys.exit(1)

_supabase = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_SERVICE_KEY"],
)

# ── 2. verify tables exist ─────────────────────────────────────────────────────
try:
    _supabase.table("vault_entries").select("id").limit(1).execute()
    _supabase.table("task_cards").select("id").limit(1).execute()
    print("[2/5] Supabase tables reachable OK")
except Exception as e:
    print(f"[2/5] FAIL — table check: {e}")
    sys.exit(1)

# ── 3. insert a test task card (required by upsert_vault_entry) ───────────────
card_id = str(uuid.uuid4())
try:
    _supabase.table("task_cards").insert({
        "id":           card_id,
        "requester_id": "U_SMOKE_TEST",
        "channel_id":   "C_SMOKE_TEST",
        "thread_ts":    "0000000000.000000",
        "question_raw": "smoke test: what is the deploy process?",
        "status":       "draft",
    }).execute()
    print(f"[3/5] task card created  (id={card_id[:8]}…)")
except Exception as e:
    print(f"[3/5] FAIL — task card insert: {e}")
    sys.exit(1)

# ── helper so we can clean up even on failure ──────────────────────────────────
def _cleanup(card_id, entry_id):
    try:
        _supabase.table("task_cards").delete().eq("id", card_id).execute()
        if entry_id:
            _supabase.table("vault_entries").delete().eq("id", entry_id).execute()
    except Exception:
        pass


# ── 4. upsert_vault_entry with signal_1 ───────────────────────────────────────
entry_id = None
try:
    result = upsert_vault_entry(
        task_card_id=card_id,
        question_canonical="what is the deploy process?",
        answer="Push to main, CI runs, Fly.io deploys automatically.",
        owner_id="U_SMOKE_RESOLVER",
        signal="signal_1",
    )
    entry_id = result["entry_id"]
    assert result["status"] == "verified", f"expected verified, got {result['status']}"
    assert result["confidence_score"] == 0.90, f"expected 0.90, got {result['confidence_score']}"
    print(f"[4/5] upsert signal_1 OK  entry_id={entry_id[:8]}… status=verified conf=0.90")
except Exception as e:
    print(f"[4/5] FAIL — upsert_vault_entry: {e}")
    _cleanup(card_id, entry_id)
    sys.exit(1)

# ── 5. search_vault should find the entry we just wrote ───────────────────────
try:
    hit = search_vault("what is the deploy process?")
    assert hit["match_found"], "search returned no match"
    assert hit["entry_id"] == entry_id, f"wrong entry returned: {hit['entry_id']}"
    assert hit["confidence"] >= 0.85, f"similarity too low: {hit['confidence']}"
    print(f"[5/5] search_vault OK  similarity={hit['confidence']:.3f}")
except Exception as e:
    print(f"[5/5] FAIL — search_vault: {e}")
    _cleanup(card_id, entry_id)
    sys.exit(1)

# ── 6. update_status ──────────────────────────────────────────────────────────
try:
    r = update_status(card_id, "human_working")
    assert r["success"] is True
    print("[6/6] update_status OK")
except Exception as e:
    print(f"[6/6] FAIL — update_status: {e}")
    _cleanup(card_id, entry_id)
    sys.exit(1)

# ── cleanup ───────────────────────────────────────────────────────────────────
_cleanup(card_id, entry_id)
print("\nAll checks passed. vault-service is operational.")
