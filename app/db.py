"""SQLite 建表与连接。"""
from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS students (
    sid TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    class_name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS courses (
    cid TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    credit REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sid TEXT NOT NULL,
    cid TEXT NOT NULL,
    term TEXT NOT NULL,
    score REAL NOT NULL,
    UNIQUE(sid, cid, term)
);
CREATE INDEX IF NOT EXISTS idx_scores_sid ON scores(sid);
CREATE INDEX IF NOT EXISTS idx_scores_cid ON scores(cid);
"""


def connect(db_path: str | Path = ":memory:") -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn
