#!/usr/bin/env python3
"""Static contract for the clean, real-character ZhongGuo promo fixture."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tools" / "fixtures" / "zg361_acceptance"
DECISIONS = FIXTURE / "common" / "decisions" / "zga_decisions.txt"
EFFECTS = FIXTURE / "common" / "scripted_effects" / "zga_effects.txt"
EVENTS = FIXTURE / "events" / "zga_events.txt"
BOM = b"\xef\xbb\xbf"
POLICY_CHAIN = (
    (6, 1, 7),
    (7, 7, 8),
    (8, 20, 9),
    (9, 22, 10),
    (10, 26, 11),
    (11, 361, 12),
)


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
    effects = bom_text(EFFECTS)
    events = bom_text(EVENTS)

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
    assert "character:han_8052" in initialize
    assert "character:han_5253" in initialize
    assert initialize.count("NOT = { this = character:han_5253 }") == 2
    assert "character:han_5253 = { save_scope_as = zga_personal_result_target }" in personal
    assert "ordered_vassal" not in personal
    assert "liege = root" in personal
    assert "zg361_is_current_liege_review_record_trigger = yes" in personal
    assert "ZGA: TEST PASS historical_personal_result_target_han_5253" in personal
    assert "ZGA: TEST FAIL historical_personal_result_target_han_5253" in personal
    for identifier in (1, 7, 20, 22, 26, 361):
        assert f"NOT = {{ has_variable = zg361_mechanism_{identifier:03d}_choice }}" in personal

    assert "trigger_event = { id = zga_acceptance.5 days = 2 }" in verify_board
    assert "ZGA: TEST PASS clean_jingcha_dispatch_scheduled" in verify_board

    personal_settlement = top_level_block(events, "zga_acceptance.2")
    assert "character:han_5253 = { save_scope_as = zga_personal_result_target }" in personal_settlement
    assert "random_vassal" in personal_settlement  # optional real small-cohort probe remains
    assert "trigger_event = { id = zga_acceptance.6 days = 2 }" in personal_settlement
    assert "ZGA: TEST PASS clean_policy_chain_scheduled" in personal_settlement

    jingcha = top_level_block(events, "zga_acceptance.5")
    assert "hidden = yes" in jingcha
    assert "this = character:han_8052" in jingcha
    assert "trigger_event = zg361.40" in jingcha
    assert "trigger_event = { id = zga_acceptance.3 days = 2 }" in jingcha
    assert "ZGA: TEST PASS clean_jingcha_dispatched" in jingcha
    assert "ZGA: TEST PASS jingcha_mandate_issued" in jingcha

    previous_mechanism_id = None
    for carrier_id, mechanism_id, successor_id in POLICY_CHAIN:
        body = top_level_block(events, f"zga_acceptance.{carrier_id}")
        assert "hidden = yes" in body
        assert "this = character:han_5253" in body
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
    assert "this = character:han_5253" in completion
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
