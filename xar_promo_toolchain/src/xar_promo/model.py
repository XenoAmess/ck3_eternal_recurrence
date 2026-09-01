"""Dependency-free model and validator for the native v1 project manifest."""

from __future__ import annotations

import re
import datetime as dt
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, Mapping

from .errors import ManifestError


FORMAT_VERSION = 1
PROJECT_KIND = "xar_promo_project_config"
RUN_KIND = "xar_promo_run_manifest"
POLICY_STRATEGY = "append-only-content-addressed"
IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
SHA256 = re.compile(r"^[0-9A-Fa-f]{64}$")
DECISIONS = frozenset({"approved", "rejected"})
CHAPTER_STATES = frozenset({"planned", "ready"})
COLLECTIONS = frozenset({"raw", "derived"})


def _object(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ManifestError(f"{context} must be an object")
    return value


def _array(value: Any, context: str) -> list[Any]:
    if not isinstance(value, list):
        raise ManifestError(f"{context} must be an array")
    return value


def _string(value: Any, context: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ManifestError(f"{context} must be a non-empty string")
    return value.strip()


def _identifier(value: Any, context: str) -> str:
    result = _string(value, context)
    if IDENTIFIER.fullmatch(result) is None:
        raise ManifestError(
            f"{context} must start with an ASCII letter/digit and contain only "
            "letters, digits, '.', '_' or '-' (maximum 128 characters)"
        )
    return result


def _integer(value: Any, context: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ManifestError(f"{context} must be an integer >= {minimum}")
    return value


def _boolean(value: Any, context: str) -> bool:
    if not isinstance(value, bool):
        raise ManifestError(f"{context} must be a boolean")
    return value


def _only_keys(value: Mapping[str, Any], allowed: set[str], context: str) -> None:
    extras = sorted(set(value) - allowed)
    if extras:
        raise ManifestError(f"{context} has unsupported fields: {', '.join(extras)}")


def portable_relative_path(value: Any, context: str) -> str:
    raw = _string(value, context)
    if "\\" in raw:
        raise ManifestError(f"{context} must use portable '/' separators")
    path = PurePosixPath(raw)
    if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        raise ManifestError(f"{context} must be a normalized relative path")
    if re.match(r"^[A-Za-z]:", raw):
        raise ManifestError(f"{context} must not be a drive-qualified path")
    return path.as_posix()


def _localized_text(value: Any, context: str, *, allow_empty: bool = False) -> dict[str, str]:
    rows = _object(value, context)
    if not rows and not allow_empty:
        raise ManifestError(f"{context} must contain at least one locale")
    result: dict[str, str] = {}
    for locale, text in rows.items():
        result[_string(locale, f"{context} locale")] = _string(text, f"{context}.{locale}")
    return result


@dataclass(frozen=True)
class ArtifactPolicy:
    strategy: str
    raw_directory: str
    derived_directory: str
    manifest_history_directory: str
    preserve_process_material: bool

    @classmethod
    def from_mapping(cls, value: Any) -> "ArtifactPolicy":
        row = _object(value, "artifact_policy")
        _only_keys(
            row,
            {
                "strategy",
                "raw_directory",
                "derived_directory",
                "manifest_history_directory",
                "preserve_process_material",
            },
            "artifact_policy",
        )
        strategy = _string(row.get("strategy"), "artifact_policy.strategy")
        if strategy != POLICY_STRATEGY:
            raise ManifestError(
                f"artifact_policy.strategy must be {POLICY_STRATEGY!r}"
            )
        preserve = _boolean(
            row.get("preserve_process_material"),
            "artifact_policy.preserve_process_material",
        )
        if not preserve:
            raise ManifestError("v1 requires preserve_process_material=true")
        directories = (
            portable_relative_path(row.get("raw_directory"), "artifact_policy.raw_directory"),
            portable_relative_path(row.get("derived_directory"), "artifact_policy.derived_directory"),
            portable_relative_path(
                row.get("manifest_history_directory"),
                "artifact_policy.manifest_history_directory",
            ),
        )
        if len(set(directories)) != len(directories):
            raise ManifestError("artifact policy directories must be distinct")
        return cls(strategy, *directories, preserve)

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy": self.strategy,
            "raw_directory": self.raw_directory,
            "derived_directory": self.derived_directory,
            "manifest_history_directory": self.manifest_history_directory,
            "preserve_process_material": self.preserve_process_material,
        }


@dataclass(frozen=True)
class SourceRecord:
    artifact_id: str
    collection: str
    role: str
    path: str
    label: str
    bytes: int
    sha256: str
    media_type: str | None = None
    source_name: str | None = None

    @classmethod
    def from_mapping(cls, value: Any, context: str) -> "SourceRecord":
        row = _object(value, context)
        _only_keys(
            row,
            {"id", "collection", "role", "path", "label", "bytes", "sha256", "media_type", "source_name"},
            context,
        )
        collection = _string(row.get("collection"), f"{context}.collection")
        if collection not in COLLECTIONS:
            raise ManifestError(f"{context}.collection must be raw or derived")
        digest = _string(row.get("sha256"), f"{context}.sha256").upper()
        if SHA256.fullmatch(digest) is None:
            raise ManifestError(f"{context}.sha256 must contain 64 hexadecimal characters")
        media_type = row.get("media_type")
        source_name = row.get("source_name")
        return cls(
            artifact_id=_identifier(row.get("id"), f"{context}.id"),
            collection=collection,
            role=_identifier(row.get("role"), f"{context}.role"),
            path=portable_relative_path(row.get("path"), f"{context}.path"),
            label=_string(row.get("label"), f"{context}.label"),
            bytes=_integer(row.get("bytes"), f"{context}.bytes"),
            sha256=digest,
            media_type=None if media_type is None else _string(media_type, f"{context}.media_type"),
            source_name=None if source_name is None else _string(source_name, f"{context}.source_name"),
        )

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "id": self.artifact_id,
            "collection": self.collection,
            "role": self.role,
            "path": self.path,
            "label": self.label,
            "bytes": self.bytes,
            "sha256": self.sha256,
        }
        if self.media_type is not None:
            result["media_type"] = self.media_type
        if self.source_name is not None:
            result["source_name"] = self.source_name
        return result


@dataclass(frozen=True)
class Cue:
    cue_id: str
    narration: dict[str, str]
    subtitles: dict[str, str]

    @classmethod
    def from_mapping(cls, value: Any, context: str) -> "Cue":
        row = _object(value, context)
        _only_keys(row, {"id", "narration", "subtitles"}, context)
        return cls(
            cue_id=_identifier(row.get("id"), f"{context}.id"),
            narration=_localized_text(row.get("narration"), f"{context}.narration"),
            subtitles=_localized_text(row.get("subtitles", {}), f"{context}.subtitles", allow_empty=True),
        )

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.cue_id, "narration": self.narration, "subtitles": self.subtitles}


