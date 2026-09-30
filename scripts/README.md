# Scripts

## Read-only health check

Run `healthcheck.py` on the Linux host being checked with Python 3.8 or newer.
It uses the standard library and existing Docker/systemd/firmware access. It
never installs tools, repairs permissions, restarts services or changes a
Docker context. Host measurements and Docker's current context can target
different machines; confirm Docker targets the Pi before interpreting the
combined report as Pi evidence.

```sh
python3 scripts/healthcheck.py
python3 scripts/healthcheck.py --mount /actual/mountpoint \
  --expect-container actual-container-name --json
python3 scripts/healthcheck.py --config /private/healthcheck.json --json
python3 scripts/healthcheck.py --help
```

Root `/` is always checked. Repeat `--path`, `--mount` and
`--expect-container` for confirmed additional paths, mount points and exact
Docker names. `--path` checks the containing filesystem. `--mount` also requires
a detected mount point; same-filesystem bind mounts may need separate
verification. Disk identity, inodes, permissions and data integrity are separate
checks. Missing configured paths/mounts fail; inaccessible observations are
`UNKNOWN`.

The default report selects capacity, container state/health, failed systemd
units, available memory, five-minute load per CPU, Linux memory pressure,
sysfs temperature, Pi power/throttling flags, configured backup evidence and
explicit HTTP probes. An unavailable source is `UNKNOWN`, including Docker
socket denial, systemd bus denial, absent `vcgencmd`, unsupported PSI and a
missing thermal interface. These do not prove a service or the Pi has failed.
A report with no configured backup marker or HTTP probes records `UNKNOWN`
for that coverage rather than silently implying it passed.

Use `--skip-docker`, `--skip-systemd`, `--skip-resources`, `--skip-thermal`,
`--skip-backup` or `--skip-http` to deliberately exclude a category. **Changed
from the earlier interface:** `--skip-docker` excludes only Docker. For a
filesystem-only run, explicitly skip all six categories. A skipped category
has no result and a green selected report does not establish its health.
Required Docker names cannot be combined with `--skip-docker`.

| Exit | Interpretation |
| --- | --- |
| 0 | All selected observations passed |
| 1 | At least one `WARN` or `UNKNOWN`, with no observed critical failure |
| 2 | An observed `FAIL`, or invalid CLI/config arguments |

`FAIL` takes precedence over `WARN`/`UNKNOWN`. Docker healthy means running
with a reported `(healthy)` result, with coverage limited to that actual
probe. A running container with no health result is `UNKNOWN`; starting or an
unrequired stopped container is `WARN`. Unhealthy/dead/restarting containers,
missing required names from a successful query, and required containers that
are not running fail. A denied, timed-out, malformed or undecodable query is
`UNKNOWN` even when names are required; it cannot establish their absence.

## Private configuration and thresholds

Keep host-specific config outside this public repository, or under ignored
`private/`; use owner-only access. No configuration is auto-discovered.
Config and recovery-marker leaf files must be regular, non-symlink, owned by
the current user and mode 0600. Nonregular files, including named pipes, are
rejected with nonblocking opens; do not pass raw devices or change their modes.
`--config` accepts a JSON object of at most 64 KiB. Unknown keys and invalid
values are rejected before observations. These are the allowed keys:

| Key | Value and default |
| --- | --- |
| `paths`, `mounts`, `expected_containers` | Lists of nonempty strings; default `[]` |
| `thresholds` | Object with the numeric keys in the table below |
| `systemd_scope` | `system` (default) or `user`; chooses the failed-unit bus |
| `thermal_path` | Verified millidegree-C sysfs file; default `/sys/class/thermal/thermal_zone0/temp` |
| `backup_marker` | Path to a verified static config/export byte-recovery marker; no default |
| `backup_max_age_hours` | Positive maximum snapshot packaging age; default `48` |
| `http_probes` | Up to 16 explicit objects described below; default `[]` |

CLI lists append to configured lists. CLI scalar values override config values.
Every threshold also has a flag with underscores replaced by hyphens, for
example `--memory-warn-percent 15`. Thresholds must be finite, nonnegative and
ordered; percentage thresholds must be between 0 and 100. Choose suitable
values from observed workload behavior; the defaults are proposed review
thresholds, not measured Pi capacity or vendor failure limits.

| Threshold key | Default | Meaning |
| --- | --- | --- |
| `min_free_percent` | 10 | Fail below this free-capacity percentage |
| `memory_warn_percent`, `memory_fail_percent` | 10, 5 | Warn/fail below available-memory percentage (`MemAvailable/MemTotal`) |
| `load_warn_per_cpu`, `load_fail_per_cpu` | 1, 2 | Warn/fail at or above five-minute load divided by CPU count; load includes I/O waits |
| `pressure_warn_percent`, `pressure_fail_percent` | 10, 25 | Warn/fail at or above memory PSI `some avg10` stall percentage |
| `temperature_warn_c`, `temperature_fail_c` | 70, 80 | Warn/fail at or above configured sysfs temperature |

An illustrative config follows. It is a template; the paths, exact name, port
and endpoint are invented placeholders to replace with verified values before
use. The probe is not asserted to be supported by any deployed application.

