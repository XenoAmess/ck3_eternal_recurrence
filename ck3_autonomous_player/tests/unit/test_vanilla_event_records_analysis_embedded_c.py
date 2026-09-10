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
from xar_autoplayer.vanilla_events.records_embedded_c import (
    EMBEDDED_C_VANILLA_OBSERVATIONS,
    EMBEDDED_C_VANILLA_TIMELINE_CONTRACTS,
    _LEGACY_EMBEDDED_C_VANILLA_TIMELINE_CONTRACTS,
)
from xar_autoplayer.vanilla_events.registry import (
    PLAYER_SENTINEL,
    materialize_vanilla_timeline_contract,
)


EXPECTED_KEYS = tuple(EMBEDDED_C_VANILLA_TIMELINE_CONTRACTS)
_LEGACY_BINDING_KEYS = (
    "date_raw",
    "date_raw_range",
    "root_character_id",
    "character_scopes",
    "unique_character_scope_excludes",
)
_CAMPAIGN_IDS = {
    29037,
    31003,
    32904,
    56656,
    16780004,
    36354,
    29575,
    32922,
    27051,
    30987,
}


def _assert_no_campaign_identity(
    testcase: unittest.TestCase,
    value: object,
    *,
    path: str,
) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _assert_no_campaign_identity(
                testcase,
                item,
                path=f"{path}.{key}",
            )
        return
    if isinstance(value, (tuple, list)):
        for index, item in enumerate(value):
            _assert_no_campaign_identity(
                testcase,
                item,
                path=f"{path}[{index}]",
            )
        return
    if type(value) is int:
        testcase.assertNotIn(value, _CAMPAIGN_IDS, path)


def _legacy_binding_fields(contract: dict[str, object]) -> dict[str, object]:
    binding = {
        key: contract[key]
        for key in _LEGACY_BINDING_KEYS
        if key in contract
    }
    for variant_key in ("scope_variants", "option_variants"):
        variants = []
        for index, variant in enumerate(contract.get(variant_key, ())):
            variant_binding = {
                key: variant[key]
                for key in _LEGACY_BINDING_KEYS
                if key in variant
            }
            if variant_binding:
                variants.append({"variant_index": index, **variant_binding})
        if variants:
            binding[f"{variant_key}_bindings"] = tuple(variants)
    return binding


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
                        "source_sha256",
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
                self.assertEqual(len(analysis["source_sha256"]), 1)
                for source_path, source_hash in analysis["source_sha256"].items():
                    self.assertTrue(source_path.startswith("events/"))
                    self.assertEqual(len(source_hash), 64)
                    self.assertEqual(source_hash, source_hash.upper())
                json.dumps(analysis, allow_nan=False)

    def test_safe_options_match_existing_contracts(self) -> None:
        for event_key in EXPECTED_KEYS:
            with self.subTest(event_key=event_key):
                contract = EMBEDDED_C_VANILLA_TIMELINE_CONTRACTS[event_key]
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

    def test_yearly_5050_uses_the_exact_build_definition_source(self) -> None:
        self.assertEqual(
            VANILLA_EMBEDDED_C_ANALYSIS["yearly.5050"]["source_sha256"],
            {
                "events/yearly_events/yearly_events_5.txt": (
                    "BA47BA01C55CF9C7E73F469F9FC1C5F1F439B86AC33EF7C31292B821197F3CC5"
                )
            },
        )

    def test_contracts_are_campaign_neutral_and_build_bound(self) -> None:
        self.assertEqual(
            tuple(_LEGACY_EMBEDDED_C_VANILLA_TIMELINE_CONTRACTS),
            EXPECTED_KEYS,
        )
        for event_key, contract in EMBEDDED_C_VANILLA_TIMELINE_CONTRACTS.items():
            with self.subTest(event_key=event_key):
                self.assertNotIn("date_raw", contract)
                self.assertNotIn("date_raw_range", contract)
                self.assertEqual(
                    contract["date_policy"],
                    "product-observation-window",
                )
                self.assertEqual(contract["root_character_id"], PLAYER_SENTINEL)
                _assert_no_campaign_identity(self, contract, path=event_key)
                json.dumps(contract, allow_nan=False)

    def test_removed_live_bindings_are_verbatim_migration_observations(self) -> None:
        self.assertEqual(set(EMBEDDED_C_VANILLA_OBSERVATIONS), set(EXPECTED_KEYS))
        for event_key, legacy in (
            _LEGACY_EMBEDDED_C_VANILLA_TIMELINE_CONTRACTS.items()
        ):
            with self.subTest(event_key=event_key):
                exemplars = EMBEDDED_C_VANILLA_OBSERVATIONS[event_key][
                    "exemplars"
                ]
                self.assertEqual(len(exemplars), 1)
                exemplar = exemplars[0]
                self.assertEqual(exemplar["run"], "legacy-migrated")
                self.assertEqual(exemplar["kind"], "legacy-live-binding")
                self.assertEqual(exemplar["review_kind"], "migration-only")
                binding = {
                    key: value
                    for key, value in exemplar.items()
                    if key not in {"run", "kind", "review_kind"}
                }
                self.assertEqual(binding, _legacy_binding_fields(legacy))
                json.dumps(exemplar, allow_nan=False)

    def test_numeric_aliases_become_portable_role_relations(self) -> None:
        succession = EMBEDDED_C_VANILLA_TIMELINE_CONTRACTS[
            "ep3_governor_yearly.3060"
        ]
        self.assertEqual(
            succession["character_scopes"],
            {"root_scope": PLAYER_SENTINEL},
        )
        self.assertEqual(
            succession["character_scope_matches_any"],
            {
                "new_holder": ("emperor",),
                "emperor": ("new_holder",),
            },
        )
        self.assertEqual(
            succession["unique_character_scope_excludes"],
            {
                "previous_holder": (PLAYER_SENTINEL,),
                "new_holder": (PLAYER_SENTINEL,),
                "emperor": (PLAYER_SENTINEL,),
            },
        )

        compliment = EMBEDDED_C_VANILLA_TIMELINE_CONTRACTS[
            "sway_ongoing.1002"
        ]
        self.assertEqual(
            compliment["character_scopes"],
            {"owner": PLAYER_SENTINEL},
        )
        self.assertEqual(
            compliment["character_scope_matches_any"],
            {
                "target": ("compliment_receiver",),
                "compliment_receiver": ("target",),
            },
        )

        interaction = EMBEDDED_C_VANILLA_TIMELINE_CONTRACTS[
            "tgp_interaction_event.0016"
        ]
        self.assertEqual(
            interaction["character_scopes"],
            {
                "secondary_recipient": PLAYER_SENTINEL,
                "governor_joining": PLAYER_SENTINEL,
            },
        )
        self.assertIn(
            "actor",
            interaction["character_scope_differs_from"]["recipient"],
        )
        self.assertIn(
            "recipient",
            interaction["character_scope_differs_from"]["actor"],
        )

        materialized = materialize_vanilla_timeline_contract(interaction, 47001)
        self.assertEqual(materialized["root_character_id"], 47001)
        self.assertEqual(
            materialized["character_scopes"],
            {"secondary_recipient": 47001, "governor_joining": 47001},
        )
        self.assertEqual(
            materialized["unique_character_scope_excludes"]["actor"],
            (47001,),
        )

    def test_boundaries_do_not_promote_historical_ids(self) -> None:
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
                self.assertIn("source_sha256", analysis)
                self.assertNotIn("source_hash", analysis)
                json.dumps(boundaries, allow_nan=False)


if __name__ == "__main__":
    unittest.main()
