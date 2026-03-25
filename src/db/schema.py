"""Database schema definition for v1."""

from __future__ import annotations


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS emails (
  id TEXT PRIMARY KEY,
  sender TEXT,
  subject TEXT,
  body TEXT,
  received_at TEXT,
  created_at TEXT
);

CREATE TABLE IF NOT EXISTS tasks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email_id TEXT,
  sender TEXT,
  subject TEXT,
  original_body TEXT,
  cleaned_text TEXT,
  task_title TEXT,
  deadline_text TEXT,
  normalized_deadline TEXT,
  priority TEXT,
  status TEXT,
  extraction_confidence REAL,
  needs_review INTEGER,
  extraction_method TEXT,
  user_corrected INTEGER,
  corrected_task_title TEXT,
  corrected_deadline_text TEXT,
  corrected_normalized_deadline TEXT,
  corrected_priority TEXT,
  notes TEXT,
  created_at TEXT,
  updated_at TEXT,
  completed_at TEXT,
  FOREIGN KEY(email_id) REFERENCES emails(id)
);

CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_needs_review ON tasks(needs_review);
CREATE INDEX IF NOT EXISTS idx_tasks_deadline ON tasks(normalized_deadline);
CREATE INDEX IF NOT EXISTS idx_tasks_sender ON tasks(sender);
"""


RESET_SQL = """
PRAGMA foreign_keys = OFF;
DROP TABLE IF EXISTS tasks;
DROP TABLE IF EXISTS emails;
PRAGMA foreign_keys = ON;
"""

