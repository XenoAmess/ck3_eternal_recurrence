"""Optional ``edge-tts`` provider adapter."""

from __future__ import annotations

import importlib
import importlib.metadata
from pathlib import Path
from types import ModuleType

from .provider import (
    ProviderIdentity,
    TtsProviderUnavailableError,
    TtsRequest,
)


class EdgeTtsProvider:
    """Lazy Edge TTS adapter with an injectable module for deterministic tests."""

    def __init__(
        self,
        *,
        module: ModuleType | object | None = None,
        tool_version: str | None = None,
    ) -> None:
        self._module = module
        self._import_error: Exception | None = None
        if tool_version is None:
            try:
                tool_version = importlib.metadata.version("edge-tts")
            except importlib.metadata.PackageNotFoundError as error:
                self._import_error = error
        if not isinstance(tool_version, str) or not tool_version.strip():
            self._identity: ProviderIdentity | None = None
        else:
            self._identity = ProviderIdentity("edge-tts", tool_version.strip())

    @property
    def identity(self) -> ProviderIdentity:
        if self._identity is None:
            raise TtsProviderUnavailableError(
                "edge-tts is not installed; install the optional TTS runtime "
                "or use offline cache validation with an explicit "
                "ProviderIdentity"
            ) from self._import_error
        return self._identity

    def _runtime(self) -> object:
        if self._module is not None:
            return self._module
        try:
            self._module = importlib.import_module("edge_tts")
        except Exception as error:
            raise TtsProviderUnavailableError(
                f"edge-tts runtime import failed: {error}"
            ) from error
        return self._module

    def synthesize(self, request: TtsRequest, destination: Path) -> None:
        self.identity
        if request.audio_format != "mp3":
            raise ValueError("EdgeTtsProvider currently emits mp3 only")
        runtime = self._runtime()
        communicate = getattr(runtime, "Communicate", None)
        if not callable(communicate):
            raise TtsProviderUnavailableError(
                "edge-tts runtime does not expose Communicate"
            )
        communicator = communicate(
            request.text,
            request.voice,
            rate=request.rate,
            volume=request.volume,
            pitch=request.pitch,
        )
        save_sync = getattr(communicator, "save_sync", None)
        if not callable(save_sync):
            raise TtsProviderUnavailableError(
                "edge-tts Communicate does not expose save_sync"
            )
        save_sync(str(destination))


__all__ = ["EdgeTtsProvider"]
