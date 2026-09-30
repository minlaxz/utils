# myaddr-service

Keeps [myaddr.tools](https://myaddr.tools) IPv4 records up to date. A systemd user timer runs `myaddr.sh` every hour. Linux only; no root needed.

## Install

```bash
cp .env.sample .env
# edit .env: MYADDR_KEYS="key1 key2 ..."
./install.sh
```

`install.sh` does this:

- copies `myaddr.sh` to `~/.local/bin/`
- copies `.env` to `~/.config/myaddr/.env` (mode 600)
- installs `systemd/myaddr.service` and `systemd/myaddr.timer` to `~/.config/systemd/user/`
- enables the timer and runs one update now
- runs `loginctl enable-linger` so the timer runs when you are logged out

The timer runs 1 minute after boot, then every hour.

## Change keys

Edit `.env` in this directory, then run `./install.sh` again. Or edit `~/.config/myaddr/.env` directly. The next run uses the new keys.

## Check

```bash
systemctl --user list-timers myaddr.timer
journalctl --user -u myaddr.service
systemctl --user start myaddr.service   # run now
```

If one key fails, the other keys still update. The log shows `key #N failed` (keys are numbered, not printed) and the service run is marked failed.

## Stop / remove

```bash
systemctl --user disable --now myaddr.timer   # stop, keep files
./uninstall.sh                                # remove, keep ~/.config/myaddr/.env
./uninstall.sh --purge                        # remove everything
```
