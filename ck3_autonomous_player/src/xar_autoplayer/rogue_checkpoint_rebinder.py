"""Rebind one copied rogue one-life checkpoint to a prepared environment.

The CK3 save is opaque and must remain byte-for-byte unchanged.  Only the
three succession-lifecycle anchors persisted in driver-state v2 are replaced.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Callable, ContextManager

from .bridge.native_driver import load_native_driver_state_for_resume
from .bridge.succession_transition_contract import (
    ROGUE_ONE_LIFE,
    bind_succession_lifecycle_from_environment_v1,
    legacy_rogue_one_life_binding_v1,
    normalize_succession_lifecycle_binding_v1,
)
from .environment import (
    EnvironmentSpec,
    ck3_process_inventory,
    ensure_state_path_safe,
    sha256_file,
    verify_profile,
    write_bytes_atomic,
    write_json_atomic,
)
from .errors import AgentError
from .locking import exclusive_state_lock
from .native_session import (
    NATIVE_DRIVER_STATE_FILENAME,
    NATIVE_SESSION_CHECKPOINT_FILENAME,
    NATIVE_SESSION_QUEUE_DIRNAME,
    validate_cold_start_checkpoint_for_pipe,
)
from .runtime import validate_native_bridge_pipe_name


ROGUE_CHECKPOINT_REBIND_V1_SCHEMA = "xar.ck3.rogue-checkpoint-rebind/v1"
_ROGUE_PACT_CONTRACT = "terminal_settlement_required"
_PREPARED_ENVIRONMENT_SOURCE = "prepared-environment-manifest"


def _load_json_object(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AgentError(
            f"rogue checkpoint driver state is unreadable: {path}: {error}"
        ) from error
    if not isinstance(payload, dict):
        raise AgentError("rogue checkpoint driver state must be a JSON object")
    return payload


def _rogue_binding(value: object, label: str) -> dict[str, object]:
    try:
        binding = normalize_succession_lifecycle_binding_v1(value)
    except ValueError as error:
        raise AgentError(f"{label} is malformed: {error}") from error
    if (
        binding.get("lifecycle") != ROGUE_ONE_LIFE
        or binding.get("xar_enabled") != "xar_on"
        or binding.get("pact_contract") != _ROGUE_PACT_CONTRACT
    ):
        raise AgentError(f"{label} is not the frozen rogue xar_on profile")

    source = binding.get("source")
    if source == legacy_rogue_one_life_binding_v1()["source"]:
        if binding != legacy_rogue_one_life_binding_v1():
            raise AgentError(f"{label} is not the exact legacy rogue binding")
    elif source == _PREPARED_ENVIRONMENT_SOURCE:
        if binding.get("environment_sha256") is None:
            raise AgentError(f"{label} lacks its prepared environment digest")
    else:
        raise AgentError(f"{label} uses an unsupported rogue binding source")
    return binding


def _source_lifecycle_anchors(
    payload: dict[str, object],
) -> tuple[dict[str, object], dict[str, object]]:
    """Return the checkpoint and one consistent, contract-issued binding."""

    if payload.get("format_version") != 2:
        raise AgentError("rogue checkpoint rebind requires driver-state v2")
    checkpoint = payload.get("last_checkpoint")
    history = payload.get("command_history")
    if not isinstance(checkpoint, dict) or not isinstance(history, list):
        raise AgentError("rogue checkpoint driver lacks checkpoint history")
    history_index = checkpoint.get("history_index")
    if (
        isinstance(history_index, bool)
        or not isinstance(history_index, int)
        or history_index < 1
        or history_index > len(history)
    ):
        raise AgentError("rogue checkpoint history index is malformed")
    anchor = history[history_index - 1]
    result = anchor.get("result") if isinstance(anchor, dict) else None
    saved = result.get("checkpoint") if isinstance(result, dict) else None
    if (
        not isinstance(anchor, dict)
        or anchor.get("index") != history_index
        or anchor.get("command") != "save-checkpoint"
        or anchor.get("ok") is not True
        or not isinstance(saved, dict)
    ):
        raise AgentError(
            "rogue checkpoint history anchor is not its matching save-checkpoint"
        )

    top_binding = _rogue_binding(
        payload.get("succession_lifecycle"), "driver lifecycle binding"
    )
    checkpoint_binding = _rogue_binding(
        checkpoint.get("succession_lifecycle"),
        "last-checkpoint lifecycle binding",
    )
    anchor_binding = _rogue_binding(
        saved.get("succession_lifecycle"),
        "history-anchor lifecycle binding",
    )
    if not (top_binding == checkpoint_binding == anchor_binding):
        raise AgentError("rogue checkpoint lifecycle anchors are mixed")
    return checkpoint, top_binding


def _zero_ck3_inventory() -> dict[str, object]:
    inventory = ck3_process_inventory()
    processes = inventory.get("processes")
    if not isinstance(processes, list):
        raise AgentError("CK3 process inventory is malformed")
    if processes:
        raise AgentError(
            "rogue checkpoint rebind requires zero running ck3.exe processes; "
            f"observed {len(processes)}"
        )
    return inventory


def _assert_save_anchor(
    save_path: Path, checkpoint: dict[str, object]
) -> dict[str, object]:
    if checkpoint.get("name") != NATIVE_SESSION_CHECKPOINT_FILENAME:
        raise AgentError("rogue checkpoint name is not canonical")
    expected_size = checkpoint.get("size")
    expected_sha256 = checkpoint.get("sha256")
    try:
        size = save_path.stat().st_size
        digest = sha256_file(save_path)
    except OSError as error:
        raise AgentError(
            f"rogue checkpoint save is unavailable: {save_path}: {error}"
        ) from error
    if (
        isinstance(expected_size, bool)
        or not isinstance(expected_size, int)
        or expected_size <= 0
        or not isinstance(expected_sha256, str)
        or len(expected_sha256) != 64
        or any(character not in "0123456789abcdef" for character in expected_sha256)
        or size != expected_size
        or digest != expected_sha256
    ):
        raise AgentError("rogue checkpoint save bytes differ from driver state")
    return {"path": str(save_path.resolve()), "size": size, "sha256": digest}


def _replace_lifecycle_anchors(
    payload: dict[str, object], binding: dict[str, object]
) -> dict[str, object]:
    rebound = copy.deepcopy(payload)
    checkpoint = rebound["last_checkpoint"]
    assert isinstance(checkpoint, dict)
    history = rebound["command_history"]
    assert isinstance(history, list)
    history_index = checkpoint["history_index"]
    assert isinstance(history_index, int)
    anchor = history[history_index - 1]
    assert isinstance(anchor, dict)
    result = anchor["result"]
    assert isinstance(result, dict)
    saved = result["checkpoint"]
    assert isinstance(saved, dict)
    rebound["succession_lifecycle"] = copy.deepcopy(binding)
    checkpoint["succession_lifecycle"] = copy.deepcopy(binding)
    saved["succession_lifecycle"] = copy.deepcopy(binding)
    return rebound


def rebind_rogue_checkpoint_v1(
    spec: EnvironmentSpec,
    *,
    expected_pipe_name: str | None = None,
    lock_factory: Callable[[Path, str], ContextManager[None]] = (
        exclusive_state_lock
    ),
) -> dict[str, object]:
    """Rebind a copied rogue checkpoint without launching or touching CK3."""

    ensure_state_path_safe(spec.state_dir)
    driver_path = (
        spec.state_dir
        / NATIVE_SESSION_QUEUE_DIRNAME
        / NATIVE_DRIVER_STATE_FILENAME
    ).resolve()
    save_path = (
        spec.profile_dir / "save games" / NATIVE_SESSION_CHECKPOINT_FILENAME
    ).resolve()

    with lock_factory(spec.state_dir, "rogue-checkpoint-rebind-v1"):
        inventory = _zero_ck3_inventory()
        manifest = verify_profile(spec, xar_enabled="xar_on")
        try:
            target_binding = bind_succession_lifecycle_from_environment_v1(
                manifest,
                lifecycle=ROGUE_ONE_LIFE,
            )
        except ValueError as error:
            raise AgentError(
                f"target prepared manifest is not rogue xar_on: {error}"
            ) from error

        try:
            source_bytes = driver_path.read_bytes()
            source_sha256 = sha256_file(driver_path)
        except OSError as error:
            raise AgentError(
                f"rogue checkpoint driver state is unavailable: {error}"
            ) from error
        source = _load_json_object(driver_path)
        checkpoint, source_binding = _source_lifecycle_anchors(source)
        pipe_name = source.get("pipe_name")
        if not isinstance(pipe_name, str) or not pipe_name:
            raise AgentError("rogue checkpoint driver pipe is malformed")
        validate_native_bridge_pipe_name(pipe_name)
        if expected_pipe_name is not None and pipe_name != expected_pipe_name:
            raise AgentError(
                "rogue checkpoint driver pipe differs from the requested pipe"
            )

        try:
            consumer_before = load_native_driver_state_for_resume(
                driver_path, pipe_name
            )
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
            raise AgentError(
                f"rogue checkpoint driver is not consumer-compatible: {error}"
            ) from error
        if consumer_before is None:
            raise AgentError("rogue checkpoint driver is not consumer-compatible")
        save_before = _assert_save_anchor(save_path, checkpoint)
        validate_cold_start_checkpoint_for_pipe(spec, pipe_name)

        rebound = _replace_lifecycle_anchors(source, target_binding)
        try:
            write_json_atomic(driver_path, rebound)
            consumer_after = load_native_driver_state_for_resume(
                driver_path, pipe_name
            )
            if consumer_after is None:
                raise AgentError(
                    "rebound rogue checkpoint is not consumer-compatible"
                )
            checkpoint_after = validate_cold_start_checkpoint_for_pipe(
                spec, pipe_name
            )
            save_after = _assert_save_anchor(
                save_path, rebound["last_checkpoint"]
            )
            if save_after != save_before:
                raise AgentError(
                    "rogue checkpoint save bytes changed during rebind"
                )
            if consumer_after.get("succession_lifecycle") != target_binding:
                raise AgentError(
                    "consumer did not retain the rebound lifecycle binding"
                )
        except Exception:
            write_bytes_atomic(driver_path, source_bytes)
            raise

        target_sha256 = sha256_file(driver_path)
        return {
            "schema": ROGUE_CHECKPOINT_REBIND_V1_SCHEMA,
            "status": "rebound",
            "ok": True,
            "ck3_launch_attempted": False,
            "desktop_interaction": False,
            "state_dir": str(spec.state_dir.resolve()),
            "profile_dir": str(spec.profile_dir.resolve()),
            "pipe_name": pipe_name,
            "process_inventory": inventory,
            "environment": {
                "source_sha256": source_binding["environment_sha256"],
                "target_sha256": target_binding["environment_sha256"],
            },
            "driver_state": {
                "path": str(driver_path),
                "source_sha256": source_sha256,
                "target_sha256": target_sha256,
                "format_version": 2,
                "rewritten_paths": [
                    "succession_lifecycle",
                    "last_checkpoint.succession_lifecycle",
                    (
                        "command_history[last_checkpoint.history_index-1]."
                        "result.checkpoint.succession_lifecycle"
                    ),
                ],
            },
            "save": {
                "source": save_before,
                "target": save_after,
                "bytes_unchanged": True,
            },
            "post_rebind_validation": {
                "native_driver_consumer": "passed",
                "cold_checkpoint_validator": "passed",
                "checkpoint": checkpoint_after,
            },
            "no_launch_preflight_expectations": {
                "pipe_name": pipe_name,
                "expected_character_id": consumer_after.get(
                    "episode_character_id"
                ),
                "expected_episode_run_id": consumer_after.get(
                    "episode_run_id"
                ),
                "expected_checkpoint_sha256": save_after["sha256"],
                "expected_driver_state_sha256": target_sha256,
                "xar_enabled": "xar_on",
                "succession_lifecycle": ROGUE_ONE_LIFE,
            },
        }
