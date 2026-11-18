"""Create an external CK3 fixture; never start the game or modify the product."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
from typing import Literal, NotRequired, TypedDict

from product import SOURCE, TARGETS


class FileReceipt(TypedDict):
    path: str
    size: int
    sha256: str


class FixtureReport(TypedDict):
    schema: Literal["cht.external-fixture.v1", "cht.external-gui-fixture.v1"]
    fixture_root: str
    expected_pass_markers: list[str]
    required_start: str
    required_end: str
    required_auxiliary_markers: list[str]
    entry_character_history_id: int
    entry_bookmark_key: str
    covers: str
    does_not_cover: list[str]
    ck3_started: bool
    files: list[FileReceipt]
    gui_choices: NotRequired[bool]
    maximum_natural_days: NotRequired[int]
    entry: NotRequired[str]
    preparation: NotRequired[str]
    expected_gui_steps: NotRequired[list[str]]


def test_marker(name: str, condition: str) -> str:
    return f"""    if = {{
        limit = {{ {condition} }}
        debug_log = "CHTT: PASS {name}"
    }}
    else = {{ debug_log = "CHTT: FAIL {name}" }}
"""


def prepare(output: Path, *, gui_choices: bool = False) -> FixtureReport:
    if type(gui_choices) is not bool:
        raise ValueError("gui_choices must be a strict boolean")
    output = output.resolve()
    if output.exists() or SOURCE == output or SOURCE in output.parents:
        raise ValueError("fixture output must be a new directory outside product source")
    event = """namespace = chtt

chtt.0001 = {
    type = character_event
    trigger = { is_ai = no this = character:1128 }
    hidden = yes
    immediate = {
        debug_log = "CHTT: START production-effect-matrix"
        if = {
            limit = {
                is_ai = no
                exists = capital_province
                capital_province.barony.holder = root
                capital_province = { has_ongoing_holding_construction = no }
            }
            capital_province.barony = { save_scope_as = barony }
            scope:barony.title_province = {
                if = {
                    limit = { NOT = { has_holding_type = castle_holding } }
                    set_holding_type = castle_holding
                }
            }
"""
    order = ["city", "temple", "tribal", "nomad", "temple_citadel", "castle"]
    by_kind = {target.kind: target.holding for target in TARGETS}
    markers = []
    for kind in order:
        holding = by_kind[kind]
        marker = f"convert-{kind}"
        markers.append(marker)
        event += f"            cht_convert_to_{kind}_effect = yes\n"
        event += test_marker(marker, f"scope:barony.title_province = {{ has_holding_type = {holding} }}")
    event += test_marker("same-type-rejected", "NOT = { scope:barony = { ch_barony_is_valid_for_castle_trigger = { CHARACTER = root } } }")
    event += "            cht_convert_to_castle_effect = yes\n"
    event += test_marker("same-type-unchanged", "scope:barony.title_province = { has_holding_type = castle_holding }")
    event += """            random_living_character = {
                limit = { is_ai = yes is_landed = yes }
                debug_log = "CHTT: AI guard actor reached"
                cht_convert_to_city_effect = yes
            }
"""
    event += test_marker("ai-effect-blocked", "scope:barony.title_province = { has_holding_type = castle_holding }")
    event += "            root.primary_title = { save_scope_as = barony }\n"
    event += test_marker("non-barony-rejected", "NOT = { scope:barony = { cht_barony_is_convertible_trigger = { CHARACTER = root } } }")
    event += """            debug_log = "CHTT: END production-effect-matrix"
        }
        else = { debug_log = "CHTT: FAIL fixture-precondition" }
    }
}
"""
    on_action = """on_game_start = { on_actions = { chtt_on_start } }
chtt_on_start = {
    effect = {
        every_player = {
            limit = { this = character:1128 }
            trigger_event = { id = chtt.0001 days = 1 }
        }
    }
}
"""
    payloads = {
        "descriptor.mod": b'name="CHT External Acceptance Fixture"\nversion="1.0.0"\nsupported_version="1.20.*"\n',
        "common/on_action/chtt_on_actions.txt": on_action.encode("utf-8-sig"),
        "events/chtt_events.txt": event.encode("utf-8-sig"),
    }
    output.mkdir(parents=True)
    for relative, data in payloads.items():
        path = output / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    if gui_choices:
        fixture = Path(__file__).parent / "fixtures/gui_choices"
        for source in sorted(fixture.rglob("*")):
            if source.is_file():
                target = output / source.relative_to(fixture)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
    markers += ["same-type-rejected", "same-type-unchanged", "ai-effect-blocked", "non-barony-rejected"]
    report: FixtureReport = {
        "schema": "cht.external-fixture.v1",
        "fixture_root": str(output),
        "expected_pass_markers": markers,
        "required_start": "CHTT: START production-effect-matrix",
        "required_end": "CHTT: END production-effect-matrix",
        "required_auxiliary_markers": ["CHTT: AI guard actor reached"],
        "entry_character_history_id": 1128,
        "entry_bookmark_key": "bookmark_rags_to_riches_duke_robert",
        "covers": "production scripted effects and title predicates",
        "does_not_cover": ["GUI decision execution", "native selector selection", "decision cost", "save/reload", "all buildings preserved"],
        "ck3_started": False,
        "files": [{"path": relative, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()} for relative, data in sorted(payloads.items())],
    }
    if gui_choices:
        report.update({
            "schema": "cht.external-gui-fixture.v1",
            "gui_choices": True,
            "maximum_natural_days": 0,
            "entry": "on_game_start_after_lobby -> chtt_gui.1 -> unchanged chtt.0001 matrix",
            "preparation": "Add 1000 isolated gold; original production-effect matrix restores capital castle; no production city decision or payment is automated.",
            "expected_gui_steps": ["record paused baseline", "actual production city decision and Rossano selector", "verify conversion/cost/untouched capital", "actual GUI Save and Load", "verify reloaded state"],
            "does_not_cover": ["native bridge qualification", "all building preservation", "full mod combinations", "UI business until actual operator execution"],
            "files": [{"path": p.relative_to(output).as_posix(), "size": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(output.rglob("*")) if p.is_file()],
        })
    (output.parent / f"{output.name}.fixture.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--gui-choices", action="store_true", help="Prepare explicit zero-day production GUI/cost and Save/Load probes")
    args = parser.parse_args()
    try:
        print(json.dumps(prepare(args.output, gui_choices=args.gui_choices), ensure_ascii=False, indent=2))
    except (OSError, ValueError) as error:
        parser.exit(1, f"CHT FIXTURE FAILED: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
