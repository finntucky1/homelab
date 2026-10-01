# Historical candidate Compose source

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
