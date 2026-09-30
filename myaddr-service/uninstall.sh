#!/usr/bin/env bash
# Remove timer, service, script. Keeps ~/.config/myaddr/.env (pass --purge to delete it).
set -euo pipefail
systemctl --user disable --now myaddr.timer 2>/dev/null || true
rm -f "$HOME/.config/systemd/user/myaddr.service" "$HOME/.config/systemd/user/myaddr.timer"
rm -f "$HOME/.local/bin/myaddr.sh"
systemctl --user daemon-reload
[[ "${1:-}" == "--purge" ]] && rm -rf "$HOME/.config/myaddr"
echo "uninstalled"
