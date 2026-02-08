# Breakthroughs + Goal Drift (V1)

Breakthroughs and drift are complementary, deterministic, goal-linked loops:

- Breakthrough path: `Goal -> Insights -> Behaviour change -> Breakthrough -> New goal`
- Drift path: `Goal -> Repeated misses -> Gentle check-in -> Adjust goal`

## Principles

- **Time-based:** patterns must be sustained across weeks.
- **Relative:** progress and drift are compared with user-specific baselines.
- **Goal-linked:** each event belongs to one goal.
- **Narrative:** messages are supportive, flexible, and non-judgmental.

## Data model

- `goals`
  - `id`, `user_id`, `name`, `type`, `baseline_value`, `created_at`
- `goal_progress`
  - `id`, `goal_id`, `week_start`, `metric_value`, `score`
- `breakthroughs`
  - `id`, `goal_id`, `triggered_at`, `improvement_percent`, `duration_weeks`, `message`, `next_goal_suggestion`
- `goal_drift_events`
  - `id`, `goal_id`, `triggered_at`, `weeks_off_track`, `message`, `status`
  - `status in {pending, acknowledged, resolved}`
- `goal_adjustments`
  - `id`, `goal_id`, `old_target`, `new_target`, `reason`, `adjusted_at`

## Weekly scoring

Scoring uses `score in {0,1,2}`:

- `2` (green): strong alignment
- `1` (amber): near baseline / small drift
- `0` (red): off-track

## Breakthrough rules

- `reduce_food_delivery`: >=25% reduction for 3 consecutive green weeks.
- `save_more_money`: monthly surplus for 2 months.
- `healthy_spending`: 4 green weeks out of 6.
- `reduce_nightlife`: >=30% late-night spend reduction for 4 weeks.

## Drift rules

A goal drift event triggers when any condition holds over a 4-week window:

- `red_weeks >= 3`, or
- `4` consecutive amber/red weeks, or
- average weekly metric above baseline with `4` off-track weeks.

When triggered:

1. Create a `goal_drift_events` record.
2. Generate a soft reflection message (supportive, context-first tone).
3. Optional push notification:
   - Title: `Quick check-in on your goal`
   - Body: kind prompt to keep, relax, switch, or pause the goal.

## Adaptive insights context

Monthly insight generation now includes adaptive signals in LLM context:

- Active goals.
- Selected goals.
- Drift counts (`recent_drift_events`, `pending_drift_events`).
- Breakthrough count over last 60 days.
- Estimated ignored insight pressure (`ignored_insights`).
- Optional tone preference (`insight_tone_preference`).

The model does not learn weights between runs; adaptivity comes from richer per-run context.

## Runtime wiring

- Weekly job: `weekly_breakthrough_review`
  1. Seed V1 goals (idempotent).
  2. Compute/update last full week's goal metrics.
  3. Score progress (0/1/2).
  4. Trigger breakthroughs when rule thresholds are met.
  5. Trigger drift check-ins when drift thresholds are met.
  6. Send optional breakthrough and drift notifications.

## CLI

Run manually:

```bash
mentos breakthroughs --notify
```
