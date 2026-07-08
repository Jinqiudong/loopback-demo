# LoopBack — Demo Script

**Total runtime:** under 3:00
**Roles:** Jie = BA (requester) · Jinqiu = DE + Product Owner (resolver)
**Visual device:** A loop diagram builds progressively after each act — closing shot reveals the complete picture.

---

## High-Level Structure

| Time | Section | What it shows | Diagram state |
|------|---------|---------------|---------------|
| 0:00–0:30 | Intro | Problem + product in 30 seconds | Empty loop |
| 0:30–0:50 | Ambient moment | Mira captures knowledge without @mention | — |
| 0:50–1:25 | Act 1 — Cold start | AI-human in a loop, GitHub investigation | Cold start path added |
| 1:25–2:00 | Act 2 — Vault hit | Knowledge Vault payoff, semantic search | Vault shortcut path added |
| 2:00–2:45 | Act 3 — Channel Insights | Patterns → product fixes | Enhancement loop added |
| 2:45–3:00 | Closing | Complete loop revealed | Full loop |

**One story:** A data team's recurring approval rate confusion — discovered, resolved, saved automatically, never asked again, turned into a product fix.

---

## Intro (0:00–0:30)

No slides. Text overlay on real Slack or voiceover.

> "Teams repeat the same questions in Slack every day.
> The answers disappear when the thread goes quiet.
> LoopBack turns every resolved conversation into organizational memory —
> and every pattern into a product fix."

Show: LoopBack logo · tagline · cut to Slack

---

## Ambient moment (0:30–0:50)

**What this shows:** Mira captures knowledge from a normal conversation — no @mention needed.

**Exact messages:**

Jie posts (no @Mira, just a regular channel message):
```
why is the approval data showing lower numbers this morning?
```

Jinqiu replies in thread:
```
NULL values in the product_type field are being excluded from the approval rate calculation. Use WHERE product_type IS NOT NULL when you query da_approval_metrics to get accurate numbers for now.
```

Jie replies:
```
got it, thanks!
```

Mira appears automatically in the thread:
> *"Looks like this was resolved! Want me to save it to the Knowledge Vault?"*
> **[Save it ✓]** [No thanks]

Jie clicks **Save it ✓** → Mira: *"Saved to the Knowledge Vault ✓"*

**Narration:**
> "LoopBack doesn't require your team to change their workflow.
> Mira watches in the background — when a question gets resolved, she asks if it's worth saving.
> No @mention. No extra steps."

---

## Act 1 — Cold start (0:50–1:25)

**What this shows:** Mira investigates the codebase autonomously, confirms direction before escalating, then steps back. AI-human in a loop — Mira listens, never relays.

**Exact messages:**

Jie types:
```
@Mira we're seeing an unexpected drop in our approval rate this week — can you help me investigate?
```

Card: Draft → 🔍 Searching *(Mira reads Vault, searches GitHub codebase and Slack history)*

Card → 🔎 **Direction Check** · Mira posts in thread:
> *"Based on what I found: `product_type` is nullable in `raw_applications` — applications with NULL product_type are excluded from approval rate calculations. This matches known issue #003 in your analytics repo. Does this look like the right direction?"*

Jie replies:
```
yes
```

Card → 🆕 **First time this has been asked** *(findings visible in card, Jinqiu looped in)*

Jinqiu replies directly to Jie in thread *(Mira stays silent)*:
```
Confirmed — product_type was missing from ~18% of records after the March 12 schema migration. The NOT NULL constraint has been added and the backfill is complete. Your numbers should normalize in the next 24-hour refresh cycle.
```

Jie reacts ✅ → Card → **✅ Verified Answer** · source thread link visible

**Narration:**
> "Mira investigated the codebase autonomously, found the root cause, and confirmed direction
> before looping anyone in. Then she stepped back completely.
> Jinqiu answered Jie directly — Mira never forwarded a single message."

---

## Act 2 — Vault hit (1:25–2:00)

**What this shows:** Same root cause, different person, different words, instant answer. Semantic understanding — not keyword matching. Resolver never disturbed.

**Exact messages:**

New BA (second account or different channel):
```
@Mira why does our data show fewer approvals this month?
```

Card: Draft → ⚡ **Answered from Knowledge Vault** *(appears in ~3 seconds)*

Card shows:
- Answer text
- **77% confidence**
- answered by @Jinqiu
- source thread link

New BA clicks **This helped ✓** → Card → ✅ Verified · confidence ticks up

**Narration:**
> "Three months later. A different BA. A completely different way of phrasing it.
> Mira recognized the intent — not the keywords — and returned a verified answer in seconds.
> The resolver was never disturbed."

---

## Act 3 — Channel Insights (2:00–2:45)

**What this shows:** Accumulated questions surface as a pattern. Mira generates an AI-written Enhancement Opportunity. Support becomes product backlog.

**Exact messages:**

Jinqiu types:
```
@Mira insights
```

Time period selector appears → Jinqiu clicks **This Month**

Canvas updates — show three sections:
- ✅ **Knowledge** — verified answers, grouped by topic
- 💡 **Answered, Pending** — unconfirmed, waiting for more confirmations
- ❓ **Open Questions** — still being worked on

Scroll to **Enhancement Opportunity** (Claude-generated from actual task cards):
> *"Four questions this month traced back to the same root cause: `product_type` is nullable
> in `raw_applications`. I recommend adding a NOT NULL constraint and backfilling historical
> records — this would prevent the recurring approval rate confusion."*

Jinqiu clicks **Approve** → Mira: *"Added to the product backlog."*

**Narration:**
> "After enough questions are resolved, Mira starts to see what they collectively reveal.
> This wasn't written from a template — Claude read the actual task cards and decided what
> was worth surfacing. Support becomes product backlog."

---

## Closing (2:45–3:00)

Reveal the complete loop diagram — all paths lit up.

> *"Every problem solved becomes organizational memory.*
> *Every pattern becomes a product fix.*
> **LoopBack.**"

Fade to logo.

---

## Before you test / record

**Scope:** Run ambient + Act 1 first to seed data. Act 2 only works after Act 1 creates a verified Vault entry. Act 3 needs 3-5 task cards in the channel.

**Recommended test order:**
1. Run ambient moment (no @Mira, casual conversation, save it)
2. Run Act 1 twice with different approval-rate questions to build task cards
3. Test Act 2 with the exact wording above
4. Test Act 3: `@Mira insights` → This Month → check Canvas has content → `@Mira analyze`
5. Do a full dry run timing each section

**Scopes needed in Slack app:**
- `channels:history` — ambient detection reads thread history
- `canvases:write` — Channel Insights Canvas
- `message.channels` event subscribed
- `app_home_opened` event subscribed

**Environment:**
- `VAULT_STUB=false`, real Supabase connected
- `GITHUB_TOKEN` set, `loopback-analytics` repo public
- `SLACK_USER_TOKEN` set (for Real-Time Search API)
- App on Railway before recording (no terminal visible)

**Loop diagram files needed:**
- Excalidraw: https://excalidraw.com/#json=6aOyvnQyQ9se8Lbt24sof,p81gkch2FgQ3U97Ij7g3AA
- Export 3 PNGs: act1 (blue path) · act2 (blue+green) · full reveal

**Final submission:**
- [ ] Video uploaded to YouTube/Vimeo, set to **Public**
- [ ] Sandbox URL shared with `slackhack@salesforce.com` AND `testing@devpost.com`
- [ ] Devpost page complete before July 13, 5pm PT
