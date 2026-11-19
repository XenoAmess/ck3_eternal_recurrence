"""Publish one exact plan once to the selected shared held host."""
from __future__ import annotations

import argparse
import ast
import copy
from contextlib import contextmanager
from collections.abc import Mapping
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import time
from collections.abc import Iterator
from typing import Protocol, runtime_checkable

from ck3_mod_acceptance_keeper import check_pin, live_lease, pin, read_json, require, utc, write_new
from ck3_mod_acceptance_launcher import frozen_run
from ck3_mod_acceptance_background_types import strings_field, text_field


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


NORMAL_EXIT_NATIVE_TOOLS = frozenset({"ck3_query_normal_exit_context_v1", "ck3_request_normal_exit_v1"})


def _require_failed_host_exit_plan_v1(steps: object, frozen: object) -> None:
    """Use the host's existing exit-only contract; never grant business recovery."""
    with _frozen_exit_sdk_v1(frozen) as (_, _, terminal):
        terminal.require_failed_host_normal_exit_plan_v1(steps)


def _normal_exit_plan_v1(steps: object, frozen: object) -> bool:
    if (not isinstance(steps, list) or len(steps) != 1 or not isinstance(steps[0], dict)
            or steps[0].get('tool') not in (*NORMAL_EXIT_NATIVE_TOOLS, 'ck3_observe_normal_exit_v1')):
        return False
    _require_failed_host_exit_plan_v1(steps, frozen)
    return True


def _queue_object(value: object, label: str) -> dict[str, object]:
    """Validate the inspected JSON object without trusting an annotation or alias."""
    if not isinstance(value, dict):
        raise ValueError(label + " object required")
    result: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ValueError(label + " requires string field names")
        result[key] = item
    return result


def _native_capability_names(value: object, label: str) -> frozenset[str]:
    if not isinstance(value, list):
        raise ValueError(label + " capability string array required")
    result: set[str] = set()
    for item in value:
        if not isinstance(item, str) or not item or item in result:
            raise ValueError(label + " has an invalid or duplicate capability")
        result.add(item)
    return frozenset(result)


def _native_positive_integer(value: object, label: str) -> int:
    if type(value) is not int or value < 1:
        raise ValueError(label + " requires a positive literal integer")
    return value


@runtime_checkable
class _ExitBuildV1(Protocol):
    @property
    def game_version(self) -> str: ...


@runtime_checkable
class _ExitVersionV1(Protocol):
    CK3_12004: _ExitBuildV1
    CK3_1210: _ExitBuildV1
    def require_exact_native_build(self, game_version: object, executable_sha256: object) -> _ExitBuildV1: ...


@runtime_checkable
class _ExitContractV1(Protocol):
    CORE_EXIT_CAPABILITY: str
    NORMAL_EXIT_MAP_CAPABILITY: str


@runtime_checkable
class _ExitTerminalV1(Protocol):
    def require_failed_host_normal_exit_plan_v1(self, value: object) -> None: ...


def _exit_sdk_bytes_v1(path: Path, reference: object) -> bytes:
    """Read exact frozen metadata; no import path or installed-package fallback."""
    row = _queue_object(reference, "Frozen exit SDK source pin")
    if set(row) not in ({"bytes", "sha256"}, {"path", "bytes", "sha256"}):
        raise ValueError("Frozen exit SDK source pin fields differ")
    if "path" in row and (not isinstance(row["path"], str) or Path(row["path"]).resolve() != path.resolve()):
        raise ValueError("Frozen exit SDK source pin crossed its exact path")
    size, digest = row.get("bytes"), row.get("sha256")
    if (type(size) is not int or size < 1 or size > 2 * 1024 * 1024
            or not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None
            or path.is_symlink() or not path.is_file()):
        raise ValueError("Frozen exit SDK source pin is malformed or unavailable")
    raw = path.read_bytes()
    if len(raw) != size or hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError("Frozen exit SDK source bytes changed: " + str(path))
    return raw


