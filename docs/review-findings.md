# Repository and live-system review

Reviewed on 2026-09-23. This review covers the repository and the supplied
starter material. No Pi shell, live Compose definitions, container inspection,
storage-permission output or gateway rules were available. Hardware and service
names remain owner-reported. GitHub access is not access to the Pi.

The rows below record evidence gaps, not discovered live-system defects.
Import only sanitized material using [the collection guide](pi-evidence.md).

| Priority / area | Evidence available | What remains unverified | Acceptance evidence |
| --- | --- | --- | --- |
| P0 / Compose and service inventory | `docker-compose/README.md` defines an import process; no live stack YAML is present. `docs/inventory.md` labels services as reported. | Actual services, image versions/digests, overrides, profiles, dependencies, restart policy, privileges and deployment owner. | Sanitized source and all overrides with load order; selective runtime inspection; same-file-order validation; differences between source and runtime explained. |
| P0 / Storage and mappings | Documentation identifies reported NVMe boot storage and an external SSD. | Actual source paths, bind mounts versus named volumes, capacity, filesystem boundaries, required mounts at startup and shared media/download paths. | Device/mount/capacity output mapped to each persistent service path; reviewed mount persistence and startup dependencies; absent-storage behavior assessed before deployment changes. |
| P0 / Recovery destination and consistency | The repository describes recovery requirements and provides local rehearsal material; see `backups/README.md` and its restore record. | An agreed independent destination, live source set, application export/backup capability, ownership, retention and observed recovery of any reported service. | Agreed source/destination/retention; consistency procedure for each writer; approved isolated application restore with data checks and measured time; failure notification demonstrated. |
| P1 / Permissions | No numeric ownership, ACL or effective application-user evidence has been supplied. | Whether configuration, downloads and media are accessible to the intended services with appropriate rights. | Bind-path mode/UID/GID and parent traversal checks, configured and effective application identity, ACL/user-namespace review where relevant. Fix only a demonstrated mismatch. |
| P1 / Network exposure | Network components and WireGuard are reported in `networking/README.md`. | Listening/bound addresses, network modes, firewall/forwarding rules, IPv6 reachability, UPnP and intended LAN/VPN access. | Service access matrix reconciled with bind addresses and gateway rules; authorized reachability tests from intended and prohibited network roles. No public exposure is authorized by this review. |
| P1 / Health and monitoring | `scripts/healthcheck.py` reads capacity and Docker state; unit tests exercise simulated inputs. | Real container health checks, application readiness, endpoint access, alert delivery and host telemetry. | Sanitized health definitions reviewed without credentials; observed application checks plus documented warning/failure delivery. Local tests cannot establish live health or uptime. |
| P1 / Logging | A selective inspection command is provided; no live log-driver configuration has been supplied. | Actual per-container drivers, rotation limits, log growth, retention and notification requirements. | Per-container driver/rotation evidence, relevant daemon defaults and a suitable retention decision. Check application-managed logs separately. |

## How evidence will change recommendations

Check the full stack's path relationships before suggesting new mappings:
renaming a container path can break a dependent service even when the underlying
files remain present. Ownership fields alone are insufficient for a permission
fix; the application may run as a different identity than the configured
container entrypoint. Avoid blanket recursive ownership changes.

Review published addresses together with network mode, Docker version and the
gateway policy. Docker publishes ports on host interfaces according to their
binding; actual Internet reachability requires further routing and firewall
evidence. A loopback binding also needs version-aware review. These distinctions
come from [Docker's port-publishing documentation](https://docs.docker.com/engine/network/port-publishing/);
no particular exposure has been observed here.

For logging, inspect each existing container rather than assuming the current
daemon default applies to it. Docker documents that changed daemon defaults
apply to newly created containers, and `json-file` does not rotate by default.
This is a review criterion, not a claim about this Pi. See
[Docker logging configuration](https://docs.docker.com/engine/logging/configure/).

Choose an application-consistent method only after the actual application
version and data locations are known. A successful snapshot and restore rehearsal
with disposable files proves the tested sample workflow; it cannot prove that a
live application database can be recovered, that VPN access can be restored,
or that a whole host can be rebuilt. Track each separately in
[the restore record](../backups/restore-test.md).

## Decision boundary

Repository improvements and safe local tests may proceed now. Live service
changes, installations on the Pi, reboots, deletions and public exposure need
explicit approval with a concrete change and rollback plan. No such changes
were performed during this review. The next input is sanitized Pi evidence and
an agreed backup destination; service-specific configuration fixes remain
blocked until that evidence supports them.
