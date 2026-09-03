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
import inspect
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
from zhongguo_phase2_final_promo_completion import (
    validate_final_promo_completion,
)
from zhongguo_phase2_publish_target import validate_publish_target_authority
from zhongguo_phase2_promo_cuts import cut_for_config_name


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ROOT / "mod_zhongguo_style" / "promo" / "phase2-promo-project.json"
DEFAULT_AUTHORING_LEDGER = (
    ROOT / "mod_zhongguo_style" / "promo" / "phase2-authoring-claims.json"
)
PHASE2_MOD_TOOLS = ROOT / "mod_zhongguo_style" / "tools"
if str(PHASE2_MOD_TOOLS) not in sys.path:
    sys.path.insert(0, str(PHASE2_MOD_TOOLS))

from validate_phase2_authoring_claims import (  # noqa: E402
    materialize_ledger,
    validate_ledger,
)

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
    # The promo tool is intentionally kept in an isolated checkout.  On
    # Windows that checkout can be materialized by a different local service
    # account (for example, the build/sandbox account), which makes recent
    # Git versions reject it as a "dubious ownership" repository.  Bind the
    # safe-directory exception to this exact checkout for each read-only
    # probe instead of requiring a global Git configuration mutation.
    safe_root = str(root.expanduser().resolve())
    completed = subprocess.run(
        ["git", "-c", f"safe.directory={safe_root}", "-C", safe_root, *args],
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
        "preset_project_id": isinstance(payload.get("project"), Mapping)
        and payload["project"].get("id") == "zhongguo-361-phase2-promo",
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
    payload = materialize_ledger(ledger_path) if ledger_path.is_file() else {}
    chapters = payload.get("chapters")
    rows = chapters if isinstance(chapters, list) else []
    ids = tuple(row.get("id") for row in rows if isinstance(row, Mapping))
    language = payload.get("language_policy")
    language = language if isinstance(language, Mapping) else {}
    promotion = payload.get("promotion_mapping")
    promotion = promotion if isinstance(promotion, Mapping) else {}
    gameplay_rows = [
        row
        for row in rows
        if isinstance(row, Mapping) and row.get("type") == "ck3_clean_span"
    ]
    expected_producers = {
        scenario.span_id: scenario.producer_key for scenario in PHASE2_CAPTURE_SCENARIOS
    }
    visible_contracts: list[dict[str, object]] = []
    for row in gameplay_rows:
        binding = row.get("footage_binding")
        binding = binding if isinstance(binding, Mapping) else {}
        claim = row.get("claim")
        claim = claim if isinstance(claim, Mapping) else {}
        observations = claim.get("required_visible_observations")
        visible_contracts.append(
            {
                "span_id": row.get("id"),
                "producer_key": binding.get("producer_key"),
                "required_postcondition": binding.get("required_postcondition"),
                "required_visible_observations": (
                    list(observations) if isinstance(observations, list) else []
                ),
            }
        )
    checks = {
        "validator_green": not errors,
        "exact_ten_claims": len(rows) == 10,
        "canonical_order": ids == EXPECTED_CHAPTERS,
        "chinese_primary_english_secondary": language.get("primary_narration")
        == "zh-CN"
        and language.get("primary_visual_text") == "zh-CN"
        and language.get("secondary_visual_text") == "en"
        and language.get("simultaneous_subtitles") == ["zh-CN", "en"],
        "semantic_line_breaks_then_measured_wrap": promotion.get("narration_zh_cn")
        == "cue.narration_zh_cn"
        and promotion.get("subtitle_zh_cn")
        == "newline_join(cue.subtitle_zh_cn_lines)"
        and promotion.get("subtitle_en") == "newline_join(cue.subtitle_en_lines)"
        and promotion.get("semantic_breaks")
        == "explicit-newline-between-editorial-lines"
        and promotion.get("automatic_wrap")
        == "promo-renderer-wraps-within-each-editorial-line",
        "xiaoxiao": language.get("current_builder_voice") == VOICE,
        "eight_visible_observation_contracts": len(visible_contracts) == 8
        and all(
            row["producer_key"] == expected_producers.get(row["span_id"])
            and isinstance(row["required_postcondition"], str)
            and bool(str(row["required_postcondition"]).strip())
            and len(row["required_visible_observations"]) >= 2
            for row in visible_contracts
        ),
        "draft_not_release_claim": all(
            isinstance(row, Mapping)
            and isinstance(row.get("cue"), Mapping)
            and row["cue"].get("release_usable") is False
            for row in rows
        ),
    }
    ready = all(checks.values())
    return {
        "record": None if not ledger_path.is_file() else _sha256(ledger_path),
        "result": "GREEN" if ready else "RED",
        "status": payload.get("authoring_status"),
        "checks": checks,
        "validation_errors": errors,
        "claims": rows,
        "language_contract": dict(language),
        "promotion_mapping": dict(promotion),
        "visible_observation_contracts": visible_contracts,
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
    completion_attestation: Path | None = None,
    publish_target_authority: Path | None = None,
) -> dict[str, object]:
    config = project_config.expanduser().resolve()
    try:
        cut = cut_for_config_name(config.name)
    except ValueError as error:
        raise RunbookError(str(error)) from error
    if authoring_ledger.expanduser().resolve().name != cut.authoring_ledger_name:
        raise RunbookError(
            f"cut {cut.cut_id!r} requires authoring ledger {cut.authoring_ledger_name!r}"
        )
    promo = promo_tool_root.expanduser().resolve()
    capture = None if capture_root is None else capture_root.expanduser().resolve()
    project, blockers = _project_gate(config)
    authoring, authoring_blockers = _authoring_ledger_gate(authoring_ledger)
    blockers.extend(authoring_blockers)

    footage = validate_footage_intake(capture)
    footage_ready = footage["result"] == "GREEN"
    if not footage_ready:
        blockers.insert(0, "footage_pending")

    publish_target = validate_publish_target_authority(publish_target_authority)
    if publish_target["result"] != "GREEN":
        blockers.append("publish_target_pending")
    completion_kwargs: dict[str, object] = {
        "footage_intake": footage,
        "publish_target": publish_target,
    }
    # The dual-completion gate is integrated independently.  Consume its
    # project-specific subject parameter when present while retaining a clean
    # cherry-pick boundary for the two parallel work packages.
    if "deliverable_id" in inspect.signature(
        validate_final_promo_completion
    ).parameters:
        completion_kwargs["deliverable_id"] = cut.deliverable_artifact_id
    completion = validate_final_promo_completion(
        completion_attestation,
        **completion_kwargs,
    )
    blockers.extend(str(code) for code in completion["reason_codes"])

    media = _file_input(media_preflight_report)
    media_checks = {"expected_sha_bound": False, "receipt_green": False}
    media_payload: Mapping[str, object] = {}
    if media_preflight_report is not None and media_preflight_report.is_file():
        payload = _json(media_preflight_report)
        media_payload = payload
        record = media["record"]
        assert isinstance(record, Mapping)
        receipt_project = payload.get("project")
        receipt_project = receipt_project if isinstance(receipt_project, Mapping) else {}
        receipt_voice = payload.get("voice")
        receipt_voice = receipt_voice if isinstance(receipt_voice, Mapping) else {}
        receipt_subtitles = payload.get("subtitle_engine")
        receipt_subtitles = receipt_subtitles if isinstance(receipt_subtitles, Mapping) else {}
        receipt_media = payload.get("media")
        receipt_media = receipt_media if isinstance(receipt_media, Mapping) else {}
        capability = receipt_media.get("capability_query")
        capability = capability if isinstance(capability, Mapping) else {}
        execution = payload.get("execution_attestation")
        execution = execution if isinstance(execution, Mapping) else {}
        readiness = payload.get("final_promo_readiness")
        readiness = readiness if isinstance(readiness, Mapping) else {}
        implementation = payload.get("preflight_implementation")
        implementation = implementation if isinstance(implementation, Mapping) else {}
        receipt_config = receipt_project.get("config")
        receipt_config = receipt_config if isinstance(receipt_config, Mapping) else {}
        media_checks = {
            "expected_sha_bound": isinstance(expected_media_preflight_sha256, str) and record["sha256"] == expected_media_preflight_sha256.upper(),
            "receipt_green": payload.get("result") == "GREEN",
            "preflight_implementation_bound": implementation.get("sha256")
            == _sha256(ROOT / "mod_zhongguo_style/tools/preflight_phase2_media.py")["sha256"],
            "project_config_bound": receipt_config.get("sha256") == project["record"]["sha256"],
            "ten_chapter_project": receipt_project.get("chapters") == 10,
            "xiaoxiao_provider_configured_without_secret": receipt_voice.get("id") == VOICE
            and receipt_voice.get("provider") == "edge-tts"
            and receipt_voice.get("configured") is True
            and receipt_voice.get("credential_presence") == "not-applicable"
            and receipt_voice.get("credential_value_exposed") is False
            and receipt_voice.get("synthesis_performed") is False,
            "bilingual_safe_area": isinstance(payload.get("subtitle_layout"), Mapping) and {row.get("id") for row in payload["subtitle_layout"].get("tracks", []) if isinstance(row, Mapping)} == {"zh-CN", "en"},
            "semantic_wrap_dependency": receipt_subtitles.get("automatic_wrap_measured_in_memory") is True
            and receipt_subtitles.get("ass_written") is False,
            "codec_geometry_audio_capabilities": capability.get("video_encoder") == "libx264"
            and capability.get("video_geometry") == [1920, 1080]
            and capability.get("pixel_format") == "yuv420p"
            and capability.get("audio_encoder") == "aac"
            and capability.get("audio_sample_rate") == 48000
            and capability.get("audio_channels") == 2
            and capability.get("container_muxer") == "mp4",
            "no_media_execution": all(
                execution.get(key) is False
                for key in (
                    "ck3_started",
                    "tts_synthesis_performed",
                    "subtitle_media_written",
                    "ffmpeg_encode_started",
                    "work_directory_created",
                    "candidate_generated",
                )
            ),
            "typed_production_boundary": (
                isinstance(readiness.get("reason_codes"), list)
                and readiness.get("reason_codes")
                == [
                    code
                    for code in (
                        "fresh_promo_tool_fetch_required",
                        "footage_pending",
                        "publish_target_pending",
                    )
                    if code in readiness.get("reason_codes", [])
                ]
                and readiness.get("result")
                == ("RED" if readiness.get("reason_codes") else "GREEN")
            ),
        }
    media["checks"] = media_checks
    if not all(media_checks.values()):
        blockers.append("media_receipt_pending")
    elif "fresh_promo_tool_fetch_required" in media_payload.get(
        "final_promo_readiness", {}
    ).get("reason_codes", []):
        blockers.insert(0, "fresh_promo_tool_fetch_required")

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
    media_sha_arg = "<NEW_MEDIA_RECEIPT_SHA256>"
    candidate_run = work_dir.expanduser().resolve() / "candidate-run" / "run-manifest.json"
    deliverable = work_dir.expanduser().resolve() / cut.deliverable_relative_path
    authoring_attempt = work_dir.expanduser().resolve().with_name(
        work_dir.expanduser().resolve().name + "-authoring"
    )
    promoted_config = authoring_attempt / config.name
    footage_intake_report = authoring_attempt / "footage-intake.json"
    source_review_receipt = authoring_attempt / "source-review-receipt.json"
    promotion_receipt = authoring_attempt / "authoring-promotion-receipt.json"
    tts_prime_receipt = authoring_attempt / "tts-cache-prime-receipt.json"
    media_receipt = authoring_attempt / "media-preflight.json"
    export_directory = work_dir.expanduser().resolve().with_name(
        work_dir.expanduser().resolve().name + "-export"
    )
    post_candidate_root = candidate_run.parent / "post-candidate"
    post_candidate_receipt = post_candidate_root / "materialization-receipt.json"
    evidence_bundle = post_candidate_root / "evidence-bundle.json"
    automated_audit_report = post_candidate_root / "automated-audit.json"
    final_storyboard = post_candidate_root / "final-storyboard.json"
    bound_probe = post_candidate_root / "bound-ffprobe.json"
    pending_review_directory = post_candidate_root / "pending-review"
    review_command_audit_directory = post_candidate_root / "review-command-audit"
    claims_source_review_receipt = (
        post_candidate_root / "human-reviews" / "claims-and-source-pass.json"
    )
    final_candidate_review_receipt = (
        post_candidate_root / "human-reviews" / "final-candidate-pass.json"
    )
    release_export_policy = post_candidate_root / "release-export-policy.json"
    cli_prefix = [str(python.resolve()), "-m", "xar_promo.cli"]
    media_arg = str(media_receipt)
    media_preflight_command = [
        str(python.resolve()),
        str(ROOT / "mod_zhongguo_style/tools/preflight_phase2_media.py"),
        "--output",
        media_arg,
        "--project-config",
        str(promoted_config),
        "--expected-toolchain-head",
        "<FETCHED_PROMO_TOOL_HEAD>",
        "--planned-work-dir",
        str(work_dir.resolve()),
        "--planned-tts-cache",
        str(tts_cache.resolve()),
        "--planned-export-dir",
        str(export_directory),
        "--capture-root",
        capture_arg,
    ]
    if publish_target_authority is not None:
        media_preflight_command.extend(
            ("--publish-target-authority", str(publish_target_authority.resolve()))
        )

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
            "id": "bind_green_footage_intake",
            "gate": "one new hash-bound intake report for the immutable eight-span capture bundle",
            "command": [str(python.resolve()), str(ROOT / "tools/zhongguo_phase2_footage_intake.py"), "--capture-root", capture_arg, "--output", str(footage_intake_report)],
        },
        {
            "ordinal": 3,
            "id": "source_footage_human_review_1x",
            "human_pause": True,
            "gate": "named human watches all eight raw spans completely at 1x and writes the cut-specific source-review receipt at the declared path; confirms every promoted cue is supported; historical characters only; no fixture/test UI; no crop, mask, or redaction",
            "receipt_path": str(source_review_receipt),
        },
        {
            "ordinal": 4,
            "id": "promote_reviewed_authoring_into_project",
            "gate": "the command consumes the real source-review receipt and GREEN intake; it cannot infer approval and writes a new ready project instead of overwriting the draft",
            "command": [str(python.resolve()), str(ROOT / "mod_zhongguo_style/tools/promote_phase2_reviewed_authoring.py"), "--project-config", str(config), "--authoring-ledger", str(authoring_ledger.expanduser().resolve()), "--footage-intake-report", str(footage_intake_report), "--source-review-receipt", str(source_review_receipt), "--output-project", str(promoted_config), "--output-receipt", str(promotion_receipt)],
        },
        {
            "ordinal": 5,
            "id": "refresh_media_receipt_after_fetch",
            "gate": "new cut-specific receipt path; promoted config SHA; 24-hour validity; expected tool HEAD from step 1; Xiaoxiao, fonts, subtitle safe area, FFmpeg/ffprobe bytes GREEN",
            "command": media_preflight_command,
        },
        {
            "ordinal": 6,
            "id": "prime_reviewed_xiaoxiao_cache",
            "command": [str(python.resolve()), str(ROOT / "mod_zhongguo_style/tools/prime_phase2_tts_cache.py"), "--cut", cut.cut_id, "--project-config", str(promoted_config), "--media-preflight-report", media_arg, "--expected-media-preflight-sha256", media_sha_arg, "--tts-cache", str(tts_cache.resolve()), "--output", str(tts_prime_receipt), "--ffmpeg", ffmpeg, "--ffprobe", ffprobe],
            "gate": "real Edge TTS only after the fresh cut-specific media receipt; every reviewed cue must have a valid content-addressed Xiaoxiao entry; failures remain RED and must never be replaced with fabricated audio",
        },
        {
            "ordinal": 7,
            "id": "validate_only",
            "command": [str(python.resolve()), str(ROOT / "mod_zhongguo_style/tools/build_phase2_promo_video.py"), "--cut", cut.cut_id, "--project-config", str(promoted_config), "--capture-root", capture_arg, "--seed-preflight-report", seed_arg, "--media-preflight-report", media_arg, "--expected-media-preflight-sha256", media_sha_arg, "--work-dir", str(work_dir.resolve()), "--tts-cache", str(tts_cache.resolve()), "--ffmpeg", ffmpeg, "--ffprobe", ffprobe, "--run-id", cut.default_run_id, "--validate-only"],
            "gate": "read-only GREEN; exact 10 chapters/8 spans/runtime claims; no work directory created",
        },
        {
            "ordinal": 8,
            "id": "build_unreviewed_candidate",
            "command": [str(python.resolve()), str(ROOT / "mod_zhongguo_style/tools/build_phase2_promo_video.py"), "--cut", cut.cut_id, "--project-config", str(promoted_config), "--capture-root", capture_arg, "--seed-preflight-report", seed_arg, "--media-preflight-report", media_arg, "--expected-media-preflight-sha256", media_sha_arg, "--work-dir", str(work_dir.resolve()), "--tts-cache", str(tts_cache.resolve()), "--ffmpeg", ffmpeg, "--ffprobe", ffprobe, "--run-id", cut.default_run_id],
            "gate": "new external work directory; offline content-addressed Xiaoxiao cache only; capture and receipt bytes unchanged after build",
        },
        {
            "ordinal": 9,
            "id": "prepare_exact_deliverable_review",
            "commands": [
                [str(python.resolve()), str(ROOT / "mod_zhongguo_style/tools/materialize_phase2_post_candidate.py"), "--cut", cut.cut_id, "--project-config", str(promoted_config), "--run-manifest", str(candidate_run), "--output-root", str(post_candidate_root), "--export-directory", str(export_directory), "--ffmpeg", ffmpeg, "--ffprobe", ffprobe, "--validate-only"],
                [str(python.resolve()), str(ROOT / "mod_zhongguo_style/tools/materialize_phase2_post_candidate.py"), "--cut", cut.cut_id, "--project-config", str(promoted_config), "--run-manifest", str(candidate_run), "--output-root", str(post_candidate_root), "--export-directory", str(export_directory), "--ffmpeg", ffmpeg, "--ffprobe", ffprobe],
                cli_prefix + ["audit", str(candidate_run), "--subject-artifact-id", cut.deliverable_artifact_id, "--evidence-bundle", str(evidence_bundle), "--report", str(automated_audit_report), "--report-artifact-id", f"{cut.cut_id}-automated-audit"],
            ],
            "gate": "materialize the cut-specific bound probe, exact final storyboard, frame evidence bundle, pending review package and release policy; then run the concrete automated integrity audit, which cannot grant approval",
        },
        {
            "ordinal": 10,
            "id": "final_video_human_review_1x",
            "human_pause": True,
            "gate": "independent named human watches the exact MP4 completely at 1x; verifies narration claims, Xiaoxiao audio, zh-CN/en synchronization and wrapping, safe area, opening/finale, chapter boundaries, no loading/test UI; then explicitly approves or rejects its SHA-256",
            "review_package": str(pending_review_directory / "review-package.json"),
            "review_template": str(pending_review_directory / "review-template.json"),
            "required_receipts": [
                str(claims_source_review_receipt),
                str(final_candidate_review_receipt),
            ],
            "distinct_named_reviewers_required": True,
        },
        {
            "ordinal": 11,
            "id": "record_signoff",
            "command": None,
            "command_interface": {
                "fixed_argv": cli_prefix + ["signoff", "--run-manifest", str(candidate_run), "--artifact-id", cut.deliverable_artifact_id],
                "required_human_arguments": ["--reviewer", "--decision"],
                "allowed_decisions": ["approved", "rejected"],
                "automatic_execution_allowed": False,
            },
            "gate": "approval is valid only for the exact deliverable bytes built in step 8",
        },
        {
            "ordinal": 12,
            "id": "export_preflight_then_local_bundle",
            "commands": [
                cli_prefix + ["validate", str(candidate_run), "--profile", "release"],
                cli_prefix + ["export", str(candidate_run), str(export_directory), "--policy", str(release_export_policy), "--validate-only"],
                cli_prefix + ["export", str(candidate_run), str(export_directory), "--policy", str(release_export_policy)],
            ],
            "gate": "release profile GREEN, selected deliverable approved, strict allowlist GREEN; export is local and does not publish",
        },
        {
            "ordinal": 13,
            "id": "external_publish",
            "command": None,
            "gate": "separate explicit operator action only after a GREEN publish-target authority names the platform, account, credential reference and locator prefix; no repository tool uploads; verify remote page and preserve a byte-bound receipt after the authorized upload",
            "publish_target": publish_target["target"],
        },
        {
            "ordinal": 14,
            "id": "verify_complete_attestation",
            "command": None,
            "command_interface": {
                "fixed_argv": [str(python.resolve()), str(Path(__file__).resolve()), "--output", str(work_dir.resolve().with_name(work_dir.resolve().name + "-complete-runbook.json")), "--promo-tool-root", str(promo), "--project-config", str(promoted_config), "--authoring-ledger", str(authoring_ledger.expanduser().resolve()), "--capture-root", capture_arg, "--tts-cache", str(tts_cache.resolve()), "--work-dir", str(work_dir.resolve())],
                "required_runtime_bindings": ["--seed-preflight-report", "--media-preflight-report", "--expected-media-preflight-sha256", "--completion-attestation", "--publish-target-authority"],
                "automatic_completion_claim_allowed": False,
            },
            "gate": "COMPLETE only when candidate probe, claims audit, two independent 1x receipts, approved signoff, exact export manifest/files, explicit publish-target authority, and its verified HTTPS publication receipt all bind the same bytes",
        },
    ]

    blockers = list(dict.fromkeys(blockers))
    complete = not blockers and completion["status"] == "COMPLETE"
    return {
        "schema_version": 1,
        "kind": "zg361_phase2_final_promo_deterministic_runbook",
        "result": "GREEN" if complete else "RED",
        "status": "COMPLETE" if complete else "waiting-for-inputs",
        "reason_code": None if not blockers else blockers[0],
        "blockers": blockers,
        "scope": "no-media planning only",
        "cut": {
            "id": cut.cut_id,
            "preset_project_id": "zhongguo-361-phase2-promo",
            "run_id": cut.default_run_id,
            "deliverable_artifact_id": cut.deliverable_artifact_id,
            "deliverable_relative_path": cut.deliverable_relative_path.as_posix(),
        },
        "editorial_plan": {
            "chapter_order": list(cut.editorial_chapter_order),
            "reprises": [
                {
                    "source_chapter_id": reprise.source_chapter_id,
                    "after_chapter_id": reprise.after_chapter_id,
                    "duration_seconds": reprise.duration_seconds,
                    "start_offset_seconds": reprise.start_offset_seconds,
                    "narration": "generated-silence",
                    "new_evidence_claim": False,
                }
                for reprise in cut.reprises
            ],
            "capture_order_changed": False,
        },
        "execution_attestation": {"commands_executed": False, "ck3_started": False, "tts_generated": False, "subtitle_media_generated": False, "ffmpeg_started": False, "candidate_generated": False},
        "project": project,
        "authoring_claim_ledger": authoring,
        "fixed_contract": {
            "voice": VOICE,
            "subtitle_locales": ["zh-CN", "en"],
            "chapter_count": 10,
            "canonical_span_count": 8,
            "canonical_spans": [scenario.span_id for scenario in PHASE2_CAPTURE_SCENARIOS],
            "shared_capture_reuse": "same byte-bound canonical eight spans may feed both editorial cuts",
            "footage_session_policy": {
                "cross_span_restart_allowed": True,
                "cross_span_pid_or_generation_equality_required": False,
                "shared_identity": [
                    "canonical_seed_save_lineage",
                    "source_commit_and_tree",
                    "game_version_and_exe",
                    "product_only_mod_mount_tree",
                ],
                "per_span_continuity": [
                    "session_id",
                    "bridge_pid",
                    "connection_generation",
                    "pre_action_post_revision_chain",
                    "start_end_checkpoint_hashes",
                    "postcondition",
                    "cleanup",
                ],
                "seed_generation_to_loaded_proof_hash_continuous": True,
                "seed_generation_session_may_differ_from_capture": True,
                "forbidden_sources": ["phase1", "old-version", "fixture"],
                "legacy_single_session_compatible": True,
                "capture_reuse": {
                    "independent_edit_projects_allowed": True,
                    "same_verified_source_hashes_required_per_candidate": True,
                    "source_copy_or_regeneration_required": False,
                },
            },
        },
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
            "publish_target_authority": publish_target,
            "tts_cache": {"path": str(tts_cache.resolve()), "required_voice": VOICE, "must_be_prepopulated_content_addressed": True},
        },
        "completion_gate": completion,
        "dependency_graph": final_promo_execution_dag(),
        "ordered_steps": steps,
        "hash_backfill_fields": [
            "promo_toolchain.head_after_fetch", "authoring_ledger.bytes_sha256", "authoring_ledger.each_claim_cue_and_language_lines", "project_config.promoted_bytes_sha256", "seed_preflight.bytes_sha256", "media_preflight.bytes_sha256", "capture.timeline.bytes_sha256", "capture.report.bytes_sha256", "capture.evidence_index.bytes_sha256", "capture.raw_recording.bytes_sha256", "capture.canonical_seed_save_lineage.source_game_mount", "capture.seed_generation_loaded_save_hash_and_provenance_continuity", "capture.each_clean_span.session_pre_action_post_revision_checkpoint_cleanup", "capture.each_clean_span.start_end", "tts.each_cue.text_sha256_audio_bytes_sha256_provider_version_voice", "subtitles.zh_cn_ass_bytes_sha256", "subtitles.en_ass_bytes_sha256", "generated_cards.each_bytes_sha256", "chapters.each_mp4_bytes_sha256", "source_review.reviewer_reviewed_at_capture_sha256_all_eight", "deliverable.mp4_bytes_sha256", "deliverable.bound_ffprobe_envelope_sha256_duration_codecs", "claims_audit.report_sha256_subject_sha256", "review_round_1.receipt_sha256_candidate_sha256", "review_round_2.receipt_sha256_candidate_sha256", "signed_run_manifest.bytes_sha256", "export.bundle_manifest_sha256_deliverable_sha256", "publish_target.authority_sha256_target_account_credential_reference_locator_prefix", "publication.receipt_sha256_target_id_account_id_locator_export_manifest_sha256_candidate_sha256"
        ],
        "release_gates": [
            "step 1 fetched toolchain is clean and exactly origin/main", "fresh receipt is bound to that tool commit and remains unexpired", "the byte-bound 10/10 bilingual authoring ledger is GREEN and only footage-supported claims are promoted into the project", "all eight canonical spans share one canonical seed/save lineage and exact source/game/mod mount, and each span has a continuous session plus clean begin/end gates; clean CK3 restarts are allowed only between spans", "Xiaoxiao narration is content-addressed and ffprobe-measured", "zh-CN and en subtitles remain synchronized and inside 1920x1080 safe margins", "final video is H.264/yuv420p at 1920x1080 plus AAC 48kHz stereo and under 1200 seconds", "claims audit passes against the exact candidate", "two independent named reviewers each provide a full-duration 1x receipt bound to that candidate and audit", "approved run signoff binds the exact final MP4 SHA-256", "export manifest and exported deliverable hashes match the candidate", "an owner-approved publish target names the platform, account, credential reference and locator prefix", "a real HTTPS locator under that authorized prefix and remote-verification receipt bind the same target, export and candidate; only then may status be COMPLETE"
        ],
        "planned_paths": {
            "authoring_attempt": str(authoring_attempt),
            "footage_intake_report": str(footage_intake_report),
            "source_review_receipt": str(source_review_receipt),
            "promoted_project_config": str(promoted_config),
            "authoring_promotion_receipt": str(promotion_receipt),
            "tts_cache_prime_receipt": str(tts_prime_receipt),
            "media_preflight_receipt": str(media_receipt),
            "post_candidate_root": str(post_candidate_root),
            "post_candidate_receipt": str(post_candidate_receipt),
            "bound_probe": str(bound_probe),
            "final_storyboard": str(final_storyboard),
            "evidence_bundle": str(evidence_bundle),
            "automated_audit_report": str(automated_audit_report),
            "pending_review_directory": str(pending_review_directory),
            "review_command_audit_directory": str(review_command_audit_directory),
            "claims_source_review_receipt": str(claims_source_review_receipt),
            "final_candidate_review_receipt": str(final_candidate_review_receipt),
            "release_export_policy": str(release_export_policy),
            "export_directory": str(export_directory),
            "work_dir": str(work_dir.resolve()),
            "candidate_run_manifest": str(candidate_run),
            "deliverable": str(deliverable),
        },
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--output", type=Path, required=True)
    result.add_argument("--project-config", type=Path, default=DEFAULT_CONFIG)
    result.add_argument(
        "--authoring-ledger", type=Path, default=DEFAULT_AUTHORING_LEDGER
    )
    result.add_argument(
        "--publish-target-authority",
        type=Path,
        help=(
            "explicit owner-approved video platform/account/credential-reference "
            "contract; absence is typed publish_target_pending"
        ),
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
    result.add_argument(
        "--completion-attestation",
        type=Path,
        help=(
            "optional existing final candidate/audit/review/export/publish binding; "
            "without it the runbook cannot become COMPLETE"
        ),
    )
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
        completion_attestation=args.completion_attestation,
        publish_target_authority=args.publish_target_authority,
    )
    output.write_text(json.dumps(runbook, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"runbook={output}")
    print(f"runbook_sha256={_sha256(output)['sha256']}")
    print(f"FINAL PROMO RUNBOOK: {runbook['result']} [{runbook['reason_code']}]")
    return 0 if runbook["result"] == "GREEN" else 2


if __name__ == "__main__":
    raise SystemExit(main())
