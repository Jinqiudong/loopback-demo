# LoopBack — Architecture

---

## What LoopBack is

**One-liner:** Every problem your organization solves should only ever need to be solved once.

LoopBack is a Slack-native system with three layers of value:

- **Mira** — the AI colleague in Slack. She searches three knowledge tiers in order,
  checks in with the requester before looping in anyone, and never relays between requester and resolver.
- **Knowledge Vault** — the growing, verified memory Mira builds from every resolved conversation.
- **Channel Insights** — Show the summary of your channel activitis, present the Knowledge Vault, and Mira's PM identity analyzes Vault patterns to surface
  Enhancement Opportunities, turning repeated support questions into product signals.

---

## The problem

Every conversation in Slack disappears the moment the thread goes quiet. The person asking
just wants to be unblocked. The person answering may have answered this before. And nobody
connects the dots: the same question asked seven times signals a product gap — but that signal
is invisible unless something is listening. The oppotunites for product improvement or process improvement never get noticed. LoopBack listens.

---

## Core mechanism

```
User @ Mira with a question
    │
    ▼
Intent classification (Claude) — question or noise?
    │ QUESTION
    ▼
Tier 1: Knowledge Vault (fastest — always first)
    ├─ confidence ≥ 0.82  → return verified answer → pending_confirm with requester
    └─ no match → Tier 2
            │
            ▼
Tier 2: Agentic investigation (Claude tool-use loop — MCP pattern)
    Claude receives the question + tool list and autonomously decides what to search:
    ├─ search_github(query)        — searches analytics codebase (SQL, schema)
    ├─ read_file(path)             — reads specific files from the repo
    ├─ search_slack_history(query) — Real-Time Search API
    └─ read_known_issues()         — reads known issues doc directly

    Claude runs multiple tool calls until it has enough context.
    This is what makes Mira a genuine agent, not a scripted chatbot.
            │
            ├─ findings assembled → direction_check card posted to requester:
            │   "Based on what I found, does this look right?"
            │   Requester confirms → Mira loops in resolver WITH full context already assembled
            └─ nothing found → escalate directly to resolver
                    │
                    ▼
Tier 3: Escalate to resolver
    Task card includes Mira's investigation findings (not empty)
    Resolver replies DIRECTLY in thread — Mira listens, never relays
    Mira captures the answer automatically (no resolver action needed)
            │
            ▼
Three-signal auto-save (no manual steps, requester signals only):
    Signal 1 (clear confirm)  → verified   (confidence: 0.90, +0.05 per reuse)
    Signal 2 (silence)        → unconfirmed → accumulates trust via future reuse
    Signal 3 (denial)         → escalate, old answer pushed to version_history
            │
            ▼
Channel Insights (async, on @Mira insights)
    Claude analyzes accumulated task cards semantically
    Surfaces Enhancement Opportunities (LLM-generated, no templates)
    Channel Insights Canvas updated — Impact / Knowledge Vault / Open / Opportunities
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
│         │   Channel Insights Canvas (@Mira insights)         │
└─────────┼──────────────────────────────────────────────────┘
          │  Python import (API contract — 5 functions)
          ▼
  ┌──────────────────┐
  │  vault-service   │
  │ (Knowledge Vault)│
  └──────────────────┘
          │
          ▼
  ┌──────────────────┐     ┌──────────────────┐
  │    Supabase      │     │   GitHub MCP     │
  │  (PostgreSQL +   │     │ (via investigator │
  │    pgvector)     │     │  Claude tool use) │
  └──────────────────┘     └──────────────────┘
```

---

## Intent classification — how Mira decides what to do

Every `@Mira` mention goes through `services/intent.py` — four lightweight Claude classifiers,
each returning a single word at `max_tokens=10`. No parsing, no regex, no keyword matching.

| Classifier | Input | Output | Used when |
|---|---|---|---|
| `classify_intent` | The @mention text | `QUESTION / INSIGHTS / NOISE` | Every @mention — top-level routing |
| `classify_resolution` | Requester's reply in thread | `RESOLVED / ONGOING` | Detecting "got it", "makes sense", "好的谢谢", "👍" |
| `classify_direction_response` | Requester's reply to direction check | `ESCALATE / RESOLVED / UNCLEAR` | After Tier 2 findings — should Mira loop in a resolver? |
| `classify_is_deflection` | Resolver's answer text | `DEFLECTION / ANSWER` | Detecting "please open a ticket" instead of a real answer |

