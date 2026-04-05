# HelloTalk API Endpoints

Discovered endpoints from traffic analysis. This is a living document — update as new endpoints are found.

## Base URLs

| Environment | URL |
|---|---|
| API | `https://api.hellotalk.com` (TBD — confirm via traffic capture) |
| CDN | TBD |
| WebSocket | TBD |

## Authentication

- **Method**: TBD (likely JWT or session token)
- **Login flow**: TBD
- **Token refresh**: TBD

## Endpoints

### User / Profile

| Method | Path | Description | Notes |
|---|---|---|---|
| GET | `/user/profile` | Fetch own profile | TBD |
| PUT | `/user/profile` | Update profile | TBD |
| GET | `/user/{id}` | Fetch another user's profile | TBD |

### Discovery / Matching

| Method | Path | Description | Notes |
|---|---|---|---|
| GET | `/discovery` | Get partner suggestions | TBD — params for language, location, filters? |
| GET | `/search` | Search for users | TBD |

### Messaging

| Method | Path | Description | Notes |
|---|---|---|---|
| GET | `/conversations` | List conversations | TBD |
| POST | `/messages` | Send a message | TBD |

### Moments (Social Feed)

| Method | Path | Description | Notes |
|---|---|---|---|
| GET | `/moments` | Fetch moments feed | TBD |
| POST | `/moments` | Create a moment | TBD |
| POST | `/moments/{id}/like` | Like a moment | TBD |
| POST | `/moments/{id}/comment` | Comment on a moment | TBD |

### Corrections

| Method | Path | Description | Notes |
|---|---|---|---|
| POST | `/corrections` | Submit a correction | TBD |

---

*Fill in by running `python scripts/parse-traffic.py` against captured traffic.*
