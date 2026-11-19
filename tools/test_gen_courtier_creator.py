#!/usr/bin/env python3
"""Protect the main xar courtier source/metadata/fixture contract for exact CK3 1.21.0.3."""
import unittest
from pathlib import Path
import io
import json
import tempfile
import sys
from typing import ClassVar
from unittest import mock
from gen_vivhite_courtier import TraitMetadata

import extract_courtier_traits
import gen_courtier_creator as generator


class NewVanillaCourtierMetadataTests(unittest.TestCase):
    traits: ClassVar[list[TraitMetadata]]
    by_key: ClassVar[dict[str, TraitMetadata]]
    catalogs: ClassVar[dict[str, list[TraitMetadata]]]
    union: ClassVar[list[TraitMetadata]]
    @classmethod
    def setUpClass(cls) -> None:
        _, cls.traits = generator.load_snapshot()
        cls.by_key = {trait["key"]: trait for trait in cls.traits}
        cls.catalogs, cls.union = generator.build_catalogs(cls.traits)

    def test_erudite_and_new_scholar_have_distinct_identity_and_cost(self) -> None:
        self.assertNotIn("scholar", self.by_key)
        self.assertEqual(self.by_key["erudite"]["ruler_designer_cost"], 50)
        self.assertEqual(self.by_key["erudite"]["category"], "lifestyle")
        self.assertEqual(self.by_key["lifestyle_scholar"]["ruler_designer_cost"], 15)
        self.assertEqual(self.by_key["lifestyle_scholar"]["minimum_age"], 16)
        self.assertTrue(self.by_key["lifestyle_scholar"]["has_track"])
        self.assertEqual(self.by_key["herald"]["ruler_designer_cost"], 100)

    def test_new_clergy_and_debug_traits_stay_out_of_the_catalog(self) -> None:
        catalog_keys = {trait["key"] for trait in self.union}
        for key in ("cleric", "debug_enable_raiding_without_restrictions",
                    "debug_enable_raiding_per_standard_restrictions"):
            self.assertIn(key, self.by_key)
            self.assertNotIn(key, catalog_keys)

    def test_old_source_snapshot_cannot_regenerate_new_product(self) -> None:
        with self.assertRaisesRegex(ValueError, "source game version"):
            generator.load_snapshot(generator.SNAPSHOT.with_name("courtier_traits_1_19_0_6.json"))

    def test_junction_source_uses_reproducible_logical_snapshot_identity(self) -> None:
        self.assertEqual(extract_courtier_traits.source_label(extract_courtier_traits.DEFAULT_SOURCE),
                         "Crusader Kings III/game/common/traits/00_traits.txt")


    def test_all_snapshot_field_types_reject_json_confusion_before_consumption(self) -> None:
        original = generator.SNAPSHOT.read_text(encoding="utf-8-sig")
        mutations: tuple[tuple[str, object], ...] = (
            ("schema_version", True), ("schema_version", 1.0), ("schema_version", "1"),
            ("trait_count", True), ("trait_count", 311.0), ("trait_count", "311"),
            ("key", True), ("category", []), ("category", 1),
            ("physical", 1), ("physical", "yes"), ("shown_in_ruler_designer", 0),
            ("ruler_designer_cost", True), ("ruler_designer_cost", 10.0), ("ruler_designer_cost", None),
            ("minimum_age", True), ("minimum_age", 16.0), ("minimum_age", "16"),
            ("maximum_age", True), ("maximum_age", []), ("valid_sex", []),
            ("valid_sex", {}), ("valid_sex", True), ("valid_sex", "unknown"),
            ("group", 1), ("group_equivalence", False), ("opposites", [1]),
            ("opposites", "merchant_associate"), ("level", True), ("level", 2.0),
            ("has_track", 1), ("has_track", None),
        )
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "snapshot.json"
            for key, value in mutations:
                payload = json.loads(original)
                target = payload if key in {"schema_version", "trait_count"} else payload["traits"][0]
                target[key] = value
                path.write_text(json.dumps(payload), encoding="utf-8")
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    generator.load_snapshot(path)
            for key in generator.REQUIRED_TRAIT_FIELDS:
                payload = json.loads(original); del payload["traits"][0][key]
                path.write_text(json.dumps(payload), encoding="utf-8")
                with self.subTest(missing=key), self.assertRaises(ValueError):
                    generator.load_snapshot(path)
            for value in ([], None, True, {"schema_version": 1}):
                path.write_text(json.dumps(value), encoding="utf-8")
                with self.subTest(root=value), self.assertRaises(ValueError):
                    generator.load_snapshot(path)
            for field, value in (("source", []), ("traits", {})):
                payload=json.loads(original);payload[field]=value
                path.write_text(json.dumps(payload), encoding="utf-8")
                with self.subTest(field=field), self.assertRaises(ValueError):
                    generator.load_snapshot(path)
            for field in ("game_version", "file", "sha256", "extra"):
                payload=json.loads(original);payload["source"][field]=True
                path.write_text(json.dumps(payload), encoding="utf-8")
                with self.subTest(source_field=field), self.assertRaises(ValueError):
                    generator.load_snapshot(path)

    def test_florin_native_catalog_reaches_xar_prices_age_and_opposite_consumers(self) -> None:
        self.assertEqual(generator.SNAPSHOT.name, "courtier_traits_1_21_0_3.json")
        self.assertEqual({key:len(value) for key,value in self.catalogs.items()},
                         {"education":25,"commander":17,"physical":38,"personality":36,"other":114})
        self.assertEqual((len(self.traits),len(self.union)),(311,230))
        self.assertEqual(sum(trait["shown_in_ruler_designer"] for trait in self.traits),229)
        keys={trait["key"] for trait in self.union}
        self.assertTrue({"devoted","merchant_associate","lifestyle_merchant","dealbreaker"}<=keys)
        self.assertTrue({"adopted_no_inheritance","education_republican_knowledge_5"}.isdisjoint(keys))
        conflicts=generator.build_conflicts(self.traits,self.union)
        self.assertEqual(len(generator.conflict_pairs(self.union,conflicts)),96)
        self.assertEqual(conflicts["merchant_associate"],["lifestyle_merchant"])
        self.assertEqual(conflicts["lifestyle_merchant"],["merchant_associate"])
        effects=generator.generated_effects(self.catalogs,self.union,conflicts)
        values=generator.generated_values(self.union);triggers=generator.generated_triggers(self.union,conflicts)
        for key,cost in (("devoted",0),("merchant_associate",10),("lifestyle_merchant",10),("dealbreaker",10)):
            self.assertEqual(self.by_key[key]["ruler_designer_cost"],cost)
            self.assertIn("trait:"+key,effects);self.assertIn("trait:"+key,values);self.assertIn("trait:"+key,triggers)
        for key in ("lifestyle_merchant","dealbreaker"):
            self.assertIn("var:xar_cc_age >= 16",generator.metadata_checks(self.by_key[key]))
        self.assertIn("xar_cc_remove_selected_trait_effect = { TRAIT = trait:lifestyle_merchant }",effects)
        self.assertIn("xar_cc_remove_selected_trait_effect = { TRAIT = trait:merchant_associate }",effects)
        self.assertNotIn("ervc_",effects+values+triggers)

    def test_reviewed_extraction_requires_explicit_version_and_protects_historical_default(self) -> None:
        current="793718c2388f8d7b6c009468a2f5f8f5d1d8443acec4a015614ffac4f05b98cd"
        with mock.patch.object(sys,"argv",["extract_courtier_traits.py"]), mock.patch("sys.stderr",new=io.StringIO()):
            with self.assertRaises(SystemExit) as rejected:
                extract_courtier_traits.parse_args()
            self.assertEqual(rejected.exception.code,2)
        with self.assertRaisesRegex(ValueError,"historical default"):
            extract_courtier_traits.validate_reviewed_output("1.21.0.3",current,extract_courtier_traits.DEFAULT_OUTPUT,explicit_output=False)
        with self.assertRaisesRegex(ValueError,"historical default"):
            extract_courtier_traits.validate_reviewed_output("1.21.0.3",current,extract_courtier_traits.DEFAULT_OUTPUT,explicit_output=True)
        with tempfile.TemporaryDirectory() as temporary:
            output=Path(temporary)/"new.json"
            extract_courtier_traits.validate_reviewed_output("1.21.0.3",current,output,explicit_output=True)
            self.assertFalse(output.exists())
            with self.assertRaisesRegex(ValueError,"source SHA256"):
                extract_courtier_traits.validate_reviewed_output("1.20.0.3",current,output,explicit_output=True)

    def test_real_shared_fixture_consumes_main_catalog_and_preserves_rite_assertions(self) -> None:
        import prepare_courtier_1_20_fixture as fixture
        output=fixture.extra_ui_effects("xar")
        self.assertIn("name = xar_cc_catalog_other value = 114",output)
        self.assertIn("CCA120: PASS florin_trait_catalog",output)
        for key in ("devoted","merchant_associate","lifestyle_merchant","dealbreaker"):
            self.assertIn("name = xar_cc_catalog_other target = trait:"+key,output)
        self.assertNotIn("ervc_",output)
        self.assertIn("var:xar_cc_selected_rite = root.rite",output)
        self.assertIn("var:xar_cc_selected_rite = faith:aluk.main_rite",output)
        with self.assertRaises(ValueError):fixture.extra_ui_effects("unknown")

if __name__ == "__main__":
    unittest.main()
