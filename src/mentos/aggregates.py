import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger("mentos.aggregates")


def rebuild_daily(conn, days: int = 35) -> None:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    since_iso = since.isoformat()

    conn.execute(
        "DELETE FROM aggregates_daily WHERE day >= date(?)",
        (since_iso,),
    )

    cur = conn.execute(
        """
        SELECT
          date(COALESCE(settled_at, created_at)) as day,
          category,
          SUM(CASE WHEN amount < 0 THEN -amount ELSE 0 END) as total_amount,
          SUM(CASE WHEN amount < 0 THEN 1 ELSE 0 END) as cnt
        FROM transactions
        WHERE created_at >= ? AND is_pending = 0
        GROUP BY day, category
        """,
        (since_iso,),
    )

    rows = cur.fetchall()
    for row in rows:
        conn.execute(
            """
            INSERT INTO aggregates_daily (id, user_id, day, category, total_amount, count, created_at, updated_at)
            VALUES (hex(randomblob(16)), ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """,
            ("user_1", row[0], row[1] or "uncategorized", row[2] or 0, row[3] or 0),
        )
    conn.commit()
    logger.info("Rebuilt aggregates for last %s days", days)
