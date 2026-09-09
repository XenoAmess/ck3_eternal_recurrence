"""Focused checks for reusable manager-A event analysis metadata."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from xar_autoplayer.vanilla_events.records_analysis_manager_a import (  # noqa: E402
    MANAGER_A_VANILLA_EVENT_ANALYSIS,
)
from xar_autoplayer.vanilla_events.records_manager_a import (  # noqa: E402
    MANAGER_VANILLA_TIMELINE_CONTRACTS_A,
)
from xar_autoplayer.vanilla_events.registry import (  # noqa: E402
    EXACT_CK3_BUILD,
    EXACT_CK3_EXE_SHA256,
)


class ManagerAAnalysisTests(unittest.TestCase):
    def test_exactly_the_35_non_holy_war_contracts_are_migrated(self) -> None:
        expected = set(MANAGER_VANILLA_TIMELINE_CONTRACTS_A) - {
            "great_holy_war.0011"
        }
        self.assertEqual(len(expected), 35)
        self.assertEqual(set(MANAGER_A_VANILLA_EVENT_ANALYSIS), expected)

    def test_records_are_json_safe_and_build_bound_without_source_claims(self) -> None:
        encoded = json.dumps(
            MANAGER_A_VANILLA_EVENT_ANALYSIS,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
        )
        self.assertEqual(json.loads(encoded), MANAGER_A_VANILLA_EVENT_ANALYSIS)
        self.assertNotIn("source_sha256", encoded)

        for record in MANAGER_A_VANILLA_EVENT_ANALYSIS.values():
            self.assertEqual(
                record["exact_build"],
                {
                    "game_version": EXACT_CK3_BUILD,
                    "ck3_executable_sha256": EXACT_CK3_EXE_SHA256,
                },
            )
            self.assertTrue(record["migrated_from"].startswith("tools/zg361_"))
            self.assertTrue(record["review_summary"])
            self.assertEqual(
                record["safe_option"]["basis"], "existing-reviewed-contract"
            )

    def test_default_option_boundaries_match_existing_contracts(self) -> None:
        for event_key, record in MANAGER_A_VANILLA_EVENT_ANALYSIS.items():
            contract = MANAGER_VANILLA_TIMELINE_CONTRACTS_A[event_key]
            boundary = record["option_boundary"]["default"]
            option_count = contract["option_count"]
            expected_indices = list(
                contract.get("native_option_indices", tuple(range(option_count)))
            )
            self.assertEqual(boundary["rendered_option_count"], option_count)
            self.assertEqual(
                boundary["rendered_native_option_indices"], expected_indices
            )
            self.assertEqual(
                record["safe_option"]["default"],
                {
                    "selected_authored_option_number": contract[
                        "selected_option_number"
                    ],
                    "selected_native_option_index": contract[
                        "selected_native_option_index"
                    ],
                },
            )

    def test_scope_boundaries_are_role_based_and_preserve_variants(self) -> None:
        for event_key, record in MANAGER_A_VANILLA_EVENT_ANALYSIS.items():
            contract = MANAGER_VANILLA_TIMELINE_CONTRACTS_A[event_key]
            boundary = record["scope_boundary"]
            self.assertEqual(
                boundary["identity_policy"],
                "role-and-relation-only; campaign-specific numeric identities omitted",
            )
            self.assertEqual(
                len(boundary["variants"]), len(contract.get("scope_variants", ()))
            )
            self.assertNotIn("root_character_id", boundary["default"])
            self.assertNotIn("character_scopes", boundary["default"])


if __name__ == "__main__":
    unittest.main()
