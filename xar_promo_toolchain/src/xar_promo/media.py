"""Dependency-free ffprobe command construction and JSON interpretation."""

from __future__ import annotations

import json
import hashlib
import math
import os
import re
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any, Callable, Mapping

from .errors import PromoToolchainError
from .process import CommandResult, CommandSpec, command_token, run_command


class MediaProbeError(PromoToolchainError):
    """ffprobe output was unavailable or did not satisfy its JSON contract."""


BOUND_MEDIA_PROBE_FORMAT_VERSION = 1
BOUND_MEDIA_PROBE_KIND = "xar-promo-bound-media-probe"
_SHA256 = re.compile(r"^[0-9A-Fa-f]{64}$")


@dataclass(frozen=True)
class MediaStream:
    index: int | None
    codec_type: str | None
    codec_name: str | None
    width: int | None
    height: int | None
    sample_rate: int | None
    channels: int | None
    duration_seconds: float | None
    average_frame_rate: Fraction | None
    raw: Mapping[str, Any]


@dataclass(frozen=True)
class MediaProbe:
    streams: tuple[MediaStream, ...]
    format: Mapping[str, Any]
    duration_seconds: float | None
    raw: Mapping[str, Any]

    @property
    def video_streams(self) -> tuple[MediaStream, ...]:
        return tuple(row for row in self.streams if row.codec_type == "video")

    @property
    def audio_streams(self) -> tuple[MediaStream, ...]:
        return tuple(row for row in self.streams if row.codec_type == "audio")

    def require_duration(self) -> float:
        if self.duration_seconds is None:
            raise MediaProbeError("ffprobe did not report a positive finite duration")
        return self.duration_seconds


