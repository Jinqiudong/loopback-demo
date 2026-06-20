# LoopBack — Design Reference

Full design background for LoopBack. Referenced from `CLAUDE.md` — read
that file first for the short version and submission requirements; this
file is the detailed reference for anything related to the actual
product mechanism.

If you're an AI reading this: treat every decision below as settled and
intentional, not open for re-litigation, unless the human explicitly asks
to revisit it.

---

## What LoopBack is

**One-liner:** Every problem your organization solves should only ever need
to be solved once.

LoopBack is a Slack-native system with two core pieces:

- **Mira** — the AI you `@` in Slack, just like a colleague. She understands
  intent, checks the Knowledge Vault, searches Slack history, and escalates
  to a human only when genuinely needed.
- **Knowledge Vault** — the growing, verified memory Mira builds from every
  conversation she and a human resolve together.

Mira does **not** sit between the requester and the resolver as a relay.
They talk directly, in the same thread, exactly as they always have. Mira's
job is to work alongside that conversation — checking for existing answers
before a human needs to get involved, and documenting what happens
afterward.

---

## Why this exists (the actual problem)

Every conversation in Slack is shaped by the person having it — subjective,
colored by context, phrasing, and how much time the person answering can
spare. The person asking just wants to be unblocked. The person answering
needs to understand what's being asked and check whether they've already
solved this before spending time explaining.

That effort — every clarification, every explanation — disappears the
moment a thread goes quiet. McKinsey data: knowledge workers spend ~20% of
their workweek re-finding information someone else already knew.

LoopBack's bet: knowledge doesn't need to be manually documented. It's
produced constantly in Slack — it just needs to be captured at the moment
it's created, verified by the person who created it, and made reusable.

---

## Core mechanism (read this before writing any resolution logic)

### The basic loop

```
User @ Mira with a question
  → Mira understands intent (semantic, not keyword matching)
  → Mira creates a task card
  → Mira checks the Knowledge Vault FIRST (cheapest, fastest check)
      → Vault has a verified answer → Mira replies instantly, done
      → Vault has no answer → Mira searches Slack history
          → History has a candidate → Mira surfaces it, may ask a
            clarifying question to confirm it's the same problem
          → Still nothing → Mira escalates: posts the task card to
            the resolver
              → Resolver replies DIRECTLY to the requester, in the
                same thread — Mira does not relay this message
              → Mira listens in the background throughout
              → Once the exchange settles, Mira documents it,
                writes a new Vault entry, and follows up with the
                requester: "did this actually resolve it?"
```

### Why Vault-first matters

Checking the Vault before searching Slack history or escalating to a human
is a deliberate cost/performance decision — it's the cheapest possible
check and should run on every single incoming question before anything
else happens.

### Why Mira never relays

This was an explicit architectural decision, not a default. Mira checking
the Vault and history is fine because that's faster than waiting on a
human. But the moment a real conversation is needed, she steps back. The
goal: escalation should never feel like talking to a bot first and a
person second. Build her as a *listener*, not a *relay*.

---

## The Resolution Cycle (status state machine)

This is the single most important piece of logic in the system. Implement
it exactly as specified — the nuances here (especially around the two
flavors of `unconfirmed`) are intentional, not arbitrary.

### Status values

```
draft           → just created, no owner yet
ai_searching    → Mira is searching Vault + Slack history (AI owns this)
human_working   → escalated, waiting on a resolver to answer in-thread
pending_confirm → an answer has been given, waiting on the requester
                  to confirm whether it actually worked
verified        → confirmed correct, no further action needed
unconfirmed      → no clear confirmation either way (see two sub-cases
                  below) — still stored, still usable, just not yet trusted
escalate        → requester said the answer was wrong; routes back to
                  human_working with a NEW resolution cycle
```

### Status → who's responsible

| status | owner | what they do |
|---|---|---|
| draft | — | just created, nobody acting yet |
| ai_searching | AI (Mira) | searches on her own, no human needed |
| human_working | resolver | answers directly in the thread |
| pending_confirm | requester (User) | needs to confirm if the answer helped |
| unconfirmed | — | no active owner, waiting for the *next* person to confirm it |
| verified | — | done, no further action |
| escalate | resolver | same handling as human_working |

### The three confirmation signals

Triggered once an answer has been given and the task card enters
`pending_confirm`. A 30-minute window opens.

**Signal 1 — Clear confirmation**
Requester explicitly confirms it worked (e.g. "thanks, that fixed it",
✅ reaction). → status becomes `verified` immediately. No friction — the
person already said what they needed to say.

**Signal 2 — Silence / ambiguous response (two sub-cases, see below)**
Silence is the *most common* real-world outcome — do not treat it as
failure. Mira follows up once after the 30-minute window. If still
unanswered (or only ambiguously answered), the entry is saved as
`unconfirmed`.

Two distinct paths into `unconfirmed`, which matter for confidence
scoring even though they display identically to the user:

- **Ambiguous reply** (e.g. "hmm, maybe?", "let me check") — the requester
  *did* respond, just not clearly. This is a weak positive signal.
  Confidence should start higher than the silent case.
- **Two rounds of silence** (no response to the original answer, then no
  response to the one follow-up either) — zero information. Confidence
  should start lower than the ambiguous case.

Both display to the user identically: **"Suggested, not yet verified"**
— never the word "unconfirmed" in user-facing copy. Calling something
"unconfirmed" makes people hesitant to try it; "Suggested" invites them to
be the one who verifies it instead.

