# LoopBack — Implementation Plan

Slack Agent Builder Challenge · Deadline: July 13, 2026, 5pm PT

---

## Ownership

| Area | Owner | Scope |
|------|-------|-------|
| Mira (conversational layer) | jinqiu.dong@capitalone.com | Slack Bolt app, intent classification, task card (Block Kit), resolution detection |
| Knowledge Vault storage + mechanism | valerianyang2020@gmail.com / j.yang1@wustl.edu | Schema, embeddings, semantic search, confidence scoring, version history, status state machine backend |
| Knowledge Vault Dashboard | Together | App Home UI, entry display, version timeline view |
| Integration, demo, submission | Together | Merge, test, record, submit |

The interface between Mira and the Vault is a fixed API contract — three functions, defined once,
**locked by 6/22**. As long as both sides honor it, each person can build independently without
blocking the other.

---

## Timeline at a Glance

| Dates | Phase | Who's active | Goal |
|-------|-------|-------------|------|
| 6/20 – 6/22 | Foundations + contract lock-in | Both, daily | Skeletons built, API contract locked |
| 6/23 – 6/25 | Parallel build + final sync | Both | Each side functional, one real integration test before travel |
| 6/26 – 7/6 | Independent build window | Jie only (Jinqiu OOO) | Vault mechanism fully built: signals, confidence, versioning |
| 7/6 – 7/9 | Integration sprint | Both | Merge, debug, Dashboard wired up, seed data, staging deploy |
| 7/10 – 7/12 | Demo + submission prep | Both | Video recorded, Devpost page complete, sandbox tested |
| 7/13 | Submit | Both | Submitted with buffer before 5pm PT |

> **The single highest-risk point in this plan is 6/22.** If the API contract isn't locked by then,
> the 6/26–7/6 independent window doesn't work — Jie would be guessing at an interface instead of
> building against a fixed one.

---

## Detailed Tasks

### Week 1 — 6/20 to 6/26: Foundations & Contract Lock-in

#### Day 1–2 (6/20–6/21) — Jinqiu: Mira skeleton
- [x] Slack Bolt app set up, responds to @ mentions
- [x] Intent classification via Claude API: question vs. noise
- [x] Draft task card Block Kit template (draft status only)

#### Day 1–2 (6/20–6/21) — Jie: Vault skeleton
- [ ] Create Supabase project, enable pgvector extension
- [ ] Run CREATE TABLE statements for `task_cards` and `vault_entries`
- [ ] Draft the API contract: `search_vault`, `upsert_vault_entry`, `update_status`

#### Day 3 (6/22) — Both: Lock the interface
- [ ] Walk through all three API functions together, line by line
- [ ] Agree on exact status enum spelling — typos here break everything downstream
- [ ] Run one mock end-to-end test using fake data on both sides

> 📅 Calendar: "LoopBack: API Contract Lock-in Meeting" — 6/22, 10:00–11:30 AM ET

#### Day 4–5 (6/23–6/25) — Jinqiu
- [x] Wire up Vault-priority query logic (against stub API)
- [ ] No match → Slack history search
- [ ] Still no match → escalate to resolver, task card status switches

#### Day 4–5 (6/23–6/24) — Jie
- [ ] Embedding pipeline working end-to-end
- [ ] `search_vault` implemented with cosine similarity
- [ ] Test semantic search accuracy on 5–10 sample question pairs (different wording, same intent)

#### Day 6 (6/25) — Both: Real integration test
- [ ] Run a full path against the real Supabase instance, not mocks
- [ ] Confirm Jinqiu's side correctly reads Vault's real API responses

> 📅 Calendar: "LoopBack: Real Integration Test" — 6/25, 5:00–6:00 PM ET (last sync before travel)

**Week 1 done means:** API contract locked, both sides can work independently, one full (if rough)
path has run successfully at least once.

---

### Week 2 — 6/26 to 7/6: Independent Build Window

Jinqiu is traveling and not actively working this window. Jie builds independently against the
locked contract — no blocking dependency on Jinqiu during this period.

#### Jie — Knowledge Vault mechanism
- [ ] Full three-signal logic inside `upsert_vault_entry`:
  - [ ] signal_1 (clear confirmation) → `verified`
  - [ ] signal_2 (two-tier: ambiguous reply vs. second silence) → `unconfirmed`, with different starting confidence
  - [ ] signal_3 (denial) → `escalate`, old answer pushed to `version_history`, new answer overwrites display
