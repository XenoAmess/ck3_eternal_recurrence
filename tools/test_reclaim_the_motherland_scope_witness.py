"""One bounded in-memory scope-witness class; no prepare, game, or fixture copy."""
from __future__ import annotations

import ast
import codecs
import json
from pathlib import Path
import unittest

import reclaim_the_motherland_scope_witness as witness
from test_reclaim_the_motherland_contract import Block, parse_clausewitz


ROOT = Path(__file__).resolve().parents[1]


class ScopeWitnessProjection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.originals = {
            "execute": (ROOT / "tools/fixtures/reclaim_the_motherland_acceptance" /
                        witness.FIXTURE_RELATIVE).read_bytes(),
            "callback": (ROOT / "mod_reclaim_the_motherland" /
                         witness.CALLBACK_RELATIVE).read_bytes(),
        }

    def test_exact_inverse_preserves_all_original_bytes_and_line_endings(self):
        for kind, raw in self.originals.items():
            self.assertTrue(raw.startswith(codecs.BOM_UTF8))
            for original in (raw, raw.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")):
                with self.subTest(kind=kind, crlf=b"\r\n" in original):
                    projected, proof = witness.project(original, kind)
                    self.assertEqual(witness.restore(projected, kind), original)
                    self.assertEqual(proof["source"], proof["inverse"])
                    self.assertEqual(proof["projected"], witness.byte_pin(projected))
                    parse_clausewitz(projected.decode("utf-8-sig"))

    def test_payloads_are_only_readonly_observation_and_three_dumps(self):
        allowed = {"if", "limit", "else", "exists", "has_character_flag", "var:rqa_later_title",
                   "primary_title", "current_heir", "save_temporary_scope_as",
                   "debug_log", "debug_log_scopes", "var:rmtm_succession_title",
                   "var:rmtm_succession_heir", "scope:rqa_wit_v1_callback_later", "holder"}

        def entries(block):
            for entry in block.entries:
                yield entry
                if isinstance(entry.value, Block):
                    yield from entries(entry.value)

        dumps = 0
        for payload in (witness.EXECUTE, witness.CALLBACK_ENTRY, witness.CALLBACK_EXIT):
            for entry in entries(parse_clausewitz(payload)):
                self.assertIn(entry.key, allowed)
                if entry.key == "save_temporary_scope_as":
                    self.assertTrue(entry.value.startswith("rqa_wit_v1_"))
                if entry.key == "has_character_flag":
                    self.assertEqual(entry.value, "rqa_waiting_for_succession")
                if entry.key == "debug_log":
                    self.assertTrue(entry.value.startswith('"RQA_WITNESS_V1 '))
                    self.assertNotIn("PASS", entry.value)
                if entry.key == "debug_log_scopes":
                    self.assertEqual(entry.value, "yes")
                    dumps += 1
        self.assertEqual(dumps, 3)

    def test_execute_dump_is_adjacent_to_unchanged_setter_and_real_death(self):
        projected, _ = witness.project(self.originals["execute"], "execute")
        text = projected.decode("utf-8-sig").replace("\r\n", "\n")
        anchor = witness.SPECS["execute"][0]
        self.assertIn(witness.EXECUTE + anchor, text)
        self.assertIn(anchor + "\t\t\tscope:rqa_predecessor = { death = { death_reason = death_natural_causes } }", text)
        self.assertIn("save_scope_as = rqa_predecessor", text)
        self.assertIn("current_heir = { save_scope_as = rqa_later_heir }", text)
        self.assertIn("trigger_event = { id = rqa.3 days = 2 }", text)
        for token in ("rqa_wit_v1_exec_later", "rqa_wit_v1_exec_current_heir",
                      "rqa_wit_v1_exec_primary_heir"):
            self.assertIn(token, witness.EXECUTE)

    def test_callback_sandwich_keeps_original_call_exactly_once(self):
        projected, proof = witness.project(self.originals["callback"], "callback")
        text = projected.decode("utf-8-sig").replace("\r\n", "\n")
        anchor = witness.SPECS["callback"][0]
        self.assertIn(witness.CALLBACK_ENTRY + anchor + witness.CALLBACK_EXIT, text)
        self.assertEqual(text.count(anchor), 1)
        self.assertEqual(proof["scope_dump_count"], 2)
        self.assertIn("scope:rqa_wit_v1_callback_later", witness.CALLBACK_EXIT)
        self.assertIn("rqa_wit_v1_callback_holder_after", witness.CALLBACK_EXIT)
        self.assertIn("rqa_wit_v1_callback_primary_after", witness.CALLBACK_EXIT)
        for payload in (witness.CALLBACK_ENTRY, witness.CALLBACK_EXIT):
            self.assertIn("limit = { has_character_flag = rqa_waiting_for_succession }", payload)
        self.assertEqual(proof["runtime_status"], "NOT_RUN")
        self.assertFalse(proof["persistent_writes"])
        self.assertFalse(proof["business_pass"])

    def test_missing_duplicate_reprojection_and_changed_payload_are_rejected(self):
        for kind, raw in self.originals.items():
            anchor = witness.SPECS[kind][0].encode("ascii")
            original = raw.replace(b"\r\n", b"\n")
            for invalid in (original.replace(anchor, b"", 1), original + anchor):
                with self.subTest(kind=kind), self.assertRaises(ValueError):
                    witness.project(invalid, kind)
            projected, _ = witness.project(raw, kind)
            with self.assertRaises(ValueError):
                witness.project(projected, kind)
            with self.assertRaises(ValueError):
                witness.restore(projected.replace(b"debug_log_scopes = yes", b"debug_log_scopes = no", 1), kind)

    def test_public_emitter_uses_formal_input_and_declares_overlay_without_running(self):
        emitter = (ROOT / "tools/prepare_reclaim_the_motherland_1_20_fixture.py").read_text(encoding="utf-8-sig")
        adapter = (ROOT / "tools/ck3_mod_acceptance_cases/rmtm_adapter.py").read_text(encoding="utf-8-sig")
        ast.parse(emitter)
        ast.parse(adapter)
        self.assertIn('parser.add_argument("--formal-product-dir", type=Path, required=True)', emitter)
        self.assertIn('"--formal-product-dir", context["case_inputs"]["product_dir"]', adapter)
        self.assertIn('"scope_witness_projection":scope_witness_proof', emitter)
        self.assertIn('"scope_witness_projection": scope_witness', adapter)
        self.assertIn('"formal_staging_modified": False', emitter)
        self.assertIn('"current_build_scope_dump_format": "NOT_OBSERVED"', emitter)

    def test_original_day_and_family_contract_is_untouched(self):
        contract = json.loads((ROOT / "tools/ck3_mod_acceptance_cases/rmtm_core.json").read_text(encoding="utf-8-sig"))
        self.assertEqual(contract["natural_game_day_limit"], 14)
        self.assertEqual(contract["fixture_recent_independence_override_days"], 10)
        self.assertEqual(contract["original_family_count"], 36)
        self.assertEqual(contract["unchanged_family_count"], 33)
        self.assertEqual(contract["physical_qualified_family_count"], 3)


if __name__ == "__main__":
    unittest.main()
