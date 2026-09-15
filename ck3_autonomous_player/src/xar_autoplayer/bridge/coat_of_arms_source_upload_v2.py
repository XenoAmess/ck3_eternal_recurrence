"""Bounded fail-closed chunk assembly for large CK3 coat-of-arms source."""

from __future__ import annotations

import base64
from dataclasses import dataclass, field
import hashlib
import secrets
import threading
import time
from typing import Callable, Final

from .coat_of_arms_source_probe_contract import (
    COAT_OF_ARMS_SOURCE_V2_MAX_BYTES,
)

COAT_OF_ARMS_SOURCE_UPLOAD_V2_MAX_SOURCE_BYTES: Final = (
    COAT_OF_ARMS_SOURCE_V2_MAX_BYTES
)
COAT_OF_ARMS_SOURCE_UPLOAD_V2_MAX_CHUNK_BYTES: Final = 48 * 1024
COAT_OF_ARMS_SOURCE_UPLOAD_V2_MAX_CHUNKS: Final = 32
COAT_OF_ARMS_SOURCE_UPLOAD_V2_MAX_SESSIONS: Final = 2
COAT_OF_ARMS_SOURCE_UPLOAD_V2_MAX_BUFFERED_BYTES: Final = 768 * 1024
COAT_OF_ARMS_SOURCE_UPLOAD_V2_TTL_SECONDS: Final = 60
COAT_OF_ARMS_SOURCE_UPLOAD_V2_ENCODING: Final = "base64"


@dataclass
class _Upload:
    upload_id: str
    generation: int
    total_bytes: int
    source_sha256: str
    chunk_count: int
    expected_revision: int
    apply: bool
    expected_game_version: str
    expected_executable_sha256: str
    binding: dict[str, object]
    created_monotonic: float
    expires_monotonic: float
    chunks: list[bytes] = field(default_factory=list)
    buffered_bytes: int = 0


