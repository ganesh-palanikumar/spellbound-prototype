#!/usr/bin/env bash
# Deploy Jarvis code to the Raspberry Pi Zero 2W.
# Run from the repo root: ./deploy/jarvis_deploy.sh

set -euo pipefail

REMOTE="lekha@jarvis.local"
DEST="/home/lekha/spellbound"

echo "==> Syncing jarvis/ and shared/ to ${REMOTE}:${DEST}"
rsync -avz --delete \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  jarvis/ "${REMOTE}:${DEST}/jarvis/"

rsync -avz --delete \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  shared/ "${REMOTE}:${DEST}/shared/"

echo "==> Installing Python dependencies on Jarvis"
ssh "${REMOTE}" "pip3 install --quiet -r ${DEST}/jarvis/requirements.txt"

echo "==> Restarting spellbound-jarvis service"
ssh "${REMOTE}" "sudo systemctl restart spellbound-jarvis 2>/dev/null || echo 'systemd service not set up yet — run manually: cd ${DEST} && PYTHONPATH=${DEST} python3 jarvis/main.py'"

echo "==> Done. Jarvis deploy complete."
