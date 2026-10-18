"""Controlled initial supply only. No tick, casualty, or campaign credit.

The real Army effect is subtract_supply. Its percentage basis/clamp remains
unqualified, so actual typed before/after decides whether preparation succeeded.
"""
from __future__ import annotations

from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re

SCHEMA = "xar.ck3.r05-low-supply-fixture.v1"
MODE = "research_fixture_controlled_initial_supply"
MOD_NAME = "xar_r05_low_supply_fixture"
OUTER_REF = "mod/" + MOD_NAME + ".mod"
ONCE_FLAG = "xar_r05_supply_initializer_consumed"
EXE_SHA = "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518"
REQUIRED_CAPABILITIES = frozenset({
    "game.command.query-army-strengths-v1",
    "game.command.activate-ingame-decisions-v1",
    "game.command.query-ingame-decision-item-v1",
    "game.command.select-ingame-decision-item-v1",
    "game.command.confirm-ingame-decision-outcome-v1",
    "game.command.inspect-gui-window-tree-v1",
    "game.command.query-frontend-gui-route-v1",
})
REQUIRED_BUILD_FLAGS = (
    "XAR_CK3_ENABLE_INGAME_DECISIONS_OPEN_PRIVATE_V1",
    "XAR_CK3_ENABLE_INGAME_DECISION_ITEM_ACTIONS_PRIVATE_V1",
    "XAR_CK3_ENABLE_INGAME_DECISION_OUTCOME_PRIVATE_V1",
)
SOURCE_PINS = {
    "common/scripted_effects/10_dlc_tgp_natural_disaster_scripted_effects.txt":
        "235656afe6b7ea7419ee2c0f35437896ceaf7788e663ad3250729db122dae0cd",
    "common/script_values/tgp_natural_disaster_values.txt":
        "290406efd9a69e61981355f03f31c2bd48dcbd487936d4c814e668e901f114cd",
    "localization/english/effects_l_english.yml":
        "09cdc1360dab17dae3d6cb60e7b5b1bcef9e446bc1235fc733ef5c5fb8483c9c",
}

def require(ok, message):
    if not ok:
        raise ValueError(message)

def integer(value, name, minimum=0):
    require(type(value) is int and minimum <= value < 2**31, name + " invalid")
    return value

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def pin(path):
    path = Path(path)
    raw = path.read_bytes()
    return {"path": str(path.resolve()), "bytes": len(raw), "sha256": digest(raw)}

def write_new(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)

def config(province_id, fraction="0.999", decision_key="xar_r05_initialize_low_supply"):
    integer(province_id, "province_id", 1)
    require(type(fraction) is str and re.fullmatch(r"0\.\d{1,5}", fraction) is not None,
            "fraction must be an explicit decimal between0 and1, at most5 places")
    require(Decimal(0) < Decimal(fraction) < Decimal(1), "fraction must be strictly between0 and1")
    require(type(decision_key) is str and re.fullmatch(r"xar_r05_[a-z0-9_]{1,100}", decision_key) is not None,
            "fixture decision key invalid")
    return {"province_id": province_id, "supply_loss_fraction": fraction, "decision_key": decision_key}

