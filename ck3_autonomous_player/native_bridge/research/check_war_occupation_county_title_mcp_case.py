"""One new production-serializer JSON case through existing registered MCP.

No game, transport process, listener, source mutation or old fixture suite runs.
The legacy branch copies this same emitted body and removes only county_title_id.
"""
from __future__ import annotations

import argparse
import asyncio
import copy
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import sys
import traceback

sys.dont_write_bytecode = True
CHECKS: list[str] = []


def require(condition: object, message: str) -> None:
    if condition is not True:
        raise RuntimeError(message)
    CHECKS.append(message)


def pin(path: Path) -> dict[str, object]:
    raw = path.read_bytes()
    return {"path": path.resolve().as_posix(), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}


def write(path: Path, value: object) -> None:
    path.write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def load_projected_contract(source_root: Path, contract: Path) -> None:
    sys.path.insert(0, str(source_root / "tools"))
    sys.path.insert(0, str(source_root / "ck3_autonomous_player" / "src"))
    importlib.import_module("xar_autoplayer.bridge")
    name = "xar_autoplayer.bridge.war_occupation_targets_contract"
    spec = importlib.util.spec_from_file_location(name, contract)
    if spec is None or spec.loader is None:
        raise RuntimeError("External occupation contract module could not be loaded")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)


class SerializedAnswerDriver:
    """Owned in-memory actual-query seam; answer is real emitted native JSON."""

    def __init__(self, answer: dict[str, object]) -> None:
        self.answer = copy.deepcopy(answer)
        body = answer["war_occupation_targets_v1"]
        self.step = "query-war-occupation-targets-v1-" + str(body["war_id"])
        self.public_revision = 1
        self.snapshot = {
            "snapshot_id": "native:" + str(body["snapshot_revision"]),
            "revision": self.public_revision,
            "native_revision": body["snapshot_revision"],
            "date_raw": body["date_raw"],
            "paused": True,
            "played_character": {"character_id": body["actor_character_id"], "alive": True},
            "active_wars": [{"war_id": body["war_id"], "player_side": body["player_side"]}],
        }
        self.executed: list[dict[str, object]] = []

    def take_snapshot(self) -> dict[str, object]:
        return copy.deepcopy(self.snapshot)

    def capabilities(self) -> dict[str, object]:
        return {
            "bridge_capabilities": ["game.command.query-war-occupation-targets-v1-N"],
            "action_steps": [self.step],
        }

    def execute_step(self, step: str, *, expected_revision: int | None = None) -> dict[str, object]:
        require(step == self.step, "Existing service dispatches the exact occupation step")
        require(expected_revision == self.public_revision, "Existing service preserves expected public revision")
        self.executed.append({"step": step, "expected_revision": expected_revision})
        return copy.deepcopy(self.answer)


IDENTITY_OCCUPATION_FIELDS = (
    "holding_title_id", "province_id", "legal_holder_character_id", "territory_side",
    "occupation_observable", "is_occupied", "occupying_character_id", "occupier_side",
    "counted_occupied_by_opposing_side",
)


def require_preserved(result: dict[str, object], native_body: dict[str, object], label: str) -> dict[str, object]:
    require(result.get("read_only") is True, label + ": existing registered read-only service result")
    body = result["war_occupation_targets_v1"]
    require(body["schema"] == native_body["schema"] and body["schema_version"] == native_body["schema_version"], label + ": existing schema unchanged")
    require(body["available"] is True and body["collection_complete"] is True, label + ": complete native occupation stays available")
    require(body["side_counts"] == native_body["side_counts"], label + ": native side counts preserved exactly")
    require(len(body["rows"]) == len(native_body["rows"]), label + ": native row order/count retained")
    for index, (observed, emitted) in enumerate(zip(body["rows"], native_body["rows"])):
        require(all(observed[key] == emitted[key] for key in IDENTITY_OCCUPATION_FIELDS), label + f": row{index} full identity/occupation preserved")
    return body


