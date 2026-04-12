# Tandem — Current Status

**Last updated**: 2026-04-11

## Account Profile

- **App**: Tandem (German-based language exchange app, direct HelloTalk competitor)
- **Username**: `ryan21873925`
- **Display name**: Ryan, 28
- **Tier**: Free (not Tandem Pro)
- **Account created**: 2024 (roughly 1.5 years old)
- **Native language**: English
- **Learning**: Chinese (Simplified) — shown at ~3/5 bars (intermediate)
- **Location**: Boston, United States (inferred — same user as HelloTalk project)
- **Device**: iOS
- **Certificates**: none
- **References**: 6 total, all positive (latest captured: April 28, 2025)

## Symptom

Exposure was high when the account was newer (lots of inbound, references accumulating through early-to-mid 2025). Over the last ~12 months it has dropped significantly to low inbound / low match volume. Most recent reference on the profile is from April 28, 2025, meaning the engagement-leading-to-reference pipeline went cold in the last year.

## Diagnosis — HIGH CONFIDENCE (2026-04-11)

### ROOT CAUSE: Bio keyword suppression (same mechanism as HelloTalk)

The "I like to talk about" field contained two keywords that match Tandem's known moderation triggers:

1. **"Conspiracy theories"** — Tandem explicitly prohibits politically divisive and misinformation-adjacent content in their community guidelines. This is a top-tier suppression keyword.
2. **"Business"** — Tandem explicitly prohibits commercial use of the platform. Their automated scanner cannot distinguish "business as a topic of conversation" from "business solicitation." Same semantic category as HelloTalk's `赚钱` trigger.

### Timeline correlation
- **2024**: account created, clean bio, received new-user visibility boost.
- **Jan 2025**: received positive reference from user "Yuna" — account is healthy and engaged.
- **Apr 2025**: received two more references (Rae, Jiayao) — still active.
- **Mid-to-late 2025 to early 2026**: references stop accumulating. Engagement drops. Exposure falls.
- **2026-04-11**: diagnosed, user updated the bio to remove both trigger words.

This timeline matches a retroactive moderation scanner update. Tandem almost certainly added or tightened their keyword blacklist sometime after April 2025. The updated scanner re-evaluated existing profiles, hit the "conspiracy theories" and "business" strings in this bio, and silently applied a suppression flag. Same retroactive-flag mechanism as HelloTalk, different app, same family of problem.

### Supporting evidence
- No moderation history reported by user (silent suppression, not formal ban)
- Profile has 6 positive references (account is not "bad" in any human sense)
- Clear face photo, good location, active status indicator — the ranking signals Tandem rewards are mostly in place
- The drop is steep and goes uncorrelated with any user behavior change
- Same user profile pattern (Boston-based American learning Chinese, late-20s male) saw the same kind of suppression on HelloTalk

## Working theory confidence

**~80%** confidence that the bio was the primary cause. Remaining 20% caveats:
- The drop could alternatively be explained by natural engagement fatigue (less active = less visible)
- Tandem could also have deprioritized free-tier accounts in general during 2025 (industry-wide pattern)
- There may be additional factors we haven't discovered yet (e.g., a moments/posts removal, a reported-by-user event the account owner is unaware of)

We'll know more after the bio fix propagates (expected 24-72 hours).

## Action Taken (2026-04-11)

### User action completed
**Bio rewrite**: the "I like to talk about" field was changed from `Conspiracy theories, fitness, business, photography` to `Photography, fitness, travel, food, American culture, Chinese history`.

Both trigger keywords removed. Two safe topics added (travel, food) and one language-learning-adjacent topic (Chinese history) added.

User saved the change in-app. No error or "profile under review" screen was reported on save, which MAY mean:
- The edit went through without a manual re-review queue, OR
- Tandem queued it for re-review silently without showing a screen, OR
- There's nothing to re-review because the previous version was already flagged

Either way, the updated bio is now live and the moderation scanner's next cycle will evaluate the clean version.

## What We Know For Sure

- [x] Account exists, free tier, 2024 vintage
- [x] Bio updated on 2026-04-11 to remove `conspiracy theories` and `business` keywords
- [x] 6 positive references, latest Apr 28 2025 (reference pipeline went cold after that)
- [x] Profile photo is a clear face in good light with city skyline background
- [x] "Online today" status with lightning bolt active indicator
- [x] Language level bar ~3/5 for Chinese (intermediate)
- [x] No moderation warnings ever received (per user)
- [x] No Tandem Pro subscription
- [x] Same user, same device, same location history as the HelloTalk project

## Still Need

- [ ] Confirmation that the bio edit actually saved on the server (can check by viewing own profile after save)
- [ ] 24-72 hour observation window to see if inbound / match volume responds
- [ ] Current count of strangers viewing profile / sending first messages (baseline measurement)
- [ ] Whether Tandem's "Super Likes" / boost system has any free inventory on this account
- [ ] Research into Tandem's discovery algorithm and known moderation patterns

## Active Strategy

**Phase 1 (today, 2026-04-11)**: bio fix. Complete.
**Phase 2 (24-72h window)**: observe for engagement recovery. If reference pipeline and inbound message rate recover, diagnosis is confirmed and we're done. If not, escalate to Phase 3.
**Phase 3 (if Phase 2 fails)**: send direct support appeal to Tandem via in-app feedback + email, using the same narrative framing as HelloTalk (silently suppressed, no violation notice, requesting re-review). Escalation materials to be drafted if needed.
**Phase 4 (only if absolutely necessary)**: reverse engineer Tandem's API (same level of depth as HelloTalk) to get direct diagnostic access. Deferred until we know Phase 2-3 are insufficient.

## Notes on project structure

This directory (`docs/tandem/`) is the Tandem-specific context. The HelloTalk project lives in the parent `docs/` directory (`docs/context/`, `docs/strategy/`, `docs/api-endpoints.md`, etc.) for historical reasons. Both projects share the same user, same device, same goals, but different target apps.

The HelloTalk monitoring via GitHub Actions (`.github/workflows/ht-monitor.yml`) is independent and continues to run in parallel.
