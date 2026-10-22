"""Real registered knowledge lookup; no gameplay access or action contract."""
from __future__ import annotations

import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Never
import unittest

REPO = Path(os.environ.get("XAR_R31_SOURCE_REPO", str(Path(__file__).resolve().parents[3]))).resolve()
CANDIDATE = Path(os.environ.get("XAR_R31_SOURCE_ONLY_CANDIDATE_ROOT", str(REPO))).resolve()
DOCUMENTS = Path(os.environ.get("XAR_R31_SOURCE_ONLY_DOCUMENT_ROOT", str(REPO))).resolve()
sys.path.insert(0, str(REPO / "ck3_autonomous_player/src"))


def load_candidate(name: str, relative: str) -> None:
    spec = importlib.util.spec_from_file_location(name, CANDIDATE / relative)
    if spec is None or spec.loader is None:
        raise ValueError("Candidate module cannot load: " + name)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)


if CANDIDATE != REPO:
    # Initialize the real parent package before replacing its registry leaf.
    # __init__ imports the registry constants, so a partial leaf is insufficient.
    import xar_autoplayer.vanilla_events

    load_candidate("xar_autoplayer.vanilla_events.records_pilgrimage_travel_source_only_12004",
        "ck3_autonomous_player/src/xar_autoplayer/vanilla_events/records_pilgrimage_travel_source_only_12004.py")
    load_candidate("xar_autoplayer.vanilla_events.registry",
        "ck3_autonomous_player/src/xar_autoplayer/vanilla_events/registry.py")
    # Re-run the actual package composition/export using the candidate leaf.
    # MCP imports this public re-export, not the registry leaf directly.
    importlib.reload(xar_autoplayer.vanilla_events)

from mcp import Client, ClientSession
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.vanilla_events.policy import recommend_registered_vanilla_event_option_v1
from xar_autoplayer.vanilla_events.registry import query_vanilla_event_knowledge_v1


R0034_KEYS: tuple[str, ...] = (
    "travel_start_event.1060", "pilgrimage_intent.1030",
    "pilgrimage.3102", "pilgrimage_intent.1100",
)
R0034_BATCH = "promo/ck3_faith_and_power/episode02/docs/knowledge/r0034-events-source-analysis-12004.json"
R0034_OCCURRENCES = "promo/ck3_faith_and_power/episode02/docs/knowledge/r0034-events-occurrence.json"


