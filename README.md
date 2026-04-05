# HelloTalk Reverse Engineering

Research environment for understanding HelloTalk's internals — how the app works, its API structure, matching algorithms, and interaction mechanics.

## Goal

Learn how HelloTalk works under the hood and explore ways to optimize interactions (more matches, better visibility, increased engagement).

## Structure

```
docs/           — Research notes and findings
  app-overview.md       — How HelloTalk works at a high level
  api-endpoints.md      — Discovered API endpoints and behavior
  matching-algorithm.md — How the matching/discovery system works
  interaction-model.md  — How interactions (corrections, moments, chat) work
  rate-limits.md        — Known rate limits and throttling behavior
scripts/        — Helper scripts for analysis
  proxy-setup.sh        — mitmproxy setup for traffic capture
  parse-traffic.py      — Parse captured traffic logs
  api-client.py         — Lightweight HelloTalk API client for testing
tools/          — Reusable tooling
  har-analyzer.py       — Analyze HAR files from browser/proxy
captures/       — Raw traffic captures (gitignored)
```

## Approach

1. **Traffic Analysis** — Use mitmproxy/Charles to capture and inspect API calls
2. **APK Analysis** — Decompile the Android APK to understand client-side logic
3. **API Mapping** — Document all endpoints, parameters, and response shapes
4. **Behavior Testing** — Experiment with different interaction patterns to understand ranking/visibility
5. **Automation** — Build scripts to test hypotheses about the matching and engagement systems

## Setup

```bash
pip install -r requirements.txt
```

For traffic capture:
```bash
bash scripts/proxy-setup.sh
```

## Disclaimer

This project is for educational and personal research purposes only. Respect HelloTalk's Terms of Service and other users' privacy.
