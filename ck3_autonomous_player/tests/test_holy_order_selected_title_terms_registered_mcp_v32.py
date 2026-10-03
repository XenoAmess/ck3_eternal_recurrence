"""One offline registered MCP chain consuming the production selected-title full wire.

Only SDK registration, endpoint receive and paused snapshot metadata are fixture
stubs. The original unique native reader case is reused without re-execution.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import uuid
from unittest.mock import patch

TOOL = "ck3_query_player_holy_order_selected_title_terms_v1"

class Metadata:
    def __init__(self): self.model_config = {}
    def model_rebuild(self, *, force): pass
    def model_json_schema(self):
        return {"type": "object", "additionalProperties": self.model_config.get("extra") != "forbid"}

class CapturingSdkServer:
    def __init__(self, **kwargs): self._tool_manager = SimpleNamespace(_tools={})
    def tool(self, **kwargs):
        def register(function):
            self._tool_manager._tools[function.__name__] = SimpleNamespace(
                function=function, annotations=kwargs.get("annotations"),
                fn_metadata=SimpleNamespace(arg_model=Metadata()))
            return function
        return register
    def resource(self, uri): return lambda function: function

def main():
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--native-wire", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    sdk = ModuleType("mcp"); sdk.__path__ = []
    sdk_server = ModuleType("mcp.server"); sdk_server.MCPServer = CapturingSdkServer
    sdk_types = ModuleType("mcp.types")
    sdk_types.ToolAnnotations = lambda **kwargs: SimpleNamespace(**kwargs)
    sys.modules.update({"mcp": sdk, "mcp.server": sdk_server, "mcp.types": sdk_types})
    sys.path.insert(0, str(args.source_root / "tools"))
    sys.path.insert(0, str(root / "ck3_autonomous_player" / "src"))
    from xar_autoplayer.bridge.mcp_server import create_server
    from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, NativeProtocolState
    wire = json.loads(args.native_wire.read_bytes())
    result = wire["result"]
    inner = result["player_holy_order_selected_title_terms"]
    snapshot = {
        "snapshot_id": "holy-order-selected-title-synthetic-frame", "revision": 9001,
        "native_revision": result["snapshot_revision"], "date_raw": result["date_raw"],
        "paused": True, "map_ready": True,
        "played_character": {"character_id": inner["played_character_id"], "alive": True},
        "diagnostics": {"hello": {"expected_ck3_version": result["game_version"],
                                   "expected_ck3_sha256": result["executable_sha256"]}},
    }
    state = NativeProtocolState("holy-order-selected-title-offline-no-pipe")
    requests = []
    class Endpoint:
        def send(self, request):
            requests.append(deepcopy(request))
            assert request["request_id"] == wire["request_id"]
            state.ingest(wire)
    driver = NativeHeadlessGameplayDriver.__new__(NativeHeadlessGameplayDriver)
    driver.endpoint = Endpoint(); driver.state = state; driver.command_timeout_seconds = 1.0
    driver.allow_private_player_religion_context_query = True
    driver.take_snapshot = lambda: deepcopy(snapshot)
    server = create_server(driver)
    registered = server._tool_manager._tools[TOOL]
    calls = []
    relevant = {TOOL, "query_player_holy_order_selected_title_terms_private_v1",
                "read_private_g2_native_query_v1", "ingest", "wait_for_command_result",
                "normalize_player_holy_order_selected_title_terms_v1"}
    def trace(frame, event, argument):
        if event == "call" and frame.f_code.co_name in relevant:
            calls.append({"function": frame.f_code.co_name, "source": frame.f_code.co_filename})
    with patch("uuid.uuid4", return_value=uuid.UUID(int=0x3203)):
        sys.setprofile(trace)
        try: observed = registered.function(expected_revision=9001)
        finally: sys.setprofile(None)
    assert registered.annotations.readOnlyHint is True
    assert len(requests) == 1
    assert requests[0]["step"] == result["step"]
    assert requests[0]["expected_revision"] == result["snapshot_revision"]
    assert requests[0]["expected_snapshot_revision"] == result["snapshot_revision"]
    assert all(observed[key] == value for key, value in inner.items())
    assert observed["status"] == "observed" and observed["read_only"] is True
    assert observed["advertised"] is False
    assert observed["decisions"][0]["candidates_available"] is True
    assert observed["decisions"][0]["candidates"] == []
    titles = observed["decisions"][1]["candidates"] + observed["decisions"][2]["candidates"]
    assert [title["title_id"] for title in titles] == [2164260913, 2181038151, 2197815385]
    assert [title["resource_costs_raw"][3] for title in titles] == [1100000, 4200000, 2500000]
    assert [title["resource_costs_raw"][9] for title in titles] == [-12345] * 3
    assert titles[0]["can_take"] is False and titles[0]["can_afford"] is True
    assert titles[1]["can_take"] is True and titles[1]["can_afford"] is False
    assert titles[0]["can_afford_reason_literal"] == ""
    required = {
        ("mcp_server.py", TOOL), ("native_driver.py", "query_player_holy_order_selected_title_terms_private_v1"),
        ("player_holy_order_selected_title_terms_private_transport.py", "query_player_holy_order_selected_title_terms_private_v1"),
        ("g2_private_query_transport.py", "read_private_g2_native_query_v1"),
        ("native_driver.py", "ingest"), ("native_driver.py", "wait_for_command_result"),
        ("player_holy_order_selected_title_terms_private_transport.py", "normalize_player_holy_order_selected_title_terms_v1"),
    }
    assert required <= {(Path(call["source"]).name, call["function"]) for call in calls}
    (out / "registered-mcp-mapped.json").write_text(json.dumps(observed, indent=2) + "\n", encoding="utf-8")
    receipt = {"status": "GREEN", "focused_case_count": 1, "registered_tool": TOOL,
               "actual_call_chain": calls, "execute_step_requests": requests,
               "full_native_body_preserved": True, "empty_candidates_preserved": True,
               "full_refs_independent_predicates_and_signed_costs_preserved": True,
               "readiness": "static-ready", "live": False, "old_reader_executions": 0,
               "game_contacted": False, "window_operations": 0, "sdk_invocations": 0,
               "stub_boundary": "SDK registration API, endpoint receive of production full wire, synthetic paused snapshot metadata only"}
    (out / "RESULT.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "GREEN", "focused_case_count": 1, "registered_tool": TOOL}))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
