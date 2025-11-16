-- AI skill database schema

CREATE TABLE IF NOT EXISTS ai_embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    embedding BLOB NOT NULL,
    metadata TEXT,
    model TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ai_embeddings_model ON ai_embeddings(model);
CREATE INDEX IF NOT EXISTS idx_ai_embeddings_created ON ai_embeddings(created_at);

CREATE TABLE IF NOT EXISTS ai_completions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt TEXT NOT NULL,
    response TEXT NOT NULL,
    model TEXT NOT NULL,
    provider TEXT NOT NULL,
    tokens_used INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ai_completions_model ON ai_completions(model);
CREATE INDEX IF NOT EXISTS idx_ai_completions_created ON ai_completions(created_at);
