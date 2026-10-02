#!/usr/bin/env python3
"""Read-only Linux host checks and explicit HTTP/name-resolution probes."""

import argparse
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import stat
import sys
import urllib.error
import urllib.parse
import urllib.request


LEVELS = {"PASS": 0, "WARN": 1, "UNKNOWN": 1, "FAIL": 2}
NAME = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_.-]{0,127}")
UNIT = re.compile(r"[a-zA-Z0-9_.:@\\-]+")
SNAPSHOT = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}")
DEFAULTS = {
    "min_free_percent": 10.0,
    "memory_warn_percent": 10.0, "memory_fail_percent": 5.0,
    "load_warn_per_cpu": 1.0, "load_fail_per_cpu": 2.0,
    "pressure_warn_percent": 10.0, "pressure_fail_percent": 25.0,
    "temperature_warn_c": 70.0, "temperature_fail_c": 80.0,
}


class SafeParser(argparse.ArgumentParser):
    def error(self, unused):
        # argparse otherwise repeats invalid private paths, URLs and values.
        super().error("Invalid healthcheck arguments or private configuration; use --help and scripts/README.md")


def result(name, status, detail, action="", **metrics):
    report = {"name": name, "status": status, "detail": detail, "action": action}
    if metrics:
        report["metrics"] = metrics
    return report


def read_text(path, limit=65536, private=False):
    """Read bounded regular-file bytes without waiting for a FIFO writer."""
    location = Path(path).expanduser()
    flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0)
    if private:
        if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "getuid"):
            raise ValueError("Private POSIX file verification is unavailable")
        flags |= os.O_NOFOLLOW
    descriptor = os.open(str(location), flags)
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode):
            raise ValueError("Input must be a regular file")
        if private and (info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o600):
            raise ValueError("Private input must be owned by this user and mode 0600")
        with os.fdopen(descriptor, "rb") as source:
            descriptor = None
            content = source.read(limit + 1)
    finally:
        if descriptor is not None:
            os.close(descriptor)
    if len(content) > limit:
        raise ValueError("Oversized input")
    return content.decode("utf-8")


def disk_check(path, minimum_free, require_mount=False):
    location = Path(path).expanduser()
    name = "mount" if require_mount else "filesystem"
    try:
        location.stat()
        if require_mount and not location.is_mount():
            return result(name, "FAIL", "Not a detected mount point: {}".format(location),
                          "Verify the intended disk and mount before using its data.")
        usage = shutil.disk_usage(location)
        if usage.total <= 0 or not 0 <= usage.free <= usage.total:
            raise ValueError("Invalid capacity counters")
        free_percent = 100.0 * usage.free / usage.total
        status = "PASS" if free_percent >= minimum_free else "FAIL"
        return result(name, status,
                      "{}: {:.1f}% free ({:.1f} GiB); minimum {:.1f}%".format(
                          location, free_percent, usage.free / (1024 ** 3), minimum_free),
                      "Review growth and retention before deleting data." if status == "FAIL" else "",
                      free_percent=round(free_percent, 2), minimum_free_percent=minimum_free)
    except FileNotFoundError:
        return result(name, "FAIL", "Path does not exist: {}".format(location),
                      "Confirm the configured path and intended mount.")
    except (OSError, ValueError, UnicodeError):
        return result(name, "UNKNOWN", "Cannot inspect configured filesystem capacity.",
                      "Check the path and existing read access; do not weaken permissions.")


