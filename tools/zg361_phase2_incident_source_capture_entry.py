#!/usr/bin/env python3
"""Managed-product live entry for the strict ``zg361.50`` checkpoint.

The source state opens with the notice owner played.  The formal entry performs
one typed native player switch to the known recipient without advancing the
date, freezes that switch receipt, and uses the shared production timeline
entry to reach the real product event.  Once the event is visible, the
capture-only layer waits read-only, delegates to the strict Incident seam and
emits the schema-2 row consumed by the four-span registry assembler.
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
    LEGACY_SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION,
)


LIVE_CAPTURE_KIND: Final = (
    "zg361_phase2_incident_source_checkpoint_live_capture"
)
REGISTRY_CAPTURE_ENTRY_KIND: Final = (
    "zg361_phase2_source_checkpoint_capture_entry"
)
SOURCE_EVENT_DEFINITION_KEY: Final = "zg361.50"
INITIAL_PLAYER_CHARACTER_ID: Final = 32904
TARGET_SUBJECT_CHARACTER_ID: Final = 29037
PLAYER_SWITCH_RECEIPT_KIND: Final = (
    "zg361_phase2_incident_source_player_switch_receipt"
)
GENERIC_REBIND_AUTHORITY: Final = (
    "native game.command.set-played-character-v1-N with same-paused-date "
    "postcondition receipt"
)
REGISTRY_CAPTURE_ENTRY_SCHEMA_VERSION: Final = (
    LEGACY_SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION
)


class IncidentSourceCaptureService(Protocol):
    def snapshot(self) -> dict[str, object]: ...

    def query_current_event_window_context_v1(
        self, event_instance_id: int, *, expected_revision: int
    ) -> dict[str, object]: ...

    def set_player_character_v1(
        self,
        character_id: int,
        *,
        expected_revision: int | None = None,
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


def _json_bytes(value: Mapping[str, object]) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _write_json_exclusive(path: Path, value: Mapping[str, object]) -> None:
    target = path.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with target.open("xb") as output:
            output.write(_json_bytes(value))
    except FileExistsError as error:
        raise IncidentSourceCaptureEntryError(
            "incident_source_player_switch_receipt_already_exists",
            {"path": str(target)},
        ) from error


def _switch_binding(value: object, *, require_event_free: bool) -> dict[str, object]:
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
        "active_event_instance_id": active.get("instance_id"),
        "active_event_option_count": active.get("option_count"),
    }
    positive = (
        lambda item: isinstance(item, int)
        and not isinstance(item, bool)
        and item > 0
    )
    valid = (
        isinstance(binding["snapshot_id"], str)
        and bool(binding["snapshot_id"])
        and isinstance(binding["revision"], int)
        and not isinstance(binding["revision"], bool)
        and int(binding["revision"]) >= 0
        and positive(binding["native_revision"])
        and isinstance(binding["date_raw"], int)
        and not isinstance(binding["date_raw"], bool)
        and positive(binding["player_character_id"])
        and positive(binding["bridge_pid"])
        and positive(binding["connection_generation"])
        and binding["paused"] is True
        and binding["map_ready"] is True
        and played.get("alive") is True
        and (not require_event_free or snapshot.get("active_event") is None)
    )
    if not valid:
        raise IncidentSourceCaptureEntryError(
            "incident_source_player_switch_binding_invalid",
            {
                "require_event_free": require_event_free,
                "binding": binding,
            },
        )
    return binding


def _player_switch_receipt(
    value: object,
    *,
    before: Mapping[str, object],
    after: Mapping[str, object],
    seed_lineage_id: str,
    initial_player_character_id: int,
    target_subject_character_id: int,
) -> dict[str, object]:
    native = deepcopy(dict(value)) if isinstance(value, Mapping) else {}
    valid = (
        native.get("schema_version") == 1
        and native.get("accepted") is True
        and native.get("status") == "switched"
        and native.get("backend_id") == "native-headless"
        and native.get("step")
        == f"set-played-character-v1-{target_subject_character_id}"
        and native.get("from_character_id") == initial_player_character_id
        and native.get("to_character_id") == target_subject_character_id
        and native.get("prior_episode_character_id")
        == initial_player_character_id
        and native.get("episode_character_id") == target_subject_character_id
        and native.get("date_raw") == before.get("date_raw")
        and native.get("before_revision") == before.get("revision")
        and native.get("after_revision") == after.get("revision")
        and native.get("native_revision") == after.get("native_revision")
        and native.get("paused") is True
        and native.get("map_ready") is True
        and native.get("postcondition_verified") is True
        and native.get("episode_rebind_performed") is True
        and native.get("one_life_terminal_cleared") is True
        and before.get("player_character_id") == initial_player_character_id
        and after.get("player_character_id") == target_subject_character_id
        and before.get("date_raw") == after.get("date_raw")
        and before.get("bridge_pid") == after.get("bridge_pid")
        and before.get("connection_generation")
        == after.get("connection_generation")
        and before.get("active_event_instance_id") is None
        and after.get("active_event_instance_id") is None
        and isinstance(before.get("revision"), int)
        and isinstance(after.get("revision"), int)
        and int(before["revision"]) < int(after["revision"])
    )
    if not valid:
        raise IncidentSourceCaptureEntryError(
            "incident_source_player_switch_receipt_invalid",
            {
                "initial_player_character_id": initial_player_character_id,
                "target_subject_character_id": target_subject_character_id,
                "before": dict(before),
                "after": dict(after),
                "native_receipt": native,
            },
        )
    return {
        "schema_version": 1,
        "kind": PLAYER_SWITCH_RECEIPT_KIND,
        "result": "GREEN",
        "evidence_class": "real_ck3",
        "state_origin": "managed_product",
        "seed_lineage_id": seed_lineage_id,
        "initial_player_character_id": initial_player_character_id,
        "target_subject_character_id": target_subject_character_id,
        "date_raw": int(after["date_raw"]),
        "before_binding": deepcopy(dict(before)),
        "after_binding": deepcopy(dict(after)),
        "native_receipt": native,
        "generic_character_rebind_used": True,
        "generic_character_rebind_authority": GENERIC_REBIND_AUTHORITY,
        "provider_observed": True,
        "action_ack_used_as_state_evidence": False,
    }


def validate_incident_source_player_switch_receipt(
    value: object,
    *,
    seed_lineage_id: str,
    tracked_ck3_pid: int,
    initial_player_character_id: int = INITIAL_PLAYER_CHARACTER_ID,
    target_subject_character_id: int = TARGET_SUBJECT_CHARACTER_ID,
) -> dict[str, object]:
    """Re-hash and validate one frozen native switch receipt."""

    locator = deepcopy(dict(value)) if isinstance(value, Mapping) else {}
    payload = locator.get("payload")
    payload = deepcopy(dict(payload)) if isinstance(payload, Mapping) else {}
    before = payload.get("before_binding")
    before = dict(before) if isinstance(before, Mapping) else {}
    after = payload.get("after_binding")
    after = dict(after) if isinstance(after, Mapping) else {}
    raw_path = locator.get("path")
    path = Path(str(raw_path)).resolve() if isinstance(raw_path, str) else Path()
    expected_sha = str(locator.get("sha256", "")).upper()
    file_payload = None
    if path.is_file():
        try:
            file_payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            file_payload = None
    normalized = _player_switch_receipt(
        payload.get("native_receipt"),
        before=before,
        after=after,
        seed_lineage_id=seed_lineage_id,
        initial_player_character_id=initial_player_character_id,
        target_subject_character_id=target_subject_character_id,
    )
    valid = (
        isinstance(raw_path, str)
        and Path(raw_path).is_absolute()
        and path.is_file()
        and isinstance(locator.get("bytes"), int)
        and not isinstance(locator.get("bytes"), bool)
        and locator.get("bytes") == path.stat().st_size
        and len(expected_sha) == 64
        and expected_sha == _sha256(path)
        and file_payload == payload == normalized
        and before.get("bridge_pid") == tracked_ck3_pid
        and after.get("bridge_pid") == tracked_ck3_pid
    )
    if not valid:
        raise IncidentSourceCaptureEntryError(
            "incident_source_player_switch_receipt_invalid",
            {
                "player_switch_receipt": locator,
                "tracked_ck3_pid": tracked_ck3_pid,
            },
        )
    return locator


def switch_incident_source_subject_v1(
    service: IncidentSourceCaptureService,
    *,
    receipt_path: Path,
    seed_lineage_id: str,
    capture_lineage: Mapping[str, object],
    tracked_ck3_pid: int,
    initial_player_character_id: int = INITIAL_PLAYER_CHARACTER_ID,
    target_subject_character_id: int = TARGET_SUBJECT_CHARACTER_ID,
) -> dict[str, object]:
    """Switch the paused owner to the target and freeze transport evidence.

    The returned locator can be retained while an external single-threaded
    production driver advances the same managed session to ``zg361.50``.
    """

    before_switch = _switch_binding(service.snapshot(), require_event_free=True)
    if before_switch["bridge_pid"] != tracked_ck3_pid:
        raise IncidentSourceCaptureEntryError(
            "incident_source_managed_session_mismatch",
            {
                "tracked_ck3_pid": tracked_ck3_pid,
                "observed_bridge_pid": before_switch["bridge_pid"],
            },
        )
    if before_switch["player_character_id"] != initial_player_character_id:
        raise IncidentSourceCaptureEntryError(
            "incident_source_initial_player_binding_mismatch",
            {
                "expected_initial_player_character_id": (
                    initial_player_character_id
                ),
                "observed_player_character_id": before_switch[
                    "player_character_id"
                ],
            },
        )
    native_switch = service.set_player_character_v1(
        target_subject_character_id,
        expected_revision=int(before_switch["revision"]),
    )
    after_switch = _switch_binding(service.snapshot(), require_event_free=True)
    switch_payload = _player_switch_receipt(
        native_switch,
        before=before_switch,
        after=after_switch,
        seed_lineage_id=seed_lineage_id,
        initial_player_character_id=initial_player_character_id,
        target_subject_character_id=target_subject_character_id,
    )
    _write_json_exclusive(receipt_path, switch_payload)
    locator = {**_record(receipt_path), "payload": switch_payload}
    locator = validate_incident_source_player_switch_receipt(
        locator,
        seed_lineage_id=seed_lineage_id,
        tracked_ck3_pid=tracked_ck3_pid,
        initial_player_character_id=initial_player_character_id,
        target_subject_character_id=target_subject_character_id,
    )
    effective_lineage = deepcopy(dict(capture_lineage))
    effective_lineage["generic_character_rebind_used"] = True
    effective_lineage["generic_character_rebind_authority"] = (
        GENERIC_REBIND_AUTHORITY
    )
    return {
        "schema_version": 1,
        "kind": "zg361_phase2_incident_source_subject_switch",
        "result": "GREEN",
        "player_switch_receipt": locator,
        "capture_lineage": effective_lineage,
        "generic_character_rebind_used": True,
        "generic_character_rebind_authority": GENERIC_REBIND_AUTHORITY,
    }


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
        "schema_version": REGISTRY_CAPTURE_ENTRY_SCHEMA_VERSION,
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
        "generic_character_rebind_used": True,
        "generic_character_rebind_authority": GENERIC_REBIND_AUTHORITY,
        "player_switch_receipt": deepcopy(summary["player_switch_receipt"]),
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
            "generic_character_rebind_used": True,
            "player_switch_receipt": {
                key: summary["player_switch_receipt"][key]
                for key in ("path", "bytes", "sha256")
            },
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
    player_switch_receipt: Mapping[str, object] | None = None,
    initial_player_character_id: int = INITIAL_PLAYER_CHARACTER_ID,
    target_subject_character_id: int = TARGET_SUBJECT_CHARACTER_ID,
    timeout_seconds: float = 120.0,
    poll_interval_seconds: float = 0.25,
    monotonic: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
) -> dict[str, object]:
    """Wait read-only for a real event, then persist its strict checkpoint."""

    switch_receipt_path = receipt_path.resolve().parent / "player-switch-receipt.json"
    output_paths = {
        "receipt": receipt_path.resolve(),
        "registry_entry": registry_entry_path.resolve(),
    }
    if player_switch_receipt is None:
        output_paths["player_switch_receipt"] = switch_receipt_path
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
        "generic_character_rebind_used": False,
        "generic_character_rebind_authority": None,
        "initial_player_character_id": initial_player_character_id,
        "target_subject_character_id": target_subject_character_id,
        "player_switch_receipt": None,
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
        or not isinstance(initial_player_character_id, int)
        or isinstance(initial_player_character_id, bool)
        or initial_player_character_id <= 0
        or not isinstance(target_subject_character_id, int)
        or isinstance(target_subject_character_id, bool)
        or target_subject_character_id <= 0
        or initial_player_character_id == target_subject_character_id
    ):
        fail(
            "incident_source_capture_arguments_invalid",
            {
                "timeout_seconds": timeout_seconds,
                "poll_interval_seconds": poll_interval_seconds,
                "tracked_ck3_pid": tracked_ck3_pid,
                "initial_player_character_id": initial_player_character_id,
                "target_subject_character_id": target_subject_character_id,
            },
        )
    existing = [str(path) for path in output_paths.values() if path.exists()]
    if existing:
        fail(
            "incident_source_capture_output_already_exists",
            {"existing_outputs": existing},
        )

    try:
        if player_switch_receipt is None:
            switched = switch_incident_source_subject_v1(
                service,
                receipt_path=switch_receipt_path,
                seed_lineage_id=seed_lineage_id,
                capture_lineage=capture_lineage,
                tracked_ck3_pid=tracked_ck3_pid,
                initial_player_character_id=initial_player_character_id,
                target_subject_character_id=target_subject_character_id,
            )
            switch_locator = deepcopy(switched["player_switch_receipt"])
            effective_lineage = deepcopy(switched["capture_lineage"])
        else:
            switch_locator = validate_incident_source_player_switch_receipt(
                player_switch_receipt,
                seed_lineage_id=seed_lineage_id,
                tracked_ck3_pid=tracked_ck3_pid,
                initial_player_character_id=initial_player_character_id,
                target_subject_character_id=target_subject_character_id,
            )
            effective_lineage = deepcopy(dict(capture_lineage))
            effective_lineage["generic_character_rebind_used"] = True
            effective_lineage["generic_character_rebind_authority"] = (
                GENERIC_REBIND_AUTHORITY
            )
    except IncidentSourceCaptureEntryError as error:
        fail(error.reason_code, error.evidence)
    except Exception as error:
        fail(
            "incident_source_player_switch_failed",
            {
                "error_type": type(error).__name__,
                "message": str(error),
            },
        )
    evidence.update(
        {
            "generic_character_rebind_used": True,
            "generic_character_rebind_authority": GENERIC_REBIND_AUTHORITY,
            "player_switch_receipt": deepcopy(switch_locator),
        }
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
                    capture_lineage=effective_lineage,
                    player_switch_receipt=switch_locator,
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
                            REGISTRY_CAPTURE_ENTRY_SCHEMA_VERSION
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
                    "generic_character_rebind_used": True,
                    "generic_character_rebind_authority": (
                        GENERIC_REBIND_AUTHORITY
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


def produce_and_capture_incident_source_checkpoint(
    service: IncidentSourceCaptureService,
    *,
    evidence_path: Path,
    checkpoint_root: Path,
    receipt_path: Path,
    registry_entry_path: Path,
    seed_lineage_id: str,
    capture_lineage: Mapping[str, object],
    tracked_ck3_pid: int,
    production_evidence_out: dict[str, object] | None = None,
    initial_player_character_id: int = INITIAL_PLAYER_CHARACTER_ID,
    target_subject_character_id: int = TARGET_SUBJECT_CHARACTER_ID,
    timeout_seconds: float = 120.0,
    poll_interval_seconds: float = 0.25,
    monotonic: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
    runtime_diagnostic_probe: Callable[[], str | None] | None = None,
) -> dict[str, object]:
    """Drive the product to ``zg361.50`` and then freeze it read-only.

    The switch is deliberately separated from the production timeline entry:
    its immutable receipt proves that the same managed subject was selected
    before any map advance.  The production entry owns every advance and
    interrupt drain, stops on the real event identity, and only then hands the
    already-visible paused frame to the capture-only helper above.
    """

    switch_receipt_path = (
        receipt_path.resolve().parent / "player-switch-receipt.json"
    )
    # ``run_zhongguo_acceptance`` imports this capture module before it adds
    # the autonomous-player source tree to ``sys.path``.  Delay the production
    # dependency until runtime, after the runner has completed that bootstrap.
    from zg361_phase2_promotion_source_production_entry import (
        PromotionProductionEntryError,
        enter_promotion_source_checkpoint_v1,
    )

    switched = switch_incident_source_subject_v1(
        service,
        receipt_path=switch_receipt_path,
        seed_lineage_id=seed_lineage_id,
        capture_lineage=capture_lineage,
        tracked_ck3_pid=tracked_ck3_pid,
        initial_player_character_id=initial_player_character_id,
        target_subject_character_id=target_subject_character_id,
    )
    production_evidence = (
        {} if production_evidence_out is None else production_evidence_out
    )
    try:
        production = enter_promotion_source_checkpoint_v1(
            service,
            timeout_seconds=timeout_seconds,
            poll_interval_seconds=poll_interval_seconds,
            pause_on_event_definition_key=SOURCE_EVENT_DEFINITION_KEY,
            clock=monotonic,
            sleeper=sleep,
            evidence_out=production_evidence,
            runtime_diagnostic_probe=runtime_diagnostic_probe,
        )
    except PromotionProductionEntryError as error:
        raise IncidentSourceCaptureEntryError(
            "incident_source_production_entry_failed",
            {
                "error_type": type(error).__name__,
                "message": str(error),
                "production_entry": deepcopy(production_evidence),
            },
        ) from error
    if not (
        production.get("result") == "GREEN"
        and production.get("readiness")
        == f"paused-real-{SOURCE_EVENT_DEFINITION_KEY}"
        and isinstance(production.get("target_binding"), Mapping)
    ):
        raise IncidentSourceCaptureEntryError(
            "incident_source_production_target_unproven",
            {"production_entry": deepcopy(production)},
        )
    return wait_for_and_capture_incident_source_checkpoint(
        service,
        evidence_path=evidence_path,
        checkpoint_root=checkpoint_root,
        receipt_path=receipt_path,
        registry_entry_path=registry_entry_path,
        seed_lineage_id=seed_lineage_id,
        capture_lineage=capture_lineage,
        tracked_ck3_pid=tracked_ck3_pid,
        player_switch_receipt=switched["player_switch_receipt"],
        initial_player_character_id=initial_player_character_id,
        target_subject_character_id=target_subject_character_id,
        timeout_seconds=timeout_seconds,
        poll_interval_seconds=poll_interval_seconds,
        monotonic=monotonic,
        sleep=sleep,
    )


__all__ = [
    "GENERIC_REBIND_AUTHORITY",
    "INITIAL_PLAYER_CHARACTER_ID",
    "LIVE_CAPTURE_KIND",
    "PLAYER_SWITCH_RECEIPT_KIND",
    "REGISTRY_CAPTURE_ENTRY_KIND",
    "SOURCE_EVENT_DEFINITION_KEY",
    "TARGET_SUBJECT_CHARACTER_ID",
    "IncidentSourceCaptureEntryError",
    "IncidentSourceCaptureService",
    "build_schema2_incident_registry_capture_entry",
    "produce_and_capture_incident_source_checkpoint",
    "switch_incident_source_subject_v1",
    "validate_incident_source_player_switch_receipt",
    "wait_for_and_capture_incident_source_checkpoint",
]
