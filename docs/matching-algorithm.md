# HelloTalk Matching / Discovery Algorithm

## How Discovery Works (Hypotheses)

The discovery feed shows potential language partners. Understanding what controls ranking here is the key to getting more interactions.

## Known Factors (from app UI)

- **Language pair**: Must be a complementary match (you speak what they learn, they speak what you learn)
- **Online status**: "Online now" users appear higher
- **Location**: Nearby users may be prioritized
- **VIP status**: VIP members likely get boosted visibility
- **Profile completeness**: Photos, bio, voice intro may affect ranking

## Hypotheses to Test

### H1: Activity recency boosts ranking
- Users who were recently active (sent messages, posted moments) appear higher
- Test: Compare visibility after periods of activity vs inactivity

### H2: Profile engagement rate matters
- Profiles with higher response rates get shown more
- Test: Track response rate vs discovery impressions

### H3: Moments posting increases discovery visibility
- Posting moments acts as a signal of engagement
- Test: Post moments at different frequencies and track partner requests

### H4: Correction activity boosts ranking
- Correcting others' posts signals you're a good partner
- Test: Do corrections for a week, measure discovery traffic

### H5: Time-of-day targeting
- Posting/being active when your target language's native speakers are online
- Test: Compare engagement at different times relative to target timezone

## Experiments

| # | Hypothesis | Method | Status | Result |
|---|---|---|---|---|
| 1 | Activity recency | Track ranking after active vs idle periods | Not started | — |
| 2 | Response rate | Monitor discovery after varying response patterns | Not started | — |
| 3 | Moments frequency | Post 0/1/3/5 moments per day, track results | Not started | — |
| 4 | Corrections | Do 10+ corrections daily for 1 week | Not started | — |
| 5 | Time-of-day | Log engagement by hour | Not started | — |
