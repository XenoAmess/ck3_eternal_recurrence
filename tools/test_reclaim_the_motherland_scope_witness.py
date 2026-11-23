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




class ScopeWitnessReadOnlyConsumer(unittest.TestCase):
    """Explicit software fixtures only; no actual CK3 or D5 facts."""

    LABELS = {"character": "Character", "title": "Landed title"}

    @classmethod
    def payload(cls, phase="execute", language="english", number=0x8100002A):
        required = next(item[3] for item in witness._SCOPE_PHASES if item[0] == phase)
        rows = ["Software current scope only", "Root: SOFTWARE FIXTURE", "", "Saved event targets:"]
        for name, kind in required:
            value = witness._SCOPE_DEBUG_FORMATS[language].replace("$NAME$", "Software NAME (Internal ID: 7)")
            value = value.replace("$TYPE|U$", cls.LABELS[kind]).replace("$ID$", str(number))
            rows.append(name + ": " + value)
        return ("\n".join(rows) + "\n").encode("utf-8")

    @classmethod
    def raw_log(cls, language="english", number=0x8100002A):
        values = []
        for phase, begin, end, _ in witness._SCOPE_PHASES:
            values += [witness.PREFIX + b" " + begin + b"\n",
                       cls.payload(phase, language, number),
                       witness.PREFIX + b" " + end + b"\n"]
        return b"".join(values)

    @staticmethod
    def source(raw):
        return {"path": "SOFTWARE-FIXTURE-ONLY/debug.log", **witness.byte_pin(raw)}

    def parsed(self, raw):
        return witness.parse_original_scope_witness_log(raw, self.source(raw),
            layout="UNPREFIXED_SOFTWARE_FIXTURE_V1", language="english", kind_labels=self.LABELS)

    def test_three_exact_containers_and_byte_ranges_are_only_software_data(self):
        raw = self.raw_log()
        result = self.parsed(raw)
        self.assertEqual(result["status"], "PARSED_SOFTWARE_FIXTURE_ONLY")
        self.assertEqual([row["phase"] for row in result["containers"]],
                         ["execute", "callback_entry", "callback_exit"])
        self.assertFalse(result["business_pass"])
        self.assertFalse(result["execute_time_identity_qualified"])
        for container in result["containers"]:
            for row in container["parsed_data"]["targets"]:
                a, z = row["row_byte_range"]
                self.assertEqual(raw[a:z].decode("utf-8"), row["raw_row"])
                self.assertEqual(row["full_packed_id"], 0x8100002A)

    def test_real_log_default_remains_unbound_without_transport_and_type_sample(self):
        raw = self.raw_log()
        result = witness.parse_original_scope_witness_log(raw, self.source(raw))
        self.assertEqual(result["status"], "UNBOUND_LOG_TRANSPORT_AND_TYPE_LABELS")
        self.assertIn("required_actual_sample", result)
        self.assertTrue(all("parsed_data" not in row for row in result["containers"]))
        with self.assertRaises(witness.ScopeWitnessParseError):
            witness.parse_original_scope_witness_log(raw, self.source(raw), layout="CURRENT267_QUALIFIED")

    def test_zero_and_high_generation_are_preserved_with_no_native_actor_authority(self):
        for number in (0, 1, 0x01000001, 0x80000000, 0xFFFFFFFE):
            with self.subTest(number=number):
                result = witness.parse_scope_dump_payload(self.payload(number=number), "execute",
                    language="english", kind_labels=self.LABELS)
                self.assertEqual({row["full_packed_id"] for row in result["targets"]}, {number})
                self.assertEqual(result["world_binding"], "NOT_CHECKED")
                self.assertNotIn("native_revision", result)

    def test_all_static_localized_suffixes_and_multibyte_offsets_preserve_full_id(self):
        for language in witness._SCOPE_DEBUG_FORMATS:
            with self.subTest(language=language):
                raw = self.payload(language=language).replace(b"Software NAME", "测试名字".encode())
                result = witness.parse_scope_dump_payload(raw, "execute", language=language,
                    kind_labels=self.LABELS, origin_byte=73)
                for row in result["targets"]:
                    a, z = row["row_byte_range"]
                    self.assertEqual(raw[a-73:z-73].decode(), row["raw_row"])

    def test_wrong_kind_missing_duplicate_and_saved_list_only_targets_are_rejected(self):
        raw = self.payload()
        row = raw.splitlines(keepends=True)[4]
        failures = [raw.replace(b"Landed title", b"Character", 1), raw.replace(row, b"", 1),
                    raw + row, raw.replace(b"Saved event targets:", b"Saved list targets:"),
                    raw.replace(row, row + row.replace(b": ", b":: ", 1), 1)]
        for bad in failures:
            with self.subTest(bad=bad), self.assertRaises(witness.ScopeWitnessParseError):
                witness.parse_scope_dump_payload(bad, "execute", language="english", kind_labels=self.LABELS)

    def test_invalid_full_id_width_sentinel_sign_and_noncanonical_decimal_are_rejected(self):
        raw = self.payload(number=1)
        for token in (b"4294967295", b"4294967296", b"-1", b"01", b"9" * 20):
            bad = raw.replace(b" - 1)#!", b" - " + token + b")#!", 1)
            with self.subTest(token=token), self.assertRaises(witness.ScopeWitnessParseError):
                witness.parse_scope_dump_payload(bad, "execute", language="english", kind_labels=self.LABELS)

    def test_duplicate_missing_reordered_truncated_and_marker_suffix_containers_reject(self):
        raw = self.raw_log()
        end = witness.PREFIX + b" EXEC_END\n"
        phases = raw.split(witness.PREFIX + b" CALLBACK_ENTRY_BEGIN\n", 1)
        bad_logs = [raw + end, raw.replace(end, b"", 1), raw[:-10],
                    raw.replace(b"EXEC_BEGIN\n", b"EXEC_BEGIN_fake\n", 1),
                    phases[1] + witness.PREFIX + b" CALLBACK_ENTRY_BEGIN\n" + phases[0]]
        for bad in bad_logs:
            with self.subTest(bad=bad), self.assertRaises(witness.ScopeWitnessParseError):
                self.parsed(bad)

    def test_file_pin_rejects_hash_bytes_bool_or_unknown_fields_without_file_reads(self):
        raw = self.raw_log()
        original = self.source(raw)
        cases = [{**original, "bytes": True}, {**original, "bytes": len(raw)+1},
                 {**original, "sha256": "0"*64}, {**original, "caller_title_id": 1}]
        for source in cases:
            with self.subTest(source=source), self.assertRaises(witness.ScopeWitnessParseError):
                witness.extract_original_scope_dump_containers(raw, source)

    def test_unobserved_logger_decoration_is_retained_but_never_silently_stripped(self):
        raw = self.raw_log().replace(witness.PREFIX, b"[SOFTWARE logger] " + witness.PREFIX)
        result = witness.extract_original_scope_dump_containers(raw, self.source(raw))
        self.assertEqual(len(result["containers"]), 3)
        self.assertEqual(result["status"], "UNBOUND_LOG_TRANSPORT_AND_TYPE_LABELS")
        with self.assertRaises(witness.ScopeWitnessParseError):
            self.parsed(raw)

    def test_incomplete_utf8_nul_format_and_ambiguous_kind_labels_are_rejected(self):
        raw = self.payload()
        cases = [raw+b"\xff", raw+b"\x00", raw.replace(b")#!", b")", 1)]
        for bad in cases:
            with self.subTest(bad=bad), self.assertRaises(witness.ScopeWitnessParseError):
                witness.parse_scope_dump_payload(bad, "execute", language="english", kind_labels=self.LABELS)
        with self.assertRaises(witness.ScopeWitnessParseError):
            witness.parse_scope_dump_payload(raw, "execute", language="english",
                kind_labels={"character": "same", "title": "same"})