@dataclass(frozen=True)
class Chapter:
    chapter_id: str
    kind: str
    state: str
    title: dict[str, str]
    cues: tuple[Cue, ...]
    artifact_ids: tuple[str, ...]

    @classmethod
    def from_mapping(cls, value: Any, context: str) -> "Chapter":
        row = _object(value, context)
        _only_keys(row, {"id", "type", "state", "title", "cues", "artifact_ids"}, context)
        state = _string(row.get("state"), f"{context}.state")
        if state not in CHAPTER_STATES:
            raise ManifestError(f"{context}.state must be planned or ready")
        cues = tuple(
            Cue.from_mapping(item, f"{context}.cues[{index}]")
            for index, item in enumerate(_array(row.get("cues", []), f"{context}.cues"))
        )
        cue_ids = [item.cue_id for item in cues]
        if len(cue_ids) != len(set(cue_ids)):
            raise ManifestError(f"{context}.cues contains duplicate ids")
        artifact_ids = tuple(
            _identifier(item, f"{context}.artifact_ids[{index}]")
            for index, item in enumerate(_array(row.get("artifact_ids", []), f"{context}.artifact_ids"))
        )
        if len(artifact_ids) != len(set(artifact_ids)):
            raise ManifestError(f"{context}.artifact_ids contains duplicates")
        return cls(
            chapter_id=_identifier(row.get("id"), f"{context}.id"),
            kind=_identifier(row.get("type"), f"{context}.type"),
            state=state,
            title=_localized_text(row.get("title"), f"{context}.title"),
            cues=cues,
            artifact_ids=artifact_ids,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.chapter_id,
            "type": self.kind,
            "state": self.state,
            "title": self.title,
            "cues": [item.to_dict() for item in self.cues],
            "artifact_ids": list(self.artifact_ids),
        }