**Signal 3 — Clear denial**
Requester explicitly says it didn't work. → routes back to `human_working`
(escalate), running the resolution cycle again. When the resolver gives a
new answer, the **old answer is not deleted** — it's pushed into
`version_history`, and the new answer becomes `current_answer`. Both AI
and humans should always be able to see exactly what changed and when.

### Confidence accumulation (the key trust mechanism)

Confidence must **never depend on a single person responding within a
time window.** It accumulates across independent users over time, the
same way trust actually builds on a real team:

```
First user → answer saved as `unconfirmed`, low confidence
Second user hits the same question (via Vault match), doesn't flag it
  as wrong → confidence rises
Enough independent positive signals accumulate → status flips to
  `verified`, even though no single person ever gave an explicit "yes"
```

This is the whole point of `unconfirmed`: it's not a dead end, it's a
suggestion waiting for the next person to validate it. Don't build a
flow where an unconfirmed answer is hidden or discarded — surface it,
just labeled honestly as not-yet-verified.

---

## Task Card behavior

The task card is a single Block Kit message that **updates in place** as
it moves through the lifecycle above — not a stream of separate bot
messages. Users should watch one card change state, not get spammed.

Every status transition should be reflected:
1. In the task card's visible state (for whoever is in the thread)
2. In `task_cards` table's `status` field (source of truth)
3. Eventually surfaced in the Knowledge Vault Dashboard's expandable
   history view (full transparency: what was searched, who was looped
   in, every state it passed through)

Verified answers should show **how long ago** they were verified — trust
should visibly decay over time even for `verified` status, since policies
and systems change. (Not yet implemented in Week 1 — flagging for later.)

---

## Data model (owned by teammate, but Mira's side needs to know the shape)

Two tables, not one. Different lifecycles, different query patterns.

### `task_cards` — short-lived, tracks one interaction

```sql
id                  uuid (PK)
requester_id        text
channel_id          text
thread_ts           text
question_raw        text
question_intent     text
status              text  -- see enum above
resolver_id         text
vault_entry_id      uuid (FK -> vault_entries.id)
search_log          jsonb
confidence_signal   text  -- signal_1 / signal_2 / signal_3
created_at          timestamp
updated_at          timestamp
```

### `vault_entries` — long-lived, reusable knowledge

```sql
id                  uuid (PK)
question_canonical  text
embedding           vector(1536)
current_answer      text
owner_id            text
status              text  -- verified / unconfirmed / outdated
confidence_score    float
usage_count         int
source_thread       text
last_confirmed_at   timestamp
version_history     jsonb[]  -- [{answer, valid_from, valid_until, changed_by, reason}]
created_at          timestamp
```

Relationship: `task_cards.vault_entry_id → vault_entries.id`. One vault
entry can be referenced by many task cards (every time it's reused).

---

## API contract between Mira and the Vault

These three functions are the **entire interface** between the two halves
of the system. Treat the shape as fixed — if it needs to change, that's a
two-person conversation, not a unilateral edit.

### `search_vault(query_text)`

```
Returns:
{
  match_found: boolean,
  entry_id: uuid | null,
  answer: string | null,
  owner_id: string | null,
  confidence: float,           // 0-1
  last_confirmed_at: string | null
}
```

Threshold guidance: confidence > 0.85 = direct match, return instantly.
0.7–0.85 = ask a clarifying question first. Below 0.7 = treat as no match.

### `upsert_vault_entry(task_card_id, answer, owner_id, signal)`

```
Input:
{
  task_card_id: uuid,
  question_canonical: string,
  answer: string,
  owner_id: string,
  signal: 'signal_1' | 'signal_2' | 'signal_3'
}

Returns:
{
  entry_id: uuid,
  status: 'verified' | 'unconfirmed' | 'outdated',
  confidence_score: float
}
```

### `update_status(task_card_id, new_status)`

```
Input: { task_card_id: uuid, new_status: string }
Returns: { success: boolean, updated_at: string }
```

---

## Naming conventions

- The AI is **Mira** — always referred to by name in code comments, UI
  copy, and docs. Never "the bot" or "TaskBridge" (old name, fully
  retired).
- The knowledge store is the **Knowledge Vault**, not "Dictionary" (old
  name, retired) and not "TaskBridge" (old name, retired).
- People are **requester** / **resolver** (or User / Owner — both used
  interchangeably across docs, pick one and be consistent within a single
  file).
- Project name: **LoopBack**.

---

## Current build status (update this section as work progresses)

- ✅ Week 1, Day 1-2: Slack Bolt skeleton, intent classification
  (question vs. noise only — no fine-grained categories yet), draft-status
  task card. Lives in `mira-app/`.
- ✅ Week 1, Day 3-5: VaultClient wrapper + stub mode; mention handler updated
  to full draft → ai_searching → pending_confirm / human_working flow;
  task card updated to render search results and Confirm / Not Helpful buttons.
  API signatures not yet locked with teammate — pending alignment meeting.
- ⏳ Week 2 (6/26–7/6): Teammate builds independently — full three-signal
  logic, confidence accumulation, version history, 30-min timer + follow-up.
- ⏳ Week 3 (7/6–7/9): Integration sprint, Dashboard (App Home), task card
  polish, seed data.
- ⏳ Week 4 (7/10–7/13): Demo recording, Devpost submission.

See `implementation-plan.md` (same `docs/implementation/` folder) for the full
day-by-day breakdown.
