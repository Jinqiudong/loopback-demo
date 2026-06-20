# ARCHITECTURE.md

System architecture for LoopBack. This is the technical structure
reference — for product mechanism and design rationale, see
`docs/DESIGN.md`. For day-by-day build status, see
`docs/implementation-plan.md`.

---

## High-level overview

```
                         Slack Workspace
                  (the only surface end users see)
┌──────────────────────────────────────────────────────────┐
│                                                            │
│   User/Requester ◄──────────────────────► Resolver/Owner  │
│         │           (direct, in-thread)          ▲        │
│         │                                          │        │
│         ▼                                          │        │
│   ┌─────────────┐                          ┌──────┴─────┐ │
│   │   mira-app   │ ── escalates, listens ──►│  (Slack    │ │
│   │   (Mira)     │                          │   thread)  │ │
│   └──────┬───────┘                          └────────────┘ │
│          │                                                  │
└──────────┼──────────────────────────────────────────────────┘
           │  API contract (3 functions, see docs/DESIGN.md)
           ▼
   ┌──────────────────┐
   │  vault-service     │
   │  (Knowledge Vault) │
   └──────────────────┘
           │
           ▼
   ┌──────────────────┐
   │  Supabase          │
   │  (PostgreSQL +     │
   │   pgvector)         │
   └──────────────────┘
```

Two independently deployable services, talking to each other through a
fixed API contract. Neither needs to know the other's internals.

---

## Components

### 1. `mira-app/` — the conversational layer

**Owns:** everything that happens inside Slack.

```
mira-app/
├── app.py                  # entry point — starts the Bolt app (Socket Mode)
├── config.py                # env var loading + validation
├── handlers/
│   └── mention_handler.py   # listens for @Mira mentions, routes to services
├── services/
│   ├── intent.py             # Claude API — classifies question vs. noise
│   ├── task_card.py          # builds Block Kit task card UI, per status
│   └── vault_client.py       # HTTP client for calling vault-service's API
│                              #   (Day 3-5 addition — wraps the 3 contract
│                              #   functions so the rest of mira-app never
│                              #   talks to Supabase directly)
└── dashboard/                # App Home — Knowledge Vault Dashboard UI
    └── home_view.py           # (Week 3 addition)
```

**Responsibilities:**
- Receive Slack events (`app_mention`, message replies, reactions)
- Classify intent (Claude API)
- Call `vault-service` to check for an existing answer before doing
  anything else (cost optimization — see `docs/DESIGN.md` § Why
  Vault-first matters)
- Search Slack history when the Vault has no match (Real-Time Search API)
- Render and update the task card (Block Kit) as it moves through the
  Resolution Cycle
- Detect confirmation signals (reactions, reply text, silence/timers)
- Render the Knowledge Vault Dashboard inside App Home

**Does NOT own:** embeddings, confidence scoring, the database schema, or
any persistence logic. Mira talks to the Vault only through the three
contract functions — see "API Contract" below.

---

### 2. `vault-service/` — the storage and verification layer

**Owns:** everything related to persisting and retrieving knowledge.

```
vault-service/
├── schema.sql                # CREATE TABLE statements (task_cards, vault_entries)
├── api/
│   ├── search_vault.py        # semantic search against vault_entries
│   ├── upsert_vault_entry.py  # writes/updates an entry, applies signal logic
│   └── update_status.py       # simple status field update on task_cards
├── embeddings.py               # OpenAI text-embedding-3-small wrapper
├── confidence.py                # confidence scoring + accumulation logic
└── requirements.txt
```

**Responsibilities:**
- Own the two-table schema (`task_cards`, `vault_entries`) — see
  `docs/DESIGN.md` § Data model for the exact fields
- Generate embeddings for new questions and stored entries
- Run cosine similarity search via pgvector
- Implement the three-signal confidence logic and the two-tier
  `unconfirmed` distinction (ambiguous reply vs. second silence)
- Implement version history (push-on-update, never delete)
- Expose exactly three functions to `mira-app` — nothing else should be
  called across the boundary

