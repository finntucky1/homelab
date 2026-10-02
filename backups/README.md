# Backups and recovery

**Updated 2026-09-30:** complete independent backup remains unestablished; no new
production job or schedule was deployed. All twelve native arr ZIPs passed CRC.
The newest Radarr archive passed private file/DB restore and isolated same-image
startup/data read. Integrations/service recovery and full DR remain unvalidated.
See [live audit](../docs/live-audit-2026-09-30.md) and [restore-test.md](restore-test.md).
Native archives share their production SSD. A private four-file pre-change
config snapshot on NVMe is a partial, same-host separate-disk copy only.

backup_config.py provides manifests/hashes, explicit destinations, private modes,
keep-all development retention, failure handling and isolated byte recovery.
It was exercised with generated inputs and a narrow actual static-config snapshot.
The new [destination preflight](../scripts/backup_destination.py) is always a
no-write dry run; [usage](../scripts/README.md) states its explicit-source, ext4
and expected-mount requirements. Run it before an approved operation; no fallback
destination is allowed. A target outside both production disks is needed for
all-host disk independence; off-host storage is needed for host-loss protection.

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

## Explicit configuration/export snapshots

`scripts/backup_config.py` uses Python 3.8+ and POSIX permissions. It accepts an
explicit file list, copies each payload under a safe label, and verifies a
manifest of sizes and SHA-256 hashes. It does not walk input directories or
extract archive contents. Restoring an application export here recovers its
opaque bytes; the application's documented isolated import remains a separate
test. No container or application is started by this tool.

```sh
python3 scripts/backup_config.py --help
python3 -m unittest discover -s tests -p 'test_backup_config.py' -v
```

Source files must already be static, or be completed exports produced using the
verified application's supported method. `--consistent-inputs` explicitly
acknowledges that prerequisite; it does not make a changing application
consistent. Source size/device/inode/mtime/ctime are checked across each bounded
read, and bytes are compared with preflight hashes. This detects common file
changes, not a coordinated transaction across multiple application files.

| Rule | Implemented behavior |
| --- | --- |
| Selection | 1–64 named regular files; absolute paths; duplicate labels refused |
| Static input extensions | `.json`, `.yaml`, `.yml`, `.conf`, `.ini`, `.xml`, `.toml`, `.txt`, `.env`, `.service` |
| Completed export extensions | `.zip`, `.tar`, `.tar.gz`, `.tgz`; stored without extraction |
| Live data refusal | No directories, raw database extensions, SQLite headers, runtime pseudo-filesystems, or symlinks in path components |
| Destination | Must already exist, owned by the current user, mode `0700`, outside source directories; size/free-space preflight |
| Limits | 256 MiB per file and 512 MiB total; 64 KiB manifest; reads use 64 KiB chunks |
| Snapshot permissions | New directories `0700`, payload and manifest files `0600`; verification refuses relaxed modes |
| Retention | Explicit **keep-all** development policy; no prune/delete operation; existing snapshot names refused |
| Restore | Verify everything first, then create a new directory outside the snapshot destination; existing targets refused |
| Failure | Exit `2`, sanitized fixed messages, no paths or contents in logs; partial new output retained for private review, never marked successful |

The tool expects trusted, private directories controlled by its operator. It
does not provide a hostile same-user security boundary, signed manifests,
encryption, transport, guaranteed power-loss durability, or remote-mount identity
verification. Restrictive file modes do not replace encryption or recovery-key
planning. A newly missing network mount may leave a local directory at its path;
verify the destination's identity before each approved production operation.

The commands below show the exact narrow **proposed configuration-only** first
run. They use explicit placeholders because a separate recovery destination
and source selection require a private review. They have not been run on the Pi.
The original four-service Compose definition was privately verified and passed
quiet Compose validation. Select that single file by its privately recorded
absolute path; no path or username is recorded here. Only reviewed original
stack definitions qualify; do not select resolved
Compose output, environment dumps, `/config` directories, raw databases, media,
downloads, VPN keys, or credentials. Real definitions may themselves contain
secrets: keep the destination and all outputs outside this public repository.

```sh
# Replace all placeholders after reviewing scope, path identity, and permissions.
# DESTINATION_ROOT and RESTORE_PARENT must already exist, owned by the operator,
# mode 0700, outside every selected source directory and on the agreed storage.
python3 scripts/backup_config.py --json create \
  --destination /APPROVED_SEPARATE_BACKUP_ROOT \
  --snapshot-id config-20260929-01 \
  --input-kind static-config --consistent-inputs \
  --file stack_definition=/VERIFIED_STATIC_STACK_DIRECTORY/docker-compose.yml
python3 scripts/backup_config.py --json verify \
  --snapshot /APPROVED_SEPARATE_BACKUP_ROOT/config-20260929-01
python3 scripts/backup_config.py --json restore \
  --snapshot /APPROVED_SEPARATE_BACKUP_ROOT/config-20260929-01 \
  --target /APPROVED_ISOLATED_RESTORE_PARENT/config-20260929-01 \
  --marker /APPROVED_PRIVATE_PROOF_DIRECTORY/config-20260929-01.json
```