def container_restart_checks(executable, names):
    """Request only selected counters; never collect a full inspect document."""
    if not names:
        return []
    unavailable = result('container-restarts', 'UNKNOWN', 'Container restart counters are unavailable or unrecognized.',
                         'Review existing Docker access and CLI compatibility; no full inspect data is collected.')
    if len(names) > 64:
        return [result('container-restarts', 'UNKNOWN', 'More than 64 observed containers; restart-counter query was not run.',
                       'Container state checks remain available; counter collection requires at most 64 observed containers.')]
    template = '{"name":{{json .Name}},"restart_count":{{json .RestartCount}}}'
    try:
        response = subprocess.run([executable, 'inspect', '--type', 'container', '--format', template] + sorted(names),
                                  capture_output=True, text=True, encoding='utf-8', errors='strict', timeout=10, check=False)
        if response.returncode != 0:
            raise ValueError('Unavailable counters')
        counters = {}
        for line in response.stdout.strip().splitlines():
            record = json.loads(line)
            if not isinstance(record, dict) or set(record) != {'name', 'restart_count'}:
                raise ValueError('Invalid counter record')
            name, count = record['name'], record['restart_count']
            if not isinstance(name, str) or not name.startswith('/'):
                raise ValueError('Invalid counter name')
            name = name[1:]
            if name not in names or name in counters or type(count) is not int or count < 0:
                raise ValueError('Invalid counter')
            counters[name] = count
        if set(counters) != set(names):
            raise ValueError('Incomplete counters')
    except (OSError, UnicodeError, ValueError, TypeError, KeyError, RecursionError, subprocess.TimeoutExpired):
        return [unavailable]
    return [result('container-restarts:{}'.format(name), 'WARN' if count else 'PASS',
                   '{} recorded restart(s) since this container was created.'.format(count),
                   'Review the counter with prior observations; a nonzero lifetime count does not establish a current fault or restart rate.' if count else '',
                   restart_count=count) for name, count in sorted(counters.items())]


def docker_checks(expected_containers=(), check_restarts=False):
    """A failed observation is UNKNOWN; only observed bad state is FAIL."""
    expected = set(expected_containers)
    executable = shutil.which("docker")
    if executable is None:
        return [result("docker", "UNKNOWN", "Docker CLI is unavailable.",
                       "Verify the intended host and existing Docker access.")]
    try:
        response = subprocess.run(
            [executable, "ps", "--all", "--format", "{{json .}}"],
            capture_output=True, text=True, encoding="utf-8", errors="strict",
            timeout=10, check=False)
    except (subprocess.TimeoutExpired, OSError, UnicodeError):
        return [result("docker", "UNKNOWN", "Docker query was unavailable, timed out, or undecodable.",
                       "Check the daemon/context and existing user access without changing socket permissions.")]
    if response.returncode != 0:
        return [result("docker", "UNKNOWN", "Docker query failed; container state is unverified.",
                       "Check the daemon/context and existing user access without changing socket permissions.")]
    lines = response.stdout.strip().splitlines()
    if not lines and not expected:
        return [result("docker", "UNKNOWN", "Docker returned no containers and no required names were configured.",
                       "Confirm the intended inventory and configure exact required names.")]
    checks, seen = [], set()
    for line in lines:
        try:
            container = json.loads(line)
            name, state, summary = (container[key] for key in ("Names", "State", "Status"))
            if not all(isinstance(value, str) and value for value in (name, state, summary)):
                raise ValueError("Invalid fields")
            if not NAME.fullmatch(name) or name in seen:
                raise ValueError("Invalid name")
        except (ValueError, KeyError, TypeError, RecursionError):
            return [result("docker", "UNKNOWN", "Unexpected Docker output; container state could not be verified.",
                           "Review Docker CLI compatibility privately and rerun the check.")]
        seen.add(name)
        state, summary_lower = state.lower(), summary.lower()
        status, action = "PASS", ""
        if "(unhealthy)" in summary_lower or state in ("dead", "restarting"):
            status, action = "FAIL", "Review the configured probe and sanitized service logs before changing the service."
        elif name in expected and state != "running":
            status, action = "FAIL", "Confirm why the required container is not running."
        elif state != "running" or "health: starting" in summary_lower:
            status, action = "WARN", "Confirm whether this state is intentional; review again after startup."
        detail = "{}: {}".format(state, summary)
        if state == "running" and not any(
                health in summary_lower for health in ("(healthy)", "(unhealthy)", "health: starting")):
            status, action = "UNKNOWN", "Review the actual probe and configure an explicit application HTTP check."
            detail += " (application health check not reported)"
        checks.append(result("container:{}".format(name), status, detail, action))
    for name in sorted(expected - seen):
        checks.append(result("container:{}".format(name), "FAIL", "Expected container is missing from Docker output.",
                             "Compare exact Docker names with the verified inventory; investigate before changing expectations."))
    if check_restarts:
        checks.extend(container_restart_checks(executable, seen))
    return checks


