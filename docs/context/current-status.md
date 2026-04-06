# Current Status

**Last updated**: 2026-04-05

## Account Profile
- **User**: American learning Chinese (Mandarin)
- **Account age**: Old (pre-2023, possibly much older)
- **Subscription**: FREE (not VIP)
- **Current visibility**: Severely degraded — 0-2 inbound messages/day (was 40+/day)
- **Moments engagement**: Barely any
- **Warnings/suspensions**: None received
- **Location history**: Highly unstable — Europe (2023) → China → US, with VPN usage throughout
- **Current location**: US (assumed)

## Diagnosis

### Root Cause Assessment (Ranked by likelihood)

**1. LOCATION CHAOS (PRIMARY SUSPECT)**
The account has bounced between Europe, China, and the US with VPN usage on top. HelloTalk tracks precise location. This pattern looks like:
- A shared/compromised account (multiple countries in short time)
- A bot or scraper (VPN + location hopping)
- Account selling/trading activity
This almost certainly triggered trust scoring penalties. Going from 40+/day to 0-2/day is a 95%+ drop — consistent with algorithmic suppression, not just natural decline.

**2. FREE TIER + NO VIP BOOST**
On free tier, no "extra profile exposure" boost. Combined with trust penalty, the account is effectively invisible.

**3. ACCOUNT STALENESS**
On-and-off usage since 2023 means long dormant periods. Algorithm deprioritizes inactive accounts. Each dormant period compounded the damage.

**4. POSSIBLE SOFT SHADOW BAN**
The 95%+ drop with zero warnings suggests algorithmic suppression rather than manual moderation action. HelloTalk's content policy confirms they can "reduce discoverability" without notification.

## What We Know For Sure
- [x] Free account, not VIP
- [x] Visibility dropped ~2023, used on and off since
- [x] Heavy location changes: Europe → China → US + VPN
- [x] No warnings or suspensions ever received
- [x] Was getting 40+/day inbound, now 0-2/day
- [x] Moments getting barely any engagement
- [x] Never received any HelloTalk system warnings

## Confirmed Settings (from screenshot 2026-04-05)
- **Location**: Hana, United States (Maui, Hawaii)
- **VPN**: OFF
- **Device**: iPhone (iOS — confirmed from screenshot UI)
- **Show Country/Region**: ON
- **Show City**: ON
- **Update Location**: ON
- **Show Age**: ON
- **Show Zodiac**: OFF
- **Show Online Status**: ON
- **Show My Like Count**: OFF ← SHOULD TURN ON
- **Show My Gifting Level**: OFF
- **Birthday Notification**: OFF ← SHOULD TURN ON
- **Personalized Ads**: OFF

## Still Need
- [ ] Profile screenshot (photo, bio, interests) — need to evaluate quality
- [ ] What does the "Who Can Find Me" setting look like? (scroll down on privacy page)
- [ ] Confirmation of language settings (Native=English, Learning=Chinese)

## Active Strategy
Executing account recovery plan — see `docs/strategy/account-recovery.md`

## Immediate Next Steps
1. ~~VPN OFF~~ — DONE (confirmed off)
2. ~~Location stabilized~~ — DONE (Hana, Hawaii — staying for a while)
3. VIP upgrade — USER DECLINED (against principles — respect this, work without it)
4. Turn on "Show My Like Count" and "Birthday Notification"
5. Check "Who Can Find Me" setting
6. Profile overhaul (need to see current profile first)
7. Email HelloTalk support (template in strategy doc)
8. Begin 7-day high-quality activity burst
9. APK decompilation — extract real API endpoints and understand matching algorithm internals
