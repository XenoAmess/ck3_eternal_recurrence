"""Command-line interface for the reusable promo project core."""

from __future__ import annotations

import argparse
import importlib
import json
import re
import sys
from pathlib import Path
from typing import Sequence

from . import __version__
from .errors import PromoToolchainError
from .export_commands import handle_export_command
from .operations import (
    DEFAULT_RUN_ID,
    DEFAULT_RUN_MANIFEST,
    PROJECT_CONFIG_NAME,
    initialize_project,
    preserve_artifact,
    record_signoff,
    start_run,
)
from .pipeline import PipelineComposer, PipelineResult
from .pipeline_commands import (
    CommandOutcome,
    handle_audit,
    handle_build,
    handle_plan,
)
from .project import load_document, validate_profile
from .registry import ComponentRegistry
from .review_commands import run_review_command


def _default_project_id(directory: Path) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", directory.name).strip(".-")
    return (slug or "promo-project")[:128]


def _load_composer(specification: str) -> PipelineComposer:
    module_name, separator, attribute_path = specification.partition(":")
    if not separator or not module_name or not attribute_path:
        raise PromoToolchainError(
            "composer must use MODULE:ATTRIBUTE syntax, for example my_project.promo:compose"
        )
    try:
        value: object = importlib.import_module(module_name)
        for name in attribute_path.split("."):
            if not name:
                raise AttributeError(attribute_path)
            value = getattr(value, name)
    except Exception as exc:
        raise PromoToolchainError(
            f"could not load composer {specification!r}: {exc}"
        ) from exc
    if not callable(value):
        raise PromoToolchainError(
            f"composer {specification!r} resolved to non-callable {type(value).__name__}"
        )
    return value


def _pipeline_result_payload(result: PipelineResult | None) -> dict[str, object] | None:
    if result is None:
        return None
    payload: dict[str, object] = {
        "status": result.status,
        "validate_only": result.validate_only,
        "workdir": str(result.workdir),
        "signoff_recorded": result.signoff_recorded,
        "phases": [item.to_mapping() for item in result.phases],
        "artifacts": [item.to_audit_mapping() for item in result.artifacts],
        "audit_record": None if result.audit_record is None else result.audit_record.to_mapping(),
    }
    if result.failure is not None:
        payload["failure"] = {
            "phase": result.failure.phase,
            "exception_type": result.failure.exception_type,
            "message": result.failure.message,
            "stdout": result.failure.stdout,
            "stderr": result.failure.stderr,
            "partial_paths": [str(path) for path in result.failure.partial_paths],
            "stdout_paths": [str(path) for path in result.failure.stdout_paths],
            "stderr_paths": [str(path) for path in result.failure.stderr_paths],
            "retained_paths": [str(path) for path in result.failure.retained_paths],
        }
    else:
        payload["failure"] = None
    return payload


def _command_outcome_payload(outcome: CommandOutcome) -> dict[str, object]:
    return {
        "command": outcome.command,
        "exit_status": outcome.exit_status,
        "status": outcome.status,
        "document": str(outcome.document_path),
        "config": None if outcome.config_path is None else str(outcome.config_path),
        "run": None if outcome.run_path is None else str(outcome.run_path),
        "adapter": outcome.adapter_id,
        "preset": outcome.preset_id,
        "workdir": None if outcome.workdir is None else str(outcome.workdir),
        "pipeline": _pipeline_result_payload(outcome.pipeline_result),
        "preserved_artifacts": [item.to_dict() for item in outcome.preserved_artifacts],
        "audit_report": None if outcome.audit_report_path is None else str(outcome.audit_report_path),
        "audit": None if outcome.audit_report is None else dict(outcome.audit_report),
        "failure": (
            None
            if outcome.failure is None
            else {
                "exception_type": outcome.failure.exception_type,
                "message": outcome.failure.message,
            }
        ),
    }


