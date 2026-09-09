from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from xar_autoplayer.vanilla_events import records_vanilla_shards as records  # noqa: E402


LEGACY_GROUPS = (
    (
        "zg361_phase2_promotion_vanilla_accolade_interrupt_contracts",
        "VANILLA_ACCOLADE_TIMELINE_CONTRACTS",
    ),
    (
        "zg361_phase2_promotion_vanilla_admin_eunuch_interrupt_contracts",
        "VANILLA_ADMIN_EUNUCH_TIMELINE_CONTRACTS",
    ),
    (
        "zg361_phase2_promotion_vanilla_diarchy_interrupt_contracts",
        "VANILLA_DIARCHY_TIMELINE_CONTRACTS",
    ),
    (
        "zg361_phase2_promotion_vanilla_dynastic_cycle_interrupt_contracts",
        "VANILLA_DYNASTIC_CYCLE_TIMELINE_CONTRACTS",
    ),
    (
        "zg361_phase2_promotion_vanilla_ep1_flavor_interrupt_contracts",
        "VANILLA_EP1_FLAVOR_TIMELINE_CONTRACTS",
    ),
    (
        "zg361_phase2_promotion_vanilla_ep3_emperor_interrupt_contracts",
        "VANILLA_EP3_EMPEROR_TIMELINE_CONTRACTS",
    ),
    (
        "zg361_phase2_promotion_vanilla_historical_character_interrupt_contracts",
        "VANILLA_HISTORICAL_CHARACTER_TIMELINE_CONTRACTS",
    ),
    (
        "zg361_phase2_promotion_vanilla_intrigue_temptation_interrupt_contracts",
        "VANILLA_INTRIGUE_TEMPTATION_TIMELINE_CONTRACTS",
    ),
    (
        "zg361_phase2_promotion_vanilla_natural_disaster_interrupt_contracts",
        "VANILLA_NATURAL_DISASTER_TIMELINE_CONTRACTS",
    ),
    (
        "zg361_phase2_promotion_vanilla_secret_interrupt_contracts",
        "VANILLA_SECRET_TIMELINE_CONTRACTS",
    ),
    (
        "zg361_phase2_promotion_vanilla_seduce_interrupt_contracts",
        "VANILLA_SEDUCE_TIMELINE_CONTRACTS",
    ),
)

EXPECTED_KEY_COUNT = 19
EXPECTED_CANONICAL_SHA256 = (
    "BF5B045B6F5661988DA65D7D1A8772E36780D0F633D33B98BFF6DD1157CFFAC5"
)


def _canonical_hash(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest().upper()


class VanillaEventRecordsShardsTests(unittest.TestCase):
    def test_all_legacy_groups_are_exported_with_identical_content(self) -> None:
        legacy_aggregate: dict[str, dict[str, object]] = {}
        exported = set(records.__all__)

        for module_name, symbol in LEGACY_GROUPS:
            with self.subTest(symbol=symbol):
                legacy_module = importlib.import_module(module_name)
                legacy_group = getattr(legacy_module, symbol)
                migrated_group = getattr(records, symbol)
                self.assertIn(symbol, exported)
                self.assertEqual(legacy_group, migrated_group)
                self.assertFalse(set(legacy_aggregate).intersection(legacy_group))
                legacy_aggregate.update(legacy_group)

        aggregate = records.VANILLA_SHARD_TIMELINE_CONTRACTS
        self.assertIn("VANILLA_SHARD_TIMELINE_CONTRACTS", exported)
        self.assertEqual(EXPECTED_KEY_COUNT, len(aggregate))
        self.assertEqual(legacy_aggregate, aggregate)
        self.assertEqual(EXPECTED_CANONICAL_SHA256, _canonical_hash(legacy_aggregate))
        self.assertEqual(EXPECTED_CANONICAL_SHA256, _canonical_hash(aggregate))

    def test_aggregate_preserves_each_exported_record_identity(self) -> None:
        aggregate = records.VANILLA_SHARD_TIMELINE_CONTRACTS
        for _module_name, symbol in LEGACY_GROUPS:
            group = getattr(records, symbol)
            for event_key, contract in group.items():
                with self.subTest(event_key=event_key):
                    self.assertIs(contract, aggregate[event_key])

    def test_duplicate_event_keys_are_rejected_during_aggregation(self) -> None:
        duplicate_key = "duplicate.event"
        with self.assertRaisesRegex(
            AssertionError,
            r"duplicate vanilla shard event keys: \['duplicate\.event'\]",
        ):
            records._aggregate_vanilla_shards((
                {duplicate_key: {"value": 1}},
                {duplicate_key: {"value": 2}},
            ))


if __name__ == "__main__":
    unittest.main()
