from __future__ import annotations

import json
from pathlib import Path
import re
import sys
import unittest


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from xar_autoplayer.vanilla_events.records_tgp_movement import (
    PLAYER_SENTINEL,
    VANILLA_TGP_MOVEMENT_ANALYSIS,
    VANILLA_TGP_MOVEMENT_OBSERVATIONS,
    VANILLA_TGP_MOVEMENT_TIMELINE_CONTRACTS,
)
from xar_autoplayer.vanilla_events.registry import (
    materialize_vanilla_timeline_contract,
    query_vanilla_event_knowledge_v1,
)
import zg361_phase2_promotion_source_production_entry as production  # noqa: E402


SUPPORT_EVENT_KEY = "tgp_movement_events.0030"
SCHEME_EVENT_KEY = "tgp_movement_events.0160"
SHA256_PATTERN = re.compile(r"^[0-9A-F]{64}$")


def _scope(name: str, type_key: str, character_id: int | None = None) -> dict[str, object]:
    identity = (
        {"status": "available", "kind": "character", "character_id": character_id}
        if character_id is not None
        else {
            "status": "unavailable",
            "reason": "generic_scope_payload_identity_not_closed",
        }
    )
    return {
        "name": name,
        "scope": {
            "status": "available",
            "type_key": type_key,
            "typed_identity": identity,
        },
    }


