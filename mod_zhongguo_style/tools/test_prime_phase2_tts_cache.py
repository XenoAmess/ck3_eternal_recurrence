#!/usr/bin/env python3
"""Focused no-network tests for the Phase2 TTS cache-prime command."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import prime_phase2_tts_cache as prime
from xar_promo.tts import TtsRequest


class _Binding:
    def __init__(self) -> None:
        self.verified = False

    def to_mapping(self):
        return {"result": "GREEN", "sha256": "A" * 64}

    def verify_unchanged(self):
        self.verified = True


class Phase2TtsCachePrimeTests(unittest.TestCase):
    def test_validate_only_plans_missing_cache_without_writes_or_provider_call(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            config_path = root / "phase2-promo-character-project.json"
            config_path.write_text("{}\n", encoding="utf-8")
            cache_root = root / "must-not-exist"
            output = root / "must-not-exist.json"
            cue = SimpleNamespace(
                cue_id="reviewed-cue",
                narration={"zh-CN": "经过人工审阅的真实旁白。"},
            )
            config = SimpleNamespace(
                narration_locale="zh-CN",
                chapters=(
                    SimpleNamespace(chapter_id="phase2_minimal_recap", cues=(cue,)),
                ),
            )
            binding = _Binding()
            args = prime.parser().parse_args(
                (
                    "--cut",
                    "character-led",
                    "--project-config",
                    str(config_path),
                    "--media-preflight-report",
                    str(root / "media.json"),
                    "--expected-media-preflight-sha256",
                    "B" * 64,
                    "--tts-cache",
                    str(cache_root),
                    "--output",
                    str(output),
                    "--validate-only",
                )
            )
            with (
                mock.patch.object(prime, "load_phase2_project_config", return_value=config),
                mock.patch.object(prime, "_require_ready_authoring"),
                mock.patch.object(
                    prime,
                    "load_media_preflight_binding",
                    return_value=binding,
                ),
                mock.patch.object(
                    prime,
                    "build_narration_request",
                    return_value=TtsRequest(
                        "经过人工审阅的真实旁白。",
                        "zh-CN-XiaoxiaoNeural",
                    ),
                ),
                mock.patch.object(
                    prime.EdgeTtsProvider,
                    "synthesize",
                    side_effect=AssertionError("validate-only contacted Edge TTS"),
                ),
            ):
                payload = prime.plan_or_prime(args)
            self.assertEqual("GREEN", payload["result"])
            self.assertEqual("missing", payload["entries"][0]["cache_state"])
            self.assertFalse(payload["execution_attestation"]["synthesis_performed"])
            self.assertTrue(binding.verified)
            self.assertFalse(cache_root.exists())
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
