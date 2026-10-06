"""One FIRST compound consumes eight new complete adopted-provider wires.

Root compiles native producers and supplies their output directory. Production
MCP registration, Driver methods, private G2 transport and protocol consume
every unchanged business body; offline replay changes only request nonce.
"""

from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import unittest

from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, NativeProtocolState
from xar_autoplayer.bridge.version_identity import CK3_12004


ACTOR_ID = 0x03000004
DATE_RAW = 53175816
NATIVE_REVISION = 701
_CASES = (
    ("draft-doctrine-choices.json", "player_religion_draft_doctrine_choices", "ck3_12004_current_draft_full_doctrine_choices_v1"),
    ("draft-groups.json", "player_religion_draft_groups", "ck3_12004_current_draft_group_model_v1"),
    ("draft-tenet-choices.json", "player_religion_draft_tenet_choices", "ck3_12004_current_draft_tenet_sources_v1"),
    ("visible-composite-costs-reasons.json", "player_religion_reform_context", "ck3_12004_player_religion_reform_query_v1"),
    ("resource-costs.json", "player_religion_draft_resource_costs", "ck3_12004_player_religion_draft_resource_costs_query_v1"),
    ("reform-ai-inputs.json", "player_religion_ai_reform_inputs", "ck3_12004_player_religion_ai_reform_inputs_v1"),
    ("rite-governance.json", "player_rite_governance", "ck3_12004_player_rite_governance_v1"),
    ("rite-members.json", "player_rite_members", "ck3_12004_rite_organization_members_v1"),
)


class AdoptedWireDriver:
    allow_private_player_religion_draft_doctrine_choices_query = True
    allow_private_player_religion_draft_groups_query = True
    allow_private_player_religion_draft_tenet_choices_query = True
    allow_private_player_religion_reform_context_query = True
    allow_private_player_religion_draft_resource_costs_query = True
    allow_private_player_religion_ai_reform_inputs_query = True
    allow_private_player_rite_governance_query = True
    allow_private_player_rite_members_query = True
    command_timeout_seconds = 1.0
    query_player_religion_draft_doctrine_choices_private_v1 = NativeHeadlessGameplayDriver.query_player_religion_draft_doctrine_choices_private_v1
    query_player_religion_draft_groups_private_v1 = NativeHeadlessGameplayDriver.query_player_religion_draft_groups_private_v1
    query_player_religion_draft_tenet_choices_private_v1 = NativeHeadlessGameplayDriver.query_player_religion_draft_tenet_choices_private_v1
    query_player_religion_reform_context_private_v1 = NativeHeadlessGameplayDriver.query_player_religion_reform_context_private_v1
    query_player_religion_draft_resource_costs_private_v1 = NativeHeadlessGameplayDriver.query_player_religion_draft_resource_costs_private_v1
    query_player_religion_ai_reform_inputs_private_v1 = NativeHeadlessGameplayDriver.query_player_religion_ai_reform_inputs_private_v1
    query_player_rite_governance_private_v1 = NativeHeadlessGameplayDriver.query_player_rite_governance_private_v1
    query_player_rite_members_private_v1 = NativeHeadlessGameplayDriver.query_player_rite_members_private_v1

    def __init__(self, packet: dict[str, object], native_key: str) -> None:
        self.packet = deepcopy(packet)
        self.state = NativeProtocolState("offline:religion-12004-adopted-whole-wire")
        result = packet["result"]
        native = result[native_key]
        self.state.ingest({
            "type": "hello", "protocol_version": 1, "pid": 1, "capabilities": [],
            "expected_ck3_version": result["game_version"],
            "expected_ck3_sha256": result["executable_sha256"],
        })
        self.snapshot = {
            "snapshot_id": f"native:{result['snapshot_revision']}",
            "revision": result["snapshot_revision"] + 1,
            "native_revision": result["snapshot_revision"], "date_raw": result["date_raw"],
            "played_character": {"character_id": native["played_character_id"], "alive": True},
            "paused": True, "map_ready": True,
            "diagnostics": {"hello": self.state.diagnostics()["hello"]},
        }
        self.sent: list[dict[str, object]] = []
        self.ingested_types: list[str] = []
        self.endpoint = self

    def take_snapshot(self) -> dict[str, object]:
        return deepcopy(self.snapshot)

    def send(self, request: dict[str, object]) -> None:
        self.sent.append(deepcopy(request))
        packet = deepcopy(self.packet)
        packet["request_id"] = request["request_id"]
        self.ingested_types.append(self.state.ingest(packet))


