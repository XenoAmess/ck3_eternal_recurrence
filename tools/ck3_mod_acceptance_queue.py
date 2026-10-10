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


def native_zero_proof(frozen, report):
    """Use the exact shared host predicate; never infer exit from process absence."""
    argv = frozen["argv"]
    host = Path(argv[argv.index("--agent-source-root") - 1]).resolve()
    check_pin({**frozen["files"][str(host)], "path": str(host)})
    tree = ast.parse(host.read_text(encoding="utf-8-sig"))
    names = {"finished_native_process_exit_zero_proof", "finished_native_exit_zero_proof"}
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    require(len(nodes) == len(names) and {node.name for node in nodes} == names,
            "Selected shared host has no exact native-zero predicate dependency closure")
    namespace = {"datetime": datetime, "re": re, "copy": copy}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(host), "exec"), namespace)
    return namespace["finished_native_exit_zero_proof"](report, report.get("managed_session_done") is True, None)


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
    for step in steps:
        kind = step.get("kind", "tool")
        require(kind in ("tool", "advance_day", "finish_hold"), "Unqualified shared queue step kind: " + str(kind))
        if kind == "tool":
            name, arguments = step.get("tool"), step.get("args", {})
            require(name in tools and isinstance(arguments, dict), "Tool/argument object is absent from actual MCP metadata")
            require("$" not in json.dumps(arguments), "Queue requires explicit arguments; symbolic host references need a reviewed extension")
            schema = copy.deepcopy(tools[name].get("inputSchema"))
            require(isinstance(schema, dict), "Actual input schema is missing: " + name)
            fresh = step.get("fresh_revision", True)
            require(type(fresh) is bool, "fresh_revision must be a literal boolean")
            # The existing host obtains the exact revision just before dispatch.
            # Leave its omitted revision field out of schema.required; validate
            # every supplied field without manufacturing a placeholder value.
            if fresh and "expected_revision" in schema.get("properties", {}) and "expected_revision" not in arguments:
                schema["required"] = [key for key in schema.get("required", []) if key != "expected_revision"]
            Draft202012Validator.check_schema(schema)
            Draft202012Validator(schema).validate(arguments)
        elif kind == "advance_day":
            require(type(step.get("days")) is int and step["days"] == 1,
                    "One original natural day per shared queued step required")
        else:
            require(len(steps) == 1, "Native-zero finish_hold must be the only submitted step")
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


def enqueue(live, plan, name):
    live, plan = Path(live).resolve(), Path(plan).resolve()
    require(Path(name).name == name and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,159}\.json", name),
            "New .json control basename required")
    frozen, context = frozen_run(live, all_pins=False)
    keeper = Path(context["keeper_root"]).resolve()
    lease = live_lease(keeper, frozen)
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
    deadline = report.get("hold_until_utc_estimated")
    require(type(deadline) in (int, float) and deadline - time.time() > (0 if finishing else 90),
            "Original host normal Quit reserve reached")
    if finishing:
        require(native_zero_proof(frozen, report) is not None, "Original shared native-zero predicate rejects finish_hold")
    else:
        require(not report.get("error") and not report.get("cleanup_ok"), "Original host failed or completed cleanup")
    argv = frozen["argv"]
    controls = Path(argv[argv.index("--control-plan-dir") + 1]).resolve()
    require(controls == live / "controls" and controls.is_dir(), "Control directory crossed actual allocation")
    target = controls / name
    require(not target.exists(), "Original control target already exists; never overwrite")
    claims = claim_plan(live / "control-once-ledger", name, raw, ids)
    # Hard-link a fully written private file into the observed *.json namespace.
    # os.link is atomic and refuses an existing target on Windows and POSIX.
    with tempfile.NamedTemporaryFile(mode="wb", prefix="pending-", suffix=".tmp", dir=controls, delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    require(pin(temporary)["sha256"] == claims["sha256"], "Exact control bytes changed before publish")
    try:
        latest = live_lease(keeper, frozen)
        os.link(temporary, target)
    finally:
        # The pending filename is never consumed by the host. Preserve it on
        # publication failure to keep the original evidence append-only.
        if target.exists() and target.read_bytes() == raw:
            temporary.unlink()
    result = {"status": "QUEUED_ONCE_ACK_NOT_BUSINESS_PASS", "at_utc": utc(), "run_id": frozen["run_id"],
              "plan": pin(plan), "published": pin(target), "step_ids": ids,
              "lease": latest["lease"], "claims": claims, "business_pass": False}
    write_new(live / "control-once-ledger" / ("receipt-" + claims["sha256"] + ".json"), result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--name", required=True)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(enqueue(args.live, args.plan, args.name)), flush=True)
        return 0
    except Exception as error:
        print(json.dumps({"status": "BLOCKED_NEVER_REPLAY", "error": repr(error), "business_pass": False}), flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
