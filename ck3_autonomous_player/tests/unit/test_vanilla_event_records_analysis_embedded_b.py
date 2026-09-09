from __future__ import annotations

import json
from pathlib import Path
import re
import sys
import unittest


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))

from xar_autoplayer.vanilla_events.records_analysis_embedded_b import (
    EMBEDDED_B_EVENT_KEYS,
    VANILLA_EMBEDDED_B_ANALYSIS,
)
from xar_autoplayer.vanilla_events.records_embedded import (
    EMBEDDED_VANILLA_TIMELINE_CONTRACTS,
)


SHA256_PATTERN = re.compile(r"^[0-9A-F]{64}$")
SLICE_START = 27
SLICE_STOP = 53


class EmbeddedBAnalysisTests(unittest.TestCase):
    def test_analysis_strictly_covers_embedded_records_28_through_53(self) -> None:
        expected = list(EMBEDDED_VANILLA_TIMELINE_CONTRACTS)[
            SLICE_START:SLICE_STOP
        ]

        self.assertEqual(list(VANILLA_EMBEDDED_B_ANALYSIS), expected)
        self.assertEqual(list(EMBEDDED_B_EVENT_KEYS), expected)
        self.assertEqual(len(VANILLA_EMBEDDED_B_ANALYSIS), 26)

    def test_records_are_json_safe_and_state_the_migration_boundary(self) -> None:
        for expected_order, (event_id, analysis) in enumerate(
            VANILLA_EMBEDDED_B_ANALYSIS.items(), start=28
        ):
            with self.subTest(event_id=event_id):
                self.assertEqual(
                    analysis["exact_build"]["game_version"],
                    "1.19.0.6",
                )
                self.assertRegex(
                    analysis["exact_build"]["ck3_executable_sha256"],
                    SHA256_PATTERN,
                )
                self.assertEqual(
                    analysis["migrated_from"]["module"],
                    "xar_autoplayer.vanilla_events.records_embedded",
                )
                self.assertEqual(
                    analysis["migrated_from"]["default_order_1_based"],
                    expected_order,
                )
                self.assertTrue(analysis["review_summary"])
                self.assertTrue(analysis["existing_boundaries"])
                if event_id == "epidemic_events.5009":
                    self.assertEqual(
                        analysis["migrated_from"]["review_kind"],
                        "exact-build-original-definition-and-live-repeat-review",
                    )
                    self.assertTrue(analysis["source_sha256"])
                    self.assertEqual(
                        analysis["existing_boundaries"][
                            "campaign_specific_binding_fields"
                        ],
                        [],
                    )
                else:
                    self.assertIn(
                        "no new exhaustive vanilla-definition review",
                        analysis["existing_boundaries"]["notes"][0],
                    )
                    self.assertNotIn("source_sha256", analysis)
                json.dumps(analysis, allow_nan=False)

    def test_safe_options_match_the_existing_contracts(self) -> None:
        fail_closed_event = "ep3_interactions_events.0630"

        for event_id, analysis in VANILLA_EMBEDDED_B_ANALYSIS.items():
            contract = EMBEDDED_VANILLA_TIMELINE_CONTRACTS[event_id]
            with self.subTest(event_id=event_id):
                if event_id == fail_closed_event:
                    self.assertIsNone(analysis["safe_option"])
                    self.assertEqual(
                        contract["handling_policy"],
                        "scenario-invalidating-fail-closed",
                    )
                    continue

                safe_option = analysis["safe_option"]
                self.assertEqual(
                    safe_option["selected_option_number"],
                    contract["selected_option_number"],
                )
                self.assertEqual(
                    safe_option["selected_native_option_index"],
                    contract["selected_native_option_index"],
                )
                self.assertTrue(safe_option["rationale"])

    def test_unavoidable_effects_are_not_misrepresented_as_no_ops(self) -> None:
        scheme = VANILLA_EMBEDDED_B_ANALYSIS["hostile_scheme_discovery.2001"]
        puppet = VANILLA_EMBEDDED_B_ANALYSIS[
            "ep3_story_cycle_admin_eunuch.5020"
        ]
        resignation = VANILLA_EMBEDDED_B_ANALYSIS["ep3_interactions_events.0630"]

        self.assertEqual(
            scheme["safe_option"]["classification"],
            "only-authored-route",
        )
        self.assertEqual(
            puppet["safe_option"]["classification"],
            "only-authored-route-with-durable-effect",
        )
        self.assertIsNone(resignation["safe_option"])
        self.assertTrue(
            any(
                "scenario-invalidating-fail-closed" in boundary
                for boundary in resignation["existing_boundaries"]["notes"]
            )
        )

    def test_new_python_files_retain_utf8_bom(self) -> None:
        source = (
            ROOT
            / "ck3_autonomous_player"
            / "src"
            / "xar_autoplayer"
            / "vanilla_events"
            / "records_analysis_embedded_b.py"
        )

        for path in (source, Path(__file__)):
            with self.subTest(path=path.name):
                self.assertTrue(path.read_bytes().startswith(b"\xef\xbb\xbf"))


if __name__ == "__main__":
    unittest.main()
