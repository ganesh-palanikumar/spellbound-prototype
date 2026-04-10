#!/usr/bin/env bash
# One-time setup: install systemd service files on both devices.
# Run from the repo root: ./deploy/install_services.sh

set -euo pipefail

echo "==> Installing systemd service on Jarvis"
scp deploy/spellbound-jarvis.service lekha@jarvis.local:/tmp/
ssh lekha@jarvis.local "sudo mv /tmp/spellbound-jarvis.service /etc/systemd/system/ && sudo systemctl daemon-reload && sudo systemctl enable spellbound-jarvis"

echo "==> Installing systemd service on Prisma"
scp deploy/spellbound-prisma.service lekha@prisma.local:/tmp/
ssh lekha@prisma.local "sudo mv /tmp/spellbound-prisma.service /etc/systemd/system/ && sudo systemctl daemon-reload && sudo systemctl enable spellbound-prisma"

echo "==> Services installed. They will start automatically on next boot."
echo "    To start now: ssh lekha@prisma.local 'sudo systemctl start spellbound-prisma'"
echo "                  ssh lekha@jarvis.local  'sudo systemctl start spellbound-jarvis'"
