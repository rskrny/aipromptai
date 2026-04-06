# Current Status

**Last updated**: 2026-04-06

## Account Profile
- **User**: American learning Chinese (Mandarin)
- **Account age**: Old (pre-2023, possibly much older)
- **Subscription**: FREE (not VIP)
- **Current visibility**: Severely degraded — 0-2 inbound messages/day (was 40+/day)
- **Moments engagement**: Barely any
- **Warnings/suspensions**: None received
- **Location history**: Highly unstable — Europe (2023) → China → US, with VPN usage throughout
- **Current location**: US (assumed)

## Diagnosis — CONFIRMED (2026-04-06)

### ROOT CAUSE: Profile Lock + Search Index Exclusion

**CONFIRMED via API:** The `go_user_search/v2/filter` endpoint returns error code 6000: `"Get Search User Plan Failed"` for this account. The search service REFUSES to create a discovery index entry. This is not a ranking issue — the account is completely excluded from the search index.

**CONFIRMED via app:** HelloTalk assistant bot displays message: "Due to system maintenance, you cannot modify your profile. All other functions won't be affected." This is a profile lock disguised as maintenance.

**CONFIRMED via API scan:** Scanned all 33 pages (491 users) of discovery results. Account 98755150 does NOT appear on any page. Every visible user has rank_score 5,000-33,999. This account is not ranked low — it is excluded entirely.

**Contributing factors:**
1. Profile is LOCKED — "system maintenance" message blocks all modifications
2. Location data CORRUPTED — choose_place endpoint returns random countries (China, Vietnam, Morocco, Nigeria) due to VPN/country-hopping history
3. `is_real_auth: false` — face verification not recognized despite being done 2 years ago in China
4. `verify_status: 2` — unknown verification state
5. `expose_feature_used: false` — never used exposure boosts despite 61 moments
6. Free tier, no VIP

## What We Know For Sure
- [x] Free account, not VIP (vip_stat=1, vip_type=0, current_vip_level="Normal")
- [x] Profile is LOCKED by "system maintenance" — cannot modify profile
- [x] Search plan error 6000 — completely excluded from discovery index
- [x] Location data corrupted — choose_place returns random countries
- [x] is_real_auth: false, verify_status: 2
- [x] Moments still distribute normally — visitors come from moments feed
- [x] 1,070 followers, 173 following, 146 mutual
- [x] 62 moments posted, exposing_count: 0
- [x] Nearby tab works (shows 491 users in Hana, Hawaii)
- [x] Messaging works normally
- [x] No warnings or suspensions ever received

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
Two-pronged: unlock old account + optimize new account. See details below.

## Technical Status (as of 2026-04-06)

### ENCRYPTION FULLY CRACKED
- **Scheme**: X25519 key exchange + AES-256-ECB with PKCS7 padding
- **Library**: Google Tink (com.google.crypto.tink.subtle.X25519) + NetEase HTProtect SDK
- **Server public key**: `f684f611b895a5d3abc124a20ca2dfd397662318cfd4fd74b80aba478c17ca68`
- **Header format**: `x-ht-pub` = server_pub_hex + client_pub_hex (128 hex chars)
- **Response format**: AES-ECB encrypted, then gzipped
- **Working client keys saved in**: `captures/our_keys.json`
- **We can decrypt ANY endpoint response from the mobile API**

### Web Client Also Cracked
- **Web IM protocol**: XTEA encryption, decrypted via JSON.parse hooks in Chrome
- **Web session**: connects via `web.hellotalk8.com/im/lg/sync/{uuid}`
- **Chrome debug port**: 9222 with remote debugging

### Key API Intelligence
- **Ranking formula** (max 33,999): `head_beauty(8000) + hobby(1000) + is_learn_native_lang(10000) + real_avatar(4000) + self_introduction(1000) + sex_match(9999)`
- **All visible users** have: user_type=3, user_status=[0], beauty_score 0.70+, rank_score 5000-33999
- **Boost system**: virtual_type 6 and 14, products id 18-21 (500-3000 impressions, 159-1794 coins)
- **Boost status**: remain_times=0, expose_state=0, total_remain_times=0

### APK Decompiled
- HelloTalk 6.3.12 fully decompiled with JADX at `/c/tmp/jadx-output/`
- All 300+ Retrofit API endpoints extracted
- Native crypto in `libNetHTProtect.so` (NetEase) + `libttcrypto.so` (BoringSSL)
- Encryption class: `com.hellotalk.feature.common.shared.configure.entity.SecretDataModel`
- AES implementation: `com.hellotalk.utils.encryption.DataUtils` (AES/ECB/PKCS7Padding)

## What We Cracked (2026-04-06)

1. **Web IM protocol fully decrypted** — XTEA encryption broken via JSON.parse/TextDecoder hooks
2. **Mobile API partially accessible** — boost status, product list, language settings work unencrypted
3. **Mobile API encryption identified but not broken** — `ht/encbin` uses unknown 256-bit EC curve (not P-256, SM2, or secp256k1). Key format = 128 hex chars (64-byte xy coords, no 04 prefix)
4. **Web client encryption identified** — RSA+AES (JSEncrypt+CryptoJS, AES-ECB, PKCS7) for analytics; XTEA for IM protocol
5. **Boost system fully mapped** — types 6 and 14, all products/prices known. Account has 0 boosts, 0 exposure.
6. **Message source analysis** — only 1/142 messages came from "recommend" (discovery). Account is invisible.

## Immediate Next Steps

### OLD ACCOUNT (98755150)
1. **EMAIL SENT** to support@hellotalk.com demanding profile unlock and discovery restoration
2. **Keep posting moments** — moments feed still distributes content, drives visitors
3. **Monitor** search plan status via API (error 6000 check) — auto-detect when/if lock lifts
4. If lock lifts: immediately optimize rank_score using known formula

### NEW ACCOUNT (username: u_sam749, email: Ryan@brandpal.ai)
1. **GET THE USER ID** — needed to monitor via API. Options:
   - Set up Proxyman on the second phone pointing to first phone's IP
   - Or: check app Settings > Account/About for numeric ID
   - Or: find it in any HelloTalk URL/share link from the new account
2. **Once we have the ID**: verify it appears in discovery, check rank_score, optimize
3. **Day 1 optimization**: clear face photo (beauty_score 0.70+), face verification (real_avatar=4000), native=English learning=Chinese (10000 pts), bio (1000), hobbies (1000)
4. **Post first moment** with photo + "please correct me" tag
5. **Do NOT log into old account on same device** — risk of account linking

### TOOLS BUILT (ready to use)
- `scripts/ht-encrypted-client.py` — full encrypted API client (discovery, profile, probe, monitor)
- `scripts/monitor-visibility.py` — continuous search plan + discovery check
- `scripts/web-bot.py` — web automation (intercept, like-moments, view-profiles)
- `scripts/extract-crypto.py` — Chrome crypto extraction
- `scripts/api-probe.py` — endpoint probing
- `captures/our_keys.json` — working X25519 keys for old account
- `captures/probe_auth.json` — auth token for old account
