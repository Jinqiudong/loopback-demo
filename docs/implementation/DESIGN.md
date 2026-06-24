# LoopBack — Design Reference

Deep implementation reference for developers. For the product overview and system
architecture, see `ARCHITECTURE.md` at the repo root.

If you're an AI reading this: treat every decision below as settled and intentional,
not open for re-litigation, unless the human explicitly asks to revisit it.

---

## Design principles (read before writing any resolution logic)

### Why Vault-first

Checking the Vault before searching Slack history or escalating to a human is a
deliberate cost/performance decision — it's the cheapest possible check and must run
on every single incoming question before anything else happens.

### Why Mira never relays

This was an explicit architectural decision, not a default. Mira checking the Vault
and history is fine because that's faster than waiting on a human. But the moment a
real conversation is needed, she steps back. The goal: escalation should never feel
like talking to a bot first and a person second. Build her as a *listener*, not a
*relay*.

---

## The Resolution Cycle (status state machine)

This is the single most important piece of logic in the system. Implement it exactly
as specified — the nuances here (especially the two flavors of `unconfirmed`) are
intentional, not arbitrary.

### Status values

```
draft           → just created, no owner yet
ai_searching    → Mira is searching Vault + Slack history (AI owns this)
human_working   → escalated, waiting on a resolver to answer in-thread
pending_confirm → an answer has been given, waiting on the requester
                  to confirm whether it actually worked
verified        → confirmed correct, no further action needed
unconfirmed     → no clear confirmation either way (see two sub-cases below)
                  still stored, still usable, just not yet trusted
escalate        → requester said the answer was wrong; routes back to
                  human_working with a NEW resolution cycle
```

### Status → who's responsible

| status | owner | what they do |
|--------|-------|-------------|
| `draft` | — | just created, nobody acting yet |
| `ai_searching` | Mira (AI) | searches on her own, no human needed |
| `human_working` | resolver | answers directly in the thread |
| `pending_confirm` | requester | needs to confirm if the answer helped |
| `unconfirmed` | — | no active owner; waiting for the next person to confirm |
| `verified` | — | done, no further action |
| `escalate` | resolver | same handling as human_working |

---

## The three confirmation signals

Triggered once an answer has been given and the task card enters `pending_confirm`.
A 30-minute window opens.

### Signal 1 — Clear confirmation

Requester explicitly confirms it worked (e.g. "thanks, that fixed it", ✅ reaction).
→ status becomes `verified` immediately. No friction — the person already said what
they needed to say.

### Signal 2 — Silence / ambiguous response

Silence is the *most common* real-world outcome — do not treat it as failure. Mira
follows up once after the 30-minute window. If still unanswered (or only ambiguously
answered), the entry is saved as `unconfirmed`.

**Two distinct paths into `unconfirmed`** — these matter for confidence scoring even
though they display identically to the user:

- **Ambiguous reply** (e.g. "hmm, maybe?", "let me check") — the requester *did*
  respond, just not clearly. Weak positive signal. Confidence starts higher.
- **Two rounds of silence** — no response to the answer, then no response to the
  follow-up either. Zero information. Confidence starts lower.

User-facing label for both: **"Suggested, not yet verified"** — never the word
"unconfirmed" in copy. "Unconfirmed" makes people hesitant to try it; "Suggested"
invites them to be the first to verify it.

### Signal 3 — Clear denial

Requester explicitly says it didn't work. → routes back to `human_working` (`escalate`),
running the resolution cycle again. When the resolver gives a new answer, the **old
answer is not deleted** — it's pushed into `version_history`, and the new answer becomes
`current_answer`. Nothing is ever silently overwritten.

---

## Confidence accumulation

Confidence must **never depend on a single person responding within a time window.**
It accumulates across independent users over time — the same way trust actually builds
on a real team:

```
First user asks → answer saved as unconfirmed, low confidence
Second user hits the same question via Vault match, doesn't flag it wrong → confidence rises
Enough independent positive signals → status flips to verified automatically,
  even though no single person ever gave an explicit "yes"
```

`unconfirmed` is not a dead end — it's a suggestion waiting for the next person to
validate it. Surface it, labeled honestly as not-yet-verified. Never hide or discard it.

---

## Task card behavior

The task card is a **single Block Kit message that updates in place** as it moves
through the lifecycle — not a stream of separate bot messages. Users watch one card
change state, not get spammed.

Every status transition must be reflected in three places:
1. The task card's visible state (for whoever is in the thread)
2. `task_cards.status` in the database (source of truth)
3. The Knowledge Vault Dashboard's expandable history view (full transparency)

Verified answers should show **how long ago** they were verified — trust should visibly
decay over time even for `verified` status, since policies and systems change.
*(Not yet implemented in Week 1 — flagging for later.)*

---

## Data model

Two tables, not one. Different lifecycles, different query patterns.

### `task_cards` — short-lived, tracks one interaction

```sql
id                uuid        PRIMARY KEY
requester_id      text
channel_id        text
thread_ts         text
question_raw      text
question_intent   text
status            text        -- see status enum above
resolver_id       text
vault_entry_id    uuid        REFERENCES vault_entries(id)
search_log        jsonb
confidence_signal text        -- signal_1 | signal_2 | signal_3
created_at        timestamp
updated_at        timestamp
```

