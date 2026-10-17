"""Publish one exact plan once to the selected shared held host."""
from __future__ import annotations

import argparse
import ast
import copy
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import time

from ck3_mod_acceptance_keeper import check_pin, live_lease, pin, read_json, require, utc, write_new
from ck3_mod_acceptance_launcher import frozen_run


def stable_report(path):
    deadline = time.monotonic() + 2
    while True:
        try:
            before = path.stat()
            raw = path.read_bytes()
            after = path.stat()
            require((before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns),
                    "Actual host report changed during read")
            value = json.loads(raw)
            require(isinstance(value, dict), "Host report object required")
            return value
        except (PermissionError, json.JSONDecodeError, ValueError):
            if time.monotonic() >= deadline:
                raise
            time.sleep(.05)


def native_zero_proof(frozen, report, *, failure_shutdown=False):
    """Use the exact shared host predicate; never infer exit from process absence."""
    argv = frozen["argv"]
    host = Path(argv[argv.index("--agent-source-root") - 1]).resolve()
    check_pin({**frozen["files"][str(host)], "path": str(host)})
    tree = ast.parse(host.read_text(encoding="utf-8-sig"))
    require(type(failure_shutdown) is bool, "failure_shutdown must be a literal boolean")
    predicate = "finished_native_failure_shutdown_proof" if failure_shutdown else "finished_native_exit_zero_proof"
    names = {"finished_native_process_exit_zero_proof", "finished_native_exit_zero_proof"}
    if failure_shutdown:
        names.add(predicate)
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    require(len(nodes) == len(names) and {node.name for node in nodes} == names,
            "Selected shared host has no exact native-zero predicate dependency closure")
    namespace = {"datetime": datetime, "re": re, "copy": copy}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(host), "exec"), namespace)
    return namespace[predicate](report, report.get("managed_session_done") is True, None)


def validate_steps(steps, report):
    require(isinstance(steps, list) and steps and all(isinstance(step, dict) for step in steps),
            "Nonempty original step array required")
    require(all(isinstance(row, dict) and row.get("finished_at") for row in report.get("steps", [])),
            "Original host controls are still in flight")
    ids = [step.get("id") for step in steps]
    require(all(isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,159}", value)
                for value in ids) and len(ids) == len(set(ids)), "Unique explicit control IDs required")
    require(not set(ids) & {row.get("id") for row in report.get("steps", [])},
            "Original step ID already consumed; never replay")
    metadata = report.get("mcp_tools", {}).get("tools")
    require(isinstance(metadata, list) and metadata and all(isinstance(row, dict) for row in metadata),
            "Actual current shared MCP metadata is missing")
    tools = {row.get("name"): row for row in metadata}
    require(len(tools) == len(metadata) and all(isinstance(name, str) for name in tools),
            "Actual current MCP metadata has duplicate or invalid names")
    from jsonschema import Draft202012Validator
    for index, step in enumerate(steps):
        kind = step.get("kind", "tool")
        bind_previous = step.get("bind_previous_revision", False)
        require(type(bind_previous) is bool, "bind_previous_revision must be a literal boolean")
        require(not bind_previous or kind == "tool" and index > 0,
                "Previous-row revision requires a preceding step in the same tool plan")
        require(kind in ("tool", "advance_day", "finish_hold"), "Unqualified shared queue step kind: " + str(kind))
        if kind == "tool":
            name, arguments = step.get("tool"), step.get("args", {})
            require(name in tools and isinstance(arguments, dict), "Tool/argument object is absent from actual MCP metadata")
            require("$" not in json.dumps(arguments), "Queue requires explicit arguments; symbolic host references need a reviewed extension")
            schema = copy.deepcopy(tools[name].get("inputSchema"))
            require(isinstance(schema, dict), "Actual input schema is missing: " + name)
            fresh = step.get("fresh_revision", True)
            require(type(fresh) is bool, "fresh_revision must be a literal boolean")
            if bind_previous:
                require(name in {"ck3_query_ingame_decision_item_v1"} and fresh is False and
                        "expected_revision" in schema.get("properties", {}) and
                        "expected_revision" not in arguments,
                        "Previous-row revision requires a declared readonly query, false fresh flag and no explicit revision")
            # The existing host obtains the exact revision just before dispatch.
            # Leave its omitted revision field out of schema.required; validate
            # every supplied field without manufacturing a placeholder value.
            if (fresh or bind_previous) and "expected_revision" in schema.get("properties", {}) and "expected_revision" not in arguments:
                schema["required"] = [key for key in schema.get("required", []) if key != "expected_revision"]
            Draft202012Validator.check_schema(schema)
            Draft202012Validator(schema).validate(arguments)
        elif kind == "advance_day":
            require(type(step.get("days")) is int and step["days"] == 1,
                    "One original natural day per shared queued step required")
        else:
            require(len(steps) == 1, "Native-zero finish_hold must be the only submitted step")
            require(type(step.get("failure_shutdown", False)) is bool,
                    "failure_shutdown must be a literal boolean")
    return ids


