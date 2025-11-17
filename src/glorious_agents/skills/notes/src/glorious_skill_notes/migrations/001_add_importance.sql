-- Migration: Add importance level to notes
-- Skill: notes
-- Version: 1
-- Purpose: Allow marking notes as important/critical for easy filtering

-- Add importance column (0=normal, 1=important, 2=critical)
ALTER TABLE notes ADD COLUMN importance INTEGER DEFAULT 0;

-- Create index for importance queries
CREATE INDEX IF NOT EXISTS idx_notes_importance ON notes(importance DESC, created_at DESC);

-- Update FTS table to include importance in searches (rebuild)
DROP TRIGGER IF EXISTS notes_ai;
DROP TRIGGER IF EXISTS notes_au;

CREATE TRIGGER notes_ai AFTER INSERT ON notes BEGIN
    INSERT INTO notes_fts(rowid, content, tags)
    VALUES (new.id, new.content, new.tags);
END;

CREATE TRIGGER notes_au AFTER UPDATE ON notes BEGIN
    DELETE FROM notes_fts WHERE rowid = old.id;
    INSERT INTO notes_fts(rowid, content, tags)
    VALUES (new.id, new.content, new.tags);
END;
