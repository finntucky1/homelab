#!/usr/bin/env python3
"""Read-only local destination preflight; never creates or copies anything."""
import argparse
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess


class DestinationError(Exception):
    pass


def inspect_mount(path):
    try:
        result = subprocess.run(
            ['findmnt', '-J', '-T', str(path), '-o', 'SOURCE,TARGET,FSTYPE,OPTIONS'],
            capture_output=True, text=True, timeout=5, check=True)
        row = json.loads(result.stdout)['filesystems'][0]
        if any(not isinstance(row[key], str) or not row[key]
               for key in ('source', 'target', 'fstype', 'options')):
            raise ValueError('Invalid mount metadata.')
        if row['fstype'] != 'ext4':
            raise DestinationError('Only reviewed ext4 storage is supported; other filesystem independence needs review.')
        source = row['source'].split('[', 1)[0]
        if not source.startswith('/dev/'):
            raise DestinationError('Local block storage is required; network independence needs a separate review.')
        result = subprocess.run(
            ['lsblk', '-J', '-s', '-p', '-o', 'NAME,TYPE', source],
            capture_output=True, text=True, timeout=5, check=True)
        tree = json.loads(result.stdout)['blockdevices']
        disks = set()
        def walk(rows, depth=0):
            if not isinstance(rows, list) or depth > 32:
                raise ValueError('Invalid device metadata.')
            for item in rows:
                if (not isinstance(item, dict) or not isinstance(item.get('type'), str)
                        or not isinstance(item.get('name'), str)
                        or not item['name'].startswith('/dev/')):
                    raise ValueError('Invalid device metadata.')
                if item['type'] == 'disk':
                    disks.add(item['name'])
                walk(item.get('children', []), depth + 1)
        walk(tree)
        if not disks:
            raise DestinationError('Physical storage ancestry could not be established.')
        options = row['options'].split(',')
        if 'rw' not in options or 'ro' in options:
            raise DestinationError('A read-write mount is required; read-only storage is refused.')
        return {'mount': row['target'], 'filesystem': row['fstype'], 'disks': disks}
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, IndexError,
            TypeError, AttributeError, RecursionError):
        raise DestinationError('Mount or physical-device inspection failed; no destination fallback.') from None


def existing_path(value):
    path = Path(value)
    if not path.is_absolute() or '..' in path.parts:
        raise DestinationError('Use existing absolute paths without parent traversal.')
    for component in (path,) + tuple(path.parents):
        try:
            if stat.S_ISLNK(component.lstat().st_mode):
                raise DestinationError('Symlink path components are refused.')
        except OSError:
            raise DestinationError('A required path is missing or inaccessible.') from None
    return path


def check_destination(destination, production, expected_mount, min_free_bytes=0):
    destination = existing_path(destination)
    expected_mount = existing_path(expected_mount)
    if not production:
        raise DestinationError('Explicit production paths are required.')
    info = destination.stat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) != 0o700:
        raise DestinationError('Destination must already be an owner-only 0700 directory owned by this user.')
    target = inspect_mount(destination)
    if Path(target['mount']) != expected_mount:
        raise DestinationError('Expected destination mount is absent; refusing a containing-filesystem fallback.')
    sources = [inspect_mount(existing_path(value)) for value in production]
    if any(target['disks'] & source['disks'] for source in sources):
        raise DestinationError('Destination shares a physical disk with a selected production path.')
    free = shutil.disk_usage(destination).free
    if free < min_free_bytes:
        raise DestinationError('Destination has less than the required free space.')
    return {'schema': 1, 'status': 'PASS', 'mode': 'dry-run',
            'physical_device_separation': 'OBSERVED for the explicitly selected production paths',
            'source_count': len(sources), 'destination_filesystem': target['filesystem'],
            'destination_free_bytes': free, 'writes_performed': False,
            'limits': 'Same-host storage does not cover host loss. This does not validate exports, retention, or recovery.'}


class PrivateArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(2, 'Invalid destination arguments; consult --help privately.\n')


def main(argv=None):
    parser = PrivateArgumentParser(description=__doc__)
    parser.add_argument('--destination', required=True)
    parser.add_argument('--production', action='append', required=True)
    parser.add_argument('--expected-mount', required=True)
    parser.add_argument('--min-free-bytes', type=int, default=0)
    args = parser.parse_args(argv)
    try:
        if args.min_free_bytes < 0:
            raise DestinationError('Minimum free space cannot be negative.')
        report = check_destination(args.destination, args.production, args.expected_mount, args.min_free_bytes)
    except (DestinationError, OSError) as error:
        message = str(error) if isinstance(error, DestinationError) else 'Destination inspection failed.'
        print(json.dumps({'schema': 1, 'status': 'FAIL', 'mode': 'dry-run', 'reason': message, 'writes_performed': False}))
        return 2
    print(json.dumps(report))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