- [ ] Confidence accumulation logic: independent confirmations from different users raise confidence over time, not dependent on a single person responding in a window
- [ ] 30-minute timer + one follow-up + second-silence fallback (cron job or delayed task queue)
- [ ] `version_history` push-on-update logic implemented and tested
- [ ] Write unit tests against the API contract so Jinqiu can verify against them on return

> **Simplification fallback:** if signal_2's two-tier logic is taking too long, ship signal_1 and
> signal_3 fully first, treat everything else as a single "unconfirmed, low confidence" bucket,
> and refine in Week 3 if time allows.

> 📅 Calendar: "LoopBack: Independent Build Window" — 6/26–7/6, all-day block on Jie's calendar

---

### Week 3 — 7/6 to 7/9: Integration Sprint

#### Day 1 (7/6) — Both: Merge & debug
- [ ] Pull Jie's 10 days of progress, run a full integration test
- [ ] Resolve any interface mismatches (field names, response formats) from independent work
- [ ] Confirm full loop end-to-end: first question → escalate → resolver answers → three-signal judgment → written to Vault → second identical question → instant Verified Answer

> 📅 Calendar: "LoopBack: Integration Sprint Kickoff" — 7/6, 6:00–7:00 PM ET

#### Day 2 (7/7) — Jinqiu: Dashboard
- [ ] App Home Dashboard UI (Block Kit)
- [ ] Entry list: question, answer, status badge, owner, confidence, usage count
- [ ] Expand-to-view full task card history per entry
- [ ] Version timeline display for outdated/updated entries

#### Day 3 (7/8) — Both: Task card polish + clarification
- [ ] Task card visual polish across every stage (draft → ai_searching → human_working → pending_confirm → verified/unconfirmed)
- [ ] Clarifying question mechanism for the 0.7–0.85 confidence band
- [ ] Seed 15–20 real Verified Answer entries covering the demo scenarios

#### Day 4 (7/9) — Both: Bug fixes + staging
- [ ] Handle edge cases: bot restarts, Slack API rate limits
- [ ] Deploy to Railway, test against a real Slack workspace
- [ ] Have someone unfamiliar with the project try it, collect first-round feedback

---

### Week 4 — 7/10 to 7/13: Demo + Submission

#### 7/10 (Fri) — Demo recording
- [ ] Write demo script following the Inspiration → What it does narrative arc
- [ ] Two Slack accounts: Jinqiu plays User, Jie plays resolver
- [ ] Record 2–3 takes, pick the best, keep under 3 minutes
- [ ] Set video to Public

> 📅 Calendar: "LoopBack: Demo Recording Day" — 7/10, 1:00–5:00 PM ET

#### 7/11 (Sat) — Devpost page
- [ ] Elevator pitch
- [ ] Project Story (with all 4 diagrams embedded) — draft in `docs/submission/project-story.md`
- [ ] Architecture diagram
- [ ] Built With: MCP, RTS API, Slack AI, Claude, Supabase
- [ ] Screenshots at 3:2 ratio, at least 3 (task card stages + dashboard)
- [ ] GitHub repo README cleanup

> 📅 Calendar: "LoopBack: Devpost Page + Submission Materials" — 7/11, 10:00 AM–6:00 PM ET

#### 7/12 (Sun) — Sandbox + final testing
- [ ] Sandbox URL ready
- [ ] Share with `testing@devpost.com` + `slackhack@salesforce.com`
- [ ] Final bug check

> 📅 Calendar: "LoopBack: Sandbox + Final Testing" — 7/12, 10:00 AM–4:00 PM ET

#### 7/13 (Mon) — Submit
- [ ] Full checklist review
- [ ] Submit before 5pm PT — do not wait until the last minute

> 📅 🚨 "LoopBack Devpost SUBMISSION DEADLINE (5pm PT)" — reminders at 1 day, 2 hours, 30 minutes before

---

## Risks

| Risk | Mitigation |
|------|-----------|
| Contract not locked by 6/22 | Highest priority — do not let this meeting slip |
| Three-signal + confidence logic more complex than expected | Simplify: ship signal_1 + signal_3 first, defer signal_2 nuance |
| Only 4 days after return before demo recording starts | Dashboard/UI polish is the first thing to cut — the core resolution loop must work |
