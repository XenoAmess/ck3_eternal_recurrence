from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.bridge.prewar_scope_contract import (
    EXECUTABLE_SHA256,
    PREWAR_SCOPE_V1_ADVERTISED,
    normalize_prewar_primary_scope,
    parse_query_prewar_scope_v1_step,
    query_prewar_scope_v1_step,
    require_current_declarable_war,
)


def _payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "contract_stage": "declaration_bound_primary_scope_v1",
        "status": "available_primary_scope",
        "snapshot_revision": 74,
        "date_raw": 53_175_816,
        "declaration_id": "29097-11-0",
        "actor_character_id": 29_829,
        "effective_target_character_id": 29_097,
        "primary_participants": [
            {
                "character_id": 29_829,
                "side": "attacker",
                "source": "declaration_primary_actor",
                "join_certainty": "primary_required",
            },
            {
                "character_id": 29_097,
                "side": "defender",
                "source": "declaration_effective_target",
                "join_certainty": "primary_required",
            },
        ],
        "primary_raised_armies": [
            {
                "army_id": 16_777_217,
                "owner_character_id": 29_829,
                "side": "attacker",
                "current_province_id": 100,
                "route_province_ids": [101, 102],
            },
            {
                "army_id": 33_554_434,
                "owner_character_id": 29_097,
                "side": "defender",
                "current_province_id": None,
                "route_province_ids": [],
            },
        ],
        "readiness": {
            "exact_build_ready": True,
            "primary_participants_ready": True,
            "primary_raised_armies_ready": True,
            "native_join_bounds_ready": False,
            "declaration_objective_provinces_ready": False,
            "contact_geometry_ready": False,
            "native_arrival_timeline_ready": False,
            "combat_v3_prewar_scope_ready": False,
            "war_entry_forecast_inputs_ready": False,
        },
        "provenance": {
            "game_version": "1.19.0.6",
            "executable_sha256": EXECUTABLE_SHA256,
            "unit_storage_slot_rva": "0x570CC80",
            "unit_identity": "CUnit+0x10_full_generation",
            "unit_owner": "CUnit+0x174_full_character_id",
            "current_province": "CUnit+0x20->CProvince+0x10",
            "paused_route": (
                "CUnit+0x38/+0x40/+0x44_pointer_rows:+0x00_ProvinceID"
            ),
            "sample_policy": "two_complete_primary_scope_samples_must_match",
            "unresolved_native_abis": [
                "join_callability_and_acceptance",
                "declaration_title_to_objective_provinces",
                "conditional_contact_entry_selection",
                "route_cost_and_movement_speed_to_arrival_date",
                "same_day_contact_insertion_order",
                "combat_v3_declaration_bound_prewar_admission",
            ],
        },
    }


class PrewarScopeRequestTests(unittest.TestCase):
    def test_literal_round_trips_but_capability_is_not_advertised(self) -> None:
        self.assertFalse(PREWAR_SCOPE_V1_ADVERTISED)
        step = query_prewar_scope_v1_step("29097-11-0")
        self.assertEqual(step, "query-prewar-scope-v1-29097-11-0")
        self.assertEqual(parse_query_prewar_scope_v1_step(step), "29097-11-0")

    def test_literal_rejects_noncanonical_or_out_of_range_ids(self) -> None:
        for step in (
            "query-prewar-scope-v1-029097-11-0",
            "query-prewar-scope-v1-29097-011-0",
            "query-prewar-scope-v1-29097-11--2",
            "query-prewar-scope-v1-0-11-0",
            f"query-prewar-scope-v1-{2**31}-11-0",
        ):
            with self.subTest(step=step):
                self.assertIsNone(parse_query_prewar_scope_v1_step(step))

    def test_current_declaration_is_identity_bound(self) -> None:
        row = {
            "declaration_id": "29097-11-0",
            "target_character_id": 29_097,
        }
        self.assertEqual(
            require_current_declarable_war({"declarable_wars": [row]}, row["declaration_id"]),
            row,
        )
        with self.assertRaisesRegex(ValueError, "absent or ambiguous"):
            require_current_declarable_war({"declarable_wars": []}, row["declaration_id"])


class PrewarScopeResultTests(unittest.TestCase):
    def test_exact_primary_slice_normalizes_without_claiming_forecast(self) -> None:
        normalized = normalize_prewar_primary_scope(
            _payload(),
            expected_declaration_id="29097-11-0",
            expected_actor_character_id=29_829,
            expected_snapshot_revision=74,
        )
        self.assertEqual(
            [row["army_id"] for row in normalized["primary_raised_armies"]],
            [16_777_217, 33_554_434],
        )
        self.assertTrue(normalized["readiness"]["primary_raised_armies_ready"])
        self.assertFalse(normalized["readiness"]["native_join_bounds_ready"])
        self.assertFalse(
            normalized["readiness"]["war_entry_forecast_inputs_ready"]
        )

    def test_owner_side_identity_and_canonical_order_are_strict(self) -> None:
        owner = _payload()
        owner["primary_raised_armies"][0]["owner_character_id"] = 29_097
        order = _payload()
        order["primary_raised_armies"].reverse()
        duplicate = _payload()
        duplicate["primary_raised_armies"][1]["army_id"] = 16_777_217
        for payload in (owner, order, duplicate):
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    normalize_prewar_primary_scope(
                        payload,
                        expected_declaration_id="29097-11-0",
                        expected_actor_character_id=29_829,
                    )

    def test_unresolved_domains_cannot_be_flipped_ready(self) -> None:
        for field in (
            "native_join_bounds_ready",
            "declaration_objective_provinces_ready",
            "contact_geometry_ready",
            "native_arrival_timeline_ready",
            "combat_v3_prewar_scope_ready",
            "war_entry_forecast_inputs_ready",
        ):
            payload = _payload()
            payload["readiness"][field] = True
            with self.subTest(field=field):
                with self.assertRaisesRegex(ValueError, "readiness"):
                    normalize_prewar_primary_scope(
                        payload,
                        expected_declaration_id="29097-11-0",
                        expected_actor_character_id=29_829,
                    )

    def test_null_is_only_legal_for_absent_current_province(self) -> None:
        payload = _payload()
        payload["primary_raised_armies"][0]["route_province_ids"] = [101, None]
        with self.assertRaises(ValueError):
            normalize_prewar_primary_scope(
                payload,
                expected_declaration_id="29097-11-0",
                expected_actor_character_id=29_829,
            )

    def test_payload_is_detached_from_input(self) -> None:
        payload = _payload()
        normalized = normalize_prewar_primary_scope(
            payload,
            expected_declaration_id="29097-11-0",
            expected_actor_character_id=29_829,
        )
        payload["primary_raised_armies"][0]["route_province_ids"].append(999)
        self.assertEqual(
            normalized["primary_raised_armies"][0]["route_province_ids"],
            [101, 102],
        )


if __name__ == "__main__":
    unittest.main()
