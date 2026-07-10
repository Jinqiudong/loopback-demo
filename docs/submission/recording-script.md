# LoopBack — Video Recording Script (v2)

**Total runtime:** 2:45–3:00
**Format:** Split-screen or single Slack window. No slides. Real working product only.
**Roles:** Jie = BA (requester account) · Jinqiu = Data Engineer + Product Owner (resolver account)
**Voice:** One narrator (either of you, or voiceover). Read the [SAY] lines at a calm, confident pace.

---

## Pre-recording checklist

- [ ] Bot running, terminal hidden (full-screen Slack)
- [ ] Vault seeded from at least one prior Act 1 run (so Act 2 gets an instant hit)
- [ ] Canvas deleted from channel (so bot creates a fresh one)
- [ ] Logged into both Jie and Jinqiu accounts (two browser windows or two devices)
- [ ] Channel: `#loopback-test-env`, all previous test messages cleared or scrolled past
- [ ] Screen recording started, mic tested

---

## INTRO — 0:00 to 0:28

**[SCREEN]** LoopBack logo + tagline, then cut to Slack channel

**[SAY]**
> "Every data team repeats the same questions in Slack.
> Someone asks why the numbers look off. Someone answers.
> The thread goes quiet. Two weeks later — someone asks again.
>
> LoopBack fixes that.
> Every resolved conversation becomes organizational memory.
> Every pattern becomes a product fix.
> And your team does none of the extra work."

---

## ACT 1 — Cold Start — 0:28 to 1:15

**[SCREEN]** Jie's Slack window, `#loopback-test-env` channel

**[SAY]**
> "Jie is a business analyst. She's noticed something wrong with the approval rate data.
> She posts a question — just a normal message. No bot commands. No @Mira."

**[JIE TYPES & SENDS]**
```
Hi team, our approval rate has been looking weird this week, it's dropped quite a bit
has anyone seen this before or know what might be causing it?
```

**[SCREEN]** Mira appears in thread automatically. Card: "🔍 Searching Knowledge Vault + Slack history + codebase..."

**[SAY]**
> "Mira detects the question automatically and starts investigating —
> reading your actual SQL schema using Claude tool use."

**[SCREEN]** Card transitions to "🔎 Direction Check". Mira's findings appear — two bullet points referencing `raw_applications.sql` and `da_approval_metrics.sql` with specific field names.

**[SAY]**
> "Mira read the schema files directly and surfaced two specific causes.
> Before looping anyone in, it asks Jie to confirm the direction."

**[JIE TYPES & SENDS]** *(in thread)*
```
yes that makes sense! can someone from the data team confirm and fix this?
```

**[SCREEN]** Card transitions to "🆕 First time this has been asked". ❓ emoji appears on Jie's original message.

**[SAY]**
> "Jie confirms. Mira escalates — the ❓ emoji signals the data team.
> Jinqiu sees the card with Mira's findings already assembled."

**[JINQIU TYPES & SENDS]** *(in same thread, directly to Jie)*
```
confirmed — product_type was missing from a batch of records after the March migration.
we've added the NOT NULL constraint and the backfill is done.
numbers should be back to normal in the next refresh cycle (tonight) 👍
```

**[SCREEN]** Card transitions to "💬 Answer found — does this help?"

**[SAY]**
> "Jinqiu answered Jie directly. Mira never forwarded a single message."

**[JIE CLICKS]** "Yes, resolved ✓" button on the card

**[SCREEN]** Card → "✅ Verified Answer" · ✅ emoji on original message · source thread link visible

**[SAY]**
> "Jie confirms. The answer is saved to the Knowledge Vault automatically.
> Next time anyone asks — Mira handles it."

---

## ACT 2 — Vault Hit — 1:15 to 1:50

**[SCREEN]** Switch to a second account (or scroll to show a new message in the channel)

**[SAY]**
> "Three days later. Different person. Different words. Same underlying question."

**[JIE (second account) TYPES & SENDS]**
```
hey quick question — why are our approved application numbers so low this month?
feels like something's off with the data
```