```json
{
  "mounts": ["/replace-with-confirmed-mount"],
  "expected_containers": ["replace-with-exact-name"],
  "thresholds": {"min_free_percent": 15},
  "backup_marker": "/private/replace-with-verified-recovery-marker.json",
  "backup_max_age_hours": 48,
  "http_probes": [
    {
      "name": "media",
      "url": "http://127.0.0.1:8080/replace-with-verified-health-path",
      "timeout_seconds": 3,
      "expected_statuses": [200]
    }
  ]
}
```

## Application response probes

No HTTP request occurs unless a probe is supplied explicitly by private config
or repeatable `--http-probe LABEL=URL`. CLI probes use a 3-second socket timeout
and expected status `200`; config probes can set `timeout_seconds` between 0.1
and 15 and a nonempty list of integer `expected_statuses` from 100 through 599.
Labels contain letters, digits, period, underscore or hyphen and must be unique.
The URL requires HTTP/HTTPS and a hostname. User/password components, query
strings, fragments, control characters and whitespace are rejected. Choose a
credential-free supported endpoint; authorization headers are not supported.

Each GET checks response headers/status without downloading the response body.
Ambient proxies and redirects are disabled; TLS verification remains enabled.
An isolated Python child receives the URL through stdin, and the parent enforces
an overall deadline of socket timeout plus one second, bounding DNS/TLS/header
work too. Probe URL, response body, headers, credentials and raw exceptions
never appear in report output; only the label, observed status and action do.
A connection/TLS failure, deadline or unexpected response status fails the
explicit reachability observation. An inaccessible/malformed local probe
worker is `UNKNOWN`. These checks establish one response from this host;
application login, meaningful data and LAN/VPN-client access still need tests.

## Backup evidence and firmware signals

`--backup-marker` and `--backup-max-age-hours` select an explicit private marker
from [the static config/export workflow](../backups/README.md). Its exact JSON
fields are `schema` (integer `1`), `kind` (`config-export-recovery`), `status`
(`verified`), `created_at` and `recovered_at` (UTC `YYYY-MM-DDTHH:MM:SSZ`),
`snapshot_id` (safe identifier) and `manifest_sha256` (64 lowercase hex digits).
The checker validates the schema, chronology and at most five minutes of clock
skew; malformed/unreadable/unverified evidence is `UNKNOWN`. A configured
missing marker or packaging age over the chosen limit fails.

Freshness uses `created_at`, the snapshot **packaging timestamp**. A recently
packaged old export may still contain old application data. The marker records
isolated byte recovery of selected static files/exports only. It is a local
assertion, not authenticated proof of backup completeness, source-data age,
application startup or recoverability. The checker does not create markers,
read backup archives or restore anything. Review source-data freshness and
periodically test application recovery separately.

`vcgencmd get_throttled` reports bits 0–3 for current under-voltage, frequency
capping, throttling and soft temperature limit, and bits 16–19 for corresponding
since-boot history. Current flags fail, history alone warns, and zero flags
pass that observation. Unknown flag bits/query failures are `UNKNOWN`.
See [Raspberry Pi's firmware command reference](https://www.raspberrypi.com/documentation/computers/os.html#get_throttled).
Historical flags do not prove a present power fault; keep that distinction when
reviewing the PoE path and cooling.

## Reports and local validation

Readable and `--json` reports include actionable guidance. JSON schema `1`
contains UTC `checked_at`, `exit_code` and `checks`; each check includes `name`,
`status`, `detail`, `action` and, where measured, `metrics`. Filesystem paths,
unit/container names and Docker status summaries may still need redaction
before public sharing. No environment values, application logs, VPN keys,
Docker configuration or HTTP endpoints are retrieved into the report.

Run simulated tests without a daemon, Pi or application endpoint:

```sh
python3 -m unittest discover -s tests -p 'test_healthcheck.py' -v
```

The tests cover healthy/critical/unsupported observations, boundaries,
malformed/denied/timed-out sources, backup schema/freshness, probe privacy and
deadlines, config/argument validation and exit/JSON contracts. Python 3.8+ is
the intended supported syntax/API; record the actual interpreter tested.
Proposed scheduling templates are in [monitoring](../monitoring/README.md);
they are not installed or enabled.

## Explicit static-file/export backup and private report collection

`backup_config.py` snapshots only explicitly enumerated static files or
completed application-supported exports. It requires a private existing
destination, consistency acknowledgement, bounded stable reads and keep-all
retention. Isolated restore refuses existing targets and can produce a private
byte-recovery marker. It does not export live applications or copy running
databases. See [backup usage](../backups/README.md) for exact commands.

`report_snapshot.py --output-dir /absolute/private/directory -- HEALTH_FLAGS`
reuses the checker and saves private readable/JSON daily bundles. Identical
semantic reports in the same UTC day deduplicate despite different checked_at
timestamps. It preserves health exit 0/1/2; collection errors use 3. It refuses
unsafe destinations and damaged/incomplete existing bundles. Reports may still
include filesystem/service labels and must stay private. See
[private reporting](../docs/private-reporting.md). Nothing is scheduled.

## Disposable backup/restore exercise

Run `python3 scripts/backup_lab.py --json` to create, snapshot, restore, validate,
and clean up generated sample data. It accepts no live source/destination paths
and needs no Docker or network access. See [the backup guide](../backups/README.md)
and [sample restore record](../backups/restore-test.md) for boundaries/results.
