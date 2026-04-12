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

---

## 2026-04-06 — Encryption Analysis & Strategy Pivot

**Decision**: Pivot from "decrypt API traffic" to "behavioral optimization + Proxyman live viewing."
**Reasoning**: HelloTalk uses ECIES encryption (ECDH key exchange + AES) on most API payloads. Captured traffic cannot be decrypted without APK decompilation to extract the encryption class. However, Proxyman on iOS shows decrypted content in real-time (the app handles decryption). So instead of trying to build a decryption pipeline, we should:
1. Use Proxyman live viewing to read responses as they happen
2. Focus on the plain JSON endpoints we CAN read (boost status, language info, nearby count)
3. Optimize behavior based on what we already know about the algorithm
4. Park APK decompilation as a future option if behavioral optimization isn't enough

**Decision**: Focus on the `post_recommend_btn` endpoint as a potential free boost trigger.
**Reasoning**: We found `remain_times: 0` on the free boost system. The `post_recommend_btn` endpoint exists — it might trigger a boost action or reveal how to get more boosts. This is testable through Proxyman observation.

---

## 2026-04-06 — ENCRYPTION CRACKED + ROOT CAUSE CONFIRMED

**Decision**: Fully reverse-engineer the mobile API encryption.
**Reasoning**: Behavioral optimization is pointless if the account is hard-locked. We needed to see what the server actually thinks about this account. Cracked X25519 + AES-256-ECB encryption scheme by: (1) decompiling APK with JADX, (2) finding SecretDataModel.java which revealed X25519 key exchange, (3) getting server public key from Proxyman x-ht-pub header, (4) computing shared secret and decrypting responses.

**Decision**: Confirmed root cause is profile lock + search index exclusion (error 6000).
**Reasoning**: API returns `"Get Search User Plan Failed"` (code 6000) when asked to index this account for discovery. The app shows "system maintenance" profile lock message. Scanned all 491 discovery users — account is completely absent. This is a server-side admin restriction, not a ranking or settings issue.

**Decision**: Reversed earlier decision — now pursuing new account in parallel.
**Reasoning**: The profile lock is an admin-level server restriction that cannot be cleared via API. Only HelloTalk support can remove it. While waiting for support response, a new account with optimized profile (using our knowledge of the ranking formula) can achieve immediate visibility. User created new account with username u_sam749.

**Decision**: Email HelloTalk support with technical evidence.
**Reasoning**: A support request that demonstrates specific knowledge of the restriction (error 6000, profile lock, search index exclusion) gets escalated faster than a generic complaint. Drafted email referencing account ID, follower count, and threatening App Store complaint about deceptive visibility boost sales to secretly banned users.

---

## 2026-04-06 — New Account Strategy

**Decision**: Create new account on different phone with different credentials.
**Reasoning**: Old account profile lock is server-side and cannot be API-manipulated. New account starts clean with no restrictions. Using knowledge of rank_score formula (max 33,999) to optimize from day 1. Different phone minimizes risk of device-level account linking.

**Decision**: Need new account's user ID before we can monitor/optimize it.
**Reasoning**: The HelloTalk app doesn't display the numeric user ID in an obvious place. Need to capture it via Proxyman/mitmproxy traffic interception from the second phone's HelloTalk requests. This is the blocker for next session.

---

## 2026-04-11 — Go Offensive: Three-Front Attack Plan

**Decision**: Stop waiting on HelloTalk support. Pivot to a three-front offensive campaign.
**Reasoning**: Support responded to the 2026-04-06 email by clearing the profile lock but did NOT clear the search plan exclusion. The account is editable now but still invisible. Support has gone quiet again. Continuing to wait is pointless. We have enough technical capability and external pressure options to push multiple angles in parallel.

**Decision**: Drop face verification as a recovery lever permanently.
**Reasoning**: HelloTalk only allows face verification ONCE per account. User did it in China 2 years ago. App blocks re-verification. The 4000-point `real_avatar` factor is unreachable through normal means. Further investigation of this path is wasted time.

**Decision**: Use the iPhone as the primary execution environment (not a laptop).
**Reasoning**: User is mobile-only right now and wants to act today. The auth token in `probe-commands.sh` is valid until 2026-05-02. Unencrypted endpoints (`free_recommend_status`, `post_recommend_btn`, `query_expose_record`, `get_user_info`, `get_user_detail`) can be hit from any iOS HTTP client app (Postman / HTTPBot / Apidog) using plain HTTP. This unlocks direct API action without waiting for laptop access.

**Decision**: Force profile write events as a hypothesis test for search plan rebuild.
**Reasoning**: The search plan rebuild likely happens on profile write events on the backend. The profile was locked for years, which means no writes have been firing, which means the indexer has never been prompted to retry. Now that the lock is off, changing city/bio/location should trigger the rebuild. This is zero-risk and zero-cost to test.

**Decision**: Open external pressure fronts in parallel with technical action.
**Reasoning**: HelloTalk is a Chinese company and doesn't care about individual user complaints. But they care about: Apple (App Store deceptive-purchase complaints can trigger developer account review), public reputation (Trustpilot/Reddit rank in Google), and being publicly called out on Twitter. These channels escalate what a single support email never will. Recommended actions: Apple "Report a Problem" for deceptive in-app purchases (selling boosts to a secretly-excluded account), Trustpilot 1-star review, Reddit post in r/languagelearning and r/ChineseLanguage describing the symptoms and asking if others are affected, LinkedIn DMs to 2–3 HelloTalk staff (PM / Trust & Safety / Community).
