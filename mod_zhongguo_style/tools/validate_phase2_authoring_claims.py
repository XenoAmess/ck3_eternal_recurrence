#!/usr/bin/env python3
"""Validate the phase-two narration/claim ledger without producing media."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import unicodedata
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parents[2]
ROOT_TOOLS = REPO_ROOT / "tools"
if str(ROOT_TOOLS) not in sys.path:
    sys.path.insert(0, str(ROOT_TOOLS))

from zhongguo_phase2_capture_choreography import (  # noqa: E402
    PHASE2_CAPTURE_SCENARIOS,
)


DEFAULT_LEDGER = (
    REPO_ROOT / "mod_zhongguo_style" / "promo" / "phase2-authoring-claims.json"
)
EXPECTED_CHAPTER_TYPES = (
    ("phase2_minimal_recap", "generated_card"),
    *((scenario.span_id, "ck3_clean_span") for scenario in PHASE2_CAPTURE_SCENARIOS),
    ("phase2_finale", "generated_card"),
)
EXPECTED_SPAN_MAP = {
    scenario.span_id: scenario.producer_key for scenario in PHASE2_CAPTURE_SCENARIOS
}
EXPECTED_POSTCONDITIONS = {
    scenario.span_id: scenario.postcondition for scenario in PHASE2_CAPTURE_SCENARIOS
}
EXPECTED_AUTHORITIES = (
    "mod_zhongguo_style/promo/phase2-brief.md",
    "mod_zhongguo_style/promo/promo-manifest.json",
    "mod_zhongguo_style/promo/phase2-readiness-2026-09-02.md",
    "docs/ck3-native-ai/phase2-producer-identity-live-2026-09-02.md",
)
EXPECTED_LANGUAGE_POLICY = {
    "primary_narration": "zh-CN",
    "primary_visual_text": "zh-CN",
    "secondary_visual_text": "en",
    "simultaneous_subtitles": ["zh-CN", "en"],
    "current_builder_narration": "zh-CN",
    "current_builder_voice": "zh-CN-XiaoxiaoNeural",
    "builder_policy_status": "aligned",
}
EXPECTED_PROMOTION_MAPPING = {
    "project_cue_shape": "id+narration+subtitles",
    "narration_zh_cn": "cue.narration_zh_cn",
    "subtitle_zh_cn": "newline_join(cue.subtitle_zh_cn_lines)",
    "subtitle_en": "newline_join(cue.subtitle_en_lines)",
    "generated_card_title": "chapter.generated_card_title",
    "semantic_breaks": "explicit-newline-between-editorial-lines",
    "automatic_wrap": "promo-renderer-wraps-within-each-editorial-line",
    "promotion_status": "blocked-until-footage-supported-source-review",
}
EXPECTED_READINESS_REVIEW = {
    "reviewed_through_commit": "d0fa15670fc9b0c049cc6d9228c839c04135e21c",
    "current_state": "static-ready-native-readiness-red-not-live",
    "same_run_phase2_clean_spans_verified": 0,
    "latest_phase2_terminal": {
        "result": "RED",
        "reason_code": "LegalConsentNotAuthorized",
        "producer_entry_count": 0,
        "footage_generated": False,
        "evidence_path": (
            "docs/ck3-native-ai/phase2-producer-identity-live-2026-09-02.md"
        ),
    },
}
MAX_ZH_LINE_UNITS = 48
MAX_EN_LINE_UNITS = 78


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _display_units(text: str) -> int:
    return sum(
        2 if unicodedata.east_asian_width(character) in {"W", "F"} else 1
        for character in text
    )


def _object(value: object, label: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{label} must be an object")
        return {}
    return value


def _nonempty_string(value: object, label: str, errors: list[str]) -> str:
    if type(value) is not str or not value.strip():
        errors.append(f"{label} must be a non-empty string")
        return ""
    return value


def _load_json(path: Path, label: str, errors: list[str]) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        errors.append(f"{label} is unreadable: {error}")
        return {}
    return _object(value, label, errors)


def _validate_authority(
    row: object, index: int, errors: list[str]
) -> None:
    authority = _object(row, f"authoring_authorities[{index}]", errors)
    relative = _nonempty_string(
        authority.get("path"), f"authoring_authorities[{index}].path", errors
    )
    expected_hash = _nonempty_string(
        authority.get("sha256"), f"authoring_authorities[{index}].sha256", errors
    )
    if not relative:
        return
    path = REPO_ROOT / relative
    if not path.is_file():
        errors.append(f"authoring authority does not exist: {relative}")
    elif expected_hash and _sha256(path) != expected_hash:
        errors.append(f"authoring authority hash drifted: {relative}")


def _validate_lines(
    value: object,
    label: str,
    maximum_units: int,
    terminal_punctuation: frozenset[str],
    errors: list[str],
) -> list[str]:
    if not isinstance(value, list) or not 1 <= len(value) <= 2:
        errors.append(f"{label} must contain one or two editorial lines")
        return []
    lines: list[str] = []
    for index, item in enumerate(value):
        line = _nonempty_string(item, f"{label}[{index}]", errors)
        if not line:
            continue
        if "\n" in line or "\r" in line:
            errors.append(f"{label}[{index}] contains an embedded line break")
        if line[-1] not in terminal_punctuation:
            errors.append(
                f"{label}[{index}] does not end at a sentence or clause boundary"
            )
        units = _display_units(line)
        if units > maximum_units:
            errors.append(
                f"{label}[{index}] exceeds the editorial safe width "
                f"({units}>{maximum_units} units)"
            )
        lines.append(line)
    return lines


def project_cue_input(cue: dict[str, Any]) -> dict[str, object]:
    """Project one reviewed ledger cue onto the exact future project shape."""

    return {
        "id": cue.get("id"),
        "narration": {"zh-CN": cue.get("narration_zh_cn")},
        "subtitles": {
            "zh-CN": "\n".join(cue.get("subtitle_zh_cn_lines", [])),
            "en": "\n".join(cue.get("subtitle_en_lines", [])),
        },
    }


def validate_ledger(path: Path) -> list[str]:
    """Return deterministic validation errors; never modify any input."""

    errors: list[str] = []
    ledger = _load_json(path, "authoring ledger", errors)
    if not ledger:
        return errors
    if ledger.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if ledger.get("kind") != "zg361_phase2_chinese_first_authoring_claim_matrix":
        errors.append("kind is not the phase-two Chinese-first authoring matrix")
    if ledger.get("authoring_status") != "draft-only-not-builder-input":
        errors.append("authoring_status must remain draft-only-not-builder-input")

    source = _object(ledger.get("source_project"), "source_project", errors)
    source_relative = _nonempty_string(source.get("path"), "source_project.path", errors)
    source_path = REPO_ROOT / source_relative if source_relative else Path()
    source_project = _load_json(source_path, "source project", errors) if source_relative else {}
    if source_relative and source_path.is_file():
        expected_hash = _nonempty_string(
            source.get("sha256"), "source_project.sha256", errors
        )
        if expected_hash and _sha256(source_path) != expected_hash:
            errors.append("source project hash drifted; re-review all authored claims")
    project = _object(source_project.get("project"), "source project.project", errors)
    if source.get("project_id") != "zhongguo-361-phase2-promo":
        errors.append("source_project.project_id is not canonical")
    if project.get("id") != source.get("project_id"):
        errors.append("source project id does not match the ledger")
    locales = _object(source_project.get("locales"), "source project.locales", errors)
    if locales.get("narration") != "zh-CN" or locales.get("subtitles") != ["zh-CN", "en"]:
        errors.append("source project must keep zh-CN narration and zh-CN/en subtitles")

    authorities = ledger.get("authoring_authorities")
    if not isinstance(authorities, list) or len(authorities) != len(EXPECTED_AUTHORITIES):
        errors.append(
            "authoring_authorities must bind brief, manifest, readiness ledger, "
            "and latest phase-two live terminal"
        )
    else:
        actual_authorities = tuple(
            row.get("path") if isinstance(row, dict) else None for row in authorities
        )
        if actual_authorities != EXPECTED_AUTHORITIES:
            errors.append("authoring_authorities are not the canonical ordered inputs")
        for index, row in enumerate(authorities):
            _validate_authority(row, index, errors)

    manifest_path = REPO_ROOT / "mod_zhongguo_style" / "promo" / "promo-manifest.json"
    manifest = _load_json(manifest_path, "promo manifest", errors)
    if (
        manifest.get("primary_language") != "zh-CN"
        or manifest.get("subtitle_languages") != ["zh-CN", "en"]
        or manifest.get("voice") != "zh-CN-XiaoxiaoNeural"
    ):
        errors.append("promo manifest Chinese-first language/voice policy drifted")
    language = _object(ledger.get("language_policy"), "language_policy", errors)
    if language != EXPECTED_LANGUAGE_POLICY:
        errors.append("ledger language policy does not exactly match the promo contract")
    if ledger.get("readiness_review") != EXPECTED_READINESS_REVIEW:
        errors.append(
            "readiness review must preserve d0fa156 and the zero-footage RED terminal"
        )
    if ledger.get("promotion_mapping") != EXPECTED_PROMOTION_MAPPING:
        errors.append("promotion mapping does not preserve semantic subtitle lines")

    source_chapters = source_project.get("chapters")
    ledger_chapters = ledger.get("chapters")
    if not isinstance(source_chapters, list) or not isinstance(ledger_chapters, list):
        errors.append("source and ledger chapters must be arrays")
        return errors
    source_shape = tuple(
        (row.get("id"), row.get("type")) if isinstance(row, dict) else (None, None)
        for row in source_chapters
    )
    ledger_shape = tuple(
        (row.get("id"), row.get("type")) if isinstance(row, dict) else (None, None)
        for row in ledger_chapters
    )
    if source_shape != EXPECTED_CHAPTER_TYPES:
        errors.append("source project does not contain the canonical ordered ten chapters")
    if ledger_shape != EXPECTED_CHAPTER_TYPES:
        errors.append("ledger does not contain the canonical ordered ten chapters")

    cue_ids: set[str] = set()
    for index, raw_chapter in enumerate(ledger_chapters):
        chapter = _object(raw_chapter, f"chapters[{index}]", errors)
        chapter_id = _nonempty_string(chapter.get("id"), f"chapters[{index}].id", errors)
        binding = _object(
            chapter.get("footage_binding"), f"{chapter_id}.footage_binding", errors
        )
        if binding.get("required_for_release") is not True or binding.get("verified") is not False:
            errors.append(f"{chapter_id} footage must remain required and unverified")
        if chapter_id in EXPECTED_SPAN_MAP:
            if chapter.get("draft_state") != "pending-real-footage":
                errors.append(f"{chapter_id} must remain pending-real-footage")
            if (
                binding.get("kind") != "same-run-real-ck3-clean-span"
                or binding.get("producer_key") != EXPECTED_SPAN_MAP[chapter_id]
                or binding.get("required_postcondition")
                != EXPECTED_POSTCONDITIONS[chapter_id]
            ):
                errors.append(f"{chapter_id} does not bind its canonical real span")
        else:
            if chapter.get("draft_state") != "draft-only":
                errors.append(f"{chapter_id} generated card must remain draft-only")
            if binding.get("kind") != "future-generated-card" or "producer_key" in binding:
                errors.append(f"{chapter_id} generated card binding is invalid")
            title = _object(
                chapter.get("generated_card_title"),
                f"{chapter_id}.generated_card_title",
                errors,
            )
            if set(title) != {"zh-CN", "en"}:
                errors.append(f"{chapter_id} generated card title must be exactly bilingual")
            for locale, limit in (("zh-CN", 48), ("en", 90)):
                value = _nonempty_string(
                    title.get(locale),
                    f"{chapter_id}.generated_card_title.{locale}",
                    errors,
                )
                if value and _display_units(value) > limit:
                    errors.append(f"{chapter_id} {locale} generated card title is too wide")
                if value and ("完成" in value or "complete" in value.casefold()):
                    errors.append(f"{chapter_id} generated card title overclaims completion")
        if chapter_id in EXPECTED_SPAN_MAP and "generated_card_title" in chapter:
            errors.append(f"{chapter_id} gameplay chapter must not define a generated title")

        cue = _object(chapter.get("cue"), f"{chapter_id}.cue", errors)
        cue_id = _nonempty_string(cue.get("id"), f"{chapter_id}.cue.id", errors)
        if cue_id in cue_ids:
            errors.append(f"duplicate cue id: {cue_id}")
        cue_ids.add(cue_id)
        narration = _nonempty_string(
            cue.get("narration_zh_cn"), f"{chapter_id}.cue.narration_zh_cn", errors
        )
        zh_lines = _validate_lines(
            cue.get("subtitle_zh_cn_lines"),
            f"{chapter_id}.cue.subtitle_zh_cn_lines",
            MAX_ZH_LINE_UNITS,
            frozenset("。！？；："),
            errors,
        )
        en_lines = _validate_lines(
            cue.get("subtitle_en_lines"),
            f"{chapter_id}.cue.subtitle_en_lines",
            MAX_EN_LINE_UNITS,
            frozenset(".!?;:"),
            errors,
        )
        if narration and zh_lines and narration != "".join(zh_lines):
            errors.append(f"{chapter_id} Chinese subtitle lines must reproduce narration exactly")
        if cue.get("release_usable") is not False:
            errors.append(f"{chapter_id} draft cue must not be release-usable")
        raw_zh_lines = cue.get("subtitle_zh_cn_lines")
        raw_en_lines = cue.get("subtitle_en_lines")
        if (
            narration
            and isinstance(raw_zh_lines, list)
            and isinstance(raw_en_lines, list)
            and len(zh_lines) == len(raw_zh_lines)
            and len(en_lines) == len(raw_en_lines)
            and zh_lines
            and en_lines
        ):
            projected = project_cue_input(cue)
            if set(projected) != {"id", "narration", "subtitles"}:
                errors.append(f"{chapter_id} project cue projection has extra fields")
            subtitles = projected["subtitles"]
            if not isinstance(subtitles, dict) or set(subtitles) != {"zh-CN", "en"}:
                errors.append(f"{chapter_id} project cue projection lacks exact subtitles")
            else:
                for locale, text in subtitles.items():
                    if type(text) is not str or "\r" in text or "\t" in text:
                        errors.append(
                            f"{chapter_id} {locale} automatic-wrap input is not renderable"
                        )
                    elif text.count("\n") != len(
                        zh_lines if locale == "zh-CN" else en_lines
                    ) - 1:
                        errors.append(
                            f"{chapter_id} {locale} semantic line breaks drifted"
                        )

        claim = _object(chapter.get("claim"), f"{chapter_id}.claim", errors)
        if claim.get("current_evidence_level") != "static-ready":
            errors.append(f"{chapter_id} current evidence must remain static-ready")
        status = claim.get("release_status")
        if type(status) is not str or not status.startswith("pending-"):
            errors.append(f"{chapter_id} release status must remain pending")
        _nonempty_string(
            claim.get("required_future_evidence"),
            f"{chapter_id}.claim.required_future_evidence",
            errors,
        )
        evidence_paths = claim.get("evidence_paths")
        if not isinstance(evidence_paths, list) or not evidence_paths:
            errors.append(f"{chapter_id} claim needs repository evidence paths")
        else:
            for evidence in evidence_paths:
                relative = _nonempty_string(
                    evidence, f"{chapter_id}.claim.evidence_path", errors
                )
                if relative and not (REPO_ROOT / relative).is_file():
                    errors.append(f"{chapter_id} evidence path does not exist: {relative}")
        observations = claim.get("required_visible_observations")
        if chapter_id in EXPECTED_SPAN_MAP and (
            not isinstance(observations, list)
            or len(observations) < 2
            or not all(type(item) is str and bool(item.strip()) for item in observations)
        ):
            errors.append(
                f"{chapter_id} needs at least two explicit visible observations"
            )
        cannot_claim = chapter.get("cannot_claim")
        if not isinstance(cannot_claim, list) or not cannot_claim or not all(
            type(item) is str and bool(item.strip()) for item in cannot_claim
        ):
            errors.append(f"{chapter_id} must state at least one cannot-claim boundary")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="required acknowledgement that this command must not author or render media",
    )
    args = parser.parse_args(argv)
    if not args.validate_only:
        parser.error("--validate-only is required; this tool has no write/render mode")
    errors = validate_ledger(args.ledger.resolve())
    if errors:
        print("VALIDATION: RED")
        for error in errors:
            print(f"- {error}")
        return 2
    print("VALIDATION: GREEN")
    print("10 chapter drafts; 8/8 gameplay cues remain bound to future real clean spans")
    print("media generated: no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
