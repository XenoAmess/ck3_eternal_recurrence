"""One synthetic completed-SAVE/cold projection; no Game or real file pair.

The existing full handoff, timeline, Close and native restore-row validators
are real. Process identities, material SAVE, driver cold flags and all native
frames are synthetic; this does not qualify a production restore consumer.
"""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from test_successor_ui_pending_ledger_v1 import SourceDriver, retain, run_ui, MACHINE, owner as validators
from xar_autoplayer import successor_ui_pending_ledger_v1 as journal
from xar_autoplayer import successor_ui_checkpoint_lineage_v1 as leaf
from xar_autoplayer.errors import AgentError
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.successor_ui_app_owner_v1 import SuccessorUIAppOwner


class CompletedCheckpointLineageTests(unittest.TestCase):
    def test_completed_pair_and_original_proofs_issue_only_a_native_owner_plan(self):
        with tempfile.TemporaryDirectory(prefix="m7-completed-lineage-") as temp:
            root = Path(temp)
            old = SourceDriver()
            ledger = retain(root, old)
            run_ui(old, ledger)
            old.event_finished()
            run_ui(old, ledger)
            original = ledger.path.read_bytes()
            intent_path = ledger._intent_path()
            original_intent = intent_path.read_bytes()
            saved_snapshot = deepcopy(old.frame)
            checkpoint = dict(status="saved", name="xar_checkpoint.ck3", strategy="native-autosave-command-v1",
                sha256="a" * 64, size=1024, date_raw=old.frame["date_raw"], history_index=9,
                episode_character_id=old.frame["episode_character_id"], episode_run_id=old.frame["episode_run_id"],
                succession_lifecycle=deepcopy(old.proof["succession_lifecycle"]))
            attempt = dict(pipe_name="synthetic-persisted-pipe", bridge_pid=ledger.game["pid"],
                episode_character_id=checkpoint["episode_character_id"], episode_run_id=checkpoint["episode_run_id"],
                succession_lifecycle=deepcopy(checkpoint["succession_lifecycle"]),
                campaign_goal=deepcopy(old.frame["campaign_goal"]))
            receipt = dict(scope="WRITE_REPLACE_RETURNED_NOT_FSYNC", status="replaced",
                write_replace_returned=True, save_binding_verified=True, checkpoint=deepcopy(checkpoint),
                attempt_binding=attempt, recorded_session_binding={key: attempt[key] for key in (
                    "pipe_name", "bridge_pid", "episode_character_id", "episode_run_id")},
                save_history_index=9, encoded_history_rows=9)
            save_result = dict(step="save-checkpoint", accepted=True, checkpoint=deepcopy(checkpoint),
                materialization={"available": True}, driver_state_replace_receipt=receipt)
            anchor = leaf.capture_completed_checkpoint_v1(ledger, save_result=save_result, snapshot=saved_snapshot)

            native = object.__new__(NativeHeadlessGameplayDriver)
            native._driver_state_lock = threading.RLock()
            native._last_checkpoint = deepcopy(checkpoint)
            native._command_history = [{"index": index} for index in range(1, 9)]
            native._command_history.append(dict(index=9, command="save-checkpoint", ok=True,
                result={key: deepcopy(value) for key, value in save_result.items()
                        if key != "driver_state_replace_receipt"}))
            native._command_history.append(dict(index=10, command="restore-checkpoint", ok=True,
                result=dict(step="restore-checkpoint", accepted=True, status="restored", backend_id="native-headless",
                    source="native-session-cold-start", checkpoint=deepcopy(checkpoint),
                    restored_date_raw=checkpoint["date_raw"], map_ready=True,
                    lifecycle={"previous_pid": ledger.game["pid"], "pid": 456})))
            native._driver_state_restored = True
            native._driver_state_restore_kind = "cold_checkpoint"
            native._episode_binding_state = "active_resumed"
            native._cold_candidate_rejection = native._pending_cold_candidate = native._driver_state_error = None
            native._session_bridge_pid = 456
            native._episode_character_id = checkpoint["episode_character_id"]
            native._episode_run_id = checkpoint["episode_run_id"]
            native._campaign_goal = deepcopy(old.frame["campaign_goal"])
            native._succession_lifecycle = deepcopy(checkpoint["succession_lifecycle"])
            native.pipe_name = attempt["pipe_name"]
            app = object.__new__(SuccessorUIAppOwner)
            app.driver, app.root, app.machine, app.epoch, app.validators = native, root, MACHINE, "f" * 64, validators
            app.service = SimpleNamespace(driver=native)
            app.service._successor_ui_app_owner_v1 = app
            app.lock = threading.RLock()
            cold_snapshot = deepcopy(saved_snapshot)
            cold_snapshot["diagnostics"].update(bridge_pid=456, connection_generation=1)
            cold_snapshot.update(snapshot_id="synthetic-new-Game:first-paused", revision=1, native_revision=2,
                                 succession_lifecycle=deepcopy(native._succession_lifecycle))
            executable = os.path.normcase(os.path.abspath("synthetic/ck3.exe"))
            def process(pid):
                if pid == 456:
                    return {"pid": 456, "creation_date": "synthetic-next-Game-birth", "executable": executable}
                return {"pid": pid, "creation_date": "synthetic-reused-old-pid-birth", "executable": executable}
            with patch("xar_autoplayer.runtime._process_identity", side_effect=process):
                native._successor_ui_cold_checkpoint_projection_v1 = leaf.capture_native_cold_projection_v1(native, snapshot=cold_snapshot)
                token = leaf.observe_native_cold_checkpoint_v1(app, snapshot=cold_snapshot, expected_executable=executable)
                plan = leaf.plan_resolved_checkpoint_retirement_v1(app, anchor=anchor, cold=token)
                self.assertIsInstance(plan, leaf.ResolvedCheckpointRetirementV1)
                self.assertIs(plan.owner, app)
                self.assertEqual(plan.ledger_sha256, hashlib.sha256(original).hexdigest())
                self.assertEqual(json.loads(plan.evidence)["new_source_epoch"], app.epoch)
                self.assertFalse(json.loads(plan.evidence)["action_replay_authorized"])
                self.assertEqual(ledger.path.read_bytes(), original)
                self.assertEqual(intent_path.read_bytes(), original_intent)
                with self.subTest("client JSON is not native authority"), self.assertRaises(TypeError):
                    leaf.plan_resolved_checkpoint_retirement_v1(app, anchor=anchor, cold=json.loads(token.body))
                with self.subTest("another owner cannot consume the token"), self.assertRaises(TypeError):
                    leaf.plan_resolved_checkpoint_retirement_v1(SimpleNamespace(**vars(app)), anchor=anchor, cold=token)
                for name, mutate in (
                    ("wrong checkpoint", lambda item: item["checkpoint"].update(sha256="b" * 64)),
                    ("wrong pipe", lambda item: item["driver_state_replace_receipt"]["attempt_binding"].update(pipe_name="foreign")),
                    ("unconfirmed driver write", lambda item: item["driver_state_replace_receipt"].update(status="unconfirmed")),
                    ("wrong old source", lambda item: item.update(source_epoch="0" * 64)),
                    ("wrong goal", lambda item: item["campaign_goal"].update(campaign_id="foreign")),
                ):
                    bad = deepcopy(anchor); mutate(bad)
                    with self.subTest(name), self.assertRaises(ValueError):
                        leaf.plan_resolved_checkpoint_retirement_v1(app, anchor=bad, cold=token)
                for status in ("pending", "handoff_unverified"):
                    bad = json.loads(original); bad["status"] = status
                    ledger.path.write_text(json.dumps(bad), encoding="utf-8")
                    with self.subTest(status), self.assertRaises(ValueError):
                        leaf.plan_resolved_checkpoint_retirement_v1(app, anchor=anchor, cold=token)
                    ledger.path.write_bytes(original)
                bad = json.loads(original)
                bad["verification"]["result"]["reconciliation"]["title_distribution_match"] = False
                bad["verification_sha256"] = journal.digest(bad["verification"])
                ledger.path.write_text(json.dumps(bad), encoding="utf-8")
                with self.subTest("original full title verifier remains required"), self.assertRaises((ValueError, AgentError)):
                    leaf.plan_resolved_checkpoint_retirement_v1(app, anchor=anchor, cold=token)
                ledger.path.write_bytes(original)
                bad = json.loads(original_intent); bad["status"] = "UNKNOWN"
                intent_path.write_text(json.dumps(bad), encoding="utf-8")
                with self.subTest("UNKNOWN Close"), self.assertRaises(ValueError):
                    leaf.plan_resolved_checkpoint_retirement_v1(app, anchor=anchor, cold=token)
                intent_path.write_bytes(original_intent)
                native._driver_state_restore_kind = "same_pid_hot"
                with self.subTest("SDK reconnect is not cold Game lineage"), self.assertRaises(ValueError):
                    leaf.observe_native_cold_checkpoint_v1(app, snapshot=cold_snapshot, expected_executable=executable)
                native._driver_state_restore_kind = "cold_checkpoint"
                native._last_checkpoint = {**checkpoint, "sha256": "b" * 64}
                with self.subTest("stale cold token"), self.assertRaises(ValueError):
                    leaf.plan_resolved_checkpoint_retirement_v1(app, anchor=anchor, cold=token)
                native._last_checkpoint = deepcopy(checkpoint)
            def old_still_alive(pid):
                return deepcopy(ledger.game) if pid == ledger.game["pid"] else process(pid)
            with patch("xar_autoplayer.runtime._process_identity", side_effect=old_still_alive):
                with self.subTest("old Game must exit"), self.assertRaises(ValueError):
                    leaf.plan_resolved_checkpoint_retirement_v1(app, anchor=anchor, cold=token)
            self.assertEqual(ledger.path.read_bytes(), original)
            self.assertEqual(intent_path.read_bytes(), original_intent)

    def test_old_birth_unknown_and_unobserved_absence_do_not_prove_exit(self):
        old = {"pid": 123, "creation_date": "synthetic-original-birth", "executable": "synthetic/ck3.exe"}
        for identity in ({"pid": 123}, {"pid": 123, "creation_date": ""},
                         {"pid": 123, "creation_date": None}, {"pid": 123, "creation_date": "None"},
                         {"pid": 999, "creation_date": "synthetic-other-birth"}):
            with self.subTest(identity), patch("xar_autoplayer.runtime._process_identity", return_value=identity), \
                    patch("xar_autoplayer.environment._toolhelp_process_entries") as enumerate_processes, \
                    self.assertRaisesRegex(ValueError, "unavailable"):
                leaf._observe_old_game_exit_v1(old)
            enumerate_processes.assert_not_called()
        with self.subTest("identity query failed"), \
                patch("xar_autoplayer.runtime._process_identity", side_effect=OSError("synthetic WMI query failed")), \
                self.assertRaisesRegex(ValueError, "unavailable"):
            leaf._observe_old_game_exit_v1(old)
        with patch("xar_autoplayer.runtime._process_identity", return_value=None):
            for entries in ([], [{"pid": 123}], [{"pid": None}]):
                with self.subTest(entries), patch("xar_autoplayer.environment._toolhelp_process_entries", return_value=entries), \
                        self.assertRaisesRegex(ValueError, "unavailable"):
                    leaf._observe_old_game_exit_v1(old)
            with self.subTest("enumeration failed"), \
                    patch("xar_autoplayer.environment._toolhelp_process_entries", side_effect=OSError("synthetic snapshot denied")), \
                    self.assertRaisesRegex(ValueError, "unavailable"):
                leaf._observe_old_game_exit_v1(old)
            with patch("xar_autoplayer.environment._toolhelp_process_entries", return_value=[{"pid": 456}]):
                if os.name == "nt":
                    proof = leaf._observe_old_game_exit_v1(old)
                    self.assertEqual(proof["status"], "old_pid_absent")
                    self.assertTrue(proof["complete_enumeration"])
                else:
                    with self.assertRaisesRegex(ValueError, "unavailable"):
                        leaf._observe_old_game_exit_v1(old)


if __name__ == "__main__":
    unittest.main()
