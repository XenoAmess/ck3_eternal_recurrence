"""Initial inputs and exact deployment closure for the 47-day threshold case."""
from __future__ import annotations

import importlib
import json
from pathlib import Path
import sys

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import acceptance_adapter as core
from acceptance_contract import Object, Pin, field, json_value, mapping, object_value, pin, read, require, text, write_once
from checkpoint_callback import checked_pin
from living_artifacts_core import render_fixture_effects, render_fixture_localization
from prepare_fixture import FixtureEmission

CASE = "threshold_suppression"
CONTRACT_NAME = "threshold_suppression.contract.json"
SOURCES = ("prepare_threshold_fixture.py", "threshold_acceptance_adapter.py", "acceptance_adapter.py", "acceptance_contract.py",
           "prepare_fixture.py", "living_artifacts_core.py", "living_artifacts_model.py", "living_artifacts_content.py",
           "checkpoint_callback.py", "checkpoint_artifacts.py", "checkpoint_producer.py", "startup_actor_binding.py",
           "management_event_contract.py", "inventory_gui_contract.py", "native_interruption_contract.py")


def same_json(left: object, right: object) -> bool:
    return json.dumps(json_value(left), sort_keys=True, separators=(",", ":")) == json.dumps(json_value(right), sort_keys=True, separators=(",", ":"))


def tree(root: Path) -> dict[str, Pin]:
    require(root.is_dir() and not any(path.is_symlink() for path in root.rglob("*")), "Exact ordinary deployment directory required")
    return {path.relative_to(root).as_posix(): pin(path) for path in sorted(root.rglob("*")) if path.is_file()}


def render_initial_inputs() -> str:
    """No settle/refresh/train/suppress call, timer, success flag or final-state write."""
    numeric = {"schema_version": 2, "level": 10, "xp_in_level": 992, "pending_xp": 0, "growth_sequence": 0,
               "last_notified_sequence": 0, "resonance": 20, "suppression_chain": 0, "unsuppressed_equipped_months": 0,
               "personality": 1, "affix_1": 1, "affix_rank_1": 1, "curse_1": 1, "curse_rank_1": 2}
    setters = "\n".join(f"set_variable = {{ name = xalw_{key} value = {value} }}" for key, value in numeric.items())
    materials = "\n".join(f"xalw_test_create_{rarity}_material_effect = yes\n"
        f"set_variable = {{ name = xalw_fixture_material_{rarity} value = scope:xalw_test_material_{rarity} }}"
        for rarity in ("common", "masterwork", "famed", "illustrious"))
    return f'''xalw_threshold_initialize_effect = {{
save_scope_as = xalw_fixture_owner
# Spendable initial resources and nonzero stress input; actual baselines are read.
add_gold = 500
add_prestige = 200
add_stress = 20
create_artifact = {{
 name = xalw_threshold_living_name
 description = xalw_test_living_description
 type = sword visuals = sword modifier = artifact_prowess_1_modifier
 wealth = 40 quality = 40 save_scope_as = xalw_test_living
 history = {{ type = created_before_history }}
}}
scope:xalw_test_living = {{
{setters}
set_variable = {{ name = xalw_kind value = flag:living }}
set_variable = {{ name = xalw_diet value = flag:armor }}
set_variable = {{ name = xalw_attuned_character value = artifact_owner }}
set_variable = {{ name = xalw_last_settled_month value = xalw_current_month_value }}
set_variable = {{ name = xalw_test_fixture_input value = yes }}
set_variable = {{ name = xalw_star_named value = yes }}
}}
set_variable = {{ name = xalw_fixture_target value = scope:xalw_test_living }}
set_variable = {{ name = xalw_fixture_initial_day value = current_date }}
{materials}
# Start the ordinary production owner lifecycle; no tested terminal effect.
xalw_discover_owner_effect = yes
debug_log = "XALW_THRESHOLD_INPUTS_READY_V1"
}}
'''


def emit_fixture(destination: Path) -> FixtureEmission:
    destination = destination.resolve()
    require(not destination.is_relative_to(TOOLS.parents[1]) and not destination.exists(), "New external fixture directory required")
    # Reuse only the four independent material constructors, not owner/level helpers.
    material_effects = render_fixture_effects().split("xalw_test_prepare_owner_effect = {", 1)[0]
    scripts = {"descriptor.mod": 'name="Living Artifacts threshold initial inputs"\nsupported_version="1.20.*"\n',
        "common/scripted_effects/xalw_threshold_inputs.txt": material_effects + render_initial_inputs(),
        "common/on_action/xalw_threshold_bootstrap.txt": "on_game_start_after_lobby = { on_actions = { xalw_threshold_bootstrap } }\nxalw_threshold_bootstrap = { effect = { every_player = { xalw_threshold_initialize_effect = yes } } }\n"}
    for language in ("english", "simp_chinese"):
        entries = render_fixture_localization("english" if language == "english" else "simp_chinese")
        entries["xalw_threshold_living_name"] = "★" + entries["xalw_test_living_name"]
        scripts[f"localization/{language}/xalw_threshold_l_{language}.yml"] = f"l_{language}:\n" + "\n".join(f' {key}:0 "{value}"' for key, value in sorted(entries.items())) + "\n"
    for relative, body in scripts.items():
        path = destination / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8-sig", newline="\n")
    emission: FixtureEmission = {"schema_version": 2, "fixture_root": str(destination), "files": tree(destination),
        "input_origin": "fixture_generated", "business_acceptance": "NOT_ASSESSED", "game_started": False}
    write_once(destination.parent / (destination.name + ".emission.json"), emission)
    return emission


