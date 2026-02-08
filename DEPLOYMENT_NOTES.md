# Mentos v0.1 Deployment Notes

- **App name:** `mentos` (from `server/fly.toml`)
- **Base URL:** `https://mentos.fly.dev` (target; deployment not completed from this environment)
- **Region:** `lhr`
- **Date/time (UTC):** 2026-02-08 13:54:12 UTC

## Execution summary

This operator run could not complete a production deployment from the current environment due to missing Fly CLI and blocked CLI install egress.

### Checks completed

- Confirmed required deployment assets exist:
  - `server/fly.toml`
  - `server/Dockerfile`
  - `server/start-web.sh`
  - `server/start-worker.sh`
- Confirmed Fly app config includes:
  - `app = "mentos"`
  - `primary_region = "lhr"`
  - health check path `/health`
  - release command `alembic -c alembic.ini upgrade head`

### Blockers encountered

1. **Local /health validation could not run via tests**
   - `pytest -q server/tests/test_health.py` failed because `fastapi` is not installed in this environment.
2. **Fly CLI unavailable**
   - `fly auth whoami` failed (`command not found: fly`).
3. **Fly CLI installation blocked**
   - `curl -L https://fly.io/install.sh | sh` failed with `curl: (56) CONNECT tunnel failed, response 403`.

Because of these blockers, secrets were not set, deploy was not executed, and smoke checks against Fly could not be run.

## Required commands to run once Fly CLI + credentials are available

```bash
# auth + app check
fly auth whoami
fly apps list | grep mentos

# (if app missing)
cd server
fly launch --no-deploy --region lhr --name mentos

# set required secrets
fly secrets set DATABASE_URL="..." --app mentos
fly secrets set JWT_SECRET="..." --app mentos
fly secrets set TOKEN_ENCRYPTION_KEY_B64="..." --app mentos
fly secrets set APPLE_AUDIENCE="..." --app mentos

# optional Monzo
fly secrets set MONZO_CLIENT_ID="..." MONZO_CLIENT_SECRET="..." MONZO_REDIRECT_URI="..." MONZO_SCOPES="..." --app mentos

# optional APNs
fly secrets set APNS_TEAM_ID="..." APNS_KEY_ID="..." APNS_BUNDLE_ID="..." APNS_USE_SANDBOX="true" --app mentos
fly secrets set APNS_AUTH_KEY_P8="$(cat /path/to/AuthKey_XXXX.p8)" --app mentos

# deploy
cd server
fly deploy --app mentos

# ensure web + worker
fly scale count web=1 worker=1 --app mentos
fly status --app mentos

# fallback migration command
fly ssh console -C "alembic upgrade head" --app mentos

# smoke tests
BASE_URL="https://mentos.fly.dev"
curl -i "$BASE_URL/health"
curl -i "$BASE_URL/me"
fly logs --app mentos --since 10m
```

## Confirmation status

- **/health OK:** ❌ not verified from this environment
- **web=1 worker=1:** ❌ not verified from this environment
- **/me returns 401 unauthenticated:** ❌ not verified from this environment

## Common ops commands

- **View logs:** `fly logs --app mentos --since 10m`
- **Run migrations:** `fly ssh console -C "alembic upgrade head" --app mentos`
- **Restart app:** `fly apps restart mentos`
- **Scale processes:** `fly scale count web=1 worker=1 --app mentos`

## Known missing integrations

- Monzo credentials: not configured in this environment.
- APNs credentials/key: not configured in this environment.
