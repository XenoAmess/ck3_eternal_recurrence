#!/usr/bin/env python3
"""Materialize one durable save at a strict unexpected-event boundary.

The promotion production entry has already paused and queried the unexpected
modal before this helper is called.  This module rebinds that exact frame,
uses CK3's native ``save-checkpoint`` command, verifies the resulting bytes,
and proves that the same modal remains paused afterwards.  Failure is returned
as evidence instead of raised so a healthy retained session is never stopped
merely because its durable fallback could not be created.
"""

from __future__ import annotations

import copy
import hashlib
from collections.abc import Mapping
from pathlib import Path
import re
from typing import Protocol

from xar_autoplayer.environment import write_json_atomic


CHECKPOINT_FILENAME = "xar_checkpoint.ck3"
SAVE_CHECKPOINT_CAPABILITY = "game.command.save-checkpoint"
SAVE_CHECKPOINT_STEP = "save-checkpoint"
_SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")
_SAME_FRAME_FIELDS = (
    "snapshot_id",
    "revision",
    "native_revision",
    "date_raw",
    "bridge_pid",
    "connection_generation",
    "player_character_id",
    "event_instance_id",
    "event_option_count",
)
_SAME_MODAL_FIELDS = tuple(
    name
    for name in _SAME_FRAME_FIELDS
    if name not in {"snapshot_id", "revision", "native_revision"}
)


class UnexpectedEventCheckpointService(Protocol):
    def capabilities(self) -> dict[str, object]: ...

    def snapshot(self) -> dict[str, object]: ...

    def save_checkpoint(self, *, expected_revision: int) -> dict[str, object]: ...


def _positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _nonnegative_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _snapshot_binding(
    value: object, capabilities: Mapping[str, object]
) -> dict[str, object]:
    snapshot = copy.deepcopy(dict(value)) if isinstance(value, Mapping) else {}
    diagnostics_value = snapshot.get("diagnostics")
    diagnostics = (
        diagnostics_value
        if isinstance(diagnostics_value, Mapping)
        else capabilities.get("diagnostics")
    )
    diagnostics = diagnostics if isinstance(diagnostics, Mapping) else {}
    played_value = snapshot.get("played_character")
    played = played_value if isinstance(played_value, Mapping) else {}
    active_value = snapshot.get("active_event")
    active = active_value if isinstance(active_value, Mapping) else {}
    binding = {
        "snapshot_id": snapshot.get("snapshot_id"),
        "revision": snapshot.get("revision"),
        "native_revision": snapshot.get("native_revision"),
        "date_raw": snapshot.get("date_raw"),
        "paused": snapshot.get("paused"),
        "map_ready": snapshot.get("map_ready"),
        "bridge_pid": diagnostics.get("bridge_pid"),
        "connection_generation": diagnostics.get("connection_generation"),
        "player_character_id": played.get("character_id"),
        "event_instance_id": active.get("instance_id"),
        "event_option_count": active.get("option_count"),
    }
    valid = (
        isinstance(binding["snapshot_id"], str)
        and bool(binding["snapshot_id"])
        and _nonnegative_int(binding["revision"])
        and _nonnegative_int(binding["native_revision"])
        and isinstance(binding["date_raw"], int)
        and not isinstance(binding["date_raw"], bool)
        and binding["paused"] is True
        and binding["map_ready"] is True
        and _positive_int(binding["bridge_pid"])
        and _positive_int(binding["connection_generation"])
        and _positive_int(binding["player_character_id"])
        and _positive_int(binding["event_instance_id"])
        and _positive_int(binding["event_option_count"])
    )
    if not valid:
        raise ValueError("current snapshot is not a bound paused event frame")
    return binding


