"""Emit external, source-bound NPC inputs; never execute or impersonate AI.

Initial actors are selected from real existing adult AI characters. Runtime
references and eligibility must subsequently be read from an actual save/native
observation. Source qualification is not live fixture or business acceptance.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import sys
from typing import Literal, TypedDict

REPO = Path(__file__).resolve().parents[2]
for directory in (REPO / "tools", Path(__file__).resolve().parent):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

from acceptance_contract import Pin, field, integer, mapping, pin, require, utc_now, write_once
from ck3_live_run_id import current_machine_id
from living_artifacts_model import FEEDING_XP, SCHEMA_VERSION, Rarity

Role = Literal["landed", "baron", "courtier", "fragile", "queue"]
RARITIES: tuple[tuple[Rarity, int], ...] = (("common", 10), ("masterwork", 40), ("famed", 75), ("illustrious", 100))
require(tuple(rarity for rarity, _ in RARITIES) == tuple(FEEDING_XP), "NPC rarity inputs must follow the shared feeding contract")
EXPECTED_EXE_SHA = "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518"


@dataclass(frozen=True)
class SourceBinding:
    relative: str
    sha256: str

    def __post_init__(self) -> None:
        require(type(self.relative) is str and re.fullmatch(r"[A-Za-z0-9_./]+", self.relative) is not None and
                not self.relative.startswith("/") and ".." not in self.relative.split("/"), "Unsafe source path")
        require(type(self.sha256) is str and re.fullmatch(r"[0-9a-f]{64}", self.sha256) is not None, "Source SHA required")


# Exact 1.20.0.4 source: global iteration; candidate lists; AI/rank/courtier
# predicates; artifact construction; native eligibility; startup; sword slot.
SOURCES: tuple[SourceBinding, ...] = (
    SourceBinding("common/scripted_effects/00_setup_tests_effect.txt", "07382901b1c6635e702006956a3536d374a939686da6089a6c9f0205940d0162"),
    SourceBinding("common/scripted_effects/00_secret_effects.txt", "4b86ba489602089969293c810a6aaee81ea5d213f7c0456f051ae8785addf7f9"),
    SourceBinding("common/scripted_effects/00_ai_conqueror_effects.txt", "1b3856cb09b3cd9c8bbca00fa9d293f846bf675039773d8f541b178b709a1385"),
    SourceBinding("common/scripted_effects/00_accolades_scripted_effects.txt", "4d0ebc960c72fb091507acb9569d4b0e0cac53404b369cb9e2d54ea54b6d0f2c"),
    SourceBinding("common/scripted_effects/00_ep1_artifact_creation_effects.txt", "1b60d78e54e1ebff7601bd13e59b2251cff47d96f595a4431c666fa3ee11a831"),
    SourceBinding("common/character_interactions/00_artifact_interactions.txt", "6272e3df8fcdfbeda14a83f3d4410251db5176496e0647f0833e252653aa8e7a"),
    SourceBinding("common/on_action/game_start.txt", "f2f5ce78a03cfbdba0f5a68fc466f8bac89126cdd4843545b4ad6d468ed238b8"),
    SourceBinding("common/on_action/inventory_on_actions.txt", "fcab2d2e740d32f3e8b5cb4058196dd3592153343ea3ae7a41c980fc0a334f67"),
    SourceBinding("common/artifacts/types/00_types.txt", "302f44a67d81185787135170904fad8022f4a23c0e3986573153ec57bcd4b83a"),
    SourceBinding("common/modifiers/00_artifact_modifiers.txt", "06495c2f0b39634895f9587a4f3fb26725183d913851d4ea1ec6f4d3b8efe059"),
)


@dataclass(frozen=True)
class NpcFixtureSpec:
    queue_count: int = 51

    def __post_init__(self) -> None:
        require(type(self.queue_count) is int and self.queue_count in (0, 51), "queue_count must be strict 0 or 51")

    @classmethod
    def parse(cls, value: object) -> NpcFixtureSpec:
        row = mapping(value, "NPC fixture spec")
        require(set(row) == {"schema_version", "queue_count"}, "NPC spec fields differ")
        integer(field(row, "schema_version"), "NPC spec version", 1, 1)
        return cls(integer(field(row, "queue_count"), "queue count", 0, 51))

    def to_json(self) -> dict[str, int]:
        return {"schema_version": 1, "queue_count": self.queue_count}


class RoleInput(TypedDict):
    role: Role
    owner_reference_variable: str
    target_reference_variable: str | None
    material_reference_variables: dict[Rarity, str]
    initial_gold_added: int
    initial_prestige_added: int
    identity_status: Literal["UNBOUND_UNTIL_ACTUAL_SAVE"]


class NpcFixtureEmission(TypedDict):
    schema: Literal["living-artifacts-npc-input-emission-v1"]
    schema_version: Literal[1]
    machine_id: str
    observed_at_utc: str
    fixture_root: str
    spec: dict[str, int]
    files: dict[str, Pin]
    source_bindings: dict[str, Pin]
    roles: list[RoleInput]
    queue_reference_variables: list[str]
    input_origin: Literal["fixture_generated"]
    qualification_scope: Literal["exact-source-and-initial-script-only"]
    runtime_status: Literal["NOT_RUN"]
    business_acceptance: Literal["NOT_ASSESSED"]
    coverage_gaps: list[str]


def verify_source(game: Path, source: SourceBinding) -> Pin:
    require(isinstance(game, Path) and isinstance(source, SourceBinding), "Typed source inputs required")
    root = game.resolve()
    target = (root / source.relative).resolve()
    require(target.is_relative_to(root), "Source escaped game root")
    result = pin(target)
    require(result["sha256"] == source.sha256, f"Exact CK3 source drift: {source.relative}")
    return result


def qualify_sources(game: Path) -> dict[str, Pin]:
    require(isinstance(game, Path), "Game Path required")
    game = game.resolve()
    result = {source.relative: verify_source(game, source) for source in SOURCES}
    executable = pin(game.parent / "binaries" / "ck3.exe")
    require(executable["sha256"] == EXPECTED_EXE_SHA, "Only exact CK3 1.20.0.4 is source-qualified")
    result["binaries/ck3.exe"] = executable
    result["product/prepare_npc_fixture.py"] = pin(Path(__file__))
    result["product/living_artifacts_core.py"] = pin(Path(__file__).with_name("living_artifacts_core.py"))
    result["product/living_artifacts_model.py"] = pin(Path(__file__).with_name("living_artifacts_model.py"))
    require(SCHEMA_VERSION == 2, "Initial artifact schema requires reviewed migration")
    return result


def _block(name: str, body: str) -> str:
    return name + " = {\n" + "\n".join("\t" + line for line in body.strip().splitlines()) + "\n}\n"


def _item(role: Role, kind: str, score: int, *, living: bool = False, undiscovered: bool = False) -> str:
    scope = "xalw_npc_created_item"
    body = f"""create_artifact = {{
    name = xalw_npc_{role}_{kind}_name
    description = xalw_npc_input_description
    type = sword
    visuals = sword
    modifier = artifact_prowess_1_modifier
    wealth = {score}
    quality = {score}
    save_scope_as = {scope}
    history = {{ type = created_before_history }}
}}
scope:{scope} = {{
    set_variable = {{ name = xalw_npc_fixture_input value = yes }}
"""
    if not undiscovered:
        body += "    set_variable = { name = xalw_schema_version value = 2 }\n"
        if living:
            body += "    if = { limit = { NOT = { xalw_is_living_trigger = yes } } xalw_awaken_artifact_effect = yes }\n"
        else:
            body += "    set_variable = { name = xalw_kind value = flag:ordinary }\n"
    body += "}\n"
    variable = "xalw_npc_fixture_target" if living else f"xalw_npc_fixture_{kind}"
    body += f"set_variable = {{ name = {variable} value = scope:{scope} }}\n"
    body += f"""if = {{
    limit = {{ OR = {{
        NOT = {{ can_equip_artifact = scope:{scope} }}
        NOT = {{ can_benefit_from_artifact = scope:{scope} }}
        scope:{scope} = {{ is_equipped = yes }}
    }} }}
    set_variable = {{ name = xalw_npc_fixture_initial_eligibility_gap value = yes }}
}}
"""
    return body


def render_npc_effects(spec: NpcFixtureSpec) -> str:
    require(type(spec) is NpcFixtureSpec, "Validated NPC spec required")
    definitions: list[str] = []
    selectors: dict[Role, str] = {
        "landed": "is_landed = yes\nhighest_held_title_tier >= tier_county\nhealth >= 4",
        "baron": "is_landed = yes\nhighest_held_title_tier = tier_barony\nhealth >= 4",
        "courtier": "is_landed = no\nis_ruler = no\nis_courtier = yes\nhealth >= 4",
        "fragile": "is_landed = no\nis_ruler = no\nis_courtier = yes\nhealth >= 2\nhealth < 4\ngold >= 0\ngold < 20\nprestige < 50",
        "queue": "is_landed = no\nis_ruler = no\nis_courtier = yes\nhealth >= 4",
    }
    roles: tuple[Role, ...] = ("landed", "baron", "courtier", "fragile") + (("queue",) if spec.queue_count else ())
    initialize: list[str] = ["save_scope_as = xalw_npc_fixture_player"]
    for role in roles:
        reference = f"xalw_npc_fixture_owner_{role}"
        create = "save_scope_as = xalw_npc_selected\nset_variable = { name = xalw_npc_fixture_claimed value = yes }\n"
        create += f"scope:xalw_npc_fixture_player = {{ set_variable = {{ name = {reference} value = scope:xalw_npc_selected }} }}\n"
        if role != "fragile":
            create += "add_gold = 500\nadd_prestige = 200\n"
        if role == "queue":
            create += "".join(_item(role, f"queue_item_{index:03d}", 10, undiscovered=True) for index in range(1, spec.queue_count + 1))
            create += "set_variable = { name = xalw_npc_fixture_queue_tail value = scope:xalw_npc_created_item }\n"
        else:
            create += _item(role, "target", 100, living=True)
            create += "".join(_item(role, "material_" + rarity, score) for rarity, score in RARITIES)
        # The product game-start sweep can run before these external inputs exist.
        # Hand the finished owner to the normal discovery/month/day-one lifecycle;
        # never invoke the AI action, queue implementation or settlement directly.
        create += "xalw_discover_owner_effect = yes\n"
        create += "set_variable = { name = xalw_npc_fixture_initial_inputs_created value = yes }\n"
        definitions.append(_block(f"xalw_npc_fixture_create_{role}_effect", create))
        select = f"""every_living_character = {{
    limit = {{
        is_alive = yes
        is_adult = yes
        is_ai = yes
        is_imprisoned = no
        has_any_artifact = no
        NOT = {{ has_variable = xalw_npc_fixture_claimed }}
        {selectors[role]}
    }}
    add_to_list = xalw_npc_candidates_{role}
}}
random_in_list = {{
    list = xalw_npc_candidates_{role}
    xalw_npc_fixture_create_{role}_effect = yes
}}
if = {{
    limit = {{ NOT = {{ has_variable = {reference} }} }}
    set_variable = {{ name = xalw_npc_fixture_missing_{role} value = yes }}
    debug_log = "XALW_NPC_INPUT_MISSING_{role.upper()}_V1"
}}
"""
        initialize.append(select)
    initialize.append('debug_log = "XALW_NPC_INITIAL_INPUTS_CREATED_V1"')
    definitions.append(_block("xalw_npc_fixture_initialize_effect", "\n".join(initialize)))
    return "\n".join(definitions)


def render_npc_localization(spec: NpcFixtureSpec, language: Literal["english", "simp_chinese"]) -> str:
    require(type(spec) is NpcFixtureSpec and type(language) is str and language in ("english", "simp_chinese"), "Validated locale inputs required")
    entries = {"xalw_npc_input_description": "NPC fixture initial input; not an AI action." if language == "english" else "NPC验收初始输入，不代表AI已经采取行动。"}
    for role in ("landed", "baron", "courtier", "fragile"):
        entries[f"xalw_npc_{role}_target_name"] = f"NPC {role} target"
        for rarity, _ in RARITIES:
            entries[f"xalw_npc_{role}_material_{rarity}_name"] = f"NPC {role} {rarity} material"
    for index in range(1, spec.queue_count + 1):
        entries[f"xalw_npc_queue_queue_item_{index:03d}_name"] = f"NPC queue input {index:03d}"
    return f"l_{language}:\n" + "\n".join(f' {key}:0 "{value}"' for key, value in sorted(entries.items())) + "\n"


def emit_npc_fixture(destination: Path, *, game: Path, spec: NpcFixtureSpec = NpcFixtureSpec()) -> NpcFixtureEmission:
    require(isinstance(destination, Path) and isinstance(game, Path) and type(spec) is NpcFixtureSpec, "Typed emission inputs required")
    destination = destination.resolve()
    manifest = destination.parent / (destination.name + ".emission.json")
    require(not destination.is_relative_to(REPO) and not destination.exists() and not manifest.exists(), "Use a new external fixture and manifest path")
    sources = qualify_sources(game)
    scripts = {
        "descriptor.mod": 'name="Living Artifacts NPC acceptance initial inputs (external only)"\nsupported_version="1.20.*"\n',
        "common/scripted_effects/xalw_npc_fixture_inputs.txt": render_npc_effects(spec),
        "common/on_action/xalw_npc_fixture_bootstrap.txt": """on_game_start_after_lobby = { on_actions = { xalw_npc_fixture_bootstrap } }
xalw_npc_fixture_bootstrap = { effect = { every_player = {
    if = { limit = { NOT = { has_variable = xalw_npc_fixture_initialized } }
        set_variable = { name = xalw_npc_fixture_initialized value = yes }
        xalw_npc_fixture_initialize_effect = yes
    }
} } }
""",
    }
    for language in ("english", "simp_chinese"):
        scripts[f"localization/{language}/xalw_npc_fixture_l_{language}.yml"] = render_npc_localization(spec, language)
    for relative, body in scripts.items():
        output = destination / relative
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("x", encoding="utf-8-sig", newline="\n") as stream:
            stream.write(body)
    roles: list[RoleInput] = []
    for role in ("landed", "baron", "courtier", "fragile"):
        roles.append({"role": role, "owner_reference_variable": f"xalw_npc_fixture_owner_{role}",
                      "target_reference_variable": "xalw_npc_fixture_target",
                      "material_reference_variables": {rarity: "xalw_npc_fixture_material_" + rarity for rarity, _ in RARITIES},
                      "initial_gold_added": 0 if role == "fragile" else 500,
                      "initial_prestige_added": 0 if role == "fragile" else 200,
                      "identity_status": "UNBOUND_UNTIL_ACTUAL_SAVE"})
    if spec.queue_count:
        roles.append({"role": "queue", "owner_reference_variable": "xalw_npc_fixture_owner_queue", "target_reference_variable": None,
                      "material_reference_variables": {}, "initial_gold_added": 500, "initial_prestige_added": 200,
                      "identity_status": "UNBOUND_UNTIL_ACTUAL_SAVE"})
    result: NpcFixtureEmission = {"schema": "living-artifacts-npc-input-emission-v1", "schema_version": 1,
        "machine_id": current_machine_id(), "observed_at_utc": utc_now(), "fixture_root": str(destination), "spec": spec.to_json(),
        "files": {relative: pin(destination / relative) for relative in sorted(scripts)}, "source_bindings": sources, "roles": roles,
        "queue_reference_variables": [f"xalw_npc_fixture_queue_item_{index:03d}" for index in range(1, spec.queue_count + 1)],
        "input_origin": "fixture_generated", "qualification_scope": "exact-source-and-initial-script-only", "runtime_status": "NOT_RUN",
        "business_acceptance": "NOT_ASSESSED", "coverage_gaps": [
            "Existing adult AI selection may lack a role; actual root missing-role flags must be read before acceptance.",
            "Native can_equip/can_benefit and initial unequipped guards must be observed; script emission does not establish legality.",
            "Production discovery is handed the completed owner once; real saved scheduling markers, not this call or the input marker, establish initial lifecycle readiness.",
            "Creation ownership callbacks and explicit discovery may inspect queue inputs before observation; 51 unchecked items and tail scheduling are NOT qualified.",
            "Initial awakening is forced through the production initializer; neither natural awakening chance nor later AI choices are qualified.",
            "No dangerous level/curse, protected/best-backup inventory, resource recovery, event branch, or I04 suppression scenario is supplied.",
            "Single-player initialization only; actual NPC adapter, CI registration and live acceptance remain pending.",
        ]}
    write_once(manifest, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--queue-count", type=int, choices=(0, 51), default=51)
    args = parser.parse_args()
    result = emit_npc_fixture(args.output, game=args.game, spec=NpcFixtureSpec(args.queue_count))
    print(result["fixture_root"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
