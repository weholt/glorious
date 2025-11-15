-- Links between entities
CREATE TABLE IF NOT EXISTS links (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  kind TEXT NOT NULL,
  a_type TEXT NOT NULL,
  a_id TEXT NOT NULL,
  b_type TEXT NOT NULL,
  b_id TEXT NOT NULL,
  weight REAL DEFAULT 1.0,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_links_a ON links(a_type, a_id);
CREATE INDEX IF NOT EXISTS idx_links_b ON links(b_type, b_id);
CREATE INDEX IF NOT EXISTS idx_links_kind ON links(kind);
