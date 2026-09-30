#!/usr/bin/env python3
"""Private, keep-all snapshots of explicit static files or completed app exports.

Python 3.8+, POSIX only. This never opens databases, walks source directories,
extracts archives, starts applications, prunes snapshots, or schedules work.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import stat
import sys


MAX_FILES = 64
MAX_FILE_BYTES = 256 * 1024 * 1024
MAX_TOTAL_BYTES = 512 * 1024 * 1024
MAX_MANIFEST_BYTES = 64 * 1024
CHUNK_BYTES = 64 * 1024
NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
CONFIG_SUFFIXES = (".json", ".yaml", ".yml", ".conf", ".ini", ".xml", ".toml", ".txt", ".env", ".service")
EXPORT_SUFFIXES = (".zip", ".tar", ".tar.gz", ".tgz")
KINDS = ("static-config", "application-export")


class BackupError(Exception):
    """Error messages are fixed text and safe for public logs."""


class SafeParser(argparse.ArgumentParser):
    def error(self, unused):
        raise BackupError("Invalid command arguments; use --help.")


def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def valid_time(value):
    if not isinstance(value, str):
        raise BackupError("Snapshot timestamp is invalid.")
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        raise BackupError("Snapshot timestamp is invalid.") from None
    if parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != value or parsed > datetime.now(timezone.utc):
        raise BackupError("Snapshot timestamp is invalid or in the future.")
    return parsed


def safe_name(value):
    if not isinstance(value, str) or not NAME.fullmatch(value):
        raise BackupError("Use a simple alphanumeric identifier with underscores or hyphens.")
    return value


def safe_path(value, exists=True):
    """Require absolute paths and refuse symlinks in every existing component."""
    if os.name != "posix" or not hasattr(os, "O_NOFOLLOW"):
        raise BackupError("This tool requires POSIX permissions and no-follow file support.")
    path = Path(value)
    if not path.is_absolute() or ".." in path.parts:
        raise BackupError("Use an absolute path without parent traversal.")
    if path == Path("/") or path.parts[1] in ("proc", "sys", "dev", "run") or Path("/var/run") in path.parents:
        raise BackupError("Refusing a filesystem root or runtime pseudo-filesystem.")
    for component in (path,) + tuple(path.parents):
        try:
            info = component.lstat()
        except FileNotFoundError:
            if component == path and not exists:
                continue
            raise BackupError("Required path or parent is missing.") from None
        if stat.S_ISLNK(info.st_mode):
            raise BackupError("Symbolic links are refused in all path components.")
    return path


def private_dir(value):
    path = safe_path(value)
    info = path.stat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) != 0o700:
        raise BackupError("Directory must already be owned by this user with mode 0700.")
    return path


def new_path(value):
    path = safe_path(value, exists=False)
    private_dir(path.parent)
    if path.exists() or path.is_symlink():
        raise BackupError("Target already exists; refusing to overwrite it.")
    return path


def overlaps(first, second):
    return first == second or first in second.parents or second in first.parents


def stamp(info):
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def read_regular(path, writer=None, private=False, max_bytes=MAX_FILE_BYTES):
    """Bounded stable reads; detect common changes, without claiming app consistency."""
    safe_path(path)
    fd = os.open(str(path), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as handle:
        before = os.fstat(handle.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_size > max_bytes:
            raise BackupError("Expected a regular file within the size limit.")
        if private and (before.st_uid != os.geteuid() or stat.S_IMODE(before.st_mode) != 0o600):
            raise BackupError("Snapshot files must be owned by this user with mode 0600.")
        digest = hashlib.sha256()
        size = 0
        header = b""
        while True:
            chunk = handle.read(CHUNK_BYTES)
            if not chunk:
                break
            if not size:
                header = chunk[:16]
            size += len(chunk)
            if size > max_bytes:
                raise BackupError("File grew beyond the size limit.")
            if writer is not None:
                writer.write(chunk)
            digest.update(chunk)
        if stamp(before) != stamp(os.fstat(handle.fileno())) or stamp(before) != stamp(path.stat()) or size != before.st_size:
            raise BackupError("Input changed during reading; use a completed static input.")
    return {"bytes": size, "sha256": digest.hexdigest()}, header


def write_new(path, content):
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as handle:
        os.fchmod(handle.fileno(), 0o600)
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())


def copy_new(source, destination, private=False):
    fd = os.open(str(destination), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as handle:
        os.fchmod(handle.fileno(), 0o600)
        record, header = read_regular(source, writer=handle, private=private)
        handle.flush()
        os.fsync(handle.fileno())
    return record, header


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode("utf-8")


def create(destination, snapshot_id, inputs, input_kind, consistent_inputs=False):
    if not consistent_inputs:
        raise BackupError("Explicitly acknowledge inputs are static or completed supported exports.")
    safe_name(snapshot_id)
    if input_kind not in KINDS or not isinstance(inputs, dict) or not 1 <= len(inputs) <= MAX_FILES:
        raise BackupError("Choose a supported input kind and between 1 and 64 explicit files.")
    destination = private_dir(destination)
    target = new_path(destination / snapshot_id)
    sources = {}
    total = 0
    for label, value in inputs.items():
        safe_name(label)
        source = safe_path(value)
        if overlaps(destination, source.parent):
            raise BackupError("Destination and source directories must be separate and non-overlapping.")
        suffixes = CONFIG_SUFFIXES if input_kind == "static-config" else EXPORT_SUFFIXES
        if not source.name.lower().endswith(suffixes):
            raise BackupError("Unsupported input extension; databases and runtime data are refused.")
        record, header = read_regular(source)
        if header == b"SQLite format 3\x00":
            raise BackupError("SQLite databases are refused; use the application's supported export.")
        total += record["bytes"]
        if total > MAX_TOTAL_BYTES:
            raise BackupError("Selected input files exceed the total size limit.")
        sources[label] = (source, record)
    if shutil.disk_usage(str(destination)).free < total + MAX_MANIFEST_BYTES:
        raise BackupError("Destination has insufficient free space for the selected inputs.")
    target.mkdir(mode=0o700)
    target.chmod(0o700)
    (target / "files").mkdir(mode=0o700)
    (target / "files").chmod(0o700)
    manifest = {"schema": 1, "kind": "config-export-snapshot", "snapshot_id": snapshot_id,
                "input_kind": input_kind, "created_at": utc_now(), "retention": "keep-all", "files": {}}
    for label, (source, expected) in sources.items():
        record, unused_header = copy_new(source, target / "files" / label)
        if record != expected:
            raise BackupError("Input changed after preflight; incomplete snapshot retained for review.")
        manifest["files"][label] = record
    write_new(target / "manifest.json", encoded(manifest))
    verify(target)
    return target


def verify(snapshot):
    snapshot = private_dir(snapshot)
    private_dir(snapshot / "files")
    if {path.name for path in snapshot.iterdir()} != {"manifest.json", "files"}:
        raise BackupError("Snapshot has missing or unexpected entries.")
    manifest_bytes = io.BytesIO()
    read_regular(snapshot / "manifest.json", writer=manifest_bytes, private=True, max_bytes=MAX_MANIFEST_BYTES)
    try:
        manifest = json.loads(manifest_bytes.getvalue().decode("utf-8"))
    except (ValueError, UnicodeError, RecursionError):
        raise BackupError("Manifest is unreadable.") from None
    keys = {"schema", "kind", "snapshot_id", "input_kind", "created_at", "retention", "files"}
    if (not isinstance(manifest, dict) or set(manifest) != keys or type(manifest["schema"]) is not int
            or manifest["schema"] != 1 or manifest["kind"] != "config-export-snapshot"
            or manifest["input_kind"] not in KINDS or manifest["retention"] != "keep-all"
            or not isinstance(manifest["files"], dict) or not 1 <= len(manifest["files"]) <= MAX_FILES):
        raise BackupError("Manifest structure is invalid.")
    safe_name(manifest["snapshot_id"])
    if manifest["snapshot_id"] != snapshot.name:
        raise BackupError("Snapshot identifier does not match its directory.")
    valid_time(manifest["created_at"])
    for label in manifest["files"]:
        safe_name(label)  # Reject traversal before examining files or making restore targets.
    if {path.name for path in (snapshot / "files").iterdir()} != set(manifest["files"]):
        raise BackupError("Payload files do not match the manifest.")
    total = 0
    for label, expected in manifest["files"].items():
        if (not isinstance(expected, dict) or set(expected) != {"bytes", "sha256"}
                or type(expected["bytes"]) is not int or not 0 <= expected["bytes"] <= MAX_FILE_BYTES
                or not isinstance(expected["sha256"], str) or not SHA256.fullmatch(expected["sha256"])):
            raise BackupError("Manifest file record is invalid.")
        record, unused_header = read_regular(snapshot / "files" / label, private=True)
        if record != expected:
            raise BackupError("Snapshot hash or size verification failed.")
        total += record["bytes"]
    if total > MAX_TOTAL_BYTES:
        raise BackupError("Snapshot exceeds the total size limit.")
    return manifest


def restore(snapshot, target, marker=None):
    snapshot = private_dir(snapshot)
    manifest = verify(snapshot)
    target = new_path(target)
    if overlaps(target, snapshot.parent):
        raise BackupError("Restore target must be outside the snapshot destination.")
    if marker is not None:
        marker = new_path(marker)
        if overlaps(marker, snapshot.parent) or overlaps(marker, target):
            raise BackupError("Recovery marker must be outside the snapshot and restore directories.")
    target.mkdir(mode=0o700)
    target.chmod(0o700)
    for label, expected in manifest["files"].items():
        record, unused_header = copy_new(snapshot / "files" / label, target / label, private=True)
        checked, unused_header = read_regular(target / label, private=True)
        if record != expected or checked != expected:
            raise BackupError("Restored bytes failed verification; incomplete restore retained for review.")
    if marker is not None:
        record, unused_header = read_regular(snapshot / "manifest.json", private=True, max_bytes=MAX_MANIFEST_BYTES)
        proof = {"schema": 1, "kind": "config-export-recovery", "status": "verified",
                 "created_at": manifest["created_at"], "recovered_at": utc_now(),
                 "snapshot_id": manifest["snapshot_id"], "manifest_sha256": record["sha256"]}
        write_new(marker, encoded(proof))
    return manifest


def parse_inputs(values):
    inputs = {}
    for value in values:
        if "=" not in value:
            raise BackupError("Provide each explicit file as LABEL=ABSOLUTE_PATH.")
        label, path = value.split("=", 1)
        safe_name(label)
        if label in inputs:
            raise BackupError("Duplicate input labels are refused.")
        inputs[label] = path
    return inputs


def main(argv=None):
    parser = SafeParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="sanitized JSON result; use before the action")
    commands = parser.add_subparsers(dest="action", required=True, parser_class=SafeParser)
    new = commands.add_parser("create", help="snapshot explicit static files or completed exports")
    new.add_argument("--destination", required=True, help="existing user-owned directory, mode 0700")
    new.add_argument("--snapshot-id", required=True, help="new simple identifier; existing entries refused")
    new.add_argument("--input-kind", choices=KINDS, required=True)
    new.add_argument("--file", action="append", required=True, help="LABEL=ABSOLUTE_PATH; repeat per file")
    new.add_argument("--consistent-inputs", action="store_true", help="acknowledge inputs are static or completed app-supported exports")
    check = commands.add_parser("verify", help="check manifest and all snapshot bytes")
    check.add_argument("--snapshot", required=True)
    recover = commands.add_parser("restore", help="restore bytes into a new isolated directory")
    recover.add_argument("--snapshot", required=True)
    recover.add_argument("--target", required=True)
    recover.add_argument("--marker", help="optional new private proof file outside snapshot/restore trees")
    json_output = "--json" in (sys.argv[1:] if argv is None else argv)
    action = "argument-validation"
    try:
        args = parser.parse_args(argv)
        action = args.action
        if action == "create":
            snapshot = create(args.destination, args.snapshot_id, parse_inputs(args.file), args.input_kind, args.consistent_inputs)
            manifest = verify(snapshot)
        elif action == "verify":
            manifest = verify(args.snapshot)
        else:
            manifest = restore(args.snapshot, args.target, args.marker)
        report = {"status": "PASS", "exit_code": 0, "action": action,
                  "scope": "static config/export bytes only; application recovery untested", "retention": "keep-all",
                  "file_count": len(manifest["files"]), "total_bytes": sum(item["bytes"] for item in manifest["files"].values())}
    except (BackupError, OSError) as exc:
        report = {"status": "FAIL", "exit_code": 2, "action": action, "retention": "keep-all",
                  "detail": str(exc) if isinstance(exc, BackupError) else "Filesystem operation failed; check access and space privately."}
    if json_output:
        print(json.dumps(report, sort_keys=True))
    else:
        print("{}: {}".format(report["status"], report.get("detail") or report.get("scope")))
    return report["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
