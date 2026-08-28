#!/usr/bin/env python3
"""Offline tests for the ZhongGuo release-localization orchestrator."""

from __future__ import annotations

import sys
from pathlib import Path
import unittest
from unittest import mock


sys.path.insert(0, str(Path(__file__).resolve().parent))
import prepare_release_localization as release_loc  # noqa: E402


class ReleaseLocalizationTests(unittest.TestCase):
    def test_batches_cover_two_thousand_and_eight_keys_once(self) -> None:
        batches = release_loc.build_batches()
        self.assertEqual(17, len(batches))
        core = [key for batch in batches if batch.source == "core" for key in batch.keys]
        mechanisms = [
            key for batch in batches if batch.source == "mechanisms" for key in batch.keys
        ]
        self.assertEqual(160, len(core))
        self.assertEqual(1848, len(mechanisms))
        self.assertEqual(len(core), len(set(core)))
        self.assertEqual(len(mechanisms), len(set(mechanisms)))
        self.assertEqual(168, len(batches[2].keys))
        self.assertEqual(55, len(batches[-1].keys))

    def test_raw_yml_decode_is_inverse_of_generator_escaping(self) -> None:
        self.assertEqual("line\\nnext", release_loc.decode_raw_yml_value("line\\\\nnext"))
        self.assertEqual('say "yes"', release_loc.decode_raw_yml_value('say \\"yes\\"'))

    def test_only_real_english_sentences_count_as_residuals(self) -> None:
        self.assertTrue(release_loc.is_translatable_english("Open the next KPI policy"))
        self.assertFalse(release_loc.is_translatable_english("KPI / PIP / HC · 361"))
        source = {"sentence": "Open the policy", "technical": "KPI / 361"}
        self.assertEqual(
            ["sentence"],
            release_loc.candidate_residuals(source, dict(source)),
        )
        self.assertEqual(
            [],
            release_loc.candidate_residuals(
                {"zg361_scoreboard_col_status": "Status"},
                {"zg361_scoreboard_col_status": "Status"},
                "german",
            ),
        )
        self.assertFalse(release_loc.is_translatable_english("—"))
        self.assertFalse(release_loc.is_translatable_english("3.75 / KPI / HC"))

    def test_malformed_batch_is_bisected_and_reassembled_in_order(self) -> None:
        english = {"one": "One", "two": "Two", "three": "Three"}
        chinese = {"one": "一", "two": "二", "three": "三"}

        def fake_request(language, display, prompt, source, *unused):
            if len(source) > 1:
                raise release_loc.minimax.TranslationError("response is not one strict JSON object")
            return language, {key: f"DE-{value}" for key, value in source.items()}

        with mock.patch.object(
            release_loc.minimax, "request_candidate", side_effect=fake_request
        ):
            result = release_loc.request_with_bisection(
                "german",
                release_loc.SOURCES["core"],
                english,
                chinese,
                "configured-for-test",
                12000,
            )
        self.assertEqual(
            {"one": "DE-One", "two": "DE-Two", "three": "DE-Three"},
            result,
        )


if __name__ == "__main__":
    unittest.main()
