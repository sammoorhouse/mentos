import json
import sqlite3
import uuid
from datetime import datetime
from typing import Any, Optional

from .crypto import encrypt, decrypt


DEFAULT_USER_ID = "user_1"
DEFAULT_CONN_ID = "monzo_default"


def ensure_user(conn: sqlite3.Connection) -> str:
    cur = conn.execute("SELECT id FROM users WHERE id = ?", (DEFAULT_USER_ID,))
    if cur.fetchone():
        return DEFAULT_USER_ID
    conn.execute(
        "INSERT INTO users (id, created_at) VALUES (?, datetime('now'))",
        (DEFAULT_USER_ID,),
    )
    conn.commit()
    return DEFAULT_USER_ID


def set_rule(conn: sqlite3.Connection, user_id: str, key: str, value: Any) -> None:
    payload = json.dumps(value)
    now = datetime.utcnow().isoformat()
    conn.execute(
        """
        INSERT INTO rules (id, user_id, key, value_json, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET value_json = excluded.value_json, updated_at = excluded.updated_at
        """,
        (str(uuid.uuid4()), user_id, key, payload, now, now),
    )
    conn.commit()


def get_rule(conn: sqlite3.Connection, key: str) -> Optional[Any]:
    cur = conn.execute("SELECT value_json FROM rules WHERE key = ?", (key,))
    row = cur.fetchone()
    if not row:
        return None
    return json.loads(row[0])


def list_rules(conn: sqlite3.Connection) -> dict[str, Any]:
    cur = conn.execute("SELECT key, value_json FROM rules")
    out: dict[str, Any] = {}
    for row in cur.fetchall():
        out[row[0]] = json.loads(row[1])
    return out


def store_monzo_token(conn: sqlite3.Connection, user_id: str, key: bytes, token: str) -> None:
    payload = encrypt(key, token.encode("utf-8"))
    now = datetime.utcnow().isoformat()
    conn.execute(
        """
        INSERT INTO monzo_connections (id, user_id, mode, scopes, status, access_token_encrypted, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET access_token_encrypted = excluded.access_token_encrypted, updated_at = excluded.updated_at
        """,
        (DEFAULT_CONN_ID, user_id, "personal_token", "", "active", payload, now, now),
    )
    conn.commit()


def load_monzo_token(conn: sqlite3.Connection, key: bytes) -> Optional[str]:
    cur = conn.execute(
        "SELECT access_token_encrypted FROM monzo_connections WHERE id = ?",
        (DEFAULT_CONN_ID,),
    )
    row = cur.fetchone()
    if not row or row[0] is None:
        return None
    return decrypt(key, row[0]).decode("utf-8")


def update_last_sync(conn: sqlite3.Connection, at_iso: str) -> None:
    conn.execute(
        """
        UPDATE monzo_connections SET last_sync_at = ?, updated_at = datetime('now')
        WHERE id = ?
        """,
        (at_iso, DEFAULT_CONN_ID),
    )
    conn.commit()


def get_last_sync(conn: sqlite3.Connection) -> Optional[str]:
    cur = conn.execute("SELECT last_sync_at FROM monzo_connections WHERE id = ?", (DEFAULT_CONN_ID,))
    row = cur.fetchone()
    return row[0] if row else None


def log_notification(conn: sqlite3.Connection, user_id: str, provider: str, payload: dict, status: str) -> None:
    now = datetime.utcnow().isoformat()
    conn.execute(
        """
        INSERT INTO notifications (id, user_id, provider, payload_json, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (str(uuid.uuid4()), user_id, provider, json.dumps(payload), status, now, now),
    )
    conn.commit()


def log_transfer(conn: sqlite3.Connection, user_id: str, from_pot: str, to_pot: str, amount: int, currency: str, status: str, raw: dict | None):
    now = datetime.utcnow().isoformat()
    conn.execute(
        """
        INSERT INTO transfers (id, user_id, from_pot_id, to_pot_id, amount, currency, status, created_at, updated_at, raw_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (str(uuid.uuid4()), user_id, from_pot, to_pot, amount, currency, status, now, now, json.dumps(raw) if raw else None),
    )
    conn.commit()


def log_raw_event(conn: sqlite3.Connection, user_id: str, kind: str, payload: dict) -> None:
    conn.execute(
        """
        INSERT INTO raw_events (id, user_id, kind, received_at, payload_json)
        VALUES (?, ?, ?, datetime('now'), ?)
        """,
        (str(uuid.uuid4()), user_id, kind, json.dumps(payload)),
    )
    conn.commit()


def prune_raw_events(conn: sqlite3.Connection, days: int) -> None:
    conn.execute(
        "DELETE FROM raw_events WHERE received_at < datetime('now', ?)",
        (f"-{days} days",),
    )
    conn.commit()
