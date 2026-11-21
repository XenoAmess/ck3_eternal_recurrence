"""Focused source-admission regression, not Native/engine/business evidence."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import gen_reclaim_native_overrides as native_projection
import gen_reclaim_vassalization_override as offer_projection
import reclaim_the_motherland_effective_law_contract as law
import reclaim_the_motherland_vanilla_contract as native

ROOT = Path(__file__).resolve().parents[1]


class RmtmFlorinSourceAdmissionTests(unittest.TestCase):
    def test_current_exact_snapshot_and_old_snapshot_remain_separate(self):
        old = json.loads((ROOT / "tools/reclaim_the_motherland_vanilla_1_21_0.json").read_text(encoding="utf-8"))
        self.assertEqual(old["steam_build_id"], "26622941")
        self.assertEqual(old["files"][old["paths"]["government"]], "BD6E5DC96F04AD3EBF12841AF4310A7437F1E032D641F2947E5C22DC354E2ACC")
        self.assertEqual(native.CONTRACT["game_version"], "1.21.0.3")
        self.assertEqual(native.CONTRACT["steam_build_id"], "26785313")
        self.assertEqual(native.CONTRACT["exe_sha256"], law.EXE_SHA)
        self.assertEqual(native.CONTRACT["files"][old["paths"]["government"]], "5F2714692EB811BDAFAB5A477D4CD4999DAA7050EEBDE3C12A44892AFA54623F")
        self.assertEqual(native.CONTRACT["definitions"], old["definitions"])
        self.assertEqual(
            {k: v for k, v in native.CONTRACT["files"].items() if k != old["paths"]["government"]},
            {k: v for k, v in old["files"].items() if k != old["paths"]["government"]},
        )

    def test_stale_engine_tuple_is_rejected_at_contract_load(self):
        for field, value in (("game_version", "1.21.0"), ("steam_build_id", "26622941"),
                             ("exe_sha256", "2f2b236a16223891c2da8b167f5f3738d2ae3e6d69de1b4fbe190a5402998acc")):
            wrong = copy.deepcopy(native.CONTRACT)
            wrong[field] = value
            spec = importlib.util.spec_from_file_location("_rmtm_wrong_build", Path(native.__file__))
            assert spec and spec.loader
            module = importlib.util.module_from_spec(spec)
            with self.subTest(field=field), patch("json.loads", return_value=wrong):
                with self.assertRaisesRegex(ValueError, "different exact build"):
                    spec.loader.exec_module(module)

    def test_actual_current_seven_files_and_both_generator_projections(self):
        if not native.GAME.is_dir():
            self.skipTest("installed exact source is optional outside this source qualification machine")
        native.assert_source_files()
        payloads = dict(native_projection.generated_payloads())
        payloads.update(offer_projection.generated_payloads())
        self.assertEqual(len(payloads), 5)
        for path, raw in payloads.items():
            self.assertEqual(path.read_bytes(), raw, path)
            self.assertIn(b"1.21.0.3 / Steam build 26785313", raw)
        self.assertEqual(native_projection.validate_committed_projections(), [])
        self.assertEqual(offer_projection.validate_committed_projection(
            payloads[offer_projection.OUTPUT], payloads[offer_projection.MODIFIERS_OUTPUT]), [])

    def test_semantic_ministry_gate_rejects_missing_flag_even_after_rehash(self):
        body = "celestial_government = {\n\tflags = {\n\t\tgovernment_is_celestial\n\t}\n}\n"
        contract = copy.deepcopy(native.CONTRACT)
        contract["government_contract"]["normalized_text_sha256"] = native.sha256_bytes(body.encode())
        with patch.object(native, "CONTRACT", contract):
            with self.assertRaisesRegex(ValueError, "lost the original ministry"):
                native.assert_government_contract(body)
        contract["government_contract"]["required_flags"] = ["government_is_celestial"]
        with patch.object(native, "CONTRACT", contract):
            with self.assertRaisesRegex(ValueError, "reviewed celestial/ministry"):
                native.assert_government_contract(body)

    def test_raw_government_sha_and_complete_definition_are_not_widened(self):
        actual = native.GAME / native.CONTRACT["paths"]["government"]
        if not actual.is_file():
            self.skipTest("installed exact source is optional outside this source qualification machine")
        raw = actual.read_bytes()
        class File:
            def __init__(self, relative):
                self.relative = relative
            def read_bytes(self):
                if self.relative == native.CONTRACT["paths"]["government"]:
                    return raw + b"\n"  # unchanged meaning still fails exact raw admission
                return (native.GAME / self.relative).read_bytes()
        class Game:
            def __truediv__(self, relative):
                return File(relative)
        with self.assertRaisesRegex(ValueError, "vanilla file changed: common/governments"):
            native.assert_source_files(Game())
        body = native.definition("tgp_has_access_to_ministry_trigger")
        with self.assertRaisesRegex(ValueError, "body changed"):
            native.assert_definition(body + "\n", "tgp_has_access_to_ministry_trigger")

    def test_selected_public_case_retains_all26_and_physical_timer_boundaries(self):
        registry = json.loads((ROOT / "tools/ck3_mod_acceptance_products.json").read_text(encoding="utf-8"))
        core = next(row for row in registry["products"]["reclaim-motherland"]["cases"] if row["id"] == "core")
        expected_path = "{repo_root}/tools/ck3_mod_acceptance_cases/rmtm_florin_keypaths.json"
        self.assertEqual(core["adapter"]["config"], expected_path)
        self.assertEqual(core["phases"]["contract"], expected_path)
        case = json.loads((ROOT / "tools/ck3_mod_acceptance_cases/rmtm_florin_keypaths.json").read_text(encoding="utf-8"))
        self.assertEqual(len(case["families"]), 26)
        self.assertEqual(case["natural_game_day_limit"], 14)
        self.assertEqual(case["formal_recent_independence_days"], 1825)
        self.assertEqual(case["fixture_recent_independence_override_days"], 10)
        self.assertEqual(case["target_engine"]["steam_build_id"], "26785313")
        self.assertEqual(case["target_engine"]["exe_sha256"], law.EXE_SHA)
        self.assertTrue(case["independent_threshold_ui_still_required"])
        self.assertEqual(case["physical_law_gate"]["phases"], ["d3", "predeath", "postdeath"])
        self.assertEqual(sum(row["representation"] == "PENDING_PHYSICAL" for row in case["families"]), 3)

    def test_old_native_frame_rejected_and_missing_physical_rows_not_credited(self):
        frame = {"backend_id": "native-headless", "source": "injected-dll-named-pipe",
                 "episode_projection": "native_campaign", "paused": True, "map_ready": True,
                 "active_event": None, "played_character": {"character_id": 11, "alive": True, "source": "native"},
                 "diagnostics": {"connected": True, "bridge_pid": 12, "connection_generation": 1,
                                 "hello": {"expected_ck3_version": law.VERSION, "expected_ck3_sha256": law.EXE_SHA}},
                 "native_revision": 1, "revision": 2, "date_raw": 53144328, "snapshot_id": "native:1"}
        self.assertEqual(law.frame(frame)[2], 11)
        frame["diagnostics"]["hello"]["expected_ck3_version"] = "1.21.0"
        with self.assertRaisesRegex(law.AdmissionError, "build differs"):
            law.frame(frame)
        with self.assertRaises(law.AdmissionError):
            law.evaluate_phase({"phase": "d3"})  # retargeting does not invent actual law rows


if __name__ == "__main__":
    unittest.main()
