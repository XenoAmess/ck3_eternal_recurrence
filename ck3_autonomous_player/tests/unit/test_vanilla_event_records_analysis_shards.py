from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))

from xar_autoplayer.vanilla_events.records_analysis_vanilla_shards import (  # noqa: E402
    VANILLA_SHARD_ANALYSIS,
    VANILLA_SHARD_OBSERVATIONS,
)
from xar_autoplayer.vanilla_events.records_vanilla_shards import (  # noqa: E402
    VANILLA_SHARD_TIMELINE_CONTRACTS,
)
from xar_autoplayer.vanilla_events.registry import (  # noqa: E402
    EXACT_CK3_BUILD,
    EXACT_CK3_EXE_SHA256,
)


EXPECTED_KEY_COUNT = 20
HASHED_EVENT_KEYS = {
    "tgp_dynastic_cycle.0091",
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
}


class VanillaEventShardAnalysisTests(unittest.TestCase):
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

    def test_only_previously_frozen_source_hashes_are_promoted(self) -> None:
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
