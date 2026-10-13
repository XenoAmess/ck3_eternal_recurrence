"""Focused production composer tests without loading a driver or connecting CK3."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType
import unittest


SOURCE = Path(__file__).resolve().parents[1] / "src/xar_autoplayer"
# A private package name loads the real new leaf and three existing contract
# leaves, without executing bridge.__init__ and its runtime-driver imports.
PACKAGE = "_ordinary_exit_observation_fixture"
for name, path in ((PACKAGE, SOURCE), (PACKAGE + ".bridge", SOURCE / "bridge")):
    package = ModuleType(name)
    package.__path__ = [str(path)]
    sys.modules[name] = package
spec = importlib.util.spec_from_file_location(
    PACKAGE + ".ordinary_war_exit_observation_v1", SOURCE / "ordinary_war_exit_observation_v1.py",
)
LEAF = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = LEAF
spec.loader.exec_module(LEAF)


def snapshot(*, after=False, side="attacker", active=False, date=1000):
    war = {"war_id": 77, "player_side": side, "primary_opponent_character_id": 52,
           "targeted_title_ids": [2132, 0]}
    return {
        "snapshot_id": "native:8" if after else "native:7",
        "revision": 9 if after else 8, "native_revision": 8 if after else 7,
        "date_raw": date, "episode_run_id": "ordinary-29829", "paused": True,
        "map_ready": True, "played_character": {"character_id": 29829, "alive": True},
        "diagnostics": {"bridge_pid": 991, "connection_generation": 3,
                        "hello": {"game_version": "1.20.0.4",
                                  "executable_sha256": LEAF.PLAYER_CLAIMS_V1_EXE_SHA256}},
        "active_wars": [war] if not after or active else [],
        "played_character_gold": {"raw": 1300000 if after else 1500000, "scale": 100000},
        "played_character_prestige": {"raw": 5000000, "scale": 100000},
        "played_character_piety": {"raw": 0, "scale": 100000},
    }


def query_envelope(post, step, **payload):
    return {
        "step": step, "accepted": True, "read_only": True, "backend_id": "native-headless",
        "query_sequence": 61, "snapshot_revision": post["native_revision"],
        "date_raw": post["date_raw"], "queried_snapshot_id": post["snapshot_id"],
        "queried_revision": post["revision"], "queried_native_revision": post["native_revision"],
        **payload,
    }


def claims(post):
    payload = {
        "schema": "xar.ck3.player-claims.v1", "schema_version": 1,
        "game_version": "1.20.0.4", "executable_sha256": LEAF.PLAYER_CLAIMS_V1_EXE_SHA256,
        "snapshot_revision": post["native_revision"], "date_raw": post["date_raw"],
        "actor_character_id": 29829, "title_ids": [2132, 0], "available": True,
        "status": "available", "unavailable_reason": None,
        "claims": [{"title_id": title, "present": False, "state": "absent",
                    "strong": None, "implicit": None} for title in (2132, 0)],
    }
    return query_envelope(post, "query-player-claims-v1-2132,0", player_claims=payload)


def holder(post, title=2132):
    payload = {
        "schema": "xar.ck3.title-holder.v1", "schema_version": 1, "available": True,
        "status": "available", "snapshot_revision": post["native_revision"],
        "date_raw": post["date_raw"], "title_id": title, "actor_character_id": 29829,
        "game_version": "1.20.0.4", "executable_sha256": LEAF.PLAYER_CLAIMS_V1_EXE_SHA256,
        "title_tier_raw": 2, "title_tier_key": "county", "holder_character_id": 52,
        "holder_immediate_liege_character_id": None, "holder_top_liege_character_id": 52,
        "holder_is_player": False, "holder_in_player_realm": False, "unavailable_reason": None,
        "title_key": "c_example", "title_key_available": True, "title_key_status": "available",
        "title_key_unavailable_reason": None,
    }
    return query_envelope(post, "query-title-holder-v1-" + str(title), title_holder=payload)


def truce(post, *, absent=False):
    payload = {
        "schema_version": 1, "backend_id": "ck3-1.20.0.4-native-player-truce-expiry-v1",
        "ck3_build": "1.20.0.4", "executable_sha256": LEAF.PLAYER_CLAIMS_V1_EXE_SHA256,
        "status": "no_truce" if absent else "available", "snapshot_revision": post["native_revision"],
        "current_date_raw": post["date_raw"], "owner_character_id": 29829, "toward_character_id": 52,
        "native_has_truce": not absent, "actual_expiry_observable": not absent,
        "expiry_date_raw": None if absent else 44800, "same_frame_stable": True,
        "readiness": not absent, "temporal_semantics": "post_application_persisted_relation_state",
        "unavailable_reason": "native_has_truce_false" if absent else None,
    }
    return query_envelope(post, "query-raiktor-actual-truce-expiry-v1-52",
                          raiktor_actual_truce_expiry=payload)


def compose(before=None, post=None, action=None, **kwargs):
    return LEAF.compose_ordinary_war_exit_observation_v1(
        before_snapshot=before if before is not None else snapshot(),
        post_snapshot=post if post is not None else snapshot(after=True),
        action_result=action if action is not None else {
            "step": "surrender-war-77", "accepted": True, "status": "submitted",
            "war_termination_result": {"outcome": "attacker_defeat", "status": "applied"},
        }, **kwargs,
    )


class OrdinaryWarExitObservationTests(unittest.TestCase):
    def test_existing_typed_materials_do_not_supply_result_identity(self):
        pre, post = snapshot(), snapshot(after=True)
        materials = {"claims_result": claims(post), "title_holder_results": [holder(post)],
                     "truce_result": truce(post)}
        frozen = copy.deepcopy((pre, post, materials))
        receipt = compose(pre, post, **materials)
        self.assertEqual(receipt["status"], "war_absent")
        self.assertTrue(receipt["war_absence_observed"])
        self.assertEqual(receipt["requested_outcome"], "player_defeat")
        self.assertEqual(receipt["requested_native_outcome"], "attacker_defeat")
        self.assertIsNone(receipt["observed_result_identity"])
        self.assertEqual(receipt["result_identity_reason"], "no_independent_result_observer")
        self.assertEqual(receipt["resources"]["gold"]["delta_raw"], -200000)
        self.assertEqual(receipt["resources"]["gold"]["action_attribution"], "unproven")
        self.assertEqual(receipt["claims"]["rows"][0]["state"], "absent")
        self.assertFalse(receipt["titles"]["all_frozen_targets_observed"])
        self.assertEqual(receipt["truce"]["expiry_date_raw"], 44800)
        self.assertEqual(receipt["issues"], [])
        self.assertEqual((pre, post, materials), frozen)
        self.assertLess(len(json.dumps(receipt).encode()), 8192)

    def test_pending_and_crossed_identity_are_observations_without_material_credit(self):
        pending = compose(post=snapshot(after=True, active=True))
        self.assertEqual(pending["status"], "war_present")
        self.assertFalse(pending["war_absence_observed"])
        self.assertEqual(pending["resources"], {})
        self.assertIsNone(pending["observed_result_identity"])
        for key, value in (("episode_run_id", "other"),
                           ("played_character", {"character_id": 30000, "alive": True}),
                           ("active_wars", None)):
            post = snapshot(after=True)
            post[key] = value
            with self.subTest(key=key):
                receipt = compose(post=post)
                self.assertEqual(receipt["status"], "unbound")
                self.assertIsNone(receipt["war_absence_observed"])
                self.assertEqual(receipt["resources"], {})
        post = snapshot(after=True)
        post["diagnostics"]["connection_generation"] = 4
        self.assertEqual(compose(post=post)["status"], "unbound")

    def test_polarity_missing_resources_and_observed_absence_remain_separate(self):
        before, post = snapshot(side="defender"), snapshot(after=True, date=1024)
        post["played_character_piety"] = None
        receipt = compose(before, post, truce_result=truce(post, absent=True))
        self.assertEqual(receipt["requested_native_outcome"], "attacker_victory")
        self.assertEqual(receipt["truce"]["status"], "no_truce")
        self.assertEqual(receipt["truce"]["direction"], "player_toward_opponent")
        self.assertIsNone(receipt["truce"]["expiry_date_raw"])
        self.assertFalse(receipt["resources"]["gold"]["same_date"])
        self.assertEqual(receipt["resources"]["gold"]["action_attribution"], "unproven")
        self.assertEqual(receipt["resources"]["piety"]["status"], "unavailable")
        self.assertIsNone(receipt["resources"]["piety"]["delta_raw"])
        for step, expected in (("enforce-demands-77", "attacker_defeat"),
                               ("offer-white-peace-77", "white_peace")):
            self.assertEqual(compose(before, post, {"step": step, "accepted": True})[
                "requested_native_outcome"], expected)

    def test_typed_query_binding_errors_do_not_change_observed_war_absence(self):
        post = snapshot(after=True)
        cases = []
        bad = claims(post)
        bad["player_claims"]["actor_character_id"] = 30000
        cases.append(("claims_result", bad, "claims"))
        bad = holder(post)
        bad["queried_revision"] = 8
        cases.append(("title_holder_results", [bad], "titles"))
        bad = truce(post)
        bad["raiktor_actual_truce_expiry"]["owner_character_id"] = 52
        cases.append(("truce_result", bad, "truce"))
        bad = truce(post)
        bad["raiktor_actual_truce_expiry"]["ck3_build"] = "1.19.0.6"
        cases.append(("truce_result", bad, "truce"))
        for argument, value, domain in cases:
            with self.subTest(argument=argument, domain=domain):
                receipt = compose(post=post, **{argument: value})
                self.assertTrue(receipt["war_absence_observed"])
                self.assertEqual(receipt[domain]["status"], "unavailable")
                self.assertIsNone(receipt["observed_result_identity"])
                self.assertTrue(receipt["issues"])

    def test_no_target_war_and_large_target_receipts_are_bounded(self):
        pre = snapshot()
        pre["active_wars"][0]["targeted_title_ids"] = []
        receipt = compose(before=pre)
        self.assertTrue(receipt["war_absence_observed"])
        self.assertEqual(receipt["target_title_count"], 0)
        pre["active_wars"][0]["targeted_title_ids"] = list(range(4096))
        receipt = compose(before=pre)
        self.assertEqual(len(receipt["target_title_ids"]), 32)
        self.assertEqual(receipt["target_titles_omitted"], 4064)
        self.assertLess(len(json.dumps(receipt).encode()), 8192)
        self.assertIsNone(compose(action={"step": "life-advance-day", "accepted": True}))
        self.assertIsNone(compose(action={"step": "surrender-war-077", "accepted": True}))
        self.assertNotIn("xar_autoplayer.bridge.native_driver", sys.modules)


if __name__ == "__main__":
    unittest.main(verbosity=2)
