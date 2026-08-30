#!/usr/bin/env python3
"""Static contract for the clean, real-character ZhongGuo promo fixture."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tools" / "fixtures" / "zg361_acceptance"
DECISIONS = FIXTURE / "common" / "decisions" / "zga_decisions.txt"
MODIFIERS = FIXTURE / "common" / "modifiers" / "zga_modifiers.txt"
EFFECTS = FIXTURE / "common" / "scripted_effects" / "zga_effects.txt"
EVENTS = FIXTURE / "events" / "zga_events.txt"
SIMP_CHINESE = FIXTURE / "localization" / "simp_chinese" / "zga_l_simp_chinese.yml"
ENGLISH = FIXTURE / "localization" / "english" / "zga_l_english.yml"
BOM = b"\xef\xbb\xbf"
POLICY_CHAIN = (
    (6, 1, 7),
    (7, 7, 8),
    (8, 20, 9),
    (9, 22, 10),
    (10, 26, 11),
    (11, 361, 12),
)
HISTORICAL_CANDIDATES = (
    ("han_6875", "k_hedong", "唐介"),
    ("han_6747", "k_jiangxi", "赵承亮"),
    ("han_6442", "k_shannan", "曾公亮"),
    ("han_5253", "k_hunan", "吕居简"),
    ("han_6680", "k_xichuan", "程瑜"),
    ("han_6071", "k_xingyuan", "陈贯"),
    ("han_6762", "k_dongchuan", "范纯诚"),
    ("han_90011", "k_kuizhou", "张诜"),
    ("han_6444", "k_lingnan", "石待用"),
    ("han_6162", "k_lingxi", "杨完"),
    ("han_6465", "k_jiangdong", "王端"),
    ("han_6963", "k_liangzhe", "蔡襄"),
    ("han_6547", "k_fujian", "韩纲"),
    ("han_6443", "k_huainan", "梁适"),
    ("han_20000", "k_qingxu", "卢士宗"),
    ("han_6774", "k_hebei", "晁宗恪"),
    ("han_50001", "k_guannei", "李参"),
    ("han_6318", "k_henan", "赵从诲"),
    ("han_7247", "c_shanzhou", "陆琪"),
    ("han_6928", "c_bozhou", "施辩"),
    ("han_6927", "c_yingzhou", "吴中复"),
)
PROMO_ASSESSOR_CANDIDATES = HISTORICAL_CANDIDATES[:18]


def bom_text(path: Path) -> str:
    payload = path.read_bytes()
    assert payload.startswith(BOM), f"missing UTF-8 BOM: {path}"
    return payload.decode("utf-8-sig")


def top_level_block(text: str, key: str) -> str:
    match = re.search(rf"(?m)^{re.escape(key)}\s*=\s*\{{", text)
    assert match is not None, f"missing block {key}"
    start = match.start()
    opening = text.index("{", match.start(), match.end())
    depth = 0
    quoted = False
    escaped = False
    for index in range(opening, len(text)):
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
                return text[start : index + 1]
    raise AssertionError(f"unterminated block {key}")


def main() -> int:
    # All CK3 fixture scripts/localization remain loadable as UTF-8 BOM files.
    fixture_files = (
        tuple(FIXTURE.rglob("*.txt"))
        + tuple(FIXTURE.rglob("*.gui"))
        + tuple(FIXTURE.rglob("*.yml"))
    )
    assert fixture_files
    for path in fixture_files:
        bom_text(path)

    decisions = bom_text(DECISIONS)
    modifiers = bom_text(MODIFIERS)
    effects = bom_text(EFFECTS)
    events = bom_text(EVENTS)
    simp_chinese = bom_text(SIMP_CHINESE)
    english = bom_text(ENGLISH)

    health_guard = top_level_block(
        modifiers, "zga_acceptance_recording_health_guard"
    )
    assert modifiers.count("zga_acceptance_recording_health_guard = {") == 1
    assert "icon = health_positive" in health_guard
    assert "health = 10" in health_guard
    for localization in (simp_chinese, english):
        assert "zga_acceptance_recording_health_guard:0" in localization
        assert "zga_acceptance_recording_health_guard_desc:0" in localization

    decision_ids = re.findall(r"(?m)^(zga_[a-z0-9_]+_decision)\s*=", decisions)
    assert decision_ids == [
        "zga_initialize_decision",
        "zga_personal_result_decision",
        "zga_jingcha_planner_decision",
        "zga_promo_policy_001_decision",
        "zga_promo_policy_007_decision",
        "zga_promo_policy_020_decision",
        "zga_promo_policy_022_decision",
        "zga_promo_policy_026_decision",
        "zga_promo_policy_361_decision",
    ]
    assert (
        "is_shown = { always = no }"
        not in top_level_block(decisions, "zga_initialize_decision")
    )
    for decision_id in decision_ids[1:]:
        body = top_level_block(decisions, decision_id)
        assert "is_shown = { always = no }" in body, decision_id
    assert decisions.count("is_shown = { always = no }") == len(decision_ids) - 1

    initialize = top_level_block(effects, "zga_initialize_effect")
    personal = top_level_block(effects, "zga_personal_result_effect")
    verify_board = top_level_block(effects, "zga_verify_player_review_effect")
    phase2_receipt_probe = top_level_block(
        effects, "zga_verify_penalty_and_appeal_effect"
    )
    assert "zg361_compute_kpi_effect = yes" in phase2_receipt_probe
    assert "zg361_apply_grade_effect = yes" in phase2_receipt_probe
    assert "zg361_grade_325_apply_effect = yes" not in phase2_receipt_probe
    assert "ZGA: TEST PASS phase2_case_facts_and_quota_reason_frozen" in phase2_receipt_probe
    assert "ZGA: TEST PASS phase2_delivery_and_receipt_idempotent" in phase2_receipt_probe
    assert "zg361_appeal_regrade_to_35_effect = yes" in phase2_receipt_probe
    assert "character:han_8052" in initialize
    assert len(
        re.findall(
            r"(?m)^\s*modifier = zga_acceptance_recording_health_guard\s*$",
            initialize,
        )
    ) == 1
    assert initialize.count("days = 120") == 1
    assert initialize.count("ZGA: TEST PASS recording_health_guard_applied") == 1
    assert initialize.index(
        "modifier = zga_acceptance_recording_health_guard"
    ) < initialize.index("set_player_character = scope:zga_song_emperor")
    assert personal.count(
        "remove_character_modifier = zga_acceptance_recording_health_guard"
    ) == 1
    assert personal.count(
        "ZGA: TEST PASS recording_health_guard_removed_before_switch"
    ) == 1
    assert personal.index(
        "remove_character_modifier = zga_acceptance_recording_health_guard"
    ) < personal.index("set_player_character = scope:zga_personal_result_target")
    candidate_ids = tuple(row[0] for row in HISTORICAL_CANDIDATES)
    assessor_ids = tuple(row[0] for row in PROMO_ASSESSOR_CANDIDATES)
    candidate_calls = tuple(
        re.findall(
            r"character:(han_[0-9]+)\s*=\s*\{\s*"
            r"zga_mark_historical_song_direct_candidate_effect\s*=\s*yes\s*\}",
            initialize,
        )
    )
    assert candidate_calls == candidate_ids
    assert len(candidate_ids) == len(set(candidate_ids)) == 21
    assert len({row[1] for row in HISTORICAL_CANDIDATES}) == 21
    assert all(row[2] for row in HISTORICAL_CANDIDATES)
    assert "ZGA: TEST PASS historical_song_direct_whitelist_complete" in initialize
    assert "ZGA: TEST PASS generated_city_officials_excluded_from_provenance" in initialize
    assert "ZGA: TEST FAIL historical_song_direct_whitelist_incomplete" in initialize
    assert "ordered_vassal" in personal
    assert "order_by = var:zg361_rank" in personal
    assert "has_character_flag = zga_historical_song_direct_candidate" in personal
    assert personal.count("zg361_is_celestial_liege_trigger = yes") >= 3
    assert "var:zg361_rank = root.var:zg361_cohort_n" not in personal
    assert "var:zg361_rank > scope:zga_personal_result_target.var:zg361_rank" in personal
    assert "liege = root" in personal
    assert "zg361_is_current_liege_review_record_trigger = yes" in personal
    assert (
        "ZGA: TEST PASS personal_result_target_selected_from_prior_historical_assessor_tail"
        in personal
    )
    assert "ZGA: TEST PASS personal_result_target_can_assess_others" in personal
    assert personal.count(
        'debug_log = "ZGA: TEST PASS historical_personal_result_target"'
    ) == 1
    assert personal.count(
        'debug_log = "ZGA: TEST FAIL historical_personal_result_target"'
    ) == 1
    data_ids = tuple(
        re.findall(
            r'ZGA: DATA historical_personal_result_target (han_[0-9]+)"', personal
        )
    )
    assert data_ids == assessor_ids
    for history_id in assessor_ids:
        assert f"limit = {{ this = character:{history_id} }}" in personal
        assert personal.count(
            f'ZGA: DATA historical_personal_result_target {history_id}"'
        ) == 1
    for history_id in candidate_ids[18:]:
        assert f"ZGA: DATA historical_personal_result_target {history_id}" not in personal
    assert personal.index(
        'ZGA: TEST PASS historical_personal_result_target"'
    ) > personal.rindex("ZGA: DATA historical_personal_result_target ")
    for variable in ("zg361_rank", "zg361_pending_grade", "zg361_last_grade"):
        assert f"set_variable = {{ name = {variable}" not in personal
    assert (
        "zg361_kpi_value <= scope:zga_personal_result_target.zg361_kpi_value"
        in personal
    )
    assert personal.count(
        "ZGA: TEST PASS personal_result_target_projected_bottom_two"
    ) == 1
    assert personal.count(
        "ZGA: TEST FAIL personal_result_target_not_projected_bottom_two"
    ) == 1
    for identifier in (1, 7, 20, 22, 26, 361):
        assert f"remove_variable = zg361_mechanism_{identifier:03d}_choice" in personal

    assert "trigger_event = { id = zga_acceptance.5 days = 10 }" in verify_board
    assert "Product Jingcha cadence is unchanged" in verify_board
    assert "ZGA: TEST PASS clean_jingcha_dispatch_scheduled" in verify_board

    personal_settlement = top_level_block(events, "zga_acceptance.2")
    assert "every_vassal" in personal_settlement
    assert "var:zga_personal_result_target_n = 1" in personal_settlement
    assert "has_character_flag = zga_historical_song_direct_candidate" in personal_settlement
    assert "zg361_is_celestial_liege_trigger = yes" in personal_settlement
    assert "character:han_5253 = { save_scope_as = zga_personal_result_target }" not in personal_settlement
    assert "random_vassal" in personal_settlement  # optional real small-cohort probe remains
    assert "trigger_event = { id = zga_acceptance.13 days = 8 }" in personal_settlement
    assert "var:zg361_result_case_state = 1" in personal_settlement
    assert "NOT = { has_character_modifier = zg361_grade_325 }" in personal_settlement
    assert "var:zg361_result_settlement_posted_serial = 0" in personal_settlement
    assert "var:zg361_result_refund_posted_serial = 0" in personal_settlement
    assert "NOT = { has_variable = zg361_result_settlement_posted_serial }" not in personal_settlement
    assert "ZGA: TEST PASS phase2_player_325_prepared_without_early_penalty" in personal_settlement

    refusal_verifier = top_level_block(events, "zga_acceptance.13")
    assert "hidden = yes" in refusal_verifier
    assert "var:zg361_result_case_state = 3" in refusal_verifier
    assert "var:zg361_result_delivery_method = 3" in refusal_verifier
    assert "var:zg361_result_settlement_posted_serial = var:zg361_result_case_serial" in refusal_verifier
    assert "ZGA: TEST PASS phase2_refused_notice_witnessed_and_settled" in refusal_verifier
    assert "zg361_deliver_325_notice_effect = yes" in refusal_verifier
    assert "zg361_settle_delivered_325_effect = yes" in refusal_verifier
    assert "ZGA: TEST PASS phase2_refused_delivery_receipt_idempotent" in refusal_verifier
    assert "trigger_event = { id = zga_acceptance.6 days = 3 }" in refusal_verifier
    assert "shipped 3.25 elimination follow-up zg361.6 arrives at D+2" in refusal_verifier
    assert "ZGA: TEST PASS clean_policy_chain_scheduled" in refusal_verifier

    jingcha = top_level_block(events, "zga_acceptance.5")
    assert "hidden = yes" in jingcha
    assert "this = character:han_8052" in jingcha
    assert "trigger_event = zg361.40" in jingcha
    assert "trigger_event = { id = zga_acceptance.3 days = 90 }" in jingcha
    assert "Jingcha timing is not changed" in jingcha
    assert "ZGA: TEST PASS clean_jingcha_dispatched" in jingcha
    assert "ZGA: TEST PASS jingcha_mandate_issued" in jingcha

    previous_mechanism_id = None
    for carrier_id, mechanism_id, successor_id in POLICY_CHAIN:
        body = top_level_block(events, f"zga_acceptance.{carrier_id}")
        assert "hidden = yes" in body
        assert "has_character_flag = zga_historical_song_direct_candidate" in body
        assert "this = character:han_5253" not in body
        assert "has_character_flag = zga_clean_policy_chain_subject" in body
        if previous_mechanism_id is not None:
            assert (
                f"has_variable = zg361_mechanism_{previous_mechanism_id:03d}_choice"
                in body
            )
        assert f"NOT = {{ has_variable = zg361_mechanism_{mechanism_id:03d}_choice }}" in body
        marker = f'ZGA: TEST PASS clean_policy_{mechanism_id:03d}_dispatched'
        product = f"trigger_event = zg361m.{mechanism_id}"
        assert marker in body
        assert product in body
        if mechanism_id == 1:
            init = "zg361_init_org_ledger_effect = yes"
            assert body.count(init) == 1
            assert body.index(init) < body.index(marker)
            assert body.index(init) < body.index(product)
        if successor_id is not None:
            successor = f"trigger_event = {{ id = zga_acceptance.{successor_id} days = 1 }}"
            assert successor in body
            assert body.index(successor) < body.index(product)
        previous_mechanism_id = mechanism_id

    final_dispatch = top_level_block(events, "zga_acceptance.11")
    assert "add_character_flag = zga_clean_policy_completion_pending" in final_dispatch
    assert "remove_character_flag = zga_clean_policy_chain_subject" in final_dispatch
    assert "ZGA: TEST PASS clean_policy_chain_all_six_dispatched" in final_dispatch

    completion = top_level_block(events, "zga_acceptance.12")
    assert "hidden = yes" in completion
    assert "has_character_flag = zga_historical_song_direct_candidate" in completion
    assert "this = character:han_5253" not in completion
    assert "has_character_flag = zga_clean_policy_completion_pending" in completion
    for identifier in (1, 7, 20, 22, 26, 361):
        assert f"has_variable = zg361_mechanism_{identifier:03d}_choice" in completion
    assert "remove_character_flag = zga_clean_policy_completion_pending" in completion
    assert "ZGA: TEST PASS clean_policy_chain_completed" in completion
    assert "ZGA: TEST FAIL clean_policy_chain_completed" in completion

    # The external fixture may precondition real history characters, but it may
    # never manufacture characters, titles, or relations for promo provenance.
    fixture_text = "\n".join(bom_text(path) for path in fixture_files)
    forbidden_construction = (
        "create_character",
        "create_title",
        "grant_title",
        "set_father",
        "set_mother",
        "set_spouse",
        "add_relation",
        "set_relation",
    )
    for token in forbidden_construction:
        assert re.search(rf"\b{re.escape(token)}\b", fixture_text) is None, token

    print("GREEN: ZhongGuo clean promo fixture and real-character provenance contracts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
