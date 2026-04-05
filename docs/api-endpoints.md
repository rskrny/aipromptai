# HelloTalk API & Technical Infrastructure

## What We Know

HelloTalk does **not** have a public API. There's no official documentation. Their GitHub organization (github.com/hellotalk) has zero public repos. This means all endpoint details must come from traffic capture.

## Infrastructure (Confirmed)

- **API Gateway**: Apache APISIX (built on Nginx + LuaJIT / OpenResty)
- **Message serialization**: Protocol Buffers — requests/responses use protobuf, converted to JSON at the gateway
- **Rate limiting**: Implemented at the gateway level using `resty.limit.req`
- **Web client**: `web.hellotalk.com` — this is the easiest way to see API calls (just open browser DevTools > Network tab)
- **WebSocket**: Used for real-time IM, with OpenResty handling protocol conversion

## How to Discover Endpoints

### Easiest Method: Browser DevTools on web.hellotalk.com
1. Go to web.hellotalk.com and log in
2. Open browser DevTools (F12) > Network tab
3. Use the app normally — browse discovery, send messages, view moments
4. Each action shows the actual API calls, URLs, headers, and response bodies
5. Export as HAR file for analysis

### Mobile Method (Advanced)
The mobile app likely uses **certificate pinning**, which blocks standard proxy tools. To capture mobile traffic you'd need:
- A rooted Android device
- Frida (runtime hooking tool) to bypass cert pinning
- mitmproxy to capture the traffic
- This is significantly harder than the browser method

### Auto-Generate API Docs
Once you have captured traffic (HAR or .mitm files), use **mitmproxy2swagger** (github.com/alufers/mitmproxy2swagger) to auto-generate an OpenAPI spec.

## Known Base URLs

| Purpose | URL | Status |
|---|---|---|
| Web client | `web.hellotalk.com` | Confirmed |
| Creator portal | `creators.hellotalk.com` | Confirmed |
| Main site | `www.hellotalk.com` | Confirmed |

Actual API base URL (e.g., `api.hellotalk.com` or similar) needs to be confirmed via traffic capture.

## Community Clone Projects (for reference)

These aren't the real API, but show what the data model probably looks like:
- **francislainy/hellotalk** on GitHub — Spring Boot API clone with TDD/Pact tests
- **leejh3224/react-native-hello-talk** — React Native clone using Firebase

## Next Steps

To map the real API, the simplest approach is:
1. Open `web.hellotalk.com` in Chrome
2. Open DevTools > Network tab
3. Use the app (browse partners, send messages, post moments)
4. Note the actual endpoint URLs, auth headers, and request/response formats
5. Document findings here
