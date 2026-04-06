# HelloTalk API — REAL Endpoints (Reverse Engineered)

**Last updated**: 2026-04-05
**Source**: Live traffic capture via Proxyman on iOS (HelloTalk v6.3.0)
**Status**: NO certificate pinning — full HTTPS interception works

---

## Base URL

**`https://api-global.hellotalk8.com`**

Note: The domain is `hellotalk8.com`, NOT `hellotalk.com`.

## CDN Infrastructure (Confirmed)

| Domain | Purpose |
|---|---|
| `api-global.hellotalk8.com` | **Main API** (214+ requests in a single session) |
| `cdn-global.hellotalk8.com` | Global CDN (images, assets) |
| `ali-hk-cdn.hellotalk8.com` | Alibaba Cloud Hong Kong CDN |
| `ali-global-cdn.hellotalk8.com` | Alibaba Cloud Global CDN |
| `hk-head-cdn.hellotalk8.com` | Hong Kong head CDN |
| `mnt-global-cdn.hellotalk8.com` | Global CDN |
| `mmt-vod-cdn.hellotalk8.com` | Video/Voice CDN |
| `cdn-cn.hellotalk8.com` | China-specific CDN |
| `sc.hellotalk8.com` | Unknown (1 request) |
| `hellotalk-app-log-oversea.cn-hongkong...` | Overseas logging (Hong Kong) |

## Server

- **Proxy**: Envoy (confirmed from response headers `server: envoy`)
- **Gateway**: Apache APISIX (confirmed from earlier research)
- **Cache**: `EO-Cache-Status` header present (edge caching)

## Authentication

**Method**: JWT Bearer Token

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHA...
```

### Required Custom Headers

| Header | Value | Description |
|---|---|---|
| `x-ht-os` | `ios` | Platform |
| `x-ht-uid` | `98755150` | User ID |
| `x-ht-did` | `29ea6362a590de...` | Device ID (fingerprint) |
| `x-ht-timezone` | `-10.00` | Timezone offset |
| `X-B3-Spanid` | `0000000000000001` | Distributed tracing (Zipkin/Jaeger) |
| `Content-Type` | `application/json` | Request body format |
| `Accept-Language` | `en-US;q=1.0, zh-Hans-US;q=0.9` | Language preference |
| `User-Agent` | `ios;6.3.0;iPhone14,3;26.4;98755150` | Format: `{os};{app_version};{device_model};{os_version};{user_id}` |

---

## REAL API Endpoints (Captured from Live Traffic)

### Discovery / User Search

| Method | Endpoint | Description |
|---|---|---|
| GET | `/go_user_search/v1/go_user_info/get_user_langs?user_id={uid}` | Get a user's language info |
| GET | `/go_user_search/v2/nearby_count?htntKey={key}&latitude={lat}&longitude={lon}&learnlang={id}&page={n}&sort=distance&userid={uid}` | **Nearby user search** with location |

#### Nearby Search Parameters
- `htntKey`: API key/session token (e.g., `a7e1869d5fd2e7954a683439fca094ff`)
- `latitude` / `longitude`: Precise GPS coordinates
- `learnlang`: Target language code (2 = Chinese)
- `page`: Pagination
- `sort`: Sort order (`distance`)
- `userid`: Your user ID

### Moments (Social Feed)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/v2/moment/latest` | Get latest moments feed |
| POST | `/v2/moment/view_content` | View a specific moment's content |
| POST | `/v2/moment/like` | Like a moment |
| POST | `/v2/moment/query_expose_record` | **Query YOUR exposure/visibility metrics** |
| POST | `/v2/moment/query_expo...` | (truncated — exposure related) |
| POST | `/go_moment/v2/get_moment_tab_info` | Get moment tab configuration |

### Virtual Products / Boost System

| Method | Endpoint | Description |
|---|---|---|
| POST | `/virtual_product/v1/virtual_product/free_recommend_status` | **Check remaining free visibility boosts** |
| POST | `/virtual_product/v1/recommend/post_recommend_btn` | Trigger a recommendation/boost action |

### Translation

| Method | Endpoint | Description |
|---|---|---|
| POST | `/translate/v1/config` | Get translation configuration |

---

## Key API Responses (Captured)

### `free_recommend_status` — Visibility Boost System

**Request Body:**
```json
{
  "os_version": "26.4",
  "nationality": "US",
  "lang_id": 1,
  "native_lang": 1,
  "os_type": 0,
  "user_id": 98755150,
  "app_version": "6.3.0",
  "virtual_type": 14
}
```

**Response Body:**
```json
{
  "status": 0,
  "msg": "success",
  "data": {
    "remain_times": 0,
    "virtual_type": 14
  }
}
```

**Analysis**: `remain_times: 0` means all free recommendation boosts are exhausted. `virtual_type: 14` is the product code for discovery recommendations. This is a key finding — the app has a built-in boost system, and this account's boosts are depleted.

### `query_expose_record` — Visibility Metrics

Response body was in a format that couldn't be previewed on iOS (likely protobuf or compressed). Contains actual exposure/visibility data. Need to export via AirDrop or capture on desktop to decode.

---

## Language Codes (Discovered)

| Code | Language |
|---|---|
| 1 | English |
| 2 | Chinese (Mandarin) |

## Platform Codes

| Code | Platform |
|---|---|
| 0 | iOS |
| 1 | Android (assumed) |

## API Response Format

Standard response wrapper:
```json
{
  "status": 0,          // 0 = success
  "msg": "success",     // Status message
  "data": { ... }       // Response payload
}
```

---

## What's Still Needed

### High Priority
- [ ] Full endpoint list (need to scroll through all 214 captured requests)
- [ ] User profile endpoint — would show account flags/trust score
- [ ] Discovery/partner search endpoint (not just nearby count)
- [ ] `query_expose_record` response decoded (need desktop export)
- [ ] Any endpoint containing `user/info`, `user/profile`, `user/status`, `account/`

### Medium Priority
- [ ] Message sending endpoints
- [ ] Correction endpoints
- [ ] Settings/privacy endpoints
- [ ] Any endpoint with `ban`, `restrict`, `flag`, `trust`, `score`, `rank`, `weight`

### To Get More Data
Export from Proxyman on iOS:
1. Tap ⋯ (More) menu at bottom right
2. Look for Export/Share option
3. Export as HAR or Proxyman format
4. Email it to yourself or share via iCloud/Google Drive
