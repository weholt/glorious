-- Planner queue for task management
CREATE TABLE IF NOT EXISTS planner_queue (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  issue_id TEXT NOT NULL,
  priority INTEGER DEFAULT 0,
  status TEXT DEFAULT 'queued',
  project_id TEXT,
  tags TEXT,
  important INTEGER DEFAULT 0,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_planner_status_priority ON planner_queue(status, priority DESC);
CREATE INDEX IF NOT EXISTS idx_planner_project ON planner_queue(project_id);
