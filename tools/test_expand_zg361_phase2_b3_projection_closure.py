"""Tests for deterministic B3 projection closure expansion."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

import expand_zg361_phase2_b3_projection_closure as expand


BOM = b"\xef\xbb\xbf"


def write(root: Path, relative: str, body: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(BOM + body.encode("utf-8"))


def write_localization_family(
    canonical: Path,
    family: str,
    english: dict[str, str],
    chinese: dict[str, str] | None = None,
) -> None:
    chinese = chinese or english
    for language in expand.LOCALIZATION_LANGUAGES:
        values = chinese if language == "simp_chinese" else english
        body = f"l_{language}:\n" + "".join(
            f' {key}:0 "{value}"\n' for key, value in values.items()
        )
        write(
            canonical,
            expand._localization_relative(family, language),
            body,
        )


class ProjectionClosureExpansionTests(unittest.TestCase):
    def test_current_core_shards_are_regenerated_before_closure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = root / "candidate"
            canonical = root / "canonical"
            candidate.mkdir()
            canonical.mkdir()
            groups = (
                (expand.CURRENT_CORE_SHARDS[0], "zg361_appeal_effect"),
                (expand.CURRENT_CORE_SHARDS[1], "zg361_elimination_effect"),
                (expand.CURRENT_CORE_SHARDS[2], "zg361_result_effect"),
                (expand.CURRENT_CORE_SHARDS[3], "zg361_review_effect"),
            )
            for relative, name in groups:
                write(
                    candidate,
                    relative.as_posix(),
                    f"{name} = {{\n    old = yes\n}}\n",
                )
            write(
                canonical,
                expand.CURRENT_CORE_SOURCE.as_posix(),
                "\n\n".join(
                    f"{name} = {{\n    current = yes\n"
                    + (
                        "    zg361_new_cross_boundary_effect = yes\n"
                        if name == "zg361_review_effect"
                        else ""
                    )
                    + "}"
                    for _relative, name in groups
                )
                + "\n",
            )

            result = expand.synchronize_current_core_effect_shards(
                candidate, canonical
            )

            self.assertTrue(result["green"])
            self.assertTrue(result["applicable"])
            self.assertEqual(4, result["definition_count"])
            self.assertEqual(1, result["max_effects_per_file"])
            self.assertTrue(result["canonical_blocks_exact"])
            self.assertEqual(4, len(result["updated_files"]))
            review = (candidate / expand.CURRENT_CORE_SHARDS[3]).read_text(
                encoding="utf-8-sig"
            )
            self.assertIn("zg361_new_cross_boundary_effect = yes", review)
            self.assertNotIn("old = yes", review)

    def test_scripted_widget_registration_copies_exact_gui_provider(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = root / "candidate"
            canonical = root / "canonical"
            candidate.mkdir()
            canonical.mkdir()
            write(
                candidate,
                "gui/scripted_widgets/zg361_scripted_widgets.txt",
                "gui/zg361_promotion_source_bridge.gui = "
                "zg361_promotion_source_bridge_window\n",
            )
            write(
                canonical,
                "gui/zg361_promotion_source_bridge.gui",
                'window = { name = "zg361_promotion_source_bridge_window" }\n',
            )

            result = expand.synchronize_scripted_widget_gui_files(
                candidate, canonical
            )

            self.assertTrue(result["green"])
            self.assertEqual(1, result["required_file_count"])
            self.assertEqual(1, len(result["updated_files"]))
            self.assertEqual(
                (
                    canonical / "gui/zg361_promotion_source_bridge.gui"
                ).read_bytes(),
                (
                    candidate / "gui/zg361_promotion_source_bridge.gui"
                ).read_bytes(),
            )

    def test_terminal_event_copies_generated_localization_fanout(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = root / "candidate"
            canonical = root / "canonical"
            candidate.mkdir()
            canonical.mkdir()
            write(
                candidate,
                "events/zg361_feedback_promotion_pip_runtime_events.txt",
                "namespace = zg361pp\n\n"
                "zg361pp.9004 = {\n"
                "    title = zg361pp.9004.t\n"
                "    desc = zg361pp.9004.desc\n"
                "    option = { name = zg361pp.9004.a }\n"
                "}\n",
            )
            english = {
                "zg361pp.9004.t": "361 Case Closed",
                "zg361pp.9004.desc": "The ledger is closed.",
                "zg361pp.9004.a": "File it.",
            }
            chinese = {
                "zg361pp.9004.t": "三六一案卷已结",
                "zg361pp.9004.desc": "账本已经收口。",
                "zg361pp.9004.a": "归档。",
            }
            write_localization_family(
                canonical,
                "zg361_feedback_promotion_pip",
                english,
                chinese,
            )

            result = expand.synchronize_b3_terminal_localization(
                candidate, canonical
            )

            self.assertTrue(result["green"])
            self.assertTrue(result["applicable"])
            self.assertEqual(
                ["zg361_feedback_promotion_pip"], result["required_families"]
            )
            self.assertEqual(3, result["required_key_count"])
            self.assertEqual(9, len(result["updated_files"]))
            self.assertEqual(9, result["provider_file_count"])
            self.assertEqual({}, result["final_missing_by_language"])
            self.assertTrue(result["placeholder_values_match_english"])
            self.assertTrue(result["provider_files_exact"])
            for language in expand.LOCALIZATION_LANGUAGES:
                target = candidate / expand._promotion_localization_relative(language)
                self.assertTrue(target.read_bytes().startswith(BOM))
                values = expand._localization_values(target)
                self.assertEqual(
                    chinese if language == "simp_chinese" else english,
                    values,
                )

    def test_all_reachable_families_copy_full_nine_language_fanout(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = root / "candidate"
            canonical = root / "canonical"
            candidate.mkdir()
            canonical.mkdir()
            for index, family in enumerate(
                expand.B3_REACHABLE_LOCALIZATION_FAMILIES, start=1
            ):
                prefix = expand.B3_LOCALIZATION_EVENT_PREFIXES[family][0]
                write(candidate, f"events/{prefix}events.txt", "namespace = probe\n")
                write_localization_family(
                    canonical,
                    family,
                    {f"probe_{index}": f"English {index}"},
                    {f"probe_{index}": f"Chinese {index}"},
                )

            result = expand.synchronize_b3_reachable_localization(
                candidate, canonical
            )

            self.assertTrue(result["green"])
            self.assertEqual(
                list(expand.B3_REACHABLE_LOCALIZATION_FAMILIES),
                result["required_families"],
            )
            self.assertEqual(7, result["required_key_count"])
            self.assertEqual(63, result["provider_file_count"])
            self.assertEqual(63, len(result["updated_files"]))
            self.assertEqual({}, result["final_missing_by_language"])
            self.assertTrue(result["placeholder_values_match_english"])
            self.assertTrue(result["provider_files_exact"])
            self.assertEqual(64, len(result["provider_inventory_sha256"]))

    def test_non_authored_translation_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = root / "candidate"
            canonical = root / "canonical"
            candidate.mkdir()
            canonical.mkdir()
            family = "zg361_career_learning"
            write(
                candidate,
                "events/zg361_career_learning_runtime_events.txt",
                "namespace = probe\n",
            )
            write_localization_family(canonical, family, {"probe_key": "English"})
            french = canonical / expand._localization_relative(family, "french")
            write(
                canonical,
                expand._localization_relative(family, "french"),
                'l_french:\n probe_key:0 "French"\n',
            )

            with self.assertRaisesRegex(
                expand.freeze.FreezeError,
                "must retain English placeholders",
            ):
                expand.synchronize_b3_reachable_localization(candidate, canonical)

            self.assertTrue(french.is_file())

    def test_parameterized_event_and_recursive_effect_are_added(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = root / "candidate"
            canonical = root / "canonical"
            candidate.mkdir()
            canonical.mkdir()
            root_effect = (
                "zg361_p2c_stage_10_manager_governance_effect = {\n"
                "    zg361_probe_schedule_effect = { EVENT = zg361probe.7 }\n"
                "}\n\n"
                "zg361_probe_schedule_effect = {\n"
                "    trigger_event = { id = $EVENT$ days = 1 }\n"
                "}\n"
            )
            root_file = (
                "common/scripted_effects/"
                "zg361_phase2_central_003_dispatch_control_effects.txt"
            )
            write(candidate, root_file, root_effect)
            write(canonical, root_file, root_effect)
            write(
                canonical,
                "events/zg361_phase2_central_001_serial_dispatch_events.txt",
                "namespace = zg361probe\n\n"
                "zg361probe.7 = {\n"
                "    immediate = {\n"
                "        zg361_probe_leaf_effect = yes\n"
                "        if = { limit = { zg361_probe_root_trigger = yes } }\n"
                "    }\n"
                "}\n",
            )
            write(
                canonical,
                "common/scripted_effects/leaf_effects.txt",
                "zg361_probe_leaf_effect = {\n"
                "    set_variable = { name = probe value = 1 }\n"
                "}\n",
            )
            write(
                canonical,
                "common/scripted_triggers/probe_triggers.txt",
                "zg361_probe_root_trigger = {\n"
                "    zg361_probe_leaf_trigger = yes\n"
                "}\n\n"
                "zg361_probe_leaf_trigger = {\n"
                "    always = yes\n"
                "}\n",
            )
            write_localization_family(
                canonical,
                "zg361_phase2_central",
                {"zg361_p2c_summary_title": "Phase 2 summary"},
                {"zg361_p2c_summary_title": "二期摘要"},
            )
            evidence_path = root / "evidence.json"
            result = expand.expand_projection_closure(
                candidate, canonical, evidence_path
            )
            self.assertTrue(result["green"])
            self.assertEqual(["zg361probe.7"], result["initial_missing_events"])
            self.assertEqual(3, result["added_file_count"])
            self.assertEqual(2, len(result["rounds"]))
            self.assertTrue(
                (
                    candidate
                    / "events/zg361_phase2_central_001_serial_dispatch_events.txt"
                ).is_file()
            )
            self.assertTrue(
                (candidate / "common/scripted_effects/leaf_effects.txt").is_file()
            )
            self.assertTrue(
                (candidate / "common/scripted_triggers/probe_triggers.txt").is_file()
            )
            persisted = json.loads(evidence_path.read_text(encoding="utf-8"))
            self.assertEqual([], persisted["final_missing_events"])
            self.assertEqual([], persisted["final_missing_effects"])
            self.assertEqual([], persisted["final_missing_triggers"])
            localization = persisted["localization_closure"]
            self.assertTrue(localization["applicable"])
            self.assertEqual(
                ["zg361_phase2_central"], localization["required_families"]
            )
            self.assertEqual(9, localization["provider_file_count"])
            self.assertEqual(9, len(localization["updated_files"]))


if __name__ == "__main__":
    unittest.main()
