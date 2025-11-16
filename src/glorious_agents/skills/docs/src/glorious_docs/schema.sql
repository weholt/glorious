-- Documentation management schema

CREATE TABLE IF NOT EXISTS docs_documents (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    epic_id TEXT,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_docs_epic ON docs_documents(epic_id);
CREATE INDEX IF NOT EXISTS idx_docs_created ON docs_documents(created_at);

CREATE TABLE IF NOT EXISTS docs_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    content TEXT NOT NULL,
    changed_by TEXT,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (doc_id) REFERENCES docs_documents(id)
);

CREATE INDEX IF NOT EXISTS idx_versions_doc ON docs_versions(doc_id);

-- Full-text search for documents
CREATE VIRTUAL TABLE IF NOT EXISTS docs_fts USING fts5(
    title,
    content,
    content=docs_documents,
    content_rowid=rowid
);

-- Triggers to keep FTS in sync
CREATE TRIGGER IF NOT EXISTS docs_fts_insert AFTER INSERT ON docs_documents BEGIN
    INSERT INTO docs_fts(rowid, title, content) VALUES (NEW.rowid, NEW.title, NEW.content);
END;

CREATE TRIGGER IF NOT EXISTS docs_fts_delete AFTER DELETE ON docs_documents BEGIN
    DELETE FROM docs_fts WHERE rowid = OLD.rowid;
END;

CREATE TRIGGER IF NOT EXISTS docs_fts_update AFTER UPDATE ON docs_documents BEGIN
    DELETE FROM docs_fts WHERE rowid = OLD.rowid;
    INSERT INTO docs_fts(rowid, title, content) VALUES (NEW.rowid, NEW.title, NEW.content);
END;
