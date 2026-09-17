from __future__ import annotations

import json
from pathlib import Path
import re
import sys
import unittest


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))

from xar_autoplayer.vanilla_events import (  # noqa: E402
    DEFAULT_VANILLA_EVENT_ANALYSIS,
    DEFAULT_VANILLA_EVENT_OBSERVATIONS,
)
from xar_autoplayer.vanilla_events.portable_evidence import (  # noqa: E402
    query_vanilla_event_evidence_index_v1,
)
from xar_autoplayer.vanilla_events.records_fervor import (  # noqa: E402
    VANILLA_FERVOR_ANALYSIS,
    VANILLA_FERVOR_OBSERVATIONS,
    VANILLA_FERVOR_TIMELINE_CONTRACTS,
)
from xar_autoplayer.vanilla_events.registry import (  # noqa: E402
    PLAYER_SENTINEL,
    query_vanilla_event_knowledge_v1,
)
from xar_autoplayer.vanilla_events.source_index import (  # noqa: E402
    query_vanilla_event_source_provenance_v1,
)


EVENT_KEY = "fervor.1002"
SHA256_PATTERN = re.compile(r"^[0-9A-F]{64}$")


class Fervor1002EventRecordTests(unittest.TestCase):
    def test_contract_is_portable_repeatable_and_exactly_projected(self) -> None:
        contract = VANILLA_FERVOR_TIMELINE_CONTRACTS[EVENT_KEY]
        self.assertEqual(contract["root_character_id"], PLAYER_SENTINEL)
        self.assertNotIn("date_raw", contract)
        self.assertEqual(
            contract["unique_character_scope_excludes"],
            {"sinful_theocrat": (PLAYER_SENTINEL,)},
        )
        self.assertEqual(contract["saved_scope_count"], 5)
        self.assertEqual(contract["snapshot_option_count"], 3)
        self.assertEqual(contract["native_option_indices"], (0, 1, 2))
        self.assertEqual(contract["selected_option_number"], 3)
        self.assertEqual(contract["selected_native_option_index"], 2)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )

    def test_source_review_keeps_religion_policy_out_of_scope(self) -> None:
        analysis = VANILLA_FERVOR_ANALYSIS[EVENT_KEY]
        self.assertEqual(analysis["definition_lines"], "633-966")
        self.assertEqual(analysis["option_lines"], "901-965")
        self.assertIn("already occurred", analysis["immediate_effect"])
        self.assertIn("1460 days", analysis["repeatability"])
        self.assertIn("no faith", analysis["domain_boundary"])
        self.assertIn("no resource", analysis["safe_option_rationale"])
        self.assertIsNone(analysis["after_effect"])
        self.assertIsNone(analysis["follow_up_event"])
        for digest in analysis["source_sha256"].values():
            self.assertRegex(digest, SHA256_PATTERN)

    def test_r860_ids_remain_observation_only(self) -> None:
        (observation,) = VANILLA_FERVOR_OBSERVATIONS[EVENT_KEY]["exemplars"]
        contract_repr = repr(VANILLA_FERVOR_TIMELINE_CONTRACTS[EVENT_KEY])

        self.assertEqual(observation["run"], "R860")
        self.assertEqual(observation["snapshot_id"], "native:63")
        self.assertEqual(observation["saved_character_ids"]["sinful_theocrat"], 56125)
        self.assertEqual(observation["rendered_native_option_indices"], [0, 1, 2])
        self.assertEqual(observation["selected_native_option_index"], 0)
        self.assertTrue(observation["source_reviewed_option_live_pending"])
        self.assertRegex(observation["formal_report_sha256"], SHA256_PATTERN)
        self.assertRegex(observation["driver_state_sha256"], SHA256_PATTERN)
        for observation_only in (53223216, 31853, 56125):
            self.assertNotIn(str(observation_only), contract_repr)

    def test_registry_source_and_portable_evidence_share_record(self) -> None:
        self.assertIs(
            DEFAULT_VANILLA_EVENT_ANALYSIS[EVENT_KEY],
            VANILLA_FERVOR_ANALYSIS[EVENT_KEY],
        )
        self.assertIs(
            DEFAULT_VANILLA_EVENT_OBSERVATIONS[EVENT_KEY],
            VANILLA_FERVOR_OBSERVATIONS[EVENT_KEY],
        )
        response = query_vanilla_event_knowledge_v1(EVENT_KEY)
        self.assertEqual(response["status"], "available")
        self.assertEqual(response["analysis"]["definition_lines"], "633-966")
        source = query_vanilla_event_source_provenance_v1(EVENT_KEY)
        self.assertEqual(source["status"], "available")
        self.assertEqual(source["definition"]["line"], 633)
        self.assertEqual(
            [row["line"] for row in source["caller_candidates"]],
            [556, 614],
        )
        portable = query_vanilla_event_evidence_index_v1(EVENT_KEY)
        self.assertEqual(portable["status"], "available")
        self.assertIn(
            "source_definition",
            {row["kind"] for row in portable["evidence"]},
        )
        json.dumps(response, allow_nan=False)


if __name__ == "__main__":
    unittest.main()
