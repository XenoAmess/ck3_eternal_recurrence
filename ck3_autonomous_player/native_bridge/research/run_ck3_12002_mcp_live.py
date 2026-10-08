#!/usr/bin/env python3
"""Official MCP client harness for one coordinator-owned CK3 migration session.

Normal mode starts CK3 through clean-source native_session. --sdk-smoke-test
uses a Python MCP fixture server only. The harness never attaches to a game.
"""

from __future__ import annotations

import argparse
import asyncio
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
import re
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
        operation = "open-append"
        try:
            with self.lock, self.path.open("a", encoding="utf-8") as stream:
                operation = "append-json-line"
                stream.write(json.dumps({
                    "at": now(), "direction": direction, "message": serialized(value),
                }, ensure_ascii=False) + "\n")
                operation = "close-append-stream"
        except OSError as error:
            annotate_write_error(error, self.path, operation, {"journal_direction": direction})
            raise


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


class CampaignSpeedPreSubmissionRevisionError(RuntimeError):
    """An exact server-side rejection before the speed request was submitted."""

    def __init__(self, receipt: dict[str, object]) -> None:
        super().__init__(receipt["original_error"])
        self.receipt = receipt


def campaign_speed_presubmission_receipt(payload: object, name: str,
        arguments: dict[str, object]) -> dict[str, object] | None:
    schema = "ck3.qol.speed-presubmission-revision.v1"
    if not isinstance(payload, dict) or payload.get("schema") != schema:
        return None
    fields = {"schema", "status", "accepted", "submitted", "step", "expected_revision",
              "current_revision", "request_sequence_before", "request_sequence_after",
              "original_error_type", "original_error"}
    message = re.fullmatch(r"native gameplay revision mismatch: expected ([0-9]+), current ([0-9]+)",
                           str(payload.get("original_error", "")))
    if (set(payload) != fields or name != "ck3_execute_step"
            or arguments.get("step") != "set-speed-1" or payload.get("step") != "set-speed-1"
            or payload.get("status") != "PRE_SUBMISSION_REVISION_MISMATCH"
            or payload.get("accepted") is not False or payload.get("submitted") is not False
            or payload.get("original_error_type") != "PreSubmissionRevisionMismatchError"
            or type(payload.get("original_error")) is not str
            or type(arguments.get("expected_revision")) is not int
            or any(type(payload.get(key)) is not int for key in
                   ("expected_revision", "current_revision", "request_sequence_before", "request_sequence_after"))
            or not 1 <= payload["expected_revision"] < payload["current_revision"] <= 2**64 - 1
            or payload["expected_revision"] != arguments["expected_revision"]
            or not 0 <= payload["request_sequence_before"] == payload["request_sequence_after"] <= 2**64 - 1
            or message is None or tuple(map(int, message.groups())) !=
               (payload["expected_revision"], payload["current_revision"])):
        raise RuntimeError("malformed speed pre-submission rejection; no retry authorized")
    return copy.deepcopy(payload)


def install_campaign_speed_presubmission_transmission(driver: object, mismatch_type: type) -> None:
    """Keep the driver's recorded failure and transmit only this proven non-submission."""
    original = driver.execute_step

    def execute_step(step: str, *, expected_revision: int | None = None) -> dict[str, object]:
        sequence_before = getattr(driver, "_request_sequence", None)
        try:
            return original(step, expected_revision=expected_revision)
        except mismatch_type as error:
            diagnostics = driver.state.diagnostics()
            hello = diagnostics.get("hello") if isinstance(diagnostics, dict) else None
            if (not isinstance(hello, dict) or diagnostics.get("connected") is not True
                    or hello.get("expected_ck3_version") != "1.20.0.4"
                    or hello.get("expected_ck3_sha256") != "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518"
                    or hello.get("game_adapter_id") != "ck3-1.20.0.4-msvc-x64"
                    or hello.get("ck3_build_match") is not True):
                raise
            sequence_after = getattr(driver, "_request_sequence", None)
            message = re.fullmatch(r"native gameplay revision mismatch: expected ([0-9]+), current ([0-9]+)", str(error))
            if (type(error) is not mismatch_type or driver.episode_projection != "native_campaign"
                    or step != "set-speed-1" or type(expected_revision) is not int
                    or type(sequence_before) is not int or type(sequence_after) is not int
                    or not 0 <= sequence_before == sequence_after <= 2**64 - 1
                    or message is None or int(message[1]) != expected_revision
                    or not 1 <= expected_revision < int(message[2]) <= 2**64 - 1):
                raise
            payload = {"schema": "ck3.qol.speed-presubmission-revision.v1",
                "status": "PRE_SUBMISSION_REVISION_MISMATCH", "accepted": False, "submitted": False,
                "step": step, "expected_revision": expected_revision, "current_revision": int(message[2]),
                "request_sequence_before": sequence_before, "request_sequence_after": sequence_after,
                "original_error_type": type(error).__name__, "original_error": str(error)}
            campaign_speed_presubmission_receipt(payload, "ck3_execute_step",
                {"step": step, "expected_revision": expected_revision})
            return payload

    driver.execute_step = execute_step


def frontend_native_build_pair(game_version: object, executable_sha256: object):
    """Preserve frontend .3/.4 domains using the existing single exact-build registry."""
    from xar_autoplayer.bridge.version_identity import CK3_12003, CK3_12004, require_exact_native_build
    build = require_exact_native_build(game_version, executable_sha256)
    if build not in (CK3_12003, CK3_12004):
        raise ValueError("frontend native build is outside the existing .3/.4 domains")
    return build


def allocated_managed_campaign_run_binding(args: argparse.Namespace) -> dict[str, object]:
    """Read the existing allocator identity for this host/state/pipe, without an episode seed."""
    state = args.state_dir.expanduser().resolve()
    if not isinstance(args.output, Path):
        raise ValueError("managed camera requires this allocated run\'s actual output path")
    output = args.output.expanduser().resolve()
    run_root = output.parent
    frozen = run_root / "frozen-argv.json"
    if frozen.is_symlink() or not frozen.is_file():
        raise ValueError("saved camera requires this allocated run's ordinary frozen-argv.json")
    raw = frozen.read_bytes()
    record = json.loads(raw)
    argv = record.get("argv") if isinstance(record, dict) else None
    if (not isinstance(record, dict) or not isinstance(record.get("run_id"), str)
            or not record["run_id"] or record["run_id"] != run_root.name
            or not isinstance(record.get("state_dir"), str) or not record["state_dir"]
            or Path(record["state_dir"]).resolve() != state
            or not isinstance(argv, list) or len(argv) < 5 or any(not isinstance(x, str) for x in argv)
            or Path(argv[4]).resolve() != Path(__file__).resolve()):
        raise ValueError("saved camera allocated run/host identity differs")
    def option(flag: str) -> str:
        if argv.count(flag) != 1 or argv.index(flag) + 1 >= len(argv):
            raise ValueError("saved camera allocated argv lacks exact " + flag)
        return argv[argv.index(flag) + 1]
    if (Path(option("--state-dir")).resolve() != state or option("--bridge-pipe") != args.bridge_pipe
            or Path(option("--agent-source-root")).resolve() != args.agent_source_root.expanduser().resolve()
            or Path(option("--output")).resolve() != output):
        raise ValueError("saved camera allocated state/pipe/source/output identity differs")
    if args.saved_campaign_server:
        if argv.count("--saved-campaign-save") != 1:
            raise ValueError("managed camera saved mode differs from its allocated argv")
    elif args.frontend_fixture_start_policy is not None:
        if (argv.count("--frontend-fixture-start-policy") != 1 or argv.count("--frontend-robert-bootstrap") != 1
                or argv.count("--fixture-profile") != 1
                or file_sha(Path(option("--frontend-fixture-start-policy")).resolve()) != file_sha(args.frontend_fixture_start_policy.resolve())):
            raise ValueError("managed camera fixture policy differs from its allocated argv")
    else:
        raise ValueError("managed camera identity requires an existing campaign startup mode")
    return {"run_id": record["run_id"], "state_dir": str(state), "bridge_pipe": args.bridge_pipe,
        "host_path": str(Path(__file__).resolve()), "frozen_argv_sha256": hashlib.sha256(raw).hexdigest()}


def finished_native_exit_zero_proof(report: dict[str, object], managed_done: bool,
                                    episode: dict[str, object] | None = None) -> dict[str, object] | None:
    """Current managed-session evidence only; missing proof never admits a dead snapshot."""
    if managed_done is not True or report.get("fixture_only") is not False or "error" not in report or report["error"] is not None:
        return None
    session = report.get("session")
    if not isinstance(session, dict) or "error" not in session or session["error"] is not None:
        return None
    native = session.get("report")
    if not isinstance(native, dict) or native.get("kind") != "ck3_native_headless_session" or native.get("mode") != "native-headless":
        return None
    if type(native.get("format_version")) is not int or native["format_version"] != 1:
        return None
    if native.get("ok") is not True or "error" not in native or native["error"] is not None or native.get("exit_reason") != "process_exit":
        return None
    if type(native.get("process_exit_code")) is not int or native["process_exit_code"] != 0:
        return None
    pid = native.get("pid")
    pipe = report.get("pipe")
    if type(pid) is not int or pid <= 0 or not isinstance(pipe, str) or not pipe.startswith('\\\\.\\pipe\\') or len(pipe) <= 9 or native.get("pipe") != pipe:
        return None
    if episode is not None and (not isinstance(episode, dict) or type(episode.get("bridge_pid")) is not int or episode["bridge_pid"] != pid):
        return None
    try:
        started = datetime.fromisoformat(native["started_at"])
        finished = datetime.fromisoformat(native["finished_at"])
        if started.tzinfo is None or finished.tzinfo is None or finished < started:
            return None
    except (KeyError, TypeError, ValueError):
        return None
    shutdown = native.get("shutdown")
    if not isinstance(shutdown, dict) or shutdown.get("ok") is not True or shutdown.get("cleanup_proven") is not True or shutdown.get("tree_gone") is not True:
        return None
    if type(shutdown.get("ck3_pid")) is not int or shutdown["ck3_pid"] != pid:
        return None
    if type(shutdown.get("ck3_exit_code")) is not int or shutdown["ck3_exit_code"] != 0:
        return None
    if type(shutdown.get("job_active_processes_final")) is not int or shutdown["job_active_processes_final"] != 0:
        return None
    if shutdown.get("contract_errors") != [] or shutdown.get("watchdog_state_after") != "absent":
        return None
    if not isinstance(shutdown.get("nonce"), str) or re.fullmatch(r"[0-9a-f]{32}", shutdown["nonce"]) is None:
        return None
    if not isinstance(shutdown.get("ck3_creation_date"), str) or not shutdown["ck3_creation_date"]:
        return None
    absent = shutdown.get("control_files_absent")
    if not isinstance(absent, dict) or not absent or any(not isinstance(key, str) or value is not True for key, value in absent.items()):
        return None
    inventory = shutdown.get("final_ck3_inventory")
    if not isinstance(inventory, dict) or type(inventory.get("tasklist_returncode")) is not int or inventory["tasklist_returncode"] != 0:
        return None
    if any(inventory.get(key) != [] for key in ("tasklist_pids", "wmi_pids", "native_pids", "processes")):
        return None
    return {"status": "not_applicable", "reason": "finished_native_process_exit_zero_cleanup_proven",
            "alive_or_business_credit": False, "managed_session_done": True,
            "pid": pid, "pipe": native["pipe"], "started_at": native["started_at"],
            "finished_at": native["finished_at"], "exit_reason": "process_exit", "process_exit_code": 0,
            "shutdown": copy.deepcopy(shutdown)}


def paused_map_readiness_admitted(snapshot: dict[str, object], report: dict[str, object]) -> bool:
    """Admit qualified native campaign frames without inventing a one-life identity."""
    if snapshot.get("map_ready") is not True or snapshot.get("paused") is not True:
        return False
    policy_input = report.get("frontend_fixture_start_policy_input")
    if not isinstance(policy_input, dict) or policy_input.get("episode_projection") != "native_campaign":
        # Preserve the original default one-life guard exactly.
        return snapshot.get("episode_identity_pending") is False
    if not isinstance(policy_input.get("policy"), dict) or snapshot.get("episode_projection") != "native_campaign":
        return False
    state = report.get("frontend_fixture_business_context")
    if not isinstance(state, dict) or any(state.get(key) is not wanted for key, wanted in {
            "actual_current_actor_bound": True, "qualification_observed": True, "start_resubmitted": False}.items()):
        return False
    if (state.get("status") != "ACTUAL_FIXTURE_QUALIFIED_BUSINESS_CONTEXT_BOUND"
            or state.get("episode_projection") != "native_campaign"):
        return False
    binding = state.get("binding")
    if not isinstance(binding, dict) or any(type(binding.get(key)) is not int or binding[key] < 1
            for key in ("actor_character_id", "bridge_pid", "connection_generation")):
        return False
    played = snapshot.get("played_character")
    diagnostics = snapshot.get("diagnostics")
    if (not isinstance(played, dict) or played.get("alive") is not True or played.get("source") != "native"
            or played.get("character_id") != binding["actor_character_id"]
            or snapshot.get("date_raw") != binding.get("date_raw") or not isinstance(diagnostics, dict)):
        return False
    if any(diagnostics.get(key) != binding[key] for key in ("bridge_pid", "connection_generation")):
        return False
    hello = diagnostics.get("hello")
    if not isinstance(hello, dict):
        return False
    try:
        build = frontend_native_build_pair(hello.get("expected_ck3_version"), hello.get("expected_ck3_sha256"))
    except ValueError:
        return False
    if any(hello.get(key) != wanted for key, wanted in {
            "pid": binding["bridge_pid"], "connection_generation": binding["connection_generation"],
            "game_adapter_id": f"ck3-{build.game_version}-msvc-x64", "expected_ck3_version": build.game_version,
            "ck3_build_match": True}.items()):
        return False
    if str(hello.get("expected_ck3_sha256")).upper() != build.executable_sha256:
        return False
    return True


def validate_saved_campaign_options(args: argparse.Namespace) -> None:
    inputs = (args.saved_campaign_save_bytes, args.saved_campaign_save_sha256,
        args.saved_campaign_player_id, args.saved_campaign_date_raw, args.saved_campaign_product_inventory)
    if args.saved_campaign_server and not args.server:
        raise SystemExit("--saved-campaign-server is an internal child-server option")
    if args.saved_campaign_save is not None:
        if (any(item is None for item in inputs) or not args.fixture_profile or args.plan is None
                or args.server or args.sdk_smoke_test or args.sdk_error_smoke_test or args.fixture_server
                or args.frontend_robert_bootstrap or args.frontend_fixture_start_policy is not None
                or args.frontend_rules_plan is not None or args.frontend_rules_diagnostic
                or args.frontend_rules_diagnostic_new_game or args.frontend_diagnostic_only
                or args.allow_verified_direct_bookmarks or args.cold_start_checkpoint or args.turns
                or args.native_fixture_inbox or args.print_default_plan):
            raise SystemExit("saved campaign requires explicit product-only profile/input/tail plan and excludes cold fixture, New Game/Start, rules, SDK, checkpoint, fixture inbox and auto turns")
        saved_campaign_expected(args)
        for step in load_plan(args.plan):
            kind = step.get("kind", "tool")
            if kind == "wait_snapshot":
                continue
            if kind != "tool" or not isinstance(step.get("tool"), str) or not (
                    step["tool"].startswith("ck3_query_") or step["tool"] in {
                        "ck3_take_snapshot", "ck3_get_capabilities", "ck3_migration_pipe_diagnostics"}):
                raise SystemExit("saved campaign initial tail plan permits read-only observations only; normal GUI Save/Load/quit has separate same-live evidence")
    elif any(item is not None for item in inputs):
        raise SystemExit("saved-campaign input fields require --saved-campaign-save")


