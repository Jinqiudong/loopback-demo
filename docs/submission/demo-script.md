# LoopBack — Demo Script

**Total runtime:** under 3:00
**Roles:** Jie = BA (requester) · Jinqiu = DE + Product Owner (resolver)
**Visual device:** A loop diagram builds progressively after each act — Act 3 reveals the complete picture.

---

## High-Level Structure

| Time | Section | What it shows | Diagram state |
|------|---------|---------------|---------------|
| 0:00–0:30 | Intro | Problem + product in 30 seconds | Empty loop |
| 0:30–1:10 | Act 1 — Cold start | AI-human in a loop, Mira listens not relays | Cold start path added |
| 1:10–1:50 | Act 2 — Vault hit | Knowledge Vault payoff, semantic search | Vault shortcut path added |
| 1:50–2:40 | Act 3 — Channel Insights | Patterns → product fixes | Enhancement loop added |
| 2:40–3:00 | Closing | Complete loop revealed | Full loop |

---

## Intro (0:00–0:30)

**Goal:** Set up the problem and product in 30 seconds. No slides — use text overlay on real Slack.

**Voiceover / text on screen:**
> "Teams repeat the same questions in Slack every day.
> The answers disappear when the thread goes quiet.
> LoopBack turns every resolved conversation into organizational memory —
> and every pattern into a product fix."

Show: LoopBack logo · tagline · then cut to Slack

**Diagram:** Show the loop outline — empty, just the shape. No content yet.

---

## Act 1 — Cold start (0:30–1:10)

**What this shows:** Mira investigates autonomously, confirms direction, steps back so humans talk directly. AI-human in a loop — Mira is the listener, not the relay.

**Use case:** Approval rate anomaly — root cause is `product_type` NULL in the analytics schema.

**What gets called:**
1. `search_vault(query)` → no match
2. Claude tool use agentic loop (`investigator.py`):
   - `search_github("approval rate product_type")` → finds `da_approval_metrics.sql`
   - `read_file("schema/raw_applications.sql")` → nullable product_type
   - `read_known_issues()` → Issue #003: 40% drop, root cause identified
3. Direction check posted → Jie replies "yes" → `update_status(human_working)`
4. Jinqiu replies in thread → `update_status(pending_confirm)`
5. Jie gives ✅ → `upsert_vault_entry(signal_1)` → **Verified**

**Script:**
1. Jie: `@Mira we're seeing an unexpected drop in our approval rate this week — can you help me investigate?`
2. Card: Draft → 🔍 Searching *(Mira reads Vault, Slack history, GitHub codebase)*
3. Card → 🔎 Direction Check · Mira posts in thread:
   > *"Based on what I found: `product_type` is nullable in `raw_applications` — applications with NULL values are excluded from approval rate calculations. This matches known issue #003. Does this look like the right direction?"*
