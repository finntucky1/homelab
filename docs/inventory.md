# Dated host and service inventory

## Current runtime addendum — incorporated September 30

The [Pi-agent follow-up](pi-runtime-follow-up.md) supersedes initial runtime access gaps below: Docker server and four running applications observed, Jellyfin healthy, actual UID/GID verified, shared download storage/current mapping confirmed, monitoring containers found, and no failed units in a bounded query. The original candidate is a different Compose source. Full current sources/versions, scrapes/alerts, network policy and complete schedulers remain unknown.

## Historical initial restricted-session baseline

Observed **2026-09-29, America/Los_Angeles**, from a restricted local session
on the actual Pi. No SSH/router session was used. Serials, private addresses,
usernames, credentials and raw logs are excluded. Momentary observations do
not establish sustained availability or hardware health.

| Evidence category | Item | Result / limitation |
| --- | --- | --- |
| Machine-observed | Device model, architecture, kernel | Raspberry Pi 5 Model B Rev 1.1; aarch64; Linux 6.18.39+rpt-rpi-2712 |
| Machine-observed | OS release | Debian GNU/Linux 13 (trixie); Debian version 13.6 |
| Machine-observed | Memory | 15 GiB displayed; about 9.8 GiB available; 2 GiB swap unused at baseline |
| Machine-observed | Root device | Samsung SSD 990 EVO **Plus** 1TB, NVMe, 931.5 GiB; ext4 root 3% used, about 860 GiB available |
| Machine-observed | External device | CT4000X10SSD9, USB solid-state device, 3.6 TiB; ext4 at /mnt/storage, 30% used, about 2.5 TiB available |
| Machine-observed | Mounts | Root and external storage mounted; fstab declares storage as ext4 with defaults. Boot and missing-disk behavior untested |
| Machine-observed | Thermal sensor | 57.3°C in one sysfs observation; sustained cooling unknown |
| Machine-observed | Tools | Python 3.13.5; Git 2.47.3; Docker client 26.1.5+dfsg1; Compose 2.26.1-4 |
| Machine-observed | Other tools | bash, systemctl, lsblk, findmnt, free, vcgencmd, curl, ss, crontab available. rg, gh, jq, shellcheck absent; no installs performed |
| Unknown | Docker runtime | Socket denied: server version, running containers, image digests, restart counts, health, effective mounts and log rotation |
| Unknown | System services/jobs | systemd bus and user crontab denied: running/failed services and active timers |
| Unknown | Throttling | vcgencmd device denied: current/historical throttling and undervoltage |
| Unknown | Network | Restricted session cannot establish actual host listeners, DNS/routes or container reachability; gateway/VPN access absent |
| Owner-reported | Infrastructure | Active cooler, PoE+ HAT, UniFi gateway/switch, WireGuard; unverified physical/admin details |

## Candidate Compose and data

One current Compose file and its .bak sibling were found in the private
server directory. The current file passed single-file Compose quiet validation.
Runtime source labels are inaccessible, so this is a **candidate authoritative
source**, not proven to describe every running container. See the
[sanitized review copy](../docker-compose/observed.compose.yaml).

| Declared service | Image | Declared host ports | Persistent paths below /mnt/storage |
| --- | --- | --- | --- |
| Portainer | portainer/portainer-ce:latest | 9000/tcp | docker/portainer → /data; read/write Docker socket |
| Jellyfin | jellyfin/jellyfin:latest | 8096/tcp | docker/jellyfin → /config; media → /media |
| qBittorrent | lscr.io/linuxserver/qbittorrent:latest | 8080/tcp, 6881/tcp+udp | docker/qbit → /config; downloads → /downloads |
| Radarr | lscr.io/linuxserver/radarr:latest | 7878/tcp | docker/radarr → /config; media → /media; torrents → /downloads |

All four declare unless-stopped and no explicit Compose healthcheck, privileged
flag, extra capabilities or dependencies. Image-provided healthchecks and
runtime privileges remain unknown. Radarr/qBittorrent declare PUID/PGID 1000;
effective application identity is unverified. Sonarr, Prowlarr and FlareSolverr
are owner-reported and absent from this candidate source, not proven absent
from the daemon.

## Backups and jobs

Radarr's native scheduled-backup directory contains four files. The latest
ZIP's filesystem modification time is **September 28, 20:25 PDT**. An isolated
restore of all three members passed CRC, byte comparisons and SQLite integrity.
See [restore evidence](../backups/restore-test.md). Application startup remains
untested. Live state and its native backups share the external SSD failure risk.

No matching backup/health unit names were found in the inspected system/user
unit directories, or matching entries in /etc/crontab. Timer queries and user
crontab were denied. Other users, application schedules and custom jobs remain
unknown. Limited searches cannot establish scheduler absence.

## Reproduce safely

Read /proc/device-tree/model and /etc/os-release; run uname -srmo,
lsblk -dn -o NAME,MODEL,TRAN,SIZE,ROTA, df -h and free -h.
Follow [pi-evidence.md](pi-evidence.md) for selective private collection.
Never publish environment dumps, database records or unfiltered logs.
Access denial is an observation gap, not a service failure.
