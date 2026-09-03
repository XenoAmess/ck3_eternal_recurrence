#!/usr/bin/env python3
"""Canonical Phase2 span-source checkpoint registry and restore contract.

The provider consumes checkpoints already produced by a real seed/capture
lineage.  It cannot create events, copy fixtures into a runtime, use the
console, or perform an arbitrary character rebind.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import re
from typing import Callable, Final, Mapping

from zhongguo_phase2_event_choreography import Phase2EventSequencePlan


SOURCE_CHECKPOINT_REGISTRY_KIND: Final = (
    "zg361_phase2_canonical_source_checkpoint_registry"
)
SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION: Final = 1
CHECKPOINT_REQUIRED_HANDLERS: Final = (
    "capture_promotion_compensation",
    "capture_projects_metrics",
    "capture_incidents_operations",
    "capture_cross_cycle_endgame",
)


class Phase2SourceCheckpointError(RuntimeError):
    result: Final = "RED"

    def __init__(self, reason_code: str, evidence: Mapping[str, object]) -> None:
        self.reason_code = reason_code
        self.evidence = {**dict(evidence), "result": "RED", "reason_code": reason_code}
        super().__init__(f"phase-two source checkpoint RED [{reason_code}]")


@dataclass(frozen=True, slots=True)
class Phase2SourceCheckpoint:
    span_id: str
    handler: str
    source_event_definition_key: str
    owner_character_id: int
    player_character_id: int
    date_raw: int
    path: Path
    bytes: int
    sha256: str
    save_lineage_id: str
    source_receipt: Mapping[str, object]


RestoreRegisteredCheckpoint = Callable[
    [Phase2SourceCheckpoint], Mapping[str, object]
]


def _positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _entry(
    value: object,
    *,
    seed_lineage_id: str,
) -> Phase2SourceCheckpoint:
    row = dict(value) if isinstance(value, Mapping) else {}
    checkpoint = row.get("checkpoint")
    checkpoint = dict(checkpoint) if isinstance(checkpoint, Mapping) else {}
    receipt = row.get("source_receipt")
    receipt = dict(receipt) if isinstance(receipt, Mapping) else {}
    raw_path = checkpoint.get("path")
    path = Path(str(raw_path)).resolve() if isinstance(raw_path, str) else Path()
    expected_bytes = checkpoint.get("bytes")
    expected_sha = str(checkpoint.get("sha256", "")).upper()
    owner = row.get("owner_character_id")
    player = row.get("player_character_id")
    date_raw = row.get("date_raw")
    event_key = row.get("source_event_definition_key")
    common_valid = (
        isinstance(row.get("span_id"), str)
        and isinstance(row.get("handler"), str)
        and isinstance(event_key, str)
        and bool(event_key)
        and _positive_int(owner)
        and _positive_int(player)
        and isinstance(date_raw, int)
        and not isinstance(date_raw, bool)
        and isinstance(raw_path, str)
        and path.is_absolute()
        and path.is_file()
        and _positive_int(expected_bytes)
        and path.stat().st_size == expected_bytes
        and re.fullmatch(r"[0-9A-F]{64}", expected_sha) is not None
        and _sha256(path) == expected_sha
        and checkpoint.get("save_lineage_id") == seed_lineage_id
    )
    receipt_valid = (
        receipt.get("result") == "GREEN"
        and receipt.get("evidence_class") == "real_ck3"
        and receipt.get("provider_observed") is True
        and receipt.get("ui_state_verified") is True
        and receipt.get("fixture_used") is False
        and receipt.get("console_used") is False
        and receipt.get("span_id") == row.get("span_id")
        and receipt.get("event_definition_key") == event_key
        and receipt.get("owner_character_id") == owner
        and receipt.get("player_character_id") == player
        and receipt.get("date_raw") == date_raw
        and str(receipt.get("checkpoint_sha256", "")).upper() == expected_sha
        and receipt.get("save_lineage_id") == seed_lineage_id
    )
    if not common_valid or not receipt_valid:
        raise Phase2SourceCheckpointError(
            "source_checkpoint_entry_invalid",
            {
                "span_id": row.get("span_id"),
                "handler": row.get("handler"),
                "checkpoint_path": str(path),
                "checkpoint_bytes_match": (
                    path.is_file() and path.stat().st_size == expected_bytes
                ),
                "checkpoint_sha256_match": (
                    path.is_file()
                    and re.fullmatch(r"[0-9A-F]{64}", expected_sha) is not None
                    and _sha256(path) == expected_sha
                ),
                "source_receipt": receipt,
            },
        )
    return Phase2SourceCheckpoint(
        span_id=str(row["span_id"]),
        handler=str(row["handler"]),
        source_event_definition_key=str(event_key),
        owner_character_id=int(owner),
        player_character_id=int(player),
        date_raw=int(date_raw),
        path=path,
        bytes=int(expected_bytes),
        sha256=expected_sha,
        save_lineage_id=seed_lineage_id,
        source_receipt=receipt,
    )


class Phase2SourceCheckpointProvider:
    def __init__(
        self,
        registry: Mapping[str, object] | None,
        *,
        restore_registered_checkpoint: RestoreRegisteredCheckpoint | None,
        expected_seed_lineage_id: str | None,
    ) -> None:
        self.registry = dict(registry) if isinstance(registry, Mapping) else None
        self.restore_registered_checkpoint = restore_registered_checkpoint
        self.expected_seed_lineage_id = expected_seed_lineage_id
        self._entries: dict[str, Phase2SourceCheckpoint] | None = None

    def preflight(self) -> dict[str, object]:
        if self.registry is None:
            raise Phase2SourceCheckpointError(
                "source_checkpoint_registry_missing",
                {"required_handlers": list(CHECKPOINT_REQUIRED_HANDLERS)},
            )
        registry = self.registry
        seed_lineage_id = registry.get("seed_lineage_id")
        capture_lineage = registry.get("capture_lineage")
        rows = registry.get("entries")
        header_valid = (
            registry.get("schema_version") == SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION
            and registry.get("registry_kind") == SOURCE_CHECKPOINT_REGISTRY_KIND
            and registry.get("result") == "GREEN"
            and registry.get("evidence_class") == "real_ck3"
            and registry.get("fixture_used") is False
            and registry.get("console_used") is False
            and isinstance(seed_lineage_id, str)
            and bool(seed_lineage_id)
            and seed_lineage_id == self.expected_seed_lineage_id
            and isinstance(capture_lineage, Mapping)
            and capture_lineage.get("seed_lineage_id") == seed_lineage_id
            and isinstance(rows, list)
        )
        if not header_valid:
            raise Phase2SourceCheckpointError(
                "source_checkpoint_registry_header_invalid",
                {
                    "registry": registry,
                    "expected_seed_lineage_id": self.expected_seed_lineage_id,
                },
            )
        assert isinstance(seed_lineage_id, str)
        assert isinstance(rows, list)
        entries = [_entry(row, seed_lineage_id=seed_lineage_id) for row in rows]
        handlers = tuple(entry.handler for entry in entries)
        if handlers != CHECKPOINT_REQUIRED_HANDLERS or len(set(handlers)) != len(handlers):
            raise Phase2SourceCheckpointError(
                "source_checkpoint_registry_coverage_invalid",
                {
                    "required_handlers": list(CHECKPOINT_REQUIRED_HANDLERS),
                    "observed_handlers": list(handlers),
                },
            )
        if any(
            entry.handler == "capture_incidents_operations"
            and entry.owner_character_id != entry.player_character_id
            for entry in entries
        ):
            raise Phase2SourceCheckpointError(
                "incident_checkpoint_player_not_owner",
                {
                    "incident_entries": [
                        {
                            "owner_character_id": entry.owner_character_id,
                            "player_character_id": entry.player_character_id,
                        }
                        for entry in entries
                        if entry.handler == "capture_incidents_operations"
                    ]
                },
            )
        self._entries = {entry.handler: entry for entry in entries}
        return {
            "schema_version": 1,
            "result": "GREEN",
            "registry_kind": SOURCE_CHECKPOINT_REGISTRY_KIND,
            "seed_lineage_id": seed_lineage_id,
            "required_handlers": list(CHECKPOINT_REQUIRED_HANDLERS),
            "entry_count": len(entries),
            "restore_interface_available": callable(
                self.restore_registered_checkpoint
            ),
            "fixture_used": False,
            "console_used": False,
        }

    def checkpoint_for_plan(
        self, plan: Phase2EventSequencePlan
    ) -> Phase2SourceCheckpoint:
        preflight = self.preflight()
        if preflight["restore_interface_available"] is not True:
            raise Phase2SourceCheckpointError(
                "registered_checkpoint_restore_provider_missing",
                {"handler": plan.handler, "preflight": preflight},
            )
        assert self._entries is not None
        entry = self._entries.get(plan.handler)
        if entry is None:
            raise Phase2SourceCheckpointError(
                "source_checkpoint_not_registered", {"handler": plan.handler}
            )
        if not (
            entry.span_id == plan.span_id
            and entry.source_event_definition_key == plan.source_event
        ):
            raise Phase2SourceCheckpointError(
                "source_checkpoint_plan_mismatch",
                {
                    "handler": plan.handler,
                    "registered_span_id": entry.span_id,
                    "registered_event": entry.source_event_definition_key,
                    "expected_span_id": plan.span_id,
                    "expected_event": plan.source_event,
                },
            )
        return entry

    def restore(self, plan: Phase2EventSequencePlan) -> dict[str, object]:
        entry = self.checkpoint_for_plan(plan)
        restore = self.restore_registered_checkpoint
        assert callable(restore)
        value = restore(entry)
        receipt = dict(value) if isinstance(value, Mapping) else {}
        if not (
            receipt.get("result") == "GREEN"
            and receipt.get("provider_observed") is True
            and receipt.get("checkpoint_sha256") == entry.sha256
            and receipt.get("save_lineage_id") == entry.save_lineage_id
            and receipt.get("player_character_id") == entry.player_character_id
            and receipt.get("owner_character_id") == entry.owner_character_id
            and receipt.get("date_raw") == entry.date_raw
            and receipt.get("event_definition_key")
            == entry.source_event_definition_key
            and receipt.get("fixture_used") is False
            and receipt.get("console_used") is False
            and receipt.get("generic_character_rebind_used") is False
        ):
            raise Phase2SourceCheckpointError(
                "registered_checkpoint_restore_not_green",
                {
                    "handler": plan.handler,
                    "checkpoint_sha256": entry.sha256,
                    "restore_receipt": receipt,
                },
            )
        return {
            "schema_version": 1,
            "result": "GREEN",
            "span_id": plan.span_id,
            "handler": plan.handler,
            "checkpoint": {
                "path": str(entry.path),
                "bytes": entry.bytes,
                "sha256": entry.sha256,
                "save_lineage_id": entry.save_lineage_id,
            },
            "expected": {
                "event_definition_key": entry.source_event_definition_key,
                "owner_character_id": entry.owner_character_id,
                "player_character_id": entry.player_character_id,
                "date_raw": entry.date_raw,
            },
            "restore_receipt": receipt,
            "fixture_used": False,
            "console_used": False,
            "generic_character_rebind_used": False,
        }


__all__ = [
    "CHECKPOINT_REQUIRED_HANDLERS",
    "SOURCE_CHECKPOINT_REGISTRY_KIND",
    "SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION",
    "Phase2SourceCheckpoint",
    "Phase2SourceCheckpointError",
    "Phase2SourceCheckpointProvider",
    "RestoreRegisteredCheckpoint",
]
