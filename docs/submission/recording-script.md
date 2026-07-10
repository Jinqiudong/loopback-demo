# LoopBack — Video Recording Script (v2)

**Total runtime:** 2:45–3:00
**Format:** Single Slack window, full screen. No slides. Real working product only.
**Roles:** Jie = BA (requester account) · Jinqiu = Data Engineer + Product Owner (resolver account)
**Voice:** One narrator. Read [SAY] lines at a calm, deliberate pace — slower than feels natural.

---

## Pre-recording checklist

- [ ] Bot running, terminal hidden (full-screen Slack)
- [ ] Vault seeded: at least one prior Act 1 run completed so Act 2 gets an instant hit
- [ ] Canvas deleted from channel (bot creates a fresh one on first insights request)
- [ ] Both accounts ready: Jie's window + Jinqiu's window (two browsers or two devices)
- [ ] Channel `#loopback-test-env` — scroll past any previous test messages
- [ ] Screen recording started, mic tested, Slack notifications silenced

---

## INTRO — 0:00 to 0:28

**[SCREEN]** LoopBack logo + tagline over a blurred Slack background, then cut to a live Slack channel

**[SAY]**
> "Knowledge workers spend nearly 20% of their workweek —
> almost a full day —
> just looking for information they or a colleague already has.
>
> It's not that teams don't have answers.
> It's that every answer lives in a thread that goes quiet.
> The next person who needs it starts from scratch.
>
> LoopBack fixes that.
> Every resolved conversation becomes organizational memory.
> Every pattern becomes a product fix."

---

## ACT 1 — Cold Start — 0:28 to 1:15

**[SCREEN]** Jie's Slack window, `#loopback-test-env` channel — empty thread, normal view

**[SAY]**
> "This is a cold start. The Knowledge Vault is empty.
> No one has answered this before.
> Jie is a business analyst — she posts a normal message. No commands. No @Mira."

**[JIE TYPES & SENDS]**
```
Hi team, our approval rate has been looking weird this week, it's dropped quite a bit
has anyone seen this before or know what might be causing it?
```

**[SCREEN]** Mira appears in the thread automatically. Card: "🔍 Searching Knowledge Vault + Slack history + codebase..."

**[SAY]**
> "Mira detects the question on her own.
> Vault is empty — so she goes deeper.
> She reads the actual SQL schema files using Claude tool use."

**[SCREEN]** Card transitions to "🔎 Direction Check" — two bullet points appear, citing specific field names and file names (`raw_applications.sql`, `da_approval_metrics.sql`)

**[SAY]**
> "She found two likely causes in the schema.
> Before looping anyone in — she checks with Jie first."

**[JIE TYPES & SENDS]** *(in thread reply)*
```
yes that makes sense! can someone from the data team confirm and fix this?
```

**[SCREEN]** Card → "🆕 First time this has been asked" · ❓ emoji appears on Jie's original message

**[SAY]**
> "Jie confirms. The ❓ signals the data team.
> Jinqiu sees the card — Mira's findings already assembled inside it."

**[JINQIU TYPES & SENDS]** *(directly in the same thread, to Jie)*
```
confirmed — product_type was missing from a batch of records after the March migration.
we've added the NOT NULL constraint and the backfill is done.
numbers should be back to normal in the next refresh cycle (tonight) 👍
```

**[SCREEN]** Card → "💬 Answer found — does this help?"

**[SAY]**
> "Jinqiu answered Jie directly.
> Mira never forwarded a single message."

**[JIE CLICKS]** "Yes, resolved ✓" on the card

**[SCREEN]** Card → "✅ Verified Answer" · ✅ emoji on original message · "answered by @Jinqiu · View original thread"

**[SAY]**
> "Knowledge is captured at the exact moment it's born —
> with the owner's name, the source thread, and the confidence score attached.
> The cold start is done. The Vault just learned something."

---

## ACT 2 — Vault Hit — 1:15 to 1:50

**[SCREEN]** New message appears in the channel — different account, different phrasing

**[SAY]**
> "Three days later. A different person.
> They don't know Jie already asked this.
> They don't know Jinqiu already answered it."

**[JIE / NEW BA TYPES & SENDS]**
```
hey quick question — why are our approved application numbers so low this month?
feels like something's off with the data
```

**[SCREEN]** Card appears in ~2–3 seconds: "⚡ Answered from Knowledge Vault"
Displays: Jinqiu's answer · confidence % · "answered by @Jinqiu" · "View original thread"

