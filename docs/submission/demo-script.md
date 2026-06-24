# LoopBack — Demo Script

3-minute demo video. Two Slack accounts: Jie plays the BA (requester), Jinqiu plays the DE / Product Owner (resolver).
Demo scenario: approval rate anomaly — a real data product issue Mira investigates using GitHub MCP.

---

## Act 1 — Cold start (~75s)
*Mira searches the Vault, reads the codebase, surfaces the root cause.*

**Goal:** Show the full investigation → direction check → resolution cycle.

1. Jie (as BA): `@Mira we're seeing an unexpected drop in our approval rate this week — can you help me investigate?`
2. Show card: Draft → **Searching** (ai_searching — "Searching Vault + Slack + codebase...")
3. Card updates to **direction_check** — Mira posts her findings in the thread:
   > *"Based on what I found: `product_type` is nullable in `raw_applications` — applications with NULL product_type are excluded from the approval rate calculation. This matches the known issue #003 in your analytics repo. Does this look like the right direction?"*
4. Jie replies: **"yes"**
5. Card transitions to **human_working** — findings visible in card, Jinqiu looped in
6. Jinqiu (as DE): replies directly to Jie in thread:
   > *"Confirmed — product_type was missing from 18% of records after the March migration. Fix is in progress."*
   *(Mira stays silent — she's listening, not relaying)*
7. Jie reacts ✅ — signal 1
8. Card updates to **Verified ✓**

**Narration beat:** "Mira didn't just escalate — she investigated first. She read your actual SQL
schema, found the root cause in the data dictionary, and confirmed the direction before
looping anyone in. The resolver started from understanding, not from scratch."

---

## Act 2 — Vault hit (~30s)
*Same root cause, new person, instant answer.*

**Goal:** Show the payoff. Mira recognises the intent even in different words.

1. Switch to a second Slack account (new BA, three months later)
2. New BA: `@Mira why is my approval data showing low numbers?`
3. Show card: Draft → Searching → **pending_confirm** in ~3 seconds
4. Card shows: ⚡ *Answered from Knowledge Vault* — confidence score, original owner (@Jinqiu), verified date
5. New BA clicks **This helped ✓**
6. Card: **Verified ✓** — confidence score ticks up

**Narration beat:** "Three months later, a different BA asks the same question in different words.
Jie is never disturbed. The answer is there, with full provenance."

---

## Act 3 — PM identity (~30s)
*Patterns become product proposals.*

**Goal:** Show Mira's third role — surfacing product insights from accumulated knowledge.

1. Jinqiu (as Product Owner): `@Mira analyze`
   *(Switch to Jinqiu's account)*
2. Mira posts an **Enhancement Proposal** card in the channel:
   - What she observed across the task cards
   - What it might mean for the product
   - Suggested next step
   - Source links to the original questions
   - [Approve] [Defer] [Reject] buttons
3. Jinqiu clicks **Approve**
4. Mira acknowledges: *"Adding to the product backlog."*

**Narration beat:** "Every resolved question teaches Mira something. Enough questions,
and she starts to see what they collectively reveal — not just answers, but product gaps."

---

## Closing line (~15s)

> "LoopBack doesn't ask your team to document more.
> Every problem solved becomes organisational memory.
> Every pattern becomes a product fix."

---

## Checklist before recording

- [ ] `loopback-analytics` repo public and accessible (GitHub MCP reads it)
- [ ] `GITHUB_TOKEN` set in `.env` with `contents: read` on `loopback-analytics`
- [ ] `VAULT_STUB=false`, real Supabase connected, schema.sql run
- [ ] 3–5 seed entries in Vault so Act 3 has patterns to analyse
- [ ] Two Slack accounts ready — BA account and DE account
- [ ] App deployed to Railway (not running locally — no terminal visible in recording)
- [ ] `message.channels` event subscribed in Slack API settings
- [ ] Record 2–3 takes, keep cleanest one under 3:00
- [ ] Set video to Public before submitting
