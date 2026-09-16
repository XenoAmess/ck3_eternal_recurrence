from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from tools import g2_preview_operator


class G2PreviewOperatorTest(unittest.TestCase):
    def test_private_timeline_query_is_a_dedicated_single_query_command(self) -> None:
        args = g2_preview_operator.parser().parse_args([
            "query-current-timeline-blocker-context-v1",
            "--manifest",
            "manifest.json",
            "--output",
            "attempt",
            "--private-timeline-query-round-id",
            "R776",
        ])
        command = g2_preview_operator.timeline_blocker_query_command(
            ["python", "agent.py"],
            timeout=390,
            readiness_timeout=300,
            private_timeline_query_round_id_value=(
                args.private_timeline_query_round_id
            ),
        )
        self.assertEqual(command, [
            "python",
            "agent.py",
            "native-query-current-timeline-blocker-context-v1",
            "--timeout",
            "390",
            "--readiness-timeout",
            "300",
            "--cold-start-checkpoint",
            "--private-timeline-query-round-id",
            "R776",
        ])
        self.assertNotIn("native-auto-run", command)
        self.assertNotIn("life-advance", command)
        self.assertNotIn("death-terminal", command)
        with self.assertRaises(SystemExit):
            g2_preview_operator.parser().parse_args([
                "query-current-timeline-blocker-context-v1",
                "--manifest",
                "manifest.json",
                "--output",
                "attempt",
                "--private-timeline-query-round-id",
                "R776A",
            ])

    def test_private_timeline_query_receipt_requires_unchanged_state_and_cleanup(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = root / "state"
            save = state / "profile" / "save games" / "xar_checkpoint.ck3"
            driver = state / "native-session" / "driver-state.json"
            save.parent.mkdir(parents=True)
            driver.parent.mkdir(parents=True)
            save.write_bytes(b"checkpoint")
            driver.write_text(json.dumps({
                "episode_character_id": 35465,
                "episode_run_id": "native-35465-test",
            }), encoding="utf-8")
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({
                "python": str(root / "python.exe"),
                "source_repo": str(root / "repo"),
                "source_commit": "b" * 40,
                "state_dir": str(state),
                "game_dir": str(root / "game"),
                "pipe": r"\\.\pipe\timeline-test",
                "dll": str(root / "bridge.dll"),
                "injector": str(root / "injector.exe"),
                "episode_character_id": 35465,
                "episode_run_id": "native-35465-test",
                "timeout_seconds": 390,
                "readiness_timeout_seconds": 300,
            }), encoding="utf-8")
            output = root / "attempt"
            agent_report = {
                "ok": True,
                "status": "GREEN_READ_ONLY",
                "round": "R776",
                "before": {"date_raw": 53411568},
                "after": {"date_raw": 53411568},
                "checks": {"date_unchanged": True, "cleanup_proven": True},
                "query_envelope": {
                    "step": "query-current-timeline-blocker-context-v1",
                    "private_build": True,
                    "read_only": True,
                    "advertised": False,
                },
                "cleanup": {"ok": True, "tree_gone": True},
            }

            def fake_run(command, stdout_path, stderr_path):
                stderr_path.write_text("", encoding="utf-8")
                if "native-one-generation-preflight" in command:
                    stdout_path.write_text("{}\n", encoding="utf-8")
                else:
                    stdout_path.write_text(
                        json.dumps(agent_report) + "\n", encoding="utf-8"
                    )
                return 0

            args = g2_preview_operator.parser().parse_args([
                "query-current-timeline-blocker-context-v1",
                "--manifest",
                str(manifest),
                "--output",
                str(output),
                "--private-timeline-query-round-id",
                "R776",
            ])
            with (
                mock.patch.object(
                    g2_preview_operator,
                    "frozen_source_identity",
                    return_value={"repo": str(root / "repo"), "commit": "b" * 40},
                ),
                mock.patch.object(g2_preview_operator, "run_logged", side_effect=fake_run),
            ):
                result = g2_preview_operator.command_query_current_timeline_blocker_context_v1(
                    args
                )
            self.assertEqual(result, 0)
            receipt = json.loads(
                (output / "operator-receipt.json").read_text(encoding="utf-8")
            )
            self.assertEqual(receipt["status"], "GREEN_READ_ONLY")
            self.assertTrue(receipt["checkpoint_unchanged"])
            self.assertTrue(receipt["driver_state_unchanged"])
            self.assertTrue(receipt["date_unchanged"])
            self.assertEqual(receipt["round"], "R776")
            self.assertEqual(receipt["gameplay_actions"], 0)
            self.assertEqual(receipt["query_envelope"]["read_only"], True)
            self.assertEqual(receipt["cleanup"]["ok"], True)

    def test_private_faction_round_is_narrowly_forwarded(self) -> None:
        args = g2_preview_operator.parser().parse_args([
            "run",
            "--manifest",
            "manifest.json",
            "--output",
            "attempt",
            "--private-faction-round-id",
            "R765",
        ])
        command = g2_preview_operator.native_auto_run_command(
            ["python", "agent.py"],
            turns=40,
            timeout=7200,
            readiness_timeout=300,
            private_faction_round_id_value=args.private_faction_round_id,
        )
        self.assertEqual(command[-3:], [
            "--allow-private-faction-gift-formal-trial",
            "--private-faction-round-id",
            "R765",
        ])
        self.assertNotIn("--allow-private-faction-gift-formal-trial", g2_preview_operator.native_auto_run_command(
            ["python", "agent.py"],
            turns=40,
            timeout=7200,
            readiness_timeout=300,
            private_faction_round_id_value=None,
        ))
        with self.assertRaises(SystemExit):
            g2_preview_operator.parser().parse_args([
                "run", "--manifest", "manifest.json", "--output", "attempt",
                "--private-faction-round-id", "<ALLOCATED_ROUND>",
            ])

    def test_verify_zip_binds_exact_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "preview.zip"
            archive.write_bytes(b"frozen-preview")
            expected = hashlib.sha256(archive.read_bytes()).hexdigest()
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = g2_preview_operator.command_verify_zip(argparse.Namespace(
                    zip=archive,
                    expected_sha256=expected,
                ))
            self.assertEqual(result, 0)
            self.assertEqual(json.loads(output.getvalue())["sha256"], expected)
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                g2_preview_operator.command_verify_zip(argparse.Namespace(
                    zip=archive,
                    expected_sha256="0" * 64,
                ))

    def test_stop_request_is_created_once_from_manifest_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = root / "state"
            state.mkdir()
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({
                "python": str(root / "python.exe"),
                "source_repo": str(root / "repo"),
                "state_dir": str(state),
                "game_dir": str(root / "game"),
                "pipe": r"\\.\pipe\test",
                "dll": str(root / "bridge.dll"),
                "injector": str(root / "injector.exe"),
            }), encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = g2_preview_operator.command_request_stop(argparse.Namespace(manifest=manifest))
            self.assertEqual(result, 0)
            stop_path = state / "native-auto-run.stop"
            self.assertEqual(stop_path.read_text(encoding="utf-8"), "stop\n")
            with self.assertRaises(FileExistsError):
                g2_preview_operator.command_request_stop(argparse.Namespace(manifest=manifest))


if __name__ == "__main__":
    unittest.main()
