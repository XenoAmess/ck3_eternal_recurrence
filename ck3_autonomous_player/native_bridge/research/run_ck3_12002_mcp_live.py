#!/usr/bin/env python3
"""Official MCP client harness for one coordinator-owned CK3 migration session.

Normal mode starts CK3 through clean-source native_session. --sdk-smoke-test
uses a Python MCP fixture server only. The harness never attaches to a game.
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import threading
import time
import traceback
import uuid


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def serialized(value: object) -> object:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json", by_alias=True, exclude_none=True)
    if hasattr(value, "message"):
        return serialized(value.message)
    if isinstance(value, BaseException):
        return {"error_type": type(value).__name__, "error": str(value)}
    return value


class JsonLines:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.lock = threading.Lock()
        path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, direction: str, value: object) -> None:
        with self.lock, self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({
                "at": now(), "direction": direction, "message": serialized(value),
            }, ensure_ascii=False) + "\n")


class RecordedStream:
    def __init__(self, stream: object, log: JsonLines, direction: str) -> None:
        self.stream, self.log, self.direction = stream, log, direction

    def __getattr__(self, name: str) -> object:
        return getattr(self.stream, name)

    async def receive(self) -> object:
        value = await self.stream.receive()
        self.log.write(self.direction, value)
        return value

    async def send(self, value: object) -> None:
        self.log.write(self.direction, value)
        await self.stream.send(value)

    def __aiter__(self) -> RecordedStream:
        return self

    async def __anext__(self) -> object:
        import anyio
        try:
            return await self.receive()
        except anyio.EndOfStream:
            raise StopAsyncIteration from None

    async def __aenter__(self) -> RecordedStream:
        await self.stream.__aenter__()
        return self

    async def __aexit__(self, *args: object) -> object:
        return await self.stream.__aexit__(*args)


def clean_imports(source: Path) -> None:
    source = source.expanduser().resolve()
    if (source / "ck3_autonomous_player/src/xar_autoplayer").is_dir():
        source = source / "ck3_autonomous_player/src"
    if not (source / "xar_autoplayer").is_dir():
        raise ValueError(f"clean source must contain xar_autoplayer: {source}")
    sys.path.insert(0, str(source))


def native_server(args: argparse.Namespace) -> None:
    clean_imports(args.agent_source_root)
    from xar_autoplayer.bridge.native_driver import (
        NativeHeadlessGameplayDriver, NativeNamedPipeServer,
    )
    from xar_autoplayer.bridge.mcp_server import create_server

    wire = JsonLines(args.native_wire)

    class RecordingEndpoint(NativeNamedPipeServer):
        def send(self, frame: dict[str, object]) -> None:
            wire.write("python-to-dll", frame)
            super().send(frame)

    class RecordingDriver(NativeHeadlessGameplayDriver):
        def _ingest(self, frame: dict[str, object]) -> None:
            wire.write("dll-to-python", frame)
            super()._ingest(frame)

    driver = RecordingDriver(
        args.bridge_pipe, endpoint=RecordingEndpoint(args.bridge_pipe),
        state_dir=args.state_dir, save_dir=args.state_dir / "profile/save games",
        command_timeout_seconds=args.command_timeout,
        checkpoint_timeout_seconds=args.command_timeout,
    )
    server = create_server(driver)

    @server.tool()
    def ck3_migration_pipe_diagnostics() -> dict[str, object]:
        """Inspect this harness's pipe, native hello, heartbeat and mailbox."""
        return {
            "pipe": driver.pipe_name,
            "transport_error": driver.endpoint.transport_error(),
            "diagnostics": driver.diagnostics(),
        }

    @server.tool()
    def ck3_migration_raw_step(
        step: str, expected_revision: int | None = None,
        request_fields: dict[str, object] | None = None,
    ) -> dict[str, object]:
        """Issue an explicit native step and preserve its unprojected result."""
        return driver._execute_primitive_step(
            step, expected_revision=expected_revision,
            required_capability="game.adapter.exact-build", request_fields=request_fields,
        )

    try:
        server.run(transport="stdio")
    finally:
        driver.close()


def fixture_server() -> None:
    """SDK/plan fixture; no project imports, Windows pipe or CK3 process."""
    from mcp.server import MCPServer
    server = MCPServer(name="ck3-migration-sdk-fixture", version="0.1.0")
    state: dict[str, object] = {
        "revision": 1, "native_revision": 1, "date_raw": 53168784,
        "speed": 2, "paused": True, "map_ready": True,
        "episode_identity_pending": False,
        "player_armies": [{"army_id": 37}],
        "played_character": {"character_id": 29829, "alive": True},
    }

    @server.tool()
    def ck3_take_snapshot() -> dict[str, object]:
        if state["paused"] is False:
            state["date_raw"] += 24
            state["revision"] += 1
        return dict(state)

    @server.tool()
    def ck3_get_capabilities() -> dict[str, object]:
        return {"fixture_only": True, "snapshot": True}

    @server.tool()
    def ck3_get_bridge_diagnostics() -> dict[str, object]:
        return {"fixture_only": True, "connected": True}

    @server.tool()
    def ck3_migration_pipe_diagnostics() -> dict[str, object]:
        return {"fixture_only": True, "diagnostics": {"connected": True}}

    @server.tool()
    def ck3_execute_step(step: str, expected_revision: int | None = None) -> dict[str, object]:
        if expected_revision != state["revision"]:
            raise ValueError("fixture revision mismatch")
        if step == "pause-map":
            state["paused"] = True
        elif step == "resume-map":
            state["paused"] = False
        elif step.startswith("set-speed-"):
            state["speed"] = int(step.rsplit("-", 1)[1])
        state["revision"] += 1
        return {"step": step, "accepted": True, "fixture_only": True}

    @server.tool()
    def ck3_migration_raw_step(step: str, expected_revision: int | None = None) -> dict[str, object]:
        if step == "fixture-run-inbox-v1":
            return {"step": step, "fixture_only": True,
                    "submission": {"command": "run xar_mcp_inbox.txt"}}
        return {"step": step, "fixture_only": True}

    @server.tool()
    def ck3_query_campaign_root_context_v1(expected_revision: int) -> dict[str, object]:
        return {"fixture_only": True, "revision": expected_revision}

    @server.tool()
    def ck3_query_loaded_feature_manifest_v1(expected_revision: int) -> dict[str, object]:
        return {"fixture_only": True, "revision": expected_revision}

    @server.tool()
    def ck3_query_army_strengths(army_ids: list[int], expected_revision: int | None = None) -> dict[str, object]:
        return {"fixture_only": True, "army_ids": army_ids, "revision": expected_revision}

    @server.tool()
    def ck3_save_checkpoint(expected_revision: int | None = None) -> dict[str, object]:
        return {"fixture_only": True, "checkpoint": {"status": "fixture", "date_raw": state["date_raw"]}}

    @server.tool()
    def ck3_auto_turn() -> dict[str, object]:
        return {"fixture_only": True, "status": "executed", "selected_step": "fixture-query"}

    @server.tool()
    def ck3_migration_fixture_error() -> dict[str, object]:
        raise RuntimeError("fixture war-termination query unavailable")

    server.run(transport="stdio")


