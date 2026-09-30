#!/usr/bin/env bash
# Install as user unit. No root needed. Needs ./.env (copy from .env.sample).
set -euo pipefail
cd "$(dirname "$0")"
[[ -f .env ]] || { echo "missing .env: cp .env.sample .env and set MYADDR_KEYS" >&2; exit 1; }
install -Dm755 myaddr.sh "$HOME/.local/bin/myaddr.sh"
install -d -m755 "$HOME/.config/myaddr" "$HOME/.config/systemd/user"
install -m600 .env "$HOME/.config/myaddr/.env"
install -m644 systemd/myaddr.service systemd/myaddr.timer "$HOME/.config/systemd/user/"
systemctl --user daemon-reload
systemctl --user enable --now myaddr.timer
loginctl enable-linger
systemctl --user start myaddr.service
systemctl --user list-timers myaddr.timer
