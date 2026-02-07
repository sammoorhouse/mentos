# mentos (Python)

Local-first personal finance nudges.

## Quick start

```bash
cd /Users/sam/dev/sammoorhouse/mentos
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
cp .env.example .env

# Generate an encryption key (32 bytes base64)
python - <<'PY'
import os, base64
print(base64.b64encode(os.urandom(32)).decode())
PY

# Fill .env (Pushover + encryption key + Monzo token)
mentos db init
mentos token set "<your-monzo-personal-token>"
mentos notify-test
mentos sync
mentos run
```

## Configure sweep (example)

```bash
mentos config set sweep_enabled true
mentos config set daily_spend_pot_id "pot_123"
mentos config set savings_pot_id "pot_456"
mentos config set sweep_min_residual 500   # £5.00
mentos config set sweep_max_amount 2000    # £20.00
```

## Commands

- `mentos db init` initialize SQLite + apply migrations
- `mentos token set <token>` store Monzo personal token (encrypted)
- `mentos sync` one-off Monzo sync
- `mentos notify-test` send a test push notification
- `mentos run` run the local loop (poll + scheduled jobs)
- `mentos report --notify` generate nightly report now
- `mentos sweep` run daily sweep now
- `mentos config set/get/list` manage rules

## Mock responses

Mock API payloads live in:
- `/Users/sam/dev/sammoorhouse/mentos/scripts/mocks/monzo_accounts.json`
- `/Users/sam/dev/sammoorhouse/mentos/scripts/mocks/monzo_pots.json`
- `/Users/sam/dev/sammoorhouse/mentos/scripts/mocks/monzo_transactions.json`
