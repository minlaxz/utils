#!/usr/bin/env bash
# Install as user unit. No root needed.
set -euo pipefail
cd "$(dirname "$0")"
install -Dm755 cleanup.sh "$HOME/.local/bin/disk-cleanup.sh"
install -d -m755 "$HOME/.config/disk-cleanup" "$HOME/.config/systemd/user"
[[ -f "$HOME/.config/disk-cleanup/.env" ]] || install -m600 .env.example "$HOME/.config/disk-cleanup/.env"
install -m644 systemd/disk-cleanup.service systemd/disk-cleanup.timer "$HOME/.config/systemd/user/"
systemctl --user daemon-reload
systemctl --user enable --now disk-cleanup.timer
loginctl enable-linger
systemctl --user list-timers disk-cleanup.timer
