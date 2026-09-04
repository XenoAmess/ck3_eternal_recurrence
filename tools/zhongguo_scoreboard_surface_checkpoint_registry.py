#!/usr/bin/env python3
"""Freeze scoreboard product surfaces observed by the managed live runner.

The builder accepts only a real paused/event-free snapshot, its full scoreboard
query, and the materialized native save receipt.  It does not create gameplay
state or infer a surface from an ACK.  The live capture helper is deliberately
small so the formal producer/runner can call it at a product state it already
reached without gaining fixture, console, OCR, coordinate, or rebind powers.
"""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import shutil
from typing import Final, Mapping

from zhongguo_scoreboard_surface_checkpoint_provider import (
    SCOREBOARD_REQUIRED_SURFACES,
    SCOREBOARD_SURFACE_REGISTRY_KIND,
    SCOREBOARD_SURFACE_REGISTRY_SCHEMA_VERSION,
    ScoreboardSurfaceCheckpointError,
    ScoreboardSurfaceService,
    scoreboard_checkpoint_sha256,
    scoreboard_surface_snapshot_binding,
    validate_scoreboard_surface_query,
)


class ScoreboardSurfaceCheckpointRegistryBuildError(RuntimeError):
    """Fail-closed registry construction error with typed evidence."""

    result: Final = "RED"

    def __init__(self, reason_code: str, evidence: Mapping[str, object]) -> None:
        self.reason_code = reason_code
        self.evidence = {
            **deepcopy(dict(evidence)),
            "result": "RED",
            "reason_code": reason_code,
        }
        super().__init__(f"scoreboard surface registry RED [{reason_code}]")


def _positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _same_runtime_binding(
    before: Mapping[str, object], after: Mapping[str, object]
) -> bool:
    return all(
        before.get(key) == after.get(key)
        for key in (
            "bridge_pid",
            "connection_generation",
            "player_character_id",
            "date_raw",
        )
    )


