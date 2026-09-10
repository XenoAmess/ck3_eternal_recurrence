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
    "MANAGER_VANILLA_TIMELINE_CONTRACTS_A",
}


class VanillaEventRecordsManagerATests(unittest.TestCase):
    def test_public_exports_cover_every_group_and_aggregate(self) -> None:
        self.assertEqual(EXPECTED_EXPORTS, set(migrated.__all__))
        for export_name in EXPECTED_EXPORTS:
            with self.subTest(export_name=export_name):
                self.assertIsNotNone(getattr(migrated, export_name))

    def test_every_source_group_has_exact_migrated_keys_and_content(self) -> None:
        expected: dict[str, dict[str, object]] = {}
        expected_order: list[str] = []
        for source_name, source_contracts, migrated_contracts in _GROUPS:
            with self.subTest(source_name=source_name):
                self.assertEqual(list(source_contracts), list(migrated_contracts))
                self.assertEqual(source_contracts, migrated_contracts)
                self.assertTrue(set(expected).isdisjoint(source_contracts))
            expected.update(source_contracts)
            expected_order.extend(source_contracts)

        self.assertEqual(
            expected_order,
            list(migrated.MANAGER_VANILLA_TIMELINE_CONTRACTS_A),
        )
        self.assertEqual(
            expected,
            migrated.MANAGER_VANILLA_TIMELINE_CONTRACTS_A,
        )
        self.assertEqual(len(expected), 36)
        self.assertFalse(any(key.startswith("zg361.") for key in expected))

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
