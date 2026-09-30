#!/usr/bin/env bash
# Install extract.py and the user systemd timer. Re-run to update.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
install -Dm755 "$here/extract.py" "$HOME/.local/lib/db-to-file/extract.py"
[ -f "$HOME/.config/db-to-file/env" ] || install -Dm600 "$here/.env" "$HOME/.config/db-to-file/env"
install -Dm644 "$here/systemd/db-to-file.service" "$HOME/.config/systemd/user/db-to-file.service"
install -Dm644 "$here/systemd/db-to-file.timer" "$HOME/.config/systemd/user/db-to-file.timer"
systemctl --user daemon-reload
systemctl --user enable --now db-to-file.timer
loginctl enable-linger
systemctl --user start db-to-file.service
systemctl --user list-timers db-to-file.timer --no-pager
