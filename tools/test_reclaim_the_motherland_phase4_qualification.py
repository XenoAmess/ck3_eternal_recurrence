"""One bounded class: no game, native build, public prepare, or matrix rerun."""
from __future__ import annotations

import ast
import codecs
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import prepare_reclaim_the_motherland_1_20_fixture as emitter
import reclaim_the_motherland_scope_witness as witness
from tools.ck3_mod_acceptance_cases import rmtm_adapter as adapter
from tools.ck3_mod_acceptance_cases._business import pin
from test_reclaim_the_motherland_contract import parse_clausewitz


SOURCE = ROOT / "tools/fixtures/reclaim_the_motherland_acceptance"
CONFIG = ROOT / "tools/ck3_mod_acceptance_cases/rmtm_core.json"
BASELINE = "f573a8f8a1a1df31704d06f5149a2758cd1fc5a1"


class Phase4PreSendQualification(unittest.TestCase):
    def test_strict_opt_in_core_and_ui_only(self):
        self.assertFalse(emitter.phase4_enabled())
        self.assertFalse(adapter.phase4_enabled({"case": "core", "case_inputs": {}}))
        self.assertTrue(adapter.phase4_enabled({"case": "core", "case_inputs": {emitter.PHASE4_OPTION: True}}))
        for value in (None, 0, 1, "true", [], {}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                emitter.phase4_enabled(value)
            with self.subTest(adapter=value), self.assertRaises(ValueError):
                adapter.phase4_enabled({"case": "core", "case_inputs": {emitter.PHASE4_OPTION: value}})
        for ui, threshold in ((False, False), (True, True)):
            with self.assertRaises(ValueError):
                emitter.phase4_enabled(True, ui_checkpoints=ui, threshold_ui=threshold)
        with self.assertRaises(ValueError):
            adapter.phase4_enabled({"case": "threshold_ui", "case_inputs": {emitter.PHASE4_OPTION: True}})

    def test_disabled_driver_exactly_matches_previous_canonical_driver(self):
        previous = subprocess.check_output(["git", "show", BASELINE + ":tools/prepare_reclaim_the_motherland_1_20_fixture.py"], cwd=ROOT)
        tree = ast.parse(previous.decode("utf-8-sig"))
        functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in ("event", "events")]
        namespace = {}
        exec(compile(ast.Module(body=functions, type_ignores=[]), "previous-driver-only", "exec"), namespace)
        for ui in (False, True):
            self.assertEqual(emitter.events(ui).encode("utf-8-sig"), namespace["events"](ui).encode("utf-8-sig"))

    def test_unique_line_projection_exact_inverse_bom_and_dates(self):
        original = emitter.events(True).encode("utf-8-sig")
        for raw in (original, original.replace(b"\n", b"\r\n")):
            projected = emitter.phase4_project(raw)
            self.assertTrue(projected.startswith(codecs.BOM_UTF8))
            self.assertEqual(emitter.phase4_project(projected, inverse=True), raw)
            self.assertNotIn(emitter.PHASE4_SEND.rstrip(), projected)
            self.assertEqual(projected.count(emitter.PHASE4_READY.encode()), 1)
            self.assertNotIn(b"debug_log_scopes", projected)
            parse_clausewitz(projected.decode("utf-8-sig"))
        for invalid in (original.replace(emitter.PHASE4_SEND, b""), original + emitter.PHASE4_SEND,
                        emitter.phase4_project(original)):
            with self.assertRaises(ValueError):
                emitter.phase4_project(invalid)
        with self.assertRaises(ValueError):
            emitter.phase4_project(emitter.phase4_project(original).replace(b"TEST READY", b"TEST PASS"), inverse=True)

    def test_only_original_probe_block_and_manual_onclick_support(self):
        support = emitter.phase4_support(SOURCE)
        original = (SOURCE / "common/scripted_guis/rqa_guis.txt").read_bytes()
        scripted = support["common/scripted_guis/rqa120_phase4_probe_gui.txt"]
        self.assertIn(scripted[len(codecs.BOM_UTF8):-1], original)
        self.assertEqual(scripted.count(b"rqa_execute_vassalization_probe_effect = yes"), 1)
        self.assertNotIn(b"rqa_initialize_gui", scripted)
        widget = support[emitter.PHASE4_GUI_RELATIVE]
        for forbidden in (b"on_start", b"trigger_when", b"run_interaction", b"PASS"):
            self.assertNotIn(forbidden, widget)
        self.assertEqual(widget.count(b"onclick ="), 1)
        self.assertEqual(widget.count(b".Execute("), 1)
        self.assertIn(b"rqa_vassalization_target_a", widget)
        self.assertIn(b"rqa_vassalization_target_b", widget)
        for relative, raw in support.items():
            self.assertTrue(raw.startswith(codecs.BOM_UTF8), relative)
            if not relative.endswith(".yml"):
                parse_clausewitz(raw.decode("utf-8-sig"))
        raw = emitter.events(True).encode("utf-8-sig")
        receipt = emitter.phase4_projection_receipt(SOURCE, raw, emitter.phase4_project(raw), support)
        self.assertEqual(receipt["original_driver"], receipt["inverse_driver"])
        self.assertEqual(receipt["runtime_status"], "NOT_RUN")
        self.assertFalse(receipt["business_pass"])
        self.assertTrue(receipt["original_d4_two_refusals_still_required"])

    def test_original_business_source_and_all_36_families_remain_unchanged(self):
        for relative in ("tools/fixtures/reclaim_the_motherland_acceptance/common/scripted_effects/rqa_effects.txt",
                         "tools/fixtures/reclaim_the_motherland_acceptance/common/scripted_guis/rqa_guis.txt"):
            self.assertEqual((ROOT / relative).read_bytes(), subprocess.check_output(["git", "show", BASELINE + ":" + relative], cwd=ROOT))
        old = json.loads(subprocess.check_output(["git", "show", BASELINE + ":tools/ck3_mod_acceptance_cases/rmtm_core.json"], cwd=ROOT))
        current = json.loads(CONFIG.read_text(encoding="utf-8-sig"))
        self.assertEqual({key: value for key, value in current.items() if key != emitter.PHASE4_OPTION}, old)
        changed = subprocess.check_output(["git", "diff", "--name-only", "--", "mod_reclaim_the_motherland"], cwd=ROOT)
        self.assertEqual(changed, b"")
        source = (SOURCE / witness.FIXTURE_RELATIVE).read_bytes()
        self.assertIn(b"phase4_two_released_rulers_refused_immediate_vassalization", source)
        self.assertIn(b"execute_threshold = accept", source)

    def test_negative_default_score_record_not_ack_or_nonnegative(self):
        d3 = {"actor_character_id": 11, "title_id": 22, "date_raw": 33}
        response = {"status": "complete", "facts": dict.fromkeys(adapter.PHASE4_QUALIFY_FACTS, True),
            "evidence": [{"path": "test-in-memory", "bytes": 1, "sha256": "test-only"}],
            "phase4_qualification": {"actor_character_id": 11, "later_title_id": 22, "date_raw": 33,
                "targets": [{"slot": slot, "character_id": cid, "primary_title_id": tid,
                    "answer_score": -1, "answer_reason": "actual complete GUI text (test only)",
                    "default_flags": [{"name": "actual flag", "selected": False}]}
                    for slot, cid, tid in (("A", 44, 55), ("B", 66, 77))]}}
        with patch.object(adapter, "check_evidence", side_effect=lambda value: value):
            self.assertEqual(adapter.validate_phase4_review(response, d3), response["phase4_qualification"])
            invalids = []
            for score in (0, 1, None, True, "-1"):
                row = copy.deepcopy(response); row["phase4_qualification"]["targets"][0]["answer_score"] = score; invalids.append(row)
            for key, value in (("actor_character_id", 99), ("later_title_id", 99), ("date_raw", 34)):
                row = copy.deepcopy(response); row["phase4_qualification"][key] = value; invalids.append(row)
            row = copy.deepcopy(response); del row["phase4_qualification"]; invalids.append(row)
            row = copy.deepcopy(response); row["evidence"] = []; invalids.append(row)
            row = copy.deepcopy(response); row["facts"][adapter.PHASE4_QUALIFY_FACTS[0]] = False; invalids.append(row)
            row = copy.deepcopy(response); row["phase4_qualification"]["targets"][1]["character_id"] = 44; invalids.append(row)
            row = copy.deepcopy(response); row["phase4_qualification"]["targets"][0]["default_flags"][0]["selected"] = 1; invalids.append(row)
            for invalid in invalids:
                with self.assertRaises(ValueError):
                    adapter.validate_phase4_review(invalid, d3)

    def test_pure_validator_checks_actual_receipt_inverse_load_order_and_files(self):
        with tempfile.TemporaryDirectory(prefix="rmtm-phase4-tiny-") as directory:
            root = Path(directory)
            fixture, state = root / "fixture", root / "state"
            support = emitter.phase4_support(SOURCE)
            original = emitter.events(True).encode("utf-8-sig")
            projected = emitter.phase4_project(original)
            files = {"events/rqa120_events.txt": projected, **support}
            projections = []
            for relative, kind, source_path in (
                (witness.FIXTURE_RELATIVE, "execute", SOURCE / witness.FIXTURE_RELATIVE),
                (witness.CALLBACK_RELATIVE, "callback", ROOT / "mod_reclaim_the_motherland" / witness.CALLBACK_RELATIVE),
            ):
                files[relative], proof = witness.project(source_path.read_bytes(), kind)
                projections.append({"relative": relative, **proof})
            for relative, raw in files.items():
                for base in (fixture, state / "profile/mod-content/fixture"):
                    target = base / relative; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(raw)
            receipt = {"ui_checkpoints": True, "threshold_ui": False,
                emitter.PHASE4_OPTION: emitter.phase4_projection_receipt(SOURCE, original, projected, support),
                "scope_witness_projection": {"scope_dump_count": 3, "projections": projections},
                "prepared_file_sha256": {name: witness.byte_pin(raw)["sha256"] for name, raw in files.items()}}
            receipt_path = fixture.with_suffix(".prepare.json")
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            profile_receipt = root / "profile-preparation.json"
            profile_receipt.write_text(json.dumps({"provenance": {"kind": "case-emitter-and-exact-formal-staging",
                "fixture": str(fixture), "product": str(ROOT / "mod_reclaim_the_motherland")}}), encoding="utf-8")
            (state / "preparation.json").write_text(json.dumps({"preparation": pin(profile_receipt)}), encoding="utf-8")
            load_path = state / "profile/dlc_load.json"
            load_path.write_text(json.dumps({"enabled_mods": ["mod/product.mod", "mod/fixture.mod"]}), encoding="utf-8")
            context = {"repo_root": str(ROOT), "state_dir": str(state), "case": "core",
                "case_inputs": {emitter.PHASE4_OPTION: True, "product_dir": str(ROOT / "mod_reclaim_the_motherland")},
                "case_spec": {"adapter": {"config": str(CONFIG)}}}
            self.assertTrue(adapter.validate_contract(context)[emitter.PHASE4_OPTION])
            self.assertLess(sum(path.stat().st_size for path in root.rglob("*") if path.is_file()), 4 * 1024 * 1024)
            disabled = copy.deepcopy(context); disabled["case_inputs"][emitter.PHASE4_OPTION] = False
            with self.assertRaises(ValueError): adapter.validate_contract(disabled)
            receipt[emitter.PHASE4_OPTION]["business_pass"] = True
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            with self.assertRaises(ValueError): adapter.validate_contract(context)
            receipt[emitter.PHASE4_OPTION]["business_pass"] = False
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            load_path.write_text(json.dumps({"enabled_mods": ["mod/fixture.mod", "mod/product.mod"]}), encoding="utf-8")
            with self.assertRaises(ValueError): adapter.validate_contract(context)
            load_path.write_text(json.dumps({"enabled_mods": ["mod/product.mod", "mod/fixture.mod"]}), encoding="utf-8")
            target = state / "profile/mod-content/fixture" / emitter.PHASE4_GUI_RELATIVE
            target.write_bytes(target.read_bytes() + b"on_start = \"fake\"\n")
            with self.assertRaises(ValueError): adapter.validate_contract(context)
        self.assertFalse(root.exists(), "Tiny temporary files must be removed")


if __name__ == "__main__":
    unittest.main()
