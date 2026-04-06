# HelloTalk Rate Limits — Free vs VIP vs PLUS

## Feature Comparison

| Feature | Free | VIP | Notes |
|---|---|---|---|
| New chats per day | **10** | **25** | First message to a new person counts |
| Translations per day | **10** | **Unlimited** | Built-in translation tool |
| Transliteration | Limited | **Unlimited** | Shows pronunciation |
| Voice-to-text (transcription) | Limited | **Unlimited** | Converts voice messages to text |
| Voiceroom time per day | **90 minutes** | **Unlimited** | Resets at midnight local time |
| Target languages | **1** | **3** | Languages you're learning |
| Grammar corrections | **10** (then needs PLUS) | **10** (then needs PLUS) | PLUS is a separate subscription |
| Ads | Yes | **No ads** | |
| Gender filter in search | No | **Yes** | Filter discovery by gender |
| Nearby user search | No | **Yes** | Find people in your area |
| Visitor page | Locked | **Unlocked** | See who viewed your profile |
| Profile exposure | Normal | **Extra exposure** | Boosted visibility in discovery |

## VIP Pricing

| Plan | Price |
|---|---|
| Monthly | ~$6.99–$12.99/month |
| Annual | ~$45.99–$79.99/year |
| Lifetime | ~$175–$199.99 |

Prices vary by region and promotional periods.

## PLUS Subscription (Separate from VIP)

PLUS unlocks **unlimited grammar corrections**. It's a separate add-on:
- ~$30/quarter to $200/lifetime (pricing varies)
- Without PLUS, you get 10 grammar corrections then hit the paywall

## Is VIP Worth It?

**Yes, if you're serious about getting more interactions.** Here's why:

- **25 vs 10 new chats/day** — 2.5x more outbound conversations
- **Unlimited translations** — huge for actually understanding messages
- **Gender filter** — find the partners you actually want to talk to
- **Visitor page** — see who's checking out your profile (can message them)
- **Extra profile exposure** — confirmed boost in discovery visibility
- **No ads** — cleaner experience

The annual plan at ~$6-7/month is the best value if you don't want to commit lifetime.

## API-Level Rate Limiting

HelloTalk uses `resty.limit.req` (OpenResty's rate limiting module) at their API gateway layer. This means:
- API calls and message frequency are throttled server-side
- Automated/rapid-fire requests will be blocked
- Rate limit specifics (requests per second, etc.) are not publicly documented

## Anti-Automation Notes

- The mobile app likely uses **certificate pinning** — standard proxy interception won't work without Frida
- The web client (web.hellotalk.com) does NOT have cert pinning — easier to observe traffic
- Sending messages too rapidly or in patterns could trigger anti-bot measures
- No confirmed reports of shadow-banning, but it's a reasonable assumption for any social platform
