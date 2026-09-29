"""One paused child result plus current first-heir relationship read."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.first_heir_companion_paused_observer import (
    observe_first_heir_companion_after_child,
)


def frame() -> dict[str, object]:
    return {
        "snapshot_id": 12, "revision": 7, "native_revision": 3,
        "date_raw": 53219928, "episode_run_id": "native-29829-test",
        "episode_character_id": 29829, "played_character_id": 29829,
        "played_character_alive": True, "paused": True, "map_ready": True,
    }


class Driver:
    def __init__(self, relation: dict[str, object]):
        self.relation = relation
        self.revisions: list[int] = []

    def query_current_first_heir_relationship_private_v1(
        self, *, expected_native_revision: int,
    ) -> dict[str, object]:
        self.revisions.append(expected_native_revision)
        return deepcopy(self.relation)


class Service:
    def __init__(self, after: dict[str, object]):
        self.after = after

    def snapshot(self) -> dict[str, object]:
        return deepcopy(self.after)


def relation(*, betrothed: int | None = 38718) -> dict[str, object]:
    return {
        "schema": "xar.ck3.current-first-heir-relationship.v1",
        "status": "available", "native_revision": 3,
        "heir_character_id": 38822, "bilateral_verified": True,
        "betrothed_character_id": betrothed,
        "primary_spouse_character_id": None, "spouse_character_ids": [],
        "read_only": True, "advertised": False,
    }


class FirstHeirCompanionTests(unittest.TestCase):
    def observe(self, driver: Driver, *, after: dict[str, object] | None = None,
                resolved: dict[str, object] | None = None) -> dict[str, object]:
        before = frame()
        if after is None:
            after = {**before, "played_character": {
                "character_id": 29829, "alive": True,
            }}
        if resolved is None:
            resolved = {
                "status": "betrothal", "material_result": True,
                "episode_run_id": "native-29829-test",
                "heir_character_id": 38822,
                "candidate_character_id": 38718,
            }
        return observe_first_heir_companion_after_child(
            driver, Service(after), before=before,
            child_observation={"same_frame": True},
            first_heir_resolved=resolved, turn_index=1,
        )

    def test_existing_native_betrothal_has_no_new_proposal_value(self) -> None:
        driver = Driver(relation())
        observed = self.observe(driver)
        self.assertEqual(driver.revisions, [3])
        self.assertEqual(observed["first_heir_relationship"]["heir_character_id"], 38822)
        self.assertIs(observed["new_proposal_eligible"], False)
        self.assertEqual(observed["new_proposal_value_status"],
                         "existing_partner_no_new_proposal_value")
        self.assertIs(observed["resolved_pair_matches_native"], True)
        self.assertIs(observed["same_frame"], True)

    def test_unpartnered_does_not_claim_final_legality_or_value(self) -> None:
        observed = self.observe(Driver(relation(betrothed=None)))
        self.assertIsNone(observed["new_proposal_eligible"])
        self.assertEqual(observed["new_proposal_value_status"],
                         "unpartnered_requires_final_legality_and_value")
        self.assertIs(observed["resolved_pair_matches_native"], False)

    def test_changed_frame_is_rejected(self) -> None:
        after = {**frame(), "native_revision": 4,
                 "played_character": {"character_id": 29829, "alive": True}}
        with self.assertRaisesRegex(ValueError, "crossed its paused child frame"):
            self.observe(Driver(relation()), after=after)


if __name__ == "__main__":
    unittest.main()