def saved_campaign_expected(args: argparse.Namespace) -> dict[str, object] | None:
    if args.saved_campaign_save is None:
        return None
    for name, maximum in (("saved_campaign_save_bytes", 2**63 - 1),
            ("saved_campaign_player_id", 2**31 - 1), ("saved_campaign_date_raw", 2**31 - 1)):
        value = getattr(args, name)
        if type(value) is not int or not 1 <= value <= maximum:
            raise ValueError(name + " must be a positive bounded integer")
    if not isinstance(args.saved_campaign_save_sha256, str) or re.fullmatch(
            r"[0-9a-fA-F]{64}", args.saved_campaign_save_sha256) is None:
        raise ValueError("saved campaign requires an exact SHA-256")
    return {"source_path": str(args.saved_campaign_save.expanduser().resolve()),
        "bytes": args.saved_campaign_save_bytes, "sha256": args.saved_campaign_save_sha256.lower(),
        "actor_character_id": args.saved_campaign_player_id, "date_raw": args.saved_campaign_date_raw}


def prepare_saved_campaign(args: argparse.Namespace, spec: object) -> dict[str, object]:
    expected = saved_campaign_expected(args)
    if expected is None:
        raise ValueError("saved campaign preparation requires its explicit input")
    source = Path(expected["source_path"])
    if source.suffix.casefold() != ".ck3" or not source.is_file() or source.is_symlink():
        raise ValueError("immutable saved campaign must be an ordinary .ck3 file")
    profile = spec.profile_dir.resolve()
    save_dir = profile / "save games"
    if source.is_relative_to(profile) or (save_dir.exists() and any(save_dir.iterdir())):
        raise ValueError("saved campaign requires a fresh profile with no existing saves")
    if (spec.state_dir / "runtime.json").exists() or (spec.state_dir / "native-session").exists():
        raise ValueError("saved campaign state has a prior managed launch or lifecycle queue")
    dlc = json.loads((profile / "dlc_load.json").read_text(encoding="utf-8-sig"))
    if not isinstance(dlc, dict) or not isinstance(dlc.get("enabled_mods"), list) or not dlc["enabled_mods"]:
        raise ValueError("saved campaign requires an explicitly prepared product-only profile")
    # An explicit product-only inventory is mandatory. The consumer must freeze
    # its formal release projection; a cold fixture registrar is never reused.
    inventory_path = args.saved_campaign_product_inventory.expanduser().resolve()
    inventory_bytes = inventory_path.read_bytes()
    inventory = json.loads(inventory_bytes)
    if (not isinstance(inventory, dict) or set(inventory) != {"schema", "profile_path", "enabled_mods", "product_files"}
            or inventory["schema"] != "ck3-saved-campaign-product-only-profile-v1"
            or Path(inventory["profile_path"]).resolve() != profile
            or inventory["enabled_mods"] != dlc["enabled_mods"]
            or not isinstance(inventory["product_files"], list) or not inventory["product_files"]):
        raise ValueError("saved campaign product-only inventory does not bind the prepared profile")
    seen = set()
    for row in inventory["product_files"]:
        if not isinstance(row, dict) or set(row) != {"path", "bytes", "sha256"}:
            raise ValueError("invalid saved campaign product file inventory row")
        path = Path(row["path"]).resolve()
        if (str(path) in seen or path.is_symlink() or not path.is_file()
                or type(row["bytes"]) is not int or not 0 <= row["bytes"] <= 2**63-1
                or not isinstance(row["sha256"], str) or re.fullmatch(r"[0-9a-fA-F]{64}", row["sha256"]) is None):
            raise ValueError("invalid or repeated saved campaign product file identity")
        seen.add(str(path))
        if path.stat().st_size != row["bytes"] or file_sha(path).lower() != row["sha256"].lower():
            raise ValueError("saved campaign product inventory file changed: " + str(path))
        if path.suffix.casefold() == ".txt" and "on_game_start_after_lobby" in path.read_text(encoding="utf-8-sig"):
            raise ValueError("saved campaign product-only profile contains a cold-start registrar: " + str(path))
    actual_files = set()
    for enabled in dlc["enabled_mods"]:
        if not isinstance(enabled, str) or not enabled:
            raise ValueError("saved campaign enabled_mods entries must be explicit descriptor paths")
        descriptor = (profile / enabled).resolve()
        if not descriptor.is_relative_to(profile) or not descriptor.is_file() or descriptor.is_symlink():
            raise ValueError("saved campaign descriptor must be an ordinary file in the fresh profile")
        paths = re.findall(r'(?m)^\s*path\s*=\s*"([^"\r\n]+)"\s*(?:#.*)?$', descriptor.read_text(encoding="utf-8-sig"))
        if len(paths) != 1:
            raise ValueError("saved campaign descriptor must resolve exactly one directory product projection")
        product = Path(paths[0]).resolve()
        if not product.is_dir() or product.is_symlink():
            raise ValueError("saved campaign product projection must be an ordinary frozen directory")
        actual_files.add(str(descriptor))
        for path in product.rglob("*"):
            if path.is_symlink():
                raise ValueError("saved campaign product projection contains a symbolic link")
            if path.is_file():
                actual_files.add(str(path.resolve()))
    if actual_files != seen:
        raise ValueError("saved campaign inventory is not the complete exact enabled product projection plus outer descriptors")
    save_dir.mkdir(parents=True, exist_ok=True)
    target = save_dir / "restored_campaign.ck3"
    digest = hashlib.sha256()
    total = 0
    with source.open("rb") as original, target.open("xb") as copied:
        while block := original.read(1024 * 1024):
            digest.update(block)
            total += len(block)
            copied.write(block)
    if total != expected["bytes"] or digest.hexdigest() != expected["sha256"]:
        raise ValueError("immutable saved campaign input bytes/SHA do not match; failed copy retained")
    if target.stat().st_size != total or file_sha(target).lower() != expected["sha256"]:
        raise ValueError("saved campaign destination readback differs from immutable input")
    return {**expected, "profile_path": str(profile), "copied_save_path": str(target),
        "load_save_name": target.stem, "product_inventory_path": str(inventory_path),
        "product_inventory_sha256": hashlib.sha256(inventory_bytes).hexdigest(),
        "status": "IMMUTABLE_SAVE_COPIED_TO_FRESH_PRODUCT_ONLY_PROFILE",
        "source_game_state_claimed": False, "product_acceptance_proven": False}


def saved_campaign_session(spec: object, config: object, args: argparse.Namespace,
        stop: threading.Event, *, output_stream: object, launch_record: dict[str, object]) -> dict[str, object]:
    import importlib
    from types import FunctionType
    module = importlib.import_module("xar_autoplayer.native_session")
    original_launch = module.launch
    launched = False

    def launch_saved_once(*launch_args: object, **launch_kwargs: object) -> object:
        nonlocal launched
        if launched:
            raise RuntimeError("saved campaign forbids a second launch or lifecycle restore")
        launched = True
        launch_kwargs.pop("continue_last_save", None)
        launch_kwargs["load_save_name"] = "restored_campaign"
        launch_kwargs["verify_prepared_profile"] = False
        handle = original_launch(*launch_args, **launch_kwargs)
        command = getattr(handle, "command", None)
        process = getattr(handle, "process", None)
        pid = getattr(process, "pid", None)
        argv = list(command) if isinstance(command, (list, tuple)) else None
        argv_admitted = (isinstance(argv, list) and all(isinstance(item, str) for item in argv)
            and argv.count("-loadsave=restored_campaign") == 1 and "-continuelastsave" not in argv
            and type(pid) is int and pid > 0)
        launch_record.update(status="ACTUAL_SINGLE_CLI_RESTORE_LAUNCHED", command=argv,
            ck3_pid=pid if type(pid) is int else None, argv_admitted=argv_admitted,
            continue_last_save=False, load_save_name="restored_campaign", captured_at=now())
        # Return the handle even if command evidence is malformed, so the
        # existing managed supervisor retains ownership and performs cleanup.
        return handle

    globals_copy = dict(vars(module))
    globals_copy["launch"] = launch_saved_once
    for name in ("_native_session_locked", "native_session"):
        original = getattr(module, name)
        bound = FunctionType(original.__code__, globals_copy, original.__name__,
            original.__defaults__, original.__closure__)
        bound.__kwdefaults__ = original.__kwdefaults__
        globals_copy[name] = bound
    native = globals_copy["native_session"](spec, native_bridge=config,
        timeout_seconds=args.timeout + args.hold_seconds + 120,
        cold_start_checkpoint=False, stop_event=stop, input_stream=None, output_stream=output_stream)
    native["saved_campaign_only"] = True
    native["single_saved_campaign_launch"] = launched
    native["saved_campaign_load_name"] = "restored_campaign"
    native["saved_campaign_launch"] = copy.deepcopy(launch_record)
    return native


def saved_campaign_admission_frame(snapshot: object, expected: dict[str, object],
        frontend_binding: dict[str, object]) -> dict[str, object] | None:
    if not isinstance(snapshot, dict) or snapshot.get("map_ready") is not True or snapshot.get("paused") is not True:
        return None
    if snapshot.get("active_event") is not None or snapshot.get("episode_projection") != "native_campaign":
        return None
    played = snapshot.get("played_character")
    diagnostics = snapshot.get("diagnostics")
    if not isinstance(played, dict) or played.get("alive") is not True or played.get("source") != "native":
        return None
    if played.get("character_id") != expected["actor_character_id"] or snapshot.get("date_raw") != expected["date_raw"]:
        return None
    if not isinstance(diagnostics, dict) or any(diagnostics.get(k) != v for k, v in frontend_binding.items()):
        raise ValueError("saved campaign crossed its observed frontend process or connection")
    hello = diagnostics.get("hello")
    if not isinstance(hello, dict) or any(hello.get(k) != v for k, v in {
            "pid": frontend_binding["bridge_pid"], "connection_generation": frontend_binding["connection_generation"],
            "game_adapter_id": "ck3-1.20.0.4-msvc-x64", "expected_ck3_version": "1.20.0.4", "ck3_build_match": True}.items()) or (
            str(hello.get("expected_ck3_sha256")).upper() != "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518"):
        raise ValueError("saved campaign lacks the exact actual .4 native build binding")
    if (type(snapshot.get("local_player_id")) is not int or snapshot["local_player_id"] < 1
            or not isinstance(snapshot.get("snapshot_id"), str) or not snapshot["snapshot_id"]
            or type(snapshot.get("native_revision")) is not int or snapshot["native_revision"] < 1
            or type(snapshot.get("revision")) is not int or snapshot["revision"] < 1):
        return None
    heartbeat = diagnostics.get("last_heartbeat")
    mailbox = heartbeat.get("main_thread_query_mailbox_v1") if isinstance(heartbeat, dict) else None
    observer = heartbeat.get("snapshot_observer_12002") if isinstance(heartbeat, dict) else None
    if not isinstance(mailbox, dict) or not isinstance(observer, dict) or heartbeat.get("pid") != frontend_binding["bridge_pid"]:
        return None
    epoch = mailbox.get("pump_epochs")
    started, completed = observer.get("started_ms"), observer.get("completed_ms")
    if (mailbox.get("ready") is not True or mailbox.get("stamp_read_success") is not True
            or type(epoch) is not int or epoch < 1 or mailbox.get("owner_verified_pump_epochs") != epoch
            or type(mailbox.get("owner_tid")) is not int or mailbox["owner_tid"] < 1
            or mailbox.get("current_tid") != mailbox["owner_tid"]
            or observer.get("read_in_progress") is not False or type(started) is not int
            or type(completed) is not int or completed < started):
        return None
    return {"actor_character_id": expected["actor_character_id"], "date_raw": expected["date_raw"],
        "local_player_id": snapshot["local_player_id"], "snapshot_id": snapshot["snapshot_id"],
        "revision": snapshot["revision"], "native_revision": snapshot["native_revision"],
        **frontend_binding, "owner_tid": mailbox["owner_tid"], "pump_epoch": epoch}


def saved_campaign_root_binding(snapshot: dict[str, object], root: object,
        frame: dict[str, object]) -> dict[str, object] | None:
    if not isinstance(root, dict) or root.get("campaign_root_context_ready") is not True:
        return None
    if root.get("backend_id") != "native-headless" or any(root.get(k) != snapshot.get(v) for k, v in {
            "queried_snapshot_id": "snapshot_id", "queried_revision": "revision",
            "queried_native_revision": "native_revision", "date_raw": "date_raw"}.items()):
        raise ValueError("saved campaign root is not bound to the observed current paused frame")
    provenance = root.get("provenance")
    if (not isinstance(provenance, dict) or provenance.get("game_version") != "1.20.0.4"
            or str(provenance.get("executable_sha256")).upper() != "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518"):
        raise ValueError("saved campaign root lacks exact .4 native provenance")
    if root.get("player_character_id") != frame["actor_character_id"] or root.get("player_character_alive") is not True:
        raise ValueError("saved campaign current native root and snapshot disagree on the living actor")
    return {**frame, "actual_current_actor_bound": True, "saved_campaign_identity_proven": True,
        "product_acceptance_proven": False}


def saved_campaign_initial_snapshot_state(value: object, pipe: str) -> str:
    """Recognize only the existing transport's finite pre-snapshot startup states."""
    if not isinstance(value, dict) or value.get("pipe") != pipe or value.get("transport_error") is not None:
        raise RuntimeError("saved campaign startup diagnostics lacks its exact pipe or has a transport error")
    diagnostics = value.get("diagnostics")
    if (not isinstance(diagnostics, dict) or diagnostics.get("pipe_name") != pipe
            or diagnostics.get("protocol_version") != 1 or diagnostics.get("transport_fatal_error") is not None
            or diagnostics.get("last_error") is not None
            or type(diagnostics.get("connected")) is not bool
            or type(diagnostics.get("semantic_state_available")) is not bool
            or type(diagnostics.get("rejected_state_snapshot_count")) is not int
            or diagnostics["rejected_state_snapshot_count"] != 0):
        raise RuntimeError("saved campaign startup diagnostics is malformed or reports a fatal/rejected native frame")
    if diagnostics["connected"] is False:
        if (diagnostics["semantic_state_available"] is not False or diagnostics.get("hello") is not None
                or diagnostics.get("bridge_pid") is not None or diagnostics.get("connection_generation") != 0):
            raise RuntimeError("saved campaign observed a native disconnection after an initial binding")
        return "WAITING_FOR_INITIAL_NATIVE_CONNECTION"
    hello = diagnostics.get("hello")
    pid, generation = diagnostics.get("bridge_pid"), diagnostics.get("connection_generation")
    if (type(pid) is not int or not 1 <= pid <= 2**32-1
            or type(generation) is not int or not 1 <= generation <= 2**64-1
            or not isinstance(hello, dict) or any(hello.get(k) != v for k, v in {
                "pid": pid, "connection_generation": generation, "game_adapter_id": "ck3-1.20.0.4-msvc-x64",
                "expected_ck3_version": "1.20.0.4", "ck3_build_match": True}.items())
            or str(hello.get("expected_ck3_sha256")).upper() != "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518"
            or not isinstance(hello.get("capabilities"), list) or "game.state.snapshot" not in hello["capabilities"]):
        raise RuntimeError("saved campaign initial native hello lacks exact .4 identity or snapshot capability")
    return ("INITIAL_NATIVE_SEMANTIC_FRAME_AVAILABLE" if diagnostics["semantic_state_available"]
        else "WAITING_FOR_INITIAL_NATIVE_SEMANTIC_FRAME")


