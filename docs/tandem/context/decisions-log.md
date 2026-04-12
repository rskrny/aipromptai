# Tandem — Decisions Log

Record of every decision made on the Tandem subproject and the reasoning behind it.

---

## 2026-04-11 — Subproject kickoff

**Decision**: Start a Tandem subproject in parallel with the ongoing HelloTalk project.
**Reasoning**: The HelloTalk project is in "wait for backend re-evaluation" state after the bio rewrite + support email were sent earlier on 2026-04-11. No further technical action on HelloTalk is required until the 24-72 hour observation window completes. The user has a second low-visibility account (Tandem) with symptomatically similar behavior, and wants to apply the same kind of analysis. Running the two projects in parallel doesn't create conflicts because the target apps and infrastructure are independent.

**Decision**: Use a lightweight approach first — no reverse engineering until we know it's needed.
**Reasoning**: HelloTalk taught us an important lesson. The API decryption work was valuable for diagnosis but the actual fix came from a non-technical action (bio rewrite). For Tandem, skip directly to profile analysis first. If visible problems are identified, fix them. Only if non-technical fixes fail do we escalate to reverse engineering.

**Decision**: Store Tandem context under `docs/tandem/` rather than restructuring `docs/` into `docs/hellotalk/` + `docs/tandem/`.
**Reasoning**: Restructuring would require updating every existing script, reference in CLAUDE.md, AGENTS.md, and any internal path references in the HelloTalk project. That's a lot of churn for very little benefit. Accept the asymmetry: HelloTalk context lives in `docs/context/`, `docs/strategy/`, etc. directly. Tandem context lives in `docs/tandem/context/`, `docs/tandem/strategy/`, etc.

---

## 2026-04-11 — Diagnosis + bio fix

**Decision**: Diagnose purely from profile screenshots before asking for more intake data.
**Reasoning**: The user sent two screenshots of the Tandem profile. Visual inspection revealed two keyword-based moderation triggers ("conspiracy theories" and "business") in the "I like to talk about" field. These are unambiguous. No need to do API analysis or ask more intake questions to confirm — the problem is visible on the face of the profile.

**Decision**: Rewrite the bio immediately rather than running diagnostic probes first.
**Reasoning**: On HelloTalk the diagnostic investigation took days and led to the same conclusion (bio rewrite) we could have reached faster from profile inspection alone. Don't repeat that mistake on Tandem. Action first, measurement second.

**Decision**: Replacement bio text is `Photography, fitness, travel, food, American culture, Chinese history`.
**Reasoning**:
- Kept "photography" and "fitness" from the original because they're safe and already verified as non-triggering (six positive references exist while those words were in the bio).
- Added "travel" and "food" because they're among the most-talked-about safe topics on any language exchange app. No keyword scanner flags them.
- Added "American culture" because it's a direct match for what Chinese learners want to practice with an American native speaker — increases match relevance.
- Added "Chinese history" because it signals deep, serious interest in Chinese language and culture — which Tandem's ranking probably rewards as a "committed learner" signal.
- Dropped "conspiracy theories" (the killer keyword) and "business" (the secondary killer).
- Total length kept short enough to fit typical Tandem field limits.

**Decision**: Do NOT mention the bio rewrite to Tandem support in any future escalation.
**Reasoning**: Same principle as the HelloTalk playbook. Mentioning a bio edit in a support ticket reads as admitting the old bio was non-compliant, which gives Tandem's trust team an "oh, you had a policy violation, case closed" off-ramp. The fact is the old content was acceptable when originally posted (the references accumulating in early 2025 prove that) — the policy changed underneath, not the content. Frame any future support ticket as "my clean account is being wrongly suppressed, please fix it."

**Decision**: Observe for 24-72 hours before taking any further action on Tandem.
**Reasoning**: Tandem's re-review cycle on profile edits is typically faster than HelloTalk's (reports suggest hours to 1-2 days, not days to a week). If the bio fix is the cause and the fix is sufficient, we should see measurable recovery in that window. Taking additional action (support ticket, boost purchase, etc.) before we know if the bio fix worked risks contaminating the signal and making it harder to tell what actually worked.

**Decision**: Defer API reverse engineering of Tandem until Phase 3 or later.
**Reasoning**: The HelloTalk reverse engineering took multiple sessions and was only directly useful for one thing (confirming the error 6000 search plan exclusion). The user's stated visibility problem on Tandem is almost certainly a one-keyword bio issue. Reverse engineering Tandem would cost days of work for very little marginal diagnostic value beyond what we already have from the screenshots.
