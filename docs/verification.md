# Verification record

Latest Pi continuation: **2026-09-29 America/Los_Angeles**. Initial integration:
2026-09-23. Historical checks below are retained as dated provenance.

## Actual Pi continuation and isolated testing

The session's device model, kernel, architecture, storage and OS identify the
actual Pi. Python 3.13.5 on ARM64 executed these checks. Bounded read-only
hardware/config/log inspection is documented in [inventory](inventory.md) and
[findings](review-findings.md). No live service/package/network/permission or
scheduler changes were applied; no remote GitHub content was updated.

| Command / check | Result | Evidence scope |
| --- | --- | --- |
| Baseline unittest discovery before changes | 28 passed, zero skips | Existing mocked/generated-data implementation on the Pi |
| Final unittest discovery | 86 passed, zero skips, exit 0 | 48 health, 17 config/export, 14 unchanged SQLite lab, 7 private reporting tests; isolated/mocked data |
| backup_lab.py --json | PASS, exit 0 | Generated SQLite online backup, two restored rows, hashes/integrity, corruption refusal, sample retention and cleanup |
| backup_config.py create/verify/restore CLI | PASS, byte match, marker 0600 | Generated static JSON fixture; damaged snapshot then refused before writes; temporary fixture removed |
| healthcheck.py --mount /mnt/storage --json | Exit 1 | Actual capacity/mount/memory/load/temperature passed; Docker/systemd/PSI/throttling and unconfigured backup/probes UNKNOWN |
| report_snapshot.py one-shot | Saved private JSON/text, exit 1 | Actual local selected checks; 0600 files. Selected filesystem-only repeated run deduplicated; exit 0 covers only that scope |
| Native Radarr archive isolated extraction | Three restored files matched; CRC PASS; SQLite integrity ok, 42 tables | Existing application-produced ZIP; app startup/integrations not tested; private temporary restore removed |
| Original and sanitized Compose config --quiet | Exit 0 | Four-service source syntax; source/runtime provenance still unknown |
| systemd calendar parser | Exit 0, America/Los_Angeles accepted | Proposed daily timer expression only |
| systemd-analyze --user verify templates | Access denied, exit 1 | Unit validation remains unverified in this restricted session; no schedule installed/enabled |
| Python 3.8 grammar parsing | Accepted | Syntax only; no Python 3.8 runtime exercised |
| Help, local Markdown targets, whitespace, diff/privacy review | Passed | CLI/documentation consistency and scoped source review; heuristic secret scan is not a universal guarantee |

Independent review reproduced FIFO hanging and deeply nested JSON failure in
early changes; both were corrected with regression tests before delivery.
Private configuration/marker leaves require current ownership, mode 0600 and
non-symlink regular files. Bounded nonblocking reads refuse FIFOs. Shared-writable
recovery evidence cannot pass. Default application probes make no requests;
explicit HTTP worker tests use mocked responses, proxies/redirects disabled and
an overall deadline, so no live app reachability is claimed.

Source provenance: GitHub connector reads retrieved the existing PR head
8d11e96b4b9d9b84cec2dd90290451cae0c9cc51 and main parent exactly. Blob/tree/commit
object IDs matched during local reconstruction. Work uses the separate local
branch codex/pi-baseline-2026-09-29. No user checkout/uncommitted work was replaced.
The draft PR remains at its prior head until an approved remote update.

Recovery-marker freshness is snapshot packaging age, not authenticated native
export age. Native Radarr archive and live state share a disk. No complete
application restore, offsite recovery, alert delivery, learner reproduction,
RPO/RTO or uptime measurement is claimed. See [restore record](../backups/restore-test.md)
and [prepared approval package](prepared-changes.md).

## Historical September 29 pre-Pi Linux verification

Downloaded the reviewed source archive and matched SHA-256
`d63a64c2929578941577f0dae607553eb16a08a5dcfe6ceba3bf1a60954d698e`.
The source ZIP records local implementation commit
`916a1d608fd87d28b33f0ee311806e410edec1d3` in its accompanying delivery record;
that Git history is not embedded in the ZIP. Remote integration preserves
the observed initial main commit as its parent and does not claim to reproduce
the original local commit IDs.