async def wait_for_saved_campaign(client: PlanClient, expected: dict[str, object], *,
        report: dict[str, object], write: object, timeout: float,
        managed_done: threading.Event | None, poll_interval: float) -> dict[str, object]:
    report["phase"] = "saved-campaign-single-command-line-restore"
    state = {"status": "WAITING_FOR_ACTUAL_SAVED_CAMPAIGN_OWNER_FRAMES", "expected": expected, "observations": [],
        "load_provider": "runtime.launch(load_save_name):single_-loadsave",
        "new_game_requested": False, "start_requested": False, "fixture_setup_requested": False,
        "product_acceptance_proven": False}
    report["saved_campaign_restore"] = state
    write()
    deadline = time.monotonic() + timeout
    binding = None
    baseline = None
    initial_snapshot_available = False
    state["startup_observations"] = []
    while True:
        if managed_done is not None and managed_done.is_set():
            raise RuntimeError("managed session ended before saved campaign admission")
        if not initial_snapshot_available:
            # R9 queried Snapshot before the launch thread had created CK3.
            # This existing pure diagnostic distinguishes that known startup
            # state without swallowing an opaque MCP tool error.
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("saved campaign initial native connection/semantic frame was not ready before original readiness deadline")
            diagnostic = await asyncio.wait_for(client.call("ck3_migration_pipe_diagnostics"), timeout=remaining)
            startup_status = saved_campaign_initial_snapshot_state(diagnostic, report["pipe"])
            initial_snapshot_available = startup_status == "INITIAL_NATIVE_SEMANTIC_FRAME_AVAILABLE"
            state["startup_observations"].append({"at": now(), "status": startup_status,
                "connected": diagnostic["diagnostics"]["connected"],
                "semantic_state_available": diagnostic["diagnostics"]["semantic_state_available"],
                "bridge_pid": diagnostic["diagnostics"].get("bridge_pid"),
                "connection_generation": diagnostic["diagnostics"].get("connection_generation")})
            write()
            if time.monotonic() >= deadline:
                raise TimeoutError("saved campaign initial native connection/semantic frame was not ready before original readiness deadline")
            if not initial_snapshot_available:
                await asyncio.sleep(min(poll_interval, max(0, deadline-time.monotonic())))
                continue
        snapshot = await client.fresh()
        launch_record = report.get("saved_campaign_launch")
        if isinstance(launch_record, dict) and launch_record.get("status") == "ACTUAL_SINGLE_CLI_RESTORE_LAUNCHED":
            if launch_record.get("argv_admitted") is not True:
                raise RuntimeError("actual saved campaign launch lacks its exact single -loadsave argv/PID evidence")
        diagnostics = snapshot.get("diagnostics")
        if binding is None and isinstance(diagnostics, dict):
            candidate = {k: diagnostics.get(k) for k in ("bridge_pid", "connection_generation")}
            if all(type(v) is int and 1 <= v <= maximum for v, maximum in (
                    (candidate["bridge_pid"], 2**32-1), (candidate["connection_generation"], 2**64-1))):
                binding = candidate
                state["observed_process_binding"] = binding
        if binding is None:
            if time.monotonic() >= deadline:
                raise TimeoutError("saved campaign native process binding was not observed before original readiness deadline")
            write()
            await asyncio.sleep(min(poll_interval, max(0, deadline-time.monotonic())))
            continue
        if (not isinstance(launch_record, dict) or launch_record.get("argv_admitted") is not True
                or launch_record.get("ck3_pid") != binding["bridge_pid"]):
            if time.monotonic() >= deadline:
                raise TimeoutError("saved campaign bridge PID was not bound to the actual single launch before readiness deadline")
            write()
            await asyncio.sleep(min(poll_interval, max(0, deadline-time.monotonic())))
            continue
        frame = saved_campaign_admission_frame(snapshot, expected, binding)
        root, admitted = None, None
        if frame is not None:
            stable = {k: v for k, v in frame.items() if k != "pump_epoch"}
            if baseline is not None and baseline[0] == stable and frame["pump_epoch"] > baseline[1]:
                root = await client.call("ck3_query_campaign_root_context_v1", {"expected_revision": snapshot["revision"]})
                after = await client.fresh()
                after_frame = saved_campaign_admission_frame(after, expected, binding)
                if (after_frame is not None and isinstance(root, dict)
                        and root.get("queried_snapshot_id") == after.get("snapshot_id")
                        and root.get("queried_revision") == after.get("revision")):
                    admitted = saved_campaign_root_binding(after, root, after_frame)
                snapshot = after
            baseline = (stable, frame["pump_epoch"])
        else:
            baseline = None
        state["observations"].append({"snapshot": snapshot, "frame": frame, "campaign_root": root, "binding": admitted})
        if admitted is not None:
            state.update(status="ACTUAL_SAVED_CAMPAIGN_CURRENT_CONTEXT_BOUND", binding=admitted,
                finished_at=now(), actual_current_actor_bound=True)
            report["readiness"] = snapshot
            report["readiness_guard"] = {"schema": "ck3-paused-map-readiness-admission-v1",
                "mode": "saved_campaign_only", "native_campaign_binding": admitted,
                "one_life_identity_fabricated": False, "product_acceptance_proven": False}
            write()
            return state
        write()
        if time.monotonic() >= deadline:
            raise TimeoutError("saved campaign did not reach exact paused event-free native identity/root before original readiness deadline")
        await asyncio.sleep(min(poll_interval, max(0, deadline-time.monotonic())))



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
        def _with_one_life_episode(self, snapshot: dict[str, object]) -> dict[str, object]:
            projected = super()._with_one_life_episode(snapshot)
            if self.episode_projection == "native_campaign" and managed_campaign_run_binding is not None:
                return {**projected, "managed_campaign_run_binding": dict(managed_campaign_run_binding)}
            return projected

        def _ingest(self, frame: dict[str, object]) -> None:
            wire.write("dll-to-python", frame)
            super()._ingest(frame)

    fixture_policy = None
    if args.frontend_fixture_start_policy is not None:
        from xar_autoplayer.bridge.frontend_fixture_start_contract import load_bound_fixture_start_policy
        fixture_policy, fixture_policy_bytes = load_bound_fixture_start_policy(
            args.frontend_fixture_start_policy, args.state_dir / "profile")
    managed_campaign_run_binding = (allocated_managed_campaign_run_binding(args)
        if fixture_policy is not None or args.saved_campaign_server else None)
    driver_options = {"episode_projection": "native_campaign"} if managed_campaign_run_binding is not None else {}
    driver = RecordingDriver(
        args.bridge_pipe, endpoint=RecordingEndpoint(args.bridge_pipe),
        state_dir=args.state_dir, save_dir=args.state_dir / "profile/save games",
        command_timeout_seconds=args.command_timeout,
        frontend_transition_timeout_seconds=240.0 if args.saved_campaign_server else 120.0,
        checkpoint_timeout_seconds=args.command_timeout, **driver_options,
    )
    if managed_campaign_run_binding is not None:
        from xar_autoplayer.bridge.driver import PreSubmissionRevisionMismatchError
        install_campaign_speed_presubmission_transmission(driver, PreSubmissionRevisionMismatchError)
    if fixture_policy is not None:
        driver.frontend_fixture_start_policy_binding = {"policy_sha256": hashlib.sha256(fixture_policy_bytes).hexdigest(),
            "preparation_sha256": fixture_policy["preparation"]["sha256"]}
        server = create_server(driver, profile_dir=args.state_dir / "profile")
    else:
        server = create_server(driver, profile_dir=args.state_dir / "profile") if args.saved_campaign_server else create_server(driver)

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


def episode_identity_frame(snapshot: object) -> dict[str, object]:
    """Admit an actual paused, alive native one-life frame, never a history ID."""
    if not isinstance(snapshot, dict):
        raise ValueError("episode anchor snapshot is not an object")
    played = snapshot.get("played_character")
    diagnostics = snapshot.get("diagnostics")
    if not isinstance(played, dict) or not isinstance(diagnostics, dict):
        raise ValueError("episode anchor lacks player or native binding")
    character = played.get("character_id")
    pid, generation = diagnostics.get("bridge_pid"), diagnostics.get("connection_generation")
    if (type(character) is not int or not 1 <= character <= 2**31 - 1 or
            snapshot.get("map_ready") is not True or snapshot.get("paused") is not True or
            played.get("alive") is not True or played.get("source") != "native" or
            type(snapshot.get("episode_character_id")) is not int or snapshot.get("episode_character_id") != character or
            snapshot.get("one_life_terminal") is not False or
            not isinstance(snapshot.get("episode_run_id"), str) or not snapshot["episode_run_id"] or
            snapshot.get("backend_id") != "native-headless" or snapshot.get("source") != "injected-dll-named-pipe" or
            type(pid) is not int or pid <= 0 or type(generation) is not int or generation <= 0):
        raise ValueError("episode anchor requires one alive native player and matching immutable episode")
    frame = {key: snapshot.get(key) for key in
             ("snapshot_id", "revision", "native_revision", "date_raw", "local_player_id", "episode_run_id")}
    if (not isinstance(frame["snapshot_id"], str) or not frame["snapshot_id"] or
            type(frame["revision"]) is not int or frame["revision"] < 0 or
            type(frame["native_revision"]) is not int or frame["native_revision"] <= 0 or
            type(frame["date_raw"]) is not int or type(frame["local_player_id"]) is not int):
        raise ValueError("episode anchor lacks an exact native frame")
    return {**frame, "runtime_character_id": character,
            "bridge_pid": pid, "connection_generation": generation}


def campaign_pause_frame_binding(snapshot: object, *, allow_running: bool = False) -> dict[str, object]:
    """Bind a complete campaign frame; heartbeat is only an owner guard."""
    if not isinstance(snapshot, dict):
        raise RuntimeError("campaign pause readback lacks a complete snapshot")
    diagnostics = snapshot.get("diagnostics")
    played = snapshot.get("played_character")
    if not isinstance(diagnostics, dict) or not isinstance(played, dict):
        raise RuntimeError("campaign pause readback lacks native identity")
    hello = diagnostics.get("hello")
    heartbeat = diagnostics.get("last_heartbeat")
    mailbox = heartbeat.get("main_thread_query_mailbox_v1") if isinstance(heartbeat, dict) else None
    if not isinstance(hello, dict) or not isinstance(mailbox, dict):
        raise RuntimeError("campaign pause readback lacks the actual owner")
    expected = {"expected_ck3_version": "1.20.0.4",
                "expected_ck3_sha256": "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518",
                "game_adapter_id": "ck3-1.20.0.4-msvc-x64", "ck3_build_match": True}
    if any(type(hello.get(k)) is not type(v) or hello[k] != v for k, v in expected.items()):
        raise RuntimeError("campaign pause readback crossed exact native build identity")
    pid, generation, actor = diagnostics.get("bridge_pid"), diagnostics.get("connection_generation"), played.get("character_id")
    numbers = {"pid": (pid, 1, 2**32 - 1), "generation": (generation, 1, 2**64 - 1),
               "actor": (actor, 1, 2**31 - 1), "date": (snapshot.get("date_raw"), 1, 2**31 - 1),
               "revision": (snapshot.get("revision"), 1, 2**64 - 1), "native_revision": (snapshot.get("native_revision"), 1, 2**64 - 1),
               "local_player": (snapshot.get("local_player_id"), 0, 2**31 - 1), "speed": (snapshot.get("speed"), 1, 5),
               "owner": (mailbox.get("owner_tid"), 1, 2**32 - 1), "pump": (mailbox.get("owner_verified_pump_epochs"), 1, 2**64 - 1),
               "rejections": (diagnostics.get("rejected_state_snapshot_count"), 0, 2**64 - 1)}
    if any(type(v) is not int or not lo <= v <= hi for v, lo, hi in numbers.values()):
        raise RuntimeError("campaign pause readback has malformed identity or clock")
    running = (allow_running is True and snapshot.get("paused") is False
               and mailbox.get("ready") is False)
    if running and (snapshot["speed"] != 1
            or type(hello.get("connection_generation")) is not int or hello["connection_generation"] != generation
            or mailbox.get("application_main_observed") is not True or mailbox.get("paused") is not False
            or mailbox.get("paused_main_thread_observed") is not False or type(mailbox.get("ready")) is not bool
            or type(mailbox.get("consecutive_verified")) is not int or mailbox["consecutive_verified"] < 0):
        raise RuntimeError("campaign pause readback lacks the complete running owner stamp")
    if (snapshot.get("episode_projection") != "native_campaign" or snapshot.get("backend_id") != "native-headless"
            or snapshot.get("source") != "injected-dll-named-pipe" or snapshot.get("map_ready") is not True
            or type(snapshot.get("format_version")) is not int or snapshot["format_version"] != 1
            or snapshot.get("complete_snapshot") is False
            or type(snapshot.get("paused")) is not bool or played.get("alive") is not True
            or snapshot.get("active_event") is not None or snapshot.get("one_life_terminal_reason") is not None
            or snapshot.get("snapshot_id") != "native:" + str(snapshot["native_revision"])
            or diagnostics.get("connected") is not True or diagnostics.get("semantic_state_available") is not True
            or diagnostics.get("last_error") is not None or diagnostics.get("transport_fatal_error") is not None
            or type(hello.get("pid")) is not int or hello["pid"] != pid
            or type(heartbeat.get("pid")) is not int or heartbeat["pid"] != pid
            or not isinstance(diagnostics.get("pipe_name"), str) or not diagnostics["pipe_name"]
            or mailbox.get("installed") is not True or (mailbox.get("ready") is not True and not running)
            or mailbox.get("stop") is not False or type(mailbox.get("failure")) is not int or mailbox["failure"] != 0
            or type(mailbox.get("current_tid")) is not int or mailbox["current_tid"] != mailbox["owner_tid"]
            or mailbox.get("stamp_read_success") is not True or type(mailbox.get("date_raw")) is not int
            or mailbox["date_raw"] != snapshot["date_raw"]):
        raise RuntimeError("campaign pause readback lost the complete same-owner frame")
    return {"identity": (pid, generation, actor, snapshot["local_player_id"], snapshot["speed"],
                         diagnostics["pipe_name"], mailbox["owner_tid"], snapshot.get("pending_character_interaction")),
            "date": snapshot["date_raw"], "revision": snapshot["revision"], "native_revision": snapshot["native_revision"],
            "pump": mailbox["owner_verified_pump_epochs"], "rejections": diagnostics["rejected_state_snapshot_count"]}


def require_campaign_pause_successor(source: dict[str, object], snapshot: object, *, allow_running: bool = False) -> dict[str, object]:
    current = campaign_pause_frame_binding(snapshot, allow_running=allow_running)
    if (current["identity"] != source["identity"] or current["rejections"] != source["rejections"]
            or any(current[k] < source[k] for k in ("date", "revision", "native_revision", "pump"))):
        raise RuntimeError("campaign pause readback owner, clock or rejection state changed")
    return current


