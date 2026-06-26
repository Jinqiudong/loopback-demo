# LoopBack

**Every problem solved becomes organizational memory. Every pattern becomes a product fix.**

---

## The problem

Teams repeat the same questions over and over in Slack. Answers live in DMs, buried threads,
or someone's head. Knowledge workers spend ~20% of their workweek re-finding information
someone else already knew (McKinsey). But the deeper problem is invisible: the same question
asked seven times is a signal that something in the product is broken — and nobody connects
those dots. LoopBack does.

---

## Mira's three roles

### 1. Support Assistant
When someone `@Mira` with a question, she works through three tiers — fastest first:

```
@Mira question
    │
    ▼
Tier 1: Knowledge Vault (semantic search, pgvector)
    ├─ confidence > 0.85  → return verified answer instantly
    ├─ confidence 0.7–0.85 → ask clarifying question first
    └─ no match
            │
            ▼
Tier 2: Parallel search (three sources simultaneously)
    ├─ Slack history      (Real-Time Search API)
    ├─ GitHub MCP         (code, SQL files, schema)
    └─ Data Dictionary MCP (field definitions, business terms)
            │
            ├─ findings assembled → task card enriched with what Mira found
            │   Mira checks in with requester: "Based on what I found,
            │   it looks like [X] — is this the right direction?"
            │   Requester confirms → Mira loops in resolver with full context
            └─ nothing useful found → escalate directly
                    │
                    ▼
Tier 3: Escalate to resolver
    Mira posts task card with all investigation findings included
    Resolver answers DIRECTLY in thread — Mira listens, never relays
    Requester gives a signal → Mira writes to Vault automatically
```

### 2. Knowledge Guardian
Every resolved conversation is captured automatically based on requester signals —
no manual action required from anyone:

```
Signal 1 (clear confirm: ✅ / "got it" / "that fixed it")
  → Vault entry written, status: verified
  → Source thread link preserved — every verified answer links back to where it came from

Signal 2 (silence — the most common outcome)
  → Mira follows up once after 30 min
  → Still no response → status: "Suggested, not yet verified"
  → Next user hits the same answer and doesn't deny it → confidence rises → auto-verified

Signal 3 (explicit denial: "this didn't work")
  → Back to resolver for another attempt
  → Old answer pushed to version_history (never deleted)
  → New answer becomes current
```

No resolver button clicks. No manual documentation. Knowledge accumulates from conversation.

### 4. Channel Intelligence
`@Mira insights` opens a time period selector. One click updates the **Channel Insights Canvas** —
a live Slack Canvas showing what the team has been asking and what got resolved:

```
✅ Knowledge        — verified answers, grouped by topic
💡 Answered Pending — answers awaiting confirmation
❓ Open Questions   — unresolved questions still in progress
```

Questions are clustered semantically (not by keyword) — similar questions surface as one topic,
not as a list of duplicates. The Canvas persists and updates each time a period is selected.

### 3. Product Manager *(the most novel part)*
After enough resolved task cards accumulate, Mira analyzes patterns across them — not
keyword matching, but semantic understanding of what problems keep recurring and what the
answers reveal about the underlying system.

When Mira detects a pattern worth surfacing, she generates an **Enhancement Proposal**:
a structured insight card in the Product Owner's Dashboard that explains what she observed
and what it might mean. The content of each proposal is AI-generated from the actual task
card data — Mira decides what's worth saying based on what she's learned.

```
Vault accumulates task cards across multiple resolved questions
    │
    ▼
Mira analyzes patterns (Claude-powered, no predefined templates)
    │
    ▼
Enhancement Proposal posted to Dashboard:
  What Mira observed, what it might signal, suggested next step
  Source links → the actual task cards that led here
  [Approve]  [Reject]  [Defer]
    │
    └─ Approved + implemented → Mira DMs original requesters:
         "Your question contributed to a product improvement."
```

---

## Demo — three acts

**Act 1 — Cold start** *(Vault empty, Mira investigates)*
> A BA asks about a data anomaly. Mira finds nothing in the Vault or Slack history, but
> GitHub MCP and the Data Dictionary surface relevant findings. Mira enriches the task card
> with what she found and checks in with the BA: *"Based on what I found, does this look
> like the right direction?"* BA confirms. Mira loops in the DE with full context. DE replies
> directly to the BA in thread. BA confirms it's resolved. Mira writes the answer to the
> Vault — verified.

**Act 2 — Vault hit** *(same problem, new person, instant answer)*
> A different BA asks a semantically similar question. Mira matches it to the verified entry
> and returns the answer in seconds with confidence score and original owner. The DE is never
> disturbed.

**Act 3 — PM identity** *(patterns surface as proposals)*
> Several task cards have accumulated. Mira runs her pattern analysis and posts an Enhancement
> Proposal to the Product Owner's Dashboard. The proposal is AI-generated from the task card
> data — Mira surfaces what she noticed and what it might mean. The Product Owner reviews and
> decides: approve, reject, or defer.

**Act 4 — Channel Intelligence** *(what has the team been asking?)*
> A PM types `@Mira insights` and selects **This Month**. The Channel Insights Canvas updates
> instantly — verified answers grouped by topic, open questions still unresolved, source thread
> links back to the original conversations. One view shows the team's knowledge health at a
> glance: what's been figured out, what's still open, and where the answers came from.

---

## What makes this different

| | Slack AI | Guru / Tettra | LoopBack |
|--|---------|--------------|---------|
| Finds answers | ✓ | ✓ | ✓ |
| Verifies answers | ✗ | Manual | Automatic |
| Zero maintenance | ✓ | ✗ | ✓ |
| Reads your codebase | ✗ | ✗ | ✓ (GitHub MCP) |
| Links answers back to source threads | ✗ | ✗ | ✓ |
| Channel knowledge health dashboard | ✗ | ✗ | ✓ (Canvas) |
| Turns support into product backlog | ✗ | ✗ | ✓ |

---

## Implementation status

| Feature | Status |
|---------|--------|
| Slack Bolt app, Socket Mode | ✅ |
| Claude intent classification | ✅ |
| Block Kit task card — all 7 lifecycle states | ✅ |
| Button handlers + resolution detection | ✅ |
| Real-Time Search API (Slack history) | ✅ |
| Vault client + 3-signal auto-save | ✅ |
| Knowledge Vault — pgvector + semantic search (Jie) | ✅ |
| Source thread links on verified answers | ✅ |
| Channel Insights Canvas (`@Mira insights`) | ✅ |
| GitHub MCP integration | ⏳ |
| Data Dictionary MCP | ⏳ |
| Pre-escalation requester check-in | ⏳ |
| Enhancement Proposal engine (Claude-powered) | ⏳ |
| Railway deploy + demo recording | ⏳ |

---

## Repository layout

```
loopback-demo/     ← this repo (code only)
├── mira-app/      # Slack bot, Claude, MCP clients, proposal engine — Jinqiu
└── vault-service/ # Knowledge Vault: embeddings, pgvector, confidence — Jie
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for system design and API contract.

---

## Tech stack

| Layer | Technology |
|-------|-----------|
| Bot framework | Slack Bolt for Python |
| Intent + extraction + proposals | Claude (`claude-sonnet-4-6`) |
| Semantic search | OpenAI `text-embedding-3-small` + pgvector |
| Database | Supabase (PostgreSQL) |
| History search | Slack Real-Time Search API |
| Code + schema search | GitHub MCP |
| Business terms | Data Dictionary MCP |
| Task card UI | Slack Block Kit |
| Dashboard | Slack Canvas API |
| Hosting | Railway |
