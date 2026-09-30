# Homelab

Raspberry Pi operations, recovery and practical Linux/networking learning.
This continuation builds on the existing draft PR without creating another
project or deploying a second stack.

## Current evidence — September 29, 2026

The actual Pi was inspected from a restricted local session: Pi 5 ARM64,
Debian 13, Samsung 990 EVO **Plus** NVMe root and a 3.6 TiB external ext4 device.
Root was 3% used and external storage 30% used at baseline. A four-service
Compose candidate was inspected and validated. Runtime Docker/systemd/network
access remains incomplete. See [dated inventory](docs/inventory.md).

An existing native Radarr ZIP was restored privately into an isolated temporary
directory. CRC, file-byte comparisons and SQLite integrity passed. The restored
application was not started, and this same-device archive is not independent
disaster recovery. See [restore evidence](backups/restore-test.md).

| Work | Implemented / exercised | Remaining boundary |
| --- | --- | --- |
| Health report | Filesystems, Docker, failed units, memory/load/pressure, temperature/throttling, recovery marker, explicit HTTP probes; readable/JSON output and failure tests | Denied tools and unconfigured probes are UNKNOWN; no deployment or uptime claim |
| Recovery | Existing synthetic SQLite lab; private static-config/export snapshots with keep-all policy; isolated actual Radarr archive/DB check | Production destination, application startup and independent copy not verified |
| Administration | Private daily report bundles with semantic deduplication and propagated status | One-shot only; no timer/notifications enabled |
| Documentation | Observed inventory, sanitized candidate Compose, findings, conditional corrections/rollback, interview notes and four-week study sequence | Runtime root causes and learner reproduction remain open |
| Delivery | Local branch based on the exact existing draft-PR head | Remote update and merge not performed |

[Verification](docs/verification.md) records commands and test outcomes.
Running tests on the Pi with generated/mocked data is isolated testing, not
evidence that live applications are healthy.

## Use the tools

Python 3.8+ standard library; exercised on Python 3.13.5 ARM64. No dependency
installation, root access or service mutation is needed.

```sh
python3 scripts/healthcheck.py --mount /mnt/storage
python3 scripts/healthcheck.py --help
python3 -m unittest discover -s tests -v
python3 scripts/backup_lab.py --json
```

Health exit codes: 0 pass; 1 warning/unknown; 2 observed failure or invalid
arguments. A running container and an HTTP response are different evidence.
The default report cannot be all-green when backup/probe evidence is missing.
Configure private endpoints/thresholds after reviewing
[scripts](scripts/README.md) and [monitoring](monitoring/README.md).

Use [backup instructions](backups/README.md) for the restricted config/export
tool and [private reporting](docs/private-reporting.md) for report collection.
Never point generic file-copy tooling at running application databases.

## Repository guide

| Location | Purpose |
| --- | --- |
| [Inventory](docs/inventory.md) | Observed facts, reports and unknowns |
| [Compose review copy](docker-compose/README.md) | Sanitized actual declarations; not a deployment instruction |
| [Findings](docs/review-findings.md) | Symptoms, evidence, likely causes and verification |
| [Prepared changes](docs/prepared-changes.md) | Access checks and approval-dependent targeted candidates |
| [Operations](docs/operations.md) | Read-only triage and maintenance |
| [Networking](networking/README.md) | Generic architecture and connectivity diagnosis |
| [Backups](backups/README.md) | Consistency, privacy and isolated restore scope |
| [Monitoring](monitoring/README.md) | Report configuration and uninstalled schedule templates |
| [Study sequence](docs/learning-exercises.md) | Oct 5–30 weekdays, 4–5 PM America/Los_Angeles |
| [Portfolio](docs/portfolio.md) | Honest interview explanations and learner evidence gates |
| [Progress record](docs/progress-2026-09-29.md) | Changed work, results, blockers and next maintenance |

Credentials, raw logs, private endpoints, databases, reports and personal
career/vehicle records stay outside public Git. No cloud synchronization is
assumed. Finances were skipped. Read [AGENTS.md](AGENTS.md) before changes.
