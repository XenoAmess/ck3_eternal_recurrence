from __future__ import annotations

import hashlib
import json
import math
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = PACKAGE_ROOT.parent
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from xar_promo.model import ProjectConfig  # noqa: E402
from xar_promo.presets.zhongguo_361_phase2 import (  # noqa: E402
    CAPTURE_CHAPTER_KIND,
    CORE_PROJECT_CONFIG_BLOCKERS,
    PHASE2_CHAPTER_CONTRACT,
    PHASE2_PROMO_CAPTURE_CONTRACT_VERSION,
    PHASE2_PROMO_CAPTURE_MODE,
    PHASE2_PROMO_CAPTURE_PRODUCER_ID,
    PHASE2_PROMO_CAPTURE_SPAN_MAP,
    PHASE2_PROMO_CLEAN_SPAN_IDS,
    PHASE2_POLICY,
    Phase2PresetError,
    build_narration_request,
    load_phase2_capture_candidate,
    load_phase2_project_config,
    phase2_capture_requirements,
    validate_phase2_project_config,
    validate_rendered_duration,
)
from xar_promo.project import load_document  # noqa: E402


PROJECT_CONFIG_PATH = (
    REPOSITORY_ROOT / "mod_zhongguo_style" / "promo" / "phase2-promo-project.json"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _file_record(path: Path) -> dict[str, object]:
    return {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": _sha256(path),
    }


def _ready_capture_config(config: ProjectConfig) -> ProjectConfig:
    payload = config.to_dict()
    for chapter in payload["chapters"]:
        if chapter["type"] == CAPTURE_CHAPTER_KIND:
            chapter["state"] = "ready"
    return ProjectConfig.from_mapping(payload)


def _write_candidate_timeline(
    root: Path,
    config: ProjectConfig,
    *,
    historical: bool = True,
    fixture_ui_absent: bool = True,
) -> Path:
    history = root / "game" / "history" / "characters" / "han.txt"
    title_history = root / "game" / "history" / "titles" / "china.txt"
    history.parent.mkdir(parents=True, exist_ok=True)
    title_history.parent.mkdir(parents=True, exist_ok=True)
    history.write_text("1001 = { name = historical_official }\n", encoding="utf-8")
    title_history.write_text("e_example = { 1066.1.1 = { holder = 1001 } }\n", encoding="utf-8")
    requirements = phase2_capture_requirements(config)
    timeline = {
        "capture_mode": PHASE2_PROMO_CAPTURE_MODE,
        "capture_contract_version": PHASE2_PROMO_CAPTURE_CONTRACT_VERSION,
        "capture_contract": {
            "mode": PHASE2_PROMO_CAPTURE_MODE,
            "version": PHASE2_PROMO_CAPTURE_CONTRACT_VERSION,
            "producer_id": PHASE2_PROMO_CAPTURE_PRODUCER_ID,
            "span_ids": list(PHASE2_PROMO_CLEAN_SPAN_IDS),
            "span_map": [
                {"chapter_id": chapter_id, "producer_key": producer_key}
                for chapter_id, producer_key in PHASE2_PROMO_CAPTURE_SPAN_MAP
            ],
        },
        "real_character_provenance": {
            "schema_version": 1,
            "subjects": [
                {
                    "subject_id": "historical_official",
                    "history_id": "1001",
                    "display_name": "史官甲",
                    "roles": ["player", "reviewed_official"],
                    "origin": "ck3_history_database" if historical else "fixture_generated",
                    "temporary_or_generated": not historical,
                    "history_source": _file_record(history),
                }
            ],
            "title_history_source": _file_record(title_history),
            "fixture_constructor_counts": {
                "create_character": 0,
                "create_title": 0,
                "grant_title": 0,
                "set_father": 0,
                "set_mother": 0,
                "set_spouse": 0,
                "add_relation": 0,
                "set_relation": 0,
            },
            "test_decision_visibility_contract": {
                "initialization_decision_before_recording_only": True,
                "all_other_fixture_decisions_permanently_hidden": True,
            },
        },
        "clean_frame_gates": [
            {
                "span_id": span_id,
                "fixture_test_ui_absent": fixture_ui_absent,
                "frames": [
                    {"phase": "begin", "fixture_test_ui_absent": fixture_ui_absent},
                    {"phase": "end", "fixture_test_ui_absent": fixture_ui_absent},
                ],
            }
            for span_id in requirements.clean_span_ids
        ],
    }
    timeline_path = root / "capture-timeline.json"
    timeline_path.write_text(
        json.dumps(timeline, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return timeline_path


class ZhongguoPhase2PresetTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = load_phase2_project_config(PROJECT_CONFIG_PATH)

    def test_checked_in_project_is_a_standard_core_config(self) -> None:
        document = load_document(PROJECT_CONFIG_PATH, check_files=False)

        self.assertEqual(document.source_format, "project-config-v1")
        self.assertIsNotNone(document.config)
        self.assertEqual(document.config, self.config)
        self.assertTrue(self.config.chapters)
        self.assertTrue(all(chapter.state == "planned" for chapter in self.config.chapters))
        self.assertEqual(
            PHASE2_CHAPTER_CONTRACT,
            tuple((chapter.chapter_id, chapter.kind) for chapter in self.config.chapters),
        )

    def _assert_invalid_project_payload(self, mutate, pattern: str) -> None:
        with tempfile.TemporaryDirectory() as temp:
            payload = json.loads(PROJECT_CONFIG_PATH.read_text(encoding="utf-8-sig"))
            mutate(payload)
            path = Path(temp) / "phase2-invalid.json"
            path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(Phase2PresetError, pattern):
                load_phase2_project_config(path)

    def test_project_rejects_missing_canonical_chapter(self) -> None:
        self._assert_invalid_project_payload(
            lambda payload: payload["chapters"].pop(4),
            "canonical ten-chapter contract",
        )

    def test_project_rejects_reordered_canonical_chapters(self) -> None:
        def reorder(payload) -> None:
            payload["chapters"][1], payload["chapters"][2] = (
                payload["chapters"][2],
                payload["chapters"][1],
            )

        self._assert_invalid_project_payload(reorder, "canonical ten-chapter contract")

    def test_project_rejects_duplicate_chapter_ids(self) -> None:
        def duplicate(payload) -> None:
            payload["chapters"][1]["id"] = payload["chapters"][2]["id"]

        self._assert_invalid_project_payload(duplicate, "duplicate ids")

    def test_direct_preset_validation_reports_duplicate_ids_before_order(self) -> None:
        duplicate = replace(
            self.config,
            chapters=(
                self.config.chapters[0],
                self.config.chapters[0],
                *self.config.chapters[2:],
            ),
        )
        with self.assertRaisesRegex(Phase2PresetError, "duplicate ids"):
            validate_phase2_project_config(duplicate)

    def test_policy_carries_project_only_requirements(self) -> None:
        self.assertEqual(PHASE2_POLICY.narration_locale, "zh-CN")
        self.assertEqual(PHASE2_POLICY.subtitle_locales, ("zh-CN", "en"))
        self.assertEqual(PHASE2_POLICY.voice, "zh-CN-XiaoxiaoNeural")
        self.assertEqual(PHASE2_POLICY.duration_limit_seconds_exclusive, 1200)
        self.assertTrue(PHASE2_POLICY.audience_has_seen_phase_one)
        self.assertTrue(PHASE2_POLICY.phase_two_increment_only)
        self.assertEqual(
            PHASE2_POLICY.tone_tags,
            ("satirical", "witty", "everyday-life", "youthful"),
        )
        self.assertTrue(PHASE2_POLICY.require_real_historical_characters)
        self.assertTrue(PHASE2_POLICY.forbid_test_decisions_in_picture)
        self.assertTrue(PHASE2_POLICY.forbid_fixture_ui_in_picture)
        self.assertTrue(PHASE2_POLICY.exclude_ck3_loading)
        self.assertTrue(PHASE2_POLICY.start_after_gameplay_hud)
        self.assertTrue(PHASE2_POLICY.preserve_all_process_material)
        self.assertIn("failed-takes", PHASE2_POLICY.process_material_kinds)
        self.assertTrue(PHASE2_POLICY.runtime_validation_required)
        self.assertTrue(PHASE2_POLICY.human_review_required)
        self.assertTrue(CORE_PROJECT_CONFIG_BLOCKERS)

    def test_capture_requirements_come_from_configured_chapters(self) -> None:
        requirements = phase2_capture_requirements(self.config)
        configured = tuple(
            chapter.chapter_id
            for chapter in self.config.chapters
            if chapter.kind == CAPTURE_CHAPTER_KIND
        )

        self.assertEqual(requirements.clean_span_ids, configured)
        self.assertEqual(len(configured), 8)
        self.assertEqual(
            requirements.mark_labels[0], "recording_started_after_gameplay_hud"
        )
        self.assertEqual(requirements.mark_labels[-1], "recording_stop_requested")
        for span_id in configured:
            self.assertIn(f"{span_id}_clean_begin", requirements.mark_labels)
            self.assertIn(f"{span_id}_clean_end", requirements.mark_labels)

    def test_phase2_capture_schema_freezes_canonical_span_map(self) -> None:
        schema_path = (
            PACKAGE_ROOT
            / "src"
            / "xar_promo"
            / "schemas"
            / "phase2-capture-contract-v1.schema.json"
        )
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        properties = schema["properties"]
        self.assertEqual(PHASE2_PROMO_CAPTURE_MODE, properties["mode"]["const"])
        self.assertEqual(
            PHASE2_PROMO_CAPTURE_CONTRACT_VERSION,
            properties["version"]["const"],
        )
        self.assertEqual(
            PHASE2_PROMO_CAPTURE_PRODUCER_ID,
            properties["producer_id"]["const"],
        )
        self.assertEqual(
            list(PHASE2_PROMO_CLEAN_SPAN_IDS),
            properties["span_ids"]["const"],
        )
        self.assertEqual(
            [
                {"chapter_id": chapter_id, "producer_key": producer_key}
                for chapter_id, producer_key in PHASE2_PROMO_CAPTURE_SPAN_MAP
            ],
            properties["span_map"]["const"],
        )

    def test_narration_request_fixes_xiaoxiao_voice(self) -> None:
        request = build_narration_request("没有 HC？很好，流程还可以继续走。", rate="+3%")

        self.assertEqual(request.voice, "zh-CN-XiaoxiaoNeural")
        self.assertEqual(request.rate, "+3%")

    def test_duration_boundary_is_strictly_less_than_twenty_minutes(self) -> None:
        self.assertEqual(validate_rendered_duration(1199.999, self.config), 1199.999)
        for invalid in (0, 1200, 1200.001, math.inf, math.nan, True):
            with self.subTest(invalid=invalid):
                with self.assertRaises(Phase2PresetError):
                    validate_rendered_duration(invalid, self.config)

    def test_planned_chapters_cannot_claim_verified_capture(self) -> None:
        with patch(
            "xar_promo.presets.zhongguo_361_phase2.load_capture_bundle"
        ) as loader:
            with self.assertRaisesRegex(Phase2PresetError, "still planned"):
                load_phase2_capture_candidate(self.config, "unused")
            loader.assert_not_called()

    def test_candidate_uses_config_requirements_and_remains_not_release_ready(self) -> None:
        ready = _ready_capture_config(self.config)
        requirements = phase2_capture_requirements(ready)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            timeline = _write_candidate_timeline(root, ready)
            fake_bundle = SimpleNamespace(timeline=SimpleNamespace(path=timeline))
            with patch(
                "xar_promo.presets.zhongguo_361_phase2.load_capture_bundle",
                return_value=fake_bundle,
            ) as loader:
                candidate = load_phase2_capture_candidate(ready, root / "capture")

        loader.assert_called_once_with(
            root / "capture",
            required_span_ids=requirements.clean_span_ids,
            required_mark_labels=requirements.mark_labels,
        )
        self.assertEqual(len(candidate.historical_subjects), 1)
        self.assertEqual(candidate.historical_subjects[0].history_id, "1001")
        self.assertTrue(candidate.fixture_ui_attested_absent)
        self.assertTrue(candidate.test_decisions_attested_absent)
        self.assertTrue(candidate.capture_report_verified)
        self.assertFalse(candidate.phase_two_runtime_claims_verified)
        self.assertFalse(candidate.human_visual_review_verified)
        self.assertFalse(candidate.release_ready)
        self.assertTrue(candidate.blockers)

    def test_candidate_rejects_generated_subject_or_fixture_ui(self) -> None:
        ready = _ready_capture_config(self.config)
        for historical, fixture_ui_absent, expected in (
            (False, True, "history database"),
            (True, False, "fixture UI absence"),
        ):
            with self.subTest(
                historical=historical,
                fixture_ui_absent=fixture_ui_absent,
            ):
                with tempfile.TemporaryDirectory() as temp:
                    root = Path(temp).resolve()
                    timeline = _write_candidate_timeline(
                        root,
                        ready,
                        historical=historical,
                        fixture_ui_absent=fixture_ui_absent,
                    )
                    fake_bundle = SimpleNamespace(timeline=SimpleNamespace(path=timeline))
                    with patch(
                        "xar_promo.presets.zhongguo_361_phase2.load_capture_bundle",
                        return_value=fake_bundle,
                    ):
                        with self.assertRaisesRegex(Phase2PresetError, expected):
                            load_phase2_capture_candidate(ready, root / "capture")

    def test_candidate_rejects_legacy_or_misordered_capture_contract(self) -> None:
        ready = _ready_capture_config(self.config)
        for mutation, expected in (
            (
                lambda value: value.pop("capture_contract"),
                "lacks its producer capture_contract",
            ),
            (
                lambda value: value.__setitem__("capture_mode", "zhongguo-361-phase1"),
                "dedicated capture_mode",
            ),
            (
                lambda value: value["capture_contract"].__setitem__(
                    "span_ids", list(reversed(PHASE2_PROMO_CLEAN_SPAN_IDS))
                ),
                "span_ids must exactly match",
            ),
        ):
            with self.subTest(expected=expected):
                with tempfile.TemporaryDirectory() as temp:
                    root = Path(temp).resolve()
                    timeline = _write_candidate_timeline(root, ready)
                    payload = json.loads(timeline.read_text(encoding="utf-8"))
                    mutation(payload)
                    timeline.write_text(
                        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8",
                    )
                    fake_bundle = SimpleNamespace(
                        timeline=SimpleNamespace(path=timeline)
                    )
                    with patch(
                        "xar_promo.presets.zhongguo_361_phase2.load_capture_bundle",
                        return_value=fake_bundle,
                    ):
                        with self.assertRaisesRegex(Phase2PresetError, expected):
                            load_phase2_capture_candidate(ready, root / "capture")


if __name__ == "__main__":
    unittest.main()
