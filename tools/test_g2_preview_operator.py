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
    def test_r778_checkpoint_binding_is_the_authoritative_sha256(self) -> None:
        self.assertEqual(
            g2_preview_operator.R778_SOURCE_CHECKPOINT_SHA256,
            "2c0f4333ae186ee91f560ad7d14abb2f2e29aaa1b4d2eacfefe0c9a8e1e505e3",
        )
        self.assertEqual(len(g2_preview_operator.R778_SOURCE_CHECKPOINT_SHA256), 64)

    def test_private_timeline_action_is_one_exact_bounded_command(self) -> None:
        args = g2_preview_operator.parser().parse_args([
            "continue-death-succession-modal-v1",
            "--manifest",
            "manifest.json",
            "--output",
            "attempt",
            "--private-timeline-action-round-id",
            "R778",
            "--expected-date-raw",
            "53411568",
        ])
        command = g2_preview_operator.death_succession_modal_action_command(
            ["python", "agent.py"],
            timeout=390,
            readiness_timeout=300,
            private_timeline_action_round_id_value=(
                args.private_timeline_action_round_id
            ),
            expected_played_character_id=35465,
            expected_episode_run_id="native-35465-cbdf997e3d80",
            expected_date_raw=args.expected_date_raw,
        )
        self.assertEqual(command, [
            "python",
            "agent.py",
            "native-continue-death-succession-modal-v1",
            "--timeout",
            "390",
            "--readiness-timeout",
            "300",
            "--cold-start-checkpoint",
            "--private-timeline-action-round-id",
            "R778",
            "--expected-played-character-id",
            "35465",
            "--expected-episode-run-id",
            "native-35465-cbdf997e3d80",
            "--expected-date-raw",
            "53411568",
        ])
        self.assertNotIn("native-auto-run", command)
        self.assertNotIn("arrange-marriage", " ".join(command))
        self.assertNotIn("death-terminal", command)

    def test_private_timeline_action_receipt_requires_material_green(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = root / "state"
            save = state / "profile" / "save games" / "xar_checkpoint.ck3"
            driver = state / "native-session" / "driver-state.json"
            game_exe = root / "game" / "binaries" / "ck3.exe"
            dll = root / "bridge.dll"
            injector = root / "injector.exe"
            save.parent.mkdir(parents=True)
            driver.parent.mkdir(parents=True)
            game_exe.parent.mkdir(parents=True)
            save.write_bytes(b"sealed")
            game_exe.write_bytes(b"ck3")
            dll.write_bytes(b"dll")
            injector.write_bytes(b"injector")
            driver.write_text(json.dumps({
                "episode_character_id": 35465,
                "episode_run_id": "native-35465-cbdf997e3d80",
            }), encoding="utf-8")
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({
                "python": str(root / "python.exe"),
                "source_repo": str(root / "repo"),
                "source_commit": "c" * 40,
                "state_dir": str(state),
                "game_dir": str(root / "game"),
                "pipe": r"\\.\pipe\timeline-action-test",
                "dll": str(dll),
                "injector": str(injector),
                "timeout_seconds": 390,
                "readiness_timeout_seconds": 300,
            }), encoding="utf-8")
            output = root / "attempt"

            def sealed_sha(path: Path) -> str:
                if path == save and path.read_bytes() == b"sealed":
                    return g2_preview_operator.R778_SOURCE_CHECKPOINT_SHA256
                if path == driver and "command_history" not in json.loads(
                    path.read_text(encoding="utf-8")
                ):
                    return g2_preview_operator.R778_SOURCE_DRIVER_STATE_SHA256
                if path == game_exe:
                    return g2_preview_operator.R778_CK3_EXE_SHA256
                if path == dll:
                    return g2_preview_operator.R781_PRIVATE_BRIDGE_SHA256
                if path == injector:
                    return g2_preview_operator.R778_INJECTOR_SHA256
                return hashlib.sha256(path.read_bytes()).hexdigest()

            def fake_run(command, stdout_path, stderr_path):
                stderr_path.write_text("", encoding="utf-8")
                if "native-one-generation-preflight" in command:
                    stdout_path.write_text("{}\n", encoding="utf-8")
                    return 0
                self.assertIn(
                    "native-continue-death-succession-modal-v1", command
                )
                save.write_bytes(b"new-material-checkpoint")
                checkpoint_sha = hashlib.sha256(save.read_bytes()).hexdigest()
                driver.write_text(json.dumps({
                    "episode_character_id": 35465,
                    "episode_run_id": "native-35465-cbdf997e3d80",
                    "command_history": [
                        {"index": index, "command": step, "ok": True}
                        for index, step in enumerate((
                            "continue-as-reconciled-successor",
                            "query-campaign-root-context-v1",
                            "save-checkpoint",
                            "restore-checkpoint",
                            "life-advance",
                            "save-checkpoint",
                        ), start=1)
                    ],
                }), encoding="utf-8")
                ack = {
                    "step": "continue-death-succession-modal-v1",
                    "accepted": True,
                    "status": "submitted",
                    "close_invocations": 1,
                    "material_result_verified": False,
                }
                report = {
                    "ok": True,
                    "status": "GREEN_MATERIAL",
                    "round": "R778",
                    "checks": {"all_material_contracts": True},
                    "action_counts": {
                        "close": 1, "life_advance": 1, "checkpoint": 1
                    },
                    "forbidden_action_counts": {
                        "marriage": 0,
                        "death_terminal": 0,
                        "python_successor_continuation": 0,
                        "generic_ui_input": 0,
                        "other_gameplay": 0,
                    },
                    "action_result": {
                        "starting_date_raw": 53411568,
                        "ending_date_raw": 53411572,
                        "submission_ack": ack,
                        "initial_query": {"observation_revision": 4573},
                        "postcondition_query": {"observation_revision": 4575},
                        "life_advance_result": {"step": "life-advance"},
                    },
                    "checkpoint": {
                        "history_index": 6,
                        "sha256": checkpoint_sha,
                        "date_raw": 53411572,
                    },
                    "cleanup": {"ok": True, "tree_gone": True},
                }
                stdout_path.write_text(
                    json.dumps(report) + "\n", encoding="utf-8"
                )
                return 0

            args = g2_preview_operator.parser().parse_args([
                "continue-death-succession-modal-v1",
                "--manifest",
                str(manifest),
                "--output",
                str(output),
                "--private-timeline-action-round-id",
                "R778",
                "--expected-date-raw",
                "53411568",
            ])
            with (
                mock.patch.object(
                    g2_preview_operator,
                    "frozen_source_identity",
                    return_value={"repo": str(root / "repo"), "commit": "c" * 40},
                ),
                mock.patch.object(
                    g2_preview_operator, "sha256", side_effect=sealed_sha
                ),
                mock.patch.object(
                    g2_preview_operator, "run_logged", side_effect=fake_run
                ),
            ):
                result = (
                    g2_preview_operator.command_continue_death_succession_modal_v1(
                        args
                    )
                )
            self.assertEqual(result, 0)
            receipt = json.loads(
                (output / "operator-receipt.json").read_text(encoding="utf-8")
            )
            self.assertEqual(receipt["status"], "GREEN_MATERIAL")
            self.assertTrue(receipt["exact_sealed_input"])
            self.assertEqual(receipt["close_actions"], 1)
            self.assertEqual(receipt["life_advance_actions"], 1)
            self.assertEqual(receipt["checkpoint_actions"], 1)
            self.assertFalse(receipt["submission_ack"]["material_result_verified"])
            self.assertEqual(receipt["checkpoint"]["history_index"], 6)

            save.write_bytes(b"sealed")
            driver.write_text(json.dumps({
                "episode_character_id": 35465,
                "episode_run_id": "native-35465-cbdf997e3d80",
            }), encoding="utf-8")
            red_output = root / "attempt-unconfirmed"

            def fake_unconfirmed_run(command, stdout_path, stderr_path):
                stderr_path.write_text("", encoding="utf-8")
                if "native-one-generation-preflight" in command:
                    stdout_path.write_text("{}\n", encoding="utf-8")
                    return 0
                ack = {
                    "step": "continue-death-succession-modal-v1",
                    "accepted": True,
                    "status": "submitted",
                    "close_invocations": 1,
                    "material_result_verified": False,
                }
                post_queries = [
                    {
                        "observation_revision": revision,
                        "current_timeline_blocker_context": {
                            "identity": "death_succession_modal"
                        },
                    }
                    for revision in (4575, 4576)
                ]
                report = {
                    "ok": False,
                    "status": "RED_SUBMITTED_UNCONFIRMED",
                    "round": "R779",
                    "checks": {"submitted_unconfirmed_preserved": True},
                    "action_counts": {
                        "close": 1, "life_advance": 0, "checkpoint": 0
                    },
                    "forbidden_action_counts": {
                        "marriage": 0,
                        "death_terminal": 0,
                        "python_successor_continuation": 0,
                        "generic_ui_input": 0,
                        "other_gameplay": 0,
                    },
                    "action_result": {
                        **ack,
                        "status": "submitted_unconfirmed",
                        "submission_ack": ack,
                        "initial_query": {"observation_revision": 4573},
                        "postcondition_queries": post_queries,
                        "postcondition_query": post_queries[-1],
                        "post_query_attempts": [
                            {"attempt": index, "query": query, "error": None}
                            for index, query in enumerate(post_queries, start=1)
                        ],
                        "post_failure": "bounded post-Close queries exhausted",
                        "life_advance_result": None,
                        "starting_date_raw": 53411568,
                        "ending_date_raw": 53411568,
                    },
                    "checkpoint": None,
                    "cleanup": {"ok": True, "tree_gone": True},
                }
                stdout_path.write_text(
                    json.dumps(report) + "\n", encoding="utf-8"
                )
                return 1

            red_args = g2_preview_operator.parser().parse_args([
                "continue-death-succession-modal-v1",
                "--manifest",
                str(manifest),
                "--output",
                str(red_output),
                "--private-timeline-action-round-id",
                "R779",
                "--expected-date-raw",
                "53411568",
            ])
            with (
                mock.patch.object(
                    g2_preview_operator,
                    "frozen_source_identity",
                    return_value={"repo": str(root / "repo"), "commit": "c" * 40},
                ),
                mock.patch.object(
                    g2_preview_operator, "sha256", side_effect=sealed_sha
                ),
                mock.patch.object(
                    g2_preview_operator,
                    "run_logged",
                    side_effect=fake_unconfirmed_run,
                ),
            ):
                red_result = (
                    g2_preview_operator.command_continue_death_succession_modal_v1(
                        red_args
                    )
                )
            self.assertEqual(red_result, 1)
            red_receipt = json.loads(
                (red_output / "operator-receipt.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                red_receipt["status"], "RED_SUBMITTED_UNCONFIRMED"
            )
            self.assertEqual(red_receipt["close_actions"], 1)
            self.assertEqual(red_receipt["life_advance_actions"], 0)
            self.assertEqual(red_receipt["checkpoint_actions"], 0)
            self.assertEqual(
                red_receipt["submission_ack"]["close_invocations"], 1
            )
            self.assertEqual(len(red_receipt["postcondition_queries"]), 2)
            self.assertEqual(len(red_receipt["post_query_attempts"]), 2)
            self.assertEqual(
                red_receipt["checkpoint_sha256_before"],
                red_receipt["checkpoint_sha256_after"],
            )

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

    def test_private_timeline_query_receipt_allows_exact_cold_restore_bookkeeping(
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
                "checks": {
                    "date_unchanged": True,
                    "single_cold_restore_bookkeeping": True,
                    "query_history_unchanged": True,
                    "driver_history_matches_query_after": True,
                    "cleanup_proven": True,
                },
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
                    driver.write_text(json.dumps({
                        "episode_character_id": 35465,
                        "episode_run_id": "native-35465-test",
                        "command_history": [{
                            "index": 1,
                            "command": "restore-checkpoint",
                            "ok": True,
                        }],
                    }), encoding="utf-8")
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
            self.assertFalse(receipt["driver_state_unchanged"])
            self.assertTrue(
                receipt["driver_state_cold_restore_bookkeeping_exact"]
            )
            self.assertTrue(receipt["driver_state_query_history_unchanged"])
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
