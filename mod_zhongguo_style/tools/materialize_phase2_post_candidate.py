#!/usr/bin/env python3
"""Materialize one Phase2 candidate's audit/review/export inputs.

The command is deliberately post-candidate.  It consumes the immutable
deliverable already preserved in a native promo run and creates a byte-bound
ffprobe envelope, an exact editorial storyboard, a pending human-review
package, a frame-only evidence bundle, and an explicit release export policy.
It never records a review decision, signs the run, exports, publishes, invokes
TTS, or changes the candidate bytes.

``--validate-only`` checks bindings and planned paths without invoking FFmpeg
or ffprobe and without creating any file or directory.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from decimal import Decimal
from pathlib import Path
from typing import Callable, Mapping, Sequence


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_TOOLS = REPOSITORY_ROOT / "tools"
if str(REPOSITORY_TOOLS) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_TOOLS))

from promo_toolchain_loader import ensure_promo_toolchain  # noqa: E402

ensure_promo_toolchain()

import xar_promo  # noqa: E402
from xar_promo.evidence import (  # noqa: E402
    bind_external_artifact,
    write_evidence_bundle_v2,
    write_sampling_plan_v2,
)
from xar_promo.export_commands import (  # noqa: E402
    POLICY_KIND,
    load_export_policy,
)
from xar_promo.media import (  # noqa: E402
    MediaProbe,
    probe_media,
    require_streams,
    write_bound_media_probe,
)
from xar_promo.process import CommandResult, run_command  # noqa: E402
from xar_promo.project import load_document, sha256_file  # noqa: E402
from xar_promo.review_commands import (  # noqa: E402
    ReviewCommandResult,
    run_review_command,
)
from xar_promo.presets.zhongguo_361_phase2 import (  # noqa: E402
    load_phase2_project_config,
)

from build_phase2_promo_video import (  # noqa: E402
    MEDIA_PREFLIGHT_ARTIFACT_ID,
    Phase2PromoBuildError,
    _require_ready_authoring,
    select_cut,
)
from zhongguo_phase2_promo_cuts import Phase2PromoCut  # noqa: E402


KIND = "zg361_phase2_post_candidate_materialization"
ProbeLoader = Callable[..., MediaProbe]
ReviewRunner = Callable[..., ReviewCommandResult]


class PostCandidateError(RuntimeError):
    """The exact post-candidate inputs could not be materialized."""


def _file_record(path: Path) -> dict[str, object]:
    resolved = path.expanduser().resolve()
    return {
        "path": str(resolved),
        "bytes": resolved.stat().st_size,
        "sha256": sha256_file(resolved).upper(),
    }


def _write_new_json(path: Path, value: Mapping[str, object]) -> dict[str, object]:
    resolved = path.expanduser().resolve()
    resolved.parent.mkdir(parents=True, exist_ok=True)
    payload = (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    try:
        with resolved.open("xb") as output:
            output.write(payload)
            output.flush()
            os.fsync(output.fileno())
    except FileExistsError as exc:
        raise PostCandidateError(f"refusing to overwrite post-candidate file: {resolved}") from exc
    return _file_record(resolved)


def _inside(path: Path, root: Path, label: str) -> Path:
    resolved = path.expanduser().resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise PostCandidateError(f"{label} must stay inside candidate run root {root}") from exc
    return resolved


def _artifact_path(run_root: Path, record, label: str) -> Path:
    return _inside(run_root / Path(record.path), run_root, label)


def _load_inputs(
    *,
    cut_id: str,
    project_config: Path,
    run_manifest: Path,
    output_root: Path,
    export_directory: Path,
) -> dict[str, object]:
    config_path = project_config.expanduser().resolve()
    run_path = run_manifest.expanduser().resolve()
    cut = select_cut(config_path, cut_id)
    config = load_phase2_project_config(config_path)
    _require_ready_authoring(config)
    loaded = load_document(run_path, check_files=True)
    if loaded.run is None:
        raise PostCandidateError("post-candidate materialization requires a native run manifest")
    if loaded.run.run_id != cut.default_run_id:
        raise PostCandidateError(
            f"cut {cut.cut_id!r} requires run id {cut.default_run_id!r}"
        )
    if (
        loaded.run.project_config.bytes != config_path.stat().st_size
        or loaded.run.project_config.sha256.upper() != sha256_file(config_path).upper()
    ):
        raise PostCandidateError("candidate run is bound to different project config bytes")
    subjects = [
        record
        for record in loaded.run.artifacts
        if record.artifact_id == cut.deliverable_artifact_id
        and record.role == "deliverable"
    ]
    if len(subjects) != 1:
        raise PostCandidateError("candidate run must contain exactly one cut deliverable")
    run_root = run_path.parent.resolve()
    subject = subjects[0]
    subject_path = _artifact_path(run_root, subject, "candidate deliverable")
    material_root = output_root.expanduser().resolve()
    if material_root.parent != run_root:
        raise PostCandidateError("post-candidate output root must be a direct child of the run root")
    if material_root.exists():
        raise PostCandidateError(f"post-candidate output root already exists: {material_root}")
    export_root = export_directory.expanduser().resolve()
    if export_root.exists():
        raise PostCandidateError(f"release export directory already exists: {export_root}")
    artifact_by_id = {record.artifact_id: record for record in loaded.run.artifacts}
    narration_paths: dict[str, tuple[Path, ...]] = {}
    for chapter in config.chapters:
        narration_ids = tuple(
            artifact_id
            for artifact_id in chapter.artifact_ids
            if artifact_id.startswith("narration.")
        )
        if len(narration_ids) != len(chapter.cues) or not narration_ids:
            raise PostCandidateError(
                f"chapter {chapter.chapter_id!r} lacks one preserved narration per cue"
            )
        try:
            records = tuple(artifact_by_id[artifact_id] for artifact_id in narration_ids)
        except KeyError as exc:
            raise PostCandidateError(
                f"candidate run lacks narration artifact {exc.args[0]!r}"
            ) from exc
        narration_paths[chapter.chapter_id] = tuple(
            _artifact_path(run_root, record, "candidate narration") for record in records
        )
    media_preflights = [
        record
        for record in loaded.run.artifacts
        if record.artifact_id == MEDIA_PREFLIGHT_ARTIFACT_ID
        and record.role == "preflight"
    ]
    if len(media_preflights) != 1:
        raise PostCandidateError("candidate run lacks its unique media-preflight artifact")
    media_preflight_path = _artifact_path(
        run_root, media_preflights[0], "media preflight"
    )
    try:
        media_preflight = json.loads(media_preflight_path.read_text(encoding="utf-8-sig"))
        ffmpeg_version = media_preflight["media"]["ffmpeg_version"]
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise PostCandidateError("retained media preflight lacks FFmpeg version") from exc
    if not isinstance(ffmpeg_version, str) or not ffmpeg_version.strip():
        raise PostCandidateError("retained media preflight FFmpeg version is invalid")
    return {
        "cut": cut,
        "config": config,
        "run_path": run_path,
        "run_root": run_root,
        "subject": subject,
        "subject_path": subject_path,
        "narration_paths": narration_paths,
        "media_preflight_path": media_preflight_path,
        "ffmpeg_version": ffmpeg_version,
        "output_root": material_root,
        "export_directory": export_root,
    }


def _probe(
    loader: ProbeLoader,
    ffprobe: str,
    path: Path,
    audit_directory: Path,
    command_runner: Callable[..., CommandResult],
) -> MediaProbe:
    return loader(
        ffprobe,
        path,
        audit_directory=audit_directory,
        command_runner=command_runner,
    )


def _storyboard(
    *,
    cut: Phase2PromoCut,
    config,
    narration_durations: Mapping[str, float],
    deliverable_duration: float,
) -> dict[str, object]:
    canonical = tuple(chapter.chapter_id for chapter in config.chapters)
    if (
        len(cut.editorial_chapter_order) != len(canonical)
        or set(cut.editorial_chapter_order) != set(canonical)
    ):
        raise PostCandidateError(
            f"cut {cut.cut_id!r} editorial order is not an exact chapter permutation"
        )
    reprises_by_boundary: dict[str, list[object]] = {}
    for reprise in cut.reprises:
        reprises_by_boundary.setdefault(reprise.after_chapter_id, []).append(reprise)
    rows: list[tuple[str, float, list[float]]] = []
    reprise_sequence = 0
    for chapter_id in cut.editorial_chapter_order:
        duration = narration_durations[chapter_id]
        rows.append((chapter_id, duration, []))
        for reprise in reprises_by_boundary.get(chapter_id, []):
            reprise_sequence += 1
            rows.append(
                (
                    f"{reprise.source_chapter_id}.reprise{reprise_sequence}",
                    float(reprise.duration_seconds),
                    [],
                )
            )
    nominal = sum(duration for _, duration, _ in rows)
    if nominal <= 0 or deliverable_duration <= 0:
        raise PostCandidateError("candidate or storyboard duration is not positive")
    scale = Decimal(str(deliverable_duration)) / Decimal(str(nominal))
    cursor = Decimal(0)
    chapters: list[dict[str, object]] = []
    for index, (chapter_id, duration, boundaries) in enumerate(rows):
        start = cursor
        end = (
            Decimal(str(deliverable_duration))
            if index == len(rows) - 1
            else cursor + Decimal(str(duration)) * scale
        )
        chapters.append(
            {
                "id": chapter_id,
                "start_seconds": float(round(start, 6)),
                "end_seconds": float(round(end, 6)),
                "boundary_seconds": boundaries,
            }
        )
        cursor = end
    return {
        "chapters": chapters,
        "boundary_seconds": [row["end_seconds"] for row in chapters[:-1]],
    }


def _command_plan(
    *,
    cut: Phase2PromoCut,
    run_path: Path,
    output_root: Path,
    export_directory: Path,
) -> dict[str, object]:
    cli = [sys.executable, "-m", "xar_promo.cli"]
    evidence_bundle = output_root / "evidence-bundle.json"
    audit_report = output_root / "automated-audit.json"
    export_policy = output_root / "release-export-policy.json"
    return {
        "automated_audit": cli
        + [
            "audit",
            str(run_path),
            "--subject-artifact-id",
            cut.deliverable_artifact_id,
            "--evidence-bundle",
            str(evidence_bundle),
            "--report",
            str(audit_report),
            "--report-artifact-id",
            f"{cut.cut_id}-automated-audit",
        ],
        "signoff": {
            "fixed_argv": cli
            + [
                "signoff",
                "--run-manifest",
                str(run_path),
                "--artifact-id",
                cut.deliverable_artifact_id,
            ],
            "required_human_arguments": ["--reviewer", "--decision"],
            "allowed_decisions": ["approved", "rejected"],
            "automatic_execution_allowed": False,
        },
        "export_validate_only": cli
        + [
            "export",
            str(run_path),
            str(export_directory),
            "--policy",
            str(export_policy),
            "--validate-only",
        ],
        "export": cli
        + [
            "export",
            str(run_path),
            str(export_directory),
            "--policy",
            str(export_policy),
        ],
        "publish": None,
    }


def _planned_paths(output_root: Path, export_directory: Path) -> dict[str, str]:
    return {
        "bound_probe": str(output_root / "bound-ffprobe.json"),
        "storyboard": str(output_root / "final-storyboard.json"),
        "review_directory": str(output_root / "pending-review"),
        "review_audit_directory": str(output_root / "review-command-audit"),
        "review_package": str(output_root / "pending-review" / "review-package.json"),
        "review_template": str(output_root / "pending-review" / "review-template.json"),
        "claims_and_source_review_receipt": str(
            output_root / "human-reviews" / "claims-and-source-pass.json"
        ),
        "final_candidate_review_receipt": str(
            output_root / "human-reviews" / "final-candidate-pass.json"
        ),
        "evidence_plan": str(output_root / "evidence-plan.json"),
        "evidence_bundle": str(output_root / "evidence-bundle.json"),
        "automated_audit_report": str(output_root / "automated-audit.json"),
        "release_export_policy": str(output_root / "release-export-policy.json"),
        "materialization_receipt": str(output_root / "materialization-receipt.json"),
        "export_directory": str(export_directory),
    }


def validate_plan(args: argparse.Namespace) -> dict[str, object]:
    bound = _load_inputs(
        cut_id=args.cut,
        project_config=args.project_config,
        run_manifest=args.run_manifest,
        output_root=args.output_root,
        export_directory=args.export_directory,
    )
    cut = bound["cut"]
    if not isinstance(cut, Phase2PromoCut):
        raise PostCandidateError("resolved cut has an invalid type")
    return {
        "schema_version": 1,
        "kind": KIND,
        "result": "GREEN",
        "status": "validated-no-write",
        "cut_id": cut.cut_id,
        "candidate": _file_record(bound["subject_path"]),
        "planned_paths": _planned_paths(
            bound["output_root"], bound["export_directory"]
        ),
        "commands": _command_plan(
            cut=cut,
            run_path=bound["run_path"],
            output_root=bound["output_root"],
            export_directory=bound["export_directory"],
        ),
        "execution_attestation": {
            "validate_only": True,
            "ffprobe_started": False,
            "ffmpeg_started": False,
            "tts_started": False,
            "approval_recorded": False,
            "exported": False,
            "published": False,
            "writes_performed": False,
        },
    }


def materialize(
    args: argparse.Namespace,
    *,
    probe_loader: ProbeLoader = probe_media,
    review_runner: ReviewRunner = run_review_command,
    command_runner: Callable[..., CommandResult] = run_command,
) -> dict[str, object]:
    bound = _load_inputs(
        cut_id=args.cut,
        project_config=args.project_config,
        run_manifest=args.run_manifest,
        output_root=args.output_root,
        export_directory=args.export_directory,
    )
    cut = bound["cut"]
    config = bound["config"]
    output_root = bound["output_root"]
    subject_path = bound["subject_path"]
    if not isinstance(cut, Phase2PromoCut):
        raise PostCandidateError("resolved cut has an invalid type")
    if not isinstance(output_root, Path) or not isinstance(subject_path, Path):
        raise PostCandidateError("resolved post-candidate paths have invalid types")

    final_probe = require_streams(
        _probe(
            probe_loader,
            args.ffprobe,
            subject_path,
            output_root / "probe-command-audit" / "deliverable",
            command_runner,
        ),
        video=True,
        audio=True,
    )
    write_bound_media_probe(
        output_root / "bound-ffprobe.json",
        media_path=subject_path,
        probe=final_probe,
    )
    narration_durations: dict[str, float] = {}
    narration_paths = bound["narration_paths"]
    for chapter in config.chapters:
        total = 0.0
        for index, path in enumerate(narration_paths[chapter.chapter_id], start=1):
            inspected = require_streams(
                _probe(
                    probe_loader,
                    args.ffprobe,
                    path,
                    output_root
                    / "probe-command-audit"
                    / "narration"
                    / chapter.chapter_id
                    / f"cue-{index:02d}",
                    command_runner,
                ),
                audio=True,
            )
            total += inspected.require_duration()
        narration_durations[chapter.chapter_id] = total
    storyboard = _storyboard(
        cut=cut,
        config=config,
        narration_durations=narration_durations,
        deliverable_duration=final_probe.require_duration(),
    )
    storyboard_path = output_root / "final-storyboard.json"
    _write_new_json(storyboard_path, storyboard)

    review = review_runner(
        ffmpeg=args.ffmpeg,
        deliverable_path=subject_path,
        storyboard_path=storyboard_path,
        probe_path=output_root / "bound-ffprobe.json",
        output_directory=output_root / "pending-review",
        audit_directory=output_root / "review-command-audit",
        plan_only=False,
        command_runner=command_runner,
    )
    if review.plan_only or review.state != "pending-human-review":
        raise PostCandidateError("review materializer did not remain pending human review")

    candidate_producer = {
        "adapter_id": "zhongguo-phase2-project",
        "tool": "xar_promo.pipeline",
        "tool_version": xar_promo.__version__,
        "operation": "compose-candidate",
        "execution": "external",
    }
    frame_producer = {
        "adapter_id": "xar-promo-review",
        "tool": str(args.ffmpeg),
        "tool_version": bound["ffmpeg_version"],
        "operation": "extract-review-frame",
        "execution": "external",
    }
    source = bind_external_artifact(
        subject_path,
        project_root=bound["run_root"],
        artifact_id=cut.deliverable_artifact_id,
        collection="derived",
        role="deliverable",
        label=f"{cut.cut_id} immutable candidate",
        media_type="video/mp4",
        producer=candidate_producer,
    )
    evidence_chapters = [
        {
            "id": frame.frame_id,
            "kind": "still",
            "source": source,
            "start_seconds": str(frame.timestamp_seconds),
            "end_seconds": str(frame.timestamp_seconds),
        }
        for frame in review.frames
    ]
    evidence_plan_path = output_root / "evidence-plan.json"
    evidence_plan = write_sampling_plan_v2(
        evidence_plan_path,
        evidence_chapters,
        project_root=bound["run_root"],
        interval_seconds=1,
        required_roles=["frame"],
        external_producers={"frame": frame_producer},
    )
    frames_by_timestamp = {
        f"{Decimal(str(frame.timestamp_seconds)):.6f}": frame.final_output
        for frame in review.frames
    }
    if len(frames_by_timestamp) != len(review.frames):
        raise PostCandidateError("review frame timestamps are not unique")
    submissions = []
    for sample in evidence_plan["samples"]:
        timestamp = sample["timestamp_seconds"]
        frame_path = frames_by_timestamp.get(timestamp)
        if frame_path is None:
            raise PostCandidateError(
                f"review package lacks evidence frame at {timestamp} seconds"
            )
        submissions.append(
            {
                "sample_id": sample["id"],
                "role": "frame",
                "path": frame_path,
                "media_type": "image/png",
                "producer": frame_producer,
            }
        )
    evidence_bundle_path = output_root / "evidence-bundle.json"
    write_evidence_bundle_v2(
        evidence_bundle_path,
        project_root=bound["run_root"],
        plan_path=evidence_plan_path,
        submissions=submissions,
    )

    export_policy = {
        "format_version": 1,
        "kind": POLICY_KIND,
        "items": [
            {
                "category": "deliverable",
                "destination": f"video/{cut.deliverable_relative_path.name}",
                "source_kind": "artifact",
                "artifact_id": cut.deliverable_artifact_id,
                "expected_role": "deliverable",
            },
            {
                "category": "audit",
                "destination": f"audit/{cut.cut_id}-automated-audit.json",
                "source_kind": "artifact",
                "artifact_id": f"{cut.cut_id}-automated-audit",
                "expected_role": "audit",
            },
            {
                "category": "project-config",
                "destination": "metadata/project-config.json",
                "source_kind": "project-config-snapshot",
            },
        ],
    }
    export_policy_path = output_root / "release-export-policy.json"
    _write_new_json(export_policy_path, export_policy)
    load_export_policy(export_policy_path)

    planned_paths = _planned_paths(output_root, bound["export_directory"])
    commands = _command_plan(
        cut=cut,
        run_path=bound["run_path"],
        output_root=output_root,
        export_directory=bound["export_directory"],
    )
    receipt = {
        "schema_version": 1,
        "kind": KIND,
        "result": "GREEN",
        "status": "pending-human-review",
        "cut_id": cut.cut_id,
        "candidate": _file_record(subject_path),
        "run_manifest_before_audit": _file_record(bound["run_path"]),
        "project_config": _file_record(args.project_config),
        "media_preflight": _file_record(bound["media_preflight_path"]),
        "bound_probe": _file_record(output_root / "bound-ffprobe.json"),
        "storyboard": _file_record(storyboard_path),
        "review_package": _file_record(Path(planned_paths["review_package"])),
        "review_template": _file_record(Path(planned_paths["review_template"])),
        "evidence_plan": _file_record(evidence_plan_path),
        "evidence_bundle": _file_record(evidence_bundle_path),
        "release_export_policy": _file_record(export_policy_path),
        "planned_paths": planned_paths,
        "commands": commands,
        "human_gates": {
            "review_receipts_required": [
                planned_paths["claims_and_source_review_receipt"],
                planned_paths["final_candidate_review_receipt"],
            ],
            "distinct_named_reviewers_required": True,
            "full_duration_playback_speed": 1,
            "signoff_required": True,
            "automatic_approval_allowed": False,
        },
        "execution_attestation": {
            "validate_only": False,
            "ffprobe_started": True,
            "ffmpeg_review_frames_started": True,
            "tts_started": False,
            "candidate_generated": False,
            "candidate_mutated": False,
            "approval_recorded": False,
            "exported": False,
            "published": False,
        },
    }
    _write_new_json(output_root / "materialization-receipt.json", receipt)
    return receipt


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--cut", required=True)
    result.add_argument("--project-config", type=Path, required=True)
    result.add_argument("--run-manifest", type=Path, required=True)
    result.add_argument("--output-root", type=Path, required=True)
    result.add_argument("--export-directory", type=Path, required=True)
    result.add_argument("--ffmpeg", default="ffmpeg")
    result.add_argument("--ffprobe", default="ffprobe")
    result.add_argument("--validate-only", action="store_true")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        payload = validate_plan(args) if args.validate_only else materialize(args)
    except Exception as exc:
        print(f"PHASE2 POST-CANDIDATE MATERIALIZATION: RED\nERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
