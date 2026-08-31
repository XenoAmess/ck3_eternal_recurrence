"""Content-addressed, atomically published TTS cache."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, replace
from pathlib import Path
import shutil
import time
from typing import Callable, Mapping
import uuid

from .provider import (
    AudioValidator,
    ProviderIdentity,
    TtsCacheValidationError,
    TtsOfflineCacheMissError,
    TtsProvider,
    TtsRequest,
    TtsSynthesisError,
)


CACHE_SCHEMA_VERSION = 1
MAX_SYNTHESIS_ATTEMPTS = 10
MAX_RETRY_BACKOFF_SECONDS = 60.0


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _cache_payload(
    request: TtsRequest,
    identity: ProviderIdentity,
) -> dict[str, object]:
    return {
        "schema": "xar-promo-tts-cache-v1",
        "provider": {
            "id": identity.provider_id,
            "tool_version": identity.tool_version,
        },
        "request": request.cache_payload(),
    }


def tts_fingerprint(
    request: TtsRequest,
    identity: ProviderIdentity,
) -> str:
    """Hash provider, tool version, and all audio-producing inputs."""

    return _sha256_bytes(_canonical_json(_cache_payload(request, identity)))


class BuiltinAudioValidator:
    """Small offline MP3/WAVE structural validator.

    It intentionally performs no network access and has no ffprobe dependency.
    Projects that already have a richer media probe can inject their own
    ``AudioValidator`` while keeping the same cache transaction.
    """

    validator_id = "xar-promo-builtin-audio"
    validator_version = "1"

    def validate(
        self, path: Path, *, expected_format: str
    ) -> Mapping[str, object]:
        if not path.is_file():
            raise TtsCacheValidationError(f"audio file is missing: {path}")
        size = path.stat().st_size
        if size <= 0:
            raise TtsCacheValidationError(f"audio file is empty: {path}")
        with path.open("rb") as source:
            header = source.read(min(size, 64 * 1024))
        if expected_format == "mp3":
            id3 = header.startswith(b"ID3")
            frame_sync = any(
                header[index] == 0xFF
                and header[index + 1] & 0xE0 == 0xE0
                and header[index + 1] & 0x06 != 0
                for index in range(max(0, len(header) - 1))
            )
            if not (id3 or frame_sync):
                raise TtsCacheValidationError(
                    f"audio file lacks an MP3 signature: {path}"
                )
            signature = "id3" if id3 else "mpeg-frame"
        elif expected_format == "wav":
            if not (header.startswith(b"RIFF") and header[8:12] == b"WAVE"):
                raise TtsCacheValidationError(
                    f"audio file lacks a WAVE signature: {path}"
                )
            signature = "riff-wave"
        else:
            raise TtsCacheValidationError(
                f"builtin validator does not support {expected_format!r}"
            )
        return {
            "format": expected_format,
            "bytes": size,
            "signature": signature,
        }


@dataclass(frozen=True)
class TtsCacheEntry:
    fingerprint: str
    entry_directory: Path
    media_path: Path
    metadata_path: Path
    metadata: dict[str, object]
    validation: dict[str, object]
    cache_hit: bool


class TtsCache:
    """Immutable-entry cache with bounded synthesis and offline lookup."""

    def __init__(
        self,
        root: Path,
        *,
        validator: AudioValidator | None = None,
    ) -> None:
        self.root = Path(root)
        self.validator = validator or BuiltinAudioValidator()

    def fingerprint(
        self,
        request: TtsRequest,
        identity: ProviderIdentity,
    ) -> str:
        return tts_fingerprint(request, identity)

    def _entry_directory(
        self,
        fingerprint: str,
        identity: ProviderIdentity,
    ) -> Path:
        if (
            len(fingerprint) != 64
            or any(character not in "0123456789ABCDEF" for character in fingerprint)
        ):
            raise ValueError("fingerprint must be 64 uppercase hex characters")
        provider_slug = "".join(
            character if character.isalnum() or character in "._-" else "_"
            for character in identity.provider_id
        ).strip("._-")
        if not provider_slug:
            raise ValueError("provider_id does not contain a usable path token")
        return self.root / provider_slug / fingerprint[:2] / fingerprint

    def _paths(
        self,
        request: TtsRequest,
        identity: ProviderIdentity,
    ) -> tuple[str, Path, Path, Path]:
        fingerprint = self.fingerprint(request, identity)
        directory = self._entry_directory(fingerprint, identity)
        return (
            fingerprint,
            directory,
            directory / f"audio.{request.audio_format}",
            directory / "metadata.json",
        )

    def validate_cached(
        self,
        request: TtsRequest,
        identity: ProviderIdentity,
    ) -> TtsCacheEntry:
        """Validate one entry using only local bytes and supplied identity."""

        fingerprint, directory, media_path, metadata_path = self._paths(
            request, identity
        )
        if not directory.is_dir():
            raise TtsCacheValidationError(
                f"TTS cache entry is missing: {directory}"
            )
        if not media_path.is_file() or not metadata_path.is_file():
            raise TtsCacheValidationError(
                f"TTS cache entry is incomplete: {directory}"
            )
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise TtsCacheValidationError(
                f"TTS cache metadata is unreadable: {metadata_path}: {error}"
            ) from error
        if not isinstance(metadata, dict):
            raise TtsCacheValidationError("TTS cache metadata must be an object")

        expected_payload = _cache_payload(request, identity)
        expected_keys = {
            "cache_schema_version",
            "fingerprint",
            "provider",
            "request",
            "media",
            "validation",
        }
        if set(metadata) != expected_keys:
            raise TtsCacheValidationError(
                "TTS cache metadata fields do not match schema v1"
            )
        if (
            metadata.get("cache_schema_version") != CACHE_SCHEMA_VERSION
            or metadata.get("fingerprint") != fingerprint
            or metadata.get("provider") != expected_payload["provider"]
            or metadata.get("request") != expected_payload["request"]
        ):
            raise TtsCacheValidationError(
                "TTS cache metadata disagrees with its content address"
            )
        stored_validation = metadata.get("validation")
        if not isinstance(stored_validation, dict) or set(stored_validation) != {
            "validator_id",
            "validator_version",
            "result",
        }:
            raise TtsCacheValidationError(
                "TTS cache validation metadata is malformed"
            )
        if not all(
            isinstance(stored_validation.get(key), str)
            and bool(stored_validation[key])
            for key in ("validator_id", "validator_version")
        ):
            raise TtsCacheValidationError(
                "TTS cache validation identity is malformed"
            )
        try:
            _canonical_json(stored_validation.get("result"))
        except (TypeError, ValueError) as error:
            raise TtsCacheValidationError(
                "stored TTS validation result is not JSON data"
            ) from error
        media = metadata.get("media")
        if not isinstance(media, dict) or set(media) != {
            "filename",
            "bytes",
            "sha256",
        }:
            raise TtsCacheValidationError("TTS cache media metadata is malformed")
        if media.get("filename") != media_path.name:
            raise TtsCacheValidationError("TTS cache media filename drifted")
        size = media_path.stat().st_size
        if media.get("bytes") != size or media.get("sha256") != _sha256_file(
            media_path
        ):
            raise TtsCacheValidationError(
                "TTS cache media bytes disagree with metadata"
            )
        validation = dict(
            self.validator.validate(
                media_path,
                expected_format=request.audio_format,
            )
        )
        try:
            _canonical_json(validation)
        except (TypeError, ValueError) as error:
            raise TtsCacheValidationError(
                "audio validator returned non-JSON metadata"
            ) from error
        return TtsCacheEntry(
            fingerprint=fingerprint,
            entry_directory=directory,
            media_path=media_path,
            metadata_path=metadata_path,
            metadata=metadata,
            validation=validation,
            cache_hit=True,
        )

    def lookup(
        self,
        request: TtsRequest,
        identity: ProviderIdentity,
    ) -> TtsCacheEntry | None:
        """Return a locally valid entry, treating corruption as a cache miss."""

        try:
            return self.validate_cached(request, identity)
        except TtsCacheValidationError:
            return None

    def _write_metadata(
        self,
        path: Path,
        metadata: dict[str, object],
    ) -> None:
        temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.partial")
        try:
            with temporary.open("x", encoding="utf-8", newline="\n") as output:
                output.write(
                    json.dumps(
                        metadata,
                        ensure_ascii=False,
                        sort_keys=True,
                        indent=2,
                        allow_nan=False,
                    )
                )
                output.write("\n")
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary, path)
        finally:
            if temporary.exists():
                temporary.unlink()

    def _publish(
        self,
        staged_directory: Path,
        *,
        request: TtsRequest,
        identity: ProviderIdentity,
    ) -> TtsCacheEntry:
        fingerprint, final_directory, _, _ = self._paths(request, identity)
        final_directory.parent.mkdir(parents=True, exist_ok=True)

        existing = self.lookup(request, identity)
        if existing is not None:
            shutil.rmtree(staged_directory)
            return existing

        quarantine: Path | None = None
        if final_directory.exists():
            quarantine_root = self.root / ".quarantine"
            quarantine_root.mkdir(parents=True, exist_ok=True)
            quarantine = quarantine_root / (
                f"{fingerprint}.{uuid.uuid4().hex}.invalid"
            )
            os.replace(final_directory, quarantine)
        try:
            os.replace(staged_directory, final_directory)
        except BaseException:
            if quarantine is not None and quarantine.exists():
                os.replace(quarantine, final_directory)
            raise

        try:
            entry = self.validate_cached(request, identity)
        except BaseException:
            broken_root = self.root / ".quarantine"
            broken_root.mkdir(parents=True, exist_ok=True)
            broken = broken_root / (
                f"{fingerprint}.{uuid.uuid4().hex}.publish-failed"
            )
            if final_directory.exists():
                os.replace(final_directory, broken)
            if quarantine is not None and quarantine.exists():
                os.replace(quarantine, final_directory)
            raise
        return replace(entry, cache_hit=False)

    def get_or_create(
        self,
        request: TtsRequest,
        provider: TtsProvider,
        *,
        offline: bool = False,
        max_attempts: int = 3,
        retry_backoff_seconds: float = 1.0,
        sleep: Callable[[float], None] = time.sleep,
    ) -> TtsCacheEntry:
        """Return cached audio or synthesize, validate, and atomically publish."""

        if not isinstance(offline, bool):
            raise ValueError("offline must be boolean")
        if (
            isinstance(max_attempts, bool)
            or not isinstance(max_attempts, int)
            or not 1 <= max_attempts <= MAX_SYNTHESIS_ATTEMPTS
        ):
            raise ValueError(
                f"max_attempts must be in 1..{MAX_SYNTHESIS_ATTEMPTS}"
            )
        if (
            isinstance(retry_backoff_seconds, bool)
            or not isinstance(retry_backoff_seconds, (int, float))
            or not 0 <= retry_backoff_seconds <= MAX_RETRY_BACKOFF_SECONDS
        ):
            raise ValueError(
                "retry_backoff_seconds must be in "
                f"0..{MAX_RETRY_BACKOFF_SECONDS}"
            )
        identity = provider.identity
        cached = self.lookup(request, identity)
        if cached is not None:
            return cached
        if offline:
            fingerprint = self.fingerprint(request, identity)
            raise TtsOfflineCacheMissError(
                "offline TTS cache validation found no valid entry: "
                f"{fingerprint}"
            )

        fingerprint, final_directory, _, _ = self._paths(request, identity)
        staging_root = self.root / ".staging"
        staging_root.mkdir(parents=True, exist_ok=True)
        failures: list[str] = []
        for attempt in range(1, max_attempts + 1):
            staged_directory = staging_root / (
                f"{fingerprint}.{os.getpid()}.{uuid.uuid4().hex}.attempt-{attempt}"
            )
            staged_directory.mkdir()
            staged_media = staged_directory / f"audio.{request.audio_format}"
            staged_metadata = staged_directory / "metadata.json"
            try:
                provider.synthesize(request, staged_media)
                validation = dict(
                    self.validator.validate(
                        staged_media,
                        expected_format=request.audio_format,
                    )
                )
                _canonical_json(validation)
                media_size = staged_media.stat().st_size
                metadata = {
                    "cache_schema_version": CACHE_SCHEMA_VERSION,
                    "fingerprint": fingerprint,
                    "provider": _cache_payload(request, identity)["provider"],
                    "request": request.cache_payload(),
                    "media": {
                        "filename": staged_media.name,
                        "bytes": media_size,
                        "sha256": _sha256_file(staged_media),
                    },
                    "validation": {
                        "validator_id": self.validator.validator_id,
                        "validator_version": self.validator.validator_version,
                        "result": validation,
                    },
                }
                self._write_metadata(staged_metadata, metadata)
                return self._publish(
                    staged_directory,
                    request=request,
                    identity=identity,
                )
            except Exception as error:
                failures.append(
                    f"attempt {attempt}: {type(error).__name__}: {error}"
                )
            finally:
                if staged_directory.exists():
                    shutil.rmtree(staged_directory)
            if attempt < max_attempts:
                sleep(float(retry_backoff_seconds) * attempt)

        if final_directory.exists() and self.lookup(request, identity) is not None:
            return self.validate_cached(request, identity)
        raise TtsSynthesisError(
            f"TTS provider {identity.provider_id}@{identity.tool_version} "
            f"failed after {max_attempts} attempts: {'; '.join(failures)}"
        )


__all__ = [
    "BuiltinAudioValidator",
    "CACHE_SCHEMA_VERSION",
    "TtsCache",
    "TtsCacheEntry",
    "tts_fingerprint",
]
