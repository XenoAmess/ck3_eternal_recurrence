#!/usr/bin/env python3
"""Static contract for the isolated Workforce #360 transition fixture."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tools" / "fixtures" / "zg361_phase2_workforce_action"
BOM = b"\xef\xbb\xbf"


def require(condition: object, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def bom_text(path: Path) -> str:
    payload = path.read_bytes()
    require(payload.startswith(BOM), f"missing UTF-8 BOM: {path}")
    return payload.decode("utf-8-sig")


def block(text: str, key: str) -> str:
    match = re.search(rf"(?m)^{re.escape(key)}\s*=\s*\{{", text)
    require(match is not None, f"missing block {key}")
    if match is None:
        raise AssertionError(f"missing block {key}")
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
    require(FIXTURE.is_dir(), "Workforce action fixture directory is missing")
    require(
        not (FIXTURE / "common" / "decisions").exists(),
        "Workforce action fixture must not add test decisions",
    )
    files = tuple(path for path in FIXTURE.rglob("*") if path.is_file())
    require(len(files) == 7, f"unexpected fixture file count: {len(files)}")
    for path in files:
        bom_text(path)

    all_text = "\n".join(bom_text(path) for path in files)
    guis = bom_text(
        FIXTURE
        / "common"
        / "scripted_guis"
        / "zga_phase2_workforce_guis.txt"
    )
    bridge = bom_text(FIXTURE / "gui" / "zga_phase2_workforce_bridge.gui")
    registration = bom_text(
        FIXTURE
        / "gui"
        / "scripted_widgets"
        / "zga_phase2_workforce_scripted_widgets.txt"
    )
    events = bom_text(FIXTURE / "events" / "zga_phase2_workforce_events.txt")

    for token in (
        "zga_phase2_workforce_summon_gui = {",
        "NOT = { has_character_flag = zga_phase2_workforce_transition_pending }",
        "var:zg361_case_al_state = 4",
        "var:zg361_p2c_m360_source_status = 1",
        "trigger_event = zga_phase2_workforce.1",
    ):
        require(token in guis, f"missing scripted GUI contract: {token}")
    require("alwaystransparent = yes" in bridge, "bridge is not invisible")
    require(
        "zga_phase2_workforce_summon_gui" in bridge,
        "bridge does not invoke the typed summon GUI",
    )
    registration_token = (
        "gui/zga_phase2_workforce_bridge.gui = "
        "zga_phase2_workforce_bridge_window"
    )
    require(
        registration_token in registration,
        "scripted widget registration is missing",
    )

    handoff = block(events, "zga_phase2_workforce.1")
    carrier = block(events, "zga_phase2_workforce.2")
    switch_back = block(events, "zga_phase2_workforce.3")
    require("hidden = yes" not in handoff, "subject handoff must be visible")
    require("hidden = yes" in carrier, "owner carrier must be hidden")
    require("hidden = yes" not in switch_back, "switch-back must be visible")
    require(
        len(re.findall(r"(?m)^\s*option\s*=\s*\{", handoff)) == 1,
        "subject handoff must expose exactly one option",
    )
    require(
        len(re.findall(r"(?m)^\s*option\s*=\s*\{", switch_back)) == 1,
        "switch-back must expose exactly one option",
    )
    for event in (handoff, carrier, switch_back):
        require(
            "zga_phase2_workforce_owner" in event,
            "event lacks typed owner scope",
        )
        require(
            "zga_phase2_workforce_subject" in event,
            "event lacks typed subject scope",
        )
    require(
        handoff.count("set_player_character =") == 1,
        "subject handoff must contain one player transition",
    )
    require(
        switch_back.count("set_player_character =") == 1,
        "switch-back must contain one player transition",
    )
    require(
        all_text.count("set_player_character =") == 2,
        "fixture must contain exactly two player transitions",
    )
    product_resume = carrier.index(
        "zg361_we_resume_m360_from_central_source_effect = {"
    )
    switch_queue = carrier.index("trigger_event = zga_phase2_workforce.3")
    require(
        product_resume < switch_queue,
        "real M360 must be queued before the switch-back card",
    )
    require(
        "TICKET_OWNER = scope:zga_phase2_workforce_owner" in carrier,
        "carrier lacks typed owner argument",
    )
    require(
        "TICKET_SUBJECT = scope:zga_phase2_workforce_subject" in carrier,
        "carrier lacks typed subject argument",
    )
    require(
        "has_variable = zg361_we_m360_receipt_choice" in switch_back,
        "switch-back is not gated by the real M360 receipt",
    )

    # The fixture may set only its own flags and select a player. Product
    # variables/receipts remain owned by the shipped public resume effect.
    require(
        re.search(
            r"\b(?:set|change)_variable\s*=\s*\{\s*name\s*=\s*zg361_",
            all_text,
        )
        is None,
        "fixture writes a product zg361 variable",
    )
    require(
        re.search(r"\bremove_variable\s*=\s*zg361_", all_text) is None,
        "fixture removes a product zg361 variable",
    )
    for token in (
        "create_character",
        "create_title",
        "grant_title",
        "add_relation",
        "set_relation",
        "decision =",
    ):
        require(token not in all_text, f"fixture contains forbidden token: {token}")

    seed_fixture = ROOT / "tools" / "fixtures" / "zg361_phase2_seed_bootstrap"
    seed_text = "\n".join(
        bom_text(path) for path in seed_fixture.rglob("*") if path.is_file()
    )
    require(
        "namespace = zga_phase2_workforce" not in seed_text,
        "seed fixture absorbed the Workforce namespace",
    )
    require(
        "zga_phase2_workforce_summon_gui" not in seed_text,
        "seed fixture absorbed the Workforce summon",
    )
    release_source = (
        ROOT / "tools" / "build_mod_zhongguo_style_release.py"
    ).read_text(encoding="utf-8")
    require(
        "zg361_phase2_workforce_action" not in release_source,
        "release builder references the acceptance-only fixture",
    )
    runner_source = (ROOT / "tools" / "run_zhongguo_acceptance.py").read_text(
        encoding="utf-8"
    )
    promo_match = re.search(
        r"(?ms)^def run_scenario\(.*?(?=^def |\Z)", runner_source
    )
    require(promo_match is not None, "normal/promo scenario function is missing")
    if promo_match is None:
        raise AssertionError("normal/promo scenario function is missing")
    require(
        "install_phase2_workforce_action_fixture" not in promo_match.group(0),
        "normal/promo scenario installs the acceptance-only fixture",
    )
    require(
        runner_source.count("install_phase2_workforce_action_fixture(") == 2,
        "Workforce fixture install must have one definition and one call site",
    )
    print("GREEN: Workforce action fixture is isolated, typed and non-release")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
