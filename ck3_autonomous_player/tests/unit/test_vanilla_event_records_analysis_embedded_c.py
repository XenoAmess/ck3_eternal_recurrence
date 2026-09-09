from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))

from xar_autoplayer.vanilla_events.records_analysis_embedded_c import (
    EMBEDDED_C_EVENT_KEYS,
    VANILLA_EMBEDDED_C_ANALYSIS,
)
from xar_autoplayer.vanilla_events.records_embedded import (
    EMBEDDED_VANILLA_TIMELINE_CONTRACTS,
)


EXPECTED_KEYS = tuple(EMBEDDED_VANILLA_TIMELINE_CONTRACTS)[53:79]


class EmbeddedAnalysisCSliceTests(unittest.TestCase):
    def test_inventory_is_exactly_default_slice_54_through_79(self) -> None:
        self.assertEqual(EMBEDDED_C_EVENT_KEYS, EXPECTED_KEYS)
        self.assertEqual(tuple(VANILLA_EMBEDDED_C_ANALYSIS), EXPECTED_KEYS)
        self.assertEqual(len(VANILLA_EMBEDDED_C_ANALYSIS), 26)

    def test_records_are_json_safe_and_preserve_required_provenance(self) -> None:
        for order, event_key in enumerate(EXPECTED_KEYS, start=54):
            with self.subTest(event_key=event_key):
                analysis = VANILLA_EMBEDDED_C_ANALYSIS[event_key]
                self.assertEqual(
                    set(analysis),
                    {
                        "exact_build",
                        "migrated_from",
                        "review_summary",
                        "safe_option",
                        "existing_boundaries",
                    },
                )
                self.assertEqual(analysis["exact_build"]["game_version"], "1.19.0.6")
                self.assertEqual(
                    analysis["exact_build"]["ck3_executable_sha256"],
                    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86",
                )
                self.assertEqual(
                    analysis["migrated_from"]["default_order_1_based"], order
                )
                self.assertTrue(analysis["review_summary"])
                json.dumps(analysis, allow_nan=False)

    def test_safe_options_match_existing_contracts(self) -> None:
        for event_key in EXPECTED_KEYS:
            with self.subTest(event_key=event_key):
                contract = EMBEDDED_VANILLA_TIMELINE_CONTRACTS[event_key]
                safe_option = VANILLA_EMBEDDED_C_ANALYSIS[event_key]["safe_option"]
                self.assertEqual(
                    safe_option["selected_option_number"],
                    contract["selected_option_number"],
                )
                self.assertEqual(
                    safe_option["selected_native_option_index"],
                    contract["selected_native_option_index"],
                )
                self.assertTrue(safe_option["rationale"])

    def test_boundaries_do_not_promote_historical_ids_or_invent_hashes(self) -> None:
        for event_key, analysis in VANILLA_EMBEDDED_C_ANALYSIS.items():
            with self.subTest(event_key=event_key):
                boundaries = analysis["existing_boundaries"]
                self.assertFalse(
                    boundaries[
                        "campaign_identity_values_promoted_to_universal_facts"
                    ]
                )
                self.assertFalse(boundaries["exhaustive_variant_review_claimed"])
                self.assertNotIn("root_character_id", boundaries)
                self.assertNotIn("date_raw", boundaries)
                self.assertNotIn("source_sha256", analysis)
                self.assertNotIn("source_hash", analysis)
                json.dumps(boundaries, allow_nan=False)


if __name__ == "__main__":
    unittest.main()
