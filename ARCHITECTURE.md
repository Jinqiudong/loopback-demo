# LoopBack — Architecture

---

## What LoopBack is

**One-liner:** Every problem your organization solves should only ever need to be solved once.

LoopBack is a Slack-native system with three layers of value:

- **Mira** — the AI colleague you `@` in Slack. She searches three knowledge tiers in parallel,
  escalates to humans only when genuinely needed, and never relays between requester and resolver.
- **Knowledge Vault** — the growing, verified memory Mira builds from every resolved conversation.
- **Product Intelligence** — Mira's PM identity: she analyzes Vault patterns to generate
  Enhancement Proposals, turning repeated support questions into product backlog items.

---

## The problem

Every conversation in Slack disappears the moment the thread goes quiet. The person asking
just wants to be unblocked. The person answering may have answered this before. And nobody
connects the dots: the same question asked seven times signals a product gap — but that signal
is invisible unless something is listening. LoopBack listens.

---

## Core mechanism

```
User @ Mira with a question
    │
    ▼
Intent classification (Claude) — question or noise?
    │ QUESTION
    ▼
Tier 1: Knowledge Vault (fastest, cheapest — always first)
    ├─ confidence > 0.85  → return verified answer instantly
    ├─ confidence 0.7–0.85 → clarifying question first
    └─ no match → Tier 2
            │
            ▼
Tier 2: Parallel search (three sources simultaneously)
    ├─ Slack history      (Real-Time Search API)
    ├─ GitHub MCP         (code, SQL, schema files)
    └─ Data Dictionary MCP (field definitions, business terms)
            │
            ├─ candidate(s) found → surface best result + clarify if needed
            └─ nothing found → Tier 3
                    │
                    ▼
Tier 3: Escalate to resolver
    Mira posts task card WITH investigation findings already included
    Resolver replies DIRECTLY in thread — Mira listens, never relays
    Mira detects resolution, DMs resolver: "Want to save this?"
    Resolution written to Vault, Mira follows up with requester
            │
            ▼
PM identity (async, background)
    Vault patterns analyzed → Enhancement Proposals generated
    Product Owner reviews in Canvas Dashboard → approve / reject / defer
    Approved fix implemented → Mira DMs original requesters to close the loop
```

---

## System overview

```
                         Slack Workspace
                  (the only surface end users see)
┌──────────────────────────────────────────────────────────────┐
│                                                               │
│  User/Requester ◄──────────────────────► Resolver/Owner      │
│        │           (direct, in-thread)          ▲            │
│        │                                        │             │
│        ▼                                        │             │
│  ┌─────────────┐                        ┌───────┴────┐       │
│  │  mira-app   │── escalates, listens ──►(Slack thread)      │
│  │   (Mira)    │                        └────────────┘       │
│  └──────┬──────┘                                             │
│         │   Canvas Dashboard (PM view + Requester view)      │
└─────────┼──────────────────────────────────────────────────┘
          │  Python import (API contract — 4 functions)
          ▼
  ┌──────────────────┐
  │  vault-service   │
  │ (Knowledge Vault)│
  └──────────────────┘
          │
          ▼
  ┌──────────────────┐     ┌──────────────────┐
  │    Supabase      │     │   GitHub MCP     │
  │  (PostgreSQL +   │     │  Data Dict MCP   │
  │    pgvector)     │     └──────────────────┘
  └──────────────────┘
```

---

## Components

### `mira-app/` — the conversational layer (Jinqiu)

```
mira-app/
├── app.py                    # entry point — Bolt app, Socket Mode
├── config.py                 # env var loading + validation
├── handlers/
│   ├── mention_handler.py    # @Mira listener, 3-tier search orchestration
│   ├── action_handler.py     # button actions (confirm / not helpful)
│   └── resolution_handler.py # detects resolver replies, triggers Vault write
├── services/
│   ├── intent.py             # Claude API — QUESTION vs NOISE
│   ├── task_card.py          # Block Kit card builder (all 7 statuses)
│   ├── vault_client.py       # Python wrapper — 4-function contract
│   ├── slack_search.py       # Real-Time Search API integration
│   ├── mcp_github.py         # GitHub MCP client (Week 2)
│   └── mcp_data_dict.py      # Data Dictionary MCP client (Week 2)
├── pm/
│   └── proposal_engine.py    # Pattern analysis → Enhancement Proposals (Week 2–3)
└── dashboard/
    └── canvas_view.py        # Slack Canvas API — dual-perspective dashboard (Week 3)
```

**Responsibilities:** intent classification, 3-tier search orchestration, task card lifecycle,
resolution detection, DM to resolver, Enhancement Proposal generation, Canvas Dashboard.

**Does NOT own:** embeddings, confidence scoring, database schema, persistence.

---

### `vault-service/` — the storage and verification layer (Jie)

