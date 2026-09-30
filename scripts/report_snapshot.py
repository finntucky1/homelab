#!/usr/bin/env python3
"""Collect healthcheck results in private, deduplicated daily bundles."""

import argparse
import contextlib
import datetime
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import sys

import healthcheck


def private_directory(path):
    """Require an existing owner-only directory; never repair permissions."""
    if not path.is_absolute():
        raise ValueError('Use an absolute report directory.')
    for part in (path,) + tuple(path.parents):
        if part.is_symlink():
            raise ValueError('Report directories must not traverse symbolic links.')
    info = path.stat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
        raise ValueError('Report directory must be owned by you and mode 0700.')


def save_report(directory, report, now=None):
    private_directory(directory)
    now = now or datetime.datetime.now(datetime.timezone.utc)
    body = json.dumps(report, sort_keys=True, indent=2) + '\n'
    # Repeated equivalent observations retain the first collection time.
    comparable = dict(report)
    comparable.pop('checked_at', None)
    digest = hashlib.sha256(json.dumps(comparable, sort_keys=True).encode('utf-8')).hexdigest()
    day = directory / now.strftime('%Y-%m-%d')
    try:
        day.mkdir(mode=0o700)
    except FileExistsError:
        private_directory(day)
    bundle = day / digest
    lines = []
    for check in report['checks']:
        lines.append('[{status}] {name}: {detail}'.format(**check))
        if check.get('action'):
            lines.append('  Action: ' + check['action'])
    readable = '\n'.join(lines) + '\n'
    try:
        bundle.mkdir(mode=0o700)
    except FileExistsError:
        private_directory(bundle)
        for name in ('health.json', 'health.txt', 'collected-at.txt'):
            p = bundle / name
            info = p.lstat()
            if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o600:
                raise ValueError('Existing report is unsafe or incomplete.')
            existing = p.read_text(encoding='utf-8')
            if name == 'health.json':
                saved = json.loads(existing)
                saved.pop('checked_at', None)
                if saved != comparable:
                    raise ValueError('Existing report is inconsistent.')
            elif name == 'health.txt' and existing != readable:
                raise ValueError('Existing report is inconsistent.')
            elif name == 'collected-at.txt':
                datetime.datetime.fromisoformat(existing.strip())
        return bundle, True
    for name, content in (('health.json', body), ('health.txt', readable)):
        p = bundle / name
        fd = os.open(str(p), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(content)
    fd = os.open(str(bundle / 'collected-at.txt'), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write(now.isoformat() + '\n')
    return bundle, False


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', required=True, type=Path, help='Existing private directory (0700); keep outside Git.')
    parser.add_argument('health_args', nargs=argparse.REMAINDER, help='Healthcheck flags after --.')
    args = parser.parse_args(argv)
    if os.name != 'posix':
        print('FAIL: Private POSIX permissions are required.', file=sys.stderr)
        return 3
    flags = args.health_args
    if flags[:1] == ['--']:
        flags = flags[1:]
    try:
        private_directory(args.output_dir)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = healthcheck.main(flags + ['--json'])
        report = json.loads(output.getvalue())
        if code not in (0, 1, 2) or not isinstance(report.get('checks'), list) or report.get('exit_code') != code:
            raise ValueError('Invalid health report.')
        _, duplicate = save_report(args.output_dir, report)
    except (OSError, ValueError, KeyError, TypeError, AttributeError, RecursionError):
        print('FAIL: Cannot collect a valid private report. Check permissions, arguments and incomplete bundles.', file=sys.stderr)
        return 3
    print('Private report {}. Health exit code: {}.'.format('already saved for this UTC day' if duplicate else 'saved', code))
    return code


if __name__ == '__main__':
    sys.exit(main())
