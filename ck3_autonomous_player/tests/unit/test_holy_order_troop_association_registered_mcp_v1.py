"""Source-backed HolyOrder associated Army references survive registered MCP, offline."""
from __future__ import annotations

import argparse
import asyncio
import copy
import hashlib
import inspect
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import patch


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--native-fixture", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.source_root / "ck3_autonomous_player/src"))
    from xar_autoplayer.bridge.mcp_server import create_server
    from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, NativeProtocolState
    from xar_autoplayer.bridge.player_holy_order_context_private_transport import (
        normalize_player_holy_order_context_v1,
        query_player_holy_order_context_private_v1,
    )

    tool_name = "ck3_query_player_holy_order_context_v1"
    native_bytes = args.native_fixture.read_bytes()
    packets = json.loads(native_bytes)["samples"]
    checks = 0
    def check(condition: bool, message: str) -> None:
        nonlocal checks
        checks += 1
        if not condition:
            raise AssertionError(message)

    class Driver:
        command_timeout_seconds = 1.0
        allow_private_player_religion_context_query = True
        query_player_holy_order_context_private_v1 = (
            NativeHeadlessGameplayDriver.query_player_holy_order_context_private_v1
        )
        def __init__(self, packet: dict) -> None:
            self.packet = packet
            result = packet["result"]
            body = result["player_holy_order_context"]
            self.snapshot = {
                "snapshot_id": f"native:{result['snapshot_revision']}",
                "revision": result["snapshot_revision"] + 1,
                "native_revision": result["snapshot_revision"],
                "date_raw": result["date_raw"],
                "played_character": {"character_id": body["played_character_id"], "alive": True},
                "paused": True, "map_ready": True,
                "diagnostics": {"hello": {
                    "expected_ck3_version": result["game_version"],
                    "expected_ck3_sha256": result["executable_sha256"],
                }},
            }
            self.sent: list[dict] = []
            self.endpoint = self
            self.state = NativeProtocolState("offline-fixture:holy-order-troop-association")
        def take_snapshot(self) -> dict:
            return copy.deepcopy(self.snapshot)
        def send(self, request: dict) -> None:
            check(request["request_id"] == self.packet["request_id"], "native request identity")
            self.sent.append(copy.deepcopy(request))
            check(self.state.ingest(copy.deepcopy(self.packet)) == "command_result", "real protocol ingest")

    async def exercise() -> list[dict]:
        observed = []
        check(len(packets) == 4, "four focused new native association scenarios")
        for index, packet in enumerate(packets):
            driver = Driver(packet)
            server = create_server(driver)
            tools = {tool.name: tool for tool in await server.list_tools()}
            check(tools[tool_name].annotations.read_only_hint, "existing registered tool remains readonly")
            request_id = packet["request_id"]
            with patch("xar_autoplayer.bridge.g2_private_query_transport.uuid.uuid4",
                       return_value=SimpleNamespace(hex=request_id[len("g2-read-"):])):
                response = await server.call_tool(tool_name, {"expected_revision": driver.snapshot["revision"]})
            check(not response.is_error, "registered MCP accepts native association observation")
            actual = response.structured_content
            native = packet["result"]["player_holy_order_context"]
            check({key: actual[key] for key in native} == native, "complete native domain preserved")
            check(len(driver.sent) == 1 and driver.sent[0]["step"] == "query-player-holy-order-context-v1",
                  "single existing native query dispatch")
            check("played_character_id" not in driver.sent[0], "actual player supplied by native frame")
            association = actual["rows"][0]["military_terms"]["troop_association"]
            check(actual["rows"][0]["military_terms"]["can_hire"] is False
                  and association["applies_to_player"] is True,
                  "already-hired final false retains player-owned association")
            if index in (1, 3):
                check(association["available"] is False and association["rows"] == []
                      and association["unavailable_reason"] == (
                          "native_troop_association_binding_unavailable" if index == 1
                          else "native_troop_association_vector_unavailable"),
                      "missing binding/vector differs from available knownempty")
            else:
                members = association["rows"]
                ids = [0xA1000000, 0xA2000001, 0xA1000000, 0xA3000002,
                       0xA4000003, 0xFFFFFFFF, 0xA7000006, 0xA8000004]
                check(association["available"] is True and [m["regiment_id"] for m in members] == ids,
                      "source order, duplicate IDs and full generations retained")
                for i, member in enumerate(members):
                    check(member["available"] is True and member["unavailable_reason"] is None,
                          "known fallback outcome is available")
                    if index == 2:
                        check(member["regiment_resolved"] is False and member["native_carmy_id"] is None
                              and member["combat_id"] is None,
                              "null native registry follows canonical invalid fallback")
                    elif i in (0, 2):
                        check(member["regiment_resolved"] is True
                              and member["native_carmy_id"] == 0xB1000000
                              and member["native_carmy_resolved"] is True
                              and member["combat_id"] == 0xC1000000 and member["combat_resolved"] is True,
                              "resolved Regiment, nativeArmy and Combat retain distinct identities")
                    elif i == 1:
                        check(member["regiment_resolved"] is True and member["native_carmy_id"] is None
                              and member["native_carmy_resolved"] is False,
                              "unraised Regiment is not an unknown reference")
                    elif i == 4:
                        check(member["regiment_resolved"] is True and member["native_carmy_id"] == 0xB2000001
                              and member["native_carmy_resolved"] is False and member["combat_id"] is None,
                              "stale Army generation rawref retained without substituting next generation")
                    else:
                        check(member["regiment_resolved"] is False and member["native_carmy_id"] is None,
                              "invalid/stale/sentinel/outofrange/null slots follow native fallback")
                if index == 0:
                    # Explicitly separate public CUnit IDs from internal CArmy IDs.
                    # Signed legacy native_carmy_id is joined by its full uint32 bits.
                    public = [{"army_id": 77, "native_carmy_id": 0xB1000000 - (1 << 32)},
                              {"army_id": 88, "native_carmy_id": 0xB6000001 - (1 << 32)}]
                    joined = [unit["army_id"] for member in members if member["native_carmy_resolved"]
                              for unit in public if (unit["native_carmy_id"] & 0xFFFFFFFF) == member["native_carmy_id"]]
                    check(joined == [77, 77], "fullbit join preserves association multiplicity without ID relabeling")
            empty = actual["rows"][1]["military_terms"]["troop_association"]
            check(empty["rows"] == [] and empty["available"] is (index != 1),
                  "valid empty source vector is distinct from missing binding")
            other = actual["rows"][2]["military_terms"]["troop_association"]
            check(other["available"] is True and other["applies_to_player"] is False and other["rows"] == [],
                  "other employer association inapplicable")
            check(actual["rows"][3]["military_terms"] is None, "nonmilitary association absent")
            observed.append(actual)
        old = copy.deepcopy(packets[0]["result"]["player_holy_order_context"])
        for row in old["rows"][:3]:
            del row["military_terms"]["troop_association"]
        check(normalize_player_holy_order_context_v1(old, snapshot=Driver(packets[0]).snapshot) == old,
              "historical wires do not require the new association field")
        return observed

    args.output_dir.mkdir(parents=True, exist_ok=True)
    report = {"schema": "xar.holy-order-troop-association-mcp-validation.v1", "status": "RED"}
    try:
        observed = asyncio.run(exercise())
        (args.output_dir / "observed.json").write_text(json.dumps(observed, ensure_ascii=False, indent=2) + "\n",
                                                     encoding="utf-8")
        report.update(status="GREEN", samples=len(packets), checks=checks, tool=tool_name,
                      native_fixture=str(args.native_fixture),
                      native_fixture_sha256=hashlib.sha256(native_bytes).hexdigest(),
                      source_root=str(args.source_root), native_domain_preserved=True,
                      live_queries=0, sdk_sessions=0, game_actions=0,
                      new_path_source=[str(inspect.getsourcefile(fn)) for fn in (
                          normalize_player_holy_order_context_v1,
                          query_player_holy_order_context_private_v1)])
    except Exception as error:
        report.update(checks=checks, error=str(error))
        raise
    finally:
        with (args.output_dir / "RESULT.json").open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
