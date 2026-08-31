"""Provider-neutral text-to-speech contracts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Mapping, Protocol, runtime_checkable

from ..errors import PromoToolchainError


_FORMAT_RE = re.compile(r"[a-z0-9][a-z0-9._-]{0,15}\Z")


class TtsError(PromoToolchainError):
    """Base error for reusable narration synthesis."""


class TtsProviderUnavailableError(TtsError):
    """The selected optional provider runtime is unavailable."""


class TtsCacheValidationError(TtsError):
    """A content-addressed cache entry failed offline validation."""


class TtsOfflineCacheMissError(TtsError):
    """Offline mode found no valid cache entry and refused network work."""


class TtsSynthesisError(TtsError):
    """All bounded provider attempts failed."""


def _required_text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value


@dataclass(frozen=True)
class ProviderIdentity:
    """The output-producing tool identity included in every cache key."""

    provider_id: str
    tool_version: str

    def __post_init__(self) -> None:
        _required_text(self.provider_id, "provider_id")
        _required_text(self.tool_version, "tool_version")


@dataclass(frozen=True)
class TtsRequest:
    """All caller-controlled inputs that can change synthesized audio."""

    text: str
    voice: str
    rate: str = "+0%"
    pitch: str = "+0Hz"
    volume: str = "+0%"
    audio_format: str = "mp3"
    cache_salt: str = ""

    def __post_init__(self) -> None:
        _required_text(self.text, "text")
        _required_text(self.voice, "voice")
        _required_text(self.rate, "rate")
        _required_text(self.pitch, "pitch")
        _required_text(self.volume, "volume")
        if (
            not isinstance(self.audio_format, str)
            or _FORMAT_RE.fullmatch(self.audio_format) is None
        ):
            raise ValueError(
                "audio_format must be a short lowercase filename token"
            )
        if not isinstance(self.cache_salt, str):
            raise ValueError("cache_salt must be a string")

    def cache_payload(self) -> dict[str, str]:
        return {
            "text": self.text,
            "voice": self.voice,
            "rate": self.rate,
            "pitch": self.pitch,
            "volume": self.volume,
            "audio_format": self.audio_format,
            "cache_salt": self.cache_salt,
        }


@runtime_checkable
class TtsProvider(Protocol):
    """A provider writes exactly one requested audio file."""

    @property
    def identity(self) -> ProviderIdentity: ...

    def synthesize(self, request: TtsRequest, destination: Path) -> None: ...


@runtime_checkable
class AudioValidator(Protocol):
    """Offline validator run before and after cache publication."""

    @property
    def validator_id(self) -> str: ...

    @property
    def validator_version(self) -> str: ...

    def validate(
        self, path: Path, *, expected_format: str
    ) -> Mapping[str, object]: ...


__all__ = [
    "AudioValidator",
    "ProviderIdentity",
    "TtsCacheValidationError",
    "TtsError",
    "TtsOfflineCacheMissError",
    "TtsProvider",
    "TtsProviderUnavailableError",
    "TtsRequest",
    "TtsSynthesisError",
]
