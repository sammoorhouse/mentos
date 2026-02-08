CREATE TABLE IF NOT EXISTS goal_drift_events (
  id TEXT PRIMARY KEY,
  goal_id TEXT NOT NULL,
  triggered_at TEXT NOT NULL,
  weeks_off_track INTEGER NOT NULL,
  message TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  FOREIGN KEY(goal_id) REFERENCES goals(id)
);

CREATE INDEX IF NOT EXISTS goal_drift_events_goal_triggered_idx
ON goal_drift_events(goal_id, triggered_at);

CREATE TABLE IF NOT EXISTS goal_adjustments (
  id TEXT PRIMARY KEY,
  goal_id TEXT NOT NULL,
  old_target REAL,
  new_target REAL,
  reason TEXT NOT NULL,
  adjusted_at TEXT NOT NULL,
  FOREIGN KEY(goal_id) REFERENCES goals(id)
);

CREATE INDEX IF NOT EXISTS goal_adjustments_goal_adjusted_idx
ON goal_adjustments(goal_id, adjusted_at);
