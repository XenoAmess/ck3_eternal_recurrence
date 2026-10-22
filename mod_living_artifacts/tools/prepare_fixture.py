"""Emit external initial inputs for checkpoint/native core acceptance.

No launcher, host, runtime download, business terminal value, automatic feeding,
production-effect override, or assertion/PASS marker is emitted here. An optional
declared initial imprint is a persistence input and grants no feeding credit.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import sys
from textwrap import dedent
from typing import Literal, TypedDict

PRODUCT_TOOLS = Path(__file__).resolve().parent
if str(PRODUCT_TOOLS) not in sys.path:
    sys.path.insert(0, str(PRODUCT_TOOLS))

from acceptance_contract import Object, Pin, integer, mapping, pin, require, write_once
from living_artifacts_core import render_fixture_effects, render_fixture_localization


class FixtureEmission(TypedDict):
    schema_version: Literal[2]
    fixture_root: str
    files: dict[str, Pin]
    input_origin: Literal["fixture_generated"]
    business_acceptance: Literal["NOT_ASSESSED"]
    game_started: Literal[False]


@dataclass(frozen=True)
class InitialFeedingImprint:
    flag: Literal["primary_armament"]
    days: Literal[90]
    origin: Literal["fixture-initial-state"]
    feeding_action_credit: Literal[False]

    def __post_init__(self) -> None:
        require(type(self.flag) is str and self.flag == "primary_armament" and
                type(self.days) is int and self.days == 90 and
                type(self.origin) is str and self.origin == "fixture-initial-state" and
                self.feeding_action_credit is False, "Declared initial imprint fields/types differ")

    @classmethod
    def parse(cls, value: object) -> InitialFeedingImprint:
        row = mapping(value, "declared initial feeding imprint")
        require(set(row) == {"flag", "days", "origin", "feeding_action_credit"}, "Closed initial imprint declaration required")
        require(type(row["flag"]) is str and row["flag"] == "primary_armament" and
                type(row["origin"]) is str and row["origin"] == "fixture-initial-state" and
                row["feeding_action_credit"] is False, "Initial imprint cannot claim a feeding action")
        integer(row["days"], "initial imprint duration", 90, 90)
        return cls("primary_armament", 90, "fixture-initial-state", False)

    def to_json(self) -> Object:
        return {"flag": self.flag, "days": self.days, "origin": self.origin, "feeding_action_credit": self.feeding_action_credit}


def render_observer_effects(*, feeding_imprint: InitialFeedingImprint | None = None) -> str:
    """Initialize refs once; actual observation belongs to retained save/native reads.

    Hidden-event debug_log has no dynamic localization context (R2 actual RED).
    No periodic observer, logger expression, or business-state rewrite is emitted.
    """
    materials = "\n".join(f"set_variable = {{ name = xalw_fixture_material_{rarity} value = scope:xalw_test_material_{rarity} }}"
                          for rarity in ("common", "masterwork", "famed", "illustrious"))
    initial = dedent("""
        xalw_fixture_initialize_effect = {
            save_scope_as = xalw_fixture_owner
            xalw_test_prepare_owner_effect = yes
            set_variable = { name = xalw_fixture_target value = scope:xalw_test_living }
            set_variable = { name = xalw_fixture_initial_day value = current_date }
            scope:xalw_test_living = {
                # G01 input: one monthly +8 must cross 1/92 -> 2/0 naturally.
                set_variable = { name = xalw_xp_in_level value = 92 }
                # Four weapon materials are deliberately non-diet input.
                set_variable = { name = xalw_diet value = flag:armor }
    """).strip()
    if feeding_imprint is not None:
        require(isinstance(feeding_imprint, InitialFeedingImprint), "Validated initial imprint value required")
        initial += ("\n        # Declared fixture persistence input; no feeding action or XP credit.\n"
                    f"        set_variable = {{ name = xalw_feeding_imprint value = flag:{feeding_imprint.flag} days = {feeding_imprint.days} }}")
    return initial + "\n    }\n" + materials + dedent("""
            debug_log = "XALW_FIXTURE_READY_V1"
        }
    """)


def emit_fixture(destination: Path, *, feeding_imprint: InitialFeedingImprint | None = None) -> FixtureEmission:
    destination = destination.resolve()
    repo = Path(__file__).resolve().parents[2]
    require(not destination.is_relative_to(repo) and not destination.exists(), "Use a new external fixture directory")
    scripts: dict[str, str] = {
        "descriptor.mod": 'name="Living Artifacts acceptance inputs (external only)"\nsupported_version="1.20.*"\n',
        "common/scripted_effects/xalw_fixture_inputs.txt": render_fixture_effects(),
        "common/scripted_effects/xalw_fixture_observer.txt": render_observer_effects(feeding_imprint=feeding_imprint),
        "common/on_action/xalw_fixture_bootstrap.txt": dedent("""
            on_game_start_after_lobby = { on_actions = { xalw_fixture_bootstrap } }
            xalw_fixture_bootstrap = { effect = { every_player = { xalw_fixture_initialize_effect = yes } } }
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
    result: FixtureEmission = {"schema_version": 2, "fixture_root": str(destination), "files": files,
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
