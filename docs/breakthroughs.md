# Breakthroughs (V1)

Breakthroughs are a deterministic, goal-linked reward loop:

`Goal -> Insights -> Behaviour change -> Breakthrough -> New goal`

## Principles

- **Time-based:** improvements must be sustained across weeks.
- **Relative:** compared with a user-specific baseline.
- **Goal-linked:** each breakthrough belongs to a single goal.
- **Narrative:** message output is encouraging and coaching-led.

## Data model

- `goals`
  - `id`, `user_id`, `name`, `type`, `baseline_value`, `created_at`
- `goal_progress`
  - `id`, `goal_id`, `week_start`, `metric_value`, `score`
- `breakthroughs`
  - `id`, `goal_id`, `triggered_at`, `improvement_percent`, `duration_weeks`, `message`, `next_goal_suggestion`

## Weekly scoring

Scoring uses `score in {0,1,2}`:

- `2` (green): strong alignment
- `1` (amber): near baseline / small drift
- `0` (red): off-track

## V1 rules

- `reduce_food_delivery`: >=25% reduction for 3 consecutive green weeks.
- `save_more_money`: monthly surplus for 2 months.
- `healthy_spending`: 4 green weeks out of 6.
- `reduce_nightlife`: >=30% late-night spend reduction for 4 weeks.

## Runtime wiring

- Weekly job: `weekly_breakthrough_review`
  1. Seed V1 goals (idempotent).
  2. Compute/update last full week's goal metrics.
  3. Score progress (0/1/2).
  4. Trigger breakthroughs when rule thresholds are met.
  5. Send optional push notification:
     - Title: `You’ve hit a breakthrough.`
     - Body: celebration + impact + next goal suggestion.

## CLI

Run manually:

```bash
mentos breakthroughs --notify
```
