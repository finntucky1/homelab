#!/usr/bin/env python3
"""Read-only filesystem and Docker status checks. No third-party packages."""

import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys


LEVELS = {"PASS": 0, "WARN": 1, "FAIL": 2}


def result(name, status, detail):
    return {"name": name, "status": status, "detail": detail}


def disk_check(path, minimum_free, require_mount=False):
    location = Path(path).expanduser()
    name = "mount" if require_mount else "filesystem"
    try:
        if not location.exists():
            return result(name, "FAIL", "Path does not exist: {}".format(location))
        if require_mount and not location.is_mount():
            return result(name, "FAIL", "Not a detected mount point: {}".format(location))
        usage = shutil.disk_usage(location)
        if usage.total <= 0:
            return result(name, "FAIL", "No capacity reported for {}".format(location))
        free_percent = 100.0 * usage.free / usage.total
        status = "PASS" if free_percent >= minimum_free else "FAIL"
        detail = "{}: {:.1f}% free ({:.1f} GiB); minimum {:.1f}%".format(
            location, free_percent, usage.free / (1024 ** 3), minimum_free
        )
        return result(name, status, detail)
    except (OSError, ValueError) as exc:
        return result(name, "FAIL", "Cannot check {}: {}".format(location, exc))


def docker_checks(expected_containers=()):
    """Report Docker observations; optional exact names must exist and run."""
    expected = set(expected_containers)
    executable = shutil.which("docker")
    if executable is None:
        status = "FAIL" if expected else "WARN"
        return [result("docker", status, "Docker CLI is not installed or not on PATH.")]
    try:
        response = subprocess.run(
            [executable, "ps", "--all", "--format", "{{json .}}"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="strict",
            timeout=10,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return [result("docker", "FAIL", "Docker query timed out after 10 seconds.")]
    except OSError:
        return [result("docker", "FAIL", "Could not execute the Docker CLI.")]
    except UnicodeError:
        return [result("docker", "FAIL", "Docker output was not valid UTF-8; container state could not be verified.")]
    if response.returncode != 0:
        return [result("docker", "FAIL", "Docker query failed. Check daemon availability and existing user access.")]

    lines = response.stdout.strip().splitlines()
    if not lines and not expected:
        return [result("docker", "WARN", "Docker returned no containers.")]
    checks = []
    seen = set()
    for line in lines:
        try:
            container = json.loads(line)
            if not isinstance(container, dict):
                raise ValueError("Expected an object")
            name = container["Names"]
            state = container["State"]
            summary = container["Status"]
            if not all(isinstance(value, str) for value in (name, state, summary)):
                raise ValueError("Expected text fields")
            if not name or not state or not summary or name in seen:
                raise ValueError("Missing fields or duplicate container name")
        except (ValueError, KeyError, TypeError):
            return [result("docker", "FAIL", "Unexpected Docker output; container state could not be verified.")]

        seen.add(name)
        state = state.lower()
        summary_lower = summary.lower()
        status = "PASS"
        if "(unhealthy)" in summary_lower or state in ("dead", "restarting"):
            status = "FAIL"
        elif name in expected and state != "running":
            status = "FAIL"
        elif state != "running" or "health: starting" in summary_lower:
            status = "WARN"
        detail = "{}: {}".format(state, summary)
        if state == "running" and not any(
            health in summary_lower for health in ("(healthy)", "(unhealthy)", "health: starting")
        ):
            if status == "PASS":
                status = "WARN"
            detail += " (application health check not reported)"
        checks.append(result("container:{}".format(name), status, detail))
    for name in sorted(expected - seen):
        checks.append(result("container:{}".format(name), "FAIL", "Expected container is missing from Docker output."))
    return checks


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", action="append", default=[], help="Additional path whose filesystem capacity is checked")
    parser.add_argument("--mount", action="append", default=[], help="Path that must also be a detected mount point")
    parser.add_argument("--min-free-percent", type=float, default=10.0, help="Minimum free capacity, 0 through 100 (default: 10)")
    parser.add_argument("--skip-docker", action="store_true", help="Run filesystem checks only")
    parser.add_argument("--expect-container", action="append", default=[], help="Exact name of a required running container; repeat for additional names")
    parser.add_argument("--json", action="store_true", help="Print structured JSON")
    args = parser.parse_args(argv)
    if not 0 <= args.min_free_percent <= 100:
        parser.error("--min-free-percent must be between 0 and 100")
    if args.skip_docker and args.expect_container:
        parser.error("--skip-docker cannot be combined with --expect-container")
    if any(not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.-]*", name) for name in args.expect_container):
        parser.error("--expect-container requires an exact Docker container name (letters, digits, underscores, periods, and hyphens)")

    checks = [disk_check(path, args.min_free_percent) for path in ["/"] + args.path]
    checks.extend(disk_check(path, args.min_free_percent, True) for path in args.mount)
    if not args.skip_docker:
        checks.extend(docker_checks(args.expect_container))
    exit_code = max(LEVELS[check["status"]] for check in checks)
    if args.json:
        print(json.dumps({"exit_code": exit_code, "checks": checks}, indent=2))
    else:
        for check in checks:
            print("[{status}] {name}: {detail}".format(**check))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