class ScoreboardSurfaceCheckpointRegistryBuilder:
    """Freeze the two live product checkpoints in matrix execution order."""

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
            and lineage.get("evidence_class") == "real_ck3"
            and lineage.get("fixture_used") is False
            and lineage.get("ocr_used") is False
            and lineage.get("coordinates_used") is False
            and lineage.get("console_used") is False
            and lineage.get("generic_character_rebind_used") is False
        ):
            raise ScoreboardSurfaceCheckpointRegistryBuildError(
                "scoreboard_surface_registry_lineage_invalid",
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
    def next_required_surface(self) -> str | None:
        index = len(self._entries)
        if index == len(SCOREBOARD_REQUIRED_SURFACES):
            return None
        return SCOREBOARD_REQUIRED_SURFACES[index]

    def record(
        self,
        surface_id: str,
        *,
        source_snapshot: Mapping[str, object],
        source_query: Mapping[str, object],
        native_save_result: Mapping[str, object],
        post_save_snapshot: Mapping[str, object],
    ) -> dict[str, object]:
        expected_surface = self.next_required_surface
        if surface_id != expected_surface:
            raise ScoreboardSurfaceCheckpointRegistryBuildError(
                "scoreboard_surface_record_order_invalid",
                {
                    "expected_surface": expected_surface,
                    "observed_surface": surface_id,
                },
            )
        try:
            before = scoreboard_surface_snapshot_binding(source_snapshot)
            after = scoreboard_surface_snapshot_binding(post_save_snapshot)
            query_contract = validate_scoreboard_surface_query(
                source_query,
                surface_id=surface_id,
                expected_player_character_id=int(
                    before["player_character_id"]
                ),
                expected_date_raw=int(before["date_raw"]),
            )
        except (ScoreboardSurfaceCheckpointError, KeyError, TypeError) as error:
            evidence = (
                error.evidence
                if isinstance(error, ScoreboardSurfaceCheckpointError)
                else {"message": str(error)}
            )
            raise ScoreboardSurfaceCheckpointRegistryBuildError(
                "scoreboard_surface_capture_observation_invalid",
                {"surface_id": surface_id, "upstream": evidence},
            ) from error
        query_binding = query_contract.get("binding")
        if not (
            _same_runtime_binding(before, after)
            and isinstance(query_binding, Mapping)
            and query_binding.get("revision") == before.get("revision")
            and query_binding.get("native_revision")
            == before.get("native_revision")
            and query_binding.get("connection_generation")
            == before.get("connection_generation")
        ):
            raise ScoreboardSurfaceCheckpointRegistryBuildError(
                "scoreboard_surface_capture_binding_changed",
                {
                    "surface_id": surface_id,
                    "before": before,
                    "after": after,
                    "query_binding": query_binding,
                },
            )

        save_result = deepcopy(dict(native_save_result))
        checkpoint = save_result.get("checkpoint")
        checkpoint = dict(checkpoint) if isinstance(checkpoint, Mapping) else {}
        raw_path = checkpoint.get("path")
        source_path = (
            Path(str(raw_path)).resolve() if isinstance(raw_path, str) else Path()
        )
        expected_bytes = checkpoint.get("size")
        expected_sha256 = str(checkpoint.get("sha256", "")).upper()
        save_valid = bool(
            save_result.get("accepted") is True
            and checkpoint.get("status") == "saved"
            and isinstance(raw_path, str)
            and source_path.is_absolute()
            and source_path.is_file()
            and _positive_int(expected_bytes)
            and source_path.stat().st_size == expected_bytes
            and len(expected_sha256) == 64
            and scoreboard_checkpoint_sha256(source_path) == expected_sha256
            and checkpoint.get("date_raw") == before.get("date_raw")
        )
        if not save_valid:
            raise ScoreboardSurfaceCheckpointRegistryBuildError(
                "scoreboard_surface_native_save_invalid",
                {
                    "surface_id": surface_id,
                    "native_save_result": save_result,
                },
            )

        self.checkpoint_root.mkdir(parents=True, exist_ok=True)
        ordinal = len(self._entries) + 1
        target = self.checkpoint_root / (
            f"{ordinal:02d}-{surface_id}-{expected_sha256[:16].lower()}.ck3"
        )
        if target.exists():
            if not (
                target.is_file()
                and target.stat().st_size == expected_bytes
                and scoreboard_checkpoint_sha256(target) == expected_sha256
            ):
                raise ScoreboardSurfaceCheckpointRegistryBuildError(
                    "scoreboard_surface_checkpoint_archive_collision",
                    {
                        "surface_id": surface_id,
                        "archive_path": str(target),
                        "expected_bytes": expected_bytes,
                        "expected_sha256": expected_sha256,
                    },
                )
        else:
            shutil.copyfile(source_path, target)
        if (
            target.stat().st_size != expected_bytes
            or scoreboard_checkpoint_sha256(target) != expected_sha256
        ):
            raise ScoreboardSurfaceCheckpointRegistryBuildError(
                "scoreboard_surface_checkpoint_archive_mismatch",
                {
                    "surface_id": surface_id,
                    "source_path": str(source_path),
                    "archive_path": str(target),
                },
            )

        native_receipt = {
            "accepted": True,
            "backend_id": save_result.get("backend_id"),
            "checkpoint": {
                "status": "saved",
                "path": str(source_path),
                "size": int(expected_bytes),
                "sha256": expected_sha256,
                "date_raw": int(before["date_raw"]),
                "strategy": checkpoint.get("strategy"),
            },
            "materialization": deepcopy(save_result.get("materialization")),
        }
        entry = {
            "surface_id": surface_id,
            "player_character_id": int(before["player_character_id"]),
            "owner_character_id": int(query_contract["owner_character_id"]),
            "date_raw": int(before["date_raw"]),
            "checkpoint": {
                "path": str(target.resolve()),
                "bytes": int(expected_bytes),
                "sha256": expected_sha256,
                "save_lineage_id": self.seed_lineage_id,
            },
            "source_snapshot_binding": before,
            "post_save_snapshot_binding": after,
            "source_query": deepcopy(dict(source_query)),
            "native_save_receipt": native_receipt,
            "capture_checks": {
                "event_free_paused_product_state": True,
                "modal_closed": True,
                "pages_closed": True,
                "surface_entry_visible": True,
                "surface_acl_observed": True,
                "save_binding_preserved": True,
                "action_ack_used_as_state_evidence": False,
            },
        }
        self._entries.append(entry)
        return deepcopy(entry)

    def finalize(self) -> dict[str, object]:
        observed = tuple(row["surface_id"] for row in self._entries)
        if observed != SCOREBOARD_REQUIRED_SURFACES:
            raise ScoreboardSurfaceCheckpointRegistryBuildError(
                "scoreboard_surface_registry_incomplete",
                {
                    "required_surfaces": list(SCOREBOARD_REQUIRED_SURFACES),
                    "observed_surfaces": list(observed),
                    "next_required_surface": self.next_required_surface,
                },
            )
        return {
            "schema_version": SCOREBOARD_SURFACE_REGISTRY_SCHEMA_VERSION,
            "registry_kind": SCOREBOARD_SURFACE_REGISTRY_KIND,
            "result": "GREEN",
            "evidence_class": "real_ck3",
            "state_origin": "product-checkpoint",
            "fixture_used": False,
            "ocr_used": False,
            "coordinates_used": False,
            "console_used": False,
            "generic_character_rebind_used": False,
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
            raise ScoreboardSurfaceCheckpointRegistryBuildError(
                "scoreboard_surface_registry_already_exists",
                {"registry_path": str(target)},
            ) from error
        return registry


def capture_current_zhongguo_scoreboard_surface_v1(
    service: ScoreboardSurfaceService,
    builder: ScoreboardSurfaceCheckpointRegistryBuilder,
    surface_id: str,
) -> dict[str, object]:
    """Capture the current real surface through query -> save -> re-observe."""

    before_snapshot = service.snapshot()
    try:
        before = scoreboard_surface_snapshot_binding(before_snapshot)
        nonce = f"zg361.scoreboard.capture.{surface_id}"
        source_query = service.query_zhongguo_scoreboard_state_v1(
            nonce,
            expected_revision=int(before["revision"]),
        )
        query_contract = validate_scoreboard_surface_query(
            source_query,
            surface_id=surface_id,
            expected_player_character_id=int(before["player_character_id"]),
            expected_date_raw=int(before["date_raw"]),
        )
        after_query_snapshot = service.snapshot()
        after_query = scoreboard_surface_snapshot_binding(after_query_snapshot)
        if not (
            _same_runtime_binding(before, after_query)
            and after_query.get("snapshot_id") == before.get("snapshot_id")
            and after_query.get("revision") == before.get("revision")
            and after_query.get("native_revision") == before.get("native_revision")
        ):
            raise ScoreboardSurfaceCheckpointRegistryBuildError(
                "scoreboard_surface_query_crossed_binding",
                {"before": before, "after_query": after_query},
            )
        save = getattr(service, "save_checkpoint", None)
        if not callable(save):
            raise ScoreboardSurfaceCheckpointRegistryBuildError(
                "scoreboard_surface_save_provider_missing",
                {"surface_id": surface_id},
            )
        native_save_result = save(expected_revision=int(before["revision"]))
        post_save_snapshot = service.snapshot()
        entry = builder.record(
            surface_id,
            source_snapshot=before_snapshot,
            source_query=source_query,
            native_save_result=native_save_result,
            post_save_snapshot=post_save_snapshot,
        )
    except ScoreboardSurfaceCheckpointRegistryBuildError:
        raise
    except ScoreboardSurfaceCheckpointError as error:
        raise ScoreboardSurfaceCheckpointRegistryBuildError(
            "scoreboard_surface_capture_observation_invalid",
            {"surface_id": surface_id, "upstream": error.evidence},
        ) from error
    except Exception as error:
        raise ScoreboardSurfaceCheckpointRegistryBuildError(
            "scoreboard_surface_capture_failed",
            {
                "surface_id": surface_id,
                "error_type": type(error).__name__,
                "message": str(error),
            },
        ) from error
    return {
        "schema_version": 1,
        "result": "GREEN",
        "evidence_class": "real_ck3",
        "surface_id": surface_id,
        "provider_observed": True,
        "event_free": True,
        "modal_page_acl_observed": True,
        "query_contract": query_contract,
        "checkpoint": deepcopy(entry["checkpoint"]),
        "next_required_surface": builder.next_required_surface,
        "action_ack_used_as_state_evidence": False,
        "fixture_used": False,
        "ocr_used": False,
        "coordinates_used": False,
        "console_used": False,
        "generic_character_rebind_used": False,
    }


__all__ = [
    "ScoreboardSurfaceCheckpointRegistryBuildError",
    "ScoreboardSurfaceCheckpointRegistryBuilder",
    "capture_current_zhongguo_scoreboard_surface_v1",
]