```
vault-service/
├── knowledge_vault/
│   └── __init__.py           # public API — 4 functions
├── schema.sql                # task_cards + vault_entries tables + match_vault_entries RPC
├── embeddings.py             # OpenAI text-embedding-3-small
├── confidence.py             # scoring constants + accumulation helpers
└── smoke_test.py             # end-to-end test against real Supabase
```

**Responsibilities:** schema ownership, embeddings, pgvector cosine similarity search,
three-signal confidence logic, version history (push-on-update, never delete).

---

### External services

| Service | Role |
|---------|------|
| Supabase (PostgreSQL + pgvector) | Persistent storage — only vault-service talks to it directly |
| GitHub MCP | Read code, SQL files, schema — Tier 2 search source |
| Data Dictionary MCP | Field definitions, business terms — Tier 2 search source |
| Slack Canvas API | Dashboard surface — richer than Block Kit, still Slack-native |

---

## API contract

The only coupling point between `mira-app` and `vault-service`. Changing any signature
requires agreement from both team members.

### `create_task_card(requester_id, channel_id, thread_ts, question_raw, question_intent)`
```
Returns: str  # task_card UUID
```

### `search_vault(query_text)`
```
Returns:
{
  match_found:       bool,
  entry_id:          uuid | None,
  answer:            str | None,
  owner_id:          str | None,
  confidence:        float,        # 0–1
  last_confirmed_at: str | None
}
```
Thresholds: `> 0.85` instant · `0.70–0.85` clarify first · `< 0.70` no match.

### `upsert_vault_entry(task_card_id, question_canonical, answer, owner_id, signal, ambiguous)`
```
signal: 'signal_1' | 'signal_2' | 'signal_3'
ambiguous: bool  # signal_2 only — True = ambiguous reply, False = silence

Returns:
{
  entry_id:         uuid,
  status:           'verified' | 'unconfirmed' | 'outdated',
  confidence_score: float
}
```

### `update_status(task_card_id, new_status)`
```
Returns: { success: bool, updated_at: str }
```

---

## Data flow — one full resolution cycle

```
1.  User @ Mira with a question
2.  Claude classifies: QUESTION → proceed / NOISE → ignore
3.  Post draft card immediately (instant feedback)
4.  create_task_card() → DB record created
5.  search_vault() — Tier 1
6a. Match (>0.85) → pending_confirm with ⚡ Vault hit card
6b. Low match (0.70–0.85) → clarifying question in thread
6c. No match → Tier 2 parallel search
7.  Tier 2: Slack history + GitHub MCP + Data Dictionary MCP
8a. Candidate found → pending_confirm with source reference
8b. Nothing → Tier 3: human_working card, register thread
9.  Resolver replies in thread → resolution_handler detects it
10. Card → pending_confirm with resolver's answer
11. Requester confirms (✅ / "got it") or denies ("still broken")
12. signal_1 → upsert_vault_entry() → verified
    signal_2 → upsert_vault_entry() → unconfirmed ("Suggested")
    signal_3 → upsert_vault_entry() → escalate, old answer → version_history
13. Mira DMs resolver: "Want to save this for next time?"
14. [Background] Vault patterns analyzed → Enhancement Proposals generated
15. [Background] Approved fixes → Mira DMs original requesters
```

---

## Dashboard — Slack Canvas

The Knowledge Vault Dashboard lives in Slack Canvas, not Block Kit App Home. Canvas supports
real tables, rich text, and structured sections — giving a proper knowledge-base experience
without leaving Slack.

**Requester view (personal):**
- My questions — status, resolution history, whether my feedback drove any product change

**Resolver / Product Owner view:**
- Open tasks (human_working) sorted by age
- Knowledge Vault health (verified / suggested / outdated counts)
- Enhancement Proposals with [Approve] [Reject] [Defer] actions

---

## Tech stack

| Layer | Technology |
|-------|-----------|
| Bot framework | Slack Bolt for Python |
| LLM — intent, extraction | Claude (`claude-sonnet-4-6`) |
| Embeddings — semantic search | OpenAI `text-embedding-3-small` |
| Database | Supabase (PostgreSQL + pgvector) |
| History search | Slack Real-Time Search API |
| Code + schema search | GitHub MCP |
| Business terms | Data Dictionary MCP |
| Task card UI | Slack Block Kit |
| Dashboard | Slack Canvas API |
| Hosting | Railway |

---

## Deployment

```
mira-app/      → Railway (Socket Mode dev → HTTP mode production)
vault-service/ → Python package imported directly by mira-app (same process)
Supabase       → hosted, free tier
```

---

## Why this split

`mira-app` is about **conversation** — understanding what's being asked, orchestrating search,
deciding when to step back. `vault-service` is about **trust** — whether an answer is reliable,
how that trust accumulates, what happens when it's wrong. Keeping these separate means each
can be built, tested, and reasoned about independently — which is also why two people can
build them in parallel without blocking each other.

The Canvas Dashboard and Enhancement Proposal engine live in `mira-app` because they are
about surfacing and acting on information, not about storing it. The storage boundary stays clean.
