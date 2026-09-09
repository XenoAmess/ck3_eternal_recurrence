"""Bind human-review boundary frames into a xar-promo audit bundle.

The generic review command extracts both sides of every editorial boundary.
For automated audit we keep the artifact first/final frames and exact
boundary-after frames, then bind those immutable PNG bytes to a deterministic
evidence-plan v2. This command never grants human approval.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from decimal import Decimal
from pathlib import Path
from typing import Any

from xar_promo.evidence import (
    bind_external_artifact,
    write_evidence_bundle_v2,
    write_sampling_plan_v2,
)


SELECTED_ROLES = frozenset({"artifact-first", "boundary-after", "artifact-final"})


class AuditEvidenceError(ValueError):
    """The review package cannot support a complete audit bundle."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as error:
        raise AuditEvidenceError(f"could not read review package {path}: {error}") from error
    if not isinstance(value, dict):
        raise AuditEvidenceError("review package root must be an object")
    return value


def _verified_selected_frames(
    package: dict[str, Any], package_path: Path
) -> list[dict[str, Any]]:
    frames = package.get("frames")
    if not isinstance(frames, list):
        raise AuditEvidenceError("review package frames must be an array")
    selected: list[dict[str, Any]] = []
    for index, raw in enumerate(frames):
        if not isinstance(raw, dict):
            raise AuditEvidenceError(f"review frame {index} must be an object")
        roles = raw.get("roles")
        if not isinstance(roles, list) or not SELECTED_ROLES.intersection(roles):
            continue
        try:
            timestamp = f"{Decimal(str(raw['timestamp_seconds'])):.6f}"
            relative = Path(str(raw["path"]))
            expected_bytes = int(raw["bytes"])
            expected_sha256 = str(raw["sha256"]).upper()
        except (KeyError, ValueError, TypeError) as error:
            raise AuditEvidenceError(f"review frame {index} metadata is invalid") from error
        path = (package_path.parent / relative).resolve()
        if not path.is_file():
            raise AuditEvidenceError(f"review frame is missing: {path}")
        if path.stat().st_size != expected_bytes or _sha256(path) != expected_sha256:
            raise AuditEvidenceError(f"review frame bytes drifted: {path}")
        selected.append({"timestamp": timestamp, "path": path})
    selected.sort(key=lambda row: Decimal(row["timestamp"]))
    timestamps = [row["timestamp"] for row in selected]
    if len(selected) < 2:
        raise AuditEvidenceError("review package must provide at least first and final frames")
    if len(timestamps) != len(set(timestamps)):
        raise AuditEvidenceError("selected review frames contain duplicate timestamps")
    if timestamps[0] != "0.000000":
        raise AuditEvidenceError("selected review frames do not begin at zero")
    return selected


def build_audit_evidence(
    *,
    project_root: Path,
    deliverable: Path,
    review_package: Path,
    output_directory: Path,
    xar_promo_version: str,
) -> dict[str, Any]:
    """Create one append-only evidence attempt and return its summary."""

    root = project_root.resolve()
    deliverable = deliverable.resolve()
    review_package = review_package.resolve()
    output_directory = output_directory.resolve()
    try:
        output_directory.relative_to(root)
    except ValueError as error:
        raise AuditEvidenceError("output directory must be inside project root") from error
    if output_directory.exists():
        raise AuditEvidenceError(f"refusing to overwrite audit evidence: {output_directory}")
    output_directory.mkdir(parents=True)

    package = _load_object(review_package)
    if package.get("state") != "pending-human-review":
        raise AuditEvidenceError("review package is not pending human review")
    if package.get("approval_granted") is not False or package.get("is_signoff") is not False:
        raise AuditEvidenceError("review package must not contain approval or signoff")
    artifact = package.get("artifact")
    if not isinstance(artifact, dict):
        raise AuditEvidenceError("review package artifact must be an object")
    if not deliverable.is_file():
        raise AuditEvidenceError(f"deliverable is missing: {deliverable}")
    expected_bytes = int(artifact.get("bytes", -1))
    expected_sha256 = str(artifact.get("sha256", "")).upper()
    if deliverable.stat().st_size != expected_bytes or _sha256(deliverable) != expected_sha256:
        raise AuditEvidenceError("deliverable bytes do not match the review package")

    frames = _verified_selected_frames(package, review_package)
    retained_frames = output_directory / "frames"
    retained_frames.mkdir()
    for index, row in enumerate(frames, start=1):
        retained = retained_frames / f"frame-{index:06d}.png"
        shutil.copyfile(row["path"], retained)
        if _sha256(retained) != _sha256(row["path"]):
            raise AuditEvidenceError(f"retained review frame bytes drifted: {retained}")
        row["path"] = retained
    source_producer = {
        "adapter_id": "rmtm-96s-zh-v1",
        "tool": "rmtm_promo.composer",
        "tool_version": "0.1.0",
        "operation": "compose-final",
        "execution": "external",
    }
    frame_producer = {
        "adapter_id": "rmtm-review-v1",
        "tool": "xar-promo",
        "tool_version": xar_promo_version,
        "operation": "review-frame-extraction",
        "execution": "external",
    }
    source = bind_external_artifact(
        deliverable,
        project_root=root,
        artifact_id="reclaim-promo-final-a01",
        collection="derived",
        role="deliverable",
        label="Reclaim the Motherland 96-second candidate",
        media_type="video/mp4",
        producer=source_producer,
    )
    chapters = [
        {
            "id": f"audit-segment-{index:04d}",
            "kind": "video",
            "source": source,
            "start_seconds": left["timestamp"],
            "end_seconds": right["timestamp"],
        }
        for index, (left, right) in enumerate(zip(frames, frames[1:]), start=1)
    ]
    plan_path = output_directory / "evidence-plan.json"
    plan = write_sampling_plan_v2(
        plan_path,
        chapters,
        project_root=root,
        interval_seconds=9999,
        required_roles=["frame"],
        external_producers={"frame": frame_producer},
    )
    by_timestamp = {row["timestamp"]: row["path"] for row in frames}
    submissions = []
    for sample in plan["samples"]:
        timestamp = sample["timestamp_seconds"]
        path = by_timestamp.get(timestamp)
        if path is None:
            raise AuditEvidenceError(f"no review frame for planned timestamp {timestamp}")
        submissions.append(
            {
                "sample_id": sample["id"],
                "role": "frame",
                "path": path,
                "media_type": "image/png",
                "producer": frame_producer,
            }
        )
    bundle_path = output_directory / "evidence-bundle.json"
    bundle = write_evidence_bundle_v2(
        bundle_path,
        project_root=root,
        plan_path=plan_path,
        submissions=submissions,
    )
    summary = {
        "kind": "rmtm-promo-audit-evidence-result",
        "approval_granted": False,
        "is_signoff": False,
        "deliverable_sha256": expected_sha256,
        "sample_count": len(plan["samples"]),
        "entry_count": len(bundle["entries"]),
        "plan": plan_path.relative_to(root).as_posix(),
        "bundle": bundle_path.relative_to(root).as_posix(),
    }
    summary_path = output_directory / "result.json"
    with summary_path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--deliverable", type=Path, required=True)
    parser.add_argument("--review-package", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--xar-promo-version", default="0.2.1")
    args = parser.parse_args()
    result = build_audit_evidence(
        project_root=args.project_root,
        deliverable=args.deliverable,
        review_package=args.review_package,
        output_directory=args.output_directory,
        xar_promo_version=args.xar_promo_version,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
