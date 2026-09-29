# Homelab

A Raspberry Pi home server project focused on Linux administration, Docker,
storage, networking, troubleshooting, and recovery. This repository brings
configuration notes and repeatable operating procedures into one place.

## Project status

The repository contains operating documentation, a read-only healthcheck, and
a disposable backup/restore lab with automated tests. Hardware and service
details below are owner-reported; they have not been checked against the live
host. No live Compose files, production backup job, or monitoring deployment
has been verified. See the [verification record](docs/verification.md).

Local status rechecked **2026-09-29**, continuing the reviewed implementation:

| Work | Implemented | Tested locally | Verified on the Pi | Next work |
| --- | --- | --- | --- | --- |
| Read-only healthcheck | Yes: capacity, mount detection, Docker state and explicit expected names | 14 simulated healthcheck tests passed | No | Run with confirmed mount points and container names; review actual probes |
| Backup and restore exercise | Yes: generated SQLite/JSON data, integrity, retention and failure checks | Disposable restore passed; all 14 backup tests passed on Linux | No | Agree on a destination and application consistency, then authorize an isolated service restore |
| Operating and learning documentation | Yes: inventory, evidence guide, runbooks, backlog and exercises | Links and documentation reviewed | No live configuration supplied | Reconcile sanitized Compose/runtime evidence with these notes |
| Production backup and monitoring | Planned only | No production job, schedule or alert delivery tested | No | Confirm services, data paths, policy, destination and notification requirements |
| GitHub delivery | Reviewed implementation on `codex/homelab-operations-2026-09-23` | Authenticated branch creation succeeded September 29 | Not applicable | Review the draft PR; merging requires explicit direction |

“Tested locally” describes simulated or generated data in a disposable Linux
workspace; all 28 tests passed with no skips. Earlier Windows results are kept
in the verification record. Neither environment establishes Pi deployment or
live application recovery.

## Reported setup

| Component | Reported configuration |
| --- | --- |
| Server | Raspberry Pi 5, 16 GB RAM, active cooling |
| System storage | 1 TB Samsung 990 EVO NVMe, used for boot |
| Data storage | External 4 TB SSD |
| Network | UniFi Cloud Gateway Max and USW-Pro-XG-8-PoE |
| Power | PoE+ HAT |
| Remote access | WireGuard |
| Container management | Docker and Portainer |
| Services | Jellyfin, Sonarr, Radarr, Prowlarr, qBittorrent, FlareSolverr |

Version numbers, storage mappings, service health, and network paths are still
to be verified. See the [inventory](docs/inventory.md).

## Start here

On the Linux host, with Python 3.8 or newer installed:

```sh
git clone https://github.com/finntucky1/homelab.git
cd homelab
git switch codex/homelab-operations-2026-09-23
python3 scripts/healthcheck.py
```

This checks root filesystem capacity and queries Docker container status. It
does not install software, restart containers, change permissions, or configure
the Pi. A running container is not proof that its application is reachable.
See the [script instructions](scripts/README.md) for mounted storage checks,
expected containers, JSON output, and exit codes. Review output before sharing
it publicly. Docker uses the CLI's active context: verify that context before
treating its response as evidence from the Pi.

To gather the missing deployment evidence, follow the short
[Pi evidence guide](docs/pi-evidence.md). The owner chose sanitized outputs
instead of direct SSH access and disposable backup testing until a destination
is selected (2026-09-23).

## Repository guide

| Location | Purpose |
| --- | --- |
| [docker-compose/](docker-compose/README.md) | Import and document sanitized live stack definitions |
| [scripts/](scripts/README.md) | Read-only host checks and future tested automation |
| [networking/](networking/README.md) | Network roles, remote access, and troubleshooting notes |
| [backups/](backups/README.md) | Tested disposable lab and production recovery prerequisites |
| [monitoring/](monitoring/README.md) | Baseline checks and monitoring roadmap |
| [docs/](docs/inventory.md) | Inventory and day-to-day operating procedures |
| [tests/](tests/test_healthcheck.py) | Simulated health failures and disposable backup/restore tests |
| [Review findings](docs/review-findings.md) | Evidence and outstanding live-review questions |
| [Learning exercises](docs/learning-exercises.md) | Practical diagnostics and recovery exercises |
| [Portfolio evidence](docs/portfolio.md) | Implementation, limitations, and interview talking points |

## Next milestones

1. Verify the host inventory and import redacted Compose definitions.
2. Choose a backup destination and prove one service can be restored.
3. Confirm network and remote-access design.
4. Add monitoring and record a troubleshooting case study.

The [initial backlog](docs/roadmap.md) contains the completion criteria.
Track future progress in [GitHub Issues](https://github.com/finntucky1/homelab/issues).
Record measured outcomes and completed work as evidence grows; this repository
does not claim unmeasured uptime or tested recovery of the live homelab.

## Local validation

```sh
python3 -m unittest discover -s tests -v
python3 scripts/backup_lab.py
git diff --check
```

The tests use temporary directories and simulated Docker responses, and do not
connect to the home server. The backup lab creates its own sample data and
isolated restore target; it cannot back up the live host. Read
[CONTRIBUTING.md](CONTRIBUTING.md) and [AGENTS.md](AGENTS.md) before adding live
configuration.
