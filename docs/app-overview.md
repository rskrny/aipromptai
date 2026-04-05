# HelloTalk App Overview

## What is HelloTalk?

HelloTalk is a language exchange app that connects native speakers of different languages so they can teach each other. Founded in 2012 in Shenzhen, China. **70+ million registered users** across 200+ countries, supporting 260+ languages. Over 1 million paid users.

## Core Features

### 1. Language Partner Matching
- You set your native language and target language(s)
- The app matches you with people who speak your target language and want to learn yours
- Discovery feed shows potential partners filtered by language, location, age, interests
- "Level Match" pairs users with similar CEFR proficiency levels
- VIP members get extra profile exposure and optimized matching

### 2. Chat / Messaging
- Text, voice, image, video, and sticker messaging
- Built-in translation (10/day free, unlimited VIP)
- Transliteration and text-to-speech
- Correction tools — partners can correct your grammar inline (like Google Docs "Suggest Edits")
- Voice-to-text transcription
- Voice/video calls powered by Agora SDK

### 3. Moments (Social Feed)
- Instagram-like feed where users post text/image updates
- Posts can be in your target language for corrections
- Comments, likes, and corrections from the community
- **Moments in Topics are ranked by engagement (likes + comments), NOT chronologically**
- Adding topic tags increases visibility

### 4. HelloTalk Live & Voicerooms
- Live audio rooms for group conversation practice
- Hosts can create themed rooms (topic-based practice)
- Free users: 90 minutes/day voiceroom time
- VIP: unlimited
- Hosts can earn gifts from viewers (convertible to real money)

### 5. Paid Practice
- Native speakers can enable "Paid Practice" — others pay HT Coins to practice with you
- You earn Diamonds, which convert to HT Coins (100 Diamonds = 110 HT Coins)
- HT Coins redeemable for real cash via PayPal or Payoneer monthly

### 6. Creator Portal
- creators.hellotalk.com — host Live events and Voicerooms to earn gifts
- Another monetization path for active users

## Technical Stack (Confirmed)

| Layer | Technology |
|---|---|
| API Gateway | Apache APISIX (Nginx + LuaJIT / OpenResty) |
| Config Store | etcd |
| Message Format | Protocol Buffers (lua-protobuf) |
| Web IM | WebSocket via OpenResty |
| Voice/Video | Agora SDK |
| AI Transcription | Agora Real-Time Transcription + LLM |
| Rate Limiting | resty.limit.req (at gateway level) |
| Legacy Backend | PHP (migrated away from) |
| Mobile Apps | Native iOS and Android |
| Web Client | web.hellotalk.com (limited features) |

### Global Server Locations
- Eastern United States
- Frankfurt (Europe)
- Singapore
- Tokyo
- Hong Kong

Europe-to-Hong Kong latency: ~150ms (optimized from 244ms via dedicated lines).

## Key Questions — ANSWERED

- [x] What does the discovery/matching algorithm prioritize? → Language pair, CEFR level, location, age, interests, VIP status
- [x] How does "online status" affect visibility? → "Show Online Status" setting exists; being online makes you appear approachable
- [x] What are the differences between free and VIP? → See rate-limits.md for full breakdown
- [x] How do Moments get surfaced? → Ranked by engagement (likes + comments) within Topics, NOT chronologically
- [ ] What actions increase your profile's ranking in search results? → VIP confirmed to give "extra exposure"; other factors still unclear
- [x] How does the correction system work? → Inline editor like Google Docs suggest mode; earns badges
- [x] What rate limits exist? → See rate-limits.md
