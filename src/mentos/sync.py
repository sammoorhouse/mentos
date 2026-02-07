import json
import logging
from datetime import datetime, timezone, timedelta

from .monzo_client import MonzoClient, MonzoError
from .storage import (
    ensure_user,
    get_last_sync,
    log_raw_event,
    prune_raw_events,
    update_last_sync,
)

logger = logging.getLogger("mentos.sync")


def _parse_iso(ts: str) -> str:
    return ts.replace("Z", "+00:00")


def _parse_dt(ts: str) -> datetime:
    return datetime.fromisoformat(_parse_iso(ts))


def sync_all(conn, token: str) -> None:
    user_id = ensure_user(conn)
    client = MonzoClient(token)

    try:
        accounts = client.list_accounts()
    except MonzoError as exc:
        logger.error("Monzo accounts error: %s", exc)
        raise

    log_raw_event(conn, user_id, "monzo.accounts", accounts)
    for acc in accounts.get("accounts", []):
        conn.execute(
            """
            INSERT OR REPLACE INTO accounts (id, user_id, name, type, currency, created_at, raw_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                acc.get("id"),
                user_id,
                acc.get("description"),
                acc.get("type"),
                acc.get("currency"),
                _parse_iso(acc.get("created", datetime.now(timezone.utc).isoformat())),
                json.dumps(acc),
            ),
        )
    conn.commit()

    account_id_for_pots = None
    for acc in accounts.get("accounts", []):
        if acc.get("id"):
            account_id_for_pots = acc.get("id")
            break

    if account_id_for_pots:
        try:
            pots = client.list_pots(account_id_for_pots)
            log_raw_event(conn, user_id, "monzo.pots", pots)
            for pot in pots.get("pots", []):
                conn.execute(
                    """
                    INSERT OR REPLACE INTO pots (id, user_id, name, balance, currency, created_at, raw_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        pot.get("id"),
                        user_id,
                        pot.get("name"),
                        pot.get("balance", 0),
                        pot.get("currency"),
                        _parse_iso(pot.get("created", datetime.now(timezone.utc).isoformat())),
                        json.dumps(pot),
                    ),
                )
            conn.commit()
        except MonzoError as exc:
            logger.error("Monzo pots error: %s", exc)
            raise

    last_sync = get_last_sync(conn)
    if last_sync:
        # small lookback to catch delayed/late transactions
        last_sync_dt = _parse_dt(last_sync) - timedelta(days=2)
        last_sync = last_sync_dt.isoformat()
        logger.info("Syncing transactions since %s (lookback)", last_sync)
    else:
        # Monzo can require verification for longer history; default to last 30 days on first sync
        last_sync = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        logger.info("No prior sync. Fetching last 30 days since %s", last_sync)

    max_seen_created = None
    for acc in accounts.get("accounts", []):
        account_id = acc.get("id")
        if not account_id:
            continue
        before = None
        verification_retry = False
        while True:
            try:
                txs = client.list_transactions(account_id, since=last_sync, before=before)
            except MonzoError as exc:
                if "verification_required" in str(exc) and not verification_retry:
                    # Retry with a narrower window (last 7 days)
                    last_sync = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
                    before = None
                    verification_retry = True
                    logger.warning(
                        "Monzo verification required. Retrying with last 7 days since %s",
                        last_sync,
                    )
                    continue
                logger.error("Monzo transactions error: %s", exc)
                raise
            log_raw_event(conn, user_id, "monzo.transactions", txs)
            items = txs.get("transactions", [])
            if not items:
                break
            for tx in items:
                merchant_name = None
                merchant = tx.get("merchant")
                if isinstance(merchant, dict):
                    merchant_name = merchant.get("name")
                created = tx.get("created")
                if created:
                    try:
                        created_dt = _parse_dt(created)
                        if max_seen_created is None or created_dt > max_seen_created:
                            max_seen_created = created_dt
                    except Exception:
                        pass
                conn.execute(
                    """
                    INSERT OR REPLACE INTO transactions (
                      id, user_id, account_id, amount, currency, description, merchant_name, category,
                      is_load, is_pending, created_at, settled_at, raw_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        tx.get("id"),
                        user_id,
                        account_id,
                        tx.get("amount", 0),
                        tx.get("currency"),
                        tx.get("description"),
                        merchant_name,
                        tx.get("category"),
                        1 if tx.get("is_load") else 0,
                        1 if tx.get("settled") is None and tx.get("created") else 0,
                        _parse_iso(tx.get("created", datetime.now(timezone.utc).isoformat())),
                        _parse_iso(tx.get("settled")) if tx.get("settled") else None,
                        json.dumps(tx),
                    ),
                )
            conn.commit()
            if len(items) < 100:
                break
            before = items[-1].get("created")
            if before and last_sync:
                try:
                    if _parse_dt(before) <= _parse_dt(last_sync):
                        break
                except Exception:
                    pass

    if max_seen_created is not None:
        update_last_sync(conn, max_seen_created.isoformat())
    else:
        update_last_sync(conn, datetime.now(timezone.utc).isoformat())

    retention = 14
    prune_raw_events(conn, retention)
