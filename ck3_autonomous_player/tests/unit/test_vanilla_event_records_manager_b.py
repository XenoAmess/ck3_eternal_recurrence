from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_ROOT = PROJECT_ROOT.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(REPOSITORY_ROOT / "tools"))

from xar_autoplayer.vanilla_events import records_manager_b as records  # noqa: E402
from xar_autoplayer.vanilla_events.registry import (  # noqa: E402
    PLAYER_SENTINEL,
    materialize_vanilla_timeline_contract,
)
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
    "MANAGER_VANILLA_LEGACY_OBSERVATIONS_B",
    "MANAGER_VANILLA_TIMELINE_CONTRACTS_B",
}

LEGACY_DATES_AND_ROOTS = {
    "ep3_emperor_yearly.8010": (53205336, 32904),
    "ep3_emperor_yearly.8000": (53150712, 29037),
    "lifestyle_nicknames.1000": (53158896, 29037),
    "parent.1005": (53205336, 32904),
    "prison_notification.2002": (53390784, 32904),
    "spymaster_task.3001": (53161632, 29037),
    "spymaster_task.0381": ((53148768, 53152656), 29037),
    "spymaster_task.0399": ((53148768, 53152896), 29037),
    "spymaster_task.0342": ((53152896, 53157024), 29037),
    "spymaster_task.0344": (53269008, 29037),
    "spymaster_task.0346": ((53152896, 53152920), 29037),
    "spymaster_task.0359": (53168112, 29037),
    "tgp_interaction_event.0010": (53245584, 32904),
    "tgp_interaction_event.0015": (53156904, 29037),
    "tgp_decision_events.0101": (53156928, 29037),
    "trait_specific_ongoing.2001": (53219640, 29037),
    "trait_specific_ongoing.3009": (53380728, 32904),
    "trait_specific_ongoing.3015": (53313672, 32904),
    "tribute_mission.1002": (53150160, 29037),
}


class VanillaEventRecordsManagerBTests(unittest.TestCase):
    def test_public_exports_cover_every_group_and_aggregate(self) -> None:
        self.assertEqual(EXPECTED_EXPORTS, set(records.__all__))
        for export_name in EXPECTED_EXPORTS:
            with self.subTest(export_name=export_name):
                self.assertIsNotNone(getattr(records, export_name))

    def test_migrated_keys_cover_the_compatibility_sources(self) -> None:
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

    def test_legacy_campaign_bindings_are_observation_only(self) -> None:
        json.dumps(
            records.MANAGER_VANILLA_LEGACY_OBSERVATIONS_B,
            allow_nan=False,
        )
        self.assertEqual(
            set(LEGACY_DATES_AND_ROOTS),
            set(records.MANAGER_VANILLA_LEGACY_OBSERVATIONS_B),
        )
        for event_key, (date_raw, root_character_id) in (
            LEGACY_DATES_AND_ROOTS.items()
        ):
            with self.subTest(event_key=event_key):
                contract = records.MANAGER_VANILLA_TIMELINE_CONTRACTS_B[
                    event_key
                ]
                binding = records.MANAGER_VANILLA_LEGACY_OBSERVATIONS_B[
                    event_key
                ]["exemplars"][0]

                self.assertEqual("legacy-live-binding", binding["kind"])
                self.assertEqual("migration-only", binding["review_kind"])
                self.assertEqual(date_raw, binding["date_raw"])
                self.assertEqual(root_character_id, binding["root_character_id"])
                self.assertNotIn("date_raw", contract)
                self.assertNotIn("date_raw_range", contract)
                self.assertEqual(PLAYER_SENTINEL, contract["root_character_id"])

        parent_binding = records.MANAGER_VANILLA_LEGACY_OBSERVATIONS_B[
            "parent.1005"
        ]["exemplars"][0]
        self.assertEqual({"parent": 29613}, parent_binding["character_scopes"])
        secret_binding = records.MANAGER_VANILLA_LEGACY_OBSERVATIONS_B[
            "spymaster_task.0342"
        ]["exemplars"][0]
        self.assertEqual(27963, secret_binding["character_scopes"]["councillor"])
        self.assertEqual(
            27051,
            secret_binding["character_scopes"]["secret_holder"],
        )

    def test_runtime_contracts_are_campaign_neutral_and_materializable(
        self,
    ) -> None:
        legacy_ids = (29037, 32904, 29613, 27963, 27051)
        for event_key, contract in (
            records.MANAGER_VANILLA_TIMELINE_CONTRACTS_B.items()
        ):
            with self.subTest(event_key=event_key):
                contract_repr = repr(contract)
                for legacy_id in legacy_ids:
                    self.assertNotIn(str(legacy_id), contract_repr)

                materialized = materialize_vanilla_timeline_contract(
                    contract, 47001
                )
                self.assertEqual(47001, materialized["root_character_id"])
                self.assertNotIn(PLAYER_SENTINEL, repr(materialized))

        secret_contract = records.MANAGER_SPYMASTER_TIMELINE_CONTRACTS[
            "spymaster_task.0342"
        ]
        self.assertEqual(
            {
                "councillor": ("active_councillor",),
                "active_councillor": ("councillor",),
                "target_character": ("secret_holder",),
                "secret_holder": ("target_character",),
            },
            secret_contract["character_scope_matches_any"],
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
