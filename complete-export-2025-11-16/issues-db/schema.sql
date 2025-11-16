CREATE TABLE issues (
	id VARCHAR(50) NOT NULL, 
	project_id VARCHAR(50) NOT NULL, 
	title VARCHAR(500) NOT NULL, 
	description VARCHAR, 
	status VARCHAR(20) NOT NULL, 
	priority INTEGER NOT NULL, 
	type VARCHAR(20) NOT NULL, 
	assignee VARCHAR(100), 
	epic_id VARCHAR(50), 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	closed_at DATETIME, 
	PRIMARY KEY (id)
)

CREATE TABLE labels (
	id VARCHAR(50) NOT NULL, 
	project_id VARCHAR(50) NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	color VARCHAR(7), 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id)
)

CREATE TABLE issue_labels (
	issue_id VARCHAR(50) NOT NULL, 
	label_name VARCHAR(100) NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (issue_id, label_name), 
	FOREIGN KEY(issue_id) REFERENCES issues (id)
)

CREATE TABLE comments (
	id VARCHAR(50) NOT NULL, 
	issue_id VARCHAR(50) NOT NULL, 
	author VARCHAR(100) NOT NULL, 
	content VARCHAR, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(issue_id) REFERENCES issues (id)
)

CREATE TABLE dependencies (
	id VARCHAR(50) NOT NULL, 
	from_issue_id VARCHAR(50) NOT NULL, 
	to_issue_id VARCHAR(50) NOT NULL, 
	type VARCHAR(20) NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(from_issue_id) REFERENCES issues (id), 
	FOREIGN KEY(to_issue_id) REFERENCES issues (id)
)

CREATE TABLE epics (
	id VARCHAR(50) NOT NULL, 
	project_id VARCHAR(50) NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	progress INTEGER NOT NULL, 
	start_date DATETIME, 
	target_date DATETIME, 
	completed_date DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(id) REFERENCES issues (id)
)

CREATE VIRTUAL TABLE issues_fts USING fts5(
    id UNINDEXED,
    title,
    description
)

CREATE TABLE 'issues_fts_data'(id INTEGER PRIMARY KEY, block BLOB)

CREATE TABLE 'issues_fts_idx'(segid, term, pgno, PRIMARY KEY(segid, term)) WITHOUT ROWID

CREATE TABLE 'issues_fts_content'(id INTEGER PRIMARY KEY, c0, c1, c2)

CREATE TABLE 'issues_fts_docsize'(id INTEGER PRIMARY KEY, sz BLOB)

CREATE TABLE 'issues_fts_config'(k PRIMARY KEY, v) WITHOUT ROWID