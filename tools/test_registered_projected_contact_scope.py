"""Consume production reader/serializer output through the registered MCP tool."""
from __future__ import annotations

import argparse
import ast
import asyncio
import copy
import hashlib
import inspect
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True


def existing_transport_helpers(source: Path) -> dict[str, object]:
    # Import the four existing fixture definitions without importing or running
    # their old matrix, and without allowing that test's sys.path insertion.
    names = {"FakeEndpoint", "_hello", "_snapshot", "_army"}
    tree = ast.parse(source.read_text(encoding="utf-8-sig"), filename=str(source))
    selected = [node for node in tree.body if isinstance(node, (ast.ClassDef, ast.FunctionDef))
                and node.name in names]
    if len(selected) != len(names):
        raise RuntimeError("existing transport helper definitions are missing")
    namespace: dict[str, object] = {}
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(source), "exec"), namespace)
    return namespace


async def check(args: argparse.Namespace) -> dict[str, object]:
    sys.path.insert(0, str(args.baseline_root / "tools"))
    sys.path.insert(0, str(args.source_root / "tools"))
    sys.path.insert(0, str(args.source_root / "ck3_autonomous_player/src"))
    from mcp import Client
    from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
    from xar_autoplayer.bridge.service import GameplayBridgeService
    from xar_autoplayer.bridge.mcp_server import create_server
    from xar_autoplayer.bridge.projected_contact_contract import (
        QUERY_PROJECTED_CONTACT_SCOPE_V1_CAPABILITY,
        normalize_projected_contact_scope,
        query_projected_contact_scope_v1_step,
    )

    helper_path = args.baseline_root / "ck3_autonomous_player/tests/unit/test_native_bridge_driver.py"
    helpers = existing_transport_helpers(helper_path)
    report: dict[str, object] = {
        "status": "RED",
        "registered_tool": "ck3_query_projected_contact_scope_v1",
        "transport_boundary": "existing FakeEndpoint; production native inner JSON is preserved",
        "source_identity_boundary": "fixture metadata describes the same native-owned subject",
        "old_test_cases_rerun": False,
        "game_contacted": False,
        "window_operations": 0,
        "full_dll_build": False,
        "helper_sha256": hashlib.sha256(helper_path.read_bytes()).hexdigest(),
        "production_python_sources": {
            "driver": inspect.getsourcefile(NativeHeadlessGameplayDriver),
            "service": inspect.getsourcefile(GameplayBridgeService),
            "mcp_registration": inspect.getsourcefile(create_server),
            "normalizer": inspect.getsourcefile(normalize_projected_contact_scope),
        },
        "cases": [],
    }
    files = sorted(args.wire_dir.glob("*.json"))
    if args.case:
        files = [path for path in files if path.stem == args.case]
    if not files:
        raise RuntimeError("no native-produced scope JSON files were supplied")
    for path in files:
        native_scope = json.loads(path.read_text(encoding="utf-8"))
        case: dict[str, object] = {
            "case": path.stem,
            "native_inner_json": str(path),
            "native_inner_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "native_status": native_scope["status"],
            "native_wire_snapshot_revision": native_scope["snapshot_revision"],
            "status": "RED",
        }
        report["cases"].append(case)
        args.result.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        available = native_scope["status"] == "available"
        subject = native_scope["subject_army_id"]
        step = query_projected_contact_scope_v1_step(subject, 3, 2)
        if available:
            normalized = normalize_projected_contact_scope(
                native_scope, expected_subject_army_id=subject,
                expected_target_province_id=3, expected_incoming_entry_province_id=2,
                expected_date_raw=43_823_104, expected_snapshot_revision=41,
                expected_subject_current_province_id=2,
                expected_subject_owner_character_id=0x1000001,
            )
            assert normalized == native_scope, "normalizer reordered or changed native scope"
            assert "actual_contact_scope_ready" not in normalized
            assert "win_odds" not in normalized
        else:
            try:
                normalize_projected_contact_scope(
                    native_scope, expected_subject_army_id=subject,
                    expected_target_province_id=3, expected_incoming_entry_province_id=2,
                    expected_date_raw=43_823_104, expected_snapshot_revision=41,
                )
            except ValueError:
                case["normalizer_unavailable_rejected"] = True
            else:
                raise AssertionError("unavailable native inputs normalized as available none")
        endpoint = helpers["FakeEndpoint"]()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name, endpoint=endpoint, command_timeout_seconds=0.2,
        )
        endpoint.publish(helpers["_hello"]("game.state.snapshot", QUERY_PROJECTED_CONTACT_SCOPE_V1_CAPABILITY))
        own = helpers["_army"](subject, province_id=2, route_province_ids=[],
                               owner_character_id=0x1000001)
        endpoint.publish(helpers["_snapshot"](41, date_raw=43_823_104, player_armies=[own]))
        snapshot = driver.take_snapshot()
        frame_receipts: list[dict[str, object]] = []

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") != "execute_step":
                return
            assert frame["step"] == step
            frame_receipts.append(copy.deepcopy(frame))
            # The endpoint is the sole fixture boundary. The inner body is the
            # byte-parsed production C++ serializer result, never a mock scope.
            response = {
                "type": "command_result", "protocol_version": 1,
                "request_id": frame["request_id"], "ok": available,
            }
            if available:
                response["result"] = {
                    "step": step, "accepted": True, "status": "available",
                    "query_sequence": 1, "snapshot_revision": 41,
                    "projected_contact_scope": copy.deepcopy(native_scope),
                    "backend_id": "native-headless",
                }
            else:
                response["error"] = "production native projected-contact inputs " + native_scope["status"]
            endpoint.publish(response)

        endpoint.send_hook = answer
        server = create_server(driver)
        async with Client(server) as client:
            tools = await client.list_tools()
            tool_rows = tools.tools if hasattr(tools, "tools") else tools
            registered = next(row for row in tool_rows if row.name == report["registered_tool"])
            schema = registered.input_schema if hasattr(registered, "input_schema") else registered.inputSchema
            assert "expected_revision" in schema["required"], "MCP revision must be mandatory"
            arguments = {"subject_army_id": subject, "target_province_id": 3,
                         "incoming_entry_province_id": 2,
                         "expected_revision": snapshot["revision"]}
            result = await client.call_tool(report["registered_tool"], arguments)
        case["registered_mcp_is_error"] = result.is_error
        case["execute_step_requests"] = frame_receipts
        if available:
            assert not result.is_error, str(result)
            body = result.structured_content
            assert body["projected_contact_scope"] == native_scope
            assert body["queried_native_revision"] == 41
            assert body["queried_revision"] == snapshot["revision"]
            assert body["queried_snapshot_id"] == snapshot["snapshot_id"]
            case["registered_mcp_structured_result"] = body
            case["public_revision"] = snapshot["revision"]
            case["full_native_body_preserved"] = True
        else:
            assert result.is_error, "unavailable inputs appeared as a successful MCP projection"
            case["registered_mcp_error_content"] = [getattr(item, "text", str(item)) for item in result.content]
        assert len(frame_receipts) == 1, "registered tool did not invoke the owning-thread native query once"
        assert frame_receipts[0]["expected_revision"] == 41
        assert driver.take_snapshot()["native_revision"] == 41
        case["status"] = "GREEN"
        driver.close()
    report["status"] = "GREEN"
    report["focused_cases_green"] = len(files)
    report["readiness"] = "static-ready"
    report["live"] = False
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--baseline-root", type=Path)
    parser.add_argument("--wire-dir", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--case")
    args = parser.parse_args()
    args.baseline_root = args.baseline_root or args.source_root
    try:
        report = asyncio.run(check(args))
    except Exception as error:
        report = json.loads(args.result.read_text(encoding="utf-8")) if args.result.exists() else {}
        report.update(status="RED", error=f"{type(error).__name__}: {error}",
                      source_root=str(args.source_root), wire_dir=str(args.wire_dir))
    args.result.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "result": str(args.result),
                      "error": report.get("error")}, indent=2))
    return 0 if report["status"] == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
