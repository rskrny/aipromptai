# CLAUDE.md

## IMPORTANT: Read AGENTS.md First

Before making ANY decisions, read `AGENTS.md`. It contains the master workflow, agent roles, and coordination rules. Every action must follow the 8-stage pipeline defined there.

## Project Purpose

This repo is a research + operations environment for recovering and maximizing a HelloTalk account's visibility. The user is an American learning Chinese with an old account that lost its "whitelisted" high-visibility status.

## User Context

The user is NOT a developer. Never give them scripts to run or technical instructions. Instead:
- Do the research yourself (web searches, analysis)
- Write findings directly into the docs
- Give practical, non-technical advice they can act on in the app
- Explain everything in plain language
- Track progress through the context system

## Workflow

Follow the 8-stage pipeline in AGENTS.md:
1. Describe Problem → 2. Identify Solution → 3. Scope/Assign → 4. Write Code → 5. Review → 6. Test → 7. Plan Release → 8. Release

## Memory System

Before working, always read:
1. `AGENTS.md` — Master instructions and pipeline
2. `docs/context/current-status.md` — Where things stand right now
3. `docs/context/findings-log.md` — What we've discovered
4. `docs/context/decisions-log.md` — What we've decided and why
5. `docs/context/blocked-ideas.md` — What we've ruled out (don't repeat)

After working, always update the relevant context files.

## Repo Structure

```
AGENTS.md                          — Master operations framework (READ FIRST)
CLAUDE.md                          — This file
docs/
  context/
    current-status.md              — Live account status and open questions
    findings-log.md                — All research findings (dated)
    decisions-log.md               — All decisions and rationale
    blocked-ideas.md               — Rejected approaches
  strategy/
    account-recovery.md            — The active recovery playbook
  app-overview.md                  — How HelloTalk works
  api-endpoints.md                 — Technical infrastructure
  matching-algorithm.md            — Discovery algorithm research
  interaction-model.md             — Engagement playbook
  rate-limits.md                   — Free vs VIP vs PLUS limits
scripts/                           — Analysis tools (for Claude, not the user)
tools/                             — Reusable tooling
captures/                          — Raw traffic data (gitignored)
```

## Key Principles

1. Account safety first — never risk a ban
2. Work within the system — optimize behavior, don't hack the API
3. Track everything — update context files after every finding
4. Plain language only — the user isn't technical
5. Follow the pipeline — no skipping stages
