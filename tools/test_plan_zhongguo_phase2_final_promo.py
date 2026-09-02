from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest


TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import plan_zhongguo_phase2_final_promo as planner  # noqa: E402


class FinalPromoRunbookTests(unittest.TestCase):
    def test_missing_footage_is_typed_and_planning_generates_no_media(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            media = root / "media.json"
            media.write_text(
                json.dumps(
                    {
                        "result": "GREEN",
                        "project": {"chapters": 10},
                        "voice": {"id": planner.VOICE},
                        "subtitle_layout": {"tracks": [{"id": "zh-CN"}, {"id": "en"}]},
                    }
                ),
                encoding="utf-8",
            )
            media_sha = hashlib.sha256(media.read_bytes()).hexdigest()
            tts = root / "tts-must-not-be-created"
            work = root / "work-must-not-be-created"
            runbook = planner.build_runbook(
                project_config=planner.DEFAULT_CONFIG,
                authoring_ledger=planner.DEFAULT_AUTHORING_LEDGER,
                promo_tool_root=Path(r"Z:\workspace\xar_promo_toolchain"),
                capture_root=root / "footage-missing",
                seed_preflight_report=None,
                media_preflight_report=media,
                expected_media_preflight_sha256=media_sha,
                tts_cache=tts,
                work_dir=work,
                python=Path(sys.executable),
                ffmpeg="missing-ffmpeg-must-not-run",
                ffprobe="missing-ffprobe-must-not-run",
            )
            self.assertEqual(runbook["result"], "RED")
            self.assertEqual(runbook["reason_code"], "footage_pending")
            self.assertEqual(runbook["blockers"], ["footage_pending"])
            self.assertEqual(
                runbook["inputs"]["capture"]["kind"],
                "zg361_phase2_footage_intake",
            )
            self.assertEqual(
                runbook["inputs"]["capture"]["scope"],
                "phase2_media_entry_only_no_native_observer_schema",
            )
            self.assertEqual(
                runbook["inputs"]["capture"]["reason_code"],
                "footage_pending",
            )
            self.assertEqual(runbook["authoring_claim_ledger"]["result"], "GREEN")
            self.assertEqual(
                len(runbook["authoring_claim_ledger"]["claims"]), 10
            )
            self.assertEqual(len(runbook["fixed_contract"]["canonical_spans"]), 8)
            self.assertEqual(runbook["fixed_contract"]["chapter_count"], 10)
            self.assertEqual(runbook["fixed_contract"]["voice"], planner.VOICE)
            self.assertEqual(
                runbook["ordered_steps"][0]["id"],
                "fetch_and_verify_promo_origin_main",
            )
            self.assertTrue(runbook["ordered_steps"][0]["required_first"])
            self.assertEqual(
                [step["id"] for step in runbook["ordered_steps"] if step.get("human_pause")],
                [
                    "source_footage_human_review_1x",
                    "final_video_human_review_1x",
                ],
            )
            self.assertFalse(tts.exists())
            self.assertFalse(work.exists())
            self.assertFalse(runbook["execution_attestation"]["ffmpeg_started"])
            self.assertFalse(runbook["execution_attestation"]["candidate_generated"])

    def test_same_inputs_produce_identical_runbook(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            kwargs = dict(
                project_config=planner.DEFAULT_CONFIG,
                authoring_ledger=planner.DEFAULT_AUTHORING_LEDGER,
                promo_tool_root=Path(r"Z:\workspace\xar_promo_toolchain"),
                capture_root=None,
                seed_preflight_report=None,
                media_preflight_report=None,
                expected_media_preflight_sha256=None,
                tts_cache=root / "tts",
                work_dir=root / "work",
                python=Path(sys.executable),
                ffmpeg="ffmpeg",
                ffprobe="ffprobe",
            )
            first = planner.build_runbook(**kwargs)
            second = planner.build_runbook(**kwargs)
            self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
