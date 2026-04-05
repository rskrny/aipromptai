# HelloTalk App Overview

## What is HelloTalk?

HelloTalk is a language exchange app that connects native speakers of different languages so they can teach each other. It has ~40M+ users worldwide.

## Core Features

### 1. Language Partner Matching
- Users set their native language and target language(s)
- The app matches you with people who speak your target language and want to learn yours
- Discovery feed shows potential partners filtered by language, location, age, gender

### 2. Chat / Messaging
- Text, voice, and video messaging
- Built-in translation, transliteration, and text-to-speech
- Correction tools — partners can correct your grammar inline
- Voice-to-text transcription

### 3. Moments (Social Feed)
- Instagram-like feed where users post text/image updates
- Posts can be in your target language for corrections
- Comments, likes, and corrections from the community
- Algorithmic feed + chronological option

### 4. HelloTalk Live
- Live audio rooms for group conversation practice
- Hosts can create themed rooms (topic-based practice)

### 5. Courses / Learning
- Structured lessons and vocabulary
- AI-powered tutoring features
- Flashcards and spaced repetition

## Platform Details

- **Platforms**: iOS (Swift), Android (Kotlin/Java)
- **Backend**: Likely a mix of REST APIs and WebSocket for real-time chat
- **CDN**: Images/media served via CDN
- **Push**: Firebase Cloud Messaging (Android), APNs (iOS)

## Key Questions to Answer

- [ ] What does the discovery/matching algorithm prioritize?
- [ ] How does "online status" and "last active" affect visibility?
- [ ] What actions increase your profile's ranking in search results?
- [ ] How do Moments get surfaced to other users?
- [ ] What are the differences between free and VIP features?
- [ ] How does the correction system work technically?
- [ ] What rate limits exist on messaging, Moments posting, and likes?
