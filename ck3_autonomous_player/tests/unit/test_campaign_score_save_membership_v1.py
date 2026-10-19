"""Small in-memory saved worlds; no decoder, actual SAVE or Native endpoint."""
from copy import deepcopy
from decimal import Decimal as D
import io
import unittest

from xar_autoplayer.campaign_score_save_reader import SaveProjection, melt_tokens, project_metrics
from xar_autoplayer.campaign_score_target_projection import enrich_metrics


TITLES = ('90={key=d_realm holder=1} 100={key=c_a holder=1} '
          '101={key=c_b holder=2 de_facto_liege=90} 102={key=c_out holder=3}')
HOUSES = '174={dynasty=174} 175={dynasty=174 parent_dynasty_house=174} 200={dynasty=200}'
CONTEXT = {"county_baronies": {"c_a": {"b_a": 12}, "c_b": {"b_b": 13}, "c_out": {"b_out": 14}},
           "founding_house_id": 174, "founding_dynasty_id": 174,
           "founding_anchor_source": "synthetic_T0",
           "baseline_counties": [{"development": "0", "control": "100"}]}


def world(*, titles=TITLES, houses=HOUSES, characters=None, extra="", context=None):
    if characters is None:
        characters = '1={dynasty_house=174} 2={dynasty_house=175} 3={dynasty_house=200}'
    source = ('date=1066.10.15 living={' + characters + '} landed_titles={' + titles + '} '
        'county_manager={c_a={development=0 control=100} c_b={development=0 control=100} '
        'c_out={development=0 control=100}} '
        'provinces={12={holding={type=castle_holding}} 13={holding={type=castle_holding}} '
        '14={holding={type=castle_holding}}} dynasties={dynasty_house={' + houses + '}} ' + extra)
    projection = SaveProjection({1})
    for token in melt_tokens(io.BytesIO(source.encode())):
        projection.token(token)
    projection.complete()
    actual_context = deepcopy(CONTEXT if context is None else context)
    metrics, detail, facts = project_metrics(projection, actor=1, founder=1,
        source_id="synthetic_checkpoint", static_context=actual_context)
    return projection, metrics, detail, facts


