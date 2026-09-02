"""Small offline contract tests for the optional Kaishek preflight adapter."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import kaishek_preflight as adapter


class KaishekPreflightTests(unittest.TestCase):
    def test_contract_floor_and_timeout_match_current_preflight(self) -> None:
        # The contract floor is stable; the checked-out HEAD is resolved per
        # invocation and recorded separately, so newer mainline slices do not
        # require a parent-code edit.
        self.assertEqual(adapter.CLI_CONTRACT_COMMIT, "b306a95")
        self.assertEqual(adapter.DEFAULT_TIMEOUT_SECONDS, 180.0)

    def test_missing_checkout_is_not_applicable_and_is_archived(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            artifact = Path(temporary) / "evidence" / "open_kaishek-preflight.json"
            result = adapter.run_preflight(
                open_kaishek_root=Path(temporary) / "missing-open-kaishek",
                artifact_path=artifact,
            )
            self.assertEqual(result["status"], "not-applicable")
            self.assertEqual(result["result"], "NOT_APPLICABLE")
            self.assertFalse(result["ok"])
            self.assertEqual(result["reason"], "open_kaishek-root-missing")
            self.assertEqual(json.loads(artifact.read_text(encoding="utf-8")), result)

    def test_green_cli_report_preserves_command_and_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "open-kaishek"
            (root / ".git" / "refs" / "heads").mkdir(parents=True)
            commit = "0123456789abcdef0123456789abcdef01234567"
            (root / ".git" / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
            (root / ".git" / "refs" / "heads" / "main").write_text(commit + "\n", encoding="utf-8")
            jar = root / "kaishek-cli" / "target" / "kaishek-cli-0.1.0-SNAPSHOT.jar"
            jar.parent.mkdir(parents=True)
            jar.write_bytes(b"jar-fixture")
            artifact = Path(temporary) / "preflight.json"
            cli_report = {
                "schema": adapter.CLI_SCHEMA,
                "status": "GREEN",
                "tool_version": "0.1.0-cli",
                "profile_id": "ck3-1.19.0.6-zg361",
                "build_fingerprint": {"version": "1.19.0.6"},
                "fixture_id": "synthetic-361-014",
                "parser": {"status": "GREEN", "sha256": "fixture-hash"},
                "validator": {"status": "GREEN"},
                "ir": {"status": "GREEN"},
                "runtime": {"status": "GREEN"},
                "root_scan": {"parser": {"status": "SKIPPED"}},
                "provenance": {
                    "ck3_started": "false",
                    "save_mutated": "false",
                    "network_used": "false",
                    "root_sha256": "",
                },
            }
            completed = mock.Mock(returncode=0, stdout=json.dumps(cli_report), stderr="")
            with mock.patch.object(adapter.subprocess, "run", return_value=completed) as run:
                with mock.patch.object(adapter.shutil, "which", return_value="java.exe"):
                    result = adapter.run_preflight(
                        open_kaishek_root=root,
                        jar_path=jar,
                        root=Path(temporary) / "corpus",
                        profile="ck3-1.19.0.6-zg361",
                        fixture="synthetic-361-014",
                        artifact_path=artifact,
                        ck3_build="1.19.0.6",
                        ck3_exe_sha256="exe-hash",
                        open_kaishek_release="v0.1.0",
                        env={"XAR_KAISHEK_PREFLIGHT_TIMEOUT_SECONDS": ""},
                    )
            self.assertEqual(result["status"], "green")
            self.assertTrue(result["ok"])
            self.assertEqual(result["provenance"]["open_kaishek_commit"], commit)
            self.assertEqual(result["provenance"]["open_kaishek_release"], "v0.1.0")
            self.assertEqual(result["provenance"]["cli_contract_commit"], "b306a95")
            self.assertEqual(
                result["provenance"]["preflight_timeout_seconds"],
                adapter.DEFAULT_TIMEOUT_SECONDS,
            )
            command = run.call_args.args[0]
            self.assertIn("preflight", command)
            self.assertIn("--root", command)
            self.assertIn("--profile", command)
            self.assertIn("--fixture", command)
            self.assertEqual(
                run.call_args.kwargs["timeout"], adapter.DEFAULT_TIMEOUT_SECONDS
            )
            self.assertEqual(json.loads(artifact.read_text(encoding="utf-8")), result)

    def test_timeout_environment_override_is_forwarded_and_archived(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            jar = Path(temporary) / "cli.jar"
            jar.write_bytes(b"jar")
            cli_report = {
                "schema": adapter.CLI_SCHEMA,
                "status": "GREEN",
                "profile_id": "ck3-1.19.0.6-zg361",
                "fixture_id": "synthetic-361-014",
                "provenance": {
                    "ck3_started": "false",
                    "save_mutated": "false",
                    "network_used": "false",
                },
            }
            completed = mock.Mock(returncode=0, stdout=json.dumps(cli_report), stderr="")
            with mock.patch.object(adapter.subprocess, "run", return_value=completed) as run:
                with mock.patch.object(adapter.shutil, "which", return_value="java.exe"):
                    result = adapter.run_preflight(
                        jar_path=jar,
                        env={"XAR_KAISHEK_PREFLIGHT_TIMEOUT_SECONDS": "17.5"},
                    )
            self.assertEqual(result["status"], "green")
            self.assertEqual(result["provenance"]["preflight_timeout_seconds"], 17.5)
            self.assertEqual(run.call_args.kwargs["timeout"], 17.5)

    def test_legacy_cli_without_preflight_is_explicitly_unsupported(self) -> None:
        """A pre-b306a95 jar must not look like a transport failure or GREEN."""

        with tempfile.TemporaryDirectory() as temporary:
            jar = Path(temporary) / "legacy-cli.jar"
            jar.write_bytes(b"legacy-jar")
            completed = mock.Mock(
                returncode=0,
                stdout=json.dumps({"status": "UNSUPPORTED", "reason": "command:preflight"}),
                stderr="",
            )
            with mock.patch.object(adapter.subprocess, "run", return_value=completed):
                with mock.patch.object(adapter.shutil, "which", return_value="java.exe"):
                    result = adapter.run_preflight(
                        jar_path=jar,
                        env={
                            "XAR_OPEN_KAISHEK_COMMIT":
                                "fedcba9876543210fedcba9876543210fedcba98"
                        },
                    )
            self.assertEqual(result["status"], "unsupported")
            self.assertEqual(result["result"], "UNSUPPORTED")
            self.assertFalse(result["ok"])
            self.assertEqual(result["cli_status"], "UNSUPPORTED")
            self.assertEqual(result["reason"], "cli-unsupported-schema")
            self.assertEqual(
                result["provenance"]["open_kaishek_commit"],
                "fedcba9876543210fedcba9876543210fedcba98",
            )

    def test_schema_only_or_nested_unsupported_never_becomes_green(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            jar = Path(temporary) / "cli.jar"
            jar.write_bytes(b"jar")
            cli_report = {
                "schema": adapter.CLI_SCHEMA,
                "status": "GREEN",
                "tool_version": "0.1.0-cli",
                "profile_id": "ck3-1.19.0.6-zg361",
                "fixture_id": "synthetic-361-014",
                "semantic": "schema-only",
                "provenance": {
                    "ck3_started": "false",
                    "save_mutated": "false",
                    "network_used": "false",
                },
            }
            completed = mock.Mock(returncode=0, stdout=json.dumps(cli_report), stderr="")
            with mock.patch.object(adapter.subprocess, "run", return_value=completed):
                with mock.patch.object(adapter.shutil, "which", return_value="java.exe"):
                    result = adapter.run_preflight(
                        jar_path=jar,
                        profile="ck3-1.19.0.6-zg361",
                        fixture="synthetic-361-014",
                    )
            self.assertEqual(result["status"], "unsupported")
            self.assertEqual(result["result"], "UNSUPPORTED")
            self.assertFalse(result["ok"])
            self.assertEqual(result["reason"], "unsupported-semantic")

    def test_invalid_json_is_failed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            jar = Path(temporary) / "cli.jar"
            jar.write_bytes(b"jar")
            completed = mock.Mock(returncode=0, stdout="not-json\n", stderr="")
            with mock.patch.object(adapter.subprocess, "run", return_value=completed):
                with mock.patch.object(adapter.shutil, "which", return_value="java.exe"):
                    result = adapter.run_preflight(jar_path=jar)
            self.assertEqual(result["status"], "failed")
            self.assertEqual(result["reason"], "invalid-cli-json")
            self.assertFalse(result["ok"])


if __name__ == "__main__":
    unittest.main()