def service_check(scope="system"):
    executable = shutil.which("systemctl")
    if not executable:
        return result("failed-services", "UNKNOWN", "systemctl is unavailable.", "Inspect failed services on the intended host.")
    command = [executable]
    if scope == "user":
        command.append("--user")
    command += ["--failed", "--no-legend", "--plain", "--no-pager"]
    try:
        response = subprocess.run(command, capture_output=True, text=True,
                                  encoding="utf-8", errors="strict", timeout=10, check=False)
        if response.returncode != 0:
            raise ValueError("Unavailable bus")
        failed = []
        for line in response.stdout.strip().splitlines():
            fields = line.split()
            if len(fields) < 4 or fields[2] != "failed" or not UNIT.fullmatch(fields[0]):
                raise ValueError("Unrecognized service output")
            failed.append(fields[0])
    except (OSError, UnicodeError, ValueError, subprocess.TimeoutExpired):
        return result("failed-services", "UNKNOWN", "{} service state is inaccessible or unrecognized.".format(scope),
                      "Inspect the intended system/user bus with existing access; an inaccessible bus is not a failed service.")
    if failed:
        return result("failed-services", "FAIL", "{} failed unit(s): {}".format(len(failed), ", ".join(failed)),
                      "Inspect each failed unit's status and sanitized logs before approving a repair.", failed_count=len(failed))
    return result("failed-services", "PASS", "No failed {} units reported.".format(scope), failed_count=0)


def memory_check(warn_percent, fail_percent, path="/proc/meminfo"):
    try:
        fields = {}
        for line in read_text(path).splitlines():
            match = re.fullmatch(r"(MemTotal|MemAvailable):\s+(\d+) kB", line)
            if match:
                fields[match[1]] = int(match[2])
        total, available = fields["MemTotal"], fields["MemAvailable"]
        if total <= 0 or not 0 <= available <= total:
            raise ValueError("Invalid memory counters")
        percent = 100.0 * available / total
    except (OSError, UnicodeError, ValueError, KeyError):
        return result("memory", "UNKNOWN", "Linux available-memory counters are unavailable or invalid.",
                      "Read memory metrics on the intended host with existing access.")
    status = "FAIL" if percent < fail_percent else "WARN" if percent < warn_percent else "PASS"
    return result("memory", status,
                  "{:.1f}% available; warning below {:.1f}%, failure below {:.1f}%.".format(percent, warn_percent, fail_percent),
                  "Review workload memory and pressure before changing limits or stopping services." if status != "PASS" else "",
                  available_percent=round(percent, 2), warn_below_percent=warn_percent, fail_below_percent=fail_percent)


def load_check(warn_per_cpu, fail_per_cpu):
    try:
        cpus = os.cpu_count()
        load = os.getloadavg()[1]
        if not cpus or not math.isfinite(load) or load < 0:
            raise ValueError("Invalid load")
        normalized = load / cpus
    except (OSError, AttributeError, ValueError):
        return result("load", "UNKNOWN", "Five-minute load or CPU count is unavailable.", "Inspect load on the intended Linux host.")
    status = "FAIL" if normalized >= fail_per_cpu else "WARN" if normalized >= warn_per_cpu else "PASS"
    return result("load", status, "5-minute load {:.2f} across {} CPUs ({:.2f} per CPU); warning {:.2f}, failure {:.2f}.".format(
        load, cpus, normalized, warn_per_cpu, fail_per_cpu),
        "Review CPU and I/O contention; load also includes tasks waiting for I/O." if status != "PASS" else "",
        load_5min=round(load, 2), cpu_count=cpus, load_per_cpu=round(normalized, 2))


def pressure_check(warn_percent, fail_percent, path="/proc/pressure/memory"):
    try:
        content = read_text(path, 4096)
        match = re.search(r"^some avg10=([0-9.]+)\s", content, re.MULTILINE)
        percent = float(match.group(1)) if match else float("nan")
        if not math.isfinite(percent) or not 0 <= percent <= 100:
            raise ValueError("Invalid pressure")
    except (OSError, UnicodeError, ValueError):
        return result("memory-pressure", "UNKNOWN", "Linux memory pressure (PSI) is unsupported, inaccessible, or invalid.",
                      "Check kernel PSI availability on the intended host; do not infer zero pressure.")
    status = "FAIL" if percent >= fail_percent else "WARN" if percent >= warn_percent else "PASS"
    return result("memory-pressure", status,
                  "Memory stall time avg10 {:.2f}%; warning {:.2f}%, failure {:.2f}%.".format(percent, warn_percent, fail_percent),
                  "Review memory contention and workload demand." if status != "PASS" else "", stall_avg10_percent=percent)


