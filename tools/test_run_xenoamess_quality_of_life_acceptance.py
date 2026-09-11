#!/usr/bin/env python3

from __future__ import annotations

import tempfile
import unittest
from unittest import mock
from pathlib import Path

import run_acceptance as acceptance
import run_xenoamess_quality_of_life_acceptance as xqol
import run_xqol_defense_acceptance as defense


class ProductOuterDescriptorTests(unittest.TestCase):
    def test_defense_only_runner_reuses_isolated_acceptance_contract(self) -> None:
        self.assertEqual(defense.base.BOOT_TIMEOUT_S, 30 * 60)
        self.assertIn("ZQA: TEST PASS defense_matrix_done", defense.DEFENSE_MARKERS)
        decision = (
            xqol.FIXTURE / "common" / "decisions" / "zqa_decisions.txt"
        ).read_text(encoding="utf-8-sig")
        self.assertIn("zqa_initialize_defense_only_decision", decision)

    def test_boot_timeout_allows_slow_local_machine_startup(self) -> None:
        self.assertEqual(xqol.BOOT_TIMEOUT_S, 30 * 60)

    def test_phase_two_toggle_is_part_of_the_live_regression(self) -> None:
        fixture_effects = (
            xqol.FIXTURE / "common" / "scripted_effects" / "zqa_effects.txt"
        ).read_text(encoding="utf-8-sig")
        fixture_guis = (
            xqol.FIXTURE / "common" / "scripted_guis" / "zqa_guis.txt"
        ).read_text(encoding="utf-8-sig")
        runner = Path(xqol.__file__).read_text(encoding="utf-8")
        self.assertIn("has_variable = xqol_auto_call_defenders_enabled", fixture_effects)
        self.assertIn("NOT = { has_variable = xqol_auto_call_defenders_enabled }", fixture_effects)
        self.assertIn("has_variable = xqol_auto_call_defenders_enabled", fixture_guis)
        self.assertIn("开启自动召集防御援军", runner)
        self.assertIn("关闭自动召集防御援军", runner)

    def test_phase_one_decisions_remain_at_the_top_of_the_product_group(self) -> None:
        runner = Path(xqol.__file__).read_text(encoding="utf-8")
        decisions = (
            xqol.ROOT
            / "mod_xenoamess_quality_of_life"
            / "common"
            / "decisions"
            / "xqol_decisions.txt"
        ).read_text(encoding="utf-8-sig")
        self.assertNotIn("scroll_to_bottom=True", runner)
        self.assertIn("sort_order = 100", decisions)
        self.assertIn("sort_order = 90", decisions)
        self.assertIn("sort_order = 80", decisions)
        self.assertIn("acceptance.pyautogui.dragTo(", runner)
        self.assertIn("int(height * 0.27)", runner)
        self.assertIn("acceptance.find_ocr_text(", runner)
        self.assertIn("int(width * 0.55), int(height * 0.05)", runner)
        self.assertIn('ensure_bridge_paused(service, artifacts, f"{stem}_pre_decision")', runner)
        self.assertIn('"pause-map", expected_revision=int(snapshot["revision"])', runner)
        self.assertNotIn('"14_conversion",\n        contains=False,', runner)

    def test_product_decision_group_uses_ck3_localization_key(self) -> None:
        for language in (
            "english",
            "french",
            "german",
            "japanese",
            "korean",
            "polish",
            "russian",
            "simp_chinese",
            "spanish",
        ):
            text = (
                xqol.SOURCE
                / "localization"
                / language
                / f"xqol_l_{language}.yml"
            ).read_text(encoding="utf-8-sig")
            self.assertIn("decision_group_type_xqol_quality_of_life:0", text)

    def test_phase_two_payment_matrix_is_live_driven(self) -> None:
        fixture = (
            xqol.FIXTURE / "common" / "scripted_effects" / "zqa_effects.txt"
        ).read_text(encoding="utf-8-sig")
        runner = Path(xqol.__file__).read_text(encoding="utf-8")
        for token in (
            "golden_obligations_perk",
            "golden_obligation_value",
            "has_usable_hook",
            "payment_full_only",
            "payment_any_above_one_only",
        ):
            self.assertIn(token, fixture)
        self.assertIn("批量索取足额牵制款", runner)
        self.assertIn("批量索取现有牵制款", runner)

    def test_phase_two_remaining_matrices_are_live_driven(self) -> None:
        interaction_fixture = (
            xqol.FIXTURE
            / "common"
            / "scripted_effects"
            / "zqa_phase2_interaction_effects.txt"
        ).read_text(encoding="utf-8-sig")
        defense_fixture = (
            xqol.FIXTURE
            / "common"
            / "scripted_effects"
            / "zqa_phase2_defense_effects.txt"
        ).read_text(encoding="utf-8-sig")
        bridge = (xqol.FIXTURE / "gui" / "zqa_bridge.gui").read_text(
            encoding="utf-8-sig"
        )
        runner = Path(xqol.__file__).read_text(encoding="utf-8")
        for token in (
            "conversion_threshold_50_filtered",
            "ransom_full_only",
            "ransom_any_one_gold",
            "release_priority_matrix",
        ):
            self.assertIn(token, interaction_fixture)
            self.assertIn(token, runner)
        for token in (
            "defense_regular_ally_called",
            "defense_overlap_dedup_and_replay_idempotent",
            "defense_paid_dynasty_member_excluded",
            "defense_resources_not_decreased",
        ):
            self.assertIn(token, defense_fixture)
            self.assertIn(token, runner)
        self.assertIn("zqa_phase2_conversion_verify_gui", bridge)
        self.assertIn("zqa_phase2_defense_verify_gui", bridge)
        self.assertIn('"65%"', runner)
        self.assertIn('"50%"', runner)
        self.assertIn("percentage_50[0] + 75", runner)
        self.assertIn("percentage_50[0] - 5", runner)
        self.assertIn("领内改信答复完毕", runner)
        self.assertIn("批量足额赎回囚犯", runner)
        self.assertIn("批量按现有钱财赎回囚犯", runner)
        self.assertIn("按最优条款批量释放囚犯", runner)

    def test_workshop_identity_is_recorded_but_not_loaded_in_isolated_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            inner = root / "descriptor.mod"
            outer = root / "xqol_acceptance.mod"
            target = root / "product"
            original = 'name="XenoAmess的体验优化"\nremote_file_id="3798133925"\n'
            inner.write_bytes(original.encode("utf-8-sig"))

            item_id = xqol.write_product_outer_descriptor(inner, outer, target)

            self.assertEqual(item_id, "3798133925")
            self.assertEqual(inner.read_text(encoding="utf-8-sig"), 'name="XenoAmess的体验优化"\n')
            rendered = outer.read_text(encoding="utf-8-sig")
            self.assertNotIn("remote_file_id", rendered)
            self.assertIn(f'path="{target.as_posix()}"', rendered)

    def test_malformed_workshop_identity_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            inner = root / "descriptor.mod"
            inner.write_text('name="x"\nremote_file_id="not-numeric"\n', encoding="utf-8-sig")

            with self.assertRaises(acceptance.RunnerError):
                xqol.write_product_outer_descriptor(inner, root / "outer.mod", root / "product")

    def test_death_verifier_waits_for_settled_title_holder(self) -> None:
        fixture = (
            xqol.FIXTURE / "common" / "scripted_guis" / "zqa_guis.txt"
        ).read_text(encoding="utf-8-sig")
        death_gui = fixture.split("zqa_death_matrix_gui = {", 1)[1].split(
            "zqa_disabled_matrix_gui = {", 1
        )[0]

        self.assertIn("has_variable = zqa_death_title", death_gui)
        self.assertIn("has_variable = zqa_death_incumbent", death_gui)
        self.assertIn("has_variable = zqa_death_successor", death_gui)
        self.assertIn("exists = holder", death_gui)
        self.assertIn("NOT = { holder = root }", death_gui)
        self.assertIn("NOT = { holder = root.var:zqa_death_incumbent }", death_gui)

        effects = (
            xqol.FIXTURE / "common" / "scripted_effects" / "zqa_effects.txt"
        ).read_text(encoding="utf-8-sig")
        death_setup = effects.split(
            "NOT = { has_character_flag = zqa_control_incumbent_subject }", 1
        )[1].split("zqa_verify_death_settlement_effect = {", 1)[0]
        self.assertIn("is_ai = yes", death_setup)
        verifier = effects.split("zqa_verify_death_settlement_effect = {", 1)[
            1
        ].split("zqa_verify_disabled_matrix_effect = {", 1)[0]
        self.assertIn("NOT = { holder = root }", verifier)
        self.assertIn("NOT = { holder = root.var:zqa_death_incumbent }", verifier)
        self.assertIn(
            "ZQA: TEST PASS death_transferred_to_non_player_successor", verifier
        )
        self.assertIn("ZQA: OBSERVED death_used_predeath_current_heir", verifier)
        self.assertIn(
            "ZQA: OBSERVED death_recomputed_non_player_successor", verifier
        )

    def test_queued_death_settlement_advances_and_repauses_map(self) -> None:
        service = mock.Mock()
        service.snapshot.side_effect = [
            {"paused": True, "revision": 10, "date_raw": 100},
            {"paused": False, "revision": 12, "date_raw": 101},
            {"paused": True, "revision": 14, "date_raw": 101},
        ]
        service.execute_step.side_effect = [
            {"accepted": True, "step": "resume-map"},
            {"accepted": True, "step": "pause-map"},
        ]
        stream = mock.Mock()

        with tempfile.TemporaryDirectory() as raw:
            evidence = xqol.settle_queued_death_succession(
                service, stream, Path(raw)
            )

        stream.has.assert_called_once_with(
            "ZQA: TEST PASS ready_for_product_disable_decisions"
        )
        self.assertEqual(
            service.execute_step.call_args_list,
            [
                mock.call("resume-map", expected_revision=10),
                mock.call("pause-map", expected_revision=12),
            ],
        )
        self.assertEqual(evidence["result"], "GREEN")
        self.assertTrue(evidence["after_paused"]["paused"])

    def test_async_advance_drains_ambient_event_and_resumes(self) -> None:
        class Stream:
            def __init__(self) -> None:
                self.calls = 0

            def has(self, marker: str) -> bool:
                self.calls += 1
                return self.calls >= 2

        service = mock.Mock()
        service.snapshot.side_effect = [
            {"paused": True, "revision": 10, "active_event": None},
            {
                "paused": False,
                "revision": 12,
                "active_event": {
                    "instance_id": 7,
                    "options": [
                        {"option_number": 1, "enabled": True},
                        {"option_number": 2, "enabled": True},
                    ],
                },
            },
            {
                "paused": True,
                "revision": 13,
                "active_event": {
                    "instance_id": 7,
                    "options": [
                        {"option_number": 1, "enabled": True},
                        {"option_number": 2, "enabled": True},
                    ],
                },
            },
            {"paused": True, "revision": 14, "active_event": None},
            {"paused": False, "revision": 15, "active_event": None},
            {"paused": True, "revision": 16, "active_event": None},
        ]
        service.execute_step.side_effect = [
            {"accepted": True, "step": "resume-map"},
            {"accepted": True, "step": "pause-map"},
            {"accepted": True, "step": "resume-map"},
            {"accepted": True, "step": "pause-map"},
        ]
        service.query_current_event_window_context_v1.return_value = {
            "current_event_window_context": {
                "event_definition_key": "tgp_tributary_task.0001"
            }
        }
        service.select_event_option.return_value = {
            "accepted": True,
            "step": "select-event-option-1",
        }

        with tempfile.TemporaryDirectory() as raw:
            evidence = xqol.advance_until_marker(
                service,
                Stream(),
                Path(raw),
                "conversion_reply",
                "ZQA: TEST PASS conversion_threshold_50_filtered",
                5,
            )

        service.select_event_option.assert_called_once_with(
            1, event_instance_id=7, expected_revision=13
        )
        self.assertEqual(len(evidence["drained_events"]), 1)
        self.assertEqual(evidence["result"], "GREEN")
        self.assertTrue(evidence["after_paused"]["paused"])

    def test_async_advance_recovers_when_event_closes_into_running_map(self) -> None:
        class Stream:
            def __init__(self) -> None:
                self.calls = 0

            def has(self, marker: str) -> bool:
                self.calls += 1
                return self.calls >= 2

        service = mock.Mock()
        service.snapshot.side_effect = [
            {"paused": True, "revision": 10, "active_event": None},
            {
                "paused": True,
                "revision": 12,
                "active_event": {
                    "instance_id": 7,
                    "options": [{"option_number": 1, "enabled": True}],
                },
            },
            {
                "paused": False,
                "revision": 13,
                "snapshot_id": "after-event",
                "active_event": None,
            },
            {"paused": False, "revision": 13, "active_event": None},
            {"paused": False, "revision": 14, "active_event": None},
            {"paused": True, "revision": 15, "active_event": None},
        ]
        service.execute_step.side_effect = [
            {"accepted": True, "step": "resume-map"},
            {"accepted": True, "step": "pause-map"},
        ]
        service.query_current_event_window_context_v1.return_value = {
            "current_event_window_context": {"event_definition_key": "test.0001"}
        }
        service.select_event_option.side_effect = xqol.BridgeUnavailableError(
            "native event selection postcondition is not paused"
        )

        with tempfile.TemporaryDirectory() as raw:
            evidence = xqol.advance_until_marker(
                service,
                Stream(),
                Path(raw),
                "defense_advance",
                "ZQA: TEST DONE xqol",
                5,
            )

        selection = evidence["drained_events"][0]["selection"]
        self.assertEqual(selection["progress_status"], "postcondition-recovered")
        self.assertFalse(selection["ending_paused"])
        self.assertEqual(evidence["result"], "GREEN")
        self.assertTrue(evidence["after_paused"]["paused"])


if __name__ == "__main__":
    unittest.main()
