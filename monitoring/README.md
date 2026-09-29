# Monitoring

The initial tool is [healthcheck.py](../scripts/healthcheck.py). Run it on demand
to inspect storage capacity and container state. It is not yet scheduled and
does not send alerts.

| Signal | Current coverage | Next step |
| --- | --- | --- |
| Root filesystem capacity | Checked by the script | Establish a suitable free-space threshold |
| External disk mount and capacity | Optional `--mount` check | Confirm the actual mount point |
| Container state and reported health | Docker status query; absent health is WARN | Verify each probe's coverage |
| Missing expected containers | Repeatable `--expect-container` exact-name checks | Confirm required names on the Pi |
| Application availability | Manual verification | Add application-specific probes |
| Temperature, power and disk health | Not implemented | Select host metrics appropriate to the Pi |
| Backup success and recovery | Separate from the healthcheck | Track [backup completion and restore evidence](../backups/README.md) |

Prometheus and Grafana are candidate improvements, not confirmed deployments.
Choose what needs action before building dashboards; define the threshold,
recipient, and response for every alert.

## Running and interpreting a check

Use confirmed values, for example:

```sh
python3 scripts/healthcheck.py --mount /actual/mountpoint \
  --expect-container actual-container-name --json
```

The exit status is `0` for all selected checks passing, `1` for review warnings,
and `2` for failed checks or invalid arguments. A missing expected container or a
required container that is not running fails. With no expected names, a deleted
container is invisible; an empty Docker inventory only warns. Every discovered
container is checked, so an unrelated intentionally stopped container can cause
a warning. A running container with no reported health probe also warns.

Before adding a schedule, run manually on the Pi, confirm Docker targets that
Pi, choose the required container names and mount points, then review each
warning. A green report does not prove that clients can use the applications,
that mounts contain the intended disks, or that backups can be restored.
The current implementation does not restart services, send notifications, or
perform repairs. For future scheduling, preserve the exit code and record the
timestamp plus JSON report privately; any alert integration should test failure
delivery and treat both stale/missing runs and failed checks as actionable.

To troubleshoot a missing expected container, compare its exact name with
`docker ps --all --format '{{.Names}}'`. Confirm whether Compose changed the
name or the service is actually missing before updating expectations. To
troubleshoot an absent health probe, review the service's actual Compose
definition and its supported health endpoint; do not invent a probe that only
tests for a process. Keep healthcheck output private until container names and
host paths are reviewed for sensitive information.

Local automated tests exercise simulated failures and output contracts. They
are not measurements of this Pi, alert delivery, uptime, or recovery.
