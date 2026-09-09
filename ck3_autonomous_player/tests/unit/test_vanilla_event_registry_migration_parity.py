#!/usr/bin/env python3
"""Transitional parity checks for the shared vanilla-event registry."""

from __future__ import annotations

import ast
from collections import defaultdict
from collections.abc import Mapping
import hashlib
from importlib import import_module
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from xar_autoplayer.vanilla_events.records_embedded import (  # noqa: E402
    EMBEDDED_VANILLA_TIMELINE_CONTRACTS,
)
from xar_autoplayer.vanilla_events.records_epidemic import (  # noqa: E402
    VANILLA_EPIDEMIC_TIMELINE_CONTRACTS,
)
from xar_autoplayer.vanilla_events.records_manager_a import (  # noqa: E402
    MANAGER_VANILLA_TIMELINE_CONTRACTS_A,
)
from xar_autoplayer.vanilla_events.records_manager_b import (  # noqa: E402
    MANAGER_VANILLA_TIMELINE_CONTRACTS_B,
)
from xar_autoplayer.vanilla_events.records_prebootstrap import (  # noqa: E402
    PREBOOTSTRAP_VANILLA_TIMELINE_CONTRACTS,
)
from xar_autoplayer.vanilla_events.records_tgp_dynastic_cycle import (  # noqa: E402
    VANILLA_TGP_DYNASTIC_CYCLE_TIMELINE_CONTRACTS,
)
from xar_autoplayer.vanilla_events.records_tgp_movement import (  # noqa: E402
    VANILLA_TGP_MOVEMENT_TIMELINE_CONTRACTS,
)
from xar_autoplayer.vanilla_events.records_trait_specific import (  # noqa: E402
    VANILLA_TRAIT_SPECIFIC_TIMELINE_CONTRACTS,
)
from xar_autoplayer.vanilla_events.records_death_management import (  # noqa: E402
    VANILLA_DEATH_MANAGEMENT_TIMELINE_CONTRACTS,
)
from xar_autoplayer.vanilla_events.records_vanilla_shards import (  # noqa: E402
    VANILLA_SHARD_TIMELINE_CONTRACTS,
)
from xar_autoplayer.vanilla_events.records_vassal_interaction import (  # noqa: E402
    VANILLA_VASSAL_INTERACTION_TIMELINE_CONTRACTS,
)
from xar_autoplayer.vanilla_events import (  # noqa: E402
    DEFAULT_VANILLA_EVENT_CONTRACT_GROUPS,
    DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS,
    VANILLA_EVENT_TIMELINE_CONTRACTS,
)
from xar_autoplayer.vanilla_events.registry import (  # noqa: E402
    build_vanilla_event_registry,
)


PRODUCTION_ENTRY = (
    ROOT / "tools" / "zg361_phase2_promotion_source_production_entry.py"
)
SEED_CAPTURE_ENTRY = ROOT / "tools" / "run_zg361_phase2_seed_capture.py"

EXPECTED_BUCKET_COUNTS = {
    "vanilla_shards": 20,
    "manager_original": 57,
    "embedded_original": 79,
    "prebootstrap": 2,
}
EXPECTED_INTENTIONAL_OVERLAPS = {
    "spymaster_task.0381": frozenset({"manager_original", "prebootstrap"}),
    "spymaster_task.0399": frozenset({"manager_original", "prebootstrap"}),
}
# Updated when exact-build .5009/.1001 REDs replaced their legacy one-shot
# bindings with portable source-backed contracts.
EXPECTED_EMBEDDED_CANONICAL_SHA256 = (
    "F7D1F8DEE3D8B717486B2CF6261A78C49D2B34C9D404440FB7F3CD7D08C8F8DE"
)

LEGACY_VANILLA_SOURCES = (
    (
        "zg361_phase2_promotion_vanilla_secret_interrupt_contracts",
        "VANILLA_SECRET_TIMELINE_CONTRACTS",
    ),
    (
        "zg361_phase2_promotion_vanilla_diarchy_interrupt_contracts",
        "VANILLA_DIARCHY_TIMELINE_CONTRACTS",
    ),
    (
        "zg361_phase2_promotion_vanilla_accolade_interrupt_contracts",
        "VANILLA_ACCOLADE_TIMELINE_CONTRACTS",
    ),
    (
        "zg361_phase2_promotion_vanilla_admin_eunuch_interrupt_contracts",
        "VANILLA_ADMIN_EUNUCH_TIMELINE_CONTRACTS",
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
        "zg361_phase2_promotion_vanilla_dynastic_cycle_interrupt_contracts",
        "VANILLA_DYNASTIC_CYCLE_TIMELINE_CONTRACTS",
    ),
    (
        "zg361_phase2_promotion_vanilla_historical_character_interrupt_contracts",
        "VANILLA_HISTORICAL_CHARACTER_TIMELINE_CONTRACTS",
    ),
    (
        "zg361_phase2_promotion_vanilla_ep3_emperor_interrupt_contracts",
        "VANILLA_EP3_EMPEROR_TIMELINE_CONTRACTS",
    ),
    (
        "zg361_phase2_promotion_vanilla_seduce_interrupt_contracts",
        "VANILLA_SEDUCE_TIMELINE_CONTRACTS",
    ),
    (
        "zg361_phase2_promotion_vanilla_ep1_flavor_interrupt_contracts",
        "VANILLA_EP1_FLAVOR_TIMELINE_CONTRACTS",
    ),
)

