-- Sandboxes table
CREATE TABLE IF NOT EXISTS sandboxes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  container_id TEXT UNIQUE,
  image TEXT,
  status TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  finished_at TEXT,
  exit_code INTEGER,
  logs TEXT
);

CREATE INDEX IF NOT EXISTS idx_sandboxes_status ON sandboxes(status);
