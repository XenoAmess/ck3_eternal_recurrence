from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import plan_zhongguo_phase2_final_promo as planner  # noqa: E402


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _media_receipt(*, production_pending: bool = True) -> dict[str, object]:
    return {
        "result": "GREEN",
        "preflight_implementation": {
            "sha256": _sha(
                planner.ROOT
                / "mod_zhongguo_style/tools/preflight_phase2_media.py"
            )
        },
        "project": {
            "chapters": 10,
            "config": {"sha256": _sha(planner.DEFAULT_CONFIG)},
        },
        "voice": {
            "id": planner.VOICE,
            "provider": "edge-tts",
            "configured": True,
            "credential_presence": "not-applicable",
            "credential_value_exposed": False,
            "synthesis_performed": False,
        },
        "subtitle_layout": {"tracks": [{"id": "zh-CN"}, {"id": "en"}]},
        "subtitle_engine": {
            "automatic_wrap_measured_in_memory": True,
            "ass_written": False,
        },
        "media": {
            "capability_query": {
                "video_encoder": "libx264",
                "video_geometry": [1920, 1080],
                "pixel_format": "yuv420p",
                "audio_encoder": "aac",
                "audio_sample_rate": 48000,
                "audio_channels": 2,
                "container_muxer": "mp4",
            }
        },
        "execution_attestation": {
            "ck3_started": False,
            "tts_synthesis_performed": False,
            "subtitle_media_written": False,
            "ffmpeg_encode_started": False,
            "work_directory_created": False,
            "candidate_generated": False,
        },
        "final_promo_readiness": {
            "result": "RED" if production_pending else "GREEN",
            "reason_codes": (
                [
                    "fresh_promo_tool_fetch_required",
                    "footage_pending",
                    "publish_target_pending",
                ]
                if production_pending
                else []
            ),
        },
    }


