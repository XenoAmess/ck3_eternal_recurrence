"""An ongoing enemy battle defers a stationary pursuit by one exact native day."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).parents[2] / "src"))
from xar_autoplayer.bridge.battle_reader_watch_v1 import CLOCK_CAPABILITIES

# Normal repository runs import its installed source. External candidate runs
# can supply a separate source file without editing the worktree.
candidate = os.environ.get("XAR_STRATEGY_UNDER_TEST")
if candidate:
    spec = importlib.util.spec_from_file_location(
        "xar_autoplayer._enemy_combat_watch_candidate", candidate)
    strategy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(strategy)
else:
    from xar_autoplayer import strategy

FIXTURE = Path(__file__).parents[1] / "fixtures/p27_enemy_already_combat_actual_projection.json"
STEPS = {"life-advance-one-day", "set-speed-1", "resume-map", "pause-map"}


class EnemyAlreadyCombatOneDayWatchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.actual = json.loads(FIXTURE.read_text(encoding="utf-8"))
        cls.snapshot = cls.actual["snapshot"]
        cls.baseline = cls.actual["baseline"]
        cls.subject_id, cls.target_id = strategy.parse_move_army_step(
            cls.baseline["selected_step"])
        cls.enemy_id = cls.actual["blocked_defender_army_ids"][0]
        assert cls.actual["blocked_phase"] == "native_war_active_combat_resume_unavailable"
        assert cls.actual["blocked_subject_army_id"] is None
        assert cls.actual["native_clock_capabilities_present"] is True
        source = cls.actual["planning_source_frame"]
        for key in ("snapshot_id", "revision", "native_revision", "date_raw"):
            assert cls.snapshot[key] == source[key]
        assert cls.snapshot["played_character"]["character_id"] == source["actor_character_id"]
        assert next(a for a in cls.snapshot["player_armies"] if a["army_id"] == cls.subject_id)["current_province_id"] != cls.target_id
        assert any(e["army_id"] == cls.enemy_id and e["current_province_id"] == cls.target_id and e["in_combat"] is True
                   for w in cls.snapshot["active_wars"] for e in w["enemy_armies"])

    def plan(self, snapshot=None, *, steps=STEPS, caps=CLOCK_CAPABILITIES):
        return strategy._general_battle_forecast_ingress(
            self.baseline, commands=[], snapshot=snapshot or self.snapshot,
            action_steps=set(steps), bridge_capabilities=set(caps))

    def test_actual_same_frame_replay_and_final_wrappers(self):
        result = self.plan()
        self.assertEqual(result["phase"], "native_war_enemy_ongoing_combat_one_day_observation")
        self.assertEqual(result["selected_step"], "life-advance-one-day")
        self.assertEqual(result["subject_army_id"], self.subject_id)
        self.assertEqual(result["active_combat_defender_army_ids"], [self.enemy_id])
        for key in ("contact_free_proven", "offensive_combat_permission", "battle_outcome_inferred", "war_or_material_credit"):
            self.assertIs(result[key], False)
        wrapped = strategy._annotate_active_combat_resume_input(result, self.snapshot)
        wrapped = strategy._h3937_hold_selected_control(wrapped, self.snapshot)
        self.assertEqual(wrapped["selected_step"], "life-advance-one-day")
        # Exercise the public chooser's actual ingress and final wrappers. The
        # retained failed plan supplies only the pre-ingress baseline; the two
        # generation-specific SDK28 wrapper names are not public dependencies.
        with patch.object(strategy, "_choose_one_life_turn_core", return_value=self.baseline):
            chosen = strategy.choose_one_life_turn(
                [], snapshot=self.snapshot, action_steps=STEPS,
                bridge_capabilities=CLOCK_CAPABILITIES)
        self.assertEqual(chosen["selected_step"], "life-advance-one-day")
        self.assertEqual(chosen["phase"], result["phase"])

    def test_fourteen_guard_negatives(self):
        def own(snapshot):
            return next(a for a in snapshot["player_armies"] if a["army_id"] == self.subject_id)
        def enemy(snapshot):
            return next(e for w in snapshot["active_wars"] for e in w["enemy_armies"] if e["army_id"] == self.enemy_id)
        changes = {
            "own_combat": lambda s: own(s).update(in_combat=True, army_state="combat"),
            "own_retreat": lambda s: own(s).update(retreating=True),
            "incoming_route": lambda s: own(s).update(route_province_ids=[self.target_id], route_read_status="complete_nonempty", move_target_province_id=self.target_id),
            "own_at_target": lambda s: own(s).update(current_province_id=self.target_id),
            "wrong_owner": lambda s: own(s).update(owner_character_id=-1),
            "unpaused": lambda s: s.update(paused=False),
            "map_unready": lambda s: s.update(map_ready=False),
            "actor_dead": lambda s: s["played_character"].update(alive=False),
            "active_event": lambda s: s.update(active_event={"instance_id": 1}),
            "pending_interaction": lambda s: s.update(pending_character_interaction={"instance_id": 1}),
            "exclusive_modal": lambda s: s.update(top_exclusive_modal_choice_hint={"status": "present"}),
            "enemy_no_combat": lambda s: enemy(s).update(in_combat=False, army_state="moving"),
        }
        for name, change in changes.items():
            with self.subTest(name=name):
                frame = deepcopy(self.snapshot)
                change(frame)
                result = self.plan(frame)
                self.assertNotEqual(result.get("phase"), "native_war_enemy_ongoing_combat_one_day_observation")
                self.assertNotEqual(result.get("selected_step"), "life-advance-one-day")
        with self.subTest(name="missing_native_clock_capability"):
            result = self.plan(caps=set(CLOCK_CAPABILITIES) - {next(iter(CLOCK_CAPABILITIES))})
            self.assertNotEqual(result.get("selected_step"), "life-advance-one-day")
        with self.subTest(name="missing_one_day_step"):
            result = self.plan(steps=STEPS - {"life-advance-one-day"})
            self.assertNotEqual(result.get("selected_step"), "life-advance-one-day")


if __name__ == "__main__":
    unittest.main()