def prepare_inputs(context: object) -> Object:
    output = Path(text(field(context, "output"), "output")).resolve()
    fixture = emit_fixture(output / "external-threshold-fixture")
    root = Path(fixture["fixture_root"])
    product = Path(text(field(field(context, "case_inputs"), "product_dir"), "formal product")).resolve()
    write_once(root / "_case_contract.json", {"product": "living-artifacts", "case": CASE, "config": field(context, "case_contract"),
        "fixture_emission": fixture, "caller_sources": {name: pin(TOOLS / name) for name in SOURCES},
        "contract_source": pin(TOOLS / CONTRACT_NAME), "formal_files": tree(product), "business_pass": False})
    preparation = importlib.import_module("ck3_mod_acceptance_prepare")
    if not isinstance(preparation, core.Preparation):
        raise ValueError("Actual shared fixture preparation API required")
    prepared = object_value(preparation.materialize_fixture_profile(mapping(context, "preparation"), root, product,
        field(field(context, "case_inputs"), "plain_configuration")))
    return object_value({"startup": {"mode": "fixture", "state_dir": prepared["state_dir"], "fixture_start_policy": prepared["fixture_start_policy"]},
        "initial_plan": write_once(output / "initial-plan.json", {"steps": []}), "profile_preparation": prepared,
        "fixture_emission": fixture, "runtime_status": "NOT_RUN", "business_pass": False, "product_release_pass": False})


def prepared_sources(context: object, state: Path) -> tuple[Pin, ...]:
    """Source, deployment and shared loaded-file table, before any game action."""
    require(state.resolve() == Path(text(field(context, "state_dir"), "allocated state")).resolve(), "Crossed allocated state")
    root = state / "profile/mod-content/fixture"
    manifest = read(root / "_case_contract.json")
    require(set(manifest) == {"product", "case", "config", "fixture_emission", "caller_sources", "contract_source", "formal_files", "business_pass"} and
        manifest["product"] == "living-artifacts" and manifest["case"] == CASE and manifest["business_pass"] is False and
        same_json(manifest["config"], field(context, "case_contract")), "Threshold deployed contract differs")
    callers = mapping(manifest["caller_sources"], "source closure")
    require(set(callers) == set(SOURCES), "Threshold source closure differs")
    refs = [core._checked_pin(callers[name], "threshold source", TOOLS / name) for name in SOURCES]
    refs.append(core._checked_pin(manifest["contract_source"], "threshold contract", TOOLS / CONTRACT_NAME))
    emission = mapping(manifest["fixture_emission"], "emission")
    require(set(emission) == set(FixtureEmission.__required_keys__) and emission["schema_version"] == 2 and type(emission["schema_version"]) is int and
        emission["input_origin"] == "fixture_generated" and emission["business_acceptance"] == "NOT_ASSESSED" and emission["game_started"] is False, "Fixture cannot grant game credit")
    emitted = mapping(emission["files"], "emitted files")
    for deployed, originals, extra in ((root, emitted, {"_case_contract.json"}), (state / "profile/mod-content/product", mapping(manifest["formal_files"], "formal files"), set())):
        require(set(tree(deployed)) == set(originals) | extra, "Loaded exact file closure differs")
        for relative, raw in originals.items():
            require(not Path(relative).is_absolute() and ".." not in Path(relative).parts, "Input relative path escaped root")
            original = checked_pin(raw, "original input")
            copied = pin(deployed / relative)
            require((copied["bytes"], copied["sha256"]) == (original["bytes"], original["sha256"]), "Loaded input bytes differ")
            refs.append(copied)
    require(read(state / "profile/dlc_load.json") == {"enabled_mods": ["mod/product.mod", "mod/fixture.mod"], "disabled_dlcs": []}, "Only formal product and threshold inputs may mount")
    refs.extend((pin(root / "_case_contract.json"), pin(state / "profile/dlc_load.json")))
    prepared_pin = checked_pin(field(read(state / "preparation.json"), "preparation"), "shared preparation")
    prepared = read(Path(prepared_pin["path"]))
    require(field(prepared, "schema") == "ck3-mod-acceptance-prepared-fixture-v1" and Path(text(field(prepared, "state_dir"), "prepared state")).resolve() == state.resolve(), "Shared preparation crossed profile/schema")
    table = mapping(field(prepared, "files"), "shared loaded files")
    loaded = {"mod/product.mod", "mod/fixture.mod", "dlc_load.json"}
    loaded.update("mod-content/product/" + name for name in mapping(manifest["formal_files"], "formal files"))
    loaded.update("mod-content/fixture/" + name for name in set(emitted) | {"_case_contract.json"})
    require(loaded <= set(table), "Shared preparation omits an actual input")
    refs.extend(core._checked_pin(table[name], "shared deployed file", state / "profile" / name) for name in sorted(loaded))
    refs.append(prepared_pin)
    return tuple(refs)
