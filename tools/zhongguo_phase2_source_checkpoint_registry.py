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

from zhongguo_phase2_event_choreography import (
    PHASE2_EVENT_SEQUENCE_PLANS,
    Phase2EventSequencePlan,
)
from zhongguo_phase2_source_checkpoint_provider import (
    CHECKPOINT_REQUIRED_HANDLERS,
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


def _source_receipt(
    value: object,
    *,
    plan: Phase2EventSequencePlan,
    owner_character_id: int,
    player_character_id: int,
    date_raw: int,
    checkpoint_sha256: str,
    seed_lineage_id: str,
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
        and receipt.get("save_lineage_id") == seed_lineage_id
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
                "expected_save_lineage_id": seed_lineage_id,
                "source_receipt": receipt,
            },
        )
    return receipt


class Phase2SourceCheckpointRegistryBuilder:
    """Freeze the four required live source checkpoints in canonical order."""

    def __init__(
        self,
        checkpoint_root: Path,
        *,
        seed_lineage_id: str,
        capture_lineage: Mapping[str, object],
    ) -> None:
        root = checkpoint_root.resolve()
        lineage = deepcopy(dict(capture_lineage))
        if not (
            isinstance(seed_lineage_id, str)
            and bool(seed_lineage_id)
            and lineage.get("seed_lineage_id") == seed_lineage_id
        ):
            raise Phase2SourceCheckpointRegistryBuildError(
                "source_checkpoint_registry_lineage_invalid",
                {
                    "checkpoint_root": str(root),
                    "seed_lineage_id": seed_lineage_id,
                    "capture_lineage": lineage,
                },
            )
        self.checkpoint_root = root
        self.seed_lineage_id = seed_lineage_id
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
        receipt = _source_receipt(
            source_receipt,
            plan=plan,
            owner_character_id=owner_character_id,
            player_character_id=player_character_id,
            date_raw=date_raw,
            checkpoint_sha256=source_sha256,
            seed_lineage_id=self.seed_lineage_id,
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
                "save_lineage_id": self.seed_lineage_id,
            },
            "source_receipt": receipt,
        }
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
            "schema_version": SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION,
            "registry_kind": SOURCE_CHECKPOINT_REGISTRY_KIND,
            "result": "GREEN",
            "evidence_class": "real_ck3",
            "fixture_used": False,
            "console_used": False,
            "seed_lineage_id": self.seed_lineage_id,
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
    seed_lineage_id = manifest.get("seed_lineage_id")
    capture_lineage = manifest.get("capture_lineage")
    entries = manifest.get("entries")
    header_valid = (
        manifest.get("schema_version") == 1
        and manifest.get("kind") == SOURCE_CHECKPOINT_CAPTURE_MANIFEST_KIND
        and manifest.get("result") == "GREEN"
        and manifest.get("evidence_class") == "real_ck3"
        and manifest.get("fixture_used") is False
        and manifest.get("console_used") is False
        and isinstance(seed_lineage_id, str)
        and bool(seed_lineage_id)
        and isinstance(capture_lineage, Mapping)
        and capture_lineage.get("seed_lineage_id") == seed_lineage_id
        and isinstance(entries, list)
    )
    if not header_valid:
        raise Phase2SourceCheckpointRegistryBuildError(
            "source_checkpoint_capture_manifest_header_invalid",
            {
                "manifest_path": str(capture_manifest_path.expanduser().resolve()),
                "seed_lineage_id": seed_lineage_id,
                "capture_lineage": capture_lineage,
                "entry_count": len(entries) if isinstance(entries, list) else None,
            },
        )
    assert isinstance(seed_lineage_id, str)
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
        seed_lineage_id=seed_lineage_id,
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
            and checkpoint.get("save_lineage_id") == seed_lineage_id
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
