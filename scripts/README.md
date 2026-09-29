# Scripts

## Read-only health check

Requirements: Linux, Python 3.8 or newer, and optionally the Docker CLI with
existing access to the local daemon. The script does not request elevated
privileges or change Docker socket permissions.

```sh
python3 scripts/healthcheck.py
python3 scripts/healthcheck.py --mount /actual/mountpoint
python3 scripts/healthcheck.py --path /actual/data/directory --min-free-percent 15
python3 scripts/healthcheck.py --expect-container actual-container-name --expect-container another-actual-name
python3 scripts/healthcheck.py --json
python3 scripts/healthcheck.py --skip-docker
```

Replace the example paths with confirmed paths on the host. Root `/` is always
checked. Repeat `--path` or `--mount` for additional locations. `--path` checks
the containing filesystem; `--mount` also requires a detected mount point.
Some same-filesystem bind mounts may not be recognized by Python's mount-point
test; verify such layouts separately.

After confirming the inventory, repeat `--expect-container` for the **exact
container names** that must exist and run. These are Docker names, not Compose
service names or patterns. A missing, exited, created, or paused required
container fails. A stopped container without an expectation produces a warning.
All discovered containers are still checked. Do not combine expectations with
`--skip-docker`: that combination is rejected before any checks run. Without
expectations the script cannot detect a deleted service.

| Exit code | Meaning |
| --- | --- |
| 0 | All selected checks passed |
| 1 | Review needed: Docker is absent without expectations, no containers exist without expectations, a container is stopped/starting, or application health is not reported |
| 2 | A check failed, a required container is missing/not running, Docker cannot verify expectations, or arguments are invalid |

The default minimum free space is 10%. Adjust it to suit the workload. Docker
commands time out after 10 seconds. Running containers without reported Docker
health are `WARN`; `PASS` requires running state and reported `(healthy)` status.
Unhealthy, dead, or restarting containers fail even when not explicitly required.
Health checks that are starting generate a warning. Missing Docker becomes a
failure when expectations are supplied. Query, decoding, or malformed-output
errors fail instead of reporting a partial success.

Run on the host whose filesystems you intend to examine. Docker uses the existing
CLI context and environment, which can target a different daemon; verify that
target before treating the result as Pi evidence. The script does not switch
contexts or request access. It checks free capacity and mount-point detection,
not disk identity, inode availability, write permissions, or application data
integrity. Reported Docker health is only evidence for the configured probe; it
does not prove end-to-end availability. Intentionally stopped containers still
generate a review warning.

Output includes paths, container names and status summaries, which may require
redaction before public sharing. The script does not retrieve container
environment variables, application logs, VPN keys, or Docker configuration.

Run the tests from the repository root with
`python3 -m unittest discover -s tests -v`.
The healthcheck tests use temporary directories and mocked Docker responses to
exercise capacity boundaries, missing mounts/containers, state and health
classification, malformed output, timeouts, decoding errors, invalid arguments,
and JSON exit codes. They do not contact the Pi or a Docker daemon and do not
establish live service health. Python 3.8+ is the intended supported syntax/API;
record the actual interpreter used when reporting verification.

## Disposable backup/restore exercise

Run `python3 scripts/backup_lab.py --json` to create, snapshot, restore, validate,
and clean up generated sample data. It accepts no live source/destination paths
and needs no Docker or network access. See [the backup guide](../backups/README.md)
and [sample restore record](../backups/restore-test.md) for boundaries and results.
