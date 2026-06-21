# LoopBack — Demo Script

3-minute demo video. Two Slack accounts: Jinqiu plays the requester, Jie plays the resolver.

---

## Act 1 — Cold start (~60s)

**Goal:** Show the full resolution cycle from scratch. No Vault data yet.

1. Jinqiu (as User): `@Mira how do I request PTO?`
2. Show card appear: Draft → Searching
3. Card updates to **human_working** — "No existing answer found, a teammate will follow up"
4. Jie (as Resolver): replies directly in the thread with the real answer
   *(Mira stays silent — she's listening, not relaying)*
5. Mira follows up in thread: "Did this resolve your question?"
6. Jinqiu clicks **Confirm ✓**
7. Card updates to **Verified ✓**

**Narration beat:** "The first time a question is asked, Mira escalates to a human.
The answer is captured, verified, and written to the Knowledge Vault."

---

## Act 2 — Vault hit (~45s)

**Goal:** Show the payoff. Same question, different wording, instant answer.

1. Switch to a second Slack account (or a different channel)
2. New user: `@Mira what's the PTO request process?`
3. Show card: Draft → Searching → **pending_confirm** in ~3 seconds
4. Card shows the verified answer with confidence score and original owner
5. New user clicks **Confirm ✓**
6. Card updates to **Verified ✓** — confidence score rises

**Narration beat:** "The second time anyone asks — even in completely different words —
Mira returns a verified answer instantly. The resolver is never disturbed again."

---

## Act 3 — Knowledge Vault Dashboard (~30s)

**Goal:** Show the knowledge base growing over time.

1. Open App Home (Mira's tab)
2. Show the entry list: question, answer, status badge, confidence, owner, usage count
3. Click into the PTO entry — expand to show the full task card history

**Narration beat:** "Every resolved conversation lives here — with full provenance.
Not a wiki someone had to write. A knowledge base that writes itself."

---

## Closing line (~15s)

> "LoopBack doesn't ask your team to document more.
> It captures knowledge at the exact moment it's created —
> so the next person who asks never has to wait."

---

## Checklist before recording

- [ ] Seed Vault with 5+ entries so Dashboard looks inhabited
- [ ] Two Slack accounts ready (requester + resolver)
- [ ] VAULT_STUB=false, real Supabase connected
- [ ] App deployed to Railway (not running locally)
- [ ] Record 2–3 takes, keep the cleanest one under 3:00
- [ ] Set video to Public before submitting
