# Four weeks of practical study

Exercise sequence for four weeks, weekdays
**4–5 PM America/Los_Angeles**. Use dates/statuses in the existing private tracker;
this guide does not reschedule sessions. The earlier October 5–30 proposal is
superseded by the owner's existing plan. No event or job is created here.
Each session: 10 minutes understand, 35 minutes exercise, 15 minutes record and
explain. Existing agent-created artifacts shorten setup; they do not mark the
learner complete. Leave completion open until an artifact/test supports it.

| Week | Monday | Tuesday | Wednesday | Thursday | Friday |
| --- | --- | --- | --- | --- | --- |
| 1: Linux/inventory | Reproduce OS/architecture/memory checks | Trace lsblk, df, mount and fstab roles without edits | Inspect numeric permissions and explain PUID vs effective process ID | Compare --path with --mount on a temporary directory; simulate missing storage | Write inventory addendum and explain one uncertainty |
| 2: Networking/containers | Trace one declared port and LAN/VPN policy | After authorized access, reconcile runtime source/images/networks | Distinguish DNS, TCP, HTTP and authentication using bounded checks | Reproduce simulated HTTP/denied-tool failure; analyze Radarr path mappings | Write incident worksheet with hypotheses and disconfirming evidence |
| 3: Backup/recovery | Map config, secrets, DB and media recovery needs | Re-run synthetic SQLite lab; explain online-backup API | Back up generated static config with backup_config.py | Corrupt only a generated snapshot; prove restore refusal and no overwrite | Document real Radarr proof boundaries and independent-destination decision |
| 4: Monitoring/automation | Tune justified thresholds against retained observations | Create one-shot private report; verify JSON and exit code | Re-run identical fixture reporting to check dedup; simulate stale marker | Review timer/crontab duplication and rollback; enable only if separately approved | Write a two-minute case study and maintenance handoff |

## Weekly deliverables and completion gates

| Week | Useful homelab result | Safe troubleshooting exercise | Documentation | Interview explanation | Evidence needed |
| --- | --- | --- | --- | --- | --- |
| 1 | Your reproduced current inventory | Ordinary directory fails required-mount check | Dated fact/source/unknown table | Why capacity and mount identity differ | Sanitized command results and two reports |
| 2 | Verified client-to-app/network/path worksheet | Simulated DNS/HTTP/authentication distinction; no live outage injection | Incident record with tested/disproved hypotheses | Why a running container and 401 response prove different things | Runtime evidence where authorized, fixture tests elsewhere |
| 3 | Supported recovery source/destination plan | Generated corruption and existing-target refusal | Restore scope, consistency, permissions and failure risks | Bytes vs DB integrity vs application recovery | Your lab reports; app startup only if actually approved/tested |
| 4 | Repeatable private health collection and response guide | Generated stale/invalid marker and incomplete bundle | Threshold rationale, scheduler decision and maintenance handoff | How unknowns and meaningful exit codes prevent false green | Reports/tests and your own recorded explanation |

Current completion: agent verified the host/storage baseline, created scripts
and exercised both synthetic and real-archive isolated recovery. Learner
reproduction and all live deployment/network/scheduling acceptance gates remain
open. No exercise should stop a live container, alter mounts, launch downloads,
or expose services. Keep reports and personal study records outside public Git.
