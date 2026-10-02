# Private repeatable health collection

September 30 direct Pi validation: manual current wrapper saved mode-0600 files
in mode-0700 directories and retained health exit 1. Replay of an identical
captured report with only checked_at changed deduplicated. Adapted service/timer
verification passed; no installation/activation occurred. Keep-all history has
no automatic rotation. See [current evidence](live-audit-2026-09-30.md#monitoring-status)
and [prepared activation/rollback](prepared-changes.md).

Demonstrated repetitive task: the September 29 inspection repeatedly collected
capacity/health observations and separated private data from shareable evidence.
The wrapper reuses healthcheck.py instead of starting another monitoring project.

Inputs: explicit existing absolute owner-only output directory and healthcheck
flags/private config after --. Outputs: daily UTC directory with SHA-256 named
bundles containing health.json, health.txt and collected-at.txt. Directories
are 0700, files 0600. Reports can include local paths/service labels, so keep
them private and review any excerpt before publication.

Example from the repository root, after choosing a private local directory:

```sh
mkdir -m 700 /absolute/private/report-directory
python3 scripts/report_snapshot.py --output-dir /absolute/private/report-directory -- --mount /mnt/storage
```

Create a new directory you own; do not repair arbitrary existing permissions.
The one-shot local workspace proof is recorded in verification.md. The output
directory stays outside the repository; no scheduler, notification or cloud
synchronization is implied.

Deduplication: identical semantic report content within the same UTC day shares
one bundle; checked_at differences are ignored and the first time is retained.
Changed observations create another bundle. This is exact content deduplication,
not aggregation or a weekly trend calculation. Retention is keep-all until an
explicit policy is approved.

Errors: missing/writable-by-others/symlink destinations and damaged/incomplete,
extra-file or malformed existing bundles are refused, never overwritten. Reads
are bounded and verify private modes and UTC timestamps. A partial failed bundle may
remain and requires review. Exit 0/1/2 preserves the healthcheck outcome; 3 means
collection failed. Flags/config that prevent the checker from producing a valid
report also produce a generic diagnostic and collector exit 3. Direct
healthcheck invalid arguments still exit 2. CLI help is available on Windows; collection requires
POSIX ownership/mode support and refuses unsupported hosts.
Completion requires a valid saved bundle with matching readable/JSON content,
verified privacy modes and propagated status; tests cover these boundaries.

A weekly administrative routine can review that week's private bundles and
write a sanitized incident note. There is no automatic weekly run. Drive,
Gmail and Calendar were not used; no synchronization or personal/vehicle task
completion is claimed. The Pi implementation was later published in existing draft PR #1; see
[delivery history](access-and-delivery.md). Finances were skipped.
