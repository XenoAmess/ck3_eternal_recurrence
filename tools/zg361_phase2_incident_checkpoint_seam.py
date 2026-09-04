#!/usr/bin/env python3
"""Strict real-checkpoint seam for the received-self Incident action cell.

The capture half only freezes an already visible real ``zg361.50`` event.  It
cannot create or advance to that event.  The execution half restores the exact
captured bytes, re-observes the event through the native event-window provider,
and then delegates gameplay to the existing Incident X/Y/Z action cell.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import time
from typing import Callable, Final, Mapping, Protocol


ROOT = Path(__file__).resolve().parents[1]
AUTOPLAYER_SRC = ROOT / "ck3_autonomous_player" / "src"
if str(AUTOPLAYER_SRC) not in sys.path:
    sys.path.insert(0, str(AUTOPLAYER_SRC))

from xar_autoplayer.bridge.event_window_context_contract import (  # noqa: E402
    QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_CAPABILITY,
    normalize_current_event_window_context_v1,
)
from xar_autoplayer.bridge.zhongguo_incident_action_cell import (  # noqa: E402
    INCIDENT_ACTION_CELL_ID,
    INCIDENT_PROFILES,
    INCIDENT_TRIGGER_EVENT_DEFINITION_KEY,
    INCIDENT_TRIGGER_OPTION_NUMBER,
    NOTICE_OWNER_SCOPE_NAME,
    IncidentActionCellError,
    run_incident_xyz_gameplay_action_cell,
)


SOURCE_CHECKPOINT_KIND: Final = (
    "zg361_phase2_incidents_operations_source_checkpoint_v1"
)
SPAN_ID: Final = "phase2_incidents_operations"
PRODUCER_KEY: Final = "incidents-operations"
HANDLER: Final = "capture_incidents_operations"
_SHA256: Final = re.compile(r"^[0-9A-F]{64}$")
_CAPTURE_CHECKS: Final = {
    "paused_map_ready_exact_event",
    "player_root_subject_bound",
    "distinct_saved_notice_owner_bound",
    "option_one_shown_enabled",
    "provider_ui_query_same_frame",
    "native_save_same_frame",
    "checkpoint_bytes_hash_bound",
    "action_ack_used_as_state_evidence",
}
_ACTION_CHECKS: Final = {
    "entry_event_identity_bound",
    "entry_option_materialized",
    "ack_not_used_as_result",
    "xyz_terminal_same_frame_ready",
    "xyz_profile_probe_receipts_frozen",
    "xyz_mixed_na_incident_matrix",
    "wrong_owner_acl_typed_red",
}


class IncidentCheckpointService(Protocol):
    """Narrow capture/restore surface; the action cell consumes the same object."""

    def snapshot(self) -> dict[str, object]: ...

    def query_current_event_window_context_v1(
        self, event_instance_id: int, *, expected_revision: int
    ) -> dict[str, object]: ...

    def save_checkpoint(
        self, *, expected_revision: int | None = None
    ) -> dict[str, object]: ...

    def restore_phase2_span_source_checkpoint_v1(
        self, **arguments: object
    ) -> dict[str, object]: ...


class IncidentCheckpointSeamError(RuntimeError):
    """Fail-closed capture, preflight, restore, or action binding error."""

    result: Final = "RED"

    def __init__(self, reason_code: str, evidence: Mapping[str, object]) -> None:
        self.reason_code = reason_code
        self.evidence = {
            **deepcopy(dict(evidence)),
            "result": "RED",
            "reason_code": reason_code,
        }
        super().__init__(f"Incident checkpoint seam RED [{reason_code}]")


def incident_checkpoint_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _nonnegative_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _typed_character_id(value: object) -> int | None:
    scope = dict(value) if isinstance(value, Mapping) else {}
    identity = scope.get("typed_identity")
    identity = dict(identity) if isinstance(identity, Mapping) else {}
    character_id = identity.get("character_id")
    if not (
        scope.get("status") == "available"
        and scope.get("type_key") == "character"
        and identity.get("status") == "available"
        and identity.get("kind") == "character"
        and _positive_int(character_id)
        and int(character_id) <= 2**31 - 1
    ):
        return None
    return int(character_id)


def _snapshot_binding(value: object) -> dict[str, object]:
    snapshot = dict(value) if isinstance(value, Mapping) else {}
    played = snapshot.get("played_character")
    played = dict(played) if isinstance(played, Mapping) else {}
    diagnostics = snapshot.get("diagnostics")
    diagnostics = dict(diagnostics) if isinstance(diagnostics, Mapping) else {}
    active = snapshot.get("active_event")
    active = dict(active) if isinstance(active, Mapping) else {}
    binding = {
        "snapshot_id": snapshot.get("snapshot_id"),
        "revision": snapshot.get("revision"),
        "native_revision": snapshot.get("native_revision"),
        "date_raw": snapshot.get("date_raw"),
        "player_character_id": played.get("character_id"),
        "bridge_pid": diagnostics.get("bridge_pid"),
        "connection_generation": diagnostics.get("connection_generation"),
        "paused": snapshot.get("paused"),
        "map_ready": snapshot.get("map_ready"),
        "event_instance_id": active.get("instance_id"),
        "event_option_count": active.get("option_count"),
    }
    valid = (
        isinstance(binding["snapshot_id"], str)
        and bool(binding["snapshot_id"])
        and _nonnegative_int(binding["revision"])
        and _positive_int(binding["native_revision"])
        and isinstance(binding["date_raw"], int)
        and not isinstance(binding["date_raw"], bool)
        and -(2**31) <= int(binding["date_raw"]) <= 2**31 - 1
        and played.get("alive") is True
        and _positive_int(binding["player_character_id"])
        and int(binding["player_character_id"]) <= 2**31 - 1
        and _positive_int(binding["bridge_pid"])
        and _positive_int(binding["connection_generation"])
        and binding["paused"] is True
        and binding["map_ready"] is True
        and _positive_int(binding["event_instance_id"])
        and int(binding["event_instance_id"]) <= 2**31 - 1
        and _positive_int(binding["event_option_count"])
        and int(binding["event_option_count"]) <= 256
    )
    if not valid:
        raise IncidentCheckpointSeamError(
            "incident_source_snapshot_not_action_ready",
            {"snapshot_binding": binding},
        )
    return binding


def _same_capture_binding(
    expected: Mapping[str, object], observed: Mapping[str, object]
) -> bool:
    return all(expected.get(key) == observed.get(key) for key in expected)


def _event_context_contract(
    value: object,
    *,
    snapshot_binding: Mapping[str, object],
    expected_owner_character_id: int | None = None,
) -> dict[str, object]:
    query = deepcopy(dict(value)) if isinstance(value, Mapping) else {}
    frame = query.get("current_event_window_context")
    try:
        normalized = normalize_current_event_window_context_v1(
            frame,
            expected_event_instance_id=int(
                snapshot_binding["event_instance_id"]
            ),
            expected_date_raw=int(snapshot_binding["date_raw"]),
            expected_snapshot_revision=int(
                snapshot_binding["native_revision"]
            ),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise IncidentCheckpointSeamError(
            "incident_source_event_context_invalid",
            {"message": str(error), "event_context_query": query},
        ) from error

    binding = query.get("binding")
    binding = dict(binding) if isinstance(binding, Mapping) else {}
    source = query.get("source")
    source = dict(source) if isinstance(source, Mapping) else {}
    root_id = _typed_character_id(normalized.get("root_scope"))
    saved = normalized.get("saved_scopes")
    owner_rows = [
        row
        for row in saved
        if isinstance(row, Mapping) and row.get("name") == NOTICE_OWNER_SCOPE_NAME
    ] if isinstance(saved, list) else []
    owner_id = (
        _typed_character_id(owner_rows[0].get("scope"))
        if len(owner_rows) == 1
        else None
    )
    options = normalized.get("options")
    option_rows = [
        row
        for row in options
        if isinstance(row, Mapping)
        and row.get("native_option_index")
        == INCIDENT_TRIGGER_OPTION_NUMBER - 1
    ] if isinstance(options, list) else []
    option = dict(option_rows[0]) if len(option_rows) == 1 else {}
    player = snapshot_binding.get("player_character_id")
    valid = (
        query.get("status") == "available"
        and query.get("scope") == "exact-current-event-window"
        and query.get("current_event_window_context_ready") is True
        and query.get("current_event_effect_indicators_ready") is True
        and binding.get("snapshot_id") == snapshot_binding.get("snapshot_id")
        and binding.get("revision") == snapshot_binding.get("revision")
        and binding.get("native_revision")
        == snapshot_binding.get("native_revision")
        and binding.get("date_raw") == snapshot_binding.get("date_raw")
        and binding.get("expected_revision")
        == snapshot_binding.get("revision")
        and binding.get("event_instance_id")
        == snapshot_binding.get("event_instance_id")
        and source.get("snapshot_id") == snapshot_binding.get("snapshot_id")
        and source.get("revision") == snapshot_binding.get("revision")
        and source.get("native_revision")
        == snapshot_binding.get("native_revision")
        and source.get("date_raw") == snapshot_binding.get("date_raw")
        and source.get("paused") is True
        and normalized.get("status") == "available"
        and normalized.get("event_definition_key")
        == INCIDENT_TRIGGER_EVENT_DEFINITION_KEY
        and normalized.get("current_event_instance_id")
        == snapshot_binding.get("event_instance_id")
        and normalized.get("window_match_count") == 1
        and root_id == player
        and _positive_int(owner_id)
        and owner_id != player
        and (
            expected_owner_character_id is None
            or owner_id == expected_owner_character_id
        )
        and isinstance(options, list)
        and len(options) == snapshot_binding.get("event_option_count")
        and option.get("rendered_index") == 0
        and option.get("shown") is True
        and option.get("enabled") is True
    )
    if not valid:
        raise IncidentCheckpointSeamError(
            "incident_source_event_context_not_received_self",
            {
                "snapshot_binding": dict(snapshot_binding),
                "event_definition_key": normalized.get(
                    "event_definition_key"
                ),
                "root_character_id": root_id,
                "notice_owner_character_id": owner_id,
                "expected_owner_character_id": expected_owner_character_id,
                "option_one": option,
                "query_binding": binding,
                "query_source": source,
            },
        )
    return {
        "capability": QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_CAPABILITY,
        "status": "available",
        "event_definition_key": INCIDENT_TRIGGER_EVENT_DEFINITION_KEY,
        "event_instance_id": int(snapshot_binding["event_instance_id"]),
        "root_character_id": int(root_id),
        "subject_character_id": int(player),
        "notice_owner_character_id": int(owner_id),
        "option_number": INCIDENT_TRIGGER_OPTION_NUMBER,
        "native_option_index": INCIDENT_TRIGGER_OPTION_NUMBER - 1,
        "option_shown": True,
        "option_enabled": True,
        "resolved_name": option.get("resolved_name"),
    }


def _validated_lineage(
    seed_lineage_id: object, capture_lineage: object
) -> dict[str, object]:
    lineage = (
        deepcopy(dict(capture_lineage))
        if isinstance(capture_lineage, Mapping)
        else {}
    )
    valid = (
        isinstance(seed_lineage_id, str)
        and bool(seed_lineage_id)
        and lineage.get("seed_lineage_id") == seed_lineage_id
        and lineage.get("evidence_class") == "real_ck3"
        and lineage.get("fixture_used") is False
        and lineage.get("ocr_used") is False
        and lineage.get("coordinates_used") is False
        and lineage.get("console_used") is False
        and lineage.get("generic_character_rebind_used") is False
    )
    if not valid:
        raise IncidentCheckpointSeamError(
            "incident_source_capture_lineage_invalid",
            {
                "seed_lineage_id": seed_lineage_id,
                "capture_lineage": lineage,
            },
        )
    return lineage


def _native_save_contract(
    value: object, *, snapshot_binding: Mapping[str, object]
) -> tuple[Path, dict[str, object]]:
    save = deepcopy(dict(value)) if isinstance(value, Mapping) else {}
    checkpoint = save.get("checkpoint")
    checkpoint = dict(checkpoint) if isinstance(checkpoint, Mapping) else {}
    materialization = save.get("materialization")
    raw_path = checkpoint.get("path")
    path = Path(str(raw_path)).resolve() if isinstance(raw_path, str) else Path()
    size = checkpoint.get("size")
    sha256 = str(checkpoint.get("sha256", "")).upper()
    valid = (
        save.get("accepted") is True
        and checkpoint.get("status") == "saved"
        and isinstance(raw_path, str)
        and Path(raw_path).is_absolute()
        and path.is_file()
        and _positive_int(size)
        and path.stat().st_size == size
        and _SHA256.fullmatch(sha256) is not None
        and incident_checkpoint_sha256(path) == sha256
        and checkpoint.get("date_raw") == snapshot_binding.get("date_raw")
        and checkpoint.get("episode_character_id")
        == snapshot_binding.get("player_character_id")
        and isinstance(checkpoint.get("strategy"), str)
        and bool(checkpoint.get("strategy"))
        and isinstance(materialization, Mapping)
        and materialization.get("available") is True
    )
    if not valid:
        raise IncidentCheckpointSeamError(
            "incident_source_native_save_invalid",
            {"native_save_result": save},
        )
    receipt = {
        "accepted": True,
        "backend_id": save.get("backend_id"),
        "checkpoint": {
            "status": "saved",
            "path": str(path),
            "size": int(size),
            "sha256": sha256,
            "date_raw": int(snapshot_binding["date_raw"]),
            "episode_character_id": int(
                snapshot_binding["player_character_id"]
            ),
            "strategy": checkpoint.get("strategy"),
        },
        "materialization": deepcopy(dict(materialization)),
    }
    return path, receipt


def _binding_record_valid(value: object) -> bool:
    binding = dict(value) if isinstance(value, Mapping) else {}
    expected_keys = {
        "snapshot_id",
        "revision",
        "native_revision",
        "date_raw",
        "player_character_id",
        "bridge_pid",
        "connection_generation",
        "paused",
        "map_ready",
        "event_instance_id",
        "event_option_count",
    }
    return (
        set(binding) == expected_keys
        and isinstance(binding["snapshot_id"], str)
        and bool(binding["snapshot_id"])
        and _nonnegative_int(binding["revision"])
        and _positive_int(binding["native_revision"])
        and isinstance(binding["date_raw"], int)
        and not isinstance(binding["date_raw"], bool)
        and _positive_int(binding["player_character_id"])
        and _positive_int(binding["bridge_pid"])
        and _positive_int(binding["connection_generation"])
        and binding["paused"] is True
        and binding["map_ready"] is True
        and _positive_int(binding["event_instance_id"])
        and _positive_int(binding["event_option_count"])
    )


def validate_received_self_incident_checkpoint_receipt(
    value: object,
    *,
    expected_seed_lineage_id: str | None = None,
) -> dict[str, object]:
    """Validate one durable capture receipt and its archived checkpoint bytes."""

    receipt = deepcopy(dict(value)) if isinstance(value, Mapping) else {}
    seed_lineage_id = receipt.get("seed_lineage_id")
    lineage = _validated_lineage(
        seed_lineage_id, receipt.get("capture_lineage")
    )
    checkpoint = receipt.get("checkpoint")
    checkpoint = dict(checkpoint) if isinstance(checkpoint, Mapping) else {}
    raw_path = checkpoint.get("path")
    path = Path(str(raw_path)).resolve() if isinstance(raw_path, str) else Path()
    expected_bytes = checkpoint.get("bytes")
    expected_sha256 = str(checkpoint.get("sha256", "")).upper()
    before = receipt.get("source_snapshot_binding")
    after_query = receipt.get("post_query_snapshot_binding")
    after_save = receipt.get("post_save_snapshot_binding")
    before_map = dict(before) if isinstance(before, Mapping) else {}
    after_query_map = (
        dict(after_query) if isinstance(after_query, Mapping) else {}
    )
    after_save_map = dict(after_save) if isinstance(after_save, Mapping) else {}
    native_save = receipt.get("native_save_receipt")
    native_save = dict(native_save) if isinstance(native_save, Mapping) else {}
    native_checkpoint = native_save.get("checkpoint")
    native_checkpoint = (
        dict(native_checkpoint)
        if isinstance(native_checkpoint, Mapping)
        else {}
    )
    capture_checks = receipt.get("capture_checks")
    capture_checks = (
        dict(capture_checks) if isinstance(capture_checks, Mapping) else {}
    )
    owner = receipt.get("owner_character_id")
    player = receipt.get("player_character_id")
    subject = receipt.get("subject_character_id")
    event_contract = _event_context_contract(
        receipt.get("event_context_query"),
        snapshot_binding=before_map,
        expected_owner_character_id=(int(owner) if _positive_int(owner) else None),
    ) if _binding_record_valid(before_map) else {}
    valid = (
        receipt.get("schema_version") == 1
        and receipt.get("kind") == SOURCE_CHECKPOINT_KIND
        and receipt.get("result") == "GREEN"
        and receipt.get("readiness") == "captured-real-checkpoint"
        and receipt.get("evidence_class") == "real_ck3"
        and receipt.get("state_origin") == "product-event"
        and receipt.get("provider_observed") is True
        and receipt.get("ui_state_verified") is True
        and receipt.get("fixture_used") is False
        and receipt.get("ocr_used") is False
        and receipt.get("coordinates_used") is False
        and receipt.get("console_used") is False
        and receipt.get("generic_character_rebind_used") is False
        and receipt.get("action_ack_used_as_state_evidence") is False
        and receipt.get("span_id") == SPAN_ID
        and receipt.get("producer_key") == PRODUCER_KEY
        and receipt.get("handler") == HANDLER
        and receipt.get("source_event_definition_key")
        == INCIDENT_TRIGGER_EVENT_DEFINITION_KEY
        and receipt.get("option_number") == INCIDENT_TRIGGER_OPTION_NUMBER
        and _positive_int(owner)
        and _positive_int(player)
        and owner != player
        and subject == player
        and receipt.get("event_root_character_id") == player
        and receipt.get("notice_owner_character_id") == owner
        and receipt.get("event_instance_id")
        == before_map.get("event_instance_id")
        and receipt.get("date_raw") == before_map.get("date_raw")
        and receipt.get("paused") is True
        and receipt.get("map_ready") is True
        and _binding_record_valid(before_map)
        and _binding_record_valid(after_query_map)
        and _binding_record_valid(after_save_map)
        and _same_capture_binding(before_map, after_query_map)
        and _same_capture_binding(before_map, after_save_map)
        and event_contract.get("root_character_id") == player
        and event_contract.get("subject_character_id") == subject
        and event_contract.get("notice_owner_character_id") == owner
        and event_contract.get("option_shown") is True
        and event_contract.get("option_enabled") is True
        and receipt.get("event_context_contract") == event_contract
        and isinstance(raw_path, str)
        and Path(raw_path).is_absolute()
        and path.is_file()
        and _positive_int(expected_bytes)
        and path.stat().st_size == expected_bytes
        and _SHA256.fullmatch(expected_sha256) is not None
        and incident_checkpoint_sha256(path) == expected_sha256
        and checkpoint.get("save_lineage_id") == seed_lineage_id
        and native_save.get("accepted") is True
        and native_checkpoint.get("status") == "saved"
        and native_checkpoint.get("size") == expected_bytes
        and str(native_checkpoint.get("sha256", "")).upper()
        == expected_sha256
        and native_checkpoint.get("date_raw") == before_map.get("date_raw")
        and native_checkpoint.get("episode_character_id") == player
        and isinstance(native_save.get("materialization"), Mapping)
        and native_save["materialization"].get("available") is True
        and set(capture_checks) == _CAPTURE_CHECKS
        and all(
            capture_checks.get(key) is True
            for key in _CAPTURE_CHECKS - {"action_ack_used_as_state_evidence"}
        )
        and capture_checks.get("action_ack_used_as_state_evidence") is False
        and (
            expected_seed_lineage_id is None
            or seed_lineage_id == expected_seed_lineage_id
        )
    )
    if not valid:
        raise IncidentCheckpointSeamError(
            "incident_source_checkpoint_receipt_invalid",
            {
                "checkpoint_path": str(path),
                "seed_lineage_id": seed_lineage_id,
                "expected_seed_lineage_id": expected_seed_lineage_id,
                "owner_character_id": owner,
                "player_character_id": player,
                "capture_checks": capture_checks,
            },
        )
    return {
        "schema_version": 1,
        "result": "GREEN",
        "readiness": "captured-real-checkpoint",
        "receipt_kind": SOURCE_CHECKPOINT_KIND,
        "checkpoint": {
            "path": str(path),
            "bytes": int(expected_bytes),
            "sha256": expected_sha256,
            "save_lineage_id": str(seed_lineage_id),
        },
        "seed_lineage_id": str(seed_lineage_id),
        "capture_lineage": lineage,
        "owner_character_id": int(owner),
        "player_character_id": int(player),
        "subject_character_id": int(subject),
        "event_instance_id": int(receipt["event_instance_id"]),
        "date_raw": int(receipt["date_raw"]),
        "event_context_contract": event_contract,
        "checks": deepcopy(capture_checks),
    }


def load_received_self_incident_checkpoint_receipt(
    path: Path, *, expected_seed_lineage_id: str | None = None
) -> dict[str, object]:
    target = path.resolve()
    try:
        value = json.loads(target.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise IncidentCheckpointSeamError(
            "incident_source_checkpoint_receipt_unreadable",
            {"receipt_path": str(target), "message": str(error)},
        ) from error
    result = validate_received_self_incident_checkpoint_receipt(
        value, expected_seed_lineage_id=expected_seed_lineage_id
    )
    result["receipt"] = {
        "path": str(target),
        "bytes": target.stat().st_size,
        "sha256": incident_checkpoint_sha256(target),
    }
    return result


def capture_current_received_self_incident_checkpoint_v1(
    service: IncidentCheckpointService,
    *,
    checkpoint_root: Path,
    receipt_path: Path,
    seed_lineage_id: str,
    capture_lineage: Mapping[str, object],
) -> dict[str, object]:
    """Freeze the currently visible real ``zg361.50`` without staging it."""

    lineage = _validated_lineage(seed_lineage_id, capture_lineage)
    receipt_target = receipt_path.resolve()
    if receipt_target.exists():
        raise IncidentCheckpointSeamError(
            "incident_source_checkpoint_receipt_already_exists",
            {"receipt_path": str(receipt_target)},
        )
    try:
        before_snapshot = service.snapshot()
        before = _snapshot_binding(before_snapshot)
        event_query = service.query_current_event_window_context_v1(
            int(before["event_instance_id"]),
            expected_revision=int(before["revision"]),
        )
        event_contract = _event_context_contract(
            event_query, snapshot_binding=before
        )
        after_query = _snapshot_binding(service.snapshot())
        if not _same_capture_binding(before, after_query):
            raise IncidentCheckpointSeamError(
                "incident_source_query_crossed_binding",
                {"before": before, "after_query": after_query},
            )
        save_result = service.save_checkpoint(
            expected_revision=int(before["revision"])
        )
        source_path, native_save_receipt = _native_save_contract(
            save_result, snapshot_binding=before
        )
        after_save = _snapshot_binding(service.snapshot())
        if not _same_capture_binding(before, after_save):
            raise IncidentCheckpointSeamError(
                "incident_source_save_crossed_binding",
                {"before": before, "after_save": after_save},
            )
    except IncidentCheckpointSeamError:
        raise
    except Exception as error:
        raise IncidentCheckpointSeamError(
            "incident_source_capture_failed",
            {"error_type": type(error).__name__, "message": str(error)},
        ) from error

    source_bytes = source_path.stat().st_size
    source_sha256 = incident_checkpoint_sha256(source_path)
    archive_root = checkpoint_root.resolve()
    archive_root.mkdir(parents=True, exist_ok=True)
    archive = archive_root / (
        "phase2-incidents-operations-zg361-50-"
        f"{source_sha256[:16].lower()}.ck3"
    )
    if archive.exists():
        if not (
            archive.is_file()
            and archive.stat().st_size == source_bytes
            and incident_checkpoint_sha256(archive) == source_sha256
        ):
            raise IncidentCheckpointSeamError(
                "incident_source_checkpoint_archive_collision",
                {
                    "archive_path": str(archive),
                    "expected_bytes": source_bytes,
                    "expected_sha256": source_sha256,
                },
            )
    else:
        shutil.copyfile(source_path, archive)
    if (
        archive.stat().st_size != source_bytes
        or incident_checkpoint_sha256(archive) != source_sha256
    ):
        raise IncidentCheckpointSeamError(
            "incident_source_checkpoint_archive_mismatch",
            {"source_path": str(source_path), "archive_path": str(archive)},
        )

    owner = int(event_contract["notice_owner_character_id"])
    player = int(event_contract["root_character_id"])
    receipt = {
        "schema_version": 1,
        "kind": SOURCE_CHECKPOINT_KIND,
        "result": "GREEN",
        "readiness": "captured-real-checkpoint",
        "evidence_class": "real_ck3",
        "state_origin": "product-event",
        "provider_observed": True,
        "ui_state_verified": True,
        "fixture_used": False,
        "ocr_used": False,
        "coordinates_used": False,
        "console_used": False,
        "generic_character_rebind_used": False,
        "action_ack_used_as_state_evidence": False,
        "span_id": SPAN_ID,
        "producer_key": PRODUCER_KEY,
        "handler": HANDLER,
        "source_event_definition_key": INCIDENT_TRIGGER_EVENT_DEFINITION_KEY,
        "option_number": INCIDENT_TRIGGER_OPTION_NUMBER,
        "player_character_id": player,
        "subject_character_id": player,
        "owner_character_id": owner,
        "event_root_character_id": player,
        "notice_owner_character_id": owner,
        "event_instance_id": int(before["event_instance_id"]),
        "date_raw": int(before["date_raw"]),
        "paused": True,
        "map_ready": True,
        "seed_lineage_id": seed_lineage_id,
        "capture_lineage": lineage,
        "source_snapshot_binding": before,
        "post_query_snapshot_binding": after_query,
        "post_save_snapshot_binding": after_save,
        "event_context_query": deepcopy(dict(event_query)),
        "event_context_contract": event_contract,
        "native_save_receipt": native_save_receipt,
        "checkpoint": {
            "path": str(archive.resolve()),
            "bytes": source_bytes,
            "sha256": source_sha256,
            "save_lineage_id": seed_lineage_id,
        },
        "capture_checks": {
            "paused_map_ready_exact_event": True,
            "player_root_subject_bound": True,
            "distinct_saved_notice_owner_bound": True,
            "option_one_shown_enabled": True,
            "provider_ui_query_same_frame": True,
            "native_save_same_frame": True,
            "checkpoint_bytes_hash_bound": True,
            "action_ack_used_as_state_evidence": False,
        },
    }
    validate_received_self_incident_checkpoint_receipt(
        receipt, expected_seed_lineage_id=seed_lineage_id
    )
    receipt_target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with receipt_target.open("x", encoding="utf-8", newline="\n") as output:
            json.dump(
                receipt,
                output,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            output.write("\n")
    except FileExistsError as error:
        raise IncidentCheckpointSeamError(
            "incident_source_checkpoint_receipt_already_exists",
            {"receipt_path": str(receipt_target)},
        ) from error
    return deepcopy(receipt)


def _restore_contract(
    value: object,
    *,
    checkpoint: Mapping[str, object],
    owner: int,
    player: int,
    date_raw: int,
) -> dict[str, object]:
    receipt = deepcopy(dict(value)) if isinstance(value, Mapping) else {}
    lifecycle = receipt.get("lifecycle")
    lifecycle = dict(lifecycle) if isinstance(lifecycle, Mapping) else {}
    valid = (
        receipt.get("schema_version") == 1
        and receipt.get("result") == "GREEN"
        and receipt.get("provider_observed") is True
        and receipt.get("restore_materialized") is True
        and receipt.get("checkpoint_sha256") == checkpoint.get("sha256")
        and receipt.get("checkpoint_bytes") == checkpoint.get("bytes")
        and receipt.get("save_lineage_id")
        == checkpoint.get("save_lineage_id")
        and receipt.get("event_definition_key")
        == INCIDENT_TRIGGER_EVENT_DEFINITION_KEY
        and receipt.get("owner_character_id") == owner
        and receipt.get("player_character_id") == player
        and receipt.get("date_raw") == date_raw
        and receipt.get("fixture_used") is False
        and receipt.get("console_used") is False
        and receipt.get("generic_character_rebind_used") is False
        and lifecycle.get("lifecycle_intent") == "restore"
        and _positive_int(lifecycle.get("previous_pid"))
        and _positive_int(lifecycle.get("pid"))
        and lifecycle.get("previous_pid") != lifecycle.get("pid")
        and _positive_int(lifecycle.get("previous_connection_generation"))
        and lifecycle.get("connection_generation")
        == int(lifecycle.get("previous_connection_generation", 0)) + 1
    )
    if not valid:
        raise IncidentCheckpointSeamError(
            "incident_source_checkpoint_restore_invalid",
            {"restore_receipt": receipt},
        )
    return receipt


def _observe_restored_source(
    service: IncidentCheckpointService, *, owner: int, player: int, date_raw: int
) -> dict[str, object]:
    before = _snapshot_binding(service.snapshot())
    if (
        before.get("player_character_id") != player
        or before.get("date_raw") != date_raw
    ):
        raise IncidentCheckpointSeamError(
            "incident_source_post_restore_binding_mismatch",
            {
                "snapshot_binding": before,
                "expected_player_character_id": player,
                "expected_date_raw": date_raw,
            },
        )
    query = service.query_current_event_window_context_v1(
        int(before["event_instance_id"]),
        expected_revision=int(before["revision"]),
    )
    contract = _event_context_contract(
        query,
        snapshot_binding=before,
        expected_owner_character_id=owner,
    )
    after = _snapshot_binding(service.snapshot())
    if not _same_capture_binding(before, after):
        raise IncidentCheckpointSeamError(
            "incident_source_post_restore_query_crossed_binding",
            {"before": before, "after_query": after},
        )
    return {
        "provider_observed": True,
        "ui_state_verified": True,
        "snapshot_binding": before,
        "event_context_contract": contract,
        "event_context_query": query,
    }


def _action_contract(value: object, *, owner: int, player: int) -> dict[str, object]:
    evidence = deepcopy(dict(value)) if isinstance(value, Mapping) else {}
    checks = evidence.get("checks")
    checks = dict(checks) if isinstance(checks, Mapping) else {}
    profiles = evidence.get("terminal_profiles")
    profiles = dict(profiles) if isinstance(profiles, Mapping) else {}
    acl = evidence.get("acl_profiles")
    acl = dict(acl) if isinstance(acl, Mapping) else {}
    acl_responses = acl.get("responses")
    acl_responses = (
        dict(acl_responses) if isinstance(acl_responses, Mapping) else {}
    )
    wrong_owner = acl.get("wrong_owner_character_id")
    kinds = {
        row.get("kind")
        for row in profiles.values()
        if isinstance(row, Mapping)
    }
    valid = (
        evidence.get("schema_version") == 1
        and evidence.get("cell_id") == INCIDENT_ACTION_CELL_ID
        and evidence.get("result") == "GREEN"
        and evidence.get("mcp_only") is True
        and evidence.get("ocr_used") is False
        and evidence.get("coordinates_used") is False
        and evidence.get("expected_owner_character_id") == owner
        and set(profiles) == set(INCIDENT_PROFILES)
        and kinds == {"na", "incident"}
        and all(
            isinstance(profiles[profile], Mapping)
            and profiles[profile].get("profile") == profile
            and profiles[profile].get("kpi_disposition")
            in {"not_staged", "pending"}
            for profile in INCIDENT_PROFILES
        )
        and _positive_int(wrong_owner)
        and wrong_owner not in {owner, player}
        and set(acl_responses) == set(INCIDENT_PROFILES)
        and all(
            isinstance(acl_responses[profile], Mapping)
            and acl_responses[profile].get("status") == "unavailable"
            and acl_responses[profile].get("unavailable_reason")
            == "owner_filter_mismatch"
            for profile in INCIDENT_PROFILES
        )
        and all(checks.get(key) is True for key in _ACTION_CHECKS)
    )
    if not valid:
        raise IncidentCheckpointSeamError(
            "incident_action_provider_postcondition_invalid",
            {
                "checks": checks,
                "profile_keys": list(profiles),
                "acl_profile_keys": list(acl_responses),
            },
        )
    return evidence


def run_received_self_incident_checkpoint_action_cell(
    service: IncidentCheckpointService,
    receipt: Mapping[str, object],
    *,
    expected_seed_lineage_id: str,
    timeout_seconds: float = 240.0,
    poll_interval_seconds: float = 0.10,
    monotonic: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
) -> dict[str, object]:
    """Restore, re-observe, act, and require the provider X/Y/Z + ACL proof."""

    source = validate_received_self_incident_checkpoint_receipt(
        receipt, expected_seed_lineage_id=expected_seed_lineage_id
    )
    checkpoint = source["checkpoint"]
    if not isinstance(checkpoint, Mapping):
        raise IncidentCheckpointSeamError(
            "incident_source_checkpoint_receipt_invalid", {"checkpoint": checkpoint}
        )
    owner = int(source["owner_character_id"])
    player = int(source["player_character_id"])
    date_raw = int(source["date_raw"])
    restore = getattr(
        service, "restore_phase2_span_source_checkpoint_v1", None
    )
    if not callable(restore):
        raise IncidentCheckpointSeamError(
            "incident_source_checkpoint_restore_provider_missing", {}
        )
    restored = _restore_contract(
        restore(
            checkpoint_path=str(checkpoint["path"]),
            expected_checkpoint_bytes=int(checkpoint["bytes"]),
            expected_checkpoint_sha256=str(checkpoint["sha256"]),
            expected_save_lineage_id=str(checkpoint["save_lineage_id"]),
            expected_event_definition_key=INCIDENT_TRIGGER_EVENT_DEFINITION_KEY,
            expected_owner_character_id=owner,
            expected_player_character_id=player,
            expected_date_raw=date_raw,
            allow_generic_character_rebind=False,
            allow_fixture=False,
            allow_console=False,
        ),
        checkpoint=checkpoint,
        owner=owner,
        player=player,
        date_raw=date_raw,
    )
    observed = _observe_restored_source(
        service, owner=owner, player=player, date_raw=date_raw
    )
    lifecycle = restored["lifecycle"]
    snapshot_binding = observed["snapshot_binding"]
    if not (
        isinstance(lifecycle, Mapping)
        and isinstance(snapshot_binding, Mapping)
        and snapshot_binding.get("bridge_pid") == lifecycle.get("pid")
        and snapshot_binding.get("connection_generation")
        == lifecycle.get("connection_generation")
    ):
        raise IncidentCheckpointSeamError(
            "incident_source_post_restore_lifecycle_mismatch",
            {
                "lifecycle": lifecycle,
                "snapshot_binding": snapshot_binding,
            },
        )
    try:
        action = run_incident_xyz_gameplay_action_cell(
            service,  # type: ignore[arg-type]
            owner_character_id=owner,
            timeout_seconds=timeout_seconds,
            poll_interval_seconds=poll_interval_seconds,
            monotonic=monotonic,
            sleep=sleep,
        )
    except IncidentActionCellError as error:
        raise IncidentCheckpointSeamError(
            "incident_action_cell_red",
            {"failure_reason": error.reason, "action_evidence": error.evidence},
        ) from error
    action = _action_contract(action, owner=owner, player=player)
    return {
        "schema_version": 1,
        "kind": "zg361_phase2_incident_checkpoint_action_seam",
        "result": "GREEN",
        "evidence_class": "real_ck3",
        "state_origin": "product-checkpoint",
        "restore_materialized": True,
        "source_provider_ui_reobserved": True,
        "gameplay_action_executed": True,
        "provider_observed_postcondition": True,
        "ack_only_is_green": False,
        "fixture_used": False,
        "console_used": False,
        "generic_character_rebind_used": False,
        "source_checkpoint": source,
        "restore_receipt": restored,
        "post_restore_source_observation": observed,
        "action_cell": action,
        "checks": {
            "exact_checkpoint_restored": True,
            "zg361_50_provider_ui_reobserved": True,
            "player_root_subject_bound": True,
            "distinct_notice_owner_bound": True,
            "option_one_shown_enabled": True,
            "action_ack_not_postcondition": True,
            "xyz_terminal_kpi_provider_observed": True,
            "wrong_owner_acl_typed_red": True,
        },
    }


__all__ = [
    "HANDLER",
    "PRODUCER_KEY",
    "SOURCE_CHECKPOINT_KIND",
    "SPAN_ID",
    "IncidentCheckpointSeamError",
    "IncidentCheckpointService",
    "capture_current_received_self_incident_checkpoint_v1",
    "incident_checkpoint_sha256",
    "load_received_self_incident_checkpoint_receipt",
    "run_received_self_incident_checkpoint_action_cell",
    "validate_received_self_incident_checkpoint_receipt",
]
