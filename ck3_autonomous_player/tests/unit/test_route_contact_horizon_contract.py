from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.war_contract import (
    QUERY_ROUTE_CONTACT_HORIZON_CAPABILITY,
    advance_route_contact_horizon_step,
    committed_route_sentinel_advance_step,
    is_life_advance_step,
    is_native_war_step,
    normalize_route_contact_horizon,
    parse_advance_route_contact_horizon_step,
    parse_committed_route_sentinel_advance_speed,
    parse_committed_route_sentinel_advance_step,
    parse_query_route_contact_horizon_step,
    query_route_contact_horizon_step,
    stationary_province_contact_free_in_horizon,
    unavoidable_current_province_contact_in_horizon,
)
from xar_autoplayer.bridge.native_driver import _action_steps


def _payload(*, contact_free: bool = True) -> dict[str, object]:
    conflicts: list[dict[str, object]] = []
    if not contact_free:
        conflicts.append(
            {
                "kind": "same_province",
                "hostile_army_id": 31,
                "province_id": 2604,
                "overlap_start_date_raw": 53_176_200,
                "overlap_end_date_raw": 53_176_200,
            }
        )
    return {
        "status": "available",
        "date_raw": 53_176_176,
        "snapshot_revision": 2**32 + 7,
        "subject_army_id": 11,
        "target_province_id": 2585,
        "hostile_army_ids": [31, 41],
        "subject_route": {
            "timeline_observable": True,
            "army_id": 11,
            "current_province_id": 2603,
            "effective_origin_province_id": 2604,
            "route_province_ids": [2604, 2595, 2585],
            "arrival_date_raws": [53_176_200, 53_176_248, 53_176_296],
        },
        "hostile_routes": [
            {
                "timeline_observable": True,
                "army_id": 31,
                "current_province_id": 2583,
                "effective_origin_province_id": 2583,
                "route_province_ids": [2594, 2599, 2604],
                "arrival_date_raws": [53_176_224, 53_176_272, 53_176_320],
            },
            {
                "timeline_observable": True,
                "army_id": 41,
                "current_province_id": 2582,
                "effective_origin_province_id": 2582,
                "route_province_ids": [],
                "arrival_date_raws": [],
            },
        ],
        "horizon_start_date_raw": 53_176_176,
        "horizon_end_date_raw": 53_176_200,
        "one_day_contact_free": contact_free,
        "conflicts": conflicts,
    }