def default_plan() -> list[dict[str, object]]:
    return [
        {"id": "pause", "tool": "ck3_execute_step", "args": {"step": "pause-map"}},
        {"id": "campaign", "tool": "ck3_query_campaign_root_context_v1", "continue_on_error": True},
        {"id": "features", "tool": "ck3_query_loaded_feature_manifest_v1", "continue_on_error": True},
        {"id": "armies", "kind": "army_strengths", "continue_on_error": True},
        {"id": "advance", "kind": "advance_day", "days": 1},
        {"id": "checkpoint", "tool": "ck3_save_checkpoint"},
        {"id": "final", "tool": "ck3_take_snapshot"},
    ]


def load_plan(path: Path) -> list[dict[str, object]]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    steps = value.get("steps") if isinstance(value, dict) else value
    if not isinstance(steps, list) or any(not isinstance(row, dict) for row in steps):
        raise ValueError("plan must be an array of objects or {steps: [...]} object")
    return steps


def lookup(value: object, path: str) -> object:
    for key in path.split("."):
        value = value[int(key)] if isinstance(value, list) else value[key]
    return value


def resolve(value: object, context: dict[str, object]) -> object:
    if isinstance(value, str) and value.startswith("$"):
        return lookup(context, value[1:])
    if isinstance(value, dict):
        if set(value) == {"$ref"}:
            return lookup(context, str(value["$ref"]).lstrip("$"))
        return {key: resolve(child, context) for key, child in value.items()}
    if isinstance(value, list):
        return [resolve(child, context) for child in value]
    return value


def tool_envelope(result: object) -> dict[str, object]:
    """SDK 2 stores snake_case attributes and emits camelCase JSON aliases."""
    value = serialized(result)
    if not isinstance(value, dict):
        raise ValueError("MCP tool result did not serialize to an object")
    # Also accept an explicit JSON-RPC/result wrapper in captured fixtures.
    nested = value.get("result")
    if isinstance(nested, dict) and any(
        name in nested for name in ("content", "structuredContent", "structured_content", "isError", "is_error")
    ):
        value = nested
    return value


def tool_payload(result: object) -> object:
    envelope = tool_envelope(result)
    structured = envelope.get("structuredContent", envelope.get("structured_content"))
    if structured is not None:
        return structured
    texts = []
    for block in envelope.get("content", []):
        text = block.get("text") if isinstance(block, dict) else getattr(block, "text", None)
        if text:
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                texts.append(text)
    return "\n".join(texts) if texts else envelope


def file_sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def fixture_session(spec: object, config: object, args: argparse.Namespace,
                    stop: threading.Event, *, output_stream: object = None) -> dict[str, object]:
    """Run the full session queue with one fixture-only first-launch override."""
    import importlib
    from types import FunctionType

    session_module = importlib.import_module("xar_autoplayer.native_session")
    original_launch = session_module.launch
    first_launch = True

    def fixture_launch(*launch_args: object, **launch_kwargs: object) -> object:
        nonlocal first_launch
        if first_launch:
            launch_kwargs["verify_prepared_profile"] = False
            first_launch = False
        return original_launch(*launch_args, **launch_kwargs)

    # Rebind the existing public entry and its queue loop locally.  Production
    # module globals remain untouched while this owned fixture thread runs.
    session_globals = dict(vars(session_module))
    session_globals["launch"] = fixture_launch
    for name in ("_native_session_locked", "native_session"):
        original = getattr(session_module, name)
        bound = FunctionType(original.__code__, session_globals, original.__name__,
                             original.__defaults__, original.__closure__)
        bound.__kwdefaults__ = original.__kwdefaults__
        session_globals[name] = bound
    report = session_globals["native_session"](
        spec, native_bridge=config, timeout_seconds=args.timeout + args.hold_seconds + 120,
        cold_start_checkpoint=args.cold_start_checkpoint, stop_event=stop,
        input_stream=None, output_stream=output_stream,
    )
    report["fixture_profile"] = True
    return report


