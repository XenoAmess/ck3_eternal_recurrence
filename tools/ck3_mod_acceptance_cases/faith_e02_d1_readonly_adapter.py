"""Original D1 save, fresh native identity, finite queries and UI selection only."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import importlib
import sys
import json
from pathlib import Path

CASE = "faith-engine-e02-d1-head-pilgrimage-readonly-v1"
PRODUCT = "faith-engine"
SAVE_BYTES = 68958787
SAVE_SHA256 = "62d18fe254d658356671269f194319a316729394da6f38b32da0d503bae1cd58"
READONLY_TOOLS = frozenset({
    "ck3_query_player_religion_context_v1", "ck3_query_player_rite_governance_v1",
    "ck3_query_player_pilgrimage_activities_v1",
})
SCENE_TOOLS = frozenset({
    "ck3_take_snapshot", "ck3_get_capabilities", "ck3_query_campaign_root_context_v1",
    "ck3_query_current_event_window_context_v1", "ck3_open_ingame_decisions_v1",
    "ck3_inspect_gui_window_tree_v1", "ck3_query_ingame_decision_item_v1",
    "ck3_select_ingame_decision_item_v1",
}) | READONLY_TOOLS
LIFECYCLE_TOOLS = frozenset({
    "ck3_query_normal_exit_context_v1", "ck3_request_normal_exit_v1",
    "ck3_observe_normal_exit_v1",
})
REQUIRED_TOOLS = SCENE_TOOLS | LIFECYCLE_TOOLS
ACTION_OPT_INS = (
    "opt_in_holy_site_creation_ui", "opt_in_holy_site_creation_create_once",
    "opt_in_holy_site_relic_actions", "opt_in_player_rite_creation_actions",
)
SCOPE = {
    "world_confirmation_allowed": False, "day_advance_allowed": False,
    "new_save_allowed": False, "ordinary_campaign_credit": False,
    "preparation_mod_mounted": False,
}


def require(value, message):
    if not value:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def pin(path):
    path = Path(path).resolve()
    h = hashlib.sha256()
    with path.open("rb") as s:
        for chunk in iter(lambda: s.read(1024 * 1024), b""):
            h.update(chunk)
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": h.hexdigest()}


def validate_contract(context):
    c = context["case_contract"]
    require(c.get("schema") == "faith-engine-e02-d1-readonly-case-v1"
            and c.get("product") == context.get("product") == PRODUCT
            and c.get("case") == context.get("case") == CASE,
            "D1 readonly case identity differs")
    saved = c.get("saved_input")
    require(isinstance(saved, dict) and set(saved) == {
                "save", "bytes", "sha256", "player_id", "date_raw"}
            and isinstance(saved["save"], str) and bool(saved["save"])
            and type(saved["bytes"]) is int and saved["bytes"] == SAVE_BYTES
            and saved["sha256"] == SAVE_SHA256,
            "D1 requires the original immutable save byte identity")
    history = c.get("historical_identity_expectation")
    require(isinstance(history, dict) and set(history) == {
                "kind", "source", "player_id", "date_raw"}
            and history["kind"] == "historical_expectation_not_fresh_observation"
            and type(history["player_id"]) is int and 0 < history["player_id"] < 2**32-1
            and type(history["date_raw"]) is int
            and type(saved["player_id"]) is int
            and type(saved["date_raw"]) is int
            and saved["player_id"] == history["player_id"]
            and saved["date_raw"] == history["date_raw"],
            "D1 startup expectations must retain their explicit historical origin")
    source = history["source"]
    require(isinstance(source, dict) and set(source) == {"path", "bytes", "sha256"}
            and isinstance(source["path"], str) and bool(source["path"])
            and type(source["bytes"]) is int and source["bytes"] > 0
            and isinstance(source["sha256"], str) and len(source["sha256"]) == 64
            and all(ch in "0123456789abcdef" for ch in source["sha256"]),
            "D1 historical expectation needs a precise source pin")
    require(c.get("profile") == {"enabled_mods": [], "product_files": []}
            and c.get("scope") == SCOPE,
            "D1 remains a vanilla readonly saved scene")
    require(isinstance(c.get("machine_id"), str) and bool(c["machine_id"])
            and c["machine_id"] != "unknown", "D1 needs an explicit executing machine")
    spec = context.get("case_spec")
    if spec is not None:
        require(all(spec.get(k) is False for k in ACTION_OPT_INS),
                "D1 must keep every existing private world-action opt-in closed")
        required, readonly = spec.get("required_mcp_tools"), spec.get("opt_in_read_only_mcp_tools")
        require(isinstance(required, list) and len(required) == len(set(required))
                and set(required) == REQUIRED_TOOLS
                and isinstance(readonly, list) and len(readonly) == len(set(readonly))
                and set(readonly) == READONLY_TOOLS,
                "D1 finite required/read-only tool set differs")
    return c


def prepare_case(context):
    from ck3_mod_acceptance_prepare import materialize_product_profile, finish_product_profile
    from ck3_live_run_id import current_machine_id
    c = validate_contract(context)
    require(current_machine_id() == c["machine_id"], "D1 machine identity differs")
    admission = context["case_inputs"]["storage_admission"]
    require(pin(admission["path"]) == admission, "D1 storage admission pin differs")
    grant = read(admission["path"])
    require(grant.get("machine_id") == c["machine_id"] and grant.get("active") is True,
            "D1 storage admission is inactive or belongs to another machine")
    expiry = datetime.fromisoformat(grant["expires_at_utc"].replace("Z", "+00:00"))
    require(expiry.tzinfo is not None and datetime.now(timezone.utc) < expiry,
            "D1 storage admission expired")
    h = c["historical_identity_expectation"]
    require(pin(h["source"]["path"]) == h["source"], "D1 historical expectation source changed")
    saved = dict(context["saved_campaign"])
    require(saved == c["saved_input"], "D1 prepared saved input differs")
    path = Path(saved["save"])
    require(path.is_file() and not path.is_symlink() and path.suffix.casefold() == ".ck3",
            "D1 original ordinary save is absent or not immutable input")
    before = path.stat()
    actual = pin(path)
    after = path.stat()
    require(actual["bytes"] == saved["bytes"] and actual["sha256"] == saved["sha256"]
            and before.st_size == after.st_size and before.st_mtime_ns == after.st_mtime_ns,
            "D1 original save bytes changed")
    profile = materialize_product_profile(context, None, context["case_inputs"]["configuration"])
    profile = finish_product_profile(context, profile, provenance={
        "machine_id": c["machine_id"], "kind": "faith-e02-D1-readonly-capture",
        "saved_input": saved, "storage_admission": admission,
        "historical_identity_expectation": h, "fresh_native_identity_observed": False,
        "preparation_mod_mounted": False, "world_actions_performed": False,
        "actual_restore_observed": False,
    })
    return {"startup": {"mode": "saved_campaign", "state_dir": profile["state_dir"],
                        "saved_campaign": {**saved, "product_inventory": profile["product_inventory"]["path"]}},
            "profile": profile, "initial_plan": context["case_spec"]["initial_plan"],
            "runtime_status": "NOT_RUN", "business_pass": False, "product_release_pass": False}


def shared_opening_binding(context):
    """Read the selected host source without assuming its subprocess import path."""
    source = Path(context["shared_source_root"]).expanduser().resolve()
    if (source / "ck3_autonomous_player/src/xar_autoplayer").is_dir():
        source = source / "ck3_autonomous_player/src"
    bridge = source / "xar_autoplayer/bridge"
    expected = bridge / "ingame_decisions_open_contract.py"
    identity = bridge / "version_identity.py"
    require(expected.is_file() and identity.is_file(), "D1 selected shared binding source is absent")
    previous_path = list(sys.path)
    try:
        sys.path.insert(0, str(source))
        module = importlib.import_module("xar_autoplayer.bridge.ingame_decisions_open_contract")
        require(Path(module.__file__).resolve() == expected.resolve(),
                "D1 opening binding import escaped the selected shared source")
        dependency = importlib.import_module("xar_autoplayer.bridge.version_identity")
        require(Path(dependency.__file__).resolve() == identity.resolve(),
                "D1 opening binding import escaped the selected shared source")
        return module.opening_binding, {"opening_contract": pin(expected), "version_identity": pin(identity)}
    finally:
        sys.path[:] = previous_path


def initial_scene_binding(frame, contract, *, binding_reader=None):
    """The paused scene date comes from this actual native frame, never the old date."""
    if binding_reader is None:
        from xar_autoplayer.bridge.ingame_decisions_open_contract import opening_binding
        binding_reader = opening_binding
    binding = binding_reader(frame)
    require(binding["played_character_id"] == contract["historical_identity_expectation"]["player_id"],
            "D1 actual native player differs from explicit expected actor")
    require(frame.get("active_event") is None, "D1 initial scene has a real event to resolve")
    return binding


def validate_capture_frame(frame, binding, *, binding_reader=None):
    if binding_reader is None:
        from xar_autoplayer.bridge.ingame_decisions_open_contract import opening_binding
        binding_reader = opening_binding
    current = binding_reader(frame)
    # UI observations may publish a new revision. Actor/date/PID/generation may not drift.
    for key in ("date_raw", "played_character_id", "game_pid", "connection_generation", "episode_run_id"):
        require(current[key] == binding[key], "D1 actual readonly scene changed " + key)
    require(frame.get("active_event") is None, "D1 readonly scene acquired a real event")


def run_case(context, client):
    from ck3_mod_acceptance_client import write_once
    c = validate_contract(context)
    before = client.snapshot()
    observed = {
        "schema": "faith-e02-D1-first-native-identity-v1",
        "machine_id": c["machine_id"], "run_id": context["run_id"],
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "first public CaseClient.snapshot return after restore",
        "saved_input": c["saved_input"],
        "historical_identity_expectation": c["historical_identity_expectation"],
        "actual_snapshot": before, "fresh_identity_validated": False,
        "business_pass": False, "world_confirmation_allowed": False,
    }
    try:
        binding_reader, binding_sources = shared_opening_binding(context)
        observed["opening_binding_sources"] = binding_sources
        binding = initial_scene_binding(before, c, binding_reader=binding_reader)
    except (ValueError, KeyError, ImportError) as error:
        observed["rejection_reason"] = str(error)
        write_once(Path(context["output"]) / "faith-e02-d1-first-native-identity.json", observed)
        raise
    observed.update(fresh_identity_validated=True, scene_binding=binding,
                    date_binding_source="this first actual native snapshot")
    write_once(Path(context["output"]) / "faith-e02-d1-first-native-identity.json", observed)
    client.checkpoint("faith-e02-d1-readonly-before", before)
    finish = client.root_checkpoint("faith-e02-d1-readonly-finish", {
        "machine_id": c["machine_id"], "case": CASE, "scene_binding": binding,
        "capture_queue_validator": "tools/faith_e02_d1_readonly_queue.py",
        "allowed_scope": "religion/governance/pilgrimage identities and source-bound decision selection queries",
        "world_confirmation_allowed": False, "day_advance_allowed": False,
        "new_save_allowed": False, "business_pass": False,
        "Root_finish_requires_original_ck3_alive": True,
    }, reserve=120)
    require(finish.get("run_id") == context["run_id"]
            and finish.get("reviewer") == client.operator_reviewer
            and finish.get("status") == "complete", "D1 readonly finish is foreign or incomplete")
    after = client.snapshot()
    validate_capture_frame(after, binding, binding_reader=binding_reader)
    client.checkpoint("faith-e02-d1-readonly-after", after)
    result = {
        "schema": "faith-e02-D1-readonly-holder-result-v1", "machine_id": c["machine_id"],
        "run_id": context["run_id"], "case": CASE, "scene_binding": binding,
        "before_snapshot_id": before.get("snapshot_id"), "after_snapshot_id": after.get("snapshot_id"),
        "root_finish": finish, "research_holder_completed": True,
        "paused_actor_date_preserved": True, "world_mutation_absence_proven": False,
        "case_contract_qualified": False, "gui_contract_qualified": False,
        "business_pass": False, "product_release_pass": False,
    }
    write_once(Path(context["output"]) / "faith-e02-d1-readonly-holder-result.json", result)
    return result


def verify_case(context):
    c = validate_contract(context)
    identity = read(Path(context["output"]) / "faith-e02-d1-first-native-identity.json")
    result = read(Path(context["output"]) / "faith-e02-d1-readonly-holder-result.json")
    require(identity.get("fresh_identity_validated") is True
            and identity.get("run_id") == result.get("run_id") == context["run_id"]
            and result.get("machine_id") == c["machine_id"]
            and result.get("case") == CASE
            and identity.get("scene_binding") == result.get("scene_binding"),
            "D1 holder result lacks its actual first-frame identity")
    return {"research_holder_completed": result.get("research_holder_completed") is True,
            "paused_actor_date_preserved": result.get("paused_actor_date_preserved") is True,
            "case_contract_qualified": False, "gui_contract_qualified": False,
            "business_pass": False, "product_release_pass": False,
            "scope": "readonly scene holder only; native fields and pixels are separate evidence"}
