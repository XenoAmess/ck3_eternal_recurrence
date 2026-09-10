from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))

from xar_autoplayer.vanilla_events import (  # noqa: E402
    DEFAULT_VANILLA_EVENT_OBSERVATIONS,
    query_vanilla_event_knowledge_v1,
)
from xar_autoplayer.vanilla_events.records_analysis_vanilla_shards import (  # noqa: E402
    VANILLA_SHARD_ANALYSIS,
    VANILLA_SHARD_OBSERVATIONS,
)
from xar_autoplayer.vanilla_events.records_vanilla_shards import (  # noqa: E402
    VANILLA_SHARD_LEGACY_LIVE_OBSERVATIONS_A,
    VANILLA_SHARD_LEGACY_LIVE_OBSERVATIONS_B,
    VANILLA_SHARD_TIMELINE_CONTRACTS,
)
from xar_autoplayer.vanilla_events.registry import (  # noqa: E402
    EXACT_CK3_BUILD,
    EXACT_CK3_EXE_SHA256,
    PLAYER_SENTINEL,
    materialize_vanilla_timeline_contract,
)


EXPECTED_KEY_COUNT = 20
HASHED_EVENT_KEYS = {
    "ep2_accolade_events.0300",
    "ep3_story_cycle_admin_eunuch.8010",
    "diarchy.8042",
    "tgp_dynastic_cycle.0091",
    "ep1_flavor.1000",
    "ep3_emperor_yearly.2170",
    "ep3_emperor_yearly.2211",
    "ep3_powerful_families.8012",
    "historical_char_creation_events.1",
    "intrigue_temptation.3020",
    "natural_disaster.8001",
    "natural_disaster.7021",
    "natural_disaster.7031",
    "natural_disaster.6901",
    "travel_danger_events.3002",
    "secrets.0108",
    "secrets.0112",
    "secrets.0122",
    "seduce_outcome.4900",
    "seduce_outcome.3901",
}
PORTABLE_PACKAGE_A_KEYS = {
    "tgp_dynastic_cycle.0091",
    "ep3_emperor_yearly.2170",
    "ep3_emperor_yearly.2211",
    "ep3_powerful_families.8012",
    "historical_char_creation_events.1",
    "intrigue_temptation.3020",
    "natural_disaster.8001",
    "natural_disaster.7021",
    "natural_disaster.6901",
    "travel_danger_events.3002",
}
PORTABLE_PACKAGE_B_KEYS = {
    "ep2_accolade_events.0300",
    "ep3_story_cycle_admin_eunuch.8010",
    "diarchy.8042",
    "ep1_flavor.1000",
    "secrets.0108",
    "secrets.0112",
    "secrets.0122",
    "seduce_outcome.4900",
    "seduce_outcome.3901",
}
PORTABLE_KEYS = set(VANILLA_SHARD_TIMELINE_CONTRACTS)
PACKAGE_A_SAFE_OPTIONS = {
    "tgp_dynastic_cycle.0091": (1, 0),
    "ep3_emperor_yearly.2170": (1, 0),
    "ep3_emperor_yearly.2211": (4, 3),
    "ep3_powerful_families.8012": (2, 1),
    "historical_char_creation_events.1": (3, 2),
    "intrigue_temptation.3020": (2, 1),
    "natural_disaster.8001": (1, 0),
    "natural_disaster.7021": (3, 2),
    "natural_disaster.6901": (1, 0),
    "travel_danger_events.3002": (2, 1),
}
PACKAGE_B_SAFE_OPTIONS = {
    "ep2_accolade_events.0300": (1, 0),
    "ep3_story_cycle_admin_eunuch.8010": (3, 2),
    "diarchy.8042": (1, 0),
    "ep1_flavor.1000": (3, 2),
    "secrets.0108": (1, 0),
    "secrets.0112": (1, 0),
    "secrets.0122": (3, 2),
    "seduce_outcome.4900": (1, 0),
    "seduce_outcome.3901": (1, 0),
}
SAFE_OPTIONS = {**PACKAGE_A_SAFE_OPTIONS, **PACKAGE_B_SAFE_OPTIONS}
SAFE_OPTIONS["natural_disaster.7031"] = (3, 2)


