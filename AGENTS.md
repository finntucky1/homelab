# Working in this repository

This is a public Raspberry Pi homelab operations and learning repository. The
hardware and services in `docs/inventory.md` are owner-reported until supported
by dated host evidence. GitHub access never implies access to the Pi.

## Conventions

- Work on a separate branch. Inspect status and preserve existing changes.
- Keep scripts small, standard-library Python, and compatible with Python 3.8+
  unless the documented minimum is deliberately changed. Use LF line endings.
- Keep facts, owner reports, proposed designs, and tested samples distinct.
  Record commands, dates, scope, and limitations with verification results.
- Never invent Compose files, image versions, mount paths, UIDs, exposure,
  recovery times, uptime, or deployment status. Review actual sources first.
- Keep README, inventory, runbooks, backlog, and script usage consistent.

## Validation

From the repository root:

```sh
python3 -m unittest discover -s tests -v
python3 scripts/healthcheck.py --help
python3 scripts/backup_lab.py
git diff --check
```

Tests and the backup lab use disposable data and simulated Docker responses.
They do not establish live Pi health or application recovery. Run meaningful
failure-path tests for script changes; documentation-only changes need link
and accuracy review, not artificial tests. Validate sanitized Compose sources
with `docker compose -f compose.yaml config --quiet` only after obtaining the
actual file/override order. Never use `up` as a validation command.

## Boundaries

- Read-only inspection and safe local tests are allowed. Ask before live
  service changes, Pi installations, reboots, deletions, or public exposure.
- Health checks must not restart services, repair permissions, install tools,
  retrieve secrets, or weaken Docker socket access.
- No passwords, API tokens, VPN keys, resolved environment dumps, application
  databases, backup archives, private endpoints, or personal administrative
  data in Git. Ignore rules are not a secret scanner; inspect the staged diff.
- The backup lab only handles data it creates. Production automation requires
  verified services and paths, an agreed destination and retention policy,
  application consistency, failure reporting, and approved isolated recovery.
- Search existing issues before creating one; use measurable acceptance
  criteria. Open a draft PR when authorized; never merge without explicit
  direction.
- Keep unrelated career, vehicle, or business automation outside this public
  repository. Obtain its requirements separately.