LEGACY_MANAGER_SOURCES = (
    ("zg361_phase2_promotion_manager_imperial_contracts", "MANAGER_IMPERIAL_TIMELINE_CONTRACTS"),
    ("zg361_phase2_promotion_manager_court_contracts", "MANAGER_COURT_TIMELINE_CONTRACTS"),
    ("zg361_phase2_promotion_manager_health_contracts", "MANAGER_HEALTH_TIMELINE_CONTRACTS"),
    ("zg361_phase2_promotion_manager_health_aging_contracts", "MANAGER_HEALTH_AGING_TIMELINE_CONTRACTS"),
    ("zg361_phase2_promotion_manager_death_contracts", "MANAGER_DEATH_TIMELINE_CONTRACTS"),
    ("zg361_phase2_promotion_manager_prison_contracts", "MANAGER_PRISON_TIMELINE_CONTRACTS"),
    ("zg361_phase2_promotion_manager_parent_contracts", "MANAGER_PARENT_TIMELINE_CONTRACTS"),
    ("zg361_phase2_promotion_manager_birth_contracts", "MANAGER_BIRTH_TIMELINE_CONTRACTS"),
    ("zg361_phase2_promotion_manager_chancellor_contracts", "MANAGER_CHANCELLOR_TIMELINE_CONTRACTS"),
    ("zg361_phase2_promotion_manager_debate_contracts", "MANAGER_DEBATE_TIMELINE_CONTRACTS"),
    ("zg361_phase2_promotion_manager_tgp_petition_contracts", "MANAGER_TGP_PETITION_TIMELINE_CONTRACTS"),
    ("zg361_phase2_promotion_manager_tgp_interaction_contracts", "MANAGER_TGP_INTERACTION_TIMELINE_CONTRACTS"),
    ("zg361_phase2_promotion_manager_tgp_ministry_contracts", "MANAGER_TGP_MINISTRY_TIMELINE_CONTRACTS"),
    ("zg361_phase2_promotion_manager_tribute_contracts", "MANAGER_TRIBUTE_TIMELINE_CONTRACTS"),
    ("zg361_phase2_promotion_manager_nickname_contracts", "MANAGER_NICKNAME_TIMELINE_CONTRACTS"),
    ("zg361_phase2_promotion_manager_spymaster_contracts", "MANAGER_SPYMASTER_TIMELINE_CONTRACTS"),
    ("zg361_phase2_promotion_manager_befriend_contracts", "MANAGER_BEFRIEND_TIMELINE_CONTRACTS"),
    ("zg361_phase2_promotion_manager_annual_summary_contracts", "MANAGER_ANNUAL_SUMMARY_TIMELINE_CONTRACTS"),
    ("zg361_phase2_promotion_manager_elimination_contracts", "MANAGER_ELIMINATION_TIMELINE_CONTRACTS"),
    ("zg361_phase2_promotion_manager_holy_war_contracts", "MANAGER_HOLY_WAR_TIMELINE_CONTRACTS"),
    ("zg361_phase2_promotion_manager_council_claim_contracts", "MANAGER_COUNCIL_CLAIM_TIMELINE_CONTRACTS"),
    ("zg361_phase2_promotion_manager_trait_contracts", "MANAGER_TRAIT_TIMELINE_CONTRACTS"),
)


def _legacy_aggregate(
    sources: tuple[tuple[str, str], ...], *, original_only: bool = False,
) -> dict[str, object]:
    aggregate: dict[str, object] = {}
    for module_name, symbol_name in sources:
        source = getattr(import_module(module_name), symbol_name)
        for event_key, contract in source.items():
            if original_only and event_key.startswith("zg361"):
                continue
            if event_key in aggregate:
                raise AssertionError(
                    f"duplicate legacy event key {event_key!r} in {module_name}"
                )
            aggregate[event_key] = contract
    return aggregate


def _top_level_assignment(path: Path, name: str) -> ast.expr:
    tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            if any(
                isinstance(target, ast.Name) and target.id == name
                for target in node.targets
            ):
                return node.value
        elif (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == name
        ):
            return node.value
    raise AssertionError(f"top-level assignment {name!r} not found in {path}")


