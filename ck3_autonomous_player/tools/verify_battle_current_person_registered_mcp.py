"""Replay one native current-person serializer frame through registered MCP.

Run with -B -O and mcp==2.0.0. This is an offline fixture, with no CK3 process
query, input, game-day or production-live credit. EXPECTED contains one case
with wire_file, expected_revision, expected_observed_date_raw,
expected_character_ids and expected_character_observations; --wire optionally
overrides that case's wire_file. The native Bucket case remains native-only.

The namespace loader reuses the successful external harness fix: finish the
contract import before bridge/__init__ can eagerly import native_driver.
That original import RED and the subsequent GREEN remain in their original
external evidence; this reusable export does not claim another test run.
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


TOOL_NAME = "ck3_query_battle_terminal_transition_v1"
MODULE_NAME = "xar_autoplayer.bridge.battle_terminal_transition_contract"
MIRROR_KEYS = (
    "prior_combat_id", "subject_public_cunit_id", "terminal_journal", "prior",
    "removal", "subject", "successor", "battle_terminal_transition_ready",
    "unavailable_reason", "character_observations",
)
EXE_SHA256 = "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def load_bridge(repo_tree: Path):
    source = repo_tree / "ck3_autonomous_player/src"
    bridge_path = source / "xar_autoplayer/bridge"
    contract_path = bridge_path / "battle_terminal_transition_contract.py"
    sys.path.insert(0, str(source))
    import xar_autoplayer

    package = types.ModuleType("xar_autoplayer.bridge")
    package.__package__ = "xar_autoplayer.bridge"
    package.__path__ = [str(bridge_path)]
    sys.modules["xar_autoplayer.bridge"] = package
    xar_autoplayer.bridge = package
    spec = importlib.util.spec_from_file_location(MODULE_NAME, contract_path)
    require(spec is not None and spec.loader is not None, "Cannot load source contract")
    contract = importlib.util.module_from_spec(spec)
    sys.modules[MODULE_NAME] = contract
    spec.loader.exec_module(contract)
    from mcp import Client
    from xar_autoplayer.bridge.mcp_server import create_server
    return contract, create_server, Client, contract_path


class CapturedWireDriver:
    """Replay the serializer body with the existing fixture envelope."""

    def __init__(self, wire: dict, case: dict, contract):
        wire = wire["result"] if isinstance(wire.get("result"), dict) else wire
        require(case.get("tool_name", TOOL_NAME) == TOOL_NAME, "Unexpected fixture tool")
        self.fixture_envelope = "battle_terminal_transition" not in wire
        self.frame = wire if self.fixture_envelope else wire["battle_terminal_transition"]
        require(isinstance(self.frame, dict), "Native serializer frame is missing")
        self.public_revision = case["expected_revision"]
        self.native_revision = self.frame["snapshot_revision"]
        self.date_raw = case["expected_observed_date_raw"]
        self.player_character_id = 29829
        self.game_version = "1.20.0.3"
        self.exe_sha256 = EXE_SHA256
        self.steps = []
        prior = self.frame["prior_combat_id"]
        subject = self.frame["subject_public_cunit_id"]
        self.arguments = {
            "prior_combat_id": None if prior == -1 else prior,
            "subject_public_cunit_id": None if subject == -1 else subject,
            "expected_revision": self.public_revision,
            "after_terminal_sequence": self.frame["terminal_journal"]["requested_after_sequence"],
            "character_ids": case["expected_character_ids"],
        }
        self.step = contract.query_battle_terminal_transition_v1_step(
            self.arguments["prior_combat_id"], self.arguments["subject_public_cunit_id"],
            self.arguments["after_terminal_sequence"], self.arguments["character_ids"],
        )
        self.capability = contract.QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY
        if self.fixture_envelope:
            wire = {
                "step": self.step, "accepted": True, "status": self.frame["status"],
                "query_sequence": 1, "snapshot_revision": self.native_revision,
                "battle_terminal_transition": self.frame,
            }
        self.wire = wire
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
            "episode_run_id": f"offline-native-wire-robert-{self.player_character_id}",
            "played_character": {"character_id": self.player_character_id, "alive": True},
            "diagnostics": {"hello": {
                "game_version": self.game_version, "executable_sha256": self.exe_sha256,
            }},
        }

    def execute_step(self, step, *, expected_revision=None):
        require(step == self.step, "MCP/service changed the native query scope")
        require(expected_revision == self.public_revision, "MCP/service changed the revision")
        self.steps.append(step)
        result = {
            key: copy.deepcopy(self.wire[key]) for key in (
                "step", "accepted", "status", "query_sequence", "snapshot_revision",
                "battle_terminal_transition",
            )
        }
        result["backend_id"] = "current-person-native-wire-fixture"
        for key in MIRROR_KEYS:
            if key in self.frame:
                result[key] = copy.deepcopy(self.frame[key])
        return result

    def wait_for_change(self, after_revision, *, timeout_seconds):
        raise RuntimeError("A current-person read must not advance any state")


async def run(args) -> None:
    repo_tree = args.repo_tree.resolve()
    contract, create_server, Client, contract_path = load_bridge(repo_tree)
    expected_path = args.expected.resolve()
    expected_bytes = expected_path.read_bytes()
    expected = json.loads(expected_bytes)
    require(len(expected["cases"]) == 1, "Expected the sole current-person wire case")
    case = expected["cases"][0]
    if args.wire is not None:
        wire_path = args.wire.resolve()
    else:
        wire_path = Path(case["wire_file"])
        if not wire_path.is_absolute():
            wire_path = expected_path.parent / wire_path
    wire_bytes = wire_path.read_bytes()
    driver = CapturedWireDriver(json.loads(wire_bytes), case, contract)
    async with Client(create_server(driver)) as client:
        listed = await client.list_tools()
        require(TOOL_NAME in {tool.name for tool in listed.tools}, "MCP tool is not registered")
        response = await client.call_tool(TOOL_NAME, driver.arguments)
    require(not response.is_error, f"Registered MCP failed: {response}")
    payload = response.structured_content
    require(isinstance(payload, dict), "MCP omitted structured content")
    require(payload["battle_terminal_transition"] == driver.frame, "MCP changed native frame values")
    require(payload["status"] == driver.frame["status"], "Leaf revoked frame status")
    require(driver.steps == [driver.step], "MCP made unexpected extra query calls")
    rows = payload["character_observations"]
    require(rows == case["expected_character_observations"], "Current-person rows differ from expectation")
    require([row["character_id"] for row in rows] == case["expected_character_ids"], "Actor order changed")
    require(payload["battle_terminal_transition"]["character_observations"] == rows, "MCP mirror differs")
    prior = payload["prior"]
    if prior is not None and prior.get("character_custody_in_observed_order") is not None:
        require(all("current_person_state" not in row for row in prior["character_custody_in_observed_order"]), "Historical custody acquired a current leaf")
    report = {
        "schema_version": 1, "status": "GREEN", "readiness": "static-ready",
        "evidence_level": "offline native serializer wire -> existing service -> registered MCP",
        "repo_tree": str(repo_tree), "contract_file": str(contract_path),
        "contract_sha256": hashlib.sha256(contract_path.read_bytes()).hexdigest(),
        "python": sys.executable, "python_version": sys.version, "command": sys.orig_argv,
        "bytecode_disabled": sys.dont_write_bytecode, "optimization_level": sys.flags.optimize,
        "expected_file": str(expected_path), "expected_sha256": hashlib.sha256(expected_bytes).hexdigest(),
        "wire_file": str(wire_path), "wire_sha256": hashlib.sha256(wire_bytes).hexdigest(),
        "name": case["name"], "tool_name": TOOL_NAME, "mcp_arguments": driver.arguments,
        "registered_mcp_runs": 1, "registered_query_calls": 1,
        "frame_preserved_exactly": True, "fixture_transport_envelope": driver.fixture_envelope,
        "character_observations": rows, "old_alive_custody_preserved": True,
        "historical_terminal_values_revoked": False,
        "native_only_case": expected.get("native_only_case"),
        "new_actual_actions": 0, "new_game_days": 0, "ck3_queries": 0,
        "boundary": "Current fixture observations only; no event severity, full roster, historical prowess, or live claim",
        "open_kaishek": {"status": "not-applicable", "reason": "Native DTO JSON and Python MCP; no Paradox script semantics are evaluated."},
    }
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "GREEN", "report": str(args.output), "cases": 1, "new_actual_actions": 0}))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-tree", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--expected", type=Path, required=True)
    parser.add_argument("--wire", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(sys.dont_write_bytecode and sys.flags.optimize >= 1, "Run this verifier with -B -O")
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
