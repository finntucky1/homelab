# Evidence-based findings — September 29, 2026

The Pi and candidate live Compose source were inspected read-only. No service,
package, permissions, network, mount or scheduler was changed. Credentials and
raw logs remain private. See [inventory](inventory.md) and
[prepared changes](prepared-changes.md).

| Priority / symptom or risk | Evidence | Likely cause / uncertainty | Correction and verification |
| --- | --- | --- | --- |
| P1 / Radarr queue/history retrieval warnings | Repeated DownloadMonitoringService warnings in bounded recent log tails | Client connectivity/authentication/configuration issue; cause unconfirmed | Test configured client privately; distinguish DNS, TCP, HTTP and authentication; verify queue/history after a targeted correction |
| P1 / download-path inconsistency | qBittorrent maps downloads to /downloads; Radarr maps distinct torrents to /downloads; samefile is false. qBittorrent saves under /downloads | Potential import/translation failure, separate from retrieval. Native backup remote-path prefix does not cover this default; backup settings can be stale | Confirm live completed paths and current mappings; candidate one-line Radarr bind edit prepared; verify both containers see the same authorized file and an import succeeds |
| P1 / readable secrets/configuration | Radarr config.xml contains API key and is 0644; native ZIP is unencrypted and 0644; qBittorrent configuration is 0644 | Local readers with parent traversal may access private state; effective application IDs unknown | Restrict individual reviewed files after access validation; preserve original modes for rollback; no recursive chmod |
| P1 / broad management port declaration | Host IP omitted on published ports; Portainer 9000 plus read/write Docker socket | Broad bind defaults; runtime and Internet exposure unknown | Confirm LAN/VPN access policy and bindings before a specific TLS/port patch; verify intended and prohibited access |
| P2 / world-writable directory | Radarr torrents directory is 0777 | Excess write access; required writers/ACLs unknown | Identify effective IDs and writers before a narrow mode/ACL proposal |
| P2 / moving image versions | All four declarations use latest | Re-creation can select another release; current digests/versions unknown | Record current digest/schema; review release and ARM64 manifest; pin only after isolated recovery |
| P2 / same-device backups | Native Radarr ZIP and live state share external SSD | Device loss destroys both | Select independent protected destination and prove application recovery before scheduling |
| Observation gap | Docker, systemd and vcgencmd access denied | Restricted session, not an established outage | Health report uses UNKNOWN; collect selective runtime evidence in an authorized owner shell |

Root was 3% used; external storage 30% used. No capacity incident was observed.
One 57.3°C sensor reading cannot establish long-term thermal health.
Torznab errors were also found in bounded tails; no indexer change is proposed
without checking the specific error privately.

## Security and maintenance context

Unspecified Docker port bindings default to all host addresses; gateway and
firewall evidence is still needed to determine Internet access. Docker before
28 has a documented adjacent-host caveat for loopback publishing; the observed
26.1.5 version is the client, and server version remains unknown. Review
[official port behavior](https://docs.docker.com/engine/network/port-publishing/)
before choosing a binding as an access control.

[Docker security guidance](https://docs.docker.com/engine/security/) explains
why daemon control is trusted. A read-only socket mount does not provide API
authorization; changing Portainer socket access requires management review.

The Pi is ARM64. LinuxServer documents ARM64 support for
[Radarr](https://docs.linuxserver.io/images/docker-radarr/) and
[qBittorrent](https://docs.linuxserver.io/images/docker-qbittorrent/).
No exact installed/candidate manifest was inspected. Check each exact candidate
manifest, including Portainer/Jellyfin, before proposing an image change.

Before updates: record current image digest, release/migration requirements,
application-consistent backup and tested rollback data. Test one service at a
time. A schema migration can require restoring compatible data as well as the
previous image. Never prune volumes or automatically downgrade a migrated
database. Per-container log rotation remains a runtime review item.
