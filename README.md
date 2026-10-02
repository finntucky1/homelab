# Homelab

Personal Raspberry Pi operations, recovery and practical Linux/networking learning, developed with Codex assistance. Owner reproduction and learner completion are recorded separately from agent implementation and testing.

## Current evidence — September 30, 2026

The Pi agent observed Raspberry Pi 5 ARM64, Debian 13, Samsung 990 EVO **Plus** NVMe root and a 3.6 TiB external ext4 SSD. Initial usage was root 3%, external storage 30%. These are point observations supplied by the Pi agent. See [inventory](docs/inventory.md).

The direct [live audit](docs/live-audit-2026-09-30.md) records Docker server `26.1.5+dfsg1`, all 12 running containers with zero restarts, and healthy declared Jellyfin/cAdvisor checks. Prometheus has three working targets and observed host/container metrics. Grafana health passes; dashboards, alerts and sustained availability remain unverified.

Radarr's actual process resolves qBittorrent and receives HTTP 200 on the service WebUI. The enabled client's configured endpoint still times out. Initial credentials established no API session; a later observed restart/profile change makes current login availability unknown. A narrow reset is prepared, conditional on confirming it is still needed and approval. Current Compose files were located and compared with runtime. Both apps share host downloads with a matching mapping; the historical candidate bind edit remains withdrawn.

All 12 native arr backup ZIPs passed CRC checks. The newest Radarr ZIP passed isolated file/SQLite restore and matching-image application startup/data read. Its native archive shares the live SSD's failure risk; complete independent backup and full disaster recovery remain unverified. See [restore evidence](backups/restore-test.md).

| Work | Implemented / exercised | Remaining boundary |
| --- | --- | --- |
| Health | Capacity/mounts, Docker/optional restart counters, failed units, load/RAM/pressure, thermal, recovery marker and explicit HTTP/DNS probes; readable/JSON states and exits | Missing evidence is UNKNOWN; no automatic repair |
| Recovery | Disposable lab; static config/export manifests/hashes; no-write destination preflight; isolated Radarr startup | Complete independent backup, integrations and full DR unverified |
| Private reports | UTC history, semantic deduplication, retained health status and POSIX modes | Manual collection; timer templates not enabled |
| Documentation | Current direct Pi audit, selected JSON, source differences and prepared rollback | Owner reproduction and access-policy checks remain open |
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
| [Live audit](docs/live-audit-2026-09-30.md), [selected JSON](docs/evidence/pi-2026-09-30.json) and [inventory](docs/inventory.md) | Current observations and dated history |
| [Compose review copy](docker-compose/README.md) | Historical candidate; no deployment instruction |
| [Findings](docs/review-findings.md) and [prepared follow-ups](docs/prepared-changes.md) | Diagnostics, prerequisites and rollback |
| [Operations](docs/operations.md) and [networking](networking/README.md) | Safe triage and access policy |
| [Verification](docs/verification.md) | Separate Pi/MSI commands, results and limits |
| [Learning exercises](docs/learning-exercises.md) and [portfolio](docs/portfolio.md) | Reproduction and learner evidence gates |
| [Backlog](docs/roadmap.md) and [delivery history](docs/access-and-delivery.md) | Remaining work and preserved history |

Credentials, raw logs, endpoints, databases, archives, reports and personal career/vehicle records stay outside public Git. Read [AGENTS.md](AGENTS.md) before changes.
