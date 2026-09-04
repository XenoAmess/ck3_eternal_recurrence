#!/usr/bin/env python3
"""Capture the real owner-facing ``zg361we.356`` Phase2 source checkpoint.

This is a wait/query/save primitive for an already-running managed product
session.  It cannot advance the timeline, select an option, load a fixture, or
rebind a character.  A completed capture is appended to three previously
captured real source entries and assembled through the canonical schema-2
registry builder.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import shutil
import time
from typing import Callable, Final, Mapping, Protocol

from zg361_phase2_cross_cycle_endgame_action_cell import (
    CrossCycleEndgameCellError,
    HANDLER,
    PRODUCER_KEY,
    SOURCE_EVENT,
    SPAN_ID,
    _event_surface,
    _paused_binding,
)
from zg361_phase2_incident_checkpoint_seam import (
    IncidentCheckpointSeamError,
    validate_received_self_incident_checkpoint_receipt,
)
from zhongguo_phase2_event_choreography import PHASE2_EVENT_SEQUENCE_PLANS
from zhongguo_phase2_source_checkpoint_provider import (
    CHECKPOINT_REQUIRED_HANDLERS,
    INCIDENT_STRICT_RECEIPT_FIELD,
    SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION,
)
from zhongguo_phase2_source_checkpoint_registry import (
    SOURCE_CHECKPOINT_CAPTURE_MANIFEST_KIND,
    build_registry_from_capture_manifest,
)


CAPTURE_PREFIX_KIND: Final = (
    "zg361_phase2_source_checkpoint_capture_manifest_live_pending"
)
CAPTURE_RECEIPT_KIND: Final = (
    "zg361_phase2_cross_cycle_endgame_source_checkpoint_v1"
)
DEFAULT_WAIT_TIMEOUT_SECONDS: Final = 300.0
DEFAULT_POLL_INTERVAL_SECONDS: Final = 0.10
_SHA256: Final = re.compile(r"^[0-9A-F]{64}$")
_PLAN_BY_HANDLER: Final = {
    plan.handler: plan
    for plan in PHASE2_EVENT_SEQUENCE_PLANS
    if plan.handler in CHECKPOINT_REQUIRED_HANDLERS
}
_PREFIX_HANDLERS: Final = CHECKPOINT_REQUIRED_HANDLERS[:-1]


class EndgameSourceCaptureService(Protocol):
    def snapshot(self) -> dict[str, object]: ...

    def query_current_event_window_context_v1(
        self, event_instance_id: int, *, expected_revision: int
    ) -> dict[str, object]: ...

    def save_checkpoint(
        self, *, expected_revision: int | None = None
    ) -> dict[str, object]: ...


class EndgameSourceCaptureError(RuntimeError):
    """Typed RED for prefix, live surface, or materialized-save failures."""

    result: Final = "RED"

    def __init__(self, reason_code: str, evidence: Mapping[str, object]) -> None:
        self.reason_code = reason_code
        self.evidence = {
            **deepcopy(dict(evidence)),
            "result": "RED",
            "reason_code": reason_code,
        }
        super().__init__(f"cross-cycle endgame source capture RED [{reason_code}]")


RegistryAssembler = Callable[..., Mapping[str, object]]


def _fail(reason_code: str, **evidence: object) -> None:
    raise EndgameSourceCaptureError(reason_code, evidence)


def _positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _read_json_object(path: Path, *, reason_code: str) -> dict[str, object]:
    target = path.expanduser().resolve()
    try:
        value = json.loads(target.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        _fail(
            reason_code,
            path=str(target),
            error=f"{type(error).__name__}: {error}",
        )
    if not isinstance(value, dict):
        _fail(reason_code, path=str(target), root_type=type(value).__name__)
    return value


def _write_json_exclusive(path: Path, value: Mapping[str, object]) -> None:
    target = path.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with target.open("x", encoding="utf-8", newline="\n") as output:
            json.dump(value, output, ensure_ascii=False, indent=2, sort_keys=True)
            output.write("\n")
    except FileExistsError as error:
        _fail("source_capture_output_already_exists", path=str(target))


def _validate_capture_lineage(
    value: object, *, seed_lineage_id: str, label: str
) -> dict[str, object]:
    lineage = deepcopy(dict(value)) if isinstance(value, Mapping) else {}
    mod_mount = lineage.get("mod_mount")
    valid = (
        lineage.get("seed_lineage_id") == seed_lineage_id
        and lineage.get("evidence_class") == "real_ck3"
        and lineage.get("fixture_used") is False
        and lineage.get("console_used") is False
        and isinstance(mod_mount, Mapping)
        and mod_mount.get("kind") == "product-only"
        and isinstance(mod_mount.get("tree_sha256"), str)
        and _SHA256.fullmatch(str(mod_mount.get("tree_sha256", "")).upper())
        is not None
    )
    if not valid:
        _fail(
            "source_capture_lineage_invalid",
            label=label,
            seed_lineage_id=seed_lineage_id,
            capture_lineage=lineage,
        )
    return lineage


def _validate_prefix_entry(
    raw: object, *, handler: str, seed_lineage_id: str
) -> dict[str, object]:
    row = deepcopy(dict(raw)) if isinstance(raw, Mapping) else {}
    plan = _PLAN_BY_HANDLER[handler]
    checkpoint = row.get("checkpoint")
    checkpoint = dict(checkpoint) if isinstance(checkpoint, Mapping) else {}
    receipt = row.get("source_receipt")
    receipt = dict(receipt) if isinstance(receipt, Mapping) else {}
    raw_path = checkpoint.get("path")
    path = (
        Path(raw_path).expanduser().resolve()
        if isinstance(raw_path, str) and Path(raw_path).is_absolute()
        else Path()
    )
    checkpoint_sha256 = str(checkpoint.get("sha256", "")).upper()
    owner = row.get("owner_character_id")
    player = row.get("player_character_id")
    date_raw = row.get("date_raw")
    valid = (
        row.get("span_id") == plan.span_id
        and row.get("handler") == handler
        and row.get("source_event_definition_key") == plan.source_event
        and _positive_int(owner)
        and _positive_int(player)
        and isinstance(date_raw, int)
        and not isinstance(date_raw, bool)
        and path.is_absolute()
        and path.is_file()
        and _positive_int(checkpoint.get("bytes"))
        and path.stat().st_size == checkpoint.get("bytes")
        and _SHA256.fullmatch(checkpoint_sha256) is not None
        and _sha256_file(path) == checkpoint_sha256
        and checkpoint.get("save_lineage_id") == seed_lineage_id
        and receipt.get("result") == "GREEN"
        and receipt.get("evidence_class") == "real_ck3"
        and receipt.get("provider_observed") is True
        and receipt.get("ui_state_verified") is True
        and receipt.get("fixture_used") is False
        and receipt.get("console_used") is False
        and receipt.get("span_id") == plan.span_id
        and receipt.get("event_definition_key") == plan.source_event
        and receipt.get("owner_character_id") == owner
        and receipt.get("player_character_id") == player
        and receipt.get("date_raw") == date_raw
        and str(receipt.get("checkpoint_sha256", "")).upper()
        == checkpoint_sha256
        and receipt.get("save_lineage_id") == seed_lineage_id
    )
    if not valid:
        _fail(
            "source_capture_prefix_entry_invalid",
            handler=handler,
            entry=row,
        )
    if handler == "capture_incidents_operations":
        strict = row.get(INCIDENT_STRICT_RECEIPT_FIELD)
        try:
            summary = validate_received_self_incident_checkpoint_receipt(
                strict,
                expected_seed_lineage_id=seed_lineage_id,
            )
        except IncidentCheckpointSeamError as error:
            _fail(
                "source_capture_prefix_incident_receipt_invalid",
                upstream_reason_code=error.reason_code,
                upstream_evidence=error.evidence,
            )
        strict_checkpoint = summary.get("checkpoint")
        strict_valid = (
            isinstance(strict_checkpoint, Mapping)
            and Path(str(strict_checkpoint.get("path"))).resolve() == path
            and strict_checkpoint.get("bytes") == checkpoint.get("bytes")
            and strict_checkpoint.get("sha256") == checkpoint_sha256
            and summary.get("owner_character_id") == owner
            and summary.get("player_character_id") == player
            and summary.get("date_raw") == date_raw
        )
        if not strict_valid:
            _fail(
                "source_capture_prefix_incident_binding_mismatch",
                entry=row,
                strict_receipt_summary=summary,
            )
    elif INCIDENT_STRICT_RECEIPT_FIELD in row:
        _fail("source_capture_prefix_incident_receipt_misrouted", handler=handler)
    return row


def preflight_endgame_source_capture_prefix(
    prefix: Mapping[str, object] | Path,
    *,
    expected_seed_lineage_id: str | None = None,
    runtime_capture_lineage: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Read-only validation of the first three real source capture rows."""

    manifest = (
        _read_json_object(
            prefix, reason_code="source_capture_prefix_unreadable"
        )
        if isinstance(prefix, Path)
        else deepcopy(dict(prefix))
    )
    seed_lineage_id = manifest.get("seed_lineage_id")
    entries = manifest.get("entries")
    header_valid = (
        manifest.get("schema_version")
        == SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION
        and manifest.get("kind") == CAPTURE_PREFIX_KIND
        and manifest.get("result") == "LIVE_PENDING"
        and manifest.get("readiness") == "live-pending-endgame-source"
        and manifest.get("evidence_class") == "real_ck3"
        and manifest.get("fixture_used") is False
        and manifest.get("console_used") is False
        and isinstance(seed_lineage_id, str)
        and bool(seed_lineage_id)
        and (
            expected_seed_lineage_id is None
            or seed_lineage_id == expected_seed_lineage_id
        )
        and isinstance(entries, list)
    )
    if not header_valid:
        _fail(
            "source_capture_prefix_header_invalid",
            expected_seed_lineage_id=expected_seed_lineage_id,
            manifest=manifest,
        )
    assert isinstance(seed_lineage_id, str)
    assert isinstance(entries, list)
    lineage = _validate_capture_lineage(
        manifest.get("capture_lineage"),
        seed_lineage_id=seed_lineage_id,
        label="prefix",
    )
    observed_handlers = tuple(
        row.get("handler") if isinstance(row, Mapping) else None
        for row in entries
    )
    if observed_handlers != _PREFIX_HANDLERS:
        _fail(
            "source_capture_prefix_coverage_invalid",
            expected_handlers=list(_PREFIX_HANDLERS),
            observed_handlers=list(observed_handlers),
        )
    validated_entries = [
        _validate_prefix_entry(
            row,
            handler=handler,
            seed_lineage_id=seed_lineage_id,
        )
        for row, handler in zip(entries, _PREFIX_HANDLERS, strict=True)
    ]
    runtime_lineage = None
    if runtime_capture_lineage is not None:
        runtime_lineage = _validate_capture_lineage(
            runtime_capture_lineage,
            seed_lineage_id=seed_lineage_id,
            label="runtime",
        )
        prefix_mount = lineage["mod_mount"]
        runtime_mount = runtime_lineage["mod_mount"]
        prefix_game = lineage.get("game")
        runtime_game = runtime_lineage.get("game")
        same_exact_product = (
            isinstance(prefix_mount, Mapping)
            and isinstance(runtime_mount, Mapping)
            and str(prefix_mount.get("tree_sha256", "")).upper()
            == str(runtime_mount.get("tree_sha256", "")).upper()
            and prefix_mount.get("enabled_mods")
            == runtime_mount.get("enabled_mods")
            and isinstance(prefix_game, Mapping)
            and isinstance(runtime_game, Mapping)
            and prefix_game.get("version") == runtime_game.get("version")
            and str(prefix_game.get("exe_sha256", "")).upper()
            == str(runtime_game.get("exe_sha256", "")).upper()
        )
        if not same_exact_product:
            _fail(
                "source_capture_runtime_lineage_mismatch",
                prefix_capture_lineage=lineage,
                runtime_capture_lineage=runtime_lineage,
            )
    return {
        "schema_version": SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION,
        "result": "GREEN",
        "readiness": "live-pending-endgame-source",
        "seed_lineage_id": seed_lineage_id,
        "capture_lineage": lineage,
        "runtime_capture_lineage": runtime_lineage,
        "entry_count": len(validated_entries),
        "handlers": list(observed_handlers),
        "entries": validated_entries,
        "fixture_used": False,
        "console_used": False,
    }


