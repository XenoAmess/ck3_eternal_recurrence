#!/usr/bin/env python3
"""Capture one real Promotion source checkpoint from an owned live session.

The callable is deliberately narrower than a CK3 runner: it consumes an
already-started managed product-only service, waits for the exact paused
``zg361pp.147`` source frame, verifies option 1 without selecting it, and
archives the native save bytes.  Its schema-2 output is the first deterministic
merge input for the four-entry canonical registry, never a complete registry.
"""

from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Callable, Mapping
from pathlib import Path
import re
import shutil
import time
from typing import Final, Protocol

from xar_autoplayer.bridge.event_window_context_contract import (
    QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_CAPABILITY,
)
from zg361_phase2_promotion_compensation_action_cell import (
    SOURCE_EVENT_DEFINITION_KEY,
    SOURCE_OPTION_NUMBER,
    _event_context,
    _snapshot_binding,
)
from zhongguo_phase2_event_choreography import phase2_event_sequence_plan
from zhongguo_phase2_source_checkpoint_provider import (
    CHECKPOINT_REQUIRED_HANDLERS,
    SOURCE_CHECKPOINT_REGISTRY_KIND,
    SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION,
)
from zhongguo_phase2_source_checkpoint_registry import (
    SOURCE_CHECKPOINT_CAPTURE_MANIFEST_KIND,
)


CAPTURE_ARTIFACT_KIND: Final = (
    "zg361_phase2_source_checkpoint_capture_artifact"
)
CAPTURE_RECEIPT_KIND: Final = (
    "zg361_phase2_promotion_source_checkpoint_receipt"
)
HANDLER: Final = "capture_promotion_compensation"
SPAN_ID: Final = "phase2_promotion_compensation"
SAVE_CHECKPOINT_CAPABILITY: Final = "game.command.save-checkpoint"
SAVE_CHECKPOINT_STEP: Final = "save-checkpoint"
CAPTURE_READINESS: Final = "captured-real-promotion-source"
EXACT_GAME_VERSION: Final = "1.19.0.6"
EXACT_EXE_SHA256: Final = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
_SHA256: Final = re.compile(r"^[0-9A-F]{64}$")
_CHARACTER_SCOPES: Final = (
    "zg361_pp_prompt_owner",
    "zg361_pp_prompt_subject",
)
_SCALAR_SCOPES: Final = (
    "zg361_pp_prompt_case",
    "zg361_pp_prompt_cycle",
    "zg361_pp_prompt_mechanism",
    "zg361_pp_prompt_state",
)
_BINDING_FIELDS: Final = (
    "snapshot_id",
    "revision",
    "native_revision",
    "date_raw",
    "player_character_id",
    "connection_generation",
    "event_instance_id",
    "event_option_count",
)


class PromotionSourceCaptureService(Protocol):
    def capabilities(self) -> dict[str, object]: ...

    def snapshot(self) -> dict[str, object]: ...

    def query_current_event_window_context_v1(
        self, event_instance_id: int, *, expected_revision: int
    ) -> dict[str, object]: ...

    def save_checkpoint(self, *, expected_revision: int) -> dict[str, object]: ...