def claim_plan(ledger, name, raw, ids):
    """Exclusive claims survive every failure; a failed attempt is never replayed."""
    ledger = Path(ledger)
    ledger.mkdir(exist_ok=True)
    digest = hashlib.sha256(raw).hexdigest()
    tokens = ["name-" + hashlib.sha256(name.encode()).hexdigest(), "content-" + digest]
    tokens.extend("step-" + hashlib.sha256(value.encode()).hexdigest() for value in ids)
    claimed = []
    try:
        for token in tokens:
            target = ledger / (token + ".json")
            write_new(target, {"at_utc": utc(), "name": name, "plan_sha256": digest, "step_ids": ids,
                               "status": "CONSUMED_BEFORE_PUBLISH_NEVER_REPLAY"})
            claimed.append(str(target))
    except FileExistsError as error:
        raise ValueError("Original control name/content/step ID already attempted; never replay") from error
    return {"sha256": digest, "claims": claimed}


def enqueue_deadline(deadline):
    if deadline is not None:
        require(type(deadline) in (int, float) and 0 < deadline < float("inf"),
                "Finite original queue deadline required")
        if time.monotonic() >= deadline:
            raise TimeoutError("Original once-only queue deadline elapsed; never replay")



STARTUP_RECOVERY_TOOLS = frozenset({
    "ck3_take_snapshot", "ck3_get_capabilities", "ck3_query_current_event_window_context_v1",
    "ck3_query_campaign_root_context_v1", "ck3_query_player_religion_context_v1",
    "ck3_query_player_holy_site_v1", "ck3_save_checkpoint", "ck3_select_event_option",
    "ck3_query_normal_exit_context_v1", "ck3_request_normal_exit_v1", "ck3_observe_normal_exit_v1",
})

def validate_startup_failure_recovery(live, frozen, report, steps, expected_error, reviewer):
    """Explicit same-process continuation; preserve the original startup failure forever."""
    import psutil
    manual_path = live / "case-output/manual-quit-awaiting.json"
    manual = read_json(manual_path)
    require(expected_error == "RuntimeError: scenario startup crossed its typed definition/root/player/frame contract"
            and report.get("error") == expected_error and
            report.get("frontend_diagnostic_hold", {}).get("reason") == expected_error,
            "Only the explicit preserved typed startup error can enter recovery")
    require(manual.get("status") == "MANUAL_QUIT_AWAITING_ORIGINAL_DEADLINE" and
            manual.get("run_id") == frozen["run_id"] == live.name and
            isinstance(reviewer, str) and reviewer and manual.get("reviewer") == reviewer,
            "Recovery reviewer differs from the actual retained-session operator")
    deadline = report.get("hold_until_utc_estimated")
    require(type(deadline) in (int, float) and deadline == manual.get("original_hold_deadline") and
            deadline - time.time() > 90 and not report.get("cleanup_ok") and
            not report.get("managed_session_done") and not report.get("finished_at"),
            "Startup recovery must retain the original live hold and quit reserve")
    require(type(manual.get("pid")) is int and manual["pid"] > 0 and
            type(manual.get("create_time")) in (int, float), "Retained process identity missing")
    process = psutil.Process(manual["pid"])
    require(process.is_running() and process.create_time() == manual["create_time"] and
            process.name().lower() == "ck3.exe", "Original retained CK3 process changed")
    require(all(step.get("kind", "tool") == "tool" and step.get("tool") in STARTUP_RECOVERY_TOOLS
                for step in steps), "Recovery is limited to existing typed startup research and normal-exit tools")
    return {"schema":"ck3-startup-failure-recovery-operation-v1", "at_utc":utc(),
            "machine_id":frozen["run_id"].split("--", 1)[0], "run_id":frozen["run_id"],
            "screen_task":frozen["screen_task"], "reviewer":reviewer, "preserved_error":expected_error,
            "state_dir":report["state_dir"], "pipe":report["pipe"],
            "same_pid":manual["pid"], "same_create_time":manual["create_time"],
            "original_hold_deadline":deadline, "manual_quit_checkpoint":pin(manual_path),
            "original_startup_qualified":False, "host_error_cleared":False, "business_pass":False}

