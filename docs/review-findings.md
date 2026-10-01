# Evidence-based findings — September 30, 2026

The MSI review reconciles initial September 29 findings with [newer Pi-agent runtime evidence](pi-runtime-follow-up.md). No live Pi action was executed on the MSI. Raw configuration/logs remain private.

| Priority / symptom | Current evidence | Uncertainty | Next verification |
| --- | --- | --- | --- |
| P1 / Radarr client health error | UID 1000 resolves service host and receives HTTP 200; enabled client uses different host | Configured-host path, authentication and cause unproven | Pi agent reviews private Test result and verifies original queue/history symptom after approved correction |
| Superseded / candidate bind mismatch | Runtime shares host downloads with matching current mapping | Candidate is different source; successful import untested | Withdraw bind edit; review actual source/completed path before mutation |
| Partly resolved / readable config | Two files changed to `0600`; actual identity/access verified; content/restarts unchanged | Native archive and parent readers/future modes unverified | Exact archive/parent review; no recursive chmod |
| P1 / same-device backups | Native archive and live state share SSD; bytes/DB checks passed | No independent copy or app startup proof | Owner chooses destination/scope; Pi agent performs approved isolated recovery |
| P1 / management exposure | Candidate publishes unconstrained host ports; Portainer writable Docker socket | Actual current binds/router policy unknown | Runtime listener/network review and intended LAN/VPN policy |
| P2 / candidate writable torrents path | Initial path was `0777` | Different runtime source; current usage/writers unknown | Identify actual paths/ACLs before narrow mode proposal |
| P2 / moving images | Historical candidate uses `latest` | Actual digests/release/schema unknown | Inventory current ARM64 versions; recover before updates |
| Partial / monitoring | Four existing monitoring containers found | Scrapes/dashboards/alerts unknown | Inspect existing config before deploying anything |
| Partial / access | Docker and bounded failed-unit query now succeeded | Complete jobs, firmware and access policy unverified | Missing coverage remains UNKNOWN |

Initial root/external usage 3%/30% showed no capacity incident; one 57.3°C reading does not establish sustained cooling. Torznab errors in bounded tails remain a separate unproven integration issue.

Private modes do not replace encryption, directory review or independent backup. Preserve original values privately and revert only a specific approved change when its verification fails. Docker health covers its own probe; zero restarts is a point counter, not uptime. Image rollback may need schema-compatible data. Log rotation remains a live review item. Earlier candidate findings remain in [dated progress history](progress-2026-09-29.md).

## Preserved security and maintenance context

Docker documents default publishing to all host addresses and an adjacent-host
loopback-publishing caveat before 28.0.0. The Pi agent observed server 26.1.5;
the effective Debian package's patch status was not checked. Confirm actual
listeners, package behavior and intended access before choosing port bindings
as an access control. See [official port behavior](https://docs.docker.com/engine/network/port-publishing/).

[Docker security guidance](https://docs.docker.com/engine/security/) treats
daemon control as trusted access. A read-only socket mount does not provide
API authorization; review Portainer administration before changing its access.

LinuxServer documents ARM64 images for [Radarr](https://docs.linuxserver.io/images/docker-radarr/)
and [qBittorrent](https://docs.linuxserver.io/images/docker-qbittorrent/). Exact
current and proposed manifests for every service still need verification.
Preserve consistent exports and version-compatible rollback data before updates;
never prune volumes or automatically downgrade a migrated database.
