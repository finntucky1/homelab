# Homelab

Personal Raspberry Pi operations, recovery and practical Linux/networking learning, developed with Codex assistance. Owner reproduction and learner completion are recorded separately from agent implementation and testing.

## Current evidence — September 30, 2026

The Pi agent observed Raspberry Pi 5 ARM64, Debian 13, Samsung 990 EVO **Plus** NVMe root and a 3.6 TiB external ext4 SSD. Initial usage was root 3%, external storage 30%. These are point observations supplied by the Pi agent. See [inventory](docs/inventory.md).

The newer [runtime follow-up](docs/pi-runtime-follow-up.md) records Docker server `26.1.5+dfsg1`, four running application containers with zero restarts, Jellyfin's passing declared health check, and existing Grafana, Prometheus, node-exporter and cAdvisor containers. Scrape coverage, alerts and sustained availability remain unverified.

Radarr's actual process resolves qBittorrent and receives HTTP 200 on the tested service path. Its enabled client uses a different host and still reports a health error; the cause is unproven. Runtime labels identify a different Compose source from the [historical candidate](docker-compose/README.md). Both apps already share host downloads with a current path mapping, so the candidate bind edit was withdrawn.

An existing native Radarr ZIP passed isolated CRC, byte comparison and SQLite integrity checks on the Pi. Application startup was not tested. The archive shares the live SSD's failure risk; independent disaster recovery is unverified. See [restore evidence](backups/restore-test.md).

| Work | Implemented / exercised | Remaining boundary |
| --- | --- | --- |
| Health | Capacity/mounts, Docker/optional restart counters, failed units, load/RAM/pressure, thermal, recovery marker and explicit HTTP/DNS probes; readable/JSON states and exits | Missing evidence is UNKNOWN; no automatic repair |
| Recovery | Disposable SQLite lab; static-config/export snapshots, manifests, hashes and isolated byte restores | Independent destination and app recovery unverified |
| Private reports | UTC history, semantic deduplication, retained health status and POSIX modes | Manual collection; timer templates not enabled |
| Documentation | Attributed inventory, diagnostic findings, rollback and learning/portfolio explanations | Owner reproduction and live checks remain open |
| GitHub | Existing working branch and draft PR #1 preserve Pi contributions | No merge authorized |

## Use the tools

Python 3.8+ standard library. Linux/POSIX is required for private config/export and reporting tools; Windows supports the synthetic lab and selected health tests. No tool installs packages or restarts services.

```sh
python3 scripts/healthcheck.py --help
python3 -m unittest discover -s tests -v
python3 scripts/backup_lab.py --json
```

Run live health checks through the Pi agent or owner terminal after confirming Docker context and private config. Health exits: `0` selected checks pass; `1` warning/unknown; `2` failure or invalid arguments. Container state, Docker health and HTTP response are distinct evidence. See [scripts](scripts/README.md), [monitoring](monitoring/README.md), [backups](backups/README.md) and [private reporting](docs/private-reporting.md).

## Repository guide

| Location | Purpose |
| --- | --- |
| [Inventory](docs/inventory.md) and [runtime follow-up](docs/pi-runtime-follow-up.md) | Observations and unknowns |
| [Compose review copy](docker-compose/README.md) | Historical candidate; no deployment instruction |
| [Findings](docs/review-findings.md) and [prepared follow-ups](docs/prepared-changes.md) | Diagnostics, prerequisites and rollback |
| [Operations](docs/operations.md) and [networking](networking/README.md) | Safe triage and access policy |
| [Verification](docs/verification.md) | Separate Pi/MSI commands, results and limits |
| [Learning exercises](docs/learning-exercises.md) and [portfolio](docs/portfolio.md) | Reproduction and learner evidence gates |
| [Backlog](docs/roadmap.md) and [delivery history](docs/access-and-delivery.md) | Remaining work and preserved history |

Credentials, raw logs, endpoints, databases, archives, reports and personal career/vehicle records stay outside public Git. Read [AGENTS.md](AGENTS.md) before changes.
