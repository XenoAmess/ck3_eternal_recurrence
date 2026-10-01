#!/usr/bin/env python3
"""Guard CK3 1.20 creator metadata against obsolete trait identities."""
import unittest

import extract_courtier_traits
import gen_courtier_creator as generator


class NewVanillaCourtierMetadataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, cls.traits = generator.load_snapshot()
        cls.by_key = {trait["key"]: trait for trait in cls.traits}
        cls.catalogs, cls.union = generator.build_catalogs(cls.traits)

    def test_erudite_and_new_scholar_have_distinct_identity_and_cost(self):
        self.assertNotIn("scholar", self.by_key)
        self.assertEqual(self.by_key["erudite"]["ruler_designer_cost"], 50)
        self.assertEqual(self.by_key["erudite"]["category"], "lifestyle")
        self.assertEqual(self.by_key["lifestyle_scholar"]["ruler_designer_cost"], 15)
        self.assertEqual(self.by_key["lifestyle_scholar"]["minimum_age"], 16)
        self.assertTrue(self.by_key["lifestyle_scholar"]["has_track"])
        self.assertEqual(self.by_key["herald"]["ruler_designer_cost"], 100)

    def test_new_clergy_and_debug_traits_stay_out_of_the_catalog(self):
        catalog_keys = {trait["key"] for trait in self.union}
        for key in ("cleric", "debug_enable_raiding_without_restrictions",
                    "debug_enable_raiding_per_standard_restrictions"):
            self.assertIn(key, self.by_key)
            self.assertNotIn(key, catalog_keys)

    def test_old_source_snapshot_cannot_regenerate_new_product(self):
        with self.assertRaisesRegex(ValueError, "source game version"):
            generator.load_snapshot(generator.SNAPSHOT.with_name("courtier_traits_1_19_0_6.json"))

    def test_junction_source_uses_reproducible_logical_snapshot_identity(self):
        self.assertEqual(extract_courtier_traits.source_label(extract_courtier_traits.DEFAULT_SOURCE),
                         "Crusader Kings III/game/common/traits/00_traits.txt")


if __name__ == "__main__":
    unittest.main()
