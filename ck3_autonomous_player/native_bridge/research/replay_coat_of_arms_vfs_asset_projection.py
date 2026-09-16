#!/usr/bin/env python3
"""Replay direct-DDS winner projections from a frozen live MCP report."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from xar_autoplayer.coat_of_arms_vfs_resolution import (
    project_coat_of_arms_vfs_asset_winner_v1,
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _diagnostics(report: dict[str, Any]) -> dict[str, object]:
    sequence = report.get("sequence")
    calls = sequence.get("calls") if isinstance(sequence, dict) else None
    if not isinstance(calls, list):
        raise ValueError("report has no MCP call sequence")
    matches = [
        call
        for call in calls
        if isinstance(call, dict)
        and call.get("tool") == "ck3_get_bridge_diagnostics"
    ]
    if not matches:
        raise ValueError("report has no explicit bridge diagnostics call")
    structured = matches[-1].get("structured_content")
    if not isinstance(structured, dict):
        raise ValueError("final bridge diagnostics call has no structured content")
    nested = structured.get("diagnostics")
    value = nested if isinstance(nested, dict) else structured
    if not isinstance(value, dict):
        raise ValueError("final bridge diagnostics payload is malformed")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--game-directory", type=Path, required=True)
    parser.add_argument(
        "--logical-path", action="append", required=True, dest="logical_paths"
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    report_path = args.report.resolve()
    raw = report_path.read_bytes()
    report = json.loads(raw.decode("utf-8"))
    diagnostics = _diagnostics(report)
    results = [
        project_coat_of_arms_vfs_asset_winner_v1(
            diagnostics,
            str(args.game_directory.resolve()),
            logical_path,
        )
        for logical_path in args.logical_paths
    ]
    output = {
        "schema": "ck3-coat-of-arms-vfs-asset-projection-replay-v1",
        "source_report": {
            "path": report_path.name,
            "bytes": len(raw),
            "sha256": _sha256(report_path),
            "repository_head": report.get("repository_head"),
        },
        "queries": results,
        "checks": {
            "all_queries_have_winners": all(
                result.get("winner") is not None for result in results
            ),
            "all_queries_bind_live_mounts": all(
                isinstance(result.get("provenance"), dict)
                and result["provenance"].get("mount_order_observed") is True
                for result in results
            ),
            "no_query_claims_engine_resolver": all(
                isinstance(result.get("provenance"), dict)
                and result["provenance"].get("engine_resolver_called") is False
                for result in results
            ),
        },
    }
    output["ok"] = all(output["checks"].values())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0 if output["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
