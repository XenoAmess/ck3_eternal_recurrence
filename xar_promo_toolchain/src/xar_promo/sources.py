"""Project-neutral visual-source planning and byte-bound preparation.

The authoring/validation phase may describe a visual that will be generated in
an attempt work directory without pretending that its bytes already exist.  A
build must resolve that plan to a real visual file and use a caller-supplied
byte inspector to establish its media family and dimensions.  The resulting
``PreparedVisual`` binds those observations to exact bytes and a SHA-256.

This module knows no game, project, renderer, or editorial policy.  In
particular, a JSON evidence manifest is evidence *about* a visual, not a visual
source itself.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Literal, Protocol, runtime_checkable

from .errors import PromoToolchainError


MediaFamily = Literal["video", "image"]
_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_SHA256 = re.compile(r"^[0-9A-Fa-f]{64}$")
_NON_VISUAL_SUFFIXES = frozenset(
    {
        ".ass",
        ".csv",
        ".ffconcat",
        ".json",
        ".m3u8",
        ".md",
        ".srt",
        ".toml",
        ".txt",
        ".xml",
        ".yaml",
        ".yml",
    }
)


class VisualSourceError(PromoToolchainError):
    """Base class for actionable visual-source failures."""


class VisualSourceValidationError(VisualSourceError):
    """A visual declaration cannot form a deterministic plan."""


class VisualResolutionError(VisualSourceError):
    """A required resolver did not produce the declared visual path."""


class VisualBindingError(VisualSourceError):
    """Resolved bytes, media type, dimensions, or digest do not agree."""


def _identifier(value: object, label: str) -> str:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise VisualSourceValidationError(
            f"{label} must be a portable identifier of at most 128 characters"
        )
    return value


def _positive_integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise VisualSourceValidationError(f"{label} must be a positive integer")
    return value


def _media_family(media_type: object, label: str) -> MediaFamily:
    if not isinstance(media_type, str) or not media_type.strip():
        raise VisualSourceValidationError(f"{label} must be a non-empty media type")
    normalized = media_type.strip().lower()
    if normalized.startswith("video/"):
        return "video"
    if normalized.startswith("image/"):
        return "image"
    raise VisualBindingError(
        f"{label} must describe visual bytes as video/* or image/*, got {media_type!r}"
    )


def _immutable_metadata(value: Mapping[str, object], label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise VisualSourceValidationError(f"{label} must be a mapping")
    rows: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str) or not key:
            raise VisualSourceValidationError(f"{label} keys must be non-empty strings")
        rows[key] = item
    return MappingProxyType(rows)


@dataclass(frozen=True, slots=True)
class SourceKind:
    """Extensible visual kind plus the media family it must resolve to."""

    id: str
    media_family: MediaFamily

    def __post_init__(self) -> None:
        _identifier(self.id, "source kind id")
        if self.media_family not in {"video", "image"}:
            raise VisualSourceValidationError(
                "source kind media_family must be 'video' or 'image'"
            )


VIDEO = SourceKind("video", "video")
STILL = SourceKind("still", "image")
GENERATED_CARD = SourceKind("generated-card", "image")
EVIDENCE_CARD = SourceKind("evidence-card", "image")


@dataclass(frozen=True, slots=True)
class VisualSource:
    """One authored visual declaration.

    ``path`` is either an existing prepared source or, when
    ``requires_resolution`` is true, the exact output planned beneath
    ``workdir``.  Relative generated paths are interpreted from ``workdir``;
    relative prepared paths are interpreted from the caller's current context.
    """

    source_id: str
    kind: SourceKind
    path: Path
    origin: str
    requires_resolution: bool = False
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _identifier(self.source_id, "visual source id")
        if not isinstance(self.kind, SourceKind):
            raise VisualSourceValidationError("visual source kind must be a SourceKind")
        object.__setattr__(self, "path", Path(self.path))
        _identifier(self.origin, "visual source origin")
        if not isinstance(self.requires_resolution, bool):
            raise VisualSourceValidationError(
                "visual source requires_resolution must be boolean"
            )
        object.__setattr__(
            self,
            "metadata",
            _immutable_metadata(self.metadata, "visual source metadata"),
        )


@dataclass(frozen=True, slots=True)
class VisualProbeResult:
    """An inspector's observation of actual visual bytes."""

    media_type: str
    width: int
    height: int

    def __post_init__(self) -> None:
        _media_family(self.media_type, "visual probe media_type")
        _positive_integer(self.width, "visual probe width")
        _positive_integer(self.height, "visual probe height")


