#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic L0 tests for the complete 361 mechanism projection."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

from gen_361_mechanisms import MOD_ROOT, effect_name, outputs
from zg361_mechanism_data import (
    LEDGERS,
    MECHANISM_COUNT,
    PROFILE_DELTAS,
    load_mechanisms,
    mechanism_deltas,
)


class MechanismGenerationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mechanisms = load_mechanisms(MOD_ROOT)
        cls.rendered = outputs(cls.mechanisms)

    def test_exact_catalogue(self) -> None:
        self.assertEqual(len(self.mechanisms), MECHANISM_COUNT)
        self.assertEqual([item.id for item in self.mechanisms], list(range(1, 362)))
        self.assertEqual(len({item.title_cn for item in self.mechanisms}), 361)
        self.assertEqual(len({item.title_en for item in self.mechanisms}), 361)

    def test_every_choice_is_reviewed_and_specific(self) -> None:
        generic = {
            "Adopt the evidence-led policy",
            "Prioritize the short-term result",
        }
        for mechanism in self.mechanisms:
            with self.subTest(mechanism=mechanism.id):
                self.assertNotIn(mechanism.option_a_en, generic)
                self.assertNotIn(mechanism.option_b_en, generic)
                self.assertNotEqual(mechanism.option_a_cn, mechanism.option_b_cn)
                self.assertNotEqual(mechanism.option_a_en, mechanism.option_b_en)
                self.assertIn(mechanism.profile, PROFILE_DELTAS)
                self.assertIn(mechanism.reference_choice, {"a", "b", "c"})

    def test_shared_ledgers_have_real_tradeoffs(self) -> None:
        for mechanism in self.mechanisms:
            choices = {
                choice: mechanism_deltas(mechanism, choice)
                for choice in ("a", "b", "c")
            }
            with self.subTest(mechanism=mechanism.id):
                self.assertEqual(len({tuple(sorted(value.items())) for value in choices.values()}), 3)
                for deltas in choices.values():
                    self.assertTrue(deltas)
                    self.assertTrue(set(deltas).issubset(LEDGERS))
                # At least one route carries an explicit cost/risk, preventing a no-brainer trio.
                self.assertTrue(
                    any(
                        value > 0
                        for choice in choices.values()
                        for key, value in choice.items()
                        if key
                        in {
                            "admin_load",
                            "appeal_risk",
                            "tech_debt",
                            "burnout",
                            "hc_pressure",
                            "pay_debt",
                            "policy_debt",
                            "budget_pressure",
                        }
                    )
                )

    def test_generated_runtime_coverage(self) -> None:
        event_path = MOD_ROOT / "events" / "zg361_generated_mechanism_events.txt"
        effect_path = (
            MOD_ROOT
            / "common"
            / "scripted_effects"
            / "zg361_generated_mechanism_effects.txt"
        )
        events = self.rendered[event_path].decode("utf-8-sig")
        effects = self.rendered[effect_path].decode("utf-8-sig")
        for mechanism in self.mechanisms:
            with self.subTest(mechanism=mechanism.id):
                self.assertEqual(events.count(f"zg361m.{mechanism.id} = {{"), 1)
                for choice in ("a", "b", "c"):
                    self.assertEqual(effects.count(f"{effect_name(mechanism.id, choice)} = {{"), 1)
                self.assertEqual(
                    effects.count(f"zg361_mechanism_{mechanism.id:03d}_ai_effect = {{"),
                    1,
                )
                self.assertIn(f"ZG361M: CASE {mechanism.id:03d}", effects)

    def test_machine_manifest_maps_every_id(self) -> None:
        manifest_path = MOD_ROOT / "docs" / "361-mechanism-manifest.json"
        manifest = json.loads(self.rendered[manifest_path].decode("utf-8"))
        self.assertEqual(manifest["mechanism_count"], 361)
        self.assertEqual([item["id"] for item in manifest["items"]], list(range(1, 362)))
        self.assertEqual({item["live_wave"] for item in manifest["items"]}, {1, 2, 3, 4})
        for item in manifest["items"]:
            self.assertEqual(len(item["implementation"]["choice_effects"]), 3)
            self.assertEqual(item["status"], "fixture-live")
        self.assertEqual(
            manifest["acceptance"]["run_id"],
            "zga_20260829_061314_ea5f04ad",
        )
        self.assertIn(
            "1083",
            manifest["acceptance"]["claim_boundary"],
        )

    def test_checked_in_projection_is_current(self) -> None:
        stale = [
            path.relative_to(MOD_ROOT).as_posix()
            for path, expected in self.rendered.items()
            if not path.is_file() or path.read_bytes() != expected
        ]
        self.assertEqual(stale, [])


if __name__ == "__main__":
    sys.exit(unittest.main())
