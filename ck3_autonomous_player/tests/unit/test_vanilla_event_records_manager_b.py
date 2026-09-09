from __future__ import annotations

from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_ROOT = PROJECT_ROOT.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(REPOSITORY_ROOT / "tools"))

from xar_autoplayer.vanilla_events import records_manager_b as records  # noqa: E402
from zg361_phase2_promotion_manager_imperial_contracts import (  # noqa: E402
    MANAGER_IMPERIAL_TIMELINE_CONTRACTS,
)
from zg361_phase2_promotion_manager_nickname_contracts import (  # noqa: E402
    MANAGER_NICKNAME_TIMELINE_CONTRACTS,
)
from zg361_phase2_promotion_manager_parent_contracts import (  # noqa: E402
    MANAGER_PARENT_TIMELINE_CONTRACTS,
)
from zg361_phase2_promotion_manager_prison_contracts import (  # noqa: E402
    MANAGER_PRISON_TIMELINE_CONTRACTS,
)
from zg361_phase2_promotion_manager_spymaster_contracts import (  # noqa: E402
    MANAGER_SPYMASTER_TIMELINE_CONTRACTS,
)
from zg361_phase2_promotion_manager_tgp_interaction_contracts import (  # noqa: E402
    MANAGER_TGP_INTERACTION_TIMELINE_CONTRACTS,
)
from zg361_phase2_promotion_manager_tgp_ministry_contracts import (  # noqa: E402
    MANAGER_TGP_MINISTRY_TIMELINE_CONTRACTS,
)
from zg361_phase2_promotion_manager_tgp_petition_contracts import (  # noqa: E402
    MANAGER_TGP_PETITION_TIMELINE_CONTRACTS,
)
from zg361_phase2_promotion_manager_trait_contracts import (  # noqa: E402
    MANAGER_TRAIT_TIMELINE_CONTRACTS,
)
from zg361_phase2_promotion_manager_tribute_contracts import (  # noqa: E402
    MANAGER_TRIBUTE_TIMELINE_CONTRACTS,
)


SOURCE_TABLES = (
    MANAGER_IMPERIAL_TIMELINE_CONTRACTS,
    MANAGER_NICKNAME_TIMELINE_CONTRACTS,
    MANAGER_PARENT_TIMELINE_CONTRACTS,
    MANAGER_PRISON_TIMELINE_CONTRACTS,
    MANAGER_SPYMASTER_TIMELINE_CONTRACTS,
    MANAGER_TGP_INTERACTION_TIMELINE_CONTRACTS,
    MANAGER_TGP_PETITION_TIMELINE_CONTRACTS,
    MANAGER_TRAIT_TIMELINE_CONTRACTS,
    MANAGER_TRIBUTE_TIMELINE_CONTRACTS,
)

EXPECTED_EXPORTS = {
    "MANAGER_IMPERIAL_TIMELINE_CONTRACTS",
    "MANAGER_NICKNAME_TIMELINE_CONTRACTS",
    "MANAGER_PARENT_TIMELINE_CONTRACTS",
    "MANAGER_PRISON_TIMELINE_CONTRACTS",
    "MANAGER_SPYMASTER_TIMELINE_CONTRACTS",
    "MANAGER_TGP_INTERACTION_TIMELINE_CONTRACTS",
    "MANAGER_TGP_MINISTRY_TIMELINE_CONTRACTS",
    "MANAGER_TGP_PETITION_TIMELINE_CONTRACTS",
    "MANAGER_TRAIT_TIMELINE_CONTRACTS",
    "MANAGER_TRIBUTE_TIMELINE_CONTRACTS",
    "MANAGER_VANILLA_TIMELINE_CONTRACTS_B",
}


class VanillaEventRecordsManagerBTests(unittest.TestCase):
    def test_public_exports_cover_every_group_and_aggregate(self) -> None:
        self.assertEqual(EXPECTED_EXPORTS, set(records.__all__))
        for export_name in EXPECTED_EXPORTS:
            with self.subTest(export_name=export_name):
                self.assertIsNotNone(getattr(records, export_name))

    def test_migrated_keys_and_contract_content_equal_sources(self) -> None:
        expected: dict[str, dict[str, object]] = {}
        for table in SOURCE_TABLES:
            self.assertTrue(expected.keys().isdisjoint(table))
            expected.update(table)

        self.assertEqual(
            records.MANAGER_VANILLA_TIMELINE_CONTRACTS_B,
            expected,
        )
        self.assertEqual(
            set(records.MANAGER_VANILLA_TIMELINE_CONTRACTS_B),
            set().union(*(set(table) for table in SOURCE_TABLES)),
        )
        self.assertIs(
            records.MANAGER_TGP_MINISTRY_TIMELINE_CONTRACTS,
            MANAGER_TGP_MINISTRY_TIMELINE_CONTRACTS,
        )
        self.assertNotIn(
            "tgp_china_ministry.0100",
            records.MANAGER_VANILLA_TIMELINE_CONTRACTS_B,
        )

    def test_aggregate_rejects_duplicate_event_definition_keys(self) -> None:
        contract = {"date_policy": "product-observation-window"}
        with self.assertRaisesRegex(
            ValueError,
            "duplicate manager vanilla event contract: duplicate.event",
        ):
            records._aggregate_manager_vanilla_timeline_contracts_b((
                {"duplicate.event": contract},
                {"duplicate.event": contract},
            ))


if __name__ == "__main__":
    unittest.main()
