"""
SQLite database layer for caching, search history, and favorites.
"""
from __future__ import annotations
import json
import logging
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Generator, List, Optional

from app.config.settings import config
from app.models.weather import FavoriteCity

logger = logging.getLogger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS weather_cache (
    cache_key   TEXT PRIMARY KEY,
    data        TEXT NOT NULL,
    cached_at   REAL NOT NULL,
    ttl         INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS search_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    city        TEXT NOT NULL,
    country     TEXT NOT NULL,
    lat         REAL NOT NULL,
    lon         REAL NOT NULL,
    searched_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS favorites (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    country     TEXT NOT NULL,
    lat         REAL NOT NULL,
    lon         REAL NOT NULL,
    added_at    REAL NOT NULL,
    UNIQUE(lat, lon)
);
"""


class Database:
    """
    Thread-safe SQLite database wrapper.
    Uses one connection per thread via threading.local.
    """

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self._db_path = db_path or config.cache.db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(
                str(self._db_path), check_same_thread=False
            )
            self._local.conn.row_factory = sqlite3.Row
            self._local.conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn.execute("PRAGMA foreign_keys=ON")
        return self._local.conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.executescript(_SCHEMA)
        logger.debug("Database initialized at %s", self._db_path)

    @contextmanager
    def _cursor(self) -> Generator[sqlite3.Cursor, None, None]:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()

    # --- Cache ---

    def cache_set(self, key: str, data: dict, ttl: int = None) -> None:
        ttl = ttl or config.cache.ttl_seconds
        with self._cursor() as cur:
            cur.execute(
                """INSERT OR REPLACE INTO weather_cache (cache_key, data, cached_at, ttl)
                   VALUES (?, ?, ?, ?)""",
                (key, json.dumps(data), datetime.now().timestamp(), ttl),
            )

    def cache_get(self, key: str) -> Optional[dict]:
        with self._cursor() as cur:
            cur.execute(
                "SELECT data, cached_at, ttl FROM weather_cache WHERE cache_key = ?",
                (key,),
            )
            row = cur.fetchone()
        if not row:
            return None
        age = datetime.now().timestamp() - row["cached_at"]
        if age > row["ttl"]:
            self.cache_delete(key)
            return None
        return json.loads(row["data"])

    def cache_delete(self, key: str) -> None:
        with self._cursor() as cur:
            cur.execute("DELETE FROM weather_cache WHERE cache_key = ?", (key,))

    def cache_clear_expired(self) -> int:
        now = datetime.now().timestamp()
        with self._cursor() as cur:
            cur.execute(
                "DELETE FROM weather_cache WHERE (? - cached_at) > ttl", (now,)
            )
            return cur.rowcount

    # --- Search History ---

    def history_add(self, city: str, country: str, lat: float, lon: float) -> None:
        with self._cursor() as cur:
            cur.execute(
                """INSERT INTO search_history (city, country, lat, lon, searched_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (city, country, lat, lon, datetime.now().timestamp()),
            )

    def history_get(self, limit: int = 20) -> List[dict]:
        with self._cursor() as cur:
            cur.execute(
                """SELECT DISTINCT city, country, lat, lon,
                          MAX(searched_at) as last_searched
                   FROM search_history
                   GROUP BY city, country
                   ORDER BY last_searched DESC
                   LIMIT ?""",
                (limit,),
            )
            return [dict(row) for row in cur.fetchall()]

    def history_clear(self) -> None:
        with self._cursor() as cur:
            cur.execute("DELETE FROM search_history")

    # --- Favorites ---

    def favorites_add(self, city: FavoriteCity) -> int:
        with self._cursor() as cur:
            cur.execute(
                """INSERT OR IGNORE INTO favorites (name, country, lat, lon, added_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (city.name, city.country, city.lat, city.lon,
                 city.added_at.timestamp()),
            )
            return cur.lastrowid

    def favorites_get(self) -> List[FavoriteCity]:
        with self._cursor() as cur:
            cur.execute("SELECT * FROM favorites ORDER BY name")
            return [
                FavoriteCity(
                    id=row["id"],
                    name=row["name"],
                    country=row["country"],
                    lat=row["lat"],
                    lon=row["lon"],
                    added_at=datetime.fromtimestamp(row["added_at"]),
                )
                for row in cur.fetchall()
            ]

    def favorites_remove(self, fav_id: int) -> None:
        with self._cursor() as cur:
            cur.execute("DELETE FROM favorites WHERE id = ?", (fav_id,))

    def favorites_exists(self, lat: float, lon: float) -> bool:
        with self._cursor() as cur:
            cur.execute(
                "SELECT 1 FROM favorites WHERE lat = ? AND lon = ?", (lat, lon)
            )
            return cur.fetchone() is not None

    def close(self) -> None:
        if hasattr(self._local, "conn") and self._local.conn:
            self._local.conn.close()
            self._local.conn = None


# Singleton instance
db = Database()
