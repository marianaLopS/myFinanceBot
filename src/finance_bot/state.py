"""Estado local del bot en SQLite: mensajes ya procesados y borradores pendientes de aclarar."""

import json
import sqlite3
import threading
from pathlib import Path


class BotState:
    def __init__(self, path: str) -> None:
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        # Los handlers llaman desde hilos (asyncio.to_thread); el lock evita escrituras cruzadas.
        self._db = sqlite3.connect(path, check_same_thread=False)
        self._lock = threading.Lock()
        with self._lock:
            self._db.execute("CREATE TABLE IF NOT EXISTS processed_updates (update_id INTEGER PRIMARY KEY)")
            self._db.execute("CREATE TABLE IF NOT EXISTS drafts (chat_id INTEGER PRIMARY KEY, draft TEXT NOT NULL)")
            self._db.commit()

    def is_processed(self, update_id: int) -> bool:
        with self._lock:
            row = self._db.execute("SELECT 1 FROM processed_updates WHERE update_id = ?", (update_id,)).fetchone()
        return row is not None

    def mark_processed(self, update_id: int) -> None:
        with self._lock:
            self._db.execute("INSERT OR IGNORE INTO processed_updates (update_id) VALUES (?)", (update_id,))
            self._db.commit()

    def get_draft(self, chat_id: int) -> dict | None:
        with self._lock:
            row = self._db.execute("SELECT draft FROM drafts WHERE chat_id = ?", (chat_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def save_draft(self, chat_id: int, draft: dict) -> None:
        with self._lock:
            self._db.execute(
                "INSERT OR REPLACE INTO drafts (chat_id, draft) VALUES (?, ?)", (chat_id, json.dumps(draft))
            )
            self._db.commit()

    def clear_draft(self, chat_id: int) -> None:
        with self._lock:
            self._db.execute("DELETE FROM drafts WHERE chat_id = ?", (chat_id,))
            self._db.commit()
