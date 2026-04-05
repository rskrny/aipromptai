# AGENTS.md — Master Operations Framework

This file is the master instruction set. Claude MUST read this before making any decisions or taking any actions in this repo. It defines the workflow, the agent roles, and how they coordinate.

---

## Mission

Get this HelloTalk account (American learning Chinese, old account with degraded visibility) back to "whitelisted" status — maximum discovery visibility, maximum inbound messages, maximum engagement. We treat this like a product problem and solve it systematically.

---

## The Pipeline (8 Stages)

Every problem we tackle flows through this pipeline. No skipping stages.

### Stage 1: DESCRIBE PROBLEM
- What exactly is wrong? Be specific with evidence.
- What does "working" look like? Define the success metric.
- What data do we have? What data do we need?

### Stage 2: IDENTIFY SOLUTION
- Research the problem space (web searches, traffic analysis, user reports)
- Generate multiple solution hypotheses
- Rank solutions by: likelihood of success, effort required, risk level
- Pick the best solution with a clear rationale

### Stage 3: SCOPE & ASSIGN WORK
- Break the solution into discrete tasks
- Assign each task to the right agent (see Agent Roles below)
- Define inputs, outputs, and dependencies between tasks
- Set acceptance criteria for each task

### Stage 4: WRITE CODE / CONTENT
- Execute the tasks — write scripts, docs, configs, strategies
- Follow existing patterns in the codebase
- Keep it simple — no over-engineering

### Stage 5: REVIEW
- Check work against acceptance criteria
- Verify no unintended side effects
- Ensure the approach is safe (won't get the account banned)

### Stage 6: TEST
- Run scripts in dry-run mode first
- Validate outputs match expectations
- Test edge cases and failure modes

### Stage 7: PLAN RELEASE
- Sequence the rollout (what happens first, second, third)
- Identify rollback plan if something goes wrong
- Document what the user needs to do (in plain, non-technical language)

### Stage 8: RELEASE
- Execute the plan
- Monitor results
- Document outcomes for future reference

---

## Agent Roles

### Lead Agent (Claude — Main Thread)
- **Role**: Orchestrator, decision-maker, user-facing communicator
- **Responsibilities**: 
  - Read AGENTS.md before every major decision
  - Route work to the right sub-agents
  - Synthesize findings from multiple agents into actionable plans
  - Communicate with the user in plain, non-technical language
  - Maintain the memory system (update context files after every major finding)
  - Own the 8-stage pipeline — ensure nothing is skipped

### Research Agent
- **Role**: Intelligence gathering
- **Responsibilities**:
  - Web searches for HelloTalk behavior, algorithm changes, user reports
  - Analyze traffic captures and API responses
  - Monitor competitor apps for comparison insights
  - Document all findings in `docs/` with sources and confidence levels
- **Trigger**: Stage 1 (Describe Problem) and Stage 2 (Identify Solution)

### Strategy Agent  
- **Role**: Tactical planning for account optimization
- **Responsibilities**:
  - Design engagement experiments (A/B test frameworks)
  - Create content calendars and posting schedules
  - Analyze what's working and what isn't based on results
  - Update `docs/strategy/` with current playbooks
- **Trigger**: Stage 2 (Identify Solution) and Stage 3 (Scope/Assign)

### Code Agent
- **Role**: Build tools and automation
- **Responsibilities**:
  - Write analysis scripts (traffic parsing, data analysis)
  - Build monitoring tools (track visibility metrics over time)
  - Create API clients for testing hypotheses
  - All code goes in `scripts/` or `tools/`
- **Trigger**: Stage 4 (Write Code)

### Review Agent
- **Role**: Quality assurance and safety
- **Responsibilities**:
  - Review all code for bugs and safety issues
  - Check strategies won't trigger HelloTalk's anti-abuse systems
  - Verify findings against multiple sources
  - Flag anything that could risk the account
- **Trigger**: Stage 5 (Review) and Stage 6 (Test)

---

## Memory & Context System

### How It Works
Agents don't share live memory. They coordinate through files in this repo:

```
docs/context/
  current-status.md    — Current state of the account and active experiments
  findings-log.md      — Chronological log of every finding (dated entries)
  decisions-log.md     — Every decision made and why
  blocked-ideas.md     — Ideas we tried that didn't work (so we don't repeat them)
```

### Rules
1. **Before starting any work**: Read `docs/context/current-status.md`
2. **After every significant finding**: Append to `docs/context/findings-log.md`
3. **After every decision**: Append to `docs/context/decisions-log.md`
4. **If something fails**: Document in `docs/context/blocked-ideas.md`
5. **Keep entries dated** with ISO format (YYYY-MM-DD)
6. **Be specific** — "visibility seems low" is useless; "0 inbound messages in 48 hours despite 5 moments posted" is useful

### File Authority
- `AGENTS.md` — This file. The master instruction. Never modify without user approval.
- `CLAUDE.md` — Project-level context for Claude sessions.
- `docs/context/*` — Living memory. Update frequently.
- `docs/strategy/*` — Current active strategies and playbooks.
- `docs/*.md` — Research reference docs (app-overview, api-endpoints, etc.)

---

## Current Problem Statement (Stage 1)

### The Problem
American user learning Chinese. Old HelloTalk account. Previously had high visibility ("whitelisted" — lots of inbound messages, high discovery ranking). Now has degraded visibility — fewer messages, lower discovery placement.

### What "Fixed" Looks Like
- Consistent inbound messages from Chinese speakers (5+ per day)
- Moments posts getting 10+ likes/corrections within 24 hours
- Profile appearing in first few pages of discovery for Chinese speakers learning English

### Hypotheses for Why Visibility Dropped

#### H1: Shadow Ban / Reduced Discoverability
HelloTalk officially acknowledges they "reduce discoverability by redirecting search results or limiting distribution of Moments or results in the Search (Find Partners) Tab." This could be active on the account.
- **Indicators**: Sudden drop in inbound messages, moments getting zero engagement
- **Fix path**: Appeal to support, modify behavior, or reset account signals

#### H2: Account Staleness Penalty
Old accounts that went inactive may be deprioritized in discovery. Many social platforms give "new user boosts" and penalize dormant accounts.
- **Indicators**: Gradual decline correlated with periods of inactivity
- **Fix path**: Sustained high-quality activity to re-signal engagement

#### H3: Algorithm Change
HelloTalk may have changed their ranking algorithm, deprioritizing certain profile types or behaviors.
- **Indicators**: Other long-term users reporting similar drops around the same time
- **Fix path**: Adapt to new algorithm signals

#### H4: Location/IP Mismatch
HelloTalk tracks precise location. If the account was created/active in one location but now used from another, or if VPN usage is detected, this could affect trust scoring.
- **Indicators**: Using VPN, moved cities, travel
- **Fix path**: Consistent location, no VPN, update profile location

#### H5: Profile/Behavior Flags
Past reports, content flags, or pattern-matching on messaging behavior may have accumulated invisible strikes.
- **Indicators**: Any past warnings, message restrictions, or content removals
- **Fix path**: Clean behavior + time, or appeal to support

---

## Active Strategy (Stage 2+)

See `docs/strategy/account-recovery.md` for the current action plan.

---

## Safety Rules

1. **Never automate messaging** — HelloTalk detects bot-like behavior
2. **Never spam** — rapid-fire actions trigger rate limits and flags  
3. **Never use multiple accounts** — HelloTalk explicitly prohibits this
4. **Never bypass security** — no cert pinning bypasses, no token theft
5. **Always keep it human-paced** — any tools we build include random delays
6. **Account safety first** — if there's any risk of a ban, don't do it