class FinalPromoRunbookTests(unittest.TestCase):
    def test_dual_cut_runbooks_keep_shared_spans_and_distinct_outputs(self) -> None:
        promo_dir = planner.ROOT / "mod_zhongguo_style" / "promo"
        rows = []
        with tempfile.TemporaryDirectory() as raw, mock.patch.object(
            planner,
            "_git",
            side_effect=lambda _root, *args: "" if args[:2] == ("status", "--short") else "a" * 40,
        ):
            root = Path(raw)
            for cut_name in ("character", "institution"):
                rows.append(
                    planner.build_runbook(
                        project_config=promo_dir / f"phase2-promo-{cut_name}-project.json",
                        authoring_ledger=promo_dir
                        / f"phase2-authoring-{cut_name}-claims.json",
                        promo_tool_root=root / "promo-tool",
                        capture_root=root / "shared-capture-missing",
                        seed_preflight_report=None,
                        media_preflight_report=None,
                        expected_media_preflight_sha256=None,
                        tts_cache=root / "shared-tts-cache",
                        work_dir=root / f"{cut_name}-work",
                        python=Path(sys.executable),
                        ffmpeg="ffmpeg-not-run",
                        ffprobe="ffprobe-not-run",
                    )
                )
        character, institution = rows
        self.assertEqual(
            character["fixed_contract"]["canonical_spans"],
            institution["fixed_contract"]["canonical_spans"],
        )
        self.assertNotEqual(character["cut"]["id"], institution["cut"]["id"])
        self.assertNotEqual(
            character["cut"]["run_id"], institution["cut"]["run_id"]
        )
        self.assertNotEqual(
            character["cut"]["deliverable_artifact_id"],
            institution["cut"]["deliverable_artifact_id"],
        )
        self.assertNotEqual(
            character["planned_paths"]["deliverable"],
            institution["planned_paths"]["deliverable"],
        )
        self.assertEqual(
            character["cut"],
            {
                "id": "character-led",
                "preset_project_id": "zhongguo-361-phase2-promo",
                "run_id": "phase2-character-led-candidate",
                "deliverable_artifact_id": "zhongguo-361-phase2-character-led-video",
                "deliverable_relative_path": "deliverable/zhongguo-361-phase2-character-led.mp4",
            },
        )
        self.assertEqual(
            institution["cut"],
            {
                "id": "institution-led",
                "preset_project_id": "zhongguo-361-phase2-promo",
                "run_id": "phase2-institution-led-candidate",
                "deliverable_artifact_id": "zhongguo-361-phase2-institution-led-video",
                "deliverable_relative_path": "deliverable/zhongguo-361-phase2-institution-led.mp4",
            },
        )
        self.assertEqual(character["reason_code"], "footage_pending")
        self.assertEqual(institution["reason_code"], "footage_pending")

    def test_missing_footage_is_typed_and_planning_generates_no_media(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            media = root / "media.json"
            media.write_text(
                json.dumps(_media_receipt()),
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
            self.assertEqual(
                runbook["reason_code"], "fresh_promo_tool_fetch_required"
            )
            self.assertEqual(
                runbook["blockers"][:3],
                [
                    "fresh_promo_tool_fetch_required",
                    "footage_pending",
                    "publish_target_pending",
                ],
            )
            self.assertIn("candidate_media_pending", runbook["blockers"])
            self.assertIn("publish_target_pending", runbook["blockers"])
            self.assertIn("publish_pending", runbook["blockers"])
            self.assertEqual(runbook["completion_gate"]["status"], "pending")
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
            self.assertTrue(
                runbook["authoring_claim_ledger"]["checks"]
                ["chinese_primary_english_secondary"]
            )
            self.assertTrue(
                runbook["authoring_claim_ledger"]["checks"]
                ["semantic_line_breaks_then_measured_wrap"]
            )
            self.assertEqual(
                len(
                    runbook["authoring_claim_ledger"]
                    ["visible_observation_contracts"]
                ),
                8,
            )
            self.assertTrue(
                all(
                    runbook["inputs"]["media_preflight"]["checks"].values()
                )
            )
            self.assertEqual(len(runbook["fixed_contract"]["canonical_spans"]), 8)
            self.assertEqual(runbook["fixed_contract"]["chapter_count"], 10)
            self.assertEqual(runbook["fixed_contract"]["voice"], planner.VOICE)
            session_policy = runbook["fixed_contract"]["footage_session_policy"]
            self.assertTrue(session_policy["cross_span_restart_allowed"])
            self.assertFalse(
                session_policy["cross_span_pid_or_generation_equality_required"]
            )
            self.assertTrue(
                session_policy["seed_generation_to_loaded_proof_same_session"]
            )
            self.assertEqual(
                session_policy["forbidden_sources"],
                ["phase1", "old-version", "fixture"],
            )
            self.assertEqual(
                session_policy["capture_reuse"],
                {
                    "independent_edit_projects_allowed": True,
                    "same_verified_source_hashes_required_per_candidate": True,
                    "source_copy_or_regeneration_required": False,
                },
            )
            bind_step = next(
                step
                for step in runbook["ordered_steps"]
                if step["id"] == "bind_green_footage_and_authoring_ledger"
            )
            self.assertIn("clean CK3 restarts between spans are allowed", bind_step["gate"])
            self.assertNotIn("same-session/PID", bind_step["gate"])
            self.assertEqual(
                runbook["ordered_steps"][0]["id"],
                "fetch_and_verify_promo_origin_main",
            )
            self.assertTrue(runbook["ordered_steps"][0]["required_first"])
            self.assertEqual(
                runbook["dependency_graph"], planner.final_promo_execution_dag()
            )
            self.assertEqual(
                runbook["dependency_graph"]["verified_eight_span_footage"],
                ["fresh_promo_tool_receipt"],
            )
            self.assertEqual(
                runbook["dependency_graph"]["composition"],
                ["zh_cn_en_subtitle_layout_safe_zone"],
            )
            self.assertEqual(
                runbook["dependency_graph"]["publish"],
                ["export", "publish_target_authority"],
            )
            self.assertEqual(
                runbook["inputs"]["publish_target_authority"]["reason_code"],
                "publish_target_pending",
            )
            publish_step = next(
                step for step in runbook["ordered_steps"]
                if step["id"] == "external_publish"
            )
            self.assertIsNone(publish_step["command"])
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

    def test_complete_status_requires_green_final_attestation_gate(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            media = root / "media.json"
            media.write_text(
                json.dumps(_media_receipt(production_pending=False)),
                encoding="utf-8",
            )
            media_sha = hashlib.sha256(media.read_bytes()).hexdigest()
            completion_gate = {
                "schema_version": 1,
                "kind": "zg361_phase2_final_promo_completion",
                "result": "GREEN",
                "status": "COMPLETE",
                "reason_codes": [],
                "checks": {},
            }
            with (
                mock.patch.object(
                    planner,
                    "validate_footage_intake",
                    return_value={"result": "GREEN", "reason_code": None},
                ),
                mock.patch.object(
                    planner,
                    "validate_final_promo_completion",
                    return_value=completion_gate,
                ),
                mock.patch.object(
                    planner,
                    "validate_publish_target_authority",
                    return_value={
                        "result": "GREEN",
                        "reason_code": None,
                        "authority": {"sha256": "B" * 64},
                        "target": {
                            "target_id": "target",
                            "platform": "platform",
                            "account_id": "account",
                            "locator_prefix": "https://media.project-owner.net/watch/",
                        },
                    },
                ),
            ):
                runbook = planner.build_runbook(
                    project_config=planner.DEFAULT_CONFIG,
                    authoring_ledger=planner.DEFAULT_AUTHORING_LEDGER,
                    promo_tool_root=Path(r"Z:\workspace\xar_promo_toolchain"),
                    capture_root=root / "capture",
                    seed_preflight_report=None,
                    media_preflight_report=media,
                    expected_media_preflight_sha256=media_sha,
                    tts_cache=root / "tts",
                    work_dir=root / "work",
                    python=Path(sys.executable),
                    ffmpeg="ffmpeg",
                    ffprobe="ffprobe",
                    completion_attestation=root / "completion.json",
                )
            self.assertEqual(runbook["result"], "GREEN")
            self.assertEqual(runbook["status"], "COMPLETE")
            self.assertEqual(runbook["blockers"], [])
            self.assertEqual(runbook["completion_gate"], completion_gate)


if __name__ == "__main__":
    unittest.main()
