#!/usr/bin/env bash
set -euo pipefail

JWT_SECRET="$(openssl rand -hex 32)"
TOKEN_ENCRYPTION_KEY_B64="$(openssl rand -base64 32 | tr -d '\n')"

cat <<SECRETS
Generated secrets (not saved to disk):

JWT_SECRET=${JWT_SECRET}
TOKEN_ENCRYPTION_KEY_B64=${TOKEN_ENCRYPTION_KEY_B64}

# Export commands:
export JWT_SECRET='${JWT_SECRET}'
export TOKEN_ENCRYPTION_KEY_B64='${TOKEN_ENCRYPTION_KEY_B64}'
SECRETS
