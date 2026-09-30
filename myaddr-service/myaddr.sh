#!/bin/bash
# Update myaddr.tools IPv4 record for every key. Usage: myaddr.sh [env-file]
set -euo pipefail
source "${1:-$HOME/.config/myaddr/.env}"
: "${MYADDR_KEYS:?MYADDR_KEYS not set}"

failed=0
n=0
for key in $MYADDR_KEYS; do
        n=$((n + 1))
        # One bad key must not block the others.
        /usr/bin/curl -sS -f \
                --connect-timeout 5 \
                --max-time 15 \
                -X PUT "https://ipv4.myaddr.tools/update?key=${key}&ip=self" \
                || { echo "key #$n failed" >&2; failed=1; }
done
exit $failed