def thermal_check(warn_c, fail_c, path="/sys/class/thermal/thermal_zone0/temp"):
    try:
        temperature = float(read_text(path, 128).strip()) / 1000
        if not math.isfinite(temperature) or not -50 <= temperature <= 150:
            raise ValueError("Invalid temperature")
    except (OSError, UnicodeError, ValueError):
        return result("temperature", "UNKNOWN", "Configured sysfs temperature is unavailable or invalid.",
                      "Verify the CPU thermal-zone path and existing read access on the Pi.")
    status = "FAIL" if temperature >= fail_c else "WARN" if temperature >= warn_c else "PASS"
    return result("temperature", status, "{:.1f} C; warning {:.1f} C, failure {:.1f} C.".format(temperature, warn_c, fail_c),
                  "Inspect cooling, workload and airflow before making host changes." if status != "PASS" else "", temperature_c=temperature)


def throttle_check():
    executable = shutil.which("vcgencmd")
    if not executable:
        return result("power-throttling", "UNKNOWN", "vcgencmd is unavailable; Pi power/throttling state is unverified.",
                      "Use the Pi's existing firmware utility if available; do not install it automatically.")
    try:
        response = subprocess.run([executable, "get_throttled"], capture_output=True, text=True,
                                  encoding="utf-8", errors="strict", timeout=5, check=False)
        match = re.fullmatch(r"throttled=0x([0-9a-fA-F]+)\s*", response.stdout)
        if response.returncode != 0 or not match:
            raise ValueError("Unavailable state")
        flags = int(match.group(1), 16)
        if flags & ~0xF000F:
            raise ValueError("Unknown flags")
    except (OSError, UnicodeError, ValueError, subprocess.TimeoutExpired):
        return result("power-throttling", "UNKNOWN", "Pi throttling query is inaccessible or unrecognized.",
                      "Inspect firmware support and existing access; do not infer normal power from missing data.")
    active, historical = flags & 0xF, (flags >> 16) & 0xF
    names = ("under-voltage", "frequency capped", "throttled", "soft temperature limit")
    states = [names[index] for index in range(4) if active & (1 << index)]
    history = [names[index] for index in range(4) if historical & (1 << index)]
    status = "FAIL" if active else "WARN" if historical else "PASS"
    detail = "Current: {}; since boot: {}.".format(
        ", ".join(states) if states else "none reported", ", ".join(history) if history else "none reported")
    return result("power-throttling", status, detail,
                  "Review the PoE/power path and cooling; historical flags do not prove a current fault." if status != "PASS" else "",
                  flags_hex=hex(flags))