def _wait_for_source_surface(
    service: EndgameSourceCaptureService,
    *,
    expected_owner_character_id: int,
    expected_date_raw: int,
    timeout_seconds: float,
    poll_interval_seconds: float,
) -> tuple[dict[str, object], dict[str, object], dict[str, object], int]:
    if (
        not _positive_int(expected_owner_character_id)
        or not isinstance(expected_date_raw, int)
        or isinstance(expected_date_raw, bool)
        or timeout_seconds <= 0
        or poll_interval_seconds < 0
    ):
        raise ValueError("endgame source capture wait contract is invalid")
    deadline = time.monotonic() + timeout_seconds
    observations: list[dict[str, object]] = []
    while time.monotonic() < deadline:
        snapshot = service.snapshot()
        if not isinstance(snapshot, Mapping):
            _fail("source_snapshot_not_an_object", snapshot=snapshot)
        played = snapshot.get("played_character")
        player = played.get("character_id") if isinstance(played, Mapping) else None
        date_raw = snapshot.get("date_raw")
        if player != expected_owner_character_id:
            _fail(
                "source_owner_mismatch",
                expected_owner_character_id=expected_owner_character_id,
                observed_player_character_id=player,
            )
        if date_raw != expected_date_raw:
            _fail(
                "source_date_mismatch",
                expected_date_raw=expected_date_raw,
                observed_date_raw=date_raw,
            )
        active = snapshot.get("active_event")
        observations.append(
            {
                "snapshot_id": snapshot.get("snapshot_id"),
                "revision": snapshot.get("revision"),
                "native_revision": snapshot.get("native_revision"),
                "date_raw": date_raw,
                "paused": snapshot.get("paused"),
                "map_ready": snapshot.get("map_ready"),
                "player_character_id": player,
                "event_instance_id": (
                    active.get("instance_id")
                    if isinstance(active, Mapping)
                    else None
                ),
            }
        )
        if not isinstance(active, Mapping):
            if poll_interval_seconds:
                time.sleep(poll_interval_seconds)
            continue
        try:
            binding = _paused_binding(
                snapshot,
                expected_player=expected_owner_character_id,
                require_event=True,
            )
            context, owner, subject = _event_surface(
                service,
                binding,
                expected_event=SOURCE_EVENT,
                expected_owner=expected_owner_character_id,
                expected_subject=None,
            )
        except CrossCycleEndgameCellError as error:
            observed_context = error.evidence.get("response")
            observed_frame = (
                observed_context.get("current_event_window_context")
                if isinstance(observed_context, Mapping)
                else None
            )
            observed_event = (
                observed_frame.get("event_definition_key")
                if isinstance(observed_frame, Mapping)
                else None
            )
            if isinstance(observed_event, str) and observed_event != SOURCE_EVENT:
                _fail(
                    "source_event_identity_mismatch",
                    expected_event_definition_key=SOURCE_EVENT,
                    observed_event_definition_key=observed_event,
                    upstream_evidence=error.evidence,
                )
            if error.reason_code in {
                "event_owner_subject_binding_invalid",
                "event_owner_drifted",
                "event_option_surface_invalid",
            }:
                _fail(
                    "source_event_surface_invalid",
                    upstream_reason_code=error.reason_code,
                    upstream_evidence=error.evidence,
                )
            if poll_interval_seconds:
                time.sleep(poll_interval_seconds)
            continue
        return dict(snapshot), dict(binding), context, subject
    _fail(
        "source_event_wait_timed_out",
        expected_event_definition_key=SOURCE_EVENT,
        expected_owner_character_id=expected_owner_character_id,
        expected_date_raw=expected_date_raw,
        observations=observations[-64:],
    )


