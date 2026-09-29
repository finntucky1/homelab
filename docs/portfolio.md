# Portfolio evidence: operations groundwork

## Problem

The GitHub repository began with only a title. A prepared starter package
described a reported Raspberry Pi homelab, but there was no verified deployment
inventory, live Compose source, or demonstrated application recovery.

## Design and implementation

- Integrated the starter documentation and dependency-free read-only check on
  a separate branch, preserving the repository's base history.
- Added project conventions, evidence collection, operating and review notes,
  a prioritized backlog, and exercises that make uncertainty explicit.
- Improved container checks to distinguish observed running processes from
  application health and detect explicitly expected containers that disappear.
- Implemented a disposable backup/restore lab to demonstrate consistency,
  integrity verification, retention boundaries, and failure handling before
  choosing a production destination or modifying any live service.

## Verification and limitations

See `docs/verification.md` for the exact local evidence and
`backups/restore-test.md` for the sample restore record. The original seven
tests were rerun before changes; the expanded suite exercises failure behavior.

No live Pi access was used. No service deployment, production backup, restored
Jellyfin/Portainer instance, firewall audit, or sustained monitoring was verified.
No uptime, RPO, RTO, or reliability improvement is claimed. The sample restore
does not establish disaster recovery capability for the reported homelab.

## Interview talking points

- "I separated reported infrastructure from observed evidence so the runbooks
  did not imply a deployment audit had happened."
- "I reproduced a false-green case: a deleted container disappears from
  `docker ps`. An explicit expected-container check makes that absence visible."
- "I distinguished a running process from application health, and tested
  failures without disrupting the server."
- "I exercised a consistent synthetic database backup and an isolated restore,
  including damaged-backup refusal. Live application recovery remains a
  separate acceptance test."
- "The integration returned 403 on authorized writes despite account push
  permission. I documented the access boundary and prepared portable delivery
  rather than treating the repository permissions field as proof of access."

September 29 update: authenticated branch creation succeeded after access was
updated. The reviewed package passed all 28 tests on Linux with no skips.
These are agent-executed verification results; the learner should reproduce
and explain the relevant exercises before presenting them as personal work.

## Lessons and next evidence

Recovery begins with dependency and storage knowledge; automation cannot fill
in unknown paths or application consistency requirements. The next evidence is
a sanitized live inventory and stack sources, followed by an agreed independent
backup destination and an approved isolated application restore. Add measured
results only after those tests occur.
