"""File-only recovery consumer for an already running episode01 game.

Read named successful rows from the owner's existing control report. Reuse the
frozen host's strict preparation-event observer with preserved native packets;
never connect to MCP, Start, select, save, edit the original report or clear RED.
"""
from __future__ import annotations

import argparse
import asyncio
import copy
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time


def load_host(path: Path, agent_source: Path):
    sys.path.insert(0, str(agent_source / "ck3_autonomous_player" / "src"))
    spec = importlib.util.spec_from_file_location("faith_e01_preserved_packet_host", path)
    module = importlib.util.module_from_spec(spec)
    if spec is None or spec.loader is None:
        raise ValueError("host source is not loadable")
    spec.loader.exec_module(module)
    return module


def successful_row(report: dict, name: str, tool: str) -> dict:
    rows = [row for row in report.get("steps", []) if isinstance(row, dict) and row.get("id") == name]
    if len(rows) != 1 or rows[0].get("ok") is not True or rows[0].get("plan", {}).get("tool") != tool:
        raise ValueError("recovery needs one successful exact tool row: " + name)
    result = rows[0].get("result")
    if not isinstance(result, dict):
        raise ValueError("recovery tool result is not an object: " + name)
    return result


async def revalidate(host, report: dict, *, previous_row: str, current_row: str,
        event_row: str, after_row: str, root_row: str | None, expected_pid: int,
        expected_generation: int) -> dict:
    submission = report["frontend_fixture_start_submission"]["result"]
    policy = report["frontend_fixture_start_policy_input"]["policy"]
    host.require_fixture_policy_submission(submission, policy)
    if submission["binding"] != {"bridge_pid": expected_pid, "connection_generation": expected_generation}:
        raise ValueError("recovery crossed the owner's original Start process/connection")
    previous = successful_row(report, previous_row, "ck3_take_snapshot")
    current = successful_row(report, current_row, "ck3_take_snapshot")
    packet = successful_row(report, event_row, "ck3_query_current_event_window_context_v1")
    after = successful_row(report, after_row, "ck3_take_snapshot")

    def frame(snapshot):
        value = host.fixture_whole_root_admission_frame(snapshot, submission, allow_active_event=True)
        if value is None:
            raise ValueError("recovery packet lacks its paused owner frame")
        event = snapshot.get("active_event")
        mailbox = snapshot.get("diagnostics", {}).get("last_heartbeat", {}).get("main_thread_query_mailbox_v1", {})
        if not isinstance(event, dict) or type(event.get("instance_id")) is not int:
            raise ValueError("recovery packet lacks the actual active event")
        return {**value, "event_instance_id": event["instance_id"], "owner_tid": mailbox["owner_tid"]}

    positions = {row["id"]: index for index, row in enumerate(report["steps"]) if isinstance(row, dict)}
    names = [previous_row, current_row, event_row, after_row]
    if len(set(names)) != 4 or [positions[name] for name in names] != sorted(positions[name] for name in names):
        raise ValueError("recovery rows must be distinct and observed in before/before/context/after order")
    state = {"first_startup_query_admission": {"previous_frame": frame(previous), "current_frame": frame(current)}}

    class PreservedPackets:
        async def call(self, tool, arguments=None):
            wanted = {"event_instance_id": current["active_event"]["instance_id"],
                "expected_revision": current["revision"]}
            if tool != "ck3_query_current_event_window_context_v1" or arguments != wanted:
                raise RuntimeError("file-only revalidation cannot dispatch a game operation")
            return copy.deepcopy(packet)

        async def fresh(self):
            return copy.deepcopy(after)

    observed = await host.observe_fixture_scenario_startup_event(PreservedPackets(), current, submission,
        policy, state=state, write=lambda: None, deadline=time.monotonic() + 10)
    root_binding = None
    if root_row is not None:
        root = successful_row(report, root_row, "ck3_query_campaign_root_context_v1")
        if positions[root_row] <= positions[after_row]:
            raise ValueError("business root query must follow the independent after snapshot")
        from xar_autoplayer.bridge.frontend_fixture_start_contract import fixture_business_context_binding
        root_binding = fixture_business_context_binding(observed, root, policy, submission)
        if root_binding is None:
            raise ValueError("recovery campaign root does not prove its declared scenario predicates")
    startup = state["startup_case"]
    return {"status": "PRESERVED_PREPARATION_PACKETS_REVALIDATED", "bridge_pid": expected_pid,
        "connection_generation": expected_generation, "actor_character_id": frame(observed)["actor_character_id"],
        "date_raw": observed["date_raw"], "event_instance_id": observed["active_event"]["instance_id"],
        "event_definition_key": policy["startup_event_admission"]["event_definition_key"],
        "native_option_indices": startup["native_option_indices"], "selected_any_option": False,
        "original_host_error": report.get("error"), "original_host_error_preserved": True,
        "original_host_run_green": False, "game_operations_performed_by_this_consumer": False,
        "verification_scope": "offline validation of the owner's preserved actual packets; no new live query",
        "row_ids": names + ([root_row] if root_row else []), "business_context_binding": root_binding,
        "fixture_target_identity_proven": False, "product_acceptance_proven": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--host-source", type=Path, required=True)
    parser.add_argument("--agent-source-root", type=Path, required=True)
    parser.add_argument("--identity-helper", type=Path, required=True)
    parser.add_argument("--expected-machine-id", required=True)
    parser.add_argument("--expected-pid", type=int, required=True)
    parser.add_argument("--expected-generation", type=int, required=True)
    parser.add_argument("--previous-row", required=True)
    parser.add_argument("--current-row", required=True)
    parser.add_argument("--event-row", required=True)
    parser.add_argument("--after-row", required=True)
    parser.add_argument("--root-row")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.output.exists() or args.output.resolve() in (args.report.resolve(), args.host_source.resolve()):
        raise ValueError("recovery output must be new and separate from the original report/source")
    machine = subprocess.check_output([sys.executable, str(args.identity_helper.resolve()), "machine"], text=True).strip()
    if machine != args.expected_machine_id:
        raise ValueError("recovery consumer is running on a different machine")
    raw = args.report.read_bytes()
    source = args.host_source.read_bytes()
    report = json.loads(raw.decode("utf-8-sig"))
    host = load_host(args.host_source, args.agent_source_root)
    result = asyncio.run(revalidate(host, report, previous_row=args.previous_row, current_row=args.current_row,
        event_row=args.event_row, after_row=args.after_row, root_row=args.root_row,
        expected_pid=args.expected_pid, expected_generation=args.expected_generation))
    result.update(schema="xar.ck3.faith-e01-preserved-packet-revalidation/v1", machine_id=machine,
        observed_at_utc=dt.datetime.now(dt.UTC).isoformat(), evidence={
            "report": {"path": str(args.report.resolve()), "sha256": hashlib.sha256(raw).hexdigest()},
            "host_source": {"path": str(args.host_source.resolve()), "sha256": hashlib.sha256(source).hexdigest()}})
    with args.output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
