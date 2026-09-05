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
    def test_batches_cover_two_thousand_and_ninety_one_keys_once(self) -> None:
        batches = release_loc.build_batches()
        self.assertEqual(19, len(batches))
        core = [key for batch in batches if batch.source == "core" for key in batch.keys]
        mechanisms = [
            key for batch in batches if batch.source == "mechanisms" for key in batch.keys
        ]
        self.assertEqual(243, len(core))
        self.assertEqual(1848, len(mechanisms))
        self.assertEqual(len(core), len(set(core)))
        self.assertEqual(len(mechanisms), len(set(mechanisms)))
        self.assertEqual(80, len(batches[2].keys))
        self.assertEqual(3, len(batches[3].keys))
        self.assertEqual(168, len(batches[4].keys))
        self.assertEqual(55, len(batches[-1].keys))

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

    def test_only_real_english_sentences_count_as_residuals(self) -> None:
        self.assertTrue(release_loc.is_translatable_english("Open the next KPI policy"))
        self.assertFalse(release_loc.is_translatable_english("KPI / PIP / HC · 361"))
        source = {"sentence": "Open the policy", "technical": "KPI / 361"}
        self.assertEqual(
            ["sentence"],
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

    def test_untranslated_value_is_bisected_instead_of_discarding_batch(self) -> None:
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
            {"one": "DE-First source", "two": "DE-Second source"}, result
        )
        self.assertEqual([("one", "two"), ("one",), ("two",)], calls)

    def test_single_key_quality_failure_gets_two_bounded_fresh_requests(self) -> None:
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
        self.assertEqual({"one": "올바른 정책 번역"}, result)
        self.assertEqual(3, calls)

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
            "bad": "Second source sentence here",
            "technical": "KPI / HC",
        }
        chinese = {
            "good": "第一条源句",
            "bad": "第二条源句",
            "technical": "KPI / HC",
        }
        source_candidate = {
            "good": "Erster Satz ist vollständig übersetzt",
            "bad": english["bad"],
            "technical": english["technical"],
        }
        requested: list[tuple[str, ...]] = []

        def fake_bisection(language, spec, request_english, request_chinese, *unused):
            requested.append(tuple(request_english))
            return {"bad": "Zweiter Satz ist vollständig übersetzt"}

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
        self.assertEqual("Zweiter Satz ist vollständig übersetzt", result["bad"])
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
        self.assertEqual(["changed", "bad"], list(requested))
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

    def test_japanese_quality_gate_rejects_chinese_copy_and_simplified_glyphs(self) -> None:
        english = {"line": "Conduct the performance review with evidence."}
        chinese = {"line": "用证据开展绩效考核。"}
        self.assertEqual(
            [],
            release_loc.candidate_quality_errors(
                english,
                chinese,
                {"line": "証拠に基づいて人事評価を実施する。"},
                "japanese",
            ),
        )
        copied = release_loc.candidate_quality_errors(
            english, chinese, dict(chinese), "japanese"
        )
        self.assertTrue(any("copied Simplified Chinese" in error for error in copied))
        self.assertTrue(any("Simplified Chinese glyphs" in error for error in copied))

    def test_japanese_review_gate_rejects_known_mixed_fragments_only(self) -> None:
        english = {"zg361m.227.b": "Give the founder most platform credit"}
        chinese = {"zg361m.227.b": "把平台成功主要记给创始人"}
        errors = release_loc.candidate_quality_errors(
            english,
            chinese,
            {"zg361m.227.b": "創始者 one に功績を与える"},
            "japanese",
        )
        self.assertTrue(any("stray Latin fragment" in error for error in errors))
        errors = release_loc.candidate_quality_errors(
            english,
            chinese,
            {"zg361m.227.b": "取舍と抽查を流程に残す"},
            "japanese",
        )
        self.assertTrue(any("Simplified Chinese glyphs" in error for error in errors))
        self.assertTrue(any("non-idiomatic Chinese" in error for error in errors))
        self.assertTrue(
            set("据占填雇剥携").isdisjoint(release_loc.JAPANESE_SIMPLIFIED_CHINESE)
        )
        self.assertEqual(
            [],
            release_loc.candidate_quality_errors(
                english,
                chinese,
                {"zg361m.227.b": "据え置き、補填、解雇、剥奪、携帯を自然に扱う"},
                "japanese",
            ),
        )

    def test_korean_quality_gate_requires_hangul_and_forbids_hanja(self) -> None:
        english = {"line": "Conduct the performance review with evidence."}
        chinese = {"line": "用证据开展绩效考核。"}
        self.assertEqual(
            [],
            release_loc.candidate_quality_errors(
                english,
                chinese,
                {"line": "근거를 바탕으로 성과 평가를 실시한다."},
                "korean",
            ),
        )
        errors = release_loc.candidate_quality_errors(
            english,
            chinese,
            {"line": "근거로 績效 評價를 실시한다."},
            "korean",
        )
        self.assertTrue(any("CJK/kana" in error for error in errors))

    def test_cjk_target_quality_gate_rejects_cyrillic_intrusions(self) -> None:
        english = {"line": "Track old awards and compare peers."}
        chinese = {"line": "跟踪旧奖励并比较同档人员。"}
        cases = (
            ("korean", "기존 старый 보상을 추적하고 동료를 비교한다."),
            ("japanese", "старый 報酬を追跡し、同僚と比較する。"),
        )
        for language, value in cases:
            with self.subTest(language=language):
                errors = release_loc.candidate_quality_errors(
                    english, chinese, {"line": value}, language
                )
                self.assertTrue(any("Cyrillic text" in error for error in errors))

        accepted = (
            ("korean", "기존 보상을 추적하고 동료를 비교한다."),
            ("japanese", "既存の報酬を追跡し、同僚と比較する。"),
        )
        for language, value in accepted:
            with self.subTest(accepted_language=language):
                self.assertEqual(
                    [],
                    release_loc.candidate_quality_errors(
                        english, chinese, {"line": value}, language
                    ),
                )

    def test_reviewed_semantic_regressions_are_release_blockers(self) -> None:
        cases = (
            ("korean", "activity_zg361_jingcha", "경찰 대계", "Jingcha as police"),
            (
                "korean",
                "setting_zg361_freq_three_year_desc",
                "3년마다 경찰 대계를 엽니다",
                "Jingcha as police",
            ),
            (
                "korean",
                "setting_zg361_on_desc",
                "공작급 이상의 천황이 평가한다",
                "Japanese emperor",
            ),
            (
                "korean",
                "zg361_demoted_desc",
                "강등 후 잔류, 봉록 반납",
                "salary surrender",
            ),
            ("polish", "zg361.30.b", "Ukryz dzikie psy", "punishment"),
            (
                "french",
                "zg361m.50.b",
                "Déprécier immédiatement les soupçons d'entraide mutuelle",
                "down-weights suspicion",
            ),
            (
                "german",
                "zg361m.101.desc",
                "Über das Organisations-LEDGER umgesetzt",
                "untranslated or mistranslated fragment",
            ),
            (
                "spanish",
                "zg361m.84.desc",
                "Se aplica mediante el libro organizational ledger compartido",
                "untranslated or mistranslated fragment",
            ),
            (
                "russian",
                "zg361m.1.a",
                "Создать поквартальный лист доказательств",
                "quarterly evidence",
            ),
        )
        for language, key, value, expected in cases:
            with self.subTest(language=language, key=key):
                errors = release_loc.candidate_quality_errors(
                    {key: "Translate this reviewed policy completely"},
                    {key: "完整翻译这条已审查政策"},
                    {key: value},
                    language,
                )
                self.assertTrue(any(expected in error for error in errors), errors)

        accepted_korean = {
            "setting_zg361_on_desc": "천조 체제의 공작급 이상 영주가 직속 관료를 평가합니다",
            "zg361_demoted_desc": "강등 후 잔류하며 봉록은 절반으로 줄어듭니다",
            "activity_zg361_jingcha": "정기 관료 대평가",
        }
        for key, value in accepted_korean.items():
            with self.subTest(accepted_korean=key):
                self.assertEqual(
                    [],
                    release_loc.candidate_quality_errors(
                        {key: "Translate this reviewed policy completely"},
                        {key: "完整翻译这条已审查政策"},
                        {key: value},
                        "korean",
                    ),
                )

    def test_review5_targeted_regressions_are_release_blockers(self) -> None:
        cases = (
            ("japanese", "zg361m.168.t", "推薦 nomination命中率", "stray Latin fragment"),
            ("japanese", "zg361m.227.b", "創業 owner に功績を与える", "mixes English 'owner'"),
            ("japanese", "zg361m.48.a", "事例品質を抽せんする", "non-idiomatic Chinese"),
            ("japanese", "zg361m.251.t", "会議拒否の政治的成本", "non-idiomatic Chinese"),
            ("japanese", "zg361m.272.a", "報酬の社内倒錯を確認する", "non-idiomatic Chinese"),
            ("japanese", "zg361m.347.b", "managers が自由に改訂する", "stray Latin fragment"),
            ("japanese", "zg361m.353.b", "リスク抑制を優先して対応力を犠牲にする", "compliance-over-capacity"),
            ("japanese", "zg361m.12.b", "翻案リスクを負う", "appeal or reversal"),
            ("japanese", "zg361m.23.a", "覆命を記録する", "appeal or reversal"),
            ("japanese", "zg361m.23.a", "評価の撤回を記録する", "appeal or reversal"),
            ("japanese", "zg361m.95.a", "覆案を確認する", "appeal or reversal"),
            ("japanese", "zg361.1.desc", "末尾規則と末尾淘汰", "end of a string"),
            ("japanese", "zg361m.272.a", "報酬倒錯を点検する", "pay inversion"),
            ("japanese", "zg361m.120.t", "onboarding 計画", "stray Latin fragment"),
            ("japanese", "zg361m.205.t", "Toil の削減", "stray Latin fragment"),
            ("japanese", "zg361m.212.b", "throughput を優先する", "stray Latin fragment"),
            ("japanese", "zg361m.295.b", "金色の handcuffs を選ぶ", "stray Latin fragment"),
            ("korean", "zg361m.50.b", "의심되는 상호 칭찬 쌍을 즉시 가중치를 낮춘다", "double-object"),
            ("korean", "zg361m.75.a", "국고 비용을 부담하고 거절권을 보장합니다", "합니다체"),
            ("korean", "zg361m.95.a", "성과 번안을 기준으로 심사한다", "adaptations"),
            ("korean", "zg361m.100.b", "권력 뇌물을 부른다", "power bribery"),
            ("korean", "zg361m.150.a", "비예정 등급 조항을 명문화", "not guaranteed"),
            ("korean", "zg361m.200.b", "제한 없는 재정의를 허용", "redefinitions"),
            ("korean", "zg361m.361.b", "인재 밀도를 어짜는 헌장", "Korean corruption"),
            ("korean", "zg361m.299.t", "Good-Leaver 및 Bad-Leaver 분류", "untranslated or mistranslated"),
            ("korean", "zg361m.347.t", "Override 권한", "untranslated or mistranslated"),
            ("korean", "zg361m.285.t", "동일 등급 내 2차 승진", "same-grade second raise"),
            ("korean", "zg361m.301.a", "개인 성장을 인정한다", "personal contribution growth"),
            ("korean", "zg361m.315.a", "신규 부서 동시 집행", "dual performance-credit"),
            ("korean", "zg361m.330.b", "즉시 외부에서 즉시 충원", "duplicated Korean adverb"),
            ("korean", "zg361m.275.t", "Offer 거절", "untranslated or mistranslated"),
            ("korean", "zg361m.305.a", "기존 cohort 동결", "untranslated or mistranslated"),
            ("polish", "zg361m.125.b", "widocznego kredytu bohatera", "visible recognition"),
            ("polish", "zg361m.252.b", "przyznać credit", "untranslated or mistranslated"),
            ("polish", "zg361m.325.a", "Zwolnij sprawdzonych wykonawców", "firing proven performers"),
            ("polish", "zg361m.325.a", "Połącz certyfikaty ze sprawdzianami, zwolnij sprawdzonych wykonawców i zatwierdź test", "firing proven performers"),
            ("polish", "zg361m.305.a", "wymagaj nadzoru przełożonego", "mere supervision"),
            ("polish", "zg361m.315.a", "z podwójnym kredytem", "financial credit"),
            ("polish", "zg361m.326.a", "przyznać kredyt organizacyjny", "financial kredyt"),
            ("polish", "zg361m.330.b", "wyjdź ze starych pracowników", "nonsensical action"),
            ("polish", "zg361m.345.a", "wykonaj mid-year check", "untranslated or mistranslated"),
            ("polish", "zg361m.359.t", "Reflow kwoty", "untranslated or mistranslated"),
            ("polish", "zg361m.347.a", "override decyzji", "untranslated or mistranslated"),
            ("polish", "zg361m.205.t", "Redukcja toil", "untranslated or mistranslated"),
            ("russian", "zg361m.125.b", "ради видимого героического кредита", "financial credit"),
            ("russian", "zg361m.325.a", "Освобождайте подтверждённых сотрудников", "from a test or assessment"),
            ("russian", "zg361m.305.a", "запретить докризисные реорганизации", "pre-crisis"),
            ("russian", "zg361m.335.a", "при сдвига сроков и подписанного выбора", "scope/accountability"),
            ("russian", "zg361m.205.t", "Сокращение toil", "untranslated or mistranslated"),
            ("russian", "zg361m.347.a", "Разрешить override", "untranslated or mistranslated"),
            ("german", "zg361m.96.b", "Eine Person sofort überspringen lassen", "leapfrog promotion"),
            ("german", "zg361m.125.a", "und reviewe das Ergebnis", "Denglish verb"),
            ("german", "zg361m.125.b", "sichtbaren Helden-Credit sichern", "Denglish phrase"),
            ("german", "zg361_review_now_decision_desc", "Wenn Sie mindestens eine Person haben", "formal address"),
            ("german", "activity_zg361_jingcha_desc", "Ruft eure Beamten an euren Sitz", "plural address"),
            ("german", "zg361_jingcha_attended", "Großer Prüfung beigewohnt", "case error"),
            ("german", "zg361.1.desc", "Die Bottom-Quote und Bottom-Tier-Aussonderung", "untranslated or mistranslated"),
            ("german", "zg361m.258.a", "Governance-Risiko ins Hauptbuch", "without a verb"),
            ("german", "zg361m.258.a", "Kontrollgruppen-Risiko protokollieren", "control-group risk"),
            ("german", "zg361m.258.a", "Kontrollgruppen-Risiken dokumentieren", "control-group risk"),
            ("german", "zg361m.275.t", "HC-Reservierung nach Offer-Ablehnung", "untranslated or mistranslated"),
            ("german", "zg361m.320.b", "Cultural Mismatch behaupten", "untranslated or mistranslated"),
            ("german", "zg361m.205.t", "Toil reduzieren", "untranslated or mistranslated"),
            ("french", "zg361m.50.b", "Réduire le poids des soupçons et encourager de fausses denúncias", "down-weights suspicion"),
            ("french", "zg361m.205.t", "Réduire le toil", "untranslated or mistranslated"),
            ("spanish", "zg361m.25.t", "Captación de Altos Rendimientos", "abstract performance"),
            ("spanish", "zg361m.125.b", "crédito de héroe visible", "visible recognition"),
            ("spanish", "zg361m.290.t", "Nombramientos a premios", "reward nominations"),
            ("spanish", "zg361m.305.a", "propiedad del superior", "property ownership"),
            ("spanish", "zg361m.315.a", "crédito dual", "financial credit"),
            ("spanish", "zg361m.353.a", "seguir los re picos de errores", "corrupted Spanish"),
            ("spanish", "zg361m.100.b", "invita al rent seeking", "untranslated or mistranslated"),
            ("spanish", "zg361m.205.t", "Reducir el toil", "untranslated or mistranslated"),
            ("spanish", "zg361m.347.a", "Permitir override", "untranslated or mistranslated"),
            ("russian", "zg361m.157.a", "назначить sponsor и owner", "untranslated or mistranslated"),
            ("french", "zg361m.134.a", "Enregistrer un owner", "untranslated or mistranslated"),
            ("french", "zg361m.351.a", "Prérégistrer règles et témoins", "control-group"),
            ("german", "zg361m.351.a", "Regeln und Kontrollen registrieren", "control-group"),
            ("korean", "zg361m.351.a", "규칙과 통제를 사전 등록", "control-group"),
            ("polish", "zg361m.351.a", "Zarejestruj zasady i kontrole", "control-group"),
            ("russian", "zg361m.351.a", "Зарегистрировать правила и контроль", "control-group"),
            ("spanish", "zg361m.351.a", "Preinscribir reglas y controles", "control-group"),
        )
        for language, key, value, expected in cases:
            with self.subTest(language=language, key=key):
                errors = release_loc.candidate_quality_errors(
                    {key: "Translate this reviewed policy completely"},
                    {key: "完整翻译这条已审查政策"},
                    {key: value},
                    language,
                )
                self.assertTrue(any(expected in error for error in errors), errors)

        accepted = (
            ("korean", "zg361m.50.b", "서로 치켜세운 두 사람의 평가 가중치를 즉시 낮춘다"),
            ("german", "zg361m.96.b", "Einer Person wegen einer herausragenden Leistung eine Beförderung über eine Stufe hinweg erlauben"),
            ("french", "zg361m.50.b", "Réduire immédiatement le poids accordé aux personnes soupçonnées de se surnoter mutuellement"),
            ("polish", "zg361m.325.a", "Zwolnij sprawdzonych wykonawców z testu praktycznego"),
            ("russian", "zg361m.325.a", "Освобождать проверенных исполнителей от практической проверки"),
            ("japanese", "zg361m.23.a", "覆された評価を記録する"),
        )
        for language, key, value in accepted:
            with self.subTest(accepted_language=language, accepted_key=key):
                self.assertEqual(
                    [],
                    release_loc.candidate_quality_errors(
                        {key: "Translate this reviewed policy completely"},
                        {key: "完整翻译这条已审查政策"},
                        {key: value},
                        language,
                    ),
                )

    def test_european_quality_gate_rejects_foreign_script_and_english_runs(self) -> None:
        english = {"line": "owner lead collaborator rescuer blocker"}
        chinese = {"line": "负责人、牵头人、协作者、救火者、阻塞者"}
        self.assertEqual(
            [],
            release_loc.candidate_quality_errors(
                english,
                chinese,
                {"line": "responsable, pilote, collaborateur, sauveteur, bloqueur"},
                "french",
            ),
        )
        errors = release_loc.candidate_quality_errors(
            english,
            chinese,
            {"line": "owner lead collaborator rescuer blocker"},
            "french",
        )
        self.assertTrue(any("copied English phrase" in error for error in errors))
        errors = release_loc.candidate_quality_errors(
            english,
            chinese,
            {"line": "responsable 与 collaborateur"},
            "french",
        )
        self.assertTrue(any("foreign-script" in error for error in errors))

    def test_review5g_exact_audit_blockers_are_rejected(self) -> None:
        cases = (
            ("japanese", "rule_zg361_bottom_ratio", "末尾枠"),
            ("japanese", "setting_zg361_ratio_relaxed_desc", "末尾10％の枠を緩和する"),
            ("japanese", "setting_zg361_ratio_off_desc", "末尾層を強制しない"),
            ("japanese", "zg361_purge_interaction", "末位処分・爵位剥奪"),
            ("japanese", "zg361_force_retire_interaction", "末位処分・強制退職"),
            ("japanese", "zg361_pip_desc", "末端淘汰プロセスへ移行する"),
            ("japanese", "zg361.1.desc", "末端ノルマ規則と末端淘汰"),
            ("japanese", "zg361.5.desc", "末端からの淘汰は避けられない"),
            ("japanese", "zg361.11.desc", "名の末尾をやい行をひとつ上へ移す"),
            ("japanese", "zg361m.32.a", "翻案データで評価する"),
            ("japanese", "zg361m.76.a", "翻案後に責任を配分する"),
            ("japanese", "zg361m.119.a", "HC申請者と選考担当者に書き戻す"),
            ("japanese", "zg361m.295.b", "二年後に vesting を加速する"),
            ("japanese", "zg361m.359.t", "翻案後の配分戻り"),
            ("korean", "zg361_demoted_desc", "말년 퇴출은 너그럽게 처리한다"),
            ("korean", "zg361.4.desc", "한 번 더 3.25면 말등 탈락이다"),
            ("korean", "zg361m.361.b", "강경 헌법을 채택한다"),
            ("russian", "zg361.4.desc", "При наличии жалованья урезается один год."),
            ("spanish", "zg361m.296.a", "Vesting trimestral tras la carencia"),
            ("spanish", "zg361m.347.t", "Presupuesto de anulación del responsable"),
            ("spanish", "zg361m.347.a", "Conceder puntos de anulación"),
            ("german", "zg361_mechanism_choice_c_tt", "Policy-Schulden im nächsten Review"),
            ("german", "zg361m.3.a", "Coaching-Review mit Krisen-Reset"),
            ("german", "zg361m.61.a", "Narrative für Ausnahmen und Template-Pflege"),
            ("german", "zg361m.84.t", "Bonus und Vesting"),
            ("german", "zg361m.84.a", "Dreijahres-Vesting-Konto"),
            ("german", "zg361m.85.a", "Vesting-Endpunkte und Peers"),
            ("german", "zg361m.114.t", "Manager-Credit für Talentexport"),
            ("german", "zg361m.114.b", "Star und Output mit Credit schützen"),
            ("german", "zg361m.119.a", "Nach Ramp-up Erfolg oder Mismatch zurückschreiben"),
            ("german", "zg361m.121.a", "Skip-Level-Review durchführen"),
            ("german", "zg361m.123.a", "manager-spezifisch nach Reviewer-Credit gewichten"),
            ("german", "zg361m.277.b", "Low Performer ersetzen"),
            ("german", "zg361m.280.a", "Beim Cohort-Eintritt eine Service-Monatsformel einfrieren"),
            ("german", "zg361m.296.t", "Monatliches Vesting"),
            ("german", "zg361m.347.t", "Manager-Override-Budget"),
            ("german", "zg361m.347.a", "Wenige Override-Punkte geben"),
            ("french", "zg361m.20.b", "Laisser un sponsor piloter le packaging"),
            ("french", "zg361m.41.a", "Fixer des objectifs de ramp-up"),
            ("french", "zg361m.130.b", "Reconvertir le faible performer"),
            ("french", "zg361m.277.b", "À la sortie d'un faible performer"),
        )
        self.assertEqual(41, len(cases))
        for language, key, value in cases:
            with self.subTest(language=language, key=key):
                self.assertTrue(
                    release_loc.targeted_quality_errors(key, value, language)
                )

        accepted = (
            ("japanese", "rule_zg361_bottom_ratio", "最下位枠"),
            ("japanese", "zg361m.32.a", "評価の覆りを記録する"),
            ("japanese", "zg361m.119.a", "HC申請者、選考担当者、最終承認者に書き戻す"),
            ("korean", "zg361m.361.b", "강제 경쟁을 우선하는 강경 헌장을 채택한다"),
            (
                "russian",
                "zg361.4.desc",
                "Казна -50, личное золото -25, заслуги -60, жалованье -25% на один год.",
            ),
            ("spanish", "zg361m.347.t", "Presupuesto de ajustes manuales discrecionales"),
        )
        for language, key, value in accepted:
            with self.subTest(accepted_language=language, accepted_key=key):
                self.assertEqual(
                    [], release_loc.targeted_quality_errors(key, value, language)
                )

    def test_review5j_exact_nonprotected_english_inventory_is_rejected(self) -> None:
        inventory_size = sum(
            len(keys) for keys in release_loc.REVIEW5J_EXACT_FORBIDDEN.values()
        )
        self.assertEqual(72, inventory_size)
        for language, keys in release_loc.REVIEW5J_EXACT_FORBIDDEN.items():
            for key, fragments in keys.items():
                with self.subTest(language=language, key=key):
                    value = f"texte {fragments[0]} text"
                    errors = release_loc.targeted_quality_errors(
                        key, value, language
                    )
                    self.assertTrue(
                        any("non-protected English" in error for error in errors),
                        errors,
                    )

    def test_final_independent_audit_blockers_are_exactly_rejected(self) -> None:
        rejected = (
            ("german", "zg361.4.desc", "Ein Performance Improvement Plan beginnt."),
            ("german", "zg361m.340.t", "#340 · Work-in-Progress-Limit"),
            ("french", "zg361m.85.a", "Réserver les packages de renouvellement."),
            (
                "german",
                "zg361m.347.a",
                "Begünstigte, Verantwortlichen und Grund benennen.",
            ),
            ("korean", "zg361m.361.b", "강경 헌장과 즉시 배달을 우선한다."),
            ("russian", "zg361m.202.a", "Назначить named supporters и проверяющего."),
            ("spanish", "zg361m.29.a", "claw back las recompensas."),
            ("french", "zg361m.136.t", "#136 · Préc réunion de calibration"),
            ("spanish", "zg361m.344.b", "Pagar el crédito y elbonus."),
        )
        self.assertEqual(
            9,
            sum(len(keys) for keys in release_loc.FINAL_EXACT_FORBIDDEN.values()),
        )
        for language, key, value in rejected:
            with self.subTest(language=language, key=key):
                errors = release_loc.targeted_quality_errors(key, value, language)
                self.assertTrue(
                    any("final independently reviewed blocker" in error for error in errors),
                    errors,
                )

        accepted = (
            (
                "german",
                "zg361.4.desc",
                "Lokalschatz -50, persönliches Gold -25, Verdienst -60 und Gehalt -25% für ein Jahr; ein Leistungsverbesserungsplan (PIP) beginnt.",
            ),
            ("german", "zg361m.340.t", "#340 · Begrenzung laufender Arbeit"),
            ("french", "zg361m.85.a", "Réserver les offres de renouvellement."),
            (
                "german",
                "zg361m.347.a",
                "Begünstigten, Lastenträger und Grund benennen.",
            ),
            ("korean", "zg361m.361.b", "강경 헌장과 즉시 업무 인도를 우선한다."),
            ("russian", "zg361m.202.a", "Назначить указанных сторонников и проверяющего."),
            ("spanish", "zg361m.29.a", "Recuperar las recompensas."),
            ("french", "zg361m.136.t", "#136 · Réunion restreinte de pré-calibration"),
            ("spanish", "zg361m.344.b", "Pagar el mérito y la bonificación."),
        )
        for language, key, value in accepted:
            with self.subTest(accepted_language=language, accepted_key=key):
                self.assertEqual(
                    [], release_loc.targeted_quality_errors(key, value, language)
                )

    def test_fourfold_settlement_requires_all_exact_numbers(self) -> None:
        errors = release_loc.targeted_quality_errors(
            "zg361_grade_325_desc",
            "Lokalschatz -50, persönliches Gold -25 und Gehalt -25% für ein Jahr.",
            "german",
        )
        self.assertTrue(any("four exact 3.25 consequences" in error for error in errors))
        self.assertEqual(
            [],
            release_loc.targeted_quality_errors(
                "zg361_grade_325_desc",
                "Lokalschatz -50, persönliches Gold -25, Verdienst -60 und Gehalt -25% für ein Jahr.",
                "german",
            ),
        )

    def test_changed_generic_descriptions_use_semantic_request_overrides(self) -> None:
        expected = {
            "zg361m.14.desc": ("3.25", "25%", "refunds"),
            "zg361m.18.desc": ("-50", "-25", "-60", "-25%"),
            "zg361m.21.desc": ("3.75", "3.5", "3.25"),
        }
        for key, fragments in expected.items():
            with self.subTest(key=key):
                value = release_loc.TRANSLATION_SOURCE_OVERRIDES[key]
                self.assertNotIn("\\n", value)
                for fragment in fragments:
                    self.assertIn(fragment, value)
                self.assertEqual(
                    [], release_loc.targeted_quality_errors(key, value, "german")
                )

        generic = "[C / P0] This policy changes later team results."
        self.assertTrue(
            release_loc.targeted_quality_errors(
                "zg361m.14.desc", generic, "german"
            )
        )
        self.assertTrue(
            release_loc.targeted_quality_errors(
                "zg361m.21.desc", generic, "german"
            )
        )

    def test_review6c_source_migration_semantic_blockers_are_rejected(self) -> None:
        rejected = (
            (
                "french",
                "zg361.4.desc",
                "Trésor -50, or -25, mérite -60, salaire -25% pendant un an; élimination du dernier tiers.",
            ),
            (
                "french",
                "zg361.4.desc",
                "Trésor -50, or -25, mérite -60, salaire -25% pendant un an; élimination du dernier niveau.",
            ),
            (
                "japanese",
                "zg361_grade_325_desc",
                "地方国庫 -50、自国庫 -25、人事評価 -60、俸給 -25% を一年間。",
            ),
            (
                "japanese",
                "zg361.4.desc",
                "地方国庫 -50、個人の金 -25、功徳 -60、俸給 -25% を一年間。もう一度 3.25 を付けば最下位として淘汰される。",
            ),
            (
                "japanese",
                "zg361m.14.desc",
                "3.25 の地方財庫等を返し、俸給 -25% を停止する。",
            ),
            (
                "japanese",
                "zg361m.14.a",
                "三項目の即時返金と俸禄停止を記録する。",
            ),
            (
                "japanese",
                "zg361m.18.desc",
                "地方財庫 -50、個人資金 -25、功績 -60、俸給 -25%。",
            ),
            (
                "japanese",
                "zg361m.18.a",
                "財庫と個人資金を凍結し、俸禄減成を記録する。",
            ),
            (
                "japanese",
                "zg361m.18.a",
                "決済時に地方国庫・個人の金・功徳を凍結する。",
            ),
            (
                "korean",
                "zg361m.21.desc",
                "3.75는 단기 승급, 3.5는 유지, 3.25는 네 가지 처벌을 받는다.",
            ),
            (
                "korean",
                "zg361m.14.a",
                "즉시 환급 세 항목과 봉록 중단을 기록한다.",
            ),
            (
                "korean",
                "zg361m.14.a",
                "재보정과 세 건의 즉시 환급, 봉급 감액 중단 항목을 항목별로 정리합니다.",
            ),
            (
                "russian",
                "zg361m.21.desc",
                "3.75 получает краткосрочное повышение, 3.5 без изменений, 3.25 — четверное наказание.",
            ),
            (
                "russian",
                "zg361m.21.desc",
                "3.75 получает краткосрочное повышение жалованья, 3.5 без изменений, 3.25 — четверное наказание; кадры без награды repeatedly уходят.",
            ),
            (
                "spanish",
                "zg361m.21.desc",
                "3.75 recibe un pequeño aumento, 3.5 no cambia y 3.25 mantiene la sanción; el talento es premiado repetidamente.",
            ),
        )
        for language, key, value in rejected:
            with self.subTest(language=language, key=key):
                self.assertTrue(
                    release_loc.targeted_quality_errors(key, value, language)
                )

        accepted = (
            (
                "french",
                "zg361.4.desc",
                "Trésor -50, or -25, mérite -60, salaire -25% pendant un an; élimination du niveau le plus bas.",
            ),
            (
                "japanese",
                "zg361_grade_325_desc",
                "地方国庫 -50、個人の金 -25、功徳 -60、俸給 -25% を一年間。",
            ),
            (
                "japanese",
                "zg361.4.desc",
                "地方国庫 -50、個人の金 -25、功徳 -60、俸給 -25% を一年間。もう一度3.25を取れば最下位として淘汰される。",
            ),
            (
                "japanese",
                "zg361m.14.a",
                "三項目の即時返金と俸給減額の停止を記録する。",
            ),
            (
                "japanese",
                "zg361m.18.a",
                "精算時に地方国庫・個人の金・功徳を凍結する。",
            ),
            (
                "korean",
                "zg361m.21.desc",
                "3.75는 단기 녹봉 인상, 3.5는 유지, 3.25는 네 가지 처벌을 받는다.",
            ),
            (
                "korean",
                "zg361m.14.a",
                "즉시 환급 세 항목과 녹봉 감액 중단을 기록한다.",
            ),
            (
                "russian",
                "zg361m.21.desc",
                "3.75 получает краткосрочное повышение жалованья, 3.5 без изменений, 3.25 — четверное наказание.",
            ),
            (
                "spanish",
                "zg361m.21.desc",
                "3.75 recibe un aumento salarial temporal, 3.5 no cambia y 3.25 mantiene la sanción; el talento no recompensado repetidamente puede marcharse.",
            ),
        )
        for language, key, value in accepted:
            with self.subTest(accepted_language=language, accepted_key=key):
                self.assertEqual(
                    [], release_loc.targeted_quality_errors(key, value, language)
                )

    def test_migrated_resource_keys_require_ck3_official_japanese_and_korean_terms(self) -> None:
        for key in release_loc.OFFICIAL_RESOURCE_KEYS:
            with self.subTest(language="japanese", key=key):
                errors = release_loc.targeted_quality_errors(
                    key,
                    "3.75 / 3.5 / 3.25、地方財務 -50、個人資金 -25、功績 -60、俸給 -25%。最下位。",
                    "japanese",
                )
                self.assertTrue(
                    any("official Japanese merit term" in error for error in errors),
                    errors,
                )
                self.assertTrue(
                    any("personal gold" in error for error in errors), errors
                )
            with self.subTest(language="korean", key=key):
                errors = release_loc.targeted_quality_errors(
                    key,
                    "3.75 / 3.5 / 3.25, 지방 국고 -50, 개인 금화 -25, 업적 -60, 녹봉 -25%.",
                    "korean",
                )
                self.assertTrue(
                    any("official Korean merit term" in error for error in errors),
                    errors,
                )

    def test_review5j_semantic_regressions_are_rejected(self) -> None:
        rejected = (
            (
                "korean",
                "zg361.4.desc",
                "해당될 경우 1년치 녹봉을 삭감한다.",
                "four exact 3.25 consequences",
            ),
            (
                "german",
                "zg361m.119.a",
                "An den HC-Anfragenden, die Auswahl und den Genehmiger zurückschreiben.",
                "selector as an accountable person",
            ),
            (
                "french",
                "zg361m.130.b",
                "Rebailler le salarié peu performant en haut potentiel.",
                "rebranding or reclassification",
            ),
        )
        for language, key, value, expected in rejected:
            with self.subTest(language=language, key=key):
                errors = release_loc.targeted_quality_errors(key, value, language)
                self.assertTrue(any(expected in error for error in errors), errors)

        accepted = (
            (
                "korean",
                "zg361.4.desc",
                "지방 국고 -50, 개인 금화 -25, 공덕 -60, 녹봉 -25%를 1년간 적용한다.",
            ),
            (
                "german",
                "zg361m.119.a",
                "An HC-Anfragenden, Auswahlverantwortlichen und Genehmiger zurückschreiben.",
            ),
            (
                "french",
                "zg361m.130.b",
                "Requalifier le salarié peu performant en haut potentiel.",
            ),
        )
        for language, key, value in accepted:
            with self.subTest(accepted_language=language, accepted_key=key):
                self.assertEqual(
                    [], release_loc.targeted_quality_errors(key, value, language)
                )

    def test_review6i_quote_repairs_preserve_policy_semantics(self) -> None:
        rejected = (
            ("korean", "zg361m.130.t", "저성과자를 다른 팀으로 떠넘기기"),
            (
                "korean",
                "zg361m.263.b",
                "임시 차관을 무기한 연장하고 프로젝트 뒤에 소속을 정한다",
            ),
            (
                "korean",
                "zg361m.263.b",
                "임시 파견을 무기한 연장하고 프로젝트 종료 후에야 책임자를 정한다",
            ),
            ("korean", "zg361m.283.t", "#283 · 무승급 인사 조치 기한"),
            (
                "polish",
                "zg361m.283.a",
                "Promocja obowiązkowa musi wyznaczyć termin podwyżki",
            ),
        )
        for language, key, value in rejected:
            with self.subTest(language=language, key=key):
                self.assertTrue(
                    release_loc.targeted_quality_errors(key, value, language)
                )

        accepted = (
            ("korean", "zg361m.130.t", "#130 · 저성과자를 다른 팀으로 떠넘기기"),
            ("korean", "zg361m.130.t", "No.130 · 저성과자를 다른 팀으로 떠넘기기"),
            (
                "korean",
                "zg361m.263.b",
                "임시 파견을 무기한 연장하고 프로젝트가 끝난 뒤에야 소속을 결정한다",
            ),
            ("korean", "zg361m.283.t", "#283 · 무급 승진의 급여 반영 기한"),
            ("korean", "zg361m.283.t", "No.283 · 무급 승진의 급여 반영 기한"),
            ("polish", "zg361m.283.t", "No.283 · Termin wyrównania płacy po awansie"),
            (
                "polish",
                "zg361m.283.a",
                "Awans obejmujący najpierw obowiązki musi wyznaczyć termin podwyżki",
            ),
        )
        for language, key, value in accepted:
            with self.subTest(accepted_language=language, accepted_key=key):
                self.assertEqual(
                    [], release_loc.targeted_quality_errors(key, value, language)
                )

    def test_language_prompts_pin_stubborn_management_terms_to_natural_targets(self) -> None:
        expected = {
            "japanese": ("本層", "この階層", "最下位", "定着面談", "サービス水準合意"),
            "korean": ("zg361.2.desc", "평가군", "cohort", "절반", "서비스 수준 협약"),
            "russian": ("оценочная", "cliff", "#295", "соглашение об уровне услуг", "интервью по удержанию"),
            "french": ("délai de carence", "cliff", "#296", "accord de niveau de service", "requalifier", "entretien de fidélisation"),
            "german": (
                "Verantwortlicher",
                "Routinearbeit",
                "Sperrfrist",
                "Anwartschaft",
                "hierarchieübergreifende",
                "leistungsschwacher Mitarbeiter",
                "Ermessensanpassung",
                "vergleichbare Beschäftigte",
                "Dienstgütevereinbarung",
                "Auswahlverantwortlicher",
                "Bindungsgespräch",
            ),
            "polish": ("umowa o poziomie usług", "skip-level", "rozmowa retencyjna"),
            "spanish": ("periodo de carencia", "cliff", "#295", "acuerdo de nivel de servicio", "trabajo en curso"),
        }
        for language, fragments in expected.items():
            with self.subTest(language=language):
                suffix = release_loc.LANGUAGE_PROMPT_SUFFIX[language]
                for fragment in fragments:
                    self.assertIn(fragment, suffix)

    def test_english_copy_gate_ignores_protected_ck3_script_tokens(self) -> None:
        token = "[TopScope.GetValue('zg_n_score')|0]"
        english = {"line": f"Current KPI: {token}"}
        chinese = {"line": f"当前 KPI：{token}"}
        candidate = {"line": f"KPI actuel : {token}"}
        self.assertEqual(
            [],
            release_loc.candidate_quality_errors(
                english, chinese, candidate, "french"
            ),
        )

    def test_residual_gate_ignores_only_protected_ck3_script_tokens(self) -> None:
        token = "[TopScope.GetValue('zg361_result_cohort_n')|0]"
        english = {"line": f"Cohort rank: {token}"}
        chinese = {"line": f"同组位次：{token}"}
        translated = {"line": f"Место в оценочной группе: {token}"}
        self.assertEqual(
            [],
            release_loc.candidate_quality_errors(
                english, chinese, translated, "russian"
            ),
        )
        untranslated = {"line": f"Место в cohort: {token}"}
        errors = release_loc.candidate_quality_errors(
            english, chinese, untranslated, "russian"
        )
        self.assertTrue(
            any("fragment 'cohort'" in error for error in errors), errors
        )

    def test_english_copy_gate_ignores_required_technical_terms(self) -> None:
        english = {"line": "KPI / OKR / PIP / HC"}
        chinese = {"line": "KPI / OKR / PIP / HC"}
        candidate = {"line": "KPI / OKR / PIP / HC"}
        self.assertEqual(
            [],
            release_loc.candidate_quality_errors(
                english, chinese, candidate, "german"
            ),
        )

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

    def test_review_now_copy_matches_same_year_idempotence_in_all_nine_languages(self) -> None:
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
        # The decision delegates both validity paths to the shared business
        # trigger; retain the same-year guard check at its actual definition.
        decision = " ".join(
            decisions.partition("zg361_review_now_decision = {")[2]
            .partition("\n}")[0].split()
        )
        business_trigger = " ".join(
            triggers.partition("zg361_review_now_business_valid_trigger = {")[2]
            .partition("\n}")[0].split()
        )
        for validity_path in ("is_valid", "is_valid_showing_failures_only"):
            self.assertIn(
                f"{validity_path} = {{ zg361_review_now_business_valid_trigger = yes }}",
                decision,
            )
        self.assertIn(
            "trigger_if = { limit = { has_variable = zg361_last_settled_year } "
            + guard + " }",
            business_trigger,
        )
        self.assertIn(guard, effects)

        expected = {
            "english": (
                "Order the evaluation bureau to rank your direct roster immediately instead of waiting for the annual season. You may settle only one review per calendar year; officials already covered by your settled review that year will not be evaluated again.",
                "Immediately review at least one direct incumbent official; you cannot settle another review in the same calendar year.",
            ),
            "simp_chinese": (
                "不等年度绩效季，现在就命考功司开榜排名。你每个自然年只能结算一次考核；本年度已纳入你结算考核的直属官员不会重复评定。",
                "立即考核至少一名直属在任官员；同一自然年不能再次结算考核。",
            ),
            "french": (
                "Ordonnez au bureau des examens de classer immédiatement vos officiers directs au lieu d'attendre la saison annuelle. Les officiers déjà évalués cette année ne seront pas réexaminés.",
                "Évaluer immédiatement au moins un titulaire en poste direct ; l'évaluation ne peut pas être répétée la même année.",
            ),
            "german": (
                "Befiehl dem Prüfungsamt, deine direkten Untergebenen sofort zu reihen, statt auf die Saisonrunde zu warten. Bereits in diesem Jahr bewertete Beamte werden nicht erneut beurteilt.",
                "Sofort mindestens einen direkten Amtsinhaber beurteilen; im selben Kalenderjahr kann keine weitere Beurteilung abgeschlossen werden.",
            ),
            "japanese": (
                "年度の考課季を待たず、直ちに考功司に命じて直属の序列を公表させる。今年すでに考課を受けた官吏は再評価されない。",
                "直属の現職官吏を少なくとも一名、ただちに考課する。同じ暦年内に再度実施することはできない。",
            ),
            "korean": (
                "연례 시즌을 기다리지 말고 평가국에 명해 직속 인원을 즉시 등급 매기게 한다. 올해 이미 평가된 관료는 다시 평가되지 않는다.",
                "즉시 최소 한 명의 현직 직속 관료를 평가한다. 같은 해에는 다시 실시할 수 없다.",
            ),
            "polish": (
                "Rozkaż biuru ocen natychmiast uszeregować twoich bezpośrednich podwładnych, zamiast czekać na sezon roczny. Urzędnicy już ocenieni w tym roku nie zostaną ocenieni ponownie.",
                "Natychmiast oceń co najmniej jednego bezpośredniego urzędnika na aktywnym stanowisku; w tym samym roku nie można przeprowadzić kolejnej oceny.",
            ),
            "russian": (
                "Приказать экзаменационной палате немедленно ранжировать ваш прямой штат, не дожидаясь годового сезона. Чиновники, уже аттестованные в этом году, не будут аттестованы повторно.",
                "Немедленно аттестовать хотя бы одного действующего прямого подчинённого чиновника; в том же календарном году повторная аттестация невозможна.",
            ),
            "spanish": (
                "Ordena a la oficina de evaluación que clasifique a tu cuadro directivo de inmediato en lugar de esperar a la temporada anual. Los oficiales ya evaluados este año no serán evaluados de nuevo.",
                "Evalúa inmediatamente al menos a un cargo titular directo en activo; no puedes realizar otra evaluación en el mismo año natural.",
            ),
        }
        for language, (description, tooltip) in expected.items():
            with self.subTest(language=language):
                path = (
                    release_loc.MOD_ROOT
                    / "localization"
                    / language
                    / f"zg361_l_{language}.yml"
                )
                values = release_loc.minimax.parse_ck3_localization(path)
                self.assertEqual(
                    description, values["zg361_review_now_decision_desc"]
                )
                self.assertEqual(
                    tooltip, values["zg361_review_now_decision_tooltip"]
                )


if __name__ == "__main__":
    unittest.main()
