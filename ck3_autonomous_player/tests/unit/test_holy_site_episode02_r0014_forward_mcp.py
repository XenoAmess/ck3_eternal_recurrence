"""One registered knowledge call for the new R0014 references; no game I/O."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
from typing import Never, get_args
import unittest

REPO = Path(os.environ.get("XAR_E02_REPO", str(Path(__file__).resolve().parents[3]))).resolve()
sys.path.insert(0, str(REPO / "ck3_autonomous_player/src"))
candidate = os.environ.get("XAR_E02_RESEARCH_CANDIDATE")
if candidate is not None:
    name = "xar_autoplayer.holy_site_episode02_research"
    spec = importlib.util.spec_from_file_location(name, candidate)
    if spec is None or spec.loader is None:
        raise ValueError("External research candidate cannot load")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)

from mcp import Client, ClientSession
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.holy_site_planning_knowledge import HolySitePlanningAction

TOOL = "ck3_query_holy_site_planning_knowledge_v1"
PREFIX = "promo/ck3_faith_and_power/episode02/docs/knowledge/"
NEW_DOCUMENTS = {
    PREFIX + "pilgrimage-3001-source-analysis.json",
    PREFIX + "pilgrimage-3001-r0014-occurrence.json",
    PREFIX + "travel-cities-1020-r0014-display-variant.json",
    PREFIX + "r0014-event-batch-summary.json",
}
TOPICS = {"artifacts", "site_effects_and_cache", "mecca", "head_of_faith", "pilgrimage", "great_holy_war"}


def object_value(value: object) -> dict[str, object]:
    """Narrow a JSON/MCP boundary without coercion or accepting foreign keys."""
    if not isinstance(value, dict):
        raise ValueError("Expected JSON object")
    out: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ValueError("JSON object key must be a string")
        out[key] = item
    return out


def list_value(value: object) -> list[object]:
    if not isinstance(value, list):
        raise ValueError("Expected JSON array")
    return list(value)


def string_value(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("Expected JSON string")
    return value


def canonical_documents() -> dict[str, Path]:
    """Project only the four immutable C11 copy targets during offline staging."""
    result: dict[str, Path] = {}
    map_path = os.environ.get("XAR_E02_CANONICAL_MAP")
    if map_path is None:
        return {relative: REPO / relative for relative in NEW_DOCUMENTS}
    mapping = object_value(json.loads(Path(map_path).read_text(encoding="utf-8")))
    if set(mapping) != NEW_DOCUMENTS:
        raise ValueError("Canonical projection must bind exactly four new targets")
    for relative, untyped_pin in mapping.items():
        pin = object_value(untyped_pin)
        path = Path(string_value(pin["path"]))
        content = path.read_bytes()
        if type(pin["bytes"]) is not int or len(content) != pin["bytes"]:
            raise ValueError("Frozen canonical document byte count differs")
        if hashlib.sha256(content).hexdigest() != string_value(pin["sha256"]):
            raise ValueError("Frozen canonical document SHA differs")
        result[relative] = path
    return result


class NoGameDriver:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def refuse(self, name: str) -> Never:
        self.calls.append(name)
        raise AssertionError("Static E02 knowledge accessed gameplay: " + name)

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


class R0014ReferenceForwardTests(unittest.IsolatedAsyncioTestCase):
    async def test_registered_new_documents_and_projected_links(self) -> None:
        projected = canonical_documents()
        driver = NoGameDriver()
        async with Client(create_server(driver)) as client:
            self.assertIsInstance(client.session, ClientSession)
            reply = await client.session.call_tool(TOOL, {"action": "demote"})
        self.assertFalse(reply.is_error)
        output = object_value(reply.structured_content)
        research = object_value(object_value(output["knowledge"])["episode02_research"])
        topics = object_value(research["topics"])
        self.assertEqual(set(topics), TOPICS)
        self.assertEqual(set(get_args(HolySitePlanningAction)), {"adopt", "create", "promote", "demote", "abandon", "enshrine_relic", "remove_relic"})
        pilgrimage = object_value(topics["pilgrimage"])
        documents = {string_value(value) for value in list_value(pilgrimage["documents"])}
        self.assertTrue(NEW_DOCUMENTS <= documents)
        self.assertEqual(len(list_value(pilgrimage["source_only_events"])), 4)
        for key in ("state_observed", "action_ready", "ordinary_auto_consumes", "historical_evidence_is_current_state", "requires_ck3", "runtime_file_access_required"):
            self.assertIs(research[key], False)
        self.assertIs(research["native_legality"], None)
        self.assertIs(output["action_ready"], False)
        self.assertIs(output["native_legality"], None)
        for value in list_value(pilgrimage["source_only_events"]):
            event = object_value(value)
            for key in ("full_occurrence_contract_registered", "selection_policy_changed", "historical_observation_is_current_state"):
                self.assertIs(event[key], False)
        rules = "\n".join(string_value(value) for value in list_value(pilgrimage["rules"]))
        for fragment in ("+100 piety", "Conditional illness", "unselected learning-option label", "without observed 7000/9001"):
            self.assertIn(fragment, rules)
        for relative in documents:
            self.assertTrue(projected.get(relative, REPO / relative).is_file(), relative)
        for relative, path in projected.items():
            document = object_value(json.loads(path.read_text(encoding="utf-8")))
            self.assertEqual(document["machine_id"], "4-8e1c2f1861")
            self.assertEqual(json.loads(json.dumps(document, ensure_ascii=False)), document)
            self.assertIn(relative, documents)
        reference_relative = string_value(research["shared_reference"])
        reference = Path(os.environ.get("XAR_E02_REFERENCE_CANDIDATE", str(REPO / reference_relative)))
        text = reference.read_text(encoding="utf-8-sig")
        checked_links = 0
        for link in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
            if "://" in link or link.startswith("#"):
                continue
            resolved = ((REPO / reference_relative).parent / link.split("#", 1)[0]).resolve()
            relative = resolved.relative_to(REPO).as_posix()
            self.assertTrue(projected.get(relative, resolved).is_file(), link)
            checked_links += 1
        for relative in NEW_DOCUMENTS:
            self.assertIn("../../" + relative, text)
        self.assertEqual(driver.calls, [])
        raw = json.dumps(output, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        print("R0014_FORWARD_ACTUAL=" + json.dumps({
            "registered_mcp_calls": 1, "driver_calls": driver.calls,
            "new_canonical_documents": sorted(NEW_DOCUMENTS),
            "checked_reference_links": checked_links,
            "canonical_projection_used": os.environ.get("XAR_E02_CANONICAL_MAP") is not None,
            "response_bytes": len(raw), "response_sha256": hashlib.sha256(raw).hexdigest(),
            "ordinary_auto_consumption_proven": False, "game_observation_or_execution": False,
        }, sort_keys=True))


if __name__ == "__main__":
    unittest.main(verbosity=2)