All four classifiers **fail closed** — an API error returns the safe default
(`NOISE`, `ONGOING`, `UNCLEAR`) so a failure never triggers an unintended action.
`classify_resolution` handles multilingual signals natively ("好的谢谢", "明白了", "alright")
because Claude understands context, not just English keywords.

---

## Components

### `mira-app/` — the conversational layer (Jinqiu)

```
mira-app/
├── app.py                    # entry point — Bolt app, Socket Mode
├── config.py                 # env var loading + validation
├── handlers/
│   ├── mention_handler.py    # @Mira listener, 3-tier search orchestration
│   ├── action_handler.py     # button actions (confirm / not helpful / insights period)
│   └── resolution_handler.py # detects resolver replies, triggers Vault write
├── services/
│   ├── intent.py             # Claude API — QUESTION vs INSIGHTS vs NOISE
│   ├── task_card.py          # Block Kit card builder (all 7 statuses)
│   ├── vault_client.py       # Python wrapper — 5-function API contract
│   ├── slack_search.py       # Slack Real-Time Search API integration
│   ├── investigator.py       # Claude tool-use agentic loop (MCP pattern)
│   │                         # Tools: search_github, read_file, search_slack_history
│   ├── mcp_github.py         # GitHub tool implementations for investigator
│   └── reactions.py          # Slack reaction helpers (status → emoji)
├── pm/
│   └── proposal_engine.py    # Claude-powered pattern analysis → Enhancement Opportunities
└── dashboard/
    └── channel_canvas.py     # Slack Canvas API — Channel Insights (Impact/KV/Open/Opportunities)
```

**Responsibilities:** intent classification, 3-tier search orchestration, task card lifecycle,
resolution detection, Enhancement Opportunity generation, Channel Insights Canvas.

**Does NOT own:** embeddings, confidence scoring, database schema, persistence.

---

### `vault-service/` — the storage and verification layer (Jie)

```
vault-service/
├── knowledge_vault/
│   └── __init__.py           # public API — 5 functions
├── api/
│   ├── search_vault.py       # semantic search endpoint
│   ├── upsert_vault_entry.py # write/update entry with signal logic
│   └── update_status.py      # task card status + vault_entry_id link
├── confidence.py             # scoring constants + accumulation helpers
├── embeddings.py             # OpenAI text-embedding-3-small
└── smoke_test.py             # end-to-end test against real Supabase
```

**Responsibilities:** schema ownership, embeddings, pgvector cosine similarity search,
three-signal confidence logic, version history (push-on-update, never delete).

---

### External services

| Service | Role |
|---------|------|
| Supabase (PostgreSQL + pgvector) | Persistent storage — only vault-service talks to it directly |
| GitHub (via Claude tool use) | Read code, SQL files, schema — Tier 2 search source |
| Slack Real-Time Search API | Workspace message history search — Tier 2 search source |
| Slack Canvas API | Channel Insights surface — markdown, live-updated |
| Slack Block Kit | Task card UI — 7-state lifecycle |

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
  confidence:        float,        # cosine similarity 0–1
  last_confirmed_at: str | None,
  source_thread:     str | None    # permalink to original resolution thread
}
```
Threshold: `≥ 0.82` → vault hit (high confidence, return answer immediately).

### `upsert_vault_entry(task_card_id, question_canonical, answer, owner_id, signal, ambiguous, source_thread)`
```
signal: 'signal_1' | 'signal_2' | 'signal_3'
ambiguous: bool  # signal_2 only — True = ambiguous reply, False = silence

Returns:
{
  entry_id:         uuid,
  status:           'verified' | 'unconfirmed',
  confidence_score: float
}
```
Also updates `task_cards.status` to match vault_entry status.

### `update_status(task_card_id, new_status, vault_entry_id=None)`
```
vault_entry_id: uuid | None  # optionally links task_card to vault entry in same call

