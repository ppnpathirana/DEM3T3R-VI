"""
@file: event_store.py
@description: Backend logic module for DEM3T3R V1.

@project: DEM3T3R V1
@author: Pasindu Pathirana
@contact: https://github.com/ppnpathirana/DEM3T3R-VI
@version: 1.0.0
@date: 2026

All rights reserved. Unauthorized copying is strictly prohibited.
"""

"""
DEM3T3R V1 EventStore — append-only SQLite event log for state machine & robot telemetry audit trail.
Supports:
- Immutable event logging with microsecond timestamps
- replay(since, until, event_type) to query chronological historical sequences
- get_last_state(as_of) to reconstruct exact state at past timestamps
- Thread-safe SQLite WAL mode
"""
import sqlite3
import json
import time
import os
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass
class Event:
    event_type: str        # 'state_transition' | 'sensor_reading' | 'detection' | 'action' | 'error'
    payload: Dict[str, Any]
    timestamp: float = None
    event_id: int = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

    @property
    def iso_time(self) -> str:
        return datetime.fromtimestamp(self.timestamp, tz=timezone.utc).isoformat()

class EventStore:
    def __init__(self, db_path: str = "cropguard_events.db"):
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.execute("PRAGMA temp_store=MEMORY")
        self._conn.execute("PRAGMA cache_size=-32000")
        self._create_table()

    def _create_table(self):
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp  REAL    NOT NULL,
                iso_time   TEXT    NOT NULL,
                event_type TEXT    NOT NULL,
                payload    TEXT    NOT NULL
            )
        """)
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_ts ON events(timestamp)")
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_type ON events(event_type)")
        self._conn.commit()

    def append(self, event_type: str, payload: Dict[str, Any]) -> int:
        """Append an immutable event. Returns the auto-assigned event_id."""
        now = time.time()
        iso = datetime.fromtimestamp(now, tz=timezone.utc).isoformat()
        cur = self._conn.execute(
            "INSERT INTO events (timestamp, iso_time, event_type, payload) VALUES (?,?,?,?)",
            (now, iso, event_type, json.dumps(payload, default=str))
        )
        self._conn.commit()
        return cur.lastrowid

    def replay(self, since: float = 0.0, until: float = None,
               event_type: str = None) -> List[Event]:
        """
        Replay events optionally filtered by time window and/or event type.
        Returns a list of Event objects in chronological order.
        """
        query = "SELECT id, timestamp, event_type, payload FROM events WHERE timestamp >= ?"
        params = [since]
        if until is not None:
            query += " AND timestamp <= ?"
            params.append(until)
        if event_type is not None:
            query += " AND event_type = ?"
            params.append(event_type)
        query += " ORDER BY timestamp ASC"

        rows = self._conn.execute(query, params).fetchall()
        return [
            Event(
                event_type=row[2],
                payload=json.loads(row[3]),
                timestamp=row[1],
                event_id=row[0]
            )
            for row in rows
        ]

    def get_last_state(self, as_of: float = None) -> Optional[str]:
        """
        Reconstruct the robot state at the given timestamp by replaying
        all state_transition events up to that point.
        """
        events = self.replay(
            until=as_of or time.time(),
            event_type="state_transition"
        )
        if not events:
            return None
        return events[-1].payload.get("new_state")

    def count(self, event_type: str = None) -> int:
        if event_type:
            row = self._conn.execute(
                "SELECT COUNT(*) FROM events WHERE event_type=?", (event_type,)
            ).fetchone()
        else:
            row = self._conn.execute("SELECT COUNT(*) FROM events").fetchone()
        return row[0] if row else 0

    def close(self):
        try:
            self._conn.close()
        except:
            pass