class ScopeWitnessObservedFormatSource(unittest.TestCase):
    """Four software boundary methods, NOT_RUN; no runtime/business qualification."""

    def test_literal_hash_and_control15_require_explicit_separate_encodings(self):
        for language in witness._SCOPE_DEBUG_FORMATS:
            literal=ScopeWitnessReadOnlyConsumer.payload(language=language)
            encoded=literal.replace(b"#weak",b"\x15weak").replace(b"#!",b"\x15!")
            for payload, encoding in ((literal,"LITERAL_HASH"),(encoded,"CONTROL15")):
                data=witness.parse_scope_dump_payload(payload,"execute",language=language,
                    kind_labels=ScopeWitnessReadOnlyConsumer.LABELS,richtext_encoding=encoding)
                self.assertFalse(data["business_pass"])
                self.assertEqual({r["full_packed_id"] for r in data["targets"]},{0x8100002A})
            with self.assertRaises(witness.ScopeWitnessParseError):
                witness.parse_scope_dump_payload(encoded,"execute",language=language,kind_labels=ScopeWitnessReadOnlyConsumer.LABELS)
            with self.assertRaises(witness.ScopeWitnessParseError):
                witness.parse_scope_dump_payload(literal,"execute",language=language,kind_labels=ScopeWitnessReadOnlyConsumer.LABELS,richtext_encoding="CONTROL15")

    @staticmethod
    def prefixed():
        raw=ScopeWitnessReadOnlyConsumer.payload(language="simp_chinese",number=0xFFFFFFFE)
        raw=raw.replace(b"#weak",b"\x15weak").replace(b"#!",b"\x15!")
        return (b"[03:57:00][D][effectimpl.cpp:656]: empty\n"+raw.split(b"\n",1)[1]).replace(b"\n",b"\r\n")

    def test_first_line_prefix_preserves_all_original_offsets_and_never_grants_runtime(self):
        raw=self.prefixed();origin=545213
        result=witness.parse_first_line_prefixed_scope_payload(raw,"execute",language="simp_chinese",
            kind_labels=ScopeWitnessReadOnlyConsumer.LABELS,origin_byte=origin)
        self.assertEqual(result["status"],"PARSED_PREFIXED_FORMAT_DATA_ONLY")
        self.assertEqual(result["original_phase_type_binding"],"NOT_OBSERVED")
        self.assertEqual(result["world_binding"],"NOT_CHECKED")
        self.assertFalse(result["business_pass"]);self.assertFalse(result["execute_time_identity_qualified"])
        for row in result["targets"]:
            a,z=row["row_byte_range"]
            self.assertEqual(raw[a-origin:z-origin].decode(),row["raw_row"])
            self.assertEqual(row["full_packed_id"],0xFFFFFFFE)
            self.assertIn("Internal ID: 7",row["raw_row"])

    def test_unknown_first_prefix_or_prefixed_and_interleaved_continuations_reject(self):
        raw=self.prefixed()
        bad=[raw.replace(b"effectimpl.cpp:656",b"unknown.cpp:656",1),
             raw.replace(b"Root: ",b"[03:57:00][D][effectimpl.cpp:656]: Root: ",1),
             raw+b"[03:57:00][D][jomini_effect_impl.cpp:444]: unrelated\r\n",
             raw+b"\x00",raw+b"\xff"]
        for value in bad:
            with self.assertRaises(witness.ScopeWitnessParseError):
                witness.parse_first_line_prefixed_scope_payload(value,"execute",language="simp_chinese",kind_labels=ScopeWitnessReadOnlyConsumer.LABELS)

    def test_actual_ordinary_fragment_cannot_supply_original_fixed_witness_names(self):
        # Original292B observed fragment, immutable DATA copy; no liege/employee remapping.
        raw=bytes.fromhex("5b30333a35373a30305d5b445d5b656666656374696d706c2e6370703a3635365d3a20656d7074790a526f6f743a20656d7074790a0a5361766564206576656e7420746172676574733a0a6c696567653a20457274756772756c20e8b596e5a786e696afe7a791e880b6206f6620635f7261696d736b6f652028496e7465726e616c2049443a203433323739202d20486973746f726963616c2049442066696374696f6e616c5f7475726b6973685f323029157765616b20efbc884368617261637465722d3433323739efbc8915210a656d706c6f7965653a205369726d6120e587bae8baabe58d91e5beae206f66202028496e7465726e616c20494420353739383329157765616b20efbc884368617261637465722d3537393833efbc8915210a0d0a")
        self.assertIn(b"Saved event targets:",raw)
        self.assertIn(b"Character-43279",raw);self.assertIn(b"Character-57983",raw)
        with self.assertRaises(witness.ScopeWitnessParseError):
            witness.parse_first_line_prefixed_scope_payload(raw,"execute",language="simp_chinese",kind_labels=ScopeWitnessReadOnlyConsumer.LABELS)
        with self.assertRaises(witness.ScopeWitnessParseError):
            witness.parse_original_scope_witness_log(raw,ScopeWitnessReadOnlyConsumer.source(raw))


if __name__ == "__main__":
    unittest.main()
