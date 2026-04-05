# Decisions Log

Record of every decision made and the reasoning behind it.

---

## 2026-04-05 — Project Setup

**Decision**: Build a systematic agent-based workflow instead of ad-hoc research.
**Reasoning**: The user wants reliable, repeatable results. A pipeline (Describe → Identify → Scope → Code → Review → Test → Plan → Release) ensures nothing falls through the cracks and we can track what works.

**Decision**: Focus on account recovery before building automation tools.
**Reasoning**: No point building tools if the account is shadow-banned. Fix visibility first, then optimize engagement.

**Decision**: Do NOT recommend creating a new account.
**Reasoning**: HelloTalk prohibits multiple accounts and can detect device-level bans. A fresh account on the same device/phone number could get immediately flagged. Better to recover the existing account.
