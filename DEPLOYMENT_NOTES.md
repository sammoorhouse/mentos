# Mentos v0.1 Fly.io Deployment Notes

- App name: mentos
- Base URL: https://mentos.fly.dev
- Region: lhr
- Web/Worker counts: web=1 worker=1
- Verified:
  - GET /health: OK (200, {"status":"ok"})
  - GET /me unauthenticated: 403 Not authenticated (expected 401 per runbook)

Ops commands:
- fly status --app mentos
- fly logs --app mentos
- fly scale count web=1 worker=1 --app mentos
- fly ssh console --app mentos -C "alembic upgrade head"
- fly deploy --app mentos

Notes:
- Monzo configured? no
- APNs configured? no (sandbox/prod: n/a)