@dataclass(frozen=True)
class SignoffRecord:
    sequence: int
    signoff_id: str
    artifact_id: str
    artifact_bytes: int
    artifact_sha256: str
    reviewer: str
    decision: str
    reviewed_at: str
    note: str | None = None

    @classmethod
    def from_mapping(cls, value: Any, context: str) -> "SignoffRecord":
        row = _object(value, context)
        _only_keys(
            row,
            {"sequence", "id", "artifact_id", "artifact_bytes", "artifact_sha256", "reviewer", "decision", "reviewed_at", "note"},
            context,
        )
        decision = _string(row.get("decision"), f"{context}.decision")
        if decision not in DECISIONS:
            raise ManifestError(f"{context}.decision must be approved or rejected")
        digest = _string(row.get("artifact_sha256"), f"{context}.artifact_sha256").upper()
        if SHA256.fullmatch(digest) is None:
            raise ManifestError(f"{context}.artifact_sha256 must be a SHA-256")
        reviewed_at = _string(row.get("reviewed_at"), f"{context}.reviewed_at")
        try:
            parsed_time = dt.datetime.fromisoformat(reviewed_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ManifestError(f"{context}.reviewed_at must be an ISO-8601 timestamp") from exc
        if parsed_time.tzinfo is None:
            raise ManifestError(f"{context}.reviewed_at must include a timezone")
        note = row.get("note")
        return cls(
            sequence=_integer(row.get("sequence"), f"{context}.sequence", minimum=1),
            signoff_id=_identifier(row.get("id"), f"{context}.id"),
            artifact_id=_identifier(row.get("artifact_id"), f"{context}.artifact_id"),
            artifact_bytes=_integer(row.get("artifact_bytes"), f"{context}.artifact_bytes"),
            artifact_sha256=digest,
            reviewer=_string(row.get("reviewer"), f"{context}.reviewer"),
            decision=decision,
            reviewed_at=reviewed_at,
            note=None if note is None else _string(note, f"{context}.note"),
        )

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "sequence": self.sequence,
            "id": self.signoff_id,
            "artifact_id": self.artifact_id,
            "artifact_bytes": self.artifact_bytes,
            "artifact_sha256": self.artifact_sha256,
            "reviewer": self.reviewer,
            "decision": self.decision,
            "reviewed_at": self.reviewed_at,
        }
        if self.note is not None:
            result["note"] = self.note
        return result


