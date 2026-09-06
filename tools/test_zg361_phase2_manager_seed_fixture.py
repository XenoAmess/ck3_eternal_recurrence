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
    assert bridge.count("duration = 0.5") == 1
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
    handoff_branch = effects[effects.index("\telse_if = {") :]
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
    assert carrier.index(
        "remove_character_flag = zga_phase2_manager_seed_handoff_pending"
    ) < failure_branch
    assert (
        "remove_character_flag = zga_phase2_manager_seed_handoff_pending"
        not in carrier[failure_branch:]
    )
    assert "trigger_event = zga_phase2_manager_seed.100" in carrier
    assert "set_player_character =" not in carrier
    for manager_entry_gate in (effects, on_actions):
        assert (
            "NOT = { has_character_flag = "
            "zga_phase2_manager_seed_handoff_pending }" in manager_entry_gate
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
        "63a390a73fbc66c4339b3f3979e77c25ef18289299dd1514f54ef1f8db3d99c8"
    )
    assert contract["source"]["bytes"] == 79528933
    assert contract["source"]["absolute_save"] == (
        "Z:\\b3r108_native_state\\profile\\save games\\autosave.ck3"
    )
    assert contract["saved_state"]["date_raw"] is None
    assert contract["saved_state"]["played_character_id"] == 29037
    transition = contract["player_transition_contract"]
    assert transition == {
        "handoff_mode": "direct_already_player_manager",
        "trigger_effect_key": "zga_phase2_manager_seed_maybe_begin_effect",
        "activation_surface": "on_game_start_after_lobby_direct_manager",
        "entry_event_definition_key": "zga_phase2_manager_seed.1",
        "source_character_id": 29037,
        "target_character_id": 29037,
        "target_source": "already_played_character",
        "owner_scope": "zga_phase2_manager_owner",
        "subject_scope": "zga_phase2_manager_subject",
        "source_date_binding": "first_paused_typed_snapshot",
        "allowed_prebootstrap_event_definition_keys": [],
        "requires_exact_activation_event_drain": False,
        "requires_final_event_at_bound_source_date": True,
        "forbids_other_prebootstrap_event_drains": True,
        "forbids_any_prebootstrap_event_input": True,
        "timeline_speed": 5,
        "timeline_speed_only_if_advancement_required": True,
        "destructive_later_event_definition_key": "ep3_interactions_events.0630",
        "requires_destructive_event_zero_input_red": True,
        "requires_source_save_hash_match": True,
        "requires_source_saved_player_identity": True,
        "requires_typed_final_player": True,
        "requires_manager_entry_revalidation": True,
        "requires_final_manager_entry_identity_match": True,
        "fixture_set_player_character_count": 0,
        "fixture_creates_character": False,
        "fixture_creates_title": False,
        "fixture_creates_relationship": False,
        "fixture_calls_product_b1": False,
        "fixture_writes_product_receipts": False,
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
