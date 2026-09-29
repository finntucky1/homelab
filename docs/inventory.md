# Host and service inventory

Status: reported baseline; current host verification is pending. Keep serial
numbers, access credentials, real addresses, and account details private.

Last reviewed: 2026-09-23. Evidence inspected: current repository and prepared
starter ZIP. Neither contains actual Compose definitions, live host outputs,
or administrative handoff requirements. The owner will supply sanitized outputs
using [pi-evidence.md](pi-evidence.md); no SSH session has been established.

| Verified repository fact | Evidence |
| --- | --- |
| Starting repository contained only `README.md` | Base commit `6d78c043caba808e78c5790a24f171432fa2745c` |
| Starter contained docs, one healthcheck, and seven tests | ZIP inventory and successful baseline test run |
| Backup destination not selected | Owner decision, 2026-09-23; disposable tests only |
| No live stack sources available | Repository and starter file inventory |

Local script verification is recorded separately in
[verification.md](verification.md); it is not host inventory evidence.

## Host

| Item | Reported value | Still to verify |
| --- | --- | --- |
| Compute | Raspberry Pi 5, 16 GB | OS release, architecture, kernel |
| Boot disk | 1 TB Samsung 990 EVO | Current device mapping, filesystem and capacity |
| External data disk | 4 TB SSD | Mount point, mount-on-boot behavior and health |
| Cooling and power | Active cooler, PoE+ HAT | Temperature and undervoltage history |
| Container platform | Docker with Portainer | Versions, stack sources and access model |

## Services

| Service | Purpose | Evidence to add |
| --- | --- | --- |
| Portainer | Container administration | Deployment method and backup location |
| Jellyfin | Personal media library | Persistent configuration and media mounts |
| Sonarr / Radarr | Media organization | Configuration locations and shared path mapping |
| Prowlarr | Indexer management | Configuration location and integration notes |
| qBittorrent | Download client | Data location and completed-download mapping |
| FlareSolverr | Companion service for supported workflows | Dependencies and resource use |
| WireGuard | Remote access | Hosting device and intended access scope, without keys |

Record the current image version and tested date when each service is imported.
Use only content and services you are authorized to access.