def render_files(value):
    value = config(value["province_id"], value["supply_loss_fraction"], value["decision_key"])
    key, province, fraction = value["decision_key"], value["province_id"], value["supply_loss_fraction"]
    # Human-only decision, the same fixed character flag for every generated key.
    # The province iterator and army_owner scope are stock script constructs.
    # Only the unique current owner's Army is admitted by the typed runner.
    decision = f'''# CONTROLLED RESEARCH FIXTURE. Does not create soldiers or force an update.
{key} = {{
    picture = {{ reference = "gfx/interface/illustrations/decisions/decision_realm.dds" }}
    decision_group_type = realm
    ai_check_interval = 0
    desc = {key}_desc
    selection_tooltip = {key}_tooltip
    is_shown = {{ is_ai = no NOT = {{ has_character_flag = {ONCE_FLAG} }} }}
    is_valid = {{ always = yes }}
    effect = {{
        add_character_flag = {ONCE_FLAG}
        province:{province} = {{
            every_army_in_location = {{
                limit = {{ army_owner = {{ this = root }} }}
                subtract_supply = {fraction}
            }}
        }}
    }}
    ai_potential = {{ always = no }}
    ai_will_do = {{ base = 0 }}
}}
'''
    descriptor = 'name="R05 controlled low supply initializer"\nversion="0.1.0"\nsupported_version="1.20.0.4"\n'
    en = f'l_english:\n {key}:0 "RESEARCH: initialize low supplies once"\n {key}_desc:0 "Controlled fixture initialization. Only supplies are reduced. Troop counts must be checked independently."\n {key}_tooltip:0 "One controlled initial supply change; this is not natural starvation."\n {key}_confirm:0 "Initialize once"\n'
    zh = f'l_simp_chinese:\n {key}:0 "研究夹具：一次性降低初始补给"\n {key}_desc:0 "受控初始条件。仅降低补给，随后必须独立核对逐槽兵数。"\n {key}_tooltip:0 "这是夹具初始化，不是自然饥饿伤亡。"\n {key}_confirm:0 "仅初始化一次"\n'
    return {
        "descriptor.mod": b"\xef\xbb\xbf" + descriptor.encode(),
        "common/decisions/xar_r05_low_supply_fixture.txt": b"\xef\xbb\xbf" + decision.encode(),
        "localization/english/xar_r05_low_supply_fixture_l_english.yml": b"\xef\xbb\xbf" + en.encode(),
        "localization/simp_chinese/xar_r05_low_supply_fixture_l_simp_chinese.yml": b"\xef\xbb\xbf" + zh.encode(),
    }

def generate_fixture(output, *, province_id, machine_id, fraction="0.999",
                     decision_key="xar_r05_initialize_low_supply"):
    output = Path(output).resolve()
    require(not output.exists(), "new fixture output required")
    require(type(machine_id) is str and machine_id, "machine_id required")
    value = config(province_id, fraction, decision_key)
    files = render_files(value)
    output.mkdir(parents=True)
    for relative, raw in files.items():
        write_new(output / relative, raw)
    manifest = {"schema": SCHEMA, "mode": MODE, "machine_id": machine_id,
        "game_version": "1.20.0.4", "executable_sha256": EXE_SHA, "config": value,
        "source_sha256": SOURCE_PINS, "once_flag": ONCE_FLAG,
        "files": [{"relative_path": name, "bytes": len(raw), "sha256": digest(raw)} for name, raw in files.items()],
        "parameter_status": "percentage display source confirmed; native base/clamp NOT qualified",
        "live_execution_performed": False, "natural_low_stock_proven": False,
        "starvation_casualty_proven": False}
    write_new(output / "fixture-manifest.json", (json.dumps(manifest, ensure_ascii=False, indent=2)+"\n").encode())
    return manifest

def validate_fixture(path):
    path = Path(path).absolute()
    # Reject junctions as well as symlinks before resolving; never traverse a
    # caller-supplied package to validate arbitrary linked directories.
    for ancestor in (path, *path.parents):
        require(not ancestor.is_symlink() and not ancestor.is_junction(), "linked fixture path rejected")
    manifest = json.loads(path.read_bytes())
    require(manifest.get("schema") == SCHEMA and manifest.get("mode") == MODE, "not R05 fixture")
    require(manifest.get("game_version") == "1.20.0.4" and manifest.get("executable_sha256") == EXE_SHA,
            "fixture exact build changed")
    require(manifest.get("once_flag") == ONCE_FLAG and manifest.get("source_sha256") == SOURCE_PINS,
            "fixture source/one-shot contract changed")
    expected = render_files(manifest["config"])
    rows = manifest.get("files")
    require(rows == [{"relative_path": n, "bytes": len(r), "sha256": digest(r)} for n,r in expected.items()],
            "manifest differs from controlled generator")
    entries = list(path.parent.rglob("*"))
    require(all(not p.is_symlink() and not p.is_junction() for p in entries), "linked fixture entry rejected")
    actual = {p.relative_to(path.parent).as_posix() for p in entries if p.is_file()}
    require(actual == set(expected) | {path.name}, "unreviewed extra fixture files")
    for name, raw in expected.items():
        target = path.parent / name
        require(not target.is_symlink() and target.read_bytes() == raw, "fixture bytes changed: " + name)
    return manifest

