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

    for gate in (
        "is_ai = no",
        "is_alive = yes",
        "is_landed = yes",
        "zg361_is_celestial_liege_trigger = yes",
        "has_game_rule = zg361_on",
        "zg361_review_now_business_valid_trigger = yes",
        "prestige >= 150",
    ):
        assert gate in on_actions
        assert gate in effects
        assert gate in scripted_gui
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
    final_event = top_level_block(events, "zga_phase2_manager_seed.1")
    assert "hidden = yes" not in final_event
    assert "theme = stewardship" in final_event
    assert final_event.count("save_scope_as = zga_phase2_manager_owner") == 1
    assert len(re.findall(r"(?m)^\s*option\s*=\s*\{", final_event)) == 1

    # The fixture may only expose acceptance identities. Product lifecycle
    # entrypoints and product receipt writes are forbidden.
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
        "set_player_character",
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
    print("GREEN: player-manager seed fixture is gated, typed and non-product")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