def _native_save_contract(
    value: object, *, binding: Mapping[str, object]
) -> tuple[Path, dict[str, object]]:
    result = deepcopy(dict(value)) if isinstance(value, Mapping) else {}
    checkpoint = result.get("checkpoint")
    checkpoint = dict(checkpoint) if isinstance(checkpoint, Mapping) else {}
    materialization = result.get("materialization")
    raw_path = checkpoint.get("path")
    path = Path(raw_path).resolve() if isinstance(raw_path, str) else Path()
    size = checkpoint.get("size")
    sha256 = str(checkpoint.get("sha256", "")).upper()
    valid = (
        result.get("accepted") is True
        and checkpoint.get("status") == "saved"
        and isinstance(raw_path, str)
        and Path(raw_path).is_absolute()
        and path.is_file()
        and _positive_int(size)
        and path.stat().st_size == size
        and _SHA256.fullmatch(sha256) is not None
        and _sha256_file(path) == sha256
        and checkpoint.get("date_raw") == binding.get("date_raw")
        and checkpoint.get("episode_character_id")
        == binding.get("player_character_id")
        and isinstance(checkpoint.get("strategy"), str)
        and bool(checkpoint.get("strategy"))
        and isinstance(materialization, Mapping)
        and materialization.get("available") is True
    )
    if not valid:
        _fail("source_native_save_invalid", native_save_result=result)
    return path, result


