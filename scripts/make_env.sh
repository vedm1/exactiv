#!/usr/bin/env bash
# Create a local .env with random throwaway credentials. Never overwrites an existing .env.
set -euo pipefail
cd "$(dirname "$0")/.."
if [ -f .env ]; then echo ".env exists, not changed"; exit 0; fi
rand() { openssl rand -hex 16; }
cat > .env <<ENV
POSTGRES_HOST=localhost
POSTGRES_PORT=5442
POSTGRES_DB=exaktiv
POSTGRES_USER=exaktiv
POSTGRES_PASSWORD=$(rand)
MINIO_ENDPOINT=http://localhost:9000
MINIO_ACCESS_KEY=exaktiv$(openssl rand -hex 4)
MINIO_SECRET_KEY=$(rand)
MINIO_BUCKET=exaktiv-smoke
ENV
chmod 600 .env
echo "created .env"
