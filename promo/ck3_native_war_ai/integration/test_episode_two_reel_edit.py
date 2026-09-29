"""Focused source and duration gates for the unsigned Episode 2 reel editor."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from war_ai_promo import episode_two_reel_edit as edit  # noqa: E402
from war_ai_promo.episode_two_second_half import CHAPTER_CARDS  # noqa: E402


REPLAY = {"E2-02": "A05", "E2-03": "A05", "E2-04": "039_040",
          "E2-05A": "020", "E2-05B": "070", "E2-05C": "036_038",
          "E2-06": "A01", "E2-07": "A01", "E2-09": "A05"}


def bound(path: Path) -> dict:
    return {"source": str(path), "bytes": 1, "sha256": "A" * 64}


def planned() -> dict:
    fake = bound(Path.cwd() / "fixture-absent")
    chapters = []
    for chapter, target in edit.TARGET_FRAMES.items():
        card_ids = CHAPTER_CARDS.get(chapter, ())
        frames = target - 30 * len(card_ids)
        attempt = f"{chapter}-real-attempt"
        capture = {"id": f"{chapter}-raw", "kind": "capture", "frames": frames,
                   "attempt_id": attempt, "span_id": f"{chapter}-span",
                   "bundle_root": str(Path.cwd() / attempt), "raw_width": 1920,
                   "raw_height": 1080, "begin_pts_seconds": "0",
                   "end_pts_seconds": str((frames - 1) / 30),
                   "source_label": f"{attempt} 原生录像",
                   "raw": {**fake, "sha256": f"{list(edit.TARGET_FRAMES).index(chapter)+1:064X}"},
                   "clean_span_audit": fake, "human_review": fake,
                   "pts_probe": fake, "recorder_final": fake,
                   "cold_load_save": fake, "cold_load_receipt": fake, "control": fake}
        cards = [{"id": f"{chapter}-{cid}", "kind": "still", "frames": 30,
                  "card_id": cid, "source_label": f"{cid} {REPLAY[cid]} 历史研究 非当前录制",
                  "image": fake, "origin": fake, "render_receipt": fake} for cid in card_ids]
        chapters.append({"id": chapter, "target_frames": target,
                         "segments": [capture, *cards]})
    return {"schema": edit.SCHEMA, "status": "reviewed-clean-spans-edit-planned",
            "synthetic": False, "human_signoff": "not-provided",
            "project_config": fake, "narration_script": fake,
            "subtitle_fragments": fake, "card_index": fake, "chapters": chapters}


class ReelEditTests(unittest.TestCase):
    def test_complete_shape_is_explicitly_unverified(self) -> None:
        result = edit.check_shape(planned())
        self.assertEqual(result["total_frames"], 1790 * 30)
        self.assertEqual(result["status"], "STRUCTURE_ONLY_UNVERIFIED_ORIGINALS")

    def test_missing_chapter_frames_or_machine_status_is_rejected(self) -> None:
        plan = planned()
        plan["chapters"][2]["segments"][0]["frames"] -= 1
        with self.assertRaisesRegex(ValueError, "frames do not cover"):
            edit.check_shape(plan)
        plan = planned()
        plan["status"] = "PTS_CANDIDATE_UNREVIEWED"
        with self.assertRaisesRegex(ValueError, "real, unsigned"):
            edit.check_shape(plan)

    def test_short_output_cannot_claim_a_long_source_interval(self) -> None:
        with self.assertRaisesRegex(ValueError, "full source PTS interval"):
            edit._capture_frame_budget(edit.Decimal("0"), edit.Decimal("100"), 30, "clip")
        with self.assertRaisesRegex(ValueError, "full source PTS interval"):
            edit._capture_frame_budget(edit.Decimal("0"), edit.Decimal("1"), 60, "clip")
        edit._capture_frame_budget(edit.Decimal("0"), edit.Decimal("1.966667"), 60, "clip")
        with self.assertRaisesRegex(ValueError, "full source PTS interval"):
            edit._capture_frame_budget(edit.Decimal("10"), edit.Decimal("12"), 60, "clip")
        edit._capture_frame_budget(edit.Decimal("10"), edit.Decimal("12"), 61, "clip")
        plan = planned()
        plan["chapters"][0]["segments"][0]["end_pts_seconds"] = "1000"
        with self.assertRaisesRegex(ValueError, "full source PTS interval"):
            edit.check_shape(plan)

    def test_cross_chapter_raw_reuse_requires_explicit_closing_recap(self) -> None:
        plan = planned()
        opening = plan["chapters"][0]["segments"][0]
        closing = plan["chapters"][-1]["segments"][0]
        closing["raw"] = opening["raw"]
        closing["end_pts_seconds"] = "59.966667"
        closing["frames"] = 1800
        plan["chapters"][-1]["segments"].append({"id": "closing-still", "kind": "still",
            "frames": 1050, "source_label": "E2 来源说明", "image": closing["raw"],
            "origin": closing["raw"], "render_receipt": closing["raw"]})
        with self.assertRaisesRegex(ValueError, "silently repeats"):
            edit.check_shape(plan)
        closing["recap_of"] = opening["id"]
        closing["source_label"] += " 回顾"
        self.assertEqual(edit.check_shape(plan)["total_frames"], 53700)

    def test_shared_endpoint_is_a_repeated_raw_frame(self) -> None:
        plan = planned()
        opening = plan["chapters"][0]["segments"][0]
        closing = plan["chapters"][-1]["segments"][0]
        closing["raw"] = opening["raw"]
        closing["begin_pts_seconds"] = opening["end_pts_seconds"]
        closing["end_pts_seconds"] = str(
            edit.Decimal(closing["begin_pts_seconds"]) + edit.Decimal(closing["frames"] - 1) / 30)
        with self.assertRaisesRegex(ValueError, "silently repeats"):
            edit.check_shape(plan)

    def test_unreviewed_clean_claim_rejected_before_adapter(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "source").mkdir()
            review = root / "source/human-review.json"
            review.write_text(json.dumps({"schema": "xar.war-promo.exact-span-human-review/v1",
                "reviewer": {"kind": "human"}, "review_scope": "full_raw_1x_and_exact_span_endpoints",
                "human_1x_full_raw_review_performed": False}), encoding="utf-8")
            clean = root / "clean.json"
            clean.write_text(json.dumps({"schema": "ck3-war-ai.episode02.clean-span-audit.v1",
                "result": "RED", "span_id": "a", "attempt_id": "real"}), encoding="utf-8")
            row = {"id": "clip", "bundle_root": str(root), "span_id": "a", "attempt_id": "real",
                   "clean_span_audit": {"source": str(clean), **edit._identity(clean)},
                   "human_review": {"source": str(review), **edit._identity(review)}}
            with self.assertRaisesRegex(ValueError, "human-reviewed GREEN"):
                edit._verify_capture(row)

    def test_wall_clock_endpoint_cannot_replace_real_frame_pts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            probe = Path(directory) / "probe.json"
            probe.write_text(json.dumps({"streams": [{"codec_type": "video", "index": 0,
                "width": 1920, "height": 1080}], "frames": [
                {"stream_index": 0, "best_effort_timestamp_time": "10.000"},
                {"stream_index": 0, "best_effort_timestamp_time": "10.033"}]}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "exact source frame PTS"):
                edit._exact_pts(probe, edit.Decimal("10.001"), edit.Decimal("10.033"), 1920, 1080)

    def test_capture_command_uses_trim_and_new_output(self) -> None:
        row = {"kind": "capture", "begin_pts_seconds": "10.000", "end_pts_seconds": "12.000", "frames": 61}
        argv = edit.segment_argv(row, Path("raw.mkv"), Path("new.mp4"), "ffmpeg")
        self.assertIn("trim=start=10.000:end=12.001", argv[argv.index("-vf") + 1])
        self.assertIn("-n", argv)
        self.assertNotIn("-frames:v", argv)
        self.assertNotIn("-stream_loop", argv)
        still = edit.segment_argv({"kind": "still", "frames": 30}, Path("card.png"),
                                  Path("still.mp4"), "ffmpeg")
        self.assertEqual(still[still.index("-frames:v") + 1], "30")

    def test_output_duration_cannot_hide_one_missing_inclusive_frame(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            attempt = Path(directory)
            (attempt / "commands").mkdir()
            (attempt / "probes").mkdir()
            def fake_run(root: Path, name: str, argv: list[str], *, cwd: Path) -> None:
                log = root / "commands" / name
                log.mkdir()
                (log / "stdout.bin").write_text(json.dumps({"streams": [{
                    "codec_type": "video", "width": edit.TARGET_WIDTH,
                    "height": edit.TARGET_HEIGHT, "avg_frame_rate": "30/1", "nb_frames": "61"}],
                    "format": {"duration": "2.000"}}), encoding="utf-8")
            with mock.patch.object(edit, "_run", side_effect=fake_run):
                with self.assertRaisesRegex(ValueError, "duration differs"):
                    edit._probe(attempt, "short", attempt / "short.mp4", "ffprobe", 61)

    def test_streaming_command_receipts_cover_nonzero_launch_and_interrupt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            attempt = Path(directory)
            (attempt / "commands").mkdir()
            with self.assertRaisesRegex(RuntimeError, "exit 7"):
                edit._run(attempt, "nonzero", [sys.executable, "-c",
                          "import sys; print('out'); print('err', file=sys.stderr); sys.exit(7)"],
                          cwd=attempt)
            log = attempt / "commands" / "nonzero"
            self.assertEqual((log / "exit-code.txt").read_text(encoding="ascii"), "7\n")
            self.assertIn(b"out", (log / "stdout.bin").read_bytes())
            self.assertIn(b"err", (log / "stderr.bin").read_bytes())
            with self.assertRaises(FileNotFoundError):
                edit._run(attempt, "not-started", [str(attempt / "missing-tool.exe")], cwd=attempt)
            log = attempt / "commands" / "not-started"
            self.assertEqual((log / "exit-code.txt").read_text(encoding="ascii"), "NOT_STARTED\n")
            self.assertEqual(json.loads((log / "execution-error.json").read_text(encoding="utf-8"))[
                "status"], "INTERRUPTED_OR_NOT_STARTED_PRESERVED")

            class InterruptedProcess:
                pid = 12345
                stopped = False
                waits = 0
                def wait(self, timeout: int | None = None) -> int:
                    self.waits += 1
                    if self.waits == 1:
                        raise KeyboardInterrupt
                    return 130
                def poll(self) -> int | None:
                    return 130 if self.stopped else None
                def terminate(self) -> None:
                    self.stopped = True
                def kill(self) -> None:
                    self.stopped = True
            child = InterruptedProcess()
            with mock.patch.object(edit.subprocess, "Popen", return_value=child):
                with self.assertRaises(KeyboardInterrupt):
                    edit._run(attempt, "interrupted", ["ffmpeg"], cwd=attempt)
            log = attempt / "commands" / "interrupted"
            self.assertTrue(child.stopped)
            self.assertEqual((log / "exit-code.txt").read_text(encoding="ascii"), "130\n")
            self.assertEqual(json.loads((log / "execution-error.json").read_text(encoding="utf-8"))[
                "exception_type"], "KeyboardInterrupt")

    def test_post_render_original_change_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "original.bin"
            source.write_bytes(b"first")
            identity = {"source": str(source), **edit._identity(source)}
            plan = planned()
            for key in ("project_config", "narration_script", "subtitle_fragments", "card_index"):
                plan[key] = identity
            for chapter in plan["chapters"]:
                for segment in chapter["segments"]:
                    keys = ("clean_span_audit", "human_review", "pts_probe", "recorder_final",
                            "cold_load_save", "cold_load_receipt", "control") if segment["kind"] == "capture" else (
                            "image", "origin", "render_receipt")
                    for key in keys:
                        segment[key] = identity
            edit._recheck_nonraw_inputs(plan)
            source.write_bytes(b"other")
            with self.assertRaisesRegex(ValueError, "SHA-256 differs"):
                edit._recheck_nonraw_inputs(plan)

    def test_bundle_manifest_or_intent_change_after_initial_read_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = root / "original.bin"
            original.write_bytes(b"source")
            identity = {"source": str(original), **edit._identity(original)}
            plan = planned()
            for key in ("project_config", "narration_script", "subtitle_fragments", "card_index"):
                plan[key] = identity
            for chapter in plan["chapters"]:
                for segment in chapter["segments"]:
                    keys = ("clean_span_audit", "human_review", "pts_probe", "recorder_final",
                            "cold_load_save", "cold_load_receipt", "control") if segment["kind"] == "capture" else (
                            "image", "origin", "render_receipt")
                    for key in keys:
                        segment[key] = identity
            source_manifest = root / "source-manifest.json"
            intent = root / "recorder-intent.json"
            source_manifest.write_text('{"a":1}', encoding="utf-8")
            intent.write_text('{"b":1}', encoding="utf-8")
            _, manifest_binding = edit._read_bound_json(source_manifest)
            _, intent_binding = edit._read_bound_json(intent)
            provenance = {"bundle": {"source_manifest": manifest_binding,
                                      "recorder_intent": intent_binding}}
            edit._recheck_nonraw_inputs(plan, provenance)
            source_manifest.write_text('{"a":2}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "SHA-256 differs"):
                edit._recheck_nonraw_inputs(plan, provenance)
            source_manifest.write_text('{"a":1}', encoding="utf-8")
            intent.write_text('{"b":2}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "SHA-256 differs"):
                edit._recheck_nonraw_inputs(plan, provenance)

    def test_build_interrupt_retains_failure_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            spec = root / "plan.json"
            spec.write_text(json.dumps(planned()), encoding="utf-8")
            attempt = root / "attempt"
            with mock.patch.object(edit.importlib.metadata, "version", return_value="0.2.1"), \
                    mock.patch.object(edit, "_installed_wheel_digest", return_value="A" * 64), \
                    mock.patch.object(edit, "verify_sources", side_effect=KeyboardInterrupt):
                with self.assertRaises(KeyboardInterrupt):
                    edit.build(spec, attempt, selected_version="0.2.1",
                               selected_wheel_sha256="A" * 64)
            failure = json.loads((attempt / "failure.json").read_text(encoding="utf-8"))
            self.assertEqual(failure["status"], "FAILED_PRESERVED")
            self.assertIn("KeyboardInterrupt", failure["error"])

    def test_current_card_cannot_borrow_another_attempt(self) -> None:
        chapter = planned()["chapters"][1]
        index = {"cards": [{"id": "E2-02", "replay": "A05"},
                           {"id": "E2-03", "replay": "A05"}],
                 "replays": {"A05": {"source_preflight":
                     str(Path.cwd() / "paired-a05" / "ck3-output" / "preflight.json"),
                     "source_save_sha256": "B" * 64}}}
        with self.assertRaisesRegex(ValueError, "same-run A05"):
            edit._same_run_card_gate(chapter, index)
        chapter["segments"][0]["attempt_id"] = "paired-a05"
        chapter["segments"][0]["cold_load_save"]["sha256"] = "B" * 64
        edit._same_run_card_gate(chapter, index)
        another = dict(chapter["segments"][0], attempt_id="borrowed-004")
        chapter["segments"].append(another)
        with self.assertRaisesRegex(ValueError, "same-run A05"):
            edit._same_run_card_gate(chapter, index)


if __name__ == "__main__":
    unittest.main()
