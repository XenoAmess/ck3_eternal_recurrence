from __future__ import annotations

import argparse
import copy
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
    def test_sway_pending_ack_pairs_and_copies_exact_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sample = root / "sample"
            sample.mkdir()
            save_bytes = b"R0340 paired checkpoint"
            save_hash = hashlib.sha256(save_bytes).hexdigest()
            (sample / "xar_checkpoint.ck3").write_bytes(save_bytes)
            driver = {
                "episode_character_id": 29829,
                "episode_run_id": "native-29829-test",
                "last_checkpoint": {
                    "episode_character_id": 29829,
                    "episode_run_id": "native-29829-test",
                    "date_raw": 53219928,
                    "sha256": save_hash, "size": len(save_bytes),
                },
            }
            (sample / "driver-state.json").write_text(
                json.dumps(driver), encoding="utf-8")
            action_id = "sway-9e297c964fd243839fedb26bf6c7ed1a"
            ledger = {
                "schema": g2_preview_operator.SWAY_FORMAL_PENDING_V1_SCHEMA,
                "pending": {
                    "stage": "receipt_pending", "action_id": action_id,
                    "actor_character_id": 29829,
                    "target_character_id": 32716,
                    "pre_capture_epoch": 7502,
                    "pre_container_generation": 13183742510539082018,
                    "pre_date_raw": 53219928, "pre_native_revision": 3,
                    "pre_target_opinion_of_actor": -5,
                    "ack": {
                        "schema": "active-scheme-sway-formal-private-v1",
                        "stage": "submitted_verification_pending",
                        "action_id": action_id,
                        "actor_character_id": 29829,
                        "target_character_id": 32716,
                        "pre_capture_epoch": 7852,
                        "pre_container_generation": 13183742510539082018,
                        "pre_date_raw": 53219928,
                        "submit_call_count": 1, "receipt_pending": True,
                    },
                }, "resolved": None,
            }
            source = root / "sway-ledger.json"
            source_bytes = json.dumps(ledger, indent=2).encode("utf-8")
            source.write_bytes(source_bytes)
            pair = g2_preview_operator.sway_formal_pending_sidecar_request
            self.assertEqual(pair(ledger, driver, save_hash, len(save_bytes)),
                             action_id)
            with self.assertRaisesRegex(ValueError, "does not match"):
                pair(ledger, {**driver, "last_checkpoint": {
                    **driver["last_checkpoint"], "sha256": "b" * 64,
                }}, save_hash, len(save_bytes))
            with self.assertRaisesRegex(ValueError, "saved pending"):
                pair({**ledger, "resolved": {"status": "applied"}},
                     driver, save_hash, len(save_bytes))
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps({
                "python": str(root / "python.exe"),
                "source_repo": str(root / "repo"),
                "state_dir": str(root / "state"),
                "game_dir": str(root / "game"),
                "pipe": r"\\.\pipe\sway-pending-test",
                "dll": str(root / "bridge.dll"),
                "injector": str(root / "injector.exe"),
            }), encoding="utf-8")
            parsed = g2_preview_operator.parser().parse_args([
                "prepare-state", "--manifest", str(manifest_path),
                "--sample-dir", str(sample),
                "--sway-formal-sidecar", str(source),
            ])
            stdout = io.StringIO()
            with (mock.patch.object(g2_preview_operator.subprocess, "run",
                                    return_value=mock.Mock(returncode=0)),
                  contextlib.redirect_stdout(stdout)):
                self.assertEqual(g2_preview_operator.command_prepare_state(parsed), 0)
            receipt = json.loads(stdout.getvalue())["sway_formal_pending_sidecar"]
            self.assertEqual(receipt["status"], "paired_no_launch")
            self.assertEqual(receipt["ledger_status"], "pending")
            self.assertEqual(receipt["action_id"], action_id)
            self.assertEqual(Path(receipt["path"]).read_bytes(), source_bytes)
            self.assertEqual(receipt["sha256"],
                             hashlib.sha256(source_bytes).hexdigest())
            self.assertIsNone(json.loads(Path(receipt["path"]).read_text(
                encoding="utf-8"))["resolved"])

    def test_child_pending_sidecar_requires_saved_formal_submit_pair(self) -> None:
        save_hash = "a" * 64
        episode = "native-29829-test"
        pending = {
            "schema": g2_preview_operator.CHILD_MATRILINEAL_SCHEMA,
            "status": "receipt_pending", "submission_state": "receipt_pending",
            "material_result": False, "accepted": True,
            "matrilineal_option_selected": True,
            "played_character_id": 29829, "heir_character_id": 37265,
            "candidate_character_id": 37267, "recipient_character_id": 32440,
            "episode_run_id": episode, "source_bridge_pid": 1234,
            "source_date_raw": 53219928,
        }
        sidecar = {"schema": g2_preview_operator.CHILD_MATRILINEAL_SCHEMA,
                   "pending": pending, "resolved": None}
        checkpoint = {"history_index": 3915, "date_raw": 53219928,
                      "sha256": save_hash, "episode_character_id": 29829,
                      "episode_run_id": episode}
        driver = {"episode_character_id": 29829, "episode_run_id": episode,
                  "last_checkpoint": checkpoint}
        result = {"step": g2_preview_operator.CHILD_MATRILINEAL_SUBMIT_STEP,
                  "status": "receipt_pending", "accepted": True,
                  "material_result": False, "played_character_id": 29829,
                  "heir_character_id": 37265, "candidate_character_id": 37267,
                  "recipient_character_id": 32440, "episode_run_id": episode}
        proof = {
            "schema": g2_preview_operator.CHILD_MATRILINEAL_PROOF_SCHEMA,
            "status": "receipt_pending_checkpointed", "ok": True,
            "child_ledger": sidecar,
            "formal_auto_run": {
                "status": "turn_limit", "cleanup": {"ok": True},
                "session": {"pid": 1234},
                "auto_run": {"turns": [{"index": 1,
                    "selected_step": g2_preview_operator.CHILD_MATRILINEAL_SUBMIT_STEP,
                    "status": "executed", "result": result}]},
                "checkpoints": [{**checkpoint, "turn_index": 1,
                    "phase": "player_child_matrilineal_submitted_pending",
                    "status": "saved", "pending_action": {
                        "heir_character_id": 37265,
                        "candidate_character_id": 37267,
                        "recipient_character_id": 32440,
                        "episode_run_id": episode,
                        "matrilineal_option_selected": True}}],
            },
        }
        paired = g2_preview_operator.child_matrilineal_pending_sidecar_pair
        self.assertEqual(paired(sidecar, driver, {}, save_hash, proof), 37267)
        with self.assertRaisesRegex(ValueError, "paired save"):
            paired(sidecar, driver, {}, "b" * 64, proof)
        changed = copy.deepcopy(proof)
        changed["formal_auto_run"]["checkpoints"][0]["pending_action"][
            "matrilineal_option_selected"] = False
        with self.assertRaisesRegex(ValueError, "saved submit"):
            paired(sidecar, driver, {}, save_hash, changed)

        later_sidecar = copy.deepcopy(sidecar)
        later_sidecar["pending"].update({
            "last_checked_bridge_pid": 4321,
            "last_checked_native_revision": 4,
            "last_outbound_pending_state": "active",
        })
        later_hash = "c" * 64
        later_checkpoint = {**checkpoint, "history_index": 3922,
                            "sha256": later_hash, "turn_index": 3,
                            "phase": "candidate_terminal_intercept", "status": "saved"}
        later_driver = {**driver, "last_checkpoint": later_checkpoint}
        continuation = {
            "schema": g2_preview_operator.CHILD_MATRILINEAL_COLD_PROOF_SCHEMA,
            # The one-time R0329 wrapper misclassified an intercepted third query.
            "status": "cold_result_not_qualified", "ok": False,
            "child_ledger": later_sidecar,
            "formal_auto_run": {
                "ok": True, "status": "candidate_terminal_intercepted",
                "cleanup": {"ok": True}, "session": {"pid": 4321},
                "fixed_seed": {"sha256": save_hash,
                               "history_index": 3915,
                               "saved_date_raw": 53219928},
                "readiness": {"bridge_pid": 4321,
                              "episode_character_id": 29829,
                              "episode_run_id": episode},
                "auto_run": {"turns": [
                    {"index": 1, "selected_step":
                     g2_preview_operator.CHILD_MATRILINEAL_RESULT_STEP,
                     "status": "executed", "result": {
                         "status": "pending", "accepted": True,
                         "material_result": False, "heir_character_id": 37265,
                         "candidate_character_id": 37267,
                         "recipient_character_id": 32440,
                         "post_native_revision": 4,
                         "outbound_pending_state": "active"}},
                    {"index": 2, "selected_step":
                     "query-war-termination-options-16777231",
                     "status": "executed"},
                    {"index": 3, "selected_step": "query-army-strengths-v1",
                     "status": "intercepted"}]},
                "checkpoints": [later_checkpoint],
            },
        }
        self.assertEqual(
            paired(later_sidecar, later_driver, {}, later_hash,
                   [proof, continuation]), 37267)
        changed = copy.deepcopy(continuation)
        changed["formal_auto_run"]["fixed_seed"]["sha256"] = "b" * 64
        with self.assertRaisesRegex(ValueError, "prior checkpoint"):
            paired(later_sidecar, later_driver, {}, later_hash,
                   [proof, changed])

        sway_hash = "d" * 64
        sway_checkpoint = {**later_checkpoint, "history_index": 3924,
                           "sha256": sway_hash, "size": 78515535,
                           "phase": "private_active_scheme_sway_receipt_pending"}
        sway_driver = {**driver, "last_checkpoint": sway_checkpoint}
        sway_action_id = "sway-9e297c964fd243839fedb26bf6c7ed1a"
        sway_pending = {
            "stage": "receipt_pending", "action_id": sway_action_id,
            "actor_character_id": 29829, "target_character_id": 32716,
            "pre_capture_epoch": 7502,
            "pre_container_generation": 13183742510539082018,
            "pre_date_raw": 53219928, "pre_native_revision": 3,
            "pre_target_opinion_of_actor": -5,
            "ack": {
                "schema": "active-scheme-sway-formal-private-v1",
                "stage": "submitted_verification_pending",
                "action_id": sway_action_id,
                "actor_character_id": 29829, "target_character_id": 32716,
                "pre_capture_epoch": 7852,
                "pre_container_generation": 13183742510539082018,
                "pre_date_raw": 53219928,
                "submit_call_count": 1, "receipt_pending": True,
            },
        }
        sway_ledger = {"schema": g2_preview_operator.SWAY_FORMAL_PENDING_V1_SCHEMA,
                       "pending": sway_pending, "resolved": None}
        sway_report = {
            "kind": "ck3_native_auto_run", "mode": "native-headless",
            "status": "private_active_scheme_sway_receipt_pending",
            "ok": False,
            "fixed_seed": {"sha256": later_hash, "history_index": 3922,
                           "saved_date_raw": 53219928},
            "session": {"pid": 171504},
            "readiness": {"bridge_pid": 171504,
                          "episode_character_id": 29829,
                          "episode_run_id": episode, "date_raw": 53219928},
            "auto_run": {"attempted_turns": 0, "turns": []},
            "private_active_scheme_sway_formal": {
                "status": "receipt_pending", "pending": sway_pending,
                "checkpoint_saved": True, "postcondition_verified": False},
            "private_active_scheme_sway_observation": {
                "same_frame": True, "readback": {
                    "actor_character_id": 29829,
                    "target_character_id": 32716,
                    "active_scheme_count": 0,
                    "matching_sway_active": False,
                }},
            "checkpoints": [sway_checkpoint],
            "first_blocker": {"last_durable_checkpoint": sway_checkpoint},
            "cleanup": {"ok": True},
        }
        self.assertEqual(paired(
            later_sidecar, sway_driver, {}, sway_hash, [proof, continuation],
            sway_continuation=sway_report, sway_sidecar=sway_ledger), 37267)
        for changed_key, changed_value in (
            ("fixed_seed", {**sway_report["fixed_seed"], "sha256": "b" * 64}),
            ("auto_run", {"attempted_turns": 1, "turns": [{
                "selected_step": g2_preview_operator.CHILD_MATRILINEAL_SUBMIT_STEP}]}),
            ("private_active_scheme_sway_formal", {
                **sway_report["private_active_scheme_sway_formal"],
                "pending": {**sway_pending, "action_id": "sway-" + "f" * 32}}),
        ):
            changed = copy.deepcopy(sway_report)
            changed[changed_key] = changed_value
            with self.assertRaisesRegex(ValueError, "Sway continuation"):
                paired(later_sidecar, sway_driver, {}, sway_hash,
                       [proof, continuation], sway_continuation=changed,
                       sway_sidecar=sway_ledger)
        with self.assertRaisesRegex(ValueError, "Sway continuation"):
            paired(later_sidecar, sway_driver, {}, sway_hash,
                   [proof, continuation], sway_continuation=sway_report,
                   sway_sidecar={**sway_ledger, "resolved": {"status": "applied"}})
        with self.assertRaisesRegex(ValueError, "paired save"):
            paired(later_sidecar, sway_driver, {}, "e" * 64,
                   [proof, continuation], sway_continuation=sway_report,
                   sway_sidecar=sway_ledger)
        parsed = g2_preview_operator.parser().parse_args([
            "prepare-state", "--manifest", "Z:/candidate/operator-manifest.json",
            "--sample-dir", "Z:/sample", "--child-matrilineal-sidecar",
            "Z:/sample/child.json", "--child-matrilineal-proof-report",
            "Z:/proof/R0328.json", "--child-matrilineal-continuation-report",
            "Z:/proof/R0339.json",
        ])
        self.assertEqual(parsed.child_matrilineal_continuation_report,
                         Path("Z:/proof/R0339.json"))
        applied_hash = "e" * 64
        applied_checkpoint = {**sway_checkpoint, "history_index": 3928,
                              "sha256": applied_hash,
                              "phase": "private_active_scheme_sway_applied"}
        applied_driver = {**driver, "last_checkpoint": applied_checkpoint}
        resolved = {
            "status": "applied", "postcondition_verified": True,
            "actor_character_id": 29829, "target_character_id": 32716,
            "action_id": sway_action_id, "pre_capture_epoch": 7502,
            "post_capture_epoch": 5817, "post_native_revision": 3,
            "post_date_raw": 53219928, "native_receipt": None,
            "next_turn_consumed": False,
        }
        resolved_ledger = {
            "schema": g2_preview_operator.SWAY_FORMAL_PENDING_V1_SCHEMA,
            "pending": None, "resolved": resolved,
        }
        applied_report = {
            "status": "private_active_scheme_sway_applied", "ok": True,
            "fixed_seed": {"sha256": sway_hash, "size": 78515535,
                           "history_index": 3924,
                           "saved_date_raw": 53219928},
            "session": {"pid": 172808},
            "readiness": {"bridge_pid": 172808,
                          "episode_character_id": 29829,
                          "episode_run_id": episode, "date_raw": 53219928},
            "auto_run": {"attempted_turns": 0, "turns": []},
            "private_active_scheme_sway_observation": {
                "status": "observed", "same_frame": True,
                "target_character_id": 32716,
                "readback": {
                    "actor_character_id": 29829,
                    "target_character_id": 32716,
                    "date_raw": 53219928,
                    "active_scheme_count": 1,
                    "matching_sway_active": True,
                    "capture_epoch": 5817,
                    "queried_native_revision": 3,
                }},
            "private_active_scheme_sway_formal": {
                **resolved, "checkpoint_saved": True},
            "checkpoints": [applied_checkpoint],
            "cleanup": {"ok": True},
        }
        resolved_pair = g2_preview_operator.sway_formal_resolved_sidecar_pair
        self.assertEqual(resolved_pair(
            resolved_ledger, applied_driver, applied_hash, 78515535,
            sway_report, applied_report), (sway_action_id, applied_checkpoint))
        self.assertEqual(paired(
            later_sidecar, applied_driver, {}, applied_hash,
            [proof, continuation], sway_continuation=sway_report,
            sway_sidecar=resolved_ledger,
            sway_applied_continuation=applied_report), 37267)
        for mutate in (
            lambda report: report["private_active_scheme_sway_observation"]
                ["readback"].update(matching_sway_active=False),
            lambda report: report["auto_run"].update(
                attempted_turns=1, turns=[{"selected_step":
                    "submit-active-scheme-sway-v1-private-32716"}]),
            lambda report: report["fixed_seed"].update(sha256="f" * 64),
        ):
            changed = copy.deepcopy(applied_report)
            mutate(changed)
            with self.assertRaises(ValueError):
                resolved_pair(resolved_ledger, applied_driver, applied_hash,
                              78515535, sway_report, changed)
        changed_ledger = copy.deepcopy(resolved_ledger)
        changed_ledger["resolved"]["action_id"] = "sway-" + "f" * 32
        with self.assertRaises(ValueError):
            resolved_pair(changed_ledger, applied_driver, applied_hash,
                          78515535, sway_report, applied_report)
        changed_ledger = copy.deepcopy(resolved_ledger)
        changed_ledger["resolved"]["pre_capture_epoch"] = 7503
        with self.assertRaises(ValueError):
            resolved_pair(changed_ledger, applied_driver, applied_hash,
                          78515535, sway_report, applied_report)
        parsed = g2_preview_operator.parser().parse_args([
            "prepare-state", "--manifest", "Z:/candidate/operator-manifest.json",
            "--sample-dir", "Z:/sample", "--sway-formal-applied-report",
            "Z:/proof/R0342.json",
        ])
        self.assertEqual(parsed.sway_formal_applied_report,
                         Path("Z:/proof/R0342.json"))
        changed = copy.deepcopy(continuation)
        changed["formal_auto_run"]["auto_run"]["turns"].append({
            "selected_step": g2_preview_operator.CHILD_MATRILINEAL_SUBMIT_STEP})
        with self.assertRaisesRegex(ValueError, "prior checkpoint"):
            paired(later_sidecar, later_driver, {}, later_hash,
                   [proof, changed])

        # R0352 saved a later child result beside an active pending ledger,
        # while the old generic bounded qualifier still returned RED.
        post_sidecar = copy.deepcopy(later_sidecar)
        post_sidecar["pending"].update({
            "last_checked_bridge_pid": 56288,
            "last_checked_native_revision": 3,
            "last_outbound_pending_state": "active",
        })
        post_hash = "f" * 64
        post_checkpoint = {**applied_checkpoint, "history_index": 3933,
                           "sha256": post_hash, "turn_index": 1,
                           "phase": "player_child_matrilineal_result_pending",
                           "ledger_status": "pending", "status": "saved"}
        post_history = [None] * 3933
        post_history[3932] = {"index": 3933, "command": "save-checkpoint",
                              "ok": True, "result": {"checkpoint": post_checkpoint}}
        post_driver = {**driver, "last_checkpoint": post_checkpoint,
                       "command_history": post_history}
        # H3933's real checkpoint cannot validate the earlier R0342 Sway
        # effect. The prepared copy must recheck Sway against H3928, while
        # child pairing below still checks the genuine H3933 driver/save.
        with self.assertRaisesRegex(ValueError, "resolved Sway readback/checkpoint"):
            resolved_pair(resolved_ledger, post_driver, post_hash, 78515535,
                          sway_report, applied_report)
        self.assertEqual(resolved_pair(
            resolved_ledger,
            {**post_driver, "last_checkpoint": applied_checkpoint},
            applied_hash, 78515535, sway_report, applied_report),
            (sway_action_id, applied_checkpoint))
        binding = {"paused": True, "date_raw": 53219928,
                   "episode_character_id": 29829, "episode_run_id": episode}
        post_report = {
            "kind": "ck3_native_auto_run", "completion_contract": "bounded",
            "status": "turn_limit", "outcome": "not_qualified", "ok": False,
            "first_blocker": {"kind": "run_bound_exhausted",
                              "last_durable_checkpoint": post_checkpoint},
            "cleanup": {"ok": True}, "session": {"pid": 56288},
            "fixed_seed": {"sha256": applied_hash, "history_index": 3928,
                           "saved_date_raw": 53219928},
            "readiness": {"bridge_pid": 56288,
                          "episode_character_id": 29829,
                          "episode_run_id": episode, "date_raw": 53219928},
            "auto_run": {"attempted_turns": 1, "visible_gameplay_turns": 0,
                         "turns": [{
                             "index": 1, "ok": True, "status": "executed",
                             "class": "query", "selected_step":
                             g2_preview_operator.CHILD_MATRILINEAL_RESULT_STEP,
                             "before": binding, "after": binding,
                             "evidence": ["child_matrilineal_result_checkpoint_saved"],
                             "result": {"status": "pending", "material_result": False,
                                        "heir_character_id": 37265,
                                        "candidate_character_id": 37267,
                                        "recipient_character_id": 32440,
                                        "post_native_revision": 3,
                                        "outbound_pending_state": "active"}}]},
            "checkpoints": [post_checkpoint],
        }
        self.assertEqual(paired(
            post_sidecar, post_driver, {}, post_hash, [proof, continuation],
            sway_continuation=sway_report, sway_sidecar=resolved_ledger,
            sway_applied_continuation=applied_report,
            post_sway_result=post_report), 37267)
        changed = copy.deepcopy(post_report)
        changed["auto_run"]["turns"][0]["selected_step"] = (
            g2_preview_operator.CHILD_MATRILINEAL_SUBMIT_STEP)
        with self.assertRaisesRegex(ValueError, "post-Sway child pending read"):
            paired(post_sidecar, post_driver, {}, post_hash,
                   [proof, continuation], sway_continuation=sway_report,
                   sway_sidecar=resolved_ledger,
                   sway_applied_continuation=applied_report,
                   post_sway_result=changed)
        changed = copy.deepcopy(post_report)
        changed["checkpoints"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "post-Sway child pending read"):
            paired(post_sidecar, post_driver, {}, post_hash,
                   [proof, continuation], sway_continuation=sway_report,
                   sway_sidecar=resolved_ledger,
                   sway_applied_continuation=applied_report,
                   post_sway_result=changed)
        parsed = g2_preview_operator.parser().parse_args([
            "prepare-state", "--manifest", "Z:/candidate/operator-manifest.json",
            "--sample-dir", "Z:/sample",
            "--child-matrilineal-post-sway-result-report", "Z:/proof/R0352.json",
        ])
        self.assertEqual(parsed.child_matrilineal_post_sway_result_report,
                         Path("Z:/proof/R0352.json"))
        # R0357 read the same still-pending proposal on a new PID and saved
        # H3937. Both result reports must link from R0342, in order; only the
        # last one has to equal the source driver's current checkpoint/ledger.
        final_sidecar = copy.deepcopy(post_sidecar)
        final_sidecar["pending"]["last_checked_bridge_pid"] = 101676
        final_hash = "e" * 64
        final_checkpoint = {**post_checkpoint, "history_index": 3937,
                            "sha256": final_hash}
        final_history = [*post_history, None, None, None, {
            "index": 3937, "command": "save-checkpoint", "ok": True,
            "result": {"checkpoint": final_checkpoint}}]
        final_driver = {**driver, "last_checkpoint": final_checkpoint,
                        "command_history": final_history}
        followup = copy.deepcopy(post_report)
        followup.update({
            "ok": True, "outcome": "qualified", "first_blocker": None,
            "session": {"pid": 101676},
            "fixed_seed": {"sha256": post_hash, "history_index": 3933,
                           "saved_date_raw": 53219928},
            "readiness": {"bridge_pid": 101676,
                          "episode_character_id": 29829,
                          "episode_run_id": episode, "date_raw": 53219928},
            "checkpoints": [final_checkpoint],
        })
        self.assertEqual(paired(
            final_sidecar, final_driver, {}, final_hash,
            [proof, continuation], sway_continuation=sway_report,
            sway_sidecar=resolved_ledger,
            sway_applied_continuation=applied_report,
            post_sway_result=post_report,
            post_sway_followups=[followup]), 37267)
        tampered_driver = copy.deepcopy(final_driver)
        tampered_driver["command_history"][3932]["result"]["checkpoint"][
            "sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "post-Sway child pending read"):
            paired(final_sidecar, tampered_driver, {}, final_hash,
                   [proof, continuation], sway_continuation=sway_report,
                   sway_sidecar=resolved_ledger,
                   sway_applied_continuation=applied_report,
                   post_sway_result=post_report,
                   post_sway_followups=[followup])
        broken = copy.deepcopy(followup)
        broken["fixed_seed"]["sha256"] = applied_hash
        with self.assertRaisesRegex(ValueError, "post-Sway child pending read"):
            paired(final_sidecar, final_driver, {}, final_hash,
                   [proof, continuation], sway_continuation=sway_report,
                   sway_sidecar=resolved_ledger,
                   sway_applied_continuation=applied_report,
                   post_sway_result=post_report,
                   post_sway_followups=[broken])
        parsed = g2_preview_operator.parser().parse_args([
            "prepare-state", "--manifest", "Z:/candidate/operator-manifest.json",
            "--sample-dir", "Z:/sample",
            "--child-matrilineal-post-sway-result-report", "Z:/proof/R0352.json",
            "--child-matrilineal-followup-result-report", "Z:/proof/R0357.json",
        ])
        self.assertEqual(parsed.child_matrilineal_followup_result_report,
                         [Path("Z:/proof/R0357.json")])

    def test_exact_war_move_contract_is_bound_in_formal_argv(self) -> None:
        path = Path("D:/frozen/exact-move.json")
        command = g2_preview_operator.native_auto_run_command(
            ["python", "-m", "xar_autoplayer"],
            turns=8, timeout=7200, readiness_timeout=1800,
            private_faction_round_id_value=None,
            exact_war_move_stop_contract=path,
            exact_war_move_stop_sha256="a" * 64,
        )
        self.assertEqual(command[-4:], [
            "--exact-war-move-stop-contract", str(path),
            "--exact-war-move-stop-sha256", "a" * 64,
        ])

    def test_child_pending_read_is_explicit_and_query_only(self) -> None:
        common = ["python", "-m", "xar_autoplayer"]
        args = g2_preview_operator.parser().parse_args([
            "run", "--manifest", "Z:/candidate/manifest.json",
            "--output", "Z:/candidate/run",
            "--private-child-matrilineal-pending-read", "37265", "37267",
        ])
        self.assertEqual(args.private_child_matrilineal_pending_read,
                         [37265, 37267])
        command = g2_preview_operator.native_auto_run_command(
            common, turns=2, timeout=600, readiness_timeout=300,
            private_faction_round_id_value=None,
            private_child_matrilineal_pending_read=(37265, 37267),
        )
        self.assertEqual(command[-3:], [
            "--private-child-matrilineal-pending-read", "37265", "37267",
        ])
        self.assertNotIn("--allow-private-family-marriage-formal-trial", command)

    def test_child_pending_recovery_routes_one_formal_life_turn(self) -> None:
        parsed = g2_preview_operator.parser().parse_args([
            "run", "--manifest", "Z:/candidate/manifest.json",
            "--output", "Z:/candidate/recovery",
            "--private-lifestyle-formal-trial",
            "--private-child-matrilineal-pending-recovery", "37265", "37267",
            "--child-matrilineal-recovery-proof-report", "Z:/proof/R0328.json",
            "--child-matrilineal-recovery-post-sway-result-report",
            "Z:/proof/R0352.json",
        ])
        self.assertEqual(parsed.private_child_matrilineal_pending_recovery,
                         [37265, 37267])
        self.assertEqual(parsed.child_matrilineal_recovery_post_sway_result_report,
                         Path("Z:/proof/R0352.json"))
        command = g2_preview_operator.native_auto_run_command(
            ["python", "-m", "xar_autoplayer"],
            turns=1, timeout=600, readiness_timeout=300,
            private_faction_round_id_value=None,
            private_lifestyle_formal_trial=True,
            private_child_matrilineal_pending_recovery=(37265, 37267),
        )
        self.assertIn("--allow-private-lifestyle-formal-trial", command)
        self.assertEqual(command[-3:], [
            "--private-child-matrilineal-pending-recovery", "37265", "37267",
        ])
        self.assertNotIn("--private-child-matrilineal-pending-read", command)

    def test_logged_child_start_callback_runs_only_after_spawn(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            seen: list[int] = []
            exit_code = g2_preview_operator.run_logged(
                [sys.executable, "-c", "print('ready')"],
                root / "stdout.txt", root / "stderr.txt",
                on_started=seen.append,
            )
            self.assertEqual(exit_code, 0)
            self.assertEqual(len(seen), 1)
            self.assertGreater(seen[0], 0)
            self.assertEqual(
                (root / "stdout.txt").read_text(encoding="utf-8").strip(),
                "ready",
            )
            seen.clear()
            with mock.patch.object(
                g2_preview_operator.subprocess, "Popen",
                side_effect=OSError("spawn failed"),
            ), self.assertRaisesRegex(OSError, "spawn failed"):
                g2_preview_operator.run_logged(
                    [sys.executable, "-c", "print('never')"],
                    root / "failed-stdout.txt", root / "failed-stderr.txt",
                    on_started=seen.append,
                )
            self.assertEqual(seen, [])

    def test_prepare_state_carries_paired_faction_gift_pending_identity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sample = root / "sample"
            sample.mkdir()
            save = sample / "xar_checkpoint.ck3"
            save.write_bytes(b"pre-gift checkpoint")
            digest = hashlib.sha256(save.read_bytes()).hexdigest()
            episode = "native-29829-test"
            driver = {
                "episode_character_id": 29829,
                "episode_run_id": episode,
                "last_checkpoint": {
                    "sha256": digest, "date_raw": 53154528,
                    "episode_character_id": 29829, "episode_run_id": episode,
                },
            }
            (sample / "driver-state.json").write_text(json.dumps(driver), encoding="utf-8")
            pending = {
                "request_id": "faction-gift-" + "a" * 32,
                "episode_run_id": episode,
                "source_faction_id": 771,
                "source_round_id": "R742",
                "source_bridge_pid": 12345,
                "source_bridge_creation_date": "old-process",
                "recipient_character_id": 33011,
                "pre_snapshot_revision": 12,
                "pre_native_snapshot_revision": 13,
                "pre_player_character_id": 29829,
                "pre_date_raw": 53154528,
                "pre_player_gold_raw": 25_000_000,
                "pre_recipient_opinion_of_player": -40,
                "pre_gift_opinion_present": False,
                "pre_source_faction_power_raw": 65_000_000,
                "pre_source_faction_discontent_raw": 45_000_000,
                "pre_source_faction_member_character_ids": [33011],
                "pre_source_faction_targeting_player": True,
                "gold_cost_raw": 7_500_000,
                "opinion_delta": 25,
                "minimum_gold_reserve_raw": 10_000_000,
                "checkpoint_sha256_before_submit": digest,
                "status": "submitted_verification_pending",
                "ack": None,
            }
            sidecar = sample / "faction-gift-pending-v1.json"
            sidecar.write_text(json.dumps({
                "schema": "xar.ck3.faction_gift_pending_v1",
                "format_version": 1,
                "pending": pending,
                "resolved_request_outcomes": {},
            }), encoding="utf-8")
            manifest = root / "manifest.json"
            state = root / "state"
            manifest.write_text(json.dumps({
                "python": str(root / "python.exe"),
                "source_repo": str(root / "repo"),
                "state_dir": str(state),
                "game_dir": str(root / "game"),
                "pipe": r"\\.\pipe\faction-gift-test",
                "dll": str(root / "bridge.dll"),
                "injector": str(root / "injector.exe"),
                "episode_character_id": 29829,
                "episode_run_id": episode,
            }), encoding="utf-8")
            args = argparse.Namespace(manifest=manifest, sample_dir=sample,
                                      faction_gift_sidecar=sidecar)
            output = io.StringIO()
            with (mock.patch.object(g2_preview_operator.subprocess, "run",
                                    return_value=mock.Mock(returncode=0)),
                  contextlib.redirect_stdout(output)):
                self.assertEqual(g2_preview_operator.command_prepare_state(args), 0)
            target = state / "native-session" / "faction-gift-pending-v1.json"
            self.assertEqual(target.read_bytes(), sidecar.read_bytes())
            receipt = json.loads(output.getvalue())
            self.assertEqual(receipt["faction_gift_pending_sidecar"]["status"],
                             "paired_no_launch")
            self.assertEqual(receipt["faction_gift_pending_sidecar"]["sha256"],
                             hashlib.sha256(sidecar.read_bytes()).hexdigest())
            sidecar.write_text(json.dumps({
                "schema": "xar.ck3.faction_gift_pending_v1",
                "format_version": 1, "pending": None,
                "resolved_request_outcomes": {pending["request_id"]: "applied"},
            }), encoding="utf-8")
            manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
            resolved_state = root / "resolved-state"
            manifest_data["state_dir"] = str(resolved_state)
            manifest.write_text(json.dumps(manifest_data), encoding="utf-8")
            with (mock.patch.object(g2_preview_operator.subprocess, "run",
                                    return_value=mock.Mock(returncode=0)),
                  contextlib.redirect_stdout(io.StringIO())):
                self.assertEqual(g2_preview_operator.command_prepare_state(
                    argparse.Namespace(manifest=manifest, sample_dir=sample)), 0)
            self.assertFalse((resolved_state / "native-session" /
                              "faction-gift-pending-v1.json").exists())
            manifest_data["state_dir"] = str(root / "explicit-resolved-state")
            manifest.write_text(json.dumps(manifest_data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "explicit faction gift sidecar"):
                g2_preview_operator.command_prepare_state(
                    argparse.Namespace(manifest=manifest, sample_dir=sample,
                                       faction_gift_sidecar=sidecar))
            pending["checkpoint_sha256_before_submit"] = "b" * 64
            with self.assertRaisesRegex(ValueError, "pre-submit save/driver"):
                g2_preview_operator.faction_gift_pending_sidecar_request(
                    {"schema": "xar.ck3.faction_gift_pending_v1",
                     "format_version": 1, "pending": pending,
                     "resolved_request_outcomes": {}},
                    driver, {"episode_character_id": 29829,
                             "episode_run_id": episode}, digest,
                )

    def test_family_pending_sidecar_pairs_saved_proposal_and_rejects_other_pair(self) -> None:
        manifest = {"episode_character_id": 29829,
                    "episode_run_id": "native-29829-2bc2d599f7f9"}
        driver = {**manifest, "last_checkpoint": {
            "episode_character_id": 29829,
            "episode_run_id": manifest["episode_run_id"],
            "date_raw": 53216640, "sha256": "a" * 64,
            "history_index": 2443,
        }}
        sidecar = {"schema": g2_preview_operator.FAMILY_PENDING_V1_SCHEMA,
                   "resolved": None, "pending": {
            "schema": g2_preview_operator.FAMILY_ACTION_V1_SCHEMA,
            "status": "receipt_pending", "submission_state": "receipt_pending",
            "material_result": False, "accepted": True,
            "played_character_id": 29829, "heir_character_id": 38822,
            "candidate_character_id": 38718, "recipient_character_id": 32897,
            "episode_run_id": manifest["episode_run_id"],
            "source_date_raw": 53216640, "source_bridge_pid": 59384,
        }}
        report = {"session": {"pid": 59384}, "checkpoints": [{
            "phase": "first_heir_marriage_submitted_pending",
            "status": "saved", "turn_index": 2,
            "sha256": "a" * 64, "history_index": 2443,
            "date_raw": 53216640,
            "episode_character_id": 29829,
            "episode_run_id": manifest["episode_run_id"],
            "pending_action": {"heir_character_id": 38822,
                               "candidate_character_id": 38718,
                               "recipient_character_id": 32897,
                               "episode_run_id": manifest["episode_run_id"]},
        }], "auto_run": {"turns": [{
            "index": 2,
            "selected_step": g2_preview_operator.FAMILY_SUBMIT_STEP,
            "result": {"status": "receipt_pending", "accepted": True,
                       "played_character_id": 29829,
                       "heir_character_id": 38822,
                       "candidate_character_id": 38718,
                       "recipient_character_id": 32897,
                       "episode_run_id": manifest["episode_run_id"]},
            "plan": {"family_marriage_choice": {
                "candidate_character_id": 38718}},
        }]}}
        self.assertEqual(g2_preview_operator.family_pending_sidecar_pair(
            sidecar, driver, manifest, "a" * 64, report), 38718)
        report["checkpoints"][0]["pending_action"]["candidate_character_id"] = 38711
        with self.assertRaisesRegex(ValueError, "not proven"):
            g2_preview_operator.family_pending_sidecar_pair(
                sidecar, driver, manifest, "a" * 64, report)

        # R0259 shape: the proposal was saved at h2443 and remained pending
        # through later result queries and the paired h2513 checkpoint.
        report["checkpoints"][0]["pending_action"]["candidate_character_id"] = 38718
        driver["last_checkpoint"].update({
            "date_raw": 53216784, "sha256": "b" * 64,
            "history_index": 2513,
        })
        report["checkpoints"].append({
            "phase": "periodic_checkpoint", "status": "saved",
            "turn_index": 36, "sha256": "b" * 64,
            "history_index": 2513, "date_raw": 53216784,
            "episode_character_id": 29829,
            "episode_run_id": manifest["episode_run_id"],
        })
        report["auto_run"]["turns"].append({
            "index": 33,
            "selected_step": "query-observed-first-heir-marriage-result-v1-private",
            "result": {"status": "pending", "heir_character_id": 38822,
                       "candidate_character_id": 38718},
        })
        self.assertEqual(g2_preview_operator.family_pending_sidecar_pair(
            sidecar, driver, manifest, "b" * 64, report), 38718)
        accepted_pending_report = copy.deepcopy(report)
        accepted_pending_report["auto_run"]["turns"][-1]["result"]["status"] = "accepted_pending"
        self.assertEqual(g2_preview_operator.family_pending_sidecar_pair(
            sidecar, driver, manifest, "b" * 64, accepted_pending_report), 38718)
        report_without_query = copy.deepcopy(report)
        report_without_query["auto_run"]["turns"].pop()
        with self.assertRaisesRegex(ValueError, "lacks pending family result query"):
            g2_preview_operator.family_pending_sidecar_pair(
                sidecar, driver, manifest, "b" * 64, report_without_query)
        report_with_later_refusal = copy.deepcopy(report)
        report_with_later_refusal["auto_run"]["turns"].append({
            "index": 34,
            "selected_step": "query-observed-first-heir-marriage-result-v1-private",
            "result": {"status": "refused", "heir_character_id": 38822,
                       "candidate_character_id": 38718},
        })
        with self.assertRaisesRegex(ValueError, "lacks pending family result query"):
            g2_preview_operator.family_pending_sidecar_pair(
                sidecar, driver, manifest, "b" * 64, report_with_later_refusal)
        report_with_duplicate = copy.deepcopy(report)
        report_with_duplicate["auto_run"]["turns"].append(
            copy.deepcopy(report_with_duplicate["auto_run"]["turns"][0]))
        with self.assertRaisesRegex(ValueError, "one saved formal submit"):
            g2_preview_operator.family_pending_sidecar_pair(
                sidecar, driver, manifest, "b" * 64, report_with_duplicate)
        with self.assertRaisesRegex(ValueError, "identity disagrees with paired save"):
            g2_preview_operator.family_pending_sidecar_pair(
                sidecar, driver, manifest, "c" * 64, report)

    def test_family_pending_sidecar_pairs_consecutive_cold_formal_runs(self) -> None:
        episode = "native-29829-2bc2d599f7f9"
        manifest = {"episode_character_id": 29829, "episode_run_id": episode}
        sidecar = {"schema": g2_preview_operator.FAMILY_PENDING_V1_SCHEMA,
                   "resolved": None, "pending": {
            "schema": g2_preview_operator.FAMILY_ACTION_V1_SCHEMA,
            "status": "receipt_pending", "submission_state": "receipt_pending",
            "material_result": False, "accepted": True,
            "played_character_id": 29829, "heir_character_id": 38822,
            "candidate_character_id": 38718, "recipient_character_id": 32897,
            "episode_run_id": episode, "source_date_raw": 53216640,
            "source_bridge_pid": 59384, "last_checked_bridge_pid": 162992,
        }}
        driver = {**manifest, "last_checkpoint": {
            "episode_character_id": 29829, "episode_run_id": episode,
            "date_raw": 53216856, "sha256": "c" * 64,
            "history_index": 2543,
        }}
        submit_report = {
            "session": {"pid": 59384},
            "checkpoints": [
                {"phase": "first_heir_marriage_submitted_pending",
                 "status": "saved", "turn_index": 2, "history_index": 2443,
                 "date_raw": 53216640, "sha256": "a" * 64,
                 "episode_character_id": 29829, "episode_run_id": episode,
                 "pending_action": {"heir_character_id": 38822,
                                    "candidate_character_id": 38718,
                                    "recipient_character_id": 32897,
                                    "episode_run_id": episode}},
                {"phase": "periodic_checkpoint", "status": "saved",
                 "turn_index": 36, "history_index": 2513,
                 "date_raw": 53216784, "sha256": "b" * 64,
                 "episode_character_id": 29829, "episode_run_id": episode},
            ],
            "auto_run": {"turns": [
                {"index": 2, "selected_step": g2_preview_operator.FAMILY_SUBMIT_STEP,
                 "result": {"status": "receipt_pending", "accepted": True,
                            "played_character_id": 29829,
                            "heir_character_id": 38822,
                            "candidate_character_id": 38718,
                            "recipient_character_id": 32897,
                            "episode_run_id": episode},
                 "plan": {"family_marriage_choice": {
                     "candidate_character_id": 38718}}},
                {"index": 33,
                 "selected_step": "query-observed-first-heir-marriage-result-v1-private",
                 "result": {"status": "pending", "heir_character_id": 38822,
                            "candidate_character_id": 38718}},
            ]},
        }
        cold_report = {
            "ok": True, "session": {"pid": 162992},
            "fixed_seed": {"sha256": "b" * 64,
                           "history_index": 2513,
                           "saved_date_raw": 53216784},
            "readiness": {"bridge_pid": 162992,
                          "episode_character_id": 29829,
                          "episode_run_id": episode},
            "checkpoints": [{"phase": "periodic_checkpoint",
                             "status": "saved", "turn_index": 14,
                             "history_index": 2543,
                             "date_raw": 53216856, "sha256": "c" * 64,
                             "episode_character_id": 29829,
                             "episode_run_id": episode}],
            "auto_run": {"turns": [
                {"index": 11,
                 "selected_step": "query-observed-first-heir-marriage-result-v1-private",
                 "result": {"status": "pending", "heir_character_id": 38822,
                            "candidate_character_id": 38718}},
                {"index": 15,
                 "selected_step": "query-observed-first-heir-marriage-result-v1-private",
                 "result": {"status": "pending", "heir_character_id": 38822,
                            "candidate_character_id": 38718}},
            ]},
        }
        reports = [submit_report, cold_report]
        self.assertEqual(g2_preview_operator.family_pending_sidecar_pair(
            sidecar, driver, manifest, "c" * 64, reports), 38718)
        bad = copy.deepcopy(reports)
        bad[1]["fixed_seed"]["sha256"] = "d" * 64
        with self.assertRaisesRegex(ValueError, "does not continue"):
            g2_preview_operator.family_pending_sidecar_pair(
                sidecar, driver, manifest, "c" * 64, bad)
        bad = copy.deepcopy(reports)
        bad[1]["auto_run"]["turns"][0]["result"]["status"] = "refused"
        with self.assertRaisesRegex(ValueError, "lacks pending family result query"):
            g2_preview_operator.family_pending_sidecar_pair(
                sidecar, driver, manifest, "c" * 64, bad)
        bad = copy.deepcopy(reports)
        bad[1]["auto_run"]["turns"].append({
            "index": 12, "selected_step": g2_preview_operator.FAMILY_SUBMIT_STEP})
        with self.assertRaisesRegex(ValueError, "does not continue"):
            g2_preview_operator.family_pending_sidecar_pair(
                sidecar, driver, manifest, "c" * 64, bad)
        bad = copy.deepcopy(reports)
        bad[1]["auto_run"]["turns"][0]["index"] = 15
        with self.assertRaisesRegex(ValueError, "lacks pending family result query"):
            g2_preview_operator.family_pending_sidecar_pair(
                sidecar, driver, manifest, "c" * 64, bad)
        with self.assertRaisesRegex(ValueError, "identity disagrees with paired save"):
            g2_preview_operator.family_pending_sidecar_pair(
                sidecar, driver, manifest, "d" * 64, reports)

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
            older_request_id = "construction-submit-" + "a" * 32
            older_candidate = {**candidate, "barony_title_id": 2173,
                               "province_id": 2628, "slot_index": 0}
            older_pending = {**pending, "action_request_id": older_request_id,
                             "candidate": older_candidate}
            older_applied = {**applied, "action_request_id": older_request_id,
                             "candidate": older_candidate,
                             "completion_status": "completed",
                             "observed_player_monthly_gold_income_raw": None}
            driver = {
                "episode_character_id": 29829,
                "episode_run_id": "native-29829-test",
                "last_checkpoint": {"history_index": 106,
                                    "episode_character_id": 29829,
                                    "episode_run_id": "native-29829-test"},
                "command_history": [
                    {"index": 90, "command": "private-submit-player-construction-v1",
                     "result": older_pending},
                    {"index": 91, "command": "private-query-player-construction-receipt-v1",
                     "result": older_applied},
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
                "pending": None, "applied": applied, "applied_prior": [older_applied],
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
            self.assertEqual(json.loads(Path(receipt["path"]).read_text(
                encoding="utf-8"))["applied_prior"], [older_applied])

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

    def test_construction_sidecar_pairs_every_prior_applied_receipt(self) -> None:
        actor = 29829
        episode = "native-29829-test"
        candidate_1 = {"barony_title_id": 2174, "province_id": 2629,
                       "building_type_id": 628, "slot_index": 1}
        candidate_2 = {"barony_title_id": 2175, "province_id": 2630,
                       "building_type_id": 629, "slot_index": 2}
        request_1 = "construction-submit-" + "a" * 32
        request_2 = "construction-submit-" + "b" * 32

        def submitted(request_id: str, candidate: dict) -> dict:
            return {"status": "submitted_verification_pending",
                    "action_request_id": request_id, "candidate": candidate,
                    "actor_character_id": actor, "episode_run_id": episode}

        def applied(request_id: str, candidate: dict) -> dict:
            return {"status": "applied", "postcondition_verified": True,
                    "completion_status": "in_progress",
                    "action_request_id": request_id, "candidate": candidate,
                    "actor_character_id": actor, "episode_run_id": episode}

        prior = {**applied(request_1, candidate_1),
                 "completion_status": "completed",
                 "observed_player_monthly_gold_income_raw": None}
        newest = applied(request_2, candidate_2)
        sidecar = {"schema": "xar.ck3.construction_formal_pending_v1",
                   "pending": None, "applied": newest, "applied_prior": [prior]}
        history = [
            {"index": 10, "command": "private-submit-player-construction-v1",
             "result": submitted(request_1, candidate_1)},
            {"index": 11, "command": "private-query-player-construction-receipt-v1",
             "result": prior},
            {"index": 20, "command": "private-submit-player-construction-v1",
             "result": submitted(request_2, candidate_2)},
            {"index": 21, "command": "private-query-player-construction-receipt-v1",
             "result": newest},
        ]
        driver = {"episode_character_id": actor, "episode_run_id": episode,
                  "last_checkpoint": {"history_index": 21,
                                      "episode_character_id": actor,
                                      "episode_run_id": episode},
                  "command_history": history}
        pair = g2_preview_operator.construction_pending_sidecar_request
        self.assertEqual(pair(sidecar, driver, {}), request_2)
        candidate_0 = {"barony_title_id": 2172, "province_id": 2627,
                       "building_type_id": 627, "slot_index": 0}
        request_0 = "construction-submit-" + "c" * 32
        earliest = applied(request_0, candidate_0)
        earliest_rows = [
            {"index": 1, "command": "private-submit-player-construction-v1",
             "result": submitted(request_0, candidate_0)},
            {"index": 2, "command": "private-query-player-construction-receipt-v1",
             "result": earliest},
        ]
        both_prior = {**sidecar, "applied_prior": [earliest, prior]}
        both_driver = {**driver, "command_history": [*earliest_rows, *history]}
        self.assertEqual(pair(both_prior, both_driver, {}), request_2)
        with self.assertRaisesRegex(ValueError, "checkpoint receipt"):
            pair(both_prior, {**both_driver, "command_history":
                              [earliest_rows[0], *history]}, {})
        self.assertEqual(pair({**sidecar, "applied_prior": []}, driver, {}), request_2)
        self.assertEqual(pair({key: value for key, value in sidecar.items()
                               if key != "applied_prior"}, driver, {}), request_2)

        for bad_prior in (None, {}, {**prior, "actor_character_id": actor + 1},
                          {**prior, "action_request_id": request_2},
                          {**prior, "candidate": candidate_2}):
            with self.subTest(bad_prior=bad_prior):
                with self.assertRaises(ValueError):
                    pair({**sidecar, "applied_prior": [bad_prior]}, driver, {})
        with self.assertRaisesRegex(ValueError, "saved submit action"):
            pair(sidecar, {**driver, "command_history": history[1:]}, {})
        with self.assertRaisesRegex(ValueError, "checkpoint receipt"):
            pair(sidecar, {**driver, "command_history":
                           [history[0], *history[2:]]}, {})
        with self.assertRaisesRegex(ValueError, "checkpoint receipt"):
            pair(sidecar, {**driver, "command_history":
                           [{**history[1], "index": 22}, history[0],
                            *history[2:]]}, {})

    def test_second_construction_pending_pairs_existing_applied_receipts(self) -> None:
        actor = 29829
        episode = "native-29829-test"
        first_id = "construction-submit-" + "a" * 32
        second_id = "construction-submit-" + "b" * 32
        older_id = "construction-submit-" + "c" * 32
        first_candidate = {"barony_title_id": 2174, "province_id": 2629,
                           "building_type_id": 628, "slot_index": 1}
        second_candidate = {"barony_title_id": 2175, "province_id": 2630,
                            "building_type_id": 629, "slot_index": 2}
        older_candidate = {"barony_title_id": 2173, "province_id": 2628,
                           "building_type_id": 627, "slot_index": 0}

        def submitted(request_id: str, candidate: dict) -> dict:
            return {"status": "submitted_verification_pending",
                    "action_request_id": request_id, "candidate": candidate,
                    "actor_character_id": actor, "episode_run_id": episode}

        def applied(request_id: str, candidate: dict) -> dict:
            return {"status": "applied", "postcondition_verified": True,
                    "completion_status": "in_progress",
                    "action_request_id": request_id, "candidate": candidate,
                    "actor_character_id": actor, "episode_run_id": episode}

        oldest = applied(older_id, older_candidate)
        existing = applied(first_id, first_candidate)
        pending = submitted(second_id, second_candidate)
        history = [
            {"index": 1, "command": "private-submit-player-construction-v1",
             "result": submitted(older_id, older_candidate)},
            {"index": 2, "command": "private-query-player-construction-receipt-v1",
             "result": oldest},
            {"index": 10, "command": "private-submit-player-construction-v1",
             "result": submitted(first_id, first_candidate)},
            {"index": 11, "command": "private-query-player-construction-receipt-v1",
             "result": existing},
            {"index": 20, "command": "private-submit-player-construction-v1",
             "result": pending},
        ]
        driver = {"episode_character_id": actor, "episode_run_id": episode,
                  "last_checkpoint": {"history_index": 20,
                                      "episode_character_id": actor,
                                      "episode_run_id": episode},
                  "command_history": history}
        sidecar = {"schema": "xar.ck3.construction_formal_pending_v1",
                   "pending": pending, "applied": existing,
                   "applied_prior": [oldest]}
        pair = g2_preview_operator.construction_pending_sidecar_request
        self.assertEqual(pair(sidecar, driver, {}), second_id)
        for bad_sidecar in (
            {**sidecar, "applied": {**existing, "action_request_id": second_id}},
            {**sidecar, "applied": {**existing, "candidate": second_candidate}},
            {**sidecar, "applied_prior": [{**oldest, "actor_character_id": actor + 1}]},
        ):
            with self.subTest(sidecar=bad_sidecar):
                with self.assertRaises(ValueError):
                    pair(bad_sidecar, driver, {})
        with self.assertRaisesRegex(ValueError, "checkpoint receipt"):
            pair(sidecar, {**driver, "command_history":
                           [*history[:3], *history[4:]]}, {})
        with self.assertRaisesRegex(ValueError, "saved submit action"):
            pair(sidecar, {**driver, "command_history": history[1:]}, {})

        # The official prepare-state path must copy this exact sidecar and
        # report the newer pending request, not silently use the old receipt.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sample = root / "sample"
            sample.mkdir()
            (sample / "xar_checkpoint.ck3").write_bytes(b"checkpoint")
            (sample / "driver-state.json").write_text(
                json.dumps(driver), encoding="utf-8")
            sidecar_path = sample / "construction-formal-pending-v1.json"
            sidecar_bytes = json.dumps(sidecar).encode("utf-8")
            sidecar_path.write_bytes(sidecar_bytes)
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps({
                "python": str(root / "python.exe"),
                "source_repo": str(root / "repo"),
                "state_dir": str(root / "state"),
                "game_dir": str(root / "game"),
                "pipe": r"\\.\pipe\ordinary-preview",
                "dll": str(root / "bridge.dll"),
                "injector": str(root / "injector.exe"),
            }), encoding="utf-8")
            args = argparse.Namespace(manifest=manifest_path, sample_dir=sample,
                                      construction_sidecar=None)
            stdout = io.StringIO()
            with (mock.patch.object(g2_preview_operator.subprocess, "run",
                                    return_value=mock.Mock(returncode=0)),
                  contextlib.redirect_stdout(stdout)):
                self.assertEqual(g2_preview_operator.command_prepare_state(args), 0)
            receipt = json.loads(stdout.getvalue())["construction_pending_sidecar"]
            self.assertEqual(receipt["ledger_status"], "pending")
            self.assertEqual(receipt["action_request_id"], second_id)
            self.assertEqual(Path(receipt["path"]).read_bytes(), sidecar_bytes)

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

    def test_completed_construction_without_income_still_requires_sidecar(self) -> None:
        actor = 29829
        episode = "native-29829-test"
        completed = {"status": "applied", "postcondition_verified": True,
                     "completion_status": "completed",
                     "observed_player_monthly_gold_income_raw": None,
                     "action_request_id": "construction-submit-" + "a" * 32,
                     "actor_character_id": actor, "episode_run_id": episode}
        driver = {"episode_character_id": actor, "episode_run_id": episode,
                  "last_checkpoint": {"history_index": 10,
                                      "episode_character_id": actor,
                                      "episode_run_id": episode},
                  "command_history": [
                      {"index": 9,
                       "command": "private-query-player-construction-receipt-v1",
                       "result": completed}]}
        requires_sidecar = g2_preview_operator.saved_in_progress_construction_without_sidecar
        self.assertTrue(requires_sidecar(driver))
        observed = {**completed, "observed_player_monthly_gold_income_raw": 603774}
        self.assertFalse(requires_sidecar({**driver, "command_history": [
            {**driver["command_history"][0], "result": observed}]}))

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
            bridge_dll = root / "bridge.dll"
            bridge_dll.write_bytes(b"\x00".join(
                step.encode("ascii")
                for step in g2_preview_operator.PRIVATE_LIFESTYLE_QUERY_STEPS
            ))
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
                "dll_sha256": hashlib.sha256(bridge_dll.read_bytes()).hexdigest(),
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
            outcomes = {"preflight": 0, "formal": 0}

            def fake_run(command, stdout_path, stderr_path, *, on_started=None):
                calls.append(command)
                stdout_path.write_text("{}\n", encoding="utf-8")
                stderr_path.write_text("", encoding="utf-8")
                if on_started is not None:
                    on_started(42137)
                return outcomes[
                    "preflight" if "native-one-generation-preflight" in command
                    else "formal"
                ]

            args = g2_preview_operator.parser().parse_args([
                "run", "--manifest", str(manifest_path),
                "--output", str(output),
            ])
            with mock.patch.object(
                g2_preview_operator, "run_logged", side_effect=fake_run
            ), mock.patch.object(
                g2_preview_operator, "live_run_state_root",
                return_value=root / "allocator",
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
                outcomes["preflight"] = 1
                blocked_args = g2_preview_operator.parser().parse_args([
                    "run", "--manifest", str(manifest_path),
                    "--output", str(root / "attempt-preflight-red"),
                ])
                blocked_result = g2_preview_operator.command_run(blocked_args)
                outcomes["preflight"] = 0
                outcomes["formal"] = 1
                red_args = g2_preview_operator.parser().parse_args([
                    "run", "--manifest", str(manifest_path),
                    "--output", str(root / "attempt-formal-red"),
                ])
                red_result = g2_preview_operator.command_run(red_args)

            self.assertEqual(result, 0)
            self.assertEqual(private_result, 0)
            self.assertEqual(family_result, 0)
            self.assertEqual(m5_result, 0)
            self.assertEqual(blocked_result, 1)
            self.assertEqual(red_result, 1)
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
            self.assertEqual(receipt["formal_runner_pid"], 42137)
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
            identities = []
            for attempt in (
                "attempt", "attempt-private", "attempt-family", "attempt-m5",
                "attempt-formal-red",
            ):
                identity_receipt = root / attempt / "live-run-identity.json"
                self.assertTrue(identity_receipt.is_file())
                payload = json.loads(identity_receipt.read_text(encoding="utf-8"))
                identities.append(payload["identities"][0])
            self.assertEqual(
                [row["sequence"] for row in identities], [1, 2, 3, 4, 5]
            )
            self.assertTrue(all(
                row["mod_key"] == "eternal-recurrence" for row in identities
            ))
            self.assertFalse(
                (root / "attempt-preflight-red" / "live-run-identity.json").exists()
            )
            namespace = (
                root / "allocator" / identities[0]["machine_id"]
                / "eternal-recurrence"
            )
            statuses = [
                json.loads(line)["status"]
                for line in (namespace / "statuses.jsonl").read_text(
                    encoding="utf-8"
                ).splitlines()
            ]
            self.assertEqual(
                statuses,
                ["launch-started", "completed-green"] * 4
                + ["launch-started", "completed-red"],
            )

    def test_live_run_state_root_requires_explicit_non_c_location(self) -> None:
        with mock.patch.dict(os.environ, {"XAR_CK3_LIVE_RUN_STATE_ROOT": ""}):
            with self.assertRaisesRegex(ValueError, "requires"):
                g2_preview_operator.live_run_state_root(None)
        if os.name == "nt":
            with self.assertRaisesRegex(ValueError, "non-C"):
                g2_preview_operator.live_run_state_root(
                    Path(r"C:\ck3-live-run-ids")
                )

    def test_private_lifestyle_dll_preflight_rejects_r0246_build_before_launch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dll = root / "bridge.dll"
            dll.write_bytes(b"native build without private LIFE dispatch")
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({
                "python": str(root / "python.exe"),
                "source_repo": str(root / "repo"),
                "state_dir": str(root / "state"),
                "game_dir": str(root / "game"),
                "pipe": r"\\.\pipe\life-preflight",
                "dll": str(dll),
                "dll_sha256": hashlib.sha256(dll.read_bytes()).hexdigest(),
                "injector": str(root / "injector.exe"),
            }), encoding="utf-8")
            verify_args = g2_preview_operator.parser().parse_args([
                "verify-private-lifestyle-dll", "--manifest", str(manifest),
            ])
            with self.assertRaisesRegex(
                ValueError, "XAR_CK3_ENABLE_G2_PLAYER_LIFESTYLE_FORMAL_WIRE_PRIVATE_V1=ON"
            ):
                g2_preview_operator.command_verify_private_lifestyle_dll(verify_args)
            run_args = g2_preview_operator.parser().parse_args([
                "run", "--manifest", str(manifest),
                "--output", str(root / "attempt"),
                "--private-lifestyle-formal-trial",
            ])
            with self.assertRaisesRegex(ValueError, "lacks native query dispatch keys"):
                g2_preview_operator.command_run(run_args)
            self.assertFalse((root / "attempt").exists())
            dll.write_bytes(b"\x00".join(
                step.encode("ascii")
                for step in g2_preview_operator.PRIVATE_LIFESTYLE_QUERY_STEPS
            ))
            record = json.loads(manifest.read_text(encoding="utf-8"))
            record["dll_sha256"] = hashlib.sha256(dll.read_bytes()).hexdigest()
            manifest.write_text(json.dumps(record), encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(
                    g2_preview_operator.command_verify_private_lifestyle_dll(verify_args), 0
                )
            receipt = json.loads(output.getvalue())
            self.assertTrue(receipt["ok"])
            self.assertFalse(receipt["game_launched"])
            self.assertEqual(receipt["dll_sha256"], record["dll_sha256"])
            dll.write_bytes(b"drift")
            with self.assertRaisesRegex(ValueError, "DLL hash mismatch"):
                g2_preview_operator.command_verify_private_lifestyle_dll(verify_args)

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

    def test_prisoner_collection_observation_is_default_off(self) -> None:
        base = dict(
            common=["python", "agent.py"], turns=1, timeout=60,
            readiness_timeout=30, private_faction_round_id_value=None,
        )
        flag = "--allow-private-prisoner-collection-observation"
        self.assertNotIn(flag, g2_preview_operator.native_auto_run_command(**base))
        self.assertIn(flag, g2_preview_operator.native_auto_run_command(
            **base, private_prisoner_collection_observation=True
        ))
        parsed = g2_preview_operator.parser().parse_args([
            "run", "--manifest", "manifest.json", "--output", "output",
            "--private-prisoner-collection-observation",
        ])
        self.assertTrue(parsed.private_prisoner_collection_observation)

    def test_private_sway_target_is_explicit_and_forwarded_to_agent(self) -> None:
        base = dict(
            common=["python", "agent.py"], turns=1, timeout=60,
            readiness_timeout=30, private_faction_round_id_value=None,
        )
        flag = "--private-active-scheme-sway-target"
        self.assertNotIn(flag, g2_preview_operator.native_auto_run_command(**base))
        command = g2_preview_operator.native_auto_run_command(
            **base, private_active_scheme_sway_target=32716,
        )
        self.assertEqual(command[-2:], [flag, "32716"])
        parsed = g2_preview_operator.parser().parse_args([
            "run", "--manifest", "manifest.json", "--output", "output",
            flag, "32716",
        ])
        self.assertEqual(parsed.private_active_scheme_sway_target, 32716)

    def test_private_sway_formal_trial_requires_opt_in_and_target(self) -> None:
        base = dict(
            common=["python", "agent.py"], turns=1, timeout=60,
            readiness_timeout=30, private_faction_round_id_value=None,
        )
        flag = "--private-active-scheme-sway-formal-trial"
        agent_flag = "--allow-private-active-scheme-sway-formal-trial"
        self.assertNotIn(agent_flag,
                         g2_preview_operator.native_auto_run_command(**base))
        command = g2_preview_operator.native_auto_run_command(
            **base, private_active_scheme_sway_target=32716,
            private_active_scheme_sway_formal_trial=True)
        self.assertIn(agent_flag, command)
        parsed = g2_preview_operator.parser().parse_args([
            "run", "--manifest", "manifest.json", "--output", "output",
            flag, "--private-active-scheme-sway-target", "32716",
        ])
        self.assertTrue(parsed.private_active_scheme_sway_formal_trial)
        self.assertEqual(parsed.private_active_scheme_sway_target, 32716)

    def test_private_realm_law_paused_query_is_explicit_and_forwarded(self) -> None:
        base = dict(
            common=["python", "agent.py"], turns=1, timeout=60,
            readiness_timeout=30, private_faction_round_id_value=None,
        )
        flag = "--private-realm-law-paused-query"
        self.assertNotIn(flag, g2_preview_operator.native_auto_run_command(**base))
        self.assertIn(flag, g2_preview_operator.native_auto_run_command(
            **base, private_realm_law_paused_query=True,
        ))
        parsed = g2_preview_operator.parser().parse_args([
            "run", "--manifest", "manifest.json", "--output", "output", flag,
        ])
        self.assertTrue(parsed.private_realm_law_paused_query)

    def test_private_activity_planner_diag_is_explicit_and_forwarded(self) -> None:
        base = dict(
            common=["python", "agent.py"], turns=1, timeout=60,
            readiness_timeout=30, private_faction_round_id_value=None,
        )
        flag = "--private-activity-planner-diag-query"
        self.assertNotIn(flag, g2_preview_operator.native_auto_run_command(**base))
        self.assertIn(flag, g2_preview_operator.native_auto_run_command(
            **base, private_activity_planner_diag_query=True,
        ))
        parsed = g2_preview_operator.parser().parse_args([
            "run", "--manifest", "manifest.json", "--output", "output", flag,
        ])
        self.assertTrue(parsed.private_activity_planner_diag_query)

    def test_private_feast_planner_open_is_explicit_and_forwarded(self) -> None:
        base = dict(
            common=["python", "agent.py"], turns=1, timeout=60,
            readiness_timeout=30, private_faction_round_id_value=None,
        )
        flag = "--private-activity-feast-planner-open"
        self.assertNotIn(flag, g2_preview_operator.native_auto_run_command(**base))
        self.assertIn(flag, g2_preview_operator.native_auto_run_command(
            **base, private_activity_feast_planner_open=True,
        ))
        parsed = g2_preview_operator.parser().parse_args([
            "run", "--manifest", "manifest.json", "--output", "output", flag,
        ])
        self.assertTrue(parsed.private_activity_feast_planner_open)

    def test_private_feast_stage1_option_read_is_explicit_and_forwarded(self) -> None:
        base = dict(
            common=["python", "agent.py"], turns=1, timeout=60,
            readiness_timeout=30, private_faction_round_id_value=None,
        )
        flag = "--private-activity-feast-stage1-option-read"
        self.assertNotIn(flag, g2_preview_operator.native_auto_run_command(**base))
        self.assertIn(flag, g2_preview_operator.native_auto_run_command(
            **base, private_activity_feast_stage1_option_read=True,
        ))
        parsed = g2_preview_operator.parser().parse_args([
            "run", "--manifest", "manifest.json", "--output", "output", flag,
        ])
        self.assertTrue(parsed.private_activity_feast_stage1_option_read)

    def test_private_feast_stage1_confirm_is_explicit_and_forwarded(self) -> None:
        base = dict(
            common=["python", "agent.py"], turns=1, timeout=60,
            readiness_timeout=30, private_faction_round_id_value=None,
        )
        flag = "--private-activity-feast-stage1-confirm"
        self.assertNotIn(flag, g2_preview_operator.native_auto_run_command(**base))
        self.assertIn(flag, g2_preview_operator.native_auto_run_command(
            **base, private_activity_feast_stage1_confirm=True,
        ))
        parsed = g2_preview_operator.parser().parse_args([
            "run", "--manifest", "manifest.json", "--output", "output", flag,
        ])
        self.assertTrue(parsed.private_activity_feast_stage1_confirm)

    def test_private_feast_stage2_gate_requires_confirm_and_forwards(self) -> None:
        base = dict(
            common=["python", "agent.py"], turns=1, timeout=60,
            readiness_timeout=30, private_faction_round_id_value=None,
        )
        flag = "--private-activity-feast-stage2-gate-read"
        self.assertNotIn(flag, g2_preview_operator.native_auto_run_command(**base))
        self.assertIn(flag, g2_preview_operator.native_auto_run_command(
            **base, private_activity_feast_stage1_confirm=True,
            private_activity_feast_stage2_gate_read=True,
        ))
        parsed = g2_preview_operator.parser().parse_args([
            "run", "--manifest", "manifest.json", "--output", "output",
            "--private-activity-feast-stage1-confirm", flag,
        ])
        self.assertTrue(parsed.private_activity_feast_stage1_confirm)
        self.assertTrue(parsed.private_activity_feast_stage2_gate_read)

    def test_private_activity_cost_slot12_raw_read_is_explicit_and_forwarded(self) -> None:
        base = dict(
            common=["python", "agent.py"], turns=1, timeout=60,
            readiness_timeout=30, private_faction_round_id_value=None,
        )
        flag = "--private-activity-cost-slot12-raw-read"
        self.assertNotIn(flag, g2_preview_operator.native_auto_run_command(**base))
        self.assertIn(flag, g2_preview_operator.native_auto_run_command(
            **base, private_activity_feast_planner_open=True,
            private_activity_cost_slot12_raw_read=True,
        ))
        parsed = g2_preview_operator.parser().parse_args([
            "run", "--manifest", "manifest.json", "--output", "output",
            "--private-activity-feast-planner-open", flag,
        ])
        self.assertTrue(parsed.private_activity_feast_planner_open)
        self.assertTrue(parsed.private_activity_cost_slot12_raw_read)

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