class PlanClient:
    def __init__(self, session: object, args: argparse.Namespace, report: dict[str, object], write: object) -> None:
        self.session, self.args, self.report, self.write = session, args, report, write
        self.tools: dict[str, dict[str, object]] = {}
        self.results: dict[str, object] = {}
        self.snapshot: dict[str, object] = {}
        self.consumed_control_plans: set[tuple[str, int]] = set()
        self.control_plan_execution_depth = 0
        self.calls = JsonLines(args.output.with_suffix(".mcp-calls.jsonl"))

    async def call(self, name: str, arguments: dict[str, object] | None = None) -> object:
        row: dict[str, object] = {"tool": name, "arguments": arguments or {}, "started_at": now()}
        self.calls.write("request", row)
        try:
            result = await self.session.call_tool(
                name, arguments or {}, read_timeout_seconds=self.args.command_timeout + 15,
            )
            row["response"] = serialized(result)
            row["payload"] = tool_payload(result)
            envelope = tool_envelope(row["response"])
            row["is_error"] = envelope.get("isError", envelope.get("is_error", False)) is True
            row["ok"] = not row["is_error"]
            if not row["ok"]:
                raise RuntimeError(f"MCP tool {name} returned an error: {row['payload']}")
            return row["payload"]
        except BaseException as error:
            row["ok"] = False
            row["error"] = f"{type(error).__name__}: {error}"
            raise
        finally:
            row["finished_at"] = now()
            self.calls.write("response", row)

    async def fresh(self) -> dict[str, object]:
        value = await self.call("ck3_take_snapshot")
        if not isinstance(value, dict):
            raise ValueError("MCP snapshot is not an object")
        self.snapshot = value
        return value

    async def invoke(self, name: str, arguments: object = None, *, fresh_revision: bool = True) -> object:
        properties = self.tools.get(name, {}).get("inputSchema", {}).get("properties", {})
        needs_snapshot = fresh_revision and "expected_revision" in properties
        if needs_snapshot or "$" in json.dumps(arguments):
            await self.fresh()
        army_ids = [
            int(row["army_id"]) for row in self.snapshot.get("player_armies", [])
            if isinstance(row, dict) and isinstance(row.get("army_id"), int)
        ][:64]
        context = {"revision": self.snapshot.get("revision"), "snapshot": self.snapshot,
                   "army_ids": army_ids, "results": self.results}
        resolved = resolve(arguments or {}, context)
        if needs_snapshot and "expected_revision" not in resolved:
            resolved["expected_revision"] = self.snapshot["revision"]
        return await self.call(name, resolved)

    async def wait_snapshot(self, expected: dict[str, object], timeout: float) -> dict[str, object]:
        deadline = time.monotonic() + timeout
        while True:
            snapshot = await self.fresh()
            if all(lookup(snapshot, key) == value for key, value in expected.items()):
                return snapshot
            if time.monotonic() >= deadline:
                raise TimeoutError(f"snapshot did not reach {expected}: {snapshot}")
            await asyncio.sleep(self.args.poll_interval)

    async def advance(self, row: dict[str, object]) -> dict[str, object]:
        await self.invoke("ck3_execute_step", {"step": "pause-map"})
        before = await self.wait_snapshot({"paused": True}, self.args.command_timeout)
        await self.invoke("ck3_execute_step", {"step": "set-speed-1"})
        await self.wait_snapshot({"speed": 1}, self.args.command_timeout)
        start = int(before["date_raw"])
        target = start + 24 * int(row.get("days", 1))
        await self.invoke("ck3_execute_step", {"step": "resume-map"})
        deadline = time.monotonic() + float(row.get("timeout", self.args.command_timeout))
        reached: dict[str, object] | None = None
        try:
            while time.monotonic() < deadline:
                current = await self.fresh()
                if current.get("active_event") is not None:
                    raise RuntimeError(
                        "an active event interrupted date advancement: "
                        f"date_raw={current['date_raw']}, target_date_raw={target}, "
                        f"paused={current.get('paused')}, "
                        f"active_event={json.dumps(current['active_event'], ensure_ascii=False, sort_keys=True)}"
                    )
                if int(current["date_raw"]) >= target:
                    reached = current
                    break
                await asyncio.sleep(self.args.poll_interval)
            if reached is None:
                raise TimeoutError("running map did not reach the requested date")
        finally:
            await self.invoke("ck3_execute_step", {"step": "pause-map"})
        after = await self.wait_snapshot({"paused": True}, self.args.command_timeout)
        if int(after["date_raw"]) < target:
            raise RuntimeError("pause readback preceded the requested date")
        return {"before": before, "running_successor": reached, "after": after,
                "requested_days": row.get("days", 1), "elapsed_hours": int(after["date_raw"]) - start}

    async def write_inbox(self, row: dict[str, object]) -> dict[str, object]:
        if not self.args.fixture_profile:
            raise ValueError("write-inbox requires the explicit --fixture-profile option")
        source = Path(row["source_file"]).expanduser().resolve()
        profile = self.args.state_dir / "profile"
        inbox = profile / "run/xar_mcp_inbox.txt"
        debug_log = profile / "logs/debug.log"
        marker = row.get("debug_marker", row.get("marker"))
        if not isinstance(marker, str) or not marker:
            raise ValueError("write-inbox requires a debug_marker to observe its execution")
        offset = debug_log.stat().st_size if debug_log.is_file() else 0
        inbox.parent.mkdir(parents=True, exist_ok=True)
        raw = source.read_text(encoding="utf-8-sig").encode("utf-8-sig")
        temporary = inbox.with_name(".xar_migration_inbox.tmp")
        temporary.write_bytes(raw)
        os.replace(temporary, inbox)
        result = {"source_file": str(source), "source_sha256": file_sha(source),
                  "inbox": str(inbox), "inbox_sha256": file_sha(inbox),
                  "debug_marker": marker, "debug_log_offset": offset,
                  "marker_observed": False, "noop_restored": False,
                  "native_run_requested": row.get("native_run", getattr(self.args, "native_fixture_inbox", False))}
        try:
            if result["native_run_requested"]:
                invocation: dict[str, object] = {"tool": "ck3_migration_raw_step",
                    "arguments": {"step": "fixture-run-inbox-v1"}, "started_at": now()}
                result["native_invocation"] = invocation
                try:
                    invocation["result"] = await self.invoke(
                        "ck3_migration_raw_step", {"step": "fixture-run-inbox-v1"})
                    invocation["ok"] = True
                except BaseException as error:
                    invocation["ok"] = False
                    invocation["error"] = f"{type(error).__name__}: {error}"
                    raise
                finally:
                    invocation["finished_at"] = now()
            deadline = time.monotonic() + float(row.get("timeout", self.args.command_timeout))
            while time.monotonic() < deadline:
                if debug_log.is_file():
                    with debug_log.open("rb") as stream:
                        stream.seek(offset)
                        tail = stream.read().decode("utf-8", errors="replace")
                    if marker in tail:
                        result["marker_observed"] = True
                        return result
                await asyncio.sleep(self.args.poll_interval)
            raise TimeoutError(f"fixture inbox did not produce debug marker {marker}")
        finally:
            temporary.write_text("# CK3 migration fixture inbox: no effects.\n", encoding="utf-8-sig")
            os.replace(temporary, inbox)
            result["noop_restored"] = True
            result["noop_sha256"] = file_sha(inbox)
            self.report.setdefault("fixture_inbox_attempts", []).append(result)
            self.write()

    async def execute(self, steps: list[dict[str, object]]) -> None:
        for index, step in enumerate(steps, 1):
            row = {"id": step.get("id", f"step-{len(self.report['steps']) + 1}"),
                   "plan": step, "started_at": now(), "ok": False}
            self.report["steps"].append(row)
            self.write()
            try:
                kind = step.get("kind", "tool")
                if kind == "advance_day":
                    result = await self.advance(step)
                elif kind in {"write-inbox", "write_inbox"}:
                    result = await self.write_inbox(step)
                elif kind == "wait_snapshot":
                    result = await self.wait_snapshot(step["expected"], float(step.get("timeout", self.args.command_timeout)))
                elif kind == "army_strengths":
                    snapshot = await self.fresh()
                    ids = [int(item["army_id"]) for item in snapshot.get("player_armies", [])][:64]
                    result = await self.invoke("ck3_query_army_strengths", {"army_ids": ids}) if ids else await self.invoke(
                        "ck3_migration_raw_step", {"step": "query-army-strengths-v1"})
                elif kind == "auto_turns":
                    result = []
                    row["result"] = result
                    row["attempted_turns"] = 0
                    row["completed_turns"] = 0
                    row["turn_snapshots"] = []
                    for _ in range(int(step.get("count", 1))):
                        row["attempted_turns"] += 1
                        self.write()
                        value = await self.invoke("ck3_auto_turn")
                        if isinstance(value, dict) and value.get("status") == "blocked":
                            row["failed_turn_result"] = value
                            raise RuntimeError(f"MCP auto turn blocked: {value}")
                        result.append(value)
                        self.write()
                        row["turn_snapshots"].append(await self.fresh())
                        row["completed_turns"] += 1
                        self.write()
                elif kind == "hold":
                    await self.hold(float(step.get("seconds", self.args.hold_seconds)))
                    result = {"held_seconds": step.get("seconds", self.args.hold_seconds)}
                elif kind == "finish_hold":
                    self.report["hold_finished_by_control_plan"] = True
                    result = {"hold_finished": True}
                elif kind == "frontend_read_only":
                    name = step["tool"]
                    if name not in {"ck3_query_frontend_gui_route_v1", "ck3_inspect_frontend_gui_tree_v1",
                                    "ck3_query_frontend_game_rule_selections_v1", "ck3_migration_pipe_diagnostics"}:
                        raise ValueError("frontend_read_only plan cannot dispatch an action")
                    if step.get("args"):
                        raise ValueError("frontend_read_only diagnostics take no game-frame arguments")
                    result = await self.call(name)
                else:
                    name = "ck3_migration_raw_step" if kind == "raw_step" else step["tool"]
                    arguments = step.get("args", {})
                    if kind == "raw_step":
                        arguments = {"step": step["step"], **arguments}
                    result = await self.invoke(name, arguments, fresh_revision=step.get("fresh_revision", True))
                row["result"] = result
                for path, expected in step.get("expect", {}).items():
                    actual = lookup(result, path)
                    if actual != expected:
                        raise ValueError(f"result {path} expected {expected!r}, received {actual!r}")
                self.results[str(row["id"])] = result
                if kind != "frontend_read_only":
                    row["after_snapshot"] = await self.fresh()
                row["ok"] = True
            except Exception as error:
                row["error"] = f"{type(error).__name__}: {error}"
                if not step.get("continue_on_error", False):
                    raise
            finally:
                row["finished_at"] = now()
                self.write()

    async def hold(self, seconds: float) -> None:
        deadline = time.monotonic() + seconds
        self.report["phase"] = "hold"
        self.report["hold_until_utc_estimated"] = time.time() + seconds
        self.write()
        while time.monotonic() < deadline and not self.report.get("hold_finished_by_control_plan", False):
            if self.control_plan_execution_depth == 0 and self.args.control_plan_dir is not None:
                for path in sorted(self.args.control_plan_dir.glob("*.json")):
                    identity = (str(path), path.stat().st_mtime_ns)
                    if identity not in self.consumed_control_plans:
                        plan = load_plan(path)
                        self.consumed_control_plans.add(identity)
                        self.report.setdefault("control_plans", []).append(str(path))
                        self.control_plan_execution_depth += 1
                        try:
                            await self.execute(plan)
                        finally:
                            self.control_plan_execution_depth -= 1
            await asyncio.sleep(min(0.25, max(0, deadline - time.monotonic())))


