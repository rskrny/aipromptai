# Current Status

**Last updated**: 2026-04-11

## Account Profile
- **User**: American learning Chinese (Mandarin)
- **Account age**: Old (pre-2023, possibly much older)
- **Subscription**: FREE (not VIP)
- **Current visibility**: Severely degraded — 0-2 inbound messages/day (was 40+/day)
- **Moments engagement**: Barely any
- **Warnings/suspensions**: None received
- **Location history**: Highly unstable — Europe (2023) → China → US, with VPN usage throughout
- **Current location**: US (assumed)

## Diagnosis — UPDATED (2026-04-11)

### ROOT CAUSE: Search Index Exclusion — account in PARTIAL REBUILD state

**STATE AS OF 2026-04-11 (encrypted probe run from GitHub Actions):**
- Profile lock LIFTED — user reports they can now edit profile fields. "System maintenance" message is gone. No warnings. Likely cleared by HelloTalk support in response to our 2026-04-06 unlock email.
- **`filter` endpoint state CHANGED**: 2026-04-06 returned `code 6000 "Get Search User Plan Failed"`. 2026-04-11 returns `code 4000 "Get Params Failed"`. Same endpoint, same params — the specific exclusion error is gone, replaced by a different error at a later pipeline stage.
- **`recommend` endpoint still excluded** but with a NEW error: `code 6000 "user flow up failed"` (previously "Get Search User Plan Failed"). User is not yet appearing in discovery feed, but the reason is different — suggests an incomplete rebuild rather than an explicit exclusion.
- **Location corruption RESOLVED**: `nearby_count` returns `{"full_country": "United States", "display_city": "Hana"}` cleanly. On 2026-04-06, `choose_place` was returning random countries. That pollution is cleared.
- **Ghost `lang: 13, is_temp: 1`** still present on `get_user_langs` alongside the legitimate `lang: 2` Chinese. Possibly a residual blocker on the ranking / indexing side.
- Visibility symptomatically still broken for the user — moments get ~10 likes (follow-graph), no new stranger DMs. Effects of the state change may take hours or days to manifest to the user.
- Face verification PERMANENTLY LOCKED OUT — user cannot redo face verification because they did it once in China 2 years ago. App blocks re-verification. `is_real_auth: false` + `verify_status: 2` is stuck; the 4000 ranking points from `real_avatar` are unreachable through normal means.
- Privacy settings confirmed correct: Who Can Find Me = Everyone, Languages = Native English / Learning Chinese, hobbies filled, photo is clear face.

### Working theory (revised 2026-04-11 post-encrypted-probe)
The account was in a fully-excluded state on 2026-04-06. Between 2026-04-06 and 2026-04-11, the profile lock lifted (support action) and the backend began a partial rebuild. Location corruption has cleared, and the filter endpoint has progressed to a later pipeline stage. The recommend feed still refuses the user but with an error that suggests an incomplete rebuild rather than permanent exclusion. We are watching a recovery-in-progress. The ghost lang 13 and/or one more support push may be what's needed to complete it.

**HISTORICAL (2026-04-06) — still valid technical state on server unless we re-check:**
- `go_user_search/v2/filter` returned error code 6000 `"Get Search User Plan Failed"` — search service refused to index this account
- Discovery scan of 491 users: account 98755150 absent from every page
- Location data corrupted — `choose_place` returned random countries (China, Vietnam, Morocco, Nigeria)
- Free tier, no VIP, `expose_feature_used: false`

### Current hypothesis (2026-04-11)
The profile lock and the search plan exclusion are separate server-side restrictions. Support cleared the lock but not the exclusion. The exclusion may be self-healing (rebuilt on next profile write event) or may need a second support push. Plan: force profile write events to trigger rebuild, hit unencrypted `post_recommend_btn` to inject into recommend feeds, and open external-pressure fronts (App Store complaint, Trustpilot, LinkedIn to staff).

## What We Know For Sure
- [x] Free account, not VIP (vip_stat=1, vip_type=0, current_vip_level="Normal")
- [x] **PROFILE LOCK LIFTED (2026-04-11)** — user can edit profile, no warning messages, likely cleared by support in response to 2026-04-06 email
- [x] **BIO REWRITTEN (2026-04-11)** — user removed "赚钱" (make money) keyword from the Chinese self-introduction. Replaced with pure language-learning intent text. This removes the likely commercial-intent moderation trigger that may be what got the account swept into a suppression bucket in early 2023 when HelloTalk updated their content policy scanner.
- [x] **SUPPORT FOLLOW-UP EMAIL SENT (2026-04-11)** — second email to support@hellotalk.com requesting escalation to senior trust & safety engineer and explicit re-indexing of account. Mentions preparing App Store complaint as stated consequence. Does not mention bio change (to avoid admitting fault for pre-existing content).
- [x] Search plan error 6000 "Get Search User Plan Failed" (2026-04-06) has since advanced to error 4000 "Get Params Failed" on filter endpoint, and error 6000 "user flow up failed" on recommend endpoint (2026-04-11) — different errors at later pipeline stages, suggesting partial rebuild in progress
- [x] Visibility still symptomatically broken as of 2026-04-11 — zero stranger DMs, moments get ~10 likes (likely follow-graph, not discovery). 1 profile view on 2026-04-11 evening but attributed to reciprocal action from a liked photo, not discovery pickup.
- [x] Face verification PERMANENTLY BLOCKED — app refuses to let user re-verify; stuck with stale record from China
- [x] Location data CORRUPTED on 2026-04-06 (choose_place returned random countries), RESOLVED by 2026-04-11 (nearby_count returns clean United States/Hana)
- [x] Ghost lang 13 (is_temp: 1) still present on get_user_langs as of 2026-04-11. Not visible in app UI.
- [x] is_real_auth: false, verify_status: 2 (2026-04-06, not re-checked yet)
- [x] Moments still distribute normally — visitors come from moments feed
- [x] 1,070 followers, 173 following, 146 mutual
- [x] 62+ moments posted, exposing_count: 0
- [x] Nearby tab works (shows 491-493 users in Hana, Hawaii)
- [x] Messaging works normally
- [x] No warnings or suspensions ever received
- [x] Profile location: Boston, United States
- [x] HelloTalk ID: @slamjacket
- [x] Auth token in `scripts/probe-commands.sh` valid until 2026-05-02 — can hit unencrypted endpoints from any device
- [x] GitHub Actions monitoring (ht-monitor workflow) operational as of 2026-04-11, runs on push to probe scripts, hits plain + encrypted API probes + endpoint discovery sweep + public page fetch, commits results to monitor/ and docs/research/

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