def backup_check(marker, max_age_hours, now=None):
    if not marker:
        return result("backup-evidence", "UNKNOWN", "No verified static config/export recovery marker is configured.",
                      "Choose a marker produced after approved isolated byte recovery; backup age alone does not prove recovery.")
    try:
        evidence = json.loads(read_text(marker, 4096, private=True))
        required = {"schema", "kind", "status", "created_at", "recovered_at", "snapshot_id", "manifest_sha256"}
        if not isinstance(evidence, dict) or set(evidence) != required:
            raise ValueError("Invalid marker schema")
        if type(evidence["schema"]) is not int or evidence["schema"] != 1 or evidence["kind"] != "config-export-recovery" or evidence["status"] != "verified":
            raise ValueError("Unverified marker")
        if not isinstance(evidence["snapshot_id"], str) or not SNAPSHOT.fullmatch(evidence["snapshot_id"]):
            raise ValueError("Invalid snapshot ID")
        if not isinstance(evidence["manifest_sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", evidence["manifest_sha256"]):
            raise ValueError("Invalid digest")
        stamps = []
        for key in ("created_at", "recovered_at"):
            if not isinstance(evidence[key], str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", evidence[key]):
                raise ValueError("Invalid timestamp")
            stamps.append(datetime.strptime(evidence[key], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc))
        current = now if now is not None else datetime.now(timezone.utc)
        age_hours = (current - stamps[0]).total_seconds() / 3600
        if stamps[1] < stamps[0] or (stamps[1] - current).total_seconds() > 300 or age_hours < -300 / 3600:
            raise ValueError("Inconsistent/future timestamps")
        age_hours = max(0.0, age_hours)
    except FileNotFoundError:
        return result("backup-evidence", "FAIL", "Configured recovery marker is missing.",
                      "Verify the selected marker and the last approved config/export recovery evidence.")
    except (OSError, UnicodeError, ValueError, TypeError, KeyError, RecursionError):
        return result("backup-evidence", "UNKNOWN", "Configured recovery marker is unreadable, malformed, or unverified.",
                      "Review the private marker source and recovery record; never create a success marker from file age alone.")
    status = "FAIL" if age_hours > max_age_hours else "PASS"
    return result("backup-evidence", status,
                  "Static config/export snapshot packaging age {:.1f}h; maximum {:.1f}h; marker records isolated byte recovery only, not source-data freshness.".format(age_hours, max_age_hours),
                  "Make and verify a new approved snapshot; this marker does not prove application recovery or authenticity." if status == "FAIL" else
                  "Periodically test application recovery separately; the marker is a local assertion, not authenticated proof.",
                  snapshot_age_hours=round(age_hours, 2), maximum_age_hours=max_age_hours)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, new_url):
        return None


def dns_worker():
    try:
        probe = validate_dns_probe(json.loads(sys.stdin.read(4097)))
        resolved = bool(socket.getaddrinfo(probe['host'], None, type=socket.SOCK_STREAM))
        report = {'resolved': resolved}
    except (OSError, UnicodeError, ValueError, KeyError, TypeError, RecursionError):
        report = {'resolved': False}
    print(json.dumps(report))
    return 0


def dns_check(probe):
    name = 'dns:{}'.format(probe['name'])
    try:
        response = subprocess.run([sys.executable, str(Path(__file__).resolve()), '--_dns-worker'],
                                  input=json.dumps(probe), capture_output=True, text=True, encoding='utf-8', errors='strict',
                                  timeout=probe['timeout_seconds'] + 1.0, check=False)
        report = json.loads(response.stdout)
        if response.returncode != 0 or not isinstance(report, dict) or set(report) != {'resolved'} or type(report['resolved']) is not bool:
            raise ValueError('Invalid resolver observation')
    except subprocess.TimeoutExpired:
        return result(name, 'FAIL', 'Configured name-resolution probe exceeded its bounded deadline.',
                      'Review resolver availability from this host; hostnames and addresses are intentionally omitted.')
    except (OSError, UnicodeError, ValueError, TypeError, KeyError, RecursionError):
        return result(name, 'UNKNOWN', 'Name-resolution worker was unavailable or returned invalid observation data.',
                      'Check local Python execution and retry; hostnames and addresses are intentionally omitted.')
    status = 'PASS' if report['resolved'] else 'FAIL'
    return result(name, status, 'Configured hostname {} through the operating-system resolver.'.format(
        'resolved' if report['resolved'] else 'could not be resolved'),
        'Resolution can use hosts files or caches; it does not prove a route or application response.' if status == 'PASS' else
        'Check the configured hostname and resolver from this host before changing network settings.')


def validate_dns_probe(probe):
    if not isinstance(probe, dict) or set(probe) - {'name', 'host', 'timeout_seconds'}:
        raise ValueError('DNS probes require only name, host and timeout_seconds')
    name, host = probe.get('name'), probe.get('host')
    if not isinstance(name, str) or not NAME.fullmatch(name):
        raise ValueError('DNS probe labels must be simple short identifiers')
    if (not isinstance(host, str) or not 1 <= len(host) <= 253
            or not all(re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?', label)
                       for label in (host[:-1] if host.endswith('.') else host).split('.')) or host.replace('.', '').isdigit()):
        raise ValueError('DNS probes require an ASCII hostname, without a URL, address, port or credentials')
    timeout = probe.get('timeout_seconds', 3.0)
    if type(timeout) not in (int, float) or not math.isfinite(timeout) or not 0.1 <= timeout <= 15:
        raise ValueError('DNS probe timeout_seconds must be between 0.1 and 15')
    return {'name': name, 'host': host, 'timeout_seconds': float(timeout)}


def http_worker():
    """Child process keeps DNS, TLS and headers under an overall parent deadline."""
    try:
        probe = json.loads(sys.stdin.read(4097))
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
        request = urllib.request.Request(probe["url"], headers={"User-Agent": "homelab-healthcheck/1"}, method="GET")
        try:
            with opener.open(request, timeout=probe["timeout_seconds"]) as response:
                code = response.status
        except urllib.error.HTTPError as response:
            code = response.code
        report = {"status_code": code}
    except (OSError, ValueError, KeyError, TypeError, RecursionError, urllib.error.URLError):
        report = {"unreachable": True}
    print(json.dumps(report))
    return 0


def http_check(probe):
    name = "application:{}".format(probe["name"])
    try:
        response = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--_http-worker"],
            input=json.dumps(probe), capture_output=True, text=True, encoding="utf-8", errors="strict",
            timeout=probe["timeout_seconds"] + 1.0, check=False)
        report = json.loads(response.stdout)
        if response.returncode != 0 or not isinstance(report, dict):
            raise ValueError("Probe worker failed")
        if report == {"unreachable": True}:
            return result(name, "FAIL", "Configured HTTP application probe could not reach a response.",
                          "Check listener, route and TLS from this host; running container state alone does not prove availability.")
        code = report["status_code"]
        if type(code) is not int or not 100 <= code <= 599:
            raise ValueError("Invalid response")
    except subprocess.TimeoutExpired:
        return result(name, "FAIL", "Configured HTTP application probe exceeded its bounded deadline.",
                      "Check listener, route, DNS and workload response time from this host.")
    except (OSError, UnicodeError, ValueError, TypeError, KeyError, RecursionError):
        return result(name, "UNKNOWN", "HTTP probe worker was unavailable or returned invalid observation data.",
                      "Check local Python execution and retry; endpoint details are intentionally omitted.")
    status = "PASS" if code in probe["expected_statuses"] else "FAIL"
    return result(name, status, "HTTP {} received; expected status {}. Redirects are not followed.".format(
        code, ", ".join(str(item) for item in probe["expected_statuses"])),
        "Review the application's supported health endpoint and access requirements." if status == "FAIL" else
        "Response status matches from this host; login, data and remote-client access are separate checks.", status_code=code)


