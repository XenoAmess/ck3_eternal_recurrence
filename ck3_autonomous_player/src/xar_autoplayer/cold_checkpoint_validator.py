"""Validate cold checkpoint anchors from an already parsed raw driver state."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Protocol, TypedDict

from .errors import AgentError
from .bridge.succession_transition_contract import (
    normalize_succession_lifecycle_binding_v1,
)


class ColdCheckpointEnvironment(Protocol):
    @property
    def profile_dir(self) -> Path: ...


class ColdCheckpointAnchorV1(TypedDict):
    name: str
    load_save_name: str
    path: str
    size: int
    sha256: str
    saved_date_raw: int
    history_index: int
    succession_lifecycle: dict[str, object] | None


def _object(value: object) -> dict[str, object] | None:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        return None
    return {key: item for key, item in value.items()}


def _same_integer(value: object, expected: int) -> bool:
    return type(value) is int and value == expected


def validate_cold_start_checkpoint_payload_for_pipe(
    spec: ColdCheckpointEnvironment, pipe_name: str, payload: object
) -> ColdCheckpointAnchorV1:
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

    document = _object(payload)
    checkpoint = _object(document.get("last_checkpoint")) if document is not None else None
    persisted_lifecycle = document.get("succession_lifecycle") if document is not None else None
    if (
        document is None
        or not _same_integer(document.get("format_version"), 2)
        or document.get("pipe_name") != pipe_name
        or checkpoint is None
        or checkpoint.get("name") != NATIVE_SESSION_CHECKPOINT_FILENAME
    ):
        raise AgentError(
            "cold checkpoint start requires a v2 driver state for this pipe"
        )
    expected_size = checkpoint.get("size")
    expected_sha256 = checkpoint.get("sha256")
    saved_date_raw = checkpoint.get("date_raw")
    history_index = checkpoint.get("history_index")
    character_id = document.get("episode_character_id")
    run_id = document.get("episode_run_id")
    history = document.get("command_history")
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
        or not _same_integer(checkpoint.get("episode_character_id"), character_id)
        or checkpoint.get("episode_run_id") != run_id
    ):
        raise AgentError("cold checkpoint state has an incomplete checkpoint anchor")
    anchor = _object(history[history_index - 1])
    result = _object(anchor.get("result")) if anchor is not None else None
    saved = _object(result.get("checkpoint")) if result is not None else None
    if (
        anchor is None
        or not _same_integer(anchor.get("index"), history_index)
        or anchor.get("command") != "save-checkpoint"
        or anchor.get("ok") is not True
        or saved is None
        or not _same_integer(saved.get("size"), expected_size)
        or saved.get("sha256") != expected_sha256
        or not _same_integer(saved.get("date_raw"), saved_date_raw)
    ):
        raise AgentError("cold checkpoint history anchor does not match the save")
    checkpoint_lifecycle = checkpoint.get("succession_lifecycle")
    saved_lifecycle = saved.get("succession_lifecycle")
    normalized_lifecycle: dict[str, object] | None = None
    lifecycle_values = (persisted_lifecycle, checkpoint_lifecycle, saved_lifecycle)
    if "succession_lifecycle" in document or any(
        value is not None
        for value in lifecycle_values
    ):
        try:
            normalized = [normalize_succession_lifecycle_binding_v1(value)
                          for value in lifecycle_values]
            if normalized[0] != normalized[1] or normalized[0] != normalized[2]:
                raise ValueError("succession lifecycle sources differ")
            normalized_lifecycle = _object(normalized[0])
            if normalized_lifecycle is None:
                raise ValueError("succession lifecycle is not an object")
        except ValueError as error:
            raise AgentError(
                "cold checkpoint succession lifecycle anchor is incomplete"
            ) from error
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
    if size != expected_size or not isinstance(digest, str) or digest != expected_sha256:
        raise AgentError("cold checkpoint bytes differ from the v2 driver state")
    return {
        "name": NATIVE_SESSION_CHECKPOINT_FILENAME,
        "load_save_name": NATIVE_SESSION_CHECKPOINT_LOAD_NAME,
        "path": str(checkpoint_path.resolve()),
        "size": size,
        "sha256": digest,
        "saved_date_raw": saved_date_raw,
        "history_index": history_index,
        "succession_lifecycle": copy.deepcopy(normalized_lifecycle),
    }
