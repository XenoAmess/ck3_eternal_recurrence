#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L0 contracts for the isolated Workforce attribution-signature package.

These tests prove deterministic generation and static CK3 source contracts.
They do not claim loader, paused-snapshot or live-game evidence.
"""

from __future__ import annotations

from pathlib import Path
import re
import unittest

import gen_zg361_workforce_attribution_fact as generator


MOD_ROOT = Path(__file__).resolve().parents[1]
PREFIX = generator.PREFIX
NAMESPACE = generator.NAMESPACE
EFFECTS_PATH = MOD_ROOT / "common/scripted_effects" / f"{PREFIX}_effects.txt"
EVENTS_PATH = MOD_ROOT / "events" / f"{PREFIX}_events.txt"
SPEC_PATH = MOD_ROOT / "docs/zg361_workforce_attribution_fact_runtime_spec.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def block(text: str, name: str) -> str:
    match = re.search(rf"(?m)^{re.escape(name)} = \{{", text)
    if match is None:
        raise AssertionError(f"missing block: {name}")
    start = match.start()
    brace = text.find("{", start)
    depth = 0
    quoted = False
    escaped = False
    for index in range(brace, len(text)):
        char = text[index]
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
            continue
        if char == '"':
            quoted = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start:index + 1]
    raise AssertionError(f"unbalanced block: {name}")


class WorkforceAttributionFactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.effects = read(EFFECTS_PATH)
        cls.events = read(EVENTS_PATH)
        cls.spec = read(SPEC_PATH) if SPEC_PATH.is_file() else ""

    def test_01_policy_table_conserves_and_preserves_slot_order(self) -> None:
        self.assertEqual(
            {
                1: (6000, 2000, 2000),
                2: (2000, 6000, 2000),
                3: (2000, 2000, 6000),
            },
            generator.ALLOCATION_POLICIES,
        )
        for policy, shares in generator.ALLOCATION_POLICIES.items():
            self.assertEqual(10000, sum(shares))
            self.assertEqual(6000, shares[policy - 1])

    def test_02_ai_rule_is_first_highest_and_rejects_unsealed_values(self) -> None:
        vectors = {
            (3, 2, 1): 1,
            (1, 3, 2): 2,
            (1, 2, 3): 3,
            (3, 3, 1): 1,
            (1, 3, 3): 2,
            (2, 2, 2): 1,
        }
        for votes, expected in vectors.items():
            self.assertEqual(expected, generator.select_ai_policy(votes), votes)
        for invalid in ((0, 2, 3), (1, 2, 4), (1, 2), (1, 2, 3, 1)):
            with self.assertRaises(ValueError):
                generator.select_ai_policy(invalid)  # type: ignore[arg-type]

    def test_03_generator_owns_only_new_projection_files(self) -> None:
        rendered = generator.outputs()
        self.assertEqual(11, len(rendered))
        self.assertEqual({EFFECTS_PATH, EVENTS_PATH}, {path for path in rendered if path.suffix == ".txt"})
        for path, payload in rendered.items():
            self.assertTrue(path.name.startswith(PREFIX))
            self.assertTrue(payload.startswith(generator.BOM))
            self.assertEqual(payload, path.read_bytes(), path)
        self.assertNotIn(MOD_ROOT / "tools/gen_361_workforce_endgame_runtime.py", rendered)
        self.assertNotIn(MOD_ROOT / "tools/gen_zg361_workforce_probation_fact.py", rendered)

    def test_04_generated_ck3_blocks_are_balanced(self) -> None:
        for name, text in (("effects", self.effects), ("events", self.events)):
            self.assertEqual(text.count("{"), text.count("}"), name)

    def test_05_arm_waits_for_real_native_m274_appointment(self) -> None:
        begin = block(self.effects, f"{PREFIX}_begin_signature_effect")
        for token in (
            "EXPECTED_STATE = 4",
            "m267_business_object_created = 1",
            "m267_object_type_code = 267",
            "m267_object_consumed = 1",
            "m267_consumer_seal_interview_votes_267 = 1",
            "m272_business_object_created = 1",
            "m272_object_type_code = 272",
            "m272_object_consumed = 1",
            "m272_consumer_issue_offer_272 = 1",
            "m274_business_object_created = 1",
            "m274_object_type_code = 274",
            "m274_object_state = 4",
            "m274_object_consumed = 1",
            "m274_consumer_resolve_counteroffer_274 = 1",
            "m274_hired = 1",
            "m274_native_appointment_confirmed = 1",
            "m274_position_receipt_id > 0",
            "m274_position_receipt_hash > 0",
        ):
            self.assertIn(token, begin)
        self.assertNotIn("EXPECTED_STATE = 3", begin)

    def test_06_arm_joins_typed_manifests_and_operation_receipts(self) -> None:
        begin = block(self.effects, f"{PREFIX}_begin_signature_effect")
        for token in (
            "m267_object_interview_ballot = 1",
            "m267_consumer_contract = 267",
            "m267_resource_interview = 1",
            "m267_resource_evidence = 1",
            "m267_receipt_choice = var:zg361_we_m267_choice",
            "m272_object_offer = 1",
            "m272_consumer_contract = 272",
            "m272_resource_gold = 1",
            "m272_resource_offer = 1",
            "m272_resource_promotion = 1",
            f"m272_object_due_cycle = scope:{PREFIX}_expected_due_cycle",
            "m272_receipt_choice = var:zg361_we_m272_choice",
            "m274_object_counteroffer = 1",
            "m274_consumer_contract = 274",
            "m274_resource_gold = 1",
            "m274_resource_offer = 1",
            "m274_resource_formal_hc = 1",
            "m274_receipt_choice = 1",
            "m274_position_type_id > 0",
            f"m274_probation_due_cycle = scope:{PREFIX}_expected_due_cycle",
        ):
            self.assertIn(token, begin)
        for mid, state in ((267, 1), (272, 3), (274, 4)):
            for field in ("owner", "subject", "cycle", "case", "state", "choice"):
                self.assertIn(f"has_variable = zg361_we_m{mid}_receipt_{field}", begin)
            self.assertIn(f"m{mid}_receipt_state = {state}", begin)

    def test_07_arm_joins_exact_business_object_ids_and_final_approver(self) -> None:
        begin = block(self.effects, f"{PREFIX}_begin_signature_effect")
        for mid in (267, 272, 274):
            self.assertIn(f"expected_m{mid}_object_id", begin)
            self.assertIn(f"add = {mid}", begin)
            self.assertIn(f"m{mid}_object_id = scope:{PREFIX}_expected_m{mid}_object_id", begin)
        self.assertIn("m272_offer_candidate = $TICKET_SUBJECT$", begin)
        self.assertIn("m272_offer_approver = $TICKET_OWNER$", begin)
        self.assertIn("m272_offer_approver = { zg361_is_celestial_liege_trigger = yes }", begin)
        self.assertIn(f"final_approver value = var:zg361_we_m272_offer_approver", begin)

    def test_08_three_real_interviewers_votes_and_evidence_are_frozen(self) -> None:
        begin = block(self.effects, f"{PREFIX}_begin_signature_effect")
        self.assertIn("m267_raw_votes_frozen = 1", begin)
        self.assertIn("m267_vote_count = 3", begin)
        self.assertIn("m267_evidence_count = 3", begin)
        for slot in (1, 2, 3):
            self.assertIn(f"has_variable = zg361_we_m267_interviewer_{slot}", begin)
            self.assertIn(f"has_variable = zg361_we_m267_vote_{slot}", begin)
            self.assertIn(f"has_variable = zg361_we_m267_vote_evidence_{slot}", begin)
            self.assertIn(f"m267_vote_{slot} >= 1", begin)
            self.assertIn(f"m267_vote_{slot} <= 3", begin)
            self.assertIn(f"m267_vote_evidence_{slot} > 0", begin)
            self.assertIn(f"interviewer_{slot} value = var:zg361_we_m267_interviewer_{slot}", begin)
            self.assertIn(f"evidence_{slot} value = var:zg361_we_m267_vote_evidence_{slot}", begin)
        self.assertEqual(3, begin.count("NOT = { var:zg361_we_m267_interviewer_"))
        self.assertEqual(3, begin.count("NOT = { var:zg361_we_m267_vote_evidence_"))

    def test_09_player_event_is_final_approver_owned_and_explicit(self) -> None:
        event = block(self.events, f"{NAMESPACE}.1")
        self.assertIn("is_ai = no", event)
        self.assertIn("theme = vassal", event)
        self.assertIn(f"this = scope:{PREFIX}_approver_scope", event)
        self.assertIn(f"var:{PREFIX}_final_approver = root", event)
        for policy, shares in generator.ALLOCATION_POLICIES.items():
            self.assertIn(f"name = {NAMESPACE}.1.option_{policy}", event)
            self.assertIn(f"SIGNER = root POLICY = {policy}", event)
            self.assertIn(f"LEAD = scope:{PREFIX}_interviewer_{policy}_scope", event)
            self.assertIn(
                f"BPS_1 = {shares[0]} BPS_2 = {shares[1]} BPS_3 = {shares[2]}",
                event,
            )
            self.assertIn("SIGNATURE_MODE = 1 TIE_RULE = 0", event)
            self.assertIn("hidden_effect = {", event)
        self.assertEqual(3, event.count(f"{PREFIX}_sign_effect"))

    def test_10_arm_dispatch_is_a_hidden_next_frame_boundary(self) -> None:
        begin = block(self.effects, f"{PREFIX}_begin_signature_effect")
        carrier = block(self.events, f"{NAMESPACE}.2")
        self.assertIn(f"name = {PREFIX}_signature_pending value = 1 }} # arm commit marker is last", begin)
        self.assertIn(f"trigger_event = {{ id = {NAMESPACE}.2 days = 1 }}", begin)
        self.assertNotIn(f"{PREFIX}_dispatch_signature_effect = yes", begin)
        self.assertIn("hidden = yes", carrier)
        self.assertIn(f"has_variable = {PREFIX}_signature_pending", carrier)
        self.assertIn(f"var:{PREFIX}_signature_pending = 1", carrier)
        self.assertIn(f"{PREFIX}_dispatch_signature_effect = yes", carrier)

    def test_11_ai_uses_only_sealed_votes_with_documented_ties(self) -> None:
        ai = block(self.effects, f"{PREFIX}_resolve_ai_signature_effect")
        self.assertIn("$SIGNER$ = { is_ai = yes zg361_is_celestial_liege_trigger = yes }", ai)
        self.assertIn(f"vote_1 >= var:{PREFIX}_vote_2", ai)
        self.assertIn(f"vote_1 >= var:{PREFIX}_vote_3", ai)
        self.assertIn(f"vote_2 >= var:{PREFIX}_vote_1", ai)
        self.assertIn(f"vote_2 >= var:{PREFIX}_vote_3", ai)
        self.assertIn(f"vote_3 > var:{PREFIX}_vote_1", ai)
        self.assertIn(f"vote_3 > var:{PREFIX}_vote_2", ai)
        self.assertEqual(3, ai.count("SIGNATURE_MODE = 2 TIE_RULE = 1"))
        self.assertNotRegex(ai, r"\brandom(?:_|\s*=)")
        self.assertNotIn("stewardship", ai)

    def test_12_signer_cannot_submit_an_arbitrary_or_equal_split(self) -> None:
        sign = block(self.effects, f"{PREFIX}_sign_effect")
        self.assertIn(f"scope:{PREFIX}_submitted_total_bps = 10000", sign)
        for policy, shares in generator.ALLOCATION_POLICIES.items():
            self.assertIn(f"$POLICY$ = {policy}", sign)
            self.assertIn(f"$BPS_{policy}$ = 6000", sign)
            for slot, share in enumerate(shares, 1):
                self.assertIn(f"$BPS_{slot}$ = {share}", sign)
            self.assertIn(f"var:{PREFIX}_interviewer_{policy} = $LEAD$", sign)
        self.assertNotIn("3333", sign)
        self.assertNotIn("3334", sign)
        self.assertNotIn("random", sign)
        self.assertIn("$SIGNATURE_MODE$ = 1 $TIE_RULE$ = 0 $SIGNER$ = { is_ai = no }", sign)
        self.assertIn("$SIGNATURE_MODE$ = 2 $TIE_RULE$ = 1 $SIGNER$ = { is_ai = yes }", sign)

    def test_13_receipt_binds_actor_evidence_and_all_three_manifests(self) -> None:
        sign = block(self.effects, f"{PREFIX}_sign_effect")
        for token in (
            "receipt_owner value",
            "receipt_subject value",
            "receipt_cycle value",
            "receipt_case value",
            "receipt_signer value = $SIGNER$",
            "receipt_policy_version value = 1",
            "receipt_policy_basis value = 1",
            "receipt_signature_mode value = $SIGNATURE_MODE$",
            "receipt_tie_rule value = $TIE_RULE$",
            "receipt_m267_object_id value",
            "receipt_m272_object_id value",
            "receipt_m274_object_id value",
            "receipt_m267_operation_choice value",
            "receipt_m272_operation_choice value",
            "receipt_m274_operation_choice value",
            "receipt_position_type_id value",
            "receipt_probation_due_cycle value",
            "receipt_appointment_id value",
            "receipt_appointment_hash value",
            "attribution_total_bps value",
            "receipt_id",
            "receipt_hash",
        ):
            self.assertIn(token, sign)
        for slot in (1, 2, 3):
            self.assertIn(f"receipt_interviewer_{slot} value = var:{PREFIX}_interviewer_{slot}", sign)
            self.assertIn(f"receipt_evidence_{slot} value = var:{PREFIX}_evidence_{slot}", sign)
        commit = f"set_variable = {{ name = {PREFIX}_signature_committed value = 1 }} # commit marker is last"
        self.assertEqual(1, sign.count(commit))
        initial_branch = sign[: sign.index("else_if = {")]
        business_writes = [line.strip() for line in initial_branch.splitlines() if "set_variable =" in line]
        self.assertEqual(commit, business_writes[-1])

    def test_14_exact_replay_does_not_issue_a_second_receipt(self) -> None:
        begin = block(self.effects, f"{PREFIX}_begin_signature_effect")
        sign = block(self.effects, f"{PREFIX}_sign_effect")
        self.assertIn(f"has_variable = {PREFIX}_signature_committed", begin)
        self.assertIn(f"var:{PREFIX}_signature_committed = 1", begin)
        self.assertIn(f"status value = 2", begin)
        replay = sign[sign.index("else_if = {"):]
        self.assertIn(f"status value = 2", replay)
        self.assertNotIn(f"name = {PREFIX}_receipt_id\n", replay)
        self.assertNotIn(f"name = {PREFIX}_receipt_hash\n", replay)

    def test_15_public_result_adapter_dispatches_without_same_chain_ack(self) -> None:
        publish = block(self.effects, f"{PREFIX}_publish_result_effect")
        header = self.effects[: self.effects.index(f"{PREFIX}_dispatch_signature_effect")]
        self.assertIn(f"{PREFIX}_publish_result_effect = {{ OWNER = <same AD owner> }}", header)
        self.assertNotIn("BPS_2 = <", header)
        self.assertIn(
            f"ATTRIBUTION_BPS_2 = var:{PREFIX}_attribution_bps_2",
            publish,
        )
        self.assertIn(
            f"ATTRIBUTION_BPS_3 = var:{PREFIX}_attribution_bps_3",
            publish,
        )
        self.assertIn("zg361_workforce_probation_fact_publish_from_result_effect", publish)
        self.assertIn(f"name = {PREFIX}_dispatch_committed value = 1 }} # dispatch receipt commit marker is last", publish)
        self.assertIn(f"trigger_event = {{ id = {NAMESPACE}.3 days = 1 }}", publish)
        self.assertIn(f"dispatch_result_settlement_receipt value = var:zg361_result_settlement_posted_serial", publish)
        self.assertIn("var:zg361_result_case_owner = $OWNER$", publish)
        self.assertNotIn("has_variable = zg361_workforce_probation_fact_state", publish)
        self.assertNotIn("var:zg361_workforce_probation_fact_state", publish)
        self.assertNotIn(f"name = {PREFIX}_consumed value = 1", publish)

    def test_16_probation_ack_is_hidden_d1_and_binds_full_result_tuple(self) -> None:
        ack = block(self.effects, f"{PREFIX}_ack_probation_publish_effect")
        event = block(self.events, f"{NAMESPACE}.3")
        self.assertIn("hidden = yes", event)
        self.assertIn(f"{PREFIX}_ack_probation_publish_effect = yes", event)
        for token in (
            "zg361_workforce_probation_fact_state",
            "zg361_workforce_probation_fact_adapter_status = 1",
            "zg361_workforce_probation_fact_source_result_owner",
            "zg361_workforce_probation_fact_source_result_cycle",
            "zg361_workforce_probation_fact_source_result_case",
            "zg361_workforce_probation_fact_source_result_state",
            "zg361_workforce_probation_fact_source_result_settlement_receipt",
            "zg361_workforce_probation_fact_source_result_grade",
            "zg361_workforce_probation_fact_source_result_reason",
            "zg361_workforce_probation_fact_source_result_kpi",
            "zg361_workforce_probation_fact_source_result_rank",
            "zg361_workforce_probation_fact_attribution_bps_1",
            "zg361_workforce_probation_fact_outcome_dimension_3",
            "zg361_workforce_probation_fact_attribution_receipt_id > 0",
            f"name = {PREFIX}_consumed value = 1 }} # consume marker is last",
        ):
            self.assertIn(token, ack)

    def test_17_route_c_has_an_exact_debt_cancellation_path(self) -> None:
        cancel = block(self.effects, f"{PREFIX}_cancel_from_m269_debt_effect")
        for token in (
            "m269_choice = 3",
            "m269_business_object_created = 0",
            "m269_debt_type_code = 269",
            "m269_debt_consumer_contract = 269",
            f"m269_debt_due_cycle = scope:{PREFIX}_expected_m269_debt_due_cycle",
            "m269_debt_escalation_count = 0",
            "m269_debt_open = 1",
            "m269_debt_consumed = 0",
            "m269_debt_visible_to_settlement = 1",
            "expected_m269_debt_id",
            "m269_receipt_owner = $OWNER$",
            "m269_receipt_subject = this",
            f"m269_receipt_cycle = var:{PREFIX}_cycle",
            f"m269_receipt_case = var:{PREFIX}_case",
            "m269_receipt_state = 5",
            "m269_receipt_choice = 3",
            "cancel_m269_receipt_choice value = var:zg361_we_m269_receipt_choice",
            "cancel_reason value = 1",
            "canceled value = 1",
            "consumed value = 1 } # cancel/consume marker is last",
        ):
            self.assertIn(token, cancel)
        self.assertNotIn("probation_fact_publish", cancel)

    def test_18_localization_is_zh_en_authored_with_seven_placeholders(self) -> None:
        en = read(MOD_ROOT / f"localization/english/{PREFIX}_l_english.yml")
        zh = read(MOD_ROOT / f"localization/simp_chinese/{PREFIX}_l_simp_chinese.yml")
        self.assertIn("exactly 10,000 basis points", en)
        self.assertIn("一万个基点", zh)
        self.assertNotEqual(en, zh)
        for language in generator.LANGUAGES:
            path = MOD_ROOT / "localization" / language / f"{PREFIX}_l_{language}.yml"
            self.assertTrue(path.read_bytes().startswith(generator.BOM), language)
            body = read(path)
            self.assertTrue(body.startswith(f"l_{language}:"), language)
            self.assertEqual(5, len(re.findall(rf"(?m)^ {re.escape(NAMESPACE)}\.", body)), language)
            if language not in {"english", "simp_chinese"}:
                self.assertEqual(
                    en.replace("l_english:", f"l_{language}:", 1),
                    body,
                    language,
                )

    def test_19_spec_is_honest_about_wiring_and_live_evidence(self) -> None:
        for token in (
            "static-ready/not-live",
            "下一事件/帧",
            "#274",
            "6000/2000/2000",
            "slot 1",
            "#269 route C",
            "loader",
            "paused snapshot",
        ):
            self.assertIn(token, self.spec)
        self.assertNotIn("production-live", self.spec)


if __name__ == "__main__":
    unittest.main()
