-- Events table for telemetry
CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
  category TEXT,
  event TEXT,
  project_id TEXT,
  skill TEXT,
  duration_ms INTEGER,
  status TEXT,
  meta JSON
);

CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
CREATE INDEX IF NOT EXISTS idx_events_category ON events(category);
CREATE INDEX IF NOT EXISTS idx_events_skill ON events(skill);
