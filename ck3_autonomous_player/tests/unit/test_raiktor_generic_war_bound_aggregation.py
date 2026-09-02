from __future__ import annotations

import copy
import unittest

from test_raiktor_war_bound_regiment_contract import _active
from test_war_termination_terms_contract import (
    WAR_ID,
    _available_raiktor_observed_terms,
)
from xar_autoplayer.bridge.raiktor_surrender_public_aggregate import (
    project_raiktor_surrender_six_domain,
)
from xar_autoplayer.bridge.war_contract import normalize_war_termination_terms


ATTACKER_ID = 29_829
DEFENDER_ID = 41_002


def _snapshot() -> dict[str, object]:
    return {
        "snapshot_id": "native:7",
        "revision": 91,
        "native_revision": 7,
        "date_raw": 53_175_816,
        "paused": True,
        "episode_run_id": "native-29829-fixture",
        "episode_character_id": ATTACKER_ID,
        "played_character": {
            "character_id": ATTACKER_ID,
            "alive": True,
        },
        "diagnostics": {
            "connection_generation": 12,
            "bridge_pid": 1003,
        },
        "active_wars": [
            {
                "war_id": WAR_ID,
                "player_side": "attacker",
                "player_is_primary_war_leader": True,
                "primary_opponent_character_id": DEFENDER_ID,
            }
        ],
    }


def _war_bound() -> dict[str, object]:
    value = _active()
    value["war_id"] = WAR_ID
    value["active_frame"]["war_id"] = WAR_ID
    value["active_frame"][
        "active_casus_belli_database_index"
    ] = 409
    value["active_frame"][
        "primary_defender_character_id"
    ] = DEFENDER_ID
    for regiment in value["regiments"]:
        regiment["bound_war_id"] = WAR_ID
    return value


def _project(war_bound: object) -> dict[str, object]:
    terms = normalize_war_termination_terms(
        _available_raiktor_observed_terms(), expected_war_id=WAR_ID
    )
    aggregate = project_raiktor_surrender_six_domain(
        _snapshot(),
        terms,
        generic_war_bound_current_value=war_bound,
    )
    if not isinstance(aggregate, dict):
        raise AssertionError("expected a typed six-domain aggregate")
    return aggregate


class RaiktorGenericWarBoundAggregationTests(unittest.TestCase):
    def test_strict_payload_promotes_only_generic_current_domain(self) -> None:
        aggregate = _project(_war_bound())

        self.assertEqual(aggregate["status"], "incomplete")
        self.assertEqual(aggregate["missing_domains"], ["truce"])
        domain = aggregate["domains"]["generic_war_bound_current"]
        self.assertTrue(domain["available"])
        self.assertEqual(
            domain["payload"]["soldiers"]["observed_current_soldiers"],
            180,
        )
        self.assertTrue(
            aggregate["readiness"]["generic_war_bound_current_ready"]
        )
        self.assertFalse(
            aggregate["readiness"]["source_specific_war_bound_ready"]
        )
        self.assertFalse(aggregate["readiness"]["pre_soldiers_ready"])
        self.assertFalse(
            aggregate["readiness"]["proven_soldier_loss_ready"]
        )
        self.assertFalse(aggregate["readiness"]["action_terms_ready"])
        self.assertFalse(
            aggregate["readiness"]["automatic_surrender_ready"]
        )

    def test_missing_or_malformed_payload_remains_typed_unavailable(self) -> None:
        malformed = _war_bound()
        malformed["soldiers"]["observed_current_soldiers"] = 3_000
        for value in (None, {}, malformed):
            with self.subTest(value=value):
                aggregate = _project(value)
                self.assertEqual(
                    aggregate["domains"]["generic_war_bound_current"],
                    {"available": False},
                )
                self.assertIn(
                    "generic_war_bound_current",
                    aggregate["missing_domains"],
                )
                self.assertFalse(
                    aggregate["readiness"][
                        "generic_war_bound_current_ready"
                    ]
                )
                self.assertFalse(
                    aggregate["readiness"]["action_terms_ready"]
                )
                self.assertFalse(
                    aggregate["readiness"]["automatic_surrender_ready"]
                )

    def test_frame_identity_or_cb_index_drift_remains_unavailable(self) -> None:
        mutations = (
            lambda value: value["active_frame"].__setitem__(
                "snapshot_revision", 92
            ),
            lambda value: value["active_frame"].__setitem__(
                "native_revision", 8
            ),
            lambda value: value["active_frame"].__setitem__(
                "date_raw", 53_175_817
            ),
            lambda value: value["active_frame"].__setitem__(
                "war_id", WAR_ID + 1
            ),
            lambda value: value["active_frame"].__setitem__(
                "primary_defender_character_id", DEFENDER_ID + 1
            ),
            lambda value: value["active_frame"].__setitem__(
                "active_casus_belli_database_index", 412
            ),
        )
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                value = _war_bound()
                mutate(value)
                aggregate = _project(value)
                self.assertEqual(
                    aggregate["domains"]["generic_war_bound_current"],
                    {"available": False},
                )
                self.assertFalse(
                    aggregate["readiness"][
                        "generic_war_bound_current_ready"
                    ]
                )

    def test_input_and_public_terms_readiness_are_not_mutated(self) -> None:
        snapshot = _snapshot()
        war_bound = _war_bound()
        terms = normalize_war_termination_terms(
            _available_raiktor_observed_terms(), expected_war_id=WAR_ID
        )
        snapshot_before = copy.deepcopy(snapshot)
        war_bound_before = copy.deepcopy(war_bound)
        readiness_before = copy.deepcopy(terms["readiness"])

        aggregate = project_raiktor_surrender_six_domain(
            snapshot,
            terms,
            generic_war_bound_current_value=war_bound,
        )

        self.assertIsInstance(aggregate, dict)
        self.assertEqual(snapshot, snapshot_before)
        self.assertEqual(war_bound, war_bound_before)
        self.assertEqual(terms["readiness"], readiness_before)
        self.assertFalse(terms["readiness"]["decision_ready"])
        self.assertFalse(terms["readiness"]["automatic_surrender_ready"])
        self.assertFalse(terms["readiness"]["ready"])


if __name__ == "__main__":
    unittest.main()
