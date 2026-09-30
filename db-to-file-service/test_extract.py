"""Self-check for extract.py. Run: python3 test_extract.py"""
import json
import os
import sqlite3
import stat
import tempfile

import extract

EMAIL = "someone@example.com"
DATA = {
    "accessToken": "tok-abc",
    "refreshToken": "must-not-leak",
    "lastRefreshAt": "2026-09-08T10:15:30.123Z",
    "lastPingAt": "2026-09-08T11:00:00.000Z",
}


def make_db(path, rows):
    con = sqlite3.connect(path)
    con.execute(
        "CREATE TABLE providerConnections (id TEXT PRIMARY KEY, provider TEXT NOT NULL,"
        " authType TEXT NOT NULL, name TEXT, email TEXT, priority INTEGER,"
        " isActive INTEGER DEFAULT 1, data TEXT NOT NULL, createdAt TEXT NOT NULL,"
        " updatedAt TEXT NOT NULL)"
    )
    for i, (email, active, updated, data) in enumerate(rows):
        con.execute(
            "INSERT INTO providerConnections VALUES (?, 'openai', 'oauth', NULL, ?, 0, ?, ?, ?, ?)",
            (str(i), email, active, json.dumps(data), updated, updated),
        )
    con.commit()
    con.close()


def main():
    with tempfile.TemporaryDirectory() as d:
        db = os.path.join(d, "data.sqlite")
        out = os.path.join(d, "auth.json")
        make_db(db, [(EMAIL, 1, "2026-01-01", DATA)])

        # first sync writes
        assert extract.sync(db, EMAIL, out) is True
        doc = json.load(open(out))
        prov = doc["providers"]["openai-codex"]
        pool = doc["credential_pool"]["openai-codex"][0]
        assert prov["tokens"]["access_token"] == "tok-abc"
        assert pool["access_token"] == "tok-abc"
        assert prov["tokens"]["refresh_token"] == ""
        assert pool["refresh_token"] == ""
        assert "must-not-leak" not in open(out).read()
        assert prov["last_refresh"] == "2026-09-07T10:15:30.123Z"
        assert pool["last_refresh"] == "2026-09-07T10:15:30.123Z"
        assert doc["updated_at"] == "2026-09-08T11:00:00.000Z"
        assert pool["id"] == "aa52f2"
        assert stat.S_IMODE(os.stat(out).st_mode) == 0o600

        # unchanged source -> no write
        before = os.stat(out).st_mtime_ns
        assert extract.sync(db, EMAIL, out) is False
        assert os.stat(out).st_mtime_ns == before

        # consumer edit gets reverted
        doc["credential_pool"]["openai-codex"][0]["request_count"] = 7
        json.dump(doc, open(out, "w"))
        assert extract.sync(db, EMAIL, out) is True
        assert json.load(open(out))["credential_pool"]["openai-codex"][0]["request_count"] == 0

        # missing row -> error, file untouched
        content = open(out).read()
        try:
            extract.sync(db, "nobody@example.com", out)
            assert False, "expected SyncError"
        except extract.SyncError:
            pass
        assert open(out).read() == content

        # multiple rows -> active + newest wins
        db2 = os.path.join(d, "data2.sqlite")
        newer = dict(DATA, accessToken="tok-new")
        inactive = dict(DATA, accessToken="tok-inactive")
        make_db(db2, [(EMAIL, 1, "2026-01-01", DATA), (EMAIL, 1, "2026-02-01", newer), (EMAIL, 0, "2026-03-01", inactive)])
        out2 = os.path.join(d, "auth2.json")
        extract.sync(db2, EMAIL, out2)
        assert json.load(open(out2))["providers"]["openai-codex"]["tokens"]["access_token"] == "tok-new"

    check_ssh()
    print("ok")


def check_ssh():
    """Fake ssh on PATH: runs the remote command locally with $HOME as cwd."""
    with tempfile.TemporaryDirectory() as d:
        home = os.path.join(d, "home")
        os.makedirs(os.path.join(home, "app"))
        bindir = os.path.join(d, "bin")
        os.mkdir(bindir)
        fake = os.path.join(bindir, "ssh")
        with open(fake, "w") as f:
            f.write('#!/bin/sh\n[ "$FAKE_SSH_FAIL" = 1 ] && { echo "no route" >&2; exit 255; }\n'
                    'for last; do :; done\ncd "$FAKE_HOME" && exec sh -c "$last"\n')
        os.chmod(fake, 0o755)
        env_before = dict(os.environ)
        os.environ.update(PATH=bindir + os.pathsep + os.environ["PATH"], FAKE_HOME=home)
        try:
            db = os.path.join(d, "data.sqlite")
            out = os.path.join(d, "auth.json")
            make_db(db, [(EMAIL, 1, "2026-01-01", DATA)])
            remote = os.path.join(home, "app", "auth.json")
            abs_dir = os.path.join(d, "abs dir")  # space checks quoting
            os.mkdir(abs_dir)

            assert extract.sync(db, EMAIL, out, ssh_targets=["h:~/app", "h:" + abs_dir]) is True
            assert open(remote).read() == open(out).read()
            assert open(os.path.join(abs_dir, "auth.json")).read() == open(out).read()
            assert stat.S_IMODE(os.stat(remote).st_mode) == 0o600

            # unchanged -> remote not replaced, no tmp left behind
            before = os.stat(remote).st_mtime_ns
            assert extract.sync(db, EMAIL, out, ssh_targets=["h:~/app"]) is False
            assert os.stat(remote).st_mtime_ns == before
            assert not os.path.exists(remote + ".tmp")

            # consumer edit on remote gets reverted
            open(remote, "w").write("{}")
            assert extract.sync(db, EMAIL, out, ssh_targets=["h:~/app"]) is True
            assert open(remote).read() == open(out).read()

            # failing host -> SyncError, local still written
            os.remove(out)
            os.environ["FAKE_SSH_FAIL"] = "1"
            try:
                extract.sync(db, EMAIL, out, ssh_targets=["h:~/app"])
                assert False, "expected SyncError"
            except extract.SyncError as e:
                assert "no route" in str(e)
            assert os.path.exists(out)

            try:
                extract.ssh_write_if_changed("nocolon", "x")
                assert False, "expected SyncError"
            except extract.SyncError:
                pass
        finally:
            os.environ.clear()
            os.environ.update(env_before)


if __name__ == "__main__":
    main()
