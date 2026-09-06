#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic L0 tests for the complete 361 mechanism projection."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys
import tempfile
import unittest

from gen_361_mechanisms import (
    MOD_ROOT,
    effect_name,
    localization_values,
    naturalize_mechanism_chinese,
    outputs,
)
from zg361_mechanism_data import (
    ACCEPTANCE_FIELDS,
    AcceptanceContract,
    LEDGERS,
    MECHANISM_COUNT,
    PROFILE_DELTAS,
    load_acceptance_contracts,
    load_mechanisms,
    mechanism_deltas,
)
from zg361_phase2_runtime_data import PHASE2_RUNTIME_SPECS
from zg361_readiness_data import (
    CUMULATIVE_COUNTS,
    READINESS_BY_ID,
    ReadinessLevel,
    ids_at_least,
)


def valid_acceptance_payload(mechanism_id: int) -> dict[str, object]:
    return {
        "acceptance_cn": f"机制 {mechanism_id:03d} 必须冻结具体案卷并核对结果。",
        "semantic_family": f"family_{mechanism_id:03d}",
        "required_state": [f"case_{mechanism_id:03d}_id 与 review_serial"],
        "visible_feedback": [f"显示机制 {mechanism_id:03d} 的具体案卷结果"],
        "batch_assertions": [f"机制 {mechanism_id:03d} 的案卷只结算一次"],
    }


class MechanismGenerationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mechanisms = load_mechanisms(MOD_ROOT)
        cls.rendered = outputs(cls.mechanisms)
        cls.effects = "\n".join(
            payload.decode("utf-8-sig")
            for path, payload in sorted(cls.rendered.items())
            if path.parent == MOD_ROOT / "common" / "scripted_effects"
            and path.name.startswith("zg361_generated_mechanism_")
            and path.name.endswith("_effects.txt")
        )

    def test_exact_catalogue(self) -> None:
        self.assertEqual(len(self.mechanisms), MECHANISM_COUNT)
        self.assertEqual([item.id for item in self.mechanisms], list(range(1, 362)))
        self.assertEqual(len({item.title_cn for item in self.mechanisms}), 361)
        self.assertEqual(len({item.title_en for item in self.mechanisms}), 361)

    def test_every_choice_is_reviewed_and_specific(self) -> None:
        generic = {
            "Adopt the evidence-led policy",
            "Prioritize the short-term result",
        }
        for mechanism in self.mechanisms:
            with self.subTest(mechanism=mechanism.id):
                self.assertNotIn(mechanism.option_a_en, generic)
                self.assertNotIn(mechanism.option_b_en, generic)
                self.assertNotEqual(mechanism.option_a_cn, mechanism.option_b_cn)
                self.assertNotEqual(mechanism.option_a_en, mechanism.option_b_en)
                self.assertIn(mechanism.profile, PROFILE_DELTAS)
                self.assertIn(mechanism.reference_choice, {"a", "b", "c"})

    def test_acceptance_contracts_are_typed_complete_and_specific(self) -> None:
        for mechanism in self.mechanisms:
            contract = mechanism.acceptance_contract
            with self.subTest(mechanism=mechanism.id):
                self.assertIsInstance(contract, AcceptanceContract)
                self.assertTrue(contract.acceptance_cn)
                self.assertTrue(contract.semantic_family)
                self.assertTrue(contract.required_state)
                self.assertTrue(contract.visible_feedback)
                self.assertTrue(contract.batch_assertions)
                for values in (
                    contract.required_state,
                    contract.visible_feedback,
                    contract.batch_assertions,
                ):
                    self.assertTrue(all(isinstance(value, str) and value for value in values))

    def test_acceptance_loader_rejects_missing_id(self) -> None:
        with tempfile.TemporaryDirectory() as raw_folder:
            folder = Path(raw_folder)
            payload = {
                f"{mechanism_id:03d}": valid_acceptance_payload(mechanism_id)
                for mechanism_id in range(1, MECHANISM_COUNT)
            }
            (folder / "acceptance_001_360.json").write_text(
                json.dumps(payload, ensure_ascii=False), encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "exactly 001..361"):
                load_acceptance_contracts(folder)

    def test_acceptance_loader_rejects_duplicate_id(self) -> None:
        with tempfile.TemporaryDirectory() as raw_folder:
            folder = Path(raw_folder)
            duplicate = {"001": valid_acceptance_payload(1)}
            for name in ("acceptance_a.json", "acceptance_b.json"):
                (folder / name).write_text(
                    json.dumps(duplicate, ensure_ascii=False), encoding="utf-8"
                )
            with self.assertRaisesRegex(ValueError, "duplicate acceptance contract"):
                load_acceptance_contracts(folder)

    def test_acceptance_loader_rejects_missing_or_wrong_typed_field(self) -> None:
        with tempfile.TemporaryDirectory() as raw_folder:
            folder = Path(raw_folder)
            missing = valid_acceptance_payload(1)
            del missing["visible_feedback"]
            (folder / "acceptance_missing.json").write_text(
                json.dumps({"001": missing}, ensure_ascii=False), encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "fields mismatch"):
                load_acceptance_contracts(folder)

        with tempfile.TemporaryDirectory() as raw_folder:
            folder = Path(raw_folder)
            wrong_type = valid_acceptance_payload(1)
            wrong_type["required_state"] = "not a list"
            (folder / "acceptance_wrong_type.json").write_text(
                json.dumps({"001": wrong_type}, ensure_ascii=False), encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "must be a non-empty list"):
                load_acceptance_contracts(folder)

    def test_acceptance_loader_rejects_generic_variable_change_only(self) -> None:
        with tempfile.TemporaryDirectory() as raw_folder:
            folder = Path(raw_folder)
            generic = valid_acceptance_payload(1)
            generic["batch_assertions"] = ["变量变化"]
            (folder / "acceptance_generic.json").write_text(
                json.dumps({"001": generic}, ensure_ascii=False), encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "generic variable-change claim"):
                load_acceptance_contracts(folder)

    def test_shared_ledgers_have_real_tradeoffs(self) -> None:
        for mechanism in self.mechanisms:
            choices = {
                choice: mechanism_deltas(mechanism, choice)
                for choice in ("a", "b", "c")
            }
            with self.subTest(mechanism=mechanism.id):
                self.assertEqual(len({tuple(sorted(value.items())) for value in choices.values()}), 3)
                for deltas in choices.values():
                    self.assertTrue(deltas)
                    self.assertTrue(set(deltas).issubset(LEDGERS))
                # At least one route carries an explicit cost/risk, preventing a no-brainer trio.
                self.assertTrue(
                    any(
                        value > 0
                        for choice in choices.values()
                        for key, value in choice.items()
                        if key
                        in {
                            "admin_load",
                            "appeal_risk",
                            "tech_debt",
                            "burnout",
                            "hc_pressure",
                            "pay_debt",
                            "policy_debt",
                            "budget_pressure",
                        }
                    )
                )

    def test_generated_runtime_coverage(self) -> None:
        event_path = MOD_ROOT / "events" / "zg361_generated_mechanism_events.txt"
        events = self.rendered[event_path].decode("utf-8-sig")
        effects = self.effects
        for mechanism in self.mechanisms:
            with self.subTest(mechanism=mechanism.id):
                self.assertEqual(events.count(f"zg361m.{mechanism.id} = {{"), 1)
                for choice in ("a", "b", "c"):
                    self.assertEqual(effects.count(f"{effect_name(mechanism.id, choice)} = {{"), 1)
                    self.assertIn(
                        f"custom_tooltip = zg361m.{mechanism.id}.{choice}.tt",
                        events,
                    )
                self.assertEqual(
                    effects.count(f"zg361_mechanism_{mechanism.id:03d}_ai_effect = {{"),
                    1,
                )
                self.assertIn(f"ZG361M: CASE {mechanism.id:03d}", effects)

    def test_org_climate_thresholds_do_not_read_unset_ledgers(self) -> None:
        effects = self.effects
        climate = effects.split("zg361_refresh_org_climate_effect = {", 1)[1]
        expected = (
            ("trust", 20, "zg361_org_high_trust"),
            ("admin_load", 35, "zg361_org_admin_overload"),
            ("burnout", 20, "zg361_org_burnout_crisis"),
            ("stability", 20, "zg361_org_delivery_stable"),
            ("tech_debt", 20, "zg361_org_tech_debt_crisis"),
            ("talent", 20, "zg361_org_talent_healthy"),
        )
        for ledger, threshold, modifier in expected:
            variable = f"zg361_org_{ledger}"
            guarded = (
                "\tif = {\n"
                "\t\tlimit = {\n"
                "\t\t\ttrigger_if = {\n"
                f"\t\t\t\tlimit = {{ has_variable = {variable} }}\n"
                f"\t\t\t\tvar:{variable} >= {threshold}\n"
                "\t\t\t}\n"
                "\t\t\ttrigger_else = { always = no }\n"
                "\t\t}\n"
                f"\t\tadd_character_modifier = {{ modifier = {modifier} years = 1 }}\n"
                "\t}"
            )
            with self.subTest(ledger=ledger):
                self.assertIn(guarded, climate)
                self.assertNotIn(
                    f"\t\tlimit = {{ var:{variable} >= {threshold} }}", climate
                )

    def test_policy_localization_renders_ids_and_line_breaks_literally(self) -> None:
        chinese_path = (
            MOD_ROOT
            / "localization"
            / "simp_chinese"
            / "zg361_mechanisms_l_simp_chinese.yml"
        )
        english_path = (
            MOD_ROOT
            / "localization"
            / "english"
            / "zg361_mechanisms_l_english.yml"
        )
        chinese = self.rendered[chinese_path].decode("utf-8-sig")
        english = self.rendered[english_path].decode("utf-8-sig")
        self.assertIn('zg361m.1.t:0 "第001号 · 绩效指标分项证据单"', chinese)
        self.assertIn('zg361m.3.t:0 "第003号 · 期中面谈与目标重置"', chinese)
        self.assertIn('zg361m.1.t:0 "No.001 · Itemized KPI Evidence Sheet"', english)
        self.assertIn(
            'zg361_next_mechanism_decision_confirm:0 "打开下一项制度评审"',
            chinese,
        )
        self.assertIn(
            'zg361_reference_charter_decision_confirm:0 "采用全部 361 项推荐默认值，立即写入组织账本"',
            chinese,
        )
        self.assertIn(
            'zg361_next_mechanism_decision_confirm:0 "Open the next policy review"',
            english,
        )
        self.assertIn(
            'zg361_reference_charter_decision_confirm:0 "Adopt all 361 recommended defaults and write them to the organizational ledger"',
            english,
        )
        for empty_slogan in (
            "叫下一位产品经理进来",
            "我全都要，现在就要",
            "Bring in the next policy owner",
            "Ship the entire portfolio",
        ):
            with self.subTest(empty_slogan=empty_slogan):
                self.assertNotIn(empty_slogan, chinese + english)
        self.assertIn(
            'zg361m.1.desc:0 "高低分必须附具体事例；申诉、绩效改进计划和晋升包复用同一份冻结证据，杜绝让下一年的现值改写旧案。"',
            chinese,
        )
        self.assertIn(
            'zg361m.18.a:0 "结算时冻结档位、名次、上司、理由（仅记账）。"',
            chinese,
        )
        self.assertIn(
            'zg361m.18.a.tt:0 "结算时冻结档位、名次、上司、理由，以及国库、个人金币、贤能三笔即时罚没与一年俸禄减成，逐项标记支付、退款和止扣状态。这项裁定只记入组织账簿；没有具体案卷时，不会据此办理款项、人事或职位变动。"',
            chinese,
        )
        self.assertIn(
            'zg361m.71.a:0 "穷尽私下沟通与正式申诉后，凭冻结证据实名公开并接受调解复核。"',
            chinese,
        )
        self.assertIn(
            'zg361m.206.a:0 "为每笔赶工记录省时本金、维护利息、风险与责任人。"',
            chinese,
        )
        self.assertIn(
            'zg361m.347.t:0 "第347号 · 经理人工调整额度"',
            chinese,
        )
        self.assertIn(
            'zg361m.18.c:0 "这项制度本局不再提案；记下一笔制度债"',
            chinese,
        )
        self.assertNotIn("决策：", chinese)
        self.assertNotIn("后果：", chinese)
        self.assertNotIn("登记路线甲倾向", chinese)
        self.assertNotIn("登记路线乙倾向", chinese)
        self.assertNotIn("／P0】", chinese)
        self.assertNotIn("／P1】", chinese)
        self.assertNotIn("／P2】", chinese)
        self.assertNotIn("CK3", chinese)
        self.assertNotIn("GUI", chinese)
        self.assertNotIn("Override", chinese)
        for untranslated_term in (
            "HC",
            "PIP",
            "owner",
            "KPI",
            "Offer",
            "sponsor",
            "backfill",
            "Cliff",
            "FIFO",
            "WIP",
            "SLA",
            "toil",
            "onboarding",
            "Check-in",
            "玩家",
            "脚本",
            "回写",
            "本卡",
            "结算器",
            "运行时纵切",
            "OKR",
            "HR",
            " vs ",
            " ID",
            "cohort",
            "PPT",
            "原生治理成果",
        ):
            with self.subTest(untranslated_term=untranslated_term):
                self.assertNotIn(untranslated_term, chinese)
        for raw_grade_phrase in (
            "背 C",
            "C 档",
            "员工 C",
            "填 C",
            "免 C",
            "的 C",
        ):
            with self.subTest(raw_grade_phrase=raw_grade_phrase):
                self.assertNotIn(raw_grade_phrase, chinese)
        self.assertIsNone(re.search(r"(?<![A-Za-z])live(?![A-Za-z])", chinese))
        self.assertIn(
            'zg361m.18.a:0 "Freeze rating; marking every payment, refund, and termination separately (ledger only)"',
            english,
        )
        self.assertIn(
            'zg361m.18.a.tt:0 "Freeze rating, rank, superior, reasons, the three immediate treasury, personal-gold, and merit charges, and the one-year salary cut at settlement, marking every payment, refund, and termination separately. This item updates only the organizational ledger and does not execute a concrete business action."',
            english,
        )
        self.assertIn(
            'zg361m.18.c:0 "Close this policy for the campaign and record one policy debt"',
            english,
        )
        self.assertNotIn("Record route A preference", english)
        self.assertNotIn("Record route B preference", english)
        self.assertNotIn("执行人物", chinese)
        self.assertNotIn("一键部署《大厂全家桶》", chinese)
        self.assertNotIn("。 本项", chinese)
        self.assertNotIn(r"\\n", chinese)
        mechanisms_by_id = {mechanism.id: mechanism for mechanism in self.mechanisms}
        long_buttons = []
        for line in chinese.splitlines():
            if not line.startswith(" zg361m."):
                continue
            if any(f".{choice}:0 \"" in line for choice in ("a", "b")):
                value = line.split(':0 "', 1)[1].removesuffix('"')
                if len(value) > 50:
                    long_buttons.append((line.split(":", 1)[0], value))
            if ".desc:0 " not in line:
                continue
            key, value = line.split(':0 "', 1)
            mechanism_id = int(key.removeprefix(" zg361m.").removesuffix(".desc"))
            description = value.removesuffix('"')
            with self.subTest(mechanism_id=mechanism_id):
                self.assertFalse(description.startswith(("。", "，", "；", "：", "！", "？")))
                self.assertNotIn(mechanisms_by_id[mechanism_id].title_cn, description)
                self.assertNotIn(mechanisms_by_id[mechanism_id].decision_cn, description)
        self.assertEqual(long_buttons, [])
        for path, rendered in self.rendered.items():
            if path.name.startswith("zg361_mechanisms_l_"):
                text = rendered.decode("utf-8-sig")
                title_lines = [
                    line
                    for line in text.splitlines()
                    if line.startswith(" zg361m.") and ".t:0 " in line
                ]
                with self.subTest(language=path.parent.name):
                    self.assertEqual(len(title_lines), 361)
                    self.assertFalse(any(':0 "#' in line for line in title_lines))

    def test_every_policy_surface_has_self_contained_copy(self) -> None:
        opening_punctuation = tuple("。！？；：，、,.!?;:)]}）】》〉」』”’…—-·/／")
        dynamic_openers = tuple("[$@")
        generic_button = re.compile(
            r"^(?:(?:按|照|选|走|采用)\s*[ＡＢＣABC](?:做|办|执行|处理|路线)?"
            r"|路线\s*[甲乙丙ＡＢＣABC]|照办|同意|执行|确定|就这么办|好|可以|知道了)"
            r"[。！？]?$",
            re.IGNORECASE,
        )
        body_choice_meta = re.compile(
            r"(?:路线\s*[甲乙丙ＡＢＣABC]|方案\s*[甲乙丙ＡＢＣABC]"
            r"|按\s*[ＡＢＣABC](?:做|办|执行|处理|走)?|(?:下方|以下).{0,8}按钮)",
            re.IGNORECASE,
        )
        mechanisms_by_id = {mechanism.id: mechanism for mechanism in self.mechanisms}

        for language in ("simp_chinese", "english"):
            values = localization_values(self.mechanisms, language)
            for key, value in values.items():
                if not (key.endswith(".desc") or key.endswith("_desc")):
                    continue
                with self.subTest(language=language, key=key):
                    visible = value.strip()
                    self.assertTrue(visible)
                    self.assertFalse(visible.startswith(opening_punctuation))
                    self.assertFalse(visible.startswith(dynamic_openers))

            for mechanism_id, mechanism in mechanisms_by_id.items():
                prefix = f"zg361m.{mechanism_id}"
                title = values[f"{prefix}.t"].split(" · ", 1)[-1]
                description = values[f"{prefix}.desc"]
                with self.subTest(language=language, mechanism=mechanism_id):
                    self.assertGreaterEqual(len(description.split(r"\n", 1)[0]), 24)
                    self.assertNotIn(title.casefold(), description.casefold())
                    self.assertIsNone(body_choice_meta.search(description))
                    for choice in ("a", "b", "c"):
                        button = values[f"{prefix}.{choice}"]
                        button_core = re.sub(
                            r"(?:（仅记账）| \(ledger only\))[。！？.!?]?$",
                            "",
                            button,
                        ).rstrip("。！？；.!?; ")
                        self.assertIsNone(generic_button.fullmatch(button.strip()))
                        self.assertNotIn(button_core.casefold(), description.casefold())
                        if language == "simp_chinese":
                            self.assertFalse(button_core.endswith("后"))

        chinese = localization_values(self.mechanisms, "simp_chinese")
        descriptions = [
            chinese[f"zg361m.{mechanism.id}.desc"]
            for mechanism in self.mechanisms
        ]
        self.assertEqual(len(set(descriptions)), MECHANISM_COUNT)
        joined = "\n".join(chinese.values())
        for malformed in (
            "责任责任人",
            "编号 发奖",
            "经理人工 调整权限 预算",
            "穷尽私下沟通和正式申诉后。",
        ):
            with self.subTest(malformed=malformed):
                self.assertNotIn(malformed, joined)
        for mechanism in self.mechanisms:
            description = chinese[f"zg361m.{mechanism.id}.desc"]
            with self.subTest(mechanism=mechanism.id, field="source-copy"):
                self.assertNotIn(
                    naturalize_mechanism_chinese(mechanism.title_cn),
                    description,
                )
                self.assertNotIn(
                    naturalize_mechanism_chinese(mechanism.decision_cn),
                    description,
                )

    def test_machine_manifest_maps_every_id(self) -> None:
        manifest_path = MOD_ROOT / "docs" / "361-mechanism-manifest.json"
        manifest = json.loads(self.rendered[manifest_path].decode("utf-8"))
        self.assertEqual(manifest["schema"], 5)
        self.assertEqual(manifest["mechanism_count"], 361)
        self.assertEqual(manifest["runtime_plan"]["coverage"], 361)
        self.assertEqual(manifest["runtime_plan"]["domain_count"], 38)
        self.assertIn("does not change domain_runtime", manifest["runtime_plan"]["claim_boundary"])
        self.assertEqual([item["id"] for item in manifest["items"]], list(range(1, 362)))
        self.assertEqual({item["live_wave"] for item in manifest["items"]}, {1, 2, 3, 4})
        phase2_ids = {int(mechanism_id) for mechanism_id in PHASE2_RUNTIME_SPECS}
        mechanisms_by_id = {mechanism.id: mechanism for mechanism in self.mechanisms}
        for item in manifest["items"]:
            self.assertEqual(len(item["implementation"]["choice_effects"]), 3)
            self.assertEqual(item["runtime_plan"]["status"], "contract-complete")
            self.assertNotIn("case.transition", item["runtime_plan"]["primitive_recipe"])
            self.assertEqual(
                item["runtime_plan"]["transition_owner"],
                "stage_dispatcher",
            )
            self.assertEqual(set(item["runtime_plan"]["choice_transitions"]), {"a", "b", "c"})
            self.assertIn("not a claim", item["runtime_plan"]["claim_boundary"])
            record = READINESS_BY_ID[item["id"]]
            expected_evidence = {
                ReadinessLevel.DESIGN_ONLY: "none",
                ReadinessLevel.PYTHON_L0: "python-l0",
                ReadinessLevel.CK3_STATIC_READY: "static-ready",
                ReadinessLevel.CENTRAL_WIRED: "static-ready",
                ReadinessLevel.CK3_LIVE: "fixture-live",
            }[record.level]
            self.assertEqual(
                item["status"]["domain_runtime"],
                "partial"
                if record.level >= ReadinessLevel.CK3_STATIC_READY
                else "not-implemented",
            )
            self.assertEqual(item["status"]["runtime_evidence"], expected_evidence)
            self.assertEqual(item["readiness"], record.manifest_payload())
            self.assertNotIsInstance(item["status"], str)
            if item["id"] in phase2_ids:
                self.assertIsInstance(item["runtime_contract"], dict)
                self.assertEqual(
                    set(item["runtime_contract"]),
                    {
                        "object_type",
                        "owner_binding",
                        "subject_binding",
                        "cycle_binding",
                        "case_binding",
                        "hook",
                        "states",
                        "feedback",
                        "permissions",
                    },
                )
            else:
                self.assertNotIn("runtime_contract", item)
            self.assertEqual(
                tuple(item["acceptance_contract"]), ACCEPTANCE_FIELDS
            )
            self.assertEqual(
                item["acceptance_contract"],
                mechanisms_by_id[item["id"]].acceptance_contract.manifest_payload(),
            )
        self.assertEqual(
            manifest["acceptance"]["run_id"],
            "zga_20260829_061314_ea5f04ad",
        )
        self.assertIn(
            "1083",
            manifest["acceptance"]["claim_boundary"],
        )
        static_ids = list(ids_at_least(ReadinessLevel.CK3_STATIC_READY))
        self.assertEqual(manifest["phase2_static"]["mechanism_ids"], static_ids)
        self.assertEqual(
            manifest["phase2_static"]["count"],
            CUMULATIVE_COUNTS["ck3-static-ready"],
        )
        self.assertEqual(
            manifest["phase2_static"]["evidence"],
            "at-least-ck3-static-ready",
        )
        self.assertEqual(
            manifest["readiness"]["cumulative_counts"],
            dict(CUMULATIVE_COUNTS),
        )
        self.assertIn(
            "do not prove complete semantics",
            manifest["phase2_static"]["claim_boundary"],
        )

    def test_checked_in_projection_is_current(self) -> None:
        stale = [
            path.relative_to(MOD_ROOT).as_posix()
            for path, expected in self.rendered.items()
            if not path.is_file() or path.read_bytes() != expected
        ]
        self.assertEqual(stale, [])


if __name__ == "__main__":
    sys.exit(unittest.main())
