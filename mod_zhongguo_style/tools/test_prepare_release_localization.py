#!/usr/bin/env python3
"""Offline tests for the ZhongGuo release-localization orchestrator."""

from __future__ import annotations

import sys
from pathlib import Path
import tempfile
import unittest
from unittest import mock


sys.path.insert(0, str(Path(__file__).resolve().parent))
import prepare_release_localization as release_loc  # noqa: E402


class ReleaseLocalizationTests(unittest.TestCase):
    def test_batches_cover_three_thousand_one_hundred_and_sixty_nine_keys_once(self) -> None:
        batches = release_loc.build_batches()
        self.assertEqual(18, len(batches))
        core = [key for batch in batches if batch.source == "core" for key in batch.keys]
        mechanisms = [
            key for batch in batches if batch.source == "mechanisms" for key in batch.keys
        ]
        self.assertEqual(236, len(core))
        self.assertEqual(2933, len(mechanisms))
        self.assertEqual(len(core), len(set(core)))
        self.assertEqual(len(mechanisms), len(set(mechanisms)))
        self.assertEqual(80, len(batches[0].keys))
        self.assertEqual(80, len(batches[1].keys))
        self.assertEqual(76, len(batches[2].keys))
        self.assertEqual(245, len(batches[3].keys))
        self.assertEqual(88, len(batches[-1].keys))

    def test_merge_raw_yml_appends_only_a_source_order_suffix(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "sample.yml"
            path.write_bytes(b'\xef\xbb\xbfl_french:\n one:0 "Old"\n')
            merged = release_loc.merge_raw_yml(
                path,
                {"one": "Un", "two": "Deux"},
            )
        self.assertEqual(
            b'\xef\xbb\xbfl_french:\n one:0 "Un"\n two:0 "Deux"\n',
            merged,
        )

    def test_merge_raw_yml_rejects_non_prefix_key_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "sample.yml"
            path.write_bytes(b'\xef\xbb\xbfl_french:\n two:0 "Deux"\n')
            with self.assertRaisesRegex(
                release_loc.ReleaseLocalizationError,
                "target yml key/order mismatch",
            ):
                release_loc.merge_raw_yml(
                    path,
                    {"one": "Un", "two": "Deux"},
                )

    def test_raw_yml_decode_is_inverse_of_generator_escaping(self) -> None:
        self.assertEqual("line\\nnext", release_loc.decode_raw_yml_value("line\\\\nnext"))
        self.assertEqual('say "yes"', release_loc.decode_raw_yml_value('say \\"yes\\"'))

    def test_non_chinese_english_copies_are_not_residual_failures(self) -> None:
        self.assertTrue(release_loc.is_translatable_english("Open the next KPI policy"))
        self.assertFalse(release_loc.is_translatable_english("KPI / PIP / HC · 361"))
        source = {"sentence": "Open the policy", "technical": "KPI / 361"}
        self.assertEqual(
            [],
            release_loc.candidate_residuals(source, dict(source)),
        )
        self.assertEqual(
            [],
            release_loc.candidate_residuals(
                {"zg361_scoreboard_col_status": "Status"},
                {"zg361_scoreboard_col_status": "Status"},
                "german",
            ),
        )
        self.assertFalse(release_loc.is_translatable_english("—"))
        self.assertFalse(release_loc.is_translatable_english("3.75 / KPI / HC"))

    def test_malformed_batch_is_bisected_and_reassembled_in_order(self) -> None:
        english = {"one": "One", "two": "Two", "three": "Three"}
        chinese = {"one": "一", "two": "二", "three": "三"}

        def fake_request(language, display, prompt, source, *unused):
            if len(source) > 1:
                raise release_loc.minimax.TranslationError("response is not one strict JSON object")
            return language, {key: f"DE-{value}" for key, value in source.items()}

        with mock.patch.object(
            release_loc.minimax, "request_candidate", side_effect=fake_request
        ):
            result = release_loc.request_with_bisection(
                "german",
                release_loc.SOURCES["core"],
                english,
                chinese,
                "configured-for-test",
                12000,
            )
        self.assertEqual(
            {"one": "DE-One", "two": "DE-Two", "three": "DE-Three"},
            result,
        )

    def test_format_valid_english_copy_does_not_trigger_bisection(self) -> None:
        english = {"one": "First source", "two": "Second source"}
        chinese = {"one": "第一项", "two": "第二项"}
        calls: list[tuple[str, ...]] = []

        def fake_request(language, display, prompt, source, *unused):
            calls.append(tuple(source))
            if len(source) > 1:
                return language, {
                    "one": "Erste Quelle",
                    "two": source["two"],
                }
            return language, {
                key: f"DE-{value}" for key, value in source.items()
            }

        with mock.patch.object(
            release_loc.minimax, "request_candidate", side_effect=fake_request
        ):
            result = release_loc.request_with_bisection(
                "german",
                release_loc.SOURCES["core"],
                english,
                chinese,
                "configured-for-test",
                12000,
            )
        self.assertEqual(
            {"one": "Erste Quelle", "two": "Second source"}, result
        )
        self.assertEqual([("one", "two")], calls)

    def test_foreign_script_does_not_trigger_non_chinese_content_retries(self) -> None:
        english = {"one": "Translate this policy"}
        chinese = {"one": "翻译这条政策"}
        calls = 0

        def fake_request(language, display, prompt, source, *unused):
            nonlocal calls
            calls += 1
            if calls < 3:
                return language, {"one": "错误中文"}
            return language, {"one": "올바른 정책 번역"}

        with mock.patch.object(
            release_loc.minimax, "request_candidate", side_effect=fake_request
        ):
            result = release_loc.request_with_bisection(
                "korean",
                release_loc.SOURCES["core"],
                english,
                chinese,
                "configured-for-test",
                12000,
            )
        self.assertEqual({"one": "错误中文"}, result)
        self.assertEqual(1, calls)

    def test_single_key_parse_failure_gets_two_bounded_fresh_requests(self) -> None:
        english = {"one": "Translate this policy"}
        chinese = {"one": "翻译这条政策"}
        calls = 0

        def fake_request(language, display, prompt, source, *unused):
            nonlocal calls
            calls += 1
            if calls < 3:
                raise release_loc.minimax.TranslationError(
                    "protected token mismatch for escaped quote"
                )
            return language, {"one": "この方針を翻訳する"}

        with mock.patch.object(
            release_loc.minimax, "request_candidate", side_effect=fake_request
        ):
            result = release_loc.request_with_bisection(
                "japanese",
                release_loc.SOURCES["core"],
                english,
                chinese,
                "configured-for-test",
                12000,
            )
        self.assertEqual({"one": "この方針を翻訳する"}, result)
        self.assertEqual(3, calls)

    def test_key_level_repair_preserves_good_values_and_requests_only_failures(self) -> None:
        batch = release_loc.Batch("core", "test_batch", ("good", "bad", "technical"))
        english = {
            "good": "First source sentence here",
            "bad": "Second source sentence here $GOLD$",
            "technical": "KPI / HC",
        }
        chinese = {
            "good": "第一条源句",
            "bad": "第二条源句",
            "technical": "KPI / HC",
        }
        source_candidate = {
            "good": "Erster Satz ist vollständig übersetzt",
            "bad": "Second source sentence here",
            "technical": english["technical"],
        }
        requested: list[tuple[str, ...]] = []

        def fake_bisection(language, spec, request_english, request_chinese, *unused):
            requested.append(tuple(request_english))
            return {"bad": "Zweiter Satz ist vollständig übersetzt $GOLD$"}

        with mock.patch.object(
            release_loc, "request_with_bisection", side_effect=fake_bisection
        ):
            result, summary = release_loc.repair_one_candidate(
                batch,
                "german",
                release_loc.SOURCES["core"],
                english,
                chinese,
                source_candidate,
                "configured-for-test",
                12000,
            )
        self.assertEqual([("bad",)], requested)
        self.assertEqual(source_candidate["good"], result["good"])
        self.assertEqual(source_candidate["technical"], result["technical"])
        self.assertEqual("Zweiter Satz ist vollständig übersetzt $GOLD$", result["bad"])
        self.assertEqual(["good", "technical"], summary["preserved_keys"])
        self.assertEqual(["bad"], summary["requested_keys"])

    def test_revision_loader_defers_token_failures_to_key_level_classification(self) -> None:
        english = {
            "good": "Keep this policy readable",
            "bad": "Translate without quotation marks",
        }
        chinese = {
            "good": "保持这条政策清晰",
            "bad": "翻译时不要添加引号",
        }
        payload = {
            "good": "Diese Richtlinie bleibt verständlich",
            "bad": 'Ohne zusätzliche "Anführungszeichen" übersetzen',
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "candidate.json"
            path.write_text(
                release_loc.json.dumps(payload, ensure_ascii=False), encoding="utf-8"
            )
            with self.assertRaises(release_loc.minimax.TranslationError):
                release_loc.load_candidate(path, english)
            candidate = release_loc.load_candidate_payload(path, english)

        preserved, requested, reset = release_loc.classify_repair_candidate(
            english, chinese, candidate, "german"
        )
        self.assertEqual({"good": payload["good"]}, preserved)
        self.assertEqual(["bad"], list(requested))
        self.assertIn("unescaped ASCII quote count", requested["bad"][0])
        self.assertEqual([], reset)

    def test_source_migration_preserves_unchanged_values_and_requests_only_delta_or_red(self) -> None:
        previous_english = {
            "good": "First policy source sentence",
            "changed": "Old policy source sentence",
            "bad": "Second policy source sentence",
            "technical": "KPI / HC",
        }
        previous_chinese = {
            "good": "第一条政策源句",
            "changed": "旧政策源句",
            "bad": "第二条政策源句",
            "technical": "KPI / HC",
        }
        current_english = dict(previous_english)
        current_english["changed"] = "New policy source sentence"
        current_chinese = dict(previous_chinese)
        current_chinese["changed"] = "新政策源句"
        candidate = {
            "good": "Der erste Richtliniensatz ist vollständig übersetzt",
            "changed": "Der alte Richtliniensatz ist vollständig übersetzt",
            "bad": previous_english["bad"],
            "technical": previous_english["technical"],
        }
        changed = release_loc.source_value_changes(
            previous_english,
            previous_chinese,
            current_english,
            current_chinese,
        )
        preserved, requested, reset = release_loc.classify_migration_candidate(
            previous_english,
            current_english,
            current_chinese,
            candidate,
            "german",
            changed,
        )
        self.assertEqual(
            {
                "changed": [
                    "English source value changed",
                    "Simplified Chinese source value changed",
                ]
            },
            changed,
        )
        self.assertEqual(candidate["good"], preserved["good"])
        self.assertEqual(candidate["technical"], preserved["technical"])
        self.assertEqual(["changed"], list(requested))
        self.assertEqual(candidate["bad"], preserved["bad"])
        self.assertEqual([], reset)

    def test_source_migration_rejects_key_order_or_coverage_changes(self) -> None:
        with self.assertRaisesRegex(
            release_loc.ReleaseLocalizationError, "key coverage or order"
        ):
            release_loc.source_value_changes(
                {"one": "One", "two": "Two"},
                {"one": "一", "two": "二"},
                {"two": "Two", "one": "One"},
                {"one": "一", "two": "二"},
            )

    def test_non_chinese_content_is_outside_format_validation(self) -> None:
        source = {"line": "Open this policy and freeze the roster"}
        chinese = {"line": "开启政策并冻结名册"}
        for language in ("english", *release_loc.LANGUAGES):
            for value in (source["line"], chinese["line"], "Смешанный cohort 俸禄 없는 문자"):
                with self.subTest(language=language, value=value):
                    self.assertEqual([], release_loc.candidate_quality_errors(
                        source, chinese, {"line": value}, language
                    ))
                    self.assertEqual([], release_loc.targeted_quality_errors(
                        "zg361m.14.desc", value, language
                    ))
                    self.assertEqual([], release_loc.candidate_residuals(
                        source, {"line": value}, language
                    ))

    def test_replacement_character_and_literal_newlines_remain_format_errors(self) -> None:
        source = {"line": "Policy"}
        for language in ("english", "simp_chinese", *release_loc.LANGUAGES):
            for value in ("invalid\ufffd", "line\nnext", "line\rnext"):
                with self.subTest(language=language, value=repr(value)):
                    self.assertTrue(release_loc.candidate_quality_errors(
                        source, source, {"line": value}, language
                    ))

    def test_candidate_loader_rejects_missing_key_or_protected_token(self) -> None:
        source = {"line": "Gold: $GOLD$ [ROOT.Char.GetName]", "other": "KPI / 361"}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "candidate.json"
            for payload, message in (
                ({"line": source["line"]}, "key set differs"),
                ({"line": "Gold: [ROOT.Char.GetName]", "other": source["other"]}, "protected-token mismatch"),
                ({"line": source["line"], "other": "361"}, "explicit token"),
            ):
                with self.subTest(message=message):
                    path.write_text(release_loc.json.dumps(payload), encoding="utf-8")
                    with self.assertRaisesRegex(release_loc.minimax.TranslationError, message):
                        release_loc.load_candidate(path, source)
            path.write_text(release_loc.json.dumps(source), encoding="utf-8")
            self.assertEqual(source, release_loc.load_candidate(path, source))

    def test_language_parser_preserves_strict_bom_header_and_syntax_checks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "target.yml"
            for language in ("english", "simp_chinese", *release_loc.LANGUAGES):
                for newline in ("\n", "\r\n"):
                    path.write_bytes((f'l_{language}:{newline} line:0 "English copy"{newline}').encode("utf-8-sig"))
                    self.assertEqual({"line": "English copy"}, release_loc.parse_language_localization(path, language))
            for data, error_type in (
                (b'l_german:\n line:0 "Value"\n', release_loc.minimax.TranslationError),
                ('l_french:\n line:0 "Value"\n'.encode("utf-8-sig"), release_loc.ReleaseLocalizationError),
                (b'\xef\xbb\xbfl_german:\n line:0 "\xff"\n', release_loc.minimax.TranslationError),
                ('l_german:\n line:0 "Value"\n line:0 "Duplicate"\n'.encode("utf-8-sig"), release_loc.minimax.TranslationError),
                ('l_german:\n line:0 Value\n'.encode("utf-8-sig"), release_loc.minimax.TranslationError),
            ):
                path.write_bytes(data)
                with self.assertRaises(error_type):
                    release_loc.parse_language_localization(path, "german")

    def test_format_audit_accepts_english_copies_and_rejects_missing_keys_or_tokens(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            mod = Path(directory)
            english = mod / "localization/english/test_l_english.yml"
            chinese = mod / "localization/simp_chinese/test_l_simp_chinese.yml"
            def write(path, language, line='Gold: $GOLD$', other=True):
                path.parent.mkdir(parents=True, exist_ok=True)
                content = f'l_{language}:\n line:0 "{line}"\n'
                if other:
                    content += ' other:0 "KPI / 361"\n'
                path.write_bytes(content.encode("utf-8-sig"))
            write(english, "english")
            write(chinese, "simp_chinese")
            spec = release_loc.SourceSpec("core", english, chinese, "test")
            targets = {}
            for language in release_loc.LANGUAGES:
                targets[language] = mod / f'localization/{language}/test_l_{language}.yml'
                write(targets[language], language)
            with mock.patch.object(release_loc, "MOD_ROOT", mod), mock.patch.object(
                release_loc, "SOURCES", {"core": spec}
            ), mock.patch("builtins.print"):
                self.assertEqual(0, release_loc.audit())
                write(targets["german"], "german", other=False)
                self.assertEqual(1, release_loc.audit())
                write(targets["german"], "german", line="Gold")
                self.assertEqual(1, release_loc.audit())

    def test_translation_generation_retains_meaning_with_format_only_acceptance(self) -> None:
        source = {"line": "Gold: $GOLD$ KPI / 361"}
        for language in release_loc.LANGUAGES:
            with self.subTest(language=language):
                prompt = release_loc.candidate_request_prompt(source, source, language, "CK3 context")
                self.assertIn("format-only release checks", prompt)
                self.assertIn("Only Simplified Chinese has real-game acceptance", prompt)
                self.assertIn("$GOLD$", prompt)
                self.assertIn("flat JSON object", prompt)
                self.assertIn("You only translate localization strings", prompt)
                self.assertIn("Preserve meaning, tone", prompt)
                self.assertIn("CK3 context", prompt)
                self.assertNotIn("CRITICAL EXACT-KEY REQUIREMENTS", prompt)
                self.assertNotIn("refunds the three immediate charges", prompt)
                self.assertNotIn("stop the salary reduction", prompt)
                self.assertEqual(" " + release_loc.FORMAT_CONTEXT, release_loc.request_key_context(source, language))
                self.assertEqual(release_loc.FORMAT_CONTEXT, release_loc.LANGUAGE_PROMPT_SUFFIX[language])

    def test_chinese_fourfold_settlement_keeps_exact_number_semantics(self) -> None:
        incomplete = "地方国库-50，个人金钱-25，俸禄-25%。"
        complete = "地方国库-50，个人金钱-25，贤能-60，俸禄-25%，持续一年。"
        for key in ("zg361_grade_325_desc", "zg361.4.desc", "zg361m.18.desc"):
            with self.subTest(key=key):
                self.assertTrue(release_loc.targeted_quality_errors(key, incomplete, "simp_chinese"))
                self.assertEqual([], release_loc.targeted_quality_errors(key, complete, "simp_chinese"))

    def test_chinese_appeal_and_reward_matrix_semantics_remain_checked(self) -> None:
        for key, incomplete, complete in (
            ("zg361m.14.desc", "申诉获准后校准结果。", "退还3.25即时扣款并停止尚未结束的25%俸禄扣减。"),
            ("zg361m.21.desc", "奖励3.75官员。", "3.75获得奖励，3.5保持不变，3.25执行四重问责。"),
        ):
            with self.subTest(key=key):
                self.assertTrue(release_loc.targeted_quality_errors(key, incomplete, "simp_chinese"))
                self.assertEqual([], release_loc.targeted_quality_errors(key, complete, "simp_chinese"))
                self.assertTrue(release_loc.candidate_quality_errors({key: "Source"}, {key: complete}, {key: incomplete}, "simp_chinese"))
        self.assertIn("refunds", release_loc.request_key_context({"zg361m.14.desc": "Source"}, "simp_chinese"))

    def test_release_audit_payload_tracks_four_sources_and_fourteen_targets(self) -> None:
        sources = [
            path
            for spec in release_loc.SOURCES.values()
            for path in (spec.english, spec.chinese)
        ]
        targets = [
            release_loc.MOD_ROOT
            / "localization"
            / language
            / spec.english.name.replace("_english.yml", f"_{language}.yml")
            for language in release_loc.LANGUAGES
            for spec in release_loc.SOURCES.values()
        ]
        payload = release_loc.release_audit_payload(sources, targets)
        self.assertEqual(1, payload["format_version"])
        self.assertEqual("mod_zhongguo_style", payload["product_id"])
        self.assertEqual("GREEN", payload["result"])
        self.assertEqual(list(release_loc.AUDIT_CHECKS), payload["checks"])
        self.assertEqual(4, len(payload["source_files"]))
        self.assertEqual(14, len(payload["target_files"]))
        for record in payload["source_files"] + payload["target_files"]:
            self.assertRegex(record["sha256"], r"^[0-9a-f]{64}$")
            self.assertGreater(record["size"], 0)
            self.assertTrue(record["path"].startswith("mod_zhongguo_style/"))

    def test_chinese_review_copy_matches_same_year_mechanics_and_other_languages_parse(self) -> None:
        guard = "NOT = { var:zg361_last_settled_year = current_year }"
        decisions = (
            release_loc.MOD_ROOT / "common" / "decisions" / "zg361_decisions.txt"
        ).read_text(encoding="utf-8-sig")
        triggers = (
            release_loc.MOD_ROOT
            / "common"
            / "scripted_triggers"
            / "zg361_triggers.txt"
        ).read_text(encoding="utf-8-sig")
        effects = "\n".join(
            path.read_text(encoding="utf-8-sig")
            for path in sorted(
                (release_loc.MOD_ROOT / "common" / "scripted_effects").glob(
                    "zg361_core_*_effects.txt"
                )
            )
        )
        # The authoritative validity path delegates to the shared business
        # trigger.  The display-only path stays unconditional because rendering
        # the same-year variable comparison exposes CK3's internal
        # `character_var_equal` key to the player.
        decision = " ".join(
            decisions.partition("zg361_review_now_decision = {")[2]
            .partition("\n}")[0].split()
        )
        business_trigger = " ".join(
            triggers.partition("zg361_review_now_business_valid_trigger = {")[2]
            .partition("\n}")[0].split()
        )
        self.assertIn(
            "is_valid = { zg361_review_now_business_valid_trigger = yes }",
            decision,
        )
        self.assertIn(
            "is_valid_showing_failures_only = { always = yes }",
            decision,
        )
        self.assertEqual(
            decision.count("zg361_review_now_business_valid_trigger = yes"), 1
        )
        self.assertNotIn("custom_description", decision)
        self.assertIn(
            "trigger_if = { limit = { has_variable = zg361_last_settled_year } "
            + guard + " }",
            business_trigger,
        )
        self.assertIn(guard, effects)

        description = "不等下一次京察召集，考功司现在便会冻结直属官员名册，开启本年的考绩程序。本决议只开启与京察共用的考核流程，不举办“京察大计”，也不视为完成京察履责。自评、互评、校准与公示会在后续阶段依次推进，通常约三百三十日后出榜。每次发起至少间隔一年，且同一自然年最多结算一次。"
        tooltip = "提前开启考核季并冻结至少一名直属在任官员；不举办京察，也不视为完成京察履责。"
        for language in ("simp_chinese", "english", *release_loc.LANGUAGES):
            with self.subTest(language=language):
                path = release_loc.MOD_ROOT / "localization" / language / f"zg361_l_{language}.yml"
                values = release_loc.parse_language_localization(path, language)
                for key in ("zg361_review_now_decision_desc", "zg361_review_now_decision_tooltip", "zg361_review_now_decision", "zg361_review_now_decision_confirm"):
                    self.assertIn(key, values)
                self.assertNotIn("zg361_review_ready_tt", values)
                self.assertNotIn("zg361_review_now_decision_valid_desc", values)
                if language == "simp_chinese":
                    self.assertEqual(description, values["zg361_review_now_decision_desc"])
                    self.assertEqual(tooltip, values["zg361_review_now_decision_tooltip"])
                    self.assertEqual("提前启动本年度考核", values["zg361_review_now_decision"])
                    self.assertEqual("提前开考", values["zg361_review_now_decision_confirm"])


if __name__ == "__main__":
    unittest.main()
