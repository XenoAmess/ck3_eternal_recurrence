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


if __name__ == "__main__":
    unittest.main(verbosity=2)
