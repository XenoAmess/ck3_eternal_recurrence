"""One new .4 compound consumes complete native-produced religion wires.

Root supplies FIRST output after compiling the new native producer. Every
business field comes from that producer; replay changes only request nonce.
This source does not open a game or start a server/SDK session.
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
RITE_ID = 0x82000002
MAIN_RITE_ID = 0x83000002
FAITH_ID = 0x84000001
RELIGION_ID = 0x85000001
DATE_RAW = 53175816
NATIVE_REVISION = 701
TARGET_RITE_ID = 0x86000003
_CASES = (
    ("basic-reform-absent-window.json", "reform-context", "player_religion_reform_context", None),
    ("basic-reform-visible-window.json", "reform-context", "player_religion_reform_context", None),
    ("current-doctrines.json", "doctrines", "player_religion_doctrines", None),
    ("learned-e0-order-duplicates.json", "doctrine-knowledge", "player_religion_doctrine_knowledge", None),
    ("lookup-native-false.json", "doctrine-knowledge", "player_religion_doctrine_knowledge", "doctrine_c"),
    ("tenets-target-knowledge.json", "tenets", "player_religion_tenets", None),
    ("tenets-current-only.json", "tenets", "player_religion_tenets", None),
)
_TENET_KEYS = {
    "schema", "game_version", "executable_sha256", "available", "unavailable_reason",
    "capture_epoch", "date_raw", "played_character_id", "faith_id", "current_rite",
    "faith_main_rite", "personal_tenets_complete", "personal_tenets",
    "effective_tenet_states", "status_values",
}
_REFORM_KEYS = {
    "schema", "game_version", "executable_sha256", "available", "unavailable_reason",
    "scope", "capture_epoch", "date_raw", "played_character_id", "readiness",
    "current_context", "current_rite_model", "main_rite_unreformed",
    "current_creation_window", "current_draft_costs", "current_draft_eligibility",
    "current_popup_choices", "current_doctrine_selection",
}
_BASIC_READINESS = {
    "current_context_ready": True,
    "current_rite_model_ready": True,
    "main_rite_status_ready": True,
    "current_window_observation_ready": True,
    "current_draft_cost_ready": False,
    "current_draft_final_eligibility_ready": False,
    "current_popup_collection_ready": False,
    "doctrine_final_selection_ready": False,
    "final_choice_legality_readiness": False,
}


def _load_wire(filename: str) -> dict[str, object]:
    directory = os.environ.get("XAR_RELIGION_12004_NATIVE_WIRE_DIR")
    if not directory:
        raise RuntimeError("Root must supply XAR_RELIGION_12004_NATIVE_WIRE_DIR")
    return json.loads((Path(directory) / filename).read_text(encoding="utf-8"))


class Religion12004WireDriver:
    """Actual Driver methods, private G2 transport and protocol result cache."""

    allow_private_player_religion_reform_context_query = True
    allow_private_player_religion_doctrines_query = True
    allow_private_player_religion_doctrine_knowledge_query = True
    allow_private_player_religion_tenets_query = True
    command_timeout_seconds = 1.0
    query_player_religion_reform_context_private_v1 = (
        NativeHeadlessGameplayDriver.query_player_religion_reform_context_private_v1
    )
    query_player_religion_doctrines_private_v1 = (
        NativeHeadlessGameplayDriver.query_player_religion_doctrines_private_v1
    )
    query_player_religion_doctrine_knowledge_private_v1 = (
        NativeHeadlessGameplayDriver.query_player_religion_doctrine_knowledge_private_v1
    )
    query_player_religion_tenets_private_v1 = (
        NativeHeadlessGameplayDriver.query_player_religion_tenets_private_v1
    )

    def __init__(self, packet: dict[str, object], native_key: str) -> None:
        self.packet = deepcopy(packet)
        self.state = NativeProtocolState("offline:religion-12004-native-wire")
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


class Religion12004Compound(unittest.IsolatedAsyncioTestCase):
    async def test_actual_whole_wires_through_registered_production_chain(self) -> None:
        outputs: dict[str, dict[str, object]] = {}
        producer_fields: dict[str, set[str]] = {}
        schemas = {
            "reform-context": "ck3_12004_player_religion_reform_query_v1",
            "doctrines": "ck3_12004_current_doctrines_v1",
            "doctrine-knowledge": "ck3_12004_played_doctrine_knowledge_v1",
            "tenets": "ck3_12004_tenet_rows_v1",
        }
        for filename, family, native_key, doctrine_key in _CASES:
            with self.subTest(wire=filename):
                packet = _load_wire(filename)
                native = packet["result"][native_key]
                driver = Religion12004WireDriver(packet, native_key)
                arguments: dict[str, object] = {"expected_revision": driver.snapshot["revision"]}
                if doctrine_key is not None:
                    arguments["doctrine_key"] = doctrine_key
                if filename == "tenets-target-knowledge.json":
                    arguments.update(target_rite_id=TARGET_RITE_ID, tenet_key="tenet_b",
                                     include_knowledge_catalogue=True)
                tool = "ck3_query_player_religion_" + family.replace("-", "_") + "_v1"
                called = await create_server(driver).call_tool(tool, arguments)
                self.assertFalse(called.is_error)
                actual = called.structured_content
                self.assertIsInstance(actual, dict)
                self.assertEqual({field: actual[field] for field in native}, native)
                self.assertEqual(actual["schema"],
                                 "ck3_12004_played_doctrine_knowledge_lookup_v1"
                                 if doctrine_key is not None else schemas[family])
                self.assertEqual(actual["game_version"], CK3_12004.game_version)
                self.assertEqual(actual["executable_sha256"], CK3_12004.executable_sha256)
                self.assertEqual(actual["exe_sha256"], CK3_12004.executable_sha256)
                self.assertIs(actual["available"], True)
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
                self.assertEqual(request["step"], "query-player-religion-" + family + "-v1")
                self.assertEqual(request["expected_revision"], NATIVE_REVISION)
                self.assertEqual(request["expected_snapshot_revision"], NATIVE_REVISION)
                self.assertNotIn("character_id", request)
                if doctrine_key is None:
                    self.assertNotIn("doctrine_key", request)
                else:
                    self.assertEqual(request["doctrine_key"], doctrine_key)
                    self.assertEqual(actual["requested_doctrine_key"], doctrine_key)
                if filename == "tenets-target-knowledge.json":
                    self.assertEqual(request["target_rite_id"], TARGET_RITE_ID)
                    self.assertEqual(request["tenet_key"], "tenet_b")
                    self.assertIs(request["include_knowledge_catalogue"], True)
                else:
                    self.assertNotIn("target_rite_id", request)
                    self.assertNotIn("tenet_key", request)
                    self.assertNotIn("include_knowledge_catalogue", request)
                self.assertIsNone(driver.state.wait_for_command_result(request["request_id"], 0.0))
                outputs[filename] = actual
                producer_fields[filename] = set(native)

        for filename, present in (
            ("basic-reform-absent-window.json", False),
            ("basic-reform-visible-window.json", True),
        ):
            with self.subTest(reform=filename):
                reform = outputs[filename]
                self.assertEqual(producer_fields[filename], _REFORM_KEYS)
                self.assertEqual(reform["readiness"], _BASIC_READINESS)
                self.assertNotIn("current_draft_creation_terms", reform)
                self.assertNotIn("current_draft_creation_terms_ready", reform["readiness"])
                context = reform["current_context"]
                self.assertEqual(context["rite_id"], RITE_ID)
                self.assertEqual(context["faith_id"], FAITH_ID)
                self.assertEqual(context["religion_id"], RELIGION_ID)
                self.assertEqual(context["faith_main_rite_id"], MAIN_RITE_ID)
                self.assertEqual(reform["current_rite_model"]["schema"], "religion_reform12002_rite_model_v1")
                main = reform["main_rite_unreformed"]
                self.assertEqual(main["faith_id"], FAITH_ID)
                self.assertEqual(main["main_rite_id"], MAIN_RITE_ID)
                self.assertIs(main["final_reform_legality_observed"], False)
                window = reform["current_creation_window"]
                self.assertIs(window["available"], True)
                self.assertIs(window["present"], present)
                self.assertIs(window["visible"], present)
                self.assertIs(window["draft_observed"], present)
                self.assertEqual(window["unavailable_reason"], "none")
                for field in ("current_draft_costs", "current_draft_eligibility",
                              "current_popup_choices", "current_doctrine_selection"):
                    self.assertIs(reform[field]["available"], False)
                    self.assertIsInstance(reform[field]["unavailable_reason"], str)
                self.assertIsNone(reform["current_draft_costs"]["piety_cost_raw"])
                self.assertIsNone(reform["current_draft_costs"]["piety_missing_signed_raw"])
                self.assertIsNone(reform["current_draft_eligibility"]["can_create_rite"])
                self.assertIsNone(reform["current_draft_eligibility"]["can_edit_rite"])
                self.assertIsNone(reform["current_popup_choices"]["doctrines"])
                self.assertIsNone(reform["current_popup_choices"]["tenets"])

        current = outputs["current-doctrines.json"]
        self.assertEqual(current["current_rite"]["rite_id"], RITE_ID)
        self.assertEqual(current["faith_main_rite"]["rite_id"], RITE_ID)
        self.assertEqual(current["faith_main_rite"]["main_rite_id"], MAIN_RITE_ID)
        self.assertEqual(current["current_rite"]["faith_id"], FAITH_ID)
        self.assertEqual(current["current_rite"]["rows"], [
            {"doctrine_key": "doctrine_a", "group_key": "group_a", "source": "rite_effective"},
            {"doctrine_key": "doctrine_b", "group_key": "group_a", "source": "rite_effective"},
        ])
        self.assertEqual(current["faith_main_rite"]["rows"], [
            {"doctrine_key": "doctrine_c", "group_key": "group_b", "source": "faith_main_rite"},
        ])
        for scope in ("current_rite", "faith_main_rite"):
            self.assertIs(current["boolean_parameters"][scope]["boolean_parameters_complete"], True)
        self.assertEqual(current["boolean_parameters"]["current_rite"]["parameters"], [
            {"key": key, "value": True} for key in ("parameter_a", "parameter_b", "parameter_a")
        ])
        self.assertEqual(current["boolean_parameters"]["faith_main_rite"]["parameters"], [
            {"key": "parameter_c", "value": True},
        ])

        learned = outputs["learned-e0-order-duplicates.json"]
        self.assertEqual(learned["schema"], "ck3_12004_played_doctrine_knowledge_v1")
        self.assertEqual(learned["query_mode"], "learned_rows")
        self.assertEqual(learned["rite_id"], RITE_ID)
        self.assertEqual(learned["knowledge_source"], "character_extension")
        self.assertEqual(learned["learned_rows"], [
            {"doctrine_key": key, "group_key": "group_a", "source": "character_extension",
             "native_knows_doctrine": True}
            for key in ("doctrine_b", "doctrine_a", "doctrine_b")
        ])
        lookup = outputs["lookup-native-false.json"]
        self.assertEqual(lookup["schema"], "ck3_12004_played_doctrine_knowledge_lookup_v1")
        self.assertEqual(lookup["query_mode"], "by_key")
        self.assertEqual(lookup["requested_doctrine_key"], "doctrine_c")
        self.assertIs(lookup["definition_found"], True)
        self.assertEqual(lookup["definition"], {
            "doctrine_key": "doctrine_c", "group_key": "group_b", "source": "definition_registry",
        })
        self.assertIs(lookup["native_knows_doctrine"], False)

        for filename in ("tenets-target-knowledge.json", "tenets-current-only.json"):
            with self.subTest(tenets=filename):
                tenets = outputs[filename]
                self.assertEqual(tenets["faith_id"], FAITH_ID)
                self.assertEqual(tenets["current_rite"], {
                    "rite_id": RITE_ID,
                    "core_tenets": [{"key": "tenet_a", "current_rite_status": 0}],
                })
                self.assertEqual(tenets["faith_main_rite"], {
                    "rite_id": MAIN_RITE_ID,
                    "core_tenets": [{"key": "tenet_b", "current_rite_status": 1},
                                    {"key": "tenet_c", "current_rite_status": 2}],
                })
                self.assertIs(tenets["personal_tenets_complete"], True)
                self.assertEqual(tenets["personal_tenets"], [
                    {"key": "tenet_c", "current_rite_status": 2},
                ])
                self.assertEqual(tenets["effective_tenet_states"], [
                    {"key": key, "current_rite_status": state}
                    for key, state in (("tenet_a", 0), ("tenet_b", 1), ("tenet_c", 2))
                ])
                self.assertEqual(tenets["status_values"], {
                    "unknown": 0, "known": 1, "prohibited": 2, "permitted": 3, "core": 4,
                })

        comparison_root = outputs["tenets-target-knowledge.json"]
        self.assertEqual(producer_fields["tenets-target-knowledge.json"], _TENET_KEYS | {
            "target_rite_tenet_comparison", "player_tenet_knowledge_catalogue",
        })
        comparison = comparison_root["target_rite_tenet_comparison"]
        self.assertEqual(comparison["schema"], "ck3_12004_target_rite_tenet_comparison_v1")
        self.assertIs(comparison["available"], True)
        self.assertIs(comparison["named_comparison_ready"], True)
        self.assertIs(comparison["read_only"], True)
        self.assertIsNone(comparison["unavailable_reason"])
        self.assertEqual(comparison["requested_target_rite_id"], TARGET_RITE_ID)
        self.assertEqual(comparison["tenet_key"], "tenet_b")
        self.assertEqual(comparison["capture_epoch"], comparison_root["capture_epoch"])
        self.assertEqual(comparison["date_raw"], DATE_RAW)
        self.assertEqual(comparison["played_character_id"], ACTOR_ID)
        self.assertIs(comparison["same_rite"], False)
        self.assertIs(comparison["same_faith"], True)
        for scope_name, rite_id, keys, status, member in (
            ("actor_rite", RITE_ID, ["tenet_a"], 1, False),
            ("target_rite", TARGET_RITE_ID, ["tenet_b", "tenet_b"], 3, True),
        ):
            scope = comparison[scope_name]
            self.assertEqual(scope["rite_id"], rite_id)
            self.assertEqual(scope["faith_id"], FAITH_ID)
            self.assertEqual(scope["faith_main_rite_id"], MAIN_RITE_ID)
            self.assertIs(scope["current_is_main"], False)
            self.assertIs(scope["core_tenets_complete"], True)
            self.assertIs(scope["faith_main_core_tenets_complete"], True)
            self.assertEqual(scope["core_tenet_keys"], keys)
            self.assertEqual(scope["faith_main_core_tenet_keys"], ["tenet_b", "tenet_c"])
            self.assertEqual(scope["named_tenet_status"], status)
            self.assertIs(scope["named_tenet_core_member"], member)
            self.assertIs(scope["named_tenet_faith_main_core_member"], True)

        catalogue = comparison_root["player_tenet_knowledge_catalogue"]
        self.assertEqual(catalogue["schema"], "ck3_12004_player_tenet_knowledge_catalogue_v1")
        self.assertEqual(catalogue["game_version"], CK3_12004.game_version)
        self.assertEqual(catalogue["executable_sha256"], CK3_12004.executable_sha256)
        self.assertEqual(catalogue["capture_epoch"], comparison_root["capture_epoch"])
        self.assertEqual(catalogue["date_raw"], DATE_RAW)
        self.assertEqual(catalogue["played_character_id"], ACTOR_ID)
        self.assertIs(catalogue["available"], True)
        self.assertIsNone(catalogue["unavailable_reason"])
        self.assertIs(catalogue["has_character_extension"], True)
        self.assertEqual(catalogue["extra_collection_source"], "character_extension_c8")
        self.assertEqual(catalogue["extra_tenet_keys"], ["tenet_b", "tenet_b"])
        self.assertIs(catalogue["native_has_prophet"], False)
        self.assertEqual(catalogue["loaded_definition_count"], 3)
        for flag in ("extra_collection_complete", "loaded_registry_complete", "knowledge_inputs_complete"):
            self.assertIs(catalogue[flag], True)
        self.assertEqual(catalogue["knowledge_formula"], "extra_c8_membership_or_prophet_perk")
        self.assertEqual(catalogue["rows"], [
            {"source_index": index, "tenet_key": key,
             "native_extra_knowledge": known, "knowledge": known}
            for index, (key, known) in enumerate((("tenet_b", True), ("tenet_a", False),
                                                 ("tenet_b", True)))
        ])
        self.assertEqual(producer_fields["tenets-current-only.json"], _TENET_KEYS)
        self.assertNotIn("target_rite_tenet_comparison", outputs["tenets-current-only.json"])
        self.assertNotIn("player_tenet_knowledge_catalogue", outputs["tenets-current-only.json"])


if __name__ == "__main__":
    unittest.main()