def validate_probe(probe):
    if not isinstance(probe, dict) or set(probe) - {"name", "url", "timeout_seconds", "expected_statuses"}:
        raise ValueError("Each HTTP probe requires only name, url, timeout_seconds and expected_statuses")
    name, url = probe.get("name"), probe.get("url")
    if not isinstance(name, str) or not NAME.fullmatch(name):
        raise ValueError("HTTP probe name must be a short label containing letters, digits, period, underscore or hyphen")
    if not isinstance(url, str) or len(url) > 2048 or any(ord(char) < 33 for char in url):
        raise ValueError("HTTP probe URL is invalid")
    try:
        parsed = urllib.parse.urlsplit(url)
        port = parsed.port
        if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username is not None or parsed.password is not None or parsed.query or parsed.fragment:
            raise ValueError("Invalid endpoint")
        if port is not None and not 1 <= port <= 65535:
            raise ValueError("Invalid port")
    except ValueError:
        raise ValueError("HTTP probe URL requires http/https, a host, and no credentials, query or fragment") from None
    timeout = probe.get("timeout_seconds", 3.0)
    if type(timeout) not in (int, float) or not math.isfinite(timeout) or not 0.1 <= timeout <= 15:
        raise ValueError("HTTP probe timeout_seconds must be between 0.1 and 15")
    statuses = probe.get("expected_statuses", [200])
    if not isinstance(statuses, list) or not statuses or len(statuses) > 16 or any(type(code) is not int or not 100 <= code <= 599 for code in statuses):
        raise ValueError("HTTP probe expected_statuses must contain 1 through 16 integer HTTP statuses")
    return {"name": name, "url": url, "timeout_seconds": float(timeout), "expected_statuses": sorted(set(statuses))}


