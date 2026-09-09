from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.vanilla_events.records_analysis_manager_b import (  # noqa: E402
    MANAGER_VANILLA_ANALYSIS_B,
)
from xar_autoplayer.vanilla_events.records_manager_b import (  # noqa: E402
    MANAGER_VANILLA_TIMELINE_CONTRACTS_B,
)
from xar_autoplayer.vanilla_events.registry import (  # noqa: E402
    EXACT_CK3_BUILD,
    EXACT_CK3_EXE_SHA256,
)


class VanillaEventAnalysisManagerBTests(unittest.TestCase):
    def test_analysis_covers_exactly_the_21_migrated_contracts(self) -> None:
        self.assertEqual(21, len(MANAGER_VANILLA_ANALYSIS_B))
        self.assertEqual(
            set(MANAGER_VANILLA_TIMELINE_CONTRACTS_B),
            set(MANAGER_VANILLA_ANALYSIS_B),
        )

    def test_every_record_is_json_safe_and_carries_reuse_boundaries(self) -> None:
        projected = json.loads(
            json.dumps(MANAGER_VANILLA_ANALYSIS_B, sort_keys=True)
        )
        self.assertEqual(MANAGER_VANILLA_ANALYSIS_B, projected)

        required = {
            "exact_build",
            "migrated_from",
            "review_basis",
            "review_summary",
            "safe_option",
            "scope_boundary",
            "option_boundary",
        }
        for event_key, analysis in MANAGER_VANILLA_ANALYSIS_B.items():
            with self.subTest(event_key=event_key):
                self.assertEqual(required, set(analysis))
                self.assertEqual(
                    {
                        "game_version": EXACT_CK3_BUILD,
                        "ck3_executable_sha256": EXACT_CK3_EXE_SHA256,
                    },
                    analysis["exact_build"],
                )
                self.assertTrue(analysis["migrated_from"].startswith("tools/"))
                self.assertEqual(
                    "existing-contract-comments-docs-and-focused-tests",
                    analysis["review_basis"],
                )
                self.assertTrue(analysis["review_summary"])
                self.assertTrue(analysis["scope_boundary"])
                self.assertTrue(analysis["option_boundary"])
                self.assertNotIn("source_sha256", analysis)

    def test_preferred_safe_options_remain_compatible_with_contracts(self) -> None:
        for event_key, contract in MANAGER_VANILLA_TIMELINE_CONTRACTS_B.items():
            with self.subTest(event_key=event_key):
                safe = MANAGER_VANILLA_ANALYSIS_B[event_key]["safe_option"]
                self.assertEqual(
                    contract["selected_native_option_index"],
                    safe["preferred_native_option_index"],
                )
                self.assertEqual(
                    contract["selected_option_number"],
                    safe["preferred_option_number"],
                )
                self.assertIn(
                    safe["preferred_native_option_index"],
                    safe["reviewed_safe_native_indices"],
                )
                self.assertTrue(safe["rationale"])

        murder_secret = MANAGER_VANILLA_ANALYSIS_B["spymaster_task.0344"]
        self.assertEqual(
            [0, 1],
            murder_secret["safe_option"]["reviewed_safe_native_indices"],
        )


if __name__ == "__main__":
    unittest.main()