@dataclass(frozen=True)
class BoundMediaProbe:
    """An ffprobe result bound to the exact bytes it describes."""

    subject_bytes: int
    subject_sha256: str
    probe: MediaProbe

    def to_dict(self) -> dict[str, Any]:
        return {
            "format_version": BOUND_MEDIA_PROBE_FORMAT_VERSION,
            "kind": BOUND_MEDIA_PROBE_KIND,
            "subject": {
                "bytes": self.subject_bytes,
                "sha256": self.subject_sha256,
            },
            "ffprobe": dict(self.probe.raw),
        }


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _validate_probe_subject(probe: MediaProbe, media_path: Path) -> tuple[Path, int]:
    path = Path(media_path).expanduser().resolve()
    if not path.is_file():
        raise MediaProbeError(f"media probe subject was not found: {path}")
    filename = probe.format.get("filename")
    if not isinstance(filename, str) or not filename.strip():
        raise MediaProbeError(
            "ffprobe format.filename is required before a probe can be byte-bound"
        )
    declared_path = Path(filename).expanduser()
    if not declared_path.is_absolute():
        declared_path = (Path.cwd() / declared_path).resolve()
    else:
        declared_path = declared_path.resolve()
    if os.path.normcase(str(declared_path)) != os.path.normcase(str(path)):
        raise MediaProbeError(
            f"ffprobe format.filename describes {declared_path}, not {path}"
        )
    size_value = probe.format.get("size")
    if isinstance(size_value, bool):
        raise MediaProbeError("ffprobe format.size must be an integer byte count")
    try:
        declared_size = int(size_value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise MediaProbeError(
            "ffprobe format.size is required before a probe can be byte-bound"
        ) from exc
    if declared_size < 0 or str(size_value).strip() != str(declared_size):
        raise MediaProbeError("ffprobe format.size must be an integer byte count")
    actual_size = path.stat().st_size
    if declared_size != actual_size:
        raise MediaProbeError(
            f"ffprobe format.size mismatch: probe reports {declared_size}, actual {actual_size}"
        )
    return path, actual_size


def bind_media_probe(media_path: Path, probe: MediaProbe) -> BoundMediaProbe:
    """Bind an already collected probe to the current exact media bytes."""

    if not isinstance(probe, MediaProbe):
        raise MediaProbeError("bound media probe requires a MediaProbe")
    path, actual_size = _validate_probe_subject(probe, media_path)
    return BoundMediaProbe(actual_size, _sha256_file(path), probe)


def parse_bound_media_probe_json(
    payload: str | bytes | bytearray,
    *,
    media_path: Path,
) -> BoundMediaProbe:
    """Parse a v1 envelope and verify its byte/SHA binding against media_path."""

    try:
        raw = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MediaProbeError(f"bound media probe returned invalid JSON: {exc}") from exc
    if not isinstance(raw, dict):
        raise MediaProbeError("bound media probe JSON root must be an object")
    if set(raw) != {"format_version", "kind", "subject", "ffprobe"}:
        raise MediaProbeError(
            "bound media probe fields must be format_version, kind, subject, and ffprobe"
        )
    if (
        raw["format_version"] != BOUND_MEDIA_PROBE_FORMAT_VERSION
        or raw["kind"] != BOUND_MEDIA_PROBE_KIND
    ):
        raise MediaProbeError("bound media probe must declare xar-promo-bound-media-probe v1")
    subject = raw["subject"]
    if not isinstance(subject, dict) or set(subject) != {"bytes", "sha256"}:
        raise MediaProbeError("bound media probe subject must contain only bytes and sha256")
    declared_bytes = subject["bytes"]
    declared_sha256 = subject["sha256"]
    if (
        isinstance(declared_bytes, bool)
        or not isinstance(declared_bytes, int)
        or declared_bytes < 0
    ):
        raise MediaProbeError("bound media probe subject.bytes must be a non-negative integer")
    if not isinstance(declared_sha256, str) or _SHA256.fullmatch(declared_sha256) is None:
        raise MediaProbeError("bound media probe subject.sha256 must be a SHA-256")
    ffprobe = raw["ffprobe"]
    if not isinstance(ffprobe, dict):
        raise MediaProbeError("bound media probe ffprobe must be an object")
    probe = parse_ffprobe_json(json.dumps(ffprobe, ensure_ascii=False))
    path, actual_bytes = _validate_probe_subject(probe, media_path)
    if actual_bytes != declared_bytes:
        raise MediaProbeError(
            f"bound media probe byte count mismatch: declared {declared_bytes}, actual {actual_bytes}"
        )
    actual_sha256 = _sha256_file(path)
    if actual_sha256 != declared_sha256.upper():
        raise MediaProbeError(
            "bound media probe SHA-256 mismatch: envelope does not describe the subject bytes"
        )
    return BoundMediaProbe(actual_bytes, actual_sha256, probe)


def load_bound_media_probe(path: Path, *, media_path: Path) -> BoundMediaProbe:
    """Read and verify a retained v1 bound-probe envelope."""

    source = Path(path)
    try:
        payload = source.read_bytes()
    except OSError as exc:
        raise MediaProbeError(f"could not read bound media probe {source}: {exc}") from exc
    return parse_bound_media_probe_json(payload, media_path=media_path)


def write_bound_media_probe(
    path: Path,
    *,
    media_path: Path,
    probe: MediaProbe,
) -> BoundMediaProbe:
    """Write a new retained v1 envelope without overwriting prior probe material."""

    bound = bind_media_probe(media_path, probe)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with target.open("x", encoding="utf-8", newline="\n") as output:
            json.dump(bound.to_dict(), output, ensure_ascii=False, indent=2, sort_keys=True)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
    except FileExistsError as exc:
        raise MediaProbeError(f"refusing to overwrite bound media probe: {target}") from exc
    return bound


def ffprobe_command(
    ffprobe: str | os.PathLike[str], media_path: str | os.PathLike[str]
) -> tuple[str, ...]:
    """Return the stable argv used for all media probes."""

    return (
        command_token(ffprobe),
        "-v",
        "error",
        "-show_streams",
        "-show_format",
        "-of",
        "json",
        command_token(media_path),
    )


def _positive_float(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return result if math.isfinite(result) and result > 0 else None


def _integer(value: Any, *, minimum: int = 0) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        result = int(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return result if result >= minimum and str(value).strip() == str(result) else None


def _frame_rate(row: Mapping[str, Any]) -> Fraction | None:
    for key in ("avg_frame_rate", "r_frame_rate"):
        value = row.get(key)
        if not isinstance(value, str):
            continue
        try:
            rate = Fraction(value)
        except (ValueError, ZeroDivisionError):
            continue
        if rate > 0:
            return rate
    return None


def _stream(row: Mapping[str, Any]) -> MediaStream:
    codec_type = row.get("codec_type")
    codec_name = row.get("codec_name")
    return MediaStream(
        index=_integer(row.get("index")),
        codec_type=codec_type if isinstance(codec_type, str) else None,
        codec_name=codec_name if isinstance(codec_name, str) else None,
        width=_integer(row.get("width"), minimum=1),
        height=_integer(row.get("height"), minimum=1),
        sample_rate=_integer(row.get("sample_rate"), minimum=1),
        channels=_integer(row.get("channels"), minimum=1),
        duration_seconds=_positive_float(row.get("duration")),
        average_frame_rate=_frame_rate(row),
        raw=dict(row),
    )


def parse_ffprobe_json(payload: str | bytes | bytearray) -> MediaProbe:
    """Parse ffprobe JSON without inferring project-specific requirements."""

    try:
        raw = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MediaProbeError(f"ffprobe returned invalid JSON: {exc}") from exc
    if not isinstance(raw, dict):
        raise MediaProbeError("ffprobe JSON root must be an object")

    raw_streams = raw.get("streams", [])
    raw_format = raw.get("format", {})
    if not isinstance(raw_streams, list):
        raise MediaProbeError("ffprobe streams must be an array")
    if not isinstance(raw_format, dict):
        raise MediaProbeError("ffprobe format must be an object")
    streams: list[MediaStream] = []
    for index, row in enumerate(raw_streams):
        if not isinstance(row, dict):
            raise MediaProbeError(f"ffprobe streams[{index}] must be an object")
        streams.append(_stream(row))

    duration = _positive_float(raw_format.get("duration"))
    if duration is None:
        duration = next(
            (row.duration_seconds for row in streams if row.duration_seconds is not None),
            None,
        )
    return MediaProbe(tuple(streams), dict(raw_format), duration, dict(raw))


CommandRunner = Callable[..., CommandResult]


def probe_media(
    ffprobe: str | os.PathLike[str],
    media_path: str | os.PathLike[str],
    *,
    audit_directory: Path,
    command_runner: CommandRunner = run_command,
) -> MediaProbe:
    """Run an injected ffprobe executable and parse its retained stdout."""

    path = Path(media_path)
    spec = CommandSpec.create(
        ffprobe_command(ffprobe, path),
        label=f"probe media {path}",
    )
    result = command_runner(spec, audit_directory=Path(audit_directory))
    try:
        return parse_ffprobe_json(result.stdout)
    except MediaProbeError as exc:
        marker = Path(audit_directory) / "probe-parse-error.json"
        marker.parent.mkdir(parents=True, exist_ok=True)
        value = {
            "schema_version": 1,
            "status": "invalid_ffprobe_json",
            "error": str(exc),
            "command_audit_directory": str(Path(audit_directory)),
        }
        try:
            with marker.open("x", encoding="utf-8", newline="\n") as handle:
                json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
                handle.write("\n")
        except FileExistsError:
            pass
        raise MediaProbeError(
            f"could not interpret ffprobe output for {path}; command and stdio "
            f"retained at {audit_directory}: {exc}"
        ) from exc


def probe_and_write_bound_media(
    ffprobe: str | os.PathLike[str],
    media_path: str | os.PathLike[str],
    *,
    output_path: Path,
    audit_directory: Path,
    command_runner: CommandRunner = run_command,
) -> BoundMediaProbe:
    """Run ffprobe with retained command audit and write an exact-byte envelope."""

    subject = Path(media_path).expanduser().resolve()
    probe = probe_media(
        ffprobe,
        subject,
        audit_directory=audit_directory,
        command_runner=command_runner,
    )
    return write_bound_media_probe(output_path, media_path=subject, probe=probe)


def require_streams(
    probe: MediaProbe,
    *,
    video: bool = False,
    audio: bool = False,
) -> MediaProbe:
    """Apply only caller-requested stream requirements."""

    missing: list[str] = []
    if video and not probe.video_streams:
        missing.append("video")
    if audio and not probe.audio_streams:
        missing.append("audio")
    if missing:
        raise MediaProbeError(
            "ffprobe output is missing required streams: " + ", ".join(missing)
        )
    return probe


__all__ = [
    "BOUND_MEDIA_PROBE_FORMAT_VERSION",
    "BOUND_MEDIA_PROBE_KIND",
    "BoundMediaProbe",
    "MediaProbe",
    "MediaProbeError",
    "MediaStream",
    "ffprobe_command",
    "bind_media_probe",
    "load_bound_media_probe",
    "parse_ffprobe_json",
    "parse_bound_media_probe_json",
    "probe_and_write_bound_media",
    "probe_media",
    "require_streams",
    "write_bound_media_probe",
]
