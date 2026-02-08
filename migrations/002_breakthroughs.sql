CREATE TABLE IF NOT EXISTS goals (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  name TEXT NOT NULL,
  type TEXT NOT NULL,
  baseline_value REAL,
  created_at TEXT NOT NULL,
  FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS goal_progress (
  id TEXT PRIMARY KEY,
  goal_id TEXT NOT NULL,
  week_start TEXT NOT NULL,
  metric_value REAL NOT NULL,
  score INTEGER NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY(goal_id) REFERENCES goals(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS goal_progress_goal_week_unique
ON goal_progress(goal_id, week_start);

CREATE TABLE IF NOT EXISTS breakthroughs (
  id TEXT PRIMARY KEY,
  goal_id TEXT NOT NULL,
  triggered_at TEXT NOT NULL,
  improvement_percent REAL NOT NULL,
  duration_weeks INTEGER NOT NULL,
  message TEXT NOT NULL,
  next_goal_suggestion TEXT,
  FOREIGN KEY(goal_id) REFERENCES goals(id)
);

CREATE INDEX IF NOT EXISTS breakthroughs_goal_triggered_idx
ON breakthroughs(goal_id, triggered_at);