@contextmanager
def _frozen_exit_sdk_v1(frozen_value: object) -> Iterator[tuple[_ExitVersionV1, _ExitContractV1, _ExitTerminalV1]]:
    """Consume the original SDK leaves from this allocation's pinned source index."""
    import secrets
    import sys
    import types
    frozen = _queue_object(frozen_value, "Frozen exit SDK allocation")
    source = frozen.get("source_root")
    manifest = _queue_object(frozen.get("runtime_manifest"), "Frozen runtime manifest")
    manifest_path = manifest.get("path")
    if not isinstance(source, str) or not source or not isinstance(manifest_path, str) or not manifest_path:
        raise ValueError("Frozen exit SDK source/runtime paths required")
    root = Path(source).resolve(strict=True)
    index_path = Path(manifest_path).resolve(strict=True).with_name("source-index.json")
    files = _queue_object(frozen.get("files"), "Frozen allocation source pins")
    index = _queue_object(json.loads(_exit_sdk_bytes_v1(index_path, files.get(str(index_path)))), "Frozen SDK index")
    if index.get("schema") != "ck3-common-source-index-v1":
        raise ValueError("Frozen exit SDK requires the canonical source index")
    rows = _queue_object(index.get("files"), "Frozen SDK index files")
    names = ("normal_exit_process_observer_v1", "normal_exit_contract_v1", "normal_exit_public_wire_v2",
        "normal_exit_host_terminal_v1", "version_identity")
    sources: list[tuple[str, Path, bytes]] = []
    for name in names:
        relative = "ck3_autonomous_player/src/xar_autoplayer/bridge/" + name + ".py"
        path = root / relative
        if not path.resolve().is_relative_to(root):
            raise ValueError("Frozen exit SDK leaf crossed its source root")
        sources.append((name, path, _exit_sdk_bytes_v1(path, rows.get(relative))))
    namespace = "_queue_exit_sdk_" + secrets.token_hex(16)
    package = types.ModuleType(namespace)
    package.__path__ = []
    if namespace in sys.modules:
        raise ValueError("Frozen exit SDK private namespace collision")
    loaded: dict[str, types.ModuleType] = {namespace: package}
    sys.modules[namespace] = package
    modules: dict[str, types.ModuleType] = {}
    try:
        for name, path, raw in sources:
            module = types.ModuleType(namespace + "." + name)
            module.__file__ = str(path)
            module.__package__ = namespace
            sys.modules[module.__name__] = module
            loaded[module.__name__] = module
            exec(compile(raw, str(path), "exec"), module.__dict__)
            modules[name] = module
        version, contract, terminal = (modules["version_identity"], modules["normal_exit_contract_v1"],
            modules["normal_exit_host_terminal_v1"])
        if (not isinstance(version, _ExitVersionV1) or not isinstance(contract, _ExitContractV1)
                or not isinstance(terminal, _ExitTerminalV1)):
            raise ValueError("Frozen exit SDK source API differs")
        yield version, contract, terminal
    finally:
        for name, module in reversed(tuple(loaded.items())):
            if sys.modules.get(name) is module:
                del sys.modules[name]


def validate_normal_exit_native_capability(tool_name: str, report: object, frozen: object = None) -> None:
    """Gate only native exit query/request; OS retained-handle observation stays usable.

    Select the existing SDK route by the exact native build, never by a
    plausible capability alias. MCP registration/action_steps alone do not prove
    the selected DLL advertises it. The caller has already bound this report's
    state, source and pipe to the frozen run before any once-only claim.
    """
    if tool_name not in NORMAL_EXIT_NATIVE_TOOLS:
        return
    current = _queue_object(report, "Actual native report")
    capabilities = _queue_object(current.get("capabilities"), "Actual native capabilities")
    diagnostics = _queue_object(capabilities.get("diagnostics"), "Actual native capability diagnostics")
    hello = _queue_object(diagnostics.get("hello"), "Actual native hello")
    pipe = current.get("pipe")
    if (not isinstance(pipe, str) or not pipe or diagnostics.get("pipe_name") != pipe
            or diagnostics.get("connected") is not True or hello.get("type") != "hello"):
        raise ValueError("Actual native hello is not bound to the current connected pipe")
    for envelope in (diagnostics, hello):
        if type(envelope.get("protocol_version")) is not int or envelope["protocol_version"] != 1:
            raise ValueError("Actual native hello protocol_version must be literal integer 1")
    pid = _native_positive_integer(diagnostics.get("bridge_pid"), "Actual native bridge PID")
    hello_pid = _native_positive_integer(hello.get("pid"), "Actual native hello PID")
    generation = _native_positive_integer(diagnostics.get("connection_generation"), "Actual native connection generation")
    hello_generation = _native_positive_integer(hello.get("connection_generation"), "Actual native hello connection generation")
    if pid > 0xFFFFFFFF or pid != hello_pid or generation != hello_generation:
        raise ValueError("Actual native hello PID/connection generation differs from its diagnostics")
    exported = _native_capability_names(capabilities.get("bridge_capabilities"), "Actual native bridge")
    advertised = _native_capability_names(hello.get("capabilities"), "Actual native hello")
    if exported != advertised:
        raise ValueError("Actual native bridge capabilities differ from the bound native hello")
    with _frozen_exit_sdk_v1(frozen) as (version, contract, _):
        build = version.require_exact_native_build(hello.get("expected_ck3_version"), hello.get("expected_ck3_sha256"))
        if (build not in (version.CK3_12004, version.CK3_1210) or hello.get("ck3_build_match") is not True
                or hello.get("game_adapter_id") != "ck3-" + build.game_version + "-msvc-x64"):
            raise ValueError("Actual native normal-exit hello lacks its supported exact build/adapter match")
        required_capability = (contract.CORE_EXIT_CAPABILITY if build == version.CK3_1210
            else contract.NORMAL_EXIT_MAP_CAPABILITY)
        # The SDK gives Core ApplicationExit precedence over the legacy route.
        if build == version.CK3_12004 and contract.CORE_EXIT_CAPABILITY in advertised:
            raise ValueError("Actual native normal-exit capability belongs to a different exact build")
        if required_capability not in advertised:
            raise ValueError(tool_name + ": actual native " + required_capability +
                " capability is unavailable (default OFF); rejected before claim/publish")


