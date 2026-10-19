"""Geographic direct holdings must stay distinct from the full subrealm."""

from __future__ import annotations

import copy
import unittest

from test_turn_bundle_v1 import PLAYER_ID, _root, _snapshot
from xar_autoplayer.bridge.turn_bundle_contract import _territory_state, build_turn_bundle_v1


class TurnBundleTerritoryV1Tests(unittest.TestCase):
    def test_unavailable_partition_preserves_its_gap_instead_of_an_empty_set(self) -> None:
        for status, reason in (
            ("unavailable", "held_title_partition_unavailable"),
            ("not_applicable", "no_primary_landed_title"),
        ):
            with self.subTest(status=status):
                territory = _territory_state(
                    _root(),
                    {"status": status, "value": None, "unavailable_reason": reason},
                    character_id=PLAYER_ID,
                )
                for name in (
                    "directly_held_geographic_county_title_ids",
                    "direct_counties_to_other_title_heirs",
                ):
                    self.assertEqual(territory[name]["status"], "unavailable")
                    self.assertIsNone(territory[name]["value"])
                    self.assertEqual(territory[name]["unavailable_reason"], reason)

    def test_missing_county_heir_keeps_complete_transfer_set_unknown(self) -> None:
        source = _root()
        source["campaign_root_context"]["held_title_partition"][1]["first_heir_character_id"] = None

        territory = build_turn_bundle_v1(_snapshot(), source)["realm_state"]["value"]["territory"]

        self.assertEqual(
            territory["directly_held_geographic_county_title_ids"]["value"], [91]
        )
        transfer = territory["direct_counties_to_other_title_heirs"]
        self.assertEqual(transfer["status"], "unavailable")
        self.assertIsNone(transfer["value"])
        self.assertEqual(transfer["unavailable_reason"], "held_county_first_heir_unavailable")

    def test_fresh_direct_counties_keep_their_scope_and_source(self) -> None:
        source, snapshot = _root(), _snapshot()
        # A persisted SEM cache is not the source of current geographic state.
        snapshot["succession_table"] = {
            "binding": {"snapshot_id": "native:1", "date_raw": 1},
            "held_title_partition": [{"title": {"title_id": 999, "tier_raw": 2}}],
        }
        original = copy.deepcopy((source, snapshot))

        bundle = build_turn_bundle_v1(snapshot, source)
        realm = bundle["realm_state"]["value"]
        territory = realm["territory"]

        self.assertEqual(realm["domain"]["value"]["size"], 6)
        self.assertEqual(
            territory["directly_held_geographic_county_title_ids"]["value"], [91]
        )
        self.assertEqual(
            territory["direct_counties_to_other_title_heirs"]["value"], [91]
        )
        self.assertEqual(
            territory["source_frame"],
            {**source["binding"], "player_character_id": PLAYER_ID, "query_sequence": 9},
        )
        for name in ("player_subrealm_county_title_ids", "succession_realm_county_loss"):
            self.assertEqual(territory[name]["status"], "unavailable")
            self.assertIsNone(territory[name]["value"])
        self.assertEqual((source, snapshot), original)
        self.assertTrue(bundle["readiness"]["ready"])

    def test_landless_family_county_is_not_geographic_territory(self) -> None:
        source = _root()
        source["campaign_root_context"]["held_title_partition"].append({
            "title": {"title_id": 92, "tier_raw": 2, "tier_key": "county"},
            "first_heir_character_id": 77,
            "capital_province_id": None,
            "primary": False,
            "capital_province_kind": "landless_noble_family_no_province",
            "title_key": "c_fixture_family",
        })

        bundle = build_turn_bundle_v1(_snapshot(), source)
        territory = bundle["realm_state"]["value"]["territory"]

        self.assertEqual(
            territory["directly_held_geographic_county_title_ids"]["value"], [91]
        )
        self.assertEqual(
            territory["direct_counties_to_other_title_heirs"]["value"], [91]
        )
        # The original succession contract still counts this family's title.
        partition = bundle["succession_state"]["value"]["partition"]["value"]
        self.assertEqual(len(partition["titles_to_other_heirs"]), 2)

    def test_legacy_county_without_geography_is_unknown_instead_of_empty(self) -> None:
        source = _root()
        source["campaign_root_context"]["held_title_partition"][1]["capital_province_id"] = None

        territory = build_turn_bundle_v1(_snapshot(), source)["realm_state"]["value"]["territory"]

        for name in (
            "directly_held_geographic_county_title_ids",
            "direct_counties_to_other_title_heirs",
        ):
            self.assertEqual(territory[name]["status"], "unavailable")
            self.assertIsNone(territory[name]["value"])
            self.assertEqual(
                territory[name]["unavailable_reason"], "held_county_geography_unavailable"
            )

    def test_missing_primary_heir_does_not_become_a_safe_transfer_forecast(self) -> None:
        source = _root()
        root = source["campaign_root_context"]
        root["primary_title_succession_character_ids"] = []
        root["held_title_partition"][0]["first_heir_character_id"] = None

        territory = build_turn_bundle_v1(_snapshot(), source)["realm_state"]["value"]["territory"]

        self.assertEqual(
            territory["directly_held_geographic_county_title_ids"]["value"], [91]
        )
        transfer = territory["direct_counties_to_other_title_heirs"]
        self.assertEqual(transfer["status"], "unavailable")
        self.assertEqual(transfer["unavailable_reason"], "primary_title_heir_unavailable")

    def test_successor_uses_current_actor_and_current_geographic_counties(self) -> None:
        source, snapshot = _root(), _snapshot()
        successor = PLAYER_ID + 1
        source["campaign_root_context"]["player_character_id"] = successor
        source["campaign_root_context"]["held_title_partition"][1]["title"]["title_id"] = 95
        snapshot["played_character"]["character_id"] = successor
        snapshot["succession_table"] = {"character_id": PLAYER_ID, "held_county_title_ids": [91]}

        territory = build_turn_bundle_v1(snapshot, source)["realm_state"]["value"]["territory"]

        self.assertEqual(territory["source_frame"]["player_character_id"], successor)
        self.assertEqual(
            territory["directly_held_geographic_county_title_ids"]["value"], [95]
        )

    def test_changed_source_date_is_rejected_and_unavailable_root_stays_empty(self) -> None:
        source = _root()
        source["campaign_root_context"]["date_raw"] -= 1
        with self.assertRaisesRegex(ValueError, "date binding changed"):
            build_turn_bundle_v1(_snapshot(), source)

        unavailable = build_turn_bundle_v1(_snapshot(), _root(available=False))
        self.assertEqual(unavailable["realm_state"]["status"], "unavailable")
        self.assertIsNone(unavailable["realm_state"]["value"])


if __name__ == "__main__":
    unittest.main()
