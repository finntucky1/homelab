# Live Pi audit — September 30, 2026

Direct observations on the live Raspberry Pi, owner timezone America/Los_Angeles.
Some evidence timestamps are October 1 UTC, which is still September 30 locally.
This audit supersedes the partial [runtime follow-up](pi-runtime-follow-up.md).
The initial restricted baseline remains historical. Machine-readable selected
evidence is in [pi-2026-09-30.json](evidence/pi-2026-09-30.json).

OBSERVED means measured here; REPORTED means supplied by the owner; INFERRED
means an explanation consistent with observations; UNKNOWN means not established.
All availability and capacity observations are point measurements.

## LIVE BASELINE

| Item | OBSERVED result |
| --- | --- |
| Hardware | Raspberry Pi 5 Model B Rev 1.1; four Cortex-A76 CPUs; aarch64 |
| OS / kernel | Debian 13.6 trixie; Linux 6.18.39+rpt-rpi-2712 |
| RAM / swap | 16,603,520 KiB total; about 10,390,272 KiB available; 2 GiB swap unused |
| Uptime | About 27 days, 20 hours at baseline; not a service availability measurement |
| Development | Python 3.13.5, Git 2.47.3 |
| Docker / Compose | Client and local server 26.1.5+dfsg1, linux/ARM64; Compose 2.26.1-4 |
| Thermal / firmware | 57.85 C baseline; current and since-boot throttling flags 0x0 |
| System services | Docker, SSH and NetworkManager active; zero failed system units |
| Jobs | Nine standard system timers; zero user timers; no user crontab; other users/root jobs incompletely audited |
| Networking | eth0, wlan0, loopback and Docker bridges observed; default route and listeners present; addresses withheld |

Active cooling, PoE+ HAT, UniFi equipment and WireGuard remain REPORTED physical
or external infrastructure. The local WireGuard tool and /etc/wireguard directory
were absent; this does not establish where the reported VPN runs. nftables and
iptables administrative inspection was denied. Firewall, router forwards, VLAN
policy, public reachability and effective SSH password/root-login policy are UNKNOWN.

## COMPLETED

- Inventoried all 12 local containers, image IDs/architecture, exact mounts,
  ports, networks, process identities, restart counts and creation labels.
- Located and read both actual Compose sources; compared current image, mount
  and restart declarations with 11 labeled containers. Created two sanitized
  review copies and validated syntax without starting containers.
- Separated Radarr transport failure, qBittorrent authentication, and path
  compatibility evidence. Prepared an exact private credential reset and rollback.
- Verified all 12 native backup ZIPs by CRC and recorded SHA-256 hashes.
- Restored the newest Radarr ZIP into temporary NVMe storage and started an
  isolated matching-image application with no production bind or network.
- Verified Prometheus scrapes and metric coverage, live readable/JSON health,
  manual private reporting, permissions, deduplication and unit/timer syntax.
- Added a tested, read-only physical-destination preflight. It refuses missing
  mounts, shared disks, unreviewed filesystems and read-only destinations.
- Integrated MSI commit 59dfd0a by fast-forward on a separate Pi branch and
  tested the combined source. This agent performed no production restart, reset,
  update, network edit or scheduler activation. A later qBittorrent restart/file
  change was observed independently of this agent's prepared reset; origin UNKNOWN.

Radarr's previously approved mode remains 0600. qBittorrent's later changed
profile was 0644; this agent reapplied the earlier exact 0600 authorization after
verifying the current app UID/GID 1000:1000 and read/write access. Bytes/inode
were unchanged by chmod, and app access still passed. This is the sole production
change by this agent in the audit continuation. The approved 0644 rollback is
narrowly scoped to those exact leaves.

## RADARR/QBITTORRENT STATUS

