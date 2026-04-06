# Blocked Ideas

Ideas we considered and rejected, so we don't revisit them.

---

## Creating a New Account
**Why blocked**: HelloTalk ToS prohibits multiple accounts. They can detect same device/phone number. Risk of permanent device-level ban. Old account has history and connections worth preserving.

## Automated Mass Messaging
**Why blocked**: HelloTalk uses rate limiting (resty.limit.req) and bot detection. Automated messaging patterns would be detected and result in suspension. Free limit is 10 new chats/day, VIP is 25 — must stay within these.

## VPN Location Spoofing
**Why blocked**: HelloTalk tracks precise location. VPN creates inconsistent location signals which could lower trust score or trigger flags. Worse, VPN IP ranges are often known and flagged by platforms.

## Certificate Pinning Bypass / API Manipulation
**Why blocked**: Modifying API requests or bypassing security measures could result in permanent account ban. We're optimizing within the system, not attacking it.
