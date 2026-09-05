#!/usr/bin/env python3
"""Own one future source-specific war-loss CK3 lifecycle.

The async orchestration seam is deliberately dependency-injected.  This file
contains no CK3 launch, debugger attach, bridge injection, or process-kill
implementation.  Its command-line entry only verifies the frozen dependencies
and the observer's detach-without-kill source contract.

A future live adapter must implement the operations consumed by
``run_exclusive_outer_owner``.  That function keeps a single process lease,
requires the source observer to restore its breakpoint and detach without
terminating the target, attaches the bridge to the same PID, passes the exact
same driver object to the existing lifecycle continuation, and calls the one
outer cleanup hook exactly once.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any, Awaitable, Callable


RESEARCH_ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = RESEARCH_ROOT.parents[2]
PACKAGE_ROOT = REPOSITORY_ROOT / "ck3_autonomous_player" / "src"
for candidate in (RESEARCH_ROOT, PACKAGE_ROOT):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

import run_g2_source_specific_war_loss_lifecycle as lifecycle  # noqa: E402
from xar_autoplayer.bridge.raiktor_source_specific_war_loss_contract import (  # noqa: E402
    EXPECTED_EXE_SHA256,
    normalize_raiktor_source_specific_capture,
)


MANIFEST_SCHEMA = "xar.ck3.g2_source_specific_war_loss_outer_owner_manifest.v1"
PREFLIGHT_SCHEMA = "xar.ck3.g2_source_specific_war_loss_outer_owner_preflight.v1"
RUN_SCHEMA = "xar.ck3.g2_source_specific_war_loss_outer_owner_run.v1"
EXPECTED_STATUS = "GREEN_STATIC_EXCLUSIVE_OUTER_OWNER_NO_LAUNCH"
EXPECTED_EVENT = "bookmark.1071.a"


class OuterOwnerContractError(ValueError):
    """The exclusive process/observer/bridge ownership contract drifted."""


def _object(value: object, name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise OuterOwnerContractError(f"{name} must be an object")
    return value


def _positive_integer(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise OuterOwnerContractError(f"{name} must be a positive integer")
    return value


def _sha256_text(value: object, name: str) -> str:
    text = str(value).strip().upper()
    if len(text) != 64 or any(character not in "0123456789ABCDEF" for character in text):
        raise OuterOwnerContractError(f"{name} must be an uppercase SHA-256")
    return text


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _resolve(path_value: object, *, repo_root: Path) -> Path:
    path = Path(str(path_value)).expanduser()
    if not path.is_absolute():
        path = repo_root / path
    return path.resolve()


def _validate_launch_receipt(value: object) -> tuple[dict[str, object], int]:
    receipt = _object(value, "normal-event launch receipt")
    pid = _positive_integer(receipt.get("pid"), "normal-event PID")
    if (
        receipt.get("startup_mode") != "normal-event"
        or receipt.get("event_target") != EXPECTED_EVENT
        or receipt.get("exclusive_slot") is not True
        or receipt.get("cleanup_owner") != "outer-owner"
    ):
        raise OuterOwnerContractError("normal-event launch ownership drifted")
    return receipt, pid


def _validate_observer_handoff(
    value: object,
    *,
    expected_pid: int,
) -> tuple[dict[str, object], dict[str, object], str]:
    handoff = _object(value, "source-observer handoff")
    if _positive_integer(handoff.get("pid"), "observer PID") != expected_pid:
        raise OuterOwnerContractError("source observer attached to another PID")
    raw_capture = _object(handoff.get("capture"), "source capture")
    capture_sha256 = _sha256_text(
        handoff.get("capture_sha256"), "source capture SHA-256"
    )
    try:
        normalized = normalize_raiktor_source_specific_capture(
            raw_capture, capture_sha256=capture_sha256
        )
    except (TypeError, ValueError) as error:
        raise OuterOwnerContractError(
            f"observer detach-without-kill contract is NO-GO: {error}"
        ) from error
    if normalized.get("capture_pid") != expected_pid:
        raise OuterOwnerContractError("normalized source capture PID drifted")
    if (
        raw_capture.get("original_breakpoint_byte_restored") is not True
        or raw_capture.get("debugger_detached") is not True
        or raw_capture.get("process_terminated") is not False
        or raw_capture.get("attach_mode") is not True
    ):
        raise OuterOwnerContractError(
            "observer did not restore, detach, and preserve the target process"
        )
    return handoff, normalized, capture_sha256


def _validate_pause_receipt(value: object, *, expected_pid: int) -> dict[str, object]:
    receipt = _object(value, "pause receipt")
    if (
        _positive_integer(receipt.get("pid"), "paused PID") != expected_pid
        or receipt.get("paused") is not True
        or receipt.get("after_observer_detach") is not True
    ):
        raise OuterOwnerContractError("same-process post-observer pause is not proven")
    return receipt


def _validate_bridge_binding(value: object, *, expected_pid: int) -> dict[str, object]:
    binding = _object(value, "bridge binding")
    if (
        _positive_integer(binding.get("bridge_pid"), "bridge PID") != expected_pid
        or binding.get("attached") is not True
        or binding.get("explicit_target_pid") != expected_pid
    ):
        raise OuterOwnerContractError("bridge is not explicitly attached to capture PID")
    return binding


def _validate_lifecycle_result(value: object, *, expected_pid: int) -> dict[str, object]:
    result = _object(value, "lifecycle continuation result")
    normalized = _object(result.get("source_normalization"), "lifecycle source")
    handoff = _object(result.get("handoff"), "lifecycle handoff")
    joined = _object(result.get("source_specific_loss_join"), "lifecycle join")
    identity = _object(joined.get("identity"), "lifecycle join identity")
    if (
        result.get("ok") is not True
        or result.get("status") != "green"
        or normalized.get("capture_pid") != expected_pid
        or handoff.get("capture_pid") != expected_pid
        or identity.get("ck3_pid") != expected_pid
    ):
        raise OuterOwnerContractError("lifecycle continuation changed process identity")
    return result


async def run_exclusive_outer_owner(
    operations: Any,
    *,
    expected_character_id: int,
    expected_date_raw: int,
    postwar_timeout: float,
    continuation: Callable[..., Awaitable[dict[str, object]]] = (
        lifecycle.run_same_lifecycle_sequence
    ),
) -> dict[str, object]:
    """Compose one caller-supplied process owner around the lifecycle seam.

    ``operations`` supplies the future platform/live adapter.  The outer owner
    is the only caller of ``final_cleanup``; observer and lifecycle phases are
    handoffs, not process owners.
    """
    if expected_character_id <= 0 or expected_date_raw < 0 or postwar_timeout <= 0:
        raise OuterOwnerContractError("outer owner arguments are invalid")

    trace: list[str] = []
    exclusive_token: object | None = None
    launch_receipt: dict[str, object] | None = None
    driver: object | None = None
    pid: int | None = None
    cleanup_calls = 0
    lifecycle_result: dict[str, object] | None = None
    normalized_source: dict[str, object] | None = None
    bridge_binding: dict[str, object] | None = None

    try:
        exclusive_token = await operations.acquire_exclusive_launch()
        if exclusive_token is None:
            raise OuterOwnerContractError("exclusive launch slot was not acquired")
        trace.append("exclusive-slot-acquired")

        launch_value = await operations.launch_normal_event_process(exclusive_token)
        launch_receipt = _object(launch_value, "normal-event launch receipt")
        raw_pid = launch_receipt.get("pid")
        if isinstance(raw_pid, int) and not isinstance(raw_pid, bool) and raw_pid > 0:
            pid = raw_pid
        launch_receipt, pid = _validate_launch_receipt(launch_receipt)
        trace.append("normal-event-process-started")

        observer_value = await operations.capture_natural_source_event(
            launch_receipt, pid
        )
        _, normalized_source, capture_sha256 = _validate_observer_handoff(
            observer_value, expected_pid=pid
        )
        trace.extend(
            (
                "observer-breakpoint-restored",
                "observer-detached-without-kill",
            )
        )

        if await operations.is_owned_process_alive(launch_receipt, pid) is not True:
            raise OuterOwnerContractError(
                "normal-event process did not survive observer detachment"
            )
        trace.append("same-process-alive-after-observer")

        pause_value = await operations.pause_owned_process(launch_receipt, pid)
        _validate_pause_receipt(pause_value, expected_pid=pid)
        trace.append("same-process-paused")

        driver = await operations.attach_bridge_to_pid(launch_receipt, pid)
        if driver is None:
            raise OuterOwnerContractError("bridge driver was not created")
        binding_value = await operations.read_bridge_binding(driver)
        bridge_binding = _validate_bridge_binding(binding_value, expected_pid=pid)
        trace.append("bridge-attached-to-capture-pid")

        lifecycle_value = await continuation(
            driver,
            source_capture=_object(observer_value, "observer handoff")["capture"],
            capture_sha256=capture_sha256,
            expected_character_id=expected_character_id,
            expected_date_raw=expected_date_raw,
            postwar_timeout=postwar_timeout,
        )
        lifecycle_result = _validate_lifecycle_result(
            lifecycle_value, expected_pid=pid
        )
        trace.append("same-driver-lifecycle-continuation-complete")
    finally:
        try:
            if launch_receipt is not None:
                cleanup_calls += 1
                await operations.final_cleanup(launch_receipt, driver, pid)
                trace.append("outer-owner-final-cleanup")
        finally:
            if exclusive_token is not None:
                await operations.release_exclusive_launch(exclusive_token)
                trace.append("exclusive-slot-released")

    if (
        cleanup_calls != 1
        or pid is None
        or normalized_source is None
        or bridge_binding is None
        or lifecycle_result is None
    ):
        raise OuterOwnerContractError("outer owner did not complete exactly one cleanup")
    return {
        "schema": RUN_SCHEMA,
        "status": "green-orchestration",
        "process_identity": {
            "normal_event_pid": pid,
            "observer_pid": normalized_source["capture_pid"],
            "bridge_pid": bridge_binding["bridge_pid"],
            "lifecycle_pid": lifecycle_result["source_specific_loss_join"]["identity"][
                "ck3_pid"
            ],
        },
        "observer_handoff": {
            "breakpoint_restored": True,
            "debugger_detached": True,
            "process_terminated": False,
            "process_alive_after_detach": True,
        },
        "ownership": {
            "exclusive_launch_owner": "outer-owner",
            "same_driver_handoff": True,
            "final_cleanup_owner": "outer-owner",
            "final_cleanup_calls": cleanup_calls,
        },
        "stage_trace": trace,
        "lifecycle_result": lifecycle_result,
        "ok": True,
    }


def _validate_observer_source(source: str) -> dict[str, object]:
    required_tokens = (
        "DebugActiveProcess(options.attach_pid)",
        "DebugSetProcessKillOnExit(FALSE)",
        "capture.original_breakpoint_byte_restored = WriteRemoteByte(",
        "if (!process_exited && capture.attach_mode)",
        "DebugActiveProcessStop(process_info.dwProcessId)",
        "} else if (!process_exited) {",
        "capture.process_terminated = TerminateProcess(",
    )
    missing = [token for token in required_tokens if token not in source]
    if missing:
        raise OuterOwnerContractError(
            f"observer detach-without-kill source proof is missing: {missing}"
        )
    try:
        attach_branch = source.index("if (!process_exited && capture.attach_mode)")
        non_attach_branch = source.index(
            "} else if (!process_exited) {", attach_branch
        )
        detach_call = source.index("DebugActiveProcessStop(process_info.dwProcessId)")
        terminate_call = source.index(
            "capture.process_terminated = TerminateProcess(", non_attach_branch
        )
    except ValueError as error:
        raise OuterOwnerContractError(
            "observer attach/non-attach cleanup branches drifted"
        ) from error
    if not (attach_branch < detach_call < non_attach_branch < terminate_call):
        raise OuterOwnerContractError("observer attach/non-attach cleanup branches drifted")
    return {
        "kill_on_debugger_exit_disabled": True,
        "original_breakpoint_restore_present": True,
        "attach_branch_detaches": True,
        "attach_branch_terminate_process_absent": True,
        "terminate_process_confined_to_non_attach_branch": True,
    }


def run_no_launch_preflight(
    manifest_path: Path,
    output_path: Path,
    *,
    repo_root: Path = REPOSITORY_ROOT,
    process_inventory: Callable[[], object] = lifecycle.postwar._process_inventory,
) -> dict[str, object]:
    if output_path.exists():
        raise OuterOwnerContractError(f"output path already exists: {output_path}")
    manifest = _object(
        json.loads(manifest_path.read_text(encoding="utf-8-sig")), "manifest"
    )
    boundaries = _object(manifest.get("boundaries"), "manifest boundaries")
    composition = _object(manifest.get("composition"), "manifest composition")
    if (
        manifest.get("schema") != MANIFEST_SCHEMA
        or manifest.get("status") != "static-ready-no-launch"
        or manifest.get("default_off") is not True
        or manifest.get("live_authorized") is not False
        or composition.get("live_adapter_implemented") is not False
        or composition.get("standalone_capture_runner_used_as_inner_phase") is not False
        or composition.get("final_cleanup_owner") != "outer-owner"
        or any(value is not False for value in boundaries.values() if isinstance(value, bool))
    ):
        raise OuterOwnerContractError("manifest static/no-launch boundary drifted")

    paths = _object(manifest.get("paths"), "manifest paths")
    hashes = _object(manifest.get("sha256"), "manifest hashes")
    required = {
        "runner",
        "lifecycle_runner",
        "source_observer",
        "standalone_capture_runner",
        "source_provider",
        "source_contract",
        "postwar_runner",
        "terms_runner",
        "capture_executable",
        "bridge_dll",
        "bridge_injector",
        "game_executable",
        "bookmark_events",
    }
    checked: dict[str, dict[str, object]] = {}
    for name in sorted(required):
        if name not in paths or name not in hashes:
            raise OuterOwnerContractError(f"manifest dependency is missing: {name}")
        path = _resolve(paths[name], repo_root=repo_root)
        expected = _sha256_text(hashes[name], f"{name} SHA-256")
        if not path.is_file():
            raise OuterOwnerContractError(f"manifest dependency is absent: {path}")
        actual = _sha256_file(path)
        if actual != expected:
            raise OuterOwnerContractError(
                f"manifest dependency drifted: {name} {actual} != {expected}"
            )
        checked[name] = {
            "path": str(path),
            "size": path.stat().st_size,
            "sha256": actual,
        }
    if checked["game_executable"]["sha256"] != EXPECTED_EXE_SHA256:
        raise OuterOwnerContractError("game executable is not exact CK3 1.19.0.6")
    source_proof = _validate_observer_source(
        Path(str(checked["source_observer"]["path"])).read_text(encoding="utf-8")
    )

    before = copy.deepcopy(process_inventory())
    after = copy.deepcopy(process_inventory())
    if before != after:
        raise OuterOwnerContractError("process inventory changed during no-launch preflight")
    report = {
        "schema": PREFLIGHT_SCHEMA,
        "status": EXPECTED_STATUS,
        "manifest_sha256": _sha256_file(manifest_path),
        "dependencies": checked,
        "observer_source_proof": source_proof,
        "process_inventory_before": before,
        "process_inventory_after": after,
        "contract": {
            "normal_event_process_survives_observer": True,
            "same_pid_bridge_attach_required": True,
            "same_driver_lifecycle_handoff_required": True,
            "outer_owner_is_only_final_cleanup_caller": True,
        },
        "no_go": {
            "live_command_available": False,
            "reason": "No concrete exclusive launch/attach/cleanup adapter exists in this package.",
            "old_standalone_capture_runner_is_invalid_inner_phase": True,
        },
        "boundaries": {
            "ck3_started_or_attached": False,
            "fixture_or_schema_claimed_as_live": False,
            "source_specific_loss_ready": False,
            "comparison_input_ready": False,
            "decision_ready": False,
            "automatic_surrender_ready": False,
            "gen034_closed": False,
        },
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_name(output_path.name + ".tmp")
    temporary.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(temporary, output_path)
    return report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        report = run_no_launch_preflight(args.manifest, args.output)
    except (OSError, UnicodeError, json.JSONDecodeError, OuterOwnerContractError) as error:
        print(f"ERROR: {type(error).__name__}: {error}", file=sys.stderr)
        return 2
    print(
        f"{report['status']} live=false live_command_available=false "
        "source_specific_loss_ready=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
