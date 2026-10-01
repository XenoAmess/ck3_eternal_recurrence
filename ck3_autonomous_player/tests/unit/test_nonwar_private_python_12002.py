"""Actual isolated 1.20 native producer JSON through private Python consumers.

Fixtures come from native owned-memory/callback tests, never a live CK3 frame.
The small endpoint below supplies only the existing outer protocol envelope.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
NATIVE = ROOT / "native_bridge"
FIXTURES = NATIVE / "research" / "fixtures"

from xar_autoplayer.bridge.current_first_heir_relationship_private_transport import (
    STEP as RELATION_STEP, query_current_first_heir_relationship_private_v1,
)
from xar_autoplayer.bridge.construction_economic_value_v1 import (
    authored_monthly_income_hundredths,
)
from xar_autoplayer.bridge.domain_construction_private_transport_v1 import (
    QUERY_NATIVE, query_construction_private,
)
from xar_autoplayer.bridge.nonwar_private_build import (
    private_native_provenance, private_native_readback_matches,
)
from xar_autoplayer.bridge.player_lifestyle_private_transport_v1 import (
    STATE_QUERY_STEP, query_player_lifestyle_private_v1,
)
from xar_autoplayer.bridge.version_identity import CK3_12002
from xar_autoplayer.current_first_heir_betrothal_formal_consumer import (
    evaluate_current_betrothal_fulfillment,
)
from xar_autoplayer.lifestyle_formal_consumer import consume_lifestyle_private_query


def fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def frame(*, actor: int, revision: int, date_raw: int) -> dict[str, object]:
    return {
        "paused": True, "map_ready": True, "revision": revision + 1,
        "native_revision": revision, "snapshot_id": f"native:{revision}",
        "date_raw": date_raw, "episode_run_id": f"native-{actor}-offline-producer",
        "played_character": {"character_id": actor, "alive": True},
        "active_event": None, "pending_character_interaction": None,
        "active_wars": [], "player_armies": [],
        "diagnostics": {"hello": {
            "expected_ck3_version": CK3_12002.game_version,
            "expected_ck3_sha256": CK3_12002.executable_sha256,
        }},
    }


class FixtureDriver:
    allow_private_current_first_heir_relationship_query = True
    allow_private_lifestyle_formal_trial = True
    command_timeout_seconds = 1.0

    def __init__(self, snapshot: dict[str, object], result: dict[str, object],
                 *, heir: int | None = None):
        self.snapshot, self.result, self.heir = snapshot, result, heir
        self.endpoint = self.state = self
        self.requests: list[dict[str, object]] = []

    def take_snapshot(self) -> dict[str, object]:
        return deepcopy(self.snapshot)

    def send(self, request: dict[str, object]) -> None:
        self.requests.append(deepcopy(request))

    def wait_for_command_result(self, request_id: str, timeout: float) -> dict[str, object]:
        if self.requests[-1]["request_id"] != request_id:
            raise AssertionError("fixture endpoint request identity changed")
        return {"type": "command_result", "protocol_version": 1,
                "request_id": request_id, "ok": True, "result": deepcopy(self.result)}

    def _execute_campaign_root_context_v1_query(self, *, expected_revision: int):
        if expected_revision != self.snapshot["revision"]:
            raise AssertionError("fixture root was queried on another public revision")
        return {"status": "available", "query_sequence": 11,
                "held_title_partition": [{"primary": True,
                                          "first_heir_character_id": self.heir}]}


class NonwarPrivatePython12002Tests(unittest.TestCase):
    def test_fixture_bytes_are_the_actual_frozen_native_producer_outputs(self):
        provenance = fixture("ck3_12002_nonwar_private_python_provenance.json")
        self.assertEqual(provenance["local_ck3_operations"], [])
        self.assertEqual(provenance["executable_sha256"], CK3_12002.executable_sha256)
        for row in provenance["fixtures"]:
            with self.subTest(file=row["file"]):
                self.assertEqual(hashlib.sha256((FIXTURES / row["file"]).read_bytes()).hexdigest(),
                                 row["sha256"])

    def test_actual_family_negative_round_trips_and_formal_consumer_still_waits(self):
        pair = fixture("ck3_12002_current_betrothal_negative.json")
        snapshot = frame(actor=pair["actor_character_id"], revision=3, date_raw=53220000)
        native = {
            "step": RELATION_STEP, "accepted": True, "private_build": True,
            "advertised": False, "read_only": True, "native_revision": 3,
            "subject_source": "public_campaign_root_primary_first_heir",
            "status": "available", "unavailable_reason": None,
            "heir_character_id": pair["heir_character_id"], "bilateral_verified": True,
            "betrothed_character_id": pair["partner_character_id"],
            "primary_spouse_character_id": None, "spouse_character_ids": [],
            "betrothal_actionability": pair,
        }
        driver = FixtureDriver(snapshot, native, heir=pair["heir_character_id"])
        relationship = query_current_first_heir_relationship_private_v1(
            driver, expected_native_revision=3)
        self.assertEqual(relationship["exact_ck3_build"], CK3_12002.game_version)
        self.assertEqual(relationship["exe_sha256"], CK3_12002.executable_sha256)
        self.assertTrue(private_native_readback_matches(snapshot, relationship))
        self.assertEqual(relationship["betrothal_actionability"], pair)
        self.assertEqual(pair["heir_adult_measure_raw"], 14)
        self.assertEqual(pair["heir_adult_threshold_raw"], 16)
        self.assertIs(pair["complete_can_send"], False)
        self.assertEqual(pair["generic_costs"]["gold_raw"], -20000)
        decision = evaluate_current_betrothal_fulfillment(relationship, snapshot)
        self.assertNotEqual(decision["status"], "recommend_action")
        self.assertEqual([request["step"] for request in driver.requests], [RELATION_STEP])

    def test_actual_life_zero_points_uses_current_state_without_a_second_focus_action(self):
        life = fixture("ck3_12002_lifestyle_state_zero_points.json")
        snapshot = frame(actor=life["player_character_id"],
                         revision=life["native_revision"], date_raw=life["date_raw"])
        native = {"step": STATE_QUERY_STEP, "private_build": True, "advertised": False,
                  "status": "available", "episode_run_id": snapshot["episode_run_id"],
                  "formal_precondition_status": "zero_unspent_points", "snapshot": life}
        driver = FixtureDriver(snapshot, native)
        result = query_player_lifestyle_private_v1(
            driver, expected_revision=snapshot["revision"], query_step=STATE_QUERY_STEP)
        self.assertEqual(result["status"], "available")
        self.assertEqual(result["snapshot"]["current_lifestyle_progress"]["unspent_perk_points"], 0)
        self.assertEqual(result["snapshot"]["current_lifestyle_progress"]["xp_total_raw"], 71250000)
        self.assertEqual(len(result["snapshot"]["owned_perk_keys"]), 7)
        plan = consume_lifestyle_private_query(
            {"selected_step": "life-advance"},
            scope={"status": "admitted", "at_peace": True}, query=result)
        # This actual state-only producer has no final legal candidate set.
        # Preserve the formal quality check instead of synthesizing readiness.
        self.assertIsNone(plan["selected_step"])
        self.assertEqual(plan["phase"], "lifestyle_min_observation_unavailable")
        self.assertEqual([request["step"] for request in driver.requests], [STATE_QUERY_STEP])
        self.assertIs(life["readiness"]["legal_perk_candidates_ready"], False)

    def test_actual_world_query_selects_verified_scope_despite_unavailable_gui(self):
        probe = fixture("ck3_12002_construction_query_only.json")
        world = probe["player_world_building_sources"]
        snapshot = frame(actor=world["player_character_id"],
                         revision=world["snapshot_revision"], date_raw=world["date_raw"])
        driver = FixtureDriver(snapshot, {"step": QUERY_NATIVE, "accepted": True,
                                          "private_probe": probe})
        result = query_construction_private(driver, expected_revision=snapshot["revision"])
        self.assertEqual(result["status"], "selected")
        self.assertEqual(result["exact_ck3_build"], CK3_12002.game_version)
        self.assertEqual(result["exe_sha256"], CK3_12002.executable_sha256)
        self.assertEqual(result["candidate"]["stock_gold_cost_raw"],
                         world["legal_samples"][0]["cost_raw_native"][0])
        self.assertEqual(result["candidate"]["authored_monthly_income_hundredths"], 70)
        self.assertEqual(len(world["legal_samples"][0]["cost_raw_slots"]), 8)
        self.assertEqual(len(world["legal_samples"][0]["cost_raw_native"]), 10)
        self.assertIsNone(result["world"]["active_constructions"][0]["native_remaining_work_raw"])
        self.assertIsNone(result["world"]["active_constructions"][0]["native_province_monthly_income_raw"])
        self.assertEqual(probe["status"], "unavailable")
        self.assertEqual(probe["player_model_sources"]["status"], "unavailable")
        self.assertEqual(probe["executor_invocations"], 0)
        self.assertEqual([request["step"] for request in driver.requests], [QUERY_NATIVE])

    def test_same_nineteen_economic_keys_have_actual_12002_authored_source_evidence(self):
        evidence = json.loads((NATIVE / "research" / "ck3_12002_construction_authored_income.json")
                              .read_text(encoding="utf-8"))
        self.assertEqual(evidence["scope_count"], 19)
        self.assertEqual(len(evidence["scope"]), 19)
        for row in evidence["scope"]:
            self.assertEqual(authored_monthly_income_hundredths(
                row["key"], exact_ck3_build=CK3_12002.game_version), row["income_hundredths"])
        self.assertIsNone(authored_monthly_income_hundredths("castle_01", exact_ck3_build="1.20.0.2"))
        self.assertIsNone(authored_monthly_income_hundredths("farm_estates_01", exact_ck3_build="unbound"))

    def test_archived_119_contract_stays_version_only(self):
        self.assertEqual(private_native_provenance({}), {"exact_ck3_build": "1.19.0.6"})
        self.assertTrue(private_native_readback_matches({}, {"exact_ck3_build": "1.19.0.6"}))


if __name__ == "__main__":
    unittest.main()
