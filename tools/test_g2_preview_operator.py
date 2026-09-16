from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

from tools import g2_preview_eligibility, g2_preview_operator


class G2PreviewOperatorTest(unittest.TestCase):
    def test_eligibility_active_context_contract_is_exact_and_additive(self) -> None:
        self.assertEqual(
            g2_preview_eligibility._active_context_contract({}),
            {
                "war_ids": [],
                "army_ids": [],
                "active_event": None,
                "pending_character_interaction": None,
                "source": "legacy-default",
            },
        )
        manifest = {
            "expected_active_context": {
                "war_ids": [5],
                "army_ids": [33],
                "active_event": None,
                "pending_character_interaction": None,
            }
        }
        self.assertEqual(
            g2_preview_eligibility._active_context_contract(manifest),
            {
                **manifest["expected_active_context"],
                "source": "manifest",
            },
        )
        with self.assertRaisesRegex(ValueError, "exactly"):
            g2_preview_eligibility._active_context_contract({
                "expected_active_context": {"war_ids": [5]}
            })
        with self.assertRaisesRegex(ValueError, "unique positive"):
            g2_preview_eligibility._active_context_contract({
                "expected_active_context": {
                    **manifest["expected_active_context"],
                    "war_ids": [5, 5],
                }
            })

    def test_eligibility_matches_frozen_continuation_context(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = root / "state"
            checkpoint = state / "profile" / "save games" / "xar_checkpoint.ck3"
            source = root / "source.ck3"
            checkpoint.parent.mkdir(parents=True)
            checkpoint.write_bytes(b"checkpoint")
            source.write_bytes(b"checkpoint")
            digest = hashlib.sha256(b"checkpoint").hexdigest()
            manifest = {
                "source_save": str(source),
                "checkpoint_sha256": digest,
                "state_dir": str(state),
                "episode_character_id": 31853,
                "date_raw": 53145000,
                "supported_government": "feudal_government",
                "xar_enabled": "xar_off",
                "succession_lifecycle": "ordinary_campaign_succession",
                "ordinary_campaign_no_pact": True,
                "expected_active_context": {
                    "war_ids": [5],
                    "army_ids": [33],
                    "active_event": None,
                    "pending_character_interaction": None,
                },
            }
            stage = {
                "ok": True,
                "readiness": {
                    "played_character_id": 31853,
                    "date_raw": 53145000,
                    "active_context": {
                        "war_ids": [5],
                        "army_ids": [33],
                        "active_event": None,
                        "pending_character_interaction": None,
                    },
                },
                "sequence": {
                    "first_query": {
                        "campaign_root_context": {
                            "government": {"key": "feudal_government"},
                            "selected_game_rule_tokens": ["xar_off"],
                        }
                    }
                },
            }
            checks = g2_preview_eligibility._qualify(
                manifest,
                stage,
                {"ck3_process_inventory": lambda: {"processes": []}},
            )
            self.assertTrue(checks["active_context_matches_manifest"])
            self.assertTrue(all(checks.values()))
            stage["readiness"]["active_context"]["war_ids"] = [6]
            self.assertFalse(g2_preview_eligibility._qualify(
                manifest,
                stage,
                {"ck3_process_inventory": lambda: {"processes": []}},
            )["active_context_matches_manifest"])

    def test_eligibility_forwards_resolved_rule_to_live_stage(self) -> None:
        legacy_binding = {
            "schema": "xar.ck3.succession-lifecycle-binding/v1",
            "lifecycle": "rogue_one_life",
            "xar_enabled": "xar_on",
            "pact_contract": "terminal_settlement_required",
            "source": "legacy-driver-default",
            "environment_sha256": None,
        }
        ordinary_binding = {
            "schema": "xar.ck3.succession-lifecycle-binding/v1",
            "lifecycle": "ordinary_campaign_succession",
            "xar_enabled": "xar_off",
            "pact_contract": "absent_by_fresh_campaign_xar_off_contract",
            "source": "prepared-environment-manifest",
            "environment_sha256": "e" * 64,
        }
        cases = (
            ({}, "xar_on", legacy_binding),
            (
                {
                    "xar_enabled": "xar_off",
                    "succession_lifecycle": "ordinary_campaign_succession",
                    "ordinary_campaign_no_pact": True,
                },
                "xar_off",
                ordinary_binding,
            ),
        )
        for lifecycle, expected_rule, expected_binding in cases:
            with (
                self.subTest(expected=expected_rule),
                tempfile.TemporaryDirectory() as directory,
            ):
                root = Path(directory)
                output = root / "eligibility"
                manifest = {
                    **lifecycle,
                    "source_repo": str(root / "repo"),
                    "timeout_seconds": 390,
                    "session_ceiling_seconds": 480,
                    "readiness_timeout_seconds": 300,
                    "pipe": r"\\.\pipe\eligibility-test",
                    "dll": str(root / "bridge.dll"),
                    "injector": str(root / "injector.exe"),
                }
                run_live_stage = mock.Mock(return_value={"ok": True})
                backend = {
                    "controlled": SimpleNamespace(
                        _run_live_stage=run_live_stage
                    ),
                    "NativeBridgeLaunchConfig": mock.Mock(
                        return_value=SimpleNamespace()
                    ),
                    "ck3_process_inventory": mock.Mock(
                        return_value={"processes": []}
                    ),
                }
                with (
                    mock.patch.object(
                        g2_preview_eligibility,
                        "_read_manifest",
                        return_value=manifest,
                    ),
                    mock.patch.object(
                        g2_preview_eligibility,
                        "_backend",
                        return_value=backend,
                    ),
                    mock.patch.object(
                        g2_preview_eligibility,
                        "_preflight",
                        return_value=(
                            SimpleNamespace(),
                            {
                                "status": "ready",
                                "succession_lifecycle_binding": (
                                    expected_binding
                                ),
                            },
                        ),
                    ),
                    mock.patch.object(
                        g2_preview_eligibility,
                        "_qualify",
                        return_value={"eligible": True},
                    ),
                    mock.patch.object(
                        sys,
                        "argv",
                        [
                            "g2_preview_eligibility.py",
                            "--manifest",
                            str(root / "manifest.json"),
                            "--output",
                            str(output),
                        ],
                    ),
                    contextlib.redirect_stdout(io.StringIO()),
                ):
                    self.assertEqual(g2_preview_eligibility.main(), 0)
                self.assertEqual(
                    run_live_stage.call_args.kwargs[
                        "prepared_xar_enabled"
                    ],
                    expected_rule,
                )
                self.assertEqual(
                    run_live_stage.call_args.kwargs[
                        "succession_lifecycle_binding"
                    ],
                    expected_binding,
                )

    def test_lifecycle_manifest_is_complete_and_legacy_default_is_explicit(self) -> None:
        self.assertEqual(
            g2_preview_operator.lifecycle_contract({}),
            {
                "xar_enabled": "xar_on",
                "succession_lifecycle": "rogue_one_life",
                "ordinary_campaign_no_pact": False,
                "source": "legacy-default",
            },
        )
        ordinary = {
            "xar_enabled": "xar_off",
            "succession_lifecycle": "ordinary_campaign_succession",
            "ordinary_campaign_no_pact": True,
        }
        self.assertEqual(
            g2_preview_operator.lifecycle_contract(ordinary),
            {**ordinary, "source": "manifest"},
        )
        self.assertEqual(
            g2_preview_eligibility._lifecycle_contract(ordinary),
            {**ordinary, "source": "manifest"},
        )
        with self.assertRaisesRegex(ValueError, "partial"):
            g2_preview_operator.lifecycle_contract({"xar_enabled": "xar_off"})
        with self.assertRaisesRegex(ValueError, "inconsistent"):
            g2_preview_eligibility._lifecycle_contract({
                **ordinary,
                "ordinary_campaign_no_pact": False,
            })

    def test_prepare_state_forwards_ordinary_profile_rule(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = root / "state"
            sample = root / "sample"
            sample.mkdir()
            (sample / "xar_checkpoint.ck3").write_bytes(b"checkpoint")
            (sample / "driver-state.json").write_text("{}", encoding="utf-8")
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps({
                "python": str(root / "python.exe"),
                "source_repo": str(root / "repo"),
                "state_dir": str(state),
                "game_dir": str(root / "game"),
                "pipe": r"\\.\pipe\ordinary-preview",
                "dll": str(root / "bridge.dll"),
                "injector": str(root / "injector.exe"),
                "xar_enabled": "xar_off",
                "succession_lifecycle": "ordinary_campaign_succession",
                "ordinary_campaign_no_pact": True,
            }), encoding="utf-8")
            calls: list[list[str]] = []

            def fake_run(command, check):
                self.assertFalse(check)
                calls.append(command)
                if "rebind-ordinary-seed-v1" in command:
                    receipt_path = Path(command[command.index("--receipt") + 1])
                    receipt_path.write_text(json.dumps({
                        "schema": "xar.ck3.ordinary-seed-rebind/v1",
                        "status": "rebound",
                        "ok": True,
                        "ck3_launch_attempted": False,
                        "pipe_name": r"\\.\pipe\ordinary-preview",
                        "no_launch_preflight_expectations": {
                            "pipe_name": r"\\.\pipe\ordinary-preview",
                            "expected_character_id": 31853,
                            "expected_episode_run_id": "native-31853-test",
                            "expected_checkpoint_sha256": "a" * 64,
                            "expected_driver_state_sha256": "b" * 64,
                            "xar_enabled": "xar_off",
                            "succession_lifecycle": (
                                "ordinary_campaign_succession"
                            ),
                            "ordinary_campaign_no_pact": True,
                        },
                    }), encoding="utf-8")
                return mock.Mock(returncode=0)

            stdout = io.StringIO()
            with (
                mock.patch.object(
                    g2_preview_operator.subprocess,
                    "run",
                    side_effect=fake_run,
                ),
                contextlib.redirect_stdout(stdout),
            ):
                result = g2_preview_operator.command_prepare_state(
                    argparse.Namespace(manifest=manifest_path, sample_dir=sample)
                )

            self.assertEqual(result, 0)
            self.assertEqual(calls[0][-3:], [
                "prepare-profile", "--xar-enabled", "xar_off"
            ])
            self.assertEqual(calls[1][-3:], [
                "verify-profile", "--xar-enabled", "xar_off"
            ])
            self.assertIn("rebind-ordinary-seed-v1", calls[2])
            self.assertEqual(
                calls[2][calls[2].index("--expected-pipe") + 1],
                r"\\.\pipe\ordinary-preview",
            )
            self.assertIn("native-one-generation-preflight", calls[3])
            self.assertIn("--ordinary-campaign-no-pact", calls[3])
            self.assertEqual(
                json.loads(stdout.getvalue())["lifecycle"]["succession_lifecycle"],
                "ordinary_campaign_succession",
            )
            preparation = json.loads(stdout.getvalue())
            self.assertEqual(
                preparation["ordinary_no_launch_preflight"], "passed"
            )
            self.assertTrue(
                Path(preparation["ordinary_seed_rebind_receipt"]).is_file()
            )

    def test_prepare_state_legacy_manifest_keeps_original_two_commands(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = root / "state"
            sample = root / "sample"
            sample.mkdir()
            (sample / "xar_checkpoint.ck3").write_bytes(b"checkpoint")
            (sample / "driver-state.json").write_text("{}", encoding="utf-8")
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps({
                "python": str(root / "python.exe"),
                "source_repo": str(root / "repo"),
                "state_dir": str(state),
                "game_dir": str(root / "game"),
                "pipe": r"\\.\pipe\legacy-preview",
                "dll": str(root / "bridge.dll"),
                "injector": str(root / "injector.exe"),
            }), encoding="utf-8")
            calls: list[list[str]] = []

            def fake_run(command, check):
                self.assertFalse(check)
                calls.append(command)
                return mock.Mock(returncode=0)

            with mock.patch.object(
                g2_preview_operator.subprocess, "run", side_effect=fake_run
            ):
                result = g2_preview_operator.command_prepare_state(
                    argparse.Namespace(manifest=manifest_path, sample_dir=sample)
                )

            self.assertEqual(result, 0)
            self.assertEqual(len(calls), 2)
            self.assertEqual(calls[0][-3:], [
                "prepare-profile", "--xar-enabled", "xar_on"
            ])
            self.assertEqual(calls[1][-3:], [
                "verify-profile", "--xar-enabled", "xar_on"
            ])
            self.assertFalse((state / "ordinary-seed-rebind-v1.json").exists())

    def test_prepare_state_rebind_failure_blocks_preflight_without_run(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = root / "state"
            sample = root / "sample"
            sample.mkdir()
            (sample / "xar_checkpoint.ck3").write_bytes(b"checkpoint")
            (sample / "driver-state.json").write_text("{}", encoding="utf-8")
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps({
                "python": str(root / "python.exe"),
                "source_repo": str(root / "repo"),
                "state_dir": str(state),
                "game_dir": str(root / "game"),
                "pipe": r"\\.\pipe\ordinary-preview",
                "dll": str(root / "bridge.dll"),
                "injector": str(root / "injector.exe"),
                "xar_enabled": "xar_off",
                "succession_lifecycle": "ordinary_campaign_succession",
                "ordinary_campaign_no_pact": True,
            }), encoding="utf-8")
            calls: list[list[str]] = []

            def fake_run(command, check):
                self.assertFalse(check)
                calls.append(command)
                return mock.Mock(
                    returncode=(1 if "rebind-ordinary-seed-v1" in command else 0)
                )

            with (
                mock.patch.object(
                    g2_preview_operator.subprocess, "run", side_effect=fake_run
                ),
                self.assertRaisesRegex(RuntimeError, "rebind failed"),
            ):
                g2_preview_operator.command_prepare_state(
                    argparse.Namespace(manifest=manifest_path, sample_dir=sample)
                )

            self.assertEqual(len(calls), 3)
            self.assertTrue(all("native-auto-run" not in call for call in calls))
            self.assertTrue(all(
                "native-one-generation-preflight" not in call for call in calls
            ))

    def test_eligibility_preflight_binds_ordinary_profile_and_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = root / "state"
            checkpoint = state / "profile" / "save games" / "xar_checkpoint.ck3"
            driver_path = state / "native-session" / "driver-state.json"
            game_exe = root / "game" / "binaries" / "ck3.exe"
            source_save = root / "source.ck3"
            dll = root / "bridge.dll"
            injector = root / "injector.exe"
            for path, payload in (
                (checkpoint, b"checkpoint"),
                (driver_path, b"driver"),
                (game_exe, b"game"),
                (source_save, b"checkpoint"),
                (dll, b"dll"),
                (injector, b"injector"),
            ):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(payload)
            binding = {
                "schema": "xar.ck3.succession-lifecycle-binding/v1",
                "lifecycle": "ordinary_campaign_succession",
                "xar_enabled": "xar_off",
                "pact_contract": "absent_by_fresh_campaign_xar_off_contract",
                "source": "prepared-environment-manifest",
                "environment_sha256": "e" * 64,
            }
            manifest = {
                "source_repo": str(root / "repo"),
                "source_commit": "a" * 40,
                "state_dir": str(state),
                "game_dir": str(root / "game"),
                "environment_sha256": "e" * 64,
                "game_exe_sha256": hashlib.sha256(b"game").hexdigest(),
                "source_save": str(source_save),
                "checkpoint_sha256": hashlib.sha256(b"checkpoint").hexdigest(),
                "driver_state_sha256": hashlib.sha256(b"driver").hexdigest(),
                "dll": str(dll),
                "dll_sha256": hashlib.sha256(b"dll").hexdigest(),
                "injector": str(injector),
                "injector_sha256": hashlib.sha256(b"injector").hexdigest(),
                "pipe": r"\\.\pipe\ordinary-preview",
                "episode_character_id": 31853,
                "episode_run_id": "native-31853-test",
                "date_raw": 53144328,
                "xar_enabled": "xar_off",
                "succession_lifecycle": "ordinary_campaign_succession",
                "ordinary_campaign_no_pact": True,
            }
            verify_profile = mock.Mock(return_value={
                "environment_sha256": "e" * 64,
                "rules": {"profile": [
                    {"rule": "xar_enabled", "setting": "xar_off"}
                ]},
            })
            backend = {
                "make_spec": mock.Mock(
                    return_value=SimpleNamespace(game_exe=game_exe)
                ),
                "verify_profile": verify_profile,
                "bind_succession_lifecycle_from_environment_v1": mock.Mock(
                    return_value=binding
                ),
                "legacy_rogue_one_life_binding_v1": mock.Mock(
                    return_value={"lifecycle": "rogue_one_life"}
                ),
                "validate_cold_start_checkpoint_for_pipe": mock.Mock(
                    return_value={
                        "saved_date_raw": 53144328,
                        "succession_lifecycle": binding,
                    }
                ),
                "load_native_driver_state_for_resume": mock.Mock(
                    return_value={
                        "episode_character_id": 31853,
                        "episode_run_id": "native-31853-test",
                        "succession_lifecycle": binding,
                    }
                ),
                "ck3_process_inventory": mock.Mock(
                    return_value={"processes": []}
                ),
            }

            def git_output(command, text):
                self.assertTrue(text)
                return "a" * 40 + "\n" if "rev-parse" in command else ""

            with mock.patch.object(
                g2_preview_eligibility.subprocess,
                "check_output",
                side_effect=git_output,
            ):
                _spec, preflight = g2_preview_eligibility._preflight(
                    manifest, backend
                )

            verify_profile.assert_called_once_with(
                mock.ANY, xar_enabled="xar_off"
            )
            self.assertEqual(
                preflight["succession_lifecycle_binding"], binding
            )
            self.assertEqual(
                preflight["lifecycle"]["succession_lifecycle"],
                "ordinary_campaign_succession",
            )

    def test_ordinary_run_forwards_preflight_formal_and_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = root / "state"
            save = state / "profile" / "save games" / "xar_checkpoint.ck3"
            driver = state / "native-session" / "driver-state.json"
            save.parent.mkdir(parents=True)
            driver.parent.mkdir(parents=True)
            save.write_bytes(b"ordinary-checkpoint")
            driver.write_text(json.dumps({
                "episode_character_id": 31853,
                "episode_run_id": "native-31853-test",
            }), encoding="utf-8")
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps({
                "python": str(root / "python.exe"),
                "source_repo": str(root / "repo"),
                "state_dir": str(state),
                "game_dir": str(root / "game"),
                "pipe": r"\\.\pipe\ordinary-preview",
                "dll": str(root / "bridge.dll"),
                "injector": str(root / "injector.exe"),
                "xar_enabled": "xar_off",
                "succession_lifecycle": "ordinary_campaign_succession",
                "ordinary_campaign_no_pact": True,
                "formal_turns": 3,
                "timeout_seconds": 390,
                "readiness_timeout_seconds": 300,
            }), encoding="utf-8")
            output = root / "attempt"
            calls: list[list[str]] = []

            def fake_run(command, stdout_path, stderr_path):
                calls.append(command)
                stdout_path.write_text("{}\n", encoding="utf-8")
                stderr_path.write_text("", encoding="utf-8")
                return 0

            args = g2_preview_operator.parser().parse_args([
                "run", "--manifest", str(manifest_path),
                "--output", str(output),
            ])
            with mock.patch.object(
                g2_preview_operator, "run_logged", side_effect=fake_run
            ):
                result = g2_preview_operator.command_run(args)

            self.assertEqual(result, 0)
            self.assertIn("--xar-enabled", calls[0])
            self.assertIn("xar_off", calls[0])
            self.assertIn("--ordinary-campaign-no-pact", calls[0])
            self.assertIn("--succession-lifecycle", calls[1])
            self.assertIn("ordinary_campaign_succession", calls[1])
            self.assertIn("--ordinary-campaign-no-pact", calls[1])
            receipt = json.loads(
                (output / "operator-receipt.json").read_text(encoding="utf-8")
            )
            self.assertEqual(receipt["lifecycle"]["xar_enabled"], "xar_off")
            self.assertTrue(
                receipt["lifecycle"]["ordinary_campaign_no_pact"]
            )

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
                    return g2_preview_operator.R781_INJECTOR_SHA256
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
