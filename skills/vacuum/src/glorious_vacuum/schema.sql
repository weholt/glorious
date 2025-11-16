-- Vacuum operations tracking
CREATE TABLE IF NOT EXISTS vacuum_operations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  mode TEXT NOT NULL,
  items_processed INTEGER DEFAULT 0,
  items_modified INTEGER DEFAULT 0,
  started_at TEXT DEFAULT CURRENT_TIMESTAMP,
  completed_at TEXT,
  status TEXT DEFAULT 'running'
);

CREATE INDEX IF NOT EXISTS idx_vacuum_status ON vacuum_operations(status);
