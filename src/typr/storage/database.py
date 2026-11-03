"""Transactional, local-only persistence. No unfinished Classic sessions are written."""
import json
import sqlite3
from pathlib import Path

SETTING_VALUES = {"animations": ("subtle", "off"), "cursor blink": ("on", "off"), "ascii art": ("on", "off")}
DEFAULTS = {key: values[0] for key, values in SETTING_VALUES.items()}


class Database:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path)
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript("""
            CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY, created TEXT DEFAULT CURRENT_TIMESTAMP,
                language TEXT NOT NULL, config TEXT NOT NULL, wpm REAL NOT NULL,
                accuracy REAL NOT NULL, duration REAL NOT NULL, samples TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS story_progress (
                story_id TEXT PRIMARY KEY, paragraph INTEGER NOT NULL CHECK(paragraph >= 0));
        """)

    def settings(self):
        return DEFAULTS | dict(self.connection.execute("SELECT key, value FROM settings"))

    def setting(self, key, value):
        with self.connection:
            self.connection.execute("INSERT OR REPLACE INTO settings VALUES (?, ?)", (key, value))

    def save_session(self, config, session):
        from typr.core.typing_engine import SessionStatus
        if session.status is not SessionStatus.FINISHED:
            raise ValueError("Only completed sessions may be stored")
        with self.connection:
            self.connection.execute(
                "INSERT INTO sessions(language, config, wpm, accuracy, duration, samples) VALUES (?, ?, ?, ?, ?, ?)",
                (config.code_language if config.mode == "developer" else config.language,
                 json.dumps(config.as_dict()), session.wpm, session.accuracy,
                 session.elapsed, json.dumps(session.samples)),
            )

    def progress(self, story_id):
        row = self.connection.execute("SELECT paragraph FROM story_progress WHERE story_id=?", (story_id,)).fetchone()
        return row[0] if row else 0

    def checkpoint(self, story_id, paragraph):
        with self.connection:
            self.connection.execute("""INSERT INTO story_progress VALUES (?, ?)
                ON CONFLICT(story_id) DO UPDATE SET paragraph=max(paragraph, excluded.paragraph)""", (story_id, paragraph))

    def restart_story(self, story_id):
        with self.connection:
            self.connection.execute("DELETE FROM story_progress WHERE story_id=?", (story_id,))

    def stats(self):
        summary = dict(self.connection.execute("""SELECT count(*) AS total, coalesce(avg(wpm),0) AS average,
            coalesce(max(wpm),0) AS best, coalesce(avg(accuracy),0) AS accuracy FROM sessions""").fetchone())
        recent = self.connection.execute("SELECT * FROM sessions ORDER BY id DESC LIMIT 50").fetchall()
        return summary, recent

    def reset(self):
        with self.connection:
            for table in ("sessions", "story_progress", "settings"):
                self.connection.execute(f"DELETE FROM {table}")

    def close(self):
        self.connection.close()
