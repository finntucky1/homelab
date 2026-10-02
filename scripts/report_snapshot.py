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


MAX_REPORT_BYTES = 4 * 1024 * 1024
BUNDLE_FILES = {'health.json', 'health.txt', 'collected-at.txt'}


class SafeParser(argparse.ArgumentParser):
    def error(self, unused):
        raise ValueError('Invalid report collector arguments.')


def private_directory(path):
    """Require an existing owner-only directory; never repair permissions."""
    if os.name != 'posix' or not hasattr(os, 'O_NOFOLLOW') or not hasattr(os, 'getuid'):
        raise ValueError('Private POSIX permissions and no-follow support are required.')
    if not path.is_absolute() or '..' in path.parts:
        raise ValueError('Use an absolute report directory.')
    for part in (path,) + tuple(path.parents):
        if part.is_symlink():
            raise ValueError('Report directories must not traverse symbolic links.')
    info = path.stat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700:
        raise ValueError('Report directory must be owned by you and mode 0700.')


def validate_report(report):
    if (not isinstance(report, dict) or set(report) != {'schema', 'checked_at', 'exit_code', 'checks'}
            or type(report['schema']) is not int or report['schema'] != 1
            or type(report['exit_code']) is not int or report['exit_code'] not in (0, 1, 2)
            or not isinstance(report['checks'], list) or not report['checks']):
        raise ValueError('Invalid health report.')
    value = report['checked_at']
    if not isinstance(value, str):
        raise ValueError('Invalid health timestamp.')
    checked = datetime.datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ')
    if checked.strftime('%Y-%m-%dT%H:%M:%SZ') != value:
        raise ValueError('Invalid health timestamp.')
    for check in report['checks']:
        if (not isinstance(check, dict) or set(check) - {'name', 'status', 'detail', 'action', 'metrics'}
                or any(not isinstance(check.get(key), str) for key in ('name', 'status', 'detail', 'action'))
                or not check['name'] or check['status'] not in healthcheck.LEVELS
                or ('metrics' in check and not isinstance(check['metrics'], dict))):
            raise ValueError('Invalid health observation.')
    if max(healthcheck.LEVELS[check['status']] for check in report['checks']) != report['exit_code']:
        raise ValueError('Inconsistent health severity.')


def collection_time(value):
    parsed = datetime.datetime.fromisoformat(value.strip())
    if (parsed.tzinfo is None or parsed.utcoffset() != datetime.timedelta(0)
            or value != parsed.isoformat() + '\n'):
        raise ValueError('Invalid UTC collection timestamp.')
    return parsed


def write_private(path, content):
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as handle:
        os.fchmod(handle.fileno(), 0o600)
        handle.write(content.encode('utf-8'))
        handle.flush()
        os.fsync(handle.fileno())


def save_report(directory, report, now=None):
    private_directory(directory)
    validate_report(report)
    now = now if now is not None else datetime.datetime.now(datetime.timezone.utc)
    if not isinstance(now, datetime.datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise ValueError('Collection time must include a timezone.')
    now = now.astimezone(datetime.timezone.utc)
    body = json.dumps(report, sort_keys=True, indent=2, allow_nan=False) + '\n'
    # Repeated equivalent observations retain the first collection time.
    comparable = dict(report)
    comparable.pop('checked_at', None)
    digest = hashlib.sha256(json.dumps(comparable, sort_keys=True, allow_nan=False).encode('utf-8')).hexdigest()
    lines = []
    for check in report['checks']:
        lines.append('[{status}] {name}: {detail}'.format(**check))
        if check.get('action'):
            lines.append('  Action: ' + check['action'])
    readable = '\n'.join(lines) + '\n'
    if any(len(content.encode('utf-8')) > MAX_REPORT_BYTES for content in (body, readable)):
        raise ValueError('Health report exceeds the private bundle size limit.')
    day = directory / now.strftime('%Y-%m-%d')
    try:
        day.mkdir(mode=0o700)
        day.chmod(0o700)
    except FileExistsError:
        private_directory(day)
    bundle = day / digest
    try:
        bundle.mkdir(mode=0o700)
        bundle.chmod(0o700)
    except FileExistsError:
        private_directory(bundle)
        if {path.name for path in bundle.iterdir()} != BUNDLE_FILES:
            raise ValueError('Existing report is unsafe or incomplete.')
        for name in sorted(BUNDLE_FILES):
            p = bundle / name
            existing = healthcheck.read_text(p, 256 if name == 'collected-at.txt' else MAX_REPORT_BYTES, private=True)
            if name == 'health.json':
                saved = json.loads(existing)
                validate_report(saved)
                saved.pop('checked_at', None)
                if saved != comparable:
                    raise ValueError('Existing report is inconsistent.')
            elif name == 'health.txt' and existing != readable:
                raise ValueError('Existing report is inconsistent.')
            elif name == 'collected-at.txt':
                if collection_time(existing).strftime('%Y-%m-%d') != day.name:
                    raise ValueError('Existing report has an inconsistent collection date.')
        return bundle, True
    for name, content in (('health.json', body), ('health.txt', readable), ('collected-at.txt', now.isoformat() + '\n')):
        write_private(bundle / name, content)
    return bundle, False


def main(argv=None):
    parser = SafeParser(description=__doc__)
    parser.add_argument('--output-dir', required=True, type=Path, help='Existing private directory (0700); keep outside Git.')
    parser.add_argument('health_args', nargs=argparse.REMAINDER, help='Healthcheck flags after --.')
    try:
        args = parser.parse_args(argv)
        flags = args.health_args
        if flags[:1] == ['--']:
            flags = flags[1:]
        private_directory(args.output_dir)
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(io.StringIO()):
            try:
                code = healthcheck.main(flags + ['--json'])
            except SystemExit:
                raise ValueError('Healthcheck did not produce a report.') from None
        report = json.loads(output.getvalue())
        validate_report(report)
        if type(code) is not int or report['exit_code'] != code:
            raise ValueError('Invalid health report.')
        _, duplicate = save_report(args.output_dir, report)
    except (OSError, ValueError, KeyError, TypeError, AttributeError, RecursionError):
        print('FAIL: Cannot collect a valid private report. Check permissions, arguments and incomplete bundles.', file=sys.stderr)
        return 3
    print('Private report {}. Health exit code: {}.'.format('already saved for this UTC day' if duplicate else 'saved', code))
    return code


if __name__ == '__main__':
    sys.exit(main())
