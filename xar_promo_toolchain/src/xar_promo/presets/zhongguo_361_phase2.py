"""Project policy for the ZhongGuo 361 phase-two promotional video.

The generic project model intentionally stays small.  Requirements that only
belong to this video live here: historical-character provenance, clean CK3
capture attestations, narration identity, sequel editorial scope, and honest
release boundaries.  No OCR is invoked or interpreted by this preset.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from xar_promo.adapters.ck3 import CaptureBundle, load_capture_bundle
from xar_promo.adapters.ck3.capture import (
    GAMEPLAY_HUD_START_MARK,
    RECORDING_STOP_MARK,
)
from xar_promo.errors import ManifestError, PromoToolchainError
from xar_promo.model import ProjectConfig
from xar_promo.tts import TtsRequest


PROJECT_ID = "zhongguo-361-phase2-promo"
ADAPTER_ID = "ck3"
PRESET_ID = "zhongguo_361_phase2"
CAPTURE_CHAPTER_KIND = "ck3_clean_span"
GENERATED_CHAPTER_KIND = "generated_card"
_SHA256_PATTERN = re.compile(r"^[0-9A-Fa-f]{64}$")
_FIXTURE_CONSTRUCTOR_KEYS = (
    "create_character",
    "create_title",
    "grant_title",
    "set_father",
    "set_mother",
    "set_spouse",
    "add_relation",
    "set_relation",
)


class Phase2PresetError(PromoToolchainError):
    """The phase-two project or capture does not satisfy its own policy."""


@dataclass(frozen=True, slots=True)
class Phase2PromoPolicy:
    narration_locale: str
    subtitle_locales: tuple[str, ...]
    voice: str
    duration_limit_seconds_exclusive: int
    audience_has_seen_phase_one: bool
    phase_two_increment_only: bool
    tone_tags: tuple[str, ...]
    require_real_historical_characters: bool
    forbid_test_decisions_in_picture: bool
    forbid_fixture_ui_in_picture: bool
    exclude_ck3_loading: bool
    start_after_gameplay_hud: bool
    preserve_all_process_material: bool
    process_material_kinds: tuple[str, ...]
    runtime_validation_required: bool
    human_review_required: bool


PHASE2_POLICY = Phase2PromoPolicy(
    narration_locale="zh-CN",
    subtitle_locales=("zh-CN", "en"),
    voice="zh-CN-XiaoxiaoNeural",
    duration_limit_seconds_exclusive=1200,
    audience_has_seen_phase_one=True,
    phase_two_increment_only=True,
    tone_tags=("satirical", "witty", "everyday-life", "youthful"),
    require_real_historical_characters=True,
    forbid_test_decisions_in_picture=True,
    forbid_fixture_ui_in_picture=True,
    exclude_ck3_loading=True,
    start_after_gameplay_hud=True,
    preserve_all_process_material=True,
    process_material_kinds=(
        "raw-recordings",
        "failed-takes",
        "tts-audio",
        "subtitles",
        "project-manifests",
        "editing-projects",
        "intermediate-exports",
        "review-and-signoff-records",
    ),
    runtime_validation_required=True,
    human_review_required=True,
)


# ProjectConfig v1 can carry locales, an exclusive duration boundary by preset
# convention, and chapters.  These remaining facts deliberately stay explicit
# instead of being smuggled into generic chapter fields.
CORE_PROJECT_CONFIG_BLOCKERS = (
    "ProjectConfig v1 has no serialized preset-policy extension for voice, "
    "audience, tone, provenance, clean-UI, or process-material requirements.",
    "Run manifests do not yet bind a phase-two runtime-claim matrix and a "
    "full-duration human visual review to one rendered deliverable.",
)


@dataclass(frozen=True, slots=True)
class CaptureRequirements:
    clean_span_ids: tuple[str, ...]
    mark_labels: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ExternalEvidenceFile:
    path: Path
    bytes: int
    sha256: str


@dataclass(frozen=True, slots=True)
class HistoricalSubject:
    subject_id: str
    history_id: str
    display_name: str
    roles: tuple[str, ...]
    history_source: ExternalEvidenceFile


@dataclass(frozen=True, slots=True)
class Phase2CaptureCandidate:
    """Verified source candidate that is intentionally not a release sign-off."""

    config: ProjectConfig
    bundle: CaptureBundle
    requirements: CaptureRequirements
    historical_subjects: tuple[HistoricalSubject, ...]
    title_history_source: ExternalEvidenceFile
    fixture_ui_attested_absent: bool
    test_decisions_attested_absent: bool
    capture_report_verified: bool
    phase_two_runtime_claims_verified: bool
    human_visual_review_verified: bool
    release_ready: bool
    blockers: tuple[str, ...]


def _read_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except OSError as exc:
        raise Phase2PresetError(f"could not read {label}: {path}: {exc}") from exc
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise Phase2PresetError(f"invalid JSON in {label}: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise Phase2PresetError(f"{label} root must be an object")
    return value


def _required_text(value: Any, context: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise Phase2PresetError(f"{context} must be a non-empty string")
    return value.strip()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
    except OSError as exc:
        raise Phase2PresetError(f"could not hash provenance source: {path}: {exc}") from exc
    return digest.hexdigest().upper()


def _external_evidence_file(
    value: Any,
    context: str,
    cache: dict[Path, ExternalEvidenceFile],
) -> ExternalEvidenceFile:
    if not isinstance(value, dict):
        raise Phase2PresetError(f"{context} must be a path/bytes/sha256 object")
    raw_path = value.get("path")
    if not isinstance(raw_path, str) or not Path(raw_path).is_absolute():
        raise Phase2PresetError(f"{context}.path must be absolute")
    path = Path(raw_path).expanduser().resolve()
    if not path.is_file():
        raise Phase2PresetError(f"{context}.path does not exist: {path}")
    raw_bytes = value.get("bytes")
    if isinstance(raw_bytes, bool) or not isinstance(raw_bytes, int) or raw_bytes < 0:
        raise Phase2PresetError(f"{context}.bytes must be an integer >= 0")
    raw_sha = value.get("sha256")
    if not isinstance(raw_sha, str) or _SHA256_PATTERN.fullmatch(raw_sha) is None:
        raise Phase2PresetError(f"{context}.sha256 must be a SHA-256 digest")
    declared_sha = raw_sha.upper()

    evidence = cache.get(path)
    if evidence is None:
        evidence = ExternalEvidenceFile(path, path.stat().st_size, _sha256(path))
        cache[path] = evidence
    if (raw_bytes, declared_sha) != (evidence.bytes, evidence.sha256):
        raise Phase2PresetError(f"{context} does not match its history source")
    return evidence


def validate_phase2_project_config(config: ProjectConfig) -> ProjectConfig:
    """Validate the generic config fields owned by this preset."""

    if config.project_id != PROJECT_ID:
        raise Phase2PresetError(f"phase-two project id must be {PROJECT_ID!r}")
    if config.adapter != ADAPTER_ID or config.preset != PRESET_ID:
        raise Phase2PresetError(
            f"phase-two pipeline must be adapter={ADAPTER_ID!r}, preset={PRESET_ID!r}"
        )
    if config.narration_locale != PHASE2_POLICY.narration_locale:
        raise Phase2PresetError("phase-two narration locale must be zh-CN")
    if config.subtitle_locales != PHASE2_POLICY.subtitle_locales:
        raise Phase2PresetError("phase-two subtitles must be ordered as zh-CN, en")
    if config.duration_limit_seconds != PHASE2_POLICY.duration_limit_seconds_exclusive:
        raise Phase2PresetError(
            "phase-two duration_limit_seconds must declare the exclusive 1200-second boundary"
        )
    if not config.chapters:
        raise Phase2PresetError("phase-two project must contain planned chapters")

    capture_count = 0
    for chapter in config.chapters:
        if chapter.kind not in {CAPTURE_CHAPTER_KIND, GENERATED_CHAPTER_KIND}:
            raise Phase2PresetError(
                f"chapter {chapter.chapter_id!r} has unsupported phase-two type {chapter.kind!r}"
            )
        if chapter.kind == CAPTURE_CHAPTER_KIND:
            capture_count += 1
        if set(chapter.title) != set(PHASE2_POLICY.subtitle_locales):
            raise Phase2PresetError(
                f"chapter {chapter.chapter_id!r} title must contain exact zh-CN/en text"
            )
        for cue in chapter.cues:
            if set(cue.narration) != {PHASE2_POLICY.narration_locale}:
                raise Phase2PresetError(
                    f"cue {cue.cue_id!r} must contain zh-CN narration only"
                )
            if set(cue.subtitles) != set(PHASE2_POLICY.subtitle_locales):
                raise Phase2PresetError(
                    f"cue {cue.cue_id!r} must contain exact zh-CN/en subtitles"
                )
    if capture_count == 0:
        raise Phase2PresetError("phase-two project must declare at least one CK3 clean span")
    return config


def load_phase2_project_config(path: str | Path) -> ProjectConfig:
    """Read one standard ProjectConfig and apply phase-two preset policy."""

    config_path = Path(path).expanduser().resolve()
    raw = _read_object(config_path, "phase-two project config")
    try:
        config = ProjectConfig.from_mapping(raw)
    except ManifestError as exc:
        raise Phase2PresetError(f"invalid phase-two ProjectConfig: {exc}") from exc
    return validate_phase2_project_config(config)


def phase2_capture_requirements(config: ProjectConfig) -> CaptureRequirements:
    """Derive all CK3 span and mark requirements from configured chapters."""

    validate_phase2_project_config(config)
    spans = tuple(
        chapter.chapter_id
        for chapter in config.chapters
        if chapter.kind == CAPTURE_CHAPTER_KIND
    )
    marks = (
        GAMEPLAY_HUD_START_MARK,
        *(
            label
            for span_id in spans
            for label in (f"{span_id}_clean_begin", f"{span_id}_clean_end")
        ),
        RECORDING_STOP_MARK,
    )
    return CaptureRequirements(spans, marks)


def build_narration_request(
    text: str,
    *,
    rate: str = "+0%",
    pitch: str = "+0Hz",
    volume: str = "+0%",
    audio_format: str = "mp3",
    cache_salt: str = "",
) -> TtsRequest:
    """Create a TTS request with the phase-two voice fixed by policy."""

    return TtsRequest(
        text=text,
        voice=PHASE2_POLICY.voice,
        rate=rate,
        pitch=pitch,
        volume=volume,
        audio_format=audio_format,
        cache_salt=cache_salt,
    )


def validate_rendered_duration(
    duration_seconds: int | float,
    config: ProjectConfig,
) -> float:
    """Require a positive final duration strictly below 1200 seconds."""

    validate_phase2_project_config(config)
    if (
        isinstance(duration_seconds, bool)
        or not isinstance(duration_seconds, (int, float))
        or not math.isfinite(float(duration_seconds))
    ):
        raise Phase2PresetError("rendered duration must be a finite number")
    duration = float(duration_seconds)
    if duration <= 0 or duration >= PHASE2_POLICY.duration_limit_seconds_exclusive:
        raise Phase2PresetError("phase-two final video must be positive and shorter than 1200 seconds")
    return duration


def _historical_provenance(
    timeline: Mapping[str, Any],
) -> tuple[tuple[HistoricalSubject, ...], ExternalEvidenceFile, bool]:
    raw = timeline.get("real_character_provenance")
    if not isinstance(raw, dict) or raw.get("schema_version") != 1:
        raise Phase2PresetError("timeline lacks schema-v1 real_character_provenance")
    raw_subjects = raw.get("subjects")
    if not isinstance(raw_subjects, list) or not raw_subjects:
        raise Phase2PresetError("real_character_provenance.subjects must be non-empty")

    cache: dict[Path, ExternalEvidenceFile] = {}
    subjects: list[HistoricalSubject] = []
    seen_history_ids: set[str] = set()
    for position, subject in enumerate(raw_subjects):
        context = f"real_character_provenance.subjects[{position}]"
        if not isinstance(subject, dict):
            raise Phase2PresetError(f"{context} must be an object")
        subject_id = _required_text(subject.get("subject_id"), f"{context}.subject_id")
        history_id = _required_text(subject.get("history_id"), f"{context}.history_id")
        if history_id in seen_history_ids:
            raise Phase2PresetError(f"real-character provenance repeats {history_id!r}")
        seen_history_ids.add(history_id)
        if subject.get("origin") != "ck3_history_database":
            raise Phase2PresetError(f"{context} is not sourced from the CK3 history database")
        if subject.get("temporary_or_generated") is not False:
            raise Phase2PresetError(f"{context} is temporary or generated")
        raw_roles = subject.get("roles")
        if not isinstance(raw_roles, list) or not raw_roles:
            raise Phase2PresetError(f"{context}.roles must be non-empty")
        roles = tuple(
            _required_text(role, f"{context}.roles[{index}]")
            for index, role in enumerate(raw_roles)
        )
        subjects.append(
            HistoricalSubject(
                subject_id=subject_id,
                history_id=history_id,
                display_name=_required_text(subject.get("display_name"), f"{context}.display_name"),
                roles=roles,
                history_source=_external_evidence_file(
                    subject.get("history_source"), f"{context}.history_source", cache
                ),
            )
        )

    title_history_source = _external_evidence_file(
        raw.get("title_history_source"),
        "real_character_provenance.title_history_source",
        cache,
    )
    constructor_counts = raw.get("fixture_constructor_counts")
    if not isinstance(constructor_counts, dict):
        raise Phase2PresetError("real-character provenance lacks fixture constructor counts")
    nonzero_or_missing = [
        key for key in _FIXTURE_CONSTRUCTOR_KEYS if constructor_counts.get(key) != 0
    ]
    if nonzero_or_missing:
        raise Phase2PresetError(
            "promo provenance used or omitted fixture constructors: "
            + ", ".join(nonzero_or_missing)
        )

    visibility = raw.get("test_decision_visibility_contract")
    test_decisions_absent = bool(
        isinstance(visibility, dict)
        and visibility.get("initialization_decision_before_recording_only") is True
        and visibility.get("all_other_fixture_decisions_permanently_hidden") is True
    )
    if not test_decisions_absent:
        raise Phase2PresetError(
            "real-character provenance does not attest that test decisions stay out of the recording"
        )
    return tuple(subjects), title_history_source, test_decisions_absent


def _fixture_ui_absence(
    timeline: Mapping[str, Any],
    requirements: CaptureRequirements,
) -> bool:
    raw_gates = timeline.get("clean_frame_gates")
    if not isinstance(raw_gates, list):
        raise Phase2PresetError("timeline clean_frame_gates must be an array")
    gates: dict[str, Mapping[str, Any]] = {}
    for raw in raw_gates:
        if isinstance(raw, dict) and isinstance(raw.get("span_id"), str):
            gates[raw["span_id"]] = raw
    for span_id in requirements.clean_span_ids:
        gate = gates.get(span_id)
        if gate is None or gate.get("fixture_test_ui_absent") is not True:
            raise Phase2PresetError(
                f"clean span {span_id!r} does not attest fixture UI absence"
            )
        frames = gate.get("frames")
        if not isinstance(frames, list) or len(frames) != 2:
            raise Phase2PresetError(f"clean span {span_id!r} lacks begin/end frame attestations")
        if any(
            not isinstance(frame, dict)
            or frame.get("fixture_test_ui_absent") is not True
            for frame in frames
        ):
            raise Phase2PresetError(
                f"clean span {span_id!r} frame does not attest fixture UI absence"
            )
    return True


def load_phase2_capture_candidate(
    config: ProjectConfig,
    artifact_root: str | Path,
) -> Phase2CaptureCandidate:
    """Verify a phase-two capture source while keeping release claims pending.

    All capture-backed chapters must first be marked ``ready`` in the project
    config.  The returned candidate still records project-runtime and human
    visual review as pending; a GREEN capture bundle alone cannot satisfy them.
    """

    validate_phase2_project_config(config)
    capture_chapters = tuple(
        chapter for chapter in config.chapters if chapter.kind == CAPTURE_CHAPTER_KIND
    )
    planned = [chapter.chapter_id for chapter in capture_chapters if chapter.state != "ready"]
    if planned:
        raise Phase2PresetError(
            "phase-two capture chapters are still planned and cannot claim verified footage: "
            + ", ".join(planned)
        )
    requirements = phase2_capture_requirements(config)
    bundle = load_capture_bundle(
        artifact_root,
        required_span_ids=requirements.clean_span_ids,
        required_mark_labels=requirements.mark_labels,
    )
    timeline = _read_object(bundle.timeline.path, "verified phase-two capture timeline")
    subjects, title_history, test_decisions_absent = _historical_provenance(timeline)
    fixture_ui_absent = _fixture_ui_absence(timeline, requirements)
    blockers = (
        "phase-two runtime claims still require the completed project-specific live matrix",
        "the rendered candidate still requires a full-duration human visual review and byte-bound sign-off",
        *CORE_PROJECT_CONFIG_BLOCKERS,
    )
    return Phase2CaptureCandidate(
        config=config,
        bundle=bundle,
        requirements=requirements,
        historical_subjects=subjects,
        title_history_source=title_history,
        fixture_ui_attested_absent=fixture_ui_absent,
        test_decisions_attested_absent=test_decisions_absent,
        capture_report_verified=True,
        phase_two_runtime_claims_verified=False,
        human_visual_review_verified=False,
        release_ready=False,
        blockers=blockers,
    )


__all__ = [
    "ADAPTER_ID",
    "CAPTURE_CHAPTER_KIND",
    "CORE_PROJECT_CONFIG_BLOCKERS",
    "GENERATED_CHAPTER_KIND",
    "PHASE2_POLICY",
    "PRESET_ID",
    "PROJECT_ID",
    "CaptureRequirements",
    "HistoricalSubject",
    "Phase2CaptureCandidate",
    "Phase2PresetError",
    "Phase2PromoPolicy",
    "build_narration_request",
    "load_phase2_capture_candidate",
    "load_phase2_project_config",
    "phase2_capture_requirements",
    "validate_phase2_project_config",
    "validate_rendered_duration",
]
