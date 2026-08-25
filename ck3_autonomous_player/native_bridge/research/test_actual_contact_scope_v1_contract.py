#!/usr/bin/env python3
"""Validate the pinned actual-contact static ABI and synthetic order fixture."""

from __future__ import annotations

import json
from pathlib import Path
import unittest


HERE = Path(__file__).resolve().parent
ABI_PATH = HERE / "actual_contact_scope_v1_abi.json"
FIXTURE_PATH = HERE / "fixtures" / "actual_contact_scope_v1_source_contract.json"


def load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"{path} must contain a JSON object")
    return value


def relation(relations: dict[str, object], source: int, target: int) -> bool:
    return bool(relations.get(f"{source}->{target}", False))


def collect_loser_ids(row: dict[str, object]) -> list[int]:
    result = row["battle_result"]
    if not result["full_id_matches"] or not result["ready"]:
        return []
    winner = int(result["winner_side"])
    if winner == -1:
        return []
    loser = row["defender"] if winner == 0 else row["attacker"]
    return [int(value) for value in loser["native_carmy_ids"]]


def select_existing(
    source: dict[str, object],
) -> tuple[dict[str, object] | None, int | None, list[int]]:
    incoming_owner = int(source["incoming"]["owner_character_id"])
    relations = source["directed_contact_relations"]
    selected: dict[str, object] | None = None
    selected_index: int | None = None
    exclusions: list[int] = []
    for index, row in enumerate(source["combat_rows_numeric_id_order"]):
        if not row["full_id_matches"]:
            raise AssertionError("fixture contains stale full CCombatID")
        compatible = False
        if not row["finalized"]:
            attacker = int(row["attacker"]["primary_character_id"])
            defender = int(row["defender"]["primary_character_id"])
            compatible = relation(relations, incoming_owner, attacker) != relation(
                relations, incoming_owner, defender
            )
        if compatible:
            selected = row
            selected_index = index
        elif selected is None:
            exclusions.extend(collect_loser_ids(row))
    return selected, selected_index, exclusions


def predict_join_side(
    source: dict[str, object], selected: dict[str, object]
) -> str:
    incoming_owner = int(source["incoming"]["owner_character_id"])
    relations = source["directed_contact_relations"]
    attacker = int(selected["attacker"]["primary_character_id"])
    defender = int(selected["defender"]["primary_character_id"])
    reverse_attacker = relation(relations, attacker, incoming_owner)
    reverse_defender = relation(relations, defender, incoming_owner)
    if reverse_attacker == reverse_defender:
        raise AssertionError("strict fixture requires exactly one reverse relation")
    return "defender" if reverse_attacker else "attacker"


def row_is_eligible(row: dict[str, object]) -> bool:
    return (
        bool(row["full_ids_match"])
        and int(row["unit_state_raw"]) == 0
        and int(row["retreat_state"]) <= 0
        and not bool(row["empty_without_gathering"])
        and not bool(row["has_valid_combat"])
    )


