#!/usr/bin/env python3
"""Managed-product live entry for the strict ``zg361.50`` checkpoint.

The entry waits without advancing or mutating CK3.  Once the product event is
already visible on the paused map it delegates capture to the strict Incident
seam, then emits the schema-2 row consumed by the four-span registry assembler.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import time
from typing import Callable, Final, Mapping, Protocol

from zg361_phase2_incident_checkpoint_seam import (
    HANDLER,
    SOURCE_CHECKPOINT_KIND,
    SPAN_ID,
    IncidentCheckpointSeamError,
    capture_current_received_self_incident_checkpoint_v1,
    validate_received_self_incident_checkpoint_receipt,
)
from zhongguo_phase2_source_checkpoint_provider import (
    INCIDENT_STRICT_RECEIPT_FIELD,
    SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION,
)


LIVE_CAPTURE_KIND: Final = (
    "zg361_phase2_incident_source_checkpoint_live_capture"
)
REGISTRY_CAPTURE_ENTRY_KIND: Final = (
    "zg361_phase2_source_checkpoint_capture_entry"
)
SOURCE_EVENT_DEFINITION_KEY: Final = "zg361.50"


class IncidentSourceCaptureService(Protocol):
    def snapshot(self) -> dict[str, object]: ...

    def query_current_event_window_context_v1(
        self, event_instance_id: int, *, expected_revision: int
    ) -> dict[str, object]: ...

    def save_checkpoint(
        self, *, expected_revision: int | None = None
    ) -> dict[str, object]: ...


class IncidentSourceCaptureEntryError(RuntimeError):
    result: Final = "RED"

    def __init__(self, reason_code: str, evidence: Mapping[str, object]) -> None:
        self.reason_code = reason_code
        self.evidence = {
            **deepcopy(dict(evidence)),
            "result": "RED",
            "reason_code": reason_code,
        }
        super().__init__(f"Incident source capture RED [{reason_code}]")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _record(path: Path) -> dict[str, object]:
    target = path.resolve()
    return {
        "path": str(target),
        "bytes": target.stat().st_size,
        "sha256": _sha256(target),
    }


def _write_json(path: Path, value: Mapping[str, object]) -> None:
    target = path.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def build_schema2_incident_registry_capture_entry(
    receipt: Mapping[str, object],
    *,
    expected_seed_lineage_id: str,
) -> dict[str, object]:
    """Project one validated strict receipt into the formal manifest row."""

    raw = deepcopy(dict(receipt))
    try:
        summary = validate_received_self_incident_checkpoint_receipt(
            raw,
            expected_seed_lineage_id=expected_seed_lineage_id,
        )
    except IncidentCheckpointSeamError as error:
        raise IncidentSourceCaptureEntryError(
            "strict_incident_receipt_invalid",
            {
                "upstream_reason_code": error.reason_code,
                "upstream_evidence": error.evidence,
            },
        ) from error
    checkpoint = summary["checkpoint"]
    assert isinstance(checkpoint, Mapping)
    owner = int(summary["owner_character_id"])
    player = int(summary["player_character_id"])
    date_raw = int(summary["date_raw"])
    sha256 = str(checkpoint["sha256"])
    lineage = str(summary["seed_lineage_id"])
    return {
        "schema_version": SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION,
        "kind": REGISTRY_CAPTURE_ENTRY_KIND,
        "result": "GREEN",
        "evidence_class": "real_ck3",
        "span_id": SPAN_ID,
        "handler": HANDLER,
        "source_event_definition_key": SOURCE_EVENT_DEFINITION_KEY,
        "owner_character_id": owner,
        "player_character_id": player,
        "date_raw": date_raw,
        "seed_lineage_id": lineage,
        "capture_lineage": deepcopy(summary["capture_lineage"]),
        "checkpoint": deepcopy(dict(checkpoint)),
        "source_receipt": {
            "result": "GREEN",
            "evidence_class": "real_ck3",
            "provider_observed": True,
            "ui_state_verified": True,
            "fixture_used": False,
            "console_used": False,
            "span_id": SPAN_ID,
            "event_definition_key": SOURCE_EVENT_DEFINITION_KEY,
            "owner_character_id": owner,
            "player_character_id": player,
            "date_raw": date_raw,
            "checkpoint_sha256": sha256,
            "save_lineage_id": lineage,
        },
        INCIDENT_STRICT_RECEIPT_FIELD: raw,
        "action_ack_used_as_state_evidence": False,
    }


def wait_for_and_capture_incident_source_checkpoint(
    service: IncidentSourceCaptureService,
    *,
    evidence_path: Path,
    checkpoint_root: Path,
    receipt_path: Path,
    registry_entry_path: Path,
    seed_lineage_id: str,
    capture_lineage: Mapping[str, object],
    tracked_ck3_pid: int,
    timeout_seconds: float = 120.0,
    poll_interval_seconds: float = 0.25,
    monotonic: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
) -> dict[str, object]:
    """Wait read-only for a real event, then persist its strict checkpoint."""

    output_paths = {
        "receipt": receipt_path.resolve(),
        "registry_entry": registry_entry_path.resolve(),
    }
    evidence: dict[str, object] = {
        "schema_version": 1,
        "kind": LIVE_CAPTURE_KIND,
        "result": "RED",
        "readiness": "waiting-for-real-product-event",
        "source_event_definition_key": SOURCE_EVENT_DEFINITION_KEY,
        "tracked_ck3_pid": tracked_ck3_pid,
        "provider_observed": False,
        "ui_state_verified": False,
        "fixture_used": False,
        "console_used": False,
        "ocr_used": False,
        "coordinates_used": False,
        "gameplay_action_executed": False,
        "action_ack_used_as_state_evidence": False,
        "poll_count": 0,
        "strict_receipt": None,
        "schema2_registry_capture_entry": None,
        "failure_reason": None,
    }

    def fail(reason_code: str, detail: Mapping[str, object]) -> None:
        evidence["failure_reason"] = reason_code
        evidence["failure_evidence"] = deepcopy(dict(detail))
        _write_json(evidence_path, evidence)
        raise IncidentSourceCaptureEntryError(reason_code, evidence)

    if (
        isinstance(timeout_seconds, bool)
        or not isinstance(timeout_seconds, (int, float))
        or timeout_seconds <= 0
        or isinstance(poll_interval_seconds, bool)
        or not isinstance(poll_interval_seconds, (int, float))
        or poll_interval_seconds <= 0
        or not isinstance(tracked_ck3_pid, int)
        or isinstance(tracked_ck3_pid, bool)
        or tracked_ck3_pid <= 0
    ):
        fail(
            "incident_source_capture_arguments_invalid",
            {
                "timeout_seconds": timeout_seconds,
                "poll_interval_seconds": poll_interval_seconds,
                "tracked_ck3_pid": tracked_ck3_pid,
            },
        )
    existing = [str(path) for path in output_paths.values() if path.exists()]
    if existing:
        fail(
            "incident_source_capture_output_already_exists",
            {"existing_outputs": existing},
        )

    deadline = monotonic() + float(timeout_seconds)
    while monotonic() <= deadline:
        snapshot = service.snapshot()
        evidence["poll_count"] = int(evidence["poll_count"]) + 1
        if not isinstance(snapshot, dict):
            fail(
                "incident_source_snapshot_invalid",
                {"snapshot_type": type(snapshot).__name__},
            )
        diagnostics = snapshot.get("diagnostics")
        observed_pid = (
            diagnostics.get("bridge_pid")
            if isinstance(diagnostics, Mapping)
            else None
        )
        if observed_pid != tracked_ck3_pid:
            fail(
                "incident_source_managed_session_mismatch",
                {
                    "tracked_ck3_pid": tracked_ck3_pid,
                    "observed_bridge_pid": observed_pid,
                },
            )
        active_event = snapshot.get("active_event")
        if isinstance(active_event, Mapping):
            if snapshot.get("paused") is not True or snapshot.get("map_ready") is not True:
                sleep(float(poll_interval_seconds))
                continue
            try:
                receipt = capture_current_received_self_incident_checkpoint_v1(
                    service,
                    checkpoint_root=checkpoint_root,
                    receipt_path=receipt_path,
                    seed_lineage_id=seed_lineage_id,
                    capture_lineage=capture_lineage,
                )
                entry = build_schema2_incident_registry_capture_entry(
                    receipt,
                    expected_seed_lineage_id=seed_lineage_id,
                )
            except IncidentCheckpointSeamError as error:
                fail(
                    "visible_event_is_not_strict_received_self_zg361_50",
                    {
                        "upstream_reason_code": error.reason_code,
                        "upstream_evidence": error.evidence,
                    },
                )
            _write_json(registry_entry_path, entry)
            evidence.update(
                {
                    "result": "GREEN",
                    "readiness": "captured-real-checkpoint",
                    "provider_observed": True,
                    "ui_state_verified": True,
                    "strict_receipt": {
                        "kind": SOURCE_CHECKPOINT_KIND,
                        **_record(receipt_path),
                    },
                    "schema2_registry_capture_entry": {
                        "kind": REGISTRY_CAPTURE_ENTRY_KIND,
                        "schema_version": (
                            SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION
                        ),
                        **_record(registry_entry_path),
                    },
                    "checkpoint": deepcopy(entry["checkpoint"]),
                    "owner_character_id": entry["owner_character_id"],
                    "player_character_id": entry["player_character_id"],
                    "subject_character_id": entry["player_character_id"],
                    "event_root_character_id": entry[
                        "player_character_id"
                    ],
                    "notice_owner_character_id": entry[
                        "owner_character_id"
                    ],
                    "option_number": 1,
                    "option_shown": True,
                    "option_enabled": True,
                    "provider_ui_same_frame": True,
                    "date_raw": entry["date_raw"],
                    "seed_lineage_id": entry["seed_lineage_id"],
                    "capture_lineage": deepcopy(
                        entry["capture_lineage"]
                    ),
                    "failure_reason": None,
                }
            )
            _write_json(evidence_path, evidence)
            return evidence
        sleep(float(poll_interval_seconds))

    fail(
        "real_zg361_50_wait_timeout",
        {
            "timeout_seconds": timeout_seconds,
            "poll_count": evidence["poll_count"],
            "state_advance_attempted": False,
        },
    )
    raise AssertionError("unreachable")


__all__ = [
    "LIVE_CAPTURE_KIND",
    "REGISTRY_CAPTURE_ENTRY_KIND",
    "SOURCE_EVENT_DEFINITION_KEY",
    "IncidentSourceCaptureEntryError",
    "IncidentSourceCaptureService",
    "build_schema2_incident_registry_capture_entry",
    "wait_for_and_capture_incident_source_checkpoint",
]
