from decimal import Decimal as D
import io
import unittest

from xar_autoplayer.campaign_development_score_v1 import (
    Interval, R, aggregate_state, build_report, interval_text, quality_power, score_360, state_intervals, UNITS,
)
from xar_autoplayer.campaign_score_save_reader import SaveProjection, melt_tokens


def metrics(**values):
    return {key: {"value": str(value), "unit": UNITS[key], "availability": "observed"}
            for key, value in values.items()}


class CampaignScoreTests(unittest.TestCase):
    def test_missing_baseline_is_interval_and_no_weight_redistribution(self):
        current = metrics(Q_realm=5, legacy_ranks=0, control_average=1, rebel_share=0)
        scores = state_intervals(current, {})
        self.assertEqual(scores["L"].lower, 0)
        self.assertLess(scores["L"].upper, 100)
        self.assertEqual(scores["U"], Interval.exact(100))
        self.assertEqual(scores["D"].upper, 80)
        a = aggregate_state(scores)
        self.assertEqual(a.lower, 10)  # only U is known, still its original 10%.

    def test_quality_uses_current_men_and_rejects_duplicate_regiments(self):
        rows = [{"regiment_id": 1, "current_available_men": "1000",
                 "effective_damage": "40", "effective_toughness": "40",
                 "stats_source_bound": True, "force_kind": "permanent_maa"}]
        self.assertEqual(quality_power(rows, damage_ref="10", toughness_ref="10"), 4000)
        with self.assertRaises(ValueError):
            quality_power(rows + rows, damage_ref="10", toughness_ref="10")

    def test_debt_rescue_and_lost_half_reproduce_design(self):
        baseline = metrics(Q_realm=10, K_dynasty=10, legacy_ranks=0, gross_income=20,
                           u_discretionary=10, P_quality=1000)
        common = dict(control_average=1, rebel_share=0, legacy_ranks=0,
                      continuation_legal=1, backup_heirs=2)
        borrow = metrics(**common, Q_realm=10, K_dynasty=10, P_quality=1000,
                         gross_income=20, total_expenses=25, military_current=15,
                         military_all_raised=15, gold=120, due_commitments=240)
        lost = metrics(**common, Q_realm=5, K_dynasty=5, P_quality=500,
                       gross_income=10, total_expenses=5, military_current=0,
                       military_all_raised=5, gold=0, due_commitments=0)
        b = aggregate_state(state_intervals(borrow, baseline))
        l = aggregate_state(state_intervals(lost, baseline))
        self.assertEqual(b.lower, D("51.725"))
        self.assertGreater(b.lower, l.upper)
        sb = score_360([Interval.exact(60)] * 359 + [b], b)
        sl = score_360([Interval.exact(60)] * 359 + [l], l)
        self.assertEqual(sb.lower.quantize(D(".01")), D("563.04"))
        self.assertEqual(sl.lower.quantize(D(".01")), D("535.98"))

    def test_gameover_denominator_and_incomplete_interval(self):
        stopped = score_360([Interval.exact(70)] * 180 + [Interval.exact(0)] * 180,
                            Interval.exact(0))
        self.assertEqual(stopped, Interval.exact(70))
        partial = score_360([Interval.exact(70)] * 180 + [Interval(D(0), D(100))] * 180,
                            Interval(D(0), D(100)))
        self.assertEqual(partial, Interval(D(70), D(940)))
        with self.assertRaises(ValueError):
            score_360([Interval.exact(70)] * 180, Interval.exact(70))

    def test_streaming_compact_blocks_cross_chunk_quotes_comments(self):
        class Chunks(io.BytesIO):
            def read(self, n=-1):
                return super().read(min(n, 7))
        source = b'SAV010\ndate=1096.9.23\nliving={1={first_name="A = B" dynasty_house=7 alive_data={gold={value=12.34}}}}\n# { ignored\nlanded_titles={landed_titles={2={key="c_x" holder=1}}}\n'
        p = SaveProjection({1})
        for token in melt_tokens(Chunks(source), p):
            p.token(token)
        p.complete()
        self.assertEqual(p.characters[1]["alive_data.gold.value"], "12.34")
        self.assertEqual(p.titles[2]["key"], "c_x")
        self.assertEqual(p.metadata["date"], "1096.9.23")

    def test_exported_repeating_decimals_have_exact_weighted_sum(self):
        from fractions import Fraction
        report = build_report(metrics(Q_realm=1), metrics(Q_realm=2), snapshot={},
                              sources=[], facts=[], machine_id="synthetic-fixture",
                              observed_at_utc="synthetic", unknown_fields=[])
        for side in ("lower", "upper"):
            exact = sum(Fraction(row[side]) * Fraction(str(row["weight"]))
                        for row in report["scores"].values())
            self.assertEqual(Fraction(report["aggregate"]["A_state"][side]), exact)
        self.assertIsNone(report["aggregate"]["S30"]["value"])

    def test_interval_display_outwards_and_partial_contribution_not_reweighted(self):
        self.assertEqual(interval_text("7.908", "25.561"), "7.90–25.57")
        b = metrics(Q_realm=10, control_average=1, rebel_share=0, K_dynasty=10, legacy_ranks=0)
        r = build_report(b, b, snapshot={}, sources=[], facts=[], machine_id="fixture",
                         observed_at_utc="synthetic", unknown_fields=[])
        self.assertEqual(r["aggregate"]["known_domains"], ["L", "U", "D"])
        self.assertEqual(r["aggregate"]["known_domains_coverage_weight"], "0.5")
        self.assertEqual(r["aggregate"]["known_domains_baseline_contribution"], "28.5")
        self.assertEqual(r["aggregate"]["known_domains_delta_contribution"], "0")

    def test_one_scan_keeps_canonical_perk_and_war_role(self):
        source = b'living={3={dynasty_house=174 alive_data={income=2}}} dynasties={dynasties={174={perk={blood_legacy_1 blood_legacy_2}}}} wars={active_wars={9={casus_belli={attacker=3 defender=7 type=refused_liege_demand_war}}}}'
        p = SaveProjection({3})
        for token in melt_tokens(io.BytesIO(source)):
            p.token(token)
        p.complete()
        self.assertEqual(p.characters[3]["alive_data.income"], "2")
        self.assertEqual(p.dynasties[174]["perk"].split(), ["blood_legacy_1", "blood_legacy_2"])
        self.assertEqual(p.wars[9]["casus_belli.defender"], "7")

    def test_explicit_static_map_and_targeted_record_selection(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from xar_autoplayer.campaign_score_save_reader import landed_title_map
        from xar_autoplayer.campaign_score_target_projection import TargetProjection
        with TemporaryDirectory(prefix="ck3-score-fixture-") as temp:
            path = Path(temp) / "titles.txt"
            path.write_text('k_x={d_x={c_x={b_x={province=12} b_y={province=13}}}}', encoding="utf-8")
            mapping = landed_title_map([path], machine_id="synthetic-fixture")
            self.assertEqual(mapping["county_baronies"], {"c_x": {"b_x": 12, "b_y": 13}})
        p = TargetProjection(characters={3}, provinces={12}, dynasty=174, war_characters={3})
        data = b'provinces={12={holding={type=castle_holding}} 13={occupant=99}} dynasties={dynasties={174={perk={blood_1 blood_2}}}} wars={active_wars={9={casus_belli={attacker=3 defender=7}} 10={casus_belli={attacker=98 defender=99}}}}'
        for token in melt_tokens(io.BytesIO(data)):
            p.token(token)
        p.complete()
        self.assertEqual(set(p.records), {"province:12", "dynasty:174", "war:9"})
        self.assertEqual([r["value"] for r in p.records["dynasty:174"]["fields"]], ["blood_1", "blood_2"])

    def test_complete_explanations_negative_cash_and_strict_date(self):
        b = metrics(Q_realm=".5", K_dynasty=1, legacy_ranks=0, gross_income=10,
                    total_expenses=3, military_current=0, military_all_raised=0,
                    gold=10, due_commitments=0, P_quality=100,
                    continuation_legal=1, backup_heirs=2)
        c = {**b, **metrics(Q_realm=".25", gold=5)}
        def report(date, strict=False):
            return build_report(c, b, snapshot={"T0": "1066.9.15", "date": date},
                sources=[], facts=[], machine_id="synthetic", observed_at_utc="synthetic",
                unknown_fields=[], strict_endpoint_verified=strict)
        r = report("1096.9.15", True)
        text = {row["id"]: row["explanation_zh"] for row in r["display_steps"]}
        for key in ["E", "M", "H"]:
            self.assertTrue(r["scores"][key]["known"])
            self.assertNotIn("缺", text[key])
        self.assertIn("max(开局,1)", text["L"])
        self.assertEqual(r["scores"]["L"]["value"], "20")
        self.assertIn("变化-5", r["facts"][0]["value_text"])
        self.assertIsNotNone(r["aggregate"]["A_end"])
        self.assertIsNone(report("1096.9.23")["aggregate"]["A_end"])
        with self.assertRaises(ValueError):
            report("1096.9.23", True)

    def test_cli_admission_current_machine_expiry_and_cumulative_cap(self):
        import importlib.util
        from datetime import datetime, timezone
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        path = Path(__file__).resolve().parents[2] / "tools" / "score_ck3_campaign.py"
        spec = importlib.util.spec_from_file_location("score_cli_fixture", path)
        cli = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cli)
        with TemporaryDirectory(prefix="ck3-score-card-fixture-") as temp:
            root = Path(temp)
            card = {"schema": "xar.first30.scoring-metadata-staging-capacity-admission/v1",
                "owner": "/root", "status": "ADMITTED", "machine_id": "synthetic",
                "scoring_metadata_staging_admitted": True, "allowed_output_root": temp,
                "at_utc": "2000-01-01T00:00:00+00:00", "review_at_utc": "2100-01-01T00:00:00+00:00",
                "maximum_logical_output_bytes": 1024, "allowed_extensions": [".json"]}
            with patch.object(cli, "current_machine_id", return_value="synthetic"):
                cli.write_new(root / "first.json", {"ok": True}, admission=card, machine_id="synthetic")
                used = (root / "first.json").stat().st_size
                self.assertEqual(cli.validate_admission(card, root, "synthetic")[1], used)
                with self.assertRaises(ValueError):
                    cli.validate_admission(card, root, "other-machine")
                with self.assertRaises(ValueError):
                    cli.validate_admission(card, root, "synthetic", now=datetime(2101, 1, 1, tzinfo=timezone.utc))
                for change in [{"owner": "other"}, {"schema": "other"}, {"maximum_logical_output_bytes": used - 1}]:
                    with self.assertRaises(ValueError):
                        cli.validate_admission({**card, **change}, root, "synthetic")
                with self.assertRaises(ValueError):
                    cli.write_new(root / "over.json", {"more": "x" * 100},
                        admission={**card, "maximum_logical_output_bytes": used + 1}, machine_id="synthetic")
                self.assertFalse((root / "over.json").exists())

    def test_cli_main_single_projection_scan_auto_map_and_export(self):
        import contextlib
        import importlib.util
        import json
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        path = Path(__file__).resolve().parents[2] / "tools" / "score_ck3_campaign.py"
        spec = importlib.util.spec_from_file_location("score_cli_end_to_end", path)
        cli = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cli)
        def world(actor, date, perks, gold):
            source = (f'date={date} living={{{actor}={{dynasty_house=174 alive_data={{gold={{value={gold}}}}}}} '
                '7={dynasty_house=174}} ' + ('dead_unprunable={1={dynasty_house=174}} ' if actor != 1 else '') +
                'provinces={12={holding={type=castle_holding}} 13={holding={type=castle_holding}}} '
                f'landed_titles={{landed_titles={{90={{key=d_x holder=7}} 100={{key=c_a holder={actor}}} '
                f'101={{key=c_b holder=7 de_facto_liege={90 if actor == 3 else 100}}}}}}} '
                'county_manager={counties={c_a={development=0 control=100} c_b={development=0 control=100}}} wars={active_wars={}} '
                f'dynasties={{dynasty_house={{174={{dynasty=174 found_date=980.1.1}}}} dynasties={{174={{{perks}}}}}}}')
            if actor == 3:
                source = source.replace('alive_data={', 'landed_data={wars={9}} alive_data={', 1)
                source = source.replace('wars={active_wars={}}', 'wars={active_wars={9={casus_belli={attacker=3 defender=7}} 10={}}}')
            p = SaveProjection({1, actor})
            for token in melt_tokens(io.BytesIO(source.encode())):
                p.token(token)
            p.complete()
            return p
        with TemporaryDirectory(prefix="ck3-score-main-fixture-") as temp:
            root = Path(temp)
            out = root / "output"
            permanent = root / "permanent.json"
            seed = root / "seed.json"
            card_path = root / "card.json"
            titles = root / "titles.txt"
            permanent.write_text(json.dumps({"machine_id": "synthetic", "independent_SAVE":
                {"path": str(root / "current.ck3"), "sha256": "synthetic"},
                "locked_copy_evidence": {"target_identity_after": {"bytes": 1}}}))
            seed.write_text(json.dumps({"episode_seed": {"path": str(root / "seed.ck3"), "size": 1}}))
            card_path.write_text(json.dumps({"schema": "xar.first30.scoring-metadata-staging-capacity-admission/v1",
                "owner": "/root", "status": "ADMITTED", "machine_id": "synthetic",
                "scoring_metadata_staging_admitted": True, "allowed_output_root": str(out),
                "at_utc": "2000-01-01T00:00:00+00:00", "review_at_utc": "2100-01-01T00:00:00+00:00",
                "maximum_logical_output_bytes": 1024*1024, "allowed_extensions": [".json"]}))
            titles.write_text('d_x={c_a={b_a={province=12}} c_b={b_b={province=13}}}')
            argv = [str(path), "--permanent-receipt", str(permanent), "--baseline-save", str(root / "seed.ck3"),
                "--baseline-receipt", str(seed), "--decoder", str(root / "unused.exe"), "--output", str(out),
                "--metadata-admission", str(card_path), "--machine-id", "synthetic", "--actor", "3", "--founder", "1",
                "--landed-titles-source", str(titles), "--attempt-id", "07"]
            worlds = [(world(3, "1096.9.23", "perk={blood_1 blood_2}", 50), {}),
                      (world(1, "1066.9.15", "", 100), {})]
            with patch.object(cli, "current_machine_id", return_value="synthetic"), patch.object(cli, "lower_priority"), \
                 patch.object(cli.reader, "melt_projection", side_effect=worlds) as melt, \
                 patch.object(cli.sys, "argv", argv), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(cli.main(), 0)
                self.assertEqual(melt.call_count, 2)  # Exactly one stream per source.
            report = json.loads((out / "score-result-07.json").read_text(encoding="utf-8"))
            self.assertTrue((out / "projection-summary-07.json").exists())
            self.assertTrue((out / "static-title-map-07.json").exists())
            self.assertEqual(report["aggregate"]["known_domains"], ["L", "U", "D"])
            self.assertEqual(report["raw_metrics"]["legacy_ranks"]["value"], "2")
            self.assertEqual(D(report["scores"]["L"]["value"]).quantize(D(".000001")), D("33.333333"))
            self.assertEqual(report["scores"]["U"]["value"], "100")
            self.assertEqual(report["scoring_detail"]["player_war_scope"]["method"], "player_landed_war_list")
            self.assertEqual(D(report["scores"]["D"]["value"]).quantize(D(".000001")), D("47.619048"))
            self.assertEqual(report["aggregate"]["known_domains_baseline_contribution"], "28.5")

    def test_conflicting_scalars_stay_unknown_and_field_cap_rejects(self):
        from xar_autoplayer.campaign_score_save_reader import project_metrics
        source = b'living={1={dynasty_house=174 alive_data={gold=1 gold=2 gold=3}}} landed_titles={100={key=c_x holder=1} 101={key=b_x holder=1}} county_manager={c_x={development=10 control=100}} provinces={12={holding={type=castle_holding} occupant=98 occupant=99}}'
        p = SaveProjection({1})
        for token in melt_tokens(io.BytesIO(source)):
            p.token(token)
        p.complete()
        self.assertNotIn("alive_data.gold", p.characters[1])
        m, _, _ = project_metrics(p, actor=1, founder=1, source_id="synthetic",
            static_context={"county_baronies": {"c_x": {"b_x": 12}}})
        self.assertEqual(m["gold"]["availability"], "unknown")
        self.assertEqual(m["Q_realm"]["availability"], "bounded")
        excessive = 'provinces={12={holding={type=castle_holding} ' + ' '.join(f'x{i}=1' for i in range(479)) + ' occupant=99}}'
        with self.assertRaisesRegex(ValueError, "scalar cap"):
            p = SaveProjection(set())
            for token in melt_tokens(io.BytesIO(excessive.encode())):
                p.token(token)

    def test_duplicate_entities_and_empty_target_record_cap(self):
        from xar_autoplayer.campaign_score_target_projection import TargetProjection
        source = b'living={1={dynasty_house=174 alive_data={gold=10}} 1={dynasty_house=174 alive_data={gold=20}} 1={dynasty_house=174 alive_data={gold=30}}}'
        p = SaveProjection({1})
        for token in melt_tokens(io.BytesIO(source)):
            p.token(token)
        p.complete()
        self.assertEqual(p.wanted_character_unknown, {1})
        self.assertNotIn(1, p.characters)
        self.assertNotIn(1, p.character_houses)
        from xar_autoplayer.campaign_score_save_reader import project_metrics
        self.assertEqual(project_metrics(p, actor=1, founder=1, source_id="synthetic")[0]["gold"]["availability"], "unknown")
        p = TargetProjection(characters={1}, provinces=set(), dynasty=174, war_characters={1})
        with self.assertRaisesRegex(ValueError, "duplicate"):
            for token in melt_tokens(io.BytesIO(source)):
                p.token(token)
        p = TargetProjection(characters=set(), provinces=set(), dynasty=174, war_characters={1})
        source = 'active_wars={' + ' '.join(f'{i}={{}}' for i in range(2049)) + '}'
        with self.assertRaisesRegex(ValueError, "count cap"):
            for token in melt_tokens(io.BytesIO(source.encode())):
                p.token(token)

    def test_root_active_wars_cannot_be_misread_as_no_rebellion(self):
        from xar_autoplayer.campaign_score_target_projection import TargetProjection, enrich_metrics
        from xar_autoplayer.campaign_score_save_reader import observation
        p = TargetProjection(characters={1}, provinces=set(), dynasty=174, war_characters={1})
        for token in melt_tokens(io.BytesIO(b'active_wars={9={casus_belli={attacker=2 defender=1}}}')):
            p.token(token)
        p.complete()
        self.assertIn("war:9", p.records)
        m = {k: observation(k, None, "synthetic", None) for k in ["Q_realm", "rebel_share"]}
        enrich_metrics(m, {"realm_counties": [], "dynasty_anchor_id": 174}, p.summary(), {}, actor=1, source_ref="synthetic")
        self.assertEqual(m["rebel_share"]["availability"], "unknown")

    def test_crlf_comment_and_utf8_across_one_two_seventeen_byte_chunks(self):
        source = ('# ignored {\r\ndate=1096.9.23 living={1={first_name="汉字" alive_data={gold={value=2}}}}').encode()
        for width in [1, 2, 17]:
            class Chunks(io.BytesIO):
                def read(self, n=-1):
                    return super().read(min(n, width))
            p = SaveProjection({1})
            for token in melt_tokens(Chunks(source)):
                p.token(token)
            p.complete()
            self.assertEqual(p.characters[1]["first_name"], "汉字")
            self.assertEqual(p.characters[1]["alive_data.gold.value"], "2")

    def test_historical_duplicate_house_merge_conflict_and_fixed_T0_anchor(self):
        from xar_autoplayer.campaign_score_save_reader import project_metrics
        context = {"county_baronies": {"c_x": {"b_x": 12}},
                   "baseline_counties": [{"development": "0", "control": "100"}],
                   "founding_house_id": 174, "founding_dynasty_id": 174, "founding_anchor_source": "baseline_save"}
        def read(houses, founder_duplicate=False):
            records = ' '.join(f'7={{dynasty_house={house}}}' if house is not None else '7={}' for house in houses)
            source = ('living={1={dynasty_house=174} 3={dynasty_house=174 alive_data={gold=50}}} '
                'dead_unprunable={' + records + (' 1={dynasty_house=175}' if founder_duplicate else '') + '} '
                'landed_titles={90={key=d_x holder=3} 100={key=c_x holder=7 de_facto_liege=90}} '
                'county_manager={c_x={development=0 control=100}} provinces={12={holding={type=castle_holding}}} '
                'dynasties={dynasty_house={174={dynasty=174} 175={dynasty=175}} dynasties={174={}}} wars={active_wars={}}')
            p = SaveProjection({1, 3})
            for token in melt_tokens(io.BytesIO(source.encode())):
                p.token(token)
            p.complete()
            metrics, detail, _ = project_metrics(p, actor=3, founder=1, source_id="current_save", static_context=context)
            return p, metrics, detail
        p, m, detail = read([174, 174, 174])
        self.assertEqual(p.character_houses[7], 174)
        self.assertEqual(p.character_duplicate_audit["identical_house_merged"], 2)
        self.assertEqual(D(m["K_dynasty"]["value"]), 1)
        p, m, detail = read([None, None])
        self.assertEqual(p.character_duplicate_audit["identical_house_merged"], 1)
        self.assertEqual(D(m["K_dynasty"]["value"]), 0)
        p, m, detail = read([174, 175, 174])
        self.assertIn(7, p.character_house_unknown)
        self.assertNotIn(7, p.character_houses)
        self.assertEqual(m["K_dynasty"]["availability"], "unknown")
        self.assertEqual(m["dynasty_county_count"]["availability"], "unknown")
        self.assertEqual(detail["unresolved_family_county_ids"], [100])
        self.assertEqual(D(m["Q_realm"]["value"]), 1)  # Title chain remains independent.
        p, m, detail = read([174], founder_duplicate=True)
        self.assertIn(1, p.wanted_character_unknown)
        self.assertEqual(detail["founder_house_id"], 174)
        self.assertEqual(m["house_anchor_id"]["source_ref"], "baseline_save")
        self.assertEqual(D(m["K_dynasty"]["value"]), 1)

    def test_explicit_player_wars_ignore_unrelated_shells_but_not_missing_or_conflicts(self):
        from xar_autoplayer.campaign_score_save_reader import player_war_defence
        fields = {"landed_data.wars": " 9", "alive_data.wars": " 1 0 0 0"}
        wars = {9: {"casus_belli.defender": "7"}, 10: {}}
        self.assertEqual(player_war_defence(fields, wars, actor=3)[0], False)
        self.assertEqual(player_war_defence(fields, {9: {"casus_belli.defender": "3"}}, actor=3)[0], True)
        cases = [({}, wars), ({"alive_data.wars": "1 0 0 0"}, wars),
            ({"landed_data.wars": "9 11"}, wars), ({"landed_data.wars": "9 9"}, wars),
            ({"landed_data.wars": ""}, wars), ({"landed_data.wars": "9", "incomplete:landed_data.wars": "true"}, wars),
            ({"landed_data.wars": "9", "nonunique:landed_data.wars": "true"}, wars),
            (fields, {9: {"casus_belli.defender": "7", "nonunique:casus_belli.defender": "true"}}),
            (fields, {9: {}})]
        for row, table in cases:
            self.assertIsNone(player_war_defence(row, table, actor=3)[0])
        from xar_autoplayer.campaign_score_save_reader import project_metrics
        for war in [{"casus_belli.defender": "invalid"}, {"casus_belli.defender": "7", "nonunique:casus_belli.defender": "true"}]:
            p = SaveProjection({3})
            p.war_containers.add(("wars", "active_wars"))
            p.wars[9] = war
            m, _, _ = project_metrics(p, actor=3, founder=3, source_id="synthetic")
            self.assertEqual(m["rebel_share"]["availability"], "unknown")
        for body, expected in [(b'wars={}', False), (b'wars={} wars={}', None)]:
            p = SaveProjection({3})
            for token in melt_tokens(io.BytesIO(b'living={3={landed_data={' + body + b'}}}')):
                p.token(token)
            p.complete()
            self.assertIs(player_war_defence(p.characters[3], {}, actor=3)[0], expected)


if __name__ == "__main__":
    unittest.main()
