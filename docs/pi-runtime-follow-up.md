# Pi runtime evidence incorporated on the MSI — September 30, 2026

Historical partial follow-up. The subsequent direct [live audit](live-audit-2026-09-30.md)
supersedes its current coverage gaps: all twelve containers, current sources,
three healthy scrapes, configured endpoint timeout and isolated Radarr startup
are now observed. The earlier evidence below retains its original scope.

Source: the Pi agent's approved runtime follow-up in [existing draft PR #1](https://github.com/finntucky1/homelab/pull/1), read September 30. The PR was last updated at `2026-09-30T07:02:18Z` when read. Individual follow-up observation timestamps were not supplied. These are **LIVE PI OBSERVATION** records supplied by that agent; the MSI did not repeat live commands or change the Pi. Initial restricted-session observations remain historical in their dated records.

| Evidence | Reported result | Scope / remaining uncertainty |
| --- | --- | --- |
| Docker runtime | Server `26.1.5+dfsg1`, `linux/arm64` | Point observation; uptime and image digests unknown |
| Four applications | Portainer, Jellyfin, qBittorrent and Radarr running; restart counts zero | Running is not end-to-end availability |
| Docker health | Jellyfin declared check passing; other three have no declared check | Missing health coverage remains UNKNOWN |
| Application identity | Actual Radarr and qBittorrent processes UID/GID `1000:1000` | Other readers, ACLs and future image behavior not established |
| Radarr-to-qBittorrent | Actual UID 1000 process resolves `qbittorrent` and receives HTTP 200 from `qbittorrent:8080` | One DNS/HTTP path; not authentication, LAN/VPN access or queue success |
| Enabled Radarr client | Configured host differs from tested hostname; health error remains | Root cause unproven; no setting edit justified yet |
| Compose provenance | Runtime creation labels identify a different source from initial candidate | Full current source/override order still needs sanitized review |
| Download binds | Same host download directory; qBittorrent `/data/downloads`, Radarr `/downloads`; current remote-path mapping matches | Earlier candidate bind correction withdrawn; successful import unverified |
| Monitoring | Existing Grafana, Prometheus, node-exporter and cAdvisor containers found | Scrape health, dashboards, alerts and access policy unverified |
| System services | No failed systemd units in bounded query | Complete schedulers/user managers/app jobs unverified |
| Approved prior change | Two config files changed `0644` to `0600` after identity/access verification | Content, application read/write access and restart counts unchanged |

The changed files were the previously identified Radarr `config.xml` and qBittorrent `qBittorrent.conf`. Native archive permissions and other parent directories were not reported changed. No client, bind, service, monitoring or schedule settings changed in that follow-up. Backups still share the live external SSD failure risk; application-level recovery remains untested.

## Evidence labels

- **LIVE PI OBSERVATION:** Pi-agent host/runtime evidence attributed to its source.
- **MSI LOCAL TEST:** command actually executed on Windows; environment, result and skips in [verification](verification.md).
- **MOCK/SYNTHETIC TEST:** generated files or simulated responses on either machine.
- **OWNER REPORT:** supplied information without independently retained observation.
- **UNKNOWN:** missing, inaccessible or incomplete evidence; never PASS.

## Work reserved for Pi Codex

Inspect the enabled client's exact private configuration/Test result and disconfirming evidence before proposing correction. Reconcile original Compose files, overrides, versions, binds and logs. Verify existing monitoring/schedulers before installing a collector. Test isolated application startup only with approved scope and independent storage. The MSI prepares code, fixtures, review and documentation; it does not remotely execute these tasks.
