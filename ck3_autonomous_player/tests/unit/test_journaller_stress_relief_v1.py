"""Synthetic adapter/real Driver guard composition; no game, pipe or desktop."""
from copy import deepcopy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from xar_autoplayer import journaller_stress_relief_v1 as j
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver as Driver
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.bridge.ingame_decisions_open_contract import opening_binding
from xar_autoplayer.bridge.event_window_context_contract import _EVENT_PROVENANCE_BY_BACKEND
from test_turn_bundle_v1 import _snapshot, _root
from test_ingame_decision_item_actions import frame, model, ack
from test_ingame_decisions_open_contract import pending_native_ack
from test_event_window_context_v1_bridge import _frame


def fixture():
    snapshot, root = _snapshot(), _root()
    snapshot.update(map_ready=True, speed=3, episode_run_id="synthetic-journaller-episode")
    snapshot["diagnostics"] = frame()["diagnostics"]
    snapshot["diagnostics"].update(bridge_pid=12700)
    snapshot["diagnostics"]["hello"].update(
        game_adapter_id="ck3-1.20.0.4-msvc-x64", expected_ck3_version="1.20.0.4",
        expected_ck3_sha256=CK3_12004.executable_sha256)
    root.update(queried_snapshot_id=snapshot["snapshot_id"], queried_revision=snapshot["revision"],
                queried_native_revision=snapshot["native_revision"])
    return snapshot, root


def build4(value):
    value.update(game_version="1.20.0.4", executable_sha256=CK3_12004.executable_sha256)
    return value


class SyntheticDriver:
    open_ingame_decisions_v1 = Driver.open_ingame_decisions_v1
    select_ingame_decision_item_v1 = Driver.select_ingame_decision_item_v1
    _decision_item_action_v1 = Driver._decision_item_action_v1
    confirm_ingame_decision_outcome_v1 = Driver.confirm_ingame_decision_outcome_v1

    def __init__(self, directory):
        self.frame, self.root = fixture()
        self.directory = Path(directory)
        self.allow_private_journaller_stress_relief_v1 = True
        self.caps = set(j.REQUIRED_CAPS)
        self.calls = []; self.selected = False; self.available = True
        self.fail = None; self.model_mutation = None; self.event_mutation = None

    def take_snapshot(self): return deepcopy(self.frame)
    def take_snapshot_without_native_command_history(self): return self.take_snapshot()
    def capabilities(self):
        return {"bridge_capabilities": sorted(self.caps), "action_steps":
                ["select-event-option-1"] if self.frame["active_event"] else []}
    def _native_driver_state_path(self): return self.directory / "driver-state.json"
    def _record_command(self, *args, **kwargs): pass

    def query_ingame_decision_item_v1(self, key, **kwargs):
        result = build4(model(opening_binding(self.frame), selected=self.selected))
        result.update(decision_key=key, detail_decision_key=key if self.selected else "",
                      row_context_reference_key=self.frame["played_character"]["character_id"],
                      detail_actor_reference_key=self.frame["played_character"]["character_id"] if self.selected else -1)
        if not self.available:
            result = build4(dict(schema="ck3-ingame-decision-item-v1", step="query-ingame-decision-item-v1",
                read_only=True, available=False, row_widget_datacontext_verified=False,
                action_qualified=False, unavailable_reason="actual_row_absent"))
        if self.model_mutation: self.model_mutation(result)
        return result

    def inspect_gui_window_tree_v1(self, kind):
        return {"scope_root_name": "decisions_view", "root_available": True, "truncated": False,
                "widgets": [{"child_path": "", "runtime_name": "decisions_view", "effective_visible": True}]}

    def _execute_primitive_step(self, step, **kwargs):
        self.calls.append(step)
        if self.fail == step: raise TimeoutError("synthetic missing ACK")
        binding = opening_binding(self.frame)
        if step == "activate-ingame-decisions-v1":
            result = build4(pending_native_ack())
            result.update({key: binding[key] for key in (
                "native_revision", "connection_generation", "game_pid", "played_character_id", "date_raw")})
            return result
        result = build4(ack(binding, "select" if step == "select-ingame-decision-item-v1" else "confirm"))
        result.update(decision_key=j.DECISION, before_actual_model=self.query_ingame_decision_item_v1(j.DECISION))
        if step == "select-ingame-decision-item-v1":
            self.selected = True
        else:
            result.update(schema="ck3-ingame-decision-outcome-confirm-v1", step=step,
                action="confirm_outcome", expected_outcome="event_window",
                expected_event_definition_key=j.EVENT, no_blocking_modal_verified=True, native_call_completed=True)
            self.frame.update(revision=self.frame["revision"] + 1,
                native_revision=self.frame["native_revision"] + 1, snapshot_id="synthetic-journal-event",
                active_event={"instance_id": 200, "option_count": 1})
        return result

    def query_current_event_window_context_v1(self, instance, **kwargs):
        context = _frame()
        context.update(snapshot_revision=self.frame["native_revision"], date_raw=self.frame["date_raw"],
            current_event_instance_id=instance, event_definition_key=j.EVENT, saved_scopes=[],
            root_scope={"status": "available", "raw_type_index": 4, "type_key": "character", "subtype": 0,
                "typed_identity": {"status": "available", "kind": "character",
                                   "character_id": self.frame["played_character"]["character_id"]}},
            provenance=deepcopy(_EVENT_PROVENANCE_BY_BACKEND["ck3-1.20.0.4-native-event-window-v1"]))
        context["options"][0].update(native_option_index=0, shown=True, enabled=True,
            fallback=False, cancel=False, unavailable_reason="")
        context["options"][0]["effect_indicators"].update(
            coverage="played-character-event-icon-indicators-1.20.0.4-v1", rows=[])
        if self.event_mutation: self.event_mutation(context)
        return {"current_event_window_context": context, "current_event_window_context_ready": True,
                "queried_revision": self.frame["revision"], "queried_native_revision": self.frame["native_revision"]}


