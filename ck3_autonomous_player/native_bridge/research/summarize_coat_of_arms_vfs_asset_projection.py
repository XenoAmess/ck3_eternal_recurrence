#!/usr/bin/env python3
"""Create a compact, hash-bound receipt from a live VFS projection report."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


SOURCE_PATHS = (
    "ck3_autonomous_player/native_bridge/research/"
    "run_frontend_gui_route_v1_live_acceptance.py",
    "ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py",
    "ck3_autonomous_player/src/xar_autoplayer/coat_of_arms_vfs_resolution.py",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _mapping(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} is not an object")
    return value


def _list(value: object, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{label} is not an array")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    report_path = args.report.resolve()
    repository = args.repository.resolve()
    raw = report_path.read_bytes()
    report = _mapping(json.loads(raw.decode("utf-8")), "report")
    sequence = _mapping(report.get("sequence"), "sequence")
    mount_run = _mapping(
        sequence.get("vfs_mount_order_diagnostics"), "mount diagnostics"
    )
    observer = _mapping(mount_run.get("observer"), "mount observer")
    projection_run = _mapping(
        sequence.get("vfs_asset_projections"), "asset projections"
    )
    requested_paths = _list(
        projection_run.get("requested_paths"), "requested paths"
    )
    projection_rows = _list(
        projection_run.get("projections"), "projection rows"
    )

    queries: list[dict[str, object]] = []
    for index, row_value in enumerate(projection_rows):
        row = _mapping(row_value, f"projection row {index}")
        projection = _mapping(row.get("projection"), f"projection {index}")
        winner = _mapping(projection.get("winner"), f"winner {index}")
        provenance = _mapping(
            projection.get("provenance"), f"provenance {index}"
        )
        candidates = _list(projection.get("candidates"), f"candidates {index}")
        queries.append(
            {
                "logical_path": projection.get("logical_path"),
                "status": projection.get("status"),
                "mount_count": projection.get("mount_count"),
                "candidate_count": projection.get("candidate_count"),
                "candidate_mount_ordinals": [
                    _mapping(value, "candidate").get("mount_ordinal")
                    for value in candidates
                ],
                "winner": {
                    "mount_ordinal": winner.get("mount_ordinal"),
                    "source_kind": winner.get("source_kind"),
                    "source_path": winner.get("source_path"),
                    "content_kind": winner.get("content_kind"),
                    "asset_bytes": winner.get("asset_bytes"),
                    "asset_sha256": winner.get("asset_sha256"),
                    "dds": winner.get("dds"),
                },
                "mount_receipt_sha256": provenance.get(
                    "mount_receipt_sha256"
                ),
                "claim_scope": provenance.get("claim_scope"),
                "engine_resolver_called": provenance.get(
                    "engine_resolver_called"
                ),
                "resource_registration_observed": provenance.get(
                    "resource_registration_observed"
                ),
                "replace_path_applied": provenance.get("replace_path_applied"),
                "definition_merge_applied": provenance.get(
                    "definition_merge_applied"
                ),
                "checks": row.get("checks"),
                "ok": row.get("ok"),
            }
        )

    source_files = []
    for relative in SOURCE_PATHS:
        path = repository / Path(*relative.split("/"))
        source_files.append(
            {
                "path": relative,
                "bytes": path.stat().st_size,
                "sha256": _sha256(path),
            }
        )

    mount_receipts = {
        value.get("mount_receipt_sha256") for value in queries
    }
    call_summary = _mapping(sequence.get("call_summary"), "call summary")
    last_call = _mapping(call_summary.get("last_call"), "last call")
    checks = {
        "report_green": report.get("ok") is True,
        "steam_offline": _mapping(report.get("steam"), "steam").get("offline")
        is True,
        "cleanup_proven": _mapping(
            report.get("cleanup"), "cleanup"
        ).get("cleanup_proven")
        is True,
        "mount_observer_complete": (
            mount_run.get("ok") is True
            and observer.get("installed") is True
            and observer.get("failure_flags") == 0
            and observer.get("failure_count") == 0
            and observer.get("slot_overwrite_count") == 0
            and observer.get("call_count")
            == observer.get("success_count")
            == observer.get("row_count")
            == len(_list(observer.get("rows"), "mount rows"))
        ),
        "all_requested_paths_returned_once": (
            len(requested_paths) == len(set(requested_paths)) == len(queries)
            and [value.get("logical_path") for value in queries]
            == requested_paths
        ),
        "all_mcp_projections_green": projection_run.get("ok") is True
        and all(value.get("ok") is True for value in queries),
        "all_winners_hash_bound": all(
            isinstance(
                _mapping(value.get("winner"), "winner").get("asset_sha256"),
                str,
            )
            and len(
                _mapping(value.get("winner"), "winner")["asset_sha256"]
            )
            == 64
            for value in queries
        ),
        "single_live_mount_receipt": len(mount_receipts) == 1
        and None not in mount_receipts,
        "claim_boundary_preserved": all(
            value.get("claim_scope")
            == "direct_dds_path_winner_projection_only"
            and value.get("engine_resolver_called") is False
            and value.get("resource_registration_observed") is False
            and value.get("replace_path_applied") is False
            and value.get("definition_merge_applied") is False
            for value in queries
        ),
    }
    output = {
        "schema": "ck3-coat-of-arms-vfs-asset-projection-native-summary-v1",
        "schema_version": 1,
        "report": {
            "path": report_path.name,
            "bytes": len(raw),
            "sha256": _sha256(report_path),
            "created_at": report.get("created_at"),
            "repository_head_before_worktree_patch": report.get(
                "repository_head"
            ),
            "elapsed_seconds": report.get("elapsed_seconds"),
        },
        "source_files": source_files,
        "binary": report.get("binary"),
        "mount_observer": {
            "kind": mount_run.get("observer_kind"),
            "call_count": observer.get("call_count"),
            "success_count": observer.get("success_count"),
            "failure_count": observer.get("failure_count"),
            "slot_overwrite_count": observer.get("slot_overwrite_count"),
            "row_count": observer.get("row_count"),
        },
        "call_summary": {
            "total": call_summary.get("total"),
            "omitted": call_summary.get("omitted"),
            "last_call": {
                "tool": last_call.get("tool"),
                "elapsed_seconds": last_call.get("elapsed_seconds"),
                "is_error": last_call.get("is_error"),
            },
        },
        "queries": queries,
        "evidence_boundary": (
            "Official MCP invoked a deterministic direct-DDS projection over "
            "the complete exact-build live mount receipt and inspected source "
            "bytes. CK3's internal resolver/resource registry was not called; "
            "replace_path and definition merging remain outside this claim."
        ),
        "checks": checks,
        "ok": all(checks.values()),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0 if output["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