@dataclass(frozen=True, slots=True)
class PreparedVisual:
    """A real visual whose type and geometry are bound to exact file bytes."""

    source_id: str
    kind: SourceKind
    path: Path
    media_type: str
    origin: str
    bytes: int
    sha256: str
    width: int
    height: int
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _identifier(self.source_id, "prepared visual source id")
        if not isinstance(self.kind, SourceKind):
            raise VisualSourceValidationError("prepared visual kind must be a SourceKind")
        path = Path(self.path)
        if not path.is_absolute():
            raise VisualBindingError("prepared visual path must be absolute")
        object.__setattr__(self, "path", path)
        observed_family = _media_family(self.media_type, "prepared visual media_type")
        if observed_family != self.kind.media_family:
            raise VisualBindingError(
                f"prepared visual kind {self.kind.id!r} requires "
                f"{self.kind.media_family}/* bytes, got {self.media_type!r}"
            )
        _identifier(self.origin, "prepared visual origin")
        _positive_integer(self.bytes, "prepared visual bytes")
        if not isinstance(self.sha256, str) or _SHA256.fullmatch(self.sha256) is None:
            raise VisualBindingError(
                "prepared visual sha256 must contain 64 hexadecimal characters"
            )
        object.__setattr__(self, "sha256", self.sha256.upper())
        _positive_integer(self.width, "prepared visual width")
        _positive_integer(self.height, "prepared visual height")
        object.__setattr__(
            self,
            "metadata",
            _immutable_metadata(self.metadata, "prepared visual metadata"),
        )


@runtime_checkable
class VisualResolver(Protocol):
    """Materialize one generated source at its planned work-directory path."""

    def __call__(self, source: VisualSource, *, workdir: Path) -> Path: ...


@runtime_checkable
class VisualProbe(Protocol):
    """Inspect actual bytes, rather than trusting a suffix or manifest claim."""

    def __call__(self, path: Path) -> VisualProbeResult: ...


def _effective_path(source: VisualSource, workdir: Path) -> tuple[Path, Path]:
    root = Path(workdir).expanduser().resolve()
    if source.requires_resolution:
        candidate = source.path if source.path.is_absolute() else root / source.path
        planned = candidate.expanduser().resolve()
        if not planned.is_relative_to(root):
            raise VisualSourceValidationError(
                f"generated visual {source.source_id!r} must be planned beneath workdir {root}"
            )
        return root, planned
    return root, source.path.expanduser().resolve()


def _reject_non_visual_path(path: Path) -> None:
    if path.suffix.lower() in _NON_VISUAL_SUFFIXES:
        raise VisualBindingError(
            f"document or manifest path cannot be used as visual media: {path}"
        )


def _require_file(path: Path, source_id: str) -> None:
    _reject_non_visual_path(path)
    if not path.is_file():
        raise VisualBindingError(
            f"visual source {source_id!r} did not resolve to an existing file: {path}"
        )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def validate_visual_source(
    source: VisualSource,
    *,
    workdir: Path,
    validate_only: bool,
) -> Path:
    """Validate a declaration and return its absolute planned path.

    A resolver-backed path may be absent only during validation.  This function
    never creates a directory, invokes a resolver, or probes media.
    """

    if not isinstance(source, VisualSource):
        raise VisualSourceValidationError("source must be a VisualSource")
    if not isinstance(validate_only, bool):
        raise VisualSourceValidationError("validate_only must be boolean")
    _, planned = _effective_path(source, Path(workdir))
    _reject_non_visual_path(planned)
    if source.requires_resolution and validate_only:
        if planned.exists() and not planned.is_file():
            raise VisualSourceValidationError(
                f"planned visual path exists but is not a file: {planned}"
            )
        return planned
    _require_file(planned, source.source_id)
    return planned


