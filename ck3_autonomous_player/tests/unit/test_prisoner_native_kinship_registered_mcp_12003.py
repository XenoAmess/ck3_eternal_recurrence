"""First registered-MCP compound for genuine whole native kinship collection wires.

Prepared FIRST_NOT_RUN. Root alone runs this standalone consumer after the new
native producer writes all six fixtures. Native kinship callbacks are synthetic; there
are no live queries, gameplay actions or release-effect readiness claims.
"""

from __future__ import annotations

import argparse
import asyncio
import copy
import hashlib
import json
from pathlib import Path
import sys


_CASES = (
    "nonchild_close_family", "unrelated", "sample_drift",
    "wrong_generation", "wrong_jailer", "not_paused",
)
_STEP = "query-player-prisoner-collection-private-v1-ransom-ordinal-2"
_TOOL = "ck3_query_player_prisoner_collection_private_v1"
_EXE_SHA256 = "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6"
_PRISONERS = [54235, 56063, 61540, 70766]
_SYNTHETIC_COSTS = [100_001 * index for index in range(1, 11)]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--native-fixture-dir", "--native-fixtures-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    sys.path.insert(0, str(args.source_root / "ck3_autonomous_player/src"))
    from xar_autoplayer.bridge.mcp_server import create_server
    from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
    from xar_autoplayer.bridge.prisoner_native_kinship_contract_12003 import (
        normalize_prisoner_native_kinship_12003,
    )

    native_wires = {}
    native_inputs = {}
    for case in _CASES:
        path = args.native_fixture_dir / f"{case}.json"
        raw = path.read_bytes()
        native_wires[case] = json.loads(raw)
        native_inputs[case] = {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest()}

    checks = 0

    def check(condition: bool, message: str) -> None:
        nonlocal checks
        checks += 1
        if not condition:
            raise AssertionError(message)

    class Endpoint:
        pipe_name = r"\\.\pipe\xar_prisoner_native_kinship_12003_fixture"

        def __init__(self) -> None:
            self.requests = []
            self.on_frame = None
            self.case = None

        def start(self, on_frame, on_disconnect) -> None:
            self.on_frame = on_frame

        def publish(self, packet: dict) -> None:
            self.on_frame(copy.deepcopy(packet))

        def send(self, request: dict) -> None:
            if request.get("type") == "ping":
                return
            check(request.get("type") == "execute_step" and request.get("step") == _STEP,
                  "only the existing selected-ordinal read-only collection query is dispatched")
            check(request.get("expected_revision") == 1014,
                  "public request binds to the actual native revision")
            check("played_character_id" not in request,
                  "player role comes from the native frame")
            check(self.case in native_wires, "the selected native fixture exists")
            self.requests.append(copy.deepcopy(request))
            # The complete native collection envelope is passed through intact.
            # No preview, collection row or transport-derived query field is made here.
            self.publish({
                "type": "command_result", "protocol_version": 1,
                "request_id": request["request_id"], "ok": True,
                "result": native_wires[self.case],
            })

        def close(self) -> None:
            pass

        def transport_error(self):
            return None

    async def exercise() -> dict:
        endpoint = Endpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name, endpoint=endpoint, command_timeout_seconds=0.1,
        )
        driver.allow_private_prisoner_collection_query = True
        observed = {}
        try:
            endpoint.publish({
                "type": "hello", "protocol_version": 1, "bridge_version": "0.1.0",
                "pid": 7878, "session_generation": 0,
                "game_version": "1.20.0.3", "expected_ck3_version": "1.20.0.3",
                "executable_sha256": _EXE_SHA256,
                "capabilities": ["game.state.snapshot", "game.command." + _STEP],
            })
            endpoint.publish({
                "type": "state_snapshot", "protocol_version": 1,
                "snapshot_id": "native:1014", "revision": 1014,
                "state": {
                    "phase": "map_hud", "date": "synthetic:release-source721",
                    "date_raw": 53286360, "speed": 1, "paused": True, "map_ready": True,
                    "history": [], "active_event": None,
                    "pending_character_interaction": None,
                    "played_character": {"character_id": 29829, "alive": True},
                    "one_life_settlement": None, "active_wars": [], "player_armies": [],
                },
            })
            server = create_server(driver)
            tools = {tool.name: tool for tool in await server.list_tools()}
            check(_TOOL in tools, "the existing private collection MCP is registered")
            check(tools[_TOOL].annotations.read_only_hint is True,
                  "the registered query remains read-only")
            for index, case in enumerate(_CASES):
                endpoint.case = case
                wire = native_wires[case]
                check(isinstance(wire, dict) and wire.get("step") == _STEP,
                      f"{case}: whole native envelope selects source ordinal 2")
                check(not any(key.startswith("queried_") for key in wire),
                      f"{case}: native wire does not invent transport fields")
                before = driver.take_snapshot()
                response = await server.call_tool(_TOOL, {
                    "expected_revision": before["revision"], "ransom_ordinal": 2,
                })
                check(not response.is_error, f"{case}: actual transport accepts the native producer wire")
                actual = response.structured_content
                observed[case] = actual
                check(all(actual.get(key) == value for key, value in wire.items()),
                      f"{case}: the entire native collection envelope survives normalization")
                check(actual["queried_revision"] == before["revision"]
                      and actual["queried_native_revision"] == 1014
                      and actual["queried_snapshot_id"] == "native:1014",
                      f"{case}: production transport supplies public/native query bindings")
                check(actual["exact_ck3_build"] == "1.20.0.3"
                      and actual["exe_sha256"].upper() == _EXE_SHA256,
                      f"{case}: existing exact-build provenance is retained")
                collection = actual["player_prisoner_collection"]
                rows = collection["prisoners"]
                check(collection["schema_version"] == 7
                      and collection["snapshot_revision"] == 1014
                      and collection["date_raw"] == 53286360
                      and collection["played_character_id"] == 29829
                      and collection["played_house_id"] == 174
                      and collection["played_dynasty_id"] == 174
                      and collection["played_dread_raw"] == 1680000
                      and collection["collection_complete"] is True
                      and collection["total_count"] == collection["returned_count"] == 4,
                      f"{case}: complete source721 schema-v7 metadata stays unchanged")
                check([row["prisoner_character_id"] for row in rows] == _PRISONERS
                      and [row["source_ordinal"] for row in rows] == [0, 1, 2, 3]
                      and all(row["jailer_character_id"] == 29829
                              and row["collection_owner_character_id"] == 29829
                              and row["custody_relation_verified"] is True for row in rows),
                      f"{case}: complete full-ID player custody stays unchanged")
                check(rows[2]["dynasty_id"] == 2237
                      and rows[2]["is_child_of_played_character"] is False
                      and rows[2]["primary_title_tier_raw"] is None,
                      f"{case}: the actual selected prisoner metadata is retained")
                check(all(row["unconditional_release_preview"].get("unavailable_reason") == "not_evaluated"
                          for ordinal, row in enumerate(rows) if ordinal != 2),
                      f"{case}: release evaluation belongs only to the selected prisoner")
                kinship = rows[2]["native_kinship"]
                check(all(row["native_kinship"].get("unavailable_reason") == "not_evaluated"
                          for ordinal, row in enumerate(rows) if ordinal != 2),
                      f"{case}: only requested ordinal has native kinship evaluated")
                if case in {"nonchild_close_family", "unrelated"}:
                    related = case == "nonchild_close_family"
                    check(kinship["status"] == "available"
                          and kinship["is_close_family_of_played_character"] is related
                          and kinship["is_close_or_extended_family_of_played_character"] is related,
                          f"{case}: actual native true/false booleans survive whole wire")
                    check(kinship["source_ordinal"] == 2
                          and kinship["prisoner_character_id"] == 61540
                          and kinship["jailer_character_id"] == 29829
                          and kinship["proof_epoch"] == actual["observation_revision"],
                          f"{case}: exact custody, ordinal and collection proof are retained")
                    detached = normalize_prisoner_native_kinship_12003(
                        kinship, native_revision=1014, date_raw=53286360,
                        proof_epoch=actual["observation_revision"],
                        player_character_id=29829, prisoner_character_id=61540,
                        source_ordinal=2, selected_ordinal=2,
                    )
                    check(detached == kinship and detached is not kinship,
                          f"{case}: strict transport value is a detached copy")
                else:
                    reason = ("native_sample_drift" if case == "sample_drift"
                              else "not_paused" if case == "not_paused"
                              else "custody_relation_unverified")
                    check(kinship["status"] == "unavailable"
                          and kinship["unavailable_reason"] == reason
                          and not any(key.startswith("is_close_") for key in kinship),
                          f"{case}: typed failure is not a false native relation or null")
                snapshot = driver.take_snapshot()
                history = snapshot["native_command_history"]
                check(len(history) == index + 1 and history[-1]["command"] == _STEP
                      and history[-1]["ok"] is True and history[-1]["result"] == actual,
                      f"{case}: the production driver records the actual validated query")
                check(snapshot["native_revision"] == 1014
                      and snapshot["date_raw"] == 53286360 and snapshot["paused"] is True,
                      f"{case}: the observer leaves the paused native frame unchanged")
            check(len(endpoint.requests) == len(_CASES),
                  "exactly six registered read-only queries and zero actions")
            return {"cases": observed, "requests": endpoint.requests,
                    "history": driver.take_snapshot()["native_command_history"]}
        finally:
            driver.close()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "schema": "xar.prisoner-native-kinship-registered-mcp-12003.v1",
        "status": "RED", "native_inputs": native_inputs,
        "source_root": str(args.source_root), "live_queries": 0, "game_actions": 0,
        "kinship_actions": 0, "full_effect_readiness_qualified": False,
        "amount_kind": "synthetic-native-fixture",
    }
    try:
        observed = asyncio.run(exercise())
        with (args.output_dir / "observed.json").open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(observed, ensure_ascii=False, indent=2) + "\n")
        report.update(status="GREEN", checks=checks, cases=len(_CASES),
                      readonly_mcp_queries=len(_CASES), output_file_count=2)
    except Exception as error:
        report.update(checks=checks, error=f"{type(error).__name__}: {error}")
        raise
    finally:
        with (args.output_dir / "RESULT.json").open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
