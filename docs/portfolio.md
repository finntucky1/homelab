# Portfolio evidence and honest interview explanations

This is agent-assisted engineering work on September 29–30, 2026. The owner defined
the goals and boundaries; the agent performed these inspections, implementations
and tests. Reproduce and explain each exercise before claiming personal
implementation/troubleshooting proficiency. No invented uptime, speedup,
incident resolution or production deployment is claimed.

## Project 1: evidence-based Pi diagnostics

Problem: reported hardware/services were being treated as a baseline without
live evidence. Work: inspect the actual Pi read-only, preserve source/runtime
distinctions, review logs privately and record constraints. Design: expose
UNKNOWN for denied access, separate container state from HTTP response evidence,
use configurable disk/resource/thermal/backup checks with actionable output.
Troubleshooting: distinguish an initial candidate path mismatch from later
runtime shared storage, and DNS/HTTP success from the enabled client's health
error. The [follow-up](pi-runtime-follow-up.md) preserves disconfirming evidence.
Result: dated inventory and tested checker; live Docker/network remediation
remains open. Evidence: [inventory](inventory.md), [findings](review-findings.md),
[tests](verification.md).

Interview draft: “I directed an assisted audit, then reproduced its checks.
The key decision was distinguishing missing evidence from an outage. I can show
how simulated unhealthy, missing-container and denied-tool cases affect the
report. The candidate suggested a path inconsistency; newer runtime evidence
showed shared storage. I would check the exact configured client before changing it.” Use “I reproduced” only after you do it.

## Project 2: recovery with explicit proof boundaries

Problem: backup existence does not establish recovery or protect against device
loss. Work: preserve the synthetic SQLite online-backup lab, add restricted
static-file/export snapshot tooling, and restore an existing native Radarr ZIP
to an isolated private temporary directory.
Design: explicit inputs, stable bounded reads, SHA-256 manifests, no overwrites,
keep-all development retention, private modes and success markers after restore.
Troubleshooting: tests reject corruption, traversal, symlinks and overlap.
Result: actual Radarr archive CRC/restored bytes/SQLite integrity passed;
application startup and independent disaster recovery were not demonstrated.
Evidence: [restore record](../backups/restore-test.md) and [verification](verification.md).

Interview draft: “I learned to separate byte integrity, database integrity and
application recovery. The assisted rehearsal recovered an existing Radarr
archive without touching live data. I reproduced failure tests and can explain
why a same-disk backup and a running-database copy are inadequate.” Again,
claim reproduction only when supported by your own retained result.

## Project 3: private repeatable reporting

Problem: repeated manual health commands and report collection are error-prone.
Work: the actual inspection repeated capacity, health and evidence collection;
a small wrapper now creates private readable/JSON daily report bundles.
Design: explicit output directory, 0700 directories/0600 files, exact semantic
deduplication within each UTC day, no secret HTTP endpoints in report output,
nonzero health status preserved and no automatic scheduler/notification.
Troubleshooting: corruption/incomplete bundles and unsafe paths are refused.
Result: fixture tests and local one-shot collection; no unattended operation
or time-saving metric claimed. Evidence: [private reporting](private-reporting.md).

Interview draft: “I used a tested wrapper to make repeated manual collection
consistent. It keeps evidence private and preserves unknown/failure exit codes,
so automation cannot quietly turn missing access into a green report. A scheduler
still needs de-duplication and access review before enabling it.”

## Completion evidence

An artifact/test result supports agent-executed work. Learner completion requires
your own explanation and reproduction, recorded privately. Use
[the four-week sequence](learning-exercises.md) to build that evidence.

## MSI development continuation

Problem: current Pi evidence had superseded the initial candidate findings, and
stored health reports needed stronger validation. The MSI preserved both Git
histories, attributed the runtime follow-up, withdrew an unsupported bind edit,
and reviewed/tested failure handling in isolated Windows/Linux environments.
Added explicit DNS-resolution and lifetime restart-counter observations; neither
automatically changes live services. Full local Linux coverage passed while
Windows host-feature skips remained visible. See [verification](verification.md).

Interview explanation to reproduce: describe one UNKNOWN case, one corrupted
report/snapshot refusal, and the evidence that disproved the candidate bind
hypothesis. Explain why resolution, HTTP status, authentication and import are
different checks. State the agent's contribution and your own retained exercises.
Do not claim learner completion, uptime or independent disaster recovery.
