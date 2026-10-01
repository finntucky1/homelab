#!/usr/bin/env python3
"""Exercise backup concepts on generated, disposable data only (Python 3.8+)."""

import argparse
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import stat
import sys
import tempfile


DATA_FILES = ("settings.json", "catalog.sqlite3")
SNAPSHOT_FILES = frozenset(DATA_FILES + ("manifest.json",))
MAX_SAMPLE_BYTES = 1024 * 1024


class LabError(Exception):
    """A safe-to-display failure in the synthetic exercise."""


def private_directory(path):
    path.mkdir(mode=0o700)
    if os.name == "posix":
        path.chmod(0o700)


def private_file(path):
    if os.name == "posix":
        path.chmod(0o600)


def file_record(path):
    if path.is_symlink() or not stat.S_ISREG(path.stat().st_mode):
        raise LabError("Sample validation failed: expected a regular file.")
    if path.stat().st_size > MAX_SAMPLE_BYTES:
        raise LabError("Sample validation failed: a file exceeds the sample size limit.")
    with path.open("rb") as handle:
        data = handle.read(MAX_SAMPLE_BYTES + 1)
    if len(data) > MAX_SAMPLE_BYTES:
        raise LabError("Sample validation failed: a file exceeds the sample size limit.")
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


class SyntheticLab:
    """Own a new temporary workspace; never accept a user's source/destination."""

    def __enter__(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="homelab-backup-demo-")
        self.root = Path(self.temporary.name).resolve()
        self.source = self.root / "synthetic-source"
        self.snapshots = self.root / "snapshots"
        self.restores = self.root / "isolated-restores"
        self.database = None
        try:
            if os.name == "posix":
                self.root.chmod(0o700)
            for path in (self.source, self.snapshots, self.restores):
                private_directory(path)
            settings = self.source / "settings.json"
            settings.write_text('{"sample": true, "name": "disposable-library"}\n', encoding="utf-8")
            private_file(settings)
            self.database = sqlite3.connect(str(self.source / "catalog.sqlite3"))
            self.database.execute("PRAGMA journal_mode=WAL")
            self.database.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, title TEXT NOT NULL)")
            self.database.executemany("INSERT INTO items (title) VALUES (?)", [("Sample A",), ("Sample B",)])
            self.database.commit()
            for path in self.source.iterdir():
                private_file(path)
            return self
        except Exception:
            self.__exit__(None, None, None)
            raise

    def __exit__(self, *unused):
        if self.database is not None:
            self.database.close()
        self.temporary.cleanup()

    def _snapshot_path(self, generation):
        if type(generation) is not int or not 1 <= generation <= 9999:
            raise LabError("Choose a sample generation between 1 and 9999.")
        if self.snapshots.is_symlink() or self.snapshots.resolve() != self.root / "snapshots":
            raise LabError("Sample workspace changed; refusing to access snapshots.")
        path = self.snapshots / "snapshot-{:04d}".format(generation)
        if path.is_symlink() or path.resolve().parent != self.snapshots:
            raise LabError("Sample snapshot boundary check failed.")
        return path

    def snapshot(self, generation):
        """Snapshot a static fixture and a committed SQLite database via its API."""
        target = self._snapshot_path(generation)
        private_directory(target)
        shutil.copyfile(str(self.source / "settings.json"), str(target / "settings.json"))
        with closing(sqlite3.connect(str(target / "catalog.sqlite3"))) as destination:
            self.database.backup(destination)
        manifest = {"schema": 1, "files": {}}
        for name in DATA_FILES:
            private_file(target / name)
            manifest["files"][name] = file_record(target / name)
        (target / "manifest.json").write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")
        private_file(target / "manifest.json")
        self.verify(generation)
        return target

    def verify(self, generation):
        target = self._snapshot_path(generation)
        if not target.is_dir() or {entry.name for entry in target.iterdir()} != SNAPSHOT_FILES:
            raise LabError("Sample validation failed: missing or unexpected snapshot files.")
        file_record(target / "manifest.json")
        try:
            manifest = json.loads((target / "manifest.json").read_text(encoding="utf-8"))
        except (ValueError, UnicodeError, RecursionError):
            raise LabError("Sample validation failed: unreadable manifest.") from None
        if (not isinstance(manifest, dict) or set(manifest) != {"schema", "files"}
                or type(manifest["schema"]) is not int or manifest["schema"] != 1 or not isinstance(manifest["files"], dict)
                or set(manifest["files"]) != set(DATA_FILES)):
            raise LabError("Sample validation failed: unexpected manifest structure.")
        for name in DATA_FILES:
            record = manifest["files"][name]
            if (not isinstance(record, dict) or set(record) != {"bytes", "sha256"}
                    or type(record["bytes"]) is not int or not 0 <= record["bytes"] <= MAX_SAMPLE_BYTES
                    or not isinstance(record["sha256"], str) or len(record["sha256"]) != 64
                    or any(char not in "0123456789abcdef" for char in record["sha256"])):
                raise LabError("Sample validation failed: invalid file record.")
            if record != file_record(target / name):
                raise LabError("Sample integrity check failed; recreate the disposable snapshot.")
        return manifest

    def restore(self, generation):
        """Restore only after checking all files, into a new isolated directory."""
        manifest = self.verify(generation)
        source = self._snapshot_path(generation)
        if self.restores.is_symlink() or self.restores.resolve() != self.root / "isolated-restores":
            raise LabError("Sample workspace changed; refusing to restore.")
        target = self.restores / "restore-{:04d}".format(generation)
        private_directory(target)  # Fails instead of overwriting an existing restore.
        for name in DATA_FILES:
            shutil.copyfile(str(source / name), str(target / name))
            private_file(target / name)
            if file_record(target / name) != manifest["files"][name]:
                raise LabError("Restored sample differs from its manifest; do not use it.")
        with closing(sqlite3.connect(str(target / "catalog.sqlite3"))) as restored:
            integrity = restored.execute("PRAGMA integrity_check").fetchone()[0]
            rows = restored.execute("SELECT id, title FROM items ORDER BY id").fetchall()
        if integrity != "ok" or rows != [(1, "Sample A"), (2, "Sample B")]:
            raise LabError("Restored sample database failed integrity or expected-content checks.")
        return target

    def retain(self, keep=2):
        """Remove old verified snapshots in this generated workspace only."""
        if type(keep) is not int or keep < 1:
            raise LabError("Sample retention must keep at least one snapshot.")
        self._snapshot_path(1)  # Check ownership boundary before listing.
        generations = []
        for entry in self.snapshots.iterdir():
            name = entry.name
            if len(name) != 13 or not name.startswith("snapshot-") or not name[9:].isdigit():
                raise LabError("Unexpected sample snapshot entry; refusing retention.")
            generation = int(name[9:])
            self.verify(generation)  # Validate ALL snapshots before any deletion.
            generations.append(generation)
        generations.sort()
        expired = generations[:-keep]
        for generation in expired:
            shutil.rmtree(str(self._snapshot_path(generation)))
        return expired


