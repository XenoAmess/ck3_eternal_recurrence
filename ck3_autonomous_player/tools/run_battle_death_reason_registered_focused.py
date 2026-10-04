"""Consume only the new native-produced wires through registered MCP tools.

This is an offline producer-wire/service/MCP fixture. It is not a CK3 live
query and gives no game-day or production-live credit. Run with -B -O.
"""

from __future__ import annotations

import argparse
import asyncio
import copy
import hashlib
import importlib.util
import json
import sys
import types
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = Path("Z:/g38")
EXE_SHA256 = "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6"
sys.path.insert(0, str(SOURCE / "ck3_autonomous_player/src"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


# The source bridge/__init__ eagerly imports native_driver. Establish its
# namespace first so the projected contract finishes before those consumers
# import it; all actual submodules still load from the frozen source path.
import xar_autoplayer

bridge_package = types.ModuleType("xar_autoplayer.bridge")
bridge_package.__package__ = "xar_autoplayer.bridge"
bridge_package.__path__ = [str(SOURCE / "ck3_autonomous_player/src/xar_autoplayer/bridge")]
sys.modules["xar_autoplayer.bridge"] = bridge_package
xar_autoplayer.bridge = bridge_package

MODULE_NAME = "xar_autoplayer.bridge.battle_terminal_transition_contract"
PROJECTED_CONTRACT = Path(sys.argv[1]) / "ck3_autonomous_player/src/xar_autoplayer/bridge/battle_terminal_transition_contract.py"
spec = importlib.util.spec_from_file_location(MODULE_NAME, PROJECTED_CONTRACT)
require(spec is not None and spec.loader is not None, "Cannot load projected contract")
module = importlib.util.module_from_spec(spec)
sys.modules[MODULE_NAME] = module
spec.loader.exec_module(module)

from mcp import Client
from xar_autoplayer.bridge.battle_control_contract import (
    QUERY_BATTLE_CONTROL_SNAPSHOT_V1_CAPABILITY,
    query_battle_control_snapshot_v1_step,
)
from xar_autoplayer.bridge.battle_terminal_transition_contract import (
    QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY,
    query_battle_terminal_transition_v1_step,
    normalize_battle_terminal_transition_v1,
)
from xar_autoplayer.bridge.mcp_server import create_server


TERMINAL_TOOL = "ck3_query_battle_terminal_transition_v1"
CONTROL_TOOL = "ck3_query_battle_control_snapshot_v1"
TERMINAL_MIRRORS = (
    "prior_combat_id", "subject_public_cunit_id", "terminal_journal", "prior",
    "removal", "subject", "successor", "battle_terminal_transition_ready",
    "unavailable_reason", "character_observations",
)
CONTROL_MIRRORS = (
    "selected_public_cunit_id", "selected_native_carmy_id", "selected_owner_character_id",
    "combat_province_id", "side_index", "side_scope",
    "affected_public_cunit_ids_in_stored_order",
    "unaffected_same_side_public_cunit_ids_in_stored_order", "side_flags", "legality",
)


class CapturedWireDriver:
    """Replay a real native serializer result without a process or action."""

    def __init__(self, wire: dict, case: dict):
        self.wire = wire["result"] if isinstance(wire.get("result"), dict) else wire
        self.case = case
        self.tool_name = case.get("tool_name", TERMINAL_TOOL)
        require(self.tool_name in {TERMINAL_TOOL, CONTROL_TOOL}, "Unexpected fixture tool")
        self.frame_key = (
            "battle_terminal_transition" if self.tool_name == TERMINAL_TOOL
            else "battle_control_snapshot"
        )
        self.fixture_envelope = self.frame_key not in self.wire
        self.frame = self.wire if self.fixture_envelope else self.wire[self.frame_key]
        require(isinstance(self.frame, dict), "Native serializer frame is missing")
        self.public_revision = case["expected_revision"]
        self.native_revision = self.frame["snapshot_revision"]
        self.date_raw = case["expected_observed_date_raw"]
        self.steps = []
        if self.tool_name == TERMINAL_TOOL:
            prior = self.frame["prior_combat_id"]
            subject = self.frame["subject_public_cunit_id"]
            self.arguments = {
                "prior_combat_id": None if prior == -1 else prior,
                "subject_public_cunit_id": None if subject == -1 else subject,
                "expected_revision": self.public_revision,
                "after_terminal_sequence": self.frame["terminal_journal"]["requested_after_sequence"],
                "character_ids": case["expected_character_ids"],
            }
            self.step = query_battle_terminal_transition_v1_step(
                self.arguments["prior_combat_id"], self.arguments["subject_public_cunit_id"],
                self.arguments["after_terminal_sequence"], self.arguments["character_ids"],
            )
            self.capability = QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY
            self.mirror_keys = TERMINAL_MIRRORS
        else:
            subject = self.frame["selected_public_cunit_id"]
            self.arguments = {"subject_army_id": subject, "expected_revision": self.public_revision}
            self.step = query_battle_control_snapshot_v1_step(subject)
            self.capability = QUERY_BATTLE_CONTROL_SNAPSHOT_V1_CAPABILITY
            self.mirror_keys = CONTROL_MIRRORS
        if self.fixture_envelope:
            # The real Serialize* function emits a frame body. The replay driver
            # supplies the same envelope fields as the existing service fixture;
            # it does not manufacture any observed frame/character/Bucket value.
            self.wire = {
                "step": self.step, "accepted": True,
                "status": self.frame.get("status", "available"),
                "query_sequence": 1, "snapshot_revision": self.native_revision,
                self.frame_key: self.frame,
            }
        require(self.wire["step"] == self.step, "Native wire step differs from requested scope")

    def capabilities(self):
        return {
            "format_version": 1, "backend_id": "current-person-native-wire-fixture",
            "source": "named-pipe", "snapshot": True, "wait_for_change": False,
            "action_steps": [], "bridge_capabilities": [self.capability],
        }

    def take_snapshot(self):
        return {
            "format_version": 1, "snapshot_id": f"wire-fixture:{self.native_revision}",
            "revision": self.public_revision, "native_revision": self.native_revision,
            "source": "named-pipe", "backend_id": "current-person-native-wire-fixture",
            "date_raw": self.date_raw, "paused": True,
            "episode_run_id": "offline-native-wire-robert-29829",
            "played_character": {"character_id": 29829, "alive": True},
            "diagnostics": {"hello": {
                "game_version": "1.20.0.3", "executable_sha256": EXE_SHA256,
            }},
        }

    def execute_step(self, step, *, expected_revision=None):
        require(step == self.step, "MCP/service changed the native query scope")
        require(expected_revision == self.public_revision, "MCP/service changed the revision")
        self.steps.append(step)
        result = {
            key: copy.deepcopy(self.wire[key]) for key in (
                "step", "accepted", "status", "query_sequence", "snapshot_revision", self.frame_key,
            )
        }
        result["backend_id"] = "current-person-native-wire-fixture"
        for key in self.mirror_keys:
            if key in self.frame:
                result[key] = copy.deepcopy(self.frame[key])
        return result

    def wait_for_change(self, after_revision, *, timeout_seconds):
        raise RuntimeError("A current-person read must not advance any state")


from xar_autoplayer.bridge.battle_terminal_transition_contract import normalize_battle_terminal_transition_v1

async def run_reason_wire():
    wire_path = Path(sys.argv[2])
    output_path = Path(sys.argv[3])
    wire_bytes = wire_path.read_bytes()
    wire = json.loads(wire_bytes)
    ids = [29829, 32750, 30470, 30784, 60822]
    frame = wire.get("result", wire)
    if "battle_terminal_transition" in frame:
        frame = frame["battle_terminal_transition"]
    case = {
        "name": "current-death-reason-only",
        "expected_revision": 1,
        "expected_observed_date_raw": 54000000,
        "expected_character_ids": ids,
    }
    driver = CapturedWireDriver(wire, case)
    server = create_server(driver)
    async with Client(server) as client:
        listed = await client.list_tools()
        require(TERMINAL_TOOL in {tool.name for tool in listed.tools}, "Existing terminal tool unregistered")
        response = await client.call_tool(TERMINAL_TOOL, driver.arguments)
    require(not response.is_error, f"Registered existing MCP failed: {response}")
    payload = response.structured_content
    require(isinstance(payload, dict), "MCP omitted structured content")
    require(payload["battle_terminal_transition"] == frame, "MCP changed the genuine native frame")
    require(driver.steps == [driver.step], "Unexpected repeated or action query")
    rows = payload["character_observations"]
    require([row["character_id"] for row in rows] == ids, "Strict requested full IDs/order changed")
    wanted = [
        {"status":"none", "reason_key":None, "unavailable_reason":None},
        {"status":"available", "reason_key":"death_battle", "unavailable_reason":None},
        {"status":"available", "reason_key":"death_fixture_heap_length_over15", "unavailable_reason":None},
        {"status":"available", "reason_key":None, "unavailable_reason":None},
        {"status":"unavailable", "reason_key":None, "unavailable_reason":"character_unresolved"},
    ]
    actual = [row["current_person_state"]["death_record"] for row in rows]
    require(actual == wanted, "Death reason value/status changed across native wire and registered MCP")
    require(not payload["battle_terminal_transition_ready"], "Character-only record acquired terminal credit")
    # Same new-field pass checks the additive older response shape, without a
    # second MCP query, old actor case, or original old wire replay.
    legacy = copy.deepcopy(frame)
    for row in legacy["character_observations"]:
        row["current_person_state"].pop("death_record")
    normalized_legacy = normalize_battle_terminal_transition_v1(
        legacy,
        expected_prior_combat_id=None,
        expected_subject_public_cunit_id=None,
        expected_after_terminal_sequence=None,
        expected_observed_date_raw=54000000,
        expected_snapshot_revision=frame["snapshot_revision"],
        expected_character_ids=ids,
    )
    require(all("death_record" not in row["current_person_state"] for row in normalized_legacy["character_observations"]),
            "Older absent optional leaf was filled with a fabricated record")
    result = {
        "status":"GREEN", "date":"2026-10-05", "iso_week":"2026-W41",
        "readiness":"static-ready native current reason leaf",
        "new_source_cases":1, "registered_existing_mcp_runs":1, "registered_query_calls":1,
        "wire":{"path":str(wire_path),"bytes":len(wire_bytes),"sha256":hashlib.sha256(wire_bytes).hexdigest()},
        "reason_values":actual, "strict_character_ids":ids,
        "native_snapshot_revision":frame["snapshot_revision"],
        "synthetic_fixture_date_raw":54000000,
        "frame_preserved_exactly":True, "old_optional_absence_preserved":True,
        "contract_projection":{"path":str(PROJECTED_CONTRACT),"sha256":hashlib.sha256(PROJECTED_CONTRACT.read_bytes()).hexdigest()},
        "python_optimized":sys.flags.optimize>0,"bytecode_disabled":sys.dont_write_bytecode,
        "native_game_queries":0,"sdk_pipe_ck3_window_operations":0,"new_game_days":0,
        "new_live_observations":0,"old_cases_rerun":0,"shared_source_writes":0,"git_operations":0,
        "qualification":"Constructed current-person producer fixture only; no native death execution, live reason, selected-event inference or complete normal-finalizer claim",
    }
    output_path.write_bytes((json.dumps(result,indent=2,ensure_ascii=True)+"\n").encode("utf-8"))
    print(json.dumps({"status":"GREEN","result":str(output_path),"existing_mcp_calls":1}))

if __name__ == "__main__":
    require(len(sys.argv)==4 and sys.dont_write_bytecode and sys.flags.optimize>=1,
            "Usage: python -B -O runner.py PROJECTION_ROOT NATIVE_WIRE OUTPUT")
    asyncio.run(run_reason_wire())
