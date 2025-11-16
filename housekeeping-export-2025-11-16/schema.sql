CREATE TABLE notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    tags TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)

CREATE VIRTUAL TABLE notes_fts USING fts5(
    content,
    tags,
    content='notes',
    content_rowid='id'
)

CREATE TABLE 'notes_fts_data'(id INTEGER PRIMARY KEY, block BLOB)

CREATE TABLE 'notes_fts_idx'(segid, term, pgno, PRIMARY KEY(segid, term)) WITHOUT ROWID

CREATE TABLE 'notes_fts_docsize'(id INTEGER PRIMARY KEY, sz BLOB)

CREATE TABLE 'notes_fts_config'(k PRIMARY KEY, v) WITHOUT ROWID

CREATE TABLE _skill_schemas (
                skill_name TEXT PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )

CREATE TABLE issues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'open',
    priority TEXT DEFAULT 'medium',
    source_note_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_note_id) REFERENCES notes(id) ON DELETE SET NULL
)

CREATE TABLE testskill_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)