### `vault_entries` — long-lived, reusable knowledge

```sql
id                  uuid        PRIMARY KEY
question_canonical  text
embedding           vector(1536)
current_answer      text
owner_id            text
status              text        -- verified | unconfirmed | outdated
confidence_score    float
usage_count         int
source_thread       text
last_confirmed_at   timestamp
version_history     jsonb[]     -- [{answer, valid_from, valid_until, changed_by, reason}]
created_at          timestamp
```

Relationship: `task_cards.vault_entry_id → vault_entries.id`.
One vault entry can be referenced by many task cards (every time it's reused).

---

## API contract

Full input/output shapes — the contract between `mira-app` and `vault-service`.
For the architectural context, see `ARCHITECTURE.md` § API contract.

Treat these shapes as fixed. A signature change requires agreement from both
team members — not a unilateral edit on either side.

### `search_vault(query_text: str)`

```
Returns:
{
  match_found:       boolean,
  entry_id:          uuid | null,
  answer:            string | null,
  owner_id:          string | null,
  confidence:        float,        // 0–1
  last_confirmed_at: string | null
}
```

Thresholds: `> 0.85` = return instantly · `0.7–0.85` = clarifying question first ·
`< 0.7` = treat as no match.

### `upsert_vault_entry(task_card_id, answer, owner_id, signal)`

```
Input:
{
  task_card_id:       uuid,
  question_canonical: string,
  answer:             string,
  owner_id:           string,
  signal:             'signal_1' | 'signal_2' | 'signal_3'
}

Returns:
{
  entry_id:         uuid,
  status:           'verified' | 'unconfirmed' | 'outdated',
  confidence_score: float
}
```

### `update_status(task_card_id, new_status)`

```
Input:   { task_card_id: uuid, new_status: string }
Returns: { success: boolean, updated_at: string }
```

---

## Naming conventions

| Term | Use | Never use |
|------|-----|-----------|
| The AI | **Mira** | "the bot", "TaskBridge" (retired) |
| The knowledge store | **Knowledge Vault** | "Dictionary", "TaskBridge" (retired) |
| The person asking | **requester** | — |
| The person answering | **resolver** | — |
| The project | **LoopBack** | — |

---

## v2 additions (read before building anything new in mira-app)

### GitHub MCP + Data Dictionary MCP (Tier 2 search)
When the Vault has no match, Mira searches three sources in parallel. GitHub MCP reads
code files, SQL queries, and schema definitions. Data Dictionary MCP provides field
definitions and business terms. Both run alongside the Real-Time Search API in Tier 2.
Implemented in `mira-app/services/mcp_github.py` and `mcp_data_dict.py` (Week 2).

### Auto-save via 3 signals (no resolver action required)
The original three-signal mechanism is preserved and is the only path into the Vault.
Resolvers do not need to click anything — Mira handles everything automatically based
on what the requester does after receiving an answer. See § The three confirmation signals.

### Enhancement Proposal engine (Mira as PM)
`mira-app/pm/proposal_engine.py` — Claude analyzes patterns across task cards semantically.
No predefined templates or hardcoded rules. Mira reads the actual task card content —
what was asked, what Mira found, how resolvers answered, what signals came back — and
decides what patterns are worth surfacing and what they might mean. The proposal content
is fully AI-generated. The Product Owner sees what Claude noticed, not what a template
was filled in with.

Pre-escalation requester check-in is also added here: when Tier 2 search finds useful
findings, Mira enriches the task card and checks in with the requester before looping in
the resolver. This reduces unnecessary escalations and gives the resolver better context.

### Slack Canvas Dashboard
Replaces Block Kit App Home. `mira-app/dashboard/canvas_view.py` uses the Canvas API
(`conversations.canvases.create`, `canvases.sections.lookup`, `canvases.edit`) to render
real tables and rich text. Two sections: Requester view + Resolver/PM view.

### Notification DM to original requesters
When an Enhancement Proposal is approved and the fix ships, Mira DMs each user who
originally asked a related question. Closes the loop: their feedback drove the fix.

---

## Current build status

- ✅ Week 1, Day 1-2: Slack Bolt skeleton, intent classification, draft task card.
- ✅ Week 1, Day 3-5: VaultClient + stub mode, full card lifecycle, button handlers.
- ✅ Week 1, Day 6+: Resolution detection, Real-Time Search API, App Home Dashboard (Block Kit), clarifying question flow, bug fixes. Vault merged (Jie). Full cold-start cycle demonstrated end-to-end.
- ⏳ Week 2 (6/26–7/6): GitHub MCP + Data Dictionary MCP, DM to resolver flow, Enhancement Proposal engine skeleton. Jie: Supabase config, real Vault live.
- ⏳ Week 3 (7/6–7/9): Canvas Dashboard, Enhancement Proposal UI, integration sprint, seed data, staging deploy.
- ⏳ Week 4 (7/10–7/13): Demo recording, Devpost submission.

See `implementation-plan.md` (same folder) for the day-by-day breakdown.
