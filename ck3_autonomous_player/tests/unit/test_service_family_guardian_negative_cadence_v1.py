"""Candidate Service guardian branch: exact source-bound query replay."""
import copy
import unittest
import json
import os
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,os.environ.get('XAR_TEST_SDK_ROOT',str(HERE.parents[1]/'src')))
import xar_autoplayer.bridge as bridge
if os.environ.get('XAR_TEST_BRIDGE_OVERLAY'):
    bridge.__path__.insert(0,os.environ['XAR_TEST_BRIDGE_OVERLAY'])
FIXTURE={int(row['source_ref'].split('AUTO')[1]):row for row in
    json.loads((HERE.parent/'fixtures/family_guardian_p43_completed_projection_v1.json').read_text(encoding='utf-8'))['rows']}
from xar_autoplayer.bridge.service import GameplayBridgeService

def sample(seq):
    row=FIXTURE[seq]
    return {'planning_source_frame':row['planning_source_frame'],
            'plan':{'family_marriage_current_relationship':row['family_marriage_current_relationship'],
                    'family_education_observations':row['family_education_observations']}}

def snapshot_for(frame, original):
    exe = original["default_query"]["character_interaction_ordinary_context"]["executable_sha256"]
    return {"revision": frame["revision"], "snapshot_id": frame["snapshot_id"],
            "native_revision": frame["native_revision"], "date_raw": frame["date_raw"],
            "episode_run_id": frame["episode_run_id"], "paused": True,
            "map_ready": True, "active_wars": [], "active_event": None,
            "pending_character_interaction": None, "one_life_terminal_reason": None,
            "played_character": {"character_id": frame["actor_character_id"],
                                 "alive": True, "stress_points": None},
            "diagnostics": {"connected": True,
                "connection_generation": frame["connection_generation"],
                "hello": {"pid": frame["bridge_pid"],
                          "expected_ck3_version": "1.20.0.4",
                          "expected_ck3_sha256": exe,
                          "ck3_build_match": True,
                          "game_adapter_id": "ck3-1.20.0.4-msvc-x64"}}}


class Driver:
    def query_character_interaction_ordinary_v1(self, *args, **kwargs):
        raise AssertionError("Service test must use the captured public query seam")

    def initiate_character_interaction_ordinary_v1(self, *args, **kwargs):
        raise AssertionError("A negative query must never submit")


class ServiceCadence(unittest.TestCase):
    def test_actual_two_dates_and_same_frame_duplicate_then_defer(self):
        service = GameplayBridgeService.__new__(GameplayBridgeService)
        service.driver = Driver()
        service._plan_private_family_child_focus_v1 = lambda planned, snapshot, needs: planned
        counts = []
        for seq in (555, 555, 559, 578):
            body = sample(seq)
            frame = body["planning_source_frame"]
            original = body["plan"]["family_education_observations"][0]
            service._observed_planning_source_frame = lambda snapshot, current=frame: current
            calls = []
            def query(interaction, child, **kwargs):
                calls.append((interaction, child, kwargs))
                captured = (original["request_attempts"][0]["query"]
                            if kwargs.get("child_full_id") is not None else original["default_query"])
                return copy.deepcopy(captured)
            service.query_character_interaction_ordinary_v1 = query
            relationship = body["plan"]["family_marriage_current_relationship"]
            planned = {"revision": frame["revision"], "plan": {
                "selected_step": "life-advance", "family_marriage_current_relationship": relationship}}
            snapshot = snapshot_for(frame, original)
            result = service._plan_private_family_education_v1(planned, snapshot, relationship=relationship)
            self.assertEqual(result["plan"]["selected_step"], "life-advance")
            counts.append(len(calls))
        self.assertEqual(counts, [2, 0, 2, 0])

    def test_war_or_modal_invalidates_defer_and_reads_again(self):
        service = GameplayBridgeService.__new__(GameplayBridgeService)
        service.driver = Driver()
        service._plan_private_family_child_focus_v1 = lambda planned, snapshot, needs: planned
        base = sample(555)
        frame = base["planning_source_frame"]
        original = base["plan"]["family_education_observations"][0]
        service._observed_planning_source_frame = lambda snapshot: frame
        calls = []
        service.query_character_interaction_ordinary_v1 = lambda *a, **k: (
            calls.append((a,k)) or copy.deepcopy(original["request_attempts"][0]["query"]
                if k.get("child_full_id") is not None else original["default_query"]))
        relationship = base["plan"]["family_marriage_current_relationship"]
        planned = {"revision": frame["revision"], "plan": {"selected_step": "life-advance"}}
        quiet = snapshot_for(frame, original)
        service._plan_private_family_education_v1(planned, quiet, relationship=relationship)
        for field, value in (("active_wars", [{"war_id": 1}]),
                             ("active_event", {"event_id": 1}),
                             ("pending_character_interaction", {"interaction_id": 1}),
                             ("paused", False)):
            before = len(calls)
            try:
                service._plan_private_family_education_v1(
                    planned, {**quiet, field: value}, relationship=relationship)
            except ValueError:
                # The captured query belongs to the old quiet frame; a changed
                # modal or pause state must reject that reply after rereading.
                pass
            self.assertGreater(len(calls), before, field)


if __name__ == "__main__":
    unittest.main()
