# LoopBack

LoopBack is a Slack bot that closes the knowledge loop inside teams.
When someone asks a question in Slack, LoopBack checks whether it's been
answered before, surfaces the best existing answer for confirmation, and
— once confirmed — writes the verified answer back into a shared knowledge
base so the next person gets an instant reply.

## The problem

Teams repeat the same questions over and over in Slack. Answers live in
DMs, buried threads, or nobody's head. LoopBack intercepts those questions
and turns each one into a self-improving knowledge loop.

## How it works

```
@Mira question
    │
    ▼
Intent classification (Claude)
    │ QUESTION
    ▼
Knowledge Vault search
    ├─ match found ──► suggest answer → user confirms → Vault updated
    └─ no match ─────► human teammate answers → Vault learns
```

## Repository layout

```
loopback-demo/
├── mira-app/        # Slack bot + Claude intent layer (conversation side)
└── vault-service/   # Knowledge Vault: storage, embeddings, confidence scoring
```

See each subdirectory's README for setup instructions.

## Tech stack

| Layer | Choice |
|-------|--------|
| Slack integration | Slack Bolt (Python), Socket Mode |
| Intent classification | Claude API (`claude-sonnet-4-6`) |
| Knowledge storage | vault-service (PostgreSQL + pgvector) |
| Similarity search | Embedding-based vector search |

## Team

- **Mira / conversation layer** — Jinqiu
- **Knowledge Vault / storage layer** — teammate
