"""Focused portability tests for embedded vanilla-event shard A."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))

from xar_autoplayer.vanilla_events import records_embedded_a as records  # noqa: E402
from xar_autoplayer.vanilla_events.registry import (  # noqa: E402
    PLAYER_SENTINEL,
    materialize_vanilla_timeline_contract,
)


_LEGACY_BINDING_KEYS = (
    "date_raw",
    "date_raw_range",
    "root_character_id",
    "character_scopes",
    "unique_character_scope_excludes",
)


def _without_campaign_bindings(value: object) -> object:
    if isinstance(value, dict):
        return {
            key: _without_campaign_bindings(item)
            for key, item in value.items()
            if key not in _LEGACY_BINDING_KEYS
        }
    if isinstance(value, tuple):
        return tuple(_without_campaign_bindings(item) for item in value)
    if isinstance(value, list):
        return [_without_campaign_bindings(item) for item in value]
    return value


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


def _assert_portable_bindings(testcase: unittest.TestCase, value: object) -> None:
    if isinstance(value, dict):
        testcase.assertNotIn("date_raw", value)
        testcase.assertNotIn("date_raw_range", value)
        if "root_character_id" in value:
            testcase.assertEqual(value["root_character_id"], PLAYER_SENTINEL)
        if "character_scopes" in value:
            testcase.assertTrue(
                all(
                    character_id == PLAYER_SENTINEL
                    for character_id in value["character_scopes"].values()
                )
            )
        if "unique_character_scope_excludes" in value:
            testcase.assertTrue(
                all(
                    character_id == PLAYER_SENTINEL
                    for excluded in value[
                        "unique_character_scope_excludes"
                    ].values()
                    for character_id in excluded
                )
            )
        for item in value.values():
            _assert_portable_bindings(testcase, item)
    elif isinstance(value, (tuple, list)):
        for item in value:
            _assert_portable_bindings(testcase, item)


class EmbeddedAVanillaTimelineContractsTests(unittest.TestCase):
    def test_public_exports_are_exact(self) -> None:
        self.assertEqual(
            ["EMBEDDED_A_VANILLA_TIMELINE_CONTRACTS"],
            records.__all__,
        )
        self.assertIsInstance(records.EMBEDDED_A_VANILLA_OBSERVATIONS, dict)

    def test_all_28_contracts_are_campaign_neutral(self) -> None:
        legacy = records._LEGACY_EMBEDDED_A_VANILLA_TIMELINE_CONTRACTS
        portable = records.EMBEDDED_A_VANILLA_TIMELINE_CONTRACTS
        self.assertEqual(len(portable), 28)
        self.assertEqual(tuple(portable), tuple(legacy))

        for event_key, contract in portable.items():
            with self.subTest(event=event_key):
                self.assertEqual(
                    contract["date_policy"],
                    "product-observation-window",
                )
                _assert_portable_bindings(self, contract)

                legacy_semantics = _without_campaign_bindings(
                    legacy[event_key]
                )
                self.assertIsInstance(legacy_semantics, dict)
                legacy_semantics.setdefault(
                    "date_policy", "product-observation-window"
                )
                self.assertEqual(
                    _without_campaign_bindings(contract),
                    legacy_semantics,
                )

    def test_removed_bindings_are_verbatim_migration_observations(self) -> None:
        legacy = records._LEGACY_EMBEDDED_A_VANILLA_TIMELINE_CONTRACTS
        observations = records.EMBEDDED_A_VANILLA_OBSERVATIONS
        expected = {
            event_key: contract
            for event_key, contract in legacy.items()
            if contract.get("root_character_id") in {29037, 32904}
        }
        self.assertEqual(len(expected), 26)
        self.assertEqual(set(observations), set(expected))

        for event_key, contract in expected.items():
            with self.subTest(event=event_key):
                exemplar = observations[event_key]["exemplars"][0]
                self.assertEqual(exemplar["run"], "legacy-migrated")
                self.assertEqual(exemplar["kind"], "legacy-live-binding")
                self.assertEqual(exemplar["review_kind"], "migration-only")
                self.assertEqual(
                    {
                        key: value
                        for key, value in exemplar.items()
                        if key not in {"run", "kind", "review_kind"}
                    },
                    _legacy_binding_fields(contract),
                )

    def test_player_bindings_materialize_for_an_unrelated_campaign(self) -> None:
        player_id = 880001
        for event_key, contract in (
            records.EMBEDDED_A_VANILLA_TIMELINE_CONTRACTS.items()
        ):
            with self.subTest(event=event_key):
                materialized = materialize_vanilla_timeline_contract(
                    contract,
                    player_id,
                )
                self.assertEqual(materialized["root_character_id"], player_id)
                self.assertNotIn(PLAYER_SENTINEL, repr(materialized))
                self.assertEqual(
                    contract["root_character_id"], PLAYER_SENTINEL
                )


if __name__ == "__main__":
    unittest.main()
