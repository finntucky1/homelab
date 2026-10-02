# Operating and maintenance notes

Start with [dated inventory](inventory.md), [findings](review-findings.md) and
[the evidence collection guide](pi-evidence.md). Confirm the Docker context
targets this Pi before treating its response as live evidence.

```sh
python3 scripts/healthcheck.py --mount /mnt/storage
```

The mount check detects a missing filesystem instead of silently measuring a
leftover directory. It does not establish disk identity or boot persistence.
Defaults also collect service/resource/thermal evidence and mark unsupported
or unconfigured coverage UNKNOWN. Exit 1 requires review; exit 2 identifies
observed failure or invalid arguments. No check restarts or repairs anything.

Add exact expected runtime container names after observing them; source names
alone do not prove the deployment. Configure explicitly reviewed HTTP endpoints
privately. A process being up, Docker health and client reachability prove
different things. Follow [script usage](../scripts/README.md).

## Triage an unavailable service

1. Determine scope: one application, all containers, host or remote access.
2. Check capacity and required mount before investigating media paths.
3. Query selective status/restarts/health, then bounded recent logs privately.
4. Test DNS, connection, HTTP and application authentication separately.
5. For Radarr, verify both the configured download client and completed-path
   translation; runtime already shares downloads with a current mapping, while
   the enabled-client error remains unproven. Do not apply the old candidate bind edit.
6. Prepare one evidence-supported change, verification and rollback.
   Obtain live-change approval, apply once, then test the original symptom.

Do not publish logs containing credentials, media titles or endpoint details.
Denied access should stay unknown, not be diagnosed as service failure.

## Updates and recovery

Record current image/application versions and exact ARM64 manifest, read release
notes and schema migrations, export consistent application state, and test the
restore boundary before approval. Rollback can require restoring compatible
data, not only changing an image tag. No indiscriminate upgrades, automatic
repair loops, volume pruning or ownership changes.

Existing Radarr archive recovery proved file/DB integrity only. Preserve an
independent protected copy and verify application startup separately.
See [backup guidance](../backups/README.md).

## Private incident record

Record date/scope, symptom/impact, bounded evidence, hypothesis and a result that
would disprove it, approved change, rollback, verification and remaining gaps.
Leave outcomes blank until observed. The current integration warnings have a
diagnostic finding, not a completed repair or measured recovery time.