def mount_fixture(profile_dir, manifest_path):
    """Prepare-only; exact generator output copied into a fresh private profile."""
    manifest_path = Path(manifest_path).resolve()
    manifest = validate_fixture(manifest_path)
    profile = Path(profile_dir).resolve()
    mount = profile / "mod" / MOD_NAME
    require(not mount.exists(), "fixture mount already exists")
    mount.mkdir(parents=True)
    files = []
    for row in manifest["files"]:
        relative = row["relative_path"]
        target = mount / relative
        write_new(target, (manifest_path.parent / relative).read_bytes())
        files.append(pin(target))
    write_new(mount / "fixture-manifest.json", manifest_path.read_bytes())
    files.append(pin(mount / "fixture-manifest.json"))
    outer = profile / OUTER_REF
    # The physical mounted path belongs to this preparation, not the portable package.
    text = 'name="R05 controlled low supply initializer"\npath=' + json.dumps(mount.as_posix()) + '\n'
    write_new(outer, text.encode())
    files.append(pin(outer))
    return {"mode": MODE, "manifest": pin(mount / "fixture-manifest.json"),
            "enabled_mods": [OUTER_REF], "files": files,
            "natural_low_stock_proven": False, "starvation_casualty_proven": False}

def validate_mount(profile_dir, mounted):
    profile = Path(profile_dir).resolve()
    require(type(mounted) is dict and mounted.get("mode") == MODE,
            "fixture mount declaration invalid")
    common = mounted.get("layout") == "common_product_carrier"
    outer_ref = "mod/product.mod" if common else OUTER_REF
    manifest_path = ((profile / "mod-content/product") if common else (profile / "mod" / MOD_NAME)) / "fixture-manifest.json"
    require(mounted.get("enabled_mods") == [outer_ref], "fixture enabled mod list changed")
    load = json.loads((profile / "dlc_load.json").read_bytes())
    require(load.get("enabled_mods") == [outer_ref] and load.get("disabled_dlcs") == [],
            "actual profile enabled mods/DLC declaration changed")
    require(pin(manifest_path) == mounted["manifest"], "mounted manifest changed")
    manifest = validate_fixture(manifest_path)
    paths = {manifest_path, *(manifest_path.parent / r["relative_path"] for r in manifest["files"]), profile / outer_ref}
    require({Path(row["path"]).resolve() for row in mounted["files"]} == paths, "mounted file inventory changed")
    for row in mounted["files"]:
        require(pin(row["path"]) == row, "mounted profile bytes changed")
    return [outer_ref]

def common_mount_receipt(profile_dir):
    """Bind the sole controlled mod copied by the existing common preparer.

    'product' is the common host's generic content-carrier slot. This metadata
    explicitly labels its contents as a research fixture, never a player product.
    """
    profile = Path(profile_dir).resolve()
    manifest_path = profile / "mod-content/product/fixture-manifest.json"
    manifest = validate_fixture(manifest_path)
    files = [pin(profile / "mod/product.mod"), pin(manifest_path)]
    files.extend(pin(manifest_path.parent / row["relative_path"]) for row in manifest["files"])
    result = {"mode": MODE,"layout":"common_product_carrier","manifest":pin(manifest_path),
        "enabled_mods":["mod/product.mod"],"files":files,
        "research_fixture_mounted":True,"player_product_or_vanilla_profile":False}
    validate_mount(profile,result)
    return result

def require_capabilities(payload):
    capabilities = payload.get("bridge_capabilities")
    require(type(capabilities) is list and all(type(x) is str for x in capabilities), "native capability list missing")
    missing = sorted(REQUIRED_CAPABILITIES - set(capabilities))
    require(not missing, "actual native capabilities missing: " + ",".join(missing))

