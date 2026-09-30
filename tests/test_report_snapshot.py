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

@unittest.skipUnless(os.name == 'posix', 'Private POSIX reports require POSIX.')
class ReportSnapshotTests(unittest.TestCase):
    def report(self, code=1):
        return {'exit_code':code, 'checks':[{'name':'docker','status':'UNKNOWN','detail':'Access unavailable.'}]}

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

    def test_missing_permissive_and_symlink_destination_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            with self.assertRaises(OSError): snapshot.save_report(root/'missing',self.report())
            (root/'open').mkdir(mode=0o755)
            with self.assertRaises(ValueError): snapshot.save_report(root/'open',self.report())
            (root/'link').symlink_to(root,target_is_directory=True)
            with self.assertRaises(ValueError): snapshot.save_report(root/'link',self.report())

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
            with self.assertRaises(OSError): snapshot.save_report(root,self.report())

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
