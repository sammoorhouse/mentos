import logging
from datetime import datetime

from .monzo_client import MonzoClient
from .storage import get_rule, log_transfer

logger = logging.getLogger("mentos.sweep")


def run_daily_sweep(conn, token: str) -> dict:
    enabled = get_rule(conn, "sweep_enabled")
    if enabled is False:
        return {"status": "skipped", "reason": "disabled"}

    daily_pot_id = get_rule(conn, "daily_spend_pot_id")
    savings_pot_id = get_rule(conn, "savings_pot_id")
    min_residual = int(get_rule(conn, "sweep_min_residual") or 0)
    max_amount = int(get_rule(conn, "sweep_max_amount") or 0)

    if not daily_pot_id or not savings_pot_id:
        return {"status": "skipped", "reason": "missing pot ids"}

    cur = conn.execute("SELECT balance, currency FROM pots WHERE id = ?", (daily_pot_id,))
    row = cur.fetchone()
    if not row:
        return {"status": "skipped", "reason": "daily pot not found"}

    balance = int(row[0])
    currency = row[1]

    available = max(balance - min_residual, 0)
    if available <= 0:
        return {"status": "skipped", "reason": "below residual"}

    amount = available if max_amount <= 0 else min(available, max_amount)
    if amount <= 0:
        return {"status": "skipped", "reason": "zero amount"}

    account_id = get_rule(conn, "primary_account_id")
    if not account_id:
        cur = conn.execute("SELECT id FROM accounts LIMIT 1")
        row = cur.fetchone()
        account_id = row[0] if row else None

    if not account_id:
        return {"status": "skipped", "reason": "missing account id"}

    client = MonzoClient(token)
    dedupe = f"sweep-{datetime.utcnow().date().isoformat()}"

    withdraw = client.withdraw_from_pot(daily_pot_id, account_id, amount, dedupe)
    log_transfer(conn, "user_1", daily_pot_id, None, amount, currency, "withdrawn", withdraw)

    try:
        deposit = client.deposit_to_pot(savings_pot_id, account_id, amount, dedupe)
        log_transfer(conn, "user_1", None, savings_pot_id, amount, currency, "deposited", deposit)
    except Exception as exc:
        log_transfer(conn, "user_1", None, savings_pot_id, amount, currency, "deposit_failed", {"error": str(exc)})
        raise

    return {"status": "ok", "amount": amount, "currency": currency}
