-- Cache entries table
CREATE TABLE IF NOT EXISTS cache_entries (
  key TEXT PRIMARY KEY,
  value BLOB NOT NULL,
  kind TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  ttl_seconds INTEGER,
  meta JSON
);

-- Index for kind-based queries
CREATE INDEX IF NOT EXISTS idx_cache_kind ON cache_entries(kind);

-- Index for TTL-based cleanup
CREATE INDEX IF NOT EXISTS idx_cache_ttl ON cache_entries(created_at, ttl_seconds);
