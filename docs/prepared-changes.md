# Prepared live follow-ups and rollback boundaries

Updated September 30 from the direct [live audit](live-audit-2026-09-30.md). The owner authorized reset preparation only. This agent executed no reset, production restart, new scheduler or new remote publication. A qBittorrent restart/profile change was observed with UNKNOWN origin; resolve current login availability before executing a reset. Keep the PR draft and unmerged.

## Prepared qBittorrent credential reset — approval required

Problem: the configured Radarr endpoint times out; separately, neither the stored
Radarr login nor latest temporary startup credential established a qBittorrent
session in the initial snapshot. The owner reported no working login. Binary
version is 5.1.4. A later independently observed restart/profile change added
nonempty credential fields; its origin/current login availability is unverified.
The newest private preimage is preserved and the reset remains unapplied.

Exact target: /mnt/storage/docker/qbit/qBittorrent/qBittorrent.conf, regular file,
owner/group 1000:1000, mode 0600. Only these Preferences keys change:

- WebUI\\Username becomes admin.
- WebUI\\Password_PBKDF2 becomes the generated private password's hash.

The private before/after files, strong random password and hash manifest are
prepared outside Git, in an owner-only approval directory with files 0600.
PBKDF2-HMAC-SHA512 uses 100,000 iterations, 16-byte salt and 64-byte result in
Qt ByteArray format, matching [qBittorrent 5.1.4 source](https://github.com/qbittorrent/qBittorrent/blob/release-5.1.4/src/base/utils/password.cpp).
No password/hash value appears in this repository or public report.

After explicit approval: recheck source hash/inode/UID/GID/mode and container
identity; stop only existing qbittorrent; compare its post-stop config with the
prepared preimage before writing. If stopping flushed settings, preserve that
version privately and rebuild/review the same two-field delta rather than
overwriting unrelated settings. Write the approved credential fields with
0600/1000:1000, then start the same container without recreate/pull. Verify
running state, restart counter semantics, sanitized logs, WebUI response and an
accepted API session with matching Origin/Referer. Inspect preferences/queue
read-only using that session. Failed login verification triggers rollback.

Expected impact: brief pause of transfers/seeding and interruption of WebUI
sessions. Consumers need the new credentials in a later approved update. The
unreachable Radarr endpoint and download paths are not changed by this reset.

Rollback: stop only qbittorrent; restore the saved exact pre-change config with
0600/1000:1000; start the same container. Prior lack of login may return. Preserve
both pre-stop and post-stop originals if qBittorrent flushed state. No data/profile
deletion, authentication bypass or protection disable is proposed.

## Prepared publication — approval required

Publish only the reviewed Pi delivery commit to the existing PR branch after
fresh fetch and safe integration of any newer MSI commit. Update the saved PR
description to reflect current evidence, preserving draft/open/unmerged state.
Impact: sanitized evidence/tooling becomes public. Rollback uses a normal follow-up
revert commit and prior description; no force push or PR merge. Exact commit and
description are recorded in the owner-facing delivery package.

## Additional narrow permissions — separate approval required

Sonarr and Prowlarr config.xml are 0644, app-owned 1000:1000, and hold API keys.
The twelve explicitly inventoried arr scheduled ZIPs are 0644 and may hold
secrets. Proposed scope: only those two config leaves and those twelve existing
archive leaves to 0600 after rechecking non-symlink ownership and app access;
save affected bytes/metadata privately first. No directories, databases or
recursive mode changes. Expected impact: local non-owner readers lose access;
apps retain owner access. Verify unchanged bytes/inodes, owner app read/write
where required, native-backup reading and no restart. Rollback only each saved
leaf to its original 0644. Future native backup modes need a separate supported
setting review; chmod of current archives does not ensure future privacy.

## Private daily reporting — installation/activation requires approval

The adapted temporary units passed systemd verification; manual collection
passed with health exit 1 and private files. Proposed time: 08:00
America/Los_Angeles, up to five minutes randomized delay, Persistent true.
Keep-all report history; no alert channel or deletion policy is configured.
Review the time/history policy before activation.

The concrete installation procedure uses the existing checkout and private
health config, replacing template paths before copying:

    install -d -m 700 "$HOME/.config/homelab" "$HOME/.local/state/homelab/reports"
    install -d -m 700 "$HOME/.config/systemd/user"
    install -m 600 APPROVED_PRIVATE_CONFIG "$HOME/.config/homelab/healthcheck.json"
    install -m 600 ADAPTED_SERVICE "$HOME/.config/systemd/user/homelab-report.service"
    install -m 600 ADAPTED_TIMER "$HOME/.config/systemd/user/homelab-report.timer"
    systemd-analyze --user verify "$HOME/.config/systemd/user/homelab-report.service" "$HOME/.config/systemd/user/homelab-report.timer"
    systemctl --user daemon-reload
    systemctl --user start homelab-report.service
    systemctl --user enable --now homelab-report.timer

No command above has been applied. Recheck absence of existing files before
installation; preserve any existing content instead of overwriting. Verify the
expected report modes, nonzero health status, timer next time and log volume.
systemd will mark health exit 1 as a non-success service result; the report still
exists. Rollback: disable/stop only the new timer, remove only newly installed
unit files after approval and daemon-reload; preserve private reports/config.
User service-manager lifetime at logout/boot is UNKNOWN; no linger change is
included. Continuous boot reporting would need that policy resolved separately.

## Completed prior permission change

The identified Radarr and qBittorrent configuration files changed `0644` to `0600` after actual application UID/GID `1000:1000` and access verification. Content, read/write access and restarts stayed unchanged. This supersedes unapplied Candidate A. Its exact-file rollback was restoring `0644`; use only after demonstrated need and live authorization. The archive/parent readers require separate review; no recursive operation.

## Withdrawn download-bind candidate

The former torrents-to-downloads edit used the initial candidate source. Runtime labels identify a different source and both apps already share downloads with a matching mapping. **Do not apply that edit or recreate Radarr from the sanitized candidate.** Keep it as historical evidence.

## Radarr diagnosis reserved for Pi Codex

1. Confirm original deployment files/project/override order privately.
2. Retain enabled client host, port, protocol and sanitized Test error. Keep credentials out of arguments/public records.
3. Compare the exact configured path with the successful service-host DNS/HTTP observation; a different hostname alone does not prove an error.
4. Distinguish DNS, transport, HTTP, authentication and queue/history; inspect completed paths separately.
5. Prepare one supported setting change with a private saved prior value and symptom-specific verification before live approval. Revert only that value if verification fails.

The configured-host timeout is demonstrated and was rechecked after the observed restart. Initial credential probes established no session; current authentication/login availability is UNKNOWN after the profile changed. The reset above is prepared, conditional on confirming it is still needed and approval. An exact Radarr endpoint/credential/path edit awaits a valid session and active preference/queue evidence. Do not launch downloads or run potentially category-creating client Test without the appropriate approved scope.

| Area | Prerequisite | Verification / rollback |
| --- | --- | --- |
| Monitoring | Review existing containers, scrapes, timers/crontab/app jobs and private report config | Manual result before approved install; disable only new timer; preserve reports |
| Recovery | Independent destination, scope, consistency, retention and keys | New isolated instance with integrations disabled and startup/data checks; preserve live state |
| Exposure/TLS | Intended access policy and actual listeners/router rules | Authorized positive/negative tests; preserve exact prior rules privately |
| Updates | Current versions/digests and compatible recovery | Isolated version test and data-aware rollback |

Selective collection: [pi-evidence.md](pi-evidence.md). Denials remain UNKNOWN; do not alter groups/socket modes/privileges. GitHub changes preserve the existing branch and newer Pi commits, then fast-forward without force. Merge remains owner-only.
