"""Focused portability checks for embedded vanilla-event shard B."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))

from xar_autoplayer.vanilla_events import records_embedded_b as migrated  # noqa: E402
from xar_autoplayer.vanilla_events.registry import (  # noqa: E402
    PLAYER_SENTINEL,
    materialize_vanilla_timeline_contract,
)


CAMPAIGN_IDS = {
    27181,
    28598,
    29037,
    29067,
    29347,
    30938,
    31647,
    32904,
}


def _assert_no_campaign_identity(
    testcase: unittest.TestCase,
    value: object,
    *,
    path: str,
) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _assert_no_campaign_identity(testcase, item, path=f"{path}.{key}")
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
        testcase.assertNotIn(value, CAMPAIGN_IDS, path)


class EmbeddedBPortableContractsTests(unittest.TestCase):
    def test_all_26_runtime_contracts_are_campaign_neutral(self) -> None:
        contracts = migrated.EMBEDDED_B_VANILLA_TIMELINE_CONTRACTS
        self.assertEqual(len(contracts), 26)
        self.assertEqual(
            list(contracts),
            list(migrated._LEGACY_EMBEDDED_B_VANILLA_TIMELINE_CONTRACTS),
        )

        for event_id, contract in contracts.items():
            with self.subTest(event_id=event_id):
                self.assertNotIn("date_raw", contract)
                self.assertNotIn("date_raw_range", contract)
                self.assertEqual(
                    contract["date_policy"],
                    "product-observation-window",
                )
                self.assertEqual(contract["root_character_id"], PLAYER_SENTINEL)
                _assert_no_campaign_identity(self, contract, path=event_id)

    def test_24_removed_bindings_are_verbatim_migration_observations(self) -> None:
        observations = migrated.EMBEDDED_B_LEGACY_BINDING_OBSERVATIONS
        self.assertEqual(len(observations), 24)
        for event_id, legacy in (
            migrated._LEGACY_EMBEDDED_B_VANILLA_TIMELINE_CONTRACTS.items()
        ):
            if legacy.get("root_character_id") == PLAYER_SENTINEL:
                self.assertNotIn(event_id, observations)
                continue
            with self.subTest(event_id=event_id):
                exemplar = observations[event_id]["exemplars"][0]
                self.assertEqual(exemplar["run"], "legacy-migrated")
                self.assertEqual(exemplar["kind"], "legacy-live-binding")
                self.assertEqual(exemplar["review_kind"], "migration-only")
                expected = migrated._legacy_binding_fields(legacy)
                self.assertEqual(
                    {
                        key: value
                        for key, value in exemplar.items()
                        if key not in {"run", "kind", "review_kind"}
                    },
                    expected,
                )
        json.dumps(observations, allow_nan=False)

    def test_player_roles_materialize_for_an_unrelated_campaign(self) -> None:
        language = materialize_vanilla_timeline_contract(
            migrated.EMBEDDED_B_VANILLA_TIMELINE_CONTRACTS[
                "learn_language_outcome.1001"
            ],
            47001,
        )
        self.assertEqual(language["root_character_id"], 47001)
        self.assertEqual(language["character_scopes"], {"target": 47001})
        self.assertEqual(
            language["unique_character_scope_excludes"],
            {"owner": (47001,)},
        )

        eunuch = materialize_vanilla_timeline_contract(
            migrated.EMBEDDED_B_VANILLA_TIMELINE_CONTRACTS[
                "ep3_story_cycle_admin_eunuch.2050"
            ],
            47001,
        )
        self.assertEqual(
            eunuch["character_scopes"],
            {"emperor": 47001},
        )
        self.assertEqual(
            eunuch["unique_character_scope_excludes"],
            {"eunuch": (47001,)},
        )

    def test_governor_fixed_npcs_became_typed_source_roles(self) -> None:
        contracts = migrated.EMBEDDED_B_VANILLA_TIMELINE_CONTRACTS

        bargain = contracts["ep3_governor_yearly.8010"]
        self.assertEqual(bargain["character_scopes"], {})
        self.assertEqual(
            {
                role: bargain["scope_types"][role]
                for role in (
                    "governor",
                    "their_title_receiver",
                    "title_receiver",
                )
            },
            {
                "governor": "character",
                "their_title_receiver": "character",
                "title_receiver": "character",
            },
        )
        self.assertEqual(
            bargain["unique_character_scope_excludes"],
            {"governor": (PLAYER_SENTINEL,)},
        )

        neighbors = contracts["ep3_governor_yearly.8100"]
        self.assertEqual(neighbors["character_scopes"], {})
        self.assertEqual(
            neighbors["character_scope_differs_from"],
            {
                "governor": ("target_family_member",),
                "neighboring_promoted_char": ("target_family_member",),
            },
        )
        self.assertEqual(
            set(neighbors["unique_character_scope_excludes"]),
            {
                "target_family_member",
                "governor",
                "neighboring_promoted_char",
            },
        )

        peers = contracts["ep3_governor_yearly.8110"]
        self.assertEqual(peers["character_scopes"], {})
        self.assertEqual(
            peers["character_scope_differs_from"],
            {"governor_1": ("governor_2",), "governor_2": ("governor_1",)},
        )

    def test_files_retain_utf8_bom(self) -> None:
        for path in (Path(migrated.__file__), Path(__file__)):
            with self.subTest(path=path.name):
                self.assertTrue(path.read_bytes().startswith(b"\xef\xbb\xbf"))


if __name__ == "__main__":
    unittest.main()
