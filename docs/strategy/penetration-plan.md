# Penetration Plan — Breaking Through the Visibility Wall

**Created**: 2026-04-06
**Status**: ACTIVE

---

## First Principles Analysis

### The Core Problem (Restated)
The account has a **hard visibility penalty**. We know this because:
- 95% drop (40→2 msgs/day) is NOT gradual decay — it's a flag being set
- Zero warnings means it's algorithmic, not manual moderation
- The drop correlates with location chaos (Europe→China→US+VPN)
- Basic behavioral changes (posting more, being active) won't clear a hard flag

### What Controls Visibility
From traffic analysis, HelloTalk's visibility system has these components:

```
[User Signals] → [Trust Score Engine] → [Visibility Weight] → [Discovery Ranking]
                                                              [Moments Distribution]
                                                              [Search Placement]
```

**Inputs we've confirmed:**
1. Location (GPS coords sent with every request)
2. Device fingerprint (x-ht-did header)
3. Account age & history
4. VIP status
5. Boost inventory (virtual_type: 14, currently depleted)
6. Activity patterns (API call frequency/timing)
7. Content engagement (likes, corrections received)
8. Language pair (native + learning)

**Outputs we need to find:**
- Trust score / account flags (hidden in encrypted profile response)
- Visibility weight (hidden in encrypted discovery response)
- Shadow ban status (hidden — no public endpoint)
- Exposure metrics (query_expose_record — encrypted)

### The Key Question
**Is the penalty a "hard flag" (boolean: restricted=true) or a "soft score" (numeric: trust=0.15)?**

If **hard flag**: Only way to fix is (a) find it and understand what clears it, or (b) get support to remove it.
If **soft score**: We need to know the weights so we can overwhelm the negative with positives.

Either way, we need to **see inside the encrypted responses**.

---

## Attack Vectors (Ranked by Feasibility)

### Vector 1: Strip Encryption Headers (IMMEDIATE — test today)
**Hypothesis**: If the client doesn't send `x-ht-pub`, the server falls back to plain JSON.
**Method**: Use Proxyman's request modification to strip the `x-ht-pub` header from all requests.
**Risk**: Low — worst case the request fails with an error.
**What we learn**: If it works, we get plaintext responses for EVERYTHING.

### Vector 2: Web Client JavaScript Extraction (IN PROGRESS)
**Hypothesis**: web.hellotalk.com uses the same API but encryption is in the JS bundle (readable).
**Method**: Fetch and deobfuscate the JS bundles, extract encryption/decryption code.
**Risk**: None — it's public JavaScript.
**What we learn**: Exact encryption algorithm, key derivation, server public key.

### Vector 3: Direct API Replay Without Encryption (IMMEDIATE)
**Hypothesis**: The API accepts unencrypted JSON if Content-Type is application/json instead of ht/encbin.
**Method**: Use the captured JWT bearer token to make direct API calls with httpx/curl.
**Risk**: Low — we're authenticating as the real user.
**What we learn**: Profile data, account flags, trust score — everything.

### Vector 4: Comparative Analysis (NEEDS SECOND ACCOUNT)
**Hypothesis**: Comparing API responses between a "healthy" and "penalized" account reveals the flag.
**Method**: Capture traffic from both accounts, diff the profile/discovery responses.
**Risk**: None if using a friend's account with permission.
**What we learn**: Exactly which field(s) differ between a visible and invisible account.

### Vector 5: Proxyman Scripting (Mac Required)
**Hypothesis**: Proxyman on Mac can run scripts that intercept and log decrypted payloads.
**Method**: Route iPhone traffic through Mac Proxyman, use scripting to capture plaintext.
**Risk**: None.
**What we learn**: Every API response in plaintext as the app decrypts it.

### Vector 6: Older App Version Downgrade
**Hypothesis**: Older HelloTalk versions didn't use ht/encbin encryption.
**Method**: Install an older APK/IPA that sends plain JSON.
**Risk**: Medium — older version might not work with current API.
**What we learn**: Full API access without encryption.

### Vector 7: APK Decompilation (Android Emulator)
**Hypothesis**: The encryption class in the APK contains the algorithm and server public key.
**Method**: Download APK, decompile with JADX, find the encryption class.
**Risk**: None — static analysis only.
**What we learn**: Complete encryption implementation, enabling us to decrypt captured traffic.

### Vector 8: Boost System Exploitation
**Hypothesis**: The boost system (virtual_type: 14) can be triggered or refreshed via API.
**Method**: Call `post_recommend_btn` endpoint directly, observe response.
**Risk**: Low — it's a legitimate app feature.
**What we learn**: How to get visibility boosts without VIP.

---

## Execution Order

### Phase A: Quick Wins (Today)
1. **Vector 1**: Have user enable Proxyman request modification, strip x-ht-pub header
2. **Vector 3**: Build and run API replay script with plain JSON content type
3. **Vector 8**: Probe the boost endpoint

### Phase B: Deep Access (This Week)
4. **Vector 2**: Extract and analyze web client JS (agent researching now)
5. **Vector 5**: Set up Mac Proxyman with scripting if user has a Mac
6. **Vector 7**: Download and decompile APK

### Phase C: Advanced (If Needed)
7. **Vector 4**: Comparative analysis with a friend's clean account
8. **Vector 6**: Older version testing

---

## Tools to Build

1. **API Probe Script** — Makes direct API calls to test unencrypted access
2. **Response Diff Tool** — Compares two accounts' API responses to find penalty flags
3. **Boost Exploiter** — Systematically tests the virtual product / boost system
4. **Proxyman Script** — Logs all decrypted HelloTalk traffic automatically
5. **JS Deobfuscator** — Extracts encryption logic from web client bundles
