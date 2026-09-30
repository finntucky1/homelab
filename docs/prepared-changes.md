# Prepared actions requiring approval

Prepared September 29, 2026; none applied. Use the **confirmed original
deployment source/project/override order** for mutations. Do not deploy the
sanitized review copy. The owner's request requires approval before live or
remote changes.

## Read-only runtime evidence

In an authorized owner shell, without changing groups/socket modes or using
root, capture these privately and redact source paths before sharing:

```sh
docker ps --format '{{.Names}} {{.Image}} {{.Status}}'
docker inspect --format '{{.Name}} restart={{.RestartCount}} status={{.State.Status}} health={{if .State.Health}}{{.State.Health.Status}}{{else}}undeclared{{end}} compose_source={{index .Config.Labels "com.docker.compose.project.config_files"}}' radarr qbittorrent portainer jellyfin
systemctl --failed --no-pager
systemctl list-timers --all --no-pager
crontab -l
```

Names are source candidates; substitute actual runtime names. Confirm Docker
context targets this Pi. Crontab entries can contain credentials; never publish
them unfiltered. No configuration changes or rollback required.

Then use installed container tools for DNS/HTTP evidence:

```sh
docker exec radarr sh -c 'getent hosts qbittorrent >/dev/null'
docker exec radarr curl --silent --output /dev/null --write-out '%{http_code}\n' --max-time 5 http://qbittorrent:8080/
```

curl availability inside Radarr is unknown. HTTP 401/403 proves HTTP
reachability, not valid authentication. Review Radarr's current client Test and
RemotePathMapping privately. Do not put credentials in shell arguments.

## Candidate A: individual configuration permissions

These two non-symlink files have observed UID/GID 1000:1000 and mode 0644,
matching declared PUID/PGID but not yet verified effective application identity:

```text
/mnt/storage/docker/radarr/config.xml
/mnt/storage/docker/qbit/qBittorrent/qBittorrent.conf
```

After identity and reader requirements are confirmed, proposed exact change:

```sh
chmod 600 /mnt/storage/docker/radarr/config.xml /mnt/storage/docker/qbit/qBittorrent/qBittorrent.conf
```

Verify modes with stat -c '%a %u %g'; confirm application configuration access
and the next supported save/backup. Do not mutate settings simply to test a
save without authorization. Rollback uses chmod 644 on these exact two files.

The selected native Radarr ZIP is also 0644, owner 1000:1000; review its exact
private filename and readers before chmod 600, with chmod 644 rollback.
Use an explicit file list, not a recursive command. A one-time archive chmod
does not control future application-created archives.

## Candidate B: align Radarr's download bind

Prerequisites: confirm runtime source, restore queue/history connectivity,
confirm actual completed paths begin /downloads, verify no required data exists
only through the old mapping, and review the current remote-path mapping.

Exact candidate one-line change in the original Radarr service:

```diff
- /mnt/storage/torrents:/downloads
+ /mnt/storage/downloads:/downloads
```

Save the original source privately; validate with the original Compose file
order using config --quiet. After approval, recreate Radarr alone with the
original project/file-order command plus up -d --no-deps radarr. Fill that
exact command from runtime provenance before execution approval; it is not
known yet.

Verify both services see the intended authorized completed file and Radarr
imports it while media persists. Do not launch a download for this test.
Rollback: restore the old one-line mapping and recreate Radarr alone with the
same original project/order. Do not move/delete host files.

## Later approval packages

- Monitoring: confirm timers/crontab/application jobs first; manually test the
  provided user-unit command/config; approve installing/enabling one scheduler.
  Rollback disables/stops that new timer and restores only its edited unit.
- Backups: choose independent destination, protected export inputs and policy.
  New config tooling keeps all development snapshots and does not copy running
  application databases. Isolated application startup still requires approval.
- Exposure/TLS and updates: runtime access, policy, exact versions and rollback
  data are missing; a specific implementation is not ready for approval.
- GitHub: review the local diff/patch, then approve updating the **existing**
  draft PR branch. No duplicate PR or merge is proposed. Remote publication
  remains pending under the owner's explicit operating rule.