class PlanClient:
    def __init__(self, session: object, args: argparse.Namespace, report: dict[str, object], write: object) -> None:
        self.session, self.args, self.report, self.write = session, args, report, write
        self.tools: dict[str, dict[str, object]] = {}
        self.results: dict[str, object] = {}
        self.snapshot: dict[str, object] = {}
        self.episode_identity: dict[str, object] | None = None
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
            rejection = campaign_speed_presubmission_receipt(row["payload"], name, arguments or {})
            if rejection is not None:
                raise CampaignSpeedPreSubmissionRevisionError(rejection)
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

    async def bind_episode_identity(self) -> dict[str, object]:
        if self.episode_identity is not None:
            raise ValueError("episode identity is already anchored; never rebind after death or restart")
        before = await self.fresh()
        frame = episode_identity_frame(before)
        root = await self.call("ck3_query_campaign_root_context_v1", {"expected_revision": frame["revision"]})
        if not isinstance(root, dict):
            raise ValueError("episode anchor campaign root is not an object")
        expected_binding = {key: frame[key] for key in ("snapshot_id", "revision", "native_revision", "date_raw")}
        expected_binding["expected_revision"] = frame["revision"]
        context = root.get("campaign_root_context", {})
        hello = before["diagnostics"].get("hello", {})
        if (root.get("status") != "available" or root.get("campaign_root_context_ready") is not True or
                root.get("binding") != expected_binding or not isinstance(context, dict) or
                context.get("player_character_id") != frame["runtime_character_id"] or
                context.get("player_character_alive") is not True or
                context.get("local_player_id") != frame["local_player_id"] or
                context.get("snapshot_revision") != frame["native_revision"] or
                context.get("date_raw") != frame["date_raw"] or
                root.get("build") != {"version": hello.get("expected_ck3_version"),
                                      "exe_sha256": hello.get("expected_ck3_sha256")}):
            raise ValueError("episode anchor campaign root crossed its exact snapshot/player/build")
        after = await self.fresh()
        if episode_identity_frame(after) != frame:
            raise ValueError("episode anchor native frame changed across campaign-root query")
        self.episode_identity = copy.deepcopy({**frame, "episode_character_id": frame["runtime_character_id"],
                                               "verified": True, "snapshot": before, "campaign_root": root})
        return copy.deepcopy(self.episode_identity)

    async def observe_terminal_window(self, row: dict[str, object]) -> dict[str, object]:
        """Observe fixed death roots under the original process binding, without a living snapshot."""
        from xar_autoplayer.bridge.frontend_gui_route_contract import frontend_gui_route_binding_from_capabilities
        from xar_autoplayer.bridge.gui_window_tree_contract import normalize_gui_window_tree_v1
        kind = row.get("window_kind")
        if kind not in {"death_succession", "death_destiny"}:
            raise ValueError("terminal window observation accepts only fixed death roots")
        anchor = self.episode_identity
        if not isinstance(anchor, dict) or anchor.get("verified") is not True:
            raise ValueError("terminal window observation requires the original episode anchor")
        binding = {key: anchor[key] for key in ("bridge_pid", "connection_generation")}
        before = await self.call("ck3_get_capabilities")
        if frontend_gui_route_binding_from_capabilities(before) != binding:
            raise ValueError("terminal window observation changed its original process binding")
        raw = await self.call("ck3_inspect_gui_window_tree_v1", {"window_kind": kind})
        # The call journal has the full raw DTO even if validation/owner reread fails.
        tree = normalize_gui_window_tree_v1(raw, kind)
        after = await self.call("ck3_get_capabilities")
        if frontend_gui_route_binding_from_capabilities(after) != binding:
            raise ValueError("terminal window observation crossed its original process binding")
        return {**tree, "observation_binding": binding,
                "anchored_episode_run_id": anchor["episode_run_id"],
                "anchored_episode_character_id": anchor["episode_character_id"],
                "terminal_actor_proven": False, "settlement_rendered_values_proven": False}

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
                   "army_ids": army_ids, "results": self.results, "episode": self.episode_identity}
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

    async def set_campaign_speed_one_presubmission_once(self, before: dict[str, object]) -> object:
        """Refresh once only after an exact non-submitted speed rejection, under one deadline."""
        diagnostics = before.get("diagnostics")
        hello = diagnostics.get("hello") if isinstance(diagnostics, dict) else None
        if (before.get("episode_projection") != "native_campaign" or not isinstance(hello, dict)
                or hello.get("expected_ck3_version") != "1.20.0.4"):
            return await self.invoke("ck3_execute_step", {"step": "set-speed-1"})
        deadline = time.monotonic() + self.args.command_timeout
        source = campaign_pause_frame_binding(before)
        if before.get("paused") is not True:
            raise RuntimeError("speed pre-submission guard requires the actual paused frame")
        evidence: dict[str, object] = {"source": "campaign_speed_presubmission_same_owner_once_v1",
            "started_at": now(), "deadline_seconds": self.args.command_timeout,
            "refresh_count": 0, "attempts": [], "initial_snapshot_id": before["snapshot_id"],
            "product_acceptance_proven": False}
        self.report.setdefault("campaign_speed_presubmission", []).append(evidence)

        def remaining() -> float:
            managed_done = getattr(self, "managed_done", None)
            if managed_done is not None and managed_done.is_set():
                raise RuntimeError("managed native session ended before speed submission")
            seconds = deadline - time.monotonic()
            if seconds <= 0:
                raise TimeoutError("speed pre-submission refresh exceeded its original deadline")
            return seconds

        async def full_frame() -> tuple[dict[str, object], dict[str, object]]:
            seconds = remaining()
            frame = await asyncio.wait_for(self.fresh(), seconds)
            bound = require_campaign_pause_successor(source, frame)
            if frame.get("paused") is not True or bound["date"] != source["date"]:
                raise RuntimeError("speed pre-submission refresh changed the actual paused date")
            return frame, bound

        async def attempt(frame: dict[str, object], bound: dict[str, object]) -> object:
            seconds = remaining()
            evidence["attempts"].append({"snapshot_id": frame["snapshot_id"],
                "expected_revision": bound["revision"], "date_raw": bound["date"]})
            return await asyncio.wait_for(self.invoke("ck3_execute_step",
                {"step": "set-speed-1", "expected_revision": bound["revision"]},
                fresh_revision=False), seconds)

        try:
            frame, bound = await full_frame()
            try:
                result = await attempt(frame, bound)
            except CampaignSpeedPreSubmissionRevisionError as error:
                receipt = error.receipt
                if receipt["expected_revision"] != bound["revision"]:
                    raise RuntimeError("speed rejection crossed its exact submitted expectation") from error
                evidence["original_rejection"] = copy.deepcopy(receipt)
                successor, successor_bound = await full_frame()
                if (successor_bound["revision"] < receipt["current_revision"]
                        or successor_bound["revision"] <= bound["revision"]):
                    raise RuntimeError("speed refresh did not reach the server's current full revision") from error
                evidence["refresh_count"] = 1
                result = await attempt(successor, successor_bound)
            # A returned ACK is never replayed. The old full speed/advance/pause readbacks remain mandatory.
            evidence.update(status="ACK_RETURNED_ORIGINAL_FULL_READBACKS_REQUIRED", finished_at=now())
            return result
        except BaseException as error:
            evidence.update(status="FAILED_OR_CANCELLED_ORIGINAL_ERROR_PRESERVED", finished_at=now(),
                error_type=type(error).__name__, error=str(error))
            raise


    async def pause_campaign_after_advance(self, starting: dict[str, object]) -> dict[str, object]:
        """At most one idempotent pause refresh under one original deadline."""
        deadline = time.monotonic() + self.args.command_timeout
        evidence: dict[str, object] = {"source": "campaign_postpause_same_owner_once_v1",
            "starting_snapshot_id": starting.get("snapshot_id"), "starting_date_raw": starting.get("date_raw"),
            "attempts": [], "status": "PENDING", "business_credit_from_heartbeat": False}
        self.report.setdefault("campaign_pause_readbacks", []).append(evidence)

        def remaining() -> float:
            value = deadline - time.monotonic()
            managed_done = getattr(self, "managed_done", None)
            if managed_done is not None and managed_done.is_set():
                raise RuntimeError("managed session finished during campaign pause readback")
            if value <= 0:
                raise TimeoutError("campaign pause readback exhausted the original command deadline")
            return value

        async def bounded(factory: object) -> object:
            timeout = remaining()
            value = await asyncio.wait_for(factory(), timeout=timeout)
            remaining()
            return value

        async def pause(arguments: dict[str, object], *, fresh_revision: bool = True) -> str:
            attempt: dict[str, object] = {"step": "pause-map", "arguments": arguments, "status": "PENDING", "rpc_started": False}
            evidence["attempts"].append(attempt)
            async def invoke() -> object:
                attempt["rpc_started"] = True
                return await self.invoke("ck3_execute_step", arguments, fresh_revision=fresh_revision)
            result = await bounded(invoke)
            status = result.get("status") if isinstance(result, dict) else None
            if (not isinstance(result, dict) or result.get("step") != "pause-map" or result.get("accepted") is not True
                    or status not in ("submitted", "already_paused")):
                attempt["status"] = "UNADMITTED_ACK"
                raise RuntimeError("campaign pause readback received an unadmitted pause ACK")
            attempt["status"] = status
            return status

        try:
            source = campaign_pause_frame_binding(starting, allow_running=True)
            ack = await pause({"step": "pause-map"})
            evidence["binding"] = {"bridge_pid": source["identity"][0], "connection_generation": source["identity"][1],
                "runtime_character_id": source["identity"][2], "owner_tid": source["identity"][6]}
            retry_at = time.monotonic() + 1.0
            retried = False
            previous = source
            while True:
                current = await bounded(self.fresh)
                observed = require_campaign_pause_successor(previous, current, allow_running=True)
                previous = observed
                if current["paused"] is True:
                    evidence.update(status="FULL_PAUSED_FRAME_OBSERVED", ending_snapshot_id=current["snapshot_id"],
                                    ending_date_raw=current["date_raw"], pause_attempt_count=len(evidence["attempts"]))
                    return current
                if ack == "submitted" and not retried and time.monotonic() >= retry_at:
                    # This is the sole extra action: bind its revision to the frame
                    # just checked, avoiding an unchecked implicit second fresh().
                    retried = True
                    ack = await pause({"step": "pause-map", "expected_revision": current["revision"]}, fresh_revision=False)
                    continue
                delay = min(self.args.poll_interval, remaining())
                if ack == "submitted" and not retried:
                    delay = min(delay, max(0.0, retry_at - time.monotonic()))
                await asyncio.sleep(delay)
        except BaseException as error:
            evidence.update(status="FAILED_OR_CANCELLED_ORIGINAL_ERROR_PRESERVED", error_type=type(error).__name__,
                            pause_attempt_count=len(evidence["attempts"]))
            raise


    async def advance(self, row: dict[str, object]) -> dict[str, object]:
        await self.invoke("ck3_execute_step", {"step": "pause-map"})
        before = await self.wait_snapshot({"paused": True}, self.args.command_timeout)
        await self.set_campaign_speed_one_presubmission_once(before)
        await self.wait_snapshot({"speed": 1}, self.args.command_timeout)
        wait_for_actor_change = row.get("wait_for_played_character_change") is True
        if wait_for_actor_change and before.get("episode_projection") != "native_campaign":
            raise ValueError("player transition wait requires a native campaign")
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
                    if wait_for_actor_change:
                        diagnostics = current.get("diagnostics") or {}
                        initial = before.get("diagnostics") or {}
                        if (current.get("episode_projection") != "native_campaign"
                                or any(diagnostics.get(key) != initial.get(key) for key in
                                       ("bridge_pid", "connection_generation", "pipe_name"))
                                or current.get("local_player_id") != before.get("local_player_id")):
                            raise ValueError("player transition crossed the admitted campaign process")
                        played = current.get("played_character") or {}
                        observer = (diagnostics.get("last_heartbeat") or {}).get("snapshot_observer_12002") or {}
                        if not (current.get("map_ready") is True and played.get("source") == "native"
                                and played.get("alive") is True and type(played.get("character_id")) is int
                                and played["character_id"] > 0
                                and played["character_id"] != before["played_character"]["character_id"]
                                and type(current.get("native_revision")) is int
                                and current["native_revision"] > int(before["native_revision"])
                                and observer.get("read_in_progress") is False
                                and type(observer.get("started_ms")) is int
                                and type(observer.get("completed_ms")) is int
                                and observer["completed_ms"] >= observer["started_ms"]):
                            await asyncio.sleep(self.args.poll_interval)
                            continue
                    reached = current
                    break
                await asyncio.sleep(self.args.poll_interval)
            if reached is None:
                raise TimeoutError("running map did not reach the requested date")
        finally:
            campaign_diagnostics = reached.get("diagnostics") if reached is not None else None
            campaign_hello = campaign_diagnostics.get("hello") if isinstance(campaign_diagnostics, dict) else None
            use_campaign_pause_readback = (reached is not None and reached.get("episode_projection") == "native_campaign"
                and isinstance(campaign_hello, dict) and campaign_hello.get("expected_ck3_version") == "1.20.0.4")
            if use_campaign_pause_readback:
                after = await self.pause_campaign_after_advance(reached)
            else:
                await self.invoke("ck3_execute_step", {"step": "pause-map"})
        if not use_campaign_pause_readback:
            after = await self.wait_snapshot({"paused": True}, self.args.command_timeout)
        if int(after["date_raw"]) < target:
            raise RuntimeError("pause readback preceded the requested date")
        result = {"before": before, "running_successor": reached, "after": after,
                  "requested_days": row.get("days", 1), "elapsed_hours": int(after["date_raw"]) - start}
        if use_campaign_pause_readback:
            result.update(requested_interval_complete=True, event_boundary=None)
        return result

    async def advance_event_boundary(self, step: dict[str, object]) -> dict[str, object]:
        """Explicit time-or-event observation; an early event is never one-day proof."""
        if step.get("allow_event_boundary") is not True or type(step.get("days", 1)) is not int or step.get("days", 1) != 1:
            raise ValueError("event-boundary advance requires explicit opt-in and days=1")
        required_tools = {"ck3_get_capabilities", "ck3_take_snapshot", "ck3_execute_step", "ck3_query_current_event_window_context_v1"}
        if not required_tools <= set(self.tools) or self.episode_identity is None:
            raise ValueError("event-boundary advance lacks actual MCP tools or episode anchor")
        capabilities = await self.call("ck3_get_capabilities")
        primitives = {"pause-map", "resume-map", "set-speed-1"}
        if (not isinstance(capabilities, dict) or capabilities.get("snapshot") is not True or
                not primitives <= set(capabilities.get("action_steps", [])) or
                capabilities.get("current_event_window_context_v1_query_supported") is not True or
                "game.command.query-current-event-window-context-v1" not in capabilities.get("bridge_capabilities", [])):
            raise ValueError("event-boundary advance lacks actual native primitives or typed event observer")
        identity_keys = ("runtime_character_id", "episode_run_id", "bridge_pid", "connection_generation")
        def same_episode(snapshot: object, *, paused: bool = True) -> None:
            if paused:
                frame = episode_identity_frame(snapshot)
            else:
                if not isinstance(snapshot, dict) or not isinstance(snapshot.get("played_character"), dict) or not isinstance(snapshot.get("diagnostics"), dict):
                    raise ValueError("running advance lacks actual player/owner binding")
                player, owner = snapshot["played_character"], snapshot["diagnostics"]
                if snapshot.get("map_ready") is not True or player.get("alive") is not True or snapshot.get("episode_character_id") != player.get("character_id"):
                    raise ValueError("running advance left its alive anchored map")
                frame = {"runtime_character_id": player.get("character_id"), "episode_run_id": snapshot.get("episode_run_id"),
                         "bridge_pid": owner.get("bridge_pid"), "connection_generation": owner.get("connection_generation")}
            if any(frame[key] != self.episode_identity[key] for key in identity_keys):
                raise ValueError("event-boundary advance crossed the anchored episode/PID/generation")
        before = await self.fresh()
        same_episode(before)
        if before.get("active_event") is not None:
            raise ValueError("event-boundary advance requires no existing active event")
        await self.invoke("ck3_execute_step", {"step": "pause-map"})
        before = await self.wait_snapshot({"paused": True}, self.args.command_timeout)
        same_episode(before)
        if before.get("active_event") is not None:
            raise ValueError("an event appeared before time advance; query it first")
        start, target = int(before["date_raw"]), int(before["date_raw"]) + 24
        await self.invoke("ck3_execute_step", {"step": "set-speed-1"})
        before_resume = await self.wait_snapshot({"speed": 1, "paused": True}, self.args.command_timeout)
        same_episode(before_resume)
        if before_resume.get("active_event") is not None:
            raise ValueError("an event appeared while setting speed; query it before resume")
        boundary = reached = None
        deadline = time.monotonic() + float(step.get("timeout", self.args.command_timeout))
        try:
            await self.invoke("ck3_execute_step", {"step": "resume-map"})
            while time.monotonic() < deadline:
                current = await self.fresh()
                same_episode(current, paused=False)
                if current.get("active_event") is not None:
                    boundary = current
                    break
                if int(current["date_raw"]) >= target:
                    reached = current
                    break
                await asyncio.sleep(self.args.poll_interval)
            if boundary is None and reached is None:
                raise TimeoutError("running map reached neither target date nor event boundary")
        finally:
            owner = self.snapshot.get("diagnostics", {})
            if (isinstance(owner, dict) and owner.get("bridge_pid") == self.episode_identity["bridge_pid"] and
                    owner.get("connection_generation") == self.episode_identity["connection_generation"]):
                await self.invoke("ck3_execute_step", {"step": "pause-map"})
        after = await self.wait_snapshot({"paused": True}, self.args.command_timeout)
        same_episode(after)
        if boundary is None and after.get("active_event") is not None:
            boundary = after
        if boundary is not None:
            event = boundary.get("active_event")
            after_event = after.get("active_event")
            if (not isinstance(event, dict) or type(event.get("instance_id")) is not int or event["instance_id"] <= 0 or
                    not isinstance(after_event, dict) or after_event.get("instance_id") != event["instance_id"] or
                    int(after["date_raw"]) < int(boundary["date_raw"])):
                raise ValueError("paused event boundary lost its full instance or date")
            observed = int(boundary["date_raw"])
            progress = "event_before_target" if observed < target else "event_at_target" if observed == target else "event_after_target"
            interval_complete = observed >= target and int(after["date_raw"]) >= target
        else:
            if int(after["date_raw"]) < target:
                raise RuntimeError("pause readback preceded the requested date")
            progress, interval_complete = "target_date_reached", True
        return {"before": before, "running_successor": reached, "event_boundary": boundary, "after": after,
                "requested_days": 1, "target_date_raw": target, "elapsed_hours": int(after["date_raw"]) - start,
                "progress_status": progress, "requested_interval_complete": interval_complete,
                "event_resolution": "typed_query_required" if boundary is not None else "none",
                "preflight": {"native_primitives": sorted(primitives), "typed_event_query_supported": True},
                "selected_event_options": 0}

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
                if kind == "episode_identity_anchor":
                    result = await self.bind_episode_identity()
                elif kind == "advance_day":
                    result = await self.advance_event_boundary(step) if step.get("allow_event_boundary") is True else await self.advance(step)
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
                elif kind == "terminal_window_read_only":
                    result = await self.observe_terminal_window(step)
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
                    # Only explicit $ref expectations opt in; legacy literals stay literal.
                    if isinstance(expected, dict) and set(expected) == {"$ref"}:
                        expected = resolve(expected, {"snapshot": self.snapshot, "result": result,
                                                       "results": self.results, "episode": self.episode_identity})
                    row.setdefault("resolved_expect", {})[path] = expected
                    actual = lookup(result, path)
                    if actual != expected:
                        raise ValueError(f"result {path} expected {expected!r}, received {actual!r}")
                self.results[str(row["id"])] = result
                if kind not in {"frontend_read_only", "terminal_window_read_only"}:
                    managed_done = getattr(self, "managed_done", None)
                    proof = (finished_native_exit_zero_proof(self.report,
                        managed_done is not None and managed_done.is_set(), self.episode_identity)
                        if kind == "finish_hold" else None)
                    if proof is None:
                        row["after_snapshot"] = await self.fresh()
                    else:
                        row["after_snapshot"] = proof
                        self.report["post_exit_finish_hold"] = {"step_id": row["id"], "proof": copy.deepcopy(proof)}
                row["ok"] = True
            except Exception as error:
                row["error"] = f"{type(error).__name__}: {error}"
                if not step.get("continue_on_error", False):
                    raise
            finally:
                row["finished_at"] = now()
                self.write()

    async def observe_final(self) -> None:
        """Only a successful final finish_hold can make post-exit observation inapplicable."""
        marker = self.report.get("post_exit_finish_hold")
        rows = self.report.get("steps", [])
        managed_done = getattr(self, "managed_done", None)
        proof = finished_native_exit_zero_proof(self.report,
            managed_done is not None and managed_done.is_set(), self.episode_identity)
        if (proof is not None and isinstance(marker, dict) and rows
                and self.report.get("hold_finished_by_control_plan") is True
                and rows[-1].get("plan", {}).get("kind") == "finish_hold"
                and marker.get("step_id") == rows[-1].get("id")
                and marker.get("proof") == proof and all(row.get("ok") is True for row in rows)):
            self.report["snapshot_final"] = copy.deepcopy(proof)
            self.report["diagnostics_final"] = copy.deepcopy(proof)
            self.report["final_observation"] = {"status": "not_applicable",
                "reason": proof["reason"], "after_finish_hold_step_id": marker["step_id"],
                "alive_or_business_credit": False}
            return
        self.report["snapshot_final"] = await self.fresh()
        self.report["diagnostics_final"] = await self.call("ck3_migration_pipe_diagnostics")


    async def hold(self, seconds: float) -> None:
        deadline = time.monotonic() + seconds
        self.report["phase"] = "hold"
        self.report["hold_until_utc_estimated"] = time.time() + seconds
        managed_done = getattr(self, "managed_done", None)
        managed_completion_written = managed_done is not None and managed_done.is_set()
        self.write()
        while time.monotonic() < deadline and not self.report.get("hold_finished_by_control_plan", False):
            if not managed_completion_written and managed_done is not None and managed_done.is_set():
                self.write()
                managed_completion_written = True
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


