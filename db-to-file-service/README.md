# db-to-file-service

Every 15 minutes, copy the Access Token from `~/data.sqlite` into `~/auth.json`. The refresh token is never copied; `refresh_token` in `auth.json` is always empty.

## Install (Linux, user systemd)

```
cp .env.example .env    # set DB_EMAIL (and DB_PATH if not ~/data.sqlite)
./install.sh
```

Rootless Docker: if `$XDG_RUNTIME_DIR/docker.pid` exists, the service runs `extract.py` inside Docker's user namespace (`nsenter -U`). There it can read a DB owned by container subuids, and files it writes stay owned by you. If Docker is down at run time, the run falls back to plain mode and fails on the DB; the next run retries. Inside the namespace `ssh` uses `/root/.ssh`, so `COPY_TO_SSH` does not work on such hosts.

`.env` is gitignored. The installer copies it to `~/.config/db-to-file/env` (mode 600) on first run only; edit that file to change settings later, then `systemctl --user restart db-to-file.service`.

## Operate

```
systemctl --user status db-to-file.timer     # next run
journalctl --user -u db-to-file.service -f   # logs
systemctl --user start db-to-file.service    # run now
systemctl --user disable --now db-to-file.timer   # stop
```

Remove everything the installer put in place:

```
./uninstall.sh
```

## Options

```
python3 extract.py --db ~/data.sqlite --email you@example.com --out ~/auth.json
```

Defaults: `--db` from `DB_PATH` (else `~/data.sqlite`), `--email` from `DB_EMAIL` (required), `--out` is `auth.json` next to `--db`. `--copy-to DIR` (repeatable) or `COPY_TO=dir1:dir2` in the env file also writes `auth.json` into each DIR (symlinks are not used; each copy is a real file). `--copy-to-ssh HOST:DIR` (repeatable) or `COPY_TO_SSH="host1:~/dir user@host2:/srv/dir"` pushes `auth.json` over `ssh` to each remote DIR, replaced atomically and only when changed; `HOST` is anything `ssh` accepts, incl. `~/.ssh/config` aliases. The timer runs without an ssh-agent, so the key needs no passphrase. A failing host is reported (exit 1) after all other targets are written. Exit 1 and leave the old `auth.json` untouched on any error.

## Test

```
python3 test_extract.py
```
