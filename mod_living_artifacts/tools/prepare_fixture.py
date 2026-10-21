"""Emit external initial inputs and a read-only getter logger for core acceptance.

No launcher, host, runtime download, business terminal value, automatic feeding,
production-effect override, or assertion/PASS marker is emitted here.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from textwrap import dedent
from typing import Literal, TypedDict

PRODUCT_TOOLS = Path(__file__).resolve().parent
if str(PRODUCT_TOOLS) not in sys.path:
    sys.path.insert(0, str(PRODUCT_TOOLS))

from acceptance_contract import Pin, pin, require, write_once
from living_artifacts_core import render_fixture_effects, render_fixture_localization


class FixtureEmission(TypedDict):
    schema_version: Literal[1]
    fixture_root: str
    files: dict[str, Pin]
    input_origin: Literal["fixture_generated"]
    business_acceptance: Literal["NOT_ASSESSED"]
    game_started: Literal[False]


def _input_log(role: str, scope: str) -> str:
    cases = []
    for rarity in ("common", "masterwork", "famed", "illustrious"):
        cases.append(f'if = {{ limit = {{ rarity = {rarity} }} debug_log = "XALW_INPUT_V1;role={role};owner=[xalw_fixture_item.GetOwner.GetID];artifact=[xalw_fixture_item.GetID];rarity={rarity}" }}')
    return f"{scope} = {{ save_scope_as = xalw_fixture_item\n" + "\n".join(cases) + "\n}"


def _sample_log(equipped: bool) -> str:
    fields = [
        "seq=[xalw_fixture_owner.MakeScope.Var('xalw_fixture_observer_sequence').GetValue|5]",
        "owner=[xalw_fixture_item.GetOwner.GetID]", "artifact=[xalw_fixture_item.GetID]",
        f"equipped={int(equipped)}",
        "game_day=[xalw_fixture_owner.MakeScope.Var('xalw_fixture_observed_day').GetValue|5]",
        "month=[xalw_fixture_owner.MakeScope.ScriptValue('xalw_current_month_value')|5]",
    ]
    for output, variable in (("level", "level"), ("xp", "xp_in_level"), ("pending", "pending_xp"),
                             ("growth", "growth_sequence"), ("last_month", "last_settled_month"), ("resonance", "resonance")):
        fields.append(f"{output}=[xalw_fixture_item.MakeScope.Var('xalw_{variable}').GetValue|5]")
    fields.append("durability=[xalw_fixture_item.GetDurability|5]")
    return 'debug_log = "XALW_SAMPLE_V1;' + ";".join(fields) + '"'


def render_observer_effects() -> str:
    """Only observer-owned metadata is written after the initial input phase."""
    input_logs = [_input_log("target", "scope:xalw_test_living")]
    input_logs.extend(_input_log(rarity, f"scope:xalw_test_material_{rarity}")
                      for rarity in ("common", "masterwork", "famed", "illustrious"))
    return dedent("""
        xalw_fixture_initialize_effect = {
            save_scope_as = xalw_fixture_owner
            xalw_test_prepare_owner_effect = yes
            set_variable = { name = xalw_fixture_target value = scope:xalw_test_living }
            set_variable = { name = xalw_fixture_observer_sequence value = 0 }
            scope:xalw_test_living = {
                # G01 input: one monthly +8 must cross 1/92 -> 2/0 naturally.
                set_variable = { name = xalw_xp_in_level value = 92 }
                # Four weapon materials are deliberately non-diet input.
                set_variable = { name = xalw_diet value = flag:armor }
            }
    """).strip() + "\n" + "\n".join(input_logs) + dedent("""
            xalw_fixture_observe_effect = yes
            debug_log = "XALW_FIXTURE_READY_V1"
            trigger_event = { id = xalw_fixture.1 days = 1 }
        }
        xalw_fixture_observe_effect = {
            save_scope_as = xalw_fixture_owner
            set_variable = { name = xalw_fixture_observed_day value = current_date }
            if = {
                limit = { var:xalw_fixture_target ?= { exists = artifact_owner } }
                var:xalw_fixture_target = {
                    save_scope_as = xalw_fixture_item
                    if = { limit = {
                        has_variable = xalw_level
                        has_variable = xalw_xp_in_level
                        has_variable = xalw_pending_xp
                        has_variable = xalw_growth_sequence
                        has_variable = xalw_last_settled_month
                        has_variable = xalw_resonance
                    }
    """) + "\n" + "if = { limit = { is_equipped = yes } " + _sample_log(True) + " }\nelse = { " + _sample_log(False) + " }\n}\nelse = { debug_log = \"XALW_OBSERVER_UNAVAILABLE_V1;reason=required_variable_missing\" }\n" + dedent("""
                }
            }
            else = { debug_log = "XALW_OBSERVER_UNAVAILABLE_V1;reason=target_reference_or_owner_missing" }
        }
    """)


def emit_fixture(destination: Path) -> FixtureEmission:
    destination = destination.resolve()
    repo = Path(__file__).resolve().parents[2]
    require(not destination.is_relative_to(repo) and not destination.exists(), "Use a new external fixture directory")
    scripts: dict[str, str] = {
        "descriptor.mod": 'name="Living Artifacts acceptance inputs (external only)"\nsupported_version="1.20.*"\n',
        "common/scripted_effects/xalw_fixture_inputs.txt": render_fixture_effects(),
        "common/scripted_effects/xalw_fixture_observer.txt": render_observer_effects(),
        "common/on_action/xalw_fixture_bootstrap.txt": dedent("""
            on_game_start_after_lobby = { on_actions = { xalw_fixture_bootstrap } }
            xalw_fixture_bootstrap = { effect = { every_player = { xalw_fixture_initialize_effect = yes } } }
        """).strip() + "\n",
        "events/xalw_fixture_events.txt": dedent("""
            namespace = xalw_fixture
            xalw_fixture.1 = {
                type = character_event
                hidden = yes
                trigger = { is_alive = yes }
                immediate = {
                    change_variable = { name = xalw_fixture_observer_sequence add = 1 }
                    xalw_fixture_observe_effect = yes
                    trigger_event = { id = xalw_fixture.1 days = 1 }
                }
            }
        """).strip() + "\n",
    }
    for language in ("simp_chinese", "english"):
        entries = render_fixture_localization("simp_chinese" if language == "simp_chinese" else "english")
        scripts[f"localization/{language}/xalw_fixture_l_{language}.yml"] = f"l_{language}:\n" + "\n".join(
            f' {key}:0 "{value}"' for key, value in sorted(entries.items())
        ) + "\n"
    for relative, body in scripts.items():
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8-sig", newline="\n")
    files = {relative: pin(destination / relative) for relative in sorted(scripts)}
    result: FixtureEmission = {"schema_version": 1, "fixture_root": str(destination), "files": files,
                               "input_origin": "fixture_generated", "business_acceptance": "NOT_ASSESSED", "game_started": False}
    write_once(destination.parent / (destination.name + ".emission.json"), result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = emit_fixture(args.output)
    print(result["fixture_root"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