class PromotionSourceCheckpointCaptureError(RuntimeError):
    result: Final = "RED"

    def __init__(self, reason_code: str, evidence: Mapping[str, object]) -> None:
        self.reason_code = reason_code
        self.evidence = {
            **copy.deepcopy(dict(evidence)),
            "result": "RED",
            "reason_code": reason_code,
        }
        super().__init__(f"promotion source capture RED [{reason_code}]")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _positive(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _managed_product_contract(
    value: object,
    *,
    seed_lineage_id: str,
    capture_lineage: Mapping[str, object],
) -> dict[str, object]:
    session = copy.deepcopy(dict(value)) if isinstance(value, Mapping) else {}
    lineage = copy.deepcopy(dict(capture_lineage))
    pid = session.get("tracked_ck3_pid")
    generation = session.get("connection_generation")
    valid = (
        session.get("schema_version") == 1
        and session.get("kind") == "zg361_phase2_managed_product_session"
        and session.get("result") == "GREEN"
        and session.get("managed_native_session") is True
        and session.get("product_only_runtime") is True
        and session.get("acceptance_fixture_loaded") is False
        and session.get("same_pid_gameplay_continuation_authorized") is True
        and _positive(pid)
        and _positive(generation)
        and session.get("seed_lineage_id") == seed_lineage_id
        and session.get("game_version") == EXACT_GAME_VERSION
        and str(session.get("executable_sha256", "")).upper()
        == EXACT_EXE_SHA256
        and lineage.get("seed_lineage_id") == seed_lineage_id
        and lineage.get("game_version") == EXACT_GAME_VERSION
        and str(lineage.get("executable_sha256", "")).upper()
        == EXACT_EXE_SHA256
        and lineage.get("evidence_class") == "real_ck3"
        and lineage.get("session_kind") == "managed_product_session"
        and lineage.get("product_only_runtime") is True
        and lineage.get("tracked_ck3_pid") == pid
        and lineage.get("connection_generation") == generation
        and lineage.get("fixture_used") is False
        and lineage.get("ocr_used") is False
        and lineage.get("coordinates_used") is False
        and lineage.get("console_used") is False
        and lineage.get("generic_character_rebind_used") is False
    )
    if not valid:
        raise PromotionSourceCheckpointCaptureError(
            "managed_product_session_contract_invalid",
            {
                "managed_session": session,
                "seed_lineage_id": seed_lineage_id,
                "capture_lineage": lineage,
            },
        )
    return session


def _capability_contract(
    service: PromotionSourceCaptureService,
    *,
    tracked_ck3_pid: int,
    connection_generation: int,
) -> dict[str, object]:
    capabilities = service.capabilities()
    bridge = capabilities.get("bridge_capabilities")
    steps = capabilities.get("action_steps")
    diagnostics = capabilities.get("diagnostics")
    bridge_set = set(bridge) if isinstance(bridge, list) else set()
    step_set = set(steps) if isinstance(steps, list) else set()
    checks = {
        "native_headless": capabilities.get("mode") == "native-headless"
        and capabilities.get("backend_id") == "native-headless"
        and capabilities.get("visual_fallback") is False,
        "connected_managed_pid_generation": isinstance(diagnostics, Mapping)
        and diagnostics.get("connected") is True
        and diagnostics.get("bridge_pid") == tracked_ck3_pid
        and diagnostics.get("connection_generation") == connection_generation,
        "event_query_capability": (
            QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_CAPABILITY in bridge_set
            and capabilities.get(
                "current_event_window_context_v1_query_supported"
            )
            is True
        ),
        "save_checkpoint_capability": SAVE_CHECKPOINT_CAPABILITY in bridge_set
        and SAVE_CHECKPOINT_STEP in step_set,
        "checkpoint_materialization": isinstance(
            capabilities.get("checkpoint_materialization"), Mapping
        )
        and capabilities["checkpoint_materialization"].get("configured") is True,
    }
    if not all(checks.values()):
        raise PromotionSourceCheckpointCaptureError(
            "promotion_source_capability_profile_incomplete",
            {"checks": checks, "capabilities": capabilities},
        )
    return {"checks": checks, "capabilities": copy.deepcopy(capabilities)}


def _snapshot(
    value: object,
    *,
    tracked_ck3_pid: int,
    connection_generation: int,
    require_event: bool,
) -> tuple[dict[str, object], dict[str, object] | None]:
    snapshot = copy.deepcopy(dict(value)) if isinstance(value, Mapping) else {}
    diagnostics = snapshot.get("diagnostics")
    if not (
        snapshot.get("paused") is True
        and snapshot.get("map_ready") is True
        and isinstance(diagnostics, Mapping)
        and diagnostics.get("bridge_pid") == tracked_ck3_pid
        and diagnostics.get("connection_generation") == connection_generation
    ):
        raise PromotionSourceCheckpointCaptureError(
            "promotion_source_session_binding_drifted", {"snapshot": snapshot}
        )
    active = snapshot.get("active_event")
    if not isinstance(active, Mapping):
        if require_event:
            raise PromotionSourceCheckpointCaptureError(
                "promotion_source_event_absent", {"snapshot": snapshot}
            )
        return snapshot, None
    try:
        binding = _snapshot_binding(snapshot, expected_event=True)
    except (TypeError, ValueError) as error:
        raise PromotionSourceCheckpointCaptureError(
            "promotion_source_snapshot_invalid",
            {"message": str(error), "snapshot": snapshot},
        ) from error
    return snapshot, binding


def _same_frame(
    expected: Mapping[str, object], observed: Mapping[str, object]
) -> bool:
    return all(expected.get(key) == observed.get(key) for key in _BINDING_FIELDS)


def _saved_character_id(row: object) -> int | None:
    scope = row.get("scope") if isinstance(row, Mapping) else None
    identity = scope.get("typed_identity") if isinstance(scope, Mapping) else None
    value = identity.get("character_id") if isinstance(identity, Mapping) else None
    if not (
        isinstance(identity, Mapping)
        and identity.get("status") == "available"
        and identity.get("kind") == "character"
        and _positive(value)
    ):
        return None
    return int(value)


def _saved_scope_projection(query: Mapping[str, object]) -> dict[str, object]:
    context = query.get("current_event_window_context")
    rows = context.get("saved_scopes") if isinstance(context, Mapping) else None
    if not isinstance(rows, list):
        raise PromotionSourceCheckpointCaptureError(
            "promotion_source_saved_scopes_absent", {"event_query": query}
        )
    by_name: dict[str, object] = {}
    for row in rows:
        if not isinstance(row, Mapping) or not isinstance(row.get("name"), str):
            raise PromotionSourceCheckpointCaptureError(
                "promotion_source_saved_scope_malformed", {"row": row}
            )
        name = str(row["name"])
        if name in by_name:
            raise PromotionSourceCheckpointCaptureError(
                "promotion_source_saved_scope_duplicate", {"name": name}
            )
        by_name[name] = copy.deepcopy(dict(row))
    required = {*_CHARACTER_SCOPES, *_SCALAR_SCOPES}
    if not required.issubset(by_name):
        raise PromotionSourceCheckpointCaptureError(
            "promotion_source_saved_scopes_incomplete",
            {"missing": sorted(required - set(by_name))},
        )
    return {name: by_name[name] for name in (*_CHARACTER_SCOPES, *_SCALAR_SCOPES)}


def _native_save(
    value: object, *, binding: Mapping[str, object]
) -> tuple[Path, dict[str, object]]:
    result = copy.deepcopy(dict(value)) if isinstance(value, Mapping) else {}
    checkpoint = result.get("checkpoint")
    checkpoint = dict(checkpoint) if isinstance(checkpoint, Mapping) else {}
    materialization = result.get("materialization")
    raw_path = checkpoint.get("path")
    path = Path(str(raw_path)).resolve() if isinstance(raw_path, str) else Path()
    size = checkpoint.get("size")
    digest = str(checkpoint.get("sha256", "")).upper()
    valid = (
        result.get("accepted") is True
        and checkpoint.get("status") == "saved"
        and isinstance(raw_path, str)
        and Path(raw_path).is_absolute()
        and path.is_file()
        and _positive(size)
        and path.stat().st_size == size
        and _SHA256.fullmatch(digest) is not None
        and _sha256(path) == digest
        and checkpoint.get("date_raw") == binding.get("date_raw")
        and checkpoint.get("episode_character_id")
        == binding.get("player_character_id")
        and isinstance(checkpoint.get("strategy"), str)
        and bool(checkpoint.get("strategy"))
        and isinstance(materialization, Mapping)
        and materialization.get("available") is True
    )
    if not valid:
        raise PromotionSourceCheckpointCaptureError(
            "promotion_source_native_save_invalid",
            {"native_save_result": result, "source_binding": dict(binding)},
        )
    return path, result


def validate_promotion_source_capture_artifact_v2(
    value: object, *, expected_seed_lineage_id: str | None = None
) -> dict[str, object]:
    artifact = copy.deepcopy(dict(value)) if isinstance(value, Mapping) else {}
    entries = artifact.get("entries")
    entry = entries[0] if isinstance(entries, list) and len(entries) == 1 else None
    entry = dict(entry) if isinstance(entry, Mapping) else {}
    checkpoint = entry.get("checkpoint")
    checkpoint = dict(checkpoint) if isinstance(checkpoint, Mapping) else {}
    receipt = entry.get("source_receipt")
    receipt = dict(receipt) if isinstance(receipt, Mapping) else {}
    raw_path = checkpoint.get("path")
    path = Path(str(raw_path)).resolve() if isinstance(raw_path, str) else Path()
    digest = str(checkpoint.get("sha256", "")).upper()
    seed = artifact.get("seed_lineage_id")
    lineage = artifact.get("capture_lineage")
    session = artifact.get("managed_product_session")
    merge = artifact.get("canonical_merge_contract")
    saved_scopes = receipt.get("saved_scope_bindings")
    source_binding = receipt.get("source_snapshot_binding")
    post_query_binding = receipt.get("post_query_snapshot_binding")
    post_save_binding = receipt.get("post_save_snapshot_binding")
    native_save = receipt.get("native_save_receipt")
    native_checkpoint = (
        native_save.get("checkpoint") if isinstance(native_save, Mapping) else None
    )
    session_contract_valid = False
    if isinstance(seed, str) and isinstance(lineage, Mapping):
        try:
            _managed_product_contract(
                session,
                seed_lineage_id=seed,
                capture_lineage=lineage,
            )
            session_contract_valid = True
        except PromotionSourceCheckpointCaptureError:
            pass
    scalar_scope_names = (
        set(saved_scopes) == {*_CHARACTER_SCOPES, *_SCALAR_SCOPES}
        if isinstance(saved_scopes, Mapping)
        else False
    )
    valid = (
        artifact.get("schema_version") == SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION
        and artifact.get("kind") == CAPTURE_ARTIFACT_KIND
        and artifact.get("result") == "GREEN"
        and artifact.get("readiness") == CAPTURE_READINESS
        and artifact.get("evidence_class") == "real_ck3"
        and artifact.get("fixture_used") is False
        and artifact.get("console_used") is False
        and artifact.get("action_ack_used_as_state_evidence") is False
        and artifact.get("incomplete_for_canonical_4_entry_registry") is True
        and artifact.get("canonical_registry_ready") is False
        and artifact.get("promotion_compensation_provider_readiness")
        == "live-pending"
        and artifact.get(
            "promotion_compensation_provider_default_off_unchanged"
        )
        is True
        and artifact.get("promotion_compensation_action_cell_live_ready")
        is False
        and artifact.get("captured_handlers") == [HANDLER]
        and artifact.get("missing_handlers") == list(CHECKPOINT_REQUIRED_HANDLERS[1:])
        and isinstance(seed, str)
        and bool(seed)
        and (expected_seed_lineage_id is None or seed == expected_seed_lineage_id)
        and isinstance(lineage, Mapping)
        and lineage.get("seed_lineage_id") == seed
        and isinstance(session, Mapping)
        and session_contract_valid
        and receipt.get("capture_lineage") == lineage
        and receipt.get("managed_product_session") == session
        and entry.get("span_id") == SPAN_ID
        and entry.get("handler") == HANDLER
        and entry.get("source_event_definition_key")
        == SOURCE_EVENT_DEFINITION_KEY
        and entry.get("owner_character_id") == entry.get("player_character_id")
        and _positive(entry.get("owner_character_id"))
        and isinstance(entry.get("date_raw"), int)
        and not isinstance(entry.get("date_raw"), bool)
        and isinstance(raw_path, str)
        and Path(raw_path).is_absolute()
        and path.is_file()
        and _positive(checkpoint.get("bytes"))
        and path.stat().st_size == checkpoint.get("bytes")
        and _SHA256.fullmatch(digest) is not None
        and _sha256(path) == digest
        and checkpoint.get("save_lineage_id") == seed
        and receipt.get("result") == "GREEN"
        and receipt.get("kind") == CAPTURE_RECEIPT_KIND
        and receipt.get("evidence_class") == "real_ck3"
        and receipt.get("provider_observed") is True
        and receipt.get("ui_state_verified") is True
        and receipt.get("fixture_used") is False
        and receipt.get("console_used") is False
        and receipt.get("action_ack_used_as_state_evidence") is False
        and receipt.get("span_id") == SPAN_ID
        and receipt.get("event_definition_key") == SOURCE_EVENT_DEFINITION_KEY
        and receipt.get("option_number") == SOURCE_OPTION_NUMBER
        and receipt.get("option_shown") is True
        and receipt.get("option_enabled") is True
        and scalar_scope_names
        and _saved_character_id(saved_scopes.get(_CHARACTER_SCOPES[0]))
        == entry.get("owner_character_id")
        and _saved_character_id(saved_scopes.get(_CHARACTER_SCOPES[1]))
        == receipt.get("subject_character_id")
        and _positive(receipt.get("subject_character_id"))
        and receipt.get("owner_character_id") == entry.get("owner_character_id")
        and receipt.get("player_character_id") == entry.get("player_character_id")
        and receipt.get("date_raw") == entry.get("date_raw")
        and receipt.get("checkpoint_sha256") == digest
        and receipt.get("save_lineage_id") == seed
        and isinstance(source_binding, Mapping)
        and isinstance(post_query_binding, Mapping)
        and isinstance(post_save_binding, Mapping)
        and _same_frame(source_binding, post_query_binding)
        and _same_frame(source_binding, post_save_binding)
        and source_binding.get("player_character_id")
        == entry.get("player_character_id")
        and source_binding.get("date_raw") == entry.get("date_raw")
        and source_binding.get("connection_generation")
        == session.get("connection_generation")
        and isinstance(native_save, Mapping)
        and native_save.get("accepted") is True
        and isinstance(native_checkpoint, Mapping)
        and native_checkpoint.get("size") == checkpoint.get("bytes")
        and str(native_checkpoint.get("sha256", "")).upper() == digest
        and native_checkpoint.get("date_raw") == entry.get("date_raw")
        and native_checkpoint.get("episode_character_id")
        == entry.get("owner_character_id")
        and isinstance(merge, Mapping)
        and merge.get("target_registry_kind") == SOURCE_CHECKPOINT_REGISTRY_KIND
        and merge.get("target_schema_version")
        == SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION
        and merge.get("capture_manifest_kind")
        == SOURCE_CHECKPOINT_CAPTURE_MANIFEST_KIND
        and merge.get("required_handler_order")
        == list(CHECKPOINT_REQUIRED_HANDLERS)
        and merge.get("entry_index") == 0
        and merge.get("merge_operation") == "append_exact_entries_without_rewrite"
        and merge.get("assembler")
        == "zhongguo_phase2_source_checkpoint_registry.py"
    )
    if not valid:
        raise PromotionSourceCheckpointCaptureError(
            "promotion_source_capture_artifact_invalid",
            {
                "seed_lineage_id": seed,
                "expected_seed_lineage_id": expected_seed_lineage_id,
                "checkpoint_path": str(path),
            },
        )
    return artifact


def capture_promotion_source_checkpoint_v2(
    service: PromotionSourceCaptureService,
    *,
    checkpoint_root: Path,
    capture_artifact_path: Path,
    seed_lineage_id: str,
    capture_lineage: Mapping[str, object],
    managed_product_session: Mapping[str, object],
    timeout_seconds: float = 30.0,
    poll_interval_seconds: float = 0.05,
    clock: Callable[[], float] = time.monotonic,
    sleeper: Callable[[float], None] = time.sleep,
) -> dict[str, object]:
    """Capture the first real registry entry; never select the source option."""

    if timeout_seconds <= 0 or poll_interval_seconds < 0:
        raise ValueError("promotion source capture timing is invalid")
    target = capture_artifact_path.resolve()
    if target.exists():
        raise PromotionSourceCheckpointCaptureError(
            "promotion_source_capture_artifact_already_exists",
            {"capture_artifact_path": str(target)},
        )
    session = _managed_product_contract(
        managed_product_session,
        seed_lineage_id=seed_lineage_id,
        capture_lineage=capture_lineage,
    )
    tracked_pid = int(session["tracked_ck3_pid"])
    generation = int(session["connection_generation"])
    capability = _capability_contract(
        service,
        tracked_ck3_pid=tracked_pid,
        connection_generation=generation,
    )

    deadline = clock() + timeout_seconds
    source_snapshot: dict[str, object] | None = None
    source_binding: dict[str, object] | None = None
    source_query: dict[str, object] | None = None
    subject_character_id: int | None = None
    while clock() < deadline:
        snapshot, binding = _snapshot(
            service.snapshot(),
            tracked_ck3_pid=tracked_pid,
            connection_generation=generation,
            require_event=False,
        )
        if binding is None:
            if poll_interval_seconds:
                sleeper(poll_interval_seconds)
            continue
        try:
            query, subject = _event_context(
                service.query_current_event_window_context_v1(
                    int(binding["event_instance_id"]),
                    expected_revision=int(binding["revision"]),
                ),
                binding=binding,
                expected_definition_key=SOURCE_EVENT_DEFINITION_KEY,
                require_source_scopes=True,
            )
        except (TypeError, ValueError) as error:
            raise PromotionSourceCheckpointCaptureError(
                "promotion_source_event_contract_invalid",
                {"message": str(error), "source_binding": binding},
            ) from error
        source_snapshot = snapshot
        source_binding = binding
        source_query = query
        subject_character_id = subject
        break
    if source_binding is None or source_query is None or source_snapshot is None:
        raise PromotionSourceCheckpointCaptureError(
            "promotion_source_event_wait_timeout",
            {"timeout_seconds": timeout_seconds},
        )
    assert subject_character_id is not None
    saved_scopes = _saved_scope_projection(source_query)

    _, after_query = _snapshot(
        service.snapshot(),
        tracked_ck3_pid=tracked_pid,
        connection_generation=generation,
        require_event=True,
    )
    assert after_query is not None
    if not _same_frame(source_binding, after_query):
        raise PromotionSourceCheckpointCaptureError(
            "promotion_source_query_crossed_frame",
            {"source_binding": source_binding, "after_query": after_query},
        )
    native_path, native_save = _native_save(
        service.save_checkpoint(expected_revision=int(source_binding["revision"])),
        binding=source_binding,
    )
    _, after_save = _snapshot(
        service.snapshot(),
        tracked_ck3_pid=tracked_pid,
        connection_generation=generation,
        require_event=True,
    )
    assert after_save is not None
    if not _same_frame(source_binding, after_save):
        raise PromotionSourceCheckpointCaptureError(
            "promotion_source_save_crossed_frame",
            {"source_binding": source_binding, "after_save": after_save},
        )

    source_bytes = native_path.stat().st_size
    source_sha256 = _sha256(native_path)
    archive_root = checkpoint_root.resolve()
    archive_root.mkdir(parents=True, exist_ok=True)
    archive = archive_root / (
        "01-phase2-promotion-compensation-zg361pp-147-"
        f"{source_sha256[:16].lower()}.ck3"
    )
    if archive.exists():
        if not (
            archive.is_file()
            and archive.stat().st_size == source_bytes
            and _sha256(archive) == source_sha256
        ):
            raise PromotionSourceCheckpointCaptureError(
                "promotion_source_checkpoint_archive_collision",
                {"archive_path": str(archive)},
            )
    else:
        shutil.copy2(native_path, archive)
    if archive.stat().st_size != source_bytes or _sha256(archive) != source_sha256:
        raise PromotionSourceCheckpointCaptureError(
            "promotion_source_checkpoint_archive_mismatch",
            {"archive_path": str(archive)},
        )

    owner = int(source_binding["player_character_id"])
    source_receipt = {
        "schema_version": 2,
        "kind": CAPTURE_RECEIPT_KIND,
        "result": "GREEN",
        "readiness": CAPTURE_READINESS,
        "evidence_class": "real_ck3",
        "state_origin": "product-event",
        "provider_observed": True,
        "ui_state_verified": True,
        "fixture_used": False,
        "console_used": False,
        "generic_character_rebind_used": False,
        "event_option_action_executed": False,
        "action_ack_used_as_state_evidence": False,
        "save_ack_is_event_state_evidence": False,
        "span_id": SPAN_ID,
        "handler": HANDLER,
        "event_definition_key": SOURCE_EVENT_DEFINITION_KEY,
        "option_number": SOURCE_OPTION_NUMBER,
        "option_shown": True,
        "option_enabled": True,
        "owner_character_id": owner,
        "player_character_id": owner,
        "subject_character_id": subject_character_id,
        "date_raw": int(source_binding["date_raw"]),
        "checkpoint_sha256": source_sha256,
        "save_lineage_id": seed_lineage_id,
        "seed_lineage_id": seed_lineage_id,
        "capture_lineage": copy.deepcopy(dict(capture_lineage)),
        "managed_product_session": session,
        "source_snapshot_binding": copy.deepcopy(source_binding),
        "post_query_snapshot_binding": copy.deepcopy(after_query),
        "post_save_snapshot_binding": copy.deepcopy(after_save),
        "saved_scope_bindings": saved_scopes,
        "event_context_query": source_query,
        "native_save_receipt": native_save,
    }
    entry = {
        "span_id": SPAN_ID,
        "handler": HANDLER,
        "source_event_definition_key": SOURCE_EVENT_DEFINITION_KEY,
        "owner_character_id": owner,
        "player_character_id": owner,
        "date_raw": int(source_binding["date_raw"]),
        "checkpoint": {
            "path": str(archive),
            "bytes": source_bytes,
            "sha256": source_sha256,
            "save_lineage_id": seed_lineage_id,
        },
        "source_receipt": source_receipt,
    }
    artifact = {
        "schema_version": SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION,
        "kind": CAPTURE_ARTIFACT_KIND,
        "result": "GREEN",
        "readiness": CAPTURE_READINESS,
        "evidence_class": "real_ck3",
        "fixture_used": False,
        "console_used": False,
        "action_ack_used_as_state_evidence": False,
        "seed_lineage_id": seed_lineage_id,
        "capture_lineage": copy.deepcopy(dict(capture_lineage)),
        "managed_product_session": session,
        "capability_preflight": capability,
        "entries": [entry],
        "captured_handlers": [HANDLER],
        "missing_handlers": list(CHECKPOINT_REQUIRED_HANDLERS[1:]),
        "incomplete_for_canonical_4_entry_registry": True,
        "canonical_registry_ready": False,
        "promotion_compensation_provider_readiness": "live-pending",
        "promotion_compensation_provider_default_off_unchanged": True,
        "promotion_compensation_action_cell_live_ready": False,
        "canonical_merge_contract": {
            "target_registry_kind": SOURCE_CHECKPOINT_REGISTRY_KIND,
            "target_schema_version": SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION,
            "capture_manifest_kind": SOURCE_CHECKPOINT_CAPTURE_MANIFEST_KIND,
            "required_handler_order": list(CHECKPOINT_REQUIRED_HANDLERS),
            "entry_index": 0,
            "merge_operation": "append_exact_entries_without_rewrite",
            "assembler": "zhongguo_phase2_source_checkpoint_registry.py",
        },
    }
    validate_promotion_source_capture_artifact_v2(
        artifact, expected_seed_lineage_id=seed_lineage_id
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with target.open("x", encoding="utf-8", newline="\n") as output:
            json.dump(artifact, output, ensure_ascii=False, indent=2)
            output.write("\n")
    except FileExistsError as error:
        raise PromotionSourceCheckpointCaptureError(
            "promotion_source_capture_artifact_already_exists",
            {"capture_artifact_path": str(target)},
        ) from error
    return artifact


def build_no_launch_preflight() -> dict[str, object]:
    """Describe the live callable without instantiating a service or CK3."""

    plan = phase2_event_sequence_plan(HANDLER)
    checks = {
        "schema_v2_fragment": SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION == 2,
        "canonical_first_handler": CHECKPOINT_REQUIRED_HANDLERS[0] == HANDLER,
        "exact_source_event": plan.source_event == SOURCE_EVENT_DEFINITION_KEY,
        "exact_option": SOURCE_OPTION_NUMBER == 1,
        "capture_callable": callable(capture_promotion_source_checkpoint_v2),
        "validator_callable": callable(
            validate_promotion_source_capture_artifact_v2
        ),
    }
    return {
        "schema_version": 1,
        "kind": "zg361_phase2_promotion_source_capture_no_launch_preflight",
        "result": "GREEN" if all(checks.values()) else "RED",
        "readiness": "static-ready-live-pending",
        "explicit_live_entrypoint": "capture_promotion_source_checkpoint_v2",
        "source_event_definition_key": SOURCE_EVENT_DEFINITION_KEY,
        "source_option_number": SOURCE_OPTION_NUMBER,
        "product_session_required": True,
        "managed_session_required": True,
        "provider_default_off_unchanged": True,
        "ck3_started": False,
        "service_instantiated": False,
        "checkpoint_written": False,
        "capture_artifact_written": False,
        "action_ack_used_as_state_evidence": False,
        "incomplete_for_canonical_4_entry_registry": True,
        "required_handler_order": list(CHECKPOINT_REQUIRED_HANDLERS),
        "checks": checks,
    }


__all__ = [
    "CAPTURE_ARTIFACT_KIND",
    "CAPTURE_READINESS",
    "CAPTURE_RECEIPT_KIND",
    "EXACT_EXE_SHA256",
    "EXACT_GAME_VERSION",
    "HANDLER",
    "PromotionSourceCheckpointCaptureError",
    "PromotionSourceCaptureService",
    "build_no_launch_preflight",
    "capture_promotion_source_checkpoint_v2",
    "validate_promotion_source_capture_artifact_v2",
]