def _unexpected_binding(value: object) -> tuple[str, dict[str, object]]:
    unexpected = value if isinstance(value, Mapping) else {}
    key = unexpected.get("event_definition_key")
    snapshot_value = unexpected.get("snapshot")
    snapshot = snapshot_value if isinstance(snapshot_value, Mapping) else {}
    event_value = unexpected.get("event")
    event = event_value if isinstance(event_value, Mapping) else {}
    query_value = unexpected.get("query")
    query = query_value if isinstance(query_value, Mapping) else {}
    context_value = query.get("current_event_window_context")
    context = context_value if isinstance(context_value, Mapping) else {}
    query_binding_value = query.get("binding")
    query_binding = (
        query_binding_value if isinstance(query_binding_value, Mapping) else {}
    )
    diagnostics_value = snapshot.get("diagnostics")
    diagnostics = diagnostics_value if isinstance(diagnostics_value, Mapping) else {}
    binding = {
        "snapshot_id": event.get("snapshot_id"),
        "revision": event.get("revision"),
        "native_revision": event.get("native_revision"),
        "date_raw": event.get("date_raw"),
        "bridge_pid": diagnostics.get("bridge_pid"),
        "connection_generation": event.get("connection_generation"),
        "player_character_id": event.get("player_character_id"),
        "event_instance_id": event.get("event_instance_id"),
        "event_option_count": event.get("event_option_count"),
    }
    query_checks = {
        "query_available": query.get("status") == "available",
        "definition_key_exact": (
            isinstance(key, str)
            and bool(key)
            and context.get("event_definition_key") == key
        ),
        "query_snapshot_exact": (
            query_binding.get("snapshot_id") == binding["snapshot_id"]
            and query_binding.get("revision") == binding["revision"]
            and query_binding.get("native_revision") == binding["native_revision"]
            and query_binding.get("event_instance_id")
            == binding["event_instance_id"]
        ),
        "source_snapshot_paused": (
            snapshot.get("paused") is True and snapshot.get("map_ready") is True
        ),
        "source_binding_complete": (
            isinstance(binding["snapshot_id"], str)
            and bool(binding["snapshot_id"])
            and _nonnegative_int(binding["revision"])
            and _nonnegative_int(binding["native_revision"])
            and isinstance(binding["date_raw"], int)
            and not isinstance(binding["date_raw"], bool)
            and _positive_int(binding["bridge_pid"])
            and _positive_int(binding["connection_generation"])
            and _positive_int(binding["player_character_id"])
            and _positive_int(binding["event_instance_id"])
            and _positive_int(binding["event_option_count"])
        ),
    }
    failed = [name for name, passed in query_checks.items() if passed is not True]
    if failed:
        raise ValueError(
            "unexpected-event evidence is not a strict queried frame: "
            + ", ".join(failed)
        )
    assert isinstance(key, str)
    return key, binding


def _same_frame(expected: Mapping[str, object], observed: Mapping[str, object]) -> bool:
    return all(expected.get(name) == observed.get(name) for name in _SAME_FRAME_FIELDS)


def _same_modal(expected: Mapping[str, object], observed: Mapping[str, object]) -> bool:
    """Compare durable gameplay identity across a publishing command.

    save-checkpoint publishes a fresh native snapshot even when the paused
    event itself is unchanged. Revisions must stay exact before submission,
    while the post-save check binds the durable modal identity instead.
    """

    return all(expected.get(name) == observed.get(name) for name in _SAME_MODAL_FIELDS)


def _checkpoint_receipt(
    value: object,
    *,
    expected_path: Path,
    binding: Mapping[str, object],
) -> tuple[dict[str, object], dict[str, object]]:
    result = copy.deepcopy(dict(value)) if isinstance(value, Mapping) else {}
    checkpoint_value = result.get("checkpoint")
    checkpoint = (
        copy.deepcopy(dict(checkpoint_value))
        if isinstance(checkpoint_value, Mapping)
        else {}
    )
    materialization_value = result.get("materialization")
    materialization = (
        materialization_value
        if isinstance(materialization_value, Mapping)
        else {}
    )
    raw_path = checkpoint.get("path")
    path = Path(raw_path).resolve() if isinstance(raw_path, str) else Path()
    size = checkpoint.get("size")
    digest = checkpoint.get("sha256")
    checks = {
        "accepted": result.get("accepted") is True,
        "checkpoint_saved": checkpoint.get("status") == "saved",
        "path_absolute": isinstance(raw_path, str) and Path(raw_path).is_absolute(),
        "path_exact": path == expected_path,
        "file_materialized": path.is_file(),
        "size_positive": _positive_int(size),
        "size_exact": path.is_file() and path.stat().st_size == size,
        "sha256_well_formed": isinstance(digest, str)
        and _SHA256.fullmatch(digest) is not None,
        "date_exact": checkpoint.get("date_raw") == binding.get("date_raw"),
        "episode_character_exact": checkpoint.get("episode_character_id")
        == binding.get("player_character_id"),
        "history_index_positive": _positive_int(checkpoint.get("history_index")),
        "strategy_present": isinstance(checkpoint.get("strategy"), str)
        and bool(checkpoint.get("strategy")),
        "materialization_available": materialization.get("available") is True,
    }
    if checks["file_materialized"] and checks["sha256_well_formed"]:
        checks["sha256_exact"] = _sha256_file(path).casefold() == str(digest).casefold()
    else:
        checks["sha256_exact"] = False
    failed = [name for name, passed in checks.items() if passed is not True]
    if failed:
        raise ValueError(
            "native unexpected-event checkpoint receipt is invalid: "
            + ", ".join(failed)
        )
    return result, checks


