# HelloTalk Rate Limits & Throttling

## Known Limits (from app behavior)

| Action | Free Limit | VIP Limit | Notes |
|---|---|---|---|
| New conversations/day | ~10? | Unlimited? | Needs verification |
| Moments posts/day | TBD | TBD | |
| Translations/day | Limited | More/Unlimited | Built-in translation feature |
| Voice-to-text/day | Limited | More | |
| Discovery views | TBD | TBD | May be infinite scroll |

## API-Level Rate Limits

To be discovered via traffic analysis. Look for:
- `X-RateLimit-*` headers
- `429 Too Many Requests` responses
- Response body error codes indicating throttling
- Exponential backoff patterns in the client code (from APK decompilation)

## Anti-Automation Detection

HelloTalk likely has some form of bot detection. Watch for:
- Device fingerprinting
- Behavioral analysis (message timing patterns)
- CAPTCHA triggers
- Account flags/shadow bans after suspicious activity

## Safe Testing Guidelines

- Use your own account only
- Keep request rates human-like (don't blast the API)
- Add random delays between actions
- Monitor for any account warnings or restrictions