def validate_steps(steps: object, report: object, frozen: object = None) -> list[str]:
    current = _queue_object(report, "Actual host report")
    if not isinstance(steps, list) or not steps:
        raise ValueError("Nonempty original step array required")
    original_steps = [_queue_object(step, "Original step") for step in steps]
    previous = current.get("steps", [])
    if not isinstance(previous, list):
        raise ValueError("Original host step array required")
    previous_rows = [_queue_object(row, "Original host step") for row in previous]
    require(all(row.get("finished_at") for row in previous_rows),
            "Original host controls are still in flight")
    ids: list[str] = []
    for step in original_steps:
        value = step.get("id")
        if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,159}", value):
            raise ValueError("Unique explicit control IDs required")
        ids.append(value)
    require(len(ids) == len(set(ids)), "Unique explicit control IDs required")
    require(not set(ids) & {row.get("id") for row in previous_rows},
            "Original step ID already consumed; never replay")
    metadata = _queue_object(current.get("mcp_tools", {}), "Actual shared MCP metadata").get("tools")
    if not isinstance(metadata, list) or not metadata:
        raise ValueError("Actual current shared MCP metadata is missing")
    tools: dict[str, dict[str, object]] = {}
    for item in metadata:
        row = _queue_object(item, "Actual shared MCP tool metadata")
        name = row.get("name")
        if not isinstance(name, str) or name in tools:
            raise ValueError("Actual current MCP metadata has duplicate or invalid names")
        tools[name] = row
    from jsonschema import Draft202012Validator
    for index, step in enumerate(original_steps):
        kind = step.get("kind", "tool")
        bind_previous = step.get("bind_previous_revision", False)
        require(type(bind_previous) is bool, "bind_previous_revision must be a literal boolean")
        require(not bind_previous or kind == "tool" and index > 0,
                "Previous-row revision requires a preceding step in the same tool plan")
        require(kind in ("tool", "advance_day", "finish_hold"), "Unqualified shared queue step kind: " + str(kind))
        if kind == "tool":
            name, arguments = step.get("tool"), step.get("args", {})
            if not isinstance(name, str) or name not in tools or not isinstance(arguments, dict):
                raise ValueError("Tool/argument object is absent from actual MCP metadata")
            validate_normal_exit_native_capability(name, current, frozen)
            require("$" not in json.dumps(arguments), "Queue requires explicit arguments; symbolic host references need a reviewed extension")
            schema = _queue_object(copy.deepcopy(tools[name].get("inputSchema")), "Actual input schema for " + name)
            properties = _queue_object(schema.get("properties", {}), "Actual input schema properties for " + name)
            fresh = step.get("fresh_revision", True)
            require(type(fresh) is bool, "fresh_revision must be a literal boolean")
            if bind_previous:
                require(name in {"ck3_query_ingame_decision_item_v1"} and fresh is False and
                        "expected_revision" in properties and
                        "expected_revision" not in arguments,
                        "Previous-row revision requires a declared readonly query, false fresh flag and no explicit revision")
            # The existing host obtains the exact revision just before dispatch.
            # Leave its omitted revision field out of schema.required; validate
            # every supplied field without manufacturing a placeholder value.
            if (fresh or bind_previous) and "expected_revision" in properties and "expected_revision" not in arguments:
                required = schema.get("required", [])
                if not isinstance(required, list) or not all(isinstance(key, str) for key in required):
                    raise ValueError("Actual input schema required field array is invalid: " + name)
                schema["required"] = [key for key in required if key != "expected_revision"]
            Draft202012Validator.check_schema(schema)
            Draft202012Validator(schema).validate(arguments)
        elif kind == "advance_day":
            require(type(step.get("days")) is int and step["days"] == 1,
                    "One original natural day per shared queued step required")
        else:
            require(len(original_steps) == 1, "Native-zero finish_hold must be the only submitted step")
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

def terminal_cleanup_evidence(keeper: Path, frozen: Mapping[str, object],
        report: dict[str, object], steps: list[dict[str, object]]) -> dict[str, object]:
    """Finish an ended game's failed host after its keeper has already exited."""
    import psutil
    require(len(steps) == 1 and steps[0].get("kind") == "finish_hold"
            and steps[0].get("failure_shutdown") is True,
            "Terminal cleanup accepts only one failure finish_hold; no game commands")
    proof = native_zero_proof(frozen, report, failure_shutdown=True)
    require(proof is not None, "Original failed host has no actual native-zero cleanup proof")
    keeper_report = _queue_object(read_json(keeper / "report.json"), "Ended keeper")
    require(keeper_report.get("task_id") == frozen.get("screen_task")
            and keeper_report.get("thread_exited") is True,
            "Terminal cleanup requires the original keeper's actual ended thread")
    require(not any((process.info.get("name") or "").lower() == "ck3.exe"
                    for process in psutil.process_iter(["name"])),
            "Terminal cleanup cannot run while a CK3 process exists")
    return {"scope": "ended-game-failed-host-only", "native_failure_cleanup": proof,
            "keeper_report": pin(keeper / "report.json"), "business_pass": False,
            "normal_close_qualified": False}


