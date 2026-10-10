"""Validate cold checkpoint anchors from an already parsed raw driver state."""

from __future__ import annotations

import copy

from .environment import EnvironmentSpec
from .errors import AgentError


def validate_cold_start_checkpoint_payload_for_pipe(
    spec: EnvironmentSpec, pipe_name: str, payload: object
) -> dict[str, object]:
    """Validate the raw anchor and actual save bytes without rereading driver state.

    The payload remains unchanged, including its complete command history.
    """
    if not isinstance(pipe_name, str) or not pipe_name:
        raise AgentError("cold checkpoint pipe name must be nonempty")
    from .native_session import (
        NATIVE_SESSION_CHECKPOINT_FILENAME,
        NATIVE_SESSION_CHECKPOINT_LOAD_NAME,
        _sha256_file,
    )

    checkpoint = payload.get("last_checkpoint") if isinstance(payload, dict) else None
    persisted_lifecycle = (
        payload.get("succession_lifecycle")
        if isinstance(payload, dict)
        else None
    )
    if (
        not isinstance(payload, dict)
        or payload.get("format_version") != 2
        or payload.get("pipe_name") != pipe_name
        or not isinstance(checkpoint, dict)
        or checkpoint.get("name") != NATIVE_SESSION_CHECKPOINT_FILENAME
    ):
        raise AgentError(
            "cold checkpoint start requires a v2 driver state for this pipe"
        )
    expected_size = checkpoint.get("size")
    expected_sha256 = checkpoint.get("sha256")
    saved_date_raw = checkpoint.get("date_raw")
    history_index = checkpoint.get("history_index")
    character_id = payload.get("episode_character_id")
    run_id = payload.get("episode_run_id")
    history = payload.get("command_history")
    if (
        isinstance(expected_size, bool)
        or not isinstance(expected_size, int)
        or expected_size <= 0
        or not isinstance(expected_sha256, str)
        or len(expected_sha256) != 64
        or any(character not in "0123456789abcdef" for character in expected_sha256)
        or isinstance(saved_date_raw, bool)
        or not isinstance(saved_date_raw, int)
        or isinstance(history_index, bool)
        or not isinstance(history_index, int)
        or history_index < 1
        or isinstance(character_id, bool)
        or not isinstance(character_id, int)
        or not isinstance(run_id, str)
        or not run_id
        or not isinstance(history, list)
        or history_index > len(history)
        or checkpoint.get("episode_character_id") != character_id
        or checkpoint.get("episode_run_id") != run_id
    ):
        raise AgentError("cold checkpoint state has an incomplete checkpoint anchor")
    anchor = history[history_index - 1]
    result = anchor.get("result") if isinstance(anchor, dict) else None
    saved = result.get("checkpoint") if isinstance(result, dict) else None
    if (
        not isinstance(anchor, dict)
        or anchor.get("index") != history_index
        or anchor.get("command") != "save-checkpoint"
        or anchor.get("ok") is not True
        or not isinstance(saved, dict)
        or saved.get("size") != expected_size
        or saved.get("sha256") != expected_sha256
        or saved.get("date_raw") != saved_date_raw
    ):
        raise AgentError("cold checkpoint history anchor does not match the save")
    checkpoint_lifecycle = checkpoint.get("succession_lifecycle")
    saved_lifecycle = saved.get("succession_lifecycle")
    if any(
        value is not None
        for value in (
            persisted_lifecycle,
            checkpoint_lifecycle,
            saved_lifecycle,
        )
    ) and not (
        isinstance(persisted_lifecycle, dict)
        and checkpoint_lifecycle == persisted_lifecycle
        and saved_lifecycle == persisted_lifecycle
    ):
        raise AgentError(
            "cold checkpoint succession lifecycle anchor is incomplete"
        )
    checkpoint_path = (
        spec.profile_dir / "save games" / NATIVE_SESSION_CHECKPOINT_FILENAME
    )
    try:
        size = checkpoint_path.stat().st_size
    except OSError as error:
        raise AgentError(
            f"cold checkpoint is unavailable: {checkpoint_path}: {error}"
        ) from error
    digest = _sha256_file(checkpoint_path)
    if size != expected_size or digest != expected_sha256:
        raise AgentError("cold checkpoint bytes differ from the v2 driver state")
    return {
        "name": NATIVE_SESSION_CHECKPOINT_FILENAME,
        "load_save_name": NATIVE_SESSION_CHECKPOINT_LOAD_NAME,
        "path": str(checkpoint_path.resolve()),
        "size": size,
        "sha256": digest,
        "saved_date_raw": saved_date_raw,
        "history_index": history_index,
        "succession_lifecycle": copy.deepcopy(persisted_lifecycle),
    }
