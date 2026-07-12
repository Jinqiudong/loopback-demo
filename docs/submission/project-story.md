# Project Story (Devpost Submission Draft)

This is the working draft for the "Project Story" section of the Devpost
submission (Inspiration / What it does / How we built it / Challenges /
Accomplishments / What we learned / What's next). Edit freely as the
build progresses — this is the living source of truth that gets copied
into the actual Devpost form before the 7/13 deadline.

---

## Inspiration

In Slack, valuable knowledge is created every day, but most of it disappears as soon as the thread goes quiet.

Someone asks a question because they are blocked. Someone else answers because they have the context. Sometimes the answer comes after a quick clarification. Sometimes it comes from a teammate who has solved the same issue before. Either way, once the conversation ends, that effort is usually trapped in a thread — hard to find, hard to trust, and easy to repeat.

That repetition is what inspired LoopBack.

We kept seeing the same pattern: the same questions resurfacing in different words, the same people being interrupted for answers they had already given, and useful explanations getting buried before they could become shared knowledge. According to McKinsey, knowledge workers spend nearly 20% of their workweek — almost a full day — just looking for information or tracking down a colleague who can help. The problem was not that teams lacked answers. The problem was that resolved answers were not becoming reusable memory.

We also realized that the most trustworthy workplace knowledge often starts with humans, not AI. It comes from the people who know the context, the requester who confirms whether an answer worked, and the owner who can verify whether it should be trusted. So instead of building an AI that replaces those people, we built LoopBack to preserve and compound what they already know. LoopBack combines AI with product mechanisms designed around how workplace knowledge is created, validated, and maintained — helping teams turn everyday conversations into reliable, reusable knowledge that grows stronger over time.

At the center of LoopBack is Mira, an AI teammate in Slack that helps turn resolved conversations into reusable knowledge. Sometimes Mira is invited directly when someone needs help. Other times, a useful exchange happens naturally: one person asks, another person answers, and Mira can lightly ask whether that answer should be saved. In both cases, humans remain the source of truth.

And once enough of those conversations accumulate, they reveal something bigger than any single answer: patterns. Repeated questions are not just support load. They are signals that something in the product, documentation, policy, or process may need to be fixed.

Every solved problem should become organizational memory. Every recurring pattern should point to what the team can improve next. That is the idea behind LoopBack.

---

## What it does

LoopBack turns resolved Slack conversations into reusable, human-confirmed knowledge, and turns repeated questions into signals for what the team should improve next.

It is built around two things working together: Mira, an AI teammate in Slack, and the Knowledge Vault, the growing memory created from resolved team conversations. Mira does not sit between the requester and the resolver. People can still talk to each other directly, exactly as they always have. Mira's role is to help useful human answers stop disappearing.

**[Diagram 1: LoopBack Mechanism Loop — placeholder]**

Mira can enter the loop in two ways. In the explicit flow, someone @mentions Mira when they need help finding, clarifying, or routing an answer. In the ambient capture flow, Mira can lightly nudge when a normal Slack thread appears to contain a useful question-and-answer exchange, asking whether it should be saved. In both cases, humans remain the source of truth.

Most knowledge tools require someone to maintain them manually: writing entries, keeping them current, deciding what is worth saving, and updating stale documentation. LoopBack works differently — it captures knowledge from conversations your team is already having, with human feedback and verification built into the process.

When someone asks Mira a question, she works through three tiers, always in the same order.

**Tier 1 — Knowledge Vault.** Mira embeds the question and searches for a semantically matching verified answer. If one exists above the confidence threshold, she returns it instantly with the answer, the original resolver's name, a confidence score, and a link back to the source thread. The person who solved it does not need to be interrupted again for the same question.

**Tier 2 — Contextual investigation.** If the Vault has no reliable match, Mira searches across available team context — Slack conversation history via the Real-Time Search API, your codebase via GitHub, and a team data dictionary. Claude drives this step as an agentic tool-use loop: it autonomously decides which tools to call, reads the actual files and messages, synthesizes what it finds, and checks in with the requester before looping in anyone else. Only after the requester confirms direction does Mira escalate — with full context already assembled.

**Tier 3 — Human escalation.** If neither the Vault nor Tier 2 yields a reliable answer, Mira creates a task card for the right resolver. The resolver replies directly to the requester in the same Slack thread. Mira never relays messages between them — when a real conversation is needed, it happens directly.

The task card is the main workflow surface. Built with Block Kit, it updates in place through seven states: draft → ai_searching → direction_check → human_working → pending_confirm → verified → escalate. No notification spam — the same card changes as the situation changes.

LoopBack separates suggested, confirmed, and verified knowledge. A suggested entry means Mira or the team identified a potentially useful answer. A confirmed answer means the requester indicated that it worked. A verified answer means the resolver or knowledge owner has confirmed it is safe to reuse. Confidence increases as the answer is successfully reused across independent conversations. If a better answer replaces an old one, LoopBack preserves the previous version in version history instead of silently overwriting it.

After enough questions accumulate, Mira goes further. She analyzes the patterns across resolved task cards — not what was most commonly asked, but what the pattern of questions reveals about the underlying product or process. She surfaces these as Enhancement Opportunities in the Channel Insights Canvas: a live Slack-native view of what the team has been asking, what has been resolved, what remains uncertain, and what keeps recurring — structured for the people who can fix the root cause.

**[Diagram 2: Resolution Cycle — placeholder]**

---

## How we built it

LoopBack is built as a Slack-native application using Slack's Bolt framework for Python, deployed on Railway. The entire experience happens inside Slack: users can @Mira in a thread, interact with task cards through Block Kit buttons, review resolved answers, and generate Channel Insights directly in a Slack Canvas without opening a separate frontend.

**Claude** is the reasoning layer throughout. It handles intent classification, the Tier 2 agentic investigation loop (autonomously deciding which tools to call and what to read), direction confirmation before escalation, and Enhancement Opportunity generation from accumulated task cards. The answer that goes into the Vault is always the resolver's original words — not an AI paraphrase.

**Slack's Real-Time Search API** is Mira's second knowledge source. When the Vault has no answer, Mira searches the workspace's entire message history for relevant conversations and surfaces the most useful result with a link back to the original thread.

**GitHub MCP via Claude tool use** extends Mira's reach into the codebase. When a question touches a data anomaly, schema issue, or field definition, Claude autonomously calls `read_file` and `search_github` tools to read the actual SQL files and schema definitions — not keywords. The same principle applies to the Data Dictionary. This is the MCP pattern: Claude drives the investigation, not scripted Python.

**The Knowledge Vault** is backed by Supabase with pgvector. Questions are embedded using OpenAI's `text-embedding-3-small` and compared via cosine similarity in Python. Each entry stores the resolved answer, source thread permalink, resolver, owner, status, confidence score, usage count, timestamps, and version history.

**The trust model** was the hardest design problem. We did not want the Vault to become a pile of AI-generated answers with unclear reliability. LoopBack's three-signal mechanism determines how trust accumulates: a clear requester confirmation (Signal 1) immediately verifies the answer at 0.90 confidence. Silence (Signal 2) saves a suggested answer at lower confidence — because in real workplaces, most people don't respond to bots after their question is answered, and silence should be a weak positive signal, not a failure. A clear denial (Signal 3) routes back to the resolver, with the old answer preserved in version history. Confidence increases by 0.05 with each independent reuse, and answers that cross 0.85 auto-verify without requiring any single person to take action.

**The Channel Insights Canvas** renders inside Slack using the Canvas API. It shows a live breakdown of questions by status, verified Knowledge Vault entries grouped by topic using cosine-similarity clustering, and AI-generated Enhancement Opportunities from Claude's analysis of actual task card content — not predefined templates.

One architectural decision mattered more than any single API call: Mira never relays. She searches because that's faster than waiting on a human. But the moment a real conversation is needed, she steps back entirely. Enforcing that as a hard constraint — not a soft guideline — required more careful state machine design than anything else in the build.

The hardest part was not just connecting Slack, Supabase, OpenAI, Claude, and GitHub. It was designing a loop where AI helps with understanding, retrieval, summarization, and pattern detection, while humans remain responsible for the knowledge itself. LoopBack uses AI to make workplace knowledge easier to find and maintain, but trust comes from the people who created, used, and verified the answer.

**[Diagram 3: Task Card by Stage — placeholder]**

---

## Challenges we ran into

**Designing a trust model that doesn't break under real human behavior.**
The easy version of confirmation is a thumbs-up button in a 30-minute window. The problem is that most people don't respond to bots after their question is answered — they got what they needed and moved on. If silence equals failure, the Vault never fills. We had to design a system where silence is a weak positive signal, not a negative one, and where trust accumulates across independent encounters over time rather than depending on any single person responding in any single window. Getting that distinction between suggested, confirmed, and verified knowledge right became one of the most important parts of the product.

**Knowing when not to get involved.**
Every Slack bot's failure mode is becoming a wall between people. We made an explicit architectural commitment — not just a stated preference — that Mira never relays messages between the requester and the resolver. The moment a real conversation is needed, she steps back and lets it happen directly. Enforcing that as a hard constraint required more careful state machine design than we expected. We also had to make the ambient capture flow intentionally lightweight: Mira only nudges once per thread, and she asks before saving anything.

**How messy real Slack conversations actually are.**
People do not usually say "this answer has resolved my issue." They say things like "got it," "makes sense," "thanks," or they say nothing at all. Sometimes a reply looks positive but does not actually mean the problem is solved. That made resolution detection harder than expected. We had to design Mira to read these signals carefully but avoid overclaiming — when the signal is not strong enough, the answer stays suggested rather than being treated as verified knowledge.

**Locking an API contract across two people building in parallel.**
The Knowledge Vault's storage and retrieval logic and Mira's conversational layer were built simultaneously by two people on separate schedules — including a period when one of us was traveling and genuinely unreachable. The only thing that kept the two sides from diverging was agreeing on an exact four-function interface before the independent build window opened, and treating that contract as fixed: any change required a conversation, not a unilateral edit.

**Claude Tag launching mid-build.**
Midway through the project, Slack's Claude Tag feature launched, bringing an AI teammate natively into Slack. That pushed us to sharpen what makes LoopBack different. LoopBack is not a general-purpose AI teammate. It is focused on a narrower problem: turning resolved human conversations into reusable organizational memory, and using repeated questions to surface where documentation, processes, or product experience need to improve. The competition clarified the positioning rather than undermining it.

**The cold start — and why we chose not to solve it with fake data.**
An empty Vault is correct behavior. Pre-seeding with unverified answers would undermine the core premise: every piece of knowledge in the Vault has provenance, a trail back to a real conversation, a real person who answered, and a real signal that the answer worked. The cold start is part of the story, not a problem to hide.

---

## Accomplishments that we're proud of

We are proud that LoopBack became more than a Slack bot. It closes the full knowledge loop: a question gets asked, an answer is found or resolved, the answer is confirmed or verified, and the result becomes reusable knowledge for the next person who needs it.

We are especially proud that LoopBack offers a lightweight approach to workspace knowledge management. Most knowledge systems ask teams to do extra work: write documentation, maintain a wiki, tag entries, or decide what should be saved after the fact. LoopBack works closer to how teams already communicate — capturing knowledge from conversations that are already happening in Slack, without asking people to change their workflow.

That mattered because conversations are one of the hardest forms of knowledge to preserve — and one of the most valuable. A conversation is not just where knowledge is exchanged; it is often where knowledge is created. Someone asks because they are blocked. Someone else answers because they have context. Through that back-and-forth, the answer that emerges is grounded in context, shaped by the people who needed it, and immediately tied to the work it helped move forward. LoopBack gives that knowledge a second life.

We are also proud of the trust model we built. Instead of treating every captured answer as automatically correct, LoopBack separates suggested, confirmed, and verified knowledge. AI helps identify, structure, and retrieve knowledge, but humans remain the source of truth through requester feedback, resolver input, and owner verification.

We designed a verification mechanism where trust doesn't depend on a single point of failure — it accumulates across independent users, the way real organizational trust actually works. And we designed the system so escalation to a human never feels like talking to a bot first — Mira listens, she doesn't relay.

Finally, we are proud that LoopBack does not stop at answering repeated questions. As resolved conversations accumulate, it turns repeated questions into Enhancement Opportunities, helping channel owners and product owners see where documentation, process, policy, or product experience may need to improve. Support work becomes product learning.

---

## What we learned

We learned that the most valuable workplace knowledge often does not begin as documentation. It begins as a conversation.

Someone asks because they are blocked. Someone else answers because they have context. Through that exchange, the answer becomes clearer, more specific, and more useful than a generic document would have been. That changed how we thought about knowledge management: the goal is not just to store information, but to preserve the context in which useful knowledge is created.

We also learned that people have to be at the center of the product design. LoopBack is not just about what AI can answer. It is about how requesters, resolvers, owners, and channel leads already work together. Each person plays a different role in making knowledge useful and trustworthy. Mira's job is not to replace those roles, but to support them: helping people find answers faster, preserve what they already know, and decide what should be trusted by others.

We learned that good AI tools should adapt to existing workflows rather than add another place for people to manage knowledge. Teams already ask, answer, clarify, and resolve things in Slack. LoopBack became stronger when we designed around those behaviors — through @Mira when help is intentional, and through lightweight capture when useful knowledge appears naturally.

Finally, we learned that repeated questions are not only interruptions. They are signals. If different people keep asking the same thing in different ways, the issue may not be the people asking. It may be unclear documentation, a confusing process, a missing product affordance, or a policy that is hard to understand. That is why LoopBack does not stop at answering questions — it also turns repeated questions into opportunities to improve the system around them.

---

## What's next for LoopBack

**Stronger trust and ownership workflows.**
LoopBack already separates suggested, confirmed, and verified knowledge, but in a real team, knowledge changes over time. We want to add owner workflows so each Knowledge Vault entry can be reviewed, approved, updated, or marked as stale by the right person — ensuring the Vault stays trustworthy as products, policies, and processes change.

**Better Vault management.**
As more conversations are captured, similar questions may create duplicate entries, old answers may become outdated, and two answers may conflict. A future version would help owners merge duplicates, detect stale answers, flag conflicting information, and turn suggested answers into cleaner canonical knowledge.

**Channel-level controls.**
Not every Slack channel should feed into LoopBack. We want to add allowlists, blocklists, owner settings, and smarter channel filters so teams can decide which spaces should contribute to the Knowledge Vault — and Mira can understand where she should stay quiet.

**Smarter ambient capture.**
Some of the most valuable knowledge happens when no one remembers to @Mira. We want Mira to become better at deciding when a thread is likely to contain reusable knowledge, when to nudge, and when to leave the conversation alone.

**More actionable Enhancement Opportunities.**
Today, LoopBack can surface repeated questions as signals. Next, we want to help teams understand what those signals mean: whether the root cause is unclear documentation, a confusing process, a missing product feature, or policy ambiguity. We also want to recommend owners, generate draft improvement proposals, and track whether repeated questions decrease after a fix is made.

**Multi-channel knowledge scoping.**
The right model is layered: channel-scoped knowledge first, with the ability to promote an answer to organization-wide scope after it has been independently verified across multiple channels. This prevents cross-department knowledge contamination while preserving the value of genuinely universal answers — and opens the door to Mira understanding her context: knowing she is in a data team's channel, not an HR channel, and adjusting her behavior accordingly.

---

## Reference: Elevator pitch

> Meet Mira, your AI teammate in Slack — she listens, learns, and builds a
> Knowledge Vault from every resolved conversation, so your team never
> solves the same problem twice.

## Reference: Market positioning

| | Slack AI | Guru / Tettra | LoopBack |
|---|---|---|---|
| Finds answers | ✓ | ✓ | ✓ |
| Verifies answers | ✗ | Manual | Auto |
| Owner accountable | ✗ | Sometimes | Always |
| Zero extra work | ✓ | ✗ | ✓ |
| Intent matching | ✗ | ✗ | ✓ |
| Direction check before escalation | ✗ | ✗ | ✓ |
| Patterns → product fixes | ✗ | ✗ | ✓ |

Slack AI finds where the conversation happened — it returns messages, noise with signal buried inside. Guru and Tettra assume someone will stop working and become a librarian. LoopBack doesn't ask anyone to document more — it captures knowledge at the exact moment it's born.
