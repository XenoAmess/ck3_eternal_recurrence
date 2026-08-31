"""Reusable narration providers and content-addressed cache."""

from .cache import (
    BuiltinAudioValidator,
    CACHE_SCHEMA_VERSION,
    TtsCache,
    TtsCacheEntry,
    tts_fingerprint,
)
from .edge import EdgeTtsProvider
from .provider import (
    AudioValidator,
    ProviderIdentity,
    TtsCacheValidationError,
    TtsError,
    TtsOfflineCacheMissError,
    TtsProvider,
    TtsProviderUnavailableError,
    TtsRequest,
    TtsSynthesisError,
)


__all__ = [
    "AudioValidator",
    "BuiltinAudioValidator",
    "CACHE_SCHEMA_VERSION",
    "EdgeTtsProvider",
    "ProviderIdentity",
    "TtsCache",
    "TtsCacheEntry",
    "TtsCacheValidationError",
    "TtsError",
    "TtsOfflineCacheMissError",
    "TtsProvider",
    "TtsProviderUnavailableError",
    "TtsRequest",
    "TtsSynthesisError",
    "tts_fingerprint",
]
