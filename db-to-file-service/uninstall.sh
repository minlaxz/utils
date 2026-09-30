#!/usr/bin/env bash
# Stop the timer and remove installed files. Leaves ~/auth.json and linger alone.
set -euo pipefail
systemctl --user disable --now db-to-file.timer 2>/dev/null || true
rm -f "$HOME/.config/systemd/user/db-to-file.service" "$HOME/.config/systemd/user/db-to-file.timer"
rm -rf "$HOME/.local/lib/db-to-file" "$HOME/.config/db-to-file"
systemctl --user daemon-reload
echo "uninstalled. auth.json kept; run 'loginctl disable-linger' if no other user services need it."