4. Jie: `yes`
5. Card → 🆕 First time this has been asked *(Mira looped in Jinqiu — with findings already visible in card)*
6. Jinqiu replies directly to Jie *(Mira stays silent — she's listening)*:
   > *"Confirmed — product_type was missing from ~18% of records after the March migration. Fix is deployed."*
7. Jie reacts ✅
8. Card → ✅ Verified Answer · source thread link

**Narration:**
> "Mira investigated the codebase autonomously, found the root cause, and confirmed the direction
> before looping anyone in. Then she stepped back. Jinqiu answered Jie directly — Mira never
> forwarded a single message. That's the key design decision: she listens, she doesn't relay."

**After Act 1 — add to diagram:** Cold start path lit up:
`Question → Mira investigates → Direction check → Human answers → ✅ Vault`

---

## Act 2 — Vault hit (1:10–1:50)

**What this shows:** Same root cause, different person, different words. Knowledge Vault returns the answer in seconds. Semantic understanding, not keyword matching.

**Use case:** Different BA, three months later, asking a semantically similar but differently worded question.

**What gets called:**
1. `search_vault("why does our data show fewer approvals")` → match found, ~77% confidence
2. Card → ⚡ Answered from Knowledge Vault
3. New BA clicks "This helped ✓" → `upsert_vault_entry(signal_1)` → confidence rises

**Script:**
1. Switch to second Slack account / different channel
2. New BA: `@Mira why does our data show fewer approvals this month?`
3. Card: Draft → ⚡ **Answered from Knowledge Vault** in ~3 seconds
4. Card shows: answer · **77% confidence** · answered by @Jinqiu · source thread link
5. New BA clicks **This helped ✓**
6. Card → ✅ Verified · confidence ticks up

**Narration:**
> "Three months later. A different BA. A completely different way of phrasing it.
> Mira recognized the intent — not the keywords — and returned a verified answer in seconds.
> The resolver was never disturbed. This is what the Vault is for."

**After Act 2 — add to diagram:** Vault shortcut path lit up:
`Question → ⚡ Vault hit → Instant answer` *(short-circuits the long path)*

---

## Act 3 — Channel Insights (1:50–2:40)

**What this shows:** Questions accumulate → Mira sees a pattern → Enhancement Opportunity.
The loop closes: support becomes product backlog.

**Use case:** Four data-quality-related questions this month, all pointing to the same schema issue.
Claude identifies the pattern and proposes a fix.

**What gets called:**
1. `@Mira insights` → time period selector
2. Jinqiu clicks **This Month** → `list_task_cards(period)` → `cluster_by_embedding()`
3. Canvas rebuilds: Knowledge / Pending / Open sections
4. Enhancement Opportunity: Claude reads task cards, generates AI-written insight
5. Jinqiu clicks **Approve**

**Script:**
1. Jinqiu: `@Mira insights`
2. Time period selector appears in channel
3. Jinqiu clicks **This Month**
4. Canvas updates — show three sections:
   - ✅ **Knowledge** — verified answers, grouped by topic
   - 💡 **Answered, Pending** — unconfirmed answers waiting for more confirmations
   - ❓ **Open Questions** — still being worked on
5. Scroll to **Enhancement Opportunity** — Claude-generated:
   > *"Four questions this month traced back to the same root cause: `product_type` is nullable in `raw_applications`. I recommend adding a NOT NULL constraint and backfilling historical records — this would prevent the recurring approval rate confusion."*
6. Jinqiu clicks **Approve**
7. Mira: *"Added to the product backlog."*

**Narration:**
> "After enough questions are resolved, Mira starts to see what they collectively reveal.
> This Enhancement Opportunity wasn't written from a template — Claude read the actual task cards
> and decided what was worth surfacing. Support becomes product backlog."

**After Act 3 — add to diagram:** Enhancement loop closed:
`Pattern detected → Enhancement Proposal → Product fix → fewer questions next time`

---

## Closing (2:40–3:00)

**Reveal the complete loop diagram** — all three paths now lit up together.

The diagram shows:
1. Cold start path: Question → investigate → human answers → Vault
2. Vault shortcut: Question → ⚡ instant answer
3. Enhancement loop: Patterns → proposal → product fix

**Voiceover:**
> "Every problem solved becomes organizational memory.
> Every pattern becomes a product fix.
> **LoopBack.**"

Fade to logo.

---

## Production notes

**Diagram design** *(needs to be built before recording):*
- Simple animated diagram — can be made in Figma, Keynote, or Excalidraw
- Shows the three paths lighting up sequentially
- Cut to updated diagram after each act (takes ~5 seconds per transition)
- Final frame: all three paths lit, LoopBack logo

**Recording format:**
- Screen recording of real Slack workspace — no staged screenshots, no slides
- App deployed to Railway (no terminal visible)
- Narration as voiceover or text overlays
- Record 2–3 takes per act, assemble best takes

---

## Pre-recording checklist

**Setup:**
- [ ] App deployed to Railway (`VAULT_STUB=false`, real Supabase)
- [ ] `GITHUB_TOKEN` set, `loopback-analytics` repo public and accessible
- [ ] `message.channels` + `app_home_opened` events subscribed in Slack API
- [ ] Two Slack accounts ready (Jie = BA, Jinqiu = DE + Product Owner)
- [ ] `investigator.py` (Claude tool use) built and tested

**Seed data:**
- [ ] 1 verified entry: the approval rate question from Act 1
- [ ] 3–4 additional data-quality task cards in the channel (for Act 3 pattern)
- [ ] Confirm Act 2 question returns ≥70% confidence Vault hit
- [ ] Confirm Enhancement Opportunity generates relevant insight for the approval rate pattern

**Loop diagram:**
- [ ] Diagram designed in Figma/Excalidraw
- [ ] Three states ready: after Act 1, after Act 2, full reveal

**Final checks:**
- [ ] Dry run — time each act, all cards update correctly
- [ ] Act 1 (including direction check) under 40 seconds
- [ ] Act 2 Vault hit visible within 5 seconds of @Mira
- [ ] Act 3 Canvas loads correctly
- [ ] Upload to YouTube/Vimeo, set to **Public**
- [ ] Share sandbox with `slackhack@salesforce.com` AND `testing@devpost.com`
