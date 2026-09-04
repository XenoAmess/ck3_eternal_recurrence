#!/usr/bin/env python3
"""Real-product scoreboard surface checkpoints and canonical restore provider.

The registry is data-only and must point at two already-materialized CK3 saves.
Preparation always uses the managed canonical restore lifecycle, then performs a
fresh scoreboard query.  Neither a save/restore ACK nor registry metadata is a
substitute for the post-restore modal, page, entry, and ACL observation.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
from pathlib import Path
import re
from typing import Final, Mapping, Protocol


SCOREBOARD_SURFACE_REGISTRY_KIND: Final = (
    "zg361_scoreboard_product_surface_checkpoint_registry"
)
SCOREBOARD_SURFACE_REGISTRY_SCHEMA_VERSION: Final = 1
SCOREBOARD_REQUIRED_SURFACES: Final = (
    "managed-capable",
    "received-only",
)
_SCOREBOARD_CASE_KIND: Final = "zhongguo.scoreboard.named-state-acl"
_SCOREBOARD_CONSUMER_ID: Final = (
    "xar-autoplayer-zhongguo-scoreboard-state-v1"
)
_SHA256_RE: Final = re.compile(r"[0-9A-F]{64}\Z")
_PROVIDER_SESSION_RE: Final = re.compile(r"[0-9A-F]{32}\Z")
_FINGERPRINT_RE: Final = re.compile(r"[0-9A-F]{64}\Z")


class ScoreboardSurfaceCheckpointError(RuntimeError):
    """Fail-closed checkpoint/provider error with durable typed evidence."""

    result: Final = "RED"

    def __init__(self, reason_code: str, evidence: Mapping[str, object]) -> None:
        self.reason_code = reason_code
        self.evidence = {
            **deepcopy(dict(evidence)),
            "result": "RED",
            "reason_code": reason_code,
        }
        super().__init__(f"scoreboard surface checkpoint RED [{reason_code}]")


@dataclass(frozen=True, slots=True)
class ScoreboardSurfaceCheckpoint:
    surface_id: str
    player_character_id: int
    owner_character_id: int
    date_raw: int
    path: Path
    bytes: int
    sha256: str
    save_lineage_id: str
    source_snapshot_binding: Mapping[str, object]
    post_save_snapshot_binding: Mapping[str, object]
    source_query: Mapping[str, object]
    native_save_receipt: Mapping[str, object]


class ScoreboardSurfaceService(Protocol):
    def snapshot(self) -> dict[str, object]: ...

    def query_zhongguo_scoreboard_state_v1(
        self, request_nonce: str, *, expected_revision: int
    ) -> dict[str, object]: ...

    def restore_phase2_span_source_checkpoint_v1(
        self, **arguments: object
    ) -> dict[str, object]: ...


def _positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _nonnegative_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def scoreboard_checkpoint_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _typed_available(value: object) -> object | None:
    row = value if isinstance(value, Mapping) else {}
    if (
        set(row) == {"status", "value", "unavailable_reason"}
        and row.get("status") == "available"
        and row.get("unavailable_reason") is None
    ):
        return row.get("value")
    return None


def _typed_unavailable(value: object, reason: str) -> bool:
    row = value if isinstance(value, Mapping) else {}
    return bool(
        set(row) == {"status", "value", "unavailable_reason"}
        and row.get("status") == "unavailable"
        and row.get("value") is None
        and row.get("unavailable_reason") == reason
    )


def _widget(value: Mapping[str, object], stable_identity: str) -> Mapping[str, object]:
    widgets = value.get("widgets")
    if not isinstance(widgets, list):
        return {}
    matches = [
        row
        for row in widgets
        if isinstance(row, Mapping)
        and row.get("stable_identity") == stable_identity
    ]
    return matches[0] if len(matches) == 1 else {}


def _widget_state(
    value: Mapping[str, object], stable_identity: str, *, visible: bool
) -> bool:
    row = _widget(value, stable_identity)
    return bool(
        _typed_available(row.get("exists")) is True
        and _typed_available(row.get("effective_visible")) is visible
        and _typed_available(row.get("enabled")) is True
    )


def _surface_query_contract(
    value: object,
    *,
    surface_id: str,
    expected_player_character_id: int | None = None,
    expected_date_raw: int | None = None,
) -> dict[str, object]:
    query = deepcopy(dict(value)) if isinstance(value, Mapping) else {}
    binding = query.get("binding")
    binding = dict(binding) if isinstance(binding, Mapping) else {}
    source = query.get("source")
    source = dict(source) if isinstance(source, Mapping) else {}
    readiness = query.get("readiness")
    readiness = dict(readiness) if isinstance(readiness, Mapping) else {}
    provenance = query.get("provenance")
    provenance = dict(provenance) if isinstance(provenance, Mapping) else {}
    player = query.get("player_character_id")
    date_raw = query.get("date_raw")
    request_nonce = query.get("request_nonce")
    query_common_valid = (
        surface_id in SCOREBOARD_REQUIRED_SURFACES
        and query.get("status") == "available"
        and query.get("case_kind") == _SCOREBOARD_CASE_KIND
        and query.get("paused") is True
        and _positive_int(player)
        and isinstance(date_raw, int)
        and not isinstance(date_raw, bool)
        and isinstance(request_nonce, str)
        and bool(request_nonce)
        and _FINGERPRINT_RE.fullmatch(
            str(query.get("tree_fingerprint_v1", ""))
        )
        is not None
        and _FINGERPRINT_RE.fullmatch(
            str(query.get("semantic_fingerprint_v1", ""))
        )
        is not None
        and _PROVIDER_SESSION_RE.fullmatch(
            str(query.get("provider_session_id", ""))
        )
        is not None
        and _positive_int(query.get("observation_sequence"))
        and _positive_int(query.get("observed_state_revision"))
        and readiness.get("state_acl_query_ready") is True
        and provenance.get("consumer_id") == _SCOREBOARD_CONSUMER_ID
        and binding.get("request_nonce") == request_nonce
        and binding.get("paused") is True
        and binding.get("player_character_id") == player
        and binding.get("date_raw") == date_raw
        and _nonnegative_int(binding.get("revision"))
        and _positive_int(binding.get("native_revision"))
        and binding.get("native_revision") == query.get("snapshot_revision")
        and _positive_int(binding.get("connection_generation"))
        and source.get("paused") is True
        and source.get("player_character_id") == player
        and source.get("date_raw") == date_raw
        and source.get("connection_generation")
        == binding.get("connection_generation")
        and source.get("revision") == binding.get("revision")
        and source.get("native_revision") == binding.get("native_revision")
    )
    if expected_player_character_id is not None:
        query_common_valid = bool(
            query_common_valid and player == expected_player_character_id
        )
    if expected_date_raw is not None:
        query_common_valid = bool(
            query_common_valid and date_raw == expected_date_raw
        )

    entry_identity = (
        "zg361_scoreboard_entry_managed"
        if surface_id == "managed-capable"
        else "zg361_scoreboard_entry_received"
    )
    other_entry_identity = (
        "zg361_scoreboard_entry_received"
        if surface_id == "managed-capable"
        else "zg361_scoreboard_entry_managed"
    )
    closed_surface_valid = bool(
        _widget_state(query, "zg361_open_scoreboard", visible=True)
        and _widget_state(query, "zg361_scoreboard_window", visible=True)
        and _widget_state(query, entry_identity, visible=True)
        and _widget_state(query, other_entry_identity, visible=False)
        and _widget_state(query, "zg361_scoreboard_entry_system", visible=False)
        and _widget_state(query, "zg361_scoreboard_modal", visible=False)
        and _widget_state(query, "zg361_scoreboard_panel", visible=False)
        and all(
            _widget_state(query, identity, visible=False)
            for identity in (
                "zg361_scoreboard_page_managed",
                "zg361_scoreboard_page_received",
                "zg361_scoreboard_page_system",
            )
        )
    )

    acl = query.get("acl")
    acl = dict(acl) if isinstance(acl, Mapping) else {}
    managed = acl.get("managed")
    managed = dict(managed) if isinstance(managed, Mapping) else {}
    received = acl.get("received_self")
    received = dict(received) if isinstance(received, Mapping) else {}
    owner_character_id: object = None
    if surface_id == "managed-capable":
        owner_character_id = _typed_available(
            managed.get("owner_character_id")
        )
        first_subject = _typed_available(
            managed.get("first_subject_character_id")
        )
        acl_valid = bool(
            managed.get("surface_available") is True
            and managed.get("current_player_can_assess_others") is True
            and owner_character_id == player
            and _positive_int(first_subject)
        )
    else:
        owner_character_id = _typed_available(
            received.get("owner_character_id")
        )
        received_subject = _typed_available(
            received.get("subject_character_id")
        )
        first_row = _typed_available(received.get("first_row_character_id"))
        tuple_values = [
            _typed_available(received.get(key))
            for key in ("cycle_serial", "result_case_serial", "b1_case_serial")
        ]
        acl_valid = bool(
            managed.get("surface_available") is False
            and managed.get("current_player_can_assess_others") is False
            and _typed_unavailable(
                managed.get("owner_character_id"), "surface_not_available"
            )
            and _typed_unavailable(
                managed.get("first_subject_character_id"),
                "surface_not_available",
            )
            and received.get("surface_available") is True
            and received.get("current_player_is_subject") is True
            and received_subject == player
            and first_row == player
            and _positive_int(owner_character_id)
            and all(_positive_int(item) for item in tuple_values)
        )

    if not (query_common_valid and closed_surface_valid and acl_valid):
        raise ScoreboardSurfaceCheckpointError(
            "scoreboard_surface_query_invalid",
            {
                "surface_id": surface_id,
                "query_common_valid": query_common_valid,
                "closed_modal_page_entry_valid": closed_surface_valid,
                "acl_valid": acl_valid,
                "expected_player_character_id": expected_player_character_id,
                "expected_date_raw": expected_date_raw,
                "query": query,
            },
        )
    if not _positive_int(owner_character_id):
        raise ScoreboardSurfaceCheckpointError(
            "scoreboard_surface_owner_invalid",
            {"surface_id": surface_id, "owner_character_id": owner_character_id},
        )
    return {
        "surface_id": surface_id,
        "player_character_id": int(player),
        "owner_character_id": int(owner_character_id),
        "date_raw": int(date_raw),
        "provider_session_id": str(query["provider_session_id"]),
        "binding": binding,
    }


def scoreboard_surface_snapshot_binding(value: object) -> dict[str, object]:
    snapshot = dict(value) if isinstance(value, Mapping) else {}
    played = snapshot.get("played_character")
    played = dict(played) if isinstance(played, Mapping) else {}
    diagnostics = snapshot.get("diagnostics")
    diagnostics = dict(diagnostics) if isinstance(diagnostics, Mapping) else {}
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
        "active_event_present": isinstance(snapshot.get("active_event"), Mapping),
        "event_free": snapshot.get("active_event") is None,
    }
    if not (
        binding["paused"] is True
        and binding["map_ready"] is True
        and binding["event_free"] is True
        and isinstance(binding["snapshot_id"], str)
        and bool(binding["snapshot_id"])
        and _nonnegative_int(binding["revision"])
        and _positive_int(binding["native_revision"])
        and isinstance(binding["date_raw"], int)
        and not isinstance(binding["date_raw"], bool)
        and _positive_int(binding["player_character_id"])
        and _positive_int(binding["bridge_pid"])
        and _positive_int(binding["connection_generation"])
    ):
        raise ScoreboardSurfaceCheckpointError(
            "scoreboard_surface_snapshot_not_event_free_paused",
            {"snapshot_binding": binding},
        )
    return binding


def validate_scoreboard_surface_query(
    value: object,
    *,
    surface_id: str,
    expected_player_character_id: int | None = None,
    expected_date_raw: int | None = None,
) -> dict[str, object]:
    """Validate one full provider state; never accept an action ACK."""

    return _surface_query_contract(
        value,
        surface_id=surface_id,
        expected_player_character_id=expected_player_character_id,
        expected_date_raw=expected_date_raw,
    )


def _entry(
    value: object,
    *,
    seed_lineage_id: str,
) -> ScoreboardSurfaceCheckpoint:
    row = deepcopy(dict(value)) if isinstance(value, Mapping) else {}
    surface_id = row.get("surface_id")
    player = row.get("player_character_id")
    owner = row.get("owner_character_id")
    date_raw = row.get("date_raw")
    checkpoint = row.get("checkpoint")
    checkpoint = dict(checkpoint) if isinstance(checkpoint, Mapping) else {}
    raw_path = checkpoint.get("path")
    path = Path(str(raw_path)).resolve() if isinstance(raw_path, str) else Path()
    expected_bytes = checkpoint.get("bytes")
    expected_sha = str(checkpoint.get("sha256", "")).upper()
    source_binding = row.get("source_snapshot_binding")
    source_binding = (
        dict(source_binding) if isinstance(source_binding, Mapping) else {}
    )
    source_query = row.get("source_query")
    post_save_binding = row.get("post_save_snapshot_binding")
    post_save_binding = (
        dict(post_save_binding)
        if isinstance(post_save_binding, Mapping)
        else {}
    )
    capture_checks = row.get("capture_checks")
    capture_checks = (
        dict(capture_checks) if isinstance(capture_checks, Mapping) else {}
    )
    native_save_receipt = row.get("native_save_receipt")
    native_save_receipt = (
        dict(native_save_receipt)
        if isinstance(native_save_receipt, Mapping)
        else {}
    )
    saved_checkpoint = native_save_receipt.get("checkpoint")
    saved_checkpoint = (
        dict(saved_checkpoint) if isinstance(saved_checkpoint, Mapping) else {}
    )
    common_valid = bool(
        surface_id in SCOREBOARD_REQUIRED_SURFACES
        and _positive_int(player)
        and _positive_int(owner)
        and isinstance(date_raw, int)
        and not isinstance(date_raw, bool)
        and isinstance(raw_path, str)
        and path.is_absolute()
        and path.is_file()
        and _positive_int(expected_bytes)
        and path.stat().st_size == expected_bytes
        and _SHA256_RE.fullmatch(expected_sha) is not None
        and scoreboard_checkpoint_sha256(path) == expected_sha
        and checkpoint.get("save_lineage_id") == seed_lineage_id
        and source_binding.get("event_free") is True
        and source_binding.get("active_event_present") is False
        and source_binding.get("paused") is True
        and source_binding.get("map_ready") is True
        and source_binding.get("player_character_id") == player
        and source_binding.get("date_raw") == date_raw
        and all(
            post_save_binding.get(key) == source_binding.get(key)
            for key in (
                "bridge_pid",
                "connection_generation",
                "player_character_id",
                "date_raw",
            )
        )
        and post_save_binding.get("event_free") is True
        and post_save_binding.get("active_event_present") is False
        and capture_checks
        == {
            "event_free_paused_product_state": True,
            "modal_closed": True,
            "pages_closed": True,
            "surface_entry_visible": True,
            "surface_acl_observed": True,
            "save_binding_preserved": True,
            "action_ack_used_as_state_evidence": False,
        }
        and native_save_receipt.get("accepted") is True
        and saved_checkpoint.get("status") == "saved"
        and saved_checkpoint.get("size") == expected_bytes
        and str(saved_checkpoint.get("sha256", "")).upper() == expected_sha
        and saved_checkpoint.get("date_raw") == date_raw
    )
    try:
        query_contract = validate_scoreboard_surface_query(
            source_query,
            surface_id=str(surface_id),
            expected_player_character_id=(int(player) if _positive_int(player) else None),
            expected_date_raw=(
                int(date_raw)
                if isinstance(date_raw, int) and not isinstance(date_raw, bool)
                else None
            ),
        )
    except ScoreboardSurfaceCheckpointError as error:
        raise ScoreboardSurfaceCheckpointError(
            "scoreboard_surface_checkpoint_entry_invalid",
            {
                "surface_id": surface_id,
                "checkpoint_path": str(path),
                "query_error": error.evidence,
            },
        ) from error
    if not common_valid or query_contract.get("owner_character_id") != owner:
        raise ScoreboardSurfaceCheckpointError(
            "scoreboard_surface_checkpoint_entry_invalid",
            {
                "surface_id": surface_id,
                "checkpoint_path": str(path),
                "checkpoint_bytes_match": (
                    path.is_file() and path.stat().st_size == expected_bytes
                ),
                "checkpoint_sha256_match": (
                    path.is_file()
                    and _SHA256_RE.fullmatch(expected_sha) is not None
                    and scoreboard_checkpoint_sha256(path) == expected_sha
                ),
                "source_snapshot_binding": source_binding,
                "native_save_receipt": native_save_receipt,
            },
        )
    return ScoreboardSurfaceCheckpoint(
        surface_id=str(surface_id),
        player_character_id=int(player),
        owner_character_id=int(owner),
        date_raw=int(date_raw),
        path=path,
        bytes=int(expected_bytes),
        sha256=expected_sha,
        save_lineage_id=seed_lineage_id,
        source_snapshot_binding=source_binding,
        post_save_snapshot_binding=post_save_binding,
        source_query=deepcopy(dict(source_query)),
        native_save_receipt=native_save_receipt,
    )


def _validated_registry(
    registry_value: Mapping[str, object] | None,
    *,
    expected_seed_lineage_id: str | None,
) -> tuple[dict[str, object], dict[str, ScoreboardSurfaceCheckpoint]]:
    if registry_value is None:
        raise ScoreboardSurfaceCheckpointError(
            "scoreboard_surface_checkpoint_registry_missing",
            {"required_surfaces": list(SCOREBOARD_REQUIRED_SURFACES)},
        )
    registry = deepcopy(dict(registry_value))
    seed_lineage_id = registry.get("seed_lineage_id")
    capture_lineage = registry.get("capture_lineage")
    rows = registry.get("entries")
    header_valid = bool(
        registry.get("schema_version")
        == SCOREBOARD_SURFACE_REGISTRY_SCHEMA_VERSION
        and registry.get("registry_kind")
        == SCOREBOARD_SURFACE_REGISTRY_KIND
        and registry.get("result") == "GREEN"
        and registry.get("evidence_class") == "real_ck3"
        and registry.get("state_origin") == "product-checkpoint"
        and registry.get("fixture_used") is False
        and registry.get("ocr_used") is False
        and registry.get("coordinates_used") is False
        and registry.get("console_used") is False
        and registry.get("generic_character_rebind_used") is False
        and isinstance(seed_lineage_id, str)
        and bool(seed_lineage_id)
        and seed_lineage_id == expected_seed_lineage_id
        and isinstance(capture_lineage, Mapping)
        and capture_lineage.get("seed_lineage_id") == seed_lineage_id
        and isinstance(rows, list)
    )
    if not header_valid:
        raise ScoreboardSurfaceCheckpointError(
            "scoreboard_surface_checkpoint_registry_header_invalid",
            {
                "registry": registry,
                "expected_seed_lineage_id": expected_seed_lineage_id,
            },
        )
    entries = [
        _entry(row, seed_lineage_id=str(seed_lineage_id)) for row in rows
    ]
    surfaces = tuple(entry.surface_id for entry in entries)
    if surfaces != SCOREBOARD_REQUIRED_SURFACES or len(set(surfaces)) != len(
        surfaces
    ):
        raise ScoreboardSurfaceCheckpointError(
            "scoreboard_surface_checkpoint_registry_coverage_invalid",
            {
                "required_surfaces": list(SCOREBOARD_REQUIRED_SURFACES),
                "observed_surfaces": list(surfaces),
            },
        )
    entry_map = {entry.surface_id: entry for entry in entries}
    evidence = {
        "schema_version": 1,
        "result": "GREEN",
        "registry_kind": SCOREBOARD_SURFACE_REGISTRY_KIND,
        "seed_lineage_id": seed_lineage_id,
        "required_surfaces": list(SCOREBOARD_REQUIRED_SURFACES),
        "entry_count": len(entries),
        "fixture_used": False,
        "ocr_used": False,
        "coordinates_used": False,
        "console_used": False,
        "generic_character_rebind_used": False,
    }
    return evidence, entry_map


def validate_scoreboard_surface_checkpoint_registry(
    registry: Mapping[str, object] | None,
    *,
    expected_seed_lineage_id: str | None,
) -> dict[str, object]:
    """Verify registry bytes and source observations without contacting CK3."""

    evidence, _entries = _validated_registry(
        registry, expected_seed_lineage_id=expected_seed_lineage_id
    )
    return evidence


class ScoreboardSurfaceCheckpointProvider:
    """Restore one registered surface and independently attest its state."""

    def __init__(
        self,
        registry: Mapping[str, object] | None,
        *,
        service: ScoreboardSurfaceService,
        expected_seed_lineage_id: str | None,
    ) -> None:
        self.registry = (
            deepcopy(dict(registry)) if isinstance(registry, Mapping) else None
        )
        self.service = service
        self.expected_seed_lineage_id = expected_seed_lineage_id
        self._entries: dict[str, ScoreboardSurfaceCheckpoint] | None = None
        self._prepare_sequence = 0

    def preflight(self) -> dict[str, object]:
        evidence, entries = _validated_registry(
            self.registry,
            expected_seed_lineage_id=self.expected_seed_lineage_id,
        )
        restore = getattr(
            self.service, "restore_phase2_span_source_checkpoint_v1", None
        )
        snapshot = getattr(self.service, "snapshot", None)
        query = getattr(
            self.service, "query_zhongguo_scoreboard_state_v1", None
        )
        if not (callable(restore) and callable(snapshot) and callable(query)):
            raise ScoreboardSurfaceCheckpointError(
                "scoreboard_surface_restore_or_query_provider_missing",
                {
                    "restore_available": callable(restore),
                    "snapshot_available": callable(snapshot),
                    "query_available": callable(query),
                },
            )
        self._entries = entries
        return {
            **evidence,
            "restore_interface_available": True,
            "query_interface_available": True,
        }

    def _prepare(self, surface_id: str) -> dict[str, object]:
        # The runner preflights both potentially large CK3 saves once before
        # binding.  The native restore rechecks the selected file's exact
        # bytes, so repeating both registry hashes before each surface would
        # add I/O without adding a real observation boundary.
        if self._entries is None:
            self.preflight()
        if surface_id not in SCOREBOARD_REQUIRED_SURFACES:
            raise ScoreboardSurfaceCheckpointError(
                "scoreboard_surface_unknown",
                {
                    "surface_id": surface_id,
                    "required_surfaces": list(SCOREBOARD_REQUIRED_SURFACES),
                },
            )
        if self._entries is None:
            raise ScoreboardSurfaceCheckpointError(
                "scoreboard_surface_registry_not_loaded", {"surface_id": surface_id}
            )
        entry = self._entries[surface_id]
        sentinel = f"scoreboard-surface:{surface_id}"
        restore = self.service.restore_phase2_span_source_checkpoint_v1(
            checkpoint_path=str(entry.path),
            expected_checkpoint_bytes=entry.bytes,
            expected_checkpoint_sha256=entry.sha256,
            expected_save_lineage_id=entry.save_lineage_id,
            expected_event_definition_key=sentinel,
            expected_owner_character_id=entry.owner_character_id,
            expected_player_character_id=entry.player_character_id,
            expected_date_raw=entry.date_raw,
            allow_generic_character_rebind=False,
            allow_fixture=False,
            allow_console=False,
        )
        lifecycle = restore.get("lifecycle") if isinstance(restore, Mapping) else None
        restore_valid = bool(
            isinstance(restore, Mapping)
            and restore.get("result") == "GREEN"
            and restore.get("provider_observed") is True
            and restore.get("restore_materialized") is True
            and restore.get("checkpoint_sha256") == entry.sha256
            and restore.get("checkpoint_bytes") == entry.bytes
            and restore.get("save_lineage_id") == entry.save_lineage_id
            and restore.get("event_definition_key") == sentinel
            and restore.get("owner_character_id") == entry.owner_character_id
            and restore.get("player_character_id") == entry.player_character_id
            and restore.get("date_raw") == entry.date_raw
            and restore.get("fixture_used") is False
            and restore.get("console_used") is False
            and restore.get("generic_character_rebind_used") is False
            and isinstance(lifecycle, Mapping)
            and lifecycle.get("lifecycle_intent") == "restore"
            and _positive_int(lifecycle.get("previous_pid"))
            and _positive_int(lifecycle.get("pid"))
            and lifecycle.get("pid") != lifecycle.get("previous_pid")
            and _positive_int(lifecycle.get("previous_connection_generation"))
            and lifecycle.get("connection_generation")
            == int(lifecycle.get("previous_connection_generation")) + 1
        )
        if not restore_valid:
            raise ScoreboardSurfaceCheckpointError(
                "scoreboard_surface_restore_not_green",
                {"surface_id": surface_id, "restore_receipt": restore},
            )

        restored_snapshot = self.service.snapshot()
        snapshot_binding = scoreboard_surface_snapshot_binding(restored_snapshot)
        if not (
            snapshot_binding["player_character_id"] == entry.player_character_id
            and snapshot_binding["date_raw"] == entry.date_raw
            and snapshot_binding["bridge_pid"] == lifecycle.get("pid")
            and snapshot_binding["connection_generation"]
            == lifecycle.get("connection_generation")
        ):
            raise ScoreboardSurfaceCheckpointError(
                "scoreboard_surface_post_restore_binding_mismatch",
                {
                    "surface_id": surface_id,
                    "expected_player_character_id": entry.player_character_id,
                    "expected_date_raw": entry.date_raw,
                    "restore_lifecycle": dict(lifecycle),
                    "snapshot_binding": snapshot_binding,
                },
            )

        self._prepare_sequence += 1
        nonce = f"zg361.scoreboard.restore.{self._prepare_sequence}.{surface_id}"
        restored_query = self.service.query_zhongguo_scoreboard_state_v1(
            nonce,
            expected_revision=int(snapshot_binding["revision"]),
        )
        restored_contract = validate_scoreboard_surface_query(
            restored_query,
            surface_id=surface_id,
            expected_player_character_id=entry.player_character_id,
            expected_date_raw=entry.date_raw,
        )
        restored_binding = restored_contract["binding"]
        source_contract = validate_scoreboard_surface_query(
            entry.source_query,
            surface_id=surface_id,
            expected_player_character_id=entry.player_character_id,
            expected_date_raw=entry.date_raw,
        )
        if not (
            isinstance(restored_binding, Mapping)
            and restored_binding.get("revision") == snapshot_binding["revision"]
            and restored_binding.get("native_revision")
            == snapshot_binding["native_revision"]
            and restored_binding.get("connection_generation")
            == snapshot_binding["connection_generation"]
            and restored_contract.get("provider_session_id")
            != source_contract.get("provider_session_id")
        ):
            raise ScoreboardSurfaceCheckpointError(
                "scoreboard_surface_post_restore_query_binding_mismatch",
                {
                    "surface_id": surface_id,
                    "snapshot_binding": snapshot_binding,
                    "restored_query_contract": restored_contract,
                    "source_query_provider_session_id": source_contract.get(
                        "provider_session_id"
                    ),
                },
            )
        return {
            "schema_version": 1,
            "surface_id": surface_id,
            "status": "ready",
            "evidence_class": "real_ck3",
            "state_origin": "product-checkpoint",
            "transition_kind": "canonical-checkpoint-clean-restart",
            "restore_materialized": True,
            "provider_observed": True,
            "checkpoint_sha256": entry.sha256,
            "checkpoint_bytes": entry.bytes,
            "save_lineage_id": entry.save_lineage_id,
            "lifecycle": dict(lifecycle),
            "source_checkpoint_query": deepcopy(dict(entry.source_query)),
            "post_restore_snapshot_binding": snapshot_binding,
            "post_restore_query": deepcopy(dict(restored_query)),
            "modal_page_acl_observed": True,
            "action_ack_used_as_postcondition": False,
            "fixture_used": False,
            "ocr_used": False,
            "coordinates_used": False,
            "console_used": False,
            "generic_character_rebind_used": False,
        }

    def prepare_zhongguo_scoreboard_surface_v1(
        self, surface_id: str
    ) -> dict[str, object]:
        """Return a typed unavailable receipt instead of leaking partial state."""

        try:
            return self._prepare(surface_id)
        except ScoreboardSurfaceCheckpointError as error:
            return {
                "schema_version": 1,
                "surface_id": surface_id,
                "status": "unavailable",
                "failure_reason": error.reason_code,
                "provider_error": error.evidence,
                "provider_observed": False,
                "action_ack_used_as_postcondition": False,
                "fixture_used": False,
                "ocr_used": False,
                "coordinates_used": False,
                "console_used": False,
                "generic_character_rebind_used": False,
            }
        except Exception as error:
            return {
                "schema_version": 1,
                "surface_id": surface_id,
                "status": "unavailable",
                "failure_reason": (
                    "scoreboard_surface_provider_exception:"
                    f"{type(error).__name__}"
                ),
                "provider_error": {"message": str(error)},
                "provider_observed": False,
                "action_ack_used_as_postcondition": False,
                "fixture_used": False,
                "ocr_used": False,
                "coordinates_used": False,
                "console_used": False,
                "generic_character_rebind_used": False,
            }


__all__ = [
    "SCOREBOARD_REQUIRED_SURFACES",
    "SCOREBOARD_SURFACE_REGISTRY_KIND",
    "SCOREBOARD_SURFACE_REGISTRY_SCHEMA_VERSION",
    "ScoreboardSurfaceCheckpoint",
    "ScoreboardSurfaceCheckpointError",
    "ScoreboardSurfaceCheckpointProvider",
    "ScoreboardSurfaceService",
    "scoreboard_checkpoint_sha256",
    "scoreboard_surface_snapshot_binding",
    "validate_scoreboard_surface_query",
    "validate_scoreboard_surface_checkpoint_registry",
]
