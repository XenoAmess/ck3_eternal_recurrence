from __future__ import annotations

import copy
from dataclasses import replace
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_promo.tts import (  # noqa: E402
    EdgeTtsProvider,
    ProviderIdentity,
    TtsCache,
    TtsCacheValidationError,
    TtsOfflineCacheMissError,
    TtsProviderUnavailableError,
    TtsRequest,
    TtsSynthesisError,
    tts_fingerprint,
)


class _FakeValidator:
    validator_id = "test-audio-validator"
    validator_version = "1"

    def validate(
        self, path: Path, *, expected_format: str
    ) -> dict[str, object]:
        payload = path.read_bytes()
        if not payload.startswith(b"VALID-AUDIO:"):
            raise TtsCacheValidationError("test audio signature is invalid")
        return {
            "format": expected_format,
            "bytes": len(payload),
            "signature": "test-valid",
        }


class _FakeProvider:
    def __init__(
        self,
        outcomes: list[str],
        *,
        provider_id: str = "fake-tts",
        tool_version: str = "1.0.0",
    ) -> None:
        self._identity = ProviderIdentity(provider_id, tool_version)
        self.outcomes = list(outcomes)
        self.calls: list[tuple[TtsRequest, Path]] = []

    @property
    def identity(self) -> ProviderIdentity:
        return self._identity

    def synthesize(self, request: TtsRequest, destination: Path) -> None:
        self.calls.append((copy.deepcopy(request), destination))
        if not self.outcomes:
            raise AssertionError("fake provider has no outcome")
        outcome = self.outcomes.pop(0)
        if outcome == "raise-after-partial":
            destination.write_bytes(b"PARTIAL")
            raise RuntimeError("transient provider failure")
        if outcome == "invalid":
            destination.write_bytes(b"NOT-AUDIO")
            return
        if outcome == "valid":
            destination.write_bytes(
                b"VALID-AUDIO:" + request.text.encode("utf-8")
            )
            return
        raise AssertionError(f"unknown fake outcome {outcome!r}")


class TtsCacheTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.cache_root = Path(self.temporary.name) / "tts-cache"
        self.cache = TtsCache(
            self.cache_root,
            validator=_FakeValidator(),
        )
        self.request = TtsRequest(
            text="A release narration with punctuation.",
            voice="example-VoiceNeural",
            rate="+3%",
            pitch="-2Hz",
            volume="+0%",
        )
        self.identity = ProviderIdentity("fake-tts", "1.0.0")

    def test_fingerprint_covers_all_output_inputs_and_tool_version(self) -> None:
        baseline = tts_fingerprint(self.request, self.identity)
        variants = (
            replace(self.request, text=self.request.text + " Again."),
            replace(self.request, voice="another-VoiceNeural"),
            replace(self.request, rate="-5%"),
            replace(self.request, pitch="+7Hz"),
            replace(self.request, volume="-10%"),
            replace(self.request, cache_salt="take-2"),
        )
        for variant in variants:
            with self.subTest(variant=variant):
                self.assertNotEqual(
                    baseline,
                    tts_fingerprint(variant, self.identity),
                )
        self.assertNotEqual(
            baseline,
            tts_fingerprint(
                self.request,
                ProviderIdentity("fake-tts", "1.0.1"),
            ),
        )

    def test_cache_hit_is_content_addressed_and_provider_is_not_recalled(
        self,
    ) -> None:
        provider = _FakeProvider(["valid"])
        created = self.cache.get_or_create(self.request, provider)
        cached = self.cache.get_or_create(self.request, provider)

        self.assertFalse(created.cache_hit)
        self.assertTrue(cached.cache_hit)
        self.assertEqual(created.fingerprint, cached.fingerprint)
        self.assertEqual(1, len(provider.calls))
        self.assertEqual(
            created.fingerprint,
            created.entry_directory.name,
        )
        self.assertEqual(
            b"VALID-AUDIO:" + self.request.text.encode("utf-8"),
            created.media_path.read_bytes(),
        )
        self.assertEqual(
            self.request.voice,
            created.metadata["request"]["voice"],
        )
        self.assertEqual(
            self.identity.tool_version,
            created.metadata["provider"]["tool_version"],
        )

    def test_retry_is_bounded_and_partial_failures_never_publish(self) -> None:
        provider = _FakeProvider(
            ["raise-after-partial", "raise-after-partial"]
        )
        sleeps: list[float] = []
        with self.assertRaises(TtsSynthesisError):
            self.cache.get_or_create(
                self.request,
                provider,
                max_attempts=2,
                retry_backoff_seconds=0.25,
                sleep=sleeps.append,
            )

        self.assertEqual(2, len(provider.calls))
        self.assertEqual([0.25], sleeps)
        self.assertIsNone(self.cache.lookup(self.request, provider.identity))
        staging = self.cache_root / ".staging"
        self.assertTrue(staging.is_dir())
        self.assertEqual([], list(staging.iterdir()))

    def test_invalid_audio_is_retried_then_atomically_published(self) -> None:
        provider = _FakeProvider(
            ["raise-after-partial", "invalid", "valid"]
        )
        sleeps: list[float] = []
        entry = self.cache.get_or_create(
            self.request,
            provider,
            max_attempts=3,
            retry_backoff_seconds=0.5,
            sleep=sleeps.append,
        )

        self.assertEqual(3, len(provider.calls))
        self.assertEqual([0.5, 1.0], sleeps)
        self.assertFalse(entry.cache_hit)
        self.assertEqual("test-valid", entry.validation["signature"])
        self.assertTrue(entry.metadata_path.is_file())
        self.assertFalse(
            any((self.cache_root / ".staging").iterdir())
        )

    def test_offline_validation_never_calls_provider(self) -> None:
        online = _FakeProvider(["valid"])
        created = self.cache.get_or_create(self.request, online)
        offline = _FakeProvider([])

        validated = self.cache.validate_cached(
            self.request,
            ProviderIdentity("fake-tts", "1.0.0"),
        )
        reused = self.cache.get_or_create(
            self.request,
            offline,
            offline=True,
        )
        self.assertEqual(created.fingerprint, validated.fingerprint)
        self.assertEqual(created.fingerprint, reused.fingerprint)
        self.assertEqual([], offline.calls)

        missing = replace(self.request, text="Not cached")
        with self.assertRaises(TtsOfflineCacheMissError):
            self.cache.get_or_create(missing, offline, offline=True)
        self.assertEqual([], offline.calls)

    def test_tamper_is_detected_offline_and_failed_retry_keeps_old_bytes(
        self,
    ) -> None:
        created = self.cache.get_or_create(
            self.request,
            _FakeProvider(["valid"]),
        )
        created.media_path.write_bytes(b"TAMPERED-BUT-PRESERVED")
        with self.assertRaises(TtsCacheValidationError):
            self.cache.validate_cached(self.request, self.identity)

        failing = _FakeProvider(["raise-after-partial"])
        with self.assertRaises(TtsSynthesisError):
            self.cache.get_or_create(
                self.request,
                failing,
                max_attempts=1,
            )
        self.assertEqual(
            b"TAMPERED-BUT-PRESERVED",
            created.media_path.read_bytes(),
        )

    def test_valid_retry_replaces_corrupt_entry_and_quarantines_old_bytes(
        self,
    ) -> None:
        created = self.cache.get_or_create(
            self.request,
            _FakeProvider(["valid"]),
        )
        created.media_path.write_bytes(b"CORRUPT-OLD-BYTES")
        repaired = self.cache.get_or_create(
            self.request,
            _FakeProvider(["valid"]),
            max_attempts=1,
        )

        self.assertFalse(repaired.cache_hit)
        self.assertTrue(repaired.media_path.read_bytes().startswith(b"VALID-AUDIO:"))
        quarantined = list((self.cache_root / ".quarantine").glob("*.invalid"))
        self.assertEqual(1, len(quarantined))
        self.assertEqual(
            b"CORRUPT-OLD-BYTES",
            (quarantined[0] / "audio.mp3").read_bytes(),
        )