def require_verified_bookmarks_picker(tree: object) -> dict[str, object]:
    """Admit only a complete native tree rooted at the ordinary bookmark picker.

    Selection/date/government/Robert identity remain independently guarded by
    the existing typed start method; tree presence is not selection proof.
    """
    if not isinstance(tree, dict) or not (
        tree.get("schema") == "ck3-frontend-gui-tree-inspection-v1"
        and tree.get("accepted") is True and tree.get("status") == "available"
        and tree.get("scope_root_name") == "frontend_bookmarks"
        and tree.get("root_available") is True and tree.get("read_only") is True
        and tree.get("truncated") is False and isinstance(tree.get("widgets"), list)
    ):
        raise RuntimeError("native tree does not prove a complete ordinary bookmarks picker")
    widgets = tree["widgets"]
    proof: dict[str, object] = {}
    for name in ("frontend_bookmarks", "character_selection", "start_button", "pick_any_character_button"):
        matches = [row for row in widgets if isinstance(row, dict) and row.get("runtime_name") == name]
        if len(matches) != 1 or not isinstance(matches[0].get("vtable_rva"), int) or matches[0]["vtable_rva"] <= 0:
            raise RuntimeError("native bookmarks picker does not uniquely resolve " + name)
        proof[name] = matches[0]
    root = proof["frontend_bookmarks"]
    any_character = proof["pick_any_character_button"]
    if root.get("child_path") != "" or root.get("effective_visible") is not True:
        raise RuntimeError("native bookmarks picker root is not currently visible")
    if any_character.get("effective_visible") is not True or any_character.get("enabled") is not True:
        raise RuntimeError("native ordinary character picker control is not active")
    return {"status": "ORDINARY_BOOKMARKS_TREE_VERIFIED", "widgets": proof,
            "selection_identity": "Existing typed start must independently prove exact stock Robert model before mutation"}