def project_new_contact(source: dict[str, object]) -> dict[str, object]:
    incoming = source["incoming"]
    incoming_owner = int(incoming["owner_character_id"])
    if int(incoming["current_soldiers"]) <= 0:
        return {"transition_kind": "none"}
    relations = source["directed_contact_relations"]
    rows = source["province_unit_rows_numeric_cunit_id_order"]

    exclusions: list[int] = []
    for combat in source["combat_rows_numeric_id_order"]:
        exclusions.extend(collect_loser_ids(combat))

    seed: dict[str, object] | None = None
    for row in rows:
        owner = int(row["owner_character_id"])
        if owner == incoming_owner or not row_is_eligible(row):
            continue
        if int(row["native_carmy_id"]) in exclusions:
            continue
        if relation(relations, incoming_owner, owner):
            seed = row
            break
    if seed is None:
        return {"transition_kind": "none"}

    seed_owner = int(seed["owner_character_id"])
    opponents: list[dict[str, int]] = []
    for row in rows:
        if not row_is_eligible(row):
            continue
        owner = int(row["owner_character_id"])
        if owner != seed_owner and not relation(relations, owner, incoming_owner):
            continue
        opponents.append(
            {
                "public_cunit_id": int(row["public_cunit_id"]),
                "native_carmy_id": int(row["native_carmy_id"]),
                "owner_character_id": owner,
            }
        )

    initiator_is_defender = bool(source["holder_relation"]) or bool(
        source["province_fallback_relation"]
    )
    opponent_ids = list(
        dict.fromkeys(row["native_carmy_id"] for row in opponents)
    )
    initiating_id = int(incoming["native_carmy_id"])
    return {
        "transition_kind": "create_new",
        "defender_seed_character_id": seed_owner,
        "defender_seed_public_cunit_id": int(seed["public_cunit_id"]),
        "loser_exclusion_native_carmy_ids": exclusions,
        "ordered_opponents": opponents,
        "initiator_is_defender": initiator_is_defender,
        "initiator_side": "defender" if initiator_is_defender else "attacker",
        "opponent_side": "attacker" if initiator_is_defender else "defender",
        "predicted_attacker_native_carmy_ids": (
            opponent_ids if initiator_is_defender else [initiating_id]
        ),
        "predicted_defender_native_carmy_ids": (
            [initiating_id] if initiator_is_defender else opponent_ids
        ),
        "raw_adjacency_kind": int(source["province"]["raw_adjacency_kind"]),
    }


def project_in_combat_observation(source: dict[str, object]) -> dict[str, object]:
    subject = source["subject"]
    combat = source["combat"]
    combat_id = int(subject["linked_combat_id"])
    if (
        combat_id <= 0
        or combat_id != int(combat["combat_id"])
        or not combat["full_id_matches"]
        or not combat["active_predicate"]
        or combat["finalized"]
        or not combat["province_identity_matches"]
        or int(combat["province_id"])
        != int(source["requested_target_province_id"])
        or int(combat["province_id"])
        != int(subject["current_province_id"])
    ):
        raise AssertionError("in-combat fixture identity is not closed")
    combat_rows = source["province_combat_ids_numeric_order"]
    if combat_rows != sorted(combat_rows) or combat_id not in combat_rows:
        raise AssertionError("in-combat fixture CombatID order is invalid")
    participants = {
        int(row["native_carmy_id"]): row
        for row in source["participant_identity_rows"]
    }

    def map_side(native_ids: list[int]) -> list[int]:
        public_ids: list[int] = []
        for native_id in native_ids:
            row = participants[int(native_id)]
            if (
                int(row["linked_combat_id"]) != combat_id
                or not row["carmy_cunit_backlink_matches"]
            ):
                raise AssertionError("participant backlink is not closed")
            public_id = int(row["public_cunit_id"])
            if public_id in public_ids:
                raise AssertionError("side contains duplicate public CUnitID")
            public_ids.append(public_id)
        return public_ids

    attackers = map_side(combat["attacker_native_carmy_ids_stored_order"])
    defenders = map_side(combat["defender_native_carmy_ids_stored_order"])
    subject_id = int(subject["public_cunit_id"])
    if (subject_id in attackers) == (subject_id in defenders):
        raise AssertionError("subject must occur in exactly one actual side")
    return {
        "scope_kind": "post_contact_observation",
        "transition_kind": "in_combat",
        "combat_id": combat_id,
        "combat_array_index": combat_rows.index(combat_id),
        "actual_target_province_id": int(combat["province_id"]),
        "subject_side": "attacker" if subject_id in attackers else "defender",
        "actual_attacker_public_cunit_ids": attackers,
        "actual_defender_public_cunit_ids": defenders,
    }


class ActualContactScopeStaticContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.abi = load_json(ABI_PATH)
        cls.fixture = load_json(FIXTURE_PATH)

    def test_exact_build_and_production_read_only_boundary(self) -> None:
        self.assertEqual(self.abi["schema_version"], 1)
        self.assertEqual(self.fixture["schema_version"], 1)
        self.assertEqual(self.abi["contract"], self.fixture["contract"])
        self.assertEqual(self.abi["game_version"], "1.19.0.6")
        self.assertEqual(
            self.abi["ck3_exe_sha256"],
            "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86",
        )
        self.assertEqual(
            self.abi["ck3_exe_sha256"], self.fixture["ck3_exe_sha256"]
        )
        self.assertTrue(self.abi["advertised"])
        self.assertTrue(self.abi["production_wired"])
        self.assertFalse(self.abi["live_validated"])
        self.assertTrue(self.fixture["not_live_evidence"])

    def test_daily_queue_inherits_manager_not_province_order(self) -> None:
        source = self.fixture["source_same_day_scheduler"]
        queue: list[int] = []
        commits = source["normal_movement_commits_by_cunit_id"]
        for cunit_id in source["cunit_manager_ids_stored_order"]:
            for commit in commits[str(cunit_id)]:
                if not commit["enqueue_suppressed_raw"]:
                    queue.append(int(commit["native_carmy_id"]))
        expected = self.fixture["expected_projection"]["same_day_scheduler"]
        self.assertEqual(queue, expected["contact_queue_native_carmy_ids"])
        self.assertEqual(
            source["target_province_cunit_ids_after_all_movement"],
            sorted(source["target_province_cunit_ids_after_all_movement"]),
        )
        self.assertEqual(
            source["target_province_cunit_ids_after_all_movement"],
            expected["target_province_cunit_ids"],
        )
        scheduler = self.abi["same_day_scheduler"]
        self.assertEqual(scheduler["daily_rva"], "0x27F9B50")
        self.assertEqual(
            scheduler["normal_movement_enqueue"]["normal_flags_byte0_zero_rva"],
            "0x2247ED9",
        )
        self.assertEqual(
            scheduler["normal_movement_enqueue"]["new_province_add_callsite_rva"],
            "0x224B460",
        )
        self.assertEqual(
            scheduler["province_unit_order"]["unsigned_insertion_range"],
            "0x220BB2D..0x220BB7A",
        )
        self.assertEqual(scheduler["contact_queue"]["tail_append_rva"], "0xA886F0")
        self.assertIn("no sort", scheduler["contact_queue"]["order"])

    def test_existing_scan_retains_last_xor_compatible_combat(self) -> None:
        source = self.fixture["source_join_existing"]
        selected, index, exclusions = select_existing(source)
        self.assertIsNotNone(selected)
        expected = self.fixture["expected_projection"]["join_existing"]
        self.assertEqual(int(selected["combat_id"]), expected["combat_id"])
        self.assertEqual(index, expected["combat_array_index"])
        self.assertEqual(exclusions, expected["loser_exclusion_native_carmy_ids"])
        predicted_side = predict_join_side(source, selected)
        self.assertEqual(predicted_side, expected["predicted_side"])
        current_attacker = [
            int(value) for value in selected["attacker"]["native_carmy_ids"]
        ]
        current_defender = [
            int(value) for value in selected["defender"]["native_carmy_ids"]
        ]
        incoming_id = int(source["incoming"]["native_carmy_id"])
        predicted_attacker = list(current_attacker)
        predicted_defender = list(current_defender)
        target = predicted_attacker if predicted_side == "attacker" else predicted_defender
        if incoming_id not in target:
            target.append(incoming_id)
        self.assertEqual(
            current_attacker, expected["current_attacker_native_carmy_ids"]
        )
        self.assertEqual(
            current_defender, expected["current_defender_native_carmy_ids"]
        )
        self.assertEqual(
            predicted_attacker, expected["predicted_attacker_native_carmy_ids"]
        )
        self.assertEqual(
            predicted_defender, expected["predicted_defender_native_carmy_ids"]
        )
        rule = self.abi["existing_combat_selection"]
        self.assertIn("last compatible", rule["selection"])
        self.assertIn("only by the first-hostile seed scan", rule["loser_exclusion"]["impact_boundary"])

    def test_seed_exclusion_does_not_filter_builder_opponents(self) -> None:
        source = self.fixture["source_create_new"]
        actual = project_new_contact(source)
        expected = self.fixture["expected_projection"]["create_new"]
        self.assertEqual(actual, expected)
        excluded = set(actual["loser_exclusion_native_carmy_ids"])
        opponents = {
            row["native_carmy_id"] for row in actual["ordered_opponents"]
        }
        self.assertIn(2001, excluded)
        self.assertIn(2001, opponents)
        self.assertEqual(actual["defender_seed_public_cunit_id"], 1002)
        self.assertEqual(
            [row["public_cunit_id"] for row in actual["ordered_opponents"]],
            [1001, 1002, 1003, 1004],
        )

    def test_constructor_boolean_is_initiator_defender(self) -> None:
        polarity = self.abi["side_orientation"]["polarity_proof"]
        self.assertIn("defender side1", polarity["true"])
        self.assertIn("attacker side0", polarity["false"])
        self.assertIn("must not be named initiator_is_attacker", polarity["correction"])
        expected = self.fixture["expected_projection"]["create_new"]
        self.assertTrue(expected["initiator_is_defender"])
        self.assertEqual(expected["initiator_side"], "defender")
        self.assertEqual(expected["opponent_side"], "attacker")
        self.assertEqual(
            expected["predicted_attacker_native_carmy_ids"],
            [2001, 2002, 2003, 2004],
        )
        self.assertEqual(expected["predicted_defender_native_carmy_ids"], [2000])

    def test_post_contact_maps_actual_combat_sides_without_sorting(self) -> None:
        source = self.fixture["source_in_combat_observation"]
        actual = project_in_combat_observation(source)
        expected = self.fixture["expected_projection"][
            "in_combat_observation"
        ]
        self.assertEqual(actual, expected)
        self.assertEqual(actual["combat_id"], 7000)
        self.assertEqual(actual["actual_target_province_id"], 902)
        self.assertEqual(
            actual["actual_attacker_public_cunit_ids"], [1002, 1000]
        )
        self.assertEqual(
            actual["actual_defender_public_cunit_ids"], [1001, 1003]
        )
        self.assertIn(
            "value and order",
            self.abi["post_contact_observation"]["reconciliation"],
        )

    def test_stable_layout_and_mutator_boundary(self) -> None:
        layouts = self.abi["layouts"]
        self.assertIn("CUnitID", layouts["CProvince"]["+0x748/+0x754"])
        self.assertIn("CCombatID", layouts["CProvince"]["+0x760/+0x76C"])
        self.assertEqual(layouts["CCombat"]["+0x20"], "attacker CCombatSide")
        self.assertEqual(layouts["CCombat"]["+0x368"], "defender CCombatSide")
        self.assertIn("CArmyID", layouts["CCombatSide"]["+0x10/+0x1C"])
        forbidden = " ".join(self.abi["execution_boundary"]["forbidden_calls"])
        for rva in ("0x23040A0", "0x2209450", "0x27FB7C0"):
            self.assertIn(rva, forbidden)

    def test_static_and_live_readiness_are_evidence_bound(self) -> None:
        abi_readiness = self.abi["readiness"]
        fixture_readiness = self.fixture["expected_projection"]["readiness"]
        self.assertEqual(abi_readiness, fixture_readiness)
        for key in (
            "exact_build_ready",
            "same_day_scheduler_static_ready",
            "province_candidate_order_static_ready",
            "existing_combat_selection_static_ready",
            "new_combat_opponent_order_static_ready",
            "constructor_side_polarity_static_ready",
            "actual_contact_scope_static_ready",
            "post_contact_observation_static_ready",
            "production_query_ready",
            "capability_advertised",
        ):
            self.assertTrue(abi_readiness[key], key)
        for key in (
            "actual_contact_scope_live_ready",
            "actual_contact_scope_ready",
        ):
            self.assertTrue(abi_readiness[key], key)
        live = self.abi["live_acceptance"]
        self.assertEqual(live["predicted_contact_date_raw"], 53178264)
        self.assertEqual(
            live["actual_contact_date_raw"],
            live["predicted_contact_date_raw"],
        )
        self.assertEqual(live["combat_id"], 335544325)
        self.assertEqual(live["attacker_army_ids"], [83886341])
        self.assertEqual(live["defender_army_ids"], [357, 33554657])
        self.assertTrue(live["cold_restore_identity_equal"])
        self.assertTrue(live["combat_v3_available_before_and_after_restore"])
        self.assertTrue(live["managed_cleanup_proven"])
        self.assertTrue(live["baseline_restored"])


if __name__ == "__main__":
    unittest.main()
