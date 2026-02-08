# Mentos Client-Server Architecture (Proposed)

This document captures the target architecture for evolving Mentos from a local single-user CLI into a full client-server product with mobile clients, visual progress tracking, and breakthrough mechanics.

## 1) High-level architecture overview

System structure:

Client  
→ Mentos API Server  
→ Data Store  
→ Insight Engine (LLM)  
→ Notification Service

Initial deployment:
- Runs entirely on a local Mac.
- CLI is the only client.
- SQLite database.
- Cron-style background jobs.
- iOS notifications via Pushcut, Pushover, or ntfy.

Future deployment:
- Mobile app (iOS/Android).
- Hosted API.
- Multi-user.
- Postgres database.
- Real-time notifications.

## 2) Core system components

### 2.1 Client layer

Current client:
- Mentos CLI.

Responsibilities:
- Trigger sync.
- Show insights.
- Show weekly progress.
- Configure goals and pots.
- View breakthroughs.

Future clients:
- iOS app.
- Web dashboard.

Future responsibilities:
- Visual weekly dot tracking.
- Breakthrough screens.
- Goal selection.
- Notification preferences.

### 2.2 API server

Runs as a local service.

Responsibilities:
- Store and manage user data.
- Connect to Monzo.
- Run scheduled jobs.
- Generate insights.
- Detect breakthroughs.
- Send notifications.

Core endpoints:
- `GET /health`
- `GET /insights`
- `GET /goals`
- `GET /breakthroughs`
- `POST /goals`
- `POST /sync`
- `POST /notifications/test`

### 2.3 Data store

Initial database:
- SQLite (local file).

Future database:
- Postgres (hosted).

Main tables:
- `users`
- `monzo_connections`
- `accounts`
- `pots`
- `transactions`
- `aggregates_daily`
- `goals`
- `goal_progress`
- `insights`
- `breakthroughs`
- `notifications`
- `job_runs`
- `raw_events`

## 3) Data flow through the system

### Step 1: Transaction ingestion
- Server connects to Monzo API.
- Pulls new transactions.
- Stores normalized transaction records.
- Stores raw payload for debugging.

### Step 2: Aggregation
- Daily and weekly spending aggregates computed.
- Category totals calculated.
- Baselines updated when needed.

### Step 3: Insight generation
- Server prepares a context object:
  - Recent transactions.
  - Weekly category totals.
  - Active goals.
  - Progress metrics.
- Sends context + insight prompts to ChatGPT.
- Receives insight messages.
- Stores them in `insights` table.

### Step 4: Goal scoring
- Deterministic weekly scoring:
  - Green
  - Amber
  - Red
- Scores stored in `goal_progress` table.

### Step 5: Breakthrough detection
- Check last N weeks for sustained improvement.
- If conditions met:
  - Create breakthrough record.
  - Trigger breakthrough message via LLM.

### Step 6: Notification dispatch
- Insight or breakthrough converted into a notification.
- Sent to iOS via notification provider.

## 4) Insight engine (LLM-driven)

The system does not hard-code insight logic.

Each insight is a “vibe directive” like:
- “Watch for expensive everyday spending.”
- “Look for too much food delivery.”
- “Check late-night spend vs health goals.”

Server sends:
- User goals.
- Recent spending patterns.
- Aggregates.
- Relevant context.

to ChatGPT.

ChatGPT returns:
- `headline`
- `message`
- `suggested_action`
- `severity`

## 5) Goals and insights relationship

Goals are high-level intentions.

Examples:
- Save more money.
- Healthy spending.
- Healthy eating.
- Reduce nightlife.
- Build investment habit.

Insights are conversational nudges that align with goals.

Mapping is loose, not rule-based.

Example:
- Goal: save money.
- Possible insights:
  - Food delivery too high.
  - Too much premium retail.
  - Cash sitting idle.

- Goal: healthy eating.
- Possible insights:
  - Frequent fast food.
  - Late-night food purchases.

## 6) Breakthrough engine

Runs weekly.

Responsibilities:
- Compute goal progress.
- Assign weekly score.
- Detect sustained improvements.
- Trigger breakthrough events.

Breakthrough triggers:
- Sustained green weeks.
- Improvement above baseline.
- Behaviour change over time.

Breakthrough output:
- Celebration message.
- Impact summary.
- Next goal suggestion.

## 7) Scheduler and job system

Jobs run locally using cron-style scheduling.

Main scheduled jobs:

Transaction sync job:
- Every 10–15 minutes.

Daily sweep job:
- 00:05 local time.
- Moves surplus from daily pot to savings pot.

Nightly insight job:
- 00:10 local time.
- Generates insights.
- Sends notification.

Weekly goal scoring job:
- Once per week.
- Updates weekly dot.
- Checks for breakthrough.

Monthly review job:
- First of month.
- Generates long-form financial report.

## 8) Notification system

Abstracted notification interface.

Initial provider options:
- Pushcut.
- Pushover.
- ntfy.

Notification types:

Insight notification example:
> “You’ve spent £96 on delivery this week.  
> That’s higher than your usual.  
> Worth a grocery run tomorrow?”

Breakthrough notification example:
> “You’ve cut delivery by £50/week for three weeks.  
> That’s real progress.  
> Ready to start a savings goal?”

## 9) Security model

Local-first but still secure.

Rules:
- All secrets stored in environment variables.
- Monzo tokens encrypted at rest.
- Minimal API scopes.
- Audit log for:
  - Transfers
  - Notifications
  - Breakthroughs

Health endpoint for monitoring.

## 10) Local deployment model

Everything runs on a single Mac.

Processes:
- `mentos-api`: local service.
- `mentos-cron`: scheduled job runner.

SQLite database file:
- `mentos.db`

Startup modes:

Development:
- `pnpm dev`

Production (local):
- `pnpm start`

Optional:
- `launchd` service to start on boot.

## 11) Future scaling path

Phase 1:
- Single user.
- Local Mac.
- CLI.
- SQLite.
- Push notifications.

Phase 2:
- Hosted API.
- Postgres.
- OAuth for multiple users.
- Mobile app.

Phase 3:
- Real-time streaming insights.
- Behaviour prediction.
- Bank-agnostic integrations.
- Cross-health and financial goals.

## 12) Minimum viable data flow summary

1. Sync transactions from Monzo.
2. Aggregate spending.
3. Send context to ChatGPT for insights.
4. Score goal progress weekly.
5. Detect breakthroughs.
6. Send iOS notifications.
7. Display via CLI (later mobile app).

## 13) Core principle of the system

The architecture is:
- LLM-first for insights.
- Deterministic for scoring.
- Narrative for motivation.
- Local-first for privacy.
- Gamified for behaviour change.

Goal:
- Turn financial behaviour into a visible, motivating loop like fitness tracking.
