# Project Story (Devpost Submission Draft)

This is the working draft for the "Project Story" section of the Devpost
submission (Inspiration / What it does / How we built it / Challenges /
Accomplishments / What we learned / What's next). Edit freely as the
build progresses — this is the living source of truth that gets copied
into the actual Devpost form before the 7/13 deadline.

Diagram placeholders below correspond to the diagrams referenced in
`docs/DESIGN.md` and `ARCHITECTURE.md`. Once final diagram images exist,
drop them in `docs/diagrams/` and update the placeholder links.

---

## Inspiration

Every conversation in Slack is shaped by the person having it. The way
someone asks a question, the way someone else answers it — it's all
subjective, colored by how much context each side already has, how
clearly the question is phrased, how much time the person answering can
spare in that moment. Two people can ask the exact same thing in
completely different words. Two people can answer the exact same
question with completely different depth, completely different framing.

The person asking has one need above all: get an answer fast enough to
keep moving. They don't always know whether their question is brand new
or something the team already solved — they just know they're blocked.
The person answering has a different need entirely. They want to
understand what's actually being asked, often clarifying it once or
twice, and they want to know — before spending the time to explain —
whether this is something they've already walked someone through before.
Multiply that across every conversation happening in a workspace, and
you get two sides with different needs, talking past each other through
the same subjective layer.

This is where Mira comes in — an AI that sits alongside the person
asking and the person answering, helping both sides align. She clarifies
intent so the question is actually understood. She checks whether this
problem has already been solved, so the owner isn't starting from
scratch. She helps the person asking get unblocked faster, and helps the
person answering spend their time only on what's genuinely new.

But every one of these conversations — every clarification, every
explanation, every moment someone gives their time to unblock someone
else — is effort. And right now, that effort disappears the moment the
thread goes quiet. According to McKinsey, knowledge workers spend nearly
20% of their workweek — almost a full day — just looking for information
or tracking down a colleague who can help. That's not a fringe
inefficiency. That's a fifth of the workweek spent re-finding what
someone else already knew.

Every resolved conversation deserves to be remembered, verified, and
made available the next time someone needs it. That belief became the
Knowledge Vault — the place where all of that effort, once spent, never
has to be spent the same way again.

That's what LoopBack is built to do.

---

## What it does

LoopBack is built around two things working together: Mira, an AI
teammate you @ in Slack just like a colleague, and the Knowledge Vault,
the growing memory Mira builds from every conversation she and a human
resolve together. Mira doesn't sit between the requester and the
resolver — they can talk to each other directly, exactly as they always
have. What she does is work alongside that conversation, stepping in
only where she can actually help.

**[Diagram 1: LoopBack Mechanism Loop — placeholder]**

When someone asks a question, Mira doesn't search keywords — she
understands intent first. She checks the Knowledge Vault for a verified
answer. If one exists, she returns it instantly, with the original
owner's name, a confidence score, and a timestamp, and the person who
solved it the first time is never disturbed again. If nothing exists
yet, she searches Slack's history for anything close, summarizes what
she finds, and asks a clarifying question if needed to confirm it's
actually the same problem. If there's truly nothing to go on — a cold
start — she escalates: posting the task card to the resolver, who
replies directly to the requester in the same thread, with Mira
listening in the background, watching how the question gets resolved,
taking notes, and following up with the requester to see if the issue
is resolved, the conversation can be ended, and the knowledge can be
verified and made ready for the next requester.

Once an answer is given, whether pulled from history or worked out fresh
with a resolver — Mira checks back in. She asks the person who asked the
question whether it actually worked. A clear yes becomes a verified
answer right away. Silence triggers a gentle follow-up; if it's still
unconfirmed after that, the answer gets saved anyway, offered to the
next person as a suggestion rather than a fact, waiting for someone to
be the first to confirm it. A clear no sends the question back to the
resolver, and whatever they resolve becomes the new answer — with the
old one preserved in a version history, so nothing is ever silently
overwritten.

Every verified answer becomes a card in the Knowledge Vault: the
question, the answer, who owns it, when it was last confirmed, and how
confident the system is that it still holds. The next time someone asks
— even in completely different words — Mira recognizes the intent and
returns the answer in seconds.

---

## How we built it

LoopBack runs on Slack's Bolt framework for Python, deployed on Railway.
Claude powers everything that requires real understanding — intent
classification, generating clarifying questions, and extracting an
answer in the resolver's own words rather than an AI paraphrase. For
semantic search, we use OpenAI's text-embedding-3-small to generate
embeddings, stored in Supabase with pgvector, so Mira can recognize when
two differently worded questions mean the same thing. Slack's
Real-Time Search API connects Mira to existing Slack history when the
Vault doesn't have an answer yet.

Every UI surface in LoopBack is built with Slack's own Block Kit — no
external frontend, nothing for people to install or open elsewhere. The
task card itself is a Block Kit message that updates in place as it
moves through its lifecycle: draft, searching, waiting on a resolver,
pending confirmation, verified. People watch the same card change state
rather than receiving a stream of separate bot messages. The Knowledge
Vault Dashboard takes that further, living in App Home — every entry
renders as a card with its current answer, trust status, owner, and
usage count, and tapping into it expands the full task card history
behind it: what was searched, who was looped in, and every state it
passed through. We built it this way deliberately — the dashboard had to
live where the work already happens, or people simply wouldn't open it.

One architectural decision mattered more than any single API call: Mira
never relays messages between the requester and the resolver. She checks
the Vault and Slack history because that's cheaper and faster than
waiting on a human, but the moment a real conversation is needed, she
steps back and lets it happen directly. We built her listening
capability — not a relay capability — specifically so escalation never
feels like talking to a bot first and a person second.

The harder problem wasn't the AI call — it was designing how a system
earns the right to tell someone "this answer is trustworthy." Diagram 2:
Resolution Cycle illustrates the full resolution cycle and verification
mechanism, modeled on how people actually behave rather than how we
wished they'd behave. Diagram 3: Task Card by Stage shows what that
mechanism looks like in practice — every stage made visible, so the path
to an answer is never a black box.

**[Diagram 2: Resolution Cycle — placeholder]**
**[Diagram 3: Task Card by Stage — placeholder]**

A clear confirmation verifies an answer immediately. Silence — the most
common outcome in real workplace conversations — isn't treated as
failure; Mira follows up once, and if it's still unanswered, the entry
is saved as "Suggested, not yet verified" rather than buried. We chose
that wording deliberately: calling something "unconfirmed" makes people
hesitant to try it, so we designed the language to invite verification
instead of implying it's broken. Confidence accumulates across users
over time instead of depending on one person responding in a window —
the same way trust actually builds on a real team. A clear denial routes
back to the resolver, and the new answer overwrites the old one in
display while keeping a full version history underneath, so nothing is
ever silently lost.

All of this — every status, every confirmation, every version —
surfaces in one place: the Knowledge Vault Dashboard. It's not a
separate tool; it lives inside Slack. Every entry shows its current
answer alongside its trust level, its owner, and how many people it's
already helped, and it can be expanded to reveal the entire history
behind it — the original question, what was searched, who was looped
in, and every state the task card passed through to get there. We
designed it this way on purpose: a knowledge base that only shows the
final answer asks people to trust it blindly. One that shows its work
earns that trust instead.

**[Diagram 4: Knowledge Vault Dashboard — placeholder]**

Week 1 of implementation is complete. On Mira's side: a Slack Bolt app
listening for `@Mira` mentions, Claude-powered intent classification
(question vs. noise), a live-updating Block Kit task card, and a
`VaultClient` layer that moves the card through its full lifecycle —
draft, searching, and either surfacing a suggested answer with Confirm /
Not Helpful buttons, or flagging the question for a human teammate. The
build split is working: Mira's conversational layer and the Knowledge
Vault's storage layer are being developed in parallel against a fixed
three-function API contract, with stub mode keeping Mira runnable
before the real Vault package is connected.

---

## Challenges we ran into

*(Update as the build progresses — this section should reflect what
actually happened, not what we expected to happen.)*

- TBD: interface contract negotiation between the two services
- TBD: anything that came up during the independent build window
- TBD: integration sprint surprises

---

## Accomplishments that we're proud of

*(Update as the build progresses.)*

- Designed a verification mechanism where trust doesn't depend on a
  single point of failure — it accumulates across independent users,
  the way real organizational trust actually works
- Designed the system so escalation to a human never feels like talking
  to a bot first — Mira listens, she doesn't relay
- TBD: anything else worth highlighting once built

---

## What we learned

*(Update as the build progresses.)*

---

## What's next for LoopBack

The Knowledge Vault doesn't just store what was solved. Over time, it
could store how the organization thinks — the dimensions considered,
the sequence followed, the judgment calls made when a problem doesn't
fit a known category. As the Vault grows, Mira could learn what
clarifying questions an expert always asks before they even show up —
so by the time a human is needed, the problem is already half-diagnosed.

That's not in scope for this submission, but it's the direction the
underlying mechanism points toward.

---

## Reference: Elevator pitch (for the Devpost tagline field)

> Meet Mira, your AI teammate — she listens, learns, and builds a
> Knowledge Vault from every resolved conversation, so your team never
> solves the same problem twice.

## Reference: Market positioning (for talking points / FAQ prep)

| | Slack AI | Guru / Tettra | LoopBack |
|---|---|---|---|
| Finds answers | ✓ | ✓ | ✓ |
| Verifies answers | ✗ | Manual | Auto |
| Owner accountable | ✗ | Sometimes | Always |
| Zero maintenance | ✓ | ✗ | ✓ |
| Intent clustering | ✗ | ✗ | ✓ |
| Clarification assist | ✗ | ✗ | ✓ |

Slack AI finds where the conversation happened. It returns messages —
noise with signal buried inside. Guru and Tettra assume someone will
stop working and become a librarian. LoopBack doesn't ask anyone to
document more — it captures knowledge at the exact moment it's born.
