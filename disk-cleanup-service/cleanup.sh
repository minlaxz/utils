#!/usr/bin/env bash
# Delete files older than MAX_AGE_HOURS under each dir in CLEANUP_DIRS (from .env).
set -euo pipefail

ENV_FILE="${1:-$HOME/.config/disk-cleanup/.env}"
# shellcheck disable=SC1090
source "$ENV_FILE"

: "${CLEANUP_DIRS:?CLEANUP_DIRS not set in $ENV_FILE}"
: "${MAX_AGE_HOURS:=24}"

for dir in $CLEANUP_DIRS; do
  if [[ ! -d "$dir" ]]; then
    echo "skip: $dir not a directory" >&2
    continue
  fi
  # ponytail: no dry-run flag; run `find "$dir" -type f -mmin +N` by hand to preview
  find "$dir" -type f -mmin "+$((MAX_AGE_HOURS * 60))" -print -delete
  find "$dir" -mindepth 1 -type d -empty -delete
done