**[SCREEN]** Card appears in ~2–3 seconds: "⚡ Answered from Knowledge Vault"
Shows: Jinqiu's answer · confidence % · "answered by @Jinqiu" · "View original thread"

**[SAY]**
> "Mira matched the intent — not the keywords.
> Jinqiu's answer from three days ago, surfaced in under three seconds.
> Jinqiu was never notified. Never disturbed."

*(pause 2 seconds — let the card speak for itself)*

---

## ACT 3 — Channel Insights — 1:50 to 2:40

**[SCREEN]** Switch to Jinqiu's account

**[SAY]**
> "After questions accumulate, Mira starts to see what they reveal collectively."

**[JINQIU TYPES & SENDS]**
```
@Mira insights
```

**[SCREEN]** Period selector appears

**[JINQIU CLICKS]** "This Month"

**[SCREEN]** "✅ Canvas updated — This Month (July 2026)"
Canvas opens — four sections visible:
- 📊 Impact (total questions, breakdown)
- 🧠 Knowledge Vault (verified entries with thread links)
- 🔔 Unanswered
- 🌱 Enhancement Opportunities (AI-generated, visible at bottom)

**[SAY]**
> "The Canvas shows everything that happened this month —
> what's resolved, what's still open, and what's been learned."

**[SCREEN]** Scroll to show 🌱 Enhancement Opportunities section in Canvas

**[SAY]**
> "And then this."

**[SCREEN]** Chat notification appears: "🌱 Enhancement Opportunity identified — see Canvas · [Approve] [Defer] [Reject]"

**[SAY]**
> "Claude read every task card from this period and wrote this itself.
> No template. No categories. It decided what was worth surfacing
> based on what it actually saw."

**[JINQIU CLICKS]** "Approve"

**[SCREEN]** Mira: "Added to the product backlog."

**[SAY]**
> "Support work just became product work."

---

## CLOSING — 2:40 to 3:00

**[SCREEN]** Full loop diagram — all three paths lit up

**[SAY]**
> "LoopBack closes the loop that Slack leaves open.
> Questions get investigated. Answers get remembered.
> Patterns become fixes.
>
> Every problem solved becomes organizational memory.
> Every pattern becomes a product fix.
>
> LoopBack."

**[SCREEN]** Logo · fade out

---

## Timing reference

| Timestamp | Beat |
|-----------|------|
| 0:00 | Logo / tagline |
| 0:10 | "Every data team repeats..." |
| 0:28 | Jie types first message |
| 0:38 | Mira appears in thread, card animates |
| 0:50 | Direction Check card visible |
| 1:00 | Jie replies "yes that makes sense" |
| 1:05 | ❓ emoji · card transitions |
| 1:08 | Jinqiu replies |
| 1:13 | Jie clicks "Yes, resolved ✓" → ✅ |
| 1:15 | Cut to Act 2 |
| 1:20 | Second question sent |
| 1:24 | Vault hit card appears |
| 1:35 | Pause on card |
| 1:50 | Cut to Act 3 |
| 1:55 | `@Mira insights` sent |
| 2:00 | Period selector · click This Month |
| 2:05 | Canvas updates |
| 2:15 | Scroll to show Enhancement Opportunities |
| 2:22 | Chat notification appears |
| 2:30 | Jinqiu clicks Approve |
| 2:35 | "Added to the product backlog." |
| 2:40 | Loop diagram reveal |
| 2:50 | Closing line |
| 3:00 | Fade out |

---

## Notes for recording

- **Pace the [SAY] lines** — read slower than feels natural. Judges re-watch at normal speed.
- **Don't explain what's on screen** — narration should add context, not describe the UI. Let Mira's cards do the talking.
- **Act 2 pause** — the 10-second pause after the vault hit card appears is intentional. The speed is the point.
- **Act 3** — show the Canvas content for at least 5 seconds before scrolling. Let viewers read the sections.
- **One take is fine** — this is a hackathon, not a product launch. Clean and real beats polished and scripted.
