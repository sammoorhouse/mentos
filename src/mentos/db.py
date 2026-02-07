import sqlite3
from pathlib import Path
from typing import Iterable


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def apply_migrations(db_path: str, migrations_dir: str) -> None:
    conn = connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
          id TEXT PRIMARY KEY,
          applied_at TEXT NOT NULL
        )
        """
    )
    conn.commit()

    migrations = sorted(Path(migrations_dir).glob("*.sql"))
    for path in migrations:
        migration_id = path.name
        cur = conn.execute(
            "SELECT 1 FROM schema_migrations WHERE id = ?", (migration_id,)
        )
        if cur.fetchone():
            continue
        sql = path.read_text()
        conn.executescript(sql)
        conn.execute(
            "INSERT INTO schema_migrations (id, applied_at) VALUES (?, datetime('now'))",
            (migration_id,),
        )
        conn.commit()

    conn.close()


def execute(conn: sqlite3.Connection, sql: str, params: Iterable | None = None):
    if params is None:
        params = []
    return conn.execute(sql, params)