async def run_case(args: argparse.Namespace) -> dict[str, object]:
    raw = args.native_json.read_bytes()
    wrapper = json.loads(raw)
    require(isinstance(wrapper, dict), "Production serializer fixture is a JSON object")
    require(wrapper.get("type") == "command_result" and wrapper.get("protocol_version") == 1 and wrapper.get("ok") is True, "Native fixture retains the existing successful command-result wrapper")
    emitted = wrapper["result"]
    require(isinstance(emitted, dict), "Existing command-result wrapper contains the production query envelope")
    require(isinstance(emitted.get("war_occupation_targets_v1"), dict), "Production dump is the existing native query envelope")
    native = emitted["war_occupation_targets_v1"]
    require(native.get("available") is True and native.get("collection_complete") is True, "Single new native collection is available and complete")
    expected_counties = [row["county_title_id"] for row in native["rows"]]
    require(args.expected_county_title_id in expected_counties, "Generation-bearing expected county FullID is emitted by the real reader/serializer")
    require(args.expected_county_title_id > 0xFFFFFF, "New production case actually carries a generated county FullID")
    require(0 in expected_counties, "Same real production collection carries a legally resolved county FullID zero")
    require(sum(value is None for value in expected_counties) >= 3, "Same production collection includes three unavailable county joins")

    load_projected_contract(args.source_root, args.contract)
    from xar_autoplayer.bridge import service as service_module
    from xar_autoplayer.bridge.mcp_server import create_server
    require(Path(service_module.normalize_war_occupation_targets_v1.__code__.co_filename).resolve() == args.contract.resolve(), "Existing service uses the external projected production normalizer")
    driver = SerializedAnswerDriver(emitted)
    server = create_server(driver)
    arguments = {"war_id": native["war_id"], "expected_revision": driver.public_revision}
    reply = await server.call_tool("ck3_query_war_occupation_targets_v1", arguments)
    result = reply.structured_content
    require(isinstance(result, dict), "Actual registered MCP returns structured content")
    body = require_preserved(result, native, "new-production-case")
    require([row["county_title_id"] for row in body["rows"]] == expected_counties, "Registered MCP preserves emitted county FullIDs and nulls exactly")
    write(args.out / "NEW-REGISTERED-MCP-RESULT.json", result)

    # Same-case compatibility branch. No second native case or old suite.
    legacy = copy.deepcopy(emitted)
    for row in legacy["war_occupation_targets_v1"]["rows"]:
        del row["county_title_id"]
    driver.answer = legacy
    legacy_reply = await server.call_tool("ck3_query_war_occupation_targets_v1", arguments)
    legacy_result = legacy_reply.structured_content
    require(isinstance(legacy_result, dict), "Same-case legacy branch returns actual registered MCP structured content")
    legacy_body = require_preserved(legacy_result, legacy["war_occupation_targets_v1"], "same-case-legacy-absence")
    require(all(row["county_title_id"] is None for row in legacy_body["rows"]), "Old body absence normalizes to county_title_id None")
    require(len(driver.executed) == 2, "One new emitted collection consumed once plus one same-body legacy branch")
    write(args.out / "SAME-CASE-LEGACY-ABSENCE-MCP-RESULT.json", legacy_result)

    return {
        "status": "GREEN",
        "readiness": "static-ready: one offline production reader/serializer case through existing registered MCP; no actual paused v64 game artifact",
        "native_fixture": pin(args.native_json),
        "projected_contract": pin(args.contract),
        "current_mcp_source": pin(args.source_root / "ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py"),
        "current_service_source": pin(args.source_root / "ck3_autonomous_player/src/xar_autoplayer/bridge/service.py"),
        "fixture_script": pin(Path(__file__)),
        "tool": "ck3_query_war_occupation_targets_v1",
        "arguments": arguments,
        "native_county_ids": expected_counties,
        "side_counts": native["side_counts"],
        "check_count": len(CHECKS), "explicit_require_checks": CHECKS,
        "registered_mcp_calls": 2,
        "new_native_collections": 1,
        "legacy_branch": "Copy of same emitted body; only county_title_id removed",
        "standalone_optimization_independent_checks": True,
        "tests_or_old_suites_rerun": False,
        "lane_game_days": 0, "game_sdk_calls": 0, "window_actions": 0,
        "shared_source_writes": 0, "Git_actions": 0,
        "results": [pin(args.out / "NEW-REGISTERED-MCP-RESULT.json"), pin(args.out / "SAME-CASE-LEGACY-ABSENCE-MCP-RESULT.json")],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--native-json", type=Path, required=True)
    parser.add_argument("--expected-county-title-id", type=int, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, default=Path("Z:/g69"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    try:
        result = asyncio.run(run_case(args))
    except Exception:
        failure = {"status":"HARNESS-RED", "traceback":traceback.format_exc(), "completed_require_checks":CHECKS, "lane_game_days":0, "game_sdk_calls":0}
        write(args.out / "HARNESS-RED.json", failure)
        raise
    write(args.out / "RESULT.json", result)
    print(json.dumps({"status":result["status"], "check_count":result["check_count"], "result":pin(args.out / "RESULT.json")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
