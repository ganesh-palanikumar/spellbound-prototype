#!/usr/bin/env bash
# Deploy Prisma code to the BeagleBone Green.
# Run from the repo root: ./deploy/prisma_deploy.sh

set -euo pipefail

REMOTE="lekha@prisma.local"
DEST="/home/lekha/spellbound"

echo "==> Syncing prisma/ and shared/ to ${REMOTE}:${DEST}"
rsync -avz --delete \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  prisma/ "${REMOTE}:${DEST}/prisma/"

rsync -avz --delete \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  shared/ "${REMOTE}:${DEST}/shared/"

echo "==> Installing Python dependencies on Prisma"
ssh "${REMOTE}" "pip3 install --quiet -r ${DEST}/prisma/requirements.txt"

echo "==> Restarting spellbound-prisma service"
ssh -t "${REMOTE}" "sudo systemctl restart spellbound-prisma 2>/dev/null || echo 'systemd service not set up yet — run manually: cd ${DEST} && PYTHONPATH=${DEST} python3 prisma/main.py'"

echo "==> Done. Prisma deploy complete."
