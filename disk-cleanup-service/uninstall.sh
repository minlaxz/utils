#!/usr/bin/env bash
# Remove timer, service, script. Keeps ~/.config/disk-cleanup/.env (pass --purge to delete it).
set -euo pipefail
systemctl --user disable --now disk-cleanup.timer 2>/dev/null || true
rm -f "$HOME/.config/systemd/user/disk-cleanup.service" "$HOME/.config/systemd/user/disk-cleanup.timer"
rm -f "$HOME/.local/bin/disk-cleanup.sh"
systemctl --user daemon-reload
[[ "${1:-}" == "--purge" ]] && rm -rf "$HOME/.config/disk-cleanup"
echo "uninstalled"
