# LoopBack — Demo Video Script

Total runtime: 2:50–3:00
Format: Single Slack window, full screen. No slides. Real working product only.
Roles: Jie = Business Analyst / requester · Jinqiu = Data Engineer / resolver
Voice: One narrator
Tone: Calm, human, understated. Let the product speak for itself.

---

## Pre-recording checklist

- Bot running, terminal hidden
- Slack full screen
- Notifications silenced
- Knowledge Vault empty at the beginning of Act 1
- Act 1 completed once before recording Act 2, so the Vault can return a verified result
- Canvas deleted before recording, so Mira creates a fresh one
- Jie and Jinqiu accounts ready in separate browser windows or devices
- Channel #loopback-test-env cleared or scrolled past previous test messages
- Screen recording started
- Microphone tested

---

# INTRO — 0:00–0:28

**[SCREEN]** LoopBack logo and tagline over a blurred Slack background.

Hold for two seconds, then cut to a live Slack channel.

**[SAY]**
> "Every day, someone asks a question
> their team may have already answered.
>
> The answer exists — in a resolved thread,
> from a colleague who took the time to explain it.
> But when the conversation ends,
> the context, the owner, and the proof that it worked
> disappear with it.
>
> LoopBack turns resolved conversations
> into verified organizational memory.
>
> Mira —
> an AI teammate who lives inside your workspace.
> She helps questions get answered,
> and captures every resolved conversation
> into a Knowledge Vault:
> a growing, verified memory built from real team exchanges.
>
> The next time anyone asks — Mira remembers."

**[SCREEN]** In the Slack message box, type and send:

```
/invite @Mira
```

**[SCREEN]** Slack confirms that Mira has joined the channel.

Hold for one quiet second.

---

# ACT 1 — LEARNING THE TEAM — 0:28–1:30

## A normal question

**[SCREEN]** Jie moves the cursor into the message box and begins typing.

```
Hi team, our approval rate has dropped quite a bit this week.
Has anyone seen this before or know what might be causing it?
```

**[SCREEN]** Jie sends the message.

Mira automatically look into the question,

Mira is checking:

- Knowledge Vault
- Slack history (via Real-Time Search API)
- Codebase (GitHub — Claude tool use)
- Data dictionary

## Mira begins learning

**[SCREEN]** The Task Card updates in place. Briefly show Claude's tool calls in progress — Claude autonomously deciding what to look at:

```
→ read_file("schema/raw_applications.sql")
→ read_file("schema/da_approval_metrics.sql")
→ search_slack_history("approval rate drop")
```

**[SAY]**
> "Mira is new here, too.
>
> She doesn't begin by knowing everything
> about the product or the way this team works.
>
> She begins by paying attention —
> running an agentic Claude tool-use loop:
> reading the actual SQL schema files from GitHub,
> searching your Slack history in real time via the Real-Time Search API,
> and deciding on her own what to look at next.
>
> This isn't keyword search.
> Claude is driving the investigation."

**[SCREEN]** Card transitions to Direction Check with two concise findings:

```
I found two things that may be related:

• product_type is missing from part of the incoming data
• the approval metric excludes records without that field
```

Show citations linking directly to the files Claude read:

```
raw_applications.sql  ↗
da_approval_metrics.sql  ↗
```

Then show:

```
Does this look like the right direction?
```

**[SAY]**
> "She read the actual files — and decided what mattered.
>
> But finding something relevant
> isn't the same as understanding what someone needs.
>
> So before looping anyone in,
> Mira checks with Jie first."

---

## The team helps Mira understand

**[SCREEN]** Jie replies in the same thread:

```
yes, that makes sense.
can someone from the data team confirm and fix it?
```

**[SCREEN]** The Task Card changes to human_working. A ❓ reaction appears on Jie's original message. The findings remain visible inside the card.

**[SAY]**
> "Jie confirms that Mira is looking
> in the right direction.
>
> It's a small moment, but it matters.
>
> Mira isn't only helping the team
> understand the problem.
>
> The team is also teaching Mira
> how their product and their work fit together."

---

## Jinqiu answers directly

**[SCREEN]** Switch to Jinqiu's Slack account. Jinqiu opens the thread.

Hold briefly so the viewer can see:

- Jie's original question
- Mira's findings
- The SQL filenames
- Jie's confirmation

**[SAY]**
> "So when Jinqiu steps in,
> no one has to begin from scratch."

**[SCREEN]** Jinqiu replies directly in the same thread:

```
confirmed — product_type was missing from a batch of records
after the March migration.

we added the NOT NULL constraint and completed the backfill.
the numbers should return to normal after tonight's refresh.
```

Pause for one second after the reply appears.

**[SAY]**
> "The answer still comes from Jinqiu.
>
> Mira helps them reach the conversation faster—
> and then she steps out of the way."

---

## The answer becomes knowledge

**[SCREEN]** The same Task Card changes to pending_confirm. Show:

```
Did this resolve your question?

[ Yes, resolved ]   [ Not yet ]
```

**[SAY]**
> "Because an answer isn't knowledge just because someone said it."

