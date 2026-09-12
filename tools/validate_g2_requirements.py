#!/usr/bin/env python3
"""Validate the fixed G2 milestone denominator and current work-package count."""

from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PATH = (
    ROOT / "docs" / "autonomous-agent-progress" / "g2-requirements-v1.json"
)
MILESTONE_KEYS = {
    "id",
    "name",
    "priority",
    "status",
    "latest_evidence",
    "planner_consumer",
    "visible_outcome",
    "open_blocker",
}
PACKAGE_KEYS = {"id", "name", "status", "latest_evidence"}


def validate(path: Path = DEFAULT_PATH) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise ValueError("G2 requirements schema_version must be 1")
    vocabulary = payload.get("status_vocabulary")
    if not isinstance(vocabulary, list) or not vocabulary:
        raise ValueError("status_vocabulary must be a nonempty list")
    allowed = set(vocabulary)

    milestones = payload.get("milestones")
    if not isinstance(milestones, list) or len(milestones) != 8:
        raise ValueError("G2 must keep exactly eight visible OODA milestones")
    _validate_rows(milestones, MILESTONE_KEYS, allowed, "milestone")
    denominator = payload.get("completion_denominator")
    if not isinstance(denominator, dict):
        raise ValueError("completion_denominator is missing")
    completed = sum(row["status"] == "complete" for row in milestones)
    if (
        denominator.get("kind") != "visible_ooda_milestones"
        or denominator.get("total") != len(milestones)
        or denominator.get("complete") != completed
        or denominator.get("progress_label") != f"{completed}/{len(milestones)}"
        or denominator.get("percent_reporting_allowed") is not False
    ):
        raise ValueError("G2 completion denominator drifted")

    work = payload.get("current_work_package")
    if not isinstance(work, dict):
        raise ValueError("current_work_package is missing")
    packages = work.get("packages")
    if not isinstance(packages, list) or not packages:
        raise ValueError("current work package has no subpackages")
    _validate_rows(packages, PACKAGE_KEYS, allowed, "subpackage")
    package_completed = sum(row["status"] == "complete" for row in packages)
    if (
        work.get("total_packages") != len(packages)
        or work.get("completed_packages") != package_completed
    ):
        raise ValueError("current work-package count drifted")

    return {
        "status": "GREEN",
        "g2_progress": denominator["progress_label"],
        "current_work_package": work.get("id"),
        "work_package_progress": f"{package_completed}/{len(packages)}",
    }


def _validate_rows(
    rows: list[object],
    required_keys: set[str],
    allowed_statuses: set[object],
    kind: str,
) -> None:
    identities: set[object] = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != required_keys:
            raise ValueError(f"{kind} keys drifted")
        if row["id"] in identities:
            raise ValueError(f"duplicate {kind} id {row['id']}")
        identities.add(row["id"])
        if row["status"] not in allowed_statuses:
            raise ValueError(f"{kind} {row['id']} uses an unknown status")
        for key in required_keys - {"status"}:
            value = row[key]
            if isinstance(value, str) and not value.strip():
                raise ValueError(f"{kind} {row['id']} has empty {key}")
        if kind == "milestone" and not isinstance(row["latest_evidence"], list):
            raise ValueError(f"milestone {row['id']} evidence must be a list")


def main() -> int:
    try:
        result = validate()
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"RED: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
