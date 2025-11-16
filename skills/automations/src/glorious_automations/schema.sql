-- Automations skill database schema

CREATE TABLE IF NOT EXISTS automations (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    trigger_topic TEXT NOT NULL,
    trigger_condition TEXT,
    actions TEXT NOT NULL,
    enabled INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_automations_trigger ON automations(trigger_topic);
CREATE INDEX IF NOT EXISTS idx_automations_enabled ON automations(enabled);

CREATE TABLE IF NOT EXISTS automation_executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    automation_id TEXT NOT NULL,
    trigger_data TEXT,
    status TEXT NOT NULL,
    result TEXT,
    error TEXT,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (automation_id) REFERENCES automations(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_executions_automation ON automation_executions(automation_id);
CREATE INDEX IF NOT EXISTS idx_executions_status ON automation_executions(status);
CREATE INDEX IF NOT EXISTS idx_executions_time ON automation_executions(executed_at);