class CoatOfArmsSourceUploadManagerV2:
    """Own short-lived uploads; any protocol conflict destroys the session."""

    def __init__(
        self,
        *,
        clock: Callable[[], float] = time.monotonic,
        token_factory: Callable[[], str] = lambda: secrets.token_hex(16),
    ) -> None:
        self._clock = clock
        self._token_factory = token_factory
        self._lock = threading.Lock()
        self._generation = 0
        self._uploads: dict[str, _Upload] = {}

    def begin(
        self,
        *,
        total_bytes: object,
        source_sha256: object,
        chunk_count: object,
        chunk_encoding: object,
        expected_revision: object,
        apply: object,
        expected_game_version: object,
        expected_executable_sha256: object,
        binding: dict[str, object],
    ) -> dict[str, object]:
        size = _integer(
            total_bytes,
            "total_bytes",
            1,
            COAT_OF_ARMS_SOURCE_UPLOAD_V2_MAX_SOURCE_BYTES,
        )
        digest = _sha256(source_sha256, "source_sha256")
        count = _integer(
            chunk_count,
            "chunk_count",
            1,
            COAT_OF_ARMS_SOURCE_UPLOAD_V2_MAX_CHUNKS,
        )
        if count * COAT_OF_ARMS_SOURCE_UPLOAD_V2_MAX_CHUNK_BYTES < size:
            raise ValueError(
                "chunk_count cannot carry total_bytes within the chunk limit"
            )
        if chunk_encoding != COAT_OF_ARMS_SOURCE_UPLOAD_V2_ENCODING:
            raise ValueError("chunk_encoding must be base64")
        revision = _integer(expected_revision, "expected_revision", 0, 2**64 - 1)
        if not isinstance(apply, bool):
            raise ValueError("apply must be boolean")
        game_version = _nonempty(expected_game_version, "expected_game_version", 32)
        executable_sha256 = _sha256(
            expected_executable_sha256,
            "expected_executable_sha256",
        )
        now = self._clock()
        with self._lock:
            self._expire(now)
            if len(self._uploads) >= COAT_OF_ARMS_SOURCE_UPLOAD_V2_MAX_SESSIONS:
                raise ValueError("coat-of-arms upload session budget exhausted")
            # Reserve each session's complete declared payload at begin time.
            # Looking only at bytes received so far lets two 512 KiB sessions
            # pass a 768 KiB process budget before either sends its first chunk.
            reserved_bytes = sum(
                item.total_bytes for item in self._uploads.values()
            )
            if (
                reserved_bytes + size
                > COAT_OF_ARMS_SOURCE_UPLOAD_V2_MAX_BUFFERED_BYTES
            ):
                raise ValueError("coat-of-arms upload byte budget exhausted")
            upload_id = _identifier(self._token_factory())
            if upload_id in self._uploads:
                raise RuntimeError("upload token factory returned an invalid or duplicate id")
            self._generation += 1
            upload = _Upload(
                upload_id=upload_id,
                generation=self._generation,
                total_bytes=size,
                source_sha256=digest,
                chunk_count=count,
                expected_revision=revision,
                apply=apply,
                expected_game_version=game_version,
                expected_executable_sha256=executable_sha256,
                binding=dict(binding),
                created_monotonic=now,
                expires_monotonic=now + COAT_OF_ARMS_SOURCE_UPLOAD_V2_TTL_SECONDS,
            )
            self._uploads[upload_id] = upload
            return self._receipt(upload, "receiving")

    def append(
        self,
        *,
        upload_id: object,
        generation: object,
        chunk_index: object,
        chunk_count: object,
        chunk_encoding: object,
        chunk_bytes: object,
        chunk_sha256: object,
        chunk_base64: object,
        source_sha256: object,
        expected_revision: object,
        apply: object,
        expected_game_version: object,
        expected_executable_sha256: object,
    ) -> dict[str, object]:
        identifier = _identifier(upload_id)
        now = self._clock()
        with self._lock:
            self._expire(now)
            upload = self._uploads.get(identifier)
            if upload is None:
                raise ValueError("coat-of-arms upload session is unavailable or expired")
            try:
                self._match(upload, generation, chunk_count, source_sha256)
                if (
                    _integer(
                        expected_revision,
                        "expected_revision",
                        0,
                        2**64 - 1,
                    )
                    != upload.expected_revision
                ):
                    raise ValueError("upload revision changed")
                if not isinstance(apply, bool) or apply is not upload.apply:
                    raise ValueError("upload apply intent changed")
                if (
                    _nonempty(
                        expected_game_version,
                        "expected_game_version",
                        32,
                    )
                    != upload.expected_game_version
                ):
                    raise ValueError("upload game version changed")
                if (
                    _sha256(
                        expected_executable_sha256,
                        "expected_executable_sha256",
                    )
                    != upload.expected_executable_sha256
                ):
                    raise ValueError("upload executable hash changed")
                index = _integer(chunk_index, "chunk_index", 0, upload.chunk_count - 1)
                if index != len(upload.chunks):
                    raise ValueError("chunk_index is duplicate or out of order")
                if chunk_encoding != COAT_OF_ARMS_SOURCE_UPLOAD_V2_ENCODING:
                    raise ValueError("chunk_encoding must be base64")
                declared_bytes = _integer(
                    chunk_bytes,
                    "chunk_bytes",
                    1,
                    COAT_OF_ARMS_SOURCE_UPLOAD_V2_MAX_CHUNK_BYTES,
                )
                encoded = _nonempty(
                    chunk_base64,
                    "chunk_base64",
                    4 * ((declared_bytes + 2) // 3),
                )
                try:
                    decoded = base64.b64decode(encoded, validate=True)
                except Exception as error:
                    raise ValueError("chunk_base64 is not canonical base64") from error
                if base64.b64encode(decoded).decode("ascii") != encoded:
                    raise ValueError("chunk_base64 is not canonical base64")
                if (
                    len(decoded) != declared_bytes
                    or hashlib.sha256(decoded).hexdigest()
                    != _sha256(chunk_sha256, "chunk_sha256")
                ):
                    raise ValueError("chunk length or SHA-256 does not match")
                if b"\0" in decoded or any(byte >= 0x80 for byte in decoded):
                    raise ValueError(
                        "coat-of-arms chunks must contain NUL-free ASCII wire bytes"
                    )
                if upload.buffered_bytes + len(decoded) > upload.total_bytes:
                    raise ValueError("chunks exceed declared total_bytes")
                upload.chunks.append(decoded)
                upload.buffered_bytes += len(decoded)
                return self._receipt(
                    upload,
                    "ready" if len(upload.chunks) == upload.chunk_count else "receiving",
                )
            except Exception:
                self._uploads.pop(identifier, None)
                raise

    def finalize(
        self,
        *,
        upload_id: object,
        generation: object,
        chunk_count: object,
        source_sha256: object,
        expected_revision: object,
        apply: object,
        expected_game_version: object,
        expected_executable_sha256: object,
    ) -> tuple[str, dict[str, object], dict[str, object]]:
        identifier = _identifier(upload_id)
        now = self._clock()
        with self._lock:
            self._expire(now)
            upload = self._uploads.pop(identifier, None)
            if upload is None:
                raise ValueError("coat-of-arms upload session is unavailable or expired")
            self._match(upload, generation, chunk_count, source_sha256)
            if (
                _integer(
                    expected_revision,
                    "expected_revision",
                    0,
                    2**64 - 1,
                )
                != upload.expected_revision
            ):
                raise ValueError("upload revision changed")
            if not isinstance(apply, bool) or apply is not upload.apply:
                raise ValueError("upload apply intent changed")
            if (
                _nonempty(
                    expected_game_version,
                    "expected_game_version",
                    32,
                )
                != upload.expected_game_version
            ):
                raise ValueError("upload game version changed")
            if (
                _sha256(
                    expected_executable_sha256,
                    "expected_executable_sha256",
                )
                != upload.expected_executable_sha256
            ):
                raise ValueError("upload executable hash changed")
            if (
                len(upload.chunks) != upload.chunk_count
                or upload.buffered_bytes != upload.total_bytes
            ):
                raise ValueError("upload is incomplete")
            payload = b"".join(upload.chunks)
            if hashlib.sha256(payload).hexdigest() != upload.source_sha256:
                raise ValueError("assembled source SHA-256 does not match")
            source = payload.decode("ascii")
            canonical = (
                source.replace("\r\n", "\n")
                .replace("\r", "\n")
                .replace("\n", "\r\n")
            )
            if canonical != source:
                raise ValueError("large source must already use canonical CRLF wire bytes")
            return source, self._receipt(upload, "committed"), dict(upload.binding)

    def abort(self, *, upload_id: object, generation: object) -> dict[str, object]:
        identifier = _identifier(upload_id)
        with self._lock:
            self._expire(self._clock())
            upload = self._uploads.pop(identifier, None)
            if upload is None:
                raise ValueError("coat-of-arms upload session is unavailable or expired")
            if _integer(generation, "generation", 1, 2**64 - 1) != upload.generation:
                raise ValueError("upload generation changed")
            return self._receipt(upload, "aborted")

    def _expire(self, now: float) -> None:
        expired = [
            key
            for key, value in self._uploads.items()
            if value.expires_monotonic <= now
        ]
        for identifier in expired:
            self._uploads.pop(identifier, None)

    @staticmethod
    def _match(
        upload: _Upload,
        generation: object,
        chunk_count: object,
        source_sha256: object,
    ) -> None:
        if _integer(generation, "generation", 1, 2**64 - 1) != upload.generation:
            raise ValueError("upload generation changed")
        if (
            _integer(
                chunk_count,
                "chunk_count",
                1,
                COAT_OF_ARMS_SOURCE_UPLOAD_V2_MAX_CHUNKS,
            )
            != upload.chunk_count
        ):
            raise ValueError("upload chunk_count changed")
        if _sha256(source_sha256, "source_sha256") != upload.source_sha256:
            raise ValueError("upload source hash changed")

    @staticmethod
    def _receipt(upload: _Upload, status: str) -> dict[str, object]:
        return {
            "schema": "coat-of-arms-source-upload-v2",
            "schema_version": 2,
            "status": status,
            "upload_id": upload.upload_id,
            "generation": upload.generation,
            "total_bytes": upload.total_bytes,
            "source_sha256": upload.source_sha256,
            "chunk_count": upload.chunk_count,
            "received_chunks": len(upload.chunks),
            "received_bytes": upload.buffered_bytes,
            "chunk_encoding": COAT_OF_ARMS_SOURCE_UPLOAD_V2_ENCODING,
            "max_chunk_bytes": COAT_OF_ARMS_SOURCE_UPLOAD_V2_MAX_CHUNK_BYTES,
            "timeout_seconds": COAT_OF_ARMS_SOURCE_UPLOAD_V2_TTL_SECONDS,
            "expected_revision": upload.expected_revision,
            "apply": upload.apply,
            "expected_game_version": upload.expected_game_version,
            "expected_executable_sha256": upload.expected_executable_sha256,
            "binding": dict(upload.binding),
        }


def _integer(value: object, label: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise ValueError(f"{label} must be an integer in {minimum}..{maximum}")
    return value


def _nonempty(value: object, label: str, maximum: int) -> str:
    if not isinstance(value, str) or not value or len(value) > maximum:
        raise ValueError(f"{label} must be a non-empty bounded string")
    return value


def _sha256(value: object, label: str) -> str:
    text = _nonempty(value, label, 64).lower()
    if len(text) != 64 or any(character not in "0123456789abcdef" for character in text):
        raise ValueError(f"{label} must be a lowercase or uppercase SHA-256")
    return text


def _identifier(value: object) -> str:
    text = _nonempty(value, "upload_id", 32)
    if len(text) != 32 or any(character not in "0123456789abcdef" for character in text):
        raise ValueError("upload_id is invalid")
    return text
