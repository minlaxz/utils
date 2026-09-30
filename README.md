# utils

Small Linux services. Each one runs as a systemd user timer and needs no root. Each folder is self-contained and has its own README.

| Service | What it does | Runs |
|---|---|---|
| [db-to-file-service](db-to-file-service/) | Copies the access token from a SQLite DB into `auth.json` | every 15 min |
| [disk-cleanup-service](disk-cleanup-service/) | Deletes old files from listed directories | hourly |
| [myaddr-service](myaddr-service/) | Updates [myaddr.tools](https://myaddr.tools) IPv4 records | hourly |

## Layout

Every service follows the same shape:

```
<name>-service/
  README.md       how to install, configure, check, remove
  install.sh      installs to ~/.local and ~/.config, enables the timer
  uninstall.sh    removes what install.sh put in place
  .env.example    settings template, .env.sample in myaddr (real .env is gitignored)
  systemd/        <name>.service and <name>.timer
```

## Quick start

```bash
cd <name>-service
cat README.md     # read first: each service needs different settings
./install.sh
```

All installers run `loginctl enable-linger`, so timers keep running after you log out.