class SavedCountyMembershipTests(unittest.TestCase):
    def test_complete_realm_and_explicit_foreign_root_remain_exact_and_source_bound(self):
        _, metrics, detail, _ = world()
        audit = detail["county_membership_audit"]
        self.assertTrue(audit["title_census_complete"])
        self.assertTrue(audit["geography_complete"])
        self.assertTrue(audit["realm"]["complete"])
        self.assertEqual(audit["realm"]["known_member_title_ids"], [100, 101])
        self.assertIs(audit["states"][102]["in_player_realm"], False)
        self.assertEqual(audit["states"][102]["realm_reason"], "complete_foreign_title_root")
        self.assertEqual(audit["source_ref"], "synthetic_checkpoint")
        self.assertEqual(audit["date"], "1066.10.15")
        self.assertEqual((metrics["realm_county_count"]["value"], metrics["dynasty_county_count"]["value"]), ("2", "2"))
        self.assertEqual((D(metrics["Q_realm"]["value"]), D(metrics["K_dynasty"]["value"])), (D(2), D(2)))

    def test_missing_liege_or_cycle_is_unknown_not_false_or_precise_shrinkage(self):
        missing = TITLES.replace("de_facto_liege=90", "de_facto_liege=999")
        cycle = TITLES.replace("90={key=d_realm holder=1}", "90={key=d_realm holder=2 de_facto_liege=101}")
        for titles, reason, terminal in ((missing, "missing_de_facto_liege_title", 999),
                                         (cycle, "cyclic_de_facto_liege", 101)):
            with self.subTest(reason=reason):
                _, metrics, detail, facts = world(titles=titles)
                audit = detail["county_membership_audit"]
                self.assertIsNone(audit["states"][101]["in_player_realm"])
                self.assertEqual(audit["states"][101]["realm_reason"], reason)
                self.assertEqual(audit["states"][101]["realm_terminal_title_id"], terminal)
                self.assertIsNone(detail["realm_county_count"])
                self.assertEqual(detail["known_realm_county_count"], 1)
                self.assertEqual(metrics["realm_county_count"]["availability"], "bounded")
                self.assertEqual((metrics["realm_county_count"]["lower"], metrics["realm_county_count"]["upper"]), ("1", "2"))
                self.assertIsNone(metrics["Q_realm"]["value"])
                self.assertIsNone(metrics["control_average"]["value"])
                self.assertIsNone(metrics["K_dynasty"]["value"])
                self.assertEqual(metrics["dynasty_county_count"]["value"], "2")
                self.assertIn("不能据此计算失地", facts[0]["value_text"])
                # Targeted occupation absence cannot turn unknown membership
                # into an exact score by iterating only the known subset.
                enrich_metrics(metrics, detail, {"records": {}, "unknown_key_fields": 0}, {},
                    actor=1, source_ref="synthetic_target")
                self.assertEqual(metrics["Q_realm"]["availability"], "unknown")

    def test_true_out_of_realm_chain_is_not_over_rejected(self):
        _, metrics, detail, _ = world(titles=TITLES.replace("90={key=d_realm holder=1}", "90={key=d_realm holder=3}"))
        self.assertTrue(detail["county_membership_audit"]["realm"]["complete"])
        self.assertIs(detail["county_membership_audit"]["states"][101]["in_player_realm"], False)
        self.assertEqual(metrics["realm_county_count"]["value"], "1")
        self.assertEqual(D(metrics["Q_realm"]["value"]), D(1))
        self.assertEqual(D(metrics["K_dynasty"]["value"]), D("1.5"))

    def test_unknown_geography_never_counts_dynamic_or_unmapped_county_as_land(self):
        context = deepcopy(CONTEXT)
        del context["county_baronies"]["c_b"]
        for titles, ctx, expected_bounds in (
            (TITLES, context, ("1", "2")),
            (TITLES + " 103={key=c_dynamic_family holder=1}", CONTEXT, ("2", "3")),
        ):
            with self.subTest(bounds=expected_bounds):
                _, metrics, detail, _ = world(titles=titles, context=ctx)
                audit = detail["county_membership_audit"]
                self.assertFalse(audit["geography_complete"])
                self.assertIsNone(detail["realm_county_count"])
                self.assertEqual((metrics["realm_county_count"]["lower"], metrics["realm_county_count"]["upper"]), expected_bounds)
                self.assertIsNone(metrics["Q_realm"]["value"])
                self.assertIsNone(metrics["K_dynasty"]["value"])

    def test_invalid_mapping_or_duplicate_county_key_is_unknown(self):
        for mutation in ("province_conflict", "empty_map", "duplicate_key", "missing_key"):
            with self.subTest(mutation=mutation):
                context, titles = deepcopy(CONTEXT), TITLES
                if mutation == "province_conflict":
                    context["county_baronies"]["c_b"]["b_b"] = 12
                elif mutation == "empty_map":
                    context["county_baronies"]["c_b"] = {}
                elif mutation == "duplicate_key":
                    titles = titles.replace("key=c_b", "key=c_a")
                else:
                    titles = titles.replace("key=c_b ", "")
                _, metrics, detail, _ = world(titles=titles, context=context)
                self.assertIsNone(detail["realm_county_count"])
                self.assertIsNone(metrics["Q_realm"]["value"])
                self.assertEqual(metrics["realm_county_count"]["availability"], "bounded")

    def test_conflicting_holder_or_liege_cannot_be_treated_as_outside(self):
        for old, new in (("holder=2", "holder=2 holder=3"),
                         ("de_facto_liege=90", "de_facto_liege=90 de_facto_liege=91")):
            with self.subTest(field=old):
                _, metrics, detail, _ = world(titles=TITLES.replace(old, new))
                self.assertIsNone(detail["county_membership_audit"]["states"][101]["in_player_realm"])
                self.assertIsNone(metrics["Q_realm"]["value"])

    def test_missing_cyclic_or_conflicting_house_path_is_not_zero_or_half_price(self):
        for houses in (
            HOUSES.replace("parent_dynasty_house=174", "parent_dynasty_house=999"),
            HOUSES.replace("parent_dynasty_house=174", "parent_dynasty_house=176") + " 176={dynasty=174 parent_dynasty_house=175}",
            HOUSES.replace("175={dynasty=174 parent_dynasty_house=174}", "175={}"),
            HOUSES.replace("175={dynasty=174", "175={dynasty=200 dynasty=174"),
        ):
            with self.subTest(houses=houses):
                _, metrics, detail, _ = world(houses=houses)
                self.assertEqual(metrics["realm_county_count"]["value"], "2")
                self.assertEqual(D(metrics["Q_realm"]["value"]), D(2))
                self.assertIsNone(metrics["K_dynasty"]["value"])
                self.assertEqual(metrics["dynasty_county_count"]["availability"], "unknown")
                self.assertEqual(detail["unresolved_family_county_ids"], [101])

    def test_cached_foreign_house_does_not_hide_parent_dynasty_conflict(self):
        titles = '102={key=c_out holder=3} ' + TITLES.replace(" 102={key=c_out holder=3}", "")
        _, metrics, detail, _ = world(titles=titles, houses=HOUSES.replace("parent_dynasty_house=174", "parent_dynasty_house=200"))
        state = detail["county_membership_audit"]["states"][101]
        self.assertIsNone(state["family_factor"])
        self.assertEqual(state["family_reason"], "parent_dynasty_disagrees")
        self.assertIsNone(metrics["K_dynasty"]["value"])

    def test_complete_lowborn_and_real_other_dynasty_are_known_exclusions(self):
        _, metrics, detail, _ = world(characters='1={dynasty_house=174} 2={} 3={dynasty_house=200}')
        self.assertTrue(detail["county_membership_audit"]["dynasty"]["complete"])
        self.assertEqual(metrics["dynasty_county_count"]["value"], "1")
        self.assertEqual(D(metrics["K_dynasty"]["value"]), D(1))

    def test_unknown_decoder_field_or_missing_title_census_never_yields_exact_zero(self):
        projection, metrics, detail, _ = world(extra="0xDEADBEEF=10")
        self.assertFalse(detail["county_membership_audit"]["title_census_complete"])
        self.assertEqual(metrics["realm_county_count"]["availability"], "unknown")
        self.assertEqual(metrics["dynasty_county_count"]["availability"], "unknown")
        self.assertIsNone(metrics["Q_realm"]["value"])
        projection = SaveProjection({1})
        for token in melt_tokens(io.BytesIO(b'living={1={}}')):
            projection.token(token)
        projection.complete()
        metrics, detail, _ = project_metrics(projection, actor=1, founder=1, source_id="synthetic_missing_census")
        self.assertIsNone(detail["realm_county_count"])
        self.assertEqual(metrics["realm_county_count"]["availability"], "unknown")

    def test_incomplete_T0_known_subset_cannot_become_dynasty_outside_cap(self):
        _, _, partial, _ = world(titles=TITLES.replace("de_facto_liege=90", "de_facto_liege=999"))
        context = deepcopy(CONTEXT)
        context["baseline_counties"] = partial["realm_counties"]
        self.assertFalse(context["baseline_counties"][0]["realm_membership_complete"])
        _, metrics, detail, _ = world(context=context)
        self.assertTrue(detail["county_membership_audit"]["realm"]["complete"])
        self.assertEqual(D(metrics["Q_realm"]["value"]), D(2))
        self.assertIsNone(metrics["K_dynasty"]["value"])


if __name__ == "__main__":
    unittest.main()