| Layer | OBSERVED evidence | Conclusion / boundary |
| --- | --- | --- |
| Process | Both running; restart counts zero; real app identities 1000:1000 | Current processes exist; this does not validate integrations |
| Docker DNS | Radarr app identity resolves qbittorrent | Service discovery works on the shared bridge |
| TCP / HTTP | Service WebUI HTTP 200; unauthenticated API HTTP 403 | qBittorrent is reachable and its API has an authentication guard |
| Configured client path | Enabled Radarr client points to a private endpoint that differs from service DNS/current container/current host; port 8080, HTTP, empty URL base; bounded request times out with curl 28 / HTTP 000 | The configured endpoint is unreachable from Radarr in this test; the failing transport path is demonstrated |
| Authentication, initial snapshot | Stored Radarr credentials and then-latest startup temporary credential each produced HTTP 200 without accepted login/SID, with correct matching Origin/Referer | Neither tested credential established a session. Current login availability is UNKNOWN after later changed credentials; HTTP 200 alone does not mean login succeeded |
| Radarr health | Download-client communication error; independent indexer errors/warnings | Radarr integration remains unhealthy |
| Paths | One host directory /mnt/storage/torrents is mounted as /data/downloads in qBittorrent and /downloads in Radarr/Sonarr; existing remote mapping /data/downloads/ to /downloads/ matches that relationship | No evidence supports the withdrawn candidate bind edit |
| Saved qBittorrent paths | On-disk preferences say /downloads/ and /downloads/incomplete/; /downloads is absent in the live qBittorrent container; /data/downloads is writable by app UID | A saved-path mismatch is observed. Active preferences and torrent-specific paths require a valid API session before a supported edit |

