# Monitoring

The direct [September 30 audit](../docs/live-audit-2026-09-30.md#monitoring-status)
verified existing Prometheus/Grafana/node-exporter/cAdvisor rather than deploying
another stack. Three scrape targets are up; host filesystem and container memory
metrics are present. Grafana health/database passes. Dashboard/auth/alert delivery
and sustained availability remain unverified. Manual current readable/JSON health
and private reporting exit 1 with explicit UNKNOWN coverage. Adapted temporary
units/calendar pass verification; no timer is installed/enabled. Exact prepared
installation and rollback: [prepared changes](../docs/prepared-changes.md).

[healthcheck.py](../scripts/healthcheck.py) provides read-only host observations
and configured application response probes. The code is prepared locally;
that does not establish Pi deployment, continuous monitoring, uptime or alert
delivery. [Script usage](../scripts/README.md) describes the private JSON config,
thresholds, actions and explicit coverage exclusions.

| Signal | Implemented observation | Limitation/action |
| --- | --- | --- |
| Capacity and mounts | Root plus explicit paths/required mount points | Verify disk identity and intended layout separately |
| Container state/health | Docker inventory; optional exact required names | Docker access denial is UNKNOWN; no health result is UNKNOWN |
| Restart counters | Opt-in `--check-container-restarts`, selected formatted lifetime counts | Zero PASS, nonzero WARN; not a restart rate; invalid/denied UNKNOWN |
| Failed units | System or user bus `systemctl --failed` | Inaccessible bus is UNKNOWN, not an observed service failure |
| Available memory | Linux `MemAvailable/MemTotal` | Configure workload thresholds; no process inspection or repairs |
| Resource contention | Five-minute load/CPU; memory PSI `some avg10` | I/O wait contributes to load; unsupported PSI is UNKNOWN |
| Temperature | Explicit/default sysfs file, thresholds | Confirm the CPU thermal zone; inaccessible data is UNKNOWN |
| Pi power/throttling | `vcgencmd get_throttled` current/history flags | Current flags fail, historical flags warn; unavailable utility is UNKNOWN |
| Application response | Explicit bounded credential-free HTTP GET/status probes | No default requests; response from this host does not establish login/data/client access |
| Hostname resolution | Explicit bounded operating-system resolver worker; hostname/address omitted | Hosts/cache may answer; resolution does not establish transport/app health |
| Backup evidence | Configured schema-validated recovery marker and snapshot packaging age | Static config/export byte evidence only; source-data age, authenticity and application recovery are separate |

Power/throttling bit interpretation follows [Raspberry Pi's firmware command
reference](https://www.raspberrypi.com/documentation/computers/os.html#get_throttled).
Threshold defaults are proposals to review after observation, not measured Pi
limits or proof that cooling/power is adequate. Current [Pi evidence](../docs/live-audit-2026-09-30.md)
verifies three existing scrape targets and measured coverage. Dashboards and
alerts remain unverified. Do not duplicate the existing stack.

## Interpreting and collecting reports

Exit `0` means selected checks passed. Exit `1` means `WARN` or `UNKNOWN` needs
review. Exit `2` means an observed critical `FAIL` or invalid arguments. A
successful Docker inventory with a missing required name fails; an inaccessible
Docker query cannot prove that name is absent. A running container without a
health result or configured HTTP probe does not establish availability.
No backup marker, HTTP or DNS probe is configured by default: those coverage gaps
are explicit `UNKNOWN` observations. A skipped category is excluded from the
report, so a green selected report does not cover it.

Run manually before scheduling, using confirmed mount points, exact container
names, application-supported health endpoints, selected backup evidence and
appropriate thresholds. Review every action. Use [the recovery guide](../backups/README.md)
to understand what a marker proves. Recent packaging does not establish recent
native export data, and byte recovery does not establish application recovery.

[report_snapshot.py](../scripts/report_snapshot.py) collects timestamped JSON
and readable reports in an explicitly selected private directory. It preserves
the health exit status and avoids duplicate equivalent bundles within the UTC
day. Reports/config belong outside public Git. Names and filesystem paths still
need redaction before public sharing. No notification destination is configured;
a saved report by itself does not deliver an alert.

## Proposed user systemd schedule

Templates are prepared in [homelab-report.service](systemd/homelab-report.service)
and [homelab-report.timer](systemd/homelab-report.timer). **They have not been
installed, enabled or run.** The proposed daily time is 08:00 in
America/Los_Angeles with up to five minutes of randomized delay; this is a
reviewable proposal, not an existing Pi schedule. `Persistent=true` can run a
missed collection after the user manager resumes. A user timer needs the user
manager to remain available; enabling login lingering would be a separate live
change requiring approval.

The unit's repository path is deliberately `/ABSOLUTE/PATH/TO/homelab`; replace
it with the confirmed checkout and verify `/usr/bin/python3` before installation.
The service expects a reviewed private config at
`~/.config/homelab/healthcheck.json` and an existing owner-only `0700` directory
at `~/.local/state/homelab/reports`. It applies `UMask=0077` and a five-minute
collection deadline. Review failures remain nonzero unit results: exit `1`
means incomplete/warning coverage and `2` means critical observations. Neither
causes a repair or restart. A collection/storage error uses exit `3`.

Complete scheduler inventory remains **unverified**. A later bounded system
failed-unit query succeeded; that does not establish all scheduled jobs. Do not assume no jobs exist. With existing access,
inspect schedules before proposing installation so a new collector cannot
silently duplicate existing work:

```sh
systemctl --user list-timers --all --no-pager
systemctl list-timers --all --no-pager
crontab -l
```

Review sanitized output only; permission errors remain unknown. Also inspect
known application/export schedulers and root-owned jobs through already
approved administrative access where applicable. Do not escalate permissions
or enable a job merely to complete discovery. Confirm schedule ownership,
report destination, marker selection and notification requirements; then obtain
approval for copying units and activating the timer. No installation/enable
command is run by these templates or this documentation change.

Before activation, validate the adapted unit/time syntax with the Pi's existing
systemd tools, run the exact service command manually, and check report access,
exit codes and duplicate behavior. Verify a simulated unknown/failure is
retained and visible to the intended reviewer. Any eventual alert integration
must test delivery and detect missing/stale runs as well as failed observations.
To roll back an approved deployment, disable its timer before removing its
units; preserve private reports and config until their retention is agreed.
This remains an approval-gated runbook, not an assertion of activation.

Automated tests use simulated host/service/HTTP observations. They do not
measure the live Pi, external alert delivery, uptime or production recovery.
