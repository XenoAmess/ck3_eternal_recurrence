#!/usr/bin/env python3
"""Capture the real owner-facing ``zg361we.356`` Phase2 source checkpoint.

This is a wait/query/save primitive for an already-running managed product
session.  It cannot advance the timeline, select an option, or load a fixture.
After saving the owner-facing event it uses the explicit native character
switch once, to the event-bound subject, so the received-self Workforce
provider can prove that ``zg361we.356`` belongs to the third cycle rather than
an arbitrary earlier cycle.  A completed capture is appended to three
previously captured real source entries and assembled through the canonical
schema-2 registry builder.
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
    LEGACY_SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION,
    validate_endgame_maturity_source_receipt,
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
PRODUCT_ONLY_MULTI_SESSION_LINEAGE_KIND: Final = (
    "zg361_phase2_product_only_multi_session_capture_lineage"
)
PRODUCT_ONLY_MULTI_BRANCH_LINEAGE_KIND: Final = (
    "zg361_phase2_product_only_multi_branch_capture_lineage"
)
MULTI_BRANCH_CAPTURE_SCHEMA_VERSION: Final = 3
MULTI_BRANCH_CAPTURE_LINEAGE_MODE: Final = (
    "multi-branch-product-only-multi-session"
)
DEFAULT_WAIT_TIMEOUT_SECONDS: Final = 300.0
DEFAULT_POLL_INTERVAL_SECONDS: Final = 0.10
MATURE_ENDGAME_OWNER_CHARACTER_ID: Final = 32904
MATURE_ENDGAME_HISTORY_COUNT: Final = 2
MATURITY_QUERY_NONCE: Final = "zg361.endgame.source.maturity"
EVENT_SCALAR_CASE_BINDING_AUTHORITY: Final = (
    "paused-zg361we.356-value-scopes+source-trigger-full-guard+"
    "received-self-current-case-provider"
)
_EVENT_SCALAR_SCOPE_NAMES: Final = (
    "zg361_we_al_cycle",
    "zg361_we_al_case",
)
MATURITY_REQUIRED_BRIDGE_CAPABILITIES: Final = (
    "game.command.set-played-character-v1-N",
    "game.command.query-zhongguo-workforce-collective-snapshot-v1",
)
_SHA256: Final = re.compile(r"^[0-9A-F]{64}$")
_PLAN_BY_HANDLER: Final = {
    plan.handler: plan
    for plan in PHASE2_EVENT_SEQUENCE_PLANS
    if plan.handler in CHECKPOINT_REQUIRED_HANDLERS
}
_PREFIX_HANDLERS: Final = CHECKPOINT_REQUIRED_HANDLERS[:-1]


class EndgameSourceCaptureService(Protocol):
    def capabilities(self) -> dict[str, object]: ...

    def snapshot(self) -> dict[str, object]: ...

    def query_current_event_window_context_v1(
        self, event_instance_id: int, *, expected_revision: int
    ) -> dict[str, object]: ...

    def save_checkpoint(
        self, *, expected_revision: int | None = None
    ) -> dict[str, object]: ...

    def set_player_character_v1(
        self, character_id: int, *, expected_revision: int
    ) -> dict[str, object]: ...

    def query_zhongguo_workforce_collective_snapshot_v1(
        self,
        request_nonce: str,
        *,
        expected_revision: int,
        owner_character_id: int,
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


def _typed_available(group: object, key: str) -> object:
    container = dict(group) if isinstance(group, Mapping) else {}
    field = container.get(key)
    if not (
        isinstance(field, Mapping)
        and set(field) == {"status", "value", "unavailable_reason"}
        and field.get("status") == "available"
        and field.get("unavailable_reason") is None
    ):
        _fail(
            "endgame_maturity_typed_field_unavailable",
            group=container,
            key=key,
        )
    return field.get("value")


def _typed_unavailable(group: object, key: str, reason: str) -> bool:
    container = dict(group) if isinstance(group, Mapping) else {}
    field = container.get(key)
    return bool(
        isinstance(field, Mapping)
        and set(field) == {"status", "value", "unavailable_reason"}
        and field.get("status") == "unavailable"
        and field.get("value") is None
        and field.get("unavailable_reason") == reason
    )


def _event_scalar_scope_binding(context: object) -> dict[str, object]:
    frame = dict(context) if isinstance(context, Mapping) else {}
    saved_rows = frame.get("saved_scopes")
    if not isinstance(saved_rows, list):
        _fail("source_event_scalar_scopes_missing", event_context=frame)
    rows = {
        str(row.get("name")): row.get("scope")
        for row in saved_rows
        if isinstance(row, Mapping) and isinstance(row.get("name"), str)
    }
    if any(
        sum(
            isinstance(row, Mapping) and row.get("name") == name
            for row in saved_rows
        )
        != 1
        for name in _EVENT_SCALAR_SCOPE_NAMES
    ):
        _fail("source_event_scalar_scopes_missing", event_context=frame)
    binding: dict[str, object] = {}
    for name in _EVENT_SCALAR_SCOPE_NAMES:
        scope = rows.get(name)
        scope = dict(scope) if isinstance(scope, Mapping) else {}
        raw_type_index = scope.get("raw_type_index")
        typed_identity = scope.get("typed_identity")
        typed_identity = (
            dict(typed_identity)
            if isinstance(typed_identity, Mapping)
            else {}
        )
        if not (
            scope.get("status") == "available"
            and _positive_int(raw_type_index)
            and raw_type_index != 4
            and scope.get("type_key") == "value"
            and scope.get("subtype") == 0
            and typed_identity
            == {
                "status": "unavailable",
                "reason": "generic_scope_payload_identity_not_closed",
            }
        ):
            _fail(
                "source_event_scalar_scope_invalid",
                scope_name=name,
                scope=scope,
            )
        binding[name] = {
            "status": "available",
            "raw_type_index": raw_type_index,
            "type_key": "value",
            "subtype": 0,
            "typed_identity": typed_identity,
        }
    return binding


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


def phase2_source_lineage_set_id(
    entry_capture_lineages: object,
) -> str:
    """Return the stable identity of ordered handler-to-seed bindings."""

    bindings = []
    if isinstance(entry_capture_lineages, list):
        for raw in entry_capture_lineages:
            row = raw if isinstance(raw, Mapping) else {}
            handler = row.get("handler")
            seed_lineage_id = row.get("seed_lineage_id")
            if not (
                isinstance(handler, str)
                and bool(handler)
                and isinstance(seed_lineage_id, str)
                and bool(seed_lineage_id)
            ):
                _fail(
                    "source_capture_lineage_set_binding_invalid",
                    entry_capture_lineage=deepcopy(dict(row)),
                )
            bindings.append(
                {
                    "handler": handler,
                    "seed_lineage_id": seed_lineage_id,
                    **(
                        {
                            "capture_run_input_checkpoint_sha256": str(
                                row["capture_run_input_checkpoint"]["sha256"]
                            ).upper()
                        }
                        if handler == "capture_incidents_operations"
                        and isinstance(
                            row.get("capture_run_input_checkpoint"), Mapping
                        )
                        and isinstance(
                            row["capture_run_input_checkpoint"].get("sha256"),
                            str,
                        )
                        else {}
                    ),
                }
            )
    if not bindings:
        _fail("source_capture_lineage_set_empty")
    payload = json.dumps(
        bindings,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")
    return "zg361-phase2-lineage-set-" + hashlib.sha256(payload).hexdigest()


def _validate_product_only_entry_lineage(
    value: object, *, seed_lineage_id: str, label: str
) -> dict[str, object]:
    lineage = deepcopy(dict(value)) if isinstance(value, Mapping) else {}
    mod_mount = lineage.get("mod_mount")
    legacy_product_only = lineage.get("product_only_runtime") is True
    projects_product_only = (
        lineage.get("product_only_mount") is True
        and isinstance(lineage.get("product_tree_sha256"), str)
        and _SHA256.fullmatch(
            str(lineage.get("product_tree_sha256", "")).upper()
        )
        is not None
        and str(lineage.get("runtime_product_tree_sha256", "")).upper()
        == str(lineage.get("product_tree_sha256", "")).upper()
    )
    canonical_product_only = (
        isinstance(mod_mount, Mapping)
        and mod_mount.get("kind") == "product-only"
        and isinstance(mod_mount.get("tree_sha256"), str)
        and _SHA256.fullmatch(str(mod_mount.get("tree_sha256", "")).upper())
        is not None
    )
    valid = (
        lineage.get("seed_lineage_id") == seed_lineage_id
        and lineage.get("evidence_class") == "real_ck3"
        and lineage.get("fixture_used") is False
        and lineage.get("console_used") is False
        and (
            legacy_product_only
            or projects_product_only
            or canonical_product_only
        )
    )
    if not valid:
        _fail(
            "source_capture_lineage_invalid",
            label=label,
            seed_lineage_id=seed_lineage_id,
            capture_lineage=lineage,
        )
    return lineage


def _validate_capture_lineage(
    value: object,
    *,
    manifest_schema_version: int,
    seed_lineage_id: str | None,
    lineage_set_id: str | None,
    label: str,
) -> dict[str, object]:
    lineage = deepcopy(dict(value)) if isinstance(value, Mapping) else {}
    if manifest_schema_version == MULTI_BRANCH_CAPTURE_SCHEMA_VERSION:
        entry_lineages = lineage.get("entry_capture_lineages")
        observed_handlers = (
            tuple(
                row.get("handler") if isinstance(row, Mapping) else None
                for row in entry_lineages
            )
            if isinstance(entry_lineages, list)
            else ()
        )
        common_valid = (
            lineage.get("schema_version") == 2
            and lineage.get("kind")
            == PRODUCT_ONLY_MULTI_BRANCH_LINEAGE_KIND
            and lineage.get("capture_lineage_mode")
            == MULTI_BRANCH_CAPTURE_LINEAGE_MODE
            and isinstance(lineage_set_id, str)
            and bool(lineage_set_id)
            and lineage.get("lineage_set_id") == lineage_set_id
            and "seed_lineage_id" not in lineage
            and lineage.get("evidence_class") == "real_ck3"
            and lineage.get("fixture_used") is False
            and lineage.get("console_used") is False
            and observed_handlers == _PREFIX_HANDLERS
        )
        for row in entry_lineages if isinstance(entry_lineages, list) else []:
            entry_seed = (
                row.get("seed_lineage_id")
                if isinstance(row, Mapping)
                else None
            )
            captured = row.get("capture_lineage") if isinstance(row, Mapping) else None
            if not (isinstance(entry_seed, str) and bool(entry_seed)):
                common_valid = False
                continue
            if row.get("handler") == "capture_incidents_operations":
                input_checkpoint = row.get("capture_run_input_checkpoint")
                input_checkpoint = (
                    dict(input_checkpoint)
                    if isinstance(input_checkpoint, Mapping)
                    else {}
                )
                raw_input_path = input_checkpoint.get("path")
                input_path = (
                    Path(raw_input_path).expanduser().resolve()
                    if isinstance(raw_input_path, str)
                    and Path(raw_input_path).is_absolute()
                    else Path()
                )
                source_input_sha256 = str(
                    input_checkpoint.get("sha256", "")
                ).upper()
                common_valid = common_valid and (
                    _SHA256.fullmatch(source_input_sha256) is not None
                    and input_path.is_absolute()
                    and input_path.is_file()
                    and _positive_int(input_checkpoint.get("bytes"))
                    and input_path.stat().st_size
                    == input_checkpoint.get("bytes")
                    and _sha256_file(input_path) == source_input_sha256
                )
            try:
                _validate_product_only_entry_lineage(
                    captured,
                    seed_lineage_id=entry_seed,
                    label=f"{label}:{row.get('handler')}",
                )
            except EndgameSourceCaptureError:
                common_valid = False
        if isinstance(entry_lineages, list):
            try:
                common_valid = common_valid and (
                    phase2_source_lineage_set_id(entry_lineages)
                    == lineage_set_id
                )
            except EndgameSourceCaptureError:
                common_valid = False
        if not common_valid:
            _fail(
                "source_capture_lineage_invalid",
                label=label,
                lineage_set_id=lineage_set_id,
                capture_lineage=lineage,
            )
        return lineage
    if not isinstance(seed_lineage_id, str):
        _fail(
            "source_capture_lineage_invalid",
            label=label,
            seed_lineage_id=seed_lineage_id,
            capture_lineage=lineage,
        )
    if lineage.get("kind") == PRODUCT_ONLY_MULTI_SESSION_LINEAGE_KIND:
        entry_lineages = lineage.get("entry_capture_lineages")
        observed_handlers = (
            tuple(
                row.get("handler") if isinstance(row, Mapping) else None
                for row in entry_lineages
            )
            if isinstance(entry_lineages, list)
            else ()
        )
        common_valid = (
            lineage.get("schema_version") == 1
            and lineage.get("capture_lineage_mode")
            == "same-seed-product-only-multi-session"
            and lineage.get("seed_lineage_id") == seed_lineage_id
            and lineage.get("evidence_class") == "real_ck3"
            and lineage.get("fixture_used") is False
            and lineage.get("console_used") is False
            and observed_handlers == _PREFIX_HANDLERS
        )
        for row in entry_lineages if isinstance(entry_lineages, list) else []:
            entry = row.get("capture_lineage") if isinstance(row, Mapping) else None
            entry = dict(entry) if isinstance(entry, Mapping) else {}
            mod_mount = entry.get("mod_mount")
            legacy_product_only = entry.get("product_only_runtime") is True
            projects_product_only = (
                entry.get("product_only_mount") is True
                and isinstance(entry.get("product_tree_sha256"), str)
                and _SHA256.fullmatch(
                    str(entry.get("product_tree_sha256", "")).upper()
                )
                is not None
                and str(entry.get("runtime_product_tree_sha256", "")).upper()
                == str(entry.get("product_tree_sha256", "")).upper()
            )
            canonical_product_only = (
                isinstance(mod_mount, Mapping)
                and mod_mount.get("kind") == "product-only"
                and isinstance(mod_mount.get("tree_sha256"), str)
                and _SHA256.fullmatch(
                    str(mod_mount.get("tree_sha256", "")).upper()
                )
                is not None
            )
            common_valid = common_valid and (
                entry.get("seed_lineage_id") == seed_lineage_id
                and entry.get("evidence_class") == "real_ck3"
                and entry.get("fixture_used") is False
                and entry.get("console_used") is False
                and (
                    legacy_product_only
                    or projects_product_only
                    or canonical_product_only
                )
            )
        if not common_valid:
            _fail(
                "source_capture_lineage_invalid",
                label=label,
                seed_lineage_id=seed_lineage_id,
                capture_lineage=lineage,
            )
        return lineage
    return _validate_product_only_entry_lineage(
        lineage,
        seed_lineage_id=seed_lineage_id,
        label=label,
    )


def _validate_multi_session_lineage_bindings(
    lineage: Mapping[str, object], entries: list[dict[str, object]]
) -> None:
    """Bind every aggregate lineage to the unchanged row that produced it."""

    if lineage.get("kind") not in (
        PRODUCT_ONLY_MULTI_SESSION_LINEAGE_KIND,
        PRODUCT_ONLY_MULTI_BRANCH_LINEAGE_KIND,
    ):
        return
    raw_lineages = lineage.get("entry_capture_lineages")
    assert isinstance(raw_lineages, list)
    for index, (raw_lineage, entry) in enumerate(
        zip(raw_lineages, entries, strict=True)
    ):
        assert isinstance(raw_lineage, Mapping)
        handler = str(entry["handler"])
        captured = raw_lineage.get("capture_lineage")
        captured = dict(captured) if isinstance(captured, Mapping) else {}
        entry_seed = raw_lineage.get("seed_lineage_id")
        if lineage.get("kind") == PRODUCT_ONLY_MULTI_SESSION_LINEAGE_KIND:
            entry_seed = lineage.get("seed_lineage_id")
        source_kind = raw_lineage.get("provenance_source")
        valid = (
            raw_lineage.get("handler") == handler
            and isinstance(entry_seed, str)
            and bool(entry_seed)
            and captured.get("seed_lineage_id") == entry_seed
        )
        if index < 2:
            record = raw_lineage.get("source_artifact")
            record = dict(record) if isinstance(record, Mapping) else {}
            raw_path = record.get("path")
            path = (
                Path(raw_path).expanduser().resolve()
                if isinstance(raw_path, str) and Path(raw_path).is_absolute()
                else Path()
            )
            sha256 = str(record.get("sha256", "")).upper()
            artifact = {}
            if (
                path.is_absolute()
                and path.is_file()
                and _positive_int(record.get("bytes"))
                and path.stat().st_size == record.get("bytes")
                and _SHA256.fullmatch(sha256) is not None
                and _sha256_file(path) == sha256
            ):
                artifact = _read_json_object(
                    path, reason_code="source_capture_lineage_artifact_unreadable"
                )
            valid = valid and (
                source_kind == "source_artifact.capture_lineage"
                and artifact.get("seed_lineage_id") == entry_seed
                and artifact.get("capture_lineage") == captured
                and artifact.get("entries") == [entry]
            )
        else:
            valid = valid and (
                source_kind == "registry_entry.capture_lineage"
                and entry.get("seed_lineage_id") == entry_seed
                and entry.get("capture_lineage") == captured
            )
        if not valid:
            _fail(
                "source_capture_lineage_entry_binding_invalid",
                handler=handler,
                entry_index=index,
                entry_capture_lineage=raw_lineage,
            )


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
    expected_lineage_set_id: str | None = None,
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
    manifest_schema_version = manifest.get("schema_version")
    seed_lineage_id = manifest.get("seed_lineage_id")
    lineage_set_id = manifest.get("lineage_set_id")
    entries = manifest.get("entries")
    common_header_valid = (
        manifest.get("kind") == CAPTURE_PREFIX_KIND
        and manifest.get("result") == "LIVE_PENDING"
        and manifest.get("readiness") == "live-pending-endgame-source"
        and manifest.get("evidence_class") == "real_ck3"
        and manifest.get("fixture_used") is False
        and manifest.get("console_used") is False
        and isinstance(entries, list)
    )
    if (
        manifest_schema_version
        == LEGACY_SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION
    ):
        identity_valid = (
            isinstance(seed_lineage_id, str)
            and bool(seed_lineage_id)
            and (
                expected_seed_lineage_id is None
                or seed_lineage_id == expected_seed_lineage_id
            )
            and expected_lineage_set_id is None
        )
    elif manifest_schema_version == MULTI_BRANCH_CAPTURE_SCHEMA_VERSION:
        identity_valid = (
            "seed_lineage_id" not in manifest
            and expected_seed_lineage_id is None
            and isinstance(lineage_set_id, str)
            and bool(lineage_set_id)
            and (
                expected_lineage_set_id is None
                or lineage_set_id == expected_lineage_set_id
            )
        )
    else:
        identity_valid = False
    header_valid = common_header_valid and identity_valid
    if not header_valid:
        _fail(
            "source_capture_prefix_header_invalid",
            expected_seed_lineage_id=expected_seed_lineage_id,
            expected_lineage_set_id=expected_lineage_set_id,
            manifest=manifest,
        )
    assert isinstance(manifest_schema_version, int)
    assert isinstance(entries, list)
    lineage = _validate_capture_lineage(
        manifest.get("capture_lineage"),
        manifest_schema_version=manifest_schema_version,
        seed_lineage_id=(
            seed_lineage_id if isinstance(seed_lineage_id, str) else None
        ),
        lineage_set_id=(
            lineage_set_id if isinstance(lineage_set_id, str) else None
        ),
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
    if manifest_schema_version == MULTI_BRANCH_CAPTURE_SCHEMA_VERSION:
        raw_entry_lineages = lineage["entry_capture_lineages"]
        assert isinstance(raw_entry_lineages, list)
        entry_seeds = {
            str(row["handler"]): str(row["seed_lineage_id"])
            for row in raw_entry_lineages
            if isinstance(row, Mapping)
        }
    else:
        assert isinstance(seed_lineage_id, str)
        entry_seeds = {handler: seed_lineage_id for handler in _PREFIX_HANDLERS}
    validated_entries = [
        _validate_prefix_entry(
            row,
            handler=handler,
            seed_lineage_id=entry_seeds[handler],
        )
        for row, handler in zip(entries, _PREFIX_HANDLERS, strict=True)
    ]
    _validate_multi_session_lineage_bindings(lineage, validated_entries)
    runtime_lineage = None
    runtime_seed_lineage_id = None
    if runtime_capture_lineage is not None:
        runtime_seed_lineage_id = runtime_capture_lineage.get(
            "seed_lineage_id"
        )
        if (
            manifest_schema_version
            == LEGACY_SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION
        ):
            runtime_seed_lineage_id = seed_lineage_id
        if not (
            isinstance(runtime_seed_lineage_id, str)
            and bool(runtime_seed_lineage_id)
        ):
            _fail(
                "source_capture_runtime_lineage_invalid",
                runtime_capture_lineage=runtime_capture_lineage,
            )
        runtime_lineage = _validate_product_only_entry_lineage(
            runtime_capture_lineage,
            seed_lineage_id=runtime_seed_lineage_id,
            label="runtime",
        )
        prefix_mount = lineage.get("mod_mount")
        runtime_mount = runtime_lineage.get("mod_mount")
        prefix_game = lineage.get("game")
        runtime_game = runtime_lineage.get("game")
        if lineage.get("kind") in (
            PRODUCT_ONLY_MULTI_SESSION_LINEAGE_KIND,
            PRODUCT_ONLY_MULTI_BRANCH_LINEAGE_KIND,
        ):
            exact_builds = []
            for row in lineage["entry_capture_lineages"]:
                entry = row["capture_lineage"]
                version = entry.get("game_version")
                executable = entry.get("executable_sha256")
                game = entry.get("game")
                if isinstance(game, Mapping):
                    version = game.get("version")
                    executable = game.get("exe_sha256")
                if version is not None or executable is not None:
                    exact_builds.append((version, str(executable).upper()))
            same_exact_product = (
                isinstance(runtime_game, Mapping)
                and bool(exact_builds)
                and all(
                    version == runtime_game.get("version")
                    and executable
                    == str(runtime_game.get("exe_sha256", "")).upper()
                    for version, executable in exact_builds
                )
            )
        else:
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
    result = {
        "schema_version": manifest_schema_version,
        "result": "GREEN",
        "readiness": "live-pending-endgame-source",
        "capture_lineage": lineage,
        "runtime_capture_lineage": runtime_lineage,
        "runtime_seed_lineage_id": runtime_seed_lineage_id,
        "entry_seed_lineage_ids": entry_seeds,
        "entry_count": len(validated_entries),
        "handlers": list(observed_handlers),
        "entries": validated_entries,
        "fixture_used": False,
        "console_used": False,
    }
    if manifest_schema_version == MULTI_BRANCH_CAPTURE_SCHEMA_VERSION:
        result["lineage_set_id"] = lineage_set_id
    else:
        result["seed_lineage_id"] = seed_lineage_id
    return result


def preflight_endgame_source_capture_service(
    service: object,
) -> dict[str, object]:
    """Check the two interfaces needed to prove third-cycle maturity."""

    required_methods = (
        "capabilities",
        "set_player_character_v1",
        "query_zhongguo_workforce_collective_snapshot_v1",
    )
    missing = [
        method_name
        for method_name in required_methods
        if not callable(getattr(service, method_name, None))
    ]
    if missing:
        _fail(
            "endgame_maturity_provider_missing",
            required_methods=list(required_methods),
            missing_methods=missing,
        )
    capabilities = service.capabilities()
    advertised = (
        capabilities.get("bridge_capabilities")
        if isinstance(capabilities, Mapping)
        else None
    )
    missing_capabilities = [
        capability
        for capability in MATURITY_REQUIRED_BRIDGE_CAPABILITIES
        if not isinstance(advertised, list) or capability not in advertised
    ]
    if missing_capabilities:
        _fail(
            "endgame_maturity_capability_not_advertised",
            required_capabilities=list(MATURITY_REQUIRED_BRIDGE_CAPABILITIES),
            missing_capabilities=missing_capabilities,
            capabilities=capabilities,
        )
    return {
        "schema_version": 1,
        "result": "GREEN",
        "readiness": "interfaces-ready-live-state-unproven",
        "required_methods": list(required_methods),
        "required_bridge_capabilities": list(
            MATURITY_REQUIRED_BRIDGE_CAPABILITIES
        ),
        "generic_character_rebind_required": True,
        "provider_observed_business_state": False,
        "ck3_launched": False,
    }


def _wait_for_source_surface(
    service: EndgameSourceCaptureService,
    *,
    expected_owner_character_id: int,
    expected_date_raw: int,
    timeout_seconds: float,
    poll_interval_seconds: float,
) -> tuple[
    dict[str, object],
    dict[str, object],
    dict[str, object],
    dict[str, object],
    int,
]:
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
                require_transport_binding=True,
            )
            context, owner, subject = _event_surface(
                service,
                binding,
                expected_event=SOURCE_EVENT,
                expected_owner=expected_owner_character_id,
                expected_subject=None,
            )
            scalar_scopes = _event_scalar_scope_binding(context)
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
        return dict(snapshot), dict(binding), context, scalar_scopes, subject
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


def _native_subject_switch_contract(
    value: object,
    *,
    before: Mapping[str, object],
    after: Mapping[str, object],
    owner_character_id: int,
    subject_character_id: int,
) -> dict[str, object]:
    receipt = deepcopy(dict(value)) if isinstance(value, Mapping) else {}
    valid = (
        receipt.get("schema_version") == 1
        and receipt.get("accepted") is True
        and receipt.get("status") == "switched"
        and receipt.get("backend_id") == "native-headless"
        and receipt.get("step")
        == f"set-played-character-v1-{subject_character_id}"
        and receipt.get("from_character_id") == owner_character_id
        and receipt.get("to_character_id") == subject_character_id
        and receipt.get("prior_episode_character_id") == owner_character_id
        and receipt.get("episode_character_id") == subject_character_id
        and receipt.get("before_revision") == before.get("revision")
        and receipt.get("after_revision") == after.get("revision")
        and receipt.get("native_revision") == after.get("native_revision")
        and receipt.get("date_raw") == before.get("date_raw")
        and receipt.get("paused") is True
        and receipt.get("map_ready") is True
        and receipt.get("postcondition_verified") is True
        and receipt.get("episode_rebind_performed") is True
        and receipt.get("one_life_terminal_cleared") is True
        and before.get("player_character_id") == owner_character_id
        and after.get("player_character_id") == subject_character_id
        and before.get("date_raw") == after.get("date_raw")
        and before.get("bridge_pid") == after.get("bridge_pid")
        and before.get("connection_generation")
        == after.get("connection_generation")
        and isinstance(before.get("revision"), int)
        and isinstance(after.get("revision"), int)
        and not isinstance(before.get("revision"), bool)
        and not isinstance(after.get("revision"), bool)
        and int(before["revision"]) < int(after["revision"])
    )
    if not valid:
        _fail(
            "endgame_maturity_player_switch_invalid",
            owner_character_id=owner_character_id,
            subject_character_id=subject_character_id,
            before=dict(before),
            after=dict(after),
            native_receipt=receipt,
        )
    return receipt


_HISTORY_SLOT_FIELDS: Final = (
    "owner_character_id",
    "subject_character_id",
    "cycle_serial",
    "case_serial",
    "m357_receipt_id",
    "m357_receipt_hash",
    "m358_receipt_id",
    "m358_receipt_hash",
    "m359_receipt_id",
    "m359_receipt_hash",
)


def _endgame_maturity_contract(
    value: object,
    *,
    binding: Mapping[str, object],
    owner_character_id: int,
    subject_character_id: int,
) -> dict[str, object]:
    response = deepcopy(dict(value)) if isinstance(value, Mapping) else {}
    provider_binding = response.get("binding")
    provider_binding = (
        dict(provider_binding) if isinstance(provider_binding, Mapping) else {}
    )
    history = response.get("history")
    history = dict(history) if isinstance(history, Mapping) else {}
    readiness = response.get("readiness")
    readiness = dict(readiness) if isinstance(readiness, Mapping) else {}
    al_case = response.get("al_case")
    al_case = dict(al_case) if isinstance(al_case, Mapping) else {}
    header_valid = (
        response.get("schema_version") == 1
        and response.get("status") == "available"
        and response.get("case_kind") == "zhongguo.workforce-collective"
        and response.get("request_nonce") == MATURITY_QUERY_NONCE
        and response.get("snapshot_revision") == binding.get("native_revision")
        and response.get("date_raw") == binding.get("date_raw")
        and response.get("paused") is True
        and response.get("player_character_id") == subject_character_id
        and response.get("subject_character_id") == subject_character_id
        and response.get("requested_owner_character_id") == owner_character_id
        and response.get("unavailable_reason") is None
        and provider_binding.get("request_nonce") == MATURITY_QUERY_NONCE
        and provider_binding.get("snapshot_id") == binding.get("snapshot_id")
        and provider_binding.get("revision") == binding.get("revision")
        and provider_binding.get("native_revision") == binding.get("native_revision")
        and provider_binding.get("date_raw") == binding.get("date_raw")
        and provider_binding.get("paused") is True
        and provider_binding.get("player_character_id") == subject_character_id
        and provider_binding.get("subject_character_id") == subject_character_id
        and provider_binding.get("owner_character_id") == owner_character_id
        and provider_binding.get("expected_revision") == binding.get("revision")
        and readiness.get("player_subject_binding_ready") is True
        and readiness.get("owner_binding_ready") is True
        and readiness.get("case_identity_ready") is True
        and readiness.get("history_ledger_ready") is True
        and readiness.get("history_order_ready") is True
        and readiness.get("three_cycle_ready") is False
        and readiness.get("same_frame_ready") is True
        and readiness.get("ready") is True
    )
    if not header_valid:
        _fail(
            "endgame_maturity_provider_binding_invalid",
            owner_character_id=owner_character_id,
            subject_character_id=subject_character_id,
            subject_binding=dict(binding),
            provider_response=response,
        )

    current_owner = _typed_available(al_case, "owner_character_id")
    current_subject = _typed_available(al_case, "subject_character_id")
    current_cycle = _typed_available(al_case, "cycle_serial")
    current_case = _typed_available(al_case, "case_serial")
    current_state = _typed_available(al_case, "state")
    current_active = _typed_available(al_case, "active")
    current_revision = _typed_available(al_case, "revision")
    current_valid = (
        current_owner == owner_character_id
        and current_subject == subject_character_id
        and _positive_int(current_cycle)
        and _positive_int(current_case)
        and current_state == 1
        and current_active is True
        and _positive_int(current_revision)
    )
    if not current_valid:
        _fail(
            "endgame_maturity_current_case_invalid",
            expected_owner_character_id=owner_character_id,
            expected_subject_character_id=subject_character_id,
            al_case=al_case,
        )

    history_count = _typed_available(history, "count")
    slots = history.get("slots")
    if not (
        history.get("status") == "partial"
        and history_count == MATURE_ENDGAME_HISTORY_COUNT
        and history.get("effective_count") == MATURE_ENDGAME_HISTORY_COUNT
        and isinstance(slots, list)
        and len(slots) == 3
    ):
        _fail(
            "endgame_maturity_history_count_invalid",
            required_status="partial",
            required_count=MATURE_ENDGAME_HISTORY_COUNT,
            history=history,
        )
    assert isinstance(slots, list)
    normalized_slots: list[dict[str, int]] = []
    receipt_ids: list[int] = []
    receipt_hashes: list[int] = []
    for index in range(MATURE_ENDGAME_HISTORY_COUNT):
        raw_slot = slots[index]
        normalized: dict[str, int] = {}
        for key in _HISTORY_SLOT_FIELDS:
            observed = _typed_available(raw_slot, key)
            if not _positive_int(observed):
                _fail(
                    "endgame_maturity_history_slot_invalid",
                    slot_index=index,
                    field=key,
                    observed=observed,
                )
            normalized[key] = int(observed)
        if normalized["owner_character_id"] != owner_character_id:
            _fail(
                "endgame_maturity_history_owner_drifted",
                slot_index=index,
                expected_owner_character_id=owner_character_id,
                observed_owner_character_id=normalized["owner_character_id"],
            )
        receipt_ids.extend(
            normalized[f"m{milestone}_receipt_id"]
            for milestone in (357, 358, 359)
        )
        receipt_hashes.extend(
            normalized[f"m{milestone}_receipt_hash"]
            for milestone in (357, 358, 359)
        )
        normalized_slots.append(normalized)
    if not all(
        _typed_unavailable(slots[2], key, "lifecycle_not_reached")
        for key in _HISTORY_SLOT_FIELDS
    ):
        _fail(
            "endgame_maturity_future_history_slot_materialized",
            slot=slots[2],
        )
    prior_cycles = [slot["cycle_serial"] for slot in normalized_slots]
    if not prior_cycles[0] < prior_cycles[1] < int(current_cycle):
        _fail(
            "endgame_maturity_cycles_not_strictly_increasing",
            prior_cycles=prior_cycles,
            current_cycle_serial=current_cycle,
        )
    if len(set(receipt_ids)) != len(receipt_ids) or len(
        set(receipt_hashes)
    ) != len(receipt_hashes):
        _fail(
            "endgame_maturity_receipt_identity_collision",
            receipt_ids=receipt_ids,
            receipt_hashes=receipt_hashes,
        )
    return {
        "schema_version": 1,
        "result": "GREEN",
        "evidence_class": "real_ck3",
        "provider_observed": True,
        "history_status": "partial",
        "history_count": MATURE_ENDGAME_HISTORY_COUNT,
        "history_effective_count": MATURE_ENDGAME_HISTORY_COUNT,
        "owner_character_id": owner_character_id,
        "subject_character_id": subject_character_id,
        "cycle_serial": int(current_cycle),
        "case_serial": int(current_case),
        "prior_cycle_serials": prior_cycles,
        "prior_slots": normalized_slots,
        "receipt_ids": receipt_ids,
        "receipt_hashes": receipt_hashes,
        "third_cycle_source_ready": True,
        "provider_response": response,
    }


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

    if expected_owner_character_id != MATURE_ENDGAME_OWNER_CHARACTER_ID:
        _fail(
            "endgame_maturity_owner_invalid",
            required_owner_character_id=MATURE_ENDGAME_OWNER_CHARACTER_ID,
            observed_owner_character_id=expected_owner_character_id,
        )
    preflight_endgame_source_capture_service(service)
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
    prefix_schema_version = int(prefix["schema_version"])
    if prefix_schema_version == MULTI_BRANCH_CAPTURE_SCHEMA_VERSION:
        seed_lineage_id = str(prefix["runtime_seed_lineage_id"])
    else:
        seed_lineage_id = str(prefix["seed_lineage_id"])
    (
        source_snapshot,
        before,
        event_context,
        event_scalar_scopes,
        subject,
    ) = _wait_for_source_surface(
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
            require_transport_binding=True,
        )
        after_context, after_owner, after_subject = _event_surface(
            service,
            after,
            expected_event=SOURCE_EVENT,
            expected_owner=expected_owner_character_id,
            expected_subject=subject,
        )
        after_event_scalar_scopes = _event_scalar_scope_binding(after_context)
    except CrossCycleEndgameCellError as error:
        _fail(
            "source_post_save_surface_invalid",
            upstream_reason_code=error.reason_code,
            upstream_evidence=error.evidence,
        )
    stable_keys = (
        "date_raw",
        "player_character_id",
        "event_instance_id",
        "bridge_pid",
        "connection_generation",
    )
    save_advanced_exactly_once = bool(
        _positive_int(before.get("revision"))
        and after.get("revision") == int(before["revision"]) + 1
        and _positive_int(before.get("native_revision"))
        and after.get("native_revision")
        == int(before["native_revision"]) + 1
        and isinstance(before.get("snapshot_id"), str)
        and isinstance(after.get("snapshot_id"), str)
        and after.get("snapshot_id") != before.get("snapshot_id")
    )
    if (
        any(before.get(key) != after.get(key) for key in stable_keys)
        or not save_advanced_exactly_once
    ):
        _fail("source_save_crossed_binding", before=before, after=after)
    if after_owner != expected_owner_character_id or after_subject != subject:
        _fail(
            "source_save_owner_subject_drifted",
            before_owner=expected_owner_character_id,
            before_subject=subject,
            after_owner=after_owner,
            after_subject=after_subject,
        )
    if after_event_scalar_scopes != event_scalar_scopes:
        _fail(
            "source_save_scalar_scopes_drifted",
            before=event_scalar_scopes,
            after=after_event_scalar_scopes,
        )

    switch_result = service.set_player_character_v1(
        subject,
        expected_revision=int(after["revision"]),
    )
    subject_snapshot = service.snapshot()
    try:
        subject_binding = _paused_binding(
            subject_snapshot,
            expected_player=subject,
            require_event=False,
            require_transport_binding=True,
        )
    except CrossCycleEndgameCellError as error:
        _fail(
            "endgame_maturity_subject_binding_invalid",
            upstream_reason_code=error.reason_code,
            upstream_evidence=error.evidence,
        )
    if subject_binding["date_raw"] != expected_date_raw:
        _fail(
            "endgame_maturity_subject_date_drifted",
            expected_date_raw=expected_date_raw,
            observed_date_raw=subject_binding["date_raw"],
        )
    native_switch = _native_subject_switch_contract(
        switch_result,
        before=after,
        after=subject_binding,
        owner_character_id=expected_owner_character_id,
        subject_character_id=subject,
    )
    workforce_response = (
        service.query_zhongguo_workforce_collective_snapshot_v1(
            MATURITY_QUERY_NONCE,
            expected_revision=int(subject_binding["revision"]),
            owner_character_id=expected_owner_character_id,
        )
    )
    maturity = _endgame_maturity_contract(
        workforce_response,
        binding=subject_binding,
        owner_character_id=expected_owner_character_id,
        subject_character_id=subject,
    )
    maturity_after_snapshot = service.snapshot()
    try:
        maturity_after = _paused_binding(
            maturity_after_snapshot,
            expected_player=subject,
            require_event=False,
            require_transport_binding=True,
        )
    except CrossCycleEndgameCellError as error:
        _fail(
            "endgame_maturity_post_query_binding_invalid",
            upstream_reason_code=error.reason_code,
            upstream_evidence=error.evidence,
        )
    if any(
        maturity_after.get(key) != subject_binding.get(key)
        for key in (
            "snapshot_id",
            "revision",
            "native_revision",
            "date_raw",
            "player_character_id",
            "bridge_pid",
            "connection_generation",
        )
    ):
        _fail(
            "endgame_maturity_provider_crossed_frame",
            before=subject_binding,
            after=maturity_after,
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
    if prefix_schema_version == MULTI_BRANCH_CAPTURE_SCHEMA_VERSION:
        entry_capture_lineages = prefix_lineage.get(
            "entry_capture_lineages"
        )
        assert isinstance(entry_capture_lineages, list)
        entry_capture_lineages.append(
            {
                "handler": HANDLER,
                "seed_lineage_id": seed_lineage_id,
                "provenance_source": "runtime_capture_lineage",
                "capture_lineage": deepcopy(dict(runtime_capture_lineage)),
            }
        )
        completed_lineage_set_id = phase2_source_lineage_set_id(
            entry_capture_lineages
        )
        prefix_lineage["lineage_set_id"] = completed_lineage_set_id
        prefix_lineage["capture_lineage_mode"] = (
            MULTI_BRANCH_CAPTURE_LINEAGE_MODE
        )
    else:
        completed_lineage_set_id = None
        prefix_lineage["capture_lineage_mode"] = (
            "same-seed-product-only-multi-session"
            if prefix_lineage.get("kind")
            == PRODUCT_ONLY_MULTI_SESSION_LINEAGE_KIND
            else "same-seed-exact-product-multi-session"
        )
    prefix_lineage["generic_character_rebind_used"] = True
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
        "generic_character_rebind_used": True,
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
        "maturity_player_switch_receipt": native_switch,
        "maturity_subject_snapshot_binding": subject_binding,
        "maturity_post_query_snapshot_binding": maturity_after,
        "maturity_provider_proof": maturity,
        "source_event_case_binding": {
            "event_definition_key": SOURCE_EVENT,
            "owner_character_id": expected_owner_character_id,
            "subject_character_id": subject,
            "cycle_serial": maturity["cycle_serial"],
            "case_serial": maturity["case_serial"],
            "event_owner_subject_scopes_observed": True,
            "received_self_current_case_provider_observed": True,
            "numeric_binding_authority": (
                EVENT_SCALAR_CASE_BINDING_AUTHORITY
            ),
            "event_scalar_saved_scopes": {
                "zg361_we_al_cycle": {
                    **deepcopy(
                        event_scalar_scopes["zg361_we_al_cycle"]
                    ),
                    "provider_field": "cycle_serial",
                    "provider_value": maturity["cycle_serial"],
                },
                "zg361_we_al_case": {
                    **deepcopy(event_scalar_scopes["zg361_we_al_case"]),
                    "provider_field": "case_serial",
                    "provider_value": maturity["case_serial"],
                },
            },
        },
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
            "owner_history_partial_two_cycles": True,
            "two_prior_history_slots_complete": True,
            "history_cycles_strictly_increasing_into_current_case": True,
            "history_receipt_ids_and_hashes_positive_and_distinct": True,
            "current_event_owner_subject_cycle_case_tuple_bound": True,
            "event_scalar_saved_scopes_typed_and_guard_bound": True,
            "subject_switch_same_pid_and_connection_generation": True,
            "generic_character_rebind_used": True,
            "action_ack_used_as_state_evidence": False,
        },
    }
    validate_endgame_maturity_source_receipt(
        receipt,
        owner_character_id=expected_owner_character_id,
        player_character_id=expected_owner_character_id,
        date_raw=expected_date_raw,
    )
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
        "schema_version": prefix_schema_version,
        "kind": SOURCE_CHECKPOINT_CAPTURE_MANIFEST_KIND,
        "result": "GREEN",
        "readiness": "captured-all-source-checkpoints",
        "evidence_class": "real_ck3",
        "fixture_used": False,
        "console_used": False,
        "capture_lineage": prefix_lineage,
        "entries": entries,
    }
    if prefix_schema_version == MULTI_BRANCH_CAPTURE_SCHEMA_VERSION:
        completed_manifest["lineage_set_id"] = completed_lineage_set_id
    else:
        completed_manifest["seed_lineage_id"] = seed_lineage_id
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
    result = {
        "schema_version": 1,
        "kind": CAPTURE_RECEIPT_KIND,
        "result": "GREEN",
        "readiness": "live-pending",
        "source_checkpoint_captured": True,
        "phase2_complete": False,
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
        "generic_character_rebind_used": True,
        "action_ack_only": False,
    }
    if prefix_schema_version == MULTI_BRANCH_CAPTURE_SCHEMA_VERSION:
        result["lineage_set_id"] = completed_lineage_set_id
        result["runtime_seed_lineage_id"] = seed_lineage_id
    else:
        result["seed_lineage_id"] = seed_lineage_id
    return result


__all__ = [
    "CAPTURE_PREFIX_KIND",
    "CAPTURE_RECEIPT_KIND",
    "MULTI_BRANCH_CAPTURE_LINEAGE_MODE",
    "MULTI_BRANCH_CAPTURE_SCHEMA_VERSION",
    "PRODUCT_ONLY_MULTI_BRANCH_LINEAGE_KIND",
    "PRODUCT_ONLY_MULTI_SESSION_LINEAGE_KIND",
    "DEFAULT_WAIT_TIMEOUT_SECONDS",
    "DEFAULT_POLL_INTERVAL_SECONDS",
    "MATURE_ENDGAME_OWNER_CHARACTER_ID",
    "EndgameSourceCaptureError",
    "capture_cross_cycle_endgame_source_checkpoint_v1",
    "phase2_source_lineage_set_id",
    "preflight_endgame_source_capture_prefix",
    "preflight_endgame_source_capture_service",
]
