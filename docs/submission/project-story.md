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

LoopBack is built around three things working together: Mira — the AI colleague you `@`
in Slack, the Knowledge Vault — the growing verified memory she builds from every resolved
conversation, and her PM identity — the ability to look across all of those conversations
and surface what they collectively reveal about the product.

**[Diagram 1: LoopBack Mechanism Loop — placeholder]**

When someone asks a question, Mira doesn't search keywords — she understands intent first.
She works through three tiers, always in the same order.

**Tier 1 — Knowledge Vault.** The fastest and cheapest check. If a verified answer exists,
Mira returns it instantly with the original owner's name, a confidence score, and a
timestamp. The person who solved it the first time is never disturbed again.

**Tier 2 — Parallel search across three sources.** If the Vault has no answer, Mira
searches simultaneously: Slack's history (via the Real-Time Search API), your codebase
(via GitHub MCP), and your data dictionary (via Data Dictionary MCP). She reads the actual
SQL files, schema definitions, and field ownership documentation — not keywords. When she
finds something relevant, she enriches the task card with her findings and checks in with
the requester: *"Based on what I found, does this look like the right direction?"* Only
after the requester confirms does she loop in the resolver — with full context already
assembled. This prevents unnecessary escalations and ensures resolvers start from
understanding, not from scratch.

**Tier 3 — Human escalation.** If neither the Vault nor Tier 2 search yields anything,
Mira escalates: posting the task card to a resolver, who replies directly to the requester
in the same thread. Mira listens in the background. She never relays.

Once an answer is given, Mira's three-signal mechanism captures what happens next.
A clear confirmation immediately verifies the answer. Silence — the most common outcome
in real workplace conversations — triggers a gentle follow-up; if still unanswered, the
answer is saved as "Suggested, not yet verified," waiting for the next person to be the
first to confirm it. A clear denial routes back to the resolver, with the old answer
preserved in version history so nothing is ever silently overwritten.

Every verified answer becomes a Knowledge Vault entry. Every entry carries the full trail:
the original question, what Mira searched, who answered, and every signal that built the
trust score. The next time anyone asks — even in completely different words — Mira
recognizes the intent and returns the answer in seconds.

**The PM identity.** After enough questions accumulate, Mira goes further. She analyzes
the patterns across resolved task cards — not what was most commonly asked, but what
the pattern of questions reveals about the underlying product. She generates Enhancement
Proposals: AI-written insights about what keeps recurring and why, surfaced in the
Knowledge Vault Dashboard for Product Owners to review and act on.

**[Diagram 2: Resolution Cycle — placeholder]**

---

## How we built it

LoopBack runs on Slack's Bolt framework for Python, deployed on Railway.
All three required technologies are used as first-class components, not checkboxes.

**Claude** powers everything that requires real understanding: intent classification,
synthesising Tier 2 search findings into concise bullet points for the task card,
generating the confirmation question Mira asks before looping in a resolver, and
writing Enhancement Proposals from Knowledge Vault patterns. The answer that goes into
the Vault is always the resolver's original words — not an AI paraphrase.

**Slack's Real-Time Search API** is Mira's second knowledge source. When the Vault has
no answer, Mira searches the workspace's entire message history for relevant conversations
and surfaces the most useful result with a link back to the original thread.

**GitHub MCP and Data Dictionary MCP** extend Mira's reach into the codebase. When a
question touches a data anomaly, a schema issue, or a field definition, Mira reads the
actual SQL files and field ownership documentation from your analytics repo. She finds
root causes, not just keywords. The same principle applies to the Data Dictionary: Mira
reads what each field means, who owns it, and what it's required for — and brings that
context directly into the task card before a human is ever looped in.

**[Diagram 3: Task Card by Stage — placeholder]**

The task card is a single Block Kit message that mutates in place through seven states.
No new messages, no notification spam — the same card changes as the situation changes.
When Mira finds something in Tier 2 search, the card updates to show her findings and
asks the requester to confirm direction. When a resolver answers, the card captures their
words and surfaces them for confirmation. When the answer is verified, the card reflects
that trust permanently.

The Knowledge Vault Dashboard lives in Slack Canvas — not a web page, not a sidebar,
but a rich Slack-native document that updates as entries are written. Every entry shows
its confidence score, owner, usage count, and the full resolution trail behind it. The
Enhancement Proposal section gives Product Owners a structured view of what Mira has
noticed across all resolved questions, with one-click approve / defer / reject actions.
We chose Canvas specifically because a dashboard that requires leaving Slack is a
dashboard that doesn't get used.

**[Diagram 4: Knowledge Vault Dashboard — placeholder]**

One architectural decision mattered more than any single API call: Mira never relays.
She searches because that's faster than waiting on a human. But the moment a real
conversation is needed, she steps back entirely. The requester and resolver talk directly,
in the same thread, exactly as they would without Mira. This was a hard constraint, not
a default — and enforcing it required more careful state machine design than anything
else in the build.

The full resolution cycle — cold start through Enhancement Proposal — is implemented
and demonstrated end-to-end. The build is split between Mira's conversational layer and
the Knowledge Vault's storage and retrieval layer, developed in parallel against a fixed
four-function API contract.

---

## Challenges we ran into

**Designing a trust model that doesn't break under real human behavior.**
The easy version of confirmation is a thumbs-up button in a 30-minute window.
The problem is that most people don't respond to bots after their question is
answered — they got what they needed and moved on. If silence equals failure,
the Vault never fills. We had to design a system where silence is a weak
positive signal, not a negative one, and where trust accumulates across
independent encounters over time rather than depending on any single person
responding in any single window.

**Knowing when not to get involved.**
Every Slack bot's failure mode is becoming a wall between people. We had to
make an explicit architectural commitment — not just a stated preference —
that Mira never relays messages between the requester and the resolver. The
moment a real conversation is needed, she steps back and lets it happen
directly. Enforcing that as a hard constraint, rather than a soft guideline,
turned out to require more careful state machine design than we expected.

**Locking an API contract across two people building in parallel.**
The Knowledge Vault's storage and retrieval logic and Mira's conversational
layer were built simultaneously by two people on separate schedules — including
a period when one of us was traveling and genuinely unreachable. The only thing
that kept the two sides from diverging was agreeing on an exact three-function
interface before the independent build window opened, and treating that contract
as fixed: any change required a conversation, not a unilateral edit.

**The cold start problem — and why we chose not to solve it with fake data.**
An empty Vault is correct behavior. Pre-seeding with unverified answers would
undermine the core premise: every piece of knowledge in the Vault has provenance,
a trail back to a real conversation, a real person who answered, and a real signal
that the answer worked. Instead, the cold start is part of the demo — the first
run shows the full resolution cycle, and the second identical question shows the
Vault returning an answer in seconds. The cold start is the story, not a problem
to hide.

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
