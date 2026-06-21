# LoopBack

LoopBack is a Slack-native AI agent that closes the knowledge loop inside teams.
When someone asks a question in Slack, Mira — LoopBack's AI — checks whether it's
been answered before, surfaces the best existing answer for confirmation, and once
confirmed, writes the verified answer back into a shared Knowledge Vault so the
next person gets an instant reply.

**Every problem your organization solves should only ever need to be solved once.**

## The problem

Teams repeat the same questions over and over in Slack. Answers live in DMs,
buried threads, or someone's head. Knowledge workers spend ~20% of their workweek
re-finding information someone else already knew (McKinsey). LoopBack intercepts
those questions and turns each resolved conversation into reusable, verified knowledge.

## How it works

```
@Mira how do I request PTO?
    │
    ▼
Intent classification (Claude) — question or noise?
    │ QUESTION
    ▼
Knowledge Vault search (semantic, via pgvector)
    ├─ match found (confidence > 0.85)
    │       └──► Suggest verified answer → user confirms → done
    ├─ low confidence (0.7–0.85)
    │       └──► Ask clarifying question to confirm it's the same problem
    └─ no match
            │
            ▼
    Slack history search (Real-Time Search API) ← in implementation
            ├─ candidate found → surface + clarify
            └─ nothing found → escalate to resolver
                    │
                    Resolver answers DIRECTLY in thread (Mira listens, never relays)
                    │
                    ▼
            Confirmation window (30 min)
            → Confirmed  → Vault entry marked verified
            → Silence    → Saved as "Suggested, not yet verified"
            → Denied     → Back to resolver, old answer preserved in version history
```

## Demo

The demo follows three acts — each one shows a different part of the knowledge loop.

**Act 1 — Cold start (the loop begins)**
> A question has never been asked before. Mira searches the Vault, finds nothing, and escalates to a resolver. The resolver answers directly in the thread — Mira never relays. Once the exchange settles, Mira follows up, the requester confirms, and the answer is written to the Vault as a verified entry.

**Act 2 — Vault hit (the loop pays off)**
> The same question is asked again — in different words. Mira recognizes the intent, retrieves the verified answer from the Vault in seconds, and surfaces it with a confidence score. The resolver is never disturbed. This is what the system is for.

**Act 3 — Knowledge Vault Dashboard**
> Open App Home to see the growing knowledge base: every verified entry, its confidence score, who owns it, how many times it's been used, and the full resolution history behind it.

---

## What makes this different

| | Slack AI | Guru / Tettra | LoopBack |
|--|---------|--------------|---------|
| Finds answers | ✓ | ✓ | ✓ |
| Verifies answers | ✗ | Manual | Automatic |
| Zero maintenance | ✓ | ✗ | ✓ |
| Knowledge has provenance | ✗ | Sometimes | Always |
| Works where teams already are | ✓ | ✗ | ✓ |

## Implementation status

| Feature | Status |
|---------|--------|
| Slack Bolt app, Socket Mode | ✅ Done |
| Claude intent classification (QUESTION / NOISE) | ✅ Done |
| Block Kit task card — all 7 lifecycle states | ✅ Done |
| Confirm / Not Helpful button handlers | ✅ Done |
| Knowledge Vault client (stub mode for dev) | ✅ Done |
| Knowledge Vault — embeddings + pgvector search | ⏳ Week 2 (Jie) |
| Knowledge Vault — 3-signal confidence logic | ⏳ Week 2 (Jie) |
| Slack Real-Time Search API integration | ⏳ Week 3 |
| App Home Dashboard | ⏳ Week 3 |
| Staging deploy + demo recording | ⏳ Week 4 |

## Repository layout

```
loopback-demo/
├── mira-app/        # Slack bot + Claude intent layer — Jinqiu
└── vault-service/   # Knowledge Vault: storage, embeddings, confidence — Jie
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full system design and API contract.
See [mira-app/README.md](mira-app/README.md) for setup and running instructions.

## Tech stack

| Layer | Technology |
|-------|-----------|
| Bot framework | Slack Bolt for Python, Socket Mode |
| Intent classification | Claude API (`claude-sonnet-4-6`) |
| Semantic search | OpenAI `text-embedding-3-small` + pgvector |
| Database | Supabase (PostgreSQL) |
| History search | Slack Real-Time Search API |
| UI | Slack Block Kit — task cards + App Home Dashboard |
| Hosting | Railway |