# A stopped keeper is never renewed. This review only permits the existing
# normal-exit SDK on the original held host, until its original deadline.
def _cleanup_pairs_v1(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        require(key not in result, "Duplicate cleanup review JSON field")
        result[key] = value
    return result


def _cleanup_original_v1(reference: object, expected: Path | None = None) -> dict[str, object]:
    row = _queue_object(reference, "Cleanup original pin")
    require(set(row) == {"path", "bytes", "sha256"}, "Exact cleanup original pin required")
    path = Path(text_field(row, "path")).resolve(strict=True)
    require(expected is None or path == expected.resolve(), "Cleanup original crossed its allocated path")
    raw = _exit_sdk_bytes_v1(path, row)
    return _queue_object(json.loads(raw, object_pairs_hook=_cleanup_pairs_v1), "Cleanup original")


def _cleanup_qualification_v1(value: object) -> dict[str, object]:
    qualification = _cleanup_original_v1(value)
    require(set(qualification) == {"schema", "queue_source", "test_source", "original_wait"}
            and qualification["schema"] == "ck3-stopped-keeper-exit-software-v1",
            "Exact cleanup software qualification required")
    source = _queue_object(qualification["queue_source"], "Qualified cleanup source")
    _exit_sdk_bytes_v1(Path(__file__).resolve(), source)
    test = _queue_object(qualification["test_source"], "Qualified cleanup tests")
    _exit_sdk_bytes_v1(Path(text_field(test, "path")), test)
    waited = _cleanup_original_v1(qualification["original_wait"])
    require(waited.get("actual_original_popen_wait") is True and type(waited.get("returncode")) is int
            and waited["returncode"] == 0, "Cleanup tests need their actual original wait zero")
    argv = strings_field(waited, "argv")
    require(any(Path(item).resolve() == Path(text_field(test, "path")).resolve() for item in argv)
            and argv.count("--queue") == 1 and argv.index("--queue") + 1 < len(argv)
            and Path(argv[argv.index("--queue") + 1]).resolve() == Path(__file__).resolve(),
            "Cleanup qualification did not execute these exact candidate tests/source")
    log_ref = _queue_object(waited.get("stderr"), "Cleanup test original stderr")
    log = _exit_sdk_bytes_v1(Path(text_field(log_ref, "path")), log_ref).decode("utf-8", errors="strict")
    require(re.search(r"(?m)^Ran [1-9][0-9]* tests? in ", log) is not None
            and re.search(r"(?m)^OK\s*$", log) is not None
            and not re.search(r"(?im)(skipped[= ]|^FAILED|^ERROR|^FAIL:)", log),
            "Cleanup qualification lacks its complete passing non-skipped unittest originals")
    return qualification


def stopped_keeper_exit_evidence_v1(live: Path, keeper: Path, frozen: Mapping[str, object],
        context: Mapping[str, object], report: dict[str, object], steps: object,
        review_path: Path, intent_name: str) -> dict[str, object]:
    """Read an explicit source handoff; it never grants or resurrects a lease."""
    review = _cleanup_original_v1(pin(review_path))
    require(set(review) == {"schema", "reviewer", "run_id", "pid", "birth_filetime", "original_hold_deadline",
            "originals", "software_qualification"} and
            review["schema"] == "ck3-stopped-keeper-normal-exit-review-v1", "Exact cleanup review required")
    require(review.get("run_id") == frozen.get("run_id") == live.name,
            "Cleanup review crossed the original run")
    reviewer = text_field(review, "reviewer")
    pid = _native_positive_integer(review.get("pid"), "Cleanup retained PID")
    birth = review.get("birth_filetime")
    require(type(birth) is str and re.fullmatch(r"[1-9][0-9]{0,19}", birth) is not None
            and int(birth) < 2**64, "Cleanup birth requires canonical uint64 text")
    deadline = review.get("original_hold_deadline")
    require(type(deadline) in (int, float) and 0 < deadline < float("inf")
            and deadline == report.get("hold_until_utc_estimated") and time.time() < deadline,
            "Cleanup cannot extend or replace the original hold deadline")
    originals = _queue_object(review.get("originals"), "Cleanup originals")
    required = {"frozen_argv": live / "frozen-argv.json", "ready_context": live / "ready-context.json",
        "manual_quit": live / "case-output/manual-quit-awaiting.json",
        "normal_quit": live / "case-output/normal-quit-awaiting.json",
        "automation_failure": live / "case-output/normal-quit-typed-automation-failure-preserved.json",
        "keeper_report": keeper / "report.json", "keeper_stop": keeper / "ROOT_STOP_REQUIRED.json"}
    require(set(originals) == set(required), "Cleanup originals are incomplete or contain unrecognized proofs")
    rows = {key: _cleanup_original_v1(originals[key], path) for key, path in required.items()}
    manual, normal, ended, stop = (rows[key] for key in ("manual_quit", "normal_quit", "keeper_report", "keeper_stop"))
    require(ended.get("task_id") == stop.get("task_id") == frozen.get("screen_task")
            and ended.get("thread_exited") is True and type(ended.get("entry_error")) is str
            and bool(ended["entry_error"]) and stop.get("reason") == "Keeper failed; stop live actions",
            "Cleanup requires the original failed and stopped keeper; no lease revival")
    require(manual.get("status") == "MANUAL_QUIT_AWAITING_ORIGINAL_DEADLINE"
            and normal.get("original_typed_exit_already_observed") is False
            and normal.get("screen_task") == frozen.get("screen_task")
            and Path(text_field(normal, "keeper_root")).resolve() == keeper,
            "Cleanup requires the original manual/normal Quit wait")
    for row in (manual, normal):
        require(row.get("run_id") == live.name and row.get("reviewer") == reviewer
                and type(row.get("pid")) is int and row["pid"] == pid
                and row.get("original_hold_deadline") == deadline
                and type(row.get("create_time")) in (int, float), "Cleanup original retained identity/deadline differs")
    require(manual["create_time"] == normal["create_time"], "Cleanup retained creation times differ")
    failure = rows["automation_failure"]
    require(failure.get("automation_replayed") is False and failure.get("business_pass") is False
            and failure.get("original_hold_deadline") == deadline
            and failure.get("error") == "ValueError: Original screen keeper no longer owns this held scene",
            "Cleanup is limited to the preserved pre-dispatch stopped-keeper failure")
    _cleanup_qualification_v1(review["software_qualification"])
    typed = _normal_exit_plan_v1(steps, frozen)
    finishing = (isinstance(steps, list) and len(steps) == 1 and isinstance(steps[0], dict)
                 and steps[0].get("kind") == "finish_hold")
    require(typed or finishing, "Stopped keeper permits normal-exit cleanup only; no business/advance/SAVE")
    require(isinstance(steps, list) and all(_queue_object(step, "Cleanup step").get("id", "").startswith(
            intent_name + "-") for step in steps), "Cleanup steps must belong to the new once-only exit intent")
    if finishing:
        require(native_zero_proof(frozen, report, failure_shutdown=steps[0].get("failure_shutdown") is True) is not None,
                "Cleanup finish requires the original host's actual native-zero proof")
    if typed and steps[0].get("tool") == "ck3_request_normal_exit_v1" and steps[0].get("args", {}).get("action") == "confirm_desktop":
        for path in (live / "controls").glob("*.json"):
            require(path.stat().st_size <= 1024 * 1024, "Original published plan exceeds cleanup bound")
            published = _queue_object(json.loads(path.read_bytes(), object_pairs_hook=_cleanup_pairs_v1), "Published original plan")
            for old in published.get("steps", []):
                previous = _queue_object(old, "Published original step")
                require(not (previous.get("tool") == "ck3_request_normal_exit_v1"
                    and _queue_object(previous.get("args", {}), "Published arguments").get("action") == "confirm_desktop"),
                    "Original exit confirmation was already published or UNKNOWN; never replay")
    return {"scope": "original-held-host-normal-exit-only", "review": pin(review_path),
        "pid": pid, "birth_filetime": birth, "create_time": manual["create_time"],
        "original_hold_deadline": deadline, "lease_renewed": False, "failure_preserved": True,
        "business_pass": False, "normal_close_qualified": False}


def _cleanup_no_previous_dispatch_v1(live: Path, report: Mapping[str, object]) -> None:
    """Do not start a second quit over any original published or UNKNOWN action."""
    require(report.get("steps") == [], "Cleanup entry requires zero original dispatched steps")
    require(not any((live / "controls").glob("*.json")), "Original published controls must never be replayed")
    ledger = live / "control-once-ledger"
    require(not ledger.exists() or not any(ledger.iterdir()),
            "Original queued or UNKNOWN claims prevent a second exit intent")


def _cleanup_no_sdk_claim_v1(state: Path) -> None:
    # Both Core and legacy normal-exit producers use this permanent once claim.
    # Any original claim is terminal/UNKNOWN evidence, never permission to retry.
    directory = state / "native-session/normal-exit-map-requests"
    require(not any(directory.glob("*.claim.json")),
            "Original SDK exit confirmation claim exists; never replay")


@runtime_checkable
class _CleanupObserverV1(Protocol):
    def verify_before_dispatch(self) -> dict[str, object]: ...
    def observe(self, timeout_ms: int = 5000) -> dict[str, object]: ...
    def close(self) -> None: ...


@runtime_checkable
class _CleanupObserverModuleV1(Protocol):
    def Win32ProcessApi(self) -> object: ...
    def RetainedProcessObserver(self, api: object, pid: int, birth: int) -> _CleanupObserverV1: ...


@contextmanager
def _cleanup_retained_observer_v1(frozen: Mapping[str, object], pid: int, birth: int) -> Iterator[_CleanupObserverV1]:
    """Load the original read-only SDK observer; never a new native/OS provider."""
    import importlib.util
    import secrets
    import sys
    source = Path(text_field(frozen, "source_root")).resolve()
    manifest = _queue_object(frozen["runtime_manifest"], "Frozen runtime")
    index_path = Path(text_field(manifest, "path")).with_name("source-index.json").resolve()
    files = _queue_object(frozen["files"], "Frozen files")
    index = _cleanup_original_v1({**_queue_object(files[str(index_path)], "Original SDK index pin"), "path":str(index_path)})
    relative = "ck3_autonomous_player/src/xar_autoplayer/bridge/normal_exit_process_observer_v1.py"
    path = source / relative
    raw = _exit_sdk_bytes_v1(path, _queue_object(index["files"], "SDK indexed files")[relative])
    name = "_cleanup_original_observer_" + secrets.token_hex(16)
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, "Original observer loader unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    observer = None
    try:
        exec(compile(raw, str(path), "exec"), module.__dict__)
        require(isinstance(module, _CleanupObserverModuleV1), "Original observer API differs")
        observer = module.RetainedProcessObserver(module.Win32ProcessApi(), pid, birth)
        observer.verify_before_dispatch()
        yield observer
    finally:
        if observer is not None:
            observer.close()
        sys.modules.pop(name, None)


def run_stopped_keeper_normal_exit_v1(live: Path, review_path: Path, intent_name: str) -> dict[str, object]:
    """Use the old public coordinator/SDK and original queue namespace, once."""
    from ck3_mod_acceptance import normal_exit_static_binding_v1
    from ck3_mod_acceptance_client import _typed_quit_codec, _typed_quit_run_v1, typed_normal_quit_evidence_v1
    live = live.resolve()
    require(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,70}", intent_name) is not None,
            "New bounded cleanup intent name required")
    frozen, context = frozen_run(live, all_pins=False)
    keeper = Path(text_field(context, "keeper_root")).resolve()
    initial = stable_report(live / "native-report.json")
    probe = [{"id": intent_name + "-001", "tool": "ck3_query_normal_exit_context_v1", "args": {}}]
    admitted = stopped_keeper_exit_evidence_v1(live, keeper, frozen, context, initial, probe, review_path, intent_name)
    _cleanup_no_previous_dispatch_v1(live, initial)
    state = Path(text_field(frozen, "state_dir")).resolve()
    _cleanup_no_sdk_claim_v1(state)
    runtime_ref = _queue_object(frozen["runtime_manifest"], "Frozen runtime reference")
    binding = normal_exit_static_binding_v1(context.get("normal_exit_managed_profile"), state_dir=state,
        run_dir=live, runtime_manifest=runtime_ref)
    profile = _queue_object(binding["profile"], "Original exit profile")
    argv = strings_field(frozen, "argv")
    require(argv.count("--normal-exit-managed-profile") == argv.count("--normal-exit-managed-profile-sha256") == 1
            and argv[argv.index("--normal-exit-managed-profile") + 1] == profile["path"]
            and argv[argv.index("--normal-exit-managed-profile-sha256") + 1] == profile["sha256"],
            "Cleanup profile crossed original frozen Host argv")
    index = Path(text_field(runtime_ref, "path")).with_name("source-index.json").resolve()
    files = _queue_object(frozen["files"], "Frozen files")
    codec, index_pin, sdk_pins = _typed_quit_codec(Path(text_field(frozen, "source_root")), index,
        {**_queue_object(files[str(index)], "Original SDK source index pin"), "path":str(index)})
    intent = live / "case-output" / (intent_name + "-once.json")
    deadline = admitted["original_hold_deadline"]
    remaining = lambda: deadline - time.time()
    sequence = 0
    paused_binding = None
    with _cleanup_retained_observer_v1(frozen, admitted["pid"], int(admitted["birth_filetime"])) as observer:
        # Exclusive intent precedes every queue publication. Never overwrite it,
        # including after a timeout, rejected query, exception or UNKNOWN confirm.
        write_new(intent, {"schema":"ck3-stopped-keeper-normal-exit-once-v1", **admitted,
            "profile":profile, "source_index":index_pin, "sdk_sources":sdk_pins,
            "confirm_maximum":1, "unknown_replayed":False})
        def invoke(tool: str, arguments: dict[str, object]) -> dict[str, object]:
            nonlocal sequence, paused_binding
            require(remaining() > 0, "Original cleanup deadline expired; never replay")
            if tool != "ck3_observe_normal_exit_v1":
                observer.verify_before_dispatch()
            sequence += 1
            name = intent_name + "-" + str(sequence).zfill(3)
            step = {"id":name, "tool":tool, "args":arguments,
                    "fresh_revision":"expected_revision" not in arguments}
            plan = live / "case-output" / (name + ".plan.json")
            write_new(plan, {"steps":[step]})
            enqueue(live, plan, name + ".json", stopped_keeper_exit_review=review_path,
                    stopped_keeper_exit_intent=intent_name)
            while remaining() > 0:
                report = stable_report(live / "native-report.json")
                rows = [row for row in report.get("steps", []) if isinstance(row, dict) and row.get("id") == name]
                require(len(rows) <= 1, "Duplicate actual cleanup step result")
                if rows and rows[0].get("finished_at"):
                    row = rows[0]
                    require(not row.get("error") and row.get("plan") == step,
                            "Original cleanup step failed or crossed its exact plan; never replay")
                    if tool != "ck3_observe_normal_exit_v1" and arguments.get("action") != "confirm_desktop":
                        frame = _queue_object(row.get("after_snapshot"), "Cleanup paused actual frame")
                        require(frame.get("paused") is True and type(frame.get("date_raw")) is int,
                                "Cleanup query requires its actual paused frame")
                        current = (frame["date_raw"], frame.get("native_revision"), frame.get("played_character"))
                        require(paused_binding is None or current == paused_binding,
                                "Cleanup crossed original paused date/revision/actor")
                        paused_binding = current
                    return _queue_object(row.get("result"), "Actual SDK normal-exit result")
                time.sleep(.1)
            raise TimeoutError("Original cleanup publication outcome unknown; never replay")
        _typed_quit_run_v1(codec, invoke, remaining, pid=admitted["pid"], birth=int(admitted["birth_filetime"]))
        report = stable_report(live / "native-report.json")
        retained = {"pid":admitted["pid"], "create_time":admitted["create_time"],
            "creation_filetime_100ns":admitted["birth_filetime"], "retained_synchronize_query_handle_acquired":True}
        evidence = typed_normal_quit_evidence_v1(report, live=live, state=state, retained_value=retained,
            context_value=context, frozen_value=frozen, source_root=Path(text_field(frozen, "source_root")),
            source_index=index, source_index_reference=index_pin, allow_preserved_failure=True)
        require(evidence is not None, "Cleanup lacks its actual SDK fact/claim/observer close evidence")
        observed = observer.observe(0)
        require(observed.get("process_identity_verified") is True and observed.get("process_exit_observed") is True
                and type(observed.get("exit_code")) is int and observed["exit_code"] == 0,
                "Cleanup retained original handle has no actual OS exit zero")
        write_new(live / "case-output" / (intent_name + "-typed-evidence.json"), evidence)
        # The original Client may finish concurrently. Only an actual native-zero
        # report permits this existing finish step, never the submitted exit ACK.
        while remaining() > 0:
            report = stable_report(live / "native-report.json")
            if report.get("hold_finished_by_control_plan") or report.get("finished_at"):
                break
            failure = bool(report.get("error"))
            if native_zero_proof(frozen, report, failure_shutdown=failure) is not None:
                name = intent_name + "-finish"
                plan = live / "case-output" / (name + ".plan.json")
                write_new(plan, {"steps":[{"id":name, "kind":"finish_hold", "failure_shutdown":failure}]})
                enqueue(live, plan, name + ".json", stopped_keeper_exit_review=review_path,
                        stopped_keeper_exit_intent=intent_name)
                break
            time.sleep(.1)
        result = {"schema":"ck3-stopped-keeper-normal-exit-result-v1", "at_utc":utc(),
            **admitted, "typed_evidence":evidence, "independent_retained_observation":observed,
            "original_keeper_renewed":False, "business_pass":False}
        write_new(live / "case-output" / (intent_name + "-result.json"), result)
        return result


