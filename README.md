# LoopBack

LoopBack is a Slack-native AI agent that closes the knowledge loop inside teams — and then
goes further, turning repeated support questions into product improvement proposals.

**Every problem your organization solves should only ever need to be solved once.**

---

## The problem

Teams repeat the same questions over and over in Slack. Answers live in DMs, buried threads,
or someone's head. Knowledge workers spend ~20% of their workweek re-finding information
someone else already knew (McKinsey). But the deeper problem is that no one connects the dots:
the same question asked seven times is a signal that something in the product is broken.
LoopBack captures both the answer *and* the pattern.

---

## Mira's three roles

### 1. Support Assistant
When someone `@Mira` with a question, she works through three tiers — fastest first:

```
@Mira why did approval rate drop 40%?
    │
    ▼
Tier 1: Knowledge Vault (semantic search, pgvector)
    ├─ confidence > 0.85  → return verified answer instantly
    ├─ confidence 0.7–0.85 → ask clarifying question first
    └─ no match
            │
            ▼
Tier 2: Parallel search across three sources
    ├─ Slack history (Real-Time Search API)
    ├─ GitHub MCP (code, SQL files, schema)
    └─ Data Dictionary MCP (field definitions, business terms)
            │
            ├─ candidate found → surface + clarify
            └─ nothing found
                    │
                    ▼
Tier 3: Escalate to resolver
    Mira posts task card with all investigation findings so far
    Resolver answers DIRECTLY in thread — Mira listens, never relays
    Mira follows up: "Did this resolve your issue?"
```

### 2. Knowledge Guardian
Every resolved conversation is an opportunity to build institutional memory:

```
Resolution detected (✅ reaction / "got it" / explicit confirm)
    │
    ▼
Mira DMs the resolver:
  "Looks like [User] confirmed your fix worked.
   Want to save this for the next person?"
  [Save it]  [Skip]
    │
    ├─ Save it → Vault entry, status: verified
    └─ No response (30 min) → Vault entry, status: "Suggested, not yet verified"
         └─ Future users confirm it works → confidence rises → auto-verified
```

Old answers are never deleted — `signal_3` (denial) pushes them into `version_history`
and the new answer takes over, preserving full audit trail.

### 3. Product Manager *(v2 — the most novel part)*
After enough resolved questions accumulate, Mira analyzes patterns and generates
**Enhancement Proposals** — product backlog cards derived from support data:

```
Vault accumulates 5+ questions pointing to the same root cause
    │
    ▼
Mira identifies: this is a product gap, not a one-off support problem
    │
    ▼
Enhancement Proposal posted to Product Owner's Dashboard:
  ┌──────────────────────────────────────────────────────┐
  │ Enhancement Proposal                                  │
  │ Source: 7 related user questions (links)              │
  │ Finding: product_type field missing → approval rate   │
  │          calculations wrong, asked 7 times            │
  │ Suggestion: add product_type as NOT NULL in schema    │
  │ Projected impact: ~60% fewer DATA_QUALITY requests    │
  │ [Approve]  [Reject]  [Defer]                         │
  └──────────────────────────────────────────────────────┘
    │
    └─ Approved + implemented → Mira DMs the original requesters:
         "You asked about approval rate in March.
          Based on your feedback, we fixed the product_type schema issue.
          This won't happen again."
```

---

## Demo — three acts

**Act 1 — Cold start** *(Vault empty, MCP finds the clue)*
> BA asks: *"Why did our approval rate drop 40%?"*
> Mira searches the Vault (empty), Slack history (nothing), then GitHub MCP — finds the `da_approval_metrics.sql` query and Data Dictionary showing `product_type` is `required for approval logic` but has massive NULLs in `raw_applications`.
> Mira escalates to DE with her findings. DE confirms and replies directly to BA. Mira asks DE to save it. DE clicks Save. Vault entry written, `verified`.

**Act 2 — Vault hit** *(same problem, new person, instant answer)*
> New BA asks: *"Why is my approval rate so low?"*
> Mira matches semantically, returns the verified answer in seconds with confidence score and original owner. DE is never disturbed.

**Act 3 — PM identity** *(patterns become proposals)*
> Five approval-rate questions have accumulated. Mira posts an Enhancement Proposal to the Product Owner's Dashboard: add `product_type` as NOT NULL. Owner approves, DE implements. Mira DMs the original requesters: *"Your feedback drove this fix."*

---

## What makes this different

| | Slack AI | Guru / Tettra | LoopBack |
|--|---------|--------------|---------|
| Finds answers | ✓ | ✓ | ✓ |
| Verifies answers | ✗ | Manual | Automatic |
| Zero maintenance | ✓ | ✗ | ✓ |
| Reads your codebase | ✗ | ✗ | ✓ (GitHub MCP) |
| Turns support into product backlog | ✗ | ✗ | ✓ |
| Closes the loop with users | ✗ | ✗ | ✓ |

---

## Implementation status

| Feature | Status |
|---------|--------|
| Slack Bolt app, Socket Mode | ✅ Done |
| Claude intent classification | ✅ Done |
| Block Kit task card — all 7 lifecycle states | ✅ Done |
| Button handlers (confirm / not helpful) | ✅ Done |
| Resolution detection (listens for resolver replies) | ✅ Done |
| Vault client + stub mode | ✅ Done |
| Real-Time Search API (Slack history) | ✅ Done |
| Knowledge Vault — embeddings + pgvector (Jie) | ✅ Done (needs Supabase config) |
| Knowledge Vault — 3-signal confidence logic (Jie) | ✅ Done (needs Supabase config) |
| GitHub MCP integration | ⏳ Week 2 |
| Data Dictionary MCP | ⏳ Week 2 |
| DM resolver "Want to save this?" | ⏳ Week 2 |
| Enhancement Proposal generation | ⏳ Week 2–3 |
| Slack Canvas Dashboard | ⏳ Week 3 |
| Railway deploy + demo recording | ⏳ Week 4 |

---

## Repository layout

```
loopback-demo/
├── mira-app/        # Slack bot, Claude intent, task cards, MCP — Jinqiu
└── vault-service/   # Knowledge Vault: embeddings, pgvector, confidence — Jie
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for system design and API contract.
See [mira-app/README.md](mira-app/README.md) for setup instructions.

---

## Tech stack

| Layer | Technology |
|-------|-----------|
| Bot framework | Slack Bolt for Python, Socket Mode |
| Intent + extraction | Claude API (`claude-sonnet-4-6`) |
| Semantic search | OpenAI `text-embedding-3-small` + pgvector |
| Database | Supabase (PostgreSQL) |
| History search | Slack Real-Time Search API |
| Code + schema search | GitHub MCP |
| Business terms | Data Dictionary MCP |
| Task card UI | Slack Block Kit |
| Dashboard | Slack Canvas API |
| Hosting | Railway |
