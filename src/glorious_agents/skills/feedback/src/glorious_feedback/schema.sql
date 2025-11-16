-- Feedback table
CREATE TABLE IF NOT EXISTS feedback (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  action_id TEXT NOT NULL,
  action_type TEXT,
  status TEXT,
  reason TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  meta JSON
);

CREATE INDEX IF NOT EXISTS idx_feedback_action_type ON feedback(action_type);
CREATE INDEX IF NOT EXISTS idx_feedback_status ON feedback(status);
