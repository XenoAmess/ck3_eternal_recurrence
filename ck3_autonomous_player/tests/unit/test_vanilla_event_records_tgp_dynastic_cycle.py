from __future__ import annotations

import json
from pathlib import Path
import re
import sys
import unittest


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))

from xar_autoplayer.vanilla_events.records_tgp_dynastic_cycle import (  # noqa: E402
    PLAYER_SENTINEL,
    VANILLA_TGP_DYNASTIC_CYCLE_ANALYSIS,
    VANILLA_TGP_DYNASTIC_CYCLE_OBSERVATIONS,
    VANILLA_TGP_DYNASTIC_CYCLE_TIMELINE_CONTRACTS,
)
from xar_autoplayer.vanilla_events.registry import (  # noqa: E402
    materialize_vanilla_timeline_contract,
    query_vanilla_event_knowledge_v1,
)


EVENT_KEY = "tgp_dynastic_cycle_events.0020"
SHA256_PATTERN = re.compile(r"^[0-9A-F]{64}$")


class TgpDynasticCycleEventRecordTests(unittest.TestCase):
    def test_contract_is_portable_and_selects_non_resource_route(self) -> None:
        contract = VANILLA_TGP_DYNASTIC_CYCLE_TIMELINE_CONTRACTS[EVENT_KEY]

        self.assertEqual(contract["root_character_id"], PLAYER_SENTINEL)
        self.assertNotIn("date_raw", contract)
        self.assertEqual(
            contract["saved_scope_name_sets"],
            (("my_situation", "my_movement", "marshal", "peasant_county"),),
        )
        self.assertEqual(contract["snapshot_option_count"], 3)
        self.assertEqual(contract["native_option_indices"], (1, 2))
        self.assertEqual(contract["selected_option_number"], 3)
        self.assertEqual(contract["selected_native_option_index"], 2)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )
        self.assertEqual(
            [variant["native_option_indices"] for variant in contract["option_variants"]],
            [(1, 2), (0, 1, 2)],
        )
        self.assertEqual(
            contract["scope_variants"][0]["saved_scope_names"],
            ("my_situation", "marshal", "peasant_county"),
        )

        materialized = materialize_vanilla_timeline_contract(contract, 32904)
        self.assertEqual(materialized["root_character_id"], 32904)
        self.assertEqual(
            materialized["unique_character_scope_excludes"],
            {"marshal": (32904,)},
        )
        self.assertEqual(contract["root_character_id"], PLAYER_SENTINEL)

    def test_exact_build_analysis_and_live_observation_are_separate(self) -> None:
        analysis = VANILLA_TGP_DYNASTIC_CYCLE_ANALYSIS[EVENT_KEY]
        exemplar, = VANILLA_TGP_DYNASTIC_CYCLE_OBSERVATIONS[EVENT_KEY][
            "exemplars"
        ]
        contract = VANILLA_TGP_DYNASTIC_CYCLE_TIMELINE_CONTRACTS[EVENT_KEY]

        self.assertEqual(analysis["exact_build"]["game_version"], "1.19.0.6")
        self.assertIn("ten years", analysis["caller_semantics"])
        self.assertIn("treasury-or-gold", analysis["safe_option_rationale"])
        for digest in analysis["source_sha256"].values():
            self.assertRegex(digest, SHA256_PATTERN)
        self.assertEqual(exemplar["event_instance_id"], 777)
        self.assertEqual(exemplar["date_raw"], 53450184)
        self.assertEqual(exemplar["saved_character_ids"], {"marshal": 36528})
        self.assertEqual(exemplar["rendered_native_option_indices"], [1, 2])
        self.assertFalse(exemplar["selection_attempted"])
        self.assertRegex(exemplar["artifact_sha256"], SHA256_PATTERN)

        contract_repr = repr(contract)
        for observation_only in (777, 53450184, 32904, 36528):
            self.assertNotIn(str(observation_only), contract_repr)

    def test_default_mcp_query_returns_detached_complete_record(self) -> None:
        response = query_vanilla_event_knowledge_v1(EVENT_KEY)

        self.assertEqual(response["status"], "available")
        self.assertEqual(response["contract"]["native_option_indices"], [1, 2])
        self.assertEqual(
            response["analysis"]["option_semantics"]["2"],
            (
                "no scripted gameplay effect beyond the declared lazy/diligent "
                "stress impact"
            ),
        )
        self.assertEqual(
            response["observations"]["exemplars"][0]["event_instance_id"],
            777,
        )
        json.dumps(response, allow_nan=False)

        response["contract"]["native_option_indices"].append(99)
        fresh = query_vanilla_event_knowledge_v1(EVENT_KEY)
        self.assertEqual(fresh["contract"]["native_option_indices"], [1, 2])


if __name__ == "__main__":
    unittest.main()