def load_frontend_rules_plan(path: Path) -> tuple[dict[str, object], bytes]:
    raw = path.expanduser().resolve().read_bytes()
    if len(raw) > 32768:
        raise ValueError("frontend rules plan exceeds 32768 bytes")
    def unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("frontend rules plan contains duplicate JSON fields")
            result[key] = value
        return result
    plan = validate_frontend_rules_plan(json.loads(raw.decode("utf-8-sig"), object_pairs_hook=unique))
    return plan, raw


def validate_frontend_rules_plan(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != {"schema", "schema_version", "rules"}:
        raise ValueError("frontend rules plan accepts only schema/version/rules intent")
    if value["schema"] != "ck3-frontend-rules-plan-v1" or type(value["schema_version"]) is not int or value["schema_version"] != 1:
        raise ValueError("unsupported frontend rules plan schema")
    rows = value["rules"]
    if not isinstance(rows, list) or not 1 <= len(rows) <= 32:
        raise ValueError("frontend rules plan requires 1..32 actual rule targets")
    result = []
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"rule_key", "desired_setting_key"}:
            raise ValueError("frontend rule target accepts only rule_key/desired_setting_key")
        for key in row.values():
            if not isinstance(key, str) or not re.fullmatch(r"[A-Za-z0-9_]{1,96}", key):
                raise ValueError("frontend rule target must be an explicit script key")
        if row["rule_key"] in seen:
            raise ValueError("frontend rules plan contains duplicate rule keys")
        seen.add(row["rule_key"])
        result.append(dict(row))
    return {"schema": value["schema"], "schema_version": 1, "rules": result}


def require_frontend_rules_native(value: object, schema: str, source: str,
        binding: object = None, *, allow_unavailable: bool = False) -> dict[str, object]:
    if not isinstance(value, dict):
        raise RuntimeError("native rules result is not an object")
    build = frontend_native_build_pair(value.get("game_version"), value.get("executable_sha256"))
    for key, expected in {"schema": schema, "schema_version": 1,
            "source": source, "backend_id": "native-headless", "read_only": True,
            "game_version": build.game_version, "executable_sha256": build.executable_sha256,
            "uses_ocr": False, "uses_mouse": False, "uses_keyboard": False}.items():
        if type(value.get(key)) is not type(expected) or value[key] != expected:
            raise RuntimeError("native rules result has an unadmitted " + key)
    native_binding = value.get("binding")
    if not isinstance(native_binding, dict) or set(native_binding) != {"bridge_pid", "connection_generation"} or any(
            type(native_binding.get(key)) is not int or not 1 <= native_binding[key] <= maximum
            for key, maximum in (("bridge_pid", 2**32 - 1), ("connection_generation", 2**64 - 1))) or (
            binding is not None and native_binding != binding):
        raise RuntimeError("native rules result crossed or lacks its frontend binding")
    if type(value.get("ready")) is not bool or not isinstance(value.get("unavailable_reason"), str) or value["ready"] != (value["unavailable_reason"] == ""):
        raise RuntimeError("native rules result has inconsistent availability")
    applied = schema == "frontend_applied_game_rules_v1" and value["ready"]
    if value.get("applied_settings_proven") is not applied:
        raise RuntimeError("native rules proof does not belong to the observed actual instance")
    if not allow_unavailable and not value["ready"]:
        raise RuntimeError("native rules are unavailable: " + value["unavailable_reason"])
    if type(value.get("query_sequence")) is not int or value["query_sequence"] < 1:
        raise RuntimeError("native rules result lacks its actual query sequence")
    return value


def require_frontend_rules_values(value: object, *, applied: bool = False,
        binding: object = None) -> dict[str, str]:
    packet = require_frontend_rules_native(value,
        "frontend_applied_game_rules_v1" if applied else "frontend_game_rule_selections_v1",
        "CGameRuleInstance.selected_settings" if applied else "CJominiGameRulesGui.current_selections", binding)
    rows, count = packet.get("selections"), packet.get("selection_count")
    if not isinstance(rows, list) or type(count) is not int or not 1 <= count <= 4096 or len(rows) != count:
        raise RuntimeError("native rules selection collection is malformed")
    values: dict[str, str] = {}
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"rule_key", "selected_setting_key"} or any(
                not isinstance(key, str) or not re.fullmatch(r"[A-Za-z0-9_]{1,96}", key) for key in row.values()):
            raise RuntimeError("native rules selected pair is malformed")
        if row["rule_key"] in values:
            raise RuntimeError("native rules selected pair has duplicate rule key")
        values[row["rule_key"]] = row["selected_setting_key"]
    return values


def require_frontend_rules_window(value: object, binding: object = None,
        *, allow_unavailable: bool = False) -> dict[str, object]:
    packet = require_frontend_rules_native(value, "frontend_game_rules_window_v1",
        "CJominiGameRulesGui.owner_root_and_stock_predicates", binding,
        allow_unavailable=allow_unavailable)
    fields = ["window_visible", "window_enabled", "is_host", "game_has_started", "may_edit", "window_closed_proven"]
    if any(type(packet.get(key)) is not bool for key in fields):
        raise RuntimeError("native rule-window predicate is malformed")
    may_edit = packet["ready"] and packet["window_visible"] and packet["window_enabled"] and packet["is_host"] and not packet["game_has_started"]
    if not packet["ready"] and any(packet[key] for key in fields):
        raise RuntimeError("unavailable native rule-window cannot assert state")
    if packet["may_edit"] is not may_edit or packet["window_closed_proven"] is not (packet["ready"] and not packet["window_visible"]):
        raise RuntimeError("native rule-window predicates are inconsistent")
    return packet


async def execute_frontend_rules_plan(client: PlanClient, plan: dict[str, object],
        *, report: dict[str, object], write: object, timeout: float,
        managed_done: threading.Event | None = None, poll_interval: float = 0.1) -> dict[str, object]:
    plan = validate_frontend_rules_plan(plan)
    if "frontend_rules_plan_execution" in report:
        raise RuntimeError("frontend rules plan was already attempted; actions cannot be retried")
    allowed = {"ck3_query_frontend_game_rules_window_v1", "ck3_activate_frontend_game_rules_v1",
        "ck3_query_frontend_game_rule_selections_v1", "ck3_select_frontend_game_rule_v1",
        "ck3_apply_and_hide_frontend_game_rules_v1", "ck3_query_frontend_applied_game_rules_v1"}
    if not allowed.issubset(client.tools):
        raise RuntimeError("frontend rules plan requires the complete typed MCP rule surface")
    execution: dict[str, object] = {"status": "RUNNING", "plan": plan, "calls": [],
        "uses_ocr": False, "uses_mouse": False, "uses_keyboard": False, "snapshot_calls": 0,
        "actions_retried": False, "applied_settings_proven": False, "window_closed_proven": False}
    report["frontend_rules_plan_execution"] = execution
    write()
    async def call(name: str, arguments: dict[str, object] | None = None) -> object:
        if name not in allowed or (managed_done is not None and managed_done.is_set()):
            raise RuntimeError("frontend rules plan scope or managed-session admission failed")
        row: dict[str, object] = {"tool": name, "arguments": arguments or {},
            "started_at": now(), "acknowledged": False, "retry_allowed": False}
        execution["calls"].append(row)
        write()
        try:
            value = await client.call(name, arguments)
            row.update(acknowledged=True, result=value)
            return value
        except BaseException as error:
            row["error"] = f"{type(error).__name__}: {error}"
            raise
        finally:
            row["finished_at"] = now()
            write()
    last_query_sequence = 0
    def later(packet: dict[str, object]) -> dict[str, object]:
        nonlocal last_query_sequence
        if packet["query_sequence"] <= last_query_sequence:
            raise RuntimeError("native rules result is not a later independent query")
        last_query_sequence = packet["query_sequence"]
        return packet
    try:
        window = later(require_frontend_rules_window(await call("ck3_query_frontend_game_rules_window_v1"), allow_unavailable=True))
        binding = window["binding"]
        if not window["ready"] or not window["window_visible"]:
            opened = await call("ck3_activate_frontend_game_rules_v1")
            if not isinstance(opened, dict) or opened.get("status") != "observed":
                raise RuntimeError("native rules Open was not independently observed")
            require_frontend_rules_values(opened.get("observation"), binding=binding)
            later(opened["observation"])
            window = later(require_frontend_rules_window(await call("ck3_query_frontend_game_rules_window_v1"), binding))
        if not window["may_edit"]:
            raise RuntimeError("native rules plan requires the actual host/not-started editable window")
        initial = await call("ck3_query_frontend_game_rule_selections_v1")
        values = require_frontend_rules_values(initial, binding=binding)
        later(initial)
        if any(row["rule_key"] not in values for row in plan["rules"]):
            raise RuntimeError("frontend rules plan target is absent from the actual selected model")
        execution["initial"] = initial
        for target in plan["rules"]:
            current_packet = await call("ck3_query_frontend_game_rule_selections_v1")
            current = require_frontend_rules_values(current_packet, binding=binding)
            later(current_packet)
            if current != values:
                raise RuntimeError("native rule choices changed between planned selections")
            key, desired = target["rule_key"], target["desired_setting_key"]
            selected = await call("ck3_select_frontend_game_rule_v1", {"rule_key": key,
                "expected_current_setting_key": current[key], "desired_setting_key": desired})
            if not isinstance(selected, dict) or selected.get("status") != "observed" or selected.get("applied_settings_proven") is not False:
                raise RuntimeError("native rule selection did not return an observed result")
            values = {**values, key: desired}
            if require_frontend_rules_values(selected.get("observation"), binding=binding) != values:
                raise RuntimeError("native rule selection changed another rule or missed its target")
            later(selected["observation"])
            verification = await call("ck3_query_frontend_game_rule_selections_v1")
            if require_frontend_rules_values(verification, binding=binding) != values:
                raise RuntimeError("later actual rule selection query did not verify the requested target")
            later(verification)
        execution["requested_selected_pairs"] = values
        applied_ack = await call("ck3_apply_and_hide_frontend_game_rules_v1")
        execution["apply_hide"] = applied_ack
        if not isinstance(applied_ack, dict) or applied_ack.get("status") != "observed" or applied_ack.get("applied_settings_proven") is not False or applied_ack.get("window_closed_proven") is not True:
            raise RuntimeError("native Apply/Hide did not independently observe its window closure")
        ack_window = require_frontend_rules_window(applied_ack.get("window_observation"), binding)
        later(ack_window)
        closed = later(require_frontend_rules_window(await call("ck3_query_frontend_game_rules_window_v1"), binding))
        execution["closed_window"] = closed
        if not closed["window_closed_proven"]:
            raise RuntimeError("a later native window query did not prove closure")
        execution["window_closed_proven"] = True
        deadline = time.monotonic() + timeout
        while True:
            actual = await call("ck3_query_frontend_applied_game_rules_v1")
            actual = later(require_frontend_rules_native(actual, "frontend_applied_game_rules_v1",
                "CGameRuleInstance.selected_settings", binding, allow_unavailable=True))
            execution["latest_applied_instance"] = actual
            if not actual["ready"] and (actual.get("selections") != [] or actual.get("selection_count") != 0):
                raise RuntimeError("unavailable actual rule instance cannot assert selected pairs")
            actual_values = require_frontend_rules_values(actual, applied=True, binding=binding) if actual["ready"] else None
            if actual_values == values:
                execution.update(status="ACTUAL_RULES_APPLIED_AND_WINDOW_CLOSED",
                    applied_settings_proven=True, finished_at=now())
                write()
                return execution
            if time.monotonic() >= deadline:
                raise TimeoutError("later actual rule-instance values did not equal the requested selected pairs")
            await asyncio.sleep(poll_interval)
    except BaseException as error:
        execution.update(status="FAILED_NO_START", error=f"{type(error).__name__}: {error}", finished_at=now())
        write()
        raise



