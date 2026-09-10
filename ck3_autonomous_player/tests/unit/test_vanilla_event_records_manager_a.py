"""Parity tests for migrated pure-original manager event records, batch A."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))

from xar_autoplayer.vanilla_events import records_manager_a as migrated  # noqa: E402
from xar_autoplayer.vanilla_events import (  # noqa: E402
    query_vanilla_event_knowledge_v1,
)
from xar_autoplayer.vanilla_events.registry import (  # noqa: E402
    PLAYER_SENTINEL,
    materialize_vanilla_timeline_contract,
)
from zg361_phase2_promotion_manager_befriend_contracts import (  # noqa: E402
    MANAGER_BEFRIEND_TIMELINE_CONTRACTS as SOURCE_BEFRIEND,
)
from zg361_phase2_promotion_manager_birth_contracts import (  # noqa: E402
    MANAGER_BIRTH_TIMELINE_CONTRACTS as SOURCE_BIRTH,
)
from zg361_phase2_promotion_manager_chancellor_contracts import (  # noqa: E402
    MANAGER_CHANCELLOR_TIMELINE_CONTRACTS as SOURCE_CHANCELLOR,
)
from zg361_phase2_promotion_manager_council_claim_contracts import (  # noqa: E402
    MANAGER_COUNCIL_CLAIM_TIMELINE_CONTRACTS as SOURCE_COUNCIL_CLAIM,
)
from zg361_phase2_promotion_manager_court_contracts import (  # noqa: E402
    MANAGER_COURT_TIMELINE_CONTRACTS as SOURCE_COURT,
)
from zg361_phase2_promotion_manager_death_contracts import (  # noqa: E402
    MANAGER_DEATH_TIMELINE_CONTRACTS as SOURCE_DEATH,
)
from zg361_phase2_promotion_manager_debate_contracts import (  # noqa: E402
    MANAGER_DEBATE_TIMELINE_CONTRACTS as SOURCE_DEBATE,
)
from zg361_phase2_promotion_manager_health_aging_contracts import (  # noqa: E402
    MANAGER_HEALTH_AGING_TIMELINE_CONTRACTS as SOURCE_HEALTH_AGING,
)
from zg361_phase2_promotion_manager_health_contracts import (  # noqa: E402
    MANAGER_HEALTH_TIMELINE_CONTRACTS as SOURCE_HEALTH,
)
from zg361_phase2_promotion_manager_holy_war_contracts import (  # noqa: E402
    MANAGER_HOLY_WAR_TIMELINE_CONTRACTS as SOURCE_HOLY_WAR,
)


_GROUPS = (
    ("befriend", SOURCE_BEFRIEND, migrated.MANAGER_BEFRIEND_TIMELINE_CONTRACTS),
    ("birth", SOURCE_BIRTH, migrated.MANAGER_BIRTH_TIMELINE_CONTRACTS),
    ("chancellor", SOURCE_CHANCELLOR, migrated.MANAGER_CHANCELLOR_TIMELINE_CONTRACTS),
    (
        "council_claim",
        SOURCE_COUNCIL_CLAIM,
        migrated.MANAGER_COUNCIL_CLAIM_TIMELINE_CONTRACTS,
    ),
    ("court", SOURCE_COURT, migrated.MANAGER_COURT_TIMELINE_CONTRACTS),
    ("death", SOURCE_DEATH, migrated.MANAGER_DEATH_TIMELINE_CONTRACTS),
    ("debate", SOURCE_DEBATE, migrated.MANAGER_DEBATE_TIMELINE_CONTRACTS),
    (
        "health_aging",
        SOURCE_HEALTH_AGING,
        migrated.MANAGER_HEALTH_AGING_TIMELINE_CONTRACTS,
    ),
    ("health", SOURCE_HEALTH, migrated.MANAGER_HEALTH_TIMELINE_CONTRACTS),
    ("holy_war", SOURCE_HOLY_WAR, migrated.MANAGER_HOLY_WAR_TIMELINE_CONTRACTS),
)

_LEGACY_GROUPS = (
    ("befriend", migrated._LEGACY_MANAGER_BEFRIEND_TIMELINE_CONTRACTS),
    ("birth", migrated._LEGACY_MANAGER_BIRTH_TIMELINE_CONTRACTS),
    ("chancellor", migrated._LEGACY_MANAGER_CHANCELLOR_TIMELINE_CONTRACTS),
    (
        "council_claim",
        migrated._LEGACY_MANAGER_COUNCIL_CLAIM_TIMELINE_CONTRACTS,
    ),
    ("court", migrated._LEGACY_MANAGER_COURT_TIMELINE_CONTRACTS),
    ("death", migrated._LEGACY_MANAGER_DEATH_TIMELINE_CONTRACTS),
    ("debate", migrated._LEGACY_MANAGER_DEBATE_TIMELINE_CONTRACTS),
    ("health_aging", migrated._LEGACY_MANAGER_HEALTH_AGING_TIMELINE_CONTRACTS),
    ("health", migrated._LEGACY_MANAGER_HEALTH_TIMELINE_CONTRACTS),
)
_LEGACY_CONTRACTS = {
    event_key: contract
    for _source_name, contracts in _LEGACY_GROUPS
    for event_key, contract in contracts.items()
}

EXPECTED_EXPORTS = {
    "MANAGER_BEFRIEND_TIMELINE_CONTRACTS",
    "MANAGER_BIRTH_TIMELINE_CONTRACTS",
    "MANAGER_CHANCELLOR_TIMELINE_CONTRACTS",
    "MANAGER_COUNCIL_CLAIM_TIMELINE_CONTRACTS",
    "MANAGER_COURT_TIMELINE_CONTRACTS",
    "MANAGER_DEATH_TIMELINE_CONTRACTS",
    "MANAGER_DEBATE_TIMELINE_CONTRACTS",
    "MANAGER_HEALTH_AGING_TIMELINE_CONTRACTS",
    "MANAGER_HEALTH_TIMELINE_CONTRACTS",
    "MANAGER_HOLY_WAR_ANALYSIS",
    "MANAGER_HOLY_WAR_OBSERVATIONS",
    "MANAGER_HOLY_WAR_TIMELINE_CONTRACTS",
    "MANAGER_VANILLA_OBSERVATIONS_A",
    "MANAGER_VANILLA_TIMELINE_CONTRACTS_A",
}

_PORTABLE_EXCLUSIONS = {
    "epidemic_events.0110",
    "great_holy_war.0011",
}
_MIGRATED_OBSERVATION_EXCLUSIONS = _PORTABLE_EXCLUSIONS | {
    "health.1006",
    "health.3001",
    "health.3101",
}
_LEGACY_BINDING_KEYS = (
    "date_raw",
    "date_raw_range",
    "root_character_id",
    "character_scopes",
    "unique_character_scope_excludes",
)
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
        testcase.assertNotIn(
            value,
            {29037, 32904, 49718, 36369, 29889},
            path,
        )


class VanillaEventRecordsManagerATests(unittest.TestCase):
    def test_public_exports_cover_every_group_and_aggregate(self) -> None:
        self.assertEqual(EXPECTED_EXPORTS, set(migrated.__all__))
        for export_name in EXPECTED_EXPORTS:
            with self.subTest(export_name=export_name):
                self.assertIsNotNone(getattr(migrated, export_name))

    def test_every_source_group_has_exact_keys_and_portable_contracts(self) -> None:
        expected_keys: set[str] = set()
        expected_order: list[str] = []
        for source_name, source_contracts, migrated_contracts in _GROUPS:
            with self.subTest(source_name=source_name):
                self.assertEqual(list(source_contracts), list(migrated_contracts))
                self.assertTrue(expected_keys.isdisjoint(source_contracts))
            expected_keys.update(source_contracts)
            expected_order.extend(source_contracts)

        self.assertEqual(
            expected_order,
            list(migrated.MANAGER_VANILLA_TIMELINE_CONTRACTS_A),
        )
        self.assertEqual(len(expected_keys), 36)
        self.assertFalse(any(key.startswith("zg361.") for key in expected_keys))

        for source_name, source_contracts, migrated_contracts in _GROUPS:
            for event_key, contract in migrated_contracts.items():
                if event_key in _PORTABLE_EXCLUSIONS:
                    continue
                with self.subTest(source=source_name, event=event_key):
                    self.assertNotIn("date_raw", contract)
                    self.assertNotIn("date_raw_range", contract)
                    self.assertEqual(
                        contract["date_policy"],
                        "product-observation-window",
                    )
                    self.assertEqual(
                        contract["root_character_id"], PLAYER_SENTINEL
                    )
                    _assert_no_campaign_identity(
                        self,
                        contract,
                        path=event_key,
                    )

                    source_contract = _LEGACY_CONTRACTS[event_key]
                    source_semantics = _without_campaign_bindings(
                        source_contract
                    )
                    self.assertIsInstance(source_semantics, dict)
                    source_semantics.setdefault(
                        "date_policy", "product-observation-window"
                    )
                    self.assertEqual(
                        _without_campaign_bindings(contract),
                        source_semantics,
                    )

    def test_legacy_campaign_bindings_are_verbatim_migration_observations(
        self,
    ) -> None:
        expected_sources = {
            event_key: contract
            for event_key, contract in _LEGACY_CONTRACTS.items()
            if event_key not in _MIGRATED_OBSERVATION_EXCLUSIONS
        }
        self.assertEqual(len(expected_sources), 31)
        self.assertEqual(
            set(migrated.MANAGER_VANILLA_OBSERVATIONS_A),
            set(expected_sources),
        )
        for event_key, source_contract in expected_sources.items():
            with self.subTest(event=event_key):
                exemplars = migrated.MANAGER_VANILLA_OBSERVATIONS_A[event_key][
                    "exemplars"
                ]
                self.assertEqual(len(exemplars), 1)
                exemplar = exemplars[0]
                self.assertEqual(exemplar["run"], "legacy-migrated")
                self.assertEqual(exemplar["kind"], "legacy-live-binding")
                self.assertEqual(exemplar["review_kind"], "migration-only")
                observed_binding = {
                    key: value
                    for key, value in exemplar.items()
                    if key not in {"run", "kind", "review_kind"}
                }
                self.assertEqual(
                    observed_binding,
                    _legacy_binding_fields(source_contract),
                )

    def test_player_relations_materialize_for_unrelated_campaign_identity(
        self,
    ) -> None:
        materialized = materialize_vanilla_timeline_contract(
            migrated.MANAGER_BIRTH_TIMELINE_CONTRACTS["birth.3032"],
            47001,
        )
        self.assertEqual(materialized["root_character_id"], 47001)
        self.assertEqual(
            materialized["character_scopes"],
            {"father": 47001, "real_father": 47001},
        )
        self.assertEqual(
            materialized["unique_character_scope_excludes"],
            {"child": (47001,), "mother": (47001,)},
        )

        physician = materialize_vanilla_timeline_contract(
            migrated.MANAGER_HEALTH_TIMELINE_CONTRACTS["health.3103"],
            47001,
        )
        self.assertEqual(
            physician["character_scopes"],
            {"sick_character": 47001, "treatment_picker": 47001},
        )
        self.assertNotIn("high_skill_option", physician["character_scopes"])
        self.assertEqual(
            physician["character_scope_matches_any"],
            {
                "physician": ("high_skill_option", "portrait"),
                "high_skill_option": ("physician", "portrait"),
                "portrait": ("physician", "high_skill_option"),
            },
        )

    def test_aggregate_rejects_duplicate_keys(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicate vanilla event contract key"):
            migrated._aggregate_contract_groups(
                ("first", {"health.7100": {"source": "first"}}),
                ("second", {"health.7100": {"source": "second"}}),
            )

    def test_holy_war_notice_is_repeatable_exact_build_knowledge(self) -> None:
        event_key = "great_holy_war.0011"
        contract = migrated.MANAGER_HOLY_WAR_TIMELINE_CONTRACTS[event_key]
        analysis = migrated.MANAGER_HOLY_WAR_ANALYSIS[event_key]
        exemplars = migrated.MANAGER_HOLY_WAR_OBSERVATIONS[event_key][
            "exemplars"
        ]

        self.assertNotIn("max_occurrences", contract)
        self.assertNotIn("date_raw", contract)
        self.assertEqual(contract["root_character_id"], PLAYER_SENTINEL)
        self.assertEqual(contract["character_scopes"], {})
        self.assertEqual(
            contract["unique_character_scope_excludes"],
            {
                "ghw_first_sponsor": (PLAYER_SENTINEL,),
                "background_temple_scope": (PLAYER_SENTINEL,),
            },
        )
        self.assertEqual(
            contract["character_scope_matches_any"],
            {
                "ghw_first_sponsor": ("background_temple_scope",),
                "background_temple_scope": ("ghw_first_sponsor",),
            },
        )
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )
        self.assertEqual(contract["selected_option_number"], 4)
        self.assertEqual(contract["selected_native_option_index"], 3)
        self.assertEqual(analysis["exact_build"]["game_version"], "1.19.0.6")
        self.assertIn("every_player", analysis["production_caller"])
        self.assertIn("no gameplay effect", analysis["option_semantics"][3])
        self.assertIn("$player", analysis["scope_boundary"])
        self.assertEqual([row["run"] for row in exemplars], ["R342", "R372"])
        self.assertEqual(
            {row["binding_kind"] for row in exemplars},
            {"legacy-live-binding"},
        )
        self.assertEqual(
            exemplars[1]["prior_same_run_occurrence"]["event_instance_id"],
            606,
        )
        self.assertEqual(exemplars[1]["event_instance_id"], 670)

        legacy = migrated.MANAGER_HOLY_WAR_OBSERVATIONS[event_key][
            "legacy_contract_binding"
        ]
        self.assertEqual(legacy["kind"], "legacy-live-binding")
        self.assertEqual(legacy["date_raw"], 53223552)
        self.assertEqual(legacy["root_character_id"], 29037)
        contract_repr = repr(contract)
        for observation_only in (53223552, 29037, 32904, 32201, 36145):
            self.assertNotIn(str(observation_only), contract_repr)

        materialized = materialize_vanilla_timeline_contract(contract, 47001)
        self.assertEqual(materialized["root_character_id"], 47001)
        self.assertEqual(
            materialized["unique_character_scope_excludes"],
            {
                "ghw_first_sponsor": (47001,),
                "background_temple_scope": (47001,),
            },
        )
        self.assertEqual(contract["root_character_id"], PLAYER_SENTINEL)

        response = query_vanilla_event_knowledge_v1(event_key)
        self.assertEqual(response["status"], "available")
        self.assertEqual(
            response["contract"]["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )
        self.assertEqual(response["contract"]["root_character_id"], "$player")
        self.assertNotIn("date_raw", response["contract"])
        self.assertEqual(
            response["analysis"]["source_sha256"][
                "events/religion_events/great_holy_war_events.txt"
            ],
            "E431A0E2FDFF5E49FB572B7184DE9B498F982B95AED875334AD1432D0F88CBA7",
        )
        self.assertEqual(
            response["observations"]["exemplars"][1]["event_instance_id"],
            670,
        )
        json.dumps(response, allow_nan=False)


if __name__ == "__main__":
    unittest.main()
