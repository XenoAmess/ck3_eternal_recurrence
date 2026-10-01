"""Migrate a copied v2 checkpoint to its newly prepared environment.

Only the environment digest in the three existing lifecycle anchors changes.
The save, episode, command history, lifecycle semantics and campaign goal are
retained. This file operation never discovers or contacts a CK3 process.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys

from .bridge.native_driver import load_native_driver_state_for_resume
from .bridge.succession_transition_contract import (
    ORDINARY_CAMPAIGN_SUCCESSION,
    bind_succession_lifecycle_from_environment_v1,
    normalize_succession_lifecycle_binding_v1,
)
from .environment import (
    EnvironmentSpec,
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
from .ordinary_seed_rebinder import (
    _assert_save_anchor,
    _load_json_object,
    _replace_lifecycle_anchors,
)
from .runtime import validate_native_bridge_pipe_name


CHECKPOINT_ENVIRONMENT_REBIND_V1_SCHEMA = (
    "xar.ck3.checkpoint-environment-rebind/v1"
)


def _checkpoint_binding(payload: dict[str, object]) -> dict[str, object]:
    if payload.get("format_version") != 2:
        raise AgentError("checkpoint environment rebind requires driver-state v2")
    checkpoint = payload.get("last_checkpoint")
    history = payload.get("command_history")
    if not isinstance(checkpoint, dict) or not isinstance(history, list):
        raise AgentError("checkpoint environment rebind lacks checkpoint history")
    index = checkpoint.get("history_index")
    if isinstance(index, bool) or not isinstance(index, int) or not 1 <= index <= len(history):
        raise AgentError("checkpoint environment rebind history index is malformed")
    anchor = history[index - 1]
    result = anchor.get("result") if isinstance(anchor, dict) else None
    saved = result.get("checkpoint") if isinstance(result, dict) else None
    if (
        not isinstance(anchor, dict)
        or anchor.get("index") != index
        or anchor.get("command") != "save-checkpoint"
        or anchor.get("ok") is not True
        or not isinstance(saved, dict)
    ):
        raise AgentError("checkpoint environment rebind history anchor is not its save")
    try:
        bindings = [
            normalize_succession_lifecycle_binding_v1(value)
            for value in (
                payload.get("succession_lifecycle"),
                checkpoint.get("succession_lifecycle"),
                saved.get("succession_lifecycle"),
            )
        ]
    except ValueError as error:
        raise AgentError(f"checkpoint lifecycle binding is malformed: {error}") from error
    if not bindings[0] == bindings[1] == bindings[2]:
        raise AgentError("checkpoint lifecycle anchors are mixed")
    return bindings[0]


def rebind_checkpoint_environment_v1(
    spec: EnvironmentSpec,
    *,
    expected_source_environment_sha256: str,
    expected_pipe_name: str,
) -> dict[str, object]:
    """Rebind a copied checkpoint under the target's existing state lock.

    The target profile must already be prepared. Its ordinary/rogue rule and
    pact semantics must match the source; this does not reclassify a campaign.
    The existing no-launch preflight still applies after this file migration.
    """
    ensure_state_path_safe(spec.state_dir)
    validate_native_bridge_pipe_name(expected_pipe_name)
    driver_path = (
        spec.state_dir / NATIVE_SESSION_QUEUE_DIRNAME / NATIVE_DRIVER_STATE_FILENAME
    ).resolve()
    save_path = (
        spec.profile_dir / "save games" / NATIVE_SESSION_CHECKPOINT_FILENAME
    ).resolve()
    with exclusive_state_lock(spec.state_dir, "checkpoint-environment-rebind-v1"):
        source_bytes = driver_path.read_bytes()
        source_sha256 = sha256_file(driver_path)
        source = _load_json_object(driver_path, "checkpoint driver state")
        source_binding = _checkpoint_binding(source)
        if source_binding["environment_sha256"] != expected_source_environment_sha256:
            raise AgentError("checkpoint source environment differs from requested migration")
        if source.get("pipe_name") != expected_pipe_name:
            raise AgentError("checkpoint driver pipe differs from requested migration")
        manifest = verify_profile(spec, xar_enabled=source_binding["xar_enabled"])
        try:
            target_binding = bind_succession_lifecycle_from_environment_v1(
                manifest,
                lifecycle=source_binding["lifecycle"],
                ordinary_campaign_no_pact=(
                    source_binding["lifecycle"] == ORDINARY_CAMPAIGN_SUCCESSION
                ),
            )
        except ValueError as error:
            raise AgentError(f"target lifecycle profile differs from source: {error}") from error
        expected_binding = copy.deepcopy(source_binding)
        expected_binding["environment_sha256"] = target_binding["environment_sha256"]
        if target_binding != expected_binding:
            raise AgentError("checkpoint migration would change lifecycle semantics")
        consumer_before = load_native_driver_state_for_resume(driver_path, expected_pipe_name)
        if consumer_before is None:
            raise AgentError("checkpoint driver is not consumer-compatible")
        validate_cold_start_checkpoint_for_pipe(spec, expected_pipe_name)
        save_before = _assert_save_anchor(save_path, source["last_checkpoint"])
        rebound = _replace_lifecycle_anchors(source, target_binding)
        try:
            write_json_atomic(driver_path, rebound)
            consumer_after = load_native_driver_state_for_resume(driver_path, expected_pipe_name)
            if consumer_after is None or consumer_after["succession_lifecycle"] != target_binding:
                raise AgentError("rebound checkpoint is not consumer-compatible")
            checkpoint_after = validate_cold_start_checkpoint_for_pipe(spec, expected_pipe_name)
            save_after = _assert_save_anchor(save_path, rebound["last_checkpoint"])
            if save_after != save_before:
                raise AgentError("checkpoint save bytes changed during environment migration")
        except Exception:
            write_bytes_atomic(driver_path, source_bytes)
            raise
        target_sha256 = sha256_file(driver_path)
        return {
            "schema": CHECKPOINT_ENVIRONMENT_REBIND_V1_SCHEMA,
            "status": "rebound",
            "ok": True,
            "ck3_launch_attempted": False,
            "desktop_interaction": False,
            "ck3_process_access": False,
            "state_dir": str(spec.state_dir.resolve()),
            "profile_dir": str(spec.profile_dir.resolve()),
            "pipe_name": expected_pipe_name,
            "environment": {
                "source_sha256": source_binding["environment_sha256"],
                "target_sha256": target_binding["environment_sha256"],
            },
            "driver_state": {
                "path": str(driver_path),
                "source_sha256": source_sha256,
                "target_sha256": target_sha256,
                "target_size": driver_path.stat().st_size,
                "format_version": 2,
                "rewritten_paths": [
                    "succession_lifecycle.environment_sha256",
                    "last_checkpoint.succession_lifecycle.environment_sha256",
                    "command_history[last_checkpoint.history_index-1].result.checkpoint.succession_lifecycle.environment_sha256",
                ],
            },
            "save": {"source": save_before, "target": save_after, "bytes_unchanged": True},
            "lifecycle": target_binding,
            "post_rebind_validation": {
                "native_driver_consumer": "passed",
                "cold_checkpoint_validator": "passed",
                "checkpoint": checkpoint_after,
            },
            "no_launch_preflight_expectations": {
                "pipe_name": expected_pipe_name,
                "expected_character_id": consumer_after["episode_character_id"],
                "expected_episode_run_id": consumer_after["episode_run_id"],
                "expected_checkpoint_sha256": save_after["sha256"],
                "expected_driver_state_sha256": target_sha256,
                "xar_enabled": target_binding["xar_enabled"],
                "succession_lifecycle": target_binding["lifecycle"],
                "ordinary_campaign_no_pact": target_binding["lifecycle"] == ORDINARY_CAMPAIGN_SUCCESSION,
            },
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", type=Path, required=True)
    parser.add_argument("--game-dir", type=Path, required=True)
    parser.add_argument("--expected-source-environment-sha256", required=True)
    parser.add_argument("--expected-pipe", required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        receipt = rebind_checkpoint_environment_v1(
            make_spec(args.state_dir, args.game_dir),
            expected_source_environment_sha256=args.expected_source_environment_sha256,
            expected_pipe_name=args.expected_pipe,
        )
        write_json_atomic(args.receipt.resolve(), receipt)
        print(json.dumps(receipt, ensure_ascii=False, indent=2))
        return 0
    except Exception as error:
        print(f"ERROR: {type(error).__name__}: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
