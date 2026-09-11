from __future__ import annotations

import json
from pathlib import Path
import re
import sys
import unittest


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))
sys.path.insert(0, str(ROOT / "tools"))

import zg361_phase2_promotion_source_production_entry as production  # noqa: E402
from xar_autoplayer.vanilla_events.records_tgp_dynastic_cycle import (  # noqa: E402
    PLAYER_SENTINEL,
    VANILLA_TGP_DYNASTIC_CYCLE_ANALYSIS,
    VANILLA_TGP_DYNASTIC_CYCLE_OBSERVATIONS,
    VANILLA_TGP_DYNASTIC_CYCLE_TIMELINE_CONTRACTS,
)
from xar_autoplayer.vanilla_events.registry import (  # noqa: E402
    materialize_vanilla_timeline_contract,
    query_vanilla_event_knowledge_v1,
)


EVENT_KEY = "tgp_dynastic_cycle_events.0020"
ADVANCEMENT_EVENT_KEY = "tgp_dynastic_cycle_events.0001"
CHAOS_EVENT_KEY = "tgp_dynastic_cycle.0081"
SHA256_PATTERN = re.compile(r"^[0-9A-F]{64}$")


class TgpDynasticCycleEventRecordTests(unittest.TestCase):
    def test_advancement_event_contract_is_portable_and_non_mutating(self) -> None:
        contract = VANILLA_TGP_DYNASTIC_CYCLE_TIMELINE_CONTRACTS[
            ADVANCEMENT_EVENT_KEY
        ]
        self.assertEqual(contract["root_character_id"], PLAYER_SENTINEL)
        self.assertNotIn("date_raw", contract)
        self.assertEqual(contract["native_option_indices"], (1, 2, 3))
        self.assertEqual(contract["snapshot_option_count"], 4)
        self.assertEqual(contract["selected_option_number"], 4)
        self.assertEqual(contract["selected_native_option_index"], 3)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )
        materialized = materialize_vanilla_timeline_contract(contract, 32904)
        self.assertEqual(materialized["root_character_id"], 32904)
        self.assertEqual(
            materialized["unique_character_scope_excludes"],
            {"servant": (32904,), "potential_friend": (32904,)},
        )
        self.assertEqual(len(contract["scope_variants"]), 2)
        self.assertEqual(
            contract["scope_variants"][0]["saved_scope_names"],
            ("my_situation", "my_movement", "servant", "friend"),
        )
        self.assertEqual(
            contract["scope_variants"][1]["saved_scope_names"],
            ("my_situation", "my_movement", "servant"),
        )

    def test_advancement_event_analysis_and_live_red_are_separate(self) -> None:
        analysis = VANILLA_TGP_DYNASTIC_CYCLE_ANALYSIS[
            ADVANCEMENT_EVENT_KEY
        ]
        r372, r414 = VANILLA_TGP_DYNASTIC_CYCLE_OBSERVATIONS[
            ADVANCEMENT_EVENT_KEY
        ]["exemplars"]
        self.assertEqual(analysis["definition_lines"], "21-216")
        self.assertIn("twenty years", analysis["option_semantics"]["2"])
        self.assertIn("stress loss", analysis["option_semantics"]["3"])
        self.assertEqual(r372["event_instance_id"], 853)
        self.assertEqual(r372["rendered_native_option_indices"], [1, 2, 3])
        self.assertFalse(r372["selection_attempted"])
        self.assertEqual(r414["run"], "R414-attempt-05")
        self.assertEqual(r414["event_instance_id"], 1074)
        self.assertEqual(r414["saved_character_ids"], {"servant": 107353})
        self.assertEqual(r414["rendered_native_option_indices"], [1, 2, 3])
        self.assertFalse(r414["selection_attempted"])
        for digest in analysis["source_sha256"].values():
            self.assertRegex(digest, SHA256_PATTERN)
        json.dumps(
            query_vanilla_event_knowledge_v1(ADVANCEMENT_EVENT_KEY),
            allow_nan=False,
        )

    def test_contract_is_portable_and_selects_non_resource_route(self) -> None:
        contract = VANILLA_TGP_DYNASTIC_CYCLE_TIMELINE_CONTRACTS[EVENT_KEY]

        self.assertEqual(contract["root_character_id"], PLAYER_SENTINEL)
        self.assertNotIn("date_raw", contract)
        self.assertEqual(
            contract["saved_scope_name_sets"],
            (("my_situation", "my_movement", "marshal", "peasant_county"),),
        )
        self.assertEqual(contract["snapshot_option_count"], 3)
        self.assertEqual(contract["native_option_indices"], (1, 2))
        self.assertEqual(contract["selected_option_number"], 3)
        self.assertEqual(contract["selected_native_option_index"], 2)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )
        self.assertEqual(
            [variant["native_option_indices"] for variant in contract["option_variants"]],
            [(1, 2), (0, 1, 2)],
        )
        self.assertEqual(
            contract["scope_variants"][0]["saved_scope_names"],
            ("my_situation", "marshal", "peasant_county"),
        )

        materialized = materialize_vanilla_timeline_contract(contract, 32904)
        self.assertEqual(materialized["root_character_id"], 32904)
        self.assertEqual(
            materialized["unique_character_scope_excludes"],
            {"marshal": (32904,)},
        )
        self.assertEqual(contract["root_character_id"], PLAYER_SENTINEL)

    def test_exact_build_analysis_and_live_observation_are_separate(self) -> None:
        analysis = VANILLA_TGP_DYNASTIC_CYCLE_ANALYSIS[EVENT_KEY]
        red, recovery = VANILLA_TGP_DYNASTIC_CYCLE_OBSERVATIONS[EVENT_KEY][
            "exemplars"
        ]
        contract = VANILLA_TGP_DYNASTIC_CYCLE_TIMELINE_CONTRACTS[EVENT_KEY]

        self.assertEqual(analysis["exact_build"]["game_version"], "1.19.0.6")
        self.assertIn("ten years", analysis["caller_semantics"])
        self.assertIn("treasury-or-gold", analysis["safe_option_rationale"])
        for digest in analysis["source_sha256"].values():
            self.assertRegex(digest, SHA256_PATTERN)
        self.assertEqual(red["event_instance_id"], 777)
        self.assertEqual(red["date_raw"], 53450184)
        self.assertEqual(red["saved_character_ids"], {"marshal": 36528})
        self.assertEqual(red["rendered_native_option_indices"], [1, 2])
        self.assertFalse(red["selection_attempted"])
        self.assertRegex(red["artifact_sha256"], SHA256_PATTERN)
        self.assertEqual(recovery["event_instance_id"], 777)
        self.assertEqual(recovery["driver_command_index"], 2164)
        self.assertEqual(recovery["selected_option_number"], 3)
        self.assertEqual(recovery["selected_native_option_index"], 2)
        self.assertTrue(recovery["postcondition_verified"])
        self.assertFalse(recovery["process_restart_required"])
        self.assertRegex(recovery["artifact_sha256"], SHA256_PATTERN)

        contract_repr = repr(contract)
        for observation_only in (777, 53450184, 32904, 36528):
            self.assertNotIn(str(observation_only), contract_repr)

    def test_default_mcp_query_returns_detached_complete_record(self) -> None:
        response = query_vanilla_event_knowledge_v1(EVENT_KEY)

        self.assertEqual(response["status"], "available")
        self.assertEqual(response["contract"]["native_option_indices"], [1, 2])
        self.assertEqual(
            response["analysis"]["option_semantics"]["2"],
            (
                "no scripted gameplay effect beyond the declared lazy/diligent "
                "stress impact"
            ),
        )
        self.assertEqual(
            response["observations"]["exemplars"][0]["event_instance_id"],
            777,
        )
        json.dumps(response, allow_nan=False)

        response["contract"]["native_option_indices"].append(99)
        fresh = query_vanilla_event_knowledge_v1(EVENT_KEY)
        self.assertEqual(fresh["contract"]["native_option_indices"], [1, 2])

    def test_chaos_contract_is_portable_single_acknowledgement(self) -> None:
        contract = VANILLA_TGP_DYNASTIC_CYCLE_TIMELINE_CONTRACTS[
            CHAOS_EVENT_KEY
        ]

        self.assertEqual(contract["root_character_id"], PLAYER_SENTINEL)
        self.assertEqual(contract["character_scopes"], {
            "huangdi": PLAYER_SENTINEL,
        })
        self.assertNotIn("date_raw", contract)
        self.assertEqual(contract["saved_scope_count"], 9)
        self.assertEqual(
            set(contract["saved_scope_name_sets"][0]),
            set(contract["scope_types"]),
        )
        self.assertEqual(contract["option_count"], 1)
        self.assertEqual(contract["snapshot_option_count"], 1)
        self.assertEqual(contract["native_option_indices"], (0,))
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )
        self.assertNotIn("max_occurrences", contract)

        materialized = materialize_vanilla_timeline_contract(contract, 32904)
        self.assertEqual(materialized["root_character_id"], 32904)
        self.assertEqual(materialized["character_scopes"], {"huangdi": 32904})
        self.assertEqual(contract["root_character_id"], PLAYER_SENTINEL)

    def test_chaos_analysis_keeps_immediate_and_option_boundaries_clear(self) -> None:
        analysis = VANILLA_TGP_DYNASTIC_CYCLE_ANALYSIS[CHAOS_EVENT_KEY]

        self.assertEqual(analysis["exact_build"]["game_version"], "1.19.0.6")
        self.assertIn("phase-transition", analysis["caller_semantics"])
        self.assertIn("destroys", analysis["immediate_effect"])
        self.assertIn("no scripted gameplay effect", analysis["option_semantics"][0])
        self.assertIsNone(analysis["after_effect"])
        self.assertIn("already happened", analysis["safe_option_rationale"])
        self.assertIn("cannot avoid", analysis["irreversibility_boundary"])
        for digest in analysis["source_sha256"].values():
            self.assertRegex(digest, SHA256_PATTERN)

    def test_chaos_r375_red_is_observation_only(self) -> None:
        exemplar = VANILLA_TGP_DYNASTIC_CYCLE_OBSERVATIONS[
            CHAOS_EVENT_KEY
        ]["exemplars"][0]
        contract = VANILLA_TGP_DYNASTIC_CYCLE_TIMELINE_CONTRACTS[
            CHAOS_EVENT_KEY
        ]

        self.assertEqual(exemplar["run"], "R375")
        self.assertEqual(exemplar["kind"], "pre-selection-live-red")
        self.assertEqual(exemplar["date_raw"], 53611224)
        self.assertEqual(exemplar["event_instance_id"], 1058)
        self.assertEqual(exemplar["root_character_id"], 32904)
        self.assertEqual(exemplar["bridge_pid"], 180544)
        self.assertEqual(exemplar["connection_generation"], 1)
        self.assertEqual(exemplar["context_snapshot_id"], "native:426")
        self.assertEqual(exemplar["context_native_revision"], 426)
        self.assertEqual(exemplar["rendered_native_option_indices"], [0])
        self.assertFalse(exemplar["selection_attempted"])
        self.assertTrue(exemplar["artifact"].endswith(
            "r375-tgp-dynastic-cycle-0081-red-freeze.json"
        ))
        self.assertEqual(
            exemplar["artifact_sha256"],
            "19860E8323136E2EED1209428BA56D09F1C4175E4250E90B43FB4AA27D0A3C35",
        )
        self.assertTrue(exemplar["park_artifact"].endswith(
            "hot-recovery-park-1.json"
        ))
        self.assertRegex(exemplar["artifact_sha256"], SHA256_PATTERN)
        self.assertRegex(exemplar["park_artifact_sha256"], SHA256_PATTERN)

        contract_repr = repr(contract)
        for observation_only in (
            53611224,
            1058,
            32904,
            50380128,
            33601840,
            71430,
            73447,
            16830863,
            180544,
            426,
        ):
            self.assertNotIn(str(observation_only), contract_repr)

    def test_stability_notice_r418_recovery_is_mcp_only_and_portable(self) -> None:
        red, recovery = VANILLA_TGP_DYNASTIC_CYCLE_OBSERVATIONS[
            "tgp_dynastic_cycle.0072"
        ]["exemplars"]
        contract_repr = repr(VANILLA_TGP_DYNASTIC_CYCLE_TIMELINE_CONTRACTS[
            "tgp_dynastic_cycle.0072"
        ])

        self.assertEqual(red["run"], "R418-attempt-04")
        self.assertFalse(red["selection_attempted"])
        self.assertEqual(recovery["run"], "R418-attempt-05")
        self.assertEqual(recovery["kind"], "same-process-hot-recovery-green")
        self.assertEqual(recovery["event_instance_id"], red["event_instance_id"])
        self.assertEqual(recovery["bridge_pid"], red["bridge_pid"])
        self.assertEqual(
            recovery["connection_generation"], red["connection_generation"]
        )
        self.assertEqual(recovery["selected_option_number"], 1)
        self.assertEqual(recovery["selected_native_option_index"], 0)
        self.assertTrue(recovery["postcondition_verified"])
        self.assertEqual(recovery["starting_snapshot_id"], "native:1731")
        self.assertEqual(recovery["ending_snapshot_id"], "native:1732")
        self.assertEqual(
            recovery["artifact_sha256"],
            "B5048E4E5384BB50B6DA0DC57A928AF7B0F56A999B27E6FD2C462180A1DCDE70",
        )
        for forbidden_mode in (
            "fixture_used",
            "ocr_used",
            "coordinates_used",
            "console_used",
        ):
            self.assertFalse(recovery[forbidden_mode])
        for observation_only in (
            54044544,
            1101,
            32904,
            204536,
            1731,
            1732,
            1733,
        ):
            self.assertNotIn(str(observation_only), contract_repr)

    def test_chaos_r375_same_process_recovery_is_mcp_only_and_portable(self) -> None:
        red, recovery = VANILLA_TGP_DYNASTIC_CYCLE_OBSERVATIONS[
            CHAOS_EVENT_KEY
        ]["exemplars"]
        contract_repr = repr(VANILLA_TGP_DYNASTIC_CYCLE_TIMELINE_CONTRACTS[
            CHAOS_EVENT_KEY
        ])

        self.assertEqual(recovery["kind"], "same-process-hot-recovery-green")
        self.assertEqual(recovery["production_live_ordinal"], 15)
        self.assertTrue(recovery["artifact"].endswith(
            "r375-live-015-tgp-dynastic-cycle-0081-green.json"
        ))
        self.assertEqual(
            recovery["artifact_sha256"],
            "573992BD13E2373DB3A827698B770D703263EC678ECDEE98595C0D48C6671789",
        )
        self.assertEqual(recovery["event_instance_id"], 1058)
        self.assertEqual(recovery["event_instance_id"], red["event_instance_id"])
        self.assertEqual(recovery["bridge_pid"], red["bridge_pid"])
        self.assertEqual(
            recovery["connection_generation"],
            red["connection_generation"],
        )
        self.assertEqual(recovery["context_query_driver_command_index"], 348)
        self.assertEqual(recovery["selection_driver_command_index"], 349)
        self.assertEqual(recovery["selected_option_number"], 1)
        self.assertEqual(recovery["selected_native_option_index"], 0)
        self.assertTrue(recovery["postcondition_verified"])
        self.assertEqual(recovery["ending_snapshot_id"], "native:427")
        self.assertFalse(recovery["process_restart_required"])
        self.assertTrue(recovery["mcp_only"])
        for forbidden_mode in (
            "fixture_used",
            "ocr_used",
            "coordinates_used",
            "console_used",
        ):
            self.assertFalse(recovery[forbidden_mode])
        self.assertRegex(recovery["artifact_sha256"], SHA256_PATTERN)

        for observation_only in (
            53611224,
            1058,
            32904,
            180544,
            "native:426",
            "native:427",
        ):
            self.assertNotIn(str(observation_only), contract_repr)

    def test_chaos_mcp_query_is_detached_and_exposes_red_evidence(self) -> None:
        response = query_vanilla_event_knowledge_v1(CHAOS_EVENT_KEY)

        self.assertEqual(response["status"], "available")
        self.assertEqual(response["contract"]["native_option_indices"], [0])
        self.assertEqual(
            response["analysis"]["option_semantics"]["0"],
            (
                "sole acknowledgement; no scripted gameplay effect and only "
                "the dynastic-cycle-end click sound"
            ),
        )
        self.assertFalse(
            response["observations"]["exemplars"][0]["selection_attempted"]
        )
        self.assertEqual(
            response["observations"]["exemplars"][1]["kind"],
            "same-process-hot-recovery-green",
        )
        self.assertTrue(
            response["observations"]["exemplars"][1]["postcondition_verified"]
        )
        json.dumps(response, allow_nan=False)

        response["contract"]["native_option_indices"].append(99)
        response["observations"]["exemplars"][0]["selection_attempted"] = True
        fresh = query_vanilla_event_knowledge_v1(CHAOS_EVENT_KEY)
        self.assertEqual(fresh["contract"]["native_option_indices"], [0])
        self.assertFalse(
            fresh["observations"]["exemplars"][0]["selection_attempted"]
        )

    def test_chaos_r375_shape_passes_production_recovery_checks(self) -> None:
        contract = production._manager_recovery_contract(
            production.KNOWN_TIMELINE_INTERRUPTS[CHAOS_EVENT_KEY],
            player=32904,
            event_key=CHAOS_EVENT_KEY,
        )
        contract = production._timeline_contract_for_window(
            contract,
            starting_date=53600000,
        )

        def scope(
            name: str,
            type_key: str,
            character_id: int | None = None,
        ) -> dict[str, object]:
            typed_identity: dict[str, object]
            if character_id is None:
                typed_identity = {
                    "status": "unavailable",
                    "reason": "generic_scope_payload_identity_not_closed",
                }
            else:
                typed_identity = {
                    "status": "available",
                    "kind": "character",
                    "character_id": character_id,
                }
            return {
                "name": name,
                "scope": {
                    "status": "available",
                    "type_key": type_key,
                    "typed_identity": typed_identity,
                },
            }

        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": CHAOS_EVENT_KEY,
            "current_event_instance_id": 1058,
            "date_raw": 53611224,
            "root_scope": scope("root", "character", 32904)["scope"],
            "saved_scopes": [
                scope("situation", "situation"),
                scope("situation_sub_region", "situation_sub_region"),
                scope("huangdi", "character", 32904),
                scope("minister_should_lose_ministry_title", "character", 50380128),
                scope("possible_conqueror", "character", 50380128),
                scope("new_liege", "character", 33601840),
                scope("member", "character", 71430),
                scope("tributary_loc", "character", 73447),
                scope("suzerain_loc", "character", 16830863),
            ],
            "options": [{
                "rendered_index": 0,
                "native_option_index": 0,
                "shown": True,
                "enabled": True,
                "fallback": False,
                "cancel": False,
            }],
        }
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53611224,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 1058},
            context=context,
            event_key=CHAOS_EVENT_KEY,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)


if __name__ == "__main__":
    unittest.main()
