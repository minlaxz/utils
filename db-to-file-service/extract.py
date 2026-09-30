#!/usr/bin/env python3
"""Sync: copy the Access Token and Refresh Timestamps from the Source DB into the Auth File.

The refresh token is never copied; refresh_token is always written empty.
"""
import argparse
import json
import os
import shlex
import sqlite3
import subprocess
import sys
from datetime import datetime, timedelta

DEFAULT_DB = os.path.expanduser(os.environ.get("DB_PATH", "~/data.sqlite"))
DEFAULT_EMAIL = os.environ.get("DB_EMAIL", "")

QUERY = (
    "SELECT data FROM providerConnections"
    " WHERE email = ? AND isActive = 1 ORDER BY updatedAt DESC"
)


class SyncError(Exception):
    pass


def shift_day(ts):
    """'2026-09-08T10:15:30.123Z' -> one day earlier, same format.

    Owner app always emits .mmmZ; other ISO variants are rejected on purpose.
    """
    if not ts.endswith("Z"):
        raise SyncError(f"unexpected timestamp format: {ts!r}")
    dt = datetime.fromisoformat(ts[:-1]) - timedelta(days=1)
    return dt.isoformat(timespec="milliseconds") + "Z"


def render(data):
    token = data["accessToken"]
    last_refresh = shift_day(data["lastRefreshAt"])
    return {
        "version": 1,
        "providers": {
            "openai-codex": {
                "tokens": {"access_token": token, "refresh_token": ""},
                "last_refresh": last_refresh,
                "auth_mode": "chatgpt",
            }
        },
        "active_provider": "openai-codex",
        "updated_at": data["lastPingAt"],
        "credential_pool": {
            "openai-codex": [
                {
                    "id": "aa52f2",
                    "label": "device_code",
                    "auth_type": "oauth",
                    "priority": 0,
                    "source": "device_code",
                    "access_token": token,
                    "refresh_token": "",
                    "last_status": None,
                    "last_status_at": None,
                    "last_error_code": None,
                    "last_error_reason": None,
                    "last_error_message": None,
                    "last_error_reset_at": None,
                    "base_url": "https://chatgpt.com/backend-api/codex",
                    "last_refresh": last_refresh,
                    "request_count": 0,
                }
            ]
        },
        "suppressed_sources": {},
    }


def read_connection(db_path, email):
    if not os.path.exists(db_path):
        raise SyncError(f"source db not found: {db_path}")
    uri = "file:" + os.path.abspath(db_path) + "?mode=ro"
    try:
        con = sqlite3.connect(uri, uri=True, timeout=10)
        try:
            rows = con.execute(QUERY, (email,)).fetchmany(2)  # ponytail: 2 is enough to warn
        finally:
            con.close()
    except sqlite3.Error as e:
        raise SyncError(f"sqlite: {e}") from e
    if not rows:
        raise SyncError(f"no active connection for {email}")
    if len(rows) > 1:
        print(f"warning: multiple active rows for {email}, using newest", file=sys.stderr)
    try:
        return json.loads(rows[0][0])
    except ValueError as e:
        raise SyncError(f"connection data is not json: {e}") from e


def write_if_changed(path, rendered):
    try:
        with open(path) as f:
            if f.read() == rendered:
                return False
    except FileNotFoundError:
        pass
    tmp = path + ".tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(rendered)
    os.replace(tmp, path)
    return True


# Same compare-then-atomic-replace as write_if_changed, run by the remote sh.
REMOTE_WRITE = (
    'set -e; umask 077; f="$1"; cat > "$f.tmp";'
    ' if cmp -s "$f.tmp" "$f"; then rm -f "$f.tmp"; echo unchanged;'
    ' else mv "$f.tmp" "$f"; echo written; fi'
)


def ssh_write_if_changed(target, rendered):
    """target is 'host:/dir' or 'host:~/dir'. Needs non-interactive ssh (key, no passphrase prompt)."""
    host, sep, path = target.partition(":")
    if not (host and sep and path):
        raise SyncError(f"bad ssh target (want host:dir): {target!r}")
    if path == "~" or path.startswith("~/"):
        path = path[2:] or "."  # remote shell starts in $HOME; quoting would block ~ expansion
    cmd = "sh -c " + shlex.quote(REMOTE_WRITE) + " _ " + shlex.quote(path.rstrip("/") + "/auth.json")
    try:
        r = subprocess.run(
            ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", host, cmd],
            input=rendered, capture_output=True, text=True, timeout=60,
        )
    except subprocess.TimeoutExpired:
        raise SyncError(f"ssh {host}: timed out")
    if r.returncode != 0:
        raise SyncError(f"ssh {host}: {r.stderr.strip() or f'exit {r.returncode}'}")
    return r.stdout.strip() == "written"


def sync(db_path, email, out_path, copy_dirs=(), ssh_targets=()):
    """Returns True if any target was replaced, False if all already identical.

    Local targets are written first; a failing ssh target does not block the others,
    but raises SyncError once all have been tried.
    """
    try:
        rendered = json.dumps(render(read_connection(db_path, email)), indent=2) + "\n"
    except (KeyError, TypeError, AttributeError, ValueError) as e:
        raise SyncError(f"bad connection data: {e!r}") from e
    targets = [out_path] + [os.path.join(d, os.path.basename(out_path)) for d in copy_dirs]
    changed = any([write_if_changed(t, rendered) for t in targets])
    errors = []
    for t in ssh_targets:
        try:
            changed = ssh_write_if_changed(t, rendered) or changed
        except SyncError as e:
            errors.append(str(e))
    if errors:
        raise SyncError("; ".join(errors))
    return changed


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--db", default=DEFAULT_DB)
    p.add_argument("--email", default=DEFAULT_EMAIL)
    p.add_argument("--out", default=None, help="default: auth.json next to --db")
    p.add_argument("--copy-to", action="append", default=None, metavar="DIR",
                   help="also write a copy into DIR (repeatable; default: COPY_TO env, colon-separated)")
    p.add_argument("--copy-to-ssh", action="append", default=None, metavar="HOST:DIR",
                   help="also write a copy into DIR on HOST over ssh (repeatable;"
                        " default: COPY_TO_SSH env, space-separated)")
    a = p.parse_args()
    if not a.email:
        p.error("--email or DB_EMAIL env required")
    out = a.out or os.path.join(os.path.dirname(os.path.abspath(a.db)), "auth.json")
    dirs = a.copy_to or [d for d in os.environ.get("COPY_TO", "").split(":") if d]
    dirs = [os.path.expanduser(d) for d in dirs]
    ssh_targets = a.copy_to_ssh or os.environ.get("COPY_TO_SSH", "").split()
    try:
        print("written" if sync(a.db, a.email, out, dirs, ssh_targets) else "unchanged")
    except (SyncError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