In a disposable Linux workspace, `python3 -m unittest discover -s tests -v`
passed all **28 tests**, zero skipped, exit 0. This includes both the POSIX
permissions and symbolic-link refusal tests previously skipped on Windows.
`python3 scripts/backup_lab.py --json` returned PASS, exit 0: two restored
SQLite rows, matching hashes, integrity check `ok`, corruption refusal,
retention of two sample snapshots, and final temporary-directory cleanup.
No Pi connection, live Docker daemon or production data was used. Script and
test contents are unchanged from the reviewed archive.

Authenticated implementation-branch creation also succeeded September 29.
The historical write-access limitation below is resolved for that operation;
see [access and delivery](access-and-delivery.md).

## Historical September 28 Windows verification

Test host: local Windows development workspace. Interpreter:
Python 3.12.14. No Pi connection or Docker daemon was used for these tests.

## Source provenance and integration

- Starting repository: `https://github.com/finntucky1/homelab`, main commit
  `6d78c043caba808e78c5790a24f171432fa2745c`, containing only `README.md`.
- The fresh clone had no local changes. Work used the separate branch
  `codex/homelab-operations-2026-09-23`.
- Retrieved the owner-supplied `homelab-starter.zip` through authenticated Drive
  access. SHA-256:
  `e70c440f803099b9d8011ab9e199b07d237262aa483c4af27b6bfc8a92924f02`.
- Inspected all 14 ZIP entries before integration; no AGENTS instructions, live
  Compose YAML, host outputs, or administrative handoff was present.
- Reran the original starter suite before modifying its healthcheck: seven
  tests passed. Documentation and scripts were then improved in this checkout.

## Final local checks

The existing implementation commit `447034079e5a7115930f939f014cec504a14c7fb`
was clean when this recheck began. No script or test behavior changed in the
recheck; the updates clarify documentation and refresh access and test evidence.

Commands below use `python3` for portability. The local run used the bundled
Python executable rather than a `python3` alias.

| Command or check | Observed result | What it establishes |
| --- | --- | --- |
| `python3 -m unittest discover -s tests -v` | 28 run, 26 passed, 2 skipped, zero failures; exit 0 | 14 healthcheck tests plus 12 executed backup tests |
| `python3 scripts/backup_lab.py --json` | PASS, exit 0 | Three synthetic snapshots; isolated two-row SQLite restore; hashes and integrity; retention removes one old sample; damage refused; generated workspace cleaned |
| `python3 scripts/healthcheck.py --help` | exit 0 | CLI imports and documented options available |
| Python 3.8 syntax parsing | All four script/test Python files accepted | Syntax compatibility only; no 3.8 runtime execution |
| Markdown local-link review and `git diff --check` | Passed | Local targets exist; no whitespace errors |
| Ignore-rule spot checks | Sensitive/runtime paths ignored; `.env.example` allowed | Representative ignore coverage only, not secret detection |
| Source/diff review | Completed, including independent script/doc review | No live deployment configurations or private data added |

The skipped cases are POSIX mode verification on Windows and real symbolic-link
creation, which the host did not permit. Neither case is reported as passed.
Windows ACLs were not audited. Linux/Pi runtime behavior remains to be checked.

Healthcheck tests cover free-space thresholds, absent paths/mounts, missing CLI,
empty inventory, required-container absence and exact names, stopped/restarting/
unhealthy/no-health states, malformed/duplicate/undecodable Docker output,
timeouts, argument validation, and JSON/exit behavior. Docker responses are
simulated; a successful test run is not a live health report.

Backup tests cover a consistent SQLite snapshot after later source changes,
hash damage, malformed/unsafe manifests, refusal to overwrite an existing
restore, retention preflight, identifier limits, cleanup, sanitized errors,
and rejection of a live source CLI option. See the fuller
[sample restore record](../backups/restore-test.md).

## Limitations and blocked acceptance criteria

- Actual Compose, storage identity/mappings, ownership, network exposure,
  health-probe coverage, log retention, and recovery dependencies are unverified.
- The owner chose sanitized output collection and disposable testing only.
  Production destination, scope, retention, encryption, notifications and
  recovery objectives are undecided. No live backup job or application restore
  was implemented or claimed.
- No schedule, alert delivery, offsite copy, power-loss recovery, uptime, RPO,
  RTO, or real application availability was measured.
- GitHub branch and issue writes were rechecked on 2026-09-27 and rejected with
  HTTP 403 despite successful reads. HTTPS push also lacked an authenticated local login. See
  [access-and-delivery.md](access-and-delivery.md). A local patch and
  source archive provide the change set; a remote PR is not claimed.
- Administrative automation is separate private work. Its inputs, records and
  implementation status are not part of this public verification record.