def capture_cross_cycle_endgame_source_checkpoint_v1(
    service: EndgameSourceCaptureService,
    *,
    prefix_manifest: Mapping[str, object] | Path,
    capture_input_root: Path,
    receipt_path: Path,
    completed_manifest_path: Path,
    registry_checkpoint_root: Path,
    registry_path: Path,
    expected_owner_character_id: int,
    expected_date_raw: int,
    runtime_capture_lineage: Mapping[str, object],
    timeout_seconds: float = DEFAULT_WAIT_TIMEOUT_SECONDS,
    poll_interval_seconds: float = DEFAULT_POLL_INTERVAL_SECONDS,
    registry_assembler: RegistryAssembler = build_registry_from_capture_manifest,
) -> dict[str, object]:
    """Wait for #356, freeze it, then emit the complete schema-2 registry."""

    for output in (
        receipt_path,
        completed_manifest_path,
        completed_manifest_path.resolve().with_name(
            completed_manifest_path.resolve().name + ".assembling"
        ),
        registry_path,
    ):
        if output.resolve().exists():
            _fail(
                "source_capture_output_already_exists",
                path=str(output.resolve()),
            )
    prefix = preflight_endgame_source_capture_prefix(
        prefix_manifest,
        runtime_capture_lineage=runtime_capture_lineage,
    )
    seed_lineage_id = str(prefix["seed_lineage_id"])
    source_snapshot, before, event_context, subject = _wait_for_source_surface(
        service,
        expected_owner_character_id=expected_owner_character_id,
        expected_date_raw=expected_date_raw,
        timeout_seconds=timeout_seconds,
        poll_interval_seconds=poll_interval_seconds,
    )
    save_result = service.save_checkpoint(
        expected_revision=int(before["revision"])
    )
    materialized_path, native_save = _native_save_contract(
        save_result,
        binding=before,
    )
    after_snapshot = service.snapshot()
    try:
        after = _paused_binding(
            after_snapshot,
            expected_player=expected_owner_character_id,
            require_event=True,
        )
        after_context, after_owner, after_subject = _event_surface(
            service,
            after,
            expected_event=SOURCE_EVENT,
            expected_owner=expected_owner_character_id,
            expected_subject=subject,
        )
    except CrossCycleEndgameCellError as error:
        _fail(
            "source_post_save_surface_invalid",
            upstream_reason_code=error.reason_code,
            upstream_evidence=error.evidence,
        )
    stable_keys = (
        "native_revision",
        "date_raw",
        "player_character_id",
        "event_instance_id",
    )
    if any(before.get(key) != after.get(key) for key in stable_keys):
        _fail("source_save_crossed_binding", before=before, after=after)
    if after_owner != expected_owner_character_id or after_subject != subject:
        _fail(
            "source_save_owner_subject_drifted",
            before_owner=expected_owner_character_id,
            before_subject=subject,
            after_owner=after_owner,
            after_subject=after_subject,
        )

    source_bytes = materialized_path.stat().st_size
    source_sha256 = _sha256_file(materialized_path)
    archive_root = capture_input_root.resolve()
    archive_root.mkdir(parents=True, exist_ok=True)
    archive = archive_root / (
        "phase2-cross-cycle-endgame-zg361we-356-"
        f"{source_sha256[:16].lower()}.ck3"
    )
    if archive.exists():
        _fail("source_capture_archive_already_exists", archive_path=str(archive))
    shutil.copyfile(materialized_path, archive)
    if archive.stat().st_size != source_bytes or _sha256_file(archive) != source_sha256:
        _fail(
            "source_capture_archive_mismatch",
            source_path=str(materialized_path),
            archive_path=str(archive),
        )

    prefix_lineage = deepcopy(dict(prefix["capture_lineage"]))
    prefix_lineage["endgame_capture_session"] = deepcopy(
        dict(runtime_capture_lineage)
    )
    prefix_lineage["capture_lineage_mode"] = (
        "same-seed-exact-product-multi-session"
    )
    receipt = {
        "schema_version": 1,
        "kind": CAPTURE_RECEIPT_KIND,
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
        "event_definition_key": SOURCE_EVENT,
        "source_event_definition_key": SOURCE_EVENT,
        "owner_character_id": expected_owner_character_id,
        "subject_character_id": subject,
        "player_character_id": expected_owner_character_id,
        "event_instance_id": int(before["event_instance_id"]),
        "date_raw": expected_date_raw,
        "paused": True,
        "map_ready": True,
        "checkpoint_sha256": source_sha256,
        "save_lineage_id": seed_lineage_id,
        "seed_lineage_id": seed_lineage_id,
        "capture_lineage": prefix_lineage,
        "source_snapshot": source_snapshot,
        "source_snapshot_binding": before,
        "post_save_snapshot_binding": after,
        "event_context": event_context,
        "post_save_event_context": after_context,
        "native_save_receipt": native_save,
        "checkpoint": {
            "path": str(archive.resolve()),
            "bytes": source_bytes,
            "sha256": source_sha256,
            "save_lineage_id": seed_lineage_id,
        },
        "capture_checks": {
            "managed_product_event_observed": True,
            "owner_facing_root_bound": True,
            "exact_date_bound": True,
            "three_options_shown_enabled": True,
            "provider_ui_query_same_frame": True,
            "native_save_same_frame": True,
            "checkpoint_bytes_hash_bound": True,
            "action_ack_used_as_state_evidence": False,
        },
    }
    entries = deepcopy(list(prefix["entries"]))
    entries.append(
        {
            "span_id": SPAN_ID,
            "handler": HANDLER,
            "source_event_definition_key": SOURCE_EVENT,
            "owner_character_id": expected_owner_character_id,
            "player_character_id": expected_owner_character_id,
            "date_raw": expected_date_raw,
            "checkpoint": deepcopy(receipt["checkpoint"]),
            "source_receipt": deepcopy(receipt),
        }
    )
    completed_manifest = {
        "schema_version": SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION,
        "kind": SOURCE_CHECKPOINT_CAPTURE_MANIFEST_KIND,
        "result": "GREEN",
        "readiness": "captured-all-source-checkpoints",
        "evidence_class": "real_ck3",
        "fixture_used": False,
        "console_used": False,
        "seed_lineage_id": seed_lineage_id,
        "capture_lineage": prefix_lineage,
        "entries": entries,
    }
    manifest_target = completed_manifest_path.resolve()
    manifest_candidate = manifest_target.with_name(
        manifest_target.name + ".assembling"
    )
    _write_json_exclusive(manifest_candidate, completed_manifest)
    try:
        registry = registry_assembler(
            manifest_candidate,
            checkpoint_root=registry_checkpoint_root,
            registry_path=registry_path,
        )
    except Exception as error:
        try:
            manifest_candidate.unlink(missing_ok=True)
        except OSError:
            pass
        _fail(
            "source_registry_assembly_failed",
            error_type=type(error).__name__,
            message=str(error),
        )
    if manifest_target.exists():
        _fail(
            "source_capture_output_already_exists",
            path=str(manifest_target),
        )
    manifest_candidate.replace(manifest_target)
    _write_json_exclusive(receipt_path, receipt)
    return {
        "schema_version": 1,
        "kind": CAPTURE_RECEIPT_KIND,
        "result": "GREEN",
        "readiness": "live-pending",
        "source_checkpoint_captured": True,
        "phase2_complete": False,
        "seed_lineage_id": seed_lineage_id,
        "capture_lineage": prefix_lineage,
        "source_receipt": receipt,
        "capture_manifest": {
            "path": str(manifest_target),
            "bytes": manifest_target.stat().st_size,
            "sha256": _sha256_file(manifest_target),
        },
        "registry": deepcopy(dict(registry)),
        "registry_artifact": {
            "path": str(registry_path.resolve()),
            "bytes": registry_path.stat().st_size,
            "sha256": _sha256_file(registry_path),
        },
        "fixture_used": False,
        "console_used": False,
        "action_ack_only": False,
    }


__all__ = [
    "CAPTURE_PREFIX_KIND",
    "CAPTURE_RECEIPT_KIND",
    "DEFAULT_WAIT_TIMEOUT_SECONDS",
    "DEFAULT_POLL_INTERVAL_SECONDS",
    "EndgameSourceCaptureError",
    "capture_cross_cycle_endgame_source_checkpoint_v1",
    "preflight_endgame_source_capture_prefix",
]
