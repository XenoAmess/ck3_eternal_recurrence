"""FIRST compiled whole native wire through registered MCP and current consumer."""

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
    from xar_autoplayer.bridge.holy_order_current_reinforcement_v1 import (
        normalize_holy_order_current_reinforcement_v1,
    )
    from xar_autoplayer.bridge.player_holy_order_context_private_transport import (
        normalize_player_holy_order_context_v1,
    )
    from xar_autoplayer.holy_order_current_reinforcement_consumer_v1 import (
        consume_holy_order_current_reinforcement_v1,
    )

    native_bytes = args.native_fixture.read_bytes()
    document = json.loads(native_bytes)
    packets = document["samples"]
    checks = 0

    def check(ok: bool, reason: str) -> None:
        nonlocal checks
        checks += 1
        if not ok:
            raise AssertionError(reason)

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
                "paused": True,
                "map_ready": True,
                "diagnostics": {"hello": {
                    "expected_ck3_version": result["game_version"],
                    "expected_ck3_sha256": result["executable_sha256"],
                }},
            }
            self.sent = []
            self.endpoint = self
            self.state = NativeProtocolState("offline-fixture:holy-order-current-reinforcement")

        def take_snapshot(self) -> dict:
            return copy.deepcopy(self.snapshot)

        def send(self, request: dict) -> None:
            check(request["request_id"] == self.packet["request_id"], "real fixture request identity")
            self.sent.append(copy.deepcopy(request))
            check(self.state.ingest(copy.deepcopy(self.packet)) == "command_result", "real native protocol ingest")

    async def exercise() -> list[dict]:
        check(len(packets) == 2, "two new whole-provider scenes")
        check("synthetic" in document["fixture_provenance"], "synthetic native callback/game-memory provenance explicit")
        results = []
        for scene, packet in enumerate(packets):
            driver = Driver(packet)
            server = create_server(driver)
            tool_name = "ck3_query_player_holy_order_context_v1"
            registered = {tool.name: tool for tool in await server.list_tools()}
            check(registered[tool_name].annotations.read_only_hint, "existing registered readonly MCP")
            request_id = packet["request_id"]
            with patch("xar_autoplayer.bridge.g2_private_query_transport.uuid.uuid4",
                       return_value=SimpleNamespace(hex=request_id[len("g2-read-"):])):
                response = await server.call_tool(tool_name, {"expected_revision": driver.snapshot["revision"]})
            check(not response.is_error, "complete native wire passes real registered Service")
            actual = response.structured_content
            native = packet["result"]["player_holy_order_context"]
            check({key: actual[key] for key in native} == native, "whole native domain preserved without row replacement")
            check(len(driver.sent) == 1 and driver.sent[0]["step"] == "query-player-holy-order-context-v1",
                  "one existing native query per new scene")
            current = consume_holy_order_current_reinforcement_v1(actual)
            check(len(current["orders"]) == 3, "actual military candidates consumed; nonmilitary omitted")
            primary, foreign, empty = current["orders"]
            if scene == 0:
                occurrences = primary["persistent_occurrences"]
                check(primary["available"] is True and primary["source_count"] == 5, "new roster observed completely")
                check([row["persistent_regiment_id"] for row in occurrences] == [
                    0xA1000000, 0xA2000001, 0xA1000000, 0xA3000002, 0xFFFFFFFF
                ], "source order, generations and duplicate occurrences preserved")
                first = occurrences[0]
                check(first["owner_character_id"] == 40001 and first["owner_character_id"] != native["played_character_id"],
                      "persistent owner distinguished from employer/Unit owner")
                check(first["monthly_replenishment_fraction_raw"] == 3000 and first["native_months_to_full"] == 4,
                      "fresh native fraction and months retained")
                check(first["chunks"][0]["observed_deficit"] == 40
                      and first["chunks"][0]["native_can_replenish"] is True
                      and first["chunks"][0]["native_chunk_can_replenish"] is False,
                      "present deficit uses physical counts; independent bools not combined")
                zero = occurrences[1]
                check(zero["monthly_replenishment_fraction_raw"] == 0 and zero["native_months_to_full"] == 0
                      and zero["chunks"][0]["current_soldiers"] == 0
                      and zero["chunks"][0]["state_raw"] == 3
                      and zero["chunks"][0]["observed_deficit"] == 100,
                      "zero timing/fraction not promoted to full strength")
                check(occurrences[3]["resolved"] is False and occurrences[3]["owner_character_id"] is None
                      and occurrences[3]["chunks"] == [], "stale Regi generation has no fabricated actual fields")
                check(foreign["available"] is True and len(foreign["persistent_occurrences"]) == 1,
                      "current candidate refill observable despite another employer")
                check(empty["available"] is True and empty["source_count"] == 0 and empty["persistent_occurrences"] == [],
                      "legal empty persistent roster")
            else:
                check(primary["available"] is False and primary["source_count"] is None
                      and primary["persistent_occurrences"] == [], "unavailable new callback is distinct from empty/zero")
            roles = primary["army_roles"]
            check(roles["available"] is True and len(roles["rows"]) == 2, "independent Army roles remain observed")
            check([role["association_index"] for role in roles["rows"]] == [0, 1], "association multiplicity retained")
            check(all(role["native_carmy_id"] == 0xC1000000 and role["public_army_id"] == 0xD1000000
                      and role["commander_character_id"] == 35000 and role["owner_character_id"] == 29829
                      for role in roles["rows"]), "Army commander, public Unit and owner have distinct copied identities")
            check(foreign["army_roles"]["applies_to_player"] is False and foreign["army_roles"]["rows"] == [],
                  "foreign order Army-role observation explicitly inapplicable")
            results.append(current)
        return results

    args.output_dir.mkdir(parents=True, exist_ok=True)
    report = {"schema": "xar.holy-order-current-reinforcement-first.v1", "status": "RED"}
    try:
        observations = asyncio.run(exercise())
        (args.output_dir / "CURRENT-CONSUMPTION.json").write_text(
            json.dumps(observations, indent=2) + "\n", encoding="utf-8")
        report.update(
            status="GREEN", checks=checks, samples=len(packets),
            source_root=str(args.source_root), native_fixture=str(args.native_fixture),
            native_fixture_sha256=hashlib.sha256(native_bytes).hexdigest(),
            native_domain_preserved=True, synthetic_callbacks=True, live=False,
            game_actions=0, new_game_days=0,
            source_paths=[str(inspect.getsourcefile(fn)) for fn in (
                normalize_player_holy_order_context_v1,
                normalize_holy_order_current_reinforcement_v1,
                consume_holy_order_current_reinforcement_v1,
            )],
        )
    except Exception as error:
        report.update(checks=checks, error=str(error))
        raise
    finally:
        with (args.output_dir / "RESULT.json").open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
