"""One persistent official MCP Client(cache=None) for explicit JSON requests.

Creating/enqueueing requests does not contact CK3. Only `serve` starts the
existing stdio server, and only explicit call_tool requests invoke its tools.
No automatic attach, retry, reconnect, gameplay policy or desktop input.
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import uuid

from r9_mcp_consumer_binding import load_binding, verify_live_inventory

BASE = Path("C:/workspace/ck3_lyd_runtime_20261004")
REPO = Path("C:/workspace/ck3_eternal_recurrence")
SERVER = REPO / "tools/ck3_native_profile_mcp.py"
ATTACH = "ck3_attach_profile_bridge_v1"
TOOLS = {
    "ck3_query_native_profile_v1", ATTACH, "ck3_resume_profile_bridge_v1",
    "ck3_take_profile_native_snapshot_v1", "ck3_query_profile_event_window_v1",
    "ck3_query_profile_pending_interaction_v1", "ck3_reply_profile_pending_interaction_v1",
    "ck3_set_profile_simulation_v1", "ck3_pause_profile_simulation_v1",
    "ck3_select_profile_event_option_v1", "ck3_save_profile_checkpoint_v1",
    "ck3_open_profile_decisions_v1", "ck3_query_profile_decision_item_v1",
    "ck3_select_profile_decision_item_v1", "ck3_confirm_profile_decision_outcome_v1",
    "ck3_query_profile_current_actor_stress_adjustment_v1",
    "ck3_query_profile_character_interaction_ordinary_v1",
    "ck3_initiate_profile_character_interaction_ordinary_v1",
    "ck3_query_normal_exit_context_v1",
    "ck3_request_normal_exit_v1",
    "ck3_observe_profile_normal_exit_v1",
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_fresh(path: Path, payload: dict) -> None:
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def inside(path: Path) -> Path:
    path = path.resolve()
    if BASE not in path.parents:
        raise ValueError("queue/output must be inside this external work package")
    return path


def validate_request(payload: dict) -> dict:
    if not isinstance(payload, dict) or payload.get("schema") != "ck3.lyd.mcp-request.v1":
        raise ValueError("wrong MCP request schema")
    request_id = payload.get("request_id")
    if not isinstance(request_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,95}", request_id):
        raise ValueError("request_id must be a portable unique identifier")
    operation = payload.get("operation")
    required = {"schema", "request_id", "operation"}
    if operation == "call_tool":
        required |= {"name", "arguments"}
        if payload.get("name") not in TOOLS or not isinstance(payload.get("arguments"), dict):
            raise ValueError("use one existing closed native tool and a JSON argument object")
    elif operation not in {"list_tools", "close"}:
        raise ValueError("operation must be list_tools, call_tool or close")
    if set(payload) != required:
        raise ValueError(f"request requires exactly {sorted(required)}")
    return payload


def enqueue(queue: Path, request_file: Path) -> dict:
    queue = inside(queue)
    queue.mkdir(parents=True, exist_ok=True)
    raw = request_file.read_bytes()
    request = validate_request(json.loads(raw.decode("utf-8-sig")))
    target = queue / f"{request['request_id']}.request.json"
    # Publish only a completely written file; hard-link creation refuses an
    # existing ID atomically on the local NTFS workspace. Keep the source bytes.
    staged = queue / f"{request['request_id']}.{uuid.uuid4().hex}.input"
    with staged.open("xb") as stream:
        stream.write(raw)
    os.link(staged, target)
    return {"queued": str(target), "request_id": request["request_id"], "sha256": sha(target), "contacted_game": False}


def preserve_native_receipts(value, output: Path, native_evidence: Path, prefix: str) -> list[dict]:
    """Copy authoritative receipt bytes, preserving SDK result data separately."""
    found = set()

    def walk(item):
        if isinstance(item, dict):
            if isinstance(item.get("receipt_path"), str):
                found.add(item["receipt_path"])
            for child in item.values():
                walk(child)
        elif isinstance(item, list):
            for child in item:
                walk(child)
        elif isinstance(item, str):
            try:
                decoded = json.loads(item)
            except ValueError:
                return
            if isinstance(decoded, (dict, list)):
                walk(decoded)

    walk(value)
    artifacts = []
    for index, name in enumerate(sorted(found), 1):
        path = Path(name).resolve()
        if native_evidence not in path.parents or not path.is_file():
            artifacts.append({"path": str(path), "status": "NOT_COPIED", "reason": "outside native evidence directory or missing"})
            continue
        target = output / f"{prefix}.native-{index:02d}.json"
        with target.open("xb") as stream:
            stream.write(path.read_bytes())
        artifacts.append({"path": str(path), "copy": target.name, "sha256": sha(target)})
    return artifacts


def admit_call_tool(request: dict, *, inventory_verified: bool, terminal_exit_requested: bool) -> bool:
    if not inventory_verified:
        raise RuntimeError("queue an explicit list_tools first; actual inventory is not verified")
    if terminal_exit_requested and request["name"] != "ck3_observe_profile_normal_exit_v1":
        raise RuntimeError("after terminal exit attempt only explicit retained-handle observation or close is allowed")
    if request["name"] == "ck3_observe_profile_normal_exit_v1" and request["arguments"] != {}:
        raise ValueError("exit observer has no public arguments")
    return (request["name"] == "ck3_request_normal_exit_v1"
            and request["arguments"].get("action") == "confirm_desktop")


async def serve(profile: Path, queue: Path, output: Path, binding_file: Path, binding_sha256: str) -> None:
    binding = load_binding(binding_file, binding_sha256, profile=profile, queue=queue, output=output, tools=TOOLS)
    from mcp import Client
    from mcp.client.stdio import StdioServerParameters, stdio_client

    queue, output = inside(queue), inside(output)
    if output.exists():
        raise ValueError("choose a fresh client output directory; sessions are not restarted or replayed")
    queue.mkdir(parents=True, exist_ok=True)
    output.mkdir(parents=True)
    profile_data = json.loads(profile.read_text(encoding="utf-8-sig"))
    native_evidence = Path(profile_data["evidence_directory"]).resolve()
    session = {"schema": "ck3.lyd.persistent-mcp-session.v1", "client_session_id": uuid.uuid4().hex,
               "profile": str(profile.resolve()), "profile_sha256": sha(profile), "server": str(SERVER),
               "server_sha256": sha(SERVER), "interpreter": sys.executable, "queue": str(queue),
               "started_at_utc": now(), "cache": None, "automatic_attach": False, "automatic_retry": False,
               "binding_file": str(binding_file.resolve()), "binding_sha256": binding_sha256,
               "epoch_id": binding["epoch_id"], "source_revision": binding["source_revision"],
               "target": binding["target"], "live_inventory_verified": False}
    write_fresh(output / "session.json", session)
    # A queue belongs to one consumer session. A new server must get a new
    # queue, so historical attach/control requests are never replayed.
    write_fresh(queue / "consumer-session.json", session)
    attach_requested = False
    inventory_verified = False
    terminal_exit_requested = False
    claimed = set()
    sequence = 0
    environment = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    parameters = StdioServerParameters(command=sys.executable,
                                       args=["-X", "utf8", str(SERVER), "--profile", str(profile.resolve())],
                                       cwd=str(REPO), env=environment)
    try:
        with (output / "server.stderr.log").open("w", encoding="utf-8") as errors:
            transport = stdio_client(parameters, errlog=errors)
            async with Client(transport, cache=None) as client:
                write_fresh(output / "ready.json", {**session, "ready_at_utc": now(), "status": "CLIENT_CONNECTED; bridge NOT_ATTACHED automatically"})
                print(json.dumps({"ready": str(output / "ready.json"), "queue": str(queue)}, ensure_ascii=False), flush=True)
                while True:
                    pending = [path for path in sorted(queue.glob("*.request.json")) if path.name not in claimed]
                    if not pending:
                        await asyncio.sleep(0.2)
                        continue
                    for path in pending:
                        claimed.add(path.name)
                        sequence += 1
                        prefix = f"{sequence:04d}-{path.name[:-13]}"
                        raw = path.read_bytes()
                        with (output / f"{prefix}.request.json").open("xb") as stream:
                            stream.write(raw)
                        record = {"schema": "ck3.lyd.mcp-dispatch.v1", "sequence": sequence,
                                  "request_path": str(path), "request_sha256": sha(path), "started_at_utc": now()}
                        write_fresh(output / f"{prefix}.started.json", record)
                        close_requested = False
                        try:
                            request = validate_request(json.loads(raw.decode("utf-8-sig")))
                            record["request_id"] = request["request_id"]
                            if request["operation"] == "close":
                                record["status"] = "CLIENT_CLOSE_REQUESTED"
                                close_requested = True
                            else:
                                if request["operation"] == "list_tools":
                                    result = await client.list_tools()
                                else:
                                    terminal_exit_requested = (admit_call_tool(request,
                                        inventory_verified=inventory_verified,
                                        terminal_exit_requested=terminal_exit_requested) or terminal_exit_requested)
                                    if request["name"] == ATTACH:
                                        if attach_requested:
                                            raise RuntimeError("attach was already requested in this client session; no replay")
                                        attach_requested = True
                                    result = await client.call_tool(request["name"], request["arguments"], read_timeout_seconds=60)
                                # This is the SDK's unmodified typed result, not a
                                # synthesized business status or wire-packet claim.
                                payload = result.model_dump(mode="json", by_alias=True, exclude_none=False)
                                result_path = output / f"{prefix}.sdk-result.json"
                                write_fresh(result_path, payload)
                                if request["operation"] == "list_tools":
                                    verify_live_inventory(payload, binding, tools=TOOLS)
                                    inventory_verified = True
                                record.update(status="MCP_RESULT_RECORDED", is_error=getattr(result, "isError", None),
                                              sdk_result=result_path.name, sdk_result_sha256=sha(result_path),
                                              native_receipts=preserve_native_receipts(payload, output, native_evidence, prefix))
                        except Exception as error:
                            record.update(status="ERROR_NO_RETRY", reason=f"{type(error).__name__}: {error}")
                        record["finished_at_utc"] = now()
                        write_fresh(output / f"{prefix}.response.json", record)
                        print(json.dumps({"request": path.name, "response": str(output / f"{prefix}.response.json"), "status": record["status"]}, ensure_ascii=False), flush=True)
                        if close_requested:
                            return
    except BaseException as error:
        write_fresh(output / "session-terminated.json", {"finished_at_utc": now(), "reason": f"{type(error).__name__}: {error}",
                                                       "retry": False, "reattach": False})
        raise
    finally:
        if not (output / "session-closed.json").exists():
            write_fresh(output / "session-closed.json", {"closed_at_utc": now(), "claimed_requests": sorted(claimed),
                                                       "attach_requested": attach_requested})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    send = commands.add_parser("enqueue", help="preserve one explicit request JSON without contacting CK3")
    send.add_argument("--queue", type=Path, required=True)
    send.add_argument("--request", type=Path, required=True)
    run = commands.add_parser("serve", help="keep one official stdio MCP session; dispatch only queued requests")
    run.add_argument("--profile", type=Path, required=True)
    run.add_argument("--queue", type=Path, required=True)
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--binding", type=Path, required=True)
    run.add_argument("--binding-sha256", required=True)
    args = parser.parse_args()
    if args.command == "enqueue":
        print(json.dumps(enqueue(args.queue, args.request), ensure_ascii=False, indent=2))
    else:
        asyncio.run(serve(args.profile, args.queue, args.output, args.binding, args.binding_sha256))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
