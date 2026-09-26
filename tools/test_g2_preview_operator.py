from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

from tools import g2_preview_eligibility, g2_preview_operator


class G2PreviewOperatorTest(unittest.TestCase):
    def test_family_pending_sidecar_pairs_saved_proposal_and_rejects_other_pair(self) -> None:
        manifest = {"episode_character_id": 29829,
                    "episode_run_id": "native-29829-test"}
        driver = {**manifest, "last_checkpoint": {
            "episode_character_id": 29829,
            "episode_run_id": "native-29829-test",
            "date_raw": 53154528, "sha256": "a" * 64,
            "history_index": 111,
        }}
        sidecar = {"schema": g2_preview_operator.FAMILY_PENDING_V1_SCHEMA,
                   "resolved": None, "pending": {
            "schema": g2_preview_operator.FAMILY_ACTION_V1_SCHEMA,
            "status": "receipt_pending", "submission_state": "receipt_pending",
            "material_result": False, "accepted": True,
            "played_character_id": 29829, "heir_character_id": 38822,
            "candidate_character_id": 38710,
            "episode_run_id": "native-29829-test",
            "source_date_raw": 53154528, "source_bridge_pid": 146776,
        }}
        report = {"session": {"pid": 146776}, "checkpoints": [{
            "phase": "first_heir_marriage_submitted_pending",
            "sha256": "a" * 64, "history_index": 111,
            "date_raw": 53154528,
            "pending_action": {"heir_character_id": 38822,
                               "candidate_character_id": 38710,
                               "episode_run_id": "native-29829-test"},
        }], "auto_run": {"turns": [{
            "selected_step": g2_preview_operator.FAMILY_SUBMIT_STEP,
            "result": {"status": "receipt_pending"},
            "plan": {"family_marriage_choice": {
                "candidate_character_id": 38710}},
        }]}}
        self.assertEqual(g2_preview_operator.family_pending_sidecar_pair(
            sidecar, driver, manifest, "a" * 64, report), 38710)
        report["checkpoints"][0]["pending_action"]["candidate_character_id"] = 38711
        with self.assertRaisesRegex(ValueError, "not proven"):
            g2_preview_operator.family_pending_sidecar_pair(
                sidecar, driver, manifest, "a" * 64, report)

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
            request_id = "construction-submit-" + "a" * 32
            pending = {"status": "submitted_verification_pending",
                       "action_request_id": request_id,
                       "actor_character_id": 31853,
                       "episode_run_id": "native-31853-test"}
            driver_bytes = json.dumps({
                "episode_character_id": 31853,
                "episode_run_id": "native-31853-test",
                "last_checkpoint": {"history_index": 96,
                                    "episode_character_id": 31853,
                                    "episode_run_id": "native-31853-test"},
                "command_history": [{"index": 95,
                                     "command": "private-submit-player-construction-v1",
                                     "result": pending}],
            }).encode("utf-8")
            (sample / "driver-state.json").write_bytes(driver_bytes)
            pending_bytes = json.dumps({
                "schema": "xar.ck3.construction_formal_pending_v1",
                "pending": pending, "applied": None,
            }).encode("utf-8")
            (sample / "construction-formal-pending-v1.json").write_bytes(pending_bytes)
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
                        "environment": {"target_sha256": "c" * 64},
                        "driver_state": {
                             "target_sha256": hashlib.sha256(driver_bytes).hexdigest(),
                        },
                        "no_launch_preflight_expectations": {
                            "pipe_name": r"\\.\pipe\ordinary-preview",
                            "expected_character_id": 31853,
                            "expected_episode_run_id": "native-31853-test",
                            "expected_checkpoint_sha256": "a" * 64,
                             "expected_driver_state_sha256": hashlib.sha256(
                                 driver_bytes).hexdigest(),
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
            updated_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(updated_manifest["environment_sha256"], "c" * 64)
            self.assertEqual(
                updated_manifest["driver_state_sha256"],
                hashlib.sha256(driver_bytes).hexdigest(),
            )
            self.assertEqual(preparation["manifest_updated"], str(manifest_path))
            sidecar = preparation["construction_pending_sidecar"]
            self.assertEqual(sidecar["status"], "paired_no_launch")
            self.assertEqual(sidecar["action_request_id"], request_id)
            self.assertEqual(sidecar["sha256"], hashlib.sha256(pending_bytes).hexdigest())
            self.assertEqual(Path(sidecar["path"]).read_bytes(), pending_bytes)

    def test_prepare_state_preserves_read_only_sources_and_rebinds_writable_copy(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = root / "state"
            sample = root / "sample"
            sample.mkdir()
            save_source = sample / "xar_checkpoint.ck3"
            driver_source = sample / "driver-state.json"
            save_source.write_bytes(b"frozen checkpoint")
            driver_source.write_bytes(b'{"frozen":true}\n')
            source_paths = (save_source, driver_source)
            source_hashes = {
                path: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in source_paths
            }
            for path in source_paths:
                path.chmod(path.stat().st_mode & ~stat.S_IWRITE)

            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps({
                "python": str(root / "python.exe"),
                "source_repo": str(root / "repo"),
                "state_dir": str(state),
                "game_dir": str(root / "game"),
                "pipe": r"\\.\pipe\ordinary-read-only-source",
                "dll": str(root / "bridge.dll"),
                "injector": str(root / "injector.exe"),
                "xar_enabled": "xar_off",
                "succession_lifecycle": "ordinary_campaign_succession",
                "ordinary_campaign_no_pact": True,
            }), encoding="utf-8")
            driver_target = state / "native-session" / "driver-state.json"
            rebound_driver = b'{"rebound":true}\n'
            calls: list[list[str]] = []

            def fake_run(command, check):
                self.assertFalse(check)
                calls.append(command)
                if "rebind-ordinary-seed-v1" in command:
                    self.assertTrue(driver_target.stat().st_mode & stat.S_IWRITE)
                    temporary = driver_target.with_suffix(".json.tmp")
                    temporary.write_bytes(rebound_driver)
                    temporary.replace(driver_target)
                    receipt_path = Path(command[command.index("--receipt") + 1])
                    receipt_path.write_text(json.dumps({
                        "schema": "xar.ck3.ordinary-seed-rebind/v1",
                        "status": "rebound",
                        "ok": True,
                        "ck3_launch_attempted": False,
                        "pipe_name": r"\\.\pipe\ordinary-read-only-source",
                        "environment": {"target_sha256": "c" * 64},
                        "driver_state": {
                            "target_sha256": hashlib.sha256(
                                rebound_driver
                            ).hexdigest(),
                        },
                        "no_launch_preflight_expectations": {
                            "pipe_name": r"\\.\pipe\ordinary-read-only-source",
                            "expected_character_id": 31853,
                            "expected_episode_run_id": "native-31853-test",
                            "expected_checkpoint_sha256": "a" * 64,
                            "expected_driver_state_sha256": hashlib.sha256(
                                rebound_driver
                            ).hexdigest(),
                            "xar_enabled": "xar_off",
                            "succession_lifecycle": (
                                "ordinary_campaign_succession"
                            ),
                            "ordinary_campaign_no_pact": True,
                        },
                    }), encoding="utf-8")
                return mock.Mock(returncode=0)

            try:
                with mock.patch.object(
                    g2_preview_operator.subprocess,
                    "run",
                    side_effect=fake_run,
                ):
                    result = g2_preview_operator.command_prepare_state(
                        argparse.Namespace(
                            manifest=manifest_path,
                            sample_dir=sample,
                        )
                    )

                self.assertEqual(result, 0)
                self.assertIn("rebind-ordinary-seed-v1", calls[2])
                for path in source_paths:
                    self.assertFalse(path.stat().st_mode & stat.S_IWRITE)
                    self.assertEqual(
                        hashlib.sha256(path.read_bytes()).hexdigest(),
                        source_hashes[path],
                    )
                save_target = (
                    state / "profile" / "save games" / "xar_checkpoint.ck3"
                )
                self.assertTrue(save_target.stat().st_mode & stat.S_IWRITE)
                self.assertTrue(driver_target.stat().st_mode & stat.S_IWRITE)
                self.assertEqual(driver_target.read_bytes(), rebound_driver)
            finally:
                for path in source_paths:
                    path.chmod(path.stat().st_mode | stat.S_IWRITE)

    def test_prepare_state_rejects_unpaired_or_overwritten_construction_sidecar(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = root / "state"
            sample = root / "sample"
            sample.mkdir()
            (sample / "xar_checkpoint.ck3").write_bytes(b"checkpoint")
            request_id = "construction-submit-" + "b" * 32
            pending = {"status": "submitted_verification_pending",
                       "action_request_id": request_id,
                       "actor_character_id": 31853,
                       "episode_run_id": "native-31853-test"}
            (sample / "driver-state.json").write_text(json.dumps({
                "episode_character_id": 31853,
                "episode_run_id": "native-31853-test",
                "last_checkpoint": {"history_index": 96,
                                    "episode_character_id": 31853,
                                    "episode_run_id": "native-31853-test"},
                "command_history": [{"index": 95,
                                     "command": "private-submit-player-construction-v1",
                                     "result": pending}],
            }), encoding="utf-8")
            sidecar_path = sample / "construction-formal-pending-v1.json"
            wrong = {"schema": "xar.ck3.construction_formal_pending_v1",
                     "pending": {**pending, "actor_character_id": 31854},
                     "applied": None}
            sidecar_path.write_text(json.dumps(wrong), encoding="utf-8")
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps({
                "python": str(root / "python.exe"),
                "source_repo": str(root / "repo"),
                "state_dir": str(state),
                "game_dir": str(root / "game"),
                "pipe": r"\\.\pipe\ordinary-preview",
                "dll": str(root / "bridge.dll"),
                "injector": str(root / "injector.exe"),
            }), encoding="utf-8")
            args = argparse.Namespace(manifest=manifest_path, sample_dir=sample)
            with mock.patch.object(g2_preview_operator.subprocess, "run") as run:
                with self.assertRaisesRegex(ValueError, "does not match"):
                    g2_preview_operator.command_prepare_state(args)
                run.assert_not_called()
            sidecar_path.write_text(json.dumps({**wrong, "pending": pending}),
                                    encoding="utf-8")
            state.mkdir()
            (state / sidecar_path.name).write_text("existing", encoding="utf-8")
            with mock.patch.object(g2_preview_operator.subprocess, "run") as run:
                with self.assertRaisesRegex(FileExistsError, "refusing to overwrite"):
                    g2_preview_operator.command_prepare_state(args)
                run.assert_not_called()

    def test_prepare_state_requires_and_copies_saved_applied_construction(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = root / "new-state"
            sample = root / "recovery-pair-h106"
            sample.mkdir()
            (sample / "xar_checkpoint.ck3").write_bytes(b"checkpoint")
            request_id = "construction-submit-" + "c" * 32
            candidate = {"barony_title_id": 2174, "province_id": 2629,
                         "building_type_id": 628, "slot_index": 1,
                         "stock_gold_cost_raw": 10000000,
                         "building_key": "hill_farms_01"}
            pending = {"status": "submitted_verification_pending",
                       "action_request_id": request_id,
                       "actor_character_id": 29829,
                       "episode_run_id": "native-29829-test",
                       "candidate": candidate}
            applied = {"status": "applied", "postcondition_verified": True,
                       "completion_status": "in_progress",
                       "completion_last_check_date_raw": 53154528,
                       "action_request_id": request_id,
                       "actor_character_id": 29829,
                       "episode_run_id": "native-29829-test",
                       "candidate": candidate}
            driver = {
                "episode_character_id": 29829,
                "episode_run_id": "native-29829-test",
                "last_checkpoint": {"history_index": 106,
                                    "episode_character_id": 29829,
                                    "episode_run_id": "native-29829-test"},
                "command_history": [
                    {"index": 95, "command": "private-submit-player-construction-v1",
                     "result": pending},
                    {"index": 103, "command": "private-query-player-construction-receipt-v1",
                     "result": applied},
                ],
            }
            (sample / "driver-state.json").write_text(json.dumps(driver), encoding="utf-8")
            sidecar_path = root / "old-state" / "construction-formal-pending-v1.json"
            sidecar_path.parent.mkdir()
            sidecar_bytes = json.dumps({
                "schema": "xar.ck3.construction_formal_pending_v1",
                "pending": None, "applied": applied,
            }).encode("utf-8")
            sidecar_path.write_bytes(sidecar_bytes)
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps({
                "python": str(root / "python.exe"),
                "source_repo": str(root / "repo"),
                "state_dir": str(state),
                "game_dir": str(root / "game"),
                "pipe": r"\\.\pipe\ordinary-preview",
                "dll": str(root / "bridge.dll"),
                "injector": str(root / "injector.exe"),
            }), encoding="utf-8")
            args = argparse.Namespace(manifest=manifest_path, sample_dir=sample,
                                      construction_sidecar=None)
            with mock.patch.object(g2_preview_operator.subprocess, "run") as run:
                with self.assertRaisesRegex(ValueError, "requires --construction-sidecar"):
                    g2_preview_operator.command_prepare_state(args)
                run.assert_not_called()

            args.construction_sidecar = sidecar_path
            stdout = io.StringIO()
            with (mock.patch.object(g2_preview_operator.subprocess, "run",
                                    return_value=mock.Mock(returncode=0)),
                  contextlib.redirect_stdout(stdout)):
                self.assertEqual(g2_preview_operator.command_prepare_state(args), 0)
            receipt = json.loads(stdout.getvalue())["construction_pending_sidecar"]
            self.assertEqual(receipt["ledger_status"], "applied")
            self.assertEqual(receipt["action_request_id"], request_id)
            self.assertEqual(receipt["source"], str(sidecar_path))
            self.assertEqual(receipt["sha256"], hashlib.sha256(sidecar_bytes).hexdigest())
            self.assertEqual(Path(receipt["path"]).read_bytes(), sidecar_bytes)

    def test_prepare_state_rejects_applied_sidecar_after_checkpoint(self) -> None:
        request_id = "construction-submit-" + "d" * 32
        applied = {"status": "applied", "postcondition_verified": True,
                   "completion_status": "in_progress", "action_request_id": request_id,
                   "actor_character_id": 29829, "episode_run_id": "native-29829-test",
                   "candidate": {"building_type_id": 628}}
        sidecar = {"schema": "xar.ck3.construction_formal_pending_v1",
                   "pending": None, "applied": applied}
        driver = {"episode_character_id": 29829,
                  "episode_run_id": "native-29829-test",
                  "last_checkpoint": {"history_index": 106,
                                      "episode_character_id": 29829,
                                      "episode_run_id": "native-29829-test"},
                  "command_history": [
                      {"index": 95, "command": "private-submit-player-construction-v1",
                       "result": {"status": "submitted_verification_pending",
                                  "action_request_id": request_id,
                                  "candidate": applied["candidate"]}},
                      {"index": 107,
                       "command": "private-query-player-construction-receipt-v1",
                       "result": applied}]}
        with self.assertRaisesRegex(ValueError, "does not match checkpoint"):
            g2_preview_operator.construction_pending_sidecar_request(sidecar, driver, {})

    def test_old_episode_construction_does_not_require_current_sidecar(self) -> None:
        driver = {
            "episode_character_id": 42000,
            "episode_run_id": "native-42000-heir",
            "last_checkpoint": {"history_index": 106,
                                "episode_character_id": 42000,
                                "episode_run_id": "native-42000-heir"},
            "command_history": [{
                "index": 103,
                "command": "private-query-player-construction-receipt-v1",
                "result": {"status": "applied", "postcondition_verified": True,
                           "completion_status": "in_progress",
                           "action_request_id": "construction-submit-" + "e" * 32,
                           "actor_character_id": 29829,
                           "episode_run_id": "native-29829-parent"},
            }],
        }
        self.assertFalse(
            g2_preview_operator.saved_in_progress_construction_without_sidecar(driver)
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
            self.assertNotIn(
                "environment_sha256",
                json.loads(manifest_path.read_text(encoding="utf-8")),
            )

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
                private_args = g2_preview_operator.parser().parse_args([
                    "run", "--manifest", str(manifest_path),
                    "--output", str(root / "attempt-private"),
                    "--private-lifestyle-formal-trial",
                ])
                private_result = g2_preview_operator.command_run(private_args)
                family_args = g2_preview_operator.parser().parse_args([
                    "run", "--manifest", str(manifest_path),
                    "--output", str(root / "attempt-family"),
                    "--private-family-marriage-formal-trial",
                ])
                family_result = g2_preview_operator.command_run(family_args)
                m5_args = g2_preview_operator.parser().parse_args([
                    "run", "--manifest", str(manifest_path),
                    "--output", str(root / "attempt-m5"),
                    "--private-m5-joint-collector",
                ])
                m5_result = g2_preview_operator.command_run(m5_args)

            self.assertEqual(result, 0)
            self.assertEqual(private_result, 0)
            self.assertEqual(family_result, 0)
            self.assertEqual(m5_result, 0)
            self.assertIn("--xar-enabled", calls[0])
            self.assertIn("xar_off", calls[0])
            self.assertIn("--ordinary-campaign-no-pact", calls[0])
            self.assertIn("--succession-lifecycle", calls[1])
            self.assertIn("ordinary_campaign_succession", calls[1])
            self.assertIn("--ordinary-campaign-no-pact", calls[1])
            self.assertNotIn("--allow-private-lifestyle-formal-trial", calls[1])
            self.assertIn("--allow-private-lifestyle-formal-trial", calls[3])
            self.assertNotIn("--allow-private-family-marriage-formal-trial", calls[1])
            self.assertNotIn("--allow-private-family-marriage-formal-trial", calls[3])
            self.assertIn("--allow-private-family-marriage-formal-trial", calls[5])
            self.assertNotIn("--allow-private-m5-joint-collector", calls[1])
            self.assertNotIn("--allow-private-m5-joint-collector", calls[3])
            self.assertNotIn("--allow-private-m5-joint-collector", calls[5])
            self.assertIn("--allow-private-m5-joint-collector", calls[7])
            receipt = json.loads(
                (output / "operator-receipt.json").read_text(encoding="utf-8")
            )
            self.assertEqual(receipt["lifecycle"]["xar_enabled"], "xar_off")
            self.assertTrue(
                receipt["lifecycle"]["ordinary_campaign_no_pact"]
            )
            self.assertFalse(receipt["private_lifestyle_formal_trial"])
            self.assertFalse(receipt["private_family_marriage_formal_trial"])
            self.assertFalse(receipt["private_m5_joint_collector"])
            private_receipt = json.loads(
                (root / "attempt-private" / "operator-receipt.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertTrue(private_receipt["private_lifestyle_formal_trial"])
            family_receipt = json.loads(
                (root / "attempt-family" / "operator-receipt.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertTrue(family_receipt["private_family_marriage_formal_trial"])
            m5_receipt = json.loads(
                (root / "attempt-m5" / "operator-receipt.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertTrue(m5_receipt["private_m5_joint_collector"])

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

    def test_private_lifestyle_trial_is_narrowly_forwarded(self) -> None:
        default_args = g2_preview_operator.parser().parse_args([
            "run", "--manifest", "manifest.json", "--output", "attempt",
        ])
        self.assertFalse(default_args.private_lifestyle_formal_trial)
        self.assertFalse(
            default_args.require_initial_lifestyle_focus_before_date_advance
        )
        args = g2_preview_operator.parser().parse_args([
            "run", "--manifest", "manifest.json", "--output", "attempt",
            "--private-lifestyle-formal-trial",
            "--require-initial-lifestyle-focus-before-date-advance",
        ])
        self.assertTrue(args.private_lifestyle_formal_trial)
        self.assertTrue(args.require_initial_lifestyle_focus_before_date_advance)
        gate_without_trial = g2_preview_operator.parser().parse_args([
            "run", "--manifest", "manifest.json", "--output", "attempt",
            "--require-initial-lifestyle-focus-before-date-advance",
        ])
        with self.assertRaisesRegex(ValueError, "requires --private-lifestyle"):
            g2_preview_operator.command_run(gate_without_trial)
        base = dict(
            turns=2,
            timeout=900,
            readiness_timeout=300,
            private_faction_round_id_value=None,
        )
        self.assertNotIn(
            "--allow-private-lifestyle-formal-trial",
            g2_preview_operator.native_auto_run_command(
                ["python", "agent.py"], **base
            ),
        )
        self.assertIn(
            "--allow-private-lifestyle-formal-trial",
            g2_preview_operator.native_auto_run_command(
                ["python", "agent.py"],
                **base,
                private_lifestyle_formal_trial=args.private_lifestyle_formal_trial,
                require_initial_lifestyle_focus_before_date_advance=(
                    args.require_initial_lifestyle_focus_before_date_advance
                ),
            ),
        )
        self.assertIn(
            "--require-initial-lifestyle-focus-before-date-advance",
            g2_preview_operator.native_auto_run_command(
                ["python", "agent.py"], **base,
                private_lifestyle_formal_trial=True,
                require_initial_lifestyle_focus_before_date_advance=True,
            ),
        )

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


    def test_windowed_prepare_state_forwards_exact_display_to_both_commands(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sample = root / "sample"
            sample.mkdir()
            (sample / "xar_checkpoint.ck3").write_bytes(b"checkpoint")
            (sample / "driver-state.json").write_text("{}", encoding="utf-8")
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps({
                "python": str(root / "python.exe"),
                "source_repo": str(root / "repo"),
                "state_dir": str(root / "state"),
                "game_dir": str(root / "game"),
                "pipe": r"\\.\pipe\windowed-preview",
                "dll": str(root / "bridge.dll"),
                "injector": str(root / "injector.exe"),
                "display_mode": "windowed",
            }), encoding="utf-8")
            calls: list[list[str]] = []

            def fake_run(command, check):
                self.assertFalse(check)
                calls.append(command)
                return mock.Mock(returncode=0)

            with mock.patch.object(g2_preview_operator.subprocess, "run", side_effect=fake_run):
                g2_preview_operator.command_prepare_state(
                    argparse.Namespace(manifest=manifest_path, sample_dir=sample)
                )
            self.assertEqual(len(calls), 2)
            for command in calls:
                self.assertEqual(command[-2:], ["--display-mode", "windowed"])
            self.assertEqual(g2_preview_operator.display_mode_contract({}), "fullscreen")
            with self.assertRaisesRegex(ValueError, "display_mode"):
                g2_preview_operator.display_mode_contract({"display_mode": "borderless"})

    def test_construction_opt_in_is_forwarded_only_when_requested(self) -> None:
        base = dict(
            common=["python", "agent.py"],
            turns=1,
            timeout=60,
            readiness_timeout=30,
            private_faction_round_id_value=None,
        )
        self.assertNotIn(
            "--allow-private-construction-formal-trial",
            g2_preview_operator.native_auto_run_command(**base),
        )
        self.assertIn(
            "--allow-private-construction-formal-trial",
            g2_preview_operator.native_auto_run_command(
                **base, private_construction_formal_trial=True
            ),
        )
        parsed = g2_preview_operator.parser().parse_args([
            "run", "--manifest", "manifest.json", "--output", "output",
            "--private-construction-formal-trial",
        ])
        self.assertTrue(parsed.private_construction_formal_trial)

    def test_family_marriage_opt_in_is_forwarded_only_when_requested(self) -> None:
        base = dict(
            common=["python", "agent.py"], turns=1, timeout=60,
            readiness_timeout=30, private_faction_round_id_value=None,
        )
        self.assertNotIn(
            "--allow-private-family-marriage-formal-trial",
            g2_preview_operator.native_auto_run_command(**base),
        )
        self.assertIn(
            "--allow-private-family-marriage-formal-trial",
            g2_preview_operator.native_auto_run_command(
                **base, private_family_marriage_formal_trial=True),
        )

    def test_owned_window_minimizes_only_matching_live_pid(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = root / "state"
            control = state / "control"
            control.mkdir(parents=True)
            game = root / "game"
            exe = game / "binaries" / "ck3.exe"
            creation = "20260926070000.000000+480"
            (control / "ck3.json").write_text(json.dumps({
                "ck3_pid": 321,
                "creation_date": creation,
                "executable": str(exe.resolve()),
            }), encoding="utf-8")
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps({
                "python": str(root / "python.exe"),
                "source_repo": str(root / "repo"),
                "state_dir": str(state),
                "game_dir": str(game),
                "pipe": r"\\.\pipe\windowed-preview",
                "dll": str(root / "bridge.dll"),
                "injector": str(root / "injector.exe"),
            }), encoding="utf-8")
            args = argparse.Namespace(
                manifest=manifest_path, expected_pid=321,
                expected_creation_date=creation, minimize=True,
            )
            inventory = {"processes": [{
                "pid": 321, "name": "ck3.exe", "creation_date": creation,
                "executable": str(exe.resolve()),
            }]}
            output = io.StringIO()
            with (
                mock.patch.object(g2_preview_operator.sys, "platform", "win32"),
                mock.patch.object(g2_preview_operator, "_owned_ck3_inventory",
                                  return_value=(inventory, lambda a, b: a == b)),
                mock.patch.object(g2_preview_operator, "_owned_ck3_window_states",
                                  side_effect=[{11: False}, {11: True}]),
                mock.patch.object(g2_preview_operator, "_minimize_owned_ck3_windows") as minimize,
                contextlib.redirect_stdout(output),
            ):
                self.assertEqual(g2_preview_operator.command_owned_window(args), 0)
            minimize.assert_called_once_with([11])
            self.assertTrue(json.loads(output.getvalue())["after_minimized"])
            args.expected_pid = 999
            with mock.patch.object(g2_preview_operator.sys, "platform", "win32"):
                with self.assertRaisesRegex(RuntimeError, "control identity differs"):
                    g2_preview_operator.command_owned_window(args)


class FamilyAllianceResultOperatorTest(unittest.TestCase):
    def test_logged_python_report_is_utf8_under_legacy_windows_encoding(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stdout = Path(directory) / "report.json"
            stderr = Path(directory) / "stderr.txt"
            command = [sys.executable, "-c", (
                'import json; print(json.dumps({"name": "罗贝尔"}, ensure_ascii=False))'
            )]
            with mock.patch.dict(os.environ, {"PYTHONIOENCODING": "cp936"}):
                self.assertEqual(
                    g2_preview_operator.run_logged(command, stdout, stderr), 0
                )
            self.assertEqual(
                g2_preview_operator.read_json(stdout)["name"], "罗贝尔"
            )
            self.assertEqual(stderr.read_text(encoding="utf-8"), "")

    def test_round_id_matches_persistent_allocator_suffix(self) -> None:
        self.assertEqual(
            g2_preview_operator.private_family_alliance_round_id("R0227"),
            "R0227",
        )
        for invalid in ("R227", "R0000", "R00227"):
            with self.assertRaises(argparse.ArgumentTypeError):
                g2_preview_operator.private_family_alliance_round_id(invalid)

    def test_prepare_state_accepts_paired_resolved_family_without_rewriting_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sample = root / "sample"
            sample.mkdir()
            state = root / "state"
            save = sample / "xar_checkpoint.ck3"
            driver = sample / "driver-state.json"
            family = sample / "first-heir-marriage-formal-v1.json"
            save.write_bytes(b"h148-paired-save")
            save_hash = g2_preview_operator.sha256(save)
            episode = "native-29829-test"
            driver.write_text(json.dumps({
                "episode_character_id": 29829, "episode_run_id": episode,
                "last_checkpoint": {"history_index": 148, "sha256": save_hash,
                                    "episode_character_id": 29829,
                                    "episode_run_id": episode},
            }), encoding="utf-8")
            family.write_text(json.dumps({
                "schema": g2_preview_operator.FAMILY_PENDING_V1_SCHEMA,
                "pending": None,
                "resolved": {
                    "status": "betrothal", "material_result": True,
                    "episode_run_id": episode,
                    "heir_character_id": 38822,
                    "candidate_character_id": 38710,
                    "source_pending": {
                        "schema": g2_preview_operator.FAMILY_ACTION_V1_SCHEMA,
                        "status": "receipt_pending", "material_result": False,
                        "played_character_id": 29829,
                        "episode_run_id": episode,
                        "heir_character_id": 38822,
                        "candidate_character_id": 38710,
                    },
                },
            }), encoding="utf-8")
            family_bytes = family.read_bytes()
            manifest_file = root / "manifest.json"
            manifest_file.write_text(json.dumps({
                "python": str(root / "python.exe"),
                "source_repo": str(root / "repo"),
                "state_dir": str(state),
                "game_dir": str(root / "game"),
                "pipe": r"\\.\pipe\family-resolved-prepare",
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
                    receipt = Path(command[command.index("--receipt") + 1])
                    rebound_driver = state / "native-session" / "driver-state.json"
                    receipt.write_text(json.dumps({
                        "schema": g2_preview_operator.ORDINARY_SEED_REBIND_V1_SCHEMA,
                        "status": "rebound", "ok": True,
                        "ck3_launch_attempted": False,
                        "pipe_name": r"\\.\pipe\family-resolved-prepare",
                        "environment": {"target_sha256": "c" * 64},
                        "driver_state": {"target_sha256":
                            g2_preview_operator.sha256(rebound_driver)},
                        "no_launch_preflight_expectations": {
                            "pipe_name": r"\\.\pipe\family-resolved-prepare",
                            "expected_character_id": 29829,
                            "expected_episode_run_id": episode,
                            "expected_checkpoint_sha256": save_hash,
                            "expected_driver_state_sha256":
                                g2_preview_operator.sha256(rebound_driver),
                            "xar_enabled": "xar_off",
                            "succession_lifecycle": "ordinary_campaign_succession",
                            "ordinary_campaign_no_pact": True,
                        },
                    }), encoding="utf-8")
                return mock.Mock(returncode=0)

            with (mock.patch.object(g2_preview_operator.subprocess, "run",
                                    side_effect=fake_run),
                  contextlib.redirect_stdout(io.StringIO()) as output):
                self.assertEqual(g2_preview_operator.command_prepare_state(
                    argparse.Namespace(manifest=manifest_file, sample_dir=sample,
                                       family_sidecar=family)), 0)
            self.assertEqual(len(calls), 4)
            self.assertIn("native-one-generation-preflight", calls[-1])
            self.assertEqual(family.read_bytes(), family_bytes)
            prepared = json.loads(output.getvalue())
            family_receipt = prepared["family_resolved_sidecar"]
            self.assertEqual(family_receipt["candidate_character_id"], 38710)
            self.assertEqual(family_receipt["sha256"],
                             hashlib.sha256(family_bytes).hexdigest())
            self.assertEqual(Path(family_receipt["path"]).read_bytes(), family_bytes)

    def test_preflight_precedes_exact_private_query_and_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            save = root / "xar_checkpoint.ck3"
            driver = root / "driver-state.json"
            proposal = root / "c10-formal-report.json"
            save.write_bytes(b"paired-save")
            driver.write_text(json.dumps({
                "episode_character_id": 29829,
                "episode_run_id": "native-29829-test",
            }), encoding="utf-8")
            proposal.write_text("{}", encoding="utf-8")
            digest = g2_preview_operator.sha256(proposal)
            manifest = {"timeout_seconds": 390,
                        "readiness_timeout_seconds": 300,
                        "xar_enabled": "xar_off",
                        "succession_lifecycle": "ordinary_campaign_succession",
                        "ordinary_campaign_no_pact": True}
            args = argparse.Namespace(
                manifest=root / "manifest.json", output=root / "attempt",
                proposal_report=proposal, proposal_report_sha256=digest,
                recipient_character_id=32266, ownership_round_id="R0999",
                timeout=None, readiness_timeout=None)
            commands = []

            def fake_run(command, stdout_path, stderr_path):
                commands.append(command)
                stderr_path.write_text("", encoding="utf-8")
                if len(commands) == 1:
                    self.assertIn("native-one-generation-preflight", command)
                    self.assertEqual(command[command.index("--xar-enabled") + 1],
                                     "xar_off")
                    self.assertEqual(
                        command[command.index("--succession-lifecycle") + 1],
                        "ordinary_campaign_succession")
                    self.assertIn("--ordinary-campaign-no-pact", command)
                    stdout_path.write_text("{}", encoding="utf-8")
                    return 0
                self.assertIn(
                    "native-query-first-heir-marriage-alliance-result-v1",
                    command)
                self.assertIn("--cold-start-checkpoint", command)
                self.assertNotIn("native-auto-run", command)
                stdout_path.write_text(json.dumps({
                    "ok": True, "round": "R0999",
                    "query_envelope": {"alliance_status": "not_allied"},
                    "before": {"frame": {"date_raw": 53155728}},
                    "after": {"frame": {"date_raw": 53155728}},
                    "checks": {"paused_frame_unchanged": True,
                               "date_unchanged": True,
                               "checkpoint_unchanged": True,
                               "window_minimized_or_hidden": True,
                               "cleanup_proven": True},
                    "cleanup": {"ok": True},
                }), encoding="utf-8")
                return 0

            with (mock.patch.object(g2_preview_operator, "load_manifest",
                                    return_value=manifest),
                  mock.patch.object(g2_preview_operator, "frozen_source_identity",
                                    return_value={"commit": "a" * 40}),
                  mock.patch.object(g2_preview_operator, "current_checkpoint_identity",
                                    return_value=(save, driver, json.loads(
                                        driver.read_text(encoding="utf-8")))),
                  mock.patch.object(g2_preview_operator, "agent_command",
                                    return_value=["python", "agent.py"]),
                  mock.patch.object(g2_preview_operator, "run_logged",
                                    side_effect=fake_run),
                  contextlib.redirect_stdout(io.StringIO())):
                self.assertEqual(
                    g2_preview_operator.command_query_first_heir_marriage_alliance_result_v1(args),
                    0)
            self.assertEqual(len(commands), 2)
            receipt = json.loads((args.output / "operator-receipt.json")
                                 .read_text(encoding="utf-8"))
            self.assertEqual(receipt["status"], "GREEN_READ_ONLY")
            self.assertEqual(receipt["query_envelope"]["alliance_status"],
                             "not_allied")
            self.assertEqual(receipt["checkpoint_sha256_before"],
                             receipt["checkpoint_sha256_after"])


if __name__ == "__main__":
    unittest.main()
