#!/usr/bin/env python3

from __future__ import annotations

import tempfile
import unittest
from unittest import mock
from pathlib import Path

import run_acceptance as acceptance
import run_xenoamess_quality_of_life_acceptance as xqol


class ProductOuterDescriptorTests(unittest.TestCase):
    def test_boot_timeout_allows_slow_local_machine_startup(self) -> None:
        self.assertEqual(xqol.BOOT_TIMEOUT_S, 30 * 60)

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
        self.assertIn("NOT = { holder = root.var:zqa_death_incumbent }", death_gui)

        effects = (
            xqol.FIXTURE / "common" / "scripted_effects" / "zqa_effects.txt"
        ).read_text(encoding="utf-8-sig")
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

        stream.wait.assert_called_once_with(
            "ZQA: TEST PASS ready_for_product_disable_decisions", 45
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


if __name__ == "__main__":
    unittest.main()
