#!/usr/bin/env python3
"""Append-only import of selected ZhongGuo 361 acceptance screenshots.

The promo project deliberately distinguishes a clean promotional recording from
an acceptance fixture.  This importer preserves that distinction: it copies
only named evidence files from one immutable GREEN run into a new promo import
directory, records both source and copied hashes, and never crops, overwrites,
or mutates the original run.  The imported stills can therefore be used for a
draft promo while the manifest continues to mark the remaining clean-recording
work explicitly.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Sequence


RUN_FILES = (
    "cell/06_calibration_event.png",
    "cell/07_result_summary.png",
    "cell/08_scoreboard_panel_raw.png",
    "cell/09_jingcha_mandate_event.png",
    "cell/09_jingcha_planner.png",
    "cell/10_superior_result.png",
    "report.json",
    "evidence-index.json",
)


class ImportError(RuntimeError):
    """A requested acceptance import cannot be created safely."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_report(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ImportError(f"cannot read acceptance report: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ImportError(f"acceptance report must be a JSON object: {path}")
    return value


def import_run(*, artifact: Path, destination: Path) -> Path:
    artifact = artifact.expanduser().resolve()
    destination = destination.expanduser().resolve()
    if not artifact.is_dir():
        raise ImportError(f"artifact run directory does not exist: {artifact}")
    if destination.exists():
        raise ImportError(
            "destination already exists; choose a new import directory so prior "
            f"promo material is preserved: {destination}"
        )
    report_path = artifact / "report.json"
    report = _read_report(report_path)
    if report.get("result") != "GREEN":
        raise ImportError(
            f"acceptance report is not GREEN: {report_path} ({report.get('result')!r})"
        )
    cell = report.get("cell")
    if not isinstance(cell, dict) or cell.get("result") != "GREEN":
        raise ImportError("acceptance cell report is not GREEN")
    destination.mkdir(parents=True)
    rows: list[dict[str, Any]] = []
    for relative in RUN_FILES:
        source = artifact / relative
        if not source.is_file():
            raise ImportError(f"required acceptance artifact is missing: {source}")
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        source_hash = _sha256(source)
        target_hash = _sha256(target)
        if source_hash != target_hash:
            raise ImportError(f"copy hash mismatch for {relative}")
        rows.append(
            {
                "relative_path": relative.replace("\\", "/"),
                "source_sha256": source_hash,
                "copied_sha256": target_hash,
                "bytes": target.stat().st_size,
            }
        )
    index = {
        "format_version": 1,
        "kind": "zg361_acceptance_still_import",
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source_artifact": str(artifact),
        "source_result": report.get("result"),
        "source_cell_result": cell.get("result"),
        "classification": "fixture-live acceptance stills; not a clean promotional recording",
        "loading_excluded": True,
        "files": rows,
    }
    index_path = destination / "import-index.json"
    index_path.write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"IMPORTED: {destination} ({len(rows)} files; fixture-live stills only)")
    return index_path


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--artifact", required=True, type=Path)
    result.add_argument("--destination", required=True, type=Path)
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        import_run(artifact=args.artifact, destination=args.destination)
    except ImportError as exc:
        print(f"RED: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
