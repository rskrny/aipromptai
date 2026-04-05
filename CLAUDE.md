# CLAUDE.md

## Project Purpose

This repo is a research environment for understanding HelloTalk (language exchange app). The goal is to learn how it works under the hood and find ways to get more interactions — more matches, more conversations, more visibility.

## User Context

The user is NOT a developer. Don't give them scripts to run or technical setup instructions. Instead:
- Do the research yourself (web searches, analysis)
- Write findings directly into the docs
- Give practical, non-technical advice they can act on in the app
- When technical work is needed (traffic analysis, APK decompilation), do it or explain results in plain language

## Repo Structure

- `docs/` — Research findings (the main content)
- `scripts/` — Helper scripts for traffic analysis (for Claude to use, not the user)
- `tools/` — Analysis tools
- `captures/` — Raw traffic data (gitignored)

## Key Docs

- `docs/app-overview.md` — How HelloTalk works
- `docs/api-endpoints.md` — Discovered API endpoints
- `docs/matching-algorithm.md` — How matching/discovery works + experiments
- `docs/interaction-model.md` — How interactions drive engagement
- `docs/rate-limits.md` — Limits and throttling