**[SAY]**
> "Mira matched the intent — not the keywords.
> Completely different phrasing. Same question.
> Jinqiu's answer, in under three seconds."

*(hold on screen 4–5 seconds — let the card speak)*

**[SAY]**
> "The resolver who solved this three days ago
> will never have to solve it again."

---

## ACT 3 — Channel Insights — 1:50 to 2:40

**[SCREEN]** Jinqiu's account — normal channel view

**[SAY]**
> "After questions accumulate, Mira goes further.
> She looks across all of them — not just what was asked,
> but what the pattern reveals."

**[JINQIU TYPES & SENDS]**
```
@Mira insights
```

**[SCREEN]** Period selector appears in channel

**[JINQIU CLICKS]** "This Month"

**[SCREEN]** "✅ Canvas updated — This Month (July 2026)" · Canvas opens

*(pause — let viewer read the Canvas sections: 📊 Impact, 🧠 Knowledge Vault, 🌱 Enhancement Opportunities)*

**[SAY]**
> "The Canvas shows what happened this month —
> what's resolved, what's still open, what's been verified."

**[SCREEN]** Scroll Canvas to show 🌱 Enhancement Opportunities section · Chat notification appears: "🌱 Enhancement Opportunity identified — see Canvas · [Approve] [Defer] [Reject]"

**[SAY]**
> "And then this.
>
> Claude read every task card from this period.
> No template. No predefined categories.
> It decided what mattered — based on what it actually saw."

**[JINQIU CLICKS]** "Approve"

**[SCREEN]** Mira: "Added to the product backlog."

**[SAY]**
> "Five questions about approval rate drops.
> One AI-written product insight.
> Support work just became product work."

---

## CLOSING — 2:40 to 3:00

**[SCREEN]** Full loop diagram — all three paths lit up simultaneously

**[SAY]**
> "Slack AI finds where the conversation happened.
> Guru and Tettra ask someone to become a librarian.
> LoopBack captures knowledge at the exact moment it's born —
> from the conversation that already happened,
> from the resolver who already answered,
> verified by the person who needed it.
>
> Every problem solved becomes organizational memory.
> Every pattern becomes a product fix.
>
> LoopBack."

**[SCREEN]** Logo · tagline · fade to black

---

## Timing reference

| Timestamp | Beat |
|-----------|------|
| 0:00 | Logo over blurred Slack |
| 0:05 | "Knowledge workers spend..." |
| 0:22 | "LoopBack fixes that." |
| 0:28 | Cut to Slack · Jie types |
| 0:35 | Message sent |
| 0:40 | Mira appears in thread · card animates |
| 0:50 | Direction Check card visible — hold 2s |
| 1:00 | Jie replies |
| 1:04 | ❓ emoji · card → human_working |
| 1:07 | Jinqiu's reply sent |
| 1:12 | Jie clicks "Yes, resolved ✓" |
| 1:14 | ✅ card · "captured at the exact moment it's born" |
| 1:18 | Cut to Act 2 |
| 1:23 | Second question sent |
| 1:26 | Vault hit card appears — hold 5s |
| 1:38 | "The resolver who solved this..." |
| 1:45 | *(brief pause)* |
| 1:50 | Cut to Act 3 |
| 1:55 | `@Mira insights` sent |
| 2:00 | Click This Month · Canvas updates |
| 2:08 | Read Canvas (Impact + KV sections) |
| 2:18 | Scroll to Enhancement Opportunities |
| 2:22 | Chat notification appears |
| 2:28 | "Claude read every task card..." |
| 2:34 | Jinqiu clicks Approve |
| 2:37 | "Added to the product backlog." |
| 2:40 | Loop diagram reveal |
| 2:46 | "Slack AI finds where..." |
| 2:57 | "LoopBack." |
| 3:00 | Fade out |

---

## Delivery notes

- **The Act 2 pause is the punchline.** Don't narrate over the vault hit card appearing. Let it sit for 4–5 seconds before saying anything. Speed is what sells this — let the viewer feel it.
- **"Mira never forwarded a single message"** — say this right after Jinqiu replies, before Jie clicks confirm. It's the hardest architectural decision in the build and the biggest differentiator from every other Slack bot.
- **Act 3 Canvas** — don't rush. Show the Impact section (stats) for 3 seconds, then scroll to Enhancement Opportunities. Give viewers time to read the AI-generated text before narrating over it.
- **The closing comparison** is the only place you name competitors — say it fast, one breath, then land on "LoopBack." cleanly with a full stop.
- **One take is fine.** Clean and real beats polished and over-rehearsed.