class VanillaEventShardAnalysisTests(unittest.TestCase):
    def test_all_shard_contracts_are_campaign_neutral(self) -> None:
        for event_key in PORTABLE_KEYS:
            with self.subTest(event_key=event_key):
                contract = VANILLA_SHARD_TIMELINE_CONTRACTS[event_key]
                self.assertNotIn("date_raw", contract)
                self.assertEqual(
                    contract["root_character_id"],
                    PLAYER_SENTINEL,
                )
                serialized = json.dumps(contract, allow_nan=False)
                self.assertNotIn("29037", serialized)
                self.assertNotIn("32904", serialized)
                self.assertEqual(
                    (
                        contract["selected_option_number"],
                        contract["selected_native_option_index"],
                    ),
                    SAFE_OPTIONS[event_key],
                )

    def test_package_a_player_relationships_materialize_portably(self) -> None:
        player = 88001
        contracts = VANILLA_SHARD_TIMELINE_CONTRACTS

        prophecy = materialize_vanilla_timeline_contract(
            contracts["ep3_emperor_yearly.2211"], player
        )
        self.assertEqual(prophecy["character_scopes"]["liege"], player)
        self.assertEqual(
            prophecy["unique_character_scope_excludes"]["vassal"],
            (player,),
        )

        family = materialize_vanilla_timeline_contract(
            contracts["ep3_powerful_families.8012"], player
        )
        self.assertEqual(family["character_scopes"]["liege"], player)
        self.assertEqual(
            family["unique_character_scope_excludes"]["generous_family"],
            (player,),
        )

        historical = materialize_vanilla_timeline_contract(
            contracts["historical_char_creation_events.1"], player
        )
        self.assertEqual(
            historical["unique_character_scope_excludes"],
            {
                "historical_character": (player,),
                "major": (player,),
            },
        )

        warning = materialize_vanilla_timeline_contract(
            contracts["natural_disaster.8001"], player
        )
        self.assertEqual(
            warning["character_scopes"],
            {
                "ruler": player,
                "disaster_province_ruler": player,
            },
        )

    def test_package_a_legacy_live_bindings_are_observations(self) -> None:
        self.assertEqual(
            set(VANILLA_SHARD_LEGACY_LIVE_OBSERVATIONS_A),
            PORTABLE_PACKAGE_A_KEYS,
        )
        json.dumps(
            VANILLA_SHARD_LEGACY_LIVE_OBSERVATIONS_A,
            allow_nan=False,
            sort_keys=True,
        )
        for event_key, metadata in (
            VANILLA_SHARD_LEGACY_LIVE_OBSERVATIONS_A.items()
        ):
            with self.subTest(event_key=event_key):
                exemplar = metadata["exemplars"][0]
                self.assertEqual(exemplar["kind"], "legacy-live-binding")
                self.assertIsInstance(exemplar["date_raw"], int)
                self.assertIn(exemplar["root_character_id"], (29037, 32904))
                self.assertEqual(
                    DEFAULT_VANILLA_EVENT_OBSERVATIONS[event_key], metadata
                )

    def test_package_b_legacy_bindings_are_complete_migration_evidence(
        self,
    ) -> None:
        self.assertEqual(
            set(VANILLA_SHARD_LEGACY_LIVE_OBSERVATIONS_B),
            PORTABLE_PACKAGE_B_KEYS,
        )
        json.dumps(
            VANILLA_SHARD_LEGACY_LIVE_OBSERVATIONS_B,
            allow_nan=False,
            sort_keys=True,
        )
        for event_key, metadata in (
            VANILLA_SHARD_LEGACY_LIVE_OBSERVATIONS_B.items()
        ):
            with self.subTest(event_key=event_key):
                exemplar = metadata["exemplars"][0]
                self.assertEqual(exemplar["kind"], "legacy-live-binding")
                self.assertEqual(exemplar["review_kind"], "migration-only")
                self.assertIsInstance(exemplar["date_raw"], int)
                self.assertIn(exemplar["root_character_id"], (29037, 32904))
                self.assertIn("character_scopes", exemplar)
                self.assertIn("unique_character_scope_excludes", exemplar)

    def test_package_b_is_portable_through_mcp_facing_query(self) -> None:
        for event_key in PORTABLE_PACKAGE_B_KEYS:
            with self.subTest(event_key=event_key):
                response = query_vanilla_event_knowledge_v1(event_key)
                self.assertEqual(response["status"], "available")
                self.assertEqual(
                    response["contract"]["root_character_id"],
                    PLAYER_SENTINEL,
                )
                self.assertNotIn("date_raw", response["contract"])
                self.assertTrue(response["analysis"]["source_sha256"])

    def test_analysis_covers_every_migrated_shard(self) -> None:
        self.assertEqual(EXPECTED_KEY_COUNT, len(VANILLA_SHARD_ANALYSIS))
        self.assertEqual(
            set(VANILLA_SHARD_TIMELINE_CONTRACTS),
            set(VANILLA_SHARD_ANALYSIS),
        )

    def test_metadata_is_json_safe_and_preserves_contract_boundaries(self) -> None:
        json.dumps(VANILLA_SHARD_ANALYSIS, ensure_ascii=False, sort_keys=True)

        for event_key, contract in VANILLA_SHARD_TIMELINE_CONTRACTS.items():
            with self.subTest(event_key=event_key):
                analysis = VANILLA_SHARD_ANALYSIS[event_key]
                self.assertEqual(
                    {
                        "game_version": EXACT_CK3_BUILD,
                        "ck3_executable_sha256": EXACT_CK3_EXE_SHA256,
                    },
                    analysis["exact_build"],
                )
                self.assertTrue(str(analysis["migrated_from"]).startswith("tools/"))
                self.assertTrue(str(analysis["review_summary"]).strip())
                self.assertEqual(
                    contract["selected_option_number"],
                    analysis["safe_option_number"],
                )
                self.assertEqual(
                    contract["selected_native_option_index"],
                    analysis["safe_native_option_index"],
                )
                option_boundary = analysis["option_boundary"]
                self.assertEqual(
                    list(contract["native_option_indices"]),
                    option_boundary["native_option_indices"],
                )
                scope_boundary = analysis["scope_boundary"]
                if "saved_scope_count" in contract:
                    self.assertEqual(
                        contract["saved_scope_count"],
                        scope_boundary["saved_scope_count"],
                    )
                else:
                    self.assertNotIn("saved_scope_count", scope_boundary)

    def test_only_frozen_source_hashes_are_promoted(self) -> None:
        actual = {
            event_key
            for event_key, analysis in VANILLA_SHARD_ANALYSIS.items()
            if "source_sha256" in analysis
        }
        self.assertEqual(HASHED_EVENT_KEYS, actual)
        for event_key in actual:
            with self.subTest(event_key=event_key):
                sources = VANILLA_SHARD_ANALYSIS[event_key]["source_sha256"]
                self.assertTrue(sources)
                for digest in sources.values():
                    self.assertRegex(digest, r"^[0-9A-F]{64}$")

    def test_reviewed_variant_shapes_remain_queryable(self) -> None:
        self.assertEqual(
            2,
            len(
                VANILLA_SHARD_ANALYSIS["ep3_emperor_yearly.2211"][
                    "option_boundary"
                ]["variants"]
            ),
        )
        for event_key in (
            "natural_disaster.8001",
            "travel_danger_events.3002",
            "secrets.0108",
            "secrets.0112",
        ):
            with self.subTest(event_key=event_key):
                self.assertIn(
                    "scope_variants",
                    VANILLA_SHARD_ANALYSIS[event_key]["scope_boundary"],
                )

    def test_r374_red_observation_is_json_safe_and_separate(self) -> None:
        json.dumps(VANILLA_SHARD_OBSERVATIONS, allow_nan=False)
        self.assertEqual(set(VANILLA_SHARD_OBSERVATIONS), {
            "natural_disaster.7031"
        })
        exemplar = VANILLA_SHARD_OBSERVATIONS[
            "natural_disaster.7031"
        ]["exemplars"][0]
        self.assertEqual(exemplar["run"], "R374")
        self.assertEqual(exemplar["saved_scope_raw_types"], {
            "situation": 60,
            "situation_sub_region": 62,
            "epicenter_county": 5,
            "river_region": 54,
        })
        self.assertEqual(exemplar["rendered_native_option_indices"], [0, 2])
        self.assertFalse(exemplar["selection_attempted"])
        for field in (
            "artifact_sha256",
            "park_artifact_sha256",
            "driver_state_artifact_sha256",
        ):
            self.assertRegex(exemplar[field], r"^[0-9A-F]{64}$")


if __name__ == "__main__":
    unittest.main()