def fixture_whole_root_admission_frame(snapshot: object, submission: dict[str, object], *,
        allow_active_event: bool = False) -> dict[str, object] | None:
    """Default root gate stays event-free; startup window queries reuse owner checks."""
    if not isinstance(snapshot, dict) or snapshot.get("map_ready") is not True or snapshot.get("paused") is not True:
        return None
    if snapshot.get("active_event") is not None and not allow_active_event:
        return None
    if snapshot.get("episode_projection") != "native_campaign":
        raise ValueError("fixture pre-query observation would bind a one-life episode")
    diagnostics = snapshot.get("diagnostics")
    if not isinstance(diagnostics, dict) or any(diagnostics.get(key) != wanted for key, wanted in submission["binding"].items()):
        raise ValueError("fixture pre-query map crossed the admitted native frontend process")
    selected_date = submission["selected_candidate"]["selected_bookmark_start_date_raw"]
    if snapshot.get("date_raw") != selected_date:
        raise ValueError("fixture pre-query startup advanced away from the actual bookmark date")
    played = snapshot.get("played_character")
    if (not isinstance(played, dict) or type(played.get("character_id")) is not int or played["character_id"] < 1
            or played.get("alive") is not True or played.get("source") != "native"
            or type(snapshot.get("local_player_id")) is not int or snapshot["local_player_id"] < 1
            or not isinstance(snapshot.get("snapshot_id"), str) or not snapshot["snapshot_id"]
            or type(snapshot.get("native_revision")) is not int or snapshot["native_revision"] < 1):
        return None
    heartbeat = diagnostics.get("last_heartbeat")
    mailbox = heartbeat.get("main_thread_query_mailbox_v1") if isinstance(heartbeat, dict) else None
    if not isinstance(heartbeat, dict) or heartbeat.get("pid") != submission["binding"]["bridge_pid"] or not isinstance(mailbox, dict):
        return None
    epoch, owner_epoch = mailbox.get("pump_epochs"), mailbox.get("owner_verified_pump_epochs")
    if (mailbox.get("ready") is not True or mailbox.get("stamp_read_success") is not True
            or type(epoch) is not int or epoch < 1 or type(owner_epoch) is not int or owner_epoch != epoch
            or type(mailbox.get("owner_tid")) is not int or mailbox["owner_tid"] < 1
            or mailbox.get("current_tid") != mailbox["owner_tid"]):
        return None
    return {"actor_character_id": played["character_id"], "date_raw": selected_date,
            "local_player_id": snapshot["local_player_id"], "snapshot_id": snapshot["snapshot_id"],
            "native_revision": snapshot["native_revision"], **submission["binding"], "pump_epoch": owner_epoch}


def capture_fixture_startup_notice_evidence(client: PlanClient, stage: str, event_id: int) -> dict[str, object]:
    """Retain raw desktop pixels and declared isolated-userdir files, never classify them."""
    import pyautogui
    profile = (client.args.state_dir / "profile").resolve()
    preparation = json.loads((client.args.state_dir / "preparation.json").read_text(encoding="utf-8-sig"))
    if Path(preparation["profile_dir"]).resolve() != profile:
        raise RuntimeError("startup notification evidence crossed the actual fixture profile")
    directory = client.args.output.parent / "startup-notice-evidence"
    directory.mkdir(exist_ok=True)
    path = directory / f"event-{event_id}-{stage}.png"
    image = pyautogui.screenshot()
    with path.open("xb") as stream:
        image.save(stream, format="PNG")
    files = {}
    for relative in preparation["profile_files"]:
        source = (profile / relative).resolve()
        if not source.is_relative_to(profile):
            raise RuntimeError("startup notification marker escaped the actual fixture profile")
        raw = source.read_bytes() if source.is_file() else None
        files[relative] = {"path": str(source), "exists": raw is not None,
            "bytes": len(raw) if raw is not None else None,
            "sha256": hashlib.sha256(raw).hexdigest() if raw is not None else None}
    return {"captured_at": now(), "screenshot": {"path": str(path), "bytes": path.stat().st_size,
            "sha256": file_sha(path), "size": list(image.size), "source": "pyautogui.screenshot/raw-desktop"},
        "profile_dir": str(profile), "declared_profile_files": files,
        "ocr": {"status": "not-run", "reason": "raw pixels retained; visible button text and decision come from typed event context"},
        "intro_character_flag_file_readback": {"status": "unavailable", "proven": False,
            "reason": "the in-memory character intro flag has no declared userdir marker file"},
        "used_for_selection_or_acceptance": False}


def verify_fixture_startup_case_contract(value: object, state_dir: Path) -> dict[str, object]:
    """Bind a product's pure proof code/data to this actual fresh fixture state."""
    if (not isinstance(value, dict) or set(value) != {"schema", "state_dir", "handler", "dependencies"}
            or value.get("schema") != "ck3-frontend-fixture-startup-case-contract-v1"
            or not isinstance(value.get("state_dir"), str) or not Path(value["state_dir"]).is_absolute()
            or Path(value["state_dir"]).resolve() != state_dir.resolve()):
        raise ValueError("startup case contract must bind the actual fixture state")
    handler, dependencies = value["handler"], value["dependencies"]
    if (not isinstance(handler, dict) or set(handler) != {"path", "bytes", "sha256", "function"}
            or not isinstance(handler.get("function"), str) or not handler["function"].isidentifier()
            or handler["function"].startswith("_") or not isinstance(dependencies, list)
            or not 0 <= len(dependencies) <= 32):
        raise ValueError("startup case must declare one pinned public pure-proof handler")
    seen = set()
    for row in [handler, *dependencies]:
        if (not isinstance(row, dict) or set(row) != ({"path", "bytes", "sha256", "function"} if row is handler
                else {"path", "bytes", "sha256"}) or not isinstance(row.get("path"), str)
                or not Path(row["path"]).is_absolute() or type(row.get("bytes")) is not int or row["bytes"] < 1
                or not isinstance(row.get("sha256"), str) or len(row["sha256"]) != 64
                or any(char not in "0123456789abcdef" for char in row["sha256"])):
            raise ValueError("startup case source/data pin is malformed")
        path = Path(row["path"])
        if path.is_symlink() or not path.is_file() or path.resolve() in seen:
            raise ValueError("startup case source/data must be distinct ordinary files")
        seen.add(path.resolve())
        raw = path.read_bytes()
        if len(raw) != row["bytes"] or hashlib.sha256(raw).hexdigest() != row["sha256"]:
            raise ValueError("startup case source/data differs from its declared pin")
    if Path(handler["path"]).suffix != ".py":
        raise ValueError("startup case handler must be a pinned Python source file")
    return value


def load_fixture_startup_case_contract(path: Path, state_dir: Path) -> tuple[dict[str, object], bytes]:
    if path.is_symlink() or not path.is_file():
        raise ValueError("startup case contract must be an ordinary file")
    raw = path.read_bytes()
    if not 1 <= len(raw) <= 65536:
        raise ValueError("startup case contract exceeds its bounded descriptor size")
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("startup case contract has duplicate keys")
            result[key] = value
        return result
    return verify_fixture_startup_case_contract(
        json.loads(raw.decode("utf-8-sig"), object_pairs_hook=unique), state_dir), raw


def fixture_startup_case_proof(contract: dict[str, object], snapshot: dict[str, object],
        event_context: dict[str, object], state_dir: Path) -> dict[str, object]:
    """Load pinned product proof only; this helper has no client or command surface."""
    import importlib.util
    from types import ModuleType
    verify_fixture_startup_case_contract(contract, state_dir)
    handler = contract["handler"]
    path = Path(handler["path"]).resolve()
    package_name = "_ck3_fixture_startup_case_" + handler["sha256"][:24]
    module_name = package_name + "." + path.stem
    package = ModuleType(package_name)
    package.__path__ = [str(path.parent)]
    old_path = list(sys.path)
    old_modules = dict(sys.modules)
    try:
        # Relative case dependencies use a private namespace. Absolute helpers
        # must also come from their declared ordinary pinned file.
        for row in contract["dependencies"]:
            dependency = Path(row["path"]).resolve()
            existing = sys.modules.get(dependency.stem) if dependency.suffix == ".py" else None
            if existing is not None and Path(getattr(existing, "__file__", "")).resolve() != dependency:
                raise ValueError("startup case dependency is already loaded from another source")
        sys.path.insert(0, str(path.parent.parent))
        sys.modules[package_name] = package
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise ValueError("startup case proof source cannot be loaded")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        callback = getattr(module, handler["function"], None)
        if not callable(callback):
            raise ValueError("startup case proof handler is absent")
        # Copy only the bounded event/frame projection, never its audit/history.
        proof_snapshot = copy.deepcopy({key:snapshot.get(key) for key in (
            "snapshot_id", "revision", "native_revision", "date_raw", "played_character",
            "active_event", "paused", "map_ready", "episode_projection", "local_player_id")})
        proof = callback({"state_dir": str(state_dir.resolve())}, proof_snapshot, copy.deepcopy(event_context))
        verify_fixture_startup_case_contract(contract, state_dir)
        if (not isinstance(proof, dict) or set(proof) != {"event_instance_id", "option_number", "proof", "business_pass"}
                or type(proof.get("event_instance_id")) is not int or proof["event_instance_id"] < 1
                or type(proof.get("option_number")) is not int or proof["option_number"] != 1
                or not isinstance(proof.get("proof"), dict) or not proof["proof"]
                or proof.get("business_pass") is not False
                or len(json.dumps(proof, ensure_ascii=False).encode("utf-8")) > 65536):
            raise ValueError("startup case pure proof returned an invalid selection qualification")
        return proof
    finally:
        sys.path[:] = old_path
        for name in list(sys.modules):
            if name == package_name or name.startswith(package_name + "."):
                if name in old_modules:
                    sys.modules[name] = old_modules[name]
                else:
                    sys.modules.pop(name, None)


async def acknowledge_fixture_startup_case(client: PlanClient, snapshot: dict[str, object],
        submission: dict[str, object], contract: dict[str, object], *, state: dict[str, object],
        write: object, deadline: float) -> dict[str, object]:
    """Select a case-qualified sole startup option once under the original owner gate."""
    if "startup_case" in state:
        raise RuntimeError("fixture startup case request cannot be replayed")
    managed_done = getattr(client, "managed_done", None)
    def within_session():
        if (time.monotonic() >= deadline or (managed_done is not None and managed_done.is_set())):
            raise RuntimeError("fixture startup case exceeded its original deadline or managed session")
    within_session()
    frame = fixture_whole_root_admission_frame(snapshot, submission, allow_active_event=True)
    diagnostics = snapshot.get("diagnostics") or {}
    heartbeat = diagnostics.get("last_heartbeat") or {}
    observer = heartbeat.get("snapshot_observer_12002") or {}
    event = snapshot.get("active_event")
    event_id = event.get("instance_id") if isinstance(event, dict) else None
    started, completed = observer.get("started_ms"), observer.get("completed_ms")
    if (frame is None or type(event_id) is not int or event_id < 1
            or observer.get("read_in_progress") is not False or type(started) is not int
            or type(completed) is not int or completed < started):
        raise RuntimeError("fixture startup case lacks a completed actual owner event frame")
    current = {**frame, "revision": snapshot["revision"], "event_instance_id": event_id,
        "owner_tid": heartbeat["main_thread_query_mailbox_v1"]["owner_tid"]}
    admission = state.get("first_startup_query_admission") or {}
    previous = admission.get("previous_frame") or {}
    if (admission.get("current_frame") != current or type(previous.get("pump_epoch")) is not int
            or previous["pump_epoch"] >= current["pump_epoch"]
            or {k:v for k,v in previous.items() if k != "pump_epoch"} != {k:v for k,v in current.items() if k != "pump_epoch"}):
        raise RuntimeError("fixture startup case requires the actual two stable owner frames")
    hello = diagnostics.get("hello") or {}
    build = frontend_native_build_pair(hello.get("expected_ck3_version"), hello.get("expected_ck3_sha256"))
    if (build.game_version != "1.20.0.4" or diagnostics.get("connected") is not True
            or hello.get("pid") != submission["binding"]["bridge_pid"]
            or hello.get("connection_generation") != submission["binding"]["connection_generation"]
            or hello.get("game_adapter_id") != f"ck3-{build.game_version}-msvc-x64"
            or hello.get("ck3_build_match") is not True):
        raise RuntimeError("fixture startup case requires the qualified current4 native build")
    record = {"status": "OBSERVING_TYPED_CASE_STARTUP_EVENT", "selection_attempted": False,
        "retry_allowed": False, "product_acceptance_proven": False, "snapshot": snapshot,
        "contract": contract, "original_deadline": deadline}
    state["startup_case"] = record
    write()
    try:
        packet = await client.call("ck3_query_current_event_window_context_v1", {
            "event_instance_id": event_id, "expected_revision": snapshot["revision"]})
        record["event_context"] = packet
        context = packet.get("current_event_window_context", {}) if isinstance(packet, dict) else {}
        identity = (context.get("root_scope") or {}).get("typed_identity") or {}
        options = context.get("options")
        public = event.get("options")
        actor = snapshot["played_character"]["character_id"]
        if (not isinstance(packet, dict) or packet.get("status") != "available"
                or packet.get("current_event_window_context_ready") is not True
                or context.get("schema") != "current-event-window-context-v1" or type(context.get("schema_version")) is not int
                or context["schema_version"] != 1 or context.get("status") != "available"
                or type(context.get("window_match_count")) is not int or context["window_match_count"] != 1
                or context.get("current_event_instance_id") != event_id or context.get("snapshot_revision") != snapshot["native_revision"]
                or context.get("date_raw") != snapshot["date_raw"] or context.get("provenance", {}).get("backend_id") != build.backend_id("event-window-v1")
                or any(packet.get(key) != snapshot.get(wanted) for key,wanted in {
                    "queried_snapshot_id":"snapshot_id", "queried_revision":"revision", "queried_native_revision":"native_revision"}.items())
                or (context.get("root_scope") or {}).get("status") != "available" or (context.get("root_scope") or {}).get("type_key") != "character"
                or identity.get("status") != "available" or identity.get("kind") != "character" or identity.get("character_id") != actor
                or not isinstance(options, list) or len(options) != 1 or any(options[0].get(k) != v for k,v in {
                    "rendered_index":0, "native_option_index":0, "shown":True, "enabled":True, "fallback":False, "cancel":False}.items())
                or type(options[0].get("native_option_index")) is not int or type(options[0].get("rendered_index")) is not int
                or not isinstance(public, list) or len(public) != 1 or type(public[0].get("option_number")) is not int
                or public[0]["option_number"] != 1 or public[0].get("enabled") is not True):
            raise RuntimeError("fixture startup case typed current event crossed its actual actor/frame/sole option")
        within_session()
        proof = fixture_startup_case_proof(contract, snapshot, packet, client.args.state_dir)
        record["case_qualification"] = proof
        if proof["event_instance_id"] != event_id:
            raise RuntimeError("startup case proof selected another actual event instance")
        within_session()
        record.update(status="NORMAL_CASE_OPTION_REQUEST_WRITTEN", selection_attempted=True, requested_at=now())
        write()
        record["selection_result"] = await client.call("ck3_select_event_option", {
            "option_number":proof["option_number"], "event_instance_id":event_id, "expected_revision":snapshot["revision"]})
        after = await client.fresh()
        record["after_snapshot"] = after
        within_session()
        after_diagnostics = after.get("diagnostics") or {}
        after_hello = after_diagnostics.get("hello") or {}
        after_observer = (after_diagnostics.get("last_heartbeat") or {}).get("snapshot_observer_12002") or {}
        if (after.get("active_event") is not None or after.get("map_ready") is not True or after.get("paused") is not True
                or after.get("date_raw") != snapshot["date_raw"] or after.get("played_character", {}).get("character_id") != actor
                or after.get("played_character", {}).get("alive") is not True or after.get("played_character", {}).get("source") != "native"
                or after.get("local_player_id") != snapshot.get("local_player_id") or after_diagnostics.get("connected") is not True
                or any(after_hello.get(k) != hello.get(k) for k in ("pid", "connection_generation", "game_adapter_id",
                    "expected_ck3_version", "expected_ck3_sha256", "ck3_build_match"))
                or after_observer.get("read_in_progress") is not False or type(after_observer.get("started_ms")) is not int
                or type(after_observer.get("completed_ms")) is not int or after_observer["completed_ms"] < after_observer["started_ms"]
                or any(after.get("diagnostics", {}).get(k) != v for k,v in submission["binding"].items())
                or fixture_whole_root_admission_frame(after, submission) is None):
            raise RuntimeError("case startup option did not independently observe the same paused actual event-free frame")
        record.update(status="NORMAL_CASE_OPTION_EVENT_GONE_OBSERVED", finished_at=now())
        write()
        return after
    except BaseException as error:
        record.update(status="CASE_STARTUP_FAILED_NO_RETRY", error=f"{type(error).__name__}: {error}", finished_at=now())
        write()
        raise


