# Decisions Log

Record of every decision made and the reasoning behind it.

---

## 2026-04-05 — Project Setup

**Decision**: Build a systematic agent-based workflow instead of ad-hoc research.
**Reasoning**: The user wants reliable, repeatable results. A pipeline (Describe → Identify → Scope → Code → Review → Test → Plan → Release) ensures nothing falls through the cracks and we can track what works.

**Decision**: Focus on account recovery before building automation tools.
**Reasoning**: No point building tools if the account is shadow-banned. Fix visibility first, then optimize engagement.

**Decision**: Do NOT recommend creating a new account.
**Reasoning**: HelloTalk prohibits multiple accounts and can detect device-level bans. A fresh account on the same device/phone number could get immediately flagged. Better to recover the existing account.

---

## 2026-04-05 — Diagnosis Complete

**Decision**: Location chaos (Europe → China → US + VPN) identified as primary root cause of visibility loss.
**Reasoning**: 95%+ drop in inbound messages (40+/day → 0-2/day) with no warnings = algorithmic suppression, not manual moderation. The only significant behavioral change was constant location hopping + VPN. HelloTalk tracks precise location. This pattern triggers trust scoring penalties on any platform.

**Decision**: VIP upgrade is required, not optional.
**Reasoning**: Free account + trust penalty = invisible. VIP's confirmed "extra profile exposure" is the fastest way to counteract algorithmic suppression. The visitor page also lets us track whether visibility is improving (measurable feedback).

**Decision**: Location stabilization is the #1 priority.
**Reasoning**: No amount of activity or VIP will help if the account keeps triggering trust flags via location inconsistency. Must: turn off VPN, enable location services, stay in one physical location, let the account's location signal stabilize.

**Decision**: Contact HelloTalk support proactively rather than waiting 3 weeks.
**Reasoning**: Given the severity of the drop (95%+) and the clear non-violation history (zero warnings), it's worth reaching out to support early while simultaneously executing the activity strategy. Two-track approach.

**Decision**: User declined VIP — respect this and optimize within free tier.
**Reasoning**: User said it's against their principles. We have 10 new chats/day and no visitor page, but the core recovery strategy (location stability, activity burst, corrections, moments) still works without VIP. We just can't measure visibility via the visitor page — will have to track inbound message count instead.

---

## 2026-04-05 — APK Decompilation Decision

**Decision**: Pursue APK decompilation to map real API endpoints.
**Reasoning**: web.hellotalk.com blocks automated access (403). Mobile app has cert pinning. The community clone gives us the probable data model shape, but to understand the actual matching algorithm, trust scoring, and visibility mechanics, we need the real source. JADX decompilation of the Android APK is the fastest path to real endpoint URLs, auth schemes, and internal logic.