def enqueue(live, plan, name, *, deadline=None, startup_recovery_error=None, startup_recovery_reviewer=None):
    enqueue_deadline(deadline)
    lease_options = {"deadline": deadline} if deadline is not None else {}
    live, plan = Path(live).resolve(), Path(plan).resolve()
    require(Path(name).name == name and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,159}\.json", name),
            "New .json control basename required")
    frozen, context = frozen_run(live, all_pins=False)
    keeper = Path(context["keeper_root"]).resolve()
    lease = live_lease(keeper, frozen, **lease_options)
    enqueue_deadline(deadline)
    report = stable_report(live / "native-report.json")
    require(Path(report["state_dir"]).resolve() == Path(frozen["state_dir"]).resolve() and
            Path(report["agent_source_root"]).resolve() == Path(frozen["source_root"]).resolve(),
            "Actual host report crossed allocated state/shared source")
    require(report.get("pipe") == frozen["argv"][frozen["argv"].index("--bridge-pipe") + 1],
            "Actual host report crossed allocated native pipe")
    require(report.get("phase") == "hold" and not report.get("finished_at") and
            not report.get("hold_finished_by_control_plan"), "Original shared host is no longer held")
    raw = plan.read_bytes()
    require(len(raw) <= 1024 * 1024, "Original control plan exceeds 1 MiB bound")
    value = json.loads(raw.decode("utf-8-sig"))
    require(isinstance(value, dict) and set(value) == {"steps"}, "Original {steps: [...]} plan object required")
    steps = value["steps"]
    ids = validate_steps(steps, report)
    finishing = len(steps) == 1 and steps[0].get("kind") == "finish_hold"
    hold_deadline = report.get("hold_until_utc_estimated")
    require(type(hold_deadline) in (int, float) and hold_deadline - time.time() > (0 if finishing else 90),
            "Original host normal Quit reserve reached")
    recovery = None
    if startup_recovery_error is not None or startup_recovery_reviewer is not None:
        require(not finishing, "Recovery does not replace original finish_hold proof")
        recovery = validate_startup_failure_recovery(live, frozen, report, steps, startup_recovery_error, startup_recovery_reviewer)
    if finishing:
        failure_shutdown = steps[0].get("failure_shutdown") is True
        require(native_zero_proof(frozen, report, failure_shutdown=failure_shutdown) is not None,
                "Original shared native-zero predicate rejects finish_hold")
    else:
        require((not report.get("error") or recovery is not None) and not report.get("cleanup_ok"), "Original host failed or completed cleanup")
    argv = frozen["argv"]
    controls = Path(argv[argv.index("--control-plan-dir") + 1]).resolve()
    require(controls == live / "controls" and controls.is_dir(), "Control directory crossed actual allocation")
    target = controls / name
    require(not target.exists(), "Original control target already exists; never overwrite")
    enqueue_deadline(deadline)
    claims = claim_plan(live / "control-once-ledger", name, raw, ids)
    if recovery is not None:
        original = live / "startup-recovery-original-error.json"
        if original.exists():
            prior = read_json(original)
            require(prior.get("error") == recovery["preserved_error"] and
                    prior.get("state_dir") == report["state_dir"] and prior.get("pipe") == report["pipe"] and
                    prior.get("hold_until_utc_estimated") == recovery["original_hold_deadline"],
                    "Original recovery failure evidence changed")
        else:
            write_new(original, report)
        recovery.update(plan=pin(plan), plan_sha256=claims["sha256"], step_ids=ids,
                        preserved_failed_report=pin(original), frozen_argv=pin(live/"frozen-argv.json"))
        write_new(live / ("startup-recovery-operation-" + claims["sha256"] + ".json"), recovery)
    # Hard-link a fully written private file into the observed *.json namespace.
    # os.link is atomic and refuses an existing target on Windows and POSIX.
    with tempfile.NamedTemporaryFile(mode="wb", prefix="pending-", suffix=".tmp", dir=controls, delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    require(pin(temporary)["sha256"] == claims["sha256"], "Exact control bytes changed before publish")
    try:
        latest = live_lease(keeper, frozen, **lease_options)
        enqueue_deadline(deadline)
        os.link(temporary, target)
    finally:
        # The pending filename is never consumed by the host. Preserve it on
        # publication failure to keep the original evidence append-only.
        if target.exists() and target.read_bytes() == raw:
            temporary.unlink()
    result = {"status": "QUEUED_ONCE_ACK_NOT_BUSINESS_PASS", "at_utc": utc(), "run_id": frozen["run_id"],
              "plan": pin(plan), "published": pin(target), "step_ids": ids,
              "lease": latest["lease"], "claims": claims, "business_pass": False}
    if recovery is not None:
        result["startup_failure_recovery"] = recovery
    write_new(live / "control-once-ledger" / ("receipt-" + claims["sha256"] + ".json"), result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--timeout-seconds", type=float, help="Bound this original submission; no retries")
    parser.add_argument("--startup-recovery-error", help="Explicit original failed-startup error; default preserves ordinary guard")
    parser.add_argument("--startup-recovery-reviewer", help="Actual retained-session operator")
    args = parser.parse_args(argv)
    try:
        if args.timeout_seconds is not None:
            require(0 < args.timeout_seconds < float("inf"), "Finite positive queue timeout required")
        deadline = None if args.timeout_seconds is None else time.monotonic() + args.timeout_seconds
        print(json.dumps(enqueue(args.live, args.plan, args.name, deadline=deadline,
            startup_recovery_error=args.startup_recovery_error,
            startup_recovery_reviewer=args.startup_recovery_reviewer)), flush=True)
        return 0
    except Exception as error:
        print(json.dumps({"status": "BLOCKED_NEVER_REPLAY", "error": repr(error), "business_pass": False}), flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
