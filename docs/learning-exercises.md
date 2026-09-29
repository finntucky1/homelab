# Learn by operating and explaining

Use a local checkout and disposable data. Do not create failures on the Pi.
Each exercise ends with evidence you can explain, not just a green command.

## 1. Read the evidence boundary

Compare `docs/inventory.md` with `docs/review-findings.md`. Pick three reported
facts and identify the read-only evidence needed to verify each. Explain why a
GitHub checkout cannot establish the Pi's OS, current services, or firewall.

Completion: a private table with claim, source, observation date, and uncertainty.
Do not promote a reported fact to verified without observing it.

## 2. Diagnose an absent disk

Create an ordinary temporary directory on your development machine and pass
it to the healthcheck once with `--path` and once with `--mount`, using
`--skip-docker --json`. Inspect the exit code (`echo $?` in a POSIX shell,
`$LASTEXITCODE` in PowerShell). No actual mount changes are needed.

Explain why a directory left behind after a disk disappears can still pass a
capacity check. State what `Path.is_mount()` cannot prove: disk identity,
mount-on-boot reliability, and some same-filesystem bind mounts.

Completion: retain the two sanitized reports and explain the different results.

## 3. Process state versus service health

Read `tests/test_healthcheck.py` and run the suite. Find cases for a healthy
container, no configured health probe, a stopped container, a missing expected
container, and a Docker timeout. Explain why an expected service must be named
explicitly and why Docker health does not prove a user's client can reach it.

On a private working branch, add a test for one new simulated failure before
changing behavior. Never stop a live container just to complete the exercise.

Completion: explain the check, threshold, exit status, and operator action for
each case. Also explain how an external scheduler could detect *no report*.

## 4. Prove a sample restore

Run `python3 scripts/backup_lab.py` and read `backups/restore-test.md`.
Locate the SQLite consistency boundary, checksum validation, isolated target,
retention boundary, and nonzero failure exit in the implementation.

Explain why copying a running application's database files is not equivalent
to using a supported consistent export. Explain why a matching checksum does
not prove the application version can use restored data.

Completion: record a sample report and three additional checks required for a
real Jellyfin, Portainer, or media-management recovery. Do not claim any of
those applications was recovered by the sample.

## 5. Trace one real service after evidence is available

Use sanitized actual Compose sources. Trace a client's connection from network
policy to published host address/port, container port, application, and storage.
Map each bind mount or named volume to its owner, consistency method, backup
scope, and restore destination. Locate health and logging configuration.

Troubleshooting task: devise read-only checks that distinguish an absent mount,
wrong UID/GID, application failure, and network restriction. Predict the result
that would disprove each hypothesis before proposing a change.

Completion: a reviewed service worksheet with evidence references and an
explicit list of unknowns. Apply changes only after live-change approval.

## 6. Explain this work in an interview

Use `docs/portfolio.md` as a starting point. Give a two-minute account of the
problem, a design decision, a reproduced failure, the verification, and the
remaining access gap. Be ready to show a test rather than quote an uptime or
recovery claim that has not been measured.
