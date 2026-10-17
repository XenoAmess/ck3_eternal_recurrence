"""Portable ordinary-planner replay of retained P39 SEM56 and AUTO55 evidence.

Run against the intended xar_autoplayer source tree on PYTHONPATH. The fixture
contains only actual completed response projections. This test submits no game
command and grants no in-game date credit.
"""
from __future__ import annotations

import copy
import gzip
import json
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from xar_autoplayer import strategy


FIXTURE = Path(__file__).parent / "fixtures" / "portable_actual56_ordinary_projection.json.gz"


def _actual_projection() -> dict:
    with gzip.open(FIXTURE, "rt", encoding="utf-8") as stream:
        value = json.load(stream)
    assert value["schema"] == "xar.p39.retreating-only-ordinary-projection/v1"
    assert value["source_kind"] == "actual_completed_response_projection"
    assert len(value["command_rows"]) == 17
    return value


class RetreatingOnlyCommittedRoutePortableTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.evidence = _actual_projection()

    def _ordinary_plan(self):
        evidence = self.evidence
        return strategy.choose_one_life_turn(
            evidence["command_rows"], snapshot=evidence["snapshot"],
            action_steps=evidence["action_steps"],
            bridge_capabilities=evidence["bridge_capabilities"],
        )

    def test_actual_old_block_and_new_existing_one_day(self):
        self.assertEqual(
            self.evidence["old_blocked_plan"]["phase"],
            "native_war_active_route_contact_horizon_unsupported",
        )
        self.assertIsNone(self.evidence["old_blocked_plan"]["selected_step"])
        with patch.object(strategy, "_retreating_only_committed_route_one_day_plan", return_value=None):
            old = self._ordinary_plan()
        self.assertEqual(old["phase"], "native_war_active_route_contact_horizon_unsupported")
        self.assertIsNone(old["selected_step"])
        new = self._ordinary_plan()
        self.assertEqual(new["phase"], "native_war_retreating_only_committed_route_one_day_observation")
        self.assertEqual(new["selected_step"], "life-advance-one-day")
        self.assertEqual(new["max_observation_days"], 1)
        self.assertIs(new["contact_free_proven"], False)
        self.assertIs(new["movement_resubmitted"], False)
        self.assertIs(new["offensive_combat_permission"], False)
        self.assertEqual(new["retreating_enemy_army_ids"], [33554495])

    def test_guarded_helper_rejects_twenty_one_counterexamples(self):
        evidence = self.evidence
        snapshot = evidence["snapshot"]
        army = snapshot["player_armies"][0]
        blocked = evidence["old_blocked_plan"]
        base = {
            "audit": blocked["route_audit"],
            "move_intent": blocked["move_intent"],
            "hostile_army_ids": (),
            "available_steps": {"life-advance-one-day"},
            "war_summary": blocked["active_wars"],
        }
        check = strategy._retreating_only_committed_route_one_day_plan
        self.assertEqual(check(snapshot, army, **base)["selected_step"], "life-advance-one-day")
        cases = [
            ("enemy_not_retreating", lambda s, a, k: s["active_wars"][0]["enemy_armies"][0].update(retreating=False)),
            ("enemy_retreat_unknown", lambda s, a, k: s["active_wars"][0]["enemy_armies"][0].update(retreating=None)),
            ("enemy_in_combat", lambda s, a, k: s["active_wars"][0]["enemy_armies"][0].update(in_combat=True)),
            ("no_observed_enemy", lambda s, a, k: s["active_wars"][0].update(enemy_armies=[])),
            ("enemy_id_missing", lambda s, a, k: s["active_wars"][0]["enemy_armies"][0].update(army_id=None)),
            ("owner_changed", lambda s, a, k: a.update(owner_character_id=999)),
            ("actor_dead", lambda s, a, k: s["played_character"].update(alive=False)),
            ("modal_present", lambda s, a, k: s.update(top_exclusive_modal_choice_hint={"status": "present"})),
            ("event_present", lambda s, a, k: s.update(active_event={"instance_id": 70})),
            ("unpaused", lambda s, a, k: s.update(paused=False)),
            ("map_unready", lambda s, a, k: s.update(map_ready=False)),
            ("no_horizon_capability", lambda s, a, k: s.update(route_contact_horizon_supported=False)),
            ("second_player_army", lambda s, a, k: s["player_armies"].append({"army_id": 123})),
            ("subject_in_combat", lambda s, a, k: a.update(in_combat=True)),
            ("subject_retreating", lambda s, a, k: a.update(retreating=True)),
            ("route_incomplete", lambda s, a, k: a.update(route_read_status="partial")),
            ("route_target_differs", lambda s, a, k: a.update(move_target_province_id=999)),
            ("unsafe_route", lambda s, a, k: k["audit"].update(status="unsafe")),
            ("no_active_intent", lambda s, a, k: k["move_intent"].update(status="unknown")),
            ("unknown_nonretreat_hostile_scope", lambda s, a, k: k.update(hostile_army_ids=(33554495,))),
            ("no_exact_one_day_step", lambda s, a, k: k.update(available_steps={"life-advance"})),
        ]
        self.assertEqual(len(cases), 21)
        for name, mutate in cases:
            with self.subTest(name=name):
                current_snapshot = copy.deepcopy(snapshot)
                current_army = current_snapshot["player_armies"][0]
                current_base = copy.deepcopy(base)
                mutate(current_snapshot, current_army, current_base)
                self.assertIsNone(check(current_snapshot, current_army, **current_base))