def attempt_unexpected_event_durable_checkpoint(
    service: UnexpectedEventCheckpointService,
    *,
    state_dir: Path,
    unexpected_event: Mapping[str, object],
    artifact_path: Path,
) -> dict[str, object]:
    """Return GREEN+durable or RED+retained-only evidence; never raise."""

    target = artifact_path.resolve()
    expected_checkpoint_path = (
        state_dir.resolve() / "profile" / "save games" / CHECKPOINT_FILENAME
    ).resolve()
    evidence: dict[str, object] = {
        "schema_version": 1,
        "kind": "zg361_phase2_unexpected_event_durable_checkpoint",
        "result": "RED",
        "durable_recovery_ready": False,
        "live_retention_may_continue": True,
        "event_definition_key": unexpected_event.get("event_definition_key"),
        "expected_checkpoint_path": str(expected_checkpoint_path),
        "source_binding": None,
        "pre_save_binding": None,
        "post_save_binding": None,
        "capability_checks": {},
        "save_result": None,
        "save_checks": {},
        "failure_reason": None,
    }
    try:
        key, source_binding = _unexpected_binding(unexpected_event)
        evidence["event_definition_key"] = key
        evidence["source_binding"] = source_binding
        capabilities_value = service.capabilities()
        capabilities = (
            capabilities_value if isinstance(capabilities_value, Mapping) else {}
        )
        diagnostics_value = capabilities.get("diagnostics")
        diagnostics = (
            diagnostics_value if isinstance(diagnostics_value, Mapping) else {}
        )
        bridge_capabilities = capabilities.get("bridge_capabilities")
        action_steps = capabilities.get("action_steps")
        materialization_value = capabilities.get("checkpoint_materialization")
        materialization = (
            materialization_value
            if isinstance(materialization_value, Mapping)
            else {}
        )
        capability_checks = {
            "native_headless": capabilities.get("mode") == "native-headless"
            and capabilities.get("backend_id") == "native-headless"
            and capabilities.get("visual_fallback") is False,
            "bridge_connected": diagnostics.get("connected") is True,
            "save_capability": isinstance(bridge_capabilities, list)
            and SAVE_CHECKPOINT_CAPABILITY in bridge_capabilities,
            "save_step": isinstance(action_steps, list)
            and SAVE_CHECKPOINT_STEP in action_steps,
            "checkpoint_materialization_configured": materialization.get(
                "configured"
            )
            is True,
        }
        evidence["capability_checks"] = capability_checks
        failed_capabilities = [
            name for name, passed in capability_checks.items() if passed is not True
        ]
        if failed_capabilities:
            raise ValueError(
                "unexpected-event checkpoint capability profile is incomplete: "
                + ", ".join(failed_capabilities)
            )

        before = _snapshot_binding(service.snapshot(), capabilities)
        evidence["pre_save_binding"] = before
        if not _same_frame(source_binding, before):
            raise ValueError(
                "unexpected event changed before durable checkpoint submission"
            )

        raw_save = service.save_checkpoint(expected_revision=int(before["revision"]))
        evidence["save_result"] = copy.deepcopy(raw_save)
        save_result, save_checks = _checkpoint_receipt(
            raw_save,
            expected_path=expected_checkpoint_path,
            binding=before,
        )
        evidence["save_result"] = save_result
        evidence["save_checks"] = save_checks

        after_capabilities_value = service.capabilities()
        after_capabilities = (
            after_capabilities_value
            if isinstance(after_capabilities_value, Mapping)
            else capabilities
        )
        after = _snapshot_binding(service.snapshot(), after_capabilities)
        evidence["post_save_binding"] = after
        if not _same_modal(before, after):
            raise ValueError(
                "unexpected event changed while durable checkpoint materialized"
            )
        evidence["result"] = "GREEN"
        evidence["durable_recovery_ready"] = True
        evidence["recovery_input"] = {
            "source_profile": str((state_dir.resolve() / "profile").resolve()),
            "source_save": str(expected_checkpoint_path),
            "expected_source_save_sha256": str(
                save_result["checkpoint"]["sha256"]
            ).casefold(),
        }
    except Exception as error:
        evidence["result"] = "RED"
        evidence["durable_recovery_ready"] = False
        evidence["failure_reason"] = f"{type(error).__name__}: {error}"

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        write_json_atomic(target, evidence)
        evidence["artifact_path"] = str(target)
        evidence["artifact_written"] = True
    except Exception as error:
        evidence["artifact_path"] = str(target)
        evidence["artifact_written"] = False
        evidence["artifact_write_error"] = f"{type(error).__name__}: {error}"
    return evidence


__all__ = [
    "CHECKPOINT_FILENAME",
    "attempt_unexpected_event_durable_checkpoint",
]
