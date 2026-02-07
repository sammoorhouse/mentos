import json
import logging
from datetime import datetime, timezone
from typing import Optional

from .monzo_client import MonzoClient
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


def sync_all(conn, token: str) -> None:
    user_id = ensure_user(conn)
    client = MonzoClient(token)

    accounts = client.list_accounts()
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

    last_sync = get_last_sync(conn)
    if last_sync:
        logger.info("Syncing transactions since %s", last_sync)
    else:
        logger.info("Syncing recent transactions")

    for acc in accounts.get("accounts", []):
        account_id = acc.get("id")
        if not account_id:
            continue
        before = None
        while True:
            txs = client.list_transactions(account_id, since=last_sync, before=before)
            log_raw_event(conn, user_id, "monzo.transactions", txs)
            items = txs.get("transactions", [])
            if not items:
                break
            for tx in items:
                merchant_name = None
                merchant = tx.get("merchant")
                if isinstance(merchant, dict):
                    merchant_name = merchant.get("name")
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

    update_last_sync(conn, datetime.now(timezone.utc).isoformat())

    retention = 14
    prune_raw_events(conn, retention)
