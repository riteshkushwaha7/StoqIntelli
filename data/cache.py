from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from threading import RLock
from typing import Any


class HybridCache:
    """Small hybrid cache using process memory + SQLite persistence."""

    def __init__(self, db_path: str | Path, default_ttl_seconds: int = 60) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.default_ttl_seconds = default_ttl_seconds
        self._memory: dict[str, tuple[Any, float | None]] = {}
        self._lock = RLock()
        self._initialize()

    def _connection(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self.db_path), check_same_thread=False)

    def _initialize(self) -> None:
        with self._connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cache_entries (
                    key TEXT PRIMARY KEY,
                    value_json TEXT NOT NULL,
                    expires_at REAL NULL
                )
                """
            )
            conn.commit()

    def get(self, key: str) -> Any | None:
        with self._lock:
            memory_item = self._memory.get(key)
            if memory_item is not None:
                value, expires_at = memory_item
                if not self._is_expired(expires_at):
                    return value
                self._memory.pop(key, None)

            with self._connection() as conn:
                row = conn.execute(
                    "SELECT value_json, expires_at FROM cache_entries WHERE key = ?",
                    (key,),
                ).fetchone()

            if row is None:
                return None

            value_json, expires_at = row
            if self._is_expired(expires_at):
                self.delete(key)
                return None

            value = json.loads(value_json)
            self._memory[key] = (value, expires_at)
            return value

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        expires_at = None
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds
        if ttl > 0:
            expires_at = time.time() + ttl

        value_json = json.dumps(value, default=str)
        with self._lock:
            self._memory[key] = (value, expires_at)
            with self._connection() as conn:
                conn.execute(
                    """
                    INSERT INTO cache_entries (key, value_json, expires_at)
                    VALUES (?, ?, ?)
                    ON CONFLICT(key) DO UPDATE SET
                        value_json = excluded.value_json,
                        expires_at = excluded.expires_at
                    """,
                    (key, value_json, expires_at),
                )
                conn.commit()

    def delete(self, key: str) -> None:
        with self._lock:
            self._memory.pop(key, None)
            with self._connection() as conn:
                conn.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
                conn.commit()

    def cleanup(self) -> None:
        now = time.time()
        with self._lock:
            expired_keys = [
                key for key, (_, expires_at) in self._memory.items() if self._is_expired(expires_at, now)
            ]
            for key in expired_keys:
                self._memory.pop(key, None)

            with self._connection() as conn:
                conn.execute(
                    "DELETE FROM cache_entries WHERE expires_at IS NOT NULL AND expires_at <= ?",
                    (now,),
                )
                conn.commit()

    @staticmethod
    def _is_expired(expires_at: float | None, now: float | None = None) -> bool:
        if expires_at is None:
            return False
        current_time = now if now is not None else time.time()
        return expires_at <= current_time