class RouteContactHorizonContractTests(unittest.TestCase):
    def test_committed_route_sentinel_step_binds_subject_target_and_date(
        self,
    ) -> None:
        step = committed_route_sentinel_advance_step(
            201_326_874, 2635, 53_257_080
        )
        self.assertEqual(
            step,
            "committed-route-sentinel-advance-army-201326874-"
            "to-2635-until-53257080",
        )
        self.assertEqual(
            parse_committed_route_sentinel_advance_step(step),
            (201_326_874, 2635, 53_257_080),
        )
        self.assertEqual(
            parse_committed_route_sentinel_advance_speed(step), 3
        )
        self.assertTrue(is_life_advance_step(step))
        for malformed in (
            "committed-route-sentinel-advance-army-0-to-2635-until-53257080",
            "committed-route-sentinel-advance-army-11-to-0-until-53257080",
            "committed-route-sentinel-advance-army-11-to-2635-until-0",
            "committed-route-sentinel-advance-army-11-to-2635-until-053257080",
            "committed-route-sentinel-advance-army-11-to-2635",
            "committed-route-sentinel-advance-army-11-to-2635-until-53257080-speed-3",
            "committed-route-sentinel-advance-army-11-to-2635-until-53257080-speed-6",
        ):
            with self.subTest(malformed=malformed):
                self.assertIsNone(
                    parse_committed_route_sentinel_advance_step(malformed)
                )

    def test_committed_route_sentinel_explicitly_binds_ab_speed(self) -> None:
        for speed in (1, 2, 4, 5):
            with self.subTest(speed=speed):
                step = committed_route_sentinel_advance_step(
                    201_326_874,
                    2635,
                    53_257_080,
                    timeline_speed=speed,
                )
                self.assertTrue(step.endswith(f"-speed-{speed}"))
                self.assertEqual(
                    parse_committed_route_sentinel_advance_step(step),
                    (201_326_874, 2635, 53_257_080),
                )
                self.assertEqual(
                    parse_committed_route_sentinel_advance_speed(step), speed
                )
                self.assertTrue(is_life_advance_step(step))

        for speed in (0, 6, True):
            with self.subTest(speed=speed):
                with self.assertRaises(ValueError):
                    committed_route_sentinel_advance_step(
                        201_326_874,
                        2635,
                        53_257_080,
                        timeline_speed=speed,
                    )

    def test_step_is_canonical_sorted_and_generation_bound(self) -> None:
        step = query_route_contact_horizon_step(11, 2585, [41, 31, 41])
        self.assertEqual(
            step,
            "query-route-contact-horizon-v1-11-to-2585-h-2-31-41",
        )
        self.assertEqual(
            parse_query_route_contact_horizon_step(step),
            (11, 2585, (31, 41)),
        )
        self.assertTrue(is_native_war_step(step))
        self.assertEqual(
            QUERY_ROUTE_CONTACT_HORIZON_CAPABILITY,
            "game.command.query-route-contact-horizon-v1-N",
        )
        advance = advance_route_contact_horizon_step(11, 2585, [41, 31])
        self.assertEqual(
            advance,
            "advance-route-contact-horizon-v1-11-to-2585-h-2-31-41",
        )
        self.assertEqual(
            parse_advance_route_contact_horizon_step(advance),
            (11, 2585, (31, 41)),
        )

    def test_parser_rejects_incomplete_or_noncanonical_scope(self) -> None:
        self.assertIsNone(
            parse_query_route_contact_horizon_step(
                "query-route-contact-horizon-v1-11-to-2585-h-2-31"
            )
        )
        self.assertIsNone(
            parse_query_route_contact_horizon_step(
                "query-route-contact-horizon-v1-11-to-2585-h-2-41-31"
            )
        )
        with self.assertRaises(ValueError):
            query_route_contact_horizon_step(11, 2585, [])

    def test_available_timeline_is_revision_bound_and_parallel(self) -> None:
        normalized = normalize_route_contact_horizon(
            _payload(),
            expected_subject_army_id=11,
            expected_target_province_id=2585,
            expected_hostile_army_ids=(31, 41),
            expected_date_raw=53_176_176,
            expected_snapshot_revision=2**32 + 7,
        )
        self.assertTrue(normalized["one_day_contact_free"])
        self.assertEqual(
            normalized["subject_route"]["arrival_date_raws"],
            [53_176_200, 53_176_248, 53_176_296],
        )

    def test_stationary_subject_uses_empty_current_province_timeline(
        self,
    ) -> None:
        payload = _payload()
        payload["target_province_id"] = 2603
        payload["subject_route"] = {
            "timeline_observable": True,
            "army_id": 11,
            "current_province_id": 2603,
            "effective_origin_province_id": 2603,
            "route_province_ids": [],
            "arrival_date_raws": [],
        }

        normalized = normalize_route_contact_horizon(
            payload,
            expected_subject_army_id=11,
            expected_target_province_id=2603,
            expected_hostile_army_ids=(31, 41),
            expected_date_raw=53_176_176,
            expected_snapshot_revision=2**32 + 7,
        )

        self.assertEqual(normalized["subject_route"]["route_province_ids"], [])
        self.assertTrue(normalized["one_day_contact_free"])

    def test_hostile_timelines_project_stationary_closed_window(self) -> None:
        normalized = normalize_route_contact_horizon(
            _payload(),
            expected_subject_army_id=11,
            expected_target_province_id=2585,
            expected_hostile_army_ids=(31, 41),
            expected_date_raw=53_176_176,
            expected_snapshot_revision=2**32 + 7,
        )

        self.assertTrue(
            stationary_province_contact_free_in_horizon(normalized, 2594)
        )
        normalized["hostile_routes"][0]["arrival_date_raws"][0] = 53_176_200
        self.assertFalse(
            stationary_province_contact_free_in_horizon(normalized, 2594)
        )

    def test_hostile_current_province_blocks_stationary_projection(self) -> None:
        normalized = normalize_route_contact_horizon(
            _payload(),
            expected_subject_army_id=11,
            expected_target_province_id=2585,
            expected_hostile_army_ids=(31, 41),
            expected_date_raw=53_176_176,
            expected_snapshot_revision=2**32 + 7,
        )

        self.assertFalse(
            stationary_province_contact_free_in_horizon(normalized, 2583)
        )

    def test_timeline_rejects_null_or_misaligned_arrivals(self) -> None:
        for arrivals in ([53_176_200, None, 53_176_296], [53_176_200]):
            payload = copy.deepcopy(_payload())
            payload["subject_route"]["arrival_date_raws"] = arrivals
            with self.assertRaises(ValueError):
                normalize_route_contact_horizon(
                    payload,
                    expected_subject_army_id=11,
                    expected_target_province_id=2585,
                    expected_hostile_army_ids=(31, 41),
                    expected_date_raw=53_176_176,
                    expected_snapshot_revision=2**32 + 7,
                )

    def test_contact_boolean_requires_matching_conflict_evidence(self) -> None:
        payload = _payload(contact_free=False)
        normalized = normalize_route_contact_horizon(
            payload,
            expected_subject_army_id=11,
            expected_target_province_id=2585,
            expected_hostile_army_ids=(31, 41),
            expected_date_raw=53_176_176,
            expected_snapshot_revision=2**32 + 7,
        )
        self.assertFalse(normalized["one_day_contact_free"])
        payload["conflicts"] = []
        with self.assertRaises(ValueError):
            normalize_route_contact_horizon(
                payload,
                expected_subject_army_id=11,
                expected_target_province_id=2585,
                expected_hostile_army_ids=(31, 41),
                expected_date_raw=53_176_176,
                expected_snapshot_revision=2**32 + 7,
            )

    def test_unavoidable_contact_requires_current_province_and_late_departure(
        self,
    ) -> None:
        payload = _payload(contact_free=False)
        payload["subject_route"]["arrival_date_raws"] = [
            53_176_440,
            53_176_488,
            53_176_536,
        ]
        payload["conflicts"][0]["province_id"] = 2603
        normalized = normalize_route_contact_horizon(
            payload,
            expected_subject_army_id=11,
            expected_target_province_id=2585,
            expected_hostile_army_ids=(31, 41),
            expected_date_raw=53_176_176,
            expected_snapshot_revision=2**32 + 7,
        )
        self.assertTrue(
            unavoidable_current_province_contact_in_horizon(normalized)
        )

        early_departure = copy.deepcopy(normalized)
        early_departure["subject_route"]["arrival_date_raws"][0] = (
            early_departure["horizon_end_date_raw"]
        )
        self.assertFalse(
            unavoidable_current_province_contact_in_horizon(early_departure)
        )

        other_province = copy.deepcopy(normalized)
        other_province["conflicts"][0]["province_id"] = 2604
        self.assertFalse(
            unavoidable_current_province_contact_in_horizon(other_province)
        )

        mixed_conflict = copy.deepcopy(normalized)
        mixed_conflict["conflicts"].append(
            {
                "kind": "opposing_edge",
                "hostile_army_id": 31,
                "subject_from_province_id": 2603,
                "subject_to_province_id": 2604,
                "hostile_from_province_id": 2604,
                "hostile_to_province_id": 2603,
                "overlap_start_date_raw": 53_176_200,
                "overlap_end_date_raw": 53_176_200,
            }
        )
        self.assertFalse(
            unavoidable_current_province_contact_in_horizon(mixed_conflict)
        )

        stationary = copy.deepcopy(normalized)
        stationary["target_province_id"] = 2603
        stationary["subject_route"].update(
            {
                "effective_origin_province_id": 2603,
                "route_province_ids": [],
                "arrival_date_raws": [],
            }
        )
        stationary["conflicts"][0]["province_id"] = 2603
        self.assertTrue(
            unavoidable_current_province_contact_in_horizon(stationary)
        )

        stationary_wrong_target = copy.deepcopy(stationary)
        stationary_wrong_target["target_province_id"] = 2585
        self.assertFalse(
            unavoidable_current_province_contact_in_horizon(
                stationary_wrong_target
            )
        )

    def test_driver_expands_only_complete_nonretreating_hostile_scope(self) -> None:
        player = {
            "army_id": 11,
            "current_province_id": 2603,
            "controllable": True,
        }
        war = {
            "war_id": 88,
            "war_objective_province_ids": [2585],
            "enemy_armies": [
                {"army_id": 41, "current_province_id": 2582},
                {
                    "army_id": 31,
                    "current_province_id": 2583,
                    "retreating": False,
                },
                {
                    "army_id": 51,
                    "current_province_id": 2584,
                    "retreating": True,
                },
            ],
        }
        steps = _action_steps(
            [
                QUERY_ROUTE_CONTACT_HORIZON_CAPABILITY,
                "game.state.war-objectives",
            ],
            active_wars=[war],
            player_armies=[player],
            paused=True,
        )
        self.assertIn(
            "query-route-contact-horizon-v1-11-to-2585-h-2-31-41",
            steps,
        )
        self.assertFalse(any("-51" in step for step in steps))


if __name__ == "__main__":
    unittest.main()
