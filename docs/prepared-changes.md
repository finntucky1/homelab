# Prepared live follow-ups and rollback boundaries

Updated September 30 from [Pi-agent follow-up](pi-runtime-follow-up.md). Live execution belongs to Pi Codex. The MSI prepares/tests changes in the existing draft PR; no merge, live deployment or scheduler activation is authorized here.

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

No exact client edit is ready: configured-host failure and authentication evidence are missing. Do not launch downloads/restart services to collect evidence.

| Area | Prerequisite | Verification / rollback |
| --- | --- | --- |
| Monitoring | Review existing containers, scrapes, timers/crontab/app jobs and private report config | Manual result before approved install; disable only new timer; preserve reports |
| Recovery | Independent destination, scope, consistency, retention and keys | New isolated instance with integrations disabled and startup/data checks; preserve live state |
| Exposure/TLS | Intended access policy and actual listeners/router rules | Authorized positive/negative tests; preserve exact prior rules privately |
| Updates | Current versions/digests and compatible recovery | Isolated version test and data-aware rollback |

Selective collection: [pi-evidence.md](pi-evidence.md). Denials remain UNKNOWN; do not alter groups/socket modes/privileges. GitHub changes preserve the existing branch and newer Pi commits, then fast-forward without force. Merge remains owner-only.