def target_witness(snapshot, strengths, *, actor_id, army_id, carmy_id, province_id,
                   minimum_physical_current=20):
    """Consume current production DTOs, with independent public/native revisions."""
    from .army_replenishment_records_contract import normalize_regiment_replenishment_records_v1
    from .army_fixed_chunk0_preparation_contract import normalize_fixed_chunk0_preparation_inputs_v1
    require(snapshot.get("paused") is True and snapshot.get("map_ready") is True, "paused ready map required")
    require(snapshot.get("active_event") is None and snapshot.get("pending_character_interaction") is None,
            "modal blocks initializer")
    actor = snapshot.get("played_character", {})
    require(actor.get("character_id") == actor_id and actor.get("alive") is True, "actual living actor differs")
    for field in ("revision", "native_revision", "date_raw"):
        require(type(snapshot.get(field)) is int, "snapshot " + field + " missing")
    for field in ("snapshot_id", "episode_run_id"):
        require(type(snapshot.get(field)) is str and snapshot[field], "snapshot binding missing")
    diagnostics = snapshot.get("diagnostics", {})
    hello = diagnostics.get("hello", {})
    version = hello.get("expected_ck3_version", hello.get("game_version"))
    sha = hello.get("expected_ck3_sha256", hello.get("executable_sha256"))
    require(version == "1.20.0.4" and type(sha) is str and sha.lower() == EXE_SHA, "actual build missing")
    pid = diagnostics.get("bridge_pid");generation = diagnostics.get("connection_generation")
    integer(pid, "game PID", 1);integer(generation, "connection generation", 1)
    roster = snapshot.get("player_armies")
    require(type(roster) is list and all(type(r) is dict for r in roster), "complete player Army roster required")
    ids = [r.get("army_id") for r in roster]
    require(len(set(ids)) == len(ids) and all(type(i) is int for i in ids), "player Army identities ambiguous")
    candidates = [r for r in roster if r.get("owner_character_id") == actor_id and r.get("current_province_id") == province_id]
    require(len(candidates) == 1 and candidates[0].get("army_id") == army_id, "location/owner does not resolve unique selected Army")
    row = candidates[0]
    require(row.get("controllable") is True and row.get("source") == "native", "Army owner/control unavailable")
    require(row.get("in_combat") is False and row.get("retreating") is False and
            (row.get("army_state"),row.get("army_state_code")) in (("regular",1),("sieging",3)),
            "Army not observed stationary regular/sieging noncombat/nonretreat")
    require(row.get("route_read_status") == "complete_empty" and row.get("route_source_count") == 0
            and row.get("route_province_ids") == [], "Army route is not complete empty")
    require(strengths.get("queried_revision") == snapshot["revision"] and
            strengths.get("queried_native_revision") == snapshot["native_revision"] and
            strengths.get("queried_snapshot_id") == snapshot["snapshot_id"], "Strength query is not same paused frame")
    rows = strengths.get("army_strengths")
    require(type(rows) is list, "Strength rows missing")
    selected = [r for r in rows if r.get("army_id") == army_id]
    require(len(selected) == 1, "selected Strength row ambiguous")
    army = selected[0]
    require(army.get("status") == "available" and army.get("scope_role") == "player" and army.get("native_carmy_id") == carmy_id,
            "actual CArmy identity/readiness differs")
    # The production query publishes not_gathering with a null day count.
    # Retain that representation; do not rewrite unknown/null into numeric0.
    days_zero=army.get("gathering_days_left")==0
    inputs=army.get("monthly_loss_budget_inputs_v1") or {}
    not_gathering=(army.get("gathering_days_status")=="not_gathering" and
        army.get("gathering_days_left") is None and inputs.get("ready") is True and
        inputs.get("native_unit_gathering") is False and inputs.get("army_gathering_count_raw")==0)
    require(army.get("gathering_days_ready") is True and (days_zero or not_gathering),
        "gathering state unavailable/nonzero")
    if row.get("army_state_code")==3:
        # Public siege state3 is not the Unit170 raw field used by the supply
        # updater. Actual source rejects raw170==3, combat or gathering.
        require(inputs.get("ready") is True and type(inputs.get("unit_native_170_raw")) is int and
            inputs["unit_native_170_raw"]!=3 and inputs.get("native_unit_in_combat") is False and
            inputs.get("native_unit_gathering") is False and inputs.get("army_gathering_count_raw")==0,
            "stationary siege lacks actual ordinary supply admission operands")
    values = {}
    for key in ("current_supply", "current_supply_capacity", "current_supply_change_monthly"):
        raw = army.get(key + "_raw")
        require(type(raw) is int and -(2**63) <= raw < 2**63 and army.get(key + "_scale") == 100000,
                "actual Q100000 " + key + " missing")
        values[key + "_raw"] = raw
    records = normalize_regiment_replenishment_records_v1(army.get("regiment_replenishment_records_v1"))
    require(len(records) == army.get("regiment_count") and all(r["ready"] for r in records), "full ordered DATA roster incomplete")
    require(len({r["army_regiment_id"] for r in records}) == len(records), "duplicate ArmyRegiment IDs")
    physical = {};aliases = [];persistent_ids = set()
    for regiment in records:
        for data in regiment["records"]:
            key = (data["persistent_regiment_id"], data["chunk_index"])
            value = (data["current_soldiers"],data["maximum_soldiers"],data["state_raw"])
            require(value[0] >= 0 and value[1] >= value[0], "nonordinary physical count")
            require(key not in physical or physical[key] == value, "conflicting physical DATA aliases")
            physical[key] = value;persistent_ids.add(key[0])
            aliases.append([regiment["army_regiment_id"],data["record_index"],*key])
    integer(minimum_physical_current, "minimum_physical_current")
    require(physical and sum(v[0] for v in physical.values()) >= minimum_physical_current,
            "too few physical soldiers for this stage")
    fixed = normalize_fixed_chunk0_preparation_inputs_v1(army.get("fixed_chunk0_preparation_inputs_v1"),
        expected_army_id=army_id, expected_carmy_id=carmy_id)
    require(fixed is not None and fixed["ready"] and fixed["referenced_persistent_ids_complete"], "current persistent classification unavailable")
    guards = {r["persistent_regiment_id"]:r["containing_guard_138_raw"] for r in fixed["persistent_regiments"]}
    require(set(guards) == persistent_ids and len(guards) == len(fixed["persistent_regiments"]),
            "persistent classification references incomplete/duplicate")
    # A regular Army can contain both ordinary and event-origin DATA. Never
    # reject that legitimate target solely because one persistent raw138==1.
    # This is inventory provenance, not an enum name or a supply-loss predicate.
    return {"machine_independent_frame": {k:snapshot[k] for k in ("snapshot_id","revision","native_revision","date_raw","episode_run_id")},
        "actor_id": actor_id,"army_id":army_id,"carmy_id":carmy_id,"province_id":province_id,"pid":pid,"generation":generation,
        "army_state":row.get("army_state"),"army_state_code":row.get("army_state_code"),
        "gathering_days_status":army.get("gathering_days_status"),
        **values,"ordered_regiment_ids":[r["army_regiment_id"] for r in records],"data_aliases":aliases,
        "physical_slots":[{"persistent_regiment_id":k[0],"chunk_index":k[1],"current_soldiers":v[0],"maximum_soldiers":v[1],"state_raw":v[2]} for k,v in sorted(physical.items())],
        "raw138_by_persistent":[[k,guards[k]] for k in sorted(guards)],
        "mixed_raw138_classes":len(set(guards.values())) > 1,
        "native_cached_current":army.get("current_soldiers"),"native_cached_maximum":army.get("maximum_soldiers")}

