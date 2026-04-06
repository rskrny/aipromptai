# HelloTalk API & Technical Infrastructure

## What We Know

HelloTalk does **not** have a public API. No official documentation exists. Their GitHub org (github.com/hellotalk) has zero public repos. The web client at `web.hellotalk.com` blocks automated access (403). The mobile app uses certificate pinning.

## Infrastructure (Confirmed)

- **API Gateway**: Apache APISIX (Nginx + LuaJIT / OpenResty)
- **Message serialization**: Protocol Buffers (lua-protobuf) → converted to JSON at gateway
- **Rate limiting**: `resty.limit.req` at gateway level
- **Web client**: `web.hellotalk.com` (403s non-browser requests — must use actual browser)
- **WebSocket**: Real-time IM via OpenResty protocol conversion
- **Voice/Video**: Agora SDK
- **Legacy backend**: PHP (migrated away from)

### Global Server Nodes
- Eastern United States
- Frankfurt (Europe)
- Singapore
- Tokyo
- Hong Kong

## Probable API Structure (from community clone analysis)

By analyzing `github.com/francislainy/hellotalk` (a Spring Boot clone that mirrors HelloTalk's data model), we can map the likely API shape:

### Base Pattern: `/api/v1/ht/{resource}`

### Users
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/ht/users/{userId}` | Get a user's profile |
| GET | `/api/v1/ht/users` | List/search users (discovery) |
| POST | `/api/v1/ht/users` | Create user (registration) |
| PUT | `/api/v1/ht/users/{userId}` | Update profile |
| DELETE | `/api/v1/ht/users/{userId}` | Delete account |

### Moments (Social Feed)
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/ht/moments/{momentId}` | Get a single moment |
| GET | `/api/v1/ht/moments` | Get moments feed |
| GET | `/api/v1/ht/moments/user?userId={id}` | Get a user's moments |
| POST | `/api/v1/ht/moments` | Create a moment |
| PUT | `/api/v1/ht/moments/{momentId}` | Update a moment |
| PUT | `/api/v1/ht/moments/{momentId}/like` | Like a moment |
| DELETE | `/api/v1/ht/moments/{momentId}/unlike` | Unlike a moment |
| DELETE | `/api/v1/ht/moments/{momentId}` | Delete a moment |

### Comments (on Moments)
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/ht/moments/{momentId}/comments` | List comments on a moment |
| GET | `/api/v1/ht/moments/{momentId}/comments/{commentId}` | Get single comment |
| POST | `/api/v1/ht/moments/{momentId}/comments` | Post a comment |
| PUT | `/api/v1/ht/moments/{momentId}/comments/{commentId}` | Edit a comment |
| DELETE | `/api/v1/ht/moments/{momentId}/comments/{commentId}` | Delete a comment |
| POST | `/api/v1/ht/moments/{momentId}/comments/{commentId}/replies` | Reply to comment |
| GET | `/api/v1/ht/moments/{momentId}/comments/{commentId}/replies` | Get replies |

### Messages / Chats
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/ht/messages/{messageId}` | Get a message |
| GET | `/api/v1/ht/messages` | List all messages |
| POST | `/api/v1/ht/messages` | Send a message |
| PUT | `/api/v1/ht/messages/{messageId}` | Edit a message |
| DELETE | `/api/v1/ht/messages/{messageId}` | Delete a message |
| GET | `/api/v1/ht/messages/chats/{chatId}` | Get a conversation |
| GET | `/api/v1/ht/messages/chats` | List all conversations |

### Followships (Friends/Partners)
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/ht/followship/{followshipId}` | Get a followship |
| GET | `/api/v1/ht/followship` | List all followships |
| GET | `/api/v1/ht/followship/from/user/{userId}` | Who this user follows |
| GET | `/api/v1/ht/followship/to/user/{userId}` | Who follows this user |
| POST | `/api/v1/ht/followship` | Follow a user |
| DELETE | `/api/v1/ht/followship/{followshipId}` | Unfollow |

### Key Data Types
- All IDs are **UUIDs**
- Request/response bodies are **JSON**
- Authentication likely via Bearer token or session cookie

## Other Community Projects

| Project | Tech | Notes |
|---|---|---|
| `francislainy/hellotalk` | Java 17 / Spring Boot | Most complete clone — mirrors full data model |
| `francislainy/hellotalk-ui` | Frontend | UI companion to above |
| `vanpersie-20/HelloTalk` | PHP | Simpler clone with Chinese UI (login=denglu, register=zhuce) |
| `leejh3224/react-native-hello-talk` | React Native / Firebase | Mobile clone |
| `shirakaba/react-nativescript-pikatalk` | React NativeScript | HelloTalk-inspired app |

## What's Still Needed

To get the REAL API (not the clone):
1. **Browser DevTools on web.hellotalk.com** — log in with a real account, open Network tab, capture actual requests
2. The clone gives us the data model shape, but the real URLs, auth headers, and query parameters need traffic capture
3. Real API likely uses protobuf (not JSON) on mobile — web client may use JSON

## APK Analysis Path

Latest APK: v6.3.12 (March 2026, 318 MB, requires Android 8.0+)
- Available on APKPure, Aptoide, Uptodown
- Can be decompiled with JADX to extract: hardcoded URLs, API endpoints, auth logic, cert pinning implementation
- Tool: `ApiEndpointExtractor` (github.com/hangga/ApiEndpointExtractor) — GUI for extracting endpoints from APKs
- The APK would reveal the REAL base URLs, endpoint paths, and authentication scheme
