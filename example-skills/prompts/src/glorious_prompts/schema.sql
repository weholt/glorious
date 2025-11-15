-- Prompts table
CREATE TABLE IF NOT EXISTS prompts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  version INTEGER DEFAULT 1,
  template TEXT NOT NULL,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  meta JSON
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_prompts_name_version ON prompts(name, version);