class EdgeTtsProviderTests(unittest.TestCase):
    def test_injected_runtime_receives_exact_request_without_locale_defaults(
        self,
    ) -> None:
        calls: list[dict[str, object]] = []

        class Communicator:
            def save_sync(self, destination: str) -> None:
                calls[-1]["destination"] = destination
                Path(destination).write_bytes(b"ID3\x04\x00\x00")

        def communicate(
            text: str,
            voice: str,
            *,
            rate: str,
            volume: str,
            pitch: str,
        ) -> Communicator:
            calls.append(
                {
                    "text": text,
                    "voice": voice,
                    "rate": rate,
                    "volume": volume,
                    "pitch": pitch,
                }
            )
            return Communicator()

        runtime = SimpleNamespace(Communicate=communicate)
        provider = EdgeTtsProvider(module=runtime, tool_version="test-edge-1")
        request = TtsRequest(
            text="Any language is supplied by the caller.",
            voice="caller-selected-VoiceNeural",
            rate="-8%",
            pitch="+4Hz",
            volume="-3%",
        )
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "narration.mp3"
            provider.synthesize(request, destination)
            self.assertTrue(destination.is_file())

        self.assertEqual("edge-tts", provider.identity.provider_id)
        self.assertEqual("test-edge-1", provider.identity.tool_version)
        self.assertEqual(
            {
                "text": request.text,
                "voice": request.voice,
                "rate": request.rate,
                "volume": request.volume,
                "pitch": request.pitch,
                "destination": str(destination),
            },
            calls[0],
        )

    def test_optional_runtime_failure_is_deferred_until_synthesis(self) -> None:
        provider = EdgeTtsProvider(tool_version="test-edge-1")
        request = TtsRequest(text="Deferred import", voice="caller-voice")
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "narration.mp3"
            with mock.patch(
                "xar_promo.tts.edge.importlib.import_module",
                side_effect=ModuleNotFoundError("edge_tts unavailable"),
            ):
                with self.assertRaises(TtsProviderUnavailableError):
                    provider.synthesize(request, destination)
        self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()
