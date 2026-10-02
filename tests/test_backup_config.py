"""Explicit-file snapshots and refusal cases, using generated fixtures only."""

import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location(
    "backup_config", Path(__file__).resolve().parents[1] / "scripts" / "backup_config.py"
)
backup = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(backup)


@unittest.skipUnless(os.name == "posix" and hasattr(os, "O_NOFOLLOW"), "POSIX no-follow support required")
class ConfigBackupTests(unittest.TestCase):
    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory(prefix="homelab-config-test-")
        self.root = Path(self.workspace.name)
        self.root.chmod(0o700)
        self.source = self.root / "sources"
        self.destination = self.root / "snapshots"
        self.recovery = self.root / "recovery"
        for path in (self.source, self.destination, self.recovery):
            path.mkdir(mode=0o700)
        self.config = self.source / "settings.json"
        self.config.write_text('{"sample":true}\n', encoding="utf-8")

    def tearDown(self):
        self.workspace.cleanup()

    def snapshot(self, identity="fixture1"):
        return backup.create(self.destination, identity, {"settings": self.config}, "static-config", True)

    def test_snapshot_verify_isolated_restore_and_marker(self):
        snapshot = self.snapshot()
        marker = self.root / "proof.json"
        manifest = backup.restore(snapshot, self.recovery / "fixture1", marker)
        self.assertEqual((self.recovery / "fixture1" / "settings").read_bytes(), self.config.read_bytes())
        proof = json.loads(marker.read_text(encoding="utf-8"))
        self.assertEqual(set(proof), {"schema", "kind", "status", "snapshot_id", "created_at", "recovered_at", "manifest_sha256"})
        self.assertEqual(proof["status"], "verified")
        self.assertEqual(proof["kind"], "config-export-recovery")
        self.assertEqual(proof["created_at"], manifest["created_at"])
        self.assertGreaterEqual(proof["recovered_at"], proof["created_at"])
        self.assertEqual(proof["manifest_sha256"], backup.read_regular(snapshot / "manifest.json")[0]["sha256"])
        for path in (snapshot, snapshot / "files", self.recovery / "fixture1"):
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o700)
        for path in (marker, snapshot / "manifest.json", snapshot / "files" / "settings", self.recovery / "fixture1" / "settings"):
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)

    def test_keep_all_and_existing_snapshot_refused(self):
        first = self.snapshot("fixture1")
        self.snapshot("fixture2")
        original = (first / "files" / "settings").read_bytes()
        with self.assertRaises(backup.BackupError):
            self.snapshot("fixture1")
        self.assertEqual(len(list(self.destination.iterdir())), 2)
        self.assertEqual((first / "files" / "settings").read_bytes(), original)
        self.assertEqual(backup.verify(first)["retention"], "keep-all")

    def test_corrupt_snapshot_refuses_restore_before_writes(self):
        snapshot = self.snapshot()
        (snapshot / "files" / "settings").write_bytes(b"corrupted fixture")
        with self.assertRaises(backup.BackupError):
            backup.restore(snapshot, self.recovery / "fixture1", self.root / "proof.json")
        self.assertEqual(list(self.recovery.iterdir()), [])
        self.assertFalse((self.root / "proof.json").exists())

    def test_existing_restore_and_marker_refused(self):
        snapshot = self.snapshot()
        target = self.recovery / "fixture1"
        target.mkdir(mode=0o700)
        sentinel = target / "sentinel"
        sentinel.write_text("keep", encoding="utf-8")
        with self.assertRaises(backup.BackupError):
            backup.restore(snapshot, target)
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")
        marker = self.root / "proof.json"
        marker.write_text("keep", encoding="utf-8")
        with self.assertRaises(backup.BackupError):
            backup.restore(snapshot, self.recovery / "fresh", marker)
        self.assertFalse((self.recovery / "fresh").exists())
        self.assertEqual(marker.read_text(encoding="utf-8"), "keep")

    def test_manifest_traversal_and_invalid_record_refused(self):
        for malformed in ({"../escape": {"bytes": 0, "sha256": "0" * 64}}, {"settings": {"bytes": True, "sha256": "0" * 64}}):
            with self.subTest(malformed=malformed):
                snapshot = self.snapshot("fixture{}".format(len(list(self.destination.iterdir()))))
                manifest = json.loads((snapshot / "manifest.json").read_text(encoding="utf-8"))
                manifest["files"] = malformed
                (snapshot / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
                with self.assertRaises(backup.BackupError):
                    backup.restore(snapshot, self.recovery / "target")
                self.assertFalse((self.recovery / "target").exists())
                self.assertFalse((self.root / "escape").exists())

    def test_missing_destination_refused_and_not_created(self):
        missing = self.root / "missing"
        with self.assertRaises(backup.BackupError):
            backup.create(missing, "fixture", {"settings": self.config}, "static-config", True)
        self.assertFalse(missing.exists())

    def test_deeply_nested_manifest_fails_with_sanitized_json(self):
        snapshot = self.snapshot()
        (snapshot / "manifest.json").write_text("[" * 16000 + "0" + "]" * 16000, encoding="utf-8")
        target = self.recovery / "fixture1"
        for action in (["verify", "--snapshot", str(snapshot)],
                       ["restore", "--snapshot", str(snapshot), "--target", str(target)]):
            with self.subTest(action=action[0]):
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    code = backup.main(["--json"] + action)
                report = json.loads(output.getvalue())
                self.assertEqual(code, 2)
                self.assertEqual(report["status"], "FAIL")
                self.assertEqual(report["detail"], "Manifest is unreadable.")
                self.assertNotIn(str(self.root), output.getvalue())
                self.assertNotIn("Traceback", output.getvalue())
                self.assertFalse(target.exists())

    def test_directory_and_database_inputs_refused(self):
        for name, data in (("running.sqlite3", b"fixture"), ("disguised.json", b"SQLite format 3\x00more")):
            source = self.source / name
            source.write_bytes(data)
            with self.assertRaises(backup.BackupError):
                backup.create(self.destination, "fixture", {"settings": source}, "static-config", True)
        with self.assertRaises(backup.BackupError):
            backup.create(self.destination, "fixture", {"settings": self.source}, "static-config", True)
        self.assertEqual(list(self.destination.iterdir()), [])

    def test_acknowledgement_and_duplicate_input_labels_required(self):
        with self.assertRaises(backup.BackupError):
            backup.create(self.destination, "fixture", {"settings": self.config}, "static-config")
        with self.assertRaises(backup.BackupError):
            backup.parse_inputs(["settings=/fixture/one", "settings=/fixture/two"])
        self.assertEqual(list(self.destination.iterdir()), [])

    def test_dest_source_overlap_and_restore_overlap_refused(self):
        within_source = self.source / "nested"
        within_source.mkdir(mode=0o700)
        with self.assertRaises(backup.BackupError):
            backup.create(within_source, "fixture", {"settings": self.config}, "static-config", True)
        snapshot = self.snapshot()
        with self.assertRaises(backup.BackupError):
            backup.restore(snapshot, self.destination / "restored")
        self.assertFalse((self.destination / "restored").exists())

    def test_symlink_sources_destinations_and_parent_components_refused(self):
        source_link = self.source / "link.json"
        source_link.symlink_to(self.config)
        dest_link = self.root / "destination-link"
        dest_link.symlink_to(self.destination, target_is_directory=True)
        for destination, source in ((self.destination, source_link), (dest_link, self.config)):
            with self.assertRaises(backup.BackupError):
                backup.create(destination, "fixture", {"settings": source}, "static-config", True)
        parent_link = self.root / "source-link"
        parent_link.symlink_to(self.source, target_is_directory=True)
        with self.assertRaises(backup.BackupError):
            backup.create(self.destination, "fixture", {"settings": parent_link / "settings.json"}, "static-config", True)
        self.assertEqual(list(self.destination.iterdir()), [])

    def test_world_readable_destination_or_snapshot_refused_without_repair(self):
        self.destination.chmod(0o755)
        with self.assertRaises(backup.BackupError):
            self.snapshot()
        self.assertEqual(stat.S_IMODE(self.destination.stat().st_mode), 0o755)
        self.destination.chmod(0o700)
        snapshot = self.snapshot()
        (snapshot / "files" / "settings").chmod(0o644)
        with self.assertRaises(backup.BackupError):
            backup.verify(snapshot)

    def test_file_size_count_and_destination_space_refused(self):
        with patch.object(backup, "MAX_FILES", 1), self.assertRaises(backup.BackupError):
            backup.create(self.destination, "fixture", {"one": self.config, "two": self.config}, "static-config", True)
        with patch.object(backup, "MAX_TOTAL_BYTES", 1), self.assertRaises(backup.BackupError):
            self.snapshot()
        with self.assertRaises(backup.BackupError):
            backup.read_regular(self.config, max_bytes=1)
        with patch.object(backup.shutil, "disk_usage", return_value=type("Usage", (), {"free": 1})()), self.assertRaises(backup.BackupError):
            self.snapshot()
        self.assertEqual(list(self.destination.iterdir()), [])

    def test_changed_source_after_preflight_refused_and_no_success_manifest(self):
        original = backup.copy_new
        def change_then_copy(source, destination, private=False):
            source.write_text('{"changed":true}\n', encoding="utf-8")
            return original(source, destination, private)
        with patch.object(backup, "copy_new", side_effect=change_then_copy), self.assertRaises(backup.BackupError):
            self.snapshot()
        self.assertFalse((self.destination / "fixture1" / "manifest.json").exists())
        self.assertTrue((self.destination / "fixture1").is_dir())  # Keep partial output for private review.

    def test_change_during_read_detected_from_metadata(self):
        original_stat = Path.stat
        def mutate_before_final_stat(path, *args, **kwargs):
            # Python 3.12 implements lstat through stat(follow_symlinks=False).
            # Mutate at the final content check, after the opened-file read.
            if path == self.config and kwargs.get("follow_symlinks", True):
                path.write_bytes(b"changed during read")
            return original_stat(path, *args, **kwargs)
        with patch.object(Path, "stat", new=mutate_before_final_stat), self.assertRaises(backup.BackupError):
            backup.read_regular(self.config)

    def test_supported_export_is_opaque_and_never_extracted(self):
        export = self.source / "completed.zip"
        export.write_bytes(b"synthetic opaque export fixture")
        snapshot = backup.create(self.destination, "export1", {"native_export": export}, "application-export", True)
        backup.restore(snapshot, self.recovery / "export1")
        self.assertEqual(list(path.name for path in (self.recovery / "export1").iterdir()), ["native_export"])
        self.assertEqual((self.recovery / "export1" / "native_export").read_bytes(), export.read_bytes())

    def test_manifest_edit_during_restore_prevents_recovery_marker(self):
        snapshot = self.snapshot()
        marker = self.root / "proof.json"
        original = backup.copy_new
        def edit_then_copy(source, destination, private=False):
            path = snapshot / "manifest.json"
            content = path.read_bytes()
            path.write_bytes(content + b" ")  # Equivalent JSON, different manifest digest.
            return original(source, destination, private)
        with patch.object(backup, "copy_new", side_effect=edit_then_copy), self.assertRaises(backup.BackupError):
            backup.restore(snapshot, self.recovery / "fixture1", marker)
        self.assertFalse(marker.exists())
        self.assertEqual((self.recovery / "fixture1" / "settings").read_bytes(), self.config.read_bytes())

    def test_sanitized_failures_exclude_os_details_and_paths(self):
        output = io.StringIO()
        with patch.object(backup, "verify", side_effect=OSError("PRIVATE-CREDENTIAL-PATH")), contextlib.redirect_stdout(output):
            code = backup.main(["--json", "verify", "--snapshot", "/PRIVATE-CREDENTIAL-PATH"])
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(output.getvalue())["status"], "FAIL")
        self.assertNotIn("PRIVATE-CREDENTIAL-PATH", output.getvalue())
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(backup.main(["--json", "--PRIVATE-CREDENTIAL-PATH"]), 2)
        self.assertNotIn("PRIVATE-CREDENTIAL-PATH", output.getvalue())


if __name__ == "__main__":
    unittest.main()
