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
- [x] Create Supabase project, enable pgvector extension
- [x] Run CREATE TABLE statements for `task_cards` and `vault_entries`
- [x] Draft the API contract: `create_task_card`, `search_vault`, `upsert_vault_entry`, `update_status`

#### Day 3 (6/22) — Both: Lock the interface
- [x] Walk through all four API functions together, line by line
- [x] Agree on exact status enum spelling
- [x] Merged feature/jie-vault-foundation into dev1-taskcard, conflicts resolved

#### Day 4–5 (6/23–6/25) — Jinqiu
- [x] Full 3-tier search: Vault → Slack history + GitHub MCP → human escalation
- [x] Slack Real-Time Search API integrated
- [x] GitHub MCP integrated (reads loopback-analytics repo)
- [x] Pre-escalation direction check (direction_handler.py)
- [x] Resolution detection (resolution_handler.py)
- [x] All 7 task card states + direction_check state
- [x] Enhancement Proposal engine (@Mira analyze)

#### Day 4–5 (6/23–6/24) — Jie
- [x] Embedding pipeline working end-to-end
- [x] `search_vault` implemented with cosine similarity (pgvector)
- [x] Full knowledge_vault package merged and integrated

#### Integration — Both
- [x] Full cold-start cycle demonstrated end-to-end in Slack
- [x] Vault merge complete, API signatures aligned
- [ ] VAULT_STUB=false + real Supabase connected (Jie provides credentials)
- [ ] Real integration test with live Supabase

**Week 1–2 done means:** Full flow working end-to-end in stub mode, Vault code complete,
real Supabase connection pending credentials handoff.

---

### Week 2 — 6/26 to 7/6: Independent Build Window ✅ COMPLETE

#### Jie — Vault + Canvas (loopback-3 branch)
- [x] Full three-signal logic (signal_1/2/3)
- [x] Confidence accumulation (Python-side cosine similarity, not pgvector RPC)
- [x] version_history push-on-update (signal_3)
- [x] source_thread tracking on vault entries
- [x] Channel Insights Canvas (`dashboard/channel_canvas.py`) — @Mira insights trigger
- [x] Three Canvas sections: ✅ Knowledge / 💡 Pending / ❓ Open, with semantic clustering
- [x] Time period buttons (This Month / Quarter / Year)
- [x] Enhancement Opportunity integrated into Canvas
- [x] Task card redesign — header block, question not repeated, source thread link
- [x] Supabase live (VAULT_STUB=false, real embeddings working)
- [x] Full cold-start cycle demonstrated end-to-end in real Slack workspace

#### Jinqiu (loopback-2 / loopback-3)
- [x] GitHub MCP (mcp_github.py) — REST API to loopback-analytics, finds root causes
- [x] Direction check handler (resolution_handler.py unified)
- [x] Enhancement Proposal engine (@Mira analyze, Claude-powered)
- [x] loopback-analytics repo with realistic SQL + data dictionary + known issues
- [x] GITHUB_TOKEN configured, GitHub MCP live in production

---

### Week 3 — 7/6 to 7/13: Polish + Demo + Submission
*(Today is 7/2. 11 days to deadline.)*

#### Must-do before recording (7/3–7/9)

- [ ] **Railway deployment** — switch Socket Mode → HTTP mode, deploy mira-app
- [ ] **MCP claim fix** — either wire real MCP protocol (stdio/HTTP) OR remove MCP from required tech claims and rely solely on Real-Time Search API (already confirmed working). Do NOT submit claiming MCP if it's REST API — technical judges will flag it.
- [ ] **Verify button → vault write end-to-end** — confirm action_handler.py "Yes resolved ✓" / "Not quite" buttons correctly call upsert_entry with signal_1/signal_3
- [ ] **Seed 5–10 vault entries** for demo so Act 2 (Vault hit) is reliable
- [ ] **Share sandbox** with `slackhack@salesforce.com` and `testing@devpost.com` — do this early, don't leave for last minute
- [ ] **Devpost page draft** — project story, architecture diagram, built-with tags
- [ ] *(nice-to-have)* Proactive proposal trigger after N resolved cards in a channel

#### Demo recording (7/10)
- [ ] Rehearse 3-act script — Act 1 (cold start + MCP finds root cause + direction check), Act 2 (Vault hit), Act 3 (Canvas + Enhancement Proposal)
- [ ] **First 60 seconds must be the strongest** — judges evaluate this hardest (official guidance)
- [ ] Jie plays BA (asks question, replies yes, gives ✅), Jinqiu plays DE (answers in thread), Jinqiu plays Product Owner (approves proposal)
- [ ] Record 2–3 takes, keep cleanest one under 3:00
- [ ] Upload to YouTube/Vimeo, set to Public

#### Devpost submission (7/11–7/12)
- [ ] Final project story copy (update docs/submission/project-story.md)
- [ ] Screenshots: task card at each major state + Canvas view (3:2 ratio, at least 3)
- [ ] Built With: Real-Time Search API, Claude (Anthropic), Supabase, Slack Canvas API, Slack Bolt
- [ ] GitHub repo public + clean README
- [ ] Double-check sandbox access for judges

#### 7/13 — Submit by 5pm PT
- [ ] Full checklist review
- [ ] Submit with buffer — do not wait until the last minute
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
