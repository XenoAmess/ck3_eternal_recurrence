#!/usr/bin/env python3
"""Focused offline tests for the Tributary Expansion Directives live runner."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import build_tributary_expansion_directives_release as release
import run_tributary_expansion_directives_acceptance as runner


class TributaryExpansionAcceptanceRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        runner.configure_harness(runner.DEFAULT_SOURCE.resolve())

    def test_startup_window_matches_repository_contract(self) -> None:
        self.assertEqual(runner.harness.BOOT_TIMEOUT_S, 30 * 60)

    def test_product_and_fixture_contracts_are_green(self) -> None:
        self.assertEqual(runner.product_source_errors(), [])
        self.assertEqual(runner.fixture_source_errors(), [])

    def test_required_markers_bind_cost_subsidy_and_war(self) -> None:
        joined = "\n".join(runner.REQUIRED_MARKERS)
        for token in (
            "decline_response_preserved_send_cost_and_gold",
            "subsidized_accept_spent_prestige_and_transferred_gold",
            "war_attacker_defender_binding",
            "TEST GAP",
        ):
            self.assertIn(token, joined)

    def test_marker_stream_reads_tea_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            log = Path(raw) / "debug.log"
            log.write_text("noise\nTEA: TEST BEGIN tributary_expansion_directives\n", encoding="utf-8")
            stream = runner.TeaMarkerStream(log)
            stream.pump()
            self.assertEqual(len(stream.lines), 1)
            self.assertIn("TEA: TEST BEGIN", stream.lines[0])

    def test_bootstrap_projects_only_release_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            profile = Path(raw) / "profile"
            result = runner.bootstrap_userdir(profile)
            product = Path(result["targets"]["product"])
            actual = {
                path.relative_to(product).as_posix()
                for path in product.rglob("*")
                if path.is_file()
            }
            self.assertEqual(actual, set(release.RUNTIME_FILES))
            self.assertEqual(result["enabled_mods"], ["mod/ted_acceptance.mod", "mod/tea_acceptance_fixture.mod"])
            self.assertIsNone(result["workshop_item_id"])
            self.assertNotIn(
                "remote_file_id",
                (product / "descriptor.mod").read_text(encoding="utf-8-sig"),
            )


if __name__ == "__main__":
    unittest.main()
