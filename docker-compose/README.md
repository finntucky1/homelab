# Current and historical Compose review evidence

The September 30 direct [live audit](../docs/live-audit-2026-09-30.md#compose-status)
located both current source files under /mnt/storage/omnieye/compose and compared
image, mount and restart declarations with eleven labeled running containers.
[live-apps.review.compose.json](live-apps.review.compose.json) has seven services;
[live-stack.review.compose.json](live-stack.review.compose.json) has eleven.
npm's original source remains unknown. Full deployment invocation/override order
is not retained; do not deploy these selected sanitized copies.

STORAGE_ROOT represents /mnt/storage and APP_CONFIG_ROOT represents
/srv/omnieye/config. Reviewed identity/timezone values are retained; other
environment values require private placeholders. Actual nonempty commands,
networks, ports, mounts and privileged flags are selected from source. Syntax
passed config --quiet with synthetic environment values. Syntax does not prove
reproducibility or authorize starting/replacing the stack.

## Historical four-service candidate

[observed.compose.yaml](observed.compose.yaml) is a sanitized **review copy**
of the privately inspected four-service source on September 29, 2026. It keeps
the observed path inconsistency so review evidence matches the original.
It is not a corrected deployment or permission to start a duplicate stack.

The private original passed single-file config --quiet. Its .bak sibling also
declares the same four services. Newer runtime creation labels identify a different source: this candidate does
not establish the running stack. Full original file/override order and current
versions remain to be reviewed. See [runtime follow-up](../docs/pi-runtime-follow-up.md).

Only STORAGE_ROOT is parameterized to preserve relationships without importing
private files. For offline syntax review from the repository root:

```sh
STORAGE_ROOT=/mnt/storage docker compose -f docker-compose/observed.compose.yaml config --quiet
```

This does not start containers or confirm mount identity, permissions, health
or exposure. No secrets/environment files were copied or rendered into Git.

See [inventory](../docs/inventory.md) for persistent paths and
[prepared follow-ups](../docs/prepared-changes.md) for withdrawal of the earlier
candidate bind edit. Configuration and app-supported exports belong in private backups;
runtime DBs, keys and backup archives do not belong in this public repository.
