"""Rebind one ordinary ``xar_off`` checkpoint to a prepared environment.

The CK3 save is an opaque artifact.  Moving a seed to another prepared state
directory changes the environment digest, so only the three persisted
succession-lifecycle anchors in driver-state v2 are rewritten.  The save is
never parsed or modified.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys
from typing import Callable, ContextManager

from .bridge.native_driver import load_native_driver_state_for_resume
from .bridge.succession_transition_contract import (
    ORDINARY_CAMPAIGN_SUCCESSION,
    bind_succession_lifecycle_from_environment_v1,
    normalize_succession_lifecycle_binding_v1,
)
from .environment import (
    EnvironmentSpec,
    ck3_process_inventory,
    ensure_state_path_safe,
    make_spec,
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


ORDINARY_SEED_REBIND_V1_SCHEMA = "xar.ck3.ordinary-seed-rebind/v1"
_ORDINARY_PACT_CONTRACT = "absent_by_fresh_campaign_xar_off_contract"


def _load_json_object(path: Path, label: str) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AgentError(f"{label} is unreadable: {path}: {error}") from error
    if not isinstance(payload, dict):
        raise AgentError(f"{label} must be a JSON object")
    return payload


def _ordinary_binding(value: object, label: str) -> dict[str, object]:
    try:
        binding = normalize_succession_lifecycle_binding_v1(value)
    except ValueError as error:
        raise AgentError(f"{label} is malformed: {error}") from error
    if (
        binding.get("lifecycle") != ORDINARY_CAMPAIGN_SUCCESSION
        or binding.get("xar_enabled") != "xar_off"
        or binding.get("pact_contract") != _ORDINARY_PACT_CONTRACT
    ):
        raise AgentError(
            f"{label} is not the frozen ordinary xar_off/no-pact profile"
        )
    return binding


def _source_lifecycle_anchors(
    payload: dict[str, object],
) -> tuple[
    dict[str, object],
    dict[str, object],
    dict[str, object],
    dict[str, object],
]:
    """Return the exact three v2 lifecycle anchors or fail closed."""

    if payload.get("format_version") != 2:
        raise AgentError("ordinary seed rebind requires driver-state v2")
    checkpoint = payload.get("last_checkpoint")
    history = payload.get("command_history")
    if not isinstance(checkpoint, dict) or not isinstance(history, list):
        raise AgentError("ordinary seed driver lacks checkpoint history")
    history_index = checkpoint.get("history_index")
    if (
        isinstance(history_index, bool)
        or not isinstance(history_index, int)
        or history_index < 1
        or history_index > len(history)
    ):
        raise AgentError("ordinary seed checkpoint history index is malformed")
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
            "ordinary seed history anchor is not its matching save-checkpoint"
        )

    top_binding = _ordinary_binding(
        payload.get("succession_lifecycle"), "driver lifecycle binding"
    )
    checkpoint_binding = _ordinary_binding(
        checkpoint.get("succession_lifecycle"),
        "last-checkpoint lifecycle binding",
    )
    anchor_binding = _ordinary_binding(
        saved.get("succession_lifecycle"),
        "history-anchor lifecycle binding",
    )
    if not (top_binding == checkpoint_binding == anchor_binding):
        raise AgentError("ordinary seed lifecycle anchors are mixed")
    return checkpoint, anchor, saved, top_binding


def _zero_ck3_inventory() -> dict[str, object]:
    inventory = ck3_process_inventory()
    processes = inventory.get("processes")
    if not isinstance(processes, list):
        raise AgentError("CK3 process inventory is malformed")
    if processes:
        raise AgentError(
            "ordinary seed rebind requires zero running ck3.exe processes; "
            f"observed {len(processes)}"
        )
    return inventory


def _assert_save_anchor(
    save_path: Path, checkpoint: dict[str, object]
) -> dict[str, object]:
    if checkpoint.get("name") != NATIVE_SESSION_CHECKPOINT_FILENAME:
        raise AgentError("ordinary seed checkpoint name is not canonical")
    expected_size = checkpoint.get("size")
    expected_sha256 = checkpoint.get("sha256")
    try:
        size = save_path.stat().st_size
        digest = sha256_file(save_path)
    except OSError as error:
        raise AgentError(
            f"ordinary seed checkpoint is unavailable: {save_path}: {error}"
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
        raise AgentError("ordinary seed save bytes differ from driver state")
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


def rebind_ordinary_seed_v1(
    spec: EnvironmentSpec,
    *,
    expected_pipe_name: str | None = None,
    lock_factory: Callable[[Path, str], ContextManager[None]] = (
        exclusive_state_lock
    ),
) -> dict[str, object]:
    """Rebind the in-place ordinary seed and return a portable receipt.

    ``spec`` must already be a freshly prepared ``xar_off`` environment with
    the copied ``xar_checkpoint.ck3`` and v2 ``driver-state.json`` in their
    canonical locations.  The driver pipe is retained; callers may supply
    ``expected_pipe_name`` as an additional assertion.
    """

    ensure_state_path_safe(spec.state_dir)
    driver_path = (
        spec.state_dir
        / NATIVE_SESSION_QUEUE_DIRNAME
        / NATIVE_DRIVER_STATE_FILENAME
    ).resolve()
    save_path = (
        spec.profile_dir / "save games" / NATIVE_SESSION_CHECKPOINT_FILENAME
    ).resolve()

    with lock_factory(spec.state_dir, "ordinary-seed-rebind-v1"):
        inventory = _zero_ck3_inventory()
        manifest = verify_profile(spec, xar_enabled="xar_off")
        try:
            target_binding = bind_succession_lifecycle_from_environment_v1(
                manifest,
                lifecycle=ORDINARY_CAMPAIGN_SUCCESSION,
                ordinary_campaign_no_pact=True,
            )
        except ValueError as error:
            raise AgentError(
                f"target prepared manifest is not ordinary xar_off: {error}"
            ) from error

        source_bytes = driver_path.read_bytes()
        source_sha256 = sha256_file(driver_path)
        source = _load_json_object(driver_path, "ordinary seed driver state")
        checkpoint, _anchor, _saved, source_binding = (
            _source_lifecycle_anchors(source)
        )
        pipe_name = source.get("pipe_name")
        if not isinstance(pipe_name, str) or not pipe_name:
            raise AgentError("ordinary seed driver pipe is malformed")
        validate_native_bridge_pipe_name(pipe_name)
        if expected_pipe_name is not None and pipe_name != expected_pipe_name:
            raise AgentError(
                "ordinary seed driver pipe differs from the requested pipe"
            )

        try:
            consumer_before = load_native_driver_state_for_resume(
                driver_path, pipe_name
            )
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
            raise AgentError(
                f"ordinary seed driver is not consumer-compatible: {error}"
            ) from error
        if consumer_before is None:
            raise AgentError("ordinary seed driver is not consumer-compatible")
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
                    "rebound ordinary seed is not consumer-compatible"
                )
            checkpoint_after = validate_cold_start_checkpoint_for_pipe(
                spec, pipe_name
            )
            save_after = _assert_save_anchor(
                save_path, rebound["last_checkpoint"]
            )
            if save_after != save_before:
                raise AgentError("ordinary seed save bytes changed during rebind")
            if consumer_after.get("succession_lifecycle") != target_binding:
                raise AgentError(
                    "consumer did not retain the rebound lifecycle binding"
                )
        except Exception:
            write_bytes_atomic(driver_path, source_bytes)
            raise

        target_sha256 = sha256_file(driver_path)
        return {
            "schema": ORDINARY_SEED_REBIND_V1_SCHEMA,
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
                "xar_enabled": "xar_off",
                "succession_lifecycle": ORDINARY_CAMPAIGN_SUCCESSION,
                "ordinary_campaign_no_pact": True,
            },
        }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Rebind one copied ordinary xar_off checkpoint to its prepared "
            "target environment without launching CK3."
        )
    )
    parser.add_argument("--state-dir", type=Path, required=True)
    parser.add_argument("--game-dir", type=Path, required=True)
    parser.add_argument("--expected-pipe")
    parser.add_argument("--receipt", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        receipt = rebind_ordinary_seed_v1(
            make_spec(arguments.state_dir, arguments.game_dir),
            expected_pipe_name=arguments.expected_pipe,
        )
        if arguments.receipt is not None:
            write_json_atomic(arguments.receipt.resolve(), receipt)
        print(json.dumps(receipt, ensure_ascii=False, indent=2))
        return 0
    except Exception as error:
        print(f"ERROR: {type(error).__name__}: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
