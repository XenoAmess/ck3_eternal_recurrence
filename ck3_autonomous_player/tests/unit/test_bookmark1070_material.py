"""Focused new-army material seam; no game or native provider is invoked."""

from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.vanilla_events.bookmark1070_material import (
    MATERIAL_METRIC,
    MATERIAL_RELATION,
    bookmark1070_army_observation_v1,
    evaluate_bookmark1070_army_material_postcondition_v1,
    plan_bookmark1070_army_material_postcondition_v1,
)


def decision():
    return {"status": "recommended", "event_definition_key": "bookmark.1070",
        "ck3_build": "1.20.0.4", "selected_native_option_index": 2,
        "choice_effect_profile": {"observable_postcondition": {
            "metric": MATERIAL_METRIC, "expected_relation": MATERIAL_RELATION,
            "material_change_required_for_evidence": True}}}


def snapshot(revision=7, *, new_army=False):
    armies = [{"army_id": 0, "owner_character_id": 29829,
               "current_province_id": 470}]
    if new_army:
        armies.append({"army_id": 268435481, "owner_character_id": 29829,
                       "current_province_id": 478})
    return {"paused": True, "map_ready": True,
        "played_character": {"character_id": 29829, "alive": True},
        "date_raw": 53145648, "revision": revision,
        "native_revision": revision + 10, "snapshot_id": f"native:{revision + 10}",
        "episode_run_id": "native-29829-material-test",
        "diagnostics": {"bridge_pid": 1234, "connection_generation": 1},
        "active_event": {"instance_id": 19} if revision == 7 else None,
        "player_armies": armies}


def army_strength():
    regiments = []
    for index, (kind, count) in enumerate((
        (None, 125), ("bowmen", 50), ("light_horsemen", 50),
        ("armored_horsemen", 25),
    )):
        regiments.append({"army_regiment_id": index, "current_soldiers": count,
            "maximum_soldiers": count, "scale": 1,
            "maa_type_status": "absent" if kind is None else "available",
            "maa_type_key": kind, "composition_unavailable_reason": None,
            "native_supply_loss_eligible": True})
    return {"status": "available", "army_id": 268435481, "native_carmy_id": 0,
        "regiment_count": 4, "current_soldiers": 250, "maximum_soldiers": 250,
        "regiment_strengths": regiments,
        "actual_army_late_event_observations_v1": {"large": "do not copy"},
        "unavailable_reason": None}


def material_case():
    before_snapshot, after_snapshot = snapshot(), snapshot(8, new_army=True)
    expected = plan_bookmark1070_army_material_postcondition_v1(decision(), before_snapshot)
    before = bookmark1070_army_observation_v1(before_snapshot)
    after = bookmark1070_army_observation_v1(after_snapshot,
        army_strengths=[army_strength()], before_army_ids=(0,))
    selection = {"status": "event_instance_advanced", "postcondition_verified": True,
        "old_event_instance_id": 19, "new_event_instance_id": None,
        "selected_native_option_index": 2,
        "starting_snapshot_id": before["snapshot_id"],
        "starting_revision": before["revision"],
        "ending_snapshot_id": after["snapshot_id"], "ending_revision": after["revision"],
        "episode_run_id": before["episode_run_id"], "bridge_pid": before["bridge_pid"],
        "connection_generation": before["connection_generation"],
        "starting_bookmark1070_armies": before, "ending_bookmark1070_armies": after}
    return expected, selection