@dataclass(frozen=True)
class ProjectConfig:
    project_id: str
    title: str
    adapter: str
    preset: str
    narration_locale: str
    subtitle_locales: tuple[str, ...]
    duration_limit_seconds: int | None
    chapters: tuple[Chapter, ...]

    @classmethod
    def from_mapping(cls, value: Any) -> "ProjectConfig":
        row = _object(value, "project config")
        _only_keys(row, {"format_version", "kind", "project", "pipeline", "locales", "constraints", "chapters"}, "project config")
        if row.get("format_version") != FORMAT_VERSION:
            raise ManifestError(f"project config format_version must be {FORMAT_VERSION}")
        if row.get("kind") != PROJECT_KIND:
            raise ManifestError(f"project config kind must be {PROJECT_KIND!r}")
        project = _object(row.get("project"), "project")
        _only_keys(project, {"id", "title"}, "project")
        pipeline = _object(row.get("pipeline"), "pipeline")
        _only_keys(pipeline, {"adapter", "preset"}, "pipeline")
        locales = _object(row.get("locales"), "locales")
        _only_keys(locales, {"narration", "subtitles"}, "locales")
        constraints = _object(row.get("constraints"), "constraints")
        _only_keys(constraints, {"duration_limit_seconds"}, "constraints")
        raw_duration = constraints.get("duration_limit_seconds")
        duration = None if raw_duration is None else _integer(raw_duration, "constraints.duration_limit_seconds", minimum=1)
        subtitles = tuple(
            _string(item, f"locales.subtitles[{index}]")
            for index, item in enumerate(_array(locales.get("subtitles"), "locales.subtitles"))
        )
        if not subtitles or len(subtitles) != len(set(subtitles)):
            raise ManifestError("locales.subtitles must be a non-empty unique array")
        chapters = tuple(
            Chapter.from_mapping(item, f"chapters[{index}]")
            for index, item in enumerate(_array(row.get("chapters"), "chapters"))
        )
        chapter_ids = [item.chapter_id for item in chapters]
        if len(chapter_ids) != len(set(chapter_ids)):
            raise ManifestError("chapters contains duplicate ids")
        return cls(
            project_id=_identifier(project.get("id"), "project.id"),
            title=_string(project.get("title"), "project.title"),
            adapter=_identifier(pipeline.get("adapter"), "pipeline.adapter"),
            preset=_identifier(pipeline.get("preset"), "pipeline.preset"),
            narration_locale=_string(locales.get("narration"), "locales.narration"),
            subtitle_locales=subtitles,
            duration_limit_seconds=duration,
            chapters=chapters,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "format_version": FORMAT_VERSION,
            "kind": PROJECT_KIND,
            "project": {"id": self.project_id, "title": self.title},
            "pipeline": {"adapter": self.adapter, "preset": self.preset},
            "locales": {"narration": self.narration_locale, "subtitles": list(self.subtitle_locales)},
            "constraints": {"duration_limit_seconds": self.duration_limit_seconds},
            "chapters": [item.to_dict() for item in self.chapters],
        }


@dataclass(frozen=True)
class ConfigBinding:
    path: str
    bytes: int
    sha256: str

    @classmethod
    def from_mapping(cls, value: Any) -> "ConfigBinding":
        row = _object(value, "project_config")
        _only_keys(row, {"path", "bytes", "sha256"}, "project_config")
        path = portable_relative_path(row.get("path"), "project_config.path")
        digest = _string(row.get("sha256"), "project_config.sha256").upper()
        if SHA256.fullmatch(digest) is None:
            raise ManifestError("project_config.sha256 must be a SHA-256")
        return cls(path, _integer(row.get("bytes"), "project_config.bytes"), digest)

    def to_dict(self) -> dict[str, Any]:
        return {"path": self.path, "bytes": self.bytes, "sha256": self.sha256}


def _history_rows(value: Any, key: str) -> tuple[dict[str, Any], ...]:
    rows = _array(value, key)
    result: list[dict[str, Any]] = []
    for index, raw in enumerate(rows, start=1):
        row = _object(raw, f"{key}[{index - 1}]")
        sequence = _integer(row.get("sequence"), f"{key}[{index - 1}].sequence", minimum=1)
        if sequence != index:
            raise ManifestError(f"{key} must be an ordered, gap-free append-only sequence")
        result.append(dict(row))
    return tuple(result)


