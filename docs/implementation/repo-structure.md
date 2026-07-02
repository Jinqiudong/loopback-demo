# LoopBack — Repo Structure Reference

This document is the single source of truth for what lives where and who owns what.
Both team members should read this before touching any file they haven't worked in before.

**Owner key:**
- 🔵 Jinqiu — mira-app (conversational layer)
- 🟢 Jie — vault-service (storage + mechanism layer)
- 🤝 Both — shared files, docs, integration points

---

## Full Tree

```
loopback-demo/
│
├── README.md                          🤝  Project overview (for evaluators/GitHub)
├── ARCHITECTURE.md                    🤝  System architecture + component diagram
├── CLAUDE.md                          🤝  AI assistant instructions (auto-loaded by Claude Code)
├── .gitignore                         🤝
│
├── mira-app/                          🔵  JINQIU'S SIDE — do not edit without checking in
│   ├── app.py                         🔵  Entry point — starts the Slack Bolt app (Socket Mode)
│   ├── config.py                      🔵  Loads + validates env vars (fail-fast on startup)
│   ├── requirements.txt               🔵  slack-bolt, anthropic, python-dotenv
│   ├── .env.example                   🔵  Template — copy to .env, fill in real keys
│   ├── .gitignore                     🔵  Covers .env, venv, __pycache__
│   │
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── mention_handler.py         🔵  @Mira listener — full 3-tier search orchestration
│   │   │                                  Tier 1: Vault → Tier 2: Slack+GitHub+DataDict
│   │   │                                  → direction_check → Tier 3: human escalation
│   │   │                                  @Mira analyze → Enhancement Proposal engine
│   │   ├── action_handler.py          🔵  Button actions: confirm / not helpful
│   │   ├── resolution_handler.py      🔵  Detects resolver replies in thread → pending_confirm
│   │   └── direction_handler.py       🔵  Pre-escalation: detects "yes" → escalate with context
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── intent.py                  🔵  Claude QUESTION/NOISE classification
│   │   ├── task_card.py               🔵  Block Kit builder — 8 states incl. direction_check
│   │   ├── vault_client.py            🔵🟢 THE CONTRACT BOUNDARY ← see section below
│   │   ├── slack_search.py            🔵  Real-Time Search API (needs SLACK_USER_TOKEN)
│   │   └── mcp_github.py              🔵  GitHub MCP — reads loopback-analytics repo
│   │
│   ├── pm/
│   │   └── proposal_engine.py         🔵  Claude-powered Enhancement Proposal from Vault patterns
│   │
│   └── dashboard/
│       ├── home_view.py               🔵  App Home Dashboard (Block Kit, legacy)
│       └── channel_canvas.py          🟢  Channel Insights Canvas — @Mira insights
│                                          Three sections: Knowledge / Pending / Open
│                                          Semantic clustering, time period filter
│
├── vault-service/                     🟢  JIE'S SIDE — do not edit without checking in
│   ├── requirements.txt               🟢
│   ├── schema.sql                     🟢  CREATE TABLE for task_cards + vault_entries
│   ├── embeddings.py                  🟢  OpenAI text-embedding-3-small wrapper
│   ├── confidence.py                  🟢  Confidence scoring + accumulation logic
│   │
│   └── api/                           🟢🔵 THE CONTRACT BOUNDARY ← see section below
│       ├── search_vault.py            🟢  Semantic search against vault_entries
│       ├── upsert_vault_entry.py      🟢  Writes/updates an entry, applies signal logic
│       └── update_status.py           🟢  Status field update on task_cards
│
└── docs/
    ├── implementation/                🤝
    │   ├── DESIGN.md                  🤝  Core mechanism, Resolution Cycle, data model,
    │   │                                  API contract shapes, naming conventions.
    │   │                                  READ THIS before touching any resolution logic.
    │   ├── implementation-plan.md     🤝  Week-by-week task breakdown, ownership, deadlines
    │   └── repo-structure.md          🤝  This file
    │
    └── submission/                    🤝  Devpost submission materials
        ├── project-story.md           🤝  Living draft — update when milestones are hit
        ├── demo-script.md             🤝  Script for the 3-min demo video (Week 4)
        └── diagrams/
            ├── Diagram 1.png          🤝  [label once confirmed with team]
            ├── Diagram 2.png          🤝  [label once confirmed with team]
            └── Diagram 3.png          🤝  [label once confirmed with team]
```

---

## The Contract Boundary

The only coupling point between the two sides. **Neither person touches the other side of this line without a conversation first.**

```
mira-app/services/vault_client.py   ←→   vault-service/api/
         🔵 Jinqiu owns this                  🟢 Jie owns this
```

### Four functions, locked 6/22

```python
# 1. Create a task card DB record when question comes in
create_task_card(requester_id, channel_id, thread_ts, question_raw, question_intent) -> str

# 2. Does a verified or suggested answer already exist?
search_vault(query_text: str) -> dict   # returns match_found, entry_id, answer, confidence

# 3. Write a resolved answer into the Vault (call on signal_1/2/3 only)
upsert_vault_entry(task_card_id, question_canonical, answer, owner_id, signal, ambiguous) -> dict

# 4. Update a task card's lifecycle status
update_status(task_card_id: str, new_status: str) -> dict
```

Full input/output shapes are in `docs/implementation/DESIGN.md` § API contract.

**Rule:** if you need to change a function signature, that's a two-person conversation —
not a unilateral edit on either side.

---

## Running Mira Locally (Jinqiu's side)

```bash
cd mira-app
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
pip install -e ../vault-service   # once Supabase is configured
cp .env.example .env
# Required: SLACK_BOT_TOKEN, SLACK_APP_TOKEN, ANTHROPIC_API_KEY
# Vault:    SUPABASE_URL, SUPABASE_SERVICE_KEY, OPENAI_API_KEY → then VAULT_STUB=false
# Search:   SLACK_USER_TOKEN (xoxp-...)
# GitHub:   GITHUB_TOKEN, GITHUB_ANALYTICS_REPO=Jinqiudong/loopback-analytics
python app.py
```

---

## Status Enum (shared — must match exactly on both sides)

Both `mira-app` and `vault-service` use these status strings. A typo here breaks the handoff.

| Value | Meaning | Who sets it |
|-------|---------|-------------|
| `draft` | Just created, no Vault check yet | Jinqiu |
| `ai_searching` | Mira is querying the Vault | Jinqiu |
| `human_working` | No answer found, waiting on a resolver | Jinqiu |
| `pending_confirm` | Answer suggested, waiting on requester | Jinqiu |
| `verified` | Confirmed correct | Jie (via upsert signal_1) |
| `unconfirmed` | Saved but not yet confirmed | Jie (via upsert signal_2) |
| `escalate` | Answer was wrong, back to resolver | Jie (via upsert signal_3) |

---

## Files Neither Person Should Edit Alone

| File | Why |
|------|-----|
| `docs/implementation/DESIGN.md` § API contract | Changing this changes what both sides build against |
| `vault-service/api/*.py` function signatures | Jinqiu's `vault_client.py` depends on these exactly |
| `mira-app/services/vault_client.py` method signatures | Jie's tests depend on these |
| Status enum values (table above) | Used in both codebases; a rename breaks the integration |