def configuration(parser, args):
    config = {}
    if args.config:
        try:
            config = json.loads(read_text(args.config, private=True))
        except (OSError, UnicodeError, ValueError, RecursionError):
            parser.error("Cannot read private JSON config; check access, size and syntax")
    allowed = {"paths", "mounts", "expected_containers", "thresholds", "systemd_scope", "thermal_path", "backup_marker", "backup_max_age_hours", "http_probes", "dns_probes", "check_container_restarts"}
    if not isinstance(config, dict) or set(config) - allowed:
        parser.error("Config must be an object containing only documented keys")
    for key in ("paths", "mounts", "expected_containers"):
        items = config.get(key, [])
        if not isinstance(items, list) or any(not isinstance(item, str) or not item for item in items):
            parser.error("Configured path/name lists must contain nonempty strings")
    thresholds = config.get("thresholds", {})
    if not isinstance(thresholds, dict) or set(thresholds) - set(DEFAULTS):
        parser.error("Config thresholds contain an unknown key")
    thresholds = dict(DEFAULTS, **thresholds)
    for key in DEFAULTS:
        value = getattr(args, key)
        if value is not None:
            thresholds[key] = value
        value = thresholds[key]
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
            parser.error("Thresholds must be finite nonnegative numbers")
        if key.endswith("percent") and value > 100:
            parser.error("Percentage thresholds must be between 0 and 100")
    for low, high in (("memory_fail_percent", "memory_warn_percent"), ("load_warn_per_cpu", "load_fail_per_cpu"),
                      ("pressure_warn_percent", "pressure_fail_percent"), ("temperature_warn_c", "temperature_fail_c")):
        if thresholds[low] >= thresholds[high]:
            parser.error("Warning and failure thresholds must be ordered and distinct")
    config["thresholds"] = thresholds
    config["paths"] = config.get("paths", []) + args.path
    config["mounts"] = config.get("mounts", []) + args.mount
    config["expected_containers"] = config.get("expected_containers", []) + args.expect_container
    if any(not NAME.fullmatch(name) for name in config["expected_containers"]):
        parser.error("Expected containers require exact Docker names, not patterns")
    if args.skip_docker and config["expected_containers"]:
        parser.error("--skip-docker cannot be combined with expected containers")
    restarts = config.get('check_container_restarts', False) or args.check_container_restarts
    if type(config.get('check_container_restarts', False)) is not bool or (restarts and args.skip_docker):
        parser.error('Restart counters require Docker checks and a boolean config value')
    config['check_container_restarts'] = restarts
    for key, fallback in (("systemd_scope", "system"), ("thermal_path", "/sys/class/thermal/thermal_zone0/temp"), ("backup_marker", None), ("backup_max_age_hours", 48.0)):
        supplied = getattr(args, key)
        config[key] = supplied if supplied is not None else config.get(key, fallback)
    if config["systemd_scope"] not in ("system", "user"):
        parser.error("systemd_scope must be system or user")
    for key in ("thermal_path", "backup_marker"):
        if config[key] is not None and (not isinstance(config[key], str) or not config[key]):
            parser.error("Configured paths must be nonempty strings")
    age = config["backup_max_age_hours"]
    if type(age) not in (int, float) or not math.isfinite(age) or age <= 0:
        parser.error("backup_max_age_hours must be finite and greater than zero")
    probes = config.get("http_probes", [])
    if not isinstance(probes, list):
        parser.error("http_probes must be a list")
    for item in args.http_probe:
        if "=" not in item:
            parser.error("--http-probe requires LABEL=URL")
        name, url = item.split("=", 1)
        probes.append({"name": name, "url": url})
    if len(probes) > 16:
        parser.error("At most 16 explicit HTTP probes are supported")
    try:
        config["http_probes"] = [validate_probe(probe) for probe in probes]
    except ValueError as error:
        parser.error(str(error))
    if len({probe["name"] for probe in config["http_probes"]}) != len(config["http_probes"]):
        parser.error("HTTP probe labels must be unique")
    probes = config.get('dns_probes', [])
    if not isinstance(probes, list):
        parser.error('dns_probes must be a list')
    for item in args.dns_probe:
        if '=' not in item:
            parser.error('--dns-probe requires LABEL=HOST')
        name, host = item.split('=', 1)
        probes.append({'name': name, 'host': host})
    if len(probes) > 16:
        parser.error('At most 16 explicit DNS probes are supported')
    try:
        config['dns_probes'] = [validate_dns_probe(probe) for probe in probes]
    except ValueError as error:
        parser.error(str(error))
    if len({probe['name'] for probe in config['dns_probes']}) != len(config['dns_probes']):
        parser.error('DNS probe labels must be unique')
    return config