**[SCREEN]** Jie clicks `Yes, resolved`.

The card changes to verified. The ❓ reaction becomes ✅.

**[SCREEN — hold 3 seconds, let the viewer read every line]**

```
Verified Answer

Answered by @Jinqiu
Verified by @Jie
Confidence: 96%
View original thread
```

**[SAY]**
> "It becomes knowledge when the person who needed it
> confirms that it worked.
>
> The answer keeps its owner,
> its source,
> and the reason the team can trust it."

Pause.

**[SAY]**
> "This time, Mira was learning.
>
> Next time, she'll remember."

---

# ACT 2 — THE NEXT TIME — 1:30–2:00

**[SCREEN]** Cut to a new message in the same channel from a different requester. The requester types:

```
hey, why are approved application numbers so low this month?
it feels like something might be wrong with the data
```

**[SAY]**
> "Three days later, someone else sees the same problem.
>
> They use different words.
> They don't know Jie asked it.
> They don't know Jinqiu already solved it."

**[SCREEN]** Send the message. Within two or three seconds, Mira displays:

```
Answered from Knowledge Vault
```

Show Jinqiu's original answer and:

```
Answered by @Jinqiu
Verified by @Jie
Confidence: 96%
View original thread
```

**[NO NARRATION FOR 4–5 SECONDS]**

Do not move the cursor. Do not scroll. Let the viewer experience the speed.

**[SAY]**
> "Different words. Same problem.
>
> Mira matched the intent using semantic vector search —
> not keywords, but meaning.
>
> The answer returns in seconds.
>
> The person who solved it the first time
> never has to solve it again."

---

# ACT 3 — WHEN QUESTIONS BECOME A SIGNAL — 2:00–2:40

**[SCREEN]** Switch back to Jinqiu's account. Jinqiu types:

```
@Mira insights
```

**[SAY]**
> "One question can be an interruption.
>
> Five questions can be a signal."

**[SCREEN]** Send the command. Mira displays a period selector. Jinqiu clicks `This Month`.

Mira confirms:

```
Canvas updated — This Month
```

Open the Slack Canvas.

---

## What the team has learned

**[SCREEN]** Show the Canvas Impact section — let it breathe for 3 seconds:

```
📊 Impact — This Month

5 questions received

  ✅  1 verified — confirmed, ready to reuse
  🔔  1 unconfirmed — suggested at 68% confidence, not yet confirmed
  ❓  3 open — still needs a human
```

**[SAY]**
> "Over time, Mira can see more than individual answers.
>
> She can see what the team keeps running into—
>
> what has been resolved,
> what is still uncertain,
> and what people keep needing help with.
>
> And she tracks how confident she is in each answer.
> The ones the team hasn't confirmed yet stay flagged — until someone does."

**[SCREEN]** Scroll slowly to `Enhancement Opportunities` section in the Canvas.

---

## From repeated questions to a product insight

**[SCREEN]** Show the Enhancement Opportunities section in the Canvas — hold 3 seconds, let the viewer read:

```
🌱 Enhancement Opportunities
AI-generated from resolved questions · This Month (July 2026)

Approval rate drops lack self-serve diagnosis  ·  5 related questions
- All 5 questions this month are variations of the same concern...
- No question was resolved without human involvement...
- Suggested: Create a runbook or dashboard annotation explaining
  common causes of approval rate fluctuations...

[ Approve ]   [ Defer ]   [ Reject ]
```

**[SAY]**
> "As Mira learns how the team works,
> she also begins to notice where the work keeps breaking down.
>
> Claude reads the actual resolved task cards —
> no predefined categories, no templates —
> and generates this analysis from what it actually saw."

**[SCREEN]** Jinqiu clicks `Approve` inside the Canvas. Canvas confirms.

**[SAY]**
> "What looked like five separate support questions
> becomes one thing the product team can fix.
>
> Support work becomes product learning."

---

# CLOSING — 2:40–3:00

**[SCREEN]** Reveal the complete LoopBack cycle. Keep the diagram simple:

```
A question
    ↓
Shared context
    ↓
A direct human answer
    ↓
Verification
    ↓
Knowledge the team can reuse
    ↓
Patterns the product team can act on
    ↺
```

Let each stage illuminate slowly.

**[SAY]**
> "Teams spend nearly a full day every week
> chasing information a colleague already has.
>
> Most knowledge tools try to fix that
> by asking someone to stop working and start documenting.
>
> Nobody does."

**[SCREEN]** Show the verified answer and the approved product insight side by side.

**[SAY]**
> "LoopBack learns inside the work itself.
>
> From the questions people ask.
>
> From the context they uncover.
>
> From the answers that actually help."

**[SCREEN]** Transition to the LoopBack logo.

**[SAY]**
> "Every problem solved becomes organizational memory.
>
> Every recurring pattern becomes a product improvement."

Brief pause.

**[SAY]**
> "LoopBack."

**[SCREEN]** Final tagline:

```
Your team should never solve the same problem twice.
```

Fade to black.

---