class Religion12004AdoptedCompound(unittest.IsolatedAsyncioTestCase):
    async def test_new_adopted_whole_wires_through_registered_mcp(self) -> None:
        directory = os.environ.get("XAR_RELIGION_12004_ADOPTED_NATIVE_WIRE_DIR")
        if not directory:
            raise RuntimeError("Root must supply XAR_RELIGION_12004_ADOPTED_NATIVE_WIRE_DIR")
        outputs: dict[str, dict[str, object]] = {}
        for filename, native_key, schema in _CASES:
            with self.subTest(wire=filename):
                packet = json.loads((Path(directory) / filename).read_text(encoding="utf-8"))
                native = packet["result"][native_key]
                driver = AdoptedWireDriver(packet, native_key)
                tool = "ck3_query_" + native_key + "_v1"
                called = await create_server(driver).call_tool(
                    tool, {"expected_revision": driver.snapshot["revision"]},
                )
                self.assertFalse(called.is_error)
                actual = called.structured_content
                self.assertIsInstance(actual, dict)
                self.assertEqual({field: actual[field] for field in native}, native)
                self.assertEqual(actual["schema"], schema)
                self.assertEqual(actual["exact_ck3_build"], CK3_12004.game_version)
                self.assertEqual(packet["result"]["executable_sha256"], CK3_12004.executable_sha256)
                if "executable_sha256" in native:
                    self.assertEqual(actual["executable_sha256"], CK3_12004.executable_sha256)
                self.assertEqual(actual["exe_sha256"], CK3_12004.executable_sha256)
                self.assertIs(actual["available"], True)
                if native_key == "player_religion_draft_resource_costs":
                    self.assertIsNone(actual["failure"])
                elif native_key != "player_rite_governance":
                    self.assertIsNone(actual["unavailable_reason"])
                self.assertEqual(actual["played_character_id"], ACTOR_ID)
                self.assertEqual(actual["date_raw"], DATE_RAW)
                self.assertEqual(actual["query_date_raw"], DATE_RAW)
                self.assertEqual(actual["snapshot_revision"], NATIVE_REVISION)
                self.assertGreater(actual["capture_epoch"], 0)
                self.assertNotEqual(actual["capture_epoch"], NATIVE_REVISION)
                self.assertEqual(actual["status"], "observed")
                self.assertIs(actual["read_only"], True)
                self.assertIs(actual["advertised"], False)
                self.assertEqual(driver.ingested_types, ["command_result"])
                self.assertEqual(len(driver.sent), 1)
                request = driver.sent[0]
                self.assertEqual(request["step"], "query-" + native_key.replace("_", "-") + "-v1")
                self.assertEqual(request["expected_revision"], NATIVE_REVISION)
                self.assertEqual(request["expected_snapshot_revision"], NATIVE_REVISION)
                self.assertNotIn("character_id", request)
                self.assertIsNone(driver.state.wait_for_command_result(request["request_id"], 0.0))
                outputs[filename] = actual

        full = outputs["draft-doctrine-choices.json"]
        self.assertIs(full["draft_observed"], True)
        self.assertIs(full["doctrine_gates_complete"], True)
        self.assertEqual(full["source_rite_id"], 0x82000002)
        self.assertEqual([slot["selected_doctrine_key"] for slot in full["slots"]], ["doctrine_a", "doctrine_c"])
        self.assertEqual([slot["group_key"] for slot in full["slots"]], ["group_a", "group_b"])
        rows = full["slots"][0]["sources"]
        self.assertEqual([row["doctrine_key"] for row in rows], ["doctrine_a", "doctrine_b", "doctrine_a"])
        self.assertEqual([row["source_index"] for row in rows], [0, 1, 2])
        self.assertEqual([row["final_selectable"] for row in rows], [True, False, True])
        self.assertIs(rows[1]["native_knows_doctrine"], False)
        self.assertIs(rows[1]["native_has_prophet"], False)
        self.assertIsNone(rows[0]["native_has_prophet"])
        hidden_row = full["slots"][1]["sources"][0]
        self.assertIs(hidden_row["passed_shown"], False)
        self.assertIs(hidden_row["native_can_pick"], False)
        self.assertIsNone(hidden_row["native_knows_doctrine"])
        self.assertIsNone(hidden_row["native_has_prophet"])

        groups = outputs["draft-groups.json"]
        self.assertIs(groups["category_materialized"], True)
        self.assertIs(groups["current_tenet_gate_complete"], True)
        self.assertIs(groups["all_group_materialized_choices_complete"], False)
        self.assertEqual(groups["current_category_slot"], 0)
        self.assertEqual(groups["current_group_key"], "group_a")
        self.assertEqual(groups["current_selected_definition_key"], "doctrine_a")
        self.assertEqual(groups["selected_slots"][0]["group_source_definition_keys"], ["doctrine_a", "doctrine_b", "doctrine_a"])
        self.assertEqual(groups["current_doctrine_cache_count"], 1)
        self.assertEqual(groups["current_tenet_source_count"], 3)
        self.assertEqual(groups["current_tenet_group_count"], 1)
        self.assertEqual(groups["current_tenet_choices"], [
            {"tenet_key": "tenet_b", "popup_group_index": 0, "popup_item_index": 0,
             "native_pick_source": 1, "final_can_pick": True},
            {"tenet_key": "tenet_c", "popup_group_index": 0, "popup_item_index": 1,
             "native_pick_source": 5, "final_can_pick": False},
        ])

        tenets = outputs["draft-tenet-choices.json"]
        self.assertIs(tenets["draft_observed"], True)
        self.assertIs(tenets["tenet_gates_complete"], True)
        self.assertEqual(tenets["source_rite_id"], 0x82000002)
        self.assertEqual(tenets["source_faith_id"], 0x84000001)
        self.assertEqual(tenets["source_main_rite_id"], 0x83000003)
        self.assertEqual(tenets["slots"], [
            {"slot_index": 7, "selected_tenet_key": "tenet_a"},
            {"slot_index": 11, "selected_tenet_key": None},
        ])
        self.assertIs(tenets["raw_category_exemption_present"], False)
        self.assertIsNone(tenets["raw_category_exemption_key"])
        rows = tenets["sources"]
        self.assertEqual([row["tenet_key"] for row in rows], ["tenet_b", "tenet_a", "tenet_b"])
        self.assertEqual([row["source_index"] for row in rows], [0, 1, 2])
        self.assertEqual([row["native_status_raw"] for row in rows], [0, 5, 0])
        self.assertEqual([row["actor_faith_status_raw"] for row in rows], [7, 0, 7])
        self.assertEqual([row["knowledge"] for row in rows], [True, False, True])
        self.assertEqual([row["final_selectable"] for row in rows], [True, False, True])
        self.assertIs(rows[1]["already_selected"], True)
        self.assertIs(rows[1]["duplicate_excluded"], True)
        self.assertTrue(all(row["native_has_prophet"] is False for row in rows))

        reform = outputs["visible-composite-costs-reasons.json"]
        self.assertEqual(len(reform["readiness"]), 10)
        for key in ("current_context_ready", "current_rite_model_ready", "main_rite_status_ready",
                    "current_window_observation_ready", "current_draft_cost_ready",
                    "current_draft_final_eligibility_ready", "current_draft_creation_terms_ready"):
            self.assertIs(reform["readiness"][key], True)
        self.assertIs(reform["readiness"]["final_choice_legality_readiness"], False)
        for key in ("current_popup_collection_ready", "doctrine_final_selection_ready"):
            self.assertIs(reform["readiness"][key], False)
        self.assertIsNone(reform["current_popup_choices"]["doctrines"])
        self.assertIsNone(reform["current_popup_choices"]["tenets"])
        costs = reform["current_draft_costs"]
        self.assertEqual(costs["piety_cost_raw"], 1250000)
        self.assertEqual(costs["piety_missing_signed_raw"], 0)
        self.assertIs(costs["has_enough_piety"], True)
        self.assertIs(costs["editing_owned_current_rite"], True)
        eligibility = reform["current_draft_eligibility"]
        self.assertIs(eligibility["can_create_rite"], False)
        self.assertIs(eligibility["can_edit_rite"], True)
        self.assertEqual(eligibility["can_create_rite_native_text"],
                         'Synthetic native create gate: "blocked"\\detail\n原生原因保留')
        self.assertEqual(eligibility["can_edit_rite_native_text"], "")
        terms = reform["current_draft_creation_terms"]
        self.assertEqual(len(terms), 17)
        self.assertEqual(terms["schema"], "ck3_12004_current_draft_creation_terms_v1")
        self.assertEqual(terms["capture_epoch"], reform["capture_epoch"])
        self.assertEqual(terms["source_rite_id"], 0x82000002)
        self.assertEqual(terms["source_faith_id"], 0x84000001)
        self.assertEqual(terms["source_main_rite_id"], 0x83000003)
        self.assertEqual(terms["actor_faith_id"], 0x84000001)
        self.assertEqual(terms["draft_divergence_raw"], 0)
        self.assertEqual(terms["faith_creation_threshold_raw"], 0)
        self.assertIs(terms["divergence_results_in_faith_creation"], True)
        self.assertIs(terms["native_create_faith_or_reform"], False)

        resource = outputs["resource-costs.json"]
        self.assertIs(resource["window_present"], True)
        self.assertIs(resource["draft_observed"], True)
        base_quote = resource["base_resource_cost_quote"]
        self.assertIs(base_quote["available"], True)
        self.assertIs(base_quote["base_resource_cost_vector_observed"], True)
        self.assertEqual(base_quote["draft_kind"], "create_rite_or_faith")
        self.assertEqual(base_quote["native_base_fee_slots_raw"],
                         [0, 0, 45000000, 0, 0, 0, 0, 0, 0, 0])
        self.assertIs(base_quote["actual_debit_observed"], False)
        self.assertIs(base_quote["post_action_net_resource_change_observed"], False)
        draft_quote = base_quote["draft_quote"]
        self.assertEqual(draft_quote["piety_cost_raw"], 45000000)
        self.assertEqual(draft_quote["piety_missing_signed_raw"], -2500000)
        self.assertIs(draft_quote["has_enough_piety"], True)
        self.assertIs(draft_quote["editing_owned_current_rite"], False)
        self.assertEqual(draft_quote["source_rite_id"], 0x82000002)

        ai = outputs["reform-ai-inputs.json"]
        self.assertEqual(ai["context_status"], "observed_controllers")
        self.assertEqual(ai["controller_count"], 2)
        self.assertEqual(ai["context"]["actual_holder_count"], 4)
        self.assertIs(ai["gate_inputs_observation_complete"], True)
        schedule_base = ai["schedule_base"]
        self.assertEqual(schedule_base["ai_status"], "not_supplied")
        self.assertEqual(schedule_base["current_actor"]["highest_tier"], 3)
        self.assertIs(schedule_base["current_actor"]["current_independent_ruler"], True)
        self.assertIs(schedule_base["native_globals"]["reformation_enabled"], True)
        self.assertEqual(schedule_base["native_globals"]["rare_period_prepare_ticks"], 40)
        controllers = ai["controllers"]
        self.assertEqual([row["kind"] for row in controllers], ["ordinary", "player_special"])
        self.assertEqual([row["active_raw"] for row in controllers], [0, 1])
        self.assertEqual([row["special_raw"] for row in controllers], [0, 1])
        schedules = [row["schedule"] for row in controllers]
        self.assertEqual([row["ai_status"] for row in schedules], ["observed", "observed"])
        caches = [row["actual_ai_cache"] for row in schedules]
        self.assertEqual([row["ai_government_flags"] for row in caches], [64, 0])
        self.assertEqual([row["ai_independent_flags"] for row in caches], [1, 1])
        self.assertEqual([row["handler_cache_gates_pass"] for row in caches], [True, False])
        timers = [row["actual_ai_timer"] for row in schedules]
        self.assertEqual([row["rare_countdown_prepare_ticks"] for row in timers], [-3, 11])
        self.assertEqual([row["rare_selected_raw"] for row in timers], [0, 1])

        governance = outputs["rite-governance.json"]
        self.assertIs(governance["frame_available"], True)
        self.assertEqual(governance["observed_components"], 3)
        self.assertIs(governance["all_components_available"], True)
        state = governance["state_rite"]
        self.assertEqual(state["actor_rite_id"], 0x82000002)
        self.assertEqual(state["actor_faith_id"], 0x84000001)
        self.assertEqual(state["actor_faith_main_rite_id"], 0x83000002)
        self.assertEqual(state["top_liege_character_id"], 0x03000005)
        self.assertEqual(state["player_primary_title"],
                         {"title_id": 0x86000001, "state_rite_id": 0x83000002,
                          "state_faith_id": 0x84000001})
        self.assertEqual(state["realm_primary_title"],
                         {"title_id": 0x87000002, "state_rite_id": 0x88000003,
                          "state_faith_id": 0x84000001})
        heads = governance["heads"]
        self.assertEqual(heads["actor_rite_head_character_id"], 0x03000007)
        self.assertEqual(heads["faith_main_rite_head_character_id"], 0x03000006)
        self.assertEqual(heads["faith_religious_head_title_id"], 0x8A000004)
        self.assertEqual(heads["faith_religious_head_holder_character_id"], 0x03000005)
        organization = governance["organization"]
        self.assertEqual(organization["rite_id"], 0x82000002)
        self.assertEqual(organization["county_count"], 0)
        self.assertEqual(organization["character_follower_count"], 0)

        members = outputs["rite-members.json"]
        self.assertEqual(members["rite_id"], 0x82000002)
        self.assertEqual(members["faith_id"], 0x84000001)
        self.assertEqual(members["religion_id"], 0x85000001)
        self.assertEqual(members["faith_character_ids"], [0x03000004, 0x03000005, 0x03000006])
        self.assertEqual(members["rite_character_ids"], [0x03000004, 0x03000005])
        self.assertEqual(members["county_title_ids"], [0x89000003])


if __name__ == "__main__":
    unittest.main()