class Bookmark1070MaterialTests(unittest.TestCase):
    def test_new_army_source_shape_uses_existing_regiment_observations(self):
        expected, selection = material_case()
        result = evaluate_bookmark1070_army_material_postcondition_v1(expected, selection)
        self.assertEqual(result["status"], "verified_change")
        self.assertEqual(result["new_army_id"], 268435481)
        self.assertEqual(result["native_carmy_id"], 0)
        self.assertEqual(result["observed_current_soldiers"], 250)
        self.assertEqual(result["observed_composition"], {
            "non_maa": 125, "bowmen": 50, "light_horsemen": 50, "armored_horsemen": 25})
        self.assertEqual(result["source_expected_levies"], 125)
        self.assertFalse(result["levy_type_identity_observed"])
        self.assertFalse(result["total_army_net_gain_used"])

    def test_capture_projects_core_fields_without_research_journals(self):
        raw = army_strength()
        before = deepcopy(raw)
        captured = bookmark1070_army_observation_v1(snapshot(8, new_army=True),
            army_strengths={"army_strengths": [raw]}, before_army_ids=[0])
        self.assertEqual(raw, before)
        self.assertNotIn("actual_army_late_event_observations_v1", captured["army_strengths"][0])
        self.assertNotIn("native_supply_loss_eligible",
                         captured["army_strengths"][0]["regiment_strengths"][0])
        self.assertIsNone(bookmark1070_army_observation_v1(snapshot())["army_strengths"])

    def test_existing_army_gains_or_other_army_losses_are_not_spawn_proof(self):
        expected, selection = material_case()
        # An unrelated original army may disappear; the independently new army still counts.
        selection["ending_bookmark1070_armies"]["player_armies"].pop(0)
        self.assertEqual(evaluate_bookmark1070_army_material_postcondition_v1(
            expected, selection)["status"], "verified_change")
        expected, selection = material_case()
        selection["ending_bookmark1070_armies"]["player_armies"] = [
            {"army_id": 0, "owner_character_id": 29829, "current_province_id": 470}]
        selection["ending_bookmark1070_armies"]["army_strengths"][0]["army_id"] = 0
        self.assertEqual(evaluate_bookmark1070_army_material_postcondition_v1(
            expected, selection)["status"], "failed")

    def test_unavailable_types_or_new_army_read_do_not_receive_credit(self):
        for mutation in ("strength", "regiments", "type", "reason"):
            with self.subTest(mutation=mutation):
                expected, selection = material_case()
                strength = selection["ending_bookmark1070_armies"]["army_strengths"][0]
                if mutation == "strength":
                    strength["status"] = "unavailable"
                elif mutation == "regiments":
                    strength["regiment_strengths"] = None
                elif mutation == "type":
                    strength["regiment_strengths"][1]["maa_type_status"] = "unavailable"
                else:
                    strength["regiment_strengths"][0]["composition_unavailable_reason"] = "unread"
                self.assertEqual(evaluate_bookmark1070_army_material_postcondition_v1(
                    expected, selection)["status"], "unavailable")

    def test_wrong_composition_owner_or_frame_fails_without_net_gain_fallback(self):
        for mutation in ("composition", "owner", "date", "actor", "generation", "instance", "revision"):
            with self.subTest(mutation=mutation):
                expected, selection = material_case()
                after = selection["ending_bookmark1070_armies"]
                if mutation == "composition":
                    after["army_strengths"][0]["regiment_strengths"][1]["maa_type_key"] = "pikemen"
                elif mutation == "owner":
                    after["player_armies"][1]["owner_character_id"] = 29830
                elif mutation == "date":
                    after["date_raw"] += 24
                elif mutation == "actor":
                    after["character_id"] = 29830
                elif mutation == "generation":
                    after["connection_generation"] += 1
                elif mutation == "instance":
                    selection["new_event_instance_id"] = 19
                else:
                    after["native_revision"] = selection["starting_bookmark1070_armies"]["native_revision"]
                self.assertEqual(evaluate_bookmark1070_army_material_postcondition_v1(
                    expected, selection)["status"], "failed")

    def test_missing_before_roster_is_unavailable_and_other_choice_not_supported(self):
        before = snapshot()
        before.pop("player_armies")
        self.assertEqual(plan_bookmark1070_army_material_postcondition_v1(
            decision(), before)["status"], "unavailable")
        other = decision()
        other["selected_native_option_index"] = 0
        self.assertIsNone(plan_bookmark1070_army_material_postcondition_v1(other, snapshot()))


if __name__ == "__main__":
    unittest.main()
