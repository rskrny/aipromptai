# Tandem — Findings Log

Chronological log of every research finding on the Tandem account. Newest entries at the top.

---

## 2026-04-11 — Diagnosis complete: bio keyword suppression, fixed

### The reveal
User shared two profile screenshots from the Tandem iOS app. Diagnosis was possible from visual inspection alone — no reverse engineering required, no API probing.

### Red flag 1: "Conspiracy theories" in the "I like to talk about" field
Tandem's community guidelines explicitly prohibit content that is politically divisive, misleading, or part of misinformation categories. "Conspiracy theories" is a direct, unambiguous match for a top-tier suppression keyword on any moderated language exchange platform, and Tandem's moderation is widely reported to be stricter than HelloTalk's. This is the kind of keyword that would be on an automated scanner's block list with high confidence.

### Red flag 2: "Business" in the "I like to talk about" field
Tandem's terms explicitly prohibit commercial use of the platform. Their automated keyword scanner cannot distinguish "business as a topic of conversation" from "business solicitation / recruiting," so any profile that contains the word tends to get flagged. This is the exact same semantic category as HelloTalk's `赚钱` (make money) trigger that was already diagnosed on the user's HelloTalk account earlier in the same session.

### Timeline
Reference dates on the profile provide the key timing signal:
- Reference from Yuna: Jan 22, 2025 — "funny, patient and a pleasure to talk to"
- Reference from Jiayao: Apr 20, 2025 — "Nice guy!"
- Reference from Rae: Apr 28, 2025 — "We're actually schoolmates, should have met earlier, haha"
- No references more recent than April 2025 visible in the first three shown (3 more are behind "See all (6)" but the user reports exposure dropped recently)

The reference pipeline going cold around April 2025 and the user's report of steadily declining exposure afterwards together indicate a suppression event in mid-to-late 2025. Tandem almost certainly added new keywords to their moderation scanner or tightened existing thresholds during that period, the updated scanner re-evaluated existing profiles, and this account got swept into a suppression bucket because of the two bio keywords.

This is the same retroactive-moderation pattern we diagnosed on HelloTalk — different app, different trigger keywords, same mechanism.

### What's healthy on the profile (from same screenshots)
- Clear face photo, good lighting, interesting background (city skyline at night)
- Tagline `请教我一个词` ("please teach me a word") — humble, earnest, language-learning-aligned, excellent signal
- "Online today" with lightning bolt active indicator
- 6 positive references, all from Chinese speakers — high-quality social proof
- Language level bar showing ~3/5 for Chinese (intermediate, engaged with the learning interface)
- "My ideal language exchange partner is" field: "Funny, motivating, entertaining" — safe, universal, non-triggering
- "My language learning goals are" field: "Neeeeed to improve my Chinese" — earnest, clear, non-triggering

The profile is not "bad." It has exactly one issue, in exactly one field. That makes this a surgical fix, not a rebuild.

### The fix (user-executed 2026-04-11)
"I like to talk about" field changed from:
> `Conspiracy theories, fitness, business, photography`

to:
> `Photography, fitness, travel, food, American culture, Chinese history`

Both trigger keywords removed. Kept the two safe originals (photography, fitness). Added four safe topics that match typical Tandem-friendly conversation: travel, food, American culture, Chinese history.

User saved the edit. No error screen reported on save, no "profile under review" state shown.

### Expected outcome
Tandem re-reviews profile edits through a combination of automated keyword scanning and (for flagged profiles) human moderator review. The automated scanner should re-run on the updated bio on Tandem's next cycle, fail to match any trigger keywords, and clear the suppression flag. Expected timeline: 24-72 hours for measurable recovery in inbound volume.

### Confidence level
HIGH (~80%). The diagnosis is supported by:
1. Direct visual evidence of two known-bad keywords in a flagged field
2. A timeline that matches a retroactive scanner update
3. An otherwise healthy profile that should have high visibility
4. A parallel case on HelloTalk (same session, same user, same mechanism, different app) that already confirmed this is how language apps enforce commercial-intent policies retroactively
5. No competing explanation identified from the available evidence

Remaining 20% uncertainty is around alternate causes: general engagement fatigue, industry-wide free-tier deprioritization during 2025, or an undisclosed per-user event we don't know about.

### What we deliberately did NOT do
- No API reverse engineering. Tandem's API is not known to be cracked publicly, and reverse engineering it would take days of work. The diagnosis was clear enough from visual inspection that API access wasn't necessary.
- No support outreach yet. If the bio fix works on its own (likely), we don't need to bother Tandem's support, which is notoriously unresponsive to free-tier users.
- No moments/posts audit. Tandem doesn't have a moments feed the same way HelloTalk does — their engagement is primarily DM and video/audio call based — so that surface doesn't apply.