@dataclass(frozen=True)
class RunManifest:
    run_id: str
    project_config: ConfigBinding
    artifact_policy: ArtifactPolicy
    phase_history: tuple[dict[str, Any], ...]
    artifacts: tuple[SourceRecord, ...]
    audits: tuple[dict[str, Any], ...]
    signoffs: tuple[SignoffRecord, ...]

    @classmethod
    def from_mapping(cls, value: Any) -> "RunManifest":
        row = _object(value, "run manifest")
        _only_keys(row, {"format_version", "kind", "run", "project_config", "artifact_policy", "phase_history", "artifacts", "audits", "signoffs"}, "run manifest")
        if row.get("format_version") != FORMAT_VERSION or row.get("kind") != RUN_KIND:
            raise ManifestError("run manifest must declare xar_promo_run_manifest format v1")
        run = _object(row.get("run"), "run")
        _only_keys(run, {"id"}, "run")
        artifacts = tuple(
            SourceRecord.from_mapping(item, f"artifacts[{index}]")
            for index, item in enumerate(_array(row.get("artifacts"), "artifacts"))
        )
        signoffs = tuple(
            SignoffRecord.from_mapping(item, f"signoffs[{index}]")
            for index, item in enumerate(_array(row.get("signoffs"), "signoffs"))
        )
        artifact_map = {item.artifact_id: item for item in artifacts}
        if len(artifact_map) != len(artifacts):
            raise ManifestError("artifacts contains duplicate ids")
        for index, signoff in enumerate(signoffs, start=1):
            if signoff.sequence != index or signoff.signoff_id != f"signoff-{index:06d}":
                raise ManifestError("signoffs must be an ordered, gap-free append-only sequence")
            artifact = artifact_map.get(signoff.artifact_id)
            if artifact is None or (signoff.artifact_bytes, signoff.artifact_sha256) != (artifact.bytes, artifact.sha256):
                raise ManifestError(f"signoff {signoff.signoff_id!r} is not bound to current immutable artifact bytes")
        return cls(
            run_id=_identifier(run.get("id"), "run.id"),
            project_config=ConfigBinding.from_mapping(row.get("project_config")),
            artifact_policy=ArtifactPolicy.from_mapping(row.get("artifact_policy")),
            phase_history=_history_rows(row.get("phase_history"), "phase_history"),
            artifacts=artifacts,
            audits=_history_rows(row.get("audits"), "audits"),
            signoffs=signoffs,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "format_version": FORMAT_VERSION,
            "kind": RUN_KIND,
            "run": {"id": self.run_id},
            "project_config": self.project_config.to_dict(),
            "artifact_policy": self.artifact_policy.to_dict(),
            "phase_history": list(self.phase_history),
            "artifacts": [item.to_dict() for item in self.artifacts],
            "audits": list(self.audits),
            "signoffs": [item.to_dict() for item in self.signoffs],
        }


def new_project_config(project_id: str, title: str, narration_locale: str, subtitle_locales: list[str], adapter: str, preset: str) -> ProjectConfig:
    payload = {
        "format_version": FORMAT_VERSION,
        "kind": PROJECT_KIND,
        "project": {"id": project_id, "title": title},
        "pipeline": {"adapter": adapter, "preset": preset},
        "locales": {"narration": narration_locale, "subtitles": subtitle_locales},
        "constraints": {"duration_limit_seconds": None},
        "chapters": [],
    }
    return ProjectConfig.from_mapping(payload)


def new_run_manifest(run_id: str, binding: ConfigBinding) -> RunManifest:
    return RunManifest.from_mapping(
        {
            "format_version": FORMAT_VERSION,
            "kind": RUN_KIND,
            "run": {"id": run_id},
            "project_config": binding.to_dict(),
            "artifact_policy": {
            "strategy": POLICY_STRATEGY,
            "raw_directory": "artifacts/raw",
            "derived_directory": "artifacts/derived",
            "manifest_history_directory": "artifacts/manifest-history",
            "preserve_process_material": True,
            },
            "phase_history": [],
            "artifacts": [],
            "audits": [],
            "signoffs": [],
        }
    )
