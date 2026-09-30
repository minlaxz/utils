#!/usr/bin/env bash
# Stop and disable timer. Files stay installed. Re-enable: systemctl --user enable --now disk-cleanup.timer
set -euo pipefail
systemctl --user disable --now disk-cleanup.timer
systemctl --user status disk-cleanup.timer --no-pager || true