def _inspect(
    source: VisualSource,
    path: Path,
    probe: VisualProbe,
) -> VisualProbeResult:
    if not callable(probe):
        raise VisualSourceValidationError("probe must implement VisualProbe")
    try:
        result = probe(path)
    except Exception as exc:
        raise VisualBindingError(
            f"could not inspect visual source {source.source_id!r}: "
            f"{str(exc) or type(exc).__name__}"
        ) from exc
    if not isinstance(result, VisualProbeResult):
        raise VisualBindingError("visual probe must return VisualProbeResult")
    observed_family = _media_family(result.media_type, "visual probe media_type")
    if observed_family != source.kind.media_family:
        raise VisualBindingError(
            f"visual source {source.source_id!r} kind {source.kind.id!r} requires "
            f"{source.kind.media_family}/* bytes, probe reported {result.media_type!r}"
        )
    return result


def prepare_visual(
    source: VisualSource,
    *,
    workdir: Path,
    resolver: VisualResolver | None,
    probe: VisualProbe,
) -> PreparedVisual:
    """Resolve, inspect, and bind one visual for a build.

    Existing prepared sources bypass ``resolver``.  Resolver-backed sources
    must return the exact path declared by the validation plan.  In both cases
    the returned file must exist before its bytes, media type, dimensions and
    digest are captured.
    """

    planned = validate_visual_source(source, workdir=workdir, validate_only=True)
    if source.requires_resolution:
        if resolver is None or not callable(resolver):
            raise VisualResolutionError(
                f"visual source {source.source_id!r} requires a VisualResolver"
            )
        try:
            resolved = resolver(source, workdir=Path(workdir).expanduser().resolve())
        except Exception as exc:
            raise VisualResolutionError(
                f"resolver failed for visual source {source.source_id!r}: "
                f"{str(exc) or type(exc).__name__}"
            ) from exc
        if not isinstance(resolved, Path):
            raise VisualResolutionError("visual resolver must return pathlib.Path")
        actual = resolved.expanduser().resolve()
        if actual != planned:
            raise VisualResolutionError(
                f"resolver returned {actual}, but visual source {source.source_id!r} "
                f"planned {planned}"
            )
    else:
        actual = planned

    _require_file(actual, source.source_id)
    observation = _inspect(source, actual, probe)
    size = actual.stat().st_size
    if size < 1:
        raise VisualBindingError(
            f"visual source {source.source_id!r} resolved to an empty file: {actual}"
        )
    return PreparedVisual(
        source_id=source.source_id,
        kind=source.kind,
        path=actual,
        media_type=observation.media_type,
        origin=source.origin,
        bytes=size,
        sha256=_sha256(actual),
        width=observation.width,
        height=observation.height,
        metadata=source.metadata,
    )


def verify_prepared_visual(
    prepared: PreparedVisual,
    *,
    probe: VisualProbe,
) -> PreparedVisual:
    """Reverify that a prepared record still describes its current bytes."""

    if not isinstance(prepared, PreparedVisual):
        raise VisualSourceValidationError("prepared must be a PreparedVisual")
    _require_file(prepared.path, prepared.source_id)
    size = prepared.path.stat().st_size
    digest = _sha256(prepared.path)
    if size != prepared.bytes or digest != prepared.sha256:
        raise VisualBindingError(
            f"prepared visual {prepared.source_id!r} no longer matches its byte binding"
        )
    source = VisualSource(
        source_id=prepared.source_id,
        kind=prepared.kind,
        path=prepared.path,
        origin=prepared.origin,
        metadata=prepared.metadata,
    )
    observation = _inspect(source, prepared.path, probe)
    if (
        observation.media_type != prepared.media_type
        or observation.width != prepared.width
        or observation.height != prepared.height
    ):
        raise VisualBindingError(
            f"prepared visual {prepared.source_id!r} no longer matches its type/dimension binding"
        )
    return prepared


__all__ = [
    "VIDEO",
    "STILL",
    "GENERATED_CARD",
    "EVIDENCE_CARD",
    "MediaFamily",
    "SourceKind",
    "VisualSource",
    "VisualProbeResult",
    "PreparedVisual",
    "VisualResolver",
    "VisualProbe",
    "VisualSourceError",
    "VisualSourceValidationError",
    "VisualResolutionError",
    "VisualBindingError",
    "validate_visual_source",
    "prepare_visual",
    "verify_prepared_visual",
]
