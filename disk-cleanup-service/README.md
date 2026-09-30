# disk-cleanup-service

Deletes old files from a list of directories. A systemd user timer runs `cleanup.sh` every hour. Linux only; no root needed.

## Install

```bash
./install.sh
# edit ~/.config/disk-cleanup/.env: set CLEANUP_DIRS and MAX_AGE_HOURS
```

`install.sh` does this:

- copies `cleanup.sh` to `~/.local/bin/disk-cleanup.sh`
- copies `.env.example` to `~/.config/disk-cleanup/.env` (mode 600), first run only
- installs `systemd/disk-cleanup.service` and `systemd/disk-cleanup.timer` to `~/.config/systemd/user/`
- enables the timer
- runs `loginctl enable-linger` so the timer runs when you are logged out

The timer runs hourly (random delay up to 5 minutes). Missed runs happen at next boot.

## Settings

`~/.config/disk-cleanup/.env`:

```bash
CLEANUP_DIRS="$HOME/Downloads/torrents /tmp/scratch"   # space-separated, no spaces inside paths
MAX_AGE_HOURS=12                                       # default 24
```

Each run deletes files older than `MAX_AGE_HOURS`, then removes empty subdirectories. The listed directories themselves stay. A path that is not a directory is skipped.

**Warning:** deletion is permanent and there is no dry run. Preview first:

```bash
find "$HOME/Downloads/torrents" -type f -mmin +720   # 720 = 12 hours * 60
```

## Check

```bash
systemctl --user list-timers disk-cleanup.timer
journalctl --user -u disk-cleanup.service       # deleted paths are logged
systemctl --user start disk-cleanup.service     # run now
```

## Stop / remove

```bash
./stop.sh                  # stop, keep files
./uninstall.sh             # remove, keep ~/.config/disk-cleanup/.env
./uninstall.sh --purge     # remove everything
```
