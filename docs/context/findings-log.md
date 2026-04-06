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

## 2026-04-05 — LIVE API Traffic Captured (Proxyman on iOS)

### Major Breakthrough: No Certificate Pinning
HelloTalk v6.3.0 on iOS does NOT enforce certificate pinning. Proxyman with SSL proxying enabled can intercept ALL API traffic. This gives us full visibility into the real API.

### Real API Base URL
`https://api-global.hellotalk8.com` — NOT hellotalk.com! The actual domain is hellotalk8.com.

### Auth Scheme: JWT Bearer Token
- Bearer token in Authorization header
- Custom headers: x-ht-os (platform), x-ht-uid (user ID), x-ht-did (device fingerprint), x-ht-timezone
- User-Agent encodes: os, app version, device model, OS version, user ID
- Server runs Envoy proxy (confirmed from headers)

### Critical Finding: Visibility Boost System
Endpoint: `/virtual_product/v1/virtual_product/free_recommend_status`
Response: `{"remain_times": 0, "virtual_type": 14}`
- HelloTalk has a built-in "recommendation" virtual product system (type 14)
- Free users get a limited number of boosts
- THIS ACCOUNT HAS ZERO REMAINING BOOSTS
- This means the account gets NO algorithmic visibility push
- VIP likely gets more or refreshed boosts — this explains part of the visibility drop

### Exposure Tracking Endpoint Found
`/v2/moment/query_expose_record` — tracks visibility/exposure metrics
- Response couldn't be decoded on iOS (likely protobuf/binary)
- Need desktop export to read the actual visibility data

### Nearby Search Endpoint
`/go_user_search/v2/nearby_count` — sends exact GPS coordinates, target language, and user ID
- Confirms location is core to matching (lat/lon sent with every search)
- htntKey parameter appears to be a session/API key

### User Profile Data Sent in API Calls
- user_id: 98755150
- nationality: US
- native_lang: 1 (English)
- lang_id: 1 (English)
- Device: iPhone 13 Pro Max, iOS 26.4
- App version: 6.3.0

---

## 2026-04-05 — API Structure Mapped (from community clone)

### Probable API Shape (from francislainy/hellotalk on GitHub)
Analyzed the most complete community clone. The real HelloTalk API likely follows a similar pattern:
- Base path: `/api/v1/ht/{resource}`
- Resources: users, moments, messages, chats, followships, comments
- All IDs are UUIDs
- Standard REST CRUD + specialized actions (like, unlike, reply)
- Moments support: create, edit, delete, like/unlike, comment, reply to comments
- Messages support: send, edit, delete, plus chat/conversation grouping
- Followships: follow/unfollow with from/to user queries

### Web Client Blocks Automated Access
- `web.hellotalk.com` returns 403 to non-browser requests
- Must use an actual browser with DevTools to capture traffic
- Mobile app uses certificate pinning — needs Frida to bypass

### APK Decompilation Path Identified
- Latest APK: v6.3.12, 318 MB, Android 8.0+
- Can be decompiled with JADX
- Tool exists to auto-extract API endpoints from APKs: `ApiEndpointExtractor`
- This would reveal: real base URLs, auth scheme, cert pinning impl, endpoint paths

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
