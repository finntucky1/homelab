# Prioritized improvement backlog

Current local continuation, 2026-09-29: actual Pi/storage and a four-service
Compose candidate inspected; existing Radarr archive restored privately and
SQLite integrity verified; application startup/runtime access still open.
Checker and private config/export/report tooling extended with isolated tests.
See [progress](progress-2026-09-29.md). No remote/live changes were applied.
The historical backlog below is retained; its unchecked items are acceptance
gates rather than claims that no partial evidence now exists.

Earlier delivery update, 2026-09-29: authenticated implementation-branch
creation succeeded. Continue the reviewed package in a draft PR; the
live-system backlog below remains open. Search for existing issues before
publishing any issue drafts.

Historical access check, 2026-09-27: GitHub's all-state issues collection returned no existing
issues or PRs; remote main remains unchanged and no remote implementation branch exists.
Creating the inventory issue returned HTTP 403, "Resource not accessible by
integration." No issue was published. Recheck for duplicates before publishing
these drafts. Delivery includes individual issue bodies for manual or CLI use.

Completed locally: starter integration, AGENTS conventions, improved read-only
healthcheck, disposable backup/restore rehearsal, collection/review guides,
learning exercises, and truthful portfolio notes. See
[verification.md](verification.md). These do not complete the live-system
acceptance criteria below.

## P0 / 1. Verify host inventory and import sanitized Docker Compose definitions

The dated inventory now contains verified OS/storage facts and a sanitized
Compose candidate. Runtime provenance and remaining deployment evidence are
still needed before reproducing the running setup.

Completion criteria:
- [ ] Record the OS, architecture, Docker/Compose versions, and service image references.
- [ ] Confirm the external disk mount and persistent-data mappings.
- [ ] Review numeric ownership, network mode/bind addresses, health checks, log rotation, and recovery dependencies against actual sources and runtime evidence.
- [ ] Import redacted copies of the actual Compose or Portainer stack sources, including relevant overrides.
- [ ] Replace secrets with placeholders and document required variables in .env.example files.
- [ ] Validate each stack with docker compose config --quiet and record the test date.

Keep live credentials, VPN keys, private endpoints, and application databases outside the public repository.

## P0 / 2. Agree on production backups and complete an isolated application restore

Establish a recovery procedure before scheduling unattended backups.

The owner chose disposable testing only while the destination is undecided.
The sample lab is complete; no production backup or live application restore is
claimed. This item depends on item 1 and a destination decision.

Completion criteria:
- [ ] Identify configuration, database, and media data that require a backup.
- [ ] Select a separate destination, retention policy, encryption approach, and failure reporting.
- [ ] Agree on recovery point/time objectives, available capacity, and a maintenance window; document access and key recovery without publishing secrets.
- [ ] Use application-supported exports or a consistent stopped-service backup.
- [ ] Restore one service in an isolated location and verify data and application behavior.
- [ ] Record measured recovery time and any failures.
- [ ] Add and test a scheduled backup job only after recovery is verified.
- [ ] Demonstrate a failed run and stale/missing-run detection through the chosen notification route.

Do not overwrite the only live copy during a test or publish backup archives and keys.

## P1 / 3. Document and verify the network and WireGuard access design

Confirm how the gateway, switch, Raspberry Pi, and remote access actually fit together.

Completion criteria:
- [ ] Verify the gateway, switch, Pi uplink, and WireGuard hosting device.
- [ ] Record DNS/DHCP ownership and intended service access at a public-safe level.
- [ ] Add a topology diagram with generic labels.
- [ ] Test intended local and remote access and document recovery if the VPN is unavailable.
- [ ] Reconcile IPv4/IPv6 listeners, published addresses, host networking, gateway forwards and UPnP with intended access; record authorized negative tests.

Do not publish private keys, controller exports, or real endpoint details.

## P1 / 4. Establish monitoring and capture a troubleshooting case study

Build monitoring around checks that lead to a useful action, and document one real diagnostic result for the portfolio.

Completion criteria:
- [ ] Run the read-only health-check script on the Pi and confirm the correct storage paths.
- [ ] Document expected long-running services and intentionally stopped containers.
- [ ] Use explicit expected container names and confirm a missing required service produces failure in a safe simulation.
- [ ] Add application availability probes and select relevant host metrics.
- [ ] Define thresholds, alert routing, and response steps before scheduling checks.
- [ ] Record one actual incident with evidence, the change made, and a measured outcome.

Prometheus and Grafana are candidate tools, not currently verified deployments.

## Private administrative automation intake

Administrative handoffs and their implementation status are tracked separately
in the private workspace. No private career, vehicle, or business records belong
in this repository, its issues, or its PR. Require an input schema, desired
output/destination, trigger, success criteria and authorized actions before any
private automation is enabled. This public backlog makes no claim about that
separate work's completion.
