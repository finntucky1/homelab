"""Verify private report collection without querying a live host."""
import contextlib
import datetime
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location('report_snapshot', SCRIPTS / 'report_snapshot.py')
snapshot = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(snapshot)


def sample_report(code=1, status='UNKNOWN'):
    return {'schema': 1, 'checked_at': '2026-09-29T00:00:00Z', 'exit_code': code,
            'checks': [{'name': 'docker', 'status': status, 'detail': 'Access unavailable.', 'action': ''}]}


class ReportValidationTests(unittest.TestCase):
    def test_health_severities_validate_without_host_probes(self):
        for code, status in ((0, 'PASS'), (1, 'WARN'), (1, 'UNKNOWN'), (2, 'FAIL')):
            with self.subTest(status=status):
                snapshot.validate_report(sample_report(code, status))

    def test_malformed_health_schema_severity_and_timestamp_refused(self):
        cases = [None, [], {}, sample_report(0), dict(sample_report(), schema=True),
                 dict(sample_report(), exit_code=True), dict(sample_report(), checks=[]),
                 dict(sample_report(), checked_at='2026-09-29T00:00:00'),
                 dict(sample_report(), checked_at='2026-9-29T00:00:00Z')]
        for report in cases:
            with self.subTest(report=report), self.assertRaises(ValueError):
                snapshot.validate_report(report)

    def test_collection_timestamp_requires_canonical_utc(self):
        self.assertEqual(snapshot.collection_time('2026-09-29T00:00:00+00:00\n').tzinfo, datetime.timezone.utc)
        for value in ('2026-09-29T00:00:00\n', '2026-09-29T00:00:00-07:00\n',
                      '2026-09-29T00:00:00+00:00', 'garbage'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                snapshot.collection_time(value)

    def test_invalid_health_arguments_are_sanitized_collection_failure(self):
        output = io.StringIO()
        with patch.object(snapshot, 'private_directory'), patch.object(snapshot.healthcheck, 'disk_check') as disk, contextlib.redirect_stderr(output):
            code = snapshot.main(['--output-dir', '/PRIVATE-SECRET', '--', '--min-free-percent', 'PRIVATE-SECRET'])
        self.assertEqual(code, 3)
        self.assertNotIn('PRIVATE-SECRET', output.getvalue())
        disk.assert_not_called()

    def test_collector_argument_errors_are_sanitized(self):
        output = io.StringIO()
        with contextlib.redirect_stderr(output):
            code = snapshot.main(['--PRIVATE-SECRET'])
        self.assertEqual(code, 3)
        self.assertNotIn('PRIVATE-SECRET', output.getvalue())

    def test_malformed_health_report_is_refused_before_save(self):
        def health(args):
            print(json.dumps(sample_report(0)))
            return 0
        with patch.object(snapshot, 'private_directory'), patch.object(snapshot, 'save_report') as save, patch.object(snapshot.healthcheck, 'main', side_effect=health), contextlib.redirect_stderr(io.StringIO()):
            code = snapshot.main(['--output-dir', '/sample'])
        self.assertEqual(code, 3)
        save.assert_not_called()

    def test_warning_and_failure_exit_codes_propagate(self):
        for code, status in ((1, 'UNKNOWN'), (2, 'FAIL')):
            def health(args):
                print(json.dumps(sample_report(code, status)))
                return code
            with self.subTest(status=status), patch.object(snapshot, 'private_directory'), patch.object(snapshot, 'save_report', return_value=(None, False)), patch.object(snapshot.healthcheck, 'main', side_effect=health), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(snapshot.main(['--output-dir', '/sample']), code)


@unittest.skipUnless(os.name == 'posix', 'Private POSIX reports require POSIX.')
class ReportSnapshotTests(unittest.TestCase):
    def report(self, code=1):
        return sample_report(code)

    def test_daily_dedup_and_permissions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            now=datetime.datetime(2026,9,29,tzinfo=datetime.timezone.utc)
            bundle,dup=snapshot.save_report(root,self.report(),now)
            self.assertFalse(dup)
            self.assertEqual(stat.S_IMODE(bundle.stat().st_mode),0o700)
            self.assertEqual(stat.S_IMODE((bundle/'health.json').stat().st_mode),0o600)
            second=self.report()
            second['checked_at']='2026-09-29T23:59:59Z'
            again,dup=snapshot.save_report(root,second,now)
            self.assertTrue(dup)
            self.assertEqual(bundle,again)
            self.assertEqual(len(list(bundle.parent.iterdir())),1)
            self.assertEqual(json.loads((bundle/'health.json').read_text())['checked_at'], '2026-09-29T00:00:00Z')
            self.assertEqual((bundle/'collected-at.txt').read_text(), now.isoformat() + '\n')

    def test_changed_observation_and_next_day_create_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            now = datetime.datetime(2026, 9, 29, tzinfo=datetime.timezone.utc)
            first, _ = snapshot.save_report(root, self.report(), now)
            changed = self.report()
            changed['checks'][0]['status'] = 'WARN'
            second, duplicate = snapshot.save_report(root, changed, now)
            self.assertFalse(duplicate)
            self.assertNotEqual(first, second)
            next_day, duplicate = snapshot.save_report(root, self.report(), now + datetime.timedelta(days=1))
            self.assertFalse(duplicate)
            self.assertNotEqual(first.parent, next_day.parent)

    def test_missing_permissive_and_symlink_destination_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            with self.assertRaises(OSError): snapshot.save_report(root/'missing',self.report())
            (root/'open').mkdir(mode=0o755)
            with self.assertRaises(ValueError): snapshot.save_report(root/'open',self.report())
            (root/'link').symlink_to(root,target_is_directory=True)
            with self.assertRaises(ValueError): snapshot.save_report(root/'link',self.report())

    def test_owner_only_but_inexact_directory_mode_refused_without_repair(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            root.chmod(0o500)
            with self.assertRaises(ValueError):
                snapshot.save_report(root, self.report())
            self.assertEqual(stat.S_IMODE(root.stat().st_mode), 0o500)
            root.chmod(0o700)

    def test_corrupt_bundle_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            bundle,_=snapshot.save_report(root,self.report())
            (bundle/'health.json').write_text('keep this damage')
            with self.assertRaises(ValueError): snapshot.save_report(root,self.report())
            self.assertEqual((bundle/'health.json').read_text(),'keep this damage')

    def test_incomplete_bundle_is_not_reported_as_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            bundle,_=snapshot.save_report(root,self.report())
            (bundle/'collected-at.txt').unlink()
            with self.assertRaises((OSError, ValueError)): snapshot.save_report(root,self.report())

    def test_extra_entries_bad_mode_and_invalid_collection_date_refused(self):
        for damage in ('extra', 'mode', 'naive', 'date'):
            with self.subTest(damage=damage), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                now = datetime.datetime(2026, 9, 29, tzinfo=datetime.timezone.utc)
                bundle, _ = snapshot.save_report(root, self.report(), now)
                stamp = bundle / 'collected-at.txt'
                if damage == 'extra':
                    (bundle / 'unexpected').write_text('keep')
                elif damage == 'mode':
                    (bundle / 'health.json').chmod(0o644)
                elif damage == 'naive':
                    stamp.write_text('2026-09-29T00:00:00\n')
                else:
                    stamp.write_text('2026-09-28T00:00:00+00:00\n')
                with self.assertRaises(ValueError):
                    snapshot.save_report(root, self.report(), now)

    def test_oversized_and_symlink_existing_files_refused(self):
        for damage in ('oversized', 'symlink'):
            with self.subTest(damage=damage), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                bundle, _ = snapshot.save_report(root, self.report())
                path = bundle / 'health.json'
                if damage == 'oversized':
                    path.write_bytes(b'x' * (snapshot.MAX_REPORT_BYTES + 1))
                else:
                    path.unlink()
                    path.symlink_to(bundle / 'health.txt')
                with self.assertRaises((OSError, ValueError)):
                    snapshot.save_report(root, self.report())

    def test_health_unknown_is_saved_and_propagated(self):
        with tempfile.TemporaryDirectory() as tmp:
            def health(args):
                print(json.dumps(self.report()))
                return 1
            output=io.StringIO()
            with patch.object(snapshot.healthcheck,'main',side_effect=health),contextlib.redirect_stdout(output):
                code=snapshot.main(['--output-dir',tmp,'--','--skip-docker'])
            self.assertEqual(code,1)
            self.assertIn('saved',output.getvalue())

    def test_malformed_report_is_failure_without_raw_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            output=io.StringIO()
            with patch.object(snapshot.healthcheck,'main',side_effect=OSError('private-secret')),contextlib.redirect_stderr(output):
                self.assertEqual(snapshot.main(['--output-dir',tmp]),3)
            self.assertNotIn('private-secret',output.getvalue())

    def test_nested_corrupt_bundle_returns_collection_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            bundle,_=snapshot.save_report(root,self.report())
            (bundle/'health.json').write_text('['*16000+'0'+']'*16000)
            def health(args):
                print(json.dumps(self.report()))
                return 1
            with patch.object(snapshot.healthcheck,'main',side_effect=health),contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(snapshot.main(['--output-dir',tmp]),3)

if __name__=='__main__':
    unittest.main()