def require_consistent_frontend_observation(
    route_before: object, tree: object, route_after: object,
    *, require_rules_button: bool = False,
) -> dict[str, object]:
    """A route packet is ready only with a complete, visible matching scope."""
    if not isinstance(route_before, dict) or not isinstance(route_after, dict):
        raise RuntimeError("native frontend route observations are not objects")
    for route in (route_before, route_after):
        if not (route.get("schema") == "ck3-frontend-gui-route-v1"
                and route.get("accepted") is True
                and route.get("route") in {"main_menu", "bookmarks"}):
            raise RuntimeError("native frontend route is not an admitted entry")
    if route_before["route"] != route_after["route"]:
        raise RuntimeError("native frontend route changed across its tree observation")
    route_name = route_after["route"]
    scope = "frontend_bookmarks" if route_name == "bookmarks" else "mainmenu_panel_bottom"
    if not isinstance(tree, dict) or not (
        tree.get("schema") == "ck3-frontend-gui-tree-inspection-v1"
        and tree.get("accepted") is True and tree.get("status") == "available"
        and tree.get("scope_root_name") == scope
        and tree.get("root_available") is True and tree.get("read_only") is True
        and tree.get("truncated") is False and isinstance(tree.get("widgets"), list)
        and tree.get("widget_count") == len(tree["widgets"])
    ):
        raise RuntimeError("native frontend tree is incomplete or does not match its entry route")
    names = [scope]
    if route_name == "main_menu":
        names.append("new_game_button")
    elif require_rules_button:
        names.append("game_rules_button")
    else:
        names.append("pick_any_character_button")
    widgets = {}
    for name in names:
        matches = [row for row in tree["widgets"] if isinstance(row, dict) and row.get("runtime_name") == name]
        if len(matches) != 1 or not isinstance(matches[0].get("vtable_rva"), int) or matches[0]["vtable_rva"] <= 0:
            raise RuntimeError("native frontend tree does not uniquely resolve " + name)
        row = matches[0]
        if row.get("effective_visible") is not True:
            raise RuntimeError("native frontend entry widget is not currently visible: " + name)
        if name != scope and row.get("enabled") is not True:
            raise RuntimeError("native frontend entry control is not enabled: " + name)
        widgets[name] = row
    if widgets[scope].get("child_path") != "":
        raise RuntimeError("native frontend tree root is not its declared scope")
    return {"status": "CONSISTENT_VISIBLE_FRONTEND_SCOPE", "route": route_name,
            "scope_root_name": scope, "widgets": widgets}


