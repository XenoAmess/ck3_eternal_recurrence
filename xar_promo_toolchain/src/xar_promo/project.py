"""Load and verify project configs, run manifests, and legacy manifests."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .errors import ArtifactError, ManifestError
from .model import PROJECT_KIND, RUN_KIND, ProjectConfig, RunManifest, SourceRecord


@dataclass(frozen=True)
class LoadedDocument:
    path: Path
    source_format: str
    raw: dict[str, Any]
    config: ProjectConfig | None = None
    run: RunManifest | None = None
    bound_config: ProjectConfig | None = None
    chapter_count: int = 0
    artifact_count: int = 0


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def read_json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise ManifestError(f"JSON document was not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ManifestError(f"invalid JSON: {path}:{exc.lineno}:{exc.colno}: {exc.msg}") from exc
    except OSError as exc:
        raise ManifestError(f"could not read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ManifestError("JSON root must be an object")
    return value


def artifact_path(record: SourceRecord, run_root: Path) -> Path:
    return (run_root / Path(record.path)).resolve()


def verify_run_artifacts(run: RunManifest, run_root: Path) -> None:
    for record in run.artifacts:
        path = artifact_path(record, run_root)
        if not path.is_file():
            raise ArtifactError(f"artifact {record.artifact_id!r} was not found: {path}")
        if path.stat().st_size != record.bytes:
            raise ArtifactError(f"artifact {record.artifact_id!r} byte count does not match")
        if sha256_file(path) != record.sha256:
            raise ArtifactError(f"artifact {record.artifact_id!r} SHA-256 does not match")


def _load_bound_config(run: RunManifest, run_path: Path) -> ProjectConfig:
    config_path = (run_path.parent / Path(run.project_config.path)).resolve()
    if not config_path.is_file():
        raise ArtifactError(f"bound project config was not found: {config_path}")
    if config_path.stat().st_size != run.project_config.bytes or sha256_file(config_path) != run.project_config.sha256:
        raise ArtifactError("run manifest project-config byte/SHA binding is stale")
    return ProjectConfig.from_mapping(read_json_object(config_path))


def _legacy_sources(raw: dict[str, Any], root: Path) -> list[tuple[Path, int | None, str | None]]:
    chapters = raw.get("chapters")
    if not isinstance(chapters, list) or not chapters:
        raise ManifestError("legacy manifest chapters must be a non-empty array")
    result: list[tuple[Path, int | None, str | None]] = []
    seen: set[str] = set()
    for index, chapter in enumerate(chapters):
        if not isinstance(chapter, dict) or not isinstance(chapter.get("id"), str) or not chapter["id"].strip():
            raise ManifestError(f"legacy chapters[{index}].id must be a non-empty string")
        if chapter["id"] in seen:
            raise ManifestError(f"legacy manifest repeats chapter id {chapter['id']!r}")
        seen.add(chapter["id"])
        if not isinstance(chapter.get("type"), str) or not chapter["type"].strip():
            raise ManifestError(f"legacy chapters[{index}].type must be a non-empty string")
        candidates: list[Any] = [chapter["source"]] if "source" in chapter else []
        for key in ("sources", "evidence_sources"):
            rows = chapter.get(key, [])
            if not isinstance(rows, list):
                raise ManifestError(f"legacy chapters[{index}].{key} must be an array")
            candidates.extend(rows)
        for candidate in candidates:
            declared_bytes: int | None = None
            declared_sha: str | None = None
            if isinstance(candidate, str):
                raw_path = candidate
            elif isinstance(candidate, dict) and isinstance(candidate.get("path"), str):
                raw_path = candidate["path"]
                declared_bytes = candidate.get("bytes")
                declared_sha = candidate.get("sha256")
            else:
                raise ManifestError(f"legacy chapters[{index}] has an invalid source")
            expanded = Path(os.path.expandvars(os.path.expanduser(raw_path)))
            result.append(((expanded if expanded.is_absolute() else root / expanded).resolve(), declared_bytes, None if declared_sha is None else str(declared_sha).upper()))
    return result


def load_document(path: Path, *, check_files: bool = True) -> LoadedDocument:
    canonical = path.expanduser().resolve()
    raw = read_json_object(canonical)
    kind = raw.get("kind")
    if kind == PROJECT_KIND:
        config = ProjectConfig.from_mapping(raw)
        return LoadedDocument(canonical, "project-config-v1", raw, config=config, chapter_count=len(config.chapters))
    if kind == RUN_KIND:
        run = RunManifest.from_mapping(raw)
        bound = _load_bound_config(run, canonical)
        if check_files:
            verify_run_artifacts(run, canonical.parent)
        return LoadedDocument(canonical, "run-manifest-v1", raw, run=run, bound_config=bound, chapter_count=len(bound.chapters), artifact_count=len(run.artifacts))
    if raw.get("format_version") != 1:
        raise ManifestError("unsupported document: expected XAR v1 config/run or legacy showcase v1")
    sources = _legacy_sources(raw, canonical.parent)
    if check_files:
        for source, declared_bytes, declared_sha in sources:
            if not source.is_file():
                raise ArtifactError(f"legacy source was not found: {source}")
            if declared_bytes is not None and source.stat().st_size != declared_bytes:
                raise ArtifactError(f"legacy source byte count does not match: {source}")
            if declared_sha is not None and sha256_file(source) != declared_sha:
                raise ArtifactError(f"legacy source SHA-256 does not match: {source}")
    return LoadedDocument(canonical, "legacy-showcase-v1", raw, chapter_count=len(raw["chapters"]), artifact_count=len(sources))


def validate_profile(document: LoadedDocument, profile: str) -> None:
    if profile == "authoring":
        return
    if document.run is None or document.bound_config is None:
        raise ManifestError("release profile requires a native run manifest")
    run, config = document.run, document.bound_config
    if not config.chapters or any(chapter.state != "ready" for chapter in config.chapters):
        raise ManifestError("release profile requires at least one chapter and all chapters ready")
    artifact_ids = {item.artifact_id for item in run.artifacts}
    for chapter in config.chapters:
        if config.narration_locale not in chapter.title:
            raise ManifestError(
                f"release chapter {chapter.chapter_id!r} lacks title locale "
                f"{config.narration_locale!r}"
            )
        missing_artifacts = sorted(set(chapter.artifact_ids) - artifact_ids)
        if missing_artifacts:
            raise ManifestError(
                f"release chapter {chapter.chapter_id!r} references missing run artifacts: "
                + ", ".join(missing_artifacts)
            )
        for cue in chapter.cues:
            if config.narration_locale not in cue.narration:
                raise ManifestError(
                    f"release cue {cue.cue_id!r} lacks narration locale "
                    f"{config.narration_locale!r}"
                )
            missing_subtitles = sorted(set(config.subtitle_locales) - set(cue.subtitles))
            if missing_subtitles:
                raise ManifestError(
                    f"release cue {cue.cue_id!r} lacks subtitle locales: "
                    + ", ".join(missing_subtitles)
                )
    deliverables = [item for item in run.artifacts if item.role == "deliverable"]
    latest = {item.artifact_id: item for item in run.signoffs}
    if not deliverables:
        raise ManifestError("release profile requires a preserved role='deliverable' artifact")
    if not any(item.artifact_id in latest and latest[item.artifact_id].decision == "approved" for item in deliverables):
        raise ManifestError("release profile requires an explicitly approved deliverable sign-off")