def run_demo():
    with SyntheticLab() as lab:
        for generation in (1, 2, 3):
            lab.snapshot(generation)
        restored = lab.restore(3)
        restored_hashes = {name: file_record(restored / name)["sha256"] for name in DATA_FILES}
        expired = lab.retain(2)
        # Deliberate damage must be refused before a restore directory is made.
        damaged = lab._snapshot_path(2) / "settings.json"
        damaged.write_text("deliberately damaged disposable sample\n", encoding="utf-8")
        try:
            lab.restore(2)
        except LabError:
            corruption_refused = not (lab.restores / "restore-0002").exists()
        else:
            corruption_refused = False
        if not corruption_refused or expired != [1]:
            raise LabError("A sample safety check failed; inspect the tests before using the example.")
        report = {
            "status": "PASS", "scope": "generated disposable data only", "exit_code": 0,
            "snapshots_created": 3, "retention_kept": 2, "retention_removed": len(expired),
            "sqlite_backup_api": True, "sqlite_integrity_check": "ok", "restored_rows": 2,
            "restored_sha256": restored_hashes, "corruption_refused_before_restore": corruption_refused,
            "permissions": "POSIX directories 0700, files 0600" if os.name == "posix" else "Windows inherited ACL; not independently verified",
            "live_sources_accessed": False, "production_recovery_tested": False,
        }
    report["temporary_workspace_removed"] = True
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit a sanitized JSON result")
    args = parser.parse_args(argv)
    try:
        report = run_demo()
    except (LabError, OSError, sqlite3.Error) as exc:
        # OS/database exception strings can contain private paths; never echo them.
        detail = str(exc) if isinstance(exc, LabError) else "Check temporary-directory access, available space, and Python SQLite support."
        report = {"status": "FAIL", "scope": "generated disposable data only", "exit_code": 2,
                  "error_type": type(exc).__name__, "detail": detail}
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("{}: disposable backup/restore exercise".format(report["status"]))
        print(report.get("detail", "SQLite restore, file hashes, corruption refusal, and sample retention passed; temporary data removed."))
        print("This does not establish recovery of the live Pi or its applications.")
    return report["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
