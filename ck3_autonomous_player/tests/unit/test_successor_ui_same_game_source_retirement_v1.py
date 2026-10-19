"""Synthetic same-Game SDK maintenance; no native read, SAVE or live proof."""
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

from test_successor_ui_pending_ledger_v1 import SourceDriver, retain, run_ui, identity, MACHINE, owner as validators
from xar_autoplayer import successor_ui_pending_ledger_v1 as journal
from xar_autoplayer import successor_ui_checkpoint_lineage_v1 as leaf
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.successor_ui_app_owner_v1 import SuccessorUIAppOwner


def completed_warm_fixture(root):
    old = SourceDriver()
    game = identity(old)
    game["executable"] = os.path.normcase(os.path.abspath(game["executable"]))
    with patch("test_successor_ui_pending_ledger_v1.identity", return_value=game):
        ledger = retain(root, old)
    run_ui(old, ledger)
    old.event_finished()
    run_ui(old, ledger)
    frame = deepcopy(old.frame)
    cp = dict(status="saved", name="xar_checkpoint.ck3", strategy="native-autosave-command-v1",
        sha256="a" * 64, size=1024, date_raw=frame["date_raw"], history_index=9,
        episode_character_id=frame["episode_character_id"], episode_run_id=frame["episode_run_id"],
        succession_lifecycle=deepcopy(old.proof["succession_lifecycle"]))
    attempt = dict(pipe_name="synthetic-warm-pipe", bridge_pid=ledger.game["pid"],
        episode_character_id=cp["episode_character_id"], episode_run_id=cp["episode_run_id"],
        succession_lifecycle=deepcopy(cp["succession_lifecycle"]), campaign_goal=deepcopy(frame["campaign_goal"]))
    receipt = dict(scope="WRITE_REPLACE_RETURNED_NOT_FSYNC", status="replaced",
        write_replace_returned=True, save_binding_verified=True, checkpoint=deepcopy(cp),
        attempt_binding=attempt, recorded_session_binding={k: attempt[k] for k in (
            "pipe_name", "bridge_pid", "episode_character_id", "episode_run_id")},
        save_history_index=9, encoded_history_rows=9)
    result = dict(step="save-checkpoint", accepted=True, checkpoint=deepcopy(cp),
        materialization={"available": True}, driver_state_replace_receipt=receipt)
    anchor = leaf.capture_completed_checkpoint_v1(ledger, save_result=result, snapshot=frame)
    native = object.__new__(NativeHeadlessGameplayDriver)
    native._driver_state_lock = threading.RLock()
    native._last_checkpoint = deepcopy(cp)
    native._driver_state_restored = True
    native._driver_state_restore_kind = "same_pid_hot"
    native._episode_binding_state = "active_resumed"
    native._cold_candidate_rejection = native._pending_cold_candidate = native._driver_state_error = None
    native._session_bridge_pid = ledger.game["pid"]
    native._episode_character_id = cp["episode_character_id"]
    native._episode_run_id = cp["episode_run_id"]
    native._campaign_goal = deepcopy(frame["campaign_goal"])
    native._succession_lifecycle = deepcopy(cp["succession_lifecycle"])
    native.pipe_name = attempt["pipe_name"]
    app = object.__new__(SuccessorUIAppOwner)
    app.driver, app.root, app.machine, app.epoch, app.validators = native, root, MACHINE, "f" * 64, validators
    app.service = SimpleNamespace(driver=native)
    app.service._successor_ui_app_owner_v1 = app
    app.lock = threading.RLock()
    frame.update(snapshot_id="synthetic-warm-next", revision=frame["revision"] + 20,
        native_revision=frame["native_revision"] + 20, date_raw=frame["date_raw"] + 24)
    frame["diagnostics"]["connection_generation"] += 1
    return app, ledger, anchor, frame


class SameGameSourceRetirementTests(unittest.TestCase):
    def test_actual_contract_archives_old_epoch_and_keeps_cold_gate(self):
        with tempfile.TemporaryDirectory(prefix="m7-warm-source-") as temp:
            app, ledger, anchor, frame = completed_warm_fixture(Path(temp))
            original = ledger.path.read_bytes()
            intent = ledger._intent_path().read_bytes()
            def plan(item=anchor, snapshot=frame):
                return leaf.plan_resolved_same_game_source_retirement_v1(app, anchor=item,
                    snapshot=snapshot, expected_executable=ledger.game["executable"])
            with patch("xar_autoplayer.runtime._process_identity", return_value=deepcopy(ledger.game)):
                good = plan()
                self.assertEqual(json.loads(good.evidence)["kind"], "same_game_resolved_source_update")
                self.assertFalse(json.loads(good.evidence)["cold_game_credit"])
                self.assertEqual(good.ledger_sha256, hashlib.sha256(original).hexdigest())
                with self.assertRaises(TypeError):
                    leaf.observe_native_cold_checkpoint_v1(app, snapshot=frame,
                        expected_executable=ledger.game["executable"])
                for field, bad in (("_driver_state_restore_kind", "cold_checkpoint"),
                        ("_driver_state_restored", False), ("_driver_state_error", "unavailable"),
                        ("_last_checkpoint", {**app.driver._last_checkpoint, "sha256": "b" * 64})):
                    actual = getattr(app.driver, field)
                    setattr(app.driver, field, bad)
                    with self.subTest(field), self.assertRaises(ValueError):
                        plan()
                    setattr(app.driver, field, actual)
                for name, mutate in (
                    ("same epoch", lambda x: x.update(source_epoch=app.epoch)),
                    ("foreign birth", lambda x: x["game_identity"].update(creation_date="foreign")),
                    ("different SAVE", lambda x: x["checkpoint"].update(sha256="b" * 64)),
                    ("unconfirmed receipt", lambda x: x["driver_state_replace_receipt"].update(status="unknown")),
                ):
                    bad = deepcopy(anchor); mutate(bad)
                    with self.subTest(name), self.assertRaises(ValueError):
                        plan(bad)
                stale = deepcopy(frame); stale["date_raw"] = anchor["checkpoint"]["date_raw"] - 1
                with self.assertRaises(ValueError):
                    plan(snapshot=stale)
                for status in ("pending", "handoff_unverified"):
                    bad = json.loads(original); bad["status"] = status
                    ledger.path.write_text(json.dumps(bad), encoding="utf-8")
                    with self.subTest(status), self.assertRaises(ValueError):
                        plan()
                    ledger.path.write_bytes(original)
                intent_path = ledger._intent_path()
                bad = json.loads(intent); bad["status"] = "UNKNOWN"
                intent_path.write_text(json.dumps(bad), encoding="utf-8")
                with self.assertRaises(ValueError):
                    plan()
                intent_path.write_bytes(intent)
                self.assertEqual(ledger.path.read_bytes(), original)
                retired = leaf.retire_completed_checkpoint_v1(app, good)
                self.assertFalse(ledger.path.exists())
                self.assertEqual(Path(retired["archive"]).read_bytes(), original)
                self.assertEqual(intent_path.read_bytes(), intent)
                fresh = journal.SuccessorUIPendingLedger(app.root, machine_id=app.machine,
                    source_epoch=app.epoch, game_identity=ledger.game,
                    verify_transition=validators._verify_natural_succession_transition,
                    close_validator=validators._ordinary_succession_close_issue,
                    timeline_classifier=validators._ordinary_succession_timeline_state)
                self.assertEqual(fresh.epoch, app.epoch)
                self.assertNotEqual(fresh.epoch, ledger.epoch)


if __name__ == "__main__":
    unittest.main()
