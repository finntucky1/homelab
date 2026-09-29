"""Exercise sample recovery, rejection paths, and confinement; no live inputs."""

import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sqlite3
import stat
import unittest
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location(
    "backup_lab", Path(__file__).resolve().parents[1] / "scripts" / "backup_lab.py"
)
backup_lab = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(backup_lab)


class BackupLabTests(unittest.TestCase):
    def test_complete_disposable_demo(self):
        report = backup_lab.run_demo()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["restored_rows"], 2)
        self.assertEqual(report["retention_removed"], 1)
        self.assertTrue(report["corruption_refused_before_restore"])
        self.assertTrue(report["temporary_workspace_removed"])
        self.assertFalse(report["live_sources_accessed"])
        self.assertFalse(report["production_recovery_tested"])

    def test_sqlite_snapshot_is_consistent_and_independent(self):
        with backup_lab.SyntheticLab() as lab:
            self.assertEqual(lab.database.execute("PRAGMA journal_mode").fetchone()[0], "wal")
            lab.snapshot(1)
            lab.database.execute("INSERT INTO items (title) VALUES ('later sample')")
            lab.database.commit()
            restored = lab.restore(1)
            with contextlib.closing(sqlite3.connect(str(restored / "catalog.sqlite3"))) as db:
                self.assertEqual(db.execute("SELECT count(*) FROM items").fetchone()[0], 2)
            self.assertEqual(lab.database.execute("SELECT count(*) FROM items").fetchone()[0], 3)

    def test_corruption_fails_before_restore_writes(self):
        with backup_lab.SyntheticLab() as lab:
            snapshot = lab.snapshot(1)
            (snapshot / "settings.json").write_text("corrupted sample", encoding="utf-8")
            with self.assertRaises(backup_lab.LabError):
                lab.restore(1)
            self.assertEqual(list(lab.restores.iterdir()), [])

    def test_manifest_cannot_add_external_paths(self):
        with backup_lab.SyntheticLab() as lab:
            snapshot = lab.snapshot(1)
            manifest = json.loads((snapshot / "manifest.json").read_text(encoding="utf-8"))
            manifest["files"]["../outside"] = {"bytes": 0, "sha256": "ignored"}
            (snapshot / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaises(backup_lab.LabError):
                lab.restore(1)
            self.assertEqual(list(lab.restores.iterdir()), [])

    def test_invalid_manifest_fails_cleanly(self):
        for content in ("not json", "[]", '{"schema": 2, "files": {}}'):
            with self.subTest(content=content), backup_lab.SyntheticLab() as lab:
                snapshot = lab.snapshot(1)
                (snapshot / "manifest.json").write_text(content, encoding="utf-8")
                with self.assertRaises(backup_lab.LabError):
                    lab.verify(1)

    def test_restore_does_not_overwrite_existing_directory(self):
        with backup_lab.SyntheticLab() as lab:
            lab.snapshot(1)
            destination = lab.restore(1)
            sentinel = destination / "sentinel.txt"
            sentinel.write_text("keep", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                lab.restore(1)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")

    def test_retention_keeps_two_and_refuses_unknown_entries(self):
        with backup_lab.SyntheticLab() as lab:
            for generation in (1, 2, 3):
                lab.snapshot(generation)
            sentinel = lab.snapshots / "unrecognized.txt"
            sentinel.write_text("keep", encoding="utf-8")
            with self.assertRaises(backup_lab.LabError):
                lab.retain(2)
            self.assertTrue(all(lab._snapshot_path(g).exists() for g in (1, 2, 3)))
            sentinel.unlink()
            self.assertEqual(lab.retain(2), [1])
            self.assertEqual(sorted(path.name for path in lab.snapshots.iterdir()), ["snapshot-0002", "snapshot-0003"])

    def test_retention_validates_all_before_deleting(self):
        with backup_lab.SyntheticLab() as lab:
            for generation in (1, 2, 3):
                lab.snapshot(generation)
            (lab._snapshot_path(3) / "settings.json").write_text("damage", encoding="utf-8")
            with self.assertRaises(backup_lab.LabError):
                lab.retain(2)
            self.assertTrue(lab._snapshot_path(1).is_dir())

    def test_path_identifiers_and_zero_retention_rejected(self):
        with backup_lab.SyntheticLab() as lab:
            for value in ("../outside", 0, -1, 10000, True):
                with self.subTest(value=value), self.assertRaises(backup_lab.LabError):
                    lab.snapshot(value)
            with self.assertRaises(backup_lab.LabError):
                lab.retain(0)

    def test_symbolic_link_file_refused(self):
        with backup_lab.SyntheticLab() as lab:
            snapshot = lab.snapshot(1)
            sample = snapshot / "settings.json"
            sample.unlink()
            try:
                sample.symlink_to(lab.source / "settings.json")
            except OSError:
                self.skipTest("This host does not permit creating symbolic links.")
            with self.assertRaises(backup_lab.LabError):
                lab.restore(1)

    @unittest.skipUnless(os.name == "posix", "POSIX mode checks require POSIX; Windows ACLs are not established.")
    def test_private_posix_permissions(self):
        with backup_lab.SyntheticLab() as lab:
            snapshot = lab.snapshot(1)
            restored = lab.restore(1)
            for directory in (lab.root, lab.source, lab.snapshots, lab.restores, snapshot, restored):
                self.assertEqual(stat.S_IMODE(directory.stat().st_mode), 0o700)
            for directory in (snapshot, restored):
                for path in directory.iterdir():
                    self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)

    def test_cleanup_after_failure(self):
        with self.assertRaises(backup_lab.LabError):
            with backup_lab.SyntheticLab() as lab:
                root = lab.root
                raise backup_lab.LabError("sample failure")
        self.assertFalse(root.exists())

    def test_sanitized_failure_report_and_exit_code(self):
        output = io.StringIO()
        with patch.object(backup_lab, "run_demo", side_effect=OSError("private-path-secret")), contextlib.redirect_stdout(output):
            code = backup_lab.main(["--json"])
        report = json.loads(output.getvalue())
        self.assertEqual(code, 2)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("temporary-directory", report["detail"])
        self.assertNotIn("private-path-secret", output.getvalue())

    def test_cli_rejects_live_source_option(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as exc:
            backup_lab.main(["--source", "production"])
        self.assertEqual(exc.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
