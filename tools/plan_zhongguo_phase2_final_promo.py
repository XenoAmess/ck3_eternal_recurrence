#!/usr/bin/env python3
"""Write a deterministic, no-media phase-two final-promo runbook.

The planner hashes inputs that already exist and emits commands for a later
production operator.  It never fetches Git, launches CK3, calls TTS, invokes
FFmpeg, or creates any candidate-media directory.  Missing capture footage is
always the first typed blocker: ``footage_pending``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

from zhongguo_phase2_capture_choreography import PHASE2_CAPTURE_SCENARIOS
from zhongguo_phase2_footage_intake import (
    final_promo_execution_dag,
    validate_footage_intake,
)


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ROOT / "mod_zhongguo_style" / "promo" / "phase2-promo-project.json"
DEFAULT_AUTHORING_LEDGER = (
    ROOT / "mod_zhongguo_style" / "promo" / "phase2-authoring-claims.json"
)
PHASE2_MOD_TOOLS = ROOT / "mod_zhongguo_style" / "tools"
if str(PHASE2_MOD_TOOLS) not in sys.path:
    sys.path.insert(0, str(PHASE2_MOD_TOOLS))

from validate_phase2_authoring_claims import validate_ledger  # noqa: E402

VOICE = "zh-CN-XiaoxiaoNeural"
EXPECTED_CHAPTERS = (
    "phase2_minimal_recap",
    *(scenario.span_id for scenario in PHASE2_CAPTURE_SCENARIOS),
    "phase2_finale",
)
class RunbookError(RuntimeError):
    pass


def _sha256(path: Path) -> dict[str, object]:
    digest = hashlib.sha256()
    try:
        size = path.stat().st_size
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as error:
        raise RunbookError(f"cannot bind {path}: {error}") from error
    return {"path": str(path.resolve()), "bytes": size, "sha256": digest.hexdigest().upper()}


def _json(path: Path) -> Mapping[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise RunbookError(f"cannot read JSON {path}: {error}") from error
    if not isinstance(value, Mapping):
        raise RunbookError(f"JSON root is not an object: {path}")
    return value


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        shell=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode:
        raise RunbookError((completed.stderr or completed.stdout).strip())
    return completed.stdout.strip()


def _file_input(path: Path | None) -> dict[str, object]:
    return {"present": path is not None and path.is_file(), "record": None if path is None or not path.is_file() else _sha256(path)}


def _project_gate(config_path: Path) -> tuple[dict[str, object], list[str]]:
    payload = _json(config_path)
    chapters = payload.get("chapters")
    rows = chapters if isinstance(chapters, list) else []
    ids = tuple(row.get("id") for row in rows if isinstance(row, Mapping))
    titles_bilingual = all(
        isinstance(row, Mapping)
        and isinstance(row.get("title"), Mapping)
        and all(isinstance(row["title"].get(locale), str) and row["title"][locale].strip() for locale in ("zh-CN", "en"))
        for row in rows
    )
    deliberately_unpromoted = all(
        isinstance(row, Mapping)
        and row.get("state") == "planned"
        and isinstance(row.get("cues"), list)
        and not row["cues"]
        and isinstance(row.get("artifact_ids"), list)
        and not row["artifact_ids"]
        for row in rows
    )
    checks = {
        "exact_ten_chapters": len(rows) == 10,
        "canonical_order": ids == EXPECTED_CHAPTERS,
        "two_generated_cards": len(rows) == 10
        and isinstance(rows[0], Mapping)
        and isinstance(rows[-1], Mapping)
        and rows[0].get("type") == "generated_card"
        and rows[-1].get("type") == "generated_card",
        "eight_canonical_clean_spans": len(rows) == 10 and all(isinstance(row, Mapping) and row.get("type") == "ck3_clean_span" for row in rows[1:-1]),
        "bilingual_claim_titles": titles_bilingual,
        "deliberately_unpromoted_before_footage": deliberately_unpromoted,
    }
    blockers = [] if all(checks.values()) else ["authoring_pending"]
    claims = [
        {
            "id": row.get("id"),
            "type": row.get("type"),
            "state": row.get("state"),
            "title": dict(row["title"]) if isinstance(row.get("title"), Mapping) else None,
        }
        for row in rows
        if isinstance(row, Mapping)
    ]
    return {
        "record": _sha256(config_path),
        "checks": checks,
        "chapter_ids": list(ids),
        "authoring_claims": claims,
    }, blockers


def _authoring_ledger_gate(path: Path) -> tuple[dict[str, object], list[str]]:
    ledger_path = path.expanduser().resolve()
    errors = validate_ledger(ledger_path)
    payload = _json(ledger_path) if ledger_path.is_file() else {}
    chapters = payload.get("chapters")
    rows = chapters if isinstance(chapters, list) else []
    ids = tuple(row.get("id") for row in rows if isinstance(row, Mapping))
    ready = not errors and ids == EXPECTED_CHAPTERS and len(rows) == 10
    return {
        "record": None if not ledger_path.is_file() else _sha256(ledger_path),
        "result": "GREEN" if ready else "RED",
        "status": payload.get("authoring_status"),
        "checks": {
            "validator_green": not errors,
            "exact_ten_claims": len(rows) == 10,
            "canonical_order": ids == EXPECTED_CHAPTERS,
            "chinese_first": isinstance(payload.get("language_policy"), Mapping)
            and payload["language_policy"].get("primary_narration") == "zh-CN",
            "simultaneous_zh_cn_en": isinstance(
                payload.get("language_policy"), Mapping
            )
            and payload["language_policy"].get("simultaneous_subtitles")
            == ["zh-CN", "en"],
            "xiaoxiao": isinstance(payload.get("language_policy"), Mapping)
            and payload["language_policy"].get("current_builder_voice") == VOICE,
            "draft_not_release_claim": all(
                isinstance(row, Mapping)
                and isinstance(row.get("cue"), Mapping)
                and row["cue"].get("release_usable") is False
                for row in rows
            ),
        },
        "validation_errors": errors,
        "claims": rows,
        "promotion_boundary": (
            "10/10 authoring is complete as a reviewed draft input; promote "
            "only after the corresponding real footage supports each claim"
        ),
    }, ([] if ready else ["authoring_claim_ledger_invalid"])


def build_runbook(
    *,
    project_config: Path,
    authoring_ledger: Path,
    promo_tool_root: Path,
    capture_root: Path | None,
    seed_preflight_report: Path | None,
    media_preflight_report: Path | None,
    expected_media_preflight_sha256: str | None,
    tts_cache: Path,
    work_dir: Path,
    python: Path,
    ffmpeg: str,
    ffprobe: str,
) -> dict[str, object]:
    config = project_config.expanduser().resolve()
    promo = promo_tool_root.expanduser().resolve()
    capture = None if capture_root is None else capture_root.expanduser().resolve()
    project, blockers = _project_gate(config)
    authoring, authoring_blockers = _authoring_ledger_gate(authoring_ledger)
    blockers.extend(authoring_blockers)

    footage = validate_footage_intake(capture)
    footage_ready = footage["result"] == "GREEN"
    if not footage_ready:
        blockers.insert(0, "footage_pending")

    media = _file_input(media_preflight_report)
    media_checks = {"expected_sha_bound": False, "receipt_green": False}
    if media_preflight_report is not None and media_preflight_report.is_file():
        payload = _json(media_preflight_report)
        record = media["record"]
        assert isinstance(record, Mapping)
        media_checks = {
            "expected_sha_bound": isinstance(expected_media_preflight_sha256, str) and record["sha256"] == expected_media_preflight_sha256.upper(),
            "receipt_green": payload.get("result") == "GREEN",
            "ten_chapter_project": isinstance(payload.get("project"), Mapping) and payload["project"].get("chapters") == 10,
            "xiaoxiao": isinstance(payload.get("voice"), Mapping) and payload["voice"].get("id") == VOICE,
            "bilingual_safe_area": isinstance(payload.get("subtitle_layout"), Mapping) and {row.get("id") for row in payload["subtitle_layout"].get("tracks", []) if isinstance(row, Mapping)} == {"zh-CN", "en"},
        }
    media["checks"] = media_checks
    if not all(media_checks.values()):
        blockers.append("media_receipt_pending")

    tool_identity = {
        "root": str(promo),
        "observed_without_fetch": {
            "head": _git(promo, "rev-parse", "HEAD"),
            "origin_main": _git(promo, "rev-parse", "origin/main"),
            "clean": not bool(_git(promo, "status", "--short")),
        },
        "production_refresh_required": True,
    }
    capture_arg = "<FOOTAGE_PENDING>" if capture is None else str(capture)
    seed_arg = "<SEED_PREFLIGHT_PENDING>" if seed_preflight_report is None else str(seed_preflight_report.resolve())
    # Step 1 is deliberately authoritative.  Even when a prior receipt is
    # supplied as a planning input, production commands consume the new
    # receipt made *after* the mandatory remote refresh.
    media_arg = "<NEW_MEDIA_RECEIPT_JSON>"
    media_sha_arg = "<NEW_MEDIA_RECEIPT_SHA256>"
    candidate_run = work_dir.expanduser().resolve() / "candidate-run" / "run-manifest.json"
    deliverable = work_dir.expanduser().resolve() / "deliverable" / "zhongguo-361-phase2.mp4"

    steps: list[dict[str, object]] = [
        {
            "ordinal": 1,
            "id": "fetch_and_verify_promo_origin_main",
            "required_first": True,
            "commands": [
                ["git", "-C", str(promo), "fetch", "origin"],
                ["git", "-C", str(promo), "merge", "--ff-only", "origin/main"],
                ["git", "-C", str(promo), "status", "--short"],
                ["git", "-C", str(promo), "rev-parse", "HEAD"],
                ["git", "-C", str(promo), "rev-parse", "origin/main"],
            ],
            "gate": "working tree clean and HEAD == origin/main; record fetched commit before every other production command",
        },
        {
            "ordinal": 2,
            "id": "refresh_media_receipt_after_fetch",
            "gate": "new receipt path; 24-hour validity; tool commit from step 1; Xiaoxiao, fonts, subtitle safe area, FFmpeg/ffprobe bytes GREEN",
            "command": [str(python.resolve()), str(ROOT / "mod_zhongguo_style/tools/preflight_phase2_media.py"), "--output", "<NEW_MEDIA_RECEIPT_JSON>"],
        },
        {
            "ordinal": 3,
            "id": "bind_green_footage_and_authoring_ledger",
            "gate": "rerun this planner against the strict media-entry intake for one same-session/PID/revision GREEN capture; require all 8 span postconditions and raw/timeline/report/index hashes bound, footage_pending cleared, and the byte-bound 10/10 authoring ledger still GREEN",
        },
        {
            "ordinal": 4,
            "id": "source_footage_human_review_1x",
            "human_pause": True,
            "gate": "named human watches all eight raw spans completely at 1x and signs exact timeline/raw/report/index hashes; confirms every drafted claim is supported; historical characters only; no fixture/test UI; no crop, mask, or redaction",
        },
        {
            "ordinal": 5,
            "id": "promote_reviewed_authoring_into_project",
            "manual_gate": True,
            "gate": "copy only footage-supported ledger cues into the ten project chapters, set ready/artifact_ids, revalidate both files, and record their new SHA-256; this is text/config work, not TTS or subtitle rendering",
        },
        {
            "ordinal": 6,
            "id": "validate_only",
            "command": [str(python.resolve()), str(ROOT / "mod_zhongguo_style/tools/build_phase2_promo_video.py"), "--project-config", str(config), "--capture-root", capture_arg, "--seed-preflight-report", seed_arg, "--media-preflight-report", media_arg, "--expected-media-preflight-sha256", media_sha_arg, "--work-dir", str(work_dir.resolve()), "--tts-cache", str(tts_cache.resolve()), "--ffmpeg", ffmpeg, "--ffprobe", ffprobe, "--run-id", "phase2-final", "--validate-only"],
            "gate": "read-only GREEN; exact 10 chapters/8 spans/runtime claims; no work directory created",
        },
        {
            "ordinal": 7,
            "id": "build_unreviewed_candidate",
            "command": [str(python.resolve()), str(ROOT / "mod_zhongguo_style/tools/build_phase2_promo_video.py"), "--project-config", str(config), "--capture-root", capture_arg, "--seed-preflight-report", seed_arg, "--media-preflight-report", media_arg, "--expected-media-preflight-sha256", media_sha_arg, "--work-dir", str(work_dir.resolve()), "--tts-cache", str(tts_cache.resolve()), "--ffmpeg", ffmpeg, "--ffprobe", ffprobe, "--run-id", "phase2-final"],
            "gate": "new external work directory; offline content-addressed Xiaoxiao cache only; capture and receipt bytes unchanged after build",
        },
        {
            "ordinal": 8,
            "id": "prepare_exact_deliverable_review",
            "commands": [
                ["xar-promo", "audit", str(candidate_run), "--subject-artifact-id", "zhongguo-361-phase2-video", "--evidence-bundle", "<AUTOMATED_EVIDENCE_BUNDLE_JSON>", "--report", "<AUTOMATED_AUDIT_REPORT_JSON>", "--report-artifact-id", "phase2-final-automated-audit"],
                ["xar-promo", "review", str(deliverable), "--storyboard", "<FINAL_STORYBOARD_JSON>", "--probe", "<BOUND_FFPROBE_ENVELOPE_JSON>", "--output-directory", "<NEW_PENDING_REVIEW_DIRECTORY>", "--audit-directory", "<NEW_REVIEW_COMMAND_AUDIT_DIRECTORY>", "--ffmpeg", ffmpeg, "--plan-only"],
                ["xar-promo", "review", str(deliverable), "--storyboard", "<FINAL_STORYBOARD_JSON>", "--probe", "<BOUND_FFPROBE_ENVELOPE_JSON>", "--output-directory", "<NEW_PENDING_REVIEW_DIRECTORY>", "--audit-directory", "<NEW_REVIEW_COMMAND_AUDIT_DIRECTORY>", "--ffmpeg", ffmpeg],
            ],
            "gate": "create byte-bound ffprobe envelope and pending review package for the exact final MP4; automated audit is not approval",
        },
        {
            "ordinal": 9,
            "id": "final_video_human_review_1x",
            "human_pause": True,
            "gate": "independent named human watches the exact MP4 completely at 1x; verifies narration claims, Xiaoxiao audio, zh-CN/en synchronization and wrapping, safe area, opening/finale, chapter boundaries, no loading/test UI; then explicitly approves or rejects its SHA-256",
        },
        {
            "ordinal": 10,
            "id": "record_signoff",
            "command": ["xar-promo", "signoff", "--run-manifest", str(candidate_run), "--artifact-id", "zhongguo-361-phase2-video", "--reviewer", "<NAMED_HUMAN>", "--decision", "<approved-or-rejected>"],
            "gate": "approval is valid only for the exact deliverable bytes reviewed in step 7",
        },
        {
            "ordinal": 11,
            "id": "export_preflight_then_local_bundle",
            "commands": [
                ["xar-promo", "validate", str(candidate_run), "--profile", "release"],
                ["xar-promo", "export", str(candidate_run), "<NEW_EXPORT_DIRECTORY>", "--policy", "<RELEASE_EXPORT_POLICY_JSON>", "--validate-only"],
                ["xar-promo", "export", str(candidate_run), "<NEW_EXPORT_DIRECTORY>", "--policy", "<RELEASE_EXPORT_POLICY_JSON>"],
            ],
            "gate": "release profile GREEN, selected deliverable approved, strict allowlist GREEN; export is local and does not publish",
        },
        {
            "ordinal": 12,
            "id": "external_publish",
            "gate": "separate explicit operator action; verify remote page after upload; keep publish_performed=false until it actually succeeds",
        },
    ]

    return {
        "schema_version": 1,
        "kind": "zg361_phase2_final_promo_deterministic_runbook",
        "result": "GREEN" if not blockers else "RED",
        "status": "ready-to-execute" if not blockers else "waiting-for-inputs",
        "reason_code": None if not blockers else blockers[0],
        "blockers": list(dict.fromkeys(blockers)),
        "scope": "no-media planning only",
        "execution_attestation": {"commands_executed": False, "ck3_started": False, "tts_generated": False, "subtitle_media_generated": False, "ffmpeg_started": False, "candidate_generated": False},
        "project": project,
        "authoring_claim_ledger": authoring,
        "fixed_contract": {"voice": VOICE, "subtitle_locales": ["zh-CN", "en"], "chapter_count": 10, "canonical_span_count": 8, "canonical_spans": [scenario.span_id for scenario in PHASE2_CAPTURE_SCENARIOS]},
        "inputs": {
            "repository": {
                "root": str(ROOT),
                "head": _git(ROOT, "rev-parse", "HEAD"),
                "clean_at_planning": not bool(_git(ROOT, "status", "--short")),
            },
            "authoring_claim_ledger": {
                "record": authoring["record"],
                "result": authoring["result"],
                "claim_count": len(authoring["claims"]),
            },
            "promo_toolchain": tool_identity,
            "capture": footage,
            "seed_preflight": _file_input(seed_preflight_report),
            "media_preflight": media,
            "tts_cache": {"path": str(tts_cache.resolve()), "required_voice": VOICE, "must_be_prepopulated_content_addressed": True},
        },
        "dependency_graph": final_promo_execution_dag(),
        "ordered_steps": steps,
        "hash_backfill_fields": [
            "promo_toolchain.head_after_fetch", "authoring_ledger.bytes_sha256", "authoring_ledger.each_claim_cue_and_language_lines", "project_config.promoted_bytes_sha256", "seed_preflight.bytes_sha256", "media_preflight.bytes_sha256", "capture.timeline.bytes_sha256", "capture.report.bytes_sha256", "capture.evidence_index.bytes_sha256", "capture.raw_recording.bytes_sha256", "capture.each_clean_span.start_end", "tts.each_cue.text_sha256_audio_bytes_sha256_provider_version_voice", "subtitles.zh_cn_ass_bytes_sha256", "subtitles.en_ass_bytes_sha256", "generated_cards.each_bytes_sha256", "chapters.each_mp4_bytes_sha256", "source_review.reviewer_reviewed_at_capture_sha256_all_eight", "deliverable.mp4_bytes_sha256", "deliverable.bound_ffprobe_envelope_sha256_duration_codecs", "final_review.package_sha256_reviewer_reviewed_at_decision", "signed_run_manifest.bytes_sha256", "export.bundle_manifest_sha256", "publication.publish_performed_remote_url_verified_at"
        ],
        "release_gates": [
            "step 1 fetched toolchain is clean and exactly origin/main", "fresh receipt is bound to that tool commit and remains unexpired", "the byte-bound 10/10 bilingual authoring ledger is GREEN and only footage-supported claims are promoted into the project", "all eight canonical spans come from one GREEN capture and have clean begin/end gates", "Xiaoxiao narration is content-addressed and ffprobe-measured", "zh-CN and en subtitles remain synchronized and inside 1920x1080 safe margins", "final video is H.264/yuv420p plus AAC 48kHz stereo and under 1200 seconds", "both independent 1x human review checkpoints are complete", "approved signoff binds the exact final MP4 SHA-256", "export release profile and allowlist are GREEN", "publish_performed remains false until external upload and page verification really complete"
        ],
        "planned_paths": {"work_dir": str(work_dir.resolve()), "candidate_run_manifest": str(candidate_run), "deliverable": str(deliverable)},
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--output", type=Path, required=True)
    result.add_argument("--project-config", type=Path, default=DEFAULT_CONFIG)
    result.add_argument(
        "--authoring-ledger", type=Path, default=DEFAULT_AUTHORING_LEDGER
    )
    result.add_argument("--promo-tool-root", type=Path, default=Path(r"Z:\workspace\xar_promo_toolchain"))
    result.add_argument("--capture-root", type=Path)
    result.add_argument("--seed-preflight-report", type=Path)
    result.add_argument("--media-preflight-report", type=Path)
    result.add_argument("--expected-media-preflight-sha256")
    result.add_argument("--tts-cache", type=Path, required=True)
    result.add_argument("--work-dir", type=Path, required=True)
    result.add_argument("--python", type=Path, default=Path(sys.executable))
    result.add_argument("--ffmpeg", default="ffmpeg")
    result.add_argument("--ffprobe", default="ffprobe")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    output = args.output.expanduser().resolve()
    if output.exists():
        raise RunbookError(f"refusing to overwrite runbook: {output}")
    if not output.parent.is_dir():
        raise RunbookError(f"runbook parent does not exist: {output.parent}")
    runbook = build_runbook(
        project_config=args.project_config,
        authoring_ledger=args.authoring_ledger,
        promo_tool_root=args.promo_tool_root,
        capture_root=args.capture_root,
        seed_preflight_report=args.seed_preflight_report,
        media_preflight_report=args.media_preflight_report,
        expected_media_preflight_sha256=args.expected_media_preflight_sha256,
        tts_cache=args.tts_cache,
        work_dir=args.work_dir,
        python=args.python,
        ffmpeg=args.ffmpeg,
        ffprobe=args.ffprobe,
    )
    output.write_text(json.dumps(runbook, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"runbook={output}")
    print(f"runbook_sha256={_sha256(output)['sha256']}")
    print(f"FINAL PROMO RUNBOOK: {runbook['result']} [{runbook['reason_code']}]")
    return 0 if runbook["result"] == "GREEN" else 2


if __name__ == "__main__":
    raise SystemExit(main())
