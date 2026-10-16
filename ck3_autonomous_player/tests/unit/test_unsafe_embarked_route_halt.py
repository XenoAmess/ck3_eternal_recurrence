"""Original P21 route observations; synthetic halt ACK/post-read are explicit."""
import copy
import gzip
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from xar_autoplayer import strategy
from xar_autoplayer.bridge import native_driver
from xar_autoplayer.bridge.war_contract import query_route_contact_horizon_step

FIXTURE = json.loads(gzip.decompress((Path(__file__).parent / "fixtures" /
    "unsafe_embarked_route_377_v1.json.gz").read_bytes()))
ARMY = 620757086
HALT = f"halt-army-{ARMY}"


class UnsafeEmbarkedRouteHalt(unittest.TestCase):
    def setUp(self):
        self.snapshot = copy.deepcopy(FIXTURE["snapshot"])
        self.history = copy.deepcopy(FIXTURE["history"])
        self.steps = set(FIXTURE["steps"]) | {"query-campaign-root-context-v1"}
        hostiles = self.history[1]["result"]["route_contact_horizon"]["hostile_army_ids"]
        self.steps.add(query_route_contact_horizon_step(ARMY, 5967, hostiles))

    def army(self):
        return next(a for a in self.snapshot["player_armies"] if a["army_id"] == ARMY)

    def plan(self):
        return strategy.choose_one_life_turn(self.history, snapshot=self.snapshot,
                                            action_steps=self.steps)

    def ack(self):
        """Exercise the production Driver branch with an explicitly synthetic ACK."""
        snapshot = self.snapshot
        class Reader:
            def take_snapshot(self):
                return copy.deepcopy(snapshot)
            def _h3937_date_hold_active(self, _frame):
                return False
            def _execute_primitive_step(self, step, **kwargs):
                self.submissions = getattr(self, "submissions", 0) + 1
                return {"step": step, "accepted": True, "status": "submitted"}
        reader = Reader()
        result = native_driver.NativeHeadlessGameplayDriver._execute_native_war_step(
            reader, HALT, expected_revision=snapshot["revision"])
        self.assertEqual(reader.submissions, 1)
        self.history.append({"index": 379, "command": HALT, "ok": True, "result": result})
        return result

    def shorten_route(self):
        """Synthetic independent publication, not a claim of current live halt success."""
        self.snapshot["native_revision"] += 1
        self.snapshot["revision"] += 1
        self.snapshot["snapshot_id"] = f'native:{self.snapshot["native_revision"]}'
        for army in self.snapshot["player_armies"] + self.snapshot["active_wars"][0]["allied_armies"]:
            if army["army_id"] == ARMY:
                army.update(route_province_ids=[5967], route_source_count=1,
                            move_target_province_id=5967)

    def publish_synthetic_replan_queries(self):
        """New-frame query contracts derived from original inputs, never live receipts."""
        originals = copy.deepcopy(FIXTURE["history"])
        current = copy.deepcopy(originals[1])
        hostiles = current["result"]["route_contact_horizon"]["hostile_army_ids"]
        current["command"] = query_route_contact_horizon_step(ARMY, 5967, hostiles)
        current["result"]["step"] = current["command"]
        horizon = current["result"]["route_contact_horizon"]
        horizon["target_province_id"] = 5967
        horizon["subject_route"]["route_province_ids"] = [5967]
        horizon["subject_route"]["arrival_date_raws"] = horizon["subject_route"]["arrival_date_raws"][:1]
        self.steps.add(current["command"])
        # The old committed target becomes a separate replan candidate after Halt.
        former_target = copy.deepcopy(originals[2])
        former_target["command"] = f"preview-move-army-{ARMY}-to-5969"
        former_target["result"]["step"] = former_target["command"]
        former_target["result"]["route_preview"].update(
            target_province_id=5969, route_province_ids=[5967, 5966, 5969])
        self.steps.add(former_target["command"])
        self.snapshot["campaign_root_context"] = {
            "status": "available", "snapshot_revision": self.snapshot["native_revision"],
            "date_raw": self.snapshot["date_raw"], "player_character_id": 40526,
            "readiness": {"ready": True}, "capital_province_id": 5965,
        }  # Synthetic capital shares one actually observed unsafe candidate.
        delta = self.snapshot["date_raw"] - FIXTURE["snapshot"]["date_raw"]
        def shift_dates(value):
            if isinstance(value, dict):
                for key, item in value.items():
                    if isinstance(item, int) and (key == "date_raw" or key.endswith("_date_raw")):
                        value[key] = item + delta
                    elif isinstance(item, list) and key.endswith("_date_raws"):
                        value[key] = [day + delta for day in item]
                    else:
                        shift_dates(item)
            elif isinstance(value, list):
                for item in value:
                    shift_dates(item)
        for row in originals + [former_target, current]:
            result = row["result"]
            shift_dates(result)
            result.update(queried_snapshot_id=self.snapshot["snapshot_id"],
                          queried_revision=self.snapshot["revision"],
                          queried_native_revision=self.snapshot["native_revision"])
            if "snapshot_revision" in result:
                result["snapshot_revision"] = self.snapshot["native_revision"]
            for payload in (result.get("route_preview"), result.get("route_contact_horizon")):
                if isinstance(payload, dict):
                    if "snapshot_revision" in payload:
                        payload["snapshot_revision"] = self.snapshot["native_revision"]
                    if "date_raw" in payload:
                        payload["date_raw"] = self.snapshot["date_raw"]
            row["index"] = max(r["index"] for r in self.history) + 1
            self.history.append(row)

    def test_actual_available_unsafe_horizon_selects_halt_before_time(self):
        self.assertFalse(self.snapshot["active_wars"][0]["player_is_primary_war_leader"])
        self.assertEqual(self.army()["army_state"], "embarked")
        self.assertEqual(self.army()["current_province_id"], 940)
        self.assertFalse(self.history[-1]["result"]["route_contact_horizon"]["one_day_contact_free"])
        plan = self.plan()
        self.assertEqual(plan["phase"], "native_war_unsafe_route_halt_submit")
        self.assertEqual(plan["selected_step"], HALT)

    def test_ack_records_actual_starting_tuple_without_claiming_stop(self):
        result = self.ack()
        action = result["war_action"]
        self.assertEqual(action["original_route_province_ids"], [5967, 5966, 5969])
        self.assertEqual(action["submitted_native_revision"], 3640)
        self.assertEqual(action["submitted_connection_generation"], 4)
        self.assertEqual(action["submitted_episode_run_id"], self.snapshot["episode_run_id"])
        self.assertFalse(action["postcondition_verified"])
        self.assertEqual(self.plan()["phase"], "native_war_unsafe_route_halt_pending")

    def test_fresh_suffix_readback_permits_replanning_without_replaying_halt(self):
        self.ack()
        self.shorten_route()
        observation = strategy._pending_unsafe_route_halt(self.history, self.snapshot, army_id=ARMY)
        self.assertTrue(observation["suffix_cancellation_observed"])
        self.assertTrue(observation["current_edge_retained"])
        self.assertFalse(observation["postcondition_verified"])
        self.assertFalse(observation["contact_free_proven"])
        plan = self.plan()
        self.assertEqual(plan["phase"], "native_war_route_contact_horizon")
        self.assertTrue(plan["selected_step"].startswith(f"query-route-contact-horizon-v1-{ARMY}-to-5967-"))
        self.assertNotEqual(plan["selected_step"], HALT)

    def test_all_actual_route_candidates_unsafe_after_synthetic_suffix_observes_one_day(self):
        self.ack()
        self.shorten_route()
        self.publish_synthetic_replan_queries()
        plan = self.plan()
        self.assertEqual(plan["phase"], "native_war_retained_unsafe_edge_one_day_watch")
        self.assertEqual(plan["selected_step"], "life-advance-one-day")
        watch = plan["retained_edge_watch"]
        self.assertFalse(watch["contact_free_proven"])
        self.assertFalse(watch["offensive_combat_permission"])
        self.assertFalse(watch["movement_resubmitted"])
        self.assertFalse(watch["war_or_material_credit"])
        self.assertTrue(plan["route_rejections"])

    def test_retained_edge_observation_survives_next_day_without_resubmitting_halt(self):
        self.ack()
        self.shorten_route()
        self.snapshot["date_raw"] += 24
        self.snapshot["native_revision"] += 1
        self.snapshot["revision"] += 1
        self.snapshot["snapshot_id"] = f'native:{self.snapshot["native_revision"]}'
        self.publish_synthetic_replan_queries()
        plan = self.plan()
        self.assertEqual(plan["selected_step"], "life-advance-one-day")
        self.assertEqual(plan["retained_edge_watch"]["halt_submission"]["submitted_date_raw"],
                         FIXTURE["snapshot"]["date_raw"])

    def test_watch_requires_fresh_halt_postread_and_exhausted_safe_replans(self):
        self.ack()
        self.shorten_route()
        self.publish_synthetic_replan_queries()
        plan = self.plan()
        audit = strategy._fresh_route_contact_horizon(self.history, self.snapshot,
            army_id=ARMY, origin_province_id=940, target_province_id=5967,
            hostile_army_ids=tuple(self.history[-1]["result"]["route_contact_horizon"]["hostile_army_ids"]),
            route_province_ids=[5967])
        audited = {"contact_horizon": audit,
                   "contact_policy": "blocked_without_qualified_combat_permission"}
        def watch(**kwargs):
            return strategy._retained_unsafe_edge_one_day_watch_plan(
                self.history, self.snapshot, self.army(), audited,
                available_steps=self.steps, war_summary=[],
                route_rejections=kwargs.get("rejections", plan["route_rejections"]))
        self.assertIsNotNone(watch())
        for rejections in ([], [{"status": "safe"}], [{"status": "contact_timeline_unavailable"}]):
            self.assertIsNone(watch(rejections=rejections))
        for field, value in (("active_event", {"event_id": "test"}),
                             ("paused", False), ("native_revision", 3640)):
            old = self.snapshot[field]
            self.snapshot[field] = value
            self.assertIsNone(watch())
            self.snapshot[field] = old
        for change in ({"in_combat": True}, {"retreating": True},
                       {"owner_character_id": 1}, {"route_province_ids": [5967, 5966]}):
            army = self.army()
            old = dict(army)
            army.update(change)
            self.assertIsNone(watch())
            army.clear()
            army.update(old)
        self.history.append({"index": 999, "command": f"move-army-{ARMY}-to-5968", "ok": True})
        self.assertIsNone(watch())

    def test_stale_or_other_generation_readback_never_confirms_suffix(self):
        self.ack()
        self.shorten_route()
        for field, value in (("native_revision", 3640), ("episode_run_id", "other")):
            with self.subTest(field=field):
                altered = dict(self.snapshot, **{field: value})
                result = strategy._pending_unsafe_route_halt(self.history, altered, army_id=ARMY)
                self.assertFalse(result["suffix_cancellation_observed"])
        self.snapshot["diagnostics"]["connection_generation"] += 1
        self.assertFalse(strategy._pending_unsafe_route_halt(
            self.history, self.snapshot, army_id=ARMY)["suffix_cancellation_observed"])

    def test_allied_embarked_retreat_candidate_does_not_require_ghost_strength(self):
        war = self.snapshot["active_wars"][0]
        self.assertIsNone(strategy._same_frame_army_strength_balance(self.snapshot, war["war_id"]))
        kwargs = dict(active_wars=[war], controlled_armies=self.snapshot["player_armies"],
            tactical_war=war, current_province_id=940, subject_army_id=ARMY,
            active_route_unsafe=True, route_rejections=[{"status": "unsafe", "target_province_id": 5969}],
            strength_balance=None)
        self.assertTrue(strategy._outnumbered_attacker_regroup_input_ready(self.snapshot, **kwargs))
        self.assertFalse(strategy._outnumbered_attacker_regroup_input_ready(
            self.snapshot, **dict(kwargs, active_route_unsafe=False)))
        for change in ({"owner_character_id": 1}, {"in_combat": True}, {"retreating": True}):
            with self.subTest(change=change):
                prior = dict(self.army())
                army = self.army()
                army.update(change)
                self.assertFalse(strategy._outnumbered_attacker_regroup_input_ready(self.snapshot, **kwargs))
                army.clear()
                army.update(prior)


if __name__ == "__main__":
    unittest.main()
