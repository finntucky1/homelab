"""Check failure handling without accessing a Docker daemon or the home server."""

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location(
    "healthcheck", Path(__file__).resolve().parents[1] / "scripts" / "healthcheck.py"
)
healthcheck = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(healthcheck)


class HealthCheckTests(unittest.TestCase):
    def test_free_space_threshold(self):
        with tempfile.TemporaryDirectory() as directory:
            for free, expected in ((25, "PASS"), (10, "PASS"), (9, "FAIL")):
                with self.subTest(free=free), patch.object(
                    healthcheck.shutil, "disk_usage",
                    return_value=SimpleNamespace(total=100, free=free),
                ):
                    self.assertEqual(healthcheck.disk_check(directory, 10)["status"], expected)

    def test_missing_path_and_unmounted_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing"
            self.assertEqual(healthcheck.disk_check(missing, 10)["status"], "FAIL")
            self.assertEqual(healthcheck.disk_check(directory, 10, True)["status"], "FAIL")

    def test_missing_docker(self):
        with patch.object(healthcheck.shutil, "which", return_value=None):
            self.assertEqual(healthcheck.docker_checks()[0]["status"], "WARN")
            self.assertEqual(healthcheck.docker_checks(["required"])[0]["status"], "FAIL")

    def test_docker_state_classification(self):
        containers = [
            {"Names": "healthy", "State": "running", "Status": "Up 1 hour (healthy)"},
            {"Names": "no-probe", "State": "running", "Status": "Up 1 hour"},
            {"Names": "unhealthy", "State": "running", "Status": "Up 1 hour (unhealthy)"},
            {"Names": "starting", "State": "running", "Status": "Up 2 seconds (health: starting)"},
            {"Names": "stopped", "State": "exited", "Status": "Exited (0)"},
            {"Names": "restarting", "State": "restarting", "Status": "Restarting (1)"},
        ]
        response = SimpleNamespace(returncode=0, stdout="\n".join(json.dumps(c) for c in containers))
        with patch.object(healthcheck.shutil, "which", return_value="/fake/docker"), patch.object(
            healthcheck.subprocess, "run", return_value=response
        ) as command:
            checks = healthcheck.docker_checks()
        self.assertEqual([c["status"] for c in checks], ["PASS", "WARN", "FAIL", "WARN", "WARN", "FAIL"])
        self.assertIn("not reported", checks[1]["detail"])
        self.assertEqual(command.call_args.args[0][1:3], ["ps", "--all"])

    def test_docker_error_timeout_empty_and_bad_output(self):
        responses = [
            (SimpleNamespace(returncode=1, stdout=""), "FAIL"),
            (SimpleNamespace(returncode=0, stdout=""), "WARN"),
            (SimpleNamespace(returncode=0, stdout="invalid json"), "FAIL"),
            (SimpleNamespace(returncode=0, stdout='{"Names": "incomplete"}'), "FAIL"),
            (SimpleNamespace(returncode=0, stdout='null'), "FAIL"),
            (SimpleNamespace(returncode=0, stdout='[]'), "FAIL"),
            (SimpleNamespace(returncode=0, stdout='{"Names": "app", "State": true, "Status": "Up"}'), "FAIL"),
            (SimpleNamespace(returncode=0, stdout='{"Names": "app", "State": "running", "Status": ""}'), "FAIL"),
        ]
        with patch.object(healthcheck.shutil, "which", return_value="/fake/docker"):
            for response, expected in responses:
                with self.subTest(response=response), patch.object(
                    healthcheck.subprocess, "run", return_value=response
                ):
                    self.assertEqual(healthcheck.docker_checks()[0]["status"], expected)
            with patch.object(healthcheck.subprocess, "run", side_effect=subprocess.TimeoutExpired("docker", 10)):
                self.assertEqual(healthcheck.docker_checks()[0]["status"], "FAIL")

    def test_expected_container_missing_from_empty_or_nonempty_output(self):
        present = json.dumps({"Names": "other", "State": "running", "Status": "Up 1 hour (healthy)"})
        with patch.object(healthcheck.shutil, "which", return_value="/fake/docker"):
            for stdout in ("", present):
                with self.subTest(stdout=stdout), patch.object(
                    healthcheck.subprocess, "run", return_value=SimpleNamespace(returncode=0, stdout=stdout)
                ):
                    checks = healthcheck.docker_checks(["required", "required"])
                required = [check for check in checks if check["name"] == "container:required"]
                self.assertEqual(len(required), 1)
                self.assertEqual(required[0]["status"], "FAIL")
                self.assertIn("missing", required[0]["detail"])

    def test_expected_container_must_run_and_report_health_to_pass(self):
        cases = [
            ("running", "Up 1 hour (healthy)", "PASS"),
            ("running", "Up 1 hour", "WARN"),
            ("running", "Up 2 seconds (health: starting)", "WARN"),
            ("running", "Up 1 hour (unhealthy)", "FAIL"),
            ("exited", "Exited (0)", "FAIL"),
            ("paused", "Up 1 hour (Paused)", "FAIL"),
        ]
        with patch.object(healthcheck.shutil, "which", return_value="/fake/docker"):
            for state, status, expected in cases:
                stdout = json.dumps({"Names": "required", "State": state, "Status": status})
                with self.subTest(state=state, status=status), patch.object(
                    healthcheck.subprocess, "run", return_value=SimpleNamespace(returncode=0, stdout=stdout)
                ):
                    checks = healthcheck.docker_checks(["required"])
                self.assertEqual(len(checks), 1)
                self.assertEqual(checks[0]["status"], expected)

    def test_expected_container_name_is_exact(self):
        stdout = json.dumps({"Names": "app-2", "State": "running", "Status": "Up 1 hour (healthy)"})
        with patch.object(healthcheck.shutil, "which", return_value="/fake/docker"), patch.object(
            healthcheck.subprocess, "run", return_value=SimpleNamespace(returncode=0, stdout=stdout)
        ):
            checks = healthcheck.docker_checks(["app"])
        self.assertEqual(checks[-1]["name"], "container:app")
        self.assertEqual(checks[-1]["status"], "FAIL")

    def test_duplicate_container_names_cannot_pass(self):
        line = json.dumps({"Names": "app", "State": "running", "Status": "Up 1 hour (healthy)"})
        with patch.object(healthcheck.shutil, "which", return_value="/fake/docker"), patch.object(
            healthcheck.subprocess, "run", return_value=SimpleNamespace(returncode=0, stdout=line + "\n" + line)
        ):
            self.assertEqual(healthcheck.docker_checks(["app"])[0]["status"], "FAIL")

    def test_docker_execution_and_decoding_errors_are_reported_without_raw_output(self):
        errors = [OSError("sensitive diagnostic"), UnicodeDecodeError("utf-8", b"\xff", 0, 1, "sensitive diagnostic")]
        with patch.object(healthcheck.shutil, "which", return_value="/fake/docker"):
            for error in errors:
                with self.subTest(error=type(error).__name__), patch.object(
                    healthcheck.subprocess, "run", side_effect=error
                ):
                    checks = healthcheck.docker_checks()
                self.assertEqual(checks[0]["status"], "FAIL")
                self.assertNotIn("sensitive diagnostic", checks[0]["detail"])

    def test_expected_missing_container_sets_json_exit_code(self):
        output = io.StringIO()
        with patch.object(healthcheck, "disk_check", return_value=healthcheck.result("filesystem", "PASS", "enough capacity")), patch.object(
            healthcheck.shutil, "which", return_value="/fake/docker"
        ), patch.object(healthcheck.subprocess, "run", return_value=SimpleNamespace(returncode=0, stdout="")), contextlib.redirect_stdout(output):
            exit_code = healthcheck.main(["--expect-container", "required", "--json"])
        report = json.loads(output.getvalue())
        self.assertEqual(exit_code, 2)
        self.assertEqual(report["exit_code"], 2)
        self.assertEqual(report["checks"][-1]["name"], "container:required")

    def test_invalid_expectations_fail_before_any_checks(self):
        arguments = [
            ["--skip-docker", "--expect-container", "required"],
            ["--expect-container", ""],
            ["--expect-container", "app other"],
            ["--expect-container", "app*"],
            ["--expect-container", "../app"],
        ]
        for args in arguments:
            with self.subTest(args=args), patch.object(healthcheck, "disk_check") as disk, patch.object(
                healthcheck, "docker_checks"
            ) as docker, contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as exc:
                healthcheck.main(args)
            self.assertEqual(exc.exception.code, 2)
            disk.assert_not_called()
            docker.assert_not_called()

    def test_json_and_failure_exit(self):
        output = io.StringIO()
        with patch.object(healthcheck, "disk_check", return_value=healthcheck.result("filesystem", "FAIL", "low capacity")), contextlib.redirect_stdout(output):
            exit_code = healthcheck.main(["--skip-docker", "--json"])
        report = json.loads(output.getvalue())
        self.assertEqual(exit_code, 2)
        self.assertEqual(report["exit_code"], 2)
        self.assertEqual(report["checks"][0]["status"], "FAIL")

    def test_invalid_thresholds(self):
        for value in ("-1", "101", "nan", "inf"):
            with self.subTest(value=value), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as exc:
                healthcheck.main(["--min-free-percent", value])
            self.assertEqual(exc.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
