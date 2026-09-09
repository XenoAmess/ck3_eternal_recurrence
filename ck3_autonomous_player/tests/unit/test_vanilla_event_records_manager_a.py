"""Parity tests for migrated pure-original manager event records, batch A."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))

from xar_autoplayer.vanilla_events import records_manager_a as migrated  # noqa: E402
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


if __name__ == "__main__":
    unittest.main()