def obj(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("Object required")
    result: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ValueError("String keys required")
        result[key] = item
    return result


def array(value: object) -> list[object]:
    if not isinstance(value, list):
        raise ValueError("Array required")
    return list(value)


def string(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("String required")
    return value


class NoGameDriver:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def refuse(self, name: str) -> Never:
        self.calls.append(name)
        raise AssertionError("Offline knowledge query attempted gameplay: " + name)

    def capabilities(self) -> object:
        return self.refuse("capabilities")

    def take_snapshot(self) -> object:
        return self.refuse("take_snapshot")

    def take_snapshot_without_native_command_history(self) -> object:
        return self.refuse("take_snapshot_without_native_command_history")

    def execute_step(self, *args: object, **kwargs: object) -> object:
        return self.refuse("execute_step")

    def wait_for_change(self, *args: object, **kwargs: object) -> object:
        return self.refuse("wait_for_change")


class R0031SourceOnlyKnowledgeTests(unittest.IsolatedAsyncioTestCase):
    async def test_existing_registered_query_source_only_positive_and_negative(self) -> None:
        driver = NoGameDriver()
        observed: list[dict[str, object]] = []
        positive_keys: tuple[str, ...] = ("pilgrimage_intent.1060", "travel_danger_events.1012")
        requested_keys = os.environ.get("XAR_R31_KNOWLEDGE_KEYS")
        if requested_keys is not None:
            positive_keys = tuple(requested_keys.split(","))
            if not positive_keys or not set(positive_keys).issubset({"pilgrimage_intent.1060", "travel_danger_events.1012", "pilgrimage.6770", "pilgrimage.6830", "pilgrimage.6820"}):
                raise ValueError("Finite R31 source-only test keys required")
        async with Client(create_server(driver)) as client:
            self.assertIsInstance(client.session, ClientSession)
            for key in positive_keys:
                reply = await client.session.call_tool("ck3_query_vanilla_event_knowledge_v1",
                    {"event_definition_key": key, "ck3_build": "1.20.0.4"})
                self.assertFalse(reply.is_error)
                output = obj(reply.structured_content)
                self.assertEqual(output["event_definition_key"], key)
                self.assertEqual(output["status"], "unavailable")
                self.assertEqual(output["unavailable_reason"], "source_analyzed_no_occurrence_contract")
                self.assertIsNone(output["contract"])
                analysis = obj(output["analysis"])
                self.assertIs(analysis["source_analysis_completed"], True)
                self.assertEqual(analysis["migration_review_status"], "source_reviewed_no_occurrence_contract")
                self.assertIsNone(analysis["current_native_legality"])
                for field in ("action_ready", "ordinary_auto_consumes", "full_occurrence_contract_registered",
                    "selection_policy_changed", "historical_index_is_current_selection_permission", "historical_evidence_is_current_state"):
                    self.assertIs(analysis[field], False)
                source_path = DOCUMENTS / string(analysis["source_document"])
                source_raw = source_path.read_bytes()
                self.assertEqual(hashlib.sha256(source_raw).hexdigest(), analysis["source_document_sha256"])
                parsed: object = json.loads(source_raw.decode("utf-8-sig"))
                source = obj(parsed)
                self.assertEqual(source["event_definition_key"], key)
                source_options = array(source["source_options"])
                query_options = array(analysis["source_options"])
                self.assertEqual(len(query_options), len(source_options))
                for actual, authored in zip(query_options, source_options):
                    left, right = obj(actual), obj(authored)
                    self.assertEqual(left["source_key"], right["source_key"])
                    self.assertEqual(left["effects"], right["effects"])
                    self.assertEqual(left["historical_native_index"], right["historical_native_index"])
                observations = obj(output["observations"])
                self.assertIs(observations["registry_consumption_succeeded_live"], False)
                self.assertEqual(observations["policy_actually_used"], "native_first_displayed_v1")
                actual = obj(observations["actual"])
                self.assertIs(actual["ack_accepted"], True)
                self.assertIs(actual["independent_old_window_gone"], True)
                observed.append({"event_definition_key": key, "source_options_read": len(query_options),
                    "source_document": analysis["source_document"], "source_document_sha256": analysis["source_document_sha256"],
                    "status": output["status"], "reason": output["unavailable_reason"], "contract": None})
            if os.environ.get("XAR_R31_POSITIVE_ONLY") != "1":
                for key, build, reason in (("travel_danger_events.unresearched_r31", "1.20.0.4", "event_definition_key_not_registered"),
                    ("pilgrimage_intent.1060", "4.0.4", "unsupported_ck3_build")):
                    reply = await client.session.call_tool("ck3_query_vanilla_event_knowledge_v1",
                        {"event_definition_key": key, "ck3_build": build})
                    self.assertFalse(reply.is_error)
                    output = obj(reply.structured_content)
                    self.assertEqual(output["status"], "unavailable")
                    self.assertEqual(output["unavailable_reason"], reason)
                    self.assertIsNone(output["contract"])
                    negative_analysis = output["analysis"]
                    self.assertTrue(negative_analysis is None or obj(negative_analysis).get("source_analysis_completed") is not True)
                    observed.append({"event_definition_key": key, "ck3_build": build, "reason": reason})
        self.assertEqual(driver.calls, [])
        print("R0031_SOURCE_ONLY_REGISTERED_MCP=" + json.dumps({"calls": observed,
            "registered_mcp_call_count": len(observed), "game_driver_calls": driver.calls,
            "candidate_shadow_loaded": CANDIDATE != REPO, "ordinary_auto_consumption_proven": False}, ensure_ascii=False))


class R0034SourceOnlyKnowledgeTests(unittest.IsolatedAsyncioTestCase):
    async def test_actual_batch_to_registered_mcp_policy_and_json_roundtrip(self) -> None:
        batch_raw = (DOCUMENTS / R0034_BATCH).read_bytes()
        batch = obj(json.loads(batch_raw))
        summary = obj(json.loads((DOCUMENTS / R0034_OCCURRENCES).read_bytes()))
        self.assertEqual(summary["source_analysis_sha256"], hashlib.sha256(batch_raw).hexdigest())
        self.assertEqual(summary["machine_id"], "4-8e1c2f1861")
        authored_events = {string(obj(row)["event_definition_key"]): obj(row)
                           for row in array(batch["events"])}
        occurrences = obj(summary["events"])
        driver = NoGameDriver()
        async with Client(create_server(driver)) as client:
            self.assertIsInstance(client.session, ClientSession)
            for key in R0034_KEYS:
                with self.subTest(event=key):
                    reply = await client.session.call_tool("ck3_query_vanilla_event_knowledge_v1",
                        {"event_definition_key": key, "ck3_build": "1.20.0.4"})
                    self.assertFalse(reply.is_error)
                    output = obj(reply.structured_content)
                    self.assertEqual(output["status"], "unavailable")
                    self.assertEqual(output["unavailable_reason"], "source_analyzed_no_occurrence_contract")
                    self.assertIsNone(output["contract"])
                    self.assertEqual(json.loads(json.dumps(output, allow_nan=False)), output)
                    analysis = obj(output["analysis"])
                    self.assertIs(analysis["source_analysis_completed"], True)
                    self.assertIsNone(analysis["current_native_legality"])
                    for field in ("action_ready", "ordinary_auto_consumes", "full_occurrence_contract_registered",
                        "selection_policy_changed", "historical_index_is_current_selection_permission",
                        "historical_evidence_is_current_state"):
                        self.assertIs(analysis[field], False)
                    source_raw = (DOCUMENTS / string(analysis["source_document"])).read_bytes()
                    self.assertEqual(hashlib.sha256(source_raw).hexdigest(), analysis["source_document_sha256"])
                    self.assertEqual(analysis["occurrence_document"], R0034_OCCURRENCES)
                    authored = authored_events[key]
                    actual_options = array(analysis["source_options"])
                    authored_options = array(authored["options"])
                    self.assertEqual(len(actual_options), len(authored_options))
                    for actual_row, authored_row in zip(actual_options, authored_options):
                        actual, expected = obj(actual_row), obj(authored_row)
                        self.assertEqual(actual["source_key"], expected["source_option_key"])
                        self.assertEqual(actual["historical_native_index"], expected["native_index_in_observed_occurrence"])
                        self.assertEqual(actual["effects"], expected["effects_source_only"])
                        self.assertIs(actual["historical_R31_selected"], False)
                    observation = obj(output["observations"])
                    self.assertEqual(observation["run_id"], "4-8e1c2f1861--faith-engine--R0034")
                    self.assertIs(observation["registry_consumption_succeeded_live"], False)
                    self.assertEqual(observation["policy_actually_used"], "native_first_displayed_v1")
                    actual = obj(observation["actual"])
                    self.assertEqual(actual, obj(occurrences[key])["actual"])
                    self.assertEqual(actual["selected_native_index"], 0)
                    self.assertIs(actual["ack_accepted"], True)
                    self.assertIs(actual["independent_old_window_gone"], True)
                    self.assertEqual(actual["actor_after_character_id"], 15893)
                    occurrence = obj(authored["historical_occurrence"])
                    typed = obj(occurrence["typed_scope_projection"])
                    context = {**typed, "event_definition_key": key,
                        "options": occurrence["displayed_options"]}
                    decision = recommend_registered_vanilla_event_option_v1(context,
                        played_character_id=15893, snapshot_option_count=len(actual_options), ck3_build="1.20.0.4")
                    self.assertEqual(decision["status"], "not_registered")
                    self.assertIsNone(decision["selected_native_option_index"])
                    self.assertIsNone(decision["selected_option_number"])
                    effects = obj(actual_options[0])["effects"]
                    if not isinstance(effects, list):
                        raise ValueError("Returned effect list required")
                    effects.append("mutated-response-only")
                    fresh = obj(query_vanilla_event_knowledge_v1(key, "1.20.0.4"))
                    fresh_options = array(obj(fresh["analysis"])["source_options"])
                    self.assertNotIn("mutated-response-only", array(obj(fresh_options[0])["effects"]))
        self.assertEqual(driver.calls, [])

    async def test_bad_mcp_fields_missing_fields_and_types_do_not_acquire_permission(self) -> None:
        driver = NoGameDriver()
        invalid: tuple[dict[str, object], ...] = (
            {}, {"event_definition_id": "pilgrimage.3102", "ck3_build": "1.20.0.4"},
            {"event_definition_key": True, "ck3_build": "1.20.0.4"},
            {"event_definition_key": 3102.0, "ck3_build": "1.20.0.4"},
            {"event_definition_key": "pilgrimage.3102", "ck3_build": True},
            {"event_definition_key": "pilgrimage.3102", "ck3_build": "1.20.0.4", "action_ready": True},
        )
        async with Client(create_server(driver)) as client:
            self.assertIsInstance(client.session, ClientSession)
            for payload in invalid:
                with self.subTest(payload=payload):
                    reply = await client.session.call_tool("ck3_query_vanilla_event_knowledge_v1", payload)
                    self.assertTrue(reply.is_error)
        malformed: tuple[dict[str, object], ...] = ({}, {"event_definition_id": "pilgrimage.3102"},
            {"event_definition_key": True}, {"event_definition_key": "pilgrimage.3102", "options": None})
        for context in malformed:
            decision = recommend_registered_vanilla_event_option_v1(context,
                played_character_id=True, snapshot_option_count=3.0, ck3_build="1.20.0.4")
            self.assertEqual(decision["status"], "not_registered")
            self.assertIsNone(decision["selected_native_option_index"])
        self.assertEqual(driver.calls, [])




R0035_MANIFEST = "promo/ck3_faith_and_power/episode02/docs/knowledge/r0035-events-source-only-analysis-12004.json"
R0035_OCCURRENCES = "promo/ck3_faith_and_power/episode02/docs/knowledge/r0035-events-occurrence.json"


class R0035SourceOnlyKnowledgeTests(unittest.IsolatedAsyncioTestCase):
    async def test_manifest_to_registered_mcp_policy_and_json_roundtrip(self) -> None:
        manifest_raw = (DOCUMENTS / R0035_MANIFEST).read_bytes()
        manifest = obj(json.loads(manifest_raw))
        events = obj(manifest["events"])
        documents = obj(manifest["source_documents"])
        summary = obj(json.loads((DOCUMENTS / R0035_OCCURRENCES).read_bytes()))
        occurrences = obj(summary["events"])
        self.assertEqual(summary["machine_id"], "4-8e1c2f1861")
        self.assertEqual(summary["run_id"], "4-8e1c2f1861--faith-engine--R0035")
        self.assertIs(summary["batch_terminal_pending"], True)
        self.assertEqual(set(events), {"pilgrimage_intent.1040", "pilgrimage_intent.1043",
            "travel_danger_events.9010", "rite_travel_events.1000"})
        driver = NoGameDriver()
        async with Client(create_server(driver)) as client:
            self.assertIsInstance(client.session, ClientSession)
            for key, raw_authored in events.items():
                with self.subTest(event=key):
                    authored = obj(raw_authored)
                    occurrence = obj(occurrences[key])
                    reply = await client.session.call_tool("ck3_query_vanilla_event_knowledge_v1",
                        {"event_definition_key": key, "ck3_build": "1.20.0.4"})
                    self.assertFalse(reply.is_error)
                    output = obj(reply.structured_content)
                    self.assertEqual(output["status"], "unavailable")
                    self.assertEqual(output["unavailable_reason"], "source_analyzed_no_occurrence_contract")
                    self.assertIsNone(output["contract"])
                    self.assertEqual(json.loads(json.dumps(output, allow_nan=False)), output)
                    analysis = obj(output["analysis"])
                    self.assertIs(analysis["source_analysis_completed"], True)
                    self.assertIsNone(analysis["current_native_legality"])
                    for field in ("action_ready", "ordinary_auto_consumes", "full_occurrence_contract_registered",
                        "selection_policy_changed", "historical_index_is_current_selection_permission",
                        "historical_evidence_is_current_state"):
                        self.assertIs(analysis[field], False)
                    document = obj(documents[string(authored["source_document_key"])])
                    self.assertEqual(analysis["source_document"], document["path"])
                    document_raw = (DOCUMENTS / string(document["path"])).read_bytes()
                    expected_sha = hashlib.sha256(document_raw).hexdigest()
                    self.assertEqual(analysis["source_document_sha256"], expected_sha)
                    if authored["source_document_key"] == "SELF":
                        self.assertEqual(expected_sha, hashlib.sha256(manifest_raw).hexdigest())
                    else:
                        self.assertEqual(expected_sha, document["sha256"])
                        retained = obj(json.loads(document_raw))
                        self.assertIn("possible_followup_effects_not_live_observed", retained)
                    self.assertEqual(analysis["occurrence_document"], R0035_OCCURRENCES)
                    self.assertEqual(analysis["source_options"], authored["source_options"])
                    self.assertEqual(analysis["source_pins"], authored["source_pins"])
                    for raw_option in array(analysis["source_options"]):
                        self.assertIs(obj(raw_option)["historical_R31_selected"], False)
                    observation = obj(output["observations"])
                    self.assertEqual(observation["run_id"], summary["run_id"])
                    self.assertEqual(observation["machine_id"], summary["machine_id"])
                    self.assertEqual(observation["actual"], occurrence["actual"])
                    self.assertIs(observation["registry_consumption_succeeded_live"], False)
                    actual = obj(observation["actual"])
                    self.assertIs(actual["ack_accepted"], True)
                    self.assertIs(actual["old_instance_gone_in_independent_snapshot"], True)
                    displayed = array(occurrence["displayed_options"])
                    first = obj(displayed[0])
                    self.assertEqual(first["rendered_index"], 0)
                    self.assertEqual(actual["selected_native_option_index"], first["native_option_index"])
                    if key == "travel_danger_events.9010":
                        self.assertEqual(first["native_option_index"], 1)
                    if key == "pilgrimage_intent.1043":
                        self.assertEqual([obj(row)["native_option_index"] for row in displayed], [0, 2])
                    context = {**obj(occurrence["typed_scope_projection"]),
                        "event_definition_key": key, "options": displayed}
                    decision = recommend_registered_vanilla_event_option_v1(context,
                        played_character_id=15893, snapshot_option_count=len(array(authored["source_options"])),
                        ck3_build="1.20.0.4")
                    self.assertEqual(decision["status"], "not_registered")
                    self.assertIsNone(decision["selected_native_option_index"])
                    self.assertIsNone(decision["selected_option_number"])
                    effects = obj(array(analysis["source_options"])[0])["effects"]
                    if not isinstance(effects, list):
                        raise ValueError("Returned effect list required")
                    effects.append("mutated-response-only-r35")
                    fresh = obj(query_vanilla_event_knowledge_v1(key, "1.20.0.4"))
                    first_fresh = obj(array(obj(fresh["analysis"])["source_options"])[0])
                    self.assertNotIn("mutated-response-only-r35", array(first_fresh["effects"]))
            historical = await client.session.call_tool("ck3_query_vanilla_event_knowledge_v1",
                {"event_definition_key": "historical_char_creation_events.1", "ck3_build": "1.20.0.4"})
            self.assertFalse(historical.is_error)
            historical_output = obj(historical.structured_content)
            self.assertEqual(historical_output["status"], "available")
            self.assertIsInstance(historical_output["contract"], dict)
        self.assertEqual(driver.calls, [])

    async def test_r35_missing_wrong_fields_and_types_do_not_grant_actions(self) -> None:
        driver = NoGameDriver()
        events = obj(obj(json.loads((DOCUMENTS / R0035_MANIFEST).read_bytes()))["events"])
        async with Client(create_server(driver)) as client:
            self.assertIsInstance(client.session, ClientSession)
            for key in events:
                invalid: tuple[dict[str, object], ...] = (
                    {"event_definition_id": key, "ck3_build": "1.20.0.4"},
                    {"event_definition_key": key, "ck3_build": True},
                    {"event_definition_key": key, "ck3_build": 1.20},
                    {"event_definition_key": key, "ck3_build": "1.20.0.4", "selected_native_option_index": 0},
                )
                for payload in invalid:
                    with self.subTest(event=key, payload=payload):
                        reply = await client.session.call_tool("ck3_query_vanilla_event_knowledge_v1", payload)
                        self.assertTrue(reply.is_error)
        self.assertEqual(driver.calls, [])
if __name__ == "__main__":
    unittest.main(verbosity=2)
