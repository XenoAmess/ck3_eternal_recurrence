"""Focused producer/consumer JSON contract regressions; no media decode or process query."""
from __future__ import annotations
import copy
import io
import json
from pathlib import Path
import unittest
from PIL import Image
from r11_visual_contract_a02 import RawStat, Recipe, decimal64, integer, load_map, object_map
from r11_recipe_a02 import ROOT, NEW_RECIPE, build_document, legacy_decimal
from r11_once_contacts_a02_final import jpeg_read

def assert_safe_json_numbers(value: object) -> None:
    if type(value) is int:
        if abs(value)>2**53-1:
            raise AssertionError("Unsafe JSON numeric identity")
    elif isinstance(value,dict):
        for item in value.values():
            assert_safe_json_numbers(item)
    elif isinstance(value,list):
        for item in value:
            assert_safe_json_numbers(item)

class ContractTests(unittest.TestCase):
    def test_real_producer_consumer_roundtrip(self) -> None:
        produced=build_document()
        value: object=json.loads(json.dumps(produced))
        consumed=Recipe.parse(value)
        actual=RawStat.from_native(Path(consumed.retained_source.path).stat())
        self.assertEqual(consumed.retained_source_stat,actual)
        self.assertEqual(consumed.process_birth_filetime,"134365505726865638")
        assert_safe_json_numbers(value)

    def test_actual_frozen_recipe_uses_same_domain(self) -> None:
        row=load_map(NEW_RECIPE)
        parsed=Recipe.parse(row)
        self.assertEqual(parsed.retained_source_stat,RawStat.from_native(Path(parsed.retained_source.path).stat()))
        assert_safe_json_numbers(row)

    def test_rawstat_json_exact_roundtrip(self) -> None:
        raw=RawStat(56479663,"1792078260762602000","13886423844274364792","844424932065981")
        value: object=json.loads(json.dumps(raw.wire()))
        self.assertEqual(RawStat.parse(value),raw)

    def test_missing_and_misspelled_stat_fields_rejected(self) -> None:
        good=object_map(build_document().get("retained_source_stat"),"stat")
        missing=good.copy()
        del missing["mtime_ns"]
        with self.assertRaises(ValueError):
            RawStat.parse(missing)
        wrong=good.copy()
        wrong["mtimeNs"]=wrong.pop("mtime_ns")
        with self.assertRaises(ValueError):
            RawStat.parse(wrong)

    def test_numeric_bool_float_and_noncanonical_decimal_rejected(self) -> None:
        bad: list[object]=[1792078260762602000,True,1.0,"001","-1"," 1","1e2",str(2**64)]
        for value in bad:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    decimal64(value,"identity")
        self.assertEqual(decimal64("0","identity"),"0")
        self.assertEqual(decimal64(str(2**64-1),"identity"),str(2**64-1))

    def test_every_stat_identity_rejects_legacy_numeric_in_consumer(self) -> None:
        row=object_map(build_document().get("retained_source_stat"),"stat")
        for field in ("mtime_ns","st_dev","st_ino"):
            bad=row.copy()
            bad[field]=1
            with self.subTest(field=field):
                with self.assertRaises(ValueError):
                    RawStat.parse(bad)

    def test_birth_filetime_consumer_rejects_numeric_missing_and_float(self) -> None:
        for value in (134365505726865638,True,1.3436550572686564e17,None):
            row=copy.deepcopy(build_document())
            binding=object_map(row["historical_binding"],"binding")
            binding["process_birth_filetime"]=value
            row["historical_binding"]=binding
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    Recipe.parse(row)

    def test_legacy_producer_rejects_coercion(self) -> None:
        self.assertEqual(legacy_decimal(134365505726865638,"birth"),"134365505726865638")
        for value in (True,1.0,"134365505726865638"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    legacy_decimal(value,"birth")

    def test_safe_numeric_counter_boundary(self) -> None:
        self.assertEqual(integer(2**53-1,"counter"),2**53-1)
        for value in (2**53,True,1.0,"1"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    integer(value,"counter")

    def test_recipe_argv_wrong_type_rejected(self) -> None:
        row=build_document()
        row["argv"]=["ffmpeg",True]
        with self.assertRaises(ValueError):
            Recipe.parse(row)

    def test_inherited_jpeg_parser_two_images_and_eof(self) -> None:
        memory=io.BytesIO()
        Image.new("RGB",(2,2)).save(memory,format="JPEG")
        image=memory.getvalue()
        stream=io.BytesIO(image+image)
        self.assertEqual(jpeg_read(stream),image)
        self.assertEqual(jpeg_read(stream),image)
        with self.assertRaises(EOFError):
            jpeg_read(stream)

if __name__=="__main__":
    unittest.main(verbosity=2)