class JournallerTests(unittest.TestCase):
    def start(self, driver, hook=lambda row: None):
        # Synthetic seam, never installed-source/game qualification.
        with patch.object(j, "verify_journaller_sources_v1", return_value=dict(j.SOURCE_PINS)):
            return j.start_journaller_stress_relief_v1(driver,
                expected_revision=driver.frame["revision"], campaign_root_result=driver.root,
                game_source_root=Path("synthetic-source-unused"), before_action=hook)

    def test_disabled_is_pure(self):
        class Forbidden:
            def __getattr__(self, key):
                if key == j.FLAG: raise AttributeError(key)
                raise AssertionError("disabled route touched " + key)
        for driver in (Forbidden(), type("NumericFlag", (), {j.FLAG: 1})()):
            result = j.start_journaller_stress_relief_v1(driver, expected_revision=1,
                campaign_root_result=None, game_source_root=None, before_action=None)
            self.assertEqual(result["status"], "disabled")

    def test_current_stress_and_decision_gate(self):
        for mode in ("low", "missing", "stale_root", "event", "incoming", "capability"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                d = SyntheticDriver(directory)
                if mode == "low": d.frame["played_character"]["stress_points"] = 99
                if mode == "missing": d.frame["played_character"].pop("stress_points")
                if mode == "stale_root": d.root["queried_native_revision"] += 1
                if mode == "event": d.frame["active_event"] = {"instance_id": 3}
                if mode == "incoming": d.frame["pending_character_interaction"] = {}
                if mode == "capability": d.caps.remove("game.command.confirm-ingame-decision-outcome-v1")
                self.assertNotEqual(self.start(d)["status"], "exact_event_observed_choice_pending")
                self.assertEqual(d.calls, [])

    def test_absent_native_model(self):
        with tempfile.TemporaryDirectory() as directory:
            d = SyntheticDriver(directory); d.available = False
            self.assertEqual(self.start(d)["status"], "no_qualified_native_journaller_model")
            self.assertEqual(d.calls, ["activate-ingame-decisions-v1"])
            self.assertFalse((Path(directory) / "journaller-stress-relief-v1").exists())

    def test_guarded_handoff_and_actor_claim(self):
        with tempfile.TemporaryDirectory() as directory:
            d = SyntheticDriver(directory); shown = []
            handoff = self.start(d, shown.append)
            self.assertEqual(handoff["status"], "exact_event_observed_choice_pending")
            self.assertEqual(handoff["event_plan"]["selected_native_option_index"], 0)
            self.assertEqual(len(d.calls), 3)
            self.assertEqual(len(shown), 3)
            self.assertFalse(handoff["event_choice_verified"])
            self.assertFalse(handoff["health_treatment_credit"])
            d.frame.update(active_event=None, revision=d.frame["revision"] + 1)
            d.frame["diagnostics"]["hello"]["pid"] += 1
            self.assertEqual(self.start(d)["status"], "same_frame_stress_unavailable")
            # Synthetic current risk: actor claim still blocks a changed PID.
            with patch.object(j, "build_ordinary_player_risk_context_v1", return_value={
                    "stress": {"status": "available", "value": {"points": 120}}}):
                self.assertEqual(self.start(d)["status"], "actor_attempt_already_claimed_no_replay")
            self.assertEqual(len(d.calls), 3)

    def test_unknown_result_never_replays(self):
        for stage in ("activate-ingame-decisions-v1", "select-ingame-decision-item-v1",
                      "confirm-ingame-decision-outcome-v1"):
            with self.subTest(stage=stage), tempfile.TemporaryDirectory() as directory:
                d = SyntheticDriver(directory); d.fail = stage
                with self.assertRaises(TimeoutError): self.start(d)
                count = len(d.calls)
                d.fail = None
                try: self.start(d)
                except Exception: pass
                self.assertEqual(len(d.calls), count)

    def test_actual_option_projection(self):
        for field, wrong in (("native_option_index", 1), ("rendered_index", 1), ("enabled", False)):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                d = SyntheticDriver(directory)
                d.event_mutation = lambda row: row["options"][0].update({field: wrong})
                with self.assertRaises((ValueError, BridgeUnavailableError)): self.start(d)
                self.assertEqual(len(d.calls), 3)

    def outcome(self, d, handoff, ending=84):
        before = handoff["event_plan"]["binding"]
        d.frame.update(revision=d.frame["revision"] + 1,
            native_revision=d.frame["native_revision"] + 1,
            snapshot_id="synthetic-after-journal-choice", active_event=None)
        d.frame["played_character"]["stress_points"] = ending
        actor = d.frame["played_character"]["character_id"]
        receipt = {"accepted": True, "event_selection": {
            "status": "event_instance_advanced", "postcondition_verified": True,
            "old_event_instance_id": 200, "new_event_instance_id": None,
            "selected_option_number": 1, "selected_native_option_index": 0,
            "starting_snapshot_id": before["snapshot_id"], "starting_revision": before["revision"],
            "ending_snapshot_id": d.frame["snapshot_id"], "ending_revision": d.frame["revision"],
            "episode_run_id": before["episode_run_id"], "connection_generation": before["connection_generation"],
            "bridge_pid": before["bridge_pid"],
            "starting_played_character_stress": {"status": "available", "character_id": actor, "stress_points": 120},
            "ending_played_character_stress": {"status": "available", "character_id": actor, "stress_points": ending}}}
        return receipt

    def test_variable_stress_interval(self):
        for points in (0, 84, 120, 130):
            with self.subTest(points=points), tempfile.TemporaryDirectory() as directory:
                d = SyntheticDriver(directory); h = self.start(d); r = self.outcome(d, h, points)
                observed = j.observe_journaller_choice_v1(h, r, d.frame)
                self.assertTrue(observed["old_event_window_absent"])
                self.assertEqual(observed["stress_delta_points"], points - 120)
                self.assertIs(observed["stress_reduction_observed"], points < 120)
                self.assertFalse(observed["health_treatment_credit"])

    def test_missing_stress_keeps_window_credit(self):
        with tempfile.TemporaryDirectory() as directory:
            d = SyntheticDriver(directory); h = self.start(d); r = self.outcome(d, h)
            r["event_selection"].pop("ending_played_character_stress")
            observed = j.observe_journaller_choice_v1(h, r, d.frame)
            self.assertTrue(observed["old_event_window_absent"])
            self.assertFalse(observed["stress_change_observed"])
            self.assertIsNone(observed["stress_reduction_observed"])

    def test_ack_cannot_replace_bound_postcondition(self):
        for field, wrong in (("postcondition_verified", False), ("old_event_instance_id", 201),
                ("selected_native_option_index", 1), ("connection_generation", 99),
                ("ending_revision", 10000), ("episode_run_id", "foreign")):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                d = SyntheticDriver(directory); h = self.start(d); r = self.outcome(d, h)
                r["event_selection"][field] = wrong
                result = j.observe_journaller_choice_v1(h, r, d.frame)
                self.assertTrue(result["selection_acknowledged"])
                self.assertFalse(result["old_event_window_absent"])
                self.assertFalse(result["stress_change_observed"])


if __name__ == "__main__": unittest.main()