def _print_command_outcome(outcome: CommandOutcome) -> int:
    stream = sys.stdout if outcome.succeeded else sys.stderr
    print(
        json.dumps(
            _command_outcome_payload(outcome),
            ensure_ascii=False,
            sort_keys=True,
        ),
        file=stream,
    )
    return outcome.exit_status


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="xar-promo",
        description="Create, verify, and preserve reusable promotional-video project metadata.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init", help="create a ProjectConfig and its first bound run without overwriting files")
    init.add_argument("project_directory", type=Path)
    init.add_argument("--project-id", help="portable stable id; defaults to the directory name")
    init.add_argument("--title", help="human title; defaults to the directory name")
    init.add_argument("--adapter", default="generic", help="project adapter id (default: generic)")
    init.add_argument("--preset", default="default", help="style preset id (default: default)")
    init.add_argument("--run-id", default=DEFAULT_RUN_ID, help=f"initial run id (default: {DEFAULT_RUN_ID})")
    init.add_argument("--narration-locale", default="und", help="primary narration locale (default: und)")
    init.add_argument(
        "--subtitle-locale",
        action="append",
        dest="subtitle_locales",
        help="required subtitle locale; repeat for multiple locales (default: narration locale)",
    )

    start = commands.add_parser("start-run", help="create another run bound to the current exact ProjectConfig bytes")
    start.add_argument("project_config", type=Path, nargs="?", default=Path(PROJECT_CONFIG_NAME))
    start.add_argument("--run-id", required=True)
    start.add_argument("--run-directory", type=Path, help="directory for run-manifest.json (default: <project>/runs/<run-id>)")

    validate = commands.add_parser("validate", help="validate a ProjectConfig, RunManifest, or legacy showcase v1 manifest")
    validate.add_argument("document", type=Path, nargs="?", default=Path(PROJECT_CONFIG_NAME))
    validate.add_argument("--profile", choices=("authoring", "release"), default="authoring")
    validate.add_argument("--structure-only", action="store_true", help="skip referenced-file byte and SHA checks")
    validate.add_argument("--json", action="store_true", dest="json_output", help="write the GREEN result as JSON")

    preserve = commands.add_parser("preserve", help="copy a file to immutable content-addressed storage and append its run record")
    preserve.add_argument("source", type=Path)
    preserve.add_argument("--run-manifest", type=Path, default=DEFAULT_RUN_MANIFEST)
    preserve.add_argument("--artifact-id", required=True)
    preserve.add_argument("--collection", choices=("raw", "derived"), required=True)
    preserve.add_argument("--role", required=True, help="semantic role such as capture, audio, subtitle, or deliverable")
    preserve.add_argument("--label")
    preserve.add_argument("--media-type")

    signoff = commands.add_parser("signoff", help="append an explicit human decision bound to preserved artifact bytes")
    signoff.add_argument("--run-manifest", type=Path, default=DEFAULT_RUN_MANIFEST)
    signoff.add_argument("--artifact-id", required=True)
    signoff.add_argument("--reviewer", required=True)
    signoff.add_argument("--decision", choices=("approved", "rejected"), required=True)
    signoff.add_argument("--note")
    signoff.add_argument("--reviewed-at", help="explicit timestamp; defaults to current UTC")

    plan = commands.add_parser(
        "plan",
        help="compose and validate a pipeline plan without invoking providers or writing",
    )
    plan.add_argument("document", type=Path, help="native ProjectConfig or RunManifest")
    plan.add_argument("--workdir", type=Path, required=True, help="fresh attempt path to validate without creating")
    plan.add_argument("--composer", required=True, help="project PipelineComposer as MODULE:ATTRIBUTE")
    plan.add_argument(
        "--validate-only",
        action="store_true",
        help="explicitly request the command's always-read-only validation mode",
    )

    build = commands.add_parser(
        "build",
        help="run a composed pipeline and preserve success or failure material in its run",
    )
    build.add_argument("run_manifest", type=Path, help="native RunManifest")
    build.add_argument("--workdir", type=Path, required=True, help="fresh attempt directory")
    build.add_argument("--composer", required=True, help="project PipelineComposer as MODULE:ATTRIBUTE")
    build.add_argument("--offline-tts", action="store_true")
    build.add_argument("--max-tts-attempts", type=int, default=3)
    build.add_argument("--retry-backoff-seconds", type=float, default=1.0)

    audit = commands.add_parser(
        "audit",
        help="write and preserve an automated audit without creating human approval",
    )
    audit.add_argument("run_manifest", type=Path, help="native RunManifest")
    audit.add_argument("--subject-artifact-id", required=True)
    audit.add_argument("--evidence-bundle", type=Path, required=True)
    audit.add_argument("--report", type=Path, required=True)
    audit.add_argument("--report-artifact-id", required=True)
    audit.add_argument("--created-at-utc")

    review = commands.add_parser(
        "review",
        help="plan or create a pending human-review package without recording sign-off",
    )
    review.add_argument("deliverable", type=Path)
    review.add_argument("--storyboard", type=Path, required=True, help="storyboard timeline JSON")
    review.add_argument(
        "--probe",
        type=Path,
        required=True,
        help="retained xar-promo-bound-media-probe v1 envelope for the deliverable",
    )
    review.add_argument("--output-directory", type=Path, required=True)
    review.add_argument("--audit-directory", type=Path, required=True)
    review.add_argument("--ffmpeg", required=True, help="ffmpeg executable or path")
    review.add_argument("--working-directory", type=Path)
    review.add_argument(
        "--plan-only",
        action="store_true",
        help="validate inputs and print the frame plan without creating directories or files",
    )

    export = commands.add_parser(
        "export",
        help="validate or create an offline release bundle from an explicit policy",
    )
    export.add_argument("run_manifest", type=Path)
    export.add_argument("destination", type=Path)
    export.add_argument("--policy", type=Path, required=True, help="strict release-export policy JSON")
    export_mode = export.add_mutually_exclusive_group()
    export_mode.add_argument(
        "--dry-run",
        action="store_true",
        help="run the complete preflight without creating the destination",
    )
    export_mode.add_argument(
        "--validate-only",
        action="store_true",
        help="validate policy, release state, and selected sources without writing",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "init":
            root = args.project_directory.expanduser().resolve()
            config, run = initialize_project(
                root,
                project_id=args.project_id or _default_project_id(root),
                title=args.title or root.name or "Promo project",
                narration_locale=args.narration_locale,
                subtitle_locales=args.subtitle_locales or [args.narration_locale],
                adapter=args.adapter,
                preset=args.preset,
                run_id=args.run_id,
            )
            print(f"INITIALIZED: config={config}; run={run}")
            return 0
        if args.command == "start-run":
            run = start_run(args.project_config, run_id=args.run_id, run_directory=args.run_directory)
            print(f"STARTED: run={run}")
            return 0
        if args.command == "validate":
            loaded = load_document(args.document, check_files=not args.structure_only)
            validate_profile(loaded, args.profile)
            result = {
                "status": "GREEN",
                "profile": args.profile,
                "source_format": loaded.source_format,
                "document": str(loaded.path),
                "chapters": loaded.chapter_count,
                "artifacts": loaded.artifact_count,
                "files_checked": not args.structure_only,
            }
            if args.json_output:
                print(json.dumps(result, ensure_ascii=False, sort_keys=True))
            else:
                print(
                    "GREEN: "
                    f"format={loaded.source_format}; profile={args.profile}; "
                    f"chapters={loaded.chapter_count}; artifacts={loaded.artifact_count}; "
                    f"files_checked={str(not args.structure_only).lower()}; document={loaded.path}"
                )
            return 0
        if args.command == "preserve":
            record = preserve_artifact(
                args.run_manifest,
                args.source,
                artifact_id=args.artifact_id,
                collection=args.collection,
                role=args.role,
                label=args.label,
                media_type=args.media_type,
            )
            print(f"PRESERVED: id={record.artifact_id}; bytes={record.bytes}; sha256={record.sha256}; path={record.path}")
            return 0
        if args.command == "signoff":
            record = record_signoff(
                args.run_manifest,
                artifact_id=args.artifact_id,
                reviewer=args.reviewer,
                decision=args.decision,
                note=args.note,
                reviewed_at=args.reviewed_at,
            )
            print(f"RECORDED: id={record.signoff_id}; artifact={record.artifact_id}; decision={record.decision}; reviewer={record.reviewer}")
            return 0
        if args.command == "plan":
            # ``plan`` is always validate-only; the explicit flag exists so
            # automation can state the no-write contract at the call site.
            outcome = handle_plan(
                args.document,
                workdir=args.workdir,
                registry=ComponentRegistry(),
                composer=_load_composer(args.composer),
            )
            return _print_command_outcome(outcome)
        if args.command == "build":
            outcome = handle_build(
                args.run_manifest,
                workdir=args.workdir,
                registry=ComponentRegistry(),
                composer=_load_composer(args.composer),
                offline_tts=args.offline_tts,
                max_tts_attempts=args.max_tts_attempts,
                retry_backoff_seconds=args.retry_backoff_seconds,
            )
            return _print_command_outcome(outcome)
        if args.command == "audit":
            outcome = handle_audit(
                args.run_manifest,
                registry=ComponentRegistry(),
                subject_artifact_id=args.subject_artifact_id,
                evidence_bundle_path=args.evidence_bundle,
                report_path=args.report,
                report_artifact_id=args.report_artifact_id,
                created_at_utc=args.created_at_utc,
            )
            return _print_command_outcome(outcome)
        if args.command == "review":
            result = run_review_command(
                ffmpeg=args.ffmpeg,
                deliverable_path=args.deliverable,
                storyboard_path=args.storyboard,
                probe_path=args.probe,
                output_directory=args.output_directory,
                audit_directory=args.audit_directory,
                plan_only=args.plan_only,
                working_directory=args.working_directory,
            )
            print(json.dumps(result.to_dict(), ensure_ascii=False, sort_keys=True))
            return 0
        if args.command == "export":
            result = handle_export_command(
                args.run_manifest,
                args.destination,
                args.policy,
                dry_run=args.dry_run,
                validate_only=args.validate_only,
            )
            stream = sys.stdout if result.exit_code == 0 else sys.stderr
            print(
                json.dumps(result.to_dict(), ensure_ascii=False, sort_keys=True),
                file=stream,
            )
            return result.exit_code
        raise AssertionError(f"unhandled command {args.command!r}")
    except PromoToolchainError as exc:
        print(f"RED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