async def acknowledge_fixture_startup_event(client: PlanClient, snapshot: dict[str, object],
        submission: dict[str, object], *, state: dict[str, object], write: object,
        deadline: float) -> dict[str, object]:
    contract = client.report.get("frontend_fixture_startup_case_contract_input", {}).get("contract")
    if contract is None:
        return await acknowledge_fixture_startup_notice(client, snapshot, submission, state=state, write=write)
    return await acknowledge_fixture_startup_case(client, snapshot, submission, contract,
        state=state, write=write, deadline=deadline)



async def acknowledge_fixture_startup_notice(client: PlanClient, snapshot: dict[str, object],
        submission: dict[str, object], *, state: dict[str, object], write: object) -> dict[str, object]:
    """Consume registry-reviewed startup presentation through the normal option tool once."""
    event = snapshot.get("active_event")
    if not isinstance(event, dict):
        return snapshot
    if "startup_notice" in state:
        raise RuntimeError("fixture startup notice request cannot be replayed")
    diagnostics = snapshot.get("diagnostics", {})
    hello = diagnostics.get("hello", {})
    played = snapshot.get("played_character", {})
    actor, event_id = played.get("character_id"), event.get("instance_id")
    if not isinstance(hello, dict):
        raise RuntimeError("fixture startup notice lacks the exact native hello")
    build = frontend_native_build_pair(hello.get("expected_ck3_version"), hello.get("expected_ck3_sha256"))
    if (snapshot.get("map_ready") is not True or snapshot.get("paused") is not True
            or snapshot.get("episode_projection") != "native_campaign"
            or any(diagnostics.get(key) != wanted for key, wanted in submission["binding"].items())
            or snapshot.get("date_raw") != submission["selected_candidate"]["selected_bookmark_start_date_raw"]
            or type(actor) is not int or actor < 1 or played.get("alive") is not True or played.get("source") != "native"
            or type(event_id) is not int or event_id < 1
            or hello.get("expected_ck3_version") != build.game_version or hello.get("expected_ck3_sha256") != build.executable_sha256):
        raise RuntimeError("fixture startup notice lacks its actual paused exact-build actor frame")
    notice = {"status": "OBSERVING_TYPED_STARTUP_EVENT", "selection_attempted": False,
        "retry_allowed": False, "snapshot": snapshot, "product_acceptance_proven": False}
    state["startup_notice"] = notice
    write()
    notice["before_evidence"] = capture_fixture_startup_notice_evidence(client, "before", event_id)
    write()
    packet = await client.call("ck3_query_current_event_window_context_v1", {
        "event_instance_id": event_id, "expected_revision": snapshot["revision"]})
    notice["event_context"] = packet
    context = packet.get("current_event_window_context", {})
    knowledge = await client.call("ck3_query_vanilla_event_knowledge_v1", {
        "event_definition_key": context.get("event_definition_key"), "ck3_build": build.game_version})
    notice["knowledge"] = knowledge
    write()
    contract, analysis = knowledge.get("contract") or {}, knowledge.get("analysis") or {}
    profile = analysis.get("selected_choice_effect_profile") or {}
    root_scope = context.get("root_scope") or {}
    identity = root_scope.get("typed_identity") or {}
    options = context.get("options")
    public_options = event.get("options")
    notice["visible_buttons_before"] = options
    if (packet.get("status") != "available" or packet.get("current_event_window_context_ready") is not True
            or context.get("schema") != "current-event-window-context-v1" or context.get("schema_version") != 1
            or context.get("status") != "available" or context.get("window_match_count") != 1
            or context.get("current_event_instance_id") != event_id
            or context.get("snapshot_revision") != snapshot["native_revision"] or context.get("date_raw") != snapshot["date_raw"]
            or context.get("provenance", {}).get("backend_id") != build.backend_id("event-window-v1")
            or any(packet.get(key) != snapshot.get(wanted) for key, wanted in {
                "queried_snapshot_id": "snapshot_id", "queried_revision": "revision", "queried_native_revision": "native_revision"}.items())
            or knowledge.get("status") != "available" or knowledge.get("ck3_exe_sha256") != build.executable_sha256
            or contract.get("startup_acknowledgement") is not True or contract.get("root_character_id") != "$player"
            or contract.get("option_count") != 1 or contract.get("snapshot_option_count") != 1
            or contract.get("native_option_indices") != [0] or contract.get("selected_option_number") != 1
            or contract.get("selected_native_option_index") != 0
            or profile.get("completeness") != "all-authored-options-and-common-after-source-reviewed"
            or profile.get("selected_option_effects") != [] or profile.get("common_after_effects") != []
            or root_scope.get("status") != "available" or root_scope.get("type_key") != "character"
            or identity.get("status") != "available" or identity.get("kind") != "character" or identity.get("character_id") != actor
            or not isinstance(options, list) or len(options) != 1
            or any(options[0].get(key) != wanted for key, wanted in {
                "rendered_index": 0, "native_option_index": 0, "shown": True, "enabled": True, "fallback": False, "cancel": False}.items())
            or not isinstance(public_options, list) or len(public_options) != 1
            or public_options[0].get("option_number") != 1 or public_options[0].get("enabled") is not True):
        raise RuntimeError("fixture startup event is not the current registry-reviewed acknowledgement")
    notice.update(status="NORMAL_OPTION_REQUEST_WRITTEN", selection_attempted=True, requested_at=now())
    write()
    selection_error = None
    try:
        notice["selection_result"] = await client.call("ck3_select_event_option", {
            "option_number": contract["selected_option_number"], "event_instance_id": event_id,
            "expected_revision": snapshot["revision"]})
        after = await client.fresh()
        notice["after_snapshot"] = after
        after_event = after.get("active_event")
        notice["visible_buttons_after"] = after_event.get("options") if isinstance(after_event, dict) else []
    except BaseException as error:
        selection_error = error
        notice["after_native_state_unavailable"] = f"{type(error).__name__}: {error}"
        raise
    finally:
        try:
            notice["after_evidence"] = capture_fixture_startup_notice_evidence(client, "after", event_id)
        except Exception as error:
            notice["after_evidence_error"] = f"{type(error).__name__}: {error}"
            if selection_error is None:
                raise
        finally:
            write()
    if (after.get("active_event") is not None or after.get("map_ready") is not True or after.get("paused") is not True
            or after.get("date_raw") != snapshot["date_raw"] or after.get("played_character", {}).get("character_id") != actor
            or any(after.get("diagnostics", {}).get(key) != wanted for key, wanted in submission["binding"].items())):
        raise RuntimeError("normal startup acknowledgement did not independently observe the same paused actor event-free")
    notice.update(status="NORMAL_OPTION_EVENT_GONE_OBSERVED", finished_at=now())
    write()
    return after


async def wait_for_fixture_business_context(client: PlanClient, policy: dict[str, object],
        submission: dict[str, object], *, report: dict[str, object], write: object,
        timeout: float, managed_done: threading.Event | None = None,
        poll_interval: float = 0.05) -> dict[str, object]:
    from xar_autoplayer.bridge.frontend_fixture_start_contract import (
        fixture_business_context_binding, require_fixture_start_submission)
    submission = require_fixture_start_submission(submission)
    state = {"status": "WAITING_FOR_ACTUAL_BUSINESS_CONTEXT", "observations": [],
        "fixture_target_identity_proven": False, "product_acceptance_proven": False,
        "start_resubmitted": False, "episode_projection": "native_campaign"}
    report["frontend_fixture_business_context"] = state
    write()
    baseline, admission_baseline, startup_baseline = None, None, None
    deadline = time.monotonic() + timeout
    try:
        while True:
            if managed_done is not None and managed_done.is_set():
                raise RuntimeError("managed session ended before fixture business binding")
            snapshot = await client.fresh()
            root, binding = None, None
            # Qualification precedes both startup presentation and the whole-root query.
            logs = await client.call("ck3_query_engine_log_literals_v1", {"log_name": "debug.log",
                "literals": policy["required_log_markers"] + policy["forbidden_log_markers"], "sample_limit": 1})
            counts = fixture_qualification_counts(logs, policy)
            if any(counts[key] for key in policy["forbidden_log_markers"]):
                raise RuntimeError("actual fixture qualification emitted a forbidden marker")
            qualified = all(counts[key] == 1 for key in policy["required_log_markers"])
            if any(counts[key] > 1 for key in policy["required_log_markers"]):
                raise RuntimeError("fixture initialization was observed more than once")
            startup_admission = None
            if qualified and snapshot.get("map_ready") is True and snapshot.get("paused") is True and snapshot.get("active_event") is not None:
                # R6 published map_ready while the GUI still loaded. Reuse the
                # owner gate, retaining the actual active event for this query.
                startup_frame = fixture_whole_root_admission_frame(snapshot, submission, allow_active_event=True)
                heartbeat = snapshot.get("diagnostics", {}).get("last_heartbeat", {})
                observer = heartbeat.get("snapshot_observer_12002", {})
                started, completed = observer.get("started_ms"), observer.get("completed_ms")
                if (observer.get("read_in_progress") is not False or type(started) is not int
                        or type(completed) is not int or completed < started):
                    startup_frame = None
                if startup_frame is not None:
                    startup_frame = {**startup_frame, "revision": snapshot["revision"],
                        "event_instance_id": snapshot["active_event"].get("instance_id"),
                        "owner_tid": heartbeat["main_thread_query_mailbox_v1"]["owner_tid"]}
                startup_admission = {"status": "WAITING_FOR_COMPLETED_STABLE_STARTUP_OWNER_FRAMES",
                    "frame": startup_frame, "product_acceptance_proven": False}
                if startup_frame is not None:
                    stable_startup = {key: value for key, value in startup_frame.items() if key != "pump_epoch"}
                    if (startup_baseline is not None and startup_baseline[0] == stable_startup
                            and startup_frame["pump_epoch"] > startup_baseline[1]):
                        startup_admission["status"] = "STABLE_STARTUP_OWNER_FRAMES_QUERY_ADMITTED"
                        state["first_startup_query_admission"] = {
                            "previous_frame": {**startup_baseline[0], "pump_epoch": startup_baseline[1]},
                            "current_frame": startup_frame, "qualification": logs,
                            "product_acceptance_proven": False}
                        write()
                        snapshot = await acknowledge_fixture_startup_event(client, snapshot, submission,
                            state=state, write=write, deadline=deadline)
                        startup_baseline = None
                    else:
                        startup_baseline = (stable_startup, startup_frame["pump_epoch"])
                else:
                    startup_baseline = None
            else:
                startup_baseline = None
            admission_frame = fixture_whole_root_admission_frame(snapshot, submission) if qualified else None
            admission = {"status": "WAITING_FOR_ORIGINAL_QUALIFICATION_LOGS" if not qualified else "WAITING_FOR_PAUSED_EVENT_FREE_OWNER_FRAMES",
                "frame": admission_frame, "product_acceptance_proven": False}
            if admission_frame is not None:
                stable_frame = {key: value for key, value in admission_frame.items() if key != "pump_epoch"}
                if (admission_baseline is not None and admission_baseline[0] == stable_frame
                        and admission_frame["pump_epoch"] > admission_baseline[1]):
                    admission["status"] = "STABLE_CURRENT_OWNER_FRAMES_QUERY_ADMITTED"
                    if "first_whole_root_query_admission" not in state:
                        state["first_whole_root_query_admission"] = {
                            "previous_frame": {**admission_baseline[0], "pump_epoch": admission_baseline[1]},
                            "current_frame": admission_frame, "qualification": logs,
                            "product_acceptance_proven": False}
                        write()
                    root = await client.call("ck3_query_campaign_root_context_v1", {"expected_revision": snapshot["revision"]})
                    after = await client.fresh()
                    # Preserve the original full native DTO and exact-frame binder.
                    if root.get("queried_snapshot_id") == after.get("snapshot_id") and root.get("queried_revision") == after.get("revision"):
                        binding = fixture_business_context_binding(after, root, policy, submission)
                    snapshot = after
                admission_baseline = (stable_frame, admission_frame["pump_epoch"])
            else:
                admission_baseline = None
            row = {"snapshot": snapshot, "campaign_root": root, "binding": binding, "qualification": logs,
                "root_query_admission": admission, "startup_query_admission": startup_admission}
            state["observations"].append(row)
            if binding is not None and qualified:
                stable = {key: value for key, value in binding.items() if key != "pump_epoch"}
                if baseline is not None and baseline[0] == stable and binding["pump_epoch"] > baseline[1]:
                    state.update(status="ACTUAL_FIXTURE_QUALIFIED_BUSINESS_CONTEXT_BOUND", binding=binding,
                        actual_current_actor_bound=True, qualification_observed=True, finished_at=now())
                    write()
                    return state
                baseline = (stable, binding["pump_epoch"])
            else:
                baseline = None
            write()
            if time.monotonic() >= deadline:
                raise TimeoutError("actual qualified fixture government/tier/player did not stabilize before deadline")
            await asyncio.sleep(poll_interval)
    except BaseException as error:
        state.update(status="FAILED_AFTER_SINGLE_START_NO_RETRY", error=f"{type(error).__name__}: {error}", finished_at=now())
        write()
        raise


def fixture_qualification_counts(value: object, policy: dict[str, object]) -> dict[str, int]:
    requested = policy["required_log_markers"] + policy["forbidden_log_markers"]
    if not isinstance(value, dict) or value.get("schema") != "xar.ck3.engine-log-literals/v1" or value.get("log_name") != "debug.log":
        raise RuntimeError("fixture qualification is not the actual server-bound fixed log query")
    if value.get("exists") is False and value.get("matches") == []:
        return {key: 0 for key in requested}
    if value.get("exists") is not True or value.get("read_only") is not True or value.get("case_sensitive") is not True:
        raise RuntimeError("fixture qualification query is malformed")
    rows = value.get("matches")
    if not isinstance(rows, list) or [row.get("literal") for row in rows if isinstance(row, dict)] != requested or any(
            not isinstance(row, dict) or type(row.get("line_count")) is not int or row["line_count"] < 0 for row in rows):
        raise RuntimeError("fixture qualification counts do not match the exact requested literals")
    return {row["literal"]: row["line_count"] for row in rows}


async def submit_fixture_robert_once(client: PlanClient, policy: dict[str, object], *,
        report: dict[str, object], write: object) -> dict[str, object]:
    if "frontend_fixture_start_submission" in report:
        raise RuntimeError("fixture Start already attempted; no request may be replayed")
    required = {"ck3_submit_frontend_fixture_robert_start_v1", "ck3_take_snapshot",
                "ck3_query_campaign_root_context_v1", "ck3_query_engine_log_literals_v1"}
    if not required <= set(client.tools):
        raise RuntimeError("fixture startup requires its actual typed submission and read-only query surface")
    state = {"status": "REQUEST_NOT_SENT", "acknowledged": False, "retry_allowed": False}
    report["frontend_fixture_start_submission"] = state
    write()
    try:
        before = await client.call("ck3_query_engine_log_literals_v1", {"log_name": "debug.log",
            "literals": policy["required_log_markers"] + policy["forbidden_log_markers"], "sample_limit": 1})
        state["before_qualification"] = before
        if any(fixture_qualification_counts(before, policy).values()):
            raise RuntimeError("fixture qualification was already present before Start")
        state.update(status="REQUEST_WRITTEN_BEFORE_SUBMISSION", requested_at=now())
        write()
        submission = await client.call("ck3_submit_frontend_fixture_robert_start_v1")
        from xar_autoplayer.bridge.frontend_fixture_start_contract import require_fixture_start_submission
        submission = require_fixture_start_submission(submission)
        state.update(status="SINGLE_START_ACKNOWLEDGED_POST_STATE_PENDING", acknowledged=True, result=submission)
        write()
        return submission
    except BaseException as error:
        state.update(status="FAILED_NO_START_RETRY", error=f"{type(error).__name__}: {error}", finished_at=now())
        write()
        raise


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
    require_rules_button: bool = False, poll_interval: float = 1.0,
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


