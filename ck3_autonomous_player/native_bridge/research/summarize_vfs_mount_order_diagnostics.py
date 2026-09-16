#!/usr/bin/env python3
"""Create a compact, reviewable receipt from a mount-order live report."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _private_observers(call: object) -> dict[str, Any]:
    if not isinstance(call, dict):
        return {}
    structured = call.get("structured_content")
    if not isinstance(structured, dict):
        return {}
    diagnostics = structured.get("diagnostics")
    observers = (
        diagnostics.get("private_observers")
        if isinstance(diagnostics, dict)
        else None
    )
    if not isinstance(observers, dict):
        observers = structured.get("private_observers")
    return observers if isinstance(observers, dict) else {}


def _paths(observer: object, *, rows_key: str, nested: bool) -> list[str]:
    if not isinstance(observer, dict):
        return []
    rows = observer.get(rows_key)
    if not isinstance(rows, list):
        return []
    result: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        value = row.get("path")
        if nested and isinstance(value, dict):
            value = value.get("preview")
        if isinstance(value, str):
            result.append(value)
    return result


def summarize(report_path: Path) -> dict[str, object]:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    sequence = report.get("sequence")
    sequence = sequence if isinstance(sequence, dict) else {}
    mount = sequence.get("vfs_mount_order_diagnostics")
    mount = mount if isinstance(mount, dict) else {}
    calls = sequence.get("calls")
    calls = calls if isinstance(calls, list) else []
    diagnostic_calls = [
        call
        for call in calls
        if isinstance(call, dict)
        and call.get("tool") == "ck3_get_bridge_diagnostics"
    ]
    final_observers = _private_observers(
        diagnostic_calls[-1] if diagnostic_calls else None
    )
    direct = final_observers.get("physfs_mounted_data_observer_v1")
    direct = direct if isinstance(direct, dict) else {}
    lifecycle = final_observers.get("vfs_mount_lifecycle_observer_v1")
    lifecycle = lifecycle if isinstance(lifecycle, dict) else {}
    return {
        "schema": "xar.ck3.coa.vfs-mount-order-live-summary.v1",
        "report": {
            # Keep the checked-in receipt relocatable. The report and summary
            # live in the same immutable run directory.
            "path": report_path.name,
            "bytes": report_path.stat().st_size,
            "sha256": _sha256(report_path),
            "repository_head": report.get("repository_head"),
            "created_at": report.get("created_at"),
        },
        "ok": report.get("ok") is True and mount.get("ok") is True,
        "steam_offline": (
            isinstance(report.get("steam"), dict)
            and report["steam"].get("offline") is True
        ),
        "elapsed_seconds": report.get("elapsed_seconds"),
        "cleanup": report.get("cleanup"),
        "observer_kind": mount.get("observer_kind"),
        "poll_count": mount.get("poll_count"),
        "expected_fragment_indices": mount.get("expected_fragment_indices"),
        "checks": mount.get("checks"),
        "physfs_mounted_data_observer_v1": {
            "installed": direct.get("installed"),
            "failure_flags": direct.get("failure_flags"),
            "call_count": direct.get("call_count"),
            "success_count": direct.get("success_count"),
            "failure_count": direct.get("failure_count"),
            "slot_overwrite_count": direct.get("slot_overwrite_count"),
            "row_count": direct.get("row_count"),
            "paths": _paths(direct, rows_key="rows", nested=False),
        },
        "vfs_mount_lifecycle_observer_v1": {
            "installed": lifecycle.get("installed"),
            "failure_flags": lifecycle.get("failure_flags"),
            "publisher_entry_count": lifecycle.get("publisher_entry_count"),
            "publisher_return_count": lifecycle.get("publisher_return_count"),
            "publisher_success_count": lifecycle.get("publisher_success_count"),
            "publisher_failure_count": lifecycle.get("publisher_failure_count"),
            "publisher_slot_count": lifecycle.get("publisher_slot_count"),
            "paths": _paths(lifecycle, rows_key="publishers", nested=True),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    summary = summarize(args.report.resolve())
    encoded = json.dumps(summary, ensure_ascii=False, indent=2) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