def assess_initialization(before, after):
    invariants = ("actor_id","army_id","carmy_id","province_id","pid","generation","ordered_regiment_ids",
                  "data_aliases","physical_slots","raw138_by_persistent","native_cached_current","native_cached_maximum",
                  "army_state","army_state_code","gathering_days_status")
    require(all(before[k] == after[k] for k in invariants), "initializer changed target identity/physical soldiers/roster")
    for key in ("date_raw","episode_run_id"):
        require(before["machine_independent_frame"][key] == after["machine_independent_frame"][key], "initializer crossed date/episode")
    require(0 <= after["current_supply_raw"] < before["current_supply_raw"], "no independently observed nonnegative supply decrease")
    require(before["current_supply_capacity_raw"] == after["current_supply_capacity_raw"],
            "initializer changed observed supply capacity")
    stock,rate = after["current_supply_raw"],after["current_supply_change_monthly_raw"]
    low = 0 <= stock < 1000000
    return {"status":"prepared_low_stock" if low else "supply_changed_not_low_stock",
            "actual_before_stock_raw":before["current_supply_raw"],"actual_after_stock_raw":stock,
            "physical_soldiers_unchanged":True,"low_stock_observed":low,
            "positive_low_stock_can_cross_zero_in_one_same_rate_update":0 < stock < 1000000 and rate < 0 and stock <= -rate,
            "initialization_at_zero":stock == 0,"natural_low_stock_proven":False,"natural_update_observed":False,
            "starvation_casualty_proven":False,"fixture_mode":MODE,"action_replay_allowed":False}
