#!/usr/bin/env python3
"""Static contract for the external phase-two MCP seed fixture."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tools" / "fixtures" / "zg361_phase2_seed_bootstrap"
ON_ACTIONS = (
    FIXTURE
    / "common"
    / "on_action"
    / "zga_phase2_seed_on_actions.txt"
)
EFFECTS = (
    FIXTURE
    / "common"
    / "scripted_effects"
    / "zga_phase2_seed_effects.txt"
)
EVENTS = FIXTURE / "events" / "zga_phase2_seed_events.txt"
SCRIPTED_GUIS = (
    FIXTURE
    / "common"
    / "scripted_guis"
    / "zga_phase2_seed_scripted_guis.txt"
)
BRIDGE_GUI = FIXTURE / "gui" / "zga_phase2_seed_bridge.gui"
SCRIPTED_WIDGETS = (
    FIXTURE
    / "gui"
    / "scripted_widgets"
    / "zga_phase2_seed_scripted_widgets.txt"
)
BOM = b"\xef\xbb\xbf"
REQUIRED_SCOPES = (
    "zga_phase2_b2_owner",
    "zga_phase2_incident_owner",
    "zga_phase2_workforce_owner",
    "zga_phase2_ai_owned_owner",
    "zga_phase2_ai_owned_subject",
)


def bom_text(path: Path) -> str:
    payload = path.read_bytes()
    assert payload.startswith(BOM), f"missing UTF-8 BOM: {path}"
    return payload.decode("utf-8-sig")


def top_level_block(text: str, key: str) -> str:
    match = re.search(rf"(?m)^{re.escape(key)}\s*=\s*\{{", text)
    assert match is not None, f"missing block {key}"
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
                return text[match.start() : index + 1]
    raise AssertionError(f"unterminated block {key}")


def main() -> int:
    assert FIXTURE.is_dir()
    assert not (FIXTURE / "common" / "decisions").exists()
    script_files = (
        tuple(FIXTURE.rglob("*.txt"))
        + tuple(FIXTURE.rglob("*.gui"))
        + tuple(FIXTURE.rglob("*.yml"))
        + tuple(FIXTURE.rglob("*.mod"))
    )
    assert script_files
    for path in script_files:
        bom_text(path)

    on_actions = bom_text(ON_ACTIONS)
    effects = bom_text(EFFECTS)
    events = bom_text(EVENTS)
    scripted_guis = bom_text(SCRIPTED_GUIS)
    bridge_gui = bom_text(BRIDGE_GUI)
    scripted_widgets = bom_text(SCRIPTED_WIDGETS)
    fixture_text = "\n".join(bom_text(path) for path in script_files)
    assert "on_game_start_after_lobby = {" in on_actions
    assert "on_actions = {" in on_actions
    assert "every_player = {" in on_actions
    assert "this = character:han_6875" in on_actions
    assert "is_ai = no" in on_actions

    assert "this = character:han_6875" in effects
    maybe_begin = top_level_block(effects, "zga_phase2_seed_maybe_begin_effect")
    assert "this = character:han_6875" in maybe_begin
    assert "is_ai = no" in maybe_begin
    assert "NOT = { has_character_flag = zga_phase2_b2_seed_bootstrap_started }" in maybe_begin
    assert "add_character_flag = zga_phase2_b2_seed_bootstrap_started" in maybe_begin
    assert "trigger_event = zga_phase2_seed.100" in maybe_begin
    assert maybe_begin.index(
        "add_character_flag = zga_phase2_b2_seed_bootstrap_started"
    ) < maybe_begin.index("trigger_event = zga_phase2_seed.100")
    assert "remove_character_flag = zga_phase2_b2_seed_bootstrap_started" not in fixture_text
    assert "save_scope_as = zga_phase2_seed_player" in effects
    assert "liege = {" in effects
    assert "trigger_event = zga_phase2_seed.101" in effects
    manager = top_level_block(events, "zga_phase2_seed.101")
    assert "is_ai = yes" in manager
    assert "liege = root" in manager
    assert "zg361_b1_open_cycle_effect = yes" in manager
    assert "zg361_ip_open_x_case_effect = {" in manager
    assert "zg361_we_open_portfolio_effect = {" in manager
    subject = top_level_block(events, "zga_phase2_seed.102")
    assert "zg361_b2_on_result_frozen_effect = yes" in subject
    assert "var:zg361_result_case_state = 2" in subject
    delivered_gate = subject[
        subject.index("var:zg361_result_case_state = 3", subject.index("zg361_b2_on_result_frozen_effect = yes")) :
    ]
    assert (
        "var:zg361_result_settlement_posted_serial = var:zg361_result_case_serial"
        in delivered_gate
    )
    assert "trigger_event = { id = zga_phase2_seed.103 days = 1 }" in subject
    assert "trigger_event = zga_phase2_seed.103" in subject
    assert not re.search(
        r"(?m)^\s*trigger_event\s*=\s*zga_phase2_seed\.1\s*$", subject
    )
    witness_poll = top_level_block(events, "zga_phase2_seed.103")
    assert "hidden = yes" in witness_poll
    assert "var:zg361_result_case_state = 2" in witness_poll
    assert "var:zg361_result_case_state = 3" in witness_poll
    assert "zg361_b2_on_notice_delivered_effect = yes" not in witness_poll
    assert "var:zg361_b2_notice_state = 3" in witness_poll
    assert "trigger_event = { id = zga_phase2_seed.103 days = 1 }" in witness_poll
    assert "trigger_event = zga_phase2_seed.1" in witness_poll

    final_event = top_level_block(events, "zga_phase2_seed.1")
    assert "hidden = yes" not in final_event
    assert "theme = stewardship" in final_event
    assert len(re.findall(r"(?m)^\s*option\s*=\s*\{", final_event)) == 1
    for scope_name in REQUIRED_SCOPES:
        assert final_event.count(f"save_scope_as = {scope_name}") == 1
    assert "trigger_event = zga_phase2_seed.1" in witness_poll

    load_safe_bridge = top_level_block(
        scripted_guis, "zga_phase2_seed_bootstrap_bridge_gui"
    )
    assert "scope = character" in load_safe_bridge
    assert "this = character:han_6875" in load_safe_bridge
    assert "is_ai = no" in load_safe_bridge
    assert "NOT = { has_character_flag = zga_phase2_b2_seed_bootstrap_started }" in load_safe_bridge
    assert "zga_phase2_seed_maybe_begin_effect = yes" in load_safe_bridge
    assert 'name = "zga_phase2_seed_bridge_window"' in bridge_gui
    assert "size = { 1 1 }" in bridge_gui
    assert 'visible = "[GetPlayer.IsValid]"' in bridge_gui
    assert "alwaystransparent = yes" in bridge_gui
    assert "filter_mouse" not in bridge_gui
    assert "GetScriptedGui('zga_phase2_seed_bootstrap_bridge_gui').IsShown" in bridge_gui
    assert "GetScriptedGui('zga_phase2_seed_bootstrap_bridge_gui').Execute" in bridge_gui
    assert scripted_widgets.strip() == (
        "gui/zga_phase2_seed_bridge.gui = zga_phase2_seed_bridge_window"
    )

    # Only shipped entry points may write product state. The external fixture
    # cannot manufacture characters, titles, relations, output variables,
    # receipts, or rolling Workforce history.
    for token in (
        "create_character",
        "create_title",
        "grant_title",
        "set_father",
        "set_mother",
        "set_spouse",
        "add_relation",
        "set_relation",
        "set_player_character",
    ):
        assert re.search(rf"\b{re.escape(token)}\b", fixture_text) is None
    assert re.search(
        r"\b(?:set|change)_variable\s*=\s*\{\s*name\s*=\s*zg361_",
        fixture_text,
    ) is None
    assert re.search(
        r"\bremove_variable\s*=\s*zg361_", fixture_text
    ) is None
    assert "add_character_modifier" not in fixture_text
    assert "zg361_ip_probe_result value" not in fixture_text
    assert "zg361_we_record_completed_357_359_history_effect" not in fixture_text
    assert "zg361_we_submit_al_357_359_receipts_effect" not in fixture_text

    release_source = (
        ROOT / "tools" / "build_mod_zhongguo_style_release.py"
    ).read_text(encoding="utf-8")
    normal_runner_source = (
        ROOT / "tools" / "run_zhongguo_acceptance.py"
    ).read_text(encoding="utf-8")
    assert "zg361_phase2_seed_bootstrap" not in release_source
    assert (
        'FIXTURE_SOURCE = ROOT / "tools" / "fixtures" / "zg361_acceptance"'
        in normal_runner_source
    )
    print("GREEN: external phase-two seed fixture remains MCP-only and non-promo")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
