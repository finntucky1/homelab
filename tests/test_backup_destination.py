import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

spec = importlib.util.spec_from_file_location('backup_destination', Path(__file__).parents[1] / 'scripts' / 'backup_destination.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class DestinationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.dest = self.root / 'destination'
        self.dest.mkdir(mode=0o700)
        self.source = self.root / 'production'
        self.source.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def mounts(self, target_disk='disk-b', source_disk='disk-a', mount='/'):
        return [{'mount': mount, 'filesystem': 'ext4', 'disks': {target_disk}},
                {'mount': '/', 'filesystem': 'ext4', 'disks': {source_disk}}]

    def test_different_physical_disk_passes_without_writes(self):
        with patch.object(module, 'inspect_mount', side_effect=self.mounts()):
            report = module.check_destination(str(self.dest), [str(self.source)], '/')
        self.assertEqual(report['status'], 'PASS')
        self.assertFalse(report['writes_performed'])
        self.assertEqual(list(self.dest.iterdir()), [])

    def test_same_physical_disk_refused_even_for_different_filesystems(self):
        with patch.object(module, 'inspect_mount', side_effect=self.mounts(source_disk='disk-b')):
            with self.assertRaisesRegex(module.DestinationError, 'shares a physical disk'):
                module.check_destination(str(self.dest), [str(self.source)], '/')

    def test_absent_expected_mount_refuses_root_fallback(self):
        expected = self.root / 'expected'
        expected.mkdir()
        with patch.object(module, 'inspect_mount', return_value=self.mounts()[0]):
            with self.assertRaisesRegex(module.DestinationError, 'mount is absent'):
                module.check_destination(str(self.dest), [str(self.source)], str(expected))

    def test_missing_destination_is_not_created(self):
        missing = self.root / 'missing'
        with self.assertRaises(module.DestinationError):
            module.check_destination(str(missing), [str(self.source)], '/')
        self.assertFalse(missing.exists())

    def test_permissive_destination_is_not_repaired(self):
        self.dest.chmod(0o755)
        with self.assertRaisesRegex(module.DestinationError, '0700'):
            module.check_destination(str(self.dest), [str(self.source)], '/')
        self.assertEqual(self.dest.stat().st_mode & 0o777, 0o755)

    def test_symlink_component_refused(self):
        alias = self.root / 'alias'
        alias.symlink_to(self.dest, target_is_directory=True)
        with self.assertRaisesRegex(module.DestinationError, 'Symlink'):
            module.check_destination(str(alias), [str(self.source)], '/')

    def test_insufficient_capacity_refused(self):
        with patch.object(module, 'inspect_mount', side_effect=self.mounts()):
            with self.assertRaisesRegex(module.DestinationError, 'free space'):
                module.check_destination(str(self.dest), [str(self.source)], '/', 10**30)

    def test_all_selected_sources_must_be_separate(self):
        rows = self.mounts() + [{'mount': '/', 'filesystem': 'ext4', 'disks': {'disk-b'}}]
        with patch.object(module, 'inspect_mount', side_effect=rows):
            with self.assertRaisesRegex(module.DestinationError, 'shares a physical disk'):
                module.check_destination(str(self.dest), [str(self.source), str(self.root)], '/')

    def test_unknown_device_inspection_fails_closed(self):
        with patch.object(module.subprocess, 'run', side_effect=OSError('private endpoint')):
            with self.assertRaisesRegex(module.DestinationError, 'no destination fallback') as context:
                module.inspect_mount(self.dest)
        self.assertNotIn('private endpoint', str(context.exception))

    def test_no_sources_refused(self):
        with self.assertRaisesRegex(module.DestinationError, 'production paths'):
            module.check_destination(str(self.dest), [], '/')

    def test_read_only_mount_refused_from_real_shaped_metadata(self):
        mount = {'filesystems': [{'source': '/dev/test1', 'target': '/',
                                'fstype': 'ext4', 'options': 'ro,relatime'}]}
        devices = {'blockdevices': [{'name': '/dev/test1', 'type': 'part',
                   'children': [{'name': '/dev/test', 'type': 'disk'}]}]}
        replies = [SimpleNamespace(stdout=json.dumps(mount)),
                   SimpleNamespace(stdout=json.dumps(devices))]
        with patch.object(module.subprocess, 'run', side_effect=replies):
            with self.assertRaisesRegex(module.DestinationError, 'read-only'):
                module.inspect_mount(self.dest)

    def test_read_write_mount_inspects_physical_ancestry(self):
        mount = {'filesystems': [{'source': '/dev/test1', 'target': '/',
                                'fstype': 'ext4', 'options': 'rw,relatime'}]}
        devices = {'blockdevices': [{'name': '/dev/test1', 'type': 'part',
                   'children': [{'name': '/dev/test', 'type': 'disk'}]}]}
        replies = [SimpleNamespace(stdout=json.dumps(mount)),
                   SimpleNamespace(stdout=json.dumps(devices))]
        with patch.object(module.subprocess, 'run', side_effect=replies):
            self.assertEqual(module.inspect_mount(self.dest)['disks'], {'/dev/test'})

    def test_invalid_cli_argument_omits_private_value(self):
        with patch('sys.stderr', new_callable=io.StringIO) as output:
            with self.assertRaises(SystemExit) as context:
                module.main(['--destination', str(self.dest), '--production', str(self.source),
                             '--expected-mount', '/', '--min-free-bytes', 'private-value'])
        self.assertEqual(context.exception.code, 2)
        self.assertNotIn('private-value', output.getvalue())

    def test_multidevice_filesystem_fails_closed(self):
        mount = {'filesystems': [{'source': '/dev/test1', 'target': '/',
                                'fstype': 'btrfs', 'options': 'rw'}]}
        with patch.object(module.subprocess, 'run', return_value=SimpleNamespace(stdout=json.dumps(mount))):
            with self.assertRaisesRegex(module.DestinationError, 'Only reviewed ext4'):
                module.inspect_mount(self.dest)

    def test_malformed_mount_fields_are_sanitized(self):
        for source in [None, 1, {}, []]:
            mount = {'filesystems': [{'source': source, 'target': '/',
                                    'fstype': 'ext4', 'options': 'rw'}]}
            with self.subTest(source=source):
                with patch.object(module.subprocess, 'run', return_value=SimpleNamespace(stdout=json.dumps(mount))):
                    with self.assertRaisesRegex(module.DestinationError, 'inspection failed'):
                        module.inspect_mount(self.dest)

    def test_malformed_device_ancestry_is_sanitized(self):
        mount = {'filesystems': [{'source': '/dev/test1', 'target': '/',
                                'fstype': 'ext4', 'options': 'rw'}]}
        devices = {'blockdevices': [{'name': None, 'type': 'disk'}]}
        replies = [SimpleNamespace(stdout=json.dumps(mount)),
                   SimpleNamespace(stdout=json.dumps(devices))]
        with patch.object(module.subprocess, 'run', side_effect=replies):
            with self.assertRaisesRegex(module.DestinationError, 'inspection failed'):
                module.inspect_mount(self.dest)
