"""Load one immutable CK3 capture run into reusable timeline projections.

The adapter consumes the evidence layout emitted by the CK3 acceptance/capture
runner.  It verifies bytes and SHA-256 values before exposing a raw recording,
ordered marks, or clean spans.  It does not perform OCR or apply any
project-specific content policy; producer-specific gate payloads remain opaque,
hash-bound evidence.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Iterator, Mapping

from xar_promo.errors import ArtifactError


REPORT_RELATIVE_PATH = "report.json"
TIMELINE_RELATIVE_PATH = "cell/promo/capture-timeline.json"
EVIDENCE_INDEX_RELATIVE_PATH = "evidence-index.json"
GAMEPLAY_HUD_START_MARK = "recording_started_after_gameplay_hud"
RECORDING_STOP_MARK = "recording_stop_requested"

_SHA256_PATTERN = re.compile(r"^[0-9A-Fa-f]{64}$")
_WINDOWS_DRIVE_PATTERN = re.compile(r"^[A-Za-z]:")
class CK3CaptureError(ArtifactError):
    """A CK3 capture run lacks evidence required for safe reuse."""


@dataclass(frozen=True, slots=True)
class CaptureFile:
    """One content-addressed file inside a capture run."""

    relative_path: str
    path: Path
    bytes: int
    sha256: str


@dataclass(frozen=True, slots=True)
class CaptureMark:
    """One ordered point on the raw recording timeline."""

    label: str
    seconds: float


@dataclass(frozen=True, slots=True)
class CleanSpan:
    """A positive, evidence-backed interval inside the gameplay recording."""

    span_id: str
    begin_mark: str
    end_mark: str
    begin_seconds: float
    end_seconds: float
    evidence: tuple[CaptureFile, ...]

    @property
    def duration_seconds(self) -> float:
        return self.end_seconds - self.begin_seconds


@dataclass(frozen=True, slots=True)
class CaptureBundle:
    """Verified CK3 source files and their reusable timeline projections."""

    artifact_root: Path
    timeline_schema: int | str
    source_kind: str
    report: CaptureFile
    timeline: CaptureFile
    evidence_index: CaptureFile
    raw_capture: CaptureFile
    marks: tuple[CaptureMark, ...]
    clean_spans: tuple[CleanSpan, ...]
    recording_start_seconds: float
    recording_stop_seconds: float

    def mark(self, label: str) -> CaptureMark:
        """Return a projected mark, raising ``KeyError`` when it is absent."""

        for mark in self.marks:
            if mark.label == label:
                return mark
        raise KeyError(label)

    def clean_span(self, span_id: str) -> CleanSpan:
        """Return a projected clean span, raising ``KeyError`` when absent."""

        for span in self.clean_spans:
            if span.span_id == span_id:
                return span
        raise KeyError(span_id)


def _read_object(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except OSError as exc:
        raise CK3CaptureError(f"could not read {label}: {path}: {exc}") from exc
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise CK3CaptureError(f"invalid JSON in {label}: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise CK3CaptureError(f"{label} root must be an object: {path}")
    return payload


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise CK3CaptureError(f"could not hash capture evidence: {path}: {exc}") from exc
    return digest.hexdigest().upper()


def _non_empty_string(value: Any, context: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CK3CaptureError(f"{context} must be a non-empty string")
    return value.strip()


def _byte_count(value: Any, context: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise CK3CaptureError(f"{context} must be an integer >= 0")
    return value


def _digest(value: Any, context: str) -> str:
    if not isinstance(value, str) or _SHA256_PATTERN.fullmatch(value) is None:
        raise CK3CaptureError(f"{context} must be a SHA-256 digest")
    return value.upper()


def _timeline_schema(value: Any) -> int | str:
    if isinstance(value, bool):
        raise CK3CaptureError("capture timeline.schema must be a positive integer or string")
    if isinstance(value, int):
        if value < 1:
            raise CK3CaptureError("capture timeline.schema must be >= 1")
        return value
    return _non_empty_string(value, "capture timeline.schema")


def _normalized_relative_path(value: Any, context: str) -> str:
    raw = _non_empty_string(value, context).replace("\\", "/")
    path = PurePosixPath(raw)
    normalized = path.as_posix()
    if (
        path.is_absolute()
        or _WINDOWS_DRIVE_PATTERN.match(raw) is not None
        or not path.parts
        or any(part in {"", ".", ".."} for part in path.parts)
        or normalized != raw
    ):
        raise CK3CaptureError(f"{context} must be a normalized relative path")
    return normalized


def _computed_file(path: Path, relative_path: str) -> CaptureFile:
    if not path.is_file():
        raise CK3CaptureError(f"required capture evidence is missing: {path}")
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise CK3CaptureError(f"could not stat capture evidence: {path}: {exc}") from exc
    return CaptureFile(relative_path, path, size, _sha256(path))


class _IndexedEvidence:
    def __init__(
        self,
        artifact_root: Path,
        rows: Mapping[str, Mapping[str, Any]],
    ) -> None:
        self.artifact_root = artifact_root
        self.rows = rows
        self.cache: dict[str, CaptureFile] = {}

    def relative(self, relative_path: str, context: str) -> CaptureFile:
        normalized = _normalized_relative_path(relative_path, context)
        row = self.rows.get(normalized)
        if row is None:
            raise CK3CaptureError(f"evidence index is missing {normalized}")

        expected_bytes = _byte_count(row.get("bytes"), f"evidence index {normalized}.bytes")
        expected_sha = _digest(row.get("sha256"), f"evidence index {normalized}.sha256")
        cached = self.cache.get(normalized)
        if cached is not None:
            if (cached.bytes, cached.sha256) != (expected_bytes, expected_sha):
                raise CK3CaptureError(f"evidence index conflicts for {normalized}")
            return cached

        path = (self.artifact_root / Path(*PurePosixPath(normalized).parts)).resolve()
        try:
            path.relative_to(self.artifact_root)
        except ValueError as exc:
            raise CK3CaptureError(f"indexed path escapes capture root: {normalized}") from exc
        evidence = _computed_file(path, normalized)
        if evidence.bytes != expected_bytes:
            raise CK3CaptureError(
                f"evidence index byte count mismatch for {normalized}: "
                f"{expected_bytes} != {evidence.bytes}"
            )
        if evidence.sha256 != expected_sha:
            raise CK3CaptureError(f"evidence index SHA-256 mismatch for {normalized}")
        self.cache[normalized] = evidence
        return evidence

    def declared(self, value: Any, context: str) -> CaptureFile:
        if not isinstance(value, dict):
            raise CK3CaptureError(f"{context} must be a path/bytes/sha256 object")
        raw_path = value.get("path")
        if not isinstance(raw_path, str) or not Path(raw_path).is_absolute():
            raise CK3CaptureError(f"{context}.path must be absolute")
        path = Path(raw_path).expanduser().resolve()
        try:
            relative = path.relative_to(self.artifact_root).as_posix()
        except ValueError as exc:
            raise CK3CaptureError(f"{context}.path lies outside the capture root") from exc
        evidence = self.relative(relative, context)
        declared_bytes = _byte_count(value.get("bytes"), f"{context}.bytes")
        declared_sha = _digest(value.get("sha256"), f"{context}.sha256")
        if (declared_bytes, declared_sha) != (evidence.bytes, evidence.sha256):
            raise CK3CaptureError(f"{context} does not match its indexed evidence")
        if evidence.path != path:
            raise CK3CaptureError(f"{context}.path does not resolve to its indexed file")
        return evidence


def _indexed_rows(index: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    raw_rows = index.get("files")
    if not isinstance(raw_rows, list):
        raise CK3CaptureError("evidence index files must be an array")
    result: dict[str, Mapping[str, Any]] = {}
    for position, raw in enumerate(raw_rows):
        if not isinstance(raw, dict):
            raise CK3CaptureError(f"evidence index files[{position}] must be an object")
        normalized = _normalized_relative_path(
            raw.get("path"), f"evidence index files[{position}].path"
        )
        if normalized in result:
            raise CK3CaptureError(f"evidence index repeats file {normalized}")
        result[normalized] = raw
    return result


def _marks(timeline: Mapping[str, Any]) -> tuple[tuple[CaptureMark, ...], dict[str, float]]:
    raw_marks = timeline.get("marks")
    if not isinstance(raw_marks, list) or not raw_marks:
        raise CK3CaptureError("capture timeline marks must be a non-empty array")
    projected: list[CaptureMark] = []
    mark_map: dict[str, float] = {}
    prior = -1.0
    for position, raw in enumerate(raw_marks):
        if not isinstance(raw, dict):
            raise CK3CaptureError(f"capture timeline marks[{position}] must be an object")
        label = _non_empty_string(raw.get("label"), f"capture timeline marks[{position}].label")
        seconds = raw.get("seconds")
        if (
            isinstance(seconds, bool)
            or not isinstance(seconds, (int, float))
            or not math.isfinite(float(seconds))
        ):
            raise CK3CaptureError(f"timeline mark {label!r} has invalid seconds")
        seconds = float(seconds)
        if seconds < 0 or seconds < prior:
            raise CK3CaptureError("capture timeline marks must be non-negative and ordered")
        if label in mark_map:
            raise CK3CaptureError(f"capture timeline repeats mark {label!r}")
        projected.append(CaptureMark(label, seconds))
        mark_map[label] = seconds
        prior = seconds

    if projected[0].label != GAMEPLAY_HUD_START_MARK:
        raise CK3CaptureError(
            "the first capture mark must attest recording_started_after_gameplay_hud"
        )
    if RECORDING_STOP_MARK not in mark_map:
        raise CK3CaptureError(f"capture timeline is missing {RECORDING_STOP_MARK}")
    if mark_map[RECORDING_STOP_MARK] <= mark_map[GAMEPLAY_HUD_START_MARK]:
        raise CK3CaptureError("the recorded gameplay window is not positive")
    return tuple(projected), mark_map


def _iter_file_records(value: Any) -> Iterator[dict[str, Any]]:
    if isinstance(value, dict):
        if {"path", "bytes", "sha256"}.issubset(value):
            yield value
        for child in value.values():
            yield from _iter_file_records(child)
    elif isinstance(value, list):
        for child in value:
            yield from _iter_file_records(child)


def _frame_evidence(
    frame: Mapping[str, Any],
    context: str,
    verifier: _IndexedEvidence,
) -> tuple[CaptureFile, ...]:
    for required in ("image", "gate"):
        if not isinstance(frame.get(required), dict):
            raise CK3CaptureError(f"{context}.{required} evidence is required")

    gate = verifier.declared(frame["gate"], f"{context}.gate")
    gate_payload = _read_object(gate.path, f"{context} gate JSON")
    expected_gate_payload = {key: value for key, value in frame.items() if key != "gate"}
    if gate_payload != expected_gate_payload:
        raise CK3CaptureError(f"{context} gate JSON does not exactly bind its timeline proof")

    evidence: list[CaptureFile] = []
    seen: set[str] = set()
    for position, record in enumerate(_iter_file_records(frame)):
        item = verifier.declared(record, f"{context}.evidence[{position}]")
        if item.relative_path not in seen:
            evidence.append(item)
            seen.add(item.relative_path)
    if gate.relative_path not in seen:
        raise CK3CaptureError(f"{context} gate evidence was not projected")
    return tuple(evidence)


def _clean_spans(
    timeline: Mapping[str, Any],
    mark_map: Mapping[str, float],
    verifier: _IndexedEvidence,
) -> tuple[CleanSpan, ...]:
    if timeline.get("clean_capture_complete") is not True:
        raise CK3CaptureError("capture timeline does not attest clean_capture_complete=true")
    if timeline.get("missing_clean_spans") != []:
        raise CK3CaptureError("capture timeline reports missing clean spans")
    raw_gates = timeline.get("clean_frame_gates")
    if not isinstance(raw_gates, list) or not raw_gates:
        raise CK3CaptureError("capture timeline clean_frame_gates must be non-empty")

    recording_start = mark_map[GAMEPLAY_HUD_START_MARK]
    recording_stop = mark_map[RECORDING_STOP_MARK]
    projected: list[CleanSpan] = []
    seen_ids: set[str] = set()
    for position, raw in enumerate(raw_gates):
        context = f"clean_frame_gates[{position}]"
        if not isinstance(raw, dict):
            raise CK3CaptureError(f"{context} must be an object")
        span_id = _non_empty_string(raw.get("span_id"), f"{context}.span_id")
        if span_id in seen_ids:
            raise CK3CaptureError(f"capture timeline repeats clean span {span_id!r}")
        seen_ids.add(span_id)
        if raw.get("result") != "GREEN":
            raise CK3CaptureError(f"clean span {span_id!r} is not GREEN")
        begin_mark = _non_empty_string(raw.get("begin_mark"), f"{context}.begin_mark")
        end_mark = _non_empty_string(raw.get("end_mark"), f"{context}.end_mark")
        if (
            begin_mark != f"{span_id}_clean_begin"
            or end_mark != f"{span_id}_clean_end"
        ):
            raise CK3CaptureError(
                f"clean span {span_id!r} does not bind its exact clean marks"
            )
        if begin_mark not in mark_map or end_mark not in mark_map:
            raise CK3CaptureError(f"clean span {span_id!r} references missing timeline marks")
        begin = mark_map[begin_mark]
        end = mark_map[end_mark]
        if end <= begin:
            raise CK3CaptureError(f"clean span {span_id!r} is not positive")
        if begin < recording_start or end > recording_stop:
            raise CK3CaptureError(
                f"clean span {span_id!r} lies outside the recorded gameplay window"
            )

        raw_frames = raw.get("frames")
        if not isinstance(raw_frames, list) or len(raw_frames) != 2:
            raise CK3CaptureError(
                f"clean span {span_id!r} must bind exact begin/end frame evidence"
            )
        frame_by_phase: dict[str, Mapping[str, Any]] = {}
        for frame_position, expected_phase in enumerate(("begin", "end")):
            frame = raw_frames[frame_position]
            frame_context = f"{context}.frames[{frame_position}]"
            if not isinstance(frame, dict):
                raise CK3CaptureError(f"{frame_context} must be an object")
            phase = frame.get("phase")
            if phase != expected_phase:
                raise CK3CaptureError(
                    f"{frame_context}.phase must be {expected_phase!r}"
                )
            if (
                frame.get("schema_version") != 1
                or frame.get("result") != "GREEN"
                or frame.get("span") != span_id
            ):
                raise CK3CaptureError(f"{frame_context} does not attest this GREEN span")
            frame_by_phase[phase] = frame
        if set(frame_by_phase) != {"begin", "end"}:
            raise CK3CaptureError(f"clean span {span_id!r} lacks begin/end frame evidence")

        evidence: list[CaptureFile] = []
        evidence_seen: set[str] = set()
        for phase in ("begin", "end"):
            for item in _frame_evidence(
                frame_by_phase[phase], f"clean span {span_id!r} {phase} frame", verifier
            ):
                if item.relative_path not in evidence_seen:
                    evidence.append(item)
                    evidence_seen.add(item.relative_path)
        projected.append(
            CleanSpan(
                span_id=span_id,
                begin_mark=begin_mark,
                end_mark=end_mark,
                begin_seconds=begin,
                end_seconds=end,
                evidence=tuple(evidence),
            )
        )
    return tuple(projected)


def _required_names(values: Iterable[str], context: str) -> tuple[str, ...]:
    result: list[str] = []
    seen: set[str] = set()
    for position, value in enumerate(values):
        name = _non_empty_string(value, f"{context}[{position}]")
        if name in seen:
            raise CK3CaptureError(f"{context} repeats {name!r}")
        result.append(name)
        seen.add(name)
    return tuple(result)


def load_capture_bundle(
    artifact_root: str | Path,
    *,
    required_span_ids: Iterable[str] = (),
    required_mark_labels: Iterable[str] = (),
) -> CaptureBundle:
    """Load and verify one CK3 capture run without mutating it.

    ``required_span_ids`` and ``required_mark_labels`` let a project impose its
    own coverage contract without embedding that project's vocabulary in this
    adapter.  Any missing or mismatched evidence raises :class:`CK3CaptureError`.
    Rejected runs are never deleted, repaired, or rewritten.
    """

    root = Path(artifact_root).expanduser().resolve()
    if not root.is_dir():
        raise CK3CaptureError(f"capture artifact root does not exist: {root}")

    report_path = root / REPORT_RELATIVE_PATH
    timeline_path = root / Path(*PurePosixPath(TIMELINE_RELATIVE_PATH).parts)
    index_path = root / EVIDENCE_INDEX_RELATIVE_PATH
    report_payload = _read_object(report_path, "capture report")
    timeline_payload = _read_object(timeline_path, "capture timeline")
    index_payload = _read_object(index_path, "evidence index")

    if report_payload.get("schema_version") != 1:
        raise CK3CaptureError("capture report schema_version must be 1")
    cell = report_payload.get("cell")
    if (
        report_payload.get("result") != "GREEN"
        or not isinstance(cell, dict)
        or cell.get("schema_version") != 1
        or cell.get("result") != "GREEN"
    ):
        cell_result = cell.get("result") if isinstance(cell, dict) else None
        raise CK3CaptureError(
            "capture report must be GREEN at root and cell; got "
            f"{report_payload.get('result')!r}/{cell_result!r}"
        )
    if index_payload.get("schema_version") != 1 or index_payload.get("result") != "GREEN":
        raise CK3CaptureError("evidence index schema_version/result must be 1/GREEN")
    indexed_root = index_payload.get("artifact_root")
    if not isinstance(indexed_root, str) or Path(indexed_root).expanduser().resolve() != root:
        raise CK3CaptureError("evidence index artifact_root does not match the requested run")

    verifier = _IndexedEvidence(root, _indexed_rows(index_payload))
    report_file = verifier.relative(REPORT_RELATIVE_PATH, "capture report")
    timeline_file = verifier.relative(TIMELINE_RELATIVE_PATH, "capture timeline")
    index_file = _computed_file(index_path, EVIDENCE_INDEX_RELATIVE_PATH)

    timeline_schema = _timeline_schema(timeline_payload.get("schema"))
    source_kind = _non_empty_string(
        timeline_payload.get("source_kind"), "capture timeline.source_kind"
    )
    source_kind_folded = source_kind.casefold()
    if "real ck3" not in source_kind_folded or "gameplay hud" not in source_kind_folded:
        raise CK3CaptureError(
            "capture timeline must classify the source as real CK3 after the gameplay HUD"
        )
    if timeline_payload.get("exclude_ck3_loading") is not True:
        raise CK3CaptureError("capture timeline does not attest exclusion of CK3 loading")

    reported_capture = cell.get("promo_capture")
    if not isinstance(reported_capture, dict):
        raise CK3CaptureError("GREEN capture report does not bind cell.promo_capture")
    if reported_capture != timeline_payload:
        raise CK3CaptureError(
            "GREEN report cell.promo_capture does not exactly bind the capture timeline"
        )

    raw_value = timeline_payload.get("raw_path")
    if not isinstance(raw_value, str) or not Path(raw_value).is_absolute():
        raise CK3CaptureError("capture timeline raw_path must be absolute")
    raw_path = Path(raw_value).expanduser().resolve()
    try:
        raw_relative = raw_path.relative_to(root).as_posix()
    except ValueError as exc:
        raise CK3CaptureError("capture raw recording must be inside the artifact root") from exc
    raw_file = verifier.relative(raw_relative, "capture timeline.raw_path")
    if raw_file.path != raw_path:
        raise CK3CaptureError("capture timeline raw_path does not resolve to indexed evidence")
    if _byte_count(timeline_payload.get("raw_bytes"), "capture timeline.raw_bytes") != raw_file.bytes:
        raise CK3CaptureError("capture timeline raw_bytes does not match the recording")
    if _digest(timeline_payload.get("raw_sha256"), "capture timeline.raw_sha256") != raw_file.sha256:
        raise CK3CaptureError("capture timeline raw_sha256 does not match the recording")

    marks, mark_map = _marks(timeline_payload)
    spans = _clean_spans(timeline_payload, mark_map, verifier)

    required_marks = _required_names(required_mark_labels, "required_mark_labels")
    missing_marks = [name for name in required_marks if name not in mark_map]
    if missing_marks:
        raise CK3CaptureError(
            "capture timeline is missing required marks: " + ", ".join(missing_marks)
        )
    required_spans = _required_names(required_span_ids, "required_span_ids")
    span_ids = {span.span_id for span in spans}
    missing_spans = [name for name in required_spans if name not in span_ids]
    if missing_spans:
        raise CK3CaptureError(
            "capture timeline is missing required clean spans: " + ", ".join(missing_spans)
        )

    return CaptureBundle(
        artifact_root=root,
        timeline_schema=timeline_schema,
        source_kind=source_kind,
        report=report_file,
        timeline=timeline_file,
        evidence_index=index_file,
        raw_capture=raw_file,
        marks=marks,
        clean_spans=spans,
        recording_start_seconds=mark_map[GAMEPLAY_HUD_START_MARK],
        recording_stop_seconds=mark_map[RECORDING_STOP_MARK],
    )
