#!/usr/bin/env python3
"""Capture the real CP26 source state needed by projects/metrics live work.

The module has no launcher and no state preparer.  Its two explicit live
operations attach to a caller-owned managed session: first observe/select route
A or B on the real ``zg361cp.26`` surface, then (after the caller has reached a
played-subject, event-free product state in the same lineage) query the native
provider and save that state.  The selection acknowledgement is retained as UI
transport evidence only; the source contribution provider is the business
state proof.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
from typing import Final, Mapping, Protocol


ROOT = Path(__file__).resolve().parents[1]
AUTOPLAYER_SRC = ROOT / "ck3_autonomous_player" / "src"
if str(AUTOPLAYER_SRC) not in sys.path:
    sys.path.insert(0, str(AUTOPLAYER_SRC))

from xar_autoplayer.bridge.service import GameplayBridgeService  # noqa: E402
from xar_autoplayer.bridge.native_driver import (  # noqa: E402
    NativeHeadlessGameplayDriver,
)
from zg361_phase2_projects_metrics_action_cell import (  # noqa: E402
    preflight_projects_metrics_gameplay_action_cell,
)


SPAN_ID: Final = "phase2_projects_metrics"
HANDLER: Final = "capture_projects_metrics"
SOURCE_EVENT: Final = "zg361cp.26"
REGISTRY_KIND: Final = "zg361_projects_metrics_source_checkpoint_registry"
REGISTRY_SCHEMA_VERSION: Final = 2
UI_RECEIPT_KIND: Final = "zg361_projects_metrics_cp26_ui_receipt"
READINESS: Final = "static-ready-live-pending"
LIVE_MODE: Final = "managed-real-ck3"
_SHA256 = re.compile(r"[0-9A-Fa-f]{64}\Z")
_GIT_SHA = re.compile(r"[0-9A-Fa-f]{40}\Z")


class ProjectsMetricsCheckpointService(Protocol):
    def capabilities(self) -> dict[str, object]: ...

    def snapshot(self) -> dict[str, object]: ...

    def query_zhongguo_projects_metrics_postcondition_v1(
        self,
        request_nonce: str,
        *,
        expected_revision: int,
        owner_character_id: int,
    ) -> dict[str, object]: ...

    def save_checkpoint(
        self, *, expected_revision: int | None = None
    ) -> dict[str, object]: ...


class ProjectsMetricsUiService(Protocol):
    def snapshot(self) -> dict[str, object]: ...

    def query_current_event_window_context_v1(
        self, event_instance_id: int, *, expected_revision: int
    ) -> dict[str, object]: ...

    def select_event_option(
        self,
        option_number: int,
        *,
        event_instance_id: int,
        expected_revision: int,
    ) -> dict[str, object]: ...


class ProjectsMetricsSourceCheckpointError(RuntimeError):
    """Typed failure with evidence suitable for a retained RED sidecar."""

    result: Final = "RED"

    def __init__(self, reason_code: str, evidence: Mapping[str, object]) -> None:
        self.reason_code = reason_code
        self.evidence = {
            **copy.deepcopy(dict(evidence)),
            "result": "RED",
            "reason_code": reason_code,
        }
        super().__init__(
            f"projects-metrics source checkpoint RED [{reason_code}]"
        )


def _fail(reason_code: str, **evidence: object) -> None:
    raise ProjectsMetricsSourceCheckpointError(reason_code, evidence)


def _positive(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        _fail("positive_integer_invalid", label=label, observed=value)
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _json_bytes(value: Mapping[str, object]) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _write_exclusive(path: Path, payload: bytes, reason_code: str) -> None:
    target = path.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with target.open("xb") as stream:
            stream.write(payload)
    except FileExistsError as error:
        raise ProjectsMetricsSourceCheckpointError(
            reason_code, {"path": str(target)}
        ) from error


def _managed_binding(
    value: object, *, require_event: bool
) -> dict[str, object]:
    snapshot = dict(value) if isinstance(value, Mapping) else {}
    played = snapshot.get("played_character")
    diagnostics = snapshot.get("diagnostics")
    active = snapshot.get("active_event")
    binding = {
        "snapshot_id": snapshot.get("snapshot_id"),
        "revision": snapshot.get("revision"),
        "native_revision": snapshot.get("native_revision"),
        "date_raw": snapshot.get("date_raw"),
        "paused": snapshot.get("paused"),
        "map_ready": snapshot.get("map_ready"),
        "player_character_id": (
            played.get("character_id") if isinstance(played, Mapping) else None
        ),
        "bridge_pid": (
            diagnostics.get("bridge_pid")
            if isinstance(diagnostics, Mapping)
            else None
        ),
        "connection_generation": (
            diagnostics.get("connection_generation")
            if isinstance(diagnostics, Mapping)
            else None
        ),
        "active_event_instance_id": (
            active.get("instance_id") if isinstance(active, Mapping) else None
        ),
        "active_event_option_count": (
            active.get("option_count") if isinstance(active, Mapping) else None
        ),
    }
    valid = (
        binding["paused"] is True
        and binding["map_ready"] is True
        and isinstance(binding["snapshot_id"], str)
        and bool(binding["snapshot_id"])
        and isinstance(binding["revision"], int)
        and not isinstance(binding["revision"], bool)
        and int(binding["revision"]) >= 0
        and _positive(binding["native_revision"], "native_revision") > 0
        and isinstance(binding["date_raw"], int)
        and not isinstance(binding["date_raw"], bool)
        and _positive(binding["player_character_id"], "player_character_id") > 0
        and _positive(binding["bridge_pid"], "bridge_pid") > 0
        and _positive(
            binding["connection_generation"], "connection_generation"
        )
        > 0
        and (
            (require_event and _positive(
                binding["active_event_instance_id"], "active_event_instance_id"
            ) > 0)
            or (not require_event and active is None)
        )
    )
    if not valid:
        _fail(
            "managed_paused_binding_invalid",
            require_event=require_event,
            binding=binding,
        )
    return binding


def _same_frame(left: Mapping[str, object], right: Mapping[str, object]) -> bool:
    return all(
        left.get(key) == right.get(key)
        for key in (
            "snapshot_id",
            "revision",
            "native_revision",
            "date_raw",
            "player_character_id",
            "bridge_pid",
            "connection_generation",
            "active_event_instance_id",
        )
    )


def _same_save_binding(
    left: Mapping[str, object], right: Mapping[str, object]
) -> bool:
    return all(
        left.get(key) == right.get(key)
        for key in (
            "date_raw",
            "player_character_id",
            "bridge_pid",
            "connection_generation",
            "active_event_instance_id",
        )
    )


def _typed_character(scope: object, label: str) -> int:
    identity = scope.get("typed_identity") if isinstance(scope, Mapping) else None
    if not (
        isinstance(identity, Mapping)
        and identity.get("status") == "available"
        and identity.get("kind") == "character"
    ):
        _fail("cp26_character_scope_unavailable", label=label, scope=scope)
    return _positive(identity.get("character_id"), label)


def _lineage(value: object) -> dict[str, object]:
    lineage = copy.deepcopy(dict(value)) if isinstance(value, Mapping) else {}
    valid = (
        lineage.get("schema_version") == 2
        and lineage.get("kind") == "zg361_projects_metrics_capture_lineage"
        and lineage.get("evidence_class") == "real_ck3"
        and lineage.get("state_origin") == "managed_product"
        and lineage.get("single_player") is True
        and lineage.get("product_only_mount") is True
        and isinstance(lineage.get("seed_lineage_id"), str)
        and bool(lineage.get("seed_lineage_id"))
        and isinstance(lineage.get("capture_lineage_id"), str)
        and bool(lineage.get("capture_lineage_id"))
        and isinstance(lineage.get("source_git_commit"), str)
        and _GIT_SHA.fullmatch(str(lineage.get("source_git_commit"))) is not None
        and isinstance(lineage.get("product_tree_sha256"), str)
        and _SHA256.fullmatch(str(lineage.get("product_tree_sha256"))) is not None
        and isinstance(lineage.get("product_enabled_mod"), str)
        and bool(lineage.get("product_enabled_mod"))
        and lineage.get("enabled_mods") == [lineage.get("product_enabled_mod")]
        and str(lineage.get("runtime_product_tree_sha256", "")).upper()
        == str(lineage.get("product_tree_sha256", "")).upper()
        and lineage.get("fixture_used") is False
        and lineage.get("console_used") is False
        and lineage.get("test_decision_used") is False
        and lineage.get("generic_character_rebind_used") is False
    )
    if not valid:
        _fail("capture_lineage_invalid", capture_lineage=lineage)
    return lineage


def observe_cp26_route_ui_live(
    service: ProjectsMetricsUiService,
    *,
    route: str,
    capture_lineage: Mapping[str, object],
    live_mode: str,
) -> dict[str, object]:
    """Observe real CP26 and submit A/B; the ACK is never business proof."""

    if live_mode != LIVE_MODE:
        _fail("explicit_live_mode_required", observed=live_mode)
    lineage = _lineage(capture_lineage)
    normalized_route = route.upper() if isinstance(route, str) else ""
    option_number = {"A": 1, "B": 2}.get(normalized_route)
    if option_number is None:
        _fail("cp26_route_not_captureable", route=route, allowed=["A", "B"])

    before = _managed_binding(service.snapshot(), require_event=True)
    response = service.query_current_event_window_context_v1(
        int(before["active_event_instance_id"]),
        expected_revision=int(before["revision"]),
    )
    context = (
        response.get("current_event_window_context")
        if isinstance(response, Mapping)
        else None
    )
    readiness = context.get("readiness") if isinstance(context, Mapping) else None
    saved_rows = context.get("saved_scopes") if isinstance(context, Mapping) else None
    saved = {
        str(row.get("name")): row.get("scope")
        for row in saved_rows
        if isinstance(row, Mapping) and isinstance(row.get("name"), str)
    } if isinstance(saved_rows, list) else {}
    owner = _typed_character(
        context.get("root_scope") if isinstance(context, Mapping) else None,
        "root_scope",
    )
    saved_owner = _typed_character(saved.get("zg361_cp_e_owner"), "saved_owner")
    subject = _typed_character(saved.get("zg361_cp_e_subject"), "saved_subject")
    options = context.get("options") if isinstance(context, Mapping) else None
    option = next(
        (
            row
            for row in options
            if isinstance(row, Mapping)
            and row.get("native_option_index") == option_number - 1
        ),
        None,
    ) if isinstance(options, list) else None
    valid = (
        isinstance(response, Mapping)
        and response.get("status") == "available"
        and isinstance(context, Mapping)
        and context.get("status") == "available"
        and context.get("event_definition_key") == SOURCE_EVENT
        and context.get("current_event_instance_id")
        == before["active_event_instance_id"]
        and context.get("snapshot_revision") == before["native_revision"]
        and context.get("date_raw") == before["date_raw"]
        and isinstance(readiness, Mapping)
        and all(
            readiness.get(key) is True
            for key in (
                "event_definition_identity_ready",
                "root_scope_ready",
                "saved_scopes_ready",
                "option_presentation_ready",
            )
        )
        and owner == saved_owner == before["player_character_id"]
        and owner != subject
        and "zg361_cp_e_cycle" in saved
        and "zg361_cp_e_case" in saved
        and isinstance(option, Mapping)
        and option.get("shown") is True
        and option.get("enabled") is True
    )
    if not valid:
        _fail(
            "real_cp26_ui_not_ready",
            binding=before,
            owner_character_id=owner,
            subject_character_id=subject,
            response=response,
        )
    acknowledgement = service.select_event_option(
        option_number,
        event_instance_id=int(before["active_event_instance_id"]),
        expected_revision=int(before["revision"]),
    )
    if not (
        isinstance(acknowledgement, Mapping)
        and acknowledgement.get("accepted") is True
        and acknowledgement.get("status") == "submitted"
    ):
        _fail(
            "cp26_route_submission_rejected",
            route=normalized_route,
            acknowledgement=acknowledgement,
        )
    return {
        "schema_version": 1,
        "kind": UI_RECEIPT_KIND,
        "result": "GREEN",
        "evidence_class": "real_ck3",
        "state_origin": "managed_product",
        "source_backend_id": "native-headless",
        "event_definition_key": SOURCE_EVENT,
        "route": normalized_route,
        "option_number": option_number,
        "native_option_index": option_number - 1,
        "owner_character_id": owner,
        "subject_character_id": subject,
        "date_raw": int(before["date_raw"]),
        "seed_lineage_id": lineage["seed_lineage_id"],
        "capture_lineage_id": lineage["capture_lineage_id"],
        "product_tree_sha256": str(lineage["product_tree_sha256"]).upper(),
        "event_binding": before,
        "event_context": copy.deepcopy(dict(context)),
        "selection_submission": copy.deepcopy(dict(acknowledgement)),
        "ui_state_verified": True,
        "provider_observed": False,
        "business_state_proven": False,
        "action_ack_is_business_postcondition": False,
        "fixture_used": False,
        "console_used": False,
        "test_decision_used": False,
        "generic_character_rebind_used": False,
    }


def _load_ui_receipt(
    path: Path,
    *,
    lineage: Mapping[str, object],
    owner: int,
    subject: int,
) -> tuple[dict[str, object], bytes, str]:
    source = path.expanduser().resolve()
    try:
        raw = source.read_bytes()
        value = json.loads(raw.decode("utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ProjectsMetricsSourceCheckpointError(
            "cp26_ui_receipt_unreadable",
            {"path": str(source), "error": f"{type(error).__name__}: {error}"},
        ) from error
    receipt = dict(value) if isinstance(value, Mapping) else {}
    selection = receipt.get("selection_submission")
    valid = (
        receipt.get("schema_version") == 1
        and receipt.get("kind") == UI_RECEIPT_KIND
        and receipt.get("result") == "GREEN"
        and receipt.get("evidence_class") == "real_ck3"
        and receipt.get("state_origin") == "managed_product"
        and receipt.get("source_backend_id") == "native-headless"
        and receipt.get("event_definition_key") == SOURCE_EVENT
        and receipt.get("route") in {"A", "B"}
        and receipt.get("option_number") in {1, 2}
        and receipt.get("option_number")
        == {"A": 1, "B": 2}.get(receipt.get("route"))
        and receipt.get("native_option_index")
        == int(receipt.get("option_number", 0)) - 1
        and receipt.get("owner_character_id") == owner
        and receipt.get("subject_character_id") == subject
        and receipt.get("seed_lineage_id") == lineage.get("seed_lineage_id")
        and receipt.get("capture_lineage_id")
        == lineage.get("capture_lineage_id")
        and str(receipt.get("product_tree_sha256", "")).upper()
        == str(lineage.get("product_tree_sha256", "")).upper()
        and receipt.get("ui_state_verified") is True
        and receipt.get("provider_observed") is False
        and receipt.get("business_state_proven") is False
        and receipt.get("action_ack_is_business_postcondition") is False
        and isinstance(selection, Mapping)
        and selection.get("accepted") is True
        and selection.get("status") == "submitted"
        and receipt.get("fixture_used") is False
        and receipt.get("console_used") is False
        and receipt.get("test_decision_used") is False
        and receipt.get("generic_character_rebind_used") is False
    )
    if not valid:
        _fail(
            "cp26_ui_receipt_invalid",
            path=str(source),
            owner_character_id=owner,
            subject_character_id=subject,
            receipt=receipt,
        )
    return receipt, raw, hashlib.sha256(raw).hexdigest().upper()


def capture_projects_metrics_source_checkpoint_live(
    service: ProjectsMetricsCheckpointService,
    *,
    owner_character_id: int,
    capture_lineage: Mapping[str, object],
    ui_receipt_path: Path,
    checkpoint_root: Path,
    registry_path: Path,
    live_mode: str,
) -> dict[str, object]:
    """Freeze a provider-proven CP26/P3-pending product checkpoint."""

    if live_mode != LIVE_MODE:
        _fail("explicit_live_mode_required", observed=live_mode)
    owner = _positive(owner_character_id, "owner_character_id")
    lineage = _lineage(capture_lineage)
    initial_snapshot = service.snapshot()
    initial = _managed_binding(initial_snapshot, require_event=False)
    subject = int(initial["player_character_id"])
    if owner == subject:
        _fail(
            "owner_must_be_distinct_ai",
            owner_character_id=owner,
            subject_character_id=subject,
        )
    ui_receipt, ui_bytes, ui_sha = _load_ui_receipt(
        ui_receipt_path,
        lineage=lineage,
        owner=owner,
        subject=subject,
    )

    preflight = preflight_projects_metrics_gameplay_action_cell(
        service,
        owner_character_id=owner,
        request_nonce_prefix="zg361.projects.metrics.source.capture",
    )
    preflight_binding = preflight.get("binding")
    source = preflight.get("source_checkpoint")
    provider = preflight.get("provider_response")
    valid_preflight = (
        preflight.get("result") == "READY"
        and preflight.get("ready_to_run") is True
        and preflight.get("checkpoint_mode") == "cp26_ready_p3_absent"
        and isinstance(preflight_binding, Mapping)
        and isinstance(source, Mapping)
        and isinstance(provider, Mapping)
        and provider.get("checkpoint_state") == "cp26_ready_p3_absent"
        and source.get("owner_character_id") == owner
        and source.get("subject_character_id") == subject
        and isinstance(source.get("cycle_serial"), int)
        and not isinstance(source.get("cycle_serial"), bool)
        and int(source.get("cycle_serial")) > 0
        and isinstance(source.get("case_serial"), int)
        and not isinstance(source.get("case_serial"), bool)
        and int(source.get("case_serial")) > 0
        and isinstance(source.get("contribution_receipt_id"), int)
        and int(source.get("contribution_receipt_id")) > 0
        and isinstance(source.get("contribution_receipt_revision"), int)
        and int(source.get("contribution_receipt_revision")) > 0
        and preflight.get("gameplay_action_executed") is False
        and preflight.get("action_ack_is_business_postcondition") is False
    )
    if not valid_preflight:
        _fail("cp26_provider_source_not_ready", preflight=preflight)
    for key in (
        "snapshot_id",
        "revision",
        "native_revision",
        "date_raw",
        "player_character_id",
        "connection_generation",
        "active_event_instance_id",
    ):
        if initial.get(key) != preflight_binding.get(key):
            _fail(
                "provider_query_crossed_source_frame",
                key=key,
                initial=initial,
                preflight_binding=preflight_binding,
            )
    after_query_snapshot = service.snapshot()
    after_query = _managed_binding(after_query_snapshot, require_event=False)
    if not _same_frame(initial, after_query):
        _fail(
            "provider_query_crossed_source_frame",
            initial=initial,
            after_query=after_query,
        )

    save = getattr(service, "save_checkpoint", None)
    if not callable(save):
        _fail("native_save_provider_missing")
    save_result = save(expected_revision=int(initial["revision"]))
    checkpoint = (
        save_result.get("checkpoint")
        if isinstance(save_result, Mapping)
        else None
    )
    checkpoint = dict(checkpoint) if isinstance(checkpoint, Mapping) else {}
    raw_path = checkpoint.get("path")
    source_path = (
        Path(str(raw_path)).resolve() if isinstance(raw_path, str) else Path()
    )
    expected_bytes = checkpoint.get("size")
    expected_sha = str(checkpoint.get("sha256", "")).upper()
    save_valid = (
        isinstance(save_result, Mapping)
        and save_result.get("accepted") is True
        and checkpoint.get("status") == "saved"
        and isinstance(raw_path, str)
        and source_path.is_absolute()
        and source_path.is_file()
        and isinstance(expected_bytes, int)
        and not isinstance(expected_bytes, bool)
        and expected_bytes > 0
        and source_path.stat().st_size == expected_bytes
        and _SHA256.fullmatch(expected_sha) is not None
        and _sha256(source_path) == expected_sha
        and checkpoint.get("date_raw") == initial["date_raw"]
    )
    if not save_valid:
        _fail("native_checkpoint_save_invalid", save_result=save_result)
    post_save_snapshot = service.snapshot()
    post_save = _managed_binding(post_save_snapshot, require_event=False)
    if not _same_save_binding(initial, post_save):
        _fail(
            "native_save_changed_product_binding",
            initial=initial,
            post_save=post_save,
        )

    root = checkpoint_root.expanduser().resolve()
    registry = registry_path.expanduser().resolve()
    if registry.exists():
        _fail("source_checkpoint_registry_already_exists", path=str(registry))
    root.mkdir(parents=True, exist_ok=True)
    stem = f"01-{SPAN_ID}-{expected_sha[:16].lower()}"
    checkpoint_target = root / f"{stem}.ck3"
    ui_target = root / f"{stem}.ui-receipt.json"
    provider_target = root / f"{stem}.provider-receipt.json"
    if any(path.exists() for path in (checkpoint_target, ui_target, provider_target)):
        _fail(
            "source_checkpoint_archive_collision",
            paths=[str(checkpoint_target), str(ui_target), str(provider_target)],
        )
    shutil.copyfile(source_path, checkpoint_target)
    if (
        checkpoint_target.stat().st_size != expected_bytes
        or _sha256(checkpoint_target) != expected_sha
    ):
        _fail(
            "source_checkpoint_archive_mismatch",
            source_path=str(source_path),
            checkpoint_path=str(checkpoint_target),
        )
    _write_exclusive(
        ui_target, ui_bytes, "source_checkpoint_ui_receipt_archive_collision"
    )
    provider_bytes = _json_bytes(dict(provider))
    _write_exclusive(
        provider_target,
        provider_bytes,
        "source_checkpoint_provider_receipt_archive_collision",
    )
    provider_sha = hashlib.sha256(provider_bytes).hexdigest().upper()

    source_receipt = {
        "result": "GREEN",
        "evidence_class": "real_ck3",
        "provider_observed": True,
        "ui_state_verified": True,
        "fixture_used": False,
        "console_used": False,
        "span_id": SPAN_ID,
        "event_definition_key": SOURCE_EVENT,
        "owner_character_id": owner,
        "player_character_id": subject,
        "date_raw": int(initial["date_raw"]),
        "checkpoint_sha256": expected_sha,
        "save_lineage_id": lineage["seed_lineage_id"],
        "cp26_route": ui_receipt["route"],
        "cp26_ui_receipt": {
            "path": str(ui_target),
            "bytes": len(ui_bytes),
            "sha256": ui_sha,
        },
        "projects_metrics_provider_receipt": {
            "path": str(provider_target),
            "bytes": len(provider_bytes),
            "sha256": provider_sha,
        },
        "provider_checkpoint_state": "cp26_ready_p3_absent",
        "p3_initializer_not_run": True,
        "action_ack_is_business_postcondition": False,
    }

    entry = {
        "span_id": SPAN_ID,
        "handler": HANDLER,
        "source_event_definition_key": SOURCE_EVENT,
        "route": ui_receipt["route"],
        "owner_character_id": owner,
        "player_character_id": subject,
        "subject_character_id": subject,
        "cycle_serial": int(source["cycle_serial"]),
        "case_serial": int(source["case_serial"]),
        "contribution_receipt_id": int(source["contribution_receipt_id"]),
        "contribution_receipt_revision": int(
            source["contribution_receipt_revision"]
        ),
        "contribution_value": int(source["contribution_value"]),
        "date_raw": int(initial["date_raw"]),
        "checkpoint": {
            "path": str(checkpoint_target),
            "bytes": int(expected_bytes),
            "sha256": expected_sha,
            "save_lineage_id": lineage["seed_lineage_id"],
        },
        "source_snapshot_binding": initial,
        "post_save_snapshot_binding": post_save,
        "ui_receipt": {
            "path": str(ui_target),
            "bytes": len(ui_bytes),
            "sha256": ui_sha,
            "payload": ui_receipt,
        },
        "provider_receipt": {
            "path": str(provider_target),
            "bytes": len(provider_bytes),
            "sha256": provider_sha,
            "payload": copy.deepcopy(dict(provider)),
        },
        "source_receipt": source_receipt,
        "native_save_receipt": copy.deepcopy(dict(save_result)),
        "capture_checks": {
            "played_character_is_subject": True,
            "owner_is_distinct": True,
            "owner_is_ai_by_product_checkpoint_contract": True,
            "paused_map": True,
            "no_active_player_event": True,
            "cp26_route_is_a_or_b": True,
            "cp26_contribution_receipt_provider_observed": True,
            "p3_initializer_not_run": True,
            "provider_state_is_cp26_ready_p3_absent": True,
            "checkpoint_bytes_sha256_verified": True,
            "ui_provider_lineage_joined": True,
            "action_ack_used_as_business_state": False,
        },
    }
    registry_value = {
        "schema_version": REGISTRY_SCHEMA_VERSION,
        "registry_kind": REGISTRY_KIND,
        "result": "GREEN",
        "readiness": "captured-real-checkpoint",
        "evidence_class": "real_ck3",
        "state_origin": "managed_product",
        "fixture_used": False,
        "console_used": False,
        "test_decision_used": False,
        "generic_character_rebind_used": False,
        "action_ack_is_business_postcondition": False,
        "provider_observed_business_state": True,
        "seed_lineage_id": lineage["seed_lineage_id"],
        "capture_lineage": lineage,
        "entries": [entry],
    }
    _write_exclusive(
        registry,
        _json_bytes(registry_value),
        "source_checkpoint_registry_already_exists",
    )
    return copy.deepcopy(registry_value)


def validate_projects_metrics_source_checkpoint_registry(
    value: object,
    *,
    expected_seed_lineage_id: str | None = None,
) -> dict[str, object]:
    """Re-hash a schema-2 registry and both retained observation receipts."""

    registry = dict(value) if isinstance(value, Mapping) else {}
    rows = registry.get("entries")
    lineage = _lineage(registry.get("capture_lineage"))
    valid_header = (
        registry.get("schema_version") == REGISTRY_SCHEMA_VERSION
        and registry.get("registry_kind") == REGISTRY_KIND
        and registry.get("result") == "GREEN"
        and registry.get("readiness") == "captured-real-checkpoint"
        and registry.get("evidence_class") == "real_ck3"
        and registry.get("state_origin") == "managed_product"
        and registry.get("fixture_used") is False
        and registry.get("console_used") is False
        and registry.get("test_decision_used") is False
        and registry.get("generic_character_rebind_used") is False
        and registry.get("action_ack_is_business_postcondition") is False
        and registry.get("provider_observed_business_state") is True
        and registry.get("seed_lineage_id") == lineage.get("seed_lineage_id")
        and (
            expected_seed_lineage_id is None
            or registry.get("seed_lineage_id") == expected_seed_lineage_id
        )
        and isinstance(rows, list)
        and len(rows) == 1
        and isinstance(rows[0], Mapping)
    )
    if not valid_header:
        _fail("source_checkpoint_registry_header_invalid", registry=registry)
    assert isinstance(rows, list) and isinstance(rows[0], Mapping)
    entry = dict(rows[0])
    checkpoint = entry.get("checkpoint")
    ui = entry.get("ui_receipt")
    provider = entry.get("provider_receipt")
    source_receipt = entry.get("source_receipt")
    checks = entry.get("capture_checks")
    checkpoint = dict(checkpoint) if isinstance(checkpoint, Mapping) else {}
    ui = dict(ui) if isinstance(ui, Mapping) else {}
    provider = dict(provider) if isinstance(provider, Mapping) else {}
    source_receipt = (
        dict(source_receipt) if isinstance(source_receipt, Mapping) else {}
    )

    def locator_valid(locator: Mapping[str, object]) -> bool:
        raw = locator.get("path")
        path = Path(str(raw)).resolve() if isinstance(raw, str) else Path()
        return bool(
            isinstance(raw, str)
            and path.is_absolute()
            and path.is_file()
            and isinstance(locator.get("bytes"), int)
            and not isinstance(locator.get("bytes"), bool)
            and path.stat().st_size == locator.get("bytes")
            and isinstance(locator.get("sha256"), str)
            and _SHA256.fullmatch(str(locator.get("sha256"))) is not None
            and _sha256(path) == str(locator.get("sha256")).upper()
        )

    checkpoint_valid = locator_valid(checkpoint)
    ui_valid = locator_valid(ui)
    provider_valid = locator_valid(provider)
    ui_payload = ui.get("payload")
    provider_payload = provider.get("payload")
    serialized_provider_matches = bool(
        isinstance(provider_payload, Mapping)
        and hashlib.sha256(_json_bytes(dict(provider_payload))).hexdigest().upper()
        == str(provider.get("sha256", "")).upper()
    )
    ui_payload_matches = False
    if ui_valid and isinstance(ui_payload, Mapping):
        try:
            ui_file_value = json.loads(
                Path(str(ui["path"])).read_text(encoding="utf-8-sig")
            )
            ui_payload_matches = ui_file_value == dict(ui_payload)
        except (OSError, UnicodeError, json.JSONDecodeError):
            ui_payload_matches = False
    checks_valid = bool(
        isinstance(checks, Mapping)
        and checks.get("action_ack_used_as_business_state") is False
        and all(
            value is True
            for name, value in checks.items()
            if name != "action_ack_used_as_business_state"
        )
    )
    entry_valid = (
        entry.get("span_id") == SPAN_ID
        and entry.get("handler") == HANDLER
        and entry.get("source_event_definition_key") == SOURCE_EVENT
        and entry.get("route") in {"A", "B"}
        and _positive(entry.get("owner_character_id"), "owner_character_id")
        != _positive(entry.get("subject_character_id"), "subject_character_id")
        and entry.get("player_character_id") == entry.get("subject_character_id")
        and _positive(entry.get("cycle_serial"), "cycle_serial") > 0
        and _positive(entry.get("case_serial"), "case_serial") > 0
        and _positive(entry.get("contribution_receipt_id"), "receipt_id") > 0
        and _positive(
            entry.get("contribution_receipt_revision"), "receipt_revision"
        )
        > 0
        and checkpoint.get("save_lineage_id") == registry.get("seed_lineage_id")
        and checkpoint_valid
        and ui_valid
        and ui_payload_matches
        and provider_valid
        and serialized_provider_matches
        and isinstance(ui_payload, Mapping)
        and ui_payload.get("route") == entry.get("route")
        and ui_payload.get("owner_character_id")
        == entry.get("owner_character_id")
        and ui_payload.get("subject_character_id")
        == entry.get("subject_character_id")
        and isinstance(provider_payload, Mapping)
        and provider_payload.get("status") == "available"
        and provider_payload.get("checkpoint_state")
        == "cp26_ready_p3_absent"
        and source_receipt.get("result") == "GREEN"
        and source_receipt.get("evidence_class") == "real_ck3"
        and source_receipt.get("provider_observed") is True
        and source_receipt.get("ui_state_verified") is True
        and source_receipt.get("fixture_used") is False
        and source_receipt.get("console_used") is False
        and source_receipt.get("span_id") == SPAN_ID
        and source_receipt.get("event_definition_key") == SOURCE_EVENT
        and source_receipt.get("owner_character_id")
        == entry.get("owner_character_id")
        and source_receipt.get("player_character_id")
        == entry.get("player_character_id")
        and source_receipt.get("date_raw") == entry.get("date_raw")
        and str(source_receipt.get("checkpoint_sha256", "")).upper()
        == str(checkpoint.get("sha256", "")).upper()
        and source_receipt.get("save_lineage_id")
        == registry.get("seed_lineage_id")
        and source_receipt.get("cp26_route") == entry.get("route")
        and source_receipt.get("cp26_ui_receipt")
        == {key: ui.get(key) for key in ("path", "bytes", "sha256")}
        and source_receipt.get("projects_metrics_provider_receipt")
        == {
            key: provider.get(key) for key in ("path", "bytes", "sha256")
        }
        and source_receipt.get("p3_initializer_not_run") is True
        and source_receipt.get("provider_checkpoint_state")
        == "cp26_ready_p3_absent"
        and source_receipt.get("action_ack_is_business_postcondition") is False
        and checks_valid
    )
    if not entry_valid:
        _fail(
            "source_checkpoint_registry_entry_invalid",
            checkpoint_valid=checkpoint_valid,
            ui_valid=ui_valid,
            ui_payload_matches=ui_payload_matches,
            provider_valid=provider_valid,
            serialized_provider_matches=serialized_provider_matches,
            checks_valid=checks_valid,
            entry=entry,
        )
    return {
        "schema_version": REGISTRY_SCHEMA_VERSION,
        "registry_kind": REGISTRY_KIND,
        "result": "GREEN",
        "readiness": "captured-real-checkpoint",
        "checkpoint_sha256": checkpoint["sha256"],
        "checkpoint_bytes": checkpoint["bytes"],
        "seed_lineage_id": registry["seed_lineage_id"],
        "owner_character_id": entry["owner_character_id"],
        "subject_character_id": entry["subject_character_id"],
        "route": entry["route"],
        "provider_observed_business_state": True,
        "action_ack_is_business_postcondition": False,
    }


def _load_json(path: Path, label: str) -> dict[str, object]:
    try:
        value = json.loads(path.expanduser().resolve().read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ProjectsMetricsSourceCheckpointError(
            f"{label}_unreadable", {"path": str(path), "message": str(error)}
        ) from error
    if not isinstance(value, dict):
        _fail(f"{label}_invalid", path=str(path))
    return value


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--live",
        action="store_true",
        help="explicitly attach to an already-running managed native session",
    )
    parser.add_argument("--bridge-pipe")
    parser.add_argument("--state-dir", type=Path)
    parser.add_argument("--save-dir", type=Path)
    subparsers = parser.add_subparsers(dest="operation", required=True)
    observe = subparsers.add_parser("observe-ui")
    observe.add_argument("--route", choices=("A", "B"), required=True)
    observe.add_argument("--capture-lineage", type=Path, required=True)
    observe.add_argument("--output", type=Path, required=True)
    capture = subparsers.add_parser("capture-checkpoint")
    capture.add_argument("--owner-character-id", type=int, required=True)
    capture.add_argument("--capture-lineage", type=Path, required=True)
    capture.add_argument("--ui-receipt", type=Path, required=True)
    capture.add_argument("--checkpoint-root", type=Path, required=True)
    capture.add_argument("--registry", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if not args.live:
        _fail("explicit_live_mode_required", observed=False)
    if not all((args.bridge_pipe, args.state_dir, args.save_dir)):
        _fail(
            "managed_session_binding_missing",
            bridge_pipe=args.bridge_pipe,
            state_dir=str(args.state_dir) if args.state_dir else None,
            save_dir=str(args.save_dir) if args.save_dir else None,
        )
    lineage = _load_json(args.capture_lineage, "capture_lineage")
    driver = NativeHeadlessGameplayDriver(
        args.bridge_pipe,
        state_dir=args.state_dir.expanduser().resolve(),
        save_dir=args.save_dir.expanduser().resolve(),
    )
    service = GameplayBridgeService(driver)
    try:
        if args.operation == "observe-ui":
            result = observe_cp26_route_ui_live(
                service,
                route=args.route,
                capture_lineage=lineage,
                live_mode=LIVE_MODE,
            )
            _write_exclusive(
                args.output,
                _json_bytes(result),
                "cp26_ui_receipt_already_exists",
            )
        else:
            result = capture_projects_metrics_source_checkpoint_live(
                service,
                owner_character_id=args.owner_character_id,
                capture_lineage=lineage,
                ui_receipt_path=args.ui_receipt,
                checkpoint_root=args.checkpoint_root,
                registry_path=args.registry,
                live_mode=LIVE_MODE,
            )
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    finally:
        driver.close()


__all__ = [
    "HANDLER",
    "LIVE_MODE",
    "READINESS",
    "REGISTRY_KIND",
    "REGISTRY_SCHEMA_VERSION",
    "SOURCE_EVENT",
    "SPAN_ID",
    "UI_RECEIPT_KIND",
    "ProjectsMetricsCheckpointService",
    "ProjectsMetricsSourceCheckpointError",
    "ProjectsMetricsUiService",
    "capture_projects_metrics_source_checkpoint_live",
    "observe_cp26_route_ui_live",
    "validate_projects_metrics_source_checkpoint_registry",
]


if __name__ == "__main__":
    raise SystemExit(main())