def _canonical_sha256(records: Mapping[str, object]) -> str:
    payload = json.dumps(
        records,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest().upper()


def _legacy_prebootstrap_contracts() -> dict[str, object]:
    result: dict[str, object] = {}
    for name in (
        "KNOWN_PRE_BOOTSTRAP_VANILLA_EVENT",
        "KNOWN_PRE_BOOTSTRAP_VANILLA_NO_SECRETS_EVENT",
    ):
        source = ast.literal_eval(_top_level_assignment(SEED_CAPTURE_ENTRY, name))
        event_key = source["event_definition_key"]
        if event_key in result:
            raise AssertionError(f"duplicate prebootstrap event key {event_key!r}")
        character_scopes = {}
        boolean_scopes: tuple[str, ...] = ()
        unique_character_scope_excludes = {}
        if event_key == "spymaster_task.0381":
            unique_character_scope_excludes = {
                "character_to_hook": source["excluded_character_to_hook_ids"],
            }
        elif event_key == "spymaster_task.0399":
            character_scopes = {
                "councillor": source["councillor_character_id"],
                "councillor_liege": source["councillor_liege_character_id"],
                "target_character": source["target_character_id"],
            }
            boolean_scopes = (source["required_boolean_scope"],)
        else:  # pragma: no cover - guarded by the two-name source manifest
            raise AssertionError(f"unexpected prebootstrap event key {event_key!r}")
        result[event_key] = {
            "date_raw": source["date_raw"],
            "root_character_id": source["root_character_id"],
            "character_scopes": character_scopes,
            **(
                {
                    "unique_character_scope_excludes": (
                        unique_character_scope_excludes
                    ),
                }
                if unique_character_scope_excludes
                else {}
            ),
            "boolean_scopes": boolean_scopes,
            "option_count": source["option_count"],
            "native_option_indices": tuple(range(source["option_count"])),
            "selected_option_number": source["selected_option_number"],
            "selected_native_option_index": source[
                "selected_native_option_index"
            ],
            "max_occurrences": 1,
        }
    return result


class VanillaEventRegistryMigrationParityTests(unittest.TestCase):
    def test_each_new_bucket_has_exact_legacy_content(self) -> None:
        legacy_vanilla = _legacy_aggregate(LEGACY_VANILLA_SOURCES)
        legacy_manager = _legacy_aggregate(
            LEGACY_MANAGER_SOURCES, original_only=True,
        )
        legacy_prebootstrap = _legacy_prebootstrap_contracts()

        self.assertEqual(VANILLA_SHARD_TIMELINE_CONTRACTS, legacy_vanilla)
        self.assertEqual(
            {
                **MANAGER_VANILLA_TIMELINE_CONTRACTS_A,
                **MANAGER_VANILLA_TIMELINE_CONTRACTS_B,
            },
            legacy_manager,
        )
        self.assertEqual(len(EMBEDDED_VANILLA_TIMELINE_CONTRACTS), 79)
        self.assertEqual(
            _canonical_sha256(EMBEDDED_VANILLA_TIMELINE_CONTRACTS),
            EXPECTED_EMBEDDED_CANONICAL_SHA256,
        )
        self.assertEqual(
            PREBOOTSTRAP_VANILLA_TIMELINE_CONTRACTS,
            legacy_prebootstrap,
        )

    def test_intentional_overlaps_preserve_both_legacy_contracts(self) -> None:
        legacy_manager = _legacy_aggregate(
            LEGACY_MANAGER_SOURCES, original_only=True,
        )
        legacy_prebootstrap = _legacy_prebootstrap_contracts()
        migrated_manager = {
            **MANAGER_VANILLA_TIMELINE_CONTRACTS_A,
            **MANAGER_VANILLA_TIMELINE_CONTRACTS_B,
        }
        for event_key in EXPECTED_INTENTIONAL_OVERLAPS:
            with self.subTest(event=event_key):
                self.assertEqual(
                    migrated_manager[event_key], legacy_manager[event_key]
                )
                self.assertEqual(
                    PREBOOTSTRAP_VANILLA_TIMELINE_CONTRACTS[event_key],
                    legacy_prebootstrap[event_key],
                )
                # Bootstrap capture has an exact-save shape while manager
                # recovery has a longer product-window shape.  They share an
                # event key intentionally but must not silently overwrite one
                # another in a flat registry.
                self.assertNotEqual(
                    migrated_manager[event_key],
                    PREBOOTSTRAP_VANILLA_TIMELINE_CONTRACTS[event_key],
                )

    def test_default_sources_are_disjoint_and_prebootstrap_conflicts(self) -> None:
        default_groups = (
            VANILLA_SHARD_TIMELINE_CONTRACTS,
            MANAGER_VANILLA_TIMELINE_CONTRACTS_A,
            MANAGER_VANILLA_TIMELINE_CONTRACTS_B,
            EMBEDDED_VANILLA_TIMELINE_CONTRACTS,
            VANILLA_EPIDEMIC_TIMELINE_CONTRACTS,
            VANILLA_TGP_MOVEMENT_TIMELINE_CONTRACTS,
            VANILLA_TGP_DYNASTIC_CYCLE_TIMELINE_CONTRACTS,
            VANILLA_VASSAL_INTERACTION_TIMELINE_CONTRACTS,
            VANILLA_TRAIT_SPECIFIC_TIMELINE_CONTRACTS,
            VANILLA_DEATH_MANAGEMENT_TIMELINE_CONTRACTS,
        )
        self.assertEqual(DEFAULT_VANILLA_EVENT_CONTRACT_GROUPS, default_groups)
        key_memberships: defaultdict[str, list[int]] = defaultdict(list)
        for group_index, records in enumerate(default_groups):
            for event_key in records:
                key_memberships[event_key].append(group_index)

        self.assertEqual(sum(map(len, default_groups)), 163)
        self.assertEqual(len(key_memberships), 163)
        self.assertEqual(
            {
                event_key: indexes
                for event_key, indexes in key_memberships.items()
                if len(indexes) > 1
            },
            {},
        )
        try:
            built = build_vanilla_event_registry(default_groups)
            self.assertEqual(set(built), set(key_memberships))
            self.assertEqual(built, DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS)
            self.assertEqual(
                VANILLA_EVENT_TIMELINE_CONTRACTS,
                DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS,
            )
            with self.assertRaisesRegex(
                ValueError,
                "conflicting vanilla event contract",
            ):
                build_vanilla_event_registry(
                    (*default_groups, PREBOOTSTRAP_VANILLA_TIMELINE_CONTRACTS)
                )
        finally:
            build_vanilla_event_registry({})

    def test_production_consumes_the_unified_default_aggregate(self) -> None:
        literal_value = _top_level_assignment(
            PRODUCTION_ENTRY, "KNOWN_TIMELINE_INTERRUPTS"
        )
        if not isinstance(literal_value, ast.Dict):
            self.fail("production KNOWN_TIMELINE_INTERRUPTS is not a dict")
        literal_keys = tuple(ast.literal_eval(key) for key in literal_value.keys)
        self.assertEqual(len(literal_keys), 17)
        self.assertTrue(all(key.startswith("zg361") for key in literal_keys))

        production_contracts = import_module(
            "zg361_phase2_promotion_source_production_entry"
        ).KNOWN_TIMELINE_INTERRUPTS
        production_vanilla = {
            event_key: contract
            for event_key, contract in production_contracts.items()
            if not event_key.startswith("zg361")
        }
        self.assertEqual(
            production_vanilla,
            DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS,
        )

    def test_bucket_counts_and_duplicate_manifest_are_exact(self) -> None:
        manager_overlap = (
            set(MANAGER_VANILLA_TIMELINE_CONTRACTS_A)
            & set(MANAGER_VANILLA_TIMELINE_CONTRACTS_B)
        )
        self.assertEqual(manager_overlap, set())

        buckets: dict[str, Mapping[str, object]] = {
            "vanilla_shards": VANILLA_SHARD_TIMELINE_CONTRACTS,
            "manager_original": {
                **MANAGER_VANILLA_TIMELINE_CONTRACTS_A,
                **MANAGER_VANILLA_TIMELINE_CONTRACTS_B,
            },
            "embedded_original": EMBEDDED_VANILLA_TIMELINE_CONTRACTS,
            "prebootstrap": PREBOOTSTRAP_VANILLA_TIMELINE_CONTRACTS,
        }
        self.assertEqual(
            {name: len(records) for name, records in buckets.items()},
            EXPECTED_BUCKET_COUNTS,
        )
        for bucket_name, records in buckets.items():
            with self.subTest(bucket=bucket_name):
                self.assertTrue(records)
                self.assertFalse(
                    [key for key in records if key.startswith("zg361")]
                )
                self.assertTrue(all(isinstance(value, Mapping) for value in records.values()))

        memberships: defaultdict[str, set[str]] = defaultdict(set)
        for bucket_name, records in buckets.items():
            for event_key in records:
                memberships[event_key].add(bucket_name)
        actual_overlaps = {
            event_key: frozenset(bucket_names)
            for event_key, bucket_names in memberships.items()
            if len(bucket_names) > 1
        }
        self.assertEqual(actual_overlaps, EXPECTED_INTENTIONAL_OVERLAPS)
        self.assertEqual(len(memberships), 156)


if __name__ == "__main__":
    unittest.main()
