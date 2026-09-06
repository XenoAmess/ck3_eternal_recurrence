#!/usr/bin/env python3
"""Static contract for the acceptance-only player-manager seed fixture."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tools" / "fixtures" / "zg361_phase2_manager_seed_bootstrap"
BOM = b"\xef\xbb\xbf"


def text(path: Path) -> str:
    payload = path.read_bytes()
    assert payload.startswith(BOM), f"missing UTF-8 BOM: {path}"
    return payload.decode("utf-8-sig")


def top_level_block(payload: str, key: str) -> str:
    match = re.search(rf"(?m)^{re.escape(key)}\s*=\s*\{{", payload)
    assert match is not None, f"missing block {key}"
    opening = payload.index("{", match.start(), match.end())
    depth = 0
    quoted = False
    escaped = False
    for index in range(opening, len(payload)):
        char = payload[index]
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
                return payload[match.start() : index + 1]
    raise AssertionError(f"unterminated block {key}")


def main() -> int:
    assert FIXTURE.is_dir()
    assert not (FIXTURE / "common" / "decisions").exists()
    files = tuple(
        path
        for path in FIXTURE.rglob("*")
        if path.is_file()
        and path.suffix.lower() in {".txt", ".gui", ".yml", ".mod"}
    )
    assert files
    payload = "\n".join(text(path) for path in files)
    effects = text(
        FIXTURE
        / "common"
        / "scripted_effects"
        / "zga_phase2_manager_seed_effects.txt"
    )
    events = text(FIXTURE / "events" / "zga_phase2_manager_seed_events.txt")
    scripted_gui = text(
        FIXTURE
        / "common"
        / "scripted_guis"
        / "zga_phase2_manager_seed_scripted_guis.txt"
    )
    on_actions = text(
        FIXTURE
        / "common"
        / "on_action"
        / "zga_phase2_manager_seed_on_actions.txt"
    )
    bridge = text(FIXTURE / "gui" / "zga_phase2_manager_seed_bridge.gui")
    widgets = text(
        FIXTURE
        / "gui"
        / "scripted_widgets"
        / "zga_phase2_manager_seed_scripted_widgets.txt"
    )
    modifiers = text(
        FIXTURE
        / "common"
        / "modifiers"
        / "zga_phase2_manager_seed_modifiers.txt"
    )

    for gate in (
        "is_ai = no",
        "is_alive = yes",
        "is_landed = yes",
        "has_game_rule = zg361_on",
    ):
        assert gate in on_actions
        assert gate in effects
        assert gate in scripted_gui
    for manager_gate in (
        "zg361_is_celestial_liege_trigger = yes",
        "zg361_review_now_business_valid_trigger = yes",
        "prestige >= 150",
    ):
        assert manager_gate in on_actions
        assert manager_gate in effects
    assert "duration = 0.5" in bridge
    assert bridge.count("duration = 0.5") == 3
    assert (
        "GetScriptedGui('zga_phase2_manager_seed_bootstrap_bridge_gui')"
        in bridge
    )
    assert (
        "gui/zga_phase2_manager_seed_bridge.gui = "
        "zga_phase2_manager_seed_bridge_window" in widgets
    )
    for terminal_signal in (
        "this = character:han_6875",
        "var:zg361_b2_m015_state = 5",
        "var:zg361_b2_m015_object_active = 0",
        "var:zg361_b2_m015_object_consumed = 1",
        "var:zg361_b2_m015_object_subject = this",
        "var:zg361_b2_m015_object_owner = liege",
        "var:zg361_b2_pip_subject_response = 3",
    ):
        assert terminal_signal in scripted_gui
        assert terminal_signal in effects
    direct_gui = top_level_block(
        scripted_gui,
        "zga_phase2_manager_seed_direct_manager_diagnostic_gui",
    )
    assert (
        "NOT = { has_character_flag = "
        "zga_phase2_manager_seed_bootstrap_started }" in direct_gui
    )
    assert "zga_phase2_manager_seed_log_direct_gates_effect = yes" in direct_gui
    direct_gui_basic_gate = direct_gui[
        : direct_gui.index("\n\t\tNOT = {\n\t\t\tAND = {")
    ]
    assert "is_ai = no" in direct_gui_basic_gate
    assert "this = character:han_6875" not in direct_gui_basic_gate
    for final_gate in (
        "zg361_is_celestial_liege_trigger = yes",
        "zg361_review_now_business_valid_trigger = yes",
        "prestige >= 150",
        "has_character_flag = zg361_b1_cycle_active",
        "has_character_flag = zg361_review_in_progress",
        "has_variable = zg361_p2c_active",
        "has_variable = zg361_pp_portfolio_queue_active",
        "any_vassal = {",
    ):
        assert final_gate not in direct_gui_basic_gate
    assert (
        "GetScriptedGui('zga_phase2_manager_seed_direct_manager_diagnostic_gui')"
        in bridge
    )
    entry_gui = top_level_block(
        scripted_gui,
        "zga_phase2_manager_seed_direct_manager_entry_gui",
    )
    for entry_gate in (
        "is_ai = no",
        "is_alive = yes",
        "is_landed = yes",
        "has_character_modifier = "
        "zga_phase2_manager_seed_survivability_modifier",
        "zg361_is_celestial_liege_trigger = yes",
        "has_game_rule = zg361_on",
        "zg361_review_now_business_valid_trigger = yes",
        "prestige >= 150",
        "NOT = { has_character_flag = zg361_b1_cycle_active }",
        "NOT = { has_character_flag = zg361_review_in_progress }",
        "var:zg361_p2c_active != 1",
        "var:zg361_pp_portfolio_queue_active != 1",
        "any_vassal = {",
        "count >= 1",
        "zg361_is_reviewable_vassal_trigger = yes",
        "liege = root",
    ):
        assert entry_gate in entry_gui
    assert (
        "NOT = { has_character_flag = "
        "zga_phase2_manager_seed_bootstrap_started }" in entry_gui
    )
    assert (
        "NOT = { has_character_flag = "
        "zga_phase2_manager_seed_handoff_pending }" in entry_gui
    )
    assert "zga_phase2_manager_seed_maybe_begin_effect = yes" in entry_gui
    assert "set_player_character =" not in entry_gui
    assert (
        "GetScriptedGui('zga_phase2_manager_seed_direct_manager_entry_gui')"
        in bridge
    )
    diagnostic = top_level_block(
        effects,
        "zga_phase2_manager_seed_log_direct_gates_effect",
    )
    assert diagnostic.count(
        "add_character_flag = zga_phase2_manager_seed_direct_gates_logged"
    ) == 1
    assert (
        "NOT = { has_character_flag = "
        "zga_phase2_manager_seed_direct_gates_logged }" in diagnostic
    )
    diagnostic_flag_tokens = set(
        re.findall(
            r"(?:has_character_flag|add_character_flag)\s*=\s*"
            r"(zga_phase2_manager_seed_direct_[a-z_]+)",
            payload,
        )
    )
    assert diagnostic_flag_tokens == {
        "zga_phase2_manager_seed_direct_gates_logged"
    }
    diagnostic_gates = {
        "human": "is_ai = no",
        "alive": "is_alive = yes",
        "landed": "is_landed = yes",
        "celestial": "zg361_is_celestial_liege_trigger = yes",
        "game_rule": "has_game_rule = zg361_on",
        "review_now": "zg361_review_now_business_valid_trigger = yes",
        "prestige_150": "prestige >= 150",
        "b1_inactive": "NOT = { has_character_flag = zg361_b1_cycle_active }",
        "review_in_progress_inactive": (
            "NOT = { has_character_flag = zg361_review_in_progress }"
        ),
        "p2c_inactive": "var:zg361_p2c_active != 1",
        "pp_inactive": "var:zg361_pp_portfolio_queue_active != 1",
        "direct_reviewable_vassal": "any_vassal = {",
    }
    for gate_name, gate_expression in diagnostic_gates.items():
        assert gate_expression in diagnostic
        assert (
            f'ZGAP2MANAGERSEED: direct gate {gate_name}=PASS' in diagnostic
        )
        assert f'ZGAP2MANAGERSEED: direct gate {gate_name}=RED' in diagnostic
    assert "count >= 1" in diagnostic
    assert "zg361_is_reviewable_vassal_trigger = yes" in diagnostic
    assert "liege = root" in diagnostic
    assert diagnostic.rindex(
        "zga_phase2_manager_seed_maybe_begin_effect = yes"
    ) > diagnostic.rindex(
        "ZGAP2MANAGERSEED: direct gate direct_reviewable_vassal=RED"
    )
    post_switch_diagnostic = top_level_block(
        effects,
        "zga_phase2_manager_seed_log_post_switch_gates_effect",
    )
    assert "this = character:han_6875" not in post_switch_diagnostic
    post_switch_gates = {
        "human": "is_ai = no",
        "alive": "is_alive = yes",
        "landed": "is_landed = yes",
        "owner_binding": "this = scope:zga_phase2_manager_owner",
        "handoff_pending": (
            "has_character_flag = zga_phase2_manager_seed_handoff_pending"
        ),
        "celestial": "zg361_is_celestial_liege_trigger = yes",
        "game_rule": "has_game_rule = zg361_on",
        "review_now": "zg361_review_now_business_valid_trigger = yes",
        "prestige_150": "prestige >= 150",
        "b1_inactive": "NOT = { has_character_flag = zg361_b1_cycle_active }",
        "review_in_progress_inactive": (
            "NOT = { has_character_flag = zg361_review_in_progress }"
        ),
        "p2c_inactive": "var:zg361_p2c_active != 1",
        "pp_inactive": "var:zg361_pp_portfolio_queue_active != 1",
        "subject_binding": "scope:zga_phase2_manager_subject = {",
    }
    for gate_name, gate_expression in post_switch_gates.items():
        assert gate_expression in post_switch_diagnostic
        assert (
            f"ZGAP2MANAGERSEED: post-switch gate {gate_name}=PASS"
            in post_switch_diagnostic
        )
        assert (
            f"ZGAP2MANAGERSEED: post-switch gate {gate_name}=RED"
            in post_switch_diagnostic
        )
    assert re.search(
        r"\b(?:set|change|remove)_variable\b",
        post_switch_diagnostic,
    ) is None
    assert re.search(
        r"\b(?:add|remove)_character_flag\b",
        post_switch_diagnostic,
    ) is None
    fixture_effect_keys = re.findall(
        r"(?m)^(zga_phase2_manager_seed_[a-z0-9_]+_effect)\s*=\s*\{",
        effects,
    )
    assert len(fixture_effect_keys) == 5
    for effect_file in (FIXTURE / "common" / "scripted_effects").glob("*.txt"):
        effect_file_payload = text(effect_file)
        effect_file_keys = re.findall(
            r"(?m)^[a-z0-9_]+_effect\s*=\s*\{",
            effect_file_payload,
        )
        assert 1 <= len(effect_file_keys) <= 10, effect_file
    maybe_begin_for_handoff = top_level_block(
        effects, "zga_phase2_manager_seed_maybe_begin_effect"
    )
    handoff_branch = maybe_begin_for_handoff[
        maybe_begin_for_handoff.index("\telse_if = {") :
    ]
    assert "zg361_review_now_business_valid_trigger = yes" not in handoff_branch
    assert "prestige >= 150" not in handoff_branch
    assert "\non_game_start = {" not in on_actions
    assert "on_game_start_after_lobby = {" in on_actions
    assert on_actions.count("zga_phase2_manager_seed_on_game_start") == 2
    opener = top_level_block(events, "zga_phase2_manager_seed.100")
    for gate in (
        "NOT = { has_character_flag = zg361_b1_cycle_active }",
        "NOT = { has_character_flag = zg361_review_in_progress }",
        "var:zg361_p2c_active != 1",
        "var:zg361_pp_portfolio_queue_active != 1",
        "zg361_review_now_business_valid_trigger = yes",
        "any_vassal = {",
        "count >= 1",
        "ordered_vassal = {",
        "zg361_is_reviewable_vassal_trigger = yes",
        "liege = root",
        "save_scope_as = zga_phase2_manager_subject",
    ):
        assert gate in opener
    assert "zga_phase2_manager_seed.10 = {" not in events
    assert "zga_phase2_manager_seed.10." not in payload
    maybe_begin = top_level_block(
        effects, "zga_phase2_manager_seed_maybe_begin_effect"
    )
    direct_branch = maybe_begin[: maybe_begin.index("\n\telse_if = {")]
    assert "zg361_is_celestial_liege_trigger = yes" in direct_branch
    assert "zg361_review_now_business_valid_trigger = yes" in direct_branch
    assert "trigger_event = zga_phase2_manager_seed.100" in direct_branch
    assert "set_player_character =" not in direct_branch
    survivability = top_level_block(
        effects, "zga_phase2_manager_seed_apply_survivability_effect"
    )
    assert "is_ai = no" in survivability
    assert "is_alive = yes" in survivability
    assert (
        "has_character_modifier = "
        "zga_phase2_manager_seed_survivability_modifier" in survivability
    )
    assert survivability.count("add_character_modifier = {") == 1
    assert "days = 1100" in survivability
    assert "health=10 epidemic_resistance=100 days=1100" in survivability
    assert (
        "zga_phase2_manager_seed_apply_survivability_effect = yes" in diagnostic
    )
    survivability_modifier = top_level_block(
        modifiers, "zga_phase2_manager_seed_survivability_modifier"
    )
    assert "health = 10" in survivability_modifier
    assert "epidemic_resistance = 100" in survivability_modifier

    seed_event = top_level_block(events, "zga_phase2_manager_seed.1")
    assert (
        "remove_character_modifier = "
        "zga_phase2_manager_seed_survivability_modifier"
    ) in seed_event
    retry_arm = top_level_block(
        effects, "zga_phase2_manager_seed_arm_daily_retry_effect"
    )
    for retry_gate in (
        "is_ai = no",
        "is_alive = yes",
        "is_landed = yes",
        "zg361_is_celestial_liege_trigger = yes",
        "has_game_rule = zg361_on",
        "NOT = { has_character_flag = "
        "zga_phase2_manager_seed_bootstrap_started }",
        "NOT = { has_character_flag = "
        "zga_phase2_manager_seed_daily_retry_armed }",
    ):
        assert retry_gate in retry_arm
    assert retry_arm.count(
        "add_character_flag = zga_phase2_manager_seed_daily_retry_armed"
    ) == 1
    assert retry_arm.count(
        "trigger_event = { id = zga_phase2_manager_seed.101 days = 1 }"
    ) == 1
    assert (
        "zga_phase2_manager_seed_arm_daily_retry_effect = yes" in diagnostic
    )
    assert diagnostic.index(
        "zga_phase2_manager_seed_arm_daily_retry_effect = yes"
    ) < diagnostic.rindex("zga_phase2_manager_seed_maybe_begin_effect = yes")
    retry_event = top_level_block(events, "zga_phase2_manager_seed.101")
    assert "hidden = yes" in retry_event
    assert retry_event.count(
        "remove_character_flag = zga_phase2_manager_seed_daily_retry_armed"
    ) == 1
    assert retry_event.count(
        "add_character_flag = zga_phase2_manager_seed_daily_retry_logged"
    ) == 1
    assert (
        "NOT = { has_character_flag = "
        "zga_phase2_manager_seed_daily_retry_logged }" in retry_event
    )
    assert retry_event.count("ZGAP2MANAGERSEED: daily retry carrier live") == 1
    assert retry_event.count(
        "zga_phase2_manager_seed_maybe_begin_effect = yes"
    ) == 1
    assert retry_event.count(
        "zga_phase2_manager_seed_arm_daily_retry_effect = yes"
    ) == 1
    assert retry_event.index(
        "remove_character_flag = zga_phase2_manager_seed_daily_retry_armed"
    ) < retry_event.index("zga_phase2_manager_seed_maybe_begin_effect = yes")
    assert retry_event.index(
        "zga_phase2_manager_seed_maybe_begin_effect = yes"
    ) < retry_event.index(
        "zga_phase2_manager_seed_arm_daily_retry_effect = yes"
    )
    assert effects.count("set_player_character =") == 1
    assert "set_player_character = scope:zga_phase2_manager_owner" in effects
    assert "add_character_flag = zga_phase2_manager_seed_handoff_pending" in effects
    assert effects.index("save_scope_as = zga_phase2_manager_subject") < effects.index(
        "set_player_character = scope:zga_phase2_manager_owner"
    )
    assert effects.index("save_scope_as = zga_phase2_manager_owner") < effects.index(
        "set_player_character = scope:zga_phase2_manager_owner"
    )
    assert (
        "trigger_event = { id = zga_phase2_manager_seed.11 days = 0 }"
        in effects
    )
    assert effects.index(
        "set_player_character = scope:zga_phase2_manager_owner"
    ) < effects.index(
        "trigger_event = { id = zga_phase2_manager_seed.11 days = 0 }"
    )
    carrier = top_level_block(events, "zga_phase2_manager_seed.11")
    assert "hidden = yes" in carrier
    assert "this = scope:zga_phase2_manager_owner" in carrier
    assert "is_ai = no" in carrier
    assert "scope:zga_phase2_manager_subject = {" in carrier
    assert "is_ai = yes" in carrier
    assert "liege = root" in carrier
    assert "zg361_review_now_business_valid_trigger = yes" in carrier
    assert "has_character_flag = zga_phase2_manager_seed_handoff_pending" in carrier
    assert "remove_character_flag = zga_phase2_manager_seed_handoff_pending" in carrier
    assert carrier.count(
        "remove_character_flag = zga_phase2_manager_seed_handoff_pending"
    ) == 1
    assert carrier.index(
        "remove_character_flag = zga_phase2_manager_seed_handoff_pending"
    ) < carrier.index("trigger_event = zga_phase2_manager_seed.100")
    failure_branch = carrier.index(
        'debug_log = "ZGAP2MANAGERSEED: RED post-switch manager binding unavailable"'
    )
    diagnostic_call = carrier.index(
        "zga_phase2_manager_seed_log_post_switch_gates_effect = yes"
    )
    assert diagnostic_call < failure_branch
    assert carrier.index(
        "remove_character_flag = zga_phase2_manager_seed_handoff_pending"
    ) < failure_branch
    assert (
        "remove_character_flag = zga_phase2_manager_seed_handoff_pending"
        not in carrier[failure_branch:]
    )
    assert "trigger_event = zga_phase2_manager_seed.100" in carrier
    assert "set_player_character =" not in carrier
    assert (
        "NOT = { has_character_flag = "
        "zga_phase2_manager_seed_handoff_pending }" in on_actions
    )
    assert (
        "NOT = { has_character_flag = "
        "zga_phase2_manager_seed_handoff_pending }" not in direct_branch
    )
    assert (
        "remove_character_flag = zga_phase2_manager_seed_handoff_pending"
        in direct_branch
    )
    for retry_gate in (effects, scripted_gui):
        assert (
            "NOT = { has_character_flag = "
            "zga_phase2_manager_seed_handoff_started }" in retry_gate
        )
    final_event = top_level_block(events, "zga_phase2_manager_seed.1")
    assert "hidden = yes" not in final_event
    assert "theme = stewardship" in final_event
    assert final_event.count("save_scope_as = zga_phase2_manager_owner") == 1
    assert len(re.findall(r"(?m)^\s*option\s*=\s*\{", final_event)) == 1

    # The fixture may only expose acceptance identities. Product lifecycle
    # entrypoints and product receipt writes are forbidden.
    assert payload.count("set_player_character =") == 1
    for token in (
        "zg361_b1_open_cycle_effect",
        "zg361_run_review_effect",
        "zg361_p2c_begin_effect",
        "zg361_pp_open_t_case_effect",
        "zg361_ip_open_x_case_effect",
        "zg361_we_open_portfolio_effect",
    ):
        assert token not in payload
    assert re.search(
        r"\b(?:set|change)_variable\s*=\s*\{\s*name\s*=\s*zg361_",
        payload,
    ) is None
    assert re.search(r"\bremove_variable\s*=\s*zg361_", payload) is None
    for token in (
        "create_character",
        "create_title",
        "grant_title",
        "set_father",
        "set_mother",
        "set_spouse",
        "add_relation",
        "set_relation",
    ):
        assert re.search(rf"\b{re.escape(token)}\b", payload) is None

    release = (ROOT / "tools" / "build_mod_zhongguo_style_release.py").read_text(
        encoding="utf-8"
    )
    normal_runner = (ROOT / "tools" / "run_zhongguo_acceptance.py").read_text(
        encoding="utf-8"
    )
    assert "zg361_phase2_manager_seed_bootstrap" not in release
    assert "zg361_phase2_manager_seed_bootstrap" not in normal_runner
    contract = json.loads(
        (ROOT / "tools" / "zg361_phase2_manager_seed_contract.json").read_text(
            encoding="utf-8"
        )
    )
    assert contract["kind"] == "zg361_phase2_player_manager_seed_request"
    assert contract["seed_purpose"] == "player-manager"
    assert contract["status"] == "blocked_live_capture_required"
    assert contract["ready"] is False
    assert contract["source"]["sha256"] == (
        "8e6ceb97e97cd6b9185ebbcce38b42fc087e0b800cd5e321037c9f29a79e45b9"
    )
    assert contract["source"]["bytes"] == 57377787
    assert contract["source"]["absolute_save"] == (
        "Z:\\p2y\\r2\\native-state\\profile\\save games\\xar_checkpoint.ck3"
    )
    assert contract["saved_state"]["date_raw"] == 53147016
    assert contract["saved_state"]["played_character_id"] == 29037
    assert contract["saved_state"]["player_history_id"] == "han_6875"
    transition = contract["player_transition_contract"]
    assert transition["handoff_mode"] == "post_exact_pip_load_gui"
    assert transition["source_character_id"] == 29037
    assert transition["target_character_id"] == 32904
    assert transition["completion_date_raw"] == 53147040
    assert transition["allowed_prebootstrap_event_definition_keys"] == [
        "zg361b2.40"
    ]
    assert transition["activation_event_selected_option_number"] == 3
    assert transition["activation_event_selected_native_option_index"] == 2
    assert transition["forbids_timeline_resume_after_activation_event_drain"] is True
    assert transition["timeline_speed"] == 5
    assert transition["fixture_set_player_character_count"] == 1
    assert transition["fixture_creates_character"] is False
    assert transition["fixture_creates_title"] is False
    assert transition["fixture_creates_relationship"] is False
    assert transition["fixture_calls_product_b1"] is False
    assert transition["fixture_writes_product_receipts"] is False
    checkpoint = contract["transition_checkpoint_contract"]
    assert checkpoint == {
        "kind": "zg361_phase2_active_manager_transition_checkpoint",
        "capture_cli": "--manager-transition-checkpoint-capture",
        "continuation_cli": "--manager-transition-checkpoint-receipt",
        "capture_on_first_typed_target_frame": True,
        "requires_same_native_pid_and_connection_generation": True,
        "requires_paused": True,
        "requires_map_ready": True,
        "requires_exact_completion_date": True,
        "requires_timeline_speed": 5,
        "requires_checkpoint_byte_hash": True,
        "clean_process_continuation": True,
        "continuation_maximum_date_raw": 53147064,
        "continuation_timeline_speed": 5,
        "continuation_forbids_unregistered_event_drains": True,
        "final_seed_ready": False,
        "clears_product_state": False,
        "writes_product_receipt": False,
        "rejected_source_save_sha256s": [
            "bf5960b7194e1222029add884743c688fee0d86f95559670c587317461519e74"
        ],
    }
    entry = contract["manager_entry_contract"]
    assert entry == {
        "event_definition_key": "zga_phase2_manager_seed.1",
        "manager_scope": "zga_phase2_manager_owner",
        "subject_scope": "zga_phase2_manager_subject",
        "requires_human": True,
        "requires_alive": True,
        "requires_landed": True,
        "requires_celestial_liege": True,
        "requires_game_rule_enabled": True,
        "minimum_existing_direct_reviewable_vassals": 1,
        "requires_b1_inactive": True,
        "requires_central_inactive": True,
        "requires_pp_inactive": True,
        "requires_review_now_eligible": True,
        "minimum_prestige": 150,
        "fixture_opens_product_b1": False,
        "fixture_writes_product_receipts": False,
    }
    print(
        "GREEN: player-manager seed fixture has a typed existing-liege "
        "handoff and non-product capture"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