**Does NOT own:** anything Slack-specific. This service has no idea what
a thread, a mention, or a Block Kit card is — it only knows questions,
answers, owners, and confidence.

---

### 3. Supabase (PostgreSQL + pgvector)

Hosted database. Both tables (`task_cards`, `vault_entries`) live here.
`vault-service` is the only component that talks to Supabase directly —
`mira-app` never queries the database; it only calls `vault-service`'s
API functions.

---

## The API contract (the seam between the two services)

This is intentionally the **only** coupling point between `mira-app` and
`vault-service`. Full input/output shapes are documented in
`docs/DESIGN.md` § API contract — summarized here for the architectural
view:

```
search_vault(query_text)
  → does a verified or suggested answer already exist?

upsert_vault_entry(task_card_id, answer, owner_id, signal)
  → writes a new resolution into the Vault, applies signal/confidence logic

update_status(task_card_id, new_status)
  → updates a task card's lifecycle status
```

If this contract needs to change, that's a conversation between both
people working on the project — not a unilateral edit on either side.

---

## Data flow: one full resolution cycle

```
1. User @ Mira with a question
        │
        ▼
2. mira-app: intent.classify_intent() → question or noise?
        │ (question)
        ▼
3. mira-app: vault_client.search_vault(query)
        │
        ├── match_found = true, confidence > 0.85
        │       └──► mira-app renders Verified Answer card → DONE
        │
        └── match_found = false (or low confidence)
                │
                ▼
        4. mira-app searches Slack history (Real-Time Search API)
                │
                ├── candidate found
                │       └──► mira-app asks a clarifying question
                │
                └── nothing found
                        │
                        ▼
                5. mira-app posts task card to resolver, status → human_working
                        │
                        ▼
                6. Resolver replies DIRECTLY to requester in-thread
                   (mira-app is listening, not relaying)
                        │
                        ▼
                7. mira-app detects resolution signal, status → pending_confirm
                        │
                        ▼
                8. 30-min window: signal 1 / 2 / 3 (see docs/DESIGN.md)
                        │
                        ▼
                9. mira-app calls vault_client.upsert_vault_entry(...)
                        │
                        ▼
                10. vault-service applies confidence logic, writes the
                    entry, returns the new status
                        │
                        ▼
                11. mira-app updates the task card to reflect final status
```

---

## Deployment

```
mira-app/       → Railway (Slack Bolt app, Socket Mode for dev,
                   HTTP mode once deployed)
vault-service/  → Railway (or same service as mira-app if simpler —
                   TBD based on how the API is exposed; could be a
                   thin internal API or a Python module imported
                   directly if both run in the same process)
Supabase        → hosted, free tier
```

**Open question (resolve during Week 1 contract lock-in):** will
`vault-service` run as a separate HTTP service that `mira-app` calls over
the network, or as a Python package that `mira-app` imports directly in
the same process? Either works with the same three-function contract —
this is a deployment detail, not a design one. Pick whichever is faster
to build and debug under the time constraint.

---

## Tech stack summary

| Layer | Technology |
|---|---|
| Bot framework | Slack Bolt for Python |
| LLM (intent, extraction, clarifying questions) | Claude (claude-sonnet-4-6) |
| Embeddings (semantic search) | OpenAI text-embedding-3-small |
| Database | Supabase (PostgreSQL + pgvector) |
| UI | Slack Block Kit (task cards) + App Home (Dashboard) — no external frontend |
| Search | Slack Real-Time Search API (history search) |
| Hosting | Railway |

---

## Why this split (not just "who's doing what")

The `mira-app` / `vault-service` boundary isn't just a convenient way to
divide work between two people — it mirrors a real product boundary:

- `mira-app` is about **conversation** — understanding what's being
  asked, talking to people, deciding when to step back and let humans
  talk directly.
- `vault-service` is about **trust** — deciding whether an answer is
  reliable enough to hand back instantly, and how that trust builds or
  decays over time.

Keeping these separate means either piece can be reasoned about, tested,
and improved without needing to understand the other's internals — which
is also why the two of us could build them in parallel, including during
the week one of us was traveling.
