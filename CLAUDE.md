# CLAUDE.md

This file is auto-loaded by Claude Code every time this project is opened.
Read this first, every session, before writing or changing any code.

---

## Who you are on this project

You are building toward a **hackathon submission with a deadline**, not an
open-ended engineering project. Act accordingly:

1. **Don't simplify away the product's differentiation.** This project's
   entire competitive edge against Slack AI / Guru / Tettra is in specific
   design decisions that look like unnecessary complexity if you're only
   optimizing for "does it run" — e.g. the two distinct paths into
   `unconfirmed` status, or Mira never relaying messages between requester
   and resolver. If a design decision in `docs/implementation/DESIGN.md` seems like it
   could be done more simply, **assume the complexity is intentional and
   ask before removing it.** It usually exists because it's the answer to
   a judging-criteria question ("how is this different from what already
   exists").

2. **Write code as if a judge will read it, not just run it.** Clear
   naming, comments on *why* for any non-obvious architectural choice
   (especially ones documented in `docs/DESIGN.md`), no dead code left
   from earlier iterations. Code quality is a direct judging criterion
   (Technological Implementation).

3. **Prioritize an end-to-end working loop over a polished single piece.**
   A complete, rough resolution cycle that can be demoed beats a
   beautifully built Knowledge Vault that doesn't connect to anything yet.
   When time is short, cut UI polish before cutting a working connection
   between Mira and the Vault. The demo video needs real, working footage
   — see submission requirements below.

4. **Don't invent product decisions.** If something isn't covered in
   `docs/DESIGN.md` and matters (e.g. exact confidence thresholds, copy
   text shown to users), ask rather than guessing — these are product
   calls the humans need to make, not implementation details.

---

## Where to find things

- **`docs/implementation/DESIGN.md`** — the full design context: core mechanism, the
  Resolution Cycle state machine, the three confirmation signals, data
  model, API contract between Mira and the Vault, naming conventions.
  **Read this before touching any resolution/status logic.**
- **`docs/implementation/implementation-plan.md`** — the week-by-week task breakdown,
  who owns what, current build status.
- **`docs/submission/project-story.md`** — the Devpost submission draft.
  **Update the relevant section every time a milestone is completed.**
  Sections marked TBD or "update as build progresses" are the ones to fill in.
- **`mira-app/`** — the conversational layer (Slack Bolt, intent
  classification, task cards, dashboard). This is Jinqiu's side.
- **`vault-service/`** — storage, embeddings, semantic search, confidence
  scoring, version history. This is the teammate's side. Treat the API
  contract in `docs/implementation/DESIGN.md` as fixed when working in `mira-app/` —
  don't assume internals of how the Vault is implemented.

---

## Hackathon Submission Requirements

**Event:** Slack Agent Builder Challenge
**Deadline:** July 13, 2026, 5:00pm PDT — no edits accepted after this time

**Track:** New Slack Agent

**Required technology (cite all that apply in submission):**
- Slack AI capabilities → Claude-powered intent classification + extraction
- MCP server integration → [confirm current status]
- Real-Time Search API → Mira's Slack history search step

**What gets submitted:**
- Project Track: New Slack Agent
- Text description of features/functionality
- ~3-minute demo video — **must show real, working footage**, not slides
- Architecture diagram
- Slack developer sandbox URL, shared with both
  `slackhack@salesforce.com` and `testing@devpost.com`

**Judging criteria — keep all four in mind, not just code quality:**
1. Technological Implementation — code quality + real use of the required tech
2. Design — UX quality, balanced frontend/backend
3. Potential Impact — reach within Slack community and beyond
4. Quality of the Idea — uniqueness vs. existing tools (Slack AI, Guru,
   Tettra). This is where the Resolution Cycle and verification mechanism
   need to come through clearly, in both the code and the demo.

---

## Naming (don't deviate)

- The AI is **Mira**. Never "the bot" or "TaskBridge" (retired name).
- The knowledge store is the **Knowledge Vault**. Never "Dictionary" or
  "TaskBridge" (retired names).
- Project name: **LoopBack**.
