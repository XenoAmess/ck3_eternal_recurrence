"""FIRST consumer of compiled whole native holy-order cost-context bytes, offline."""
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
    from xar_autoplayer.bridge.player_holy_order_hire_cost_context import validate_holy_order_hire_cost_context

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
            self.state = NativeProtocolState("offline-fixture:holy-order-hire-cost-context")

        def take_snapshot(self) -> dict:
            return copy.deepcopy(self.snapshot)

        def send(self, request: dict) -> None:
            check(request["request_id"] == self.packet["request_id"], "native request identity")
            self.sent.append(copy.deepcopy(request))
            check(self.state.ingest(copy.deepcopy(self.packet)) == "command_result", "real protocol ingest")

    async def exercise() -> list[dict]:
        observed = []
        check(len(packets) == 4, "four new compiled whole-context scenarios")
        branches = ["title_holder_zero", "ordinary", "patron_hire", "patron_recall",
                    "patron_hire", "ordinary", "ordinary", "ordinary"]
        for sample, packet in enumerate(packets):
            driver = Driver(packet)
            server = create_server(driver)
            tools = {tool.name: tool for tool in await server.list_tools()}
            check(tools[tool_name].annotations.read_only_hint, "existing registered query remains readonly")
            request_id = packet["request_id"]
            with patch("xar_autoplayer.bridge.g2_private_query_transport.uuid.uuid4",
                       return_value=SimpleNamespace(hex=request_id[len("g2-read-"):])):
                response = await server.call_tool(tool_name, {"expected_revision": driver.snapshot["revision"]})
            check(not response.is_error, "real registered MCP/Service accepts native observation")
            actual = response.structured_content
            native = packet["result"]["player_holy_order_context"]
            check({key: actual[key] for key in native} == native, "whole native domain retained without transplant")
            check(len(driver.sent) == 1 and driver.sent[0]["step"] == "query-player-holy-order-context-v1",
                  "one existing native query dispatch")
            check("played_character_id" not in driver.sent[0], "native frame supplies actual player")
            rows = actual["rows"]
            check(len(rows) == 9 and rows[8]["military_terms"] is None, "nonmilitary observer absent")
            for index, row in enumerate(rows[:8]):
                terms = row["military_terms"]
                context = terms["hire_cost_context"]
                check(terms["can_hire"] is False and terms["available"] is (sample != 1),
                      "independent source input survives final false and resource unavailable")
                if sample == 2:
                    check(context["available"] is False and context["order_title_id"] is None
                          and context["cost_branch"] is None
                          and context["unavailable_reason"] == "native_hire_cost_context_binding_unavailable",
                          "missing binding distinctly unavailable")
                    continue
                check(context["order_title_id"] == (0xFFFFFFFF if index == 7 else 0xB1000000 + index)
                      and context["order_title_resolved"] is (index not in (5, 7))
                      and context["cost_branch"] == branches[index],
                      "fullgeneration, sentinel and source branch retained")
                if index == 0:
                    check(context["available"] is True and context["title_holder_is_player"] is True
                          and context["patron_is_player"] is None and context["employed_by_other"] is None
                          and context["selected_patron_multiplier_raw"] is None,
                          "holder zero exits before later patron inputs")
                elif index in (2, 3, 4):
                    check(context["patron_is_player"] is True and context["employed_by_other"] is (index == 3),
                          "other/empty/current-player employment distinctions retained")
                    if sample == 3 and index == 3:
                        check(context["available"] is False and context["selected_patron_multiplier_raw"] is None
                              and context["unavailable_reason"] == "native_hire_cost_context_multiplier_unavailable",
                              "only demanded selected multiplier unavailable")
                    else:
                        check(context["available"] is True
                              and context["selected_patron_multiplier_raw"] == (175000 if index == 3 else -25000),
                              "actual signed loaded values retained; no stock constant substituted")
                else:
                    check(context["available"] is True and context["patron_is_player"] is False
                          and context["employed_by_other"] is None and context["selected_patron_multiplier_raw"] is None,
                          "ordinary branch does not sample patron employer/factor")
                    if index == 6:
                        check(context["order_title_holder_id"] == 0, "legal zero holder retained")
                    if index in (5, 7):
                        check(context["order_title_holder_id"] is None and context["title_holder_is_player"] is False,
                              "canonical fallback outcome distinct from unavailable")
            observed.append(actual)
        historical_shape = copy.deepcopy(packets[0]["result"]["player_holy_order_context"])
        for row in historical_shape["rows"][:8]:
            del row["military_terms"]["hire_cost_context"]
        check(normalize_player_holy_order_context_v1(historical_shape, snapshot=Driver(packets[0]).snapshot)
              == historical_shape, "additive observer may be absent in historical wire shape")
        return observed

    args.output_dir.mkdir(parents=True, exist_ok=True)
    report = {"schema": "xar.holy-order-hire-cost-context-mcp-validation.v1", "status": "RED"}
    try:
        observed = asyncio.run(exercise())
        (args.output_dir / "observed.json").write_text(json.dumps(observed, ensure_ascii=False, indent=2) + "\n",
                                                     encoding="utf-8")
        report.update(status="GREEN", samples=len(packets), checks=checks, tool=tool_name,
                      native_fixture=str(args.native_fixture), native_fixture_sha256=hashlib.sha256(native_bytes).hexdigest(),
                      source_root=str(args.source_root), whole_native_domain_preserved=True,
                      synthetic_boundary="callback/world/paused hello only; whole production reader+serializers+Service route",
                      new_live_evidence=False, game_actions=0, live_queries=0,
                      new_path_source=[str(inspect.getsourcefile(fn)) for fn in (
                          normalize_player_holy_order_context_v1, query_player_holy_order_context_private_v1,
                          validate_holy_order_hire_cost_context)])
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
