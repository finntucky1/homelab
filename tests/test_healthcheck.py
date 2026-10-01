"""Simulated health observations: no daemon, Pi, HTTP endpoint or production data."""

import contextlib
from datetime import datetime, timedelta, timezone
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import urllib.error


SPEC = importlib.util.spec_from_file_location(
    "healthcheck", Path(__file__).resolve().parents[1] / "scripts" / "healthcheck.py")
healthcheck = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(healthcheck)


def response(stdout="", code=0):
    return SimpleNamespace(returncode=code, stdout=stdout)


SKIPS = ["--skip-docker", "--skip-systemd", "--skip-resources", "--skip-thermal", "--skip-backup", "--skip-http", '--skip-dns']


class HealthCheckTests(unittest.TestCase):
    def test_free_space_threshold(self):
        with tempfile.TemporaryDirectory() as directory:
            for free, expected in ((25, "PASS"), (10, "PASS"), (9, "FAIL")):
                with self.subTest(free=free), patch.object(healthcheck.shutil, "disk_usage", return_value=SimpleNamespace(total=100, free=free)):
                    self.assertEqual(healthcheck.disk_check(directory, 10)["status"], expected)

    def test_missing_path_and_unmounted_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(healthcheck.disk_check(Path(directory) / "missing", 10)["status"], "FAIL")
            self.assertEqual(healthcheck.disk_check(directory, 10, True)["status"], "FAIL")

    def test_inaccessible_disk_is_unknown_and_sanitized(self):
        with patch.object(Path, "stat", side_effect=PermissionError("private diagnostic")):
            report = healthcheck.disk_check("/private", 10)
        self.assertEqual(report["status"], "UNKNOWN")
        self.assertNotIn("private", report["detail"])

    def test_invalid_disk_capacity_is_unknown(self):
        with tempfile.TemporaryDirectory() as directory:
            for total, free in ((0, 0), (100, -1), (100, 101)):
                with self.subTest(total=total, free=free), patch.object(healthcheck.shutil, "disk_usage", return_value=SimpleNamespace(total=total, free=free)):
                    self.assertEqual(healthcheck.disk_check(directory, 10)["status"], "UNKNOWN")

    def test_missing_docker_is_unknown_even_with_expectations(self):
        with patch.object(healthcheck.shutil, "which", return_value=None):
            for expected in ([], ["required"]):
                self.assertEqual(healthcheck.docker_checks(expected)[0]["status"], "UNKNOWN")

    def test_docker_state_classification(self):
        containers = [
            {"Names": "healthy", "State": "running", "Status": "Up 1 hour (healthy)"},
            {"Names": "no-probe", "State": "running", "Status": "Up 1 hour"},
            {"Names": "unhealthy", "State": "running", "Status": "Up 1 hour (unhealthy)"},
            {"Names": "starting", "State": "running", "Status": "Up 2 seconds (health: starting)"},
            {"Names": "stopped", "State": "exited", "Status": "Exited (0)"},
            {"Names": "restarting", "State": "restarting", "Status": "Restarting (1)"},
        ]
        with patch.object(healthcheck.shutil, "which", return_value="/fake/docker"), patch.object(healthcheck.subprocess, "run", return_value=response("\n".join(json.dumps(c) for c in containers))) as command:
            checks = healthcheck.docker_checks()
        self.assertEqual([c["status"] for c in checks], ["PASS", "UNKNOWN", "FAIL", "WARN", "WARN", "FAIL"])
        self.assertIn("not reported", checks[1]["detail"])
        self.assertEqual(command.call_args.args[0][1:3], ["ps", "--all"])

    def test_docker_blocked_or_bad_output_never_claims_failed_service(self):
        cases = [response(code=1), response(), response("invalid json"), response('{"Names": "incomplete"}'), response("null"), response("[]"), response('{"Names":"app","State":true,"Status":"Up"}'), response('{"Names":"app","State":"running","Status":""}')]
        with patch.object(healthcheck.shutil, "which", return_value="/fake/docker"):
            for observation in cases:
                with self.subTest(stdout=observation.stdout), patch.object(healthcheck.subprocess, "run", return_value=observation):
                    self.assertEqual(healthcheck.docker_checks()[0]["status"], "UNKNOWN")

    def test_docker_timeout_execution_and_decoding_are_unknown_and_sanitized(self):
        errors = [subprocess.TimeoutExpired("docker", 10), OSError("sensitive diagnostic"), UnicodeDecodeError("utf-8", b"\xff", 0, 1, "sensitive diagnostic")]
        with patch.object(healthcheck.shutil, "which", return_value="/fake/docker"):
            for error in errors:
                with self.subTest(error=type(error).__name__), patch.object(healthcheck.subprocess, "run", side_effect=error):
                    report = healthcheck.docker_checks()[0]
                self.assertEqual(report["status"], "UNKNOWN")
                self.assertNotIn("sensitive diagnostic", report["detail"])

    def test_expected_container_missing_from_successful_inventory_fails(self):
        present = json.dumps({"Names": "other", "State": "running", "Status": "Up 1 hour (healthy)"})
        with patch.object(healthcheck.shutil, "which", return_value="/fake/docker"):
            for stdout in ("", present):
                with self.subTest(stdout=stdout), patch.object(healthcheck.subprocess, "run", return_value=response(stdout)):
                    reports = healthcheck.docker_checks(["required", "required"])
                required = [item for item in reports if item["name"] == "container:required"]
                self.assertEqual(len(required), 1)
                self.assertEqual(required[0]["status"], "FAIL")

    def test_required_container_state_and_health(self):
        cases = [("running", "Up (healthy)", "PASS"), ("running", "Up", "UNKNOWN"), ("running", "Up (health: starting)", "WARN"), ("running", "Up (unhealthy)", "FAIL"), ("exited", "Exited (0)", "FAIL"), ("paused", "Up (Paused)", "FAIL")]
        with patch.object(healthcheck.shutil, "which", return_value="/fake/docker"):
            for state, summary, expected in cases:
                with self.subTest(state=state, summary=summary), patch.object(healthcheck.subprocess, "run", return_value=response(json.dumps({"Names": "required", "State": state, "Status": summary}))):
                    self.assertEqual(healthcheck.docker_checks(["required"])[0]["status"], expected)

    def test_restart_counts_are_selective_and_nonzero_is_historical_warning(self):
        observations = '\n'.join(json.dumps({'name': '/' + name, 'restart_count': count})
                                 for name, count in (('one', 0), ('two', 4)))
        with patch.object(healthcheck.subprocess, 'run', return_value=response(observations)) as command:
            reports = healthcheck.container_restart_checks('/fake/docker', {'one', 'two'})
        self.assertEqual([item['status'] for item in reports], ['PASS', 'WARN'])
        self.assertEqual(reports[1]['metrics']['restart_count'], 4)
        self.assertIn('since this container was created', reports[1]['detail'])
        args = command.call_args.args[0]
        self.assertEqual(args[:5], ['/fake/docker', 'inspect', '--type', 'container', '--format'])
        self.assertEqual(args[-2:], ['one', 'two'])
        self.assertIn('.RestartCount', args[5])
        self.assertNotIn('.Config', args[5])
        self.assertEqual(command.call_args.kwargs['timeout'], 10)

    def test_restart_denied_malformed_and_partial_observations_are_unknown(self):
        cases = [response(code=1), response(), response('private diagnostics'), response('null'),
                 response('{"name":"/app","restart_count":true}'), response('{"name":"/app","restart_count":-1}'),
                 response('{"name":"/other","restart_count":0}'), response('{"name":"app","restart_count":0}'),
                 response('{"name":"/app","restart_count":0,"private":"secret"}')]
        for observation in cases:
            with self.subTest(stdout=observation.stdout), patch.object(healthcheck.subprocess, 'run', return_value=observation):
                reports = healthcheck.container_restart_checks('/fake/docker', {'app'})
            self.assertEqual(reports[0]['status'], 'UNKNOWN')
            self.assertNotIn('secret', json.dumps(reports))
            self.assertNotIn('private diagnostics', json.dumps(reports))
        for error in (OSError('PRIVATE-SECRET'), UnicodeError('PRIVATE-SECRET'), subprocess.TimeoutExpired('docker', 10)):
            with patch.object(healthcheck.subprocess, 'run', side_effect=error):
                reports = healthcheck.container_restart_checks('/fake/docker', {'app'})
            self.assertEqual(reports[0]['status'], 'UNKNOWN')
            self.assertNotIn('PRIVATE-SECRET', json.dumps(reports))

    def test_restart_inventory_limit_and_empty_inventory_do_not_query(self):
        with patch.object(healthcheck.subprocess, 'run') as command:
            self.assertEqual(healthcheck.container_restart_checks('/fake/docker', set()), [])
            reports = healthcheck.container_restart_checks('/fake/docker', {'app{}'.format(i) for i in range(65)})
        command.assert_not_called()
        self.assertEqual(reports[0]['status'], 'UNKNOWN')

    def test_restarting_state_remains_fail_with_nonzero_restart_counter(self):
        state = json.dumps({'Names': 'app', 'State': 'restarting', 'Status': 'Restarting (1)'})
        counter = json.dumps({'name': '/app', 'restart_count': 4})
        with patch.object(healthcheck.shutil, 'which', return_value='/fake/docker'), patch.object(healthcheck.subprocess, 'run', side_effect=[response(state), response(counter)]):
            reports = healthcheck.docker_checks(['app'], check_restarts=True)
        self.assertEqual([item['status'] for item in reports], ['FAIL', 'WARN'])

    def test_container_name_is_exact_and_duplicates_are_unknown(self):
        line = json.dumps({"Names": "app-2", "State": "running", "Status": "Up (healthy)"})
        with patch.object(healthcheck.shutil, "which", return_value="/fake/docker"), patch.object(healthcheck.subprocess, "run", return_value=response(line)):
            self.assertEqual(healthcheck.docker_checks(["app"])[-1]["status"], "FAIL")
        with patch.object(healthcheck.shutil, "which", return_value="/fake/docker"), patch.object(healthcheck.subprocess, "run", return_value=response(line + "\n" + line)):
            self.assertEqual(healthcheck.docker_checks()[0]["status"], "UNKNOWN")

    def test_failed_service_and_healthy_service(self):
        with patch.object(healthcheck.shutil, "which", return_value="/fake/systemctl"):
            for stdout, expected in (("", "PASS"), ("getty@tty1.service loaded failed failed Example\n", "FAIL")):
                with self.subTest(stdout=stdout), patch.object(healthcheck.subprocess, "run", return_value=response(stdout)):
                    self.assertEqual(healthcheck.service_check()["status"], expected)

    def test_service_scope_and_unavailable_bus(self):
        with patch.object(healthcheck.shutil, "which", return_value="/fake/systemctl"), patch.object(healthcheck.subprocess, "run", return_value=response(code=1)) as command:
            self.assertEqual(healthcheck.service_check("user")["status"], "UNKNOWN")
        self.assertIn("--user", command.call_args.args[0])
        with patch.object(healthcheck.shutil, "which", return_value=None):
            self.assertEqual(healthcheck.service_check()["status"], "UNKNOWN")

    def test_service_bad_output_timeout_and_encoding_are_unknown(self):
        with patch.object(healthcheck.shutil, "which", return_value="/fake/systemctl"):
            with patch.object(healthcheck.subprocess, "run", return_value=response("unexpected output")):
                self.assertEqual(healthcheck.service_check()["status"], "UNKNOWN")
            for error in (subprocess.TimeoutExpired("systemctl", 10), OSError("private"), UnicodeError("private")):
                with patch.object(healthcheck.subprocess, "run", side_effect=error):
                    report = healthcheck.service_check()
                self.assertEqual(report["status"], "UNKNOWN")
                self.assertNotIn("private", report["detail"])

    def test_available_memory_boundaries(self):
        for available, expected in ((50, "PASS"), (10, "PASS"), (9, "WARN"), (5, "WARN"), (4, "FAIL")):
            with self.subTest(available=available), patch.object(healthcheck, "read_text", return_value="MemTotal: 100 kB\nMemAvailable: {} kB\n".format(available)):
                self.assertEqual(healthcheck.memory_check(10, 5)["status"], expected)

    def test_invalid_or_missing_memory_is_unknown(self):
        for content in ("MemTotal: 100 kB\n", "MemTotal: 0 kB\nMemAvailable: 0 kB\n", "MemTotal: 100 kB\nMemAvailable: 101 kB\n", "invalid"):
            with self.subTest(content=content), patch.object(healthcheck, "read_text", return_value=content):
                self.assertEqual(healthcheck.memory_check(10, 5)["status"], "UNKNOWN")
        with patch.object(healthcheck, "read_text", side_effect=PermissionError()):
            self.assertEqual(healthcheck.memory_check(10, 5)["status"], "UNKNOWN")

    def test_load_boundaries_normalized_per_cpu(self):
        for load, expected in ((3.9, "PASS"), (4, "WARN"), (8, "FAIL")):
            with self.subTest(load=load), patch.object(healthcheck.os, "cpu_count", return_value=4), patch.object(healthcheck.os, "getloadavg", return_value=(0, load, 0), create=True):
                self.assertEqual(healthcheck.load_check(1, 2)["status"], expected)

    def test_load_unavailable_or_invalid_is_unknown(self):
        with patch.object(healthcheck.os, "cpu_count", return_value=None):
            self.assertEqual(healthcheck.load_check(1, 2)["status"], "UNKNOWN")
        with patch.object(healthcheck.os, "getloadavg", side_effect=OSError(), create=True):
            self.assertEqual(healthcheck.load_check(1, 2)["status"], "UNKNOWN")
        with patch.object(healthcheck.os, "getloadavg", return_value=(0, float("nan"), 0), create=True):
            self.assertEqual(healthcheck.load_check(1, 2)["status"], "UNKNOWN")

    def test_pressure_thresholds_and_unsupported_unknown(self):
        for value, expected in (("0.00", "PASS"), ("10.00", "WARN"), ("25.00", "FAIL"), ("101.0", "UNKNOWN"), ("...", "UNKNOWN")):
            with self.subTest(value=value), patch.object(healthcheck, "read_text", return_value="some avg10={} avg60=0.00 avg300=0.00 total=0\n".format(value)):
                self.assertEqual(healthcheck.pressure_check(10, 25)["status"], expected)
        with patch.object(healthcheck, "read_text", side_effect=FileNotFoundError()):
            self.assertEqual(healthcheck.pressure_check(10, 25)["status"], "UNKNOWN")

    def test_temperature_thresholds_and_unavailable(self):
        for value, expected in (("45000", "PASS"), ("70000", "WARN"), ("80000", "FAIL"), ("nan", "UNKNOWN"), ("200000", "UNKNOWN"), ("invalid", "UNKNOWN")):
            with self.subTest(value=value), patch.object(healthcheck, "read_text", return_value=value):
                self.assertEqual(healthcheck.thermal_check(70, 80)["status"], expected)
        with patch.object(healthcheck, "read_text", side_effect=PermissionError()):
            self.assertEqual(healthcheck.thermal_check(70, 80)["status"], "UNKNOWN")

    def test_throttle_current_historical_and_unknown_flags(self):
        with patch.object(healthcheck.shutil, "which", return_value="/fake/vcgencmd"):
            for value, expected in (("0x0", "PASS"), ("0x1", "FAIL"), ("0x8", "FAIL"), ("0x10000", "WARN"), ("0x80000", "WARN"), ("0x10001", "FAIL"), ("0x10", "UNKNOWN"), ("invalid", "UNKNOWN")):
                with self.subTest(value=value), patch.object(healthcheck.subprocess, "run", return_value=response("throttled=" + value + "\n")):
                    self.assertEqual(healthcheck.throttle_check()["status"], expected)

    def test_throttle_missing_blocked_and_timeout_are_unknown(self):
        with patch.object(healthcheck.shutil, "which", return_value=None):
            self.assertEqual(healthcheck.throttle_check()["status"], "UNKNOWN")
        with patch.object(healthcheck.shutil, "which", return_value="/fake/vcgencmd"):
            with patch.object(healthcheck.subprocess, "run", return_value=response(code=1)):
                self.assertEqual(healthcheck.throttle_check()["status"], "UNKNOWN")
            with patch.object(healthcheck.subprocess, "run", side_effect=subprocess.TimeoutExpired("vcgencmd", 5)):
                self.assertEqual(healthcheck.throttle_check()["status"], "UNKNOWN")

    def marker(self, now, age=1):
        return {"schema": 1, "kind": "config-export-recovery", "status": "verified", "created_at": (now - timedelta(hours=age)).strftime("%Y-%m-%dT%H:%M:%SZ"), "recovered_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "snapshot_id": "sample-1", "manifest_sha256": "a" * 64}

    def test_backup_fresh_and_stale_use_snapshot_age(self):
        now = datetime(2026, 9, 29, tzinfo=timezone.utc)
        for age, expected in ((1, "PASS"), (48, "PASS"), (49, "FAIL")):
            with self.subTest(age=age), patch.object(healthcheck, "read_text", return_value=json.dumps(self.marker(now, age))):
                report = healthcheck.backup_check("private-marker", 48, now)
            self.assertEqual(report["status"], expected)
            self.assertIn("byte recovery only", report["detail"])
            self.assertNotIn("private-marker", json.dumps(report))

    def test_backup_missing_unconfigured_and_inaccessible(self):
        self.assertEqual(healthcheck.backup_check(None, 48)["status"], "UNKNOWN")
        with patch.object(healthcheck, "read_text", side_effect=FileNotFoundError()):
            self.assertEqual(healthcheck.backup_check("marker", 48)["status"], "FAIL")
        with patch.object(healthcheck, "read_text", side_effect=PermissionError("private")):
            report = healthcheck.backup_check("marker", 48)
        self.assertEqual(report["status"], "UNKNOWN")
        self.assertNotIn("private", report["detail"])

    def test_backup_rejects_unverified_schema_timestamps_and_digest(self):
        now = datetime(2026, 9, 29, tzinfo=timezone.utc)
        changes = [{"status": "failed"}, {"schema": True}, {"kind": "live-app-recovery"}, {"created_at": "2026-09-30T00:00:00Z"}, {"recovered_at": "2026-09-28T00:00:00Z"}, {"recovered_at": "2026-09-29T00:06:00Z"}, {"manifest_sha256": "bad"}, {"snapshot_id": "../unsafe"}, {"created_at": "not-a-date"}, {"unexpected": "private"}]
        for change in changes:
            evidence = dict(self.marker(now), **change)
            with self.subTest(change=change), patch.object(healthcheck, "read_text", return_value=json.dumps(evidence)):
                self.assertEqual(healthcheck.backup_check("marker", 48, now)["status"], "UNKNOWN")
        for raw in ("null", "[]", "{}", "broken"):
            with patch.object(healthcheck, "read_text", return_value=raw):
                self.assertEqual(healthcheck.backup_check("marker", 48, now)["status"], "UNKNOWN")

    def probe(self):
        return healthcheck.validate_probe({"name": "media", "url": "http://127.0.0.1:8096/private/health", "timeout_seconds": 0.5})

    def dns_probe(self):
        return healthcheck.validate_dns_probe({'name': 'resolver', 'host': 'private-host.example', 'timeout_seconds': 0.5})

    def test_dns_resolution_success_failure_and_deadline_hide_host_and_addresses(self):
        probe = self.dns_probe()
        for resolved, expected in ((True, 'PASS'), (False, 'FAIL')):
            with self.subTest(resolved=resolved), patch.object(healthcheck.subprocess, 'run', return_value=response(json.dumps({'resolved': resolved}))) as command:
                report = healthcheck.dns_check(probe)
            self.assertEqual(report['status'], expected)
            self.assertNotIn(probe['host'], json.dumps(report))
            self.assertNotIn(probe['host'], ' '.join(command.call_args.args[0]))
            self.assertEqual(command.call_args.kwargs['timeout'], 1.5)
            self.assertEqual(json.loads(command.call_args.kwargs['input'])['host'], probe['host'])
        with patch.object(healthcheck.subprocess, 'run', side_effect=subprocess.TimeoutExpired('private-host.example', 1.5)):
            report = healthcheck.dns_check(probe)
        self.assertEqual(report['status'], 'FAIL')
        self.assertNotIn(probe['host'], json.dumps(report))

    def test_dns_worker_unavailable_or_invalid_is_unknown(self):
        for stdout in ('broken', 'null', '{}', '{"resolved":1}', '{"resolved":true,"address":"PRIVATE-SECRET"}'):
            with self.subTest(stdout=stdout), patch.object(healthcheck.subprocess, 'run', return_value=response(stdout)):
                report = healthcheck.dns_check(self.dns_probe())
            self.assertEqual(report['status'], 'UNKNOWN')
            self.assertNotIn('PRIVATE-SECRET', json.dumps(report))
        with patch.object(healthcheck.subprocess, 'run', side_effect=PermissionError('PRIVATE-SECRET')):
            self.assertEqual(healthcheck.dns_check(self.dns_probe())['status'], 'UNKNOWN')

    def test_dns_worker_only_returns_boolean_observation(self):
        for answer, resolved in (([('PRIVATE-ADDRESS',)], True), ([], False)):
            output = io.StringIO()
            with patch.object(healthcheck.sys, 'stdin', io.StringIO(json.dumps(self.dns_probe()))), patch.object(healthcheck.socket, 'getaddrinfo', return_value=answer), contextlib.redirect_stdout(output):
                self.assertEqual(healthcheck.dns_worker(), 0)
            self.assertEqual(json.loads(output.getvalue()), {'resolved': resolved})
        output = io.StringIO()
        with patch.object(healthcheck.sys, 'stdin', io.StringIO(json.dumps(self.dns_probe()))), patch.object(healthcheck.socket, 'getaddrinfo', side_effect=OSError('PRIVATE-SECRET')), contextlib.redirect_stdout(output):
            healthcheck.dns_worker()
        self.assertEqual(json.loads(output.getvalue()), {'resolved': False})
        self.assertNotIn('PRIVATE-SECRET', output.getvalue())

    def test_dns_validation_rejects_addresses_urls_credential_and_invalid_input(self):
        for host in ('127.0.0.1', '::1', 'http://private-host.example', 'name:53', 'secret@name',
                     '-host.example', 'host..example', 'host..', '', 'a' * 64 + '.example'):
            with self.subTest(host=host), self.assertRaises(ValueError):
                healthcheck.validate_dns_probe({'name': 'resolver', 'host': host})
        for probe in (None, {}, dict(self.dns_probe(), name='../unsafe'), dict(self.dns_probe(), timeout_seconds=True),
                      dict(self.dns_probe(), timeout_seconds=16), dict(self.dns_probe(), headers={'secret': 'value'})):
            with self.subTest(probe=probe), self.assertRaises(ValueError):
                healthcheck.validate_dns_probe(probe)
        self.assertEqual(healthcheck.validate_dns_probe({'name': 'resolver', 'host': 'localhost.'})['timeout_seconds'], 3.0)

    def test_http_success_and_status_mismatch_hide_endpoint_and_bound_worker(self):
        probe = self.probe()
        for code, expected in ((200, "PASS"), (503, "FAIL"), (302, "FAIL")):
            with self.subTest(code=code), patch.object(healthcheck.subprocess, "run", return_value=response(json.dumps({"status_code": code}))) as command:
                report = healthcheck.http_check(probe)
            self.assertEqual(report["status"], expected)
            self.assertNotIn(probe["url"], json.dumps(report))
            self.assertNotIn(probe["url"], " ".join(command.call_args.args[0]))
            self.assertEqual(command.call_args.kwargs["timeout"], 1.5)
            self.assertEqual(json.loads(command.call_args.kwargs["input"])["url"], probe["url"])

    def test_http_unreachable_and_timeout_are_failed_observations(self):
        with patch.object(healthcheck.subprocess, "run", return_value=response('{"unreachable": true}')):
            self.assertEqual(healthcheck.http_check(self.probe())["status"], "FAIL")
        with patch.object(healthcheck.subprocess, "run", side_effect=subprocess.TimeoutExpired("private URL", 1.5)):
            report = healthcheck.http_check(self.probe())
        self.assertEqual(report["status"], "FAIL")
        self.assertNotIn("private URL", json.dumps(report))

    def test_http_worker_invalid_or_unavailable_is_unknown(self):
        for stdout in ("broken", "null", "{}", '{"status_code": true}', '{"status_code": 999}'):
            with self.subTest(stdout=stdout), patch.object(healthcheck.subprocess, "run", return_value=response(stdout)):
                self.assertEqual(healthcheck.http_check(self.probe())["status"], "UNKNOWN")
        with patch.object(healthcheck.subprocess, "run", side_effect=PermissionError("private")):
            self.assertEqual(healthcheck.http_check(self.probe())["status"], "UNKNOWN")

    def test_http_worker_disables_proxies_and_redirects(self):
        mock_response = SimpleNamespace(status=200)
        output = io.StringIO()
        with patch.object(healthcheck.sys, "stdin", io.StringIO(json.dumps(self.probe()))), patch.object(healthcheck.urllib.request, "build_opener") as builder, contextlib.redirect_stdout(output):
            builder.return_value.open.return_value.__enter__.return_value = mock_response
            self.assertEqual(healthcheck.http_worker(), 0)
        self.assertEqual(json.loads(output.getvalue()), {"status_code": 200})
        self.assertEqual(builder.call_args.args[0].proxies, {})
        self.assertIsInstance(builder.call_args.args[1], healthcheck.NoRedirect)
        self.assertIsNone(healthcheck.NoRedirect().redirect_request(None, None, 302, "", {}, "http://example.invalid"))
        request = builder.return_value.open.call_args.args[0]
        self.assertEqual(request.get_method(), "GET")
        self.assertEqual(builder.return_value.open.call_args.kwargs["timeout"], 0.5)

    def test_http_worker_errors_are_sanitized(self):
        for error in (urllib.error.URLError("private URL"), urllib.error.HTTPError("private URL", 403, "private", {}, None)):
            output = io.StringIO()
            with patch.object(healthcheck.sys, "stdin", io.StringIO(json.dumps(self.probe()))), patch.object(healthcheck.urllib.request, "build_opener") as builder, contextlib.redirect_stdout(output):
                builder.return_value.open.side_effect = error
                healthcheck.http_worker()
            self.assertNotIn("private", output.getvalue())
            self.assertEqual(json.loads(output.getvalue()), {"status_code": 403} if isinstance(error, urllib.error.HTTPError) else {"unreachable": True})

    def test_probe_validation_rejects_credentials_and_unsafe_urls(self):
        for url in ("ftp://example.invalid/", "http://user:secret@example.invalid/", "http://example.invalid/?token=secret", "http://example.invalid/#private", "http:///path", "http://example.invalid:99999/", "http://example.invalid/\nsecret", "http://[broken"):
            with self.subTest(url=url), self.assertRaises(ValueError) as error:
                healthcheck.validate_probe({"name": "app", "url": url})
            self.assertNotIn(url, str(error.exception))

    def test_probe_validation_rejects_invalid_shapes_names_timeouts_and_statuses(self):
        cases = [None, {}, {"name": "../app", "url": "http://localhost/"}, {"name": "app", "url": "http://localhost/", "headers": {"Authorization": "secret"}}]
        cases += [dict(self.probe(), timeout_seconds=value) for value in (0, 16, True, float("nan"), "3")]
        cases += [dict(self.probe(), expected_statuses=value) for value in ([], [True], [999], "200", ["200"])]
        for probe in cases:
            with self.subTest(probe=probe), self.assertRaises(ValueError):
                healthcheck.validate_probe(probe)

    def invoke(self, args, config=None):
        output = io.StringIO()
        with patch.object(healthcheck, "disk_check", return_value=healthcheck.result("filesystem", "PASS", "capacity")), contextlib.redirect_stdout(output):
            if config is None:
                code = healthcheck.main(args + ["--json"])
            else:
                with patch.object(healthcheck, "read_text", return_value=json.dumps(config)):
                    code = healthcheck.main(["--config", "private-config"] + args + ["--json"])
        return code, json.loads(output.getvalue())

    def test_selected_healthy_report_exit_zero_has_timestamp_and_actions(self):
        code, report = self.invoke(SKIPS)
        self.assertEqual(code, 0)
        self.assertEqual(report["exit_code"], 0)
        self.assertEqual(report["schema"], 1)
        self.assertRegex(report["checked_at"], r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")
        self.assertIn("action", report["checks"][0])

    def test_unknown_selected_report_exit_one_and_failure_takes_precedence(self):
        args = [item for item in SKIPS if item not in ("--skip-docker", "--skip-backup", "--skip-http")]
        with patch.object(healthcheck, "docker_checks", return_value=[healthcheck.result("docker", "UNKNOWN", "blocked")]):
            code, report = self.invoke(args)
        self.assertEqual(code, 1)
        self.assertEqual([check["status"] for check in report["checks"]], ["PASS", "UNKNOWN", "UNKNOWN", "UNKNOWN"])
        with patch.object(healthcheck, "docker_checks", return_value=[healthcheck.result("container:app", "FAIL", "unhealthy")]):
            code, report = self.invoke(args)
        self.assertEqual(code, 2)
        self.assertEqual(report["exit_code"], 2)

    def test_config_and_cli_values_combine_with_cli_threshold_precedence(self):
        config = {"paths": ["/configured"], "mounts": ["/configured-mount"], "thresholds": {"min_free_percent": 15}}
        with patch.object(healthcheck, "read_text", return_value=json.dumps(config)), patch.object(healthcheck, "disk_check", return_value=healthcheck.result("filesystem", "PASS", "capacity")) as disk, contextlib.redirect_stdout(io.StringIO()):
            healthcheck.main(SKIPS + ["--config", "private", "--path", "/cli", "--mount", "/cli-mount", "--min-free-percent", "20"])
        self.assertEqual([call.args for call in disk.call_args_list], [("/", 20.0), ("/configured", 20.0), ("/cli", 20.0), ("/configured-mount", 20.0, True), ("/cli-mount", 20.0, True)])

    def test_configured_http_and_backup_are_selected_without_endpoint_leak(self):
        config = {"http_probes": [self.probe()], "backup_marker": "private-marker", "backup_max_age_hours": 12}
        args = [item for item in SKIPS if item not in ("--skip-backup", "--skip-http")]
        with patch.object(healthcheck, "http_check", return_value=healthcheck.result("application:media", "PASS", "HTTP 200")) as http, patch.object(healthcheck, "backup_check", return_value=healthcheck.result("backup-evidence", "PASS", "static byte recovery")) as backup:
            code, report = self.invoke(args, config)
        self.assertEqual(code, 0)
        backup.assert_called_once_with("private-marker", 12)
        self.assertEqual(http.call_args.args[0]["url"], self.probe()["url"])
        self.assertNotIn("private", json.dumps(report))

    def test_explicit_http_cli_default_and_duplicate_labels(self):
        with patch.object(healthcheck, "http_check", return_value=healthcheck.result("application:app", "PASS", "HTTP 200")) as http:
            self.invoke([item for item in SKIPS if item != "--skip-http"] + ["--http-probe", "app=http://localhost/health"])
        self.assertEqual(http.call_args.args[0]["timeout_seconds"], 3.0)
        self.assert_invalid(["--http-probe", "app=http://localhost/", "--http-probe", "app=http://localhost/other"])
        self.assert_invalid(["--http-probe", "http://localhost/"])

    def test_explicit_dns_cli_config_and_restart_options(self):
        config = {'dns_probes': [self.dns_probe()], 'check_container_restarts': True}
        flags = [item for item in SKIPS if item not in ('--skip-docker', '--skip-dns')]
        with patch.object(healthcheck, 'dns_check', return_value=healthcheck.result('dns:resolver', 'PASS', 'resolved')) as dns, patch.object(healthcheck, 'docker_checks', return_value=[]) as docker:
            self.assertEqual(self.invoke(flags, config)[0], 0)
        dns.assert_called_once_with(self.dns_probe())
        docker.assert_called_once_with([], True)
        with patch.object(healthcheck, 'dns_check', return_value=healthcheck.result('dns:resolver', 'PASS', 'resolved')) as dns:
            self.invoke([item for item in SKIPS if item != '--skip-dns'] + ['--dns-probe', 'resolver=private-host.example'])
        self.assertEqual(dns.call_args.args[0]['timeout_seconds'], 3.0)
        self.assert_invalid(['--dns-probe', 'resolver=private-host.example', '--dns-probe', 'resolver=other.example'])
        self.assert_invalid(['--dns-probe', 'private-host.example'])
        self.assert_invalid(['--skip-docker', '--check-container-restarts'])
        self.assert_invalid([], {'check_container_restarts': 1})
        self.assert_invalid([], {'dns_probes': 'wrong'})

    def test_unconfigured_dns_is_unknown_without_resolver_query(self):
        with patch.object(healthcheck, 'dns_check') as dns:
            code, report = self.invoke([item for item in SKIPS if item != '--skip-dns'])
        dns.assert_not_called()
        self.assertEqual(code, 1)
        self.assertEqual(report['checks'][-1]['status'], 'UNKNOWN')

    def assert_invalid(self, args, config=None):
        with patch.object(healthcheck, "disk_check") as disk, contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            if config is None:
                healthcheck.main(args)
            else:
                with patch.object(healthcheck, "read_text", return_value=json.dumps(config)):
                    healthcheck.main(["--config", "private"] + args)
        self.assertEqual(error.exception.code, 2)
        disk.assert_not_called()

    def test_invalid_expectations_fail_before_any_checks(self):
        for args in (["--skip-docker", "--expect-container", "required"], ["--expect-container", ""], ["--expect-container", "app other"], ["--expect-container", "app*"], ["--expect-container", "../app"]):
            with self.subTest(args=args):
                self.assert_invalid(args)
        self.assert_invalid(["--skip-docker"], {"expected_containers": ["required"]})

    def test_invalid_numeric_arguments_fail_before_any_checks(self):
        for value in ("-1", "101", "nan", "inf"):
            with self.subTest(value=value):
                self.assert_invalid(["--min-free-percent", value])
        for args in (["--memory-fail-percent", "20"], ["--load-fail-per-cpu", "0"], ["--temperature-warn-c", "80"], ["--pressure-fail-percent", "5"], ["--backup-max-age-hours", "0"], ["--backup-max-age-hours", "nan"]):
            with self.subTest(args=args):
                self.assert_invalid(args)

    def test_invalid_config_types_and_unknown_keys_fail_before_any_checks(self):
        configs = [[], {"unexpected": "private"}, {"paths": "wrong"}, {"mounts": [""]}, {"expected_containers": [None]}, {"thresholds": {"unknown": 1}}, {"thresholds": {"min_free_percent": True}}, {"thresholds": []}, {"thermal_path": 1}, {"backup_marker": ""}, {"backup_max_age_hours": True}, {"systemd_scope": "other"}, {"http_probes": "wrong"}, {"http_probes": [self.probe()] * 17}]
        for config in configs:
            with self.subTest(config=config):
                self.assert_invalid([], config)

    def test_unreadable_invalid_and_oversized_config_are_sanitized(self):
        for error in (PermissionError("private detail"), ValueError("private detail")):
            output = io.StringIO()
            with patch.object(healthcheck, "read_text", side_effect=error), contextlib.redirect_stderr(output), self.assertRaises(SystemExit):
                healthcheck.main(["--config", "private-path"])
            self.assertNotIn("private detail", output.getvalue())
            self.assertNotIn("private-path", output.getvalue())
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "oversized"
            path.write_text("x" * 65537)
            with self.assertRaises(ValueError):
                healthcheck.read_text(path)

    def test_argparse_diagnostics_do_not_echo_private_values(self):
        for flags in (["--min-free-percent", "PRIVATE-SECRET"], ["--PRIVATE-SECRET"],
                      ["--systemd-scope", "PRIVATE-SECRET"]):
            output = io.StringIO()
            with patch.object(healthcheck, "disk_check") as disk, contextlib.redirect_stderr(output), self.assertRaises(SystemExit) as error:
                healthcheck.main(flags)
            self.assertEqual(error.exception.code, 2)
            self.assertNotIn("PRIVATE-SECRET", output.getvalue())
            disk.assert_not_called()


    @unittest.skipUnless(hasattr(os, "mkfifo"), "POSIX FIFO required")
    def test_fifo_and_directory_marker_are_unknown_without_blocking(self):
        with tempfile.TemporaryDirectory() as directory:
            fifo = Path(directory) / "fifo"
            os.mkfifo(str(fifo), 0o600)
            for path in (fifo, Path(directory)):
                with self.subTest(kind=path.name):
                    script = ("import importlib.util,sys; "
                              "s=importlib.util.spec_from_file_location('healthcheck',sys.argv[1]); "
                              "m=importlib.util.module_from_spec(s); s.loader.exec_module(m); "
                              "print(m.backup_check(sys.argv[2],48)['status'])")
                    observed = subprocess.run([sys.executable, "-c", script, healthcheck.__file__, str(path)],
                                              capture_output=True, text=True, timeout=1, check=False)
                    self.assertEqual(observed.returncode, 0)
                    self.assertEqual(observed.stdout.strip(), "UNKNOWN")

    @unittest.skipUnless(hasattr(os, "mkfifo"), "POSIX FIFO required")
    def test_fifo_and_directory_config_fail_before_checks_without_blocking(self):
        with tempfile.TemporaryDirectory() as directory:
            fifo = Path(directory) / "fifo"
            os.mkfifo(str(fifo), 0o600)
            for path in (fifo, Path(directory)):
                with self.subTest(kind=path.name):
                    observed = subprocess.run([sys.executable, healthcheck.__file__, "--config", str(path)],
                                              capture_output=True, text=True, timeout=1, check=False)
                    self.assertEqual(observed.returncode, 2)
                    self.assertIn("Invalid healthcheck arguments or private configuration", observed.stderr)

    @unittest.skipUnless(os.name == "posix", "POSIX ownership and modes required")
    def test_private_marker_requires_regular_owned_0600_file(self):
        now = datetime(2026, 9, 29, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / "marker.json"
            marker.write_text(json.dumps(self.marker(now)), encoding="utf-8")
            for mode, expected in ((0o666, "UNKNOWN"), (0o644, "UNKNOWN"), (0o600, "PASS")):
                marker.chmod(mode)
                with self.subTest(mode=oct(mode)):
                    self.assertEqual(healthcheck.backup_check(marker, 48, now)["status"], expected)
            original_fstat = os.fstat
            def different_owner(descriptor):
                info = original_fstat(descriptor)
                return SimpleNamespace(st_mode=info.st_mode, st_uid=os.getuid() + 1)
            with patch.object(healthcheck.os, "fstat", side_effect=different_owner):
                self.assertEqual(healthcheck.backup_check(marker, 48, now)["status"], "UNKNOWN")

    @unittest.skipUnless(os.name == "posix", "POSIX ownership and modes required")
    def test_private_config_requires_regular_owned_0600_file(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "config.json"
            config.write_text("{}", encoding="utf-8")
            for mode in (0o666, 0o644):
                config.chmod(mode)
                with self.subTest(mode=oct(mode)):
                    self.assert_invalid(["--config", str(config)])
            config.chmod(0o600)
            self.assertEqual(self.invoke(SKIPS + ["--config", str(config)])[0], 0)

    @unittest.skipUnless(os.name == "posix", "POSIX symbolic links required")
    def test_private_symlinks_rejected_but_sensor_parent_links_supported(self):
        now = datetime(2026, 9, 29, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            marker = parent / "marker.json"
            marker.write_text(json.dumps(self.marker(now)), encoding="utf-8")
            marker.chmod(0o600)
            link = parent / "marker-link"
            link.symlink_to(marker)
            self.assertEqual(healthcheck.backup_check(link, 48, now)["status"], "UNKNOWN")
            config = parent / "config.json"
            config.write_text("{}", encoding="utf-8")
            config.chmod(0o600)
            config_link = parent / "config-link"
            config_link.symlink_to(config)
            self.assert_invalid(["--config", str(config_link)])
            real = parent / "thermal"
            real.mkdir()
            (real / "temp").write_text("45000", encoding="utf-8")
            sensor_link = parent / "thermal-link"
            sensor_link.symlink_to(real, target_is_directory=True)
            self.assertEqual(healthcheck.thermal_check(70, 80, sensor_link / "temp")["status"], "PASS")
            (real / "config.json").write_text("{}", encoding="utf-8")
            (real / "config.json").chmod(0o600)
            self.assertEqual(self.invoke(SKIPS + ["--config", str(sensor_link / "config.json")])[0], 0)

    def test_regular_zero_size_proc_sensor_file_can_be_read(self):
        actual = os.fstat
        def zero_size(descriptor):
            info = actual(descriptor)
            return SimpleNamespace(st_mode=info.st_mode, st_uid=info.st_uid, st_size=0)
        with tempfile.TemporaryDirectory() as directory:
            sensor = Path(directory) / "temp"
            sensor.write_text("45000", encoding="utf-8")
            with patch.object(healthcheck.os, "fstat", side_effect=zero_size):
                self.assertEqual(healthcheck.thermal_check(70, 80, sensor)["status"], "PASS")

    def test_deep_json_config_and_marker_errors_are_sanitized(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "deep-config.json"
            config.write_text("[" * 16000 + "0" + "]" * 16000, encoding="utf-8")
            config.chmod(0o600)
            self.assert_invalid(["--config", str(config)])
            marker = Path(directory) / "deep-marker.json"
            marker.write_text("[" * 1600 + "0" + "]" * 1600, encoding="utf-8")
            marker.chmod(0o600)
            self.assertEqual(healthcheck.backup_check(marker, 48)["status"], "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
