# Restore test record

## September 29 Linux recheck

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
