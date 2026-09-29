# Backups and recovery

**Decision recorded 2026-09-23:** the destination is undecided; the owner authorized
testing disposable data only. No backup job has been deployed to the Pi. No live
application or production recovery has been tested. The implemented lab below is
an exercise and a verification tool, not a production backup command.

## Run the disposable exercise

From the repository root with Python 3.8 or newer and its standard SQLite module:

```sh
python3 scripts/backup_lab.py --json
python3 -m unittest discover -s tests -p 'test_backup_lab.py' -v
```

On Windows, use the available Python executable in place of `python3`.
The program accepts no source or destination paths, uses no network, and needs
no Docker, root access, or third-party packages. It creates its own temporary
workspace and removes that generated workspace when finished, including after
ordinary failures. An interrupted process or power loss can leave temporary
files; no permanent backup is produced.

The exercise:

1. Generates a static JSON configuration and a two-row SQLite database in WAL
   mode. These files contain only synthetic data.
2. Creates three snapshots. The static file is copied; the database is copied
   using SQLite's backup API while the source connection remains open.
3. Records each file's byte count and SHA-256 hash. Before restoration, validates
   the fixed manifest schema and exact filenames, then verifies both files.
4. Restores into a new isolated directory, checks the copied bytes, runs SQLite's
   `integrity_check`, and checks the expected records. An existing restore
   directory causes failure rather than replacement.
5. Demonstrates keeping the latest two sample snapshots. Retention validates
   every snapshot before deleting the oldest, and refuses unexpected entries.
   Deletion is confined to this run's newly created temporary workspace.
6. Deliberately corrupts a sample snapshot and confirms restoration refuses it
   before creating a restore directory.

The exit status is `0` for a passed exercise and `2` for an expected failure or
invalid command argument. `--json` produces a machine-readable result; OS and
database error messages are summarized without exposing their paths. A failed
run suggests checking temporary-directory access, available space, and SQLite
support. No external notification or scheduled job is installed.

## Design boundaries

The consistency mechanism uses Python's
[`Connection.backup`](https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.backup)
and SQLite's [online backup API](https://www.sqlite.org/backup.html). This is
appropriate for the synthetic single-database fixture; support for a real
application's complete data set must be reviewed separately.

| Concern | What the lab demonstrates | What production still needs |
| --- | --- | --- |
| Consistency | SQLite backup API for one synthetic database; static settings fixture | Application-supported exports or an approved coordinated stop/snapshot method; dependencies between databases and files |
| Integrity | Hash comparison, database integrity check, and expected sample records | Application startup and meaningful data checks after isolated recovery |
| Retention | Keep two verified snapshots inside one disposable workspace | An agreed schedule and retention policy based on recoverable history and destination capacity |
| Permissions | Explicit directories `0700` and files `0600` on POSIX | Verified source ownership, restore UID/GID, service access, destination ACLs, and encryption/key recovery |
| Failure reporting | Sanitized result and nonzero exit; temporary workspace cleanup | An approved scheduler and alert destination; detection of missing or stale backups, failed transfers, and failed restore tests |
| Recovery isolation | New temporary directory, no live application started | Separate paths and isolated networking; integrations disabled; no overwrite of the live copy |

On Windows, files inherit temporary-directory ACLs. The lab does **not** inspect
those ACLs or claim private Windows permissions. POSIX permissions and symbolic
link rejection have tests, but tests needing unavailable host features report
skips. The script uses Python 3.8-compatible syntax; see the verification record
for the interpreter actually tested.

Hashes detect accidental damage; an attacker who replaces both the file and its
manifest can replace those hashes too. This lab provides no authenticity,
encryption, remote transport, offsite storage, application integration, or
multiuser security boundary. A successful lab run says nothing about the Pi's
current storage, real databases, service configuration, uptime, or recovery time.

## Requirements before implementing a live workflow

| Required information or decision | Current status |
| --- | --- |
| Verified service versions, Compose files, and real bind/volume paths | Awaiting sanitized evidence from the Pi |
| Which configurations, databases, media, downloads, and VPN material need recovery | Not agreed |
| Destination on a separate failure domain, available capacity, access method | Destination undecided; do not assume the attached SSD is a backup destination |
| Maximum acceptable lost data and recovery time | Not agreed or measured |
| Schedule, retention, encryption, and separately stored recovery keys | Not agreed |
| Consistency method supported by each verified application | Not reviewed against live service evidence |
| Failure notification recipient/channel and access permissions | Not agreed |
| Approval for service stops, live installations, schedule activation, or deletion | Required before those live changes |

An extra directory or copy on the same disk does not protect against loss of that
disk. Decide whether a separate destination also needs an offsite copy. Keep real
configuration, credentials, VPN keys, backup archives, and recovery keys outside
this public repository.

Once evidence and decisions are available, implement and review the live workflow
before enabling it. First make one consistent backup, then restore to an isolated
test environment and check the actual application. Record its limitations and
results in [restore-test.md](restore-test.md). Only after those checks and the
required approval should the job run on a schedule. Check backup freshness and
repeat restore testing after meaningful service or storage changes.

## Learning tasks

- Explain why copying only the main file of a running WAL database may miss
  committed data, and how this lab avoids that particular problem.
- Read `test_sqlite_snapshot_is_consistent_and_independent`: why should a new row
  committed after the snapshot be absent from the restored copy?
- Follow `test_retention_validates_all_before_deleting`: explain why validating
  all candidates before deletion protects the last known sample snapshots.
- Compare a hash match, `integrity_check`, and an application login/data query.
  State what each establishes and what it leaves untested.
- Draft a recovery checklist with placeholder source/destination names, expected
  UID/GID, recovery keys, and a failure contact. Do not put real secrets in Git.
