#!/usr/bin/env python3
"""Promote one Phase2 cut only after a byte-bound real source review.

The command never records a human decision.  It consumes an existing signed
source-review receipt, a GREEN eight-span intake report, and the matching draft
ledger, then writes a new ready project config plus an audit receipt.  In
``--validate-only`` mode it performs the same reads/checks and writes nothing.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Mapping, Sequence


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_TOOLS = REPOSITORY_ROOT / "tools"
if str(REPOSITORY_TOOLS) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_TOOLS))

from zhongguo_phase2_promo_cuts import cut_for_config_name  # noqa: E402

from validate_phase2_authoring_claims import (  # noqa: E402
    materialize_ledger,
    project_cue_input,
    validate_ledger,
)


SOURCE_REVIEW_KIND = "zg361_phase2_source_review_receipt"
PROMOTION_KIND = "zg361_phase2_reviewed_authoring_promotion"
_SHA256 = re.compile(r"^[0-9A-Fa-f]{64}$")
_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class PromotionError(RuntimeError):
    """Reviewed authoring cannot be promoted without inventing evidence."""


def _read_json(path: Path, label: str) -> dict[str, object]:
    resolved = path.expanduser().resolve()
    try:
        value = json.loads(resolved.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PromotionError(f"could not read {label}: {resolved}: {exc}") from exc
    if not isinstance(value, dict):
        raise PromotionError(f"{label} root must be an object")
    return value


def _record(path: Path) -> dict[str, object]:
    resolved = path.expanduser().resolve()
    digest = hashlib.sha256()
    with resolved.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return {
        "path": str(resolved),
        "bytes": resolved.stat().st_size,
        "sha256": digest.hexdigest().upper(),
    }


def _bound(value: object, expected: Mapping[str, object], label: str) -> None:
    if not isinstance(value, Mapping):
        raise PromotionError(f"source review does not bind {label}")
    if value.get("bytes") != expected.get("bytes"):
        raise PromotionError(f"source review {label} byte count drifted")
    declared = value.get("sha256")
    if (
        not isinstance(declared, str)
        or _SHA256.fullmatch(declared) is None
        or declared.upper() != expected.get("sha256")
    ):
        raise PromotionError(f"source review {label} SHA-256 drifted")


def _timestamp(value: object) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None


def _segment_id(chapter_id: str, cue_id: str) -> str:
    raw = f"{chapter_id}.{cue_id}"
    if len(raw) <= 96 and _IDENTIFIER.fullmatch(raw) is not None:
        return raw
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    stem = re.sub(r"[^A-Za-z0-9._-]", "-", raw).strip("._-")[:72]
    result = f"{stem or 'segment'}-{digest}"
    if len(result) > 96 or _IDENTIFIER.fullmatch(result) is None:
        raise PromotionError(
            f"could not derive narration artifact id for {chapter_id!r}/{cue_id!r}"
        )
    return result


def _validate_review(
    receipt: Mapping[str, object],
    *,
    cut_id: str,
    project_record: Mapping[str, object],
    ledger_record: Mapping[str, object],
    intake_record: Mapping[str, object],
    cue_ids: Sequence[str],
) -> None:
    if receipt.get("schema_version") != 1 or receipt.get("kind") != SOURCE_REVIEW_KIND:
        raise PromotionError("source review receipt header is invalid")
    if receipt.get("result") != "GREEN" or receipt.get("decision") != "approved":
        raise PromotionError("source review receipt is not an explicit GREEN approval")
    if receipt.get("cut_id") != cut_id:
        raise PromotionError("source review receipt belongs to another editorial cut")
    if receipt.get("playback_speed") != 1 or receipt.get("full_duration_reviewed") is not True:
        raise PromotionError("source review must attest complete 1x playback")
    if not isinstance(receipt.get("reviewer"), str) or not str(receipt["reviewer"]).strip():
        raise PromotionError("source review must name its human reviewer")
    if not _timestamp(receipt.get("reviewed_at")):
        raise PromotionError("source review reviewed_at must include a timezone")
    if receipt.get("all_claims_supported") is not True:
        raise PromotionError("source review did not approve every promoted claim")
    if receipt.get("approved_cue_ids") != list(cue_ids):
        raise PromotionError("source review approved cue list is incomplete or reordered")
    if receipt.get("template_only") is not False or receipt.get("is_signoff") is not True:
        raise PromotionError("source review must be an instantiated human sign-off")
    _bound(receipt.get("project_config"), project_record, "project_config")
    _bound(receipt.get("authoring_ledger"), ledger_record, "authoring_ledger")
    _bound(receipt.get("footage_intake"), intake_record, "footage_intake")


def build_promoted_project(
    *,
    project_config: Path,
    authoring_ledger: Path,
    footage_intake_report: Path,
    source_review_receipt: Path,
) -> tuple[dict[str, object], dict[str, object]]:
    project_path = project_config.expanduser().resolve()
    ledger_path = authoring_ledger.expanduser().resolve()
    cut = cut_for_config_name(project_path.name)
    if ledger_path.name != cut.authoring_ledger_name:
        raise PromotionError(
            f"cut {cut.cut_id!r} requires ledger {cut.authoring_ledger_name!r}"
        )
    ledger_errors = validate_ledger(ledger_path)
    if ledger_errors:
        raise PromotionError("authoring ledger is RED: " + "; ".join(ledger_errors))
    project = _read_json(project_path, "project config")
    ledger_errors = []
    ledger = materialize_ledger(ledger_path, ledger_errors)
    if ledger_errors:
        raise PromotionError("could not materialize authoring ledger: " + "; ".join(ledger_errors))
    intake = _read_json(footage_intake_report, "footage intake report")
    if (
        intake.get("schema_version") != 1
        or intake.get("kind") != "zg361_phase2_footage_intake"
        or intake.get("result") != "GREEN"
        or intake.get("reason_code") is not None
    ):
        raise PromotionError("footage intake report is not a GREEN eight-span receipt")
    chapters = ledger.get("chapters")
    project_chapters = project.get("chapters")
    if not isinstance(chapters, list) or not isinstance(project_chapters, list):
        raise PromotionError("project and authoring ledger must contain chapter arrays")
    ledger_by_id = {
        str(row.get("id")): row for row in chapters if isinstance(row, Mapping)
    }
    project_ids = [
        str(row.get("id")) for row in project_chapters if isinstance(row, Mapping)
    ]
    if len(project_ids) != len(project_chapters) or project_ids != list(ledger_by_id):
        raise PromotionError("project and authoring ledger chapter order differ")
    cues = [
        ledger_by_id[chapter_id].get("cue") for chapter_id in project_ids
    ]
    if not all(isinstance(cue, dict) for cue in cues):
        raise PromotionError("authoring ledger lacks one cue per chapter")
    cue_ids = [str(cue["id"]) for cue in cues if isinstance(cue, dict)]
    receipt = _read_json(source_review_receipt, "source review receipt")
    project_record = _record(project_path)
    ledger_record = _record(ledger_path)
    intake_record = _record(footage_intake_report)
    _validate_review(
        receipt,
        cut_id=cut.cut_id,
        project_record=project_record,
        ledger_record=ledger_record,
        intake_record=intake_record,
        cue_ids=cue_ids,
    )

    promoted_chapters: list[dict[str, object]] = []
    for raw in project_chapters:
        if not isinstance(raw, Mapping):
            raise PromotionError("project chapter is not an object")
        chapter = dict(raw)
        chapter_id = str(chapter["id"])
        cue = ledger_by_id[chapter_id]["cue"]
        assert isinstance(cue, dict)
        cue_input = project_cue_input(cue)
        cue_id = str(cue_input["id"])
        chapter["state"] = "ready"
        chapter["cues"] = [cue_input]
        chapter["artifact_ids"] = [
            f"narration.{_segment_id(chapter_id, cue_id)}"
        ]
        promoted_chapters.append(chapter)
    promoted = dict(project)
    promoted["chapters"] = promoted_chapters
    audit = {
        "schema_version": 1,
        "kind": PROMOTION_KIND,
        "result": "GREEN",
        "cut_id": cut.cut_id,
        "project_config_input": project_record,
        "authoring_ledger": ledger_record,
        "footage_intake": intake_record,
        "source_review_receipt": _record(source_review_receipt),
        "reviewer": receipt["reviewer"],
        "reviewed_at": receipt["reviewed_at"],
        "approved_cue_ids": cue_ids,
        "chapters_promoted": len(promoted_chapters),
        "execution_attestation": {
            "ck3_started": False,
            "tts_started": False,
            "ffmpeg_started": False,
            "media_generated": False,
        },
    }
    return promoted, audit


def _exclusive_json(path: Path, value: Mapping[str, object]) -> dict[str, object]:
    resolved = path.expanduser().resolve()
    if not resolved.parent.is_dir():
        raise PromotionError(f"output parent does not exist: {resolved.parent}")
    data = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    try:
        with resolved.open("xb") as output:
            output.write(data)
    except FileExistsError as exc:
        raise PromotionError(f"refusing to overwrite output: {resolved}") from exc
    return _record(resolved)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--project-config", type=Path, required=True)
    result.add_argument("--authoring-ledger", type=Path, required=True)
    result.add_argument("--footage-intake-report", type=Path, required=True)
    result.add_argument("--source-review-receipt", type=Path, required=True)
    result.add_argument("--output-project", type=Path, required=True)
    result.add_argument("--output-receipt", type=Path, required=True)
    result.add_argument("--validate-only", action="store_true")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        promoted, audit = build_promoted_project(
            project_config=args.project_config,
            authoring_ledger=args.authoring_ledger,
            footage_intake_report=args.footage_intake_report,
            source_review_receipt=args.source_review_receipt,
        )
        if args.output_project.name != args.project_config.name:
            raise PromotionError(
                "promoted project must retain the canonical cut config basename"
            )
        if args.output_project.resolve() == args.project_config.resolve():
            raise PromotionError("promotion must write a new project config, not overwrite its draft")
        if args.output_project.resolve() == args.output_receipt.resolve():
            raise PromotionError("project and promotion receipt outputs must be distinct")
        if args.validate_only:
            print(
                json.dumps(
                    {
                        "result": "GREEN",
                        "cut_id": audit["cut_id"],
                        "chapters": len(promoted["chapters"]),
                        "writes_performed": False,
                    },
                    ensure_ascii=False,
                )
            )
            return 0
        project_parent = args.output_project.expanduser().resolve().parent
        receipt_parent = args.output_receipt.expanduser().resolve().parent
        if project_parent != receipt_parent:
            raise PromotionError("project and promotion receipt must share one attempt directory")
        if not project_parent.is_dir():
            raise PromotionError(
                f"promotion attempt directory does not exist: {project_parent}"
            )
        project_record = _exclusive_json(args.output_project, promoted)
        audit = {**audit, "promoted_project": project_record}
        receipt_record = _exclusive_json(args.output_receipt, audit)
    except Exception as exc:
        print(f"PHASE2 AUTHORING PROMOTION: RED\nERROR: {exc}", file=sys.stderr)
        return 2
    print("PHASE2 AUTHORING PROMOTION: GREEN")
    print(f"PROJECT: {project_record['path']} sha256={project_record['sha256']}")
    print(f"RECEIPT: {receipt_record['path']} sha256={receipt_record['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