def main(argv=None):
    if argv == ["--_http-worker"]:
        return http_worker()
    if argv == ['--_dns-worker']:
        return dns_worker()
    parser = SafeParser(description=__doc__)
    parser.add_argument("--config", help="Private JSON config; see scripts/README.md")
    parser.add_argument("--path", action="append", default=[], help="Additional filesystem path")
    parser.add_argument("--mount", action="append", default=[], help="Required detected mount point")
    parser.add_argument("--expect-container", action="append", default=[], help="Exact required Docker name")
    parser.add_argument('--check-container-restarts', action='store_true', help='Read only formatted lifetime restart counters for up to 64 observed containers')
    for key, default in DEFAULTS.items():
        parser.add_argument("--" + key.replace("_", "-"), type=float, help="Threshold (default: {})".format(default))
    parser.add_argument("--systemd-scope", choices=("system", "user"), help="Failed-unit bus scope (default: system)")
    parser.add_argument("--thermal-path", help="Verified sysfs temperature file in millidegrees C")
    parser.add_argument("--backup-marker", help="Private verified static config/export byte-recovery JSON marker")
    parser.add_argument("--backup-max-age-hours", type=float, help="Maximum marker snapshot age (default: 48)")
    parser.add_argument("--http-probe", action="append", default=[], metavar="LABEL=URL", help="Explicit credential-free HTTP response probe; repeatable")
    parser.add_argument('--dns-probe', action='append', default=[], metavar='LABEL=HOST', help='Explicit operating-system hostname-resolution probe; repeatable')
    for name in ("docker", "systemd", "resources", "thermal", "backup", "http", 'dns'):
        parser.add_argument("--skip-" + name, action="store_true", help="Exclude {} checks from this report".format(name))
    parser.add_argument("--json", action="store_true", help="Print structured JSON without private HTTP endpoints or DNS hostnames/addresses")
    args = parser.parse_args(argv)
    config = configuration(parser, args)
    thresholds = config["thresholds"]
    checks = [disk_check(path, thresholds["min_free_percent"]) for path in ["/"] + config["paths"]]
    checks += [disk_check(path, thresholds["min_free_percent"], True) for path in config["mounts"]]
    if not args.skip_docker:
        checks.extend(docker_checks(config["expected_containers"], config['check_container_restarts']))
    if not args.skip_systemd:
        checks.append(service_check(config["systemd_scope"]))
    if not args.skip_resources:
        checks += [memory_check(thresholds["memory_warn_percent"], thresholds["memory_fail_percent"]),
                   load_check(thresholds["load_warn_per_cpu"], thresholds["load_fail_per_cpu"]),
                   pressure_check(thresholds["pressure_warn_percent"], thresholds["pressure_fail_percent"])]
    if not args.skip_thermal:
        checks += [thermal_check(thresholds["temperature_warn_c"], thresholds["temperature_fail_c"], config["thermal_path"]), throttle_check()]
    if not args.skip_backup:
        checks.append(backup_check(config["backup_marker"], config["backup_max_age_hours"]))
    if not args.skip_http:
        checks += [http_check(probe) for probe in config["http_probes"]] if config["http_probes"] else [result(
            "application-probes", "UNKNOWN", "No HTTP application probes configured; running containers do not prove reachability.",
            "Review supported health endpoints and configure private explicit probes.")]
    if not args.skip_dns:
        checks += [dns_check(probe) for probe in config['dns_probes']] if config['dns_probes'] else [result(
            'dns-probes', 'UNKNOWN', 'No hostname-resolution probes configured; resolver availability is unverified.',
            'Choose an approved hostname and configure an explicit private probe, or exclude this category with --skip-dns.')]
    exit_code = max(LEVELS[check["status"]] for check in checks)
    if args.json:
        print(json.dumps({"schema": 1, "checked_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                          "exit_code": exit_code, "checks": checks}, indent=2))
    else:
        for check in checks:
            print("[{status}] {name}: {detail}".format(**check))
            if check["action"]:
                print("  Action: {}".format(check["action"]))
    return exit_code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
