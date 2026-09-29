# Operating notes

## Baseline inspection

First collect the [sanitized baseline](pi-evidence.md). Confirm the Docker
context targets the intended local daemon; the healthcheck does not override
CLI context or `DOCKER_HOST` settings. Do not infer Pi state from a workstation.

Run the read-only check from the repository:

```sh
python3 scripts/healthcheck.py
```

After confirming the external disk's actual mount point, include it with
`--mount /actual/mountpoint`. This matters because an existing directory can
remain present when the intended disk is not mounted.

Record the date, symptoms and relevant results privately. The check only
reports filesystem capacity and Docker's own state; verify important
applications through their normal client or interface as well.

Once actual long-running container names are confirmed, add repeatable
`--expect-container NAME` flags. This detects an expected container that no
longer appears in Docker's inventory. Exit 1 needs review; exit 2 is failure
or invalid arguments. A WARN for a running container without a health probe
means the application has not supplied health evidence.

## A service is unavailable

1. Determine the scope: one application, all containers, the host, or remote
   access only. Try the local network before diagnosing the VPN.
2. Review disk capacity and confirm required storage is mounted.
3. Check container state and recent application logs locally. Logs may contain
   credentials or personal data; redact any excerpt before publishing it.
4. Compare the current image, configuration and recent changes with the last
   known working setup. Write down what changed and when.
5. Make one targeted change, then verify the original symptom and persistence
   of application data. Record the result in an issue or case study.

## Before an update

Confirm the current image reference and configuration, create an appropriate
application-consistent backup, and define a rollback plan. Test one service
first. Do not prune volumes as a troubleshooting step: they may hold the only
copy of application data.

## Case study template

- Problem and observed impact:
- Evidence collected:
- Hypothesis and diagnostic steps:
- Change made:
- Verification and measured outcome:
- What would prevent recurrence:

Leave results blank until they have been observed.