async def prepare_rules_diagnostic_bookmarks(
    client, *, route, tree, proof, allow_new_game: bool, report, write,
    timeout: float, managed_done=None,
):
    """Optionally dispatch one explicit New Game, then prove stable Bookmarks.

    A callback error or unverified ACK is retained and never retried. This
    diagnostic path cannot select a ruler, apply rules, or dispatch Start.
    """
    if proof.get("consecutive_consistent_observations") != 2:
        raise RuntimeError("rules diagnostic requires two consistent entry observations")
    if route.get("route") == "bookmarks":
        require_consistent_frontend_observation(route, tree, route, require_rules_button=True)
        return route, tree, proof
    if not allow_new_game:
        raise RuntimeError("rules diagnostic requires independently observed Bookmarks; no New Game is dispatched")
    require_consistent_frontend_observation(route, tree, route)
    if route.get("route") != "main_menu":
        raise RuntimeError("explicit diagnostic New Game requires a verified main menu")
    bootstrap = report["frontend_bootstrap"]
    if "diagnostic_new_game_request" in bootstrap:
        raise RuntimeError("diagnostic New Game has already been submitted; retry is forbidden")
    bootstrap["diagnostic_new_game_request"] = {
        "tool": "ck3_activate_frontend_new_game_v1", "args": {},
        "entry_route": route, "entry_tree": tree, "entry_proof": proof,
        "retry_allowed": False,
    }
    write()
    opened = await client.call("ck3_activate_frontend_new_game_v1")
    bootstrap["diagnostic_new_game_result"] = opened
    write()
    if not isinstance(opened, dict) or opened.get("status") != "verified":
        raise RuntimeError("diagnostic native New Game did not independently verify Bookmarks; action is not retried")
    result = await wait_for_consistent_frontend(
        client, report=report, write=write, timeout=timeout,
        managed_done=managed_done, require_route="bookmarks", require_rules_button=True,
    )
    bootstrap.update(diagnostic_bookmarks_route=result[0],
                     diagnostic_bookmarks_tree=result[1], diagnostic_bookmarks_proof=result[2])
    write()
    return result


def annotate_write_error(error: OSError, path: Path, operation: str,
                         stage: dict[str, object]) -> None:
    """Attach the failing sink to the same exception; do not perform a new write."""
    context = {"sink_path": str(path), "operation": operation, **stage,
        "exception_type": type(error).__name__, "exception_message": str(error),
        "errno": error.errno, "winerror": getattr(error, "winerror", None),
        "filename": error.filename, "filename2": getattr(error, "filename2", None),
        "original_exception_traceback": traceback.format_exc()}
    error.ck3_write_error_context = context
    error.add_note("CK3 write-error context: " + json.dumps(context, ensure_ascii=False))


def write_atomic_report(path: Path, report: dict[str, object]) -> None:
    """Install one complete report; preserve old report and partial on failure."""
    partial = path.with_name(f".{path.name}.partial-{uuid.uuid4().hex}")
    operation = "open-exclusive-partial"
    try:
        with partial.open("x", encoding="utf-8") as stream:
            operation = "write-report-json"
            stream.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
            operation = "flush-report-partial"
            stream.flush()
            operation = "fsync-report-partial"
            os.fsync(stream.fileno())
            operation = "close-report-partial"
        operation = "replace-report-from-partial"
        for attempt in range(20):
            try:
                os.replace(partial, path)
            except PermissionError as error:
                if os.name != "nt" or getattr(error, "winerror", None) not in (5, 32, 33) or attempt == 19:
                    raise
                time.sleep(0.05)
            else:
                return
    except OSError as error:
        rows = report.get("steps", [])
        last = rows[-1] if rows else {}
        annotate_write_error(error, partial if operation != "replace-report-from-partial" else path,
            operation, {"report_path": str(path), "partial_path": str(partial),
                "phase": report.get("phase"), "last_step_id": last.get("id"),
                "last_step_ok": last.get("ok"), "last_step_finished_at": last.get("finished_at")})
        raise


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
        report["managed_session_done"] = done.is_set()
        write_atomic_report(args.output, report)

    frontend_rules_plan = None
    if args.frontend_rules_plan is not None:
        frontend_rules_plan, plan_bytes = load_frontend_rules_plan(args.frontend_rules_plan)
        plan_snapshot = args.output.with_suffix(".frontend-rules-plan.json")
        with plan_snapshot.open("xb") as stream:
            stream.write(plan_bytes)
        report["frontend_rules_plan_input"] = {"source_path": str(args.frontend_rules_plan.resolve()),
            "snapshot_path": str(plan_snapshot), "sha256": hashlib.sha256(plan_bytes).hexdigest(),
            "intent": frontend_rules_plan, "source_game_state_claimed": False}
        write()

    frontend_fixture_policy = None
    if args.frontend_fixture_start_policy is not None:
        clean_imports(args.agent_source_root)
        from xar_autoplayer.bridge.frontend_fixture_start_contract import load_bound_fixture_start_policy
        frontend_fixture_policy, policy_bytes = load_bound_fixture_start_policy(
            args.frontend_fixture_start_policy, args.state_dir / "profile")
        policy_snapshot = args.output.with_suffix(".frontend-fixture-start-policy.json")
        with policy_snapshot.open("xb") as stream:
            stream.write(policy_bytes)
        report["frontend_fixture_start_policy_input"] = {"source_path": str(args.frontend_fixture_start_policy.resolve()),
            "snapshot_path": str(policy_snapshot), "sha256": hashlib.sha256(policy_bytes).hexdigest(),
            "policy": frontend_fixture_policy, "episode_projection": "native_campaign", "product_acceptance_proven": False}
        write()

    startup_case_path = getattr(args, "frontend_fixture_startup_case_contract", None)
    if startup_case_path is not None:
        startup_case_contract, startup_case_bytes = load_fixture_startup_case_contract(startup_case_path, args.state_dir)
        startup_case_snapshot = args.output.with_suffix(".frontend-fixture-startup-case-contract.json")
        with startup_case_snapshot.open("xb") as stream:
            stream.write(startup_case_bytes)
        report["frontend_fixture_startup_case_contract_input"] = {
            "source_path": str(startup_case_path.resolve()), "snapshot_path": str(startup_case_snapshot),
            "sha256": hashlib.sha256(startup_case_bytes).hexdigest(), "contract": startup_case_contract,
            "product_acceptance_proven": False, "vanilla_empty_notice_qualification_claimed": False}
        write()

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
        saved_campaign = None
        if args.saved_campaign_save is not None:
            saved_campaign = prepare_saved_campaign(args, spec)
            report["saved_campaign_input"] = saved_campaign
            report["saved_campaign_launch"] = {"status": "WAITING_FOR_ACTUAL_SINGLE_CLI_RESTORE_LAUNCH", "argv_admitted": False}
            write()
        config = NativeBridgeLaunchConfig("native-headless", args.bridge_pipe,
                                         args.bridge_dll.resolve(), args.bridge_injector.resolve())
        report["identity"] = {"game_executable": str(spec.game_exe),
            "game_sha256": file_sha(spec.game_exe), "dll": str(config.dll_path),
            "dll_sha256": file_sha(config.dll_path), "injector": str(config.injector_path),
            "injector_sha256": file_sha(config.injector_path)}

        def supervise() -> None:
            try:
                with args.output.with_suffix(".session.log").open("w", encoding="utf-8") as stream:
                    if args.saved_campaign_save is not None:
                        session_state["report"] = saved_campaign_session(spec, config, args, stop, output_stream=stream,
                            launch_record=report["saved_campaign_launch"])
                        stream.write(json.dumps(session_state["report"], ensure_ascii=False) + "\n")
                    elif args.fixture_profile:
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
        child_args += ["--agent-source-root", str(args.agent_source_root), "--state-dir", str(args.state_dir),
                       "--output", str(args.output)]
    if frontend_fixture_policy is not None:
        child_args += ["--frontend-fixture-start-policy", str(policy_snapshot),
                       "--frontend-robert-bootstrap", "--fixture-profile"]
    if args.saved_campaign_save is not None:
        child_args.append("--saved-campaign-server")
    parameters = StdioServerParameters(command=sys.executable, args=child_args,
        env={"PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1",
             **({"PYTHONPATH": os.environ["PYTHONPATH"]} if "PYTHONPATH" in os.environ else {})})
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
                    client.managed_done = done if supervisor is not None else None
                    client.tools = {item.name: serialized(item) for item in listing.tools}
                    try:
                        # initialize/list_tools prove the child has already opened its pipe.
                        if supervisor is not None:
                            supervisor.start()
                        if args.saved_campaign_save is not None:
                            await wait_for_saved_campaign(client, saved_campaign, report=report, write=write,
                                timeout=args.readiness_timeout, managed_done=done if supervisor is not None else None,
                                poll_interval=args.poll_interval)
                        if args.frontend_robert_bootstrap:
                            report["phase"] = "native-frontend-robert-bootstrap"
                            report["frontend_bootstrap"] = {"status": "RUNNING", "uses_ocr": False,
                                "uses_keyboard": False, "uses_mouse": False, "attempts": []}
                            write()
                            try:
                                route, entry_tree, entry_proof = await wait_for_consistent_frontend(
                                    client, report=report, write=write, timeout=args.readiness_timeout,
                                    managed_done=done if supervisor is not None else None,
                                    require_route="bookmarks" if (args.frontend_rules_diagnostic
                                        and not args.frontend_rules_diagnostic_new_game) else None,
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
                                    try:
                                        route, entry_tree, entry_proof = await prepare_rules_diagnostic_bookmarks(
                                            client, route=route, tree=entry_tree, proof=entry_proof,
                                            allow_new_game=args.frontend_rules_diagnostic_new_game,
                                            report=report, write=write, timeout=args.readiness_timeout,
                                            managed_done=done if supervisor is not None else None,
                                        )
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
                                report["frontend_bootstrap"]["status"] = ("EXPLICIT_NEW_GAME_RULES_DIAGNOSTIC_NO_START"
                                    if args.frontend_rules_diagnostic_new_game else "READ_ONLY_ROUTE_AND_TREE_OBSERVED_NO_START")
                                write()
                                if args.hold_seconds:
                                    await client.hold(args.hold_seconds)
                                raise RuntimeError("Frontend diagnostic only; explicit New Game requested="
                                    + str(args.frontend_rules_diagnostic_new_game)
                                    + "; no ruler selection, Apply, Start or product test requested")
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
                            if frontend_rules_plan is not None:
                                await execute_frontend_rules_plan(client, frontend_rules_plan,
                                    report=report, write=write, timeout=args.readiness_timeout,
                                    managed_done=done if supervisor is not None else None,
                                    poll_interval=args.poll_interval)
                                route, entry_tree, entry_proof = await wait_for_consistent_frontend(
                                    client, report=report, write=write, timeout=args.readiness_timeout,
                                    managed_done=done if supervisor is not None else None, require_route="bookmarks")
                                report["frontend_bootstrap"].update(post_rules_route=route,
                                    post_rules_tree=entry_tree, post_rules_proof=entry_proof,
                                    post_rules_picker_proof=require_verified_bookmarks_picker(entry_tree))
                                write()
                            if frontend_fixture_policy is not None:
                                started = await submit_fixture_robert_once(client, frontend_fixture_policy, report=report, write=write)
                                await wait_for_fixture_business_context(client, frontend_fixture_policy, started,
                                    report=report, write=write, timeout=args.readiness_timeout,
                                    managed_done=done if supervisor is not None else None, poll_interval=args.poll_interval)
                                report["frontend_bootstrap"]["status"] = "SINGLE_FIXTURE_START_ACTUAL_BUSINESS_CONTEXT_BOUND"
                                write()
                            else:
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
                        while args.saved_campaign_save is None:
                            if supervisor is not None and done.is_set():
                                raise RuntimeError(f"managed session ended before readiness: {session_state}")
                            try:
                                snapshot = await client.fresh()
                                if paused_map_readiness_admitted(snapshot, report):
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
                        report["exception_traceback"] = traceback.format_exc()
                        if getattr(error, "ck3_write_error_context", None) is not None:
                            report["write_error_context"] = error.ck3_write_error_context
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
                            await client.observe_final()
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
        if getattr(error, "ck3_write_error_context", None) is not None:
            report.setdefault("write_error_context", error.ck3_write_error_context)
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
    result.add_argument("--saved-campaign-save", type=Path)
    result.add_argument("--saved-campaign-save-bytes", type=int)
    result.add_argument("--saved-campaign-save-sha256")
    result.add_argument("--saved-campaign-player-id", type=int)
    result.add_argument("--saved-campaign-date-raw", type=int)
    result.add_argument("--saved-campaign-product-inventory", type=Path)
    result.add_argument("--saved-campaign-server", action="store_true", help=argparse.SUPPRESS)
    result.add_argument("--frontend-robert-bootstrap", action="store_true",
                        help="Use existing typed native stock Robert start before map readiness; no desktop input")
    result.add_argument("--frontend-fixture-start-policy", type=Path,
                        help="Bound external cold fixture inputs; separate once-only Robert Start and actual native_campaign business context")
    result.add_argument("--frontend-fixture-startup-case-contract", type=Path,
                        help="Pinned product pure proof for a sole startup option, under the original actual owner/frame gates")
    result.add_argument("--frontend-rules-plan", type=Path,
                        help="Explicit typed rule targets before stock Robert Start; independently prove closure and actual applied values")
    result.add_argument("--frontend-rules-diagnostic", action="store_true",
                        help="Only with diagnostic-only: directly open native rules and query actual choices before hold; no Apply/Start")
    result.add_argument("--frontend-rules-diagnostic-new-game", action="store_true",
                        help="Only with rules diagnostic: allow one typed New Game from proven stable main menu; no selection/Apply/Start")
    result.add_argument("--frontend-diagnostic-only", action="store_true",
                        help="Capture typed entry route/tree and hold; frontend mutations require separate explicit diagnostic flags")
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
    validate_saved_campaign_options(args)
    if args.frontend_fixture_start_policy is not None and (not args.frontend_robert_bootstrap
            or not args.fixture_profile or args.frontend_diagnostic_only or args.frontend_rules_diagnostic
            or args.frontend_rules_diagnostic_new_game or args.cold_start_checkpoint
            or args.sdk_smoke_test or args.sdk_error_smoke_test):
        raise SystemExit("--frontend-fixture-start-policy requires explicit --fixture-profile and --frontend-robert-bootstrap without diagnostic/checkpoint/SDK modes")
    if getattr(args, "frontend_fixture_startup_case_contract", None) is not None and (
            args.frontend_fixture_start_policy is None or args.saved_campaign_save is not None or args.server):
        raise SystemExit("--frontend-fixture-startup-case-contract requires an ordinary bound cold fixture policy, without saved/server modes")
    if args.frontend_rules_plan is not None and (not args.frontend_robert_bootstrap
            or args.frontend_diagnostic_only or args.frontend_rules_diagnostic
            or args.frontend_rules_diagnostic_new_game or args.cold_start_checkpoint
            or args.sdk_smoke_test or args.sdk_error_smoke_test or args.server):
        raise SystemExit("--frontend-rules-plan requires ordinary --frontend-robert-bootstrap without diagnostic, checkpoint, SDK or server modes")
    if args.frontend_rules_diagnostic_new_game and not (args.frontend_rules_diagnostic
            and args.frontend_diagnostic_only and args.frontend_robert_bootstrap):
        raise SystemExit("--frontend-rules-diagnostic-new-game requires --frontend-rules-diagnostic, --frontend-diagnostic-only and --frontend-robert-bootstrap")
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