def enqueue(live: Path | str, plan: Path | str, name: str, *, deadline: float | None = None,
        startup_recovery_error: str | None = None, startup_recovery_reviewer: str | None = None,
        terminal_cleanup: bool = False, stopped_keeper_exit_review: Path | None = None,
        stopped_keeper_exit_intent: str | None = None) -> dict[str, object]:
    enqueue_deadline(deadline)
    lease_options = {"deadline": deadline} if deadline is not None else {}
    live, plan = Path(live).resolve(), Path(plan).resolve()
    require(Path(name).name == name and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,159}\.json", name),
            "New .json control basename required")
    frozen, context = frozen_run(live, all_pins=False)
    keeper = Path(text_field(context, "keeper_root")).resolve()
    argv = strings_field(frozen, "argv")
    require(type(terminal_cleanup) is bool, "terminal_cleanup must be a literal boolean")
    cleanup_exit = stopped_keeper_exit_review is not None
    require(not cleanup_exit or (not terminal_cleanup and startup_recovery_error is None and
            startup_recovery_reviewer is None and isinstance(stopped_keeper_exit_intent, str)),
            "Cleanup-only review cannot combine with another recovery or lease scope")
    if not terminal_cleanup and not cleanup_exit:
        live_lease(keeper, frozen, **lease_options)
    enqueue_deadline(deadline)
    report = stable_report(live / "native-report.json")
    require(Path(report["state_dir"]).resolve() == Path(text_field(frozen, "state_dir")).resolve() and
            Path(report["agent_source_root"]).resolve() == Path(text_field(frozen, "source_root")).resolve(),
            "Actual host report crossed allocated state/shared source")
    require(report.get("pipe") == argv[argv.index("--bridge-pipe") + 1],
            "Actual host report crossed allocated native pipe")
    require(report.get("phase") == "hold" and not report.get("finished_at") and
            not report.get("hold_finished_by_control_plan"), "Original shared host is no longer held")
    raw = plan.read_bytes()
    require(len(raw) <= 1024 * 1024, "Original control plan exceeds 1 MiB bound")
    value = json.loads(raw.decode("utf-8-sig"))
    require(isinstance(value, dict) and set(value) == {"steps"}, "Original {steps: [...]} plan object required")
    steps = value["steps"]
    ids = validate_steps(steps, report, frozen)
    finishing = len(steps) == 1 and steps[0].get("kind") == "finish_hold"
    typed_exit = _normal_exit_plan_v1(steps, frozen)
    cleanup = None
    if cleanup_exit:
        cleanup = stopped_keeper_exit_evidence_v1(live, keeper, frozen, context, report, steps,
            stopped_keeper_exit_review, stopped_keeper_exit_intent)
        intent_path = live / "case-output" / (stopped_keeper_exit_intent + "-once.json")
        intent = _cleanup_original_v1(pin(intent_path))
        require(intent.get("schema") == "ck3-stopped-keeper-normal-exit-once-v1" and
                intent.get("review") == cleanup["review"] and intent.get("pid") == cleanup["pid"] and
                intent.get("birth_filetime") == cleanup["birth_filetime"],
                "Cleanup queue requires its original once-only reviewed intent")
    terminal = terminal_cleanup_evidence(keeper, frozen, report, steps) if terminal_cleanup else None
    hold_deadline = report.get("hold_until_utc_estimated")
    require(type(hold_deadline) in (int, float) and hold_deadline - time.time() > (0 if finishing or typed_exit else 90),
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
        if report.get("error") and recovery is None:
            _require_failed_host_exit_plan_v1(steps, frozen)
        require(not report.get("cleanup_ok"), "Original host failed or completed cleanup")
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
        if terminal_cleanup:
            terminal = terminal_cleanup_evidence(keeper, frozen, stable_report(live / "native-report.json"), steps)
            latest = None
        elif cleanup_exit:
            first_cleanup = cleanup
            cleanup = stopped_keeper_exit_evidence_v1(live, keeper, frozen, context,
                stable_report(live / "native-report.json"), steps, stopped_keeper_exit_review, stopped_keeper_exit_intent)
            require(cleanup == first_cleanup, "Reviewed cleanup admission changed after claim; never replay")
            require(_cleanup_original_v1(pin(intent_path)) == intent, "Original cleanup intent changed")
            latest = None
        else:
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
              "lease": latest["lease"] if latest is not None else None, "claims": claims, "business_pass": False}
    if cleanup is not None:
        result["stopped_keeper_exit"] = cleanup
    if terminal is not None:
        result["terminal_cleanup"] = terminal
    if recovery is not None:
        result["startup_failure_recovery"] = recovery
    write_new(live / "control-once-ledger" / ("receipt-" + claims["sha256"] + ".json"), result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", type=Path, required=True)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--name")
    parser.add_argument("--stopped-keeper-normal-exit-review", type=Path,
                        help="Explicit qualified cleanup-only source handoff; never renews the failed keeper")
    parser.add_argument("--exit-intent-name", help="New durable once-only exit intent, never a replay")
    parser.add_argument("--timeout-seconds", type=float, help="Bound this original submission; no retries")
    parser.add_argument("--startup-recovery-error", help="Explicit original failed-startup error; default preserves ordinary guard")
    parser.add_argument("--startup-recovery-reviewer", help="Actual retained-session operator")
    parser.add_argument("--terminal-cleanup", action="store_true",
                        help="Only failure finish_hold after actual native zero cleanup and an ended keeper")
    args = parser.parse_args(argv)
    try:
        if args.stopped_keeper_normal_exit_review is not None:
            require(args.plan is None and args.name is None and args.timeout_seconds is None and
                    args.startup_recovery_error is None and args.startup_recovery_reviewer is None and
                    not args.terminal_cleanup and isinstance(args.exit_intent_name, str),
                    "Stopped keeper entry permits only original-deadline typed normal exit")
            print(json.dumps(run_stopped_keeper_normal_exit_v1(args.live,
                args.stopped_keeper_normal_exit_review, args.exit_intent_name)), flush=True)
            return 0
        require(args.plan is not None and args.name is not None and args.exit_intent_name is None,
                "Ordinary queue requires its explicit plan and name")
        if args.timeout_seconds is not None:
            require(0 < args.timeout_seconds < float("inf"), "Finite positive queue timeout required")
        deadline = None if args.timeout_seconds is None else time.monotonic() + args.timeout_seconds
        print(json.dumps(enqueue(args.live, args.plan, args.name, deadline=deadline,
            startup_recovery_error=args.startup_recovery_error,
            startup_recovery_reviewer=args.startup_recovery_reviewer,
            terminal_cleanup=args.terminal_cleanup)), flush=True)
        return 0
    except Exception as error:
        print(json.dumps({"status": "BLOCKED_NEVER_REPLAY", "error": repr(error), "business_pass": False}), flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