Returns: { success: bool, updated_at: str }
```

### `get_channel_task_cards(channel_id, since)`
```
Returns: list of enriched task card dicts:
{
  task_card_id:     str,
  question:         str,   # question_canonical from vault_entry, or question_raw
  answer:           str,   # current_answer from vault_entry
  status:           str,
  thread_ts:        str,
  source_thread:    str,   # permalink to original thread
  confidence_score: float,
  embedding:        list[float],
  owner_id:         str | None
}
```
Used by Channel Insights Canvas to build Impact / KV / Open sections.

---

## Data flow — one full resolution cycle

```
1.  User @ Mira with a question
2.  Claude classifies: QUESTION → proceed / INSIGHTS → show period selector / NOISE → ignore
3.  Post draft card immediately (instant feedback in thread)
4.  create_task_card() → DB record created
5.  search_vault() — Tier 1
6a. Match (≥0.82) → pending_confirm with ⚡ Vault hit card + "This helped ✓" button
6b. No match → Tier 2 agentic investigation
7.  investigator.py: Claude tool-use loop — search_github / read_file / search_slack_history
8a. Findings assembled → direction_check card: "Does this look like the right direction?"
    Requester confirms → card → human_working, resolver notified with full context
8b. Nothing found → Tier 3: human_working card directly
9.  Resolver replies directly in thread → resolution_handler detects reply
10. Card → pending_confirm with resolver's answer + "Yes, resolved ✓" button
11. Requester clicks button (Signal 1) or stays silent (Signal 2) or denies (Signal 3)
12. Signal 1 → upsert_vault_entry(signal_1) → task_card + vault_entry → verified (0.90)
    Signal 2 → upsert_vault_entry(signal_2) → unconfirmed (0.30–0.55)
    Signal 3 → upsert_vault_entry(signal_3) → escalate, old answer → version_history
13. Canvas auto-refreshes with latest stats (best-effort, non-blocking)
```

---

## Channel Insights Canvas

Triggered by `@Mira insights` → period selector (This Month / Quarter / Year) → Canvas updated.
Also auto-refreshes silently on every vault_confirm action.

**Four sections:**

**📊 Impact** — questions received, resolved vs open count, "Mira can now auto-serve X topics"

**🧠 Knowledge Vault** — verified entries clustered by semantic similarity + answer text.
Each cluster shows:
- Full answer text as title (knowledge summary, not the question)
- Confidence score + resolver name (via `users_info` API)
- Original thread (chronologically first) with date + question excerpt + link
- Later threads that were answered by the same knowledge, indented below

**❓ Open** — unresolved questions with status progress string:
`🔍 Investigated → ✓ Direction confirmed → ⏳ Resolver notified`

**🌱 Enhancement Opportunities** — Claude-generated from resolved task cards.
Numbered, categorized (📖 documentation / 🔧 code / 🎨 UX / 📋 process / 🚀 product),
with observed pattern + suggested fix.

---

## Tech stack

| Layer | Technology |
|-------|-----------|
| Bot framework | Slack Bolt for Python (Socket Mode) |
| LLM — intent, investigation, proposals | Claude (`claude-sonnet-4-6`) |
| Embeddings — semantic search | OpenAI `text-embedding-3-small` |
| Database | Supabase (PostgreSQL + pgvector) |
| History search | Slack Real-Time Search API |
| Code + schema search | GitHub via Claude tool use (MCP pattern) |
| Task card UI | Slack Block Kit (7-state lifecycle) |
| Channel Insights | Slack Canvas API |
| Hosting | Railway |

---

## Deployment

```
mira-app/      → Railway (Python process, Socket Mode)
vault-service/ → Python package installed in mira-app's environment (pip install -e)
               → same Railway process, imported directly
Supabase       → hosted (external)
```

---

## Why this split

`mira-app` is about **conversation** — understanding what's being asked, orchestrating search,
deciding when to step back. `vault-service` is about **trust** — whether an answer is reliable,
how that trust accumulates, what happens when it's wrong. Keeping these separate means each
can be built, tested, and reasoned about independently — which is also why two people can
build them in parallel without blocking each other.

The Canvas Dashboard and Enhancement Opportunity engine live in `mira-app` because they are
about surfacing and acting on information, not about storing it. The storage boundary stays clean.