Review restored bytes privately and record that this protects selected static
definitions only. The restore marker is created only after hash checks succeed;
it has mode `0600` and exact fields `schema: 1`, `kind: config-export-recovery`,
`status: verified`, `snapshot_id`, `manifest_sha256`, `created_at`, and
`recovered_at` (UTC `YYYY-MM-DDTHH:MM:SSZ`). It contains no source paths.
Existing markers are refused, so each new recovery test gets a new marker and
the health configuration is deliberately pointed at the chosen proof. Freshness
uses the age of `created_at`, not the later restore time. `created_at` records
this tool's snapshot packaging time; it does not authenticate the age of the
application data inside a pre-existing export. Review native export timestamps
and data coverage separately. This is evidence of
static/export byte recovery only, not application startup, complete coverage,
or protection against loss of a same-disk snapshot.

Restored files retain their safe labels instead of source filenames. For a later
approved native application import, privately give the recovered opaque export
the extension expected by that application's importer; do not expand it into
live paths. This tool does not interpret export contents or validate their
application/database semantics.

## Application consistency methods to review

Primary documentation was checked on 2026-09-29. Match the method to the installed
version and observed mount layout before selecting an input. No new native
export, application restore, or service stop was performed by this tool.

| Application | Supported method and scope |
| --- | --- |
| Sonarr | Use its completed native ZIP from System → Backup; the [official documentation](https://github.com/Servarr/Wiki/blob/master/sonarr/system.md#backup) describes manual backup and ZIP restore. Import only into an isolated matching-version test instance. |
| Radarr | Use its completed native ZIP, following the [official backup controls](https://github.com/Servarr/Wiki/blob/master/radarr/system.md#backup). September 30 file/DB and isolated same-image startup passed; integration/full service recovery remains untested. |
| Prowlarr | Use its completed native ZIP from the [official Backup controls](https://github.com/Servarr/Wiki/blob/master/prowlarr/system.md#backup); verify isolated application recovery separately. |
| Jellyfin | Observed version 10.11.8. Review its supported built-in backup scope using the [official guide](https://jellyfin.org/docs/general/administration/backup-and-restore/); completed backup/startup recovery remains unverified. For earlier versions manual backup requires stopping the server before copying complete data/configuration. No stop/copy is authorized here. |
| Portainer | The [native backup download](https://docs.portainer.io/admin/settings/general#back-up-portainer) produces a configuration archive, optionally password-protected. It does not back up managed application volumes. Native restore requires a fresh instance with an empty data volume. |
| qBittorrent | Its [official settings inventory](https://github.com/qbittorrent/qBittorrent/wiki/Frequently-Asked-Questions#where-does-qbittorrent-save-its-settings) distinguishes preferences and torrent/resume data. A single config file is not complete client recovery. A coordinated stop/profile recovery plan is pending; no raw runtime copy is implemented. |
| FlareSolverr / WireGuard | Confirm deployment, persistent state, and required recovery scope from actual definitions. VPN secret/key recovery requires a private plan; neither is included in the configuration-only candidate. |

## Requirements before implementing a live workflow

| Required information or decision | Current status |
| --- | --- |
| Verified service versions, Compose files, and real bind/volume paths | See [inventory](../docs/inventory.md) and dated Pi evidence; selected backup source list still needs review |
| Which configurations, databases, media, downloads, and VPN material need recovery | Not agreed |
| Destination on a separate failure domain, available capacity, access method | Destination undecided; do not assume the attached SSD is a backup destination |
| Maximum acceptable lost data and recovery time | Not agreed or measured |
| Schedule, retention, encryption, and separately stored recovery keys | Not agreed |
| Consistency method supported by each verified application | Primary-method review above; application-specific execution and startup recovery remain pending |
| Failure notification recipient/channel and access permissions | Not agreed |
| Approval for service stops, live installations, schedule activation, or deletion | Required before those live changes |

An extra directory or copy on the same disk does not protect against loss of that
disk. Decide whether a separate destination also needs an offsite copy. Keep real
configuration, credentials, VPN keys, backup archives, and recovery keys outside
this public repository.

Once scope and destination decisions are available, review the candidate workflow
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
