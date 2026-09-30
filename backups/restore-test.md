# Restore test record

## September 29 native Radarr archive verification

An existing native Radarr ZIP was restored into a new private temporary
directory on the Pi. This used the completed application archive, not a raw copy
of the running database. Recorded check time: **2026-09-29 22:58 PDT**
(`2026-09-30T05:58:04Z`). The archive's modification time was
`2026-09-29T03:25:48Z` (**September 28 20:25 PDT**); this is observed filesystem
mtime, not an independently authenticated export timestamp.

| Check | Observed result |
| --- | --- |
| Archive size | 3,701,463 bytes |
| Files restored | 3 files; 12,997,196 bytes expanded |
| ZIP integrity | CRC verification passed |
| Restored bytes | Matched the corresponding archive entries |
| SQLite check | `integrity_check` returned `ok`; 42 tables observed |
| Isolation and permissions | New temporary directory mode `0700`; restored files mode `0600`; no live files overwritten |
| Application startup / integrations | Not started or tested |
| Version evidence | Archive filename reported `6.1.1.10360`; runtime version was not established by this restore test |
| Cleanup | Temporary restored files removed; no archive/database/configuration contents copied into Git |
| Storage limitation | Native archive and live configuration are on the same external SSD; shared disk-failure risk |

This provides evidence that this existing archive could be read and restored
to files and that its SQLite database passed an integrity check. It does not
prove login, expected application data, integration behavior, recovery time,
off-disk recovery, or whole-stack coverage. No new backup schedule, notification,
service restart, or production replacement was performed.

To repeat this authorized archive-level check, use a completed native export
and a newly created isolated private workspace. Enumerate and bound all ZIP
entries before writes; refuse absolute names, parent traversal, symlinks,
unexpected names, and duplicate entries. Check archive CRCs, write only regular
files under that workspace with mode `0600`, and compare each restored file's
SHA-256 and byte count with its archive entry. Open only the isolated recovered
database for `integrity_check`; do not open or copy the live database. Record
sanitized counts/check outcomes, remove only the temporary workspace you created,
and leave source archives untouched. Application startup needs a separate test
instance, matching version, disabled integrations, and its own approved plan.

## September 29 explicit-file tooling verification

`backup_config.py` passed **17 generated-fixture tests on Linux**, with no skips.
The tests cover hash-verified byte recovery and a private success marker;
keep-all retention and existing snapshot refusal; corruption and traversal
refusal before restore writes; existing restore/marker preservation; missing
destinations; directory, database extension, and SQLite-header refusal; static
input acknowledgement; overlapping paths; symlinks including parent components;
mode checks without repairing existing permissions; size/count/free-space
limits; changed inputs during read and after preflight; opaque export handling;
deeply nested malformed JSON, and sanitized failures. No live source was passed
to the new script.

```sh
python3 -m unittest discover -s tests -p 'test_backup_config.py' -v
python3 scripts/backup_config.py --help
```

These fixture checks establish the explicit-file tool's tested behavior only.
Production source selection, separate destination, encryption/key recovery,
schedule, application-specific restore checks, and alert delivery remain pending.

## Historical September 29 pre-Pi Linux recheck

The unchanged reviewed lab passed in a disposable Linux workspace. All 14
backup tests passed as part of the 28-test full suite, including POSIX mode
and real symbolic-link checks; no tests were skipped. The JSON demonstration
returned PASS, exit 0, with two restored SQLite rows, matching hashes,
integrity `ok`, corruption refusal, sample retention, and cleanup. It reported
directories mode 0700 and files mode 0600. These checks used only generated
data; production application recovery remains untested. Earlier Windows
observations below are retained as dated evidence.

## Disposable sample exercise: 2026-09-23

**Passed for generated sample data only. Live system recovery remains untested.**

Rechecked **2026-09-28** with the unchanged lab on Windows/Python 3.12.14:
the disposable demonstration passed again with the same two-row restore,
integrity, corruption-refusal, retention and cleanup outcomes below. The full
suite rerun executed the 14 backup tests: 12 passed and the same two
host-dependent cases were skipped. No live source or service was accessed.

| Field | Observed result |
| --- | --- |
| Test host | Local Windows development environment, not the Raspberry Pi |
| Interpreter | Python 3.12.14; compatibility with Python 3.8 has not been executed |
| Command | `python scripts/backup_lab.py --json` |
| Exit status | `0` |
| Sources | Generated static JSON and a synthetic two-row WAL SQLite database |
| Backup mechanism | Static file copy and SQLite backup API; three generated snapshots |
| Destination | New disposable temporary directory owned by the exercise |
| Restore destination | New isolated subdirectory; no live files or services accessed |
| Data checks | Manifest byte counts and SHA-256 matched; SQLite `integrity_check` returned `ok`; two expected records restored |
| Corruption exercise | Modified sample file was refused before a restore directory was created |
| Retention exercise | One older sample snapshot removed; two retained until final workspace cleanup |
| Permissions | Windows inherited ACL; not independently verified |
| Cleanup | Temporary workspace removed on normal completion |
| Recovery time | Not measured; no production recovery objective established |
| Application recovery | Not tested; no Jellyfin, Sonarr, Radarr, Prowlarr, qBittorrent, Portainer, FlareSolverr, or WireGuard instance restored |

Dedicated test command:

```sh
python -m unittest discover -s tests -p test_backup_lab.py -v
```

Observed result: **14 tests run, 12 passed, 2 skipped, no failures**. The two skips
were the POSIX mode check on Windows and a real symbolic-link test because this
host did not permit creating symbolic links. The remaining tests cover isolated
SQLite snapshot contents after later source changes, hash corruption, manifest
rejection, refusal to overwrite an existing restore, retention preflight,
rejection of live source CLI arguments, cleanup after failure, and sanitized
failure reporting. Skips are not evidence that those host-dependent cases passed.

This run validates a sample workflow and selected error paths. It does not
establish the Pi's backup coverage, remote destination access, encrypted recovery,
service permissions, restore duration, recovery after a power loss, or recovery
of actual application databases. No backup schedule or alert delivery was tested.

## Template for a later authorized live-data restore test

Use generic labels for public evidence; keep sensitive details in a private copy.

| Field | Result |
| --- | --- |
| Test date, operator, and approved scope | Pending |
| Verified service and image/application version | Pending |
| Backup identifier, creation time, and consistency method | Pending |
| Source data coverage and explicitly excluded data | Pending |
| Destination failure domain and retention | Pending |
| Encryption and recovery-key availability | Pending; do not record keys here |
| Isolated restore destination and network restrictions | Pending |
| Restored ownership/permissions | Pending |
| Steps followed and deviations | Pending |
| File integrity, database, and actual application checks | Pending |
| Notification/failure-path checks | Pending |
| Measured restore time and recoverable data age | Not measured |
| Issues, corrective actions, and next test | Pending |

Never test restoration by overwriting the only live copy. Confirm the test
instance cannot write to production data, reach external integrations, run
download jobs, or expose services unintentionally. Obtain the required approval
before live service changes, installations on the Pi, reboots, or deletions.