class TgpMovementEventRecordTests(unittest.TestCase):
    def test_contract_is_campaign_neutral_and_exact(self) -> None:
        contract = VANILLA_TGP_MOVEMENT_TIMELINE_CONTRACTS[SCHEME_EVENT_KEY]

        self.assertEqual(contract["date_policy"], "product-observation-window")
        self.assertNotIn("date_raw", contract)
        self.assertEqual(contract["root_character_id"], PLAYER_SENTINEL)
        self.assertEqual(
            contract["unique_character_scope_excludes"],
            {"rival": (PLAYER_SENTINEL,)},
        )
        self.assertEqual(contract["character_scopes"], {})
        self.assertEqual(
            contract["saved_scope_name_sets"],
            (("my_movement", "rival", "rival_movement"),),
        )
        self.assertEqual(contract["saved_scope_count"], 3)
        self.assertEqual(
            contract["scope_types"],
            {
                "my_movement": "situation_participant_group",
                "rival": "character",
                "rival_movement": "situation_participant_group",
            },
        )
        self.assertEqual(contract["boolean_scopes"], ())
        json.dumps(contract, allow_nan=False)

    def test_contract_selects_the_non_blocking_third_option(self) -> None:
        contract = VANILLA_TGP_MOVEMENT_TIMELINE_CONTRACTS[SCHEME_EVENT_KEY]

        self.assertEqual(contract["option_count"], 3)
        self.assertEqual(contract["snapshot_option_count"], 3)
        self.assertEqual(contract["native_option_indices"], (0, 1, 2))
        self.assertEqual(contract["selected_option_number"], 3)
        self.assertEqual(contract["selected_native_option_index"], 2)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )

        analysis = VANILLA_TGP_MOVEMENT_ANALYSIS[SCHEME_EVENT_KEY]
        self.assertIsNone(analysis["after_effect"])
        self.assertIn("fifteen-year scheme", analysis["option_semantics"][0])
        self.assertIn("medium gold", analysis["option_semantics"][1])
        self.assertIn("no gold payment", analysis["option_semantics"][2])

    def test_registry_materializer_binds_player_without_mutating_record(self) -> None:
        contract = VANILLA_TGP_MOVEMENT_TIMELINE_CONTRACTS[SCHEME_EVENT_KEY]

        materialized = materialize_vanilla_timeline_contract(
            contract,
            player=90210,
        )

        self.assertEqual(materialized["root_character_id"], 90210)
        self.assertEqual(
            materialized["unique_character_scope_excludes"],
            {"rival": (90210,)},
        )
        self.assertEqual(
            materialized["saved_scope_name_sets"],
            (("my_movement", "rival", "rival_movement"),),
        )
        self.assertEqual(materialized["boolean_scopes"], ())
        self.assertEqual(materialized["native_option_indices"], (0, 1, 2))
        self.assertEqual(contract["root_character_id"], PLAYER_SENTINEL)
        self.assertEqual(
            contract["unique_character_scope_excludes"],
            {"rival": (PLAYER_SENTINEL,)},
        )
        json.dumps(materialized, allow_nan=False)

    def test_exact_build_and_source_hashes_are_frozen_analysis(self) -> None:
        analysis = VANILLA_TGP_MOVEMENT_ANALYSIS[SCHEME_EVENT_KEY]
        exact_build = analysis["exact_build"]

        self.assertEqual(exact_build["game_version"], "1.19.0.6")
        self.assertEqual(
            exact_build["ck3_executable_sha256"],
            "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86",
        )
        self.assertEqual(
            analysis["source_sha256"],
            {
                "events/dlc/tgp/tgp_movement_events.txt": (
                    "D9B172FC6C9F81216BE580C1B65DA7720CAA6EF21F049AB316361E17D3710BC6"
                ),
                "common/on_action/dlc/tgp/tgp_china_yearly_on_actions.txt": (
                    "4D6F5379E40304B56C5C1A914E8A0EE3998E8023174DC52F7E5072F7CFA40454"
                ),
                "common/on_action/yearly_on_actions.txt": (
                    "0FC85A284224A68D1CA0A4EF071D4F4A4F49896753AEC463975A12EE4E1116FA"
                ),
                "localization/simp_chinese/dlc/tgp/"
                "tgp_movement_events_l_simp_chinese.yml": (
                    "A2ADDB9940D72F79E57BC266EA62A11CB3D0C5318E79D5F93CB8F5EE01B3943F"
                ),
            },
        )
        self.assertRegex(exact_build["ck3_executable_sha256"], SHA256_PATTERN)
        for digest in analysis["source_sha256"].values():
            self.assertRegex(digest, SHA256_PATTERN)

    def test_r372_ids_and_date_remain_observation_only(self) -> None:
        exemplar, = VANILLA_TGP_MOVEMENT_OBSERVATIONS[SCHEME_EVENT_KEY]["exemplars"]
        contract = VANILLA_TGP_MOVEMENT_TIMELINE_CONTRACTS[SCHEME_EVENT_KEY]

        self.assertEqual(exemplar["run"], "R372")
        self.assertEqual(exemplar["date_raw"], 53436720)
        self.assertEqual(exemplar["event_instance_id"], 668)
        self.assertEqual(exemplar["root_character_id"], 32904)
        self.assertEqual(exemplar["saved_character_ids"], {"rival": 37625})
        self.assertFalse(exemplar["selection_attempted"])
        self.assertRegex(exemplar["artifact_sha256"], SHA256_PATTERN)

        contract_repr = repr(contract)
        for exemplar_only_value in (53436720, 668, 32904, 37625):
            self.assertNotIn(str(exemplar_only_value), contract_repr)

    def test_default_query_exposes_detached_analysis_and_observations(self) -> None:
        response = query_vanilla_event_knowledge_v1(SCHEME_EVENT_KEY)

        self.assertEqual(response["status"], "available")
        self.assertEqual(
            response["contract"]["unique_character_scope_excludes"],
            {"rival": [PLAYER_SENTINEL]},
        )
        self.assertEqual(
            response["contract"]["saved_scope_name_sets"],
            [["my_movement", "rival", "rival_movement"]],
        )
        self.assertEqual(response["contract"]["boolean_scopes"], [])
        self.assertEqual(response["contract"]["native_option_indices"], [0, 1, 2])
        self.assertEqual(
            response["analysis"]["option_semantics"],
            {
                "0": (
                    "diplomacy duel; success creates a mutual fifteen-year "
                    "scheme block"
                ),
                "1": (
                    "pays medium gold and creates the mutual fifteen-year "
                    "scheme block"
                ),
                "2": "minor intrigue lifestyle XP; no gold payment or scheme block",
            },
        )
        self.assertEqual(
            response["observations"]["exemplars"][0]["run"],
            "R372",
        )
        json.dumps(response, allow_nan=False)

        response["analysis"]["option_semantics"]["2"] = "tampered"
        response["observations"]["exemplars"][0]["run"] = "tampered"
        fresh = query_vanilla_event_knowledge_v1(SCHEME_EVENT_KEY)
        self.assertEqual(
            fresh["analysis"]["option_semantics"]["2"],
            VANILLA_TGP_MOVEMENT_ANALYSIS[SCHEME_EVENT_KEY]["option_semantics"][2],
        )
        self.assertEqual(
            fresh["observations"]["exemplars"][0]["run"],
            "R372",
        )

    def test_r414_support_contract_is_narrow_and_observation_free(self) -> None:
        contract = VANILLA_TGP_MOVEMENT_TIMELINE_CONTRACTS[SUPPORT_EVENT_KEY]
        analysis = VANILLA_TGP_MOVEMENT_ANALYSIS[SUPPORT_EVENT_KEY]
        exemplar, = VANILLA_TGP_MOVEMENT_OBSERVATIONS[SUPPORT_EVENT_KEY]["exemplars"]

        self.assertEqual(contract["root_character_id"], PLAYER_SENTINEL)
        self.assertEqual(contract["scope_types"], {
            "my_movement": "situation_participant_group",
            "other_ruler": "character",
        })
        self.assertEqual(
            contract["unique_character_scope_excludes"],
            {"other_ruler": (PLAYER_SENTINEL,)},
        )
        self.assertEqual(
            contract["saved_scope_name_sets"],
            (("my_movement", "other_ruler"),),
        )
        self.assertEqual(contract["selected_option_number"], 2)
        self.assertEqual(contract["selected_native_option_index"], 1)
        self.assertIn("changes only the player's influence", analysis["safe_option_rationale"])
        self.assertEqual(exemplar["run"], "R414")
        self.assertEqual(exemplar["snapshot_id"], "native:1287")
        self.assertFalse(exemplar["selection_attempted"])
        self.assertFalse(exemplar["product_failure_proven"])
        self.assertRegex(exemplar["artifact_sha256"], SHA256_PATTERN)
        contract_repr = repr(contract)
        for observed in (53733456, 1072, 32904, 33621094, 202268, 1287):
            self.assertNotIn(str(observed), contract_repr)

    def test_r414_support_live_shape_passes_production_checks(self) -> None:
        contract = production._manager_recovery_contract(
            production.KNOWN_TIMELINE_INTERRUPTS[SUPPORT_EVENT_KEY],
            player=32904,
            event_key=SUPPORT_EVENT_KEY,
        )
        contract = production._timeline_contract_for_window(
            contract,
            starting_date=53730000,
        )
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": SUPPORT_EVENT_KEY,
            "current_event_instance_id": 1072,
            "date_raw": 53733456,
            "root_scope": {
                "status": "available",
                "type_key": "character",
                "typed_identity": {
                    "status": "available",
                    "kind": "character",
                    "character_id": 32904,
                },
            },
            "saved_scopes": [
                _scope("my_movement", "situation_participant_group"),
                _scope("other_ruler", "character", 33621094),
            ],
            "options": [
                {
                    "rendered_index": index,
                    "native_option_index": index,
                    "shown": True,
                    "enabled": True,
                    "fallback": False,
                    "cancel": False,
                }
                for index in range(2)
            ],
        }
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53733456,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 1072},
            context=context,
            event_key=SUPPORT_EVENT_KEY,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 2)
        self.assertEqual(contract["selected_native_option_index"], 1)
        self.assertEqual(len(production.KNOWN_TIMELINE_INTERRUPTS), 328)


if __name__ == "__main__":
    unittest.main()