qBittorrent binary reports 5.1.4. The initial diagnosis profile had no saved WebUI
username or PBKDF2 password; startup logs identified admin/temporary-password
generation. The owner reported no working login and requested reset preparation.
Later runtime evidence shows a new container start at 2026-10-01T00:57:57Z and a
changed profile with nonempty credential fields. This agent did not execute the
reset or restart. Origin and current owner login availability need clarification;
the prior authentication attempts describe the initial snapshot, not these later
credentials. The newest profile is preserved privately, and the prepared reset
still changes only two fields, subject to fresh approval/preimage verification.
Four bounded login attempts were made in total; the final two used the documented
headers. No further guesses, credentials printed, category writes or downloads
were performed. API-masked passwords were not mistaken for actual stored values.
The version probe's upstream implementation initializes settings before printing;
an isolated same-image --version reproduction with a private copied profile did
not change that copy or its 0600 mode. The live file change is not attributed to
the version probe. Avoid production-profile CLI probes that initialize settings;
use isolated metadata/version checks instead. See [qBittorrent main source](https://github.com/qbittorrent/qBittorrent/blob/release-5.1.4/src/app/main.cpp)
and [application initialization](https://github.com/qbittorrent/qBittorrent/blob/release-5.1.4/src/app/application.cpp).

The demonstrated failure is the configured transport path. A routing/firewall/
stale-endpoint cause beyond that remains UNKNOWN. Authentication was an independent
blocker in the initial snapshot and is currently unverified. A client host change, credential update or
download-path correction remains a separate live change after accepted login and
active preference/queue checks. A Radarr client Test can create a missing category,
so it was not treated as a purely read-only diagnostic. See the official
[qBittorrent API](https://github.com/qbittorrent/qBittorrent/wiki/WebUI-API-(qBittorrent-5.0))
and [Radarr client Test implementation](https://github.com/Radarr/Radarr/blob/develop/src/NzbDrone.Core/Download/Clients/QBittorrent/QBittorrent.cs).

Sonarr currently has no configured download client. Sonarr/Prowlarr indexer
health errors remain separate integration work; they do not establish disk failure.

## COMPOSE STATUS

Creation labels identify project compose and directory
/mnt/storage/omnieye/compose. Both named files are present, readable and valid
when rendered individually:

- docker-compose.clean-draft.yml: seven app containers (FlareSolverr, Jellyfin,
  Portainer, Prowlarr, qBittorrent, Radarr, Sonarr).
- docker-compose.yml: four monitoring containers; the current file also declares
  the apps. Its full eleven-service review copy is preserved for comparison.
- npm has no Compose creation labels and uses the default bridge. Its original
  deployment command/source remains UNKNOWN.

The eleven labeled containers match their identified current source's image
reference, bind declarations and restart policy. Creation labels are provenance
evidence, not proof that an unchanged file could reproduce today's entire stack.
The original invocation/override order is not retained. Runtime image IDs are
recorded separately because latest tags can move.

[live-apps.review.compose.json](../docker-compose/live-apps.review.compose.json)
and [live-stack.review.compose.json](../docker-compose/live-stack.review.compose.json)
replace host roots/private environment values with placeholders. They preserve
selected networks, ports, mounts, privileges and actual nonempty commands. They
are review artifacts, not deployment instructions. The four-service
[historical candidate](../docker-compose/observed.compose.yaml) points to different
qBittorrent and Jellyfin paths and must not be used to recreate these containers.
No new dependencies were invented; no Compose up was run.

## STORAGE STATUS

| Disk / filesystem | Mounted use | Point capacity |
| --- | --- | --- |
| Samsung SSD 990 EVO Plus 1TB, /dev/nvme0n1p2 ext4 | Root /, Docker daemon data; npm data/TLS directories under private owner home | 3% used; about 859 GiB available |
| CT4000X10SSD9 4TB USB, /dev/sda1 ext4 | Actual /mnt/storage mount; apps, media, downloads and monitoring state | 30% used; about 2.46 TiB available |

Jellyfin config at /srv/omnieye/config/jellyfin resolves through findmnt to the
external SSD, despite its different path spelling. Its cache is also external.
Radarr/Sonarr/qBittorrent media and download binds use the external SSD. Config
roots for arr/qBittorrent/Portainer/Grafana/Prometheus are below /mnt/storage/docker.
The download directory is 0777 and UID/GID 1000:1000; root/media/config directory
modes vary and are recorded in selected evidence. No broad chmod or data move
was performed. No capacity incident was demonstrated. Duplicate libraries and
media content integrity were not exhaustively audited.

## BACKUP STATUS

| Question | Result |
| --- | --- |
| Same-device backup? | YES: four native ZIPs each for Radarr, Sonarr and Prowlarr reside on their production external SSD |
| Independent backup? | No complete independent production backup established. A private four-file config snapshot on NVMe is physically separate from those external-SSD configs only; it is partial and on the same host |
| File restore validated? | YES: three newest Radarr archive members, CRC and byte hashes matched |
| Database restore validated? | YES: SQLite integrity ok, 42 tables |
| Isolated application startup validated? | YES: same live image ID, Radarr 6.1.1.10360, restored API key accepted and movie count matched |
| Service recovery validated? | NO: integrations, imports, clients and network intentionally disabled |
| Full DR validated? | NO: no whole-host/disk-loss recovery, recovery keys or measured RPO/RTO |

The native API backup policy is seven-day interval / 28-day retention for all
three arr apps. Four archives per service were present, dated September 7–28.
All twelve CRC checks passed. Latest sizes: Radarr 3,701,463 bytes; Sonarr 693,768;
Prowlarr 22,324. Latest Radarr archive timestamp is September 28, 20:25:46 PDT;
packaging a copy now would not make that application data fresh. Archive modes
are 0644 and may expose embedded secrets to local readers.

The startup test copied the newest Radarr archive to temporary NVMe storage,
verified SHA-256 64707f5196a258906cf24c2b57b1b1f7579d3ca886d1c1aa12b0a4ee30b4f157,
validated extraction, then used the exact live image ID. The temporary container
had network none, no published ports, one isolated config bind, user 1000:1000,
read-only root, dropped capabilities and no-new-privileges. Startup/data read
passed in 4.93 seconds. It was stopped/removed and temporary files removed;
production PIDs/state/restarts and source archive remained unchanged. Docker
reports no kernel memory/swap limit support: a claimed enforced 512 MiB limit
would be false. The test used a 45-second startup deadline and ample observed RAM.
A temporary logging-option failure was corrected only in the isolated instance.

Bounded searches found no backup candidates for qBittorrent, Jellyfin, Portainer,
Grafana or Prometheus. npm roots were inaccessible for complete backup searching.
No remote accounts were searched. Other custom scripts, Linux config and stack
backup coverage remain UNKNOWN beyond the private pre-change static snapshot.
Prometheus's 30-day retention is metric retention, not a backup.

Critical state includes application DBs, supported exports, Compose definitions,
Linux/mount configuration, Grafana dashboards/datasources, Portainer state and
qBittorrent torrent/resume data. Config API keys, passwords, TLS/VPN keys are
secrets requiring private storage and a key-recovery plan. Media/downloads need
an explicit scope decision; cache/logs/metrics are generally regeneratable only
if the owner accepts their loss. A config file alone is not full app recovery.

The new [destination preflight](../scripts/backup_destination.py) performs no
writes and fails closed. A private NVMe directory passes for selected external
Radarr data, but fails when /etc/fstab on that NVMe is included. An all-host
destination must avoid both production disks; for host-loss recovery choose
off-host storage with a reviewed access/key plan. No purchase is prescribed.
[Backup usage](../backups/README.md) covers manifests, hashes, keep-all development
retention, failure exits and isolated restore. Production scope, consistency,
retention, encryption, destination and notifications still need agreement.

## MONITORING STATUS

All four monitoring containers run with zero restarts. Prometheus readiness
HTTP 200; targets prometheus, node-exporter and cadvisor were up without scrape
errors; PromQL up returned 1 for all three. cAdvisor memory series count was 87;
node-exporter reported one filesystem-available series for /mnt/storage. A bounded
cAdvisor response did not contain every family, so absence in that sample was
not treated as absent collection. Grafana health HTTP 200, database ok,
version 13.0.1+security-01. Dashboards, datasource permissions, alerts and delivery
remain UNKNOWN. Do not deploy a duplicate monitoring stack.

Manual private reporting succeeded with health exit 1, mode-0600 files and
mode-0700 directories. Captured-report replay deduplicated an identical semantic
report after changing only its timestamp; distinct measured reports are retained.
History uses keep-all; automatic rotation is not configured. Adapted service and
timer syntax passed verification; calendar accepts 08:00 America/Los_Angeles.
No persistent report/config directory, homelab user unit or schedule was installed.
Installation commands and rollback are in [prepared changes](prepared-changes.md).

## SECURITY STATUS

| Priority | OBSERVED issue / uncertainty | Action boundary |
| --- | --- | --- |
| IMMEDIATE | Radarr 0600 valid; qBittorrent 0600 reapplied after later 0644 profile replacement; Sonarr/Prowlarr config.xml and twelve native archives 0644 contain or may contain secrets | Exact qBittorrent mode/access reverified; additional mode changes require approval; no recursion |
| IMMEDIATE | Management ports published on all IPv4/IPv6 host interfaces; firewall/router reachability UNKNOWN | Review intended LAN/VPN policy and authorized positive/negative tests before any binding or firewall edit |
| WORTHWHILE | Portainer writable Docker socket; cAdvisor privileged with broad host binds; several apps run as root | Trusted administration and application-specific privilege review; no speculative privilege changes |
| WORTHWHILE | Docker 26.1.5; cached apt index lists 196 upgrades; moving latest image tags | No index refresh, update, image pull or reboot; stage version-compatible recovery before upgrade approval |
| WORTHWHILE | JSON-file log driver with no per-container rotation options; daemon JSON config absent | Effective daemon command defaults not audited, so actual rotation remains UNKNOWN |
| INFORMATIONAL | Socket 0660 root:docker-group; owner has docker/sudo roles; SSH effective login policy unverified | No sudo, group/socket edits or access-control bypass; daemon control is privileged trust |
| INFORMATIONAL | No .env file found in the three inspected top-level deployment directories | Does not exclude inline secrets, alternate env files or environment inherited at deployment |

Directives UsePAM yes / KbdInteractiveAuthentication no were observed in SSH
configuration. They do not prove effective password or root-login policy.
No indiscriminate hardening was applied. Only the previously authorized exact
qBittorrent mode was reapplied after its profile changed.

## TEST RESULTS

Environment: actual Pi ARM64, Debian 13.6, Python 3.13.5, local Docker daemon.
Tests use generated/mocked inputs unless the row explicitly says live.

| Command / operation | Pass | Fail | Skip | Exit / scope |
| --- | ---: | ---: | ---: | --- |
| python3 -m unittest discover -s tests -v | 126 | 0 | 0 | 0; combined MSI 110 plus 16 destination tests |
| python3 scripts/backup_lab.py --json | 1 exercise | 0 | 0 | 0; synthetic SQLite, corruption refusal, retention and cleanup |
| python3 scripts/healthcheck.py --config PRIVATE_CONFIG | 34 observations | 0 | 0 | 1; live; 12 UNKNOWN |
| Same health command with --json | 34 observations | 0 | 0 | 1; live; 12 UNKNOWN |
| python3 scripts/report_snapshot.py --output-dir PRIVATE_DIR -- --config PRIVATE_CONFIG | 1 collection | 0 | 0 | 1; private live report preserved health severity |
| Destination preflight, NVMe vs Radarr on external SSD | 1 | 0 | 0 | 0; read-only separation for this scope |
| Same preflight including NVMe /etc/fstab production source | 1 expected refusal | 0 | 0 | 2; shared physical disk detected |
| ZIP CRC / SHA-256 inventory | 12 archives | 0 | 0 | 0; read-only, all three arr apps |
| Isolated Radarr file / DB / startup / data read | 1 recovery | 0 | 0 | 0 final runner; production unchanged, no full DR |
| docker compose -f REVIEW_FILE config --quiet | 2 files | 0 | 0 | 0 each; synthetic placeholders, syntax only |
| systemd-analyze --user verify ADAPTED_SERVICE ADAPTED_TIMER | 1 | 0 | 0 | 0; temporary adapted files, no activation |
| systemd-analyze calendar '*-*-* 08:00:00 America/Los_Angeles' | 1 | 0 | 0 | 0; parser only |
| healthcheck.py / backup_destination.py --help | 2 | 0 | 0 | 0 each; current CLI imports |

Live health UNKNOWN: ten running containers lack declared Docker health checks,
memory PSI is unavailable, and backup evidence is unconfigured. Twelve explicit
HTTP probes passed; host GitHub hostname resolution and restart counters passed.
Host resolution is distinct from the separately measured Docker service DNS.
No backup proof marker was fabricated to produce green health.

The first wrapper attempt refused a missing private output directory (exit 3);
an explicit mode-0700 scratch directory resolved that prerequisite. Initial
isolated-container logging attempts failed before the final successful test;
all temporary instances were removed. These are not reported as successful attempts.
Python 3.8 grammar review is syntax compatibility only, not a 3.8 runtime test.
Final link, privacy and whitespace review is recorded in the local delivery receipt.

## GIT STATUS

Separate local branch codex/pi-live-audit-2026-09-30 starts from published d70f666
and fast-forward integrated MSI 59dfd0ae1a12e382e3ff58ce4985d597f9c6af63.
Remote origin is https://github.com/finntucky1/homelab.git. At preparation the
existing PR branch had that MSI head; PR #1 was open, draft and unmerged.
This dated source document describes preparation; the owner-facing delivery
receipt records the subsequent local commit and whether publication was approved.
No force push or merge is authorized. New publication requires a fresh fetch
and normal ancestry-preserving update to the existing branch after owner approval.

## CHANGES REQUIRING OWNER APPROVAL

[Prepared changes](prepared-changes.md) specifies exact reset fields, stop/start
scope, verification and private saved-file rollback. The owner authorized
preparation, not execution. The reset does not itself fix the unreachable Radarr
endpoint or saved download paths. Public commit publication, additional config
permissions, production backup scheduling, reporting activation, updates and
network changes retain their own approval boundaries. No exact firewall/update
change is ready from the current UNKNOWN policy information.

## INFORMATION FOR MSI CODEX

Use this audit and selected JSON as current runtime truth. Preserve historical
records but remove current claims that there are only four apps, sources/scrapes
are unknown, startup was not tested or config permissions remain unapplied.
Keep the old four-service Compose copy historical and its bind edit withdrawn.
Current transport timeout and initially rejected credentials are separate findings;
current login availability is UNKNOWN after the later profile change. Do not
publish a speculative endpoint/path fix. Fresh Pi total is 126 tests, independent
of the earlier 86 Pi or 110 MSI counts. New files are the two live Compose review
copies, destination tool/tests, this audit and selected evidence; associated
runbooks now point here. Fetch before integrating the Pi delivery commit.

Study explanations the owner can reproduce and explain:

- Linux: a directory can survive loss of its disk mount. findmnt shows the
  containing filesystem and source, while lsblk ancestry connects partitions to
  physical disks. That is why missing-mount fallback and same-disk snapshots fail
  backup readiness even when a directory exists and has ample space.
- Processes/permissions: a container's root supervisor can launch UID 1000 app
  workers. Measure the worker, not only Config.User or PUID. Mode 0600 grants
  owner read/write; process access tests verified the approved exact files.
- Docker: bridge DNS made qbittorrent resolvable within the project. Different
  container paths can share one host bind; the remote mapping translates the
  reported path. A stopped/restarting state, lifetime counter and health probe
  answer different questions. Creation labels help locate source files but do
  not prove that a current file is identical to the original deployment.
- Networking: DNS maps a name; TCP reaches a listener; HTTP proves protocol
  response; authentication needs an accepted session. HTTP 403 can establish
  reachability and HTTP 200 can still reject a login. Test the configured route
  and successful alternative separately before proposing a change.
- Recovery: CRC/hash equality checks bytes; SQLite integrity checks DB structure;
  application startup/data read checks software compatibility. Disabling network
  and production binds makes that test safe but leaves service recovery open.
  Weekly exports imply a potential data-loss interval, not an agreed RPO. Startup
  in 4.93 seconds is not whole-service RTO. Same-host separate disks still share
  host, power and compromise failure risks.
- systemd/reporting: a oneshot service defines a command; a timer triggers it.
  Syntax verification does not enable a job. Exit 1 preserves UNKNOWN evidence;
  private semantic dedup avoids repeated equivalent reports without hiding a
  changed status. Keep-all history needs a later approved capacity/retention policy.

These are agent observations and explanations. Owner reproduction, independent
operation and interview mastery have not been claimed.

## OWNER ACTIONS

1. Clarify the observed qBittorrent restart/profile change and whether a working
   login now exists, without sharing credentials. If a reset is still needed,
   approve only the two credential fields and existing-container stop/start after
   fresh preimage verification. An accepted login unblocks active-path and Radarr
   client verification; the reset would briefly interrupt transfers.
2. Approve publication of the reviewed Pi commit to existing draft PR #1 after
   fresh fetch/integration. Smallest step: approve the exact delivery commit;
   keep the PR draft and unmerged so MSI can use the current sanitized evidence.
3. Select recovery scope and a destination outside the selected production disks,
   with retention, encryption/key recovery and loss/time objectives. Smallest step:
   name an existing disk/NAS/remote destination and whether media is included;
   run the no-write preflight before any approved production job.