async def wait_for_consistent_frontend(
    client: PlanClient, *, report: dict[str, object], write: object,
    timeout: float, managed_done: object = None, require_route: str | None = None,
    require_rules_button: bool = False, poll_interval: float = 0.25,
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    """Require two consecutive route/tree/route packets; retain every attempt."""
    deadline = time.monotonic() + timeout
    previous_key = None
    streak = 0
    while True:
        row: dict[str, object] = {"at": now(), "ready": False}
        report["frontend_bootstrap"]["attempts"].append(row)
        write()
        if managed_done is not None and managed_done.is_set():
            row["error"] = "managed session ended before consistent frontend readiness"
            write()
            raise RuntimeError(row["error"])
        try:
            row["route_before"] = await client.call("ck3_query_frontend_gui_route_v1")
            route_before = row["route_before"]
            if not isinstance(route_before, dict) or route_before.get("route") not in {"main_menu", "bookmarks"}:
                raise RuntimeError("native frontend is still unavailable or outside the admitted entry routes")
            row["tree"] = await client.call("ck3_inspect_frontend_gui_tree_v1")
            row["route_after"] = await client.call("ck3_query_frontend_gui_route_v1")
            proof = require_consistent_frontend_observation(
                route_before, row["tree"], row["route_after"],
                require_rules_button=require_rules_button,
            )
            if require_route is not None and proof["route"] != require_route:
                raise RuntimeError("native frontend entry has not reached requested route: " + require_route)
            key = json.dumps({"route": proof["route"], "scope": proof["scope_root_name"],
                              "widgets": proof["widgets"]}, sort_keys=True)
            streak = streak + 1 if previous_key == key else 1
            previous_key = key
            row.update(ready=True, proof=proof, consecutive_consistent_observations=streak)
            write()
            if streak >= 2:
                return row["route_after"], row["tree"], {**proof, "consecutive_consistent_observations": streak}
        except Exception as error:
            row["error"] = f"{type(error).__name__}: {error}"
            previous_key, streak = None, 0
            write()
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("native frontend did not produce two consistent complete visible route/tree observations")
        # Poll spacing does not establish readiness; only the native packets do.
        await asyncio.sleep(min(poll_interval, remaining))


async def run(args: argparse.Namespace) -> dict[str, object]:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    args.output = args.output.expanduser().resolve()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    native_wire = args.output.with_suffix(".native-wire.jsonl")
    rpc_wire = JsonLines(args.output.with_suffix(".mcp-wire.jsonl"))
    stderr_path = args.output.with_suffix(".server-stderr.log")
    stop, done = threading.Event(), threading.Event()
    session_state: dict[str, object] = {"report": None, "error": None}
    report: dict[str, object] = {"status": "RUNNING", "phase": "initializing-mcp",
        "started_at": now(), "fixture_only": args.sdk_smoke_test,
        "fixture_profile": args.fixture_profile, "steps": [],
        "state_dir": str(args.state_dir), "agent_source_root": str(args.agent_source_root),
        "pipe": args.bridge_pipe, "native_wire": str(native_wire),
        "mcp_wire": str(rpc_wire.path), "mcp_calls": str(args.output.with_suffix(".mcp-calls.jsonl")),
        "server_stderr": str(stderr_path), "session": session_state, "error": None}

    def write() -> None:
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    supervisor: threading.Thread | None = None
    if not args.sdk_smoke_test:
        clean_imports(args.agent_source_root)
        from xar_autoplayer.environment import make_spec, verify_profile
        from xar_autoplayer.native_session import native_session
        from xar_autoplayer.runtime import NativeBridgeLaunchConfig
        spec = make_spec(args.state_dir, args.game_dir)
        if args.fixture_profile:
            report["profile"] = {"mode": "explicit-external-fixture",
                "prepared_manifest": str(spec.manifest_path),
                "enabled_mod_profile": json.loads((spec.profile_dir / "dlc_load.json").read_text(encoding="utf-8-sig")),
                "production_profile_verified": False}
        else:
            report["profile"] = verify_profile(spec)
        config = NativeBridgeLaunchConfig("native-headless", args.bridge_pipe,
                                         args.bridge_dll.resolve(), args.bridge_injector.resolve())
        report["identity"] = {"game_executable": str(spec.game_exe),
            "game_sha256": file_sha(spec.game_exe), "dll": str(config.dll_path),
            "dll_sha256": file_sha(config.dll_path), "injector": str(config.injector_path),
            "injector_sha256": file_sha(config.injector_path)}

        def supervise() -> None:
            try:
                with args.output.with_suffix(".session.log").open("w", encoding="utf-8") as stream:
                    if args.fixture_profile:
                        session_state["report"] = fixture_session(spec, config, args, stop, output_stream=stream)
                        stream.write(json.dumps(session_state["report"], ensure_ascii=False) + "\n")
                    else:
                        session_state["report"] = native_session(
                            spec, native_bridge=config, timeout_seconds=args.timeout + args.hold_seconds + 120,
                            cold_start_checkpoint=args.cold_start_checkpoint,
                            stop_event=stop, input_stream=None, output_stream=stream,
                        )
            except BaseException as error:
                session_state["error"] = f"{type(error).__name__}: {error}"
            finally:
                done.set()
        supervisor = threading.Thread(target=supervise, name="ck3-12002-official-mcp-session", daemon=False)
    write()
    child_args = [str(Path(__file__).resolve()), "--server", "--bridge-pipe", args.bridge_pipe,
                  "--native-wire", str(native_wire), "--command-timeout", str(args.command_timeout)]
    if args.sdk_smoke_test:
        child_args.append("--fixture-server")
    else:
        child_args += ["--agent-source-root", str(args.agent_source_root), "--state-dir", str(args.state_dir)]
    parameters = StdioServerParameters(command=sys.executable, args=child_args, env={"PYTHONUTF8": "1"})
    client: PlanClient | None = None
    try:
        with stderr_path.open("w", encoding="utf-8") as stderr:
            async with stdio_client(parameters, errlog=stderr) as (read_stream, write_stream):
                async with ClientSession(
                    RecordedStream(read_stream, rpc_wire, "server-to-client"),
                    RecordedStream(write_stream, rpc_wire, "client-to-server"),
                    read_timeout_seconds=args.command_timeout + 15,
                ) as session:
                    report["mcp_initialize"] = serialized(await session.initialize())
                    listing = await session.list_tools()
                    report["mcp_tools"] = serialized(listing)
                    client = PlanClient(session, args, report, write)
                    client.tools = {item.name: serialized(item) for item in listing.tools}
                    try:
                        # initialize/list_tools prove the child has already opened its pipe.
                        if supervisor is not None:
                            supervisor.start()
                        if args.frontend_robert_bootstrap:
                            report["phase"] = "native-frontend-robert-bootstrap"
                            report["frontend_bootstrap"] = {"status": "RUNNING", "uses_ocr": False,
                                "uses_keyboard": False, "uses_mouse": False, "attempts": []}
                            write()
                            try:
                                route, entry_tree, entry_proof = await wait_for_consistent_frontend(
                                    client, report=report, write=write, timeout=args.readiness_timeout,
                                    managed_done=done if supervisor is not None else None,
                                    require_route="bookmarks" if args.frontend_rules_diagnostic else None,
                                    require_rules_button=args.frontend_rules_diagnostic,
                                )
                            except Exception as error:
                                report["frontend_bootstrap"].update(
                                    status="FRONTEND_READINESS_FAILED_NO_ACTION", error=f"{type(error).__name__}: {error}")
                                write()
                                if args.hold_seconds and not done.is_set():
                                    report["frontend_diagnostic_hold"] = {"reason": "frontend readiness failure", "seconds": args.hold_seconds}
                                    write()
                                    await client.hold(args.hold_seconds)
                                raise
                            entry_route = route["route"]
                            report["frontend_bootstrap"].update(entry_route=route, entry_tree=entry_tree, entry_proof=entry_proof)
                            write()
                            if args.frontend_diagnostic_only:
                                if args.frontend_rules_diagnostic:
                                    if entry_route != "bookmarks":
                                        raise RuntimeError("rules diagnostic requires independently observed Bookmarks; no New Game is dispatched")
                                    try:
                                        rules_open = await client.call("ck3_activate_frontend_game_rules_v1")
                                        report["frontend_bootstrap"]["rules_open"] = rules_open
                                        write()
                                        rules_observation = await client.call("ck3_query_frontend_game_rule_selections_v1")
                                        report["frontend_bootstrap"]["rules_observation"] = rules_observation
                                        write()
                                        if not isinstance(rules_observation, dict) or rules_observation.get("ready") is not True:
                                            raise RuntimeError("native rules diagnostic did not observe real selected setting objects")
                                    except Exception as error:
                                        report["frontend_bootstrap"].update(status="RULES_DIAGNOSTIC_FAILED", error=f"{type(error).__name__}: {error}")
                                        write()
                                        if args.hold_seconds and not done.is_set():
                                            report["frontend_diagnostic_hold"] = {"reason": "rules diagnostic failure", "seconds": args.hold_seconds}
                                            write()
                                            await client.hold(args.hold_seconds)
                                        raise
                                    report["frontend_bootstrap"]["rules_status"] = "ACTUAL_SELECTED_SETTINGS_OBSERVED_APPLY_AND_START_NOT_REQUESTED"
                                report["frontend_bootstrap"]["status"] = "READ_ONLY_ROUTE_AND_TREE_OBSERVED_NO_START"
                                write()
                                if args.hold_seconds:
                                    await client.hold(args.hold_seconds)
                                raise RuntimeError("Frontend diagnostic only; no New Game, ruler selection, Apply, Start or product test requested")
                            if entry_route == "main_menu":
                                opened = await client.call("ck3_activate_frontend_new_game_v1")
                                report["frontend_bootstrap"]["new_game"] = opened
                                write()
                                if not isinstance(opened, dict) or opened.get("status") != "verified":
                                    raise RuntimeError("native New Game did not independently verify Bookmarks")
                                route, entry_tree, entry_proof = await wait_for_consistent_frontend(
                                    client, report=report, write=write, timeout=args.readiness_timeout,
                                    managed_done=done if supervisor is not None else None, require_route="bookmarks",
                                )
                                report["frontend_bootstrap"].update(bookmarks_tree=entry_tree, bookmarks_proof=entry_proof)
                                write()
                            elif not args.allow_verified_direct_bookmarks:
                                raise RuntimeError("direct bookmarks tree preserved; explicit guarded direct-entry option required")
                            report["frontend_bootstrap"]["picker_tree_proof"] = require_verified_bookmarks_picker(entry_tree)
                            write()
                            started = await client.call("ck3_activate_frontend_start_1066_bookmark_character_v1",
                                {"character_name_key": "bookmark_rags_to_riches_duke_robert"})
                            report["frontend_bootstrap"]["start_robert"] = started
                            write()
                            if not isinstance(started, dict) or started.get("status") != "verified":
                                raise RuntimeError("native stock Robert Start did not independently verify the map")
                            report["frontend_bootstrap"]["status"] = "NATIVE_START_VERIFIED_MAP_READINESS_PENDING"
                            write()
                        report["phase"] = "waiting-for-paused-map"
                        write()
                        deadline = time.monotonic() + args.readiness_timeout
                        while True:
                            if supervisor is not None and done.is_set():
                                raise RuntimeError(f"managed session ended before readiness: {session_state}")
                            try:
                                snapshot = await client.fresh()
                                if snapshot.get("map_ready") is True and snapshot.get("paused") is True and snapshot.get("episode_identity_pending") is False:
                                    report["readiness"] = snapshot
                                    break
                            except Exception as error:
                                report["readiness_last_error"] = f"{type(error).__name__}: {error}"
                            if time.monotonic() >= deadline:
                                raise TimeoutError("MCP did not obtain a paused playable map")
                            await asyncio.sleep(args.poll_interval)
                        report["capabilities"] = await client.call("ck3_get_capabilities")
                        report["pipe_diagnostics"] = await client.call("ck3_migration_pipe_diagnostics")
                        report["phase"] = "executing-plan"
                        write()
                        plan = ([{"id": "expected-sdk-tool-error", "tool": "ck3_migration_fixture_error"}]
                                if args.sdk_error_smoke_test else load_plan(args.plan) if args.plan else default_plan())
                        await client.execute(plan)
                        if args.turns:
                            await client.execute([{"id": "r2-turns", "kind": "auto_turns", "count": args.turns}])
                        if args.hold_seconds:
                            await client.hold(args.hold_seconds)
                    except BaseException as error:
                        report["error"] = f"{type(error).__name__}: {error}"
                        if (args.frontend_robert_bootstrap and args.hold_seconds
                                and report.get("phase") == "native-frontend-robert-bootstrap"
                                and not done.is_set() and "frontend_diagnostic_hold" not in report):
                            report["frontend_diagnostic_hold"] = {"reason": report["error"], "seconds": args.hold_seconds}
                            write()
                            try:
                                await client.hold(args.hold_seconds)
                            except BaseException as hold_error:
                                report["frontend_diagnostic_hold_error"] = f"{type(hold_error).__name__}: {hold_error}"
                    finally:
                        try:
                            report["snapshot_final"] = await client.fresh()
                            report["diagnostics_final"] = await client.call("ck3_migration_pipe_diagnostics")
                        except BaseException as error:
                            report["final_observation_error"] = f"{type(error).__name__}: {error}"
                        stop.set()
                        if supervisor is not None and supervisor.ident is not None:
                            await asyncio.to_thread(supervisor.join, 90)
                        report["managed_session_thread_finished"] = supervisor is None or not supervisor.is_alive()
                        write()
    except BaseException as error:
        report["error"] = report["error"] or f"{type(error).__name__}: {error}"
        report["exception_traceback"] = traceback.format_exc()
    finally:
        stop.set()
        if supervisor is not None and supervisor.ident is not None and supervisor.is_alive():
            await asyncio.to_thread(supervisor.join, 90)
        report["managed_session_thread_finished"] = supervisor is None or not supervisor.is_alive()
        report["finished_at"] = now()
        native_report = session_state.get("report")
        cleanup_ok = args.sdk_smoke_test or (
            isinstance(native_report, dict) and isinstance(native_report.get("shutdown"), dict)
            and native_report["shutdown"].get("ok") is True and native_report.get("ok") is True
        )
        report["cleanup_ok"] = cleanup_ok
        report["status"] = "GREEN" if (
            report["error"] is None and report.get("readiness") is not None
            and all(row.get("ok") is True for row in report["steps"])
            and report["managed_session_thread_finished"] and cleanup_ok
        ) else "RED"
        write()
    return report


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--agent-source-root", type=Path, help="clean worktree root or package src directory")
    result.add_argument("--state-dir", type=Path)
    result.add_argument("--game-dir", type=Path)
    result.add_argument("--bridge-dll", type=Path)
    result.add_argument("--bridge-injector", type=Path)
    result.add_argument("--bridge-pipe", default=r"\\.\pipe\xar_ck3_bridge_migration_12002")
    result.add_argument("--output", type=Path)
    result.add_argument("--plan", type=Path, help="JSON {steps:[...]} or step array")
    result.add_argument("--command-timeout", type=float, default=60)
    result.add_argument("--readiness-timeout", type=float, default=300)
    result.add_argument("--timeout", type=float, default=1800)
    result.add_argument("--poll-interval", type=float, default=0.05)
    result.add_argument("--hold-seconds", type=float, default=0)
    result.add_argument("--control-plan-dir", type=Path, help="read new/updated JSON plans during hold")
    result.add_argument("--turns", type=int, default=0, help="MCP ck3_auto_turn count after the plan")
    result.add_argument("--cold-start-checkpoint", action="store_true")
    result.add_argument("--frontend-robert-bootstrap", action="store_true",
                        help="Use existing typed native stock Robert start before map readiness; no desktop input")
    result.add_argument("--frontend-rules-diagnostic", action="store_true",
                        help="Only with diagnostic-only: directly open native rules and query actual choices before hold; no Apply/Start")
    result.add_argument("--frontend-diagnostic-only", action="store_true",
                        help="Capture typed entry route/tree and hold; never dispatch a frontend action")
    result.add_argument("--allow-verified-direct-bookmarks", action="store_true",
                        help="Allow direct Bookmarks only after complete typed ordinary picker tree admission")
    result.add_argument("--fixture-profile", action="store_true",
                        help="explicit external fixture profile; use owned launch without singleton verification")
    result.add_argument("--native-fixture-inbox", action="store_true",
                        help="write-inbox explicitly invokes the fixed native fixture-run-inbox-v1 step")
    result.add_argument("--print-default-plan", action="store_true")
    result.add_argument("--sdk-smoke-test", action="store_true", help="Python fixture only; never start CK3")
    result.add_argument("--sdk-error-smoke-test", action="store_true",
                        help="one actual SDK tool error; report must be RED and CK3 is never started")
    result.add_argument("--server", action="store_true", help=argparse.SUPPRESS)
    result.add_argument("--fixture-server", action="store_true", help=argparse.SUPPRESS)
    result.add_argument("--native-wire", type=Path, help=argparse.SUPPRESS)
    return result


def main() -> int:
    args = parser().parse_args()
    if args.frontend_rules_diagnostic and not (args.frontend_diagnostic_only and args.frontend_robert_bootstrap):
        raise SystemExit("--frontend-rules-diagnostic requires --frontend-diagnostic-only and --frontend-robert-bootstrap")
    if (args.frontend_diagnostic_only or args.allow_verified_direct_bookmarks) and not args.frontend_robert_bootstrap:
        raise SystemExit("frontend diagnostic/direct-entry options require --frontend-robert-bootstrap")
    if args.frontend_robert_bootstrap and (args.cold_start_checkpoint or args.sdk_smoke_test or args.sdk_error_smoke_test):
        raise SystemExit("frontend Robert bootstrap requires a fresh actual game session, not cold checkpoint or SDK fixture")
    if args.sdk_error_smoke_test:
        args.sdk_smoke_test = True
    if args.native_fixture_inbox and not args.fixture_profile:
        raise SystemExit("--native-fixture-inbox requires --fixture-profile")
    if args.print_default_plan:
        print(json.dumps({"steps": default_plan()}, indent=2))
        return 0
    if args.server:
        fixture_server() if args.fixture_server else native_server(args)
        return 0
    required = ["output"] if args.sdk_smoke_test else [
        "output", "agent_source_root", "state_dir", "game_dir", "bridge_dll", "bridge_injector",
    ]
    if any(getattr(args, name) is None for name in required):
        raise SystemExit("required options: " + ", ".join("--" + name.replace("_", "-") for name in required))
    if min(args.command_timeout, args.readiness_timeout, args.timeout, args.poll_interval) <= 0 or args.hold_seconds < 0 or args.turns < 0:
        raise SystemExit("timeouts/poll interval must be positive; hold/turns must be nonnegative")
    report = asyncio.run(run(args))
    print(json.dumps({"status": report["status"], "output": str(args.output.resolve()),
                      "fixture_only": args.sdk_smoke_test, "error": report["error"]}, ensure_ascii=False))
    return 0 if report["status"] == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
