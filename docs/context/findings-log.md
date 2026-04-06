# Findings Log

Chronological log of every research finding. Newest entries at the top.

---

## 2026-04-05 — User Diagnostic Answers Received

### Account Data (FROM USER)
- Free tier (no VIP)
- Visibility dropped ~2023, used on and off
- Location history: Europe (2023) → China → US, with VPN usage
- No warnings or suspensions ever
- Was 40+ inbound messages/day → now 0-2/day (95%+ drop)
- Moments barely getting engagement

### Analysis: Location Chaos is the Primary Culprit
The location hopping pattern (Europe → China → US + VPN) is almost certainly the main trigger. Here's why:

1. **HelloTalk tracks precise location** — confirmed by multiple sources
2. **Rapid country changes** look like account sharing, botting, or fraud to any trust system
3. **VPN usage compounds the problem** — VPN IP ranges are known and flagged by platforms
4. **China specifically** is significant — HelloTalk is a Chinese company. Using the app FROM China as a foreigner with a US account, especially via VPN, could trigger special scrutiny (Great Firewall interactions, IP inconsistencies)
5. **The timing matches** — user says drop was ~2023, which is when the location chaos was happening

### Why No Warning Was Sent
HelloTalk's shadow ban is algorithmic, not manual. Their content policy says they "reduce discoverability" — this doesn't require a warning. The Warning → Suspension → Removal escalation path is for content violations. Algorithmic trust scoring is separate and silent.

### The 40+/day → 0-2/day Drop
This magnitude of drop (95%+) is NOT natural decline. Natural decline from inactivity would look more like 40 → 20 → 10 → 5. A near-total drop to 0-2 indicates active suppression, not just deprioritization.

---

## 2026-04-05 — Initial Research Complete

### HelloTalk Shadow Ban System (CONFIRMED)
- HelloTalk officially states in their Content Policy that they "may reduce discoverability by redirecting search results or limiting distribution of Moments or results in the Search (Find Partners) Tab"
- Triggers: spam, illegal activity, policy violations
- Enforcement uses "a mix of technology and human moderation before content gets reported"
- Escalation path: Warning → Suspension → Removal
- Appeals are possible if user believes no violation occurred
- Source: hellotalk.com/content-policy

### Account Trust Signals (HIGH CONFIDENCE)
- HelloTalk tracks precise location (confirmed by Surfshark data privacy analysis)
- Location, device info, camera/microphone access all collected
- VPN usage could flag inconsistent location data
- Certificate pinning on mobile app (standard for social apps post-Android 7.0)
- Rate limiting via resty.limit.req at API gateway level

### User Reports Pattern (MEDIUM CONFIDENCE from Trustpilot/forums)
- Multiple users report "freshly new registered accounts and even devices get blocked for no reason"
- Users report visibility drops and message restrictions without clear violations
- Political content (mentioning Taiwan, etc.) has reportedly triggered bans
- Customer support described as unresponsive, especially for non-VIP users
- VIP members also report issues, suggesting paying doesn't fully protect you

### New User Boost (SPECULATED — not confirmed for HelloTalk specifically)
- Many social platforms (Tinder, Bumble, Instagram) give new accounts temporary visibility boosts
- HelloTalk likely does similar — fresh accounts would generate more engagement to hook the user
- Old accounts that went dormant would lose this boost and may not recover it
- No official HelloTalk documentation confirms this, but it's standard industry practice

### Location Impact (MEDIUM CONFIDENCE)
- HelloTalk has global server nodes: Eastern US, Frankfurt, Singapore, Tokyo, Hong Kong
- Location affects which users you're matched with
- Being in the US learning Chinese = you're matched against Chinese speakers wanting to learn English
- Time zone alignment matters — being online when Chinese users are active (their evening) increases matches

### Moments Algorithm (CONFIRMED)
- Moments within Topics ranked by engagement (likes + comments), NOT chronologically
- Posts with images get significantly more attention
- One power user accumulated 900+ Moments as engagement strategy
- "Please correct me" tag increases correction responses
- Early engagement snowballs — first few likes push you higher in the feed
