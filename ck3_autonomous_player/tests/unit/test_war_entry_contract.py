from __future__ import annotations

from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.bridge.war_entry_contract import (
    EXECUTABLE_SHA256,
    MAX_WAR_ENTRY_TARGETS,
    normalize_war_entry_assessments,
    normalize_war_entry_target_ids,
    parse_query_war_entry_assessments_step,
    query_war_entry_assessments_step,
    require_declarable_war_targets,
)


def _assessment(target: int, effective_target: int | None = None) -> dict[str, object]:
    return {
        "target_character_id": target,
        "effective_target_character_id": effective_target or target,
        "distance_raw": 2_500_000,
        "actor_power_base_raw": 55_223,
        "actor_network_contribution_raw": 44_777,
        "actor_power_total_raw": 100_000,
        "target_power_base_raw": 58_468,
        "target_network_contribution_raw": 21_532,
        "target_pre_adjustment_total_raw": 80_000,
        "target_adjustment_delta_raw": 5_000,
        "target_power_total_raw": 85_000,
        "actual_power_ratio_raw": 85_000,
        "target_ai_context_actor_entry_raw": 0,
        "actor_ai_context_target_entry_raw": 1,
        "native_flags_raw": 3,
    }


def _payload(targets: list[int] | None = None) -> dict[str, object]:
    selected = targets or [808]
    return {
        "schema_version": 1,
        "status": "available",
        "snapshot_revision": 17,
        "date_raw": 53_171_400,
        "actor_character_id": 29_829,
        "requested_target_character_ids": selected,
        "assessments": [_assessment(target) for target in selected],
        "readiness": {
            "actor_identity_ready": True,
            "targets_declarable_ready": True,
            "effective_targets_ready": True,
            "ai_context_ready": True,
            "native_output_ready": True,
            "network_decomposition_ready": True,
            "same_frame_ready": True,
            "ready": True,
        },
        "provenance": {
            "game_version": "1.19.0.6",
            "executable_sha256": EXECUTABLE_SHA256,
            "assessment_rva": "0x1878A00",
            "network_collector_rva": "0x1879850",
            "power_leaf": "CCharacter+0x1B8->+0x308",
            "fixed_point_scale": 100_000,
        },
    }


class WarEntryRequestContractTests(unittest.TestCase):
    def test_canonical_literal_round_trips_one_production_target(self) -> None:
        self.assertEqual(MAX_WAR_ENTRY_TARGETS, 1)
        targets = [808]
        step = query_war_entry_assessments_step(targets)

        self.assertEqual(
            step,
            "query-war-entry-assessments-v1-1-808",
        )
        self.assertEqual(parse_query_war_entry_assessments_step(step), targets)

    def test_request_requires_bounded_distinct_full_generation_ids(self) -> None:
        invalid = [
            [],
            [True],
            [0],
            [-1],
            [2**31],
            [808, 42],
            [808, 808],
            list(range(1, MAX_WAR_ENTRY_TARGETS + 2)),
        ]
        for value in invalid:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    normalize_war_entry_target_ids(value)

    def test_parser_rejects_noncanonical_or_ambiguous_literals(self) -> None:
        invalid = [
            "query-war-entry-assessments-v1-0-808",
            "query-war-entry-assessments-v1-1-0808",
            "query-war-entry-assessments-v1-1-0",
            "query-war-entry-assessments-v1-1-808-42",
            "query-war-entry-assessments-v1-2-808-808",
            "query-war-entry-assessments-v1-1-８０８",
            "game.command.query-war-entry-assessments-v1-N",
        ]
        for step in invalid:
            with self.subTest(step=step):
                self.assertIsNone(parse_query_war_entry_assessments_step(step))

    def test_scope_requires_every_target_in_current_declarable_wars(self) -> None:
        snapshot = {
            "declarable_wars": [
                {"target_character_id": 808},
                {"target_character_id": 42},
                {"target_character_id": 808},
            ]
        }
        self.assertEqual(
            require_declarable_war_targets(snapshot, [42]),
            [42],
        )
        with self.assertRaisesRegex(ValueError, "outside current"):
            require_declarable_war_targets(snapshot, [43])


class WarEntryAvailableResultContractTests(unittest.TestCase):
    def test_complete_available_payload_preserves_native_ratio_and_adjustment(self) -> None:
        normalized = normalize_war_entry_assessments(
            _payload(),
            expected_target_character_ids=[808],
            expected_actor_character_id=29_829,
            expected_snapshot_revision=17,
        )

        self.assertEqual(normalized["assessments"][0]["actual_power_ratio_raw"], 85_000)
        self.assertEqual(normalized["assessments"][0]["target_adjustment_delta_raw"], 5_000)
        self.assertTrue(normalized["readiness"]["ready"])

    def test_available_payload_is_all_or_nothing_and_order_bound(self) -> None:
        mutations = []
        missing = _payload()
        del missing["assessments"][0]["native_flags_raw"]
        mutations.append(missing)
        wrong_target = _payload()
        wrong_target["assessments"][0]["target_character_id"] = 42
        mutations.append(wrong_target)
        partial = _payload()
        partial["assessments"].pop()
        mutations.append(partial)
        null_value = _payload()
        null_value["assessments"][0]["actual_power_ratio_raw"] = None
        mutations.append(null_value)
        unreadied = _payload()
        unreadied["readiness"]["same_frame_ready"] = False
        mutations.append(unreadied)
        unavailable = _payload()
        unavailable["status"] = "unavailable"
        mutations.append(unavailable)

        for payload in mutations:
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    normalize_war_entry_assessments(payload)

    def test_power_decompositions_are_checked_without_recomputing_ratio(self) -> None:
        for field in (
            "actor_power_total_raw",
            "target_pre_adjustment_total_raw",
            "target_power_total_raw",
        ):
            payload = _payload()
            payload["assessments"][0][field] += 1
            with self.subTest(field=field):
                with self.assertRaisesRegex(ValueError, "decomposition"):
                    normalize_war_entry_assessments(payload)

        payload = _payload()
        payload["assessments"][0]["actual_power_ratio_raw"] = 77_777
        normalized = normalize_war_entry_assessments(payload)
        self.assertEqual(
            normalized["assessments"][0]["actual_power_ratio_raw"], 77_777
        )

    def test_provenance_and_native_snapshot_revision_are_exact(self) -> None:
        payload = _payload()
        payload["provenance"]["assessment_rva"] = "0x1878A01"
        with self.assertRaisesRegex(ValueError, "provenance"):
            normalize_war_entry_assessments(payload)

        with self.assertRaisesRegex(ValueError, "snapshot revision"):
            normalize_war_entry_assessments(
                _payload(), expected_snapshot_revision=18
            )


if __name__ == "__main__":
    unittest.main()
