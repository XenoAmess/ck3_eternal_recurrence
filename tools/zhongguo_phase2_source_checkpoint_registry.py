#!/usr/bin/env python3
"""Build the canonical Phase2 source-checkpoint registry from live receipts.

The capture runner owns CK3 and supplies checkpoints plus provider/UI receipts.
This module only freezes those already-observed bytes into a content-addressed
artifact directory.  It cannot stage product events, launch CK3, use a fixture,
or manufacture a receipt.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
from typing import Final, Mapping

from zg361_phase2_incident_checkpoint_seam import (
    IncidentCheckpointSeamError,
    validate_received_self_incident_checkpoint_receipt,
)
from zhongguo_phase2_event_choreography import (
    PHASE2_EVENT_SEQUENCE_PLANS,
    Phase2EventSequencePlan,
)
from zhongguo_phase2_source_checkpoint_provider import (
    CHECKPOINT_REQUIRED_HANDLERS,
    INCIDENT_STRICT_RECEIPT_FIELD,
    LEGACY_SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION,
    MULTI_BRANCH_CAPTURE_LINEAGE_MODE,
    PRODUCT_ONLY_MULTI_BRANCH_LINEAGE_KIND,
    SOURCE_CHECKPOINT_REGISTRY_KIND,
    SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION,
)


_PLAN_BY_HANDLER: Final = {
    plan.handler: plan
    for plan in PHASE2_EVENT_SEQUENCE_PLANS
    if plan.handler in CHECKPOINT_REQUIRED_HANDLERS
}
SOURCE_CHECKPOINT_CAPTURE_MANIFEST_KIND: Final = (
    "zg361_phase2_source_checkpoint_capture_manifest"
)
_SHA256: Final = re.compile(r"^[0-9A-Fa-f]{64}$")
_LEGACY_CAPTURE_MANIFEST_SCHEMA_VERSION: Final = 2
_CAPTURE_MANIFEST_SCHEMA_VERSION: Final = 3


class Phase2SourceCheckpointRegistryBuildError(RuntimeError):
    """Fail-closed registry construction error with machine-readable evidence."""

    result: Final = "RED"

    def __init__(self, reason_code: str, evidence: Mapping[str, object]) -> None:
        self.reason_code = reason_code
        self.evidence = {
            **deepcopy(dict(evidence)),
            "result": "RED",
            "reason_code": reason_code,
        }
        super().__init__(f"phase-two source registry RED [{reason_code}]")


def _positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _lineage_set_id(
    bindings: tuple[tuple[str, str, str | None], ...]
) -> str:
    payload = json.dumps(
        [
            {
                "handler": handler,
                "seed_lineage_id": save_lineage_id,
                **(
                    {
                        "capture_run_input_checkpoint_sha256": (
                            source_input_sha256
                        )
                    }
                    if handler == "capture_incidents_operations"
                    and source_input_sha256 is not None
                    else {}
                ),
            }
            for handler, save_lineage_id, source_input_sha256 in bindings
        ],
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")
    return "zg361-phase2-lineage-set-" + hashlib.sha256(payload).hexdigest()


def _multi_branch_capture_lineage(
    value: object, *, lineage_set_id: object
) -> tuple[dict[str, object], dict[str, str]]:
    lineage = deepcopy(dict(value)) if isinstance(value, Mapping) else {}
    rows = lineage.get("entry_capture_lineages")
    bindings: list[tuple[str, str, str | None]] = []
    valid = isinstance(rows, list)
    for raw in rows if isinstance(rows, list) else []:
        row = raw if isinstance(raw, Mapping) else {}
        handler = row.get("handler")
        save_lineage_id = row.get("seed_lineage_id")
        capture_lineage = row.get("capture_lineage")
        source_input_sha256 = None
        input_checkpoint_valid = True
        if handler == "capture_incidents_operations":
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
            input_checkpoint_valid = bool(
                _SHA256.fullmatch(source_input_sha256) is not None
                and input_path.is_absolute()
                and input_path.is_file()
                and _positive_int(input_checkpoint.get("bytes"))
                and input_path.stat().st_size == input_checkpoint.get("bytes")
                and _sha256(input_path) == source_input_sha256
            )
        row_valid = (
            isinstance(handler, str)
            and bool(handler)
            and isinstance(save_lineage_id, str)
            and bool(save_lineage_id)
            and isinstance(capture_lineage, Mapping)
            and capture_lineage.get("seed_lineage_id") == save_lineage_id
            and input_checkpoint_valid
        )
        valid = valid and row_valid
        if row_valid:
            bindings.append(
                (handler, save_lineage_id, source_input_sha256)
            )
    observed_handlers = tuple(
        handler for handler, _lineage, _source_sha in bindings
    )
    valid = bool(
        valid
        and isinstance(lineage_set_id, str)
        and lineage_set_id
        and lineage.get("schema_version") == 2
        and lineage.get("kind") == PRODUCT_ONLY_MULTI_BRANCH_LINEAGE_KIND
        and lineage.get("capture_lineage_mode")
        == MULTI_BRANCH_CAPTURE_LINEAGE_MODE
        and lineage.get("lineage_set_id") == lineage_set_id
        and "seed_lineage_id" not in lineage
        and lineage.get("evidence_class") == "real_ck3"
        and lineage.get("fixture_used") is False
        and lineage.get("console_used") is False
        and observed_handlers == CHECKPOINT_REQUIRED_HANDLERS
        and _lineage_set_id(tuple(bindings)) == lineage_set_id
    )
    if not valid:
        raise Phase2SourceCheckpointRegistryBuildError(
            "source_checkpoint_registry_lineage_set_invalid",
            {
                "lineage_set_id": lineage_set_id,
                "capture_lineage": lineage,
                "observed_handler_lineages": [
                    {
                        "handler": handler,
                        "save_lineage_id": save_lineage_id,
                        **(
                            {
                                "capture_run_input_checkpoint_sha256": (
                                    source_input_sha256
                                )
                            }
                            if source_input_sha256 is not None
                            else {}
                        ),
                    }
                    for handler, save_lineage_id, source_input_sha256 in bindings
                ],
            },
        )
    return lineage, {
        handler: save_lineage_id
        for handler, save_lineage_id, _source_sha in bindings
    }


def _source_receipt(
    value: object,
    *,
    plan: Phase2EventSequencePlan,
    owner_character_id: int,
    player_character_id: int,
    date_raw: int,
    checkpoint_sha256: str,
    save_lineage_id: str,
) -> dict[str, object]:
    receipt = deepcopy(dict(value)) if isinstance(value, Mapping) else {}
    valid = (
        receipt.get("result") == "GREEN"
        and receipt.get("evidence_class") == "real_ck3"
        and receipt.get("provider_observed") is True
        and receipt.get("ui_state_verified") is True
        and receipt.get("fixture_used") is False
        and receipt.get("console_used") is False
        and receipt.get("span_id") == plan.span_id
        and receipt.get("event_definition_key") == plan.source_event
        and receipt.get("owner_character_id") == owner_character_id
        and receipt.get("player_character_id") == player_character_id
        and receipt.get("date_raw") == date_raw
        and str(receipt.get("checkpoint_sha256", "")).upper()
        == checkpoint_sha256
        and receipt.get("save_lineage_id") == save_lineage_id
    )
    if not valid:
        raise Phase2SourceCheckpointRegistryBuildError(
            "source_checkpoint_receipt_invalid",
            {
                "handler": plan.handler,
                "span_id": plan.span_id,
                "expected_event_definition_key": plan.source_event,
                "expected_owner_character_id": owner_character_id,
                "expected_player_character_id": player_character_id,
                "expected_date_raw": date_raw,
                "expected_checkpoint_sha256": checkpoint_sha256,
                "expected_save_lineage_id": save_lineage_id,
                "source_receipt": receipt,
            },
        )
    return receipt


def _validate_strict_incident_receipt(
    value: object,
    *,
    source_checkpoint: Path,
    owner_character_id: int,
    player_character_id: int,
    date_raw: int,
    checkpoint_sha256: str,
    save_lineage_id: str,
) -> dict[str, object]:
    receipt = deepcopy(dict(value)) if isinstance(value, Mapping) else {}
    try:
        summary = validate_received_self_incident_checkpoint_receipt(
            receipt,
            expected_seed_lineage_id=save_lineage_id,
        )
    except IncidentCheckpointSeamError as error:
        raise Phase2SourceCheckpointRegistryBuildError(
            "incident_source_checkpoint_receipt_invalid",
            {
                "upstream_reason_code": error.reason_code,
                "upstream_evidence": error.evidence,
            },
        ) from error
    checkpoint = summary["checkpoint"]
    assert isinstance(checkpoint, Mapping)
    valid = (
        Path(str(checkpoint.get("path"))).resolve() == source_checkpoint
        and checkpoint.get("bytes") == source_checkpoint.stat().st_size
        and checkpoint.get("sha256") == checkpoint_sha256
        and checkpoint.get("save_lineage_id") == save_lineage_id
        and summary.get("owner_character_id") == owner_character_id
        and summary.get("player_character_id") == player_character_id
        and summary.get("subject_character_id") == player_character_id
        and summary.get("date_raw") == date_raw
    )
    if not valid:
        raise Phase2SourceCheckpointRegistryBuildError(
            "incident_source_checkpoint_registry_binding_mismatch",
            {
                "source_checkpoint": str(source_checkpoint),
                "checkpoint_sha256": checkpoint_sha256,
                "owner_character_id": owner_character_id,
                "player_character_id": player_character_id,
                "date_raw": date_raw,
                "strict_receipt_summary": summary,
            },
        )
    return receipt


def _archive_strict_incident_receipt(
    receipt: Mapping[str, object],
    *,
    checkpoint_target: Path,
    save_lineage_id: str,
) -> dict[str, object]:
    durable = deepcopy(dict(receipt))
    checkpoint = durable.get("checkpoint")
    if not isinstance(checkpoint, dict):
        raise Phase2SourceCheckpointRegistryBuildError(
            "incident_source_checkpoint_receipt_invalid",
            {"checkpoint": checkpoint},
        )
    checkpoint["path"] = str(checkpoint_target.resolve())
    validate_received_self_incident_checkpoint_receipt(
        durable,
        expected_seed_lineage_id=save_lineage_id,
    )
    payload = (
        json.dumps(durable, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    target = checkpoint_target.with_suffix(".strict-receipt.json")
    if target.exists():
        if not target.is_file() or target.read_bytes() != payload:
            raise Phase2SourceCheckpointRegistryBuildError(
                "incident_source_checkpoint_receipt_archive_collision",
                {"receipt_path": str(target)},
            )
    else:
        target.write_bytes(payload)
    return {
        "kind": "zg361_phase2_incidents_operations_source_checkpoint_receipt",
        "path": str(target.resolve()),
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest().upper(),
    }


class Phase2SourceCheckpointRegistryBuilder:
    """Freeze the four required live source checkpoints in canonical order."""

    def __init__(
        self,
        checkpoint_root: Path,
        *,
        seed_lineage_id: str | None = None,
        lineage_set_id: str | None = None,
        capture_lineage: Mapping[str, object],
    ) -> None:
        root = checkpoint_root.resolve()
        lineage = deepcopy(dict(capture_lineage))
        legacy = bool(
            isinstance(seed_lineage_id, str)
            and seed_lineage_id
            and lineage_set_id is None
            and lineage.get("seed_lineage_id") == seed_lineage_id
        )
        multi_branch = bool(
            seed_lineage_id is None
            and isinstance(lineage_set_id, str)
            and lineage_set_id
        )
        handler_lineages: dict[str, str] = {}
        if multi_branch:
            lineage, handler_lineages = _multi_branch_capture_lineage(
                lineage,
                lineage_set_id=lineage_set_id,
            )
        if not legacy and not multi_branch:
            raise Phase2SourceCheckpointRegistryBuildError(
                "source_checkpoint_registry_lineage_invalid",
                {
                    "checkpoint_root": str(root),
                    "seed_lineage_id": seed_lineage_id,
                    "lineage_set_id": lineage_set_id,
                    "capture_lineage": lineage,
                },
            )
        self.checkpoint_root = root
        self.seed_lineage_id = seed_lineage_id
        self.lineage_set_id = lineage_set_id
        self.schema_version = (
            SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION
            if multi_branch
            else LEGACY_SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION
        )
        self.handler_save_lineage_ids = (
            handler_lineages
            if multi_branch
            else {
                handler: str(seed_lineage_id)
                for handler in CHECKPOINT_REQUIRED_HANDLERS
            }
        )
        self.capture_lineage = lineage
        self._entries: list[dict[str, object]] = []

    @property
    def next_required_handler(self) -> str | None:
        index = len(self._entries)
        if index == len(CHECKPOINT_REQUIRED_HANDLERS):
            return None
        return CHECKPOINT_REQUIRED_HANDLERS[index]

    def record(
        self,
        plan: Phase2EventSequencePlan,
        *,
        source_checkpoint: Path,
        owner_character_id: int,
        player_character_id: int,
        date_raw: int,
        source_receipt: Mapping[str, object],
        save_lineage_id: str | None = None,
        strict_incident_source_checkpoint_receipt: (
            Mapping[str, object] | None
        ) = None,
    ) -> dict[str, object]:
        expected_handler = self.next_required_handler
        canonical_plan = _PLAN_BY_HANDLER.get(plan.handler)
        if not (
            expected_handler is not None
            and plan == canonical_plan
            and plan.handler == expected_handler
            and isinstance(plan.source_event, str)
            and bool(plan.source_event)
        ):
            raise Phase2SourceCheckpointRegistryBuildError(
                "source_checkpoint_record_order_invalid",
                {
                    "expected_handler": expected_handler,
                    "observed_handler": plan.handler,
                    "observed_span_id": plan.span_id,
                },
            )
        if not (
            _positive_int(owner_character_id)
            and _positive_int(player_character_id)
            and isinstance(date_raw, int)
            and not isinstance(date_raw, bool)
        ):
            raise Phase2SourceCheckpointRegistryBuildError(
                "source_checkpoint_binding_invalid",
                {
                    "handler": plan.handler,
                    "owner_character_id": owner_character_id,
                    "player_character_id": player_character_id,
                    "date_raw": date_raw,
                },
            )
        if (
            plan.handler == "capture_incidents_operations"
            and owner_character_id == player_character_id
        ):
            raise Phase2SourceCheckpointRegistryBuildError(
                "incident_checkpoint_owner_equals_player",
                {
                    "owner_character_id": owner_character_id,
                    "player_character_id": player_character_id,
                    "required_binding": (
                        "played_subject_with_distinct_notice_owner"
                    ),
                },
            )

        source = source_checkpoint.resolve()
        if not source.is_file():
            raise Phase2SourceCheckpointRegistryBuildError(
                "source_checkpoint_missing",
                {"handler": plan.handler, "source_checkpoint": str(source)},
            )
        source_bytes = source.stat().st_size
        source_sha256 = _sha256(source)
        expected_save_lineage_id = self.handler_save_lineage_ids.get(
            plan.handler
        )
        observed_save_lineage_id = (
            save_lineage_id
            if save_lineage_id is not None
            else source_receipt.get("save_lineage_id")
        )
        if not (
            isinstance(observed_save_lineage_id, str)
            and bool(observed_save_lineage_id)
            and observed_save_lineage_id == expected_save_lineage_id
        ):
            raise Phase2SourceCheckpointRegistryBuildError(
                "source_checkpoint_entry_lineage_invalid",
                {
                    "handler": plan.handler,
                    "expected_save_lineage_id": expected_save_lineage_id,
                    "observed_save_lineage_id": observed_save_lineage_id,
                },
            )
        strict_receipt = None
        if plan.handler == "capture_incidents_operations":
            strict_receipt = _validate_strict_incident_receipt(
                strict_incident_source_checkpoint_receipt,
                source_checkpoint=source,
                owner_character_id=owner_character_id,
                player_character_id=player_character_id,
                date_raw=date_raw,
                checkpoint_sha256=source_sha256,
                save_lineage_id=observed_save_lineage_id,
            )
        elif strict_incident_source_checkpoint_receipt is not None:
            raise Phase2SourceCheckpointRegistryBuildError(
                "incident_source_checkpoint_receipt_misrouted",
                {"handler": plan.handler},
            )
        receipt = _source_receipt(
            source_receipt,
            plan=plan,
            owner_character_id=owner_character_id,
            player_character_id=player_character_id,
            date_raw=date_raw,
            checkpoint_sha256=source_sha256,
            save_lineage_id=observed_save_lineage_id,
        )

        self.checkpoint_root.mkdir(parents=True, exist_ok=True)
        ordinal = len(self._entries) + 1
        target = self.checkpoint_root / (
            f"{ordinal:02d}-{plan.span_id}-{source_sha256[:16].lower()}.ck3"
        )
        if target.exists():
            if not (
                target.is_file()
                and target.stat().st_size == source_bytes
                and _sha256(target) == source_sha256
            ):
                raise Phase2SourceCheckpointRegistryBuildError(
                    "source_checkpoint_archive_collision",
                    {
                        "handler": plan.handler,
                        "archive_path": str(target),
                        "expected_bytes": source_bytes,
                        "expected_sha256": source_sha256,
                    },
                )
        else:
            shutil.copyfile(source, target)
        if target.stat().st_size != source_bytes or _sha256(target) != source_sha256:
            raise Phase2SourceCheckpointRegistryBuildError(
                "source_checkpoint_archive_mismatch",
                {
                    "handler": plan.handler,
                    "source_path": str(source),
                    "archive_path": str(target),
                    "source_bytes": source_bytes,
                    "source_sha256": source_sha256,
                },
            )

        entry = {
            "span_id": plan.span_id,
            "handler": plan.handler,
            "source_event_definition_key": plan.source_event,
            "owner_character_id": owner_character_id,
            "player_character_id": player_character_id,
            "date_raw": date_raw,
            "checkpoint": {
                "path": str(target.resolve()),
                "bytes": source_bytes,
                "sha256": source_sha256,
                "save_lineage_id": observed_save_lineage_id,
            },
            "source_receipt": receipt,
        }
        if self.schema_version == SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION:
            entry["save_lineage_id"] = observed_save_lineage_id
        if strict_receipt is not None:
            entry[INCIDENT_STRICT_RECEIPT_FIELD] = (
                _archive_strict_incident_receipt(
                    strict_receipt,
                    checkpoint_target=target,
                    save_lineage_id=observed_save_lineage_id,
                )
            )
        self._entries.append(entry)
        return deepcopy(entry)

    def finalize(self) -> dict[str, object]:
        observed = tuple(row["handler"] for row in self._entries)
        if observed != CHECKPOINT_REQUIRED_HANDLERS:
            raise Phase2SourceCheckpointRegistryBuildError(
                "source_checkpoint_registry_incomplete",
                {
                    "required_handlers": list(CHECKPOINT_REQUIRED_HANDLERS),
                    "observed_handlers": list(observed),
                    "next_required_handler": self.next_required_handler,
                },
            )
        return {
            "schema_version": self.schema_version,
            "registry_kind": SOURCE_CHECKPOINT_REGISTRY_KIND,
            "result": "GREEN",
            "evidence_class": "real_ck3",
            "fixture_used": False,
            "console_used": False,
            **(
                {"lineage_set_id": self.lineage_set_id}
                if self.schema_version
                == SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION
                else {"seed_lineage_id": self.seed_lineage_id}
            ),
            "capture_lineage": deepcopy(self.capture_lineage),
            "entries": deepcopy(self._entries),
        }

    def write(self, registry_path: Path) -> dict[str, object]:
        registry = self.finalize()
        target = registry_path.resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            with target.open("x", encoding="utf-8", newline="\n") as output:
                json.dump(registry, output, ensure_ascii=False, indent=2)
                output.write("\n")
        except FileExistsError as error:
            raise Phase2SourceCheckpointRegistryBuildError(
                "source_checkpoint_registry_already_exists",
                {"registry_path": str(target)},
            ) from error
        return registry


def _read_capture_manifest(path: Path) -> dict[str, object]:
    source = path.expanduser().resolve()
    try:
        payload = json.loads(source.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise Phase2SourceCheckpointRegistryBuildError(
            "source_checkpoint_capture_manifest_unreadable",
            {"manifest_path": str(source), "error": f"{type(error).__name__}: {error}"},
        ) from error
    if not isinstance(payload, dict):
        raise Phase2SourceCheckpointRegistryBuildError(
            "source_checkpoint_capture_manifest_invalid",
            {"manifest_path": str(source), "root_type": type(payload).__name__},
        )
    return payload


def build_registry_from_capture_manifest(
    capture_manifest_path: Path,
    *,
    checkpoint_root: Path,
    registry_path: Path,
) -> dict[str, object]:
    """Archive four already-observed live checkpoints and write the registry.

    This is deliberately an assembler, not a producer.  Every checkpoint and
    provider/UI receipt must already exist in the input manifest.  No field is
    defaulted or synthesized here.
    """

    manifest = _read_capture_manifest(capture_manifest_path)
    manifest_schema_version = manifest.get("schema_version")
    seed_lineage_id = manifest.get("seed_lineage_id")
    lineage_set_id = manifest.get("lineage_set_id")
    capture_lineage = manifest.get("capture_lineage")
    entries = manifest.get("entries")
    common_header_valid = (
        manifest_schema_version
        in (
            _LEGACY_CAPTURE_MANIFEST_SCHEMA_VERSION,
            _CAPTURE_MANIFEST_SCHEMA_VERSION,
        )
        and manifest.get("kind") == SOURCE_CHECKPOINT_CAPTURE_MANIFEST_KIND
        and manifest.get("result") == "GREEN"
        and manifest.get("evidence_class") == "real_ck3"
        and manifest.get("fixture_used") is False
        and manifest.get("console_used") is False
        and isinstance(capture_lineage, Mapping)
        and isinstance(entries, list)
    )
    handler_lineages: dict[str, str] = {}
    lineage_header_valid = False
    if manifest_schema_version == _LEGACY_CAPTURE_MANIFEST_SCHEMA_VERSION:
        lineage_header_valid = bool(
            isinstance(seed_lineage_id, str)
            and seed_lineage_id
            and "lineage_set_id" not in manifest
            and capture_lineage.get("seed_lineage_id") == seed_lineage_id
        )
        if lineage_header_valid:
            handler_lineages = {
                handler: seed_lineage_id
                for handler in CHECKPOINT_REQUIRED_HANDLERS
            }
    elif manifest_schema_version == _CAPTURE_MANIFEST_SCHEMA_VERSION:
        lineage_header_valid = bool(
            isinstance(lineage_set_id, str)
            and lineage_set_id
            and "seed_lineage_id" not in manifest
        )
        if lineage_header_valid:
            _, handler_lineages = _multi_branch_capture_lineage(
                capture_lineage,
                lineage_set_id=lineage_set_id,
            )
    if not common_header_valid or not lineage_header_valid:
        raise Phase2SourceCheckpointRegistryBuildError(
            "source_checkpoint_capture_manifest_header_invalid",
            {
                "manifest_path": str(capture_manifest_path.expanduser().resolve()),
                "seed_lineage_id": seed_lineage_id,
                "lineage_set_id": lineage_set_id,
                "capture_lineage": capture_lineage,
                "entry_count": len(entries) if isinstance(entries, list) else None,
            },
        )
    assert isinstance(manifest_schema_version, int)
    assert isinstance(capture_lineage, Mapping)
    assert isinstance(entries, list)
    observed_handlers = tuple(
        row.get("handler") if isinstance(row, Mapping) else None for row in entries
    )
    if observed_handlers != CHECKPOINT_REQUIRED_HANDLERS:
        raise Phase2SourceCheckpointRegistryBuildError(
            "source_checkpoint_capture_manifest_coverage_invalid",
            {
                "required_handlers": list(CHECKPOINT_REQUIRED_HANDLERS),
                "observed_handlers": list(observed_handlers),
            },
        )

    builder = Phase2SourceCheckpointRegistryBuilder(
        checkpoint_root,
        seed_lineage_id=(
            str(seed_lineage_id)
            if manifest_schema_version
            == _LEGACY_CAPTURE_MANIFEST_SCHEMA_VERSION
            else None
        ),
        lineage_set_id=(
            str(lineage_set_id)
            if manifest_schema_version == _CAPTURE_MANIFEST_SCHEMA_VERSION
            else None
        ),
        capture_lineage=capture_lineage,
    )
    for raw in entries:
        assert isinstance(raw, Mapping)
        handler = str(raw["handler"])
        plan = _PLAN_BY_HANDLER[handler]
        checkpoint_value = raw.get("checkpoint")
        checkpoint = (
            checkpoint_value if isinstance(checkpoint_value, Mapping) else {}
        )
        checkpoint_path_value = checkpoint.get("path")
        checkpoint_path = (
            Path(checkpoint_path_value).expanduser().resolve()
            if isinstance(checkpoint_path_value, str)
            and Path(checkpoint_path_value).is_absolute()
            else None
        )
        owner = raw.get("owner_character_id")
        player = raw.get("player_character_id")
        date_raw = raw.get("date_raw")
        checkpoint_sha = str(checkpoint.get("sha256", "")).upper()
        save_lineage_id = checkpoint.get("save_lineage_id")
        row_valid = (
            raw.get("span_id") == plan.span_id
            and raw.get("source_event_definition_key") == plan.source_event
            and _positive_int(owner)
            and _positive_int(player)
            and isinstance(date_raw, int)
            and not isinstance(date_raw, bool)
            and checkpoint_path is not None
            and checkpoint_path.is_file()
            and _positive_int(checkpoint.get("bytes"))
            and checkpoint_path.stat().st_size == checkpoint.get("bytes")
            and _SHA256.fullmatch(checkpoint_sha) is not None
            and _sha256(checkpoint_path) == checkpoint_sha
            and isinstance(save_lineage_id, str)
            and bool(save_lineage_id)
            and save_lineage_id == handler_lineages.get(handler)
        )
        if not row_valid:
            raise Phase2SourceCheckpointRegistryBuildError(
                "source_checkpoint_capture_entry_invalid",
                {
                    "handler": handler,
                    "expected_span_id": plan.span_id,
                    "expected_event_definition_key": plan.source_event,
                    "entry": deepcopy(dict(raw)),
                },
            )
        assert checkpoint_path is not None
        assert isinstance(owner, int)
        assert isinstance(player, int)
        assert isinstance(date_raw, int)
        builder.record(
            plan,
            source_checkpoint=checkpoint_path,
            owner_character_id=owner,
            player_character_id=player,
            date_raw=date_raw,
            source_receipt=(
                raw["source_receipt"]
                if isinstance(raw.get("source_receipt"), Mapping)
                else {}
            ),
            save_lineage_id=save_lineage_id,
            strict_incident_source_checkpoint_receipt=(
                raw[INCIDENT_STRICT_RECEIPT_FIELD]
                if isinstance(raw.get(INCIDENT_STRICT_RECEIPT_FIELD), Mapping)
                else None
            ),
        )
    return builder.write(registry_path)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--capture-manifest",
        type=Path,
        required=True,
        help="GREEN real-CK3 manifest containing the four existing checkpoints and receipts",
    )
    parser.add_argument(
        "--checkpoint-root",
        type=Path,
        required=True,
        help="new or content-identical archive directory for frozen checkpoint bytes",
    )
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main() -> int:
    arguments = _parser().parse_args()
    try:
        registry = build_registry_from_capture_manifest(
            arguments.capture_manifest,
            checkpoint_root=arguments.checkpoint_root,
            registry_path=arguments.output,
        )
    except Phase2SourceCheckpointRegistryBuildError as error:
        print(json.dumps(error.evidence, ensure_ascii=False), file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "result": registry["result"],
                "registry": str(arguments.output.expanduser().resolve()),
                "entry_count": len(registry["entries"]),
            },
            ensure_ascii=False,
        )
    )
    return 0


__all__ = [
    "SOURCE_CHECKPOINT_CAPTURE_MANIFEST_KIND",
    "Phase2SourceCheckpointRegistryBuildError",
    "Phase2SourceCheckpointRegistryBuilder",
    "build_registry_from_capture_manifest",
]


if __name__ == "__main__":
    raise SystemExit(main())
