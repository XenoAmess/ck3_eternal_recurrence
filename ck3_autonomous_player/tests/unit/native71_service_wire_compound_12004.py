"""One new Service wiring compound using the actual 38b and 56 native wires.

This standalone fixture replaces only backend boundaries. It requires both new
native outputs, runs the actual strict normalizers and Service candidate, and
does not run previously qualified source or numerical test suites.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def pin(path):
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest()}


def load(name, path, pins):
    pins.append(pin(path))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--continuation-root", type=Path, required=True)
    parser.add_argument("--army-wire-dir", type=Path, required=True)
    parser.add_argument("--sway-wire", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.source_root / "ck3_autonomous_player/src"))
    # Import the installed package before overlaying uniquely owned candidates.
    importlib.import_module("xar_autoplayer.bridge")
    pins = [pin(Path(__file__))]
    root = args.continuation_root
    base = "ck3_autonomous_player/src/xar_autoplayer/"
    strict = load("xar_autoplayer.bridge.army_daily_assault_loss_inputs_contract",
                  root / "continuation-38b/candidate" / base /
                  "bridge/army_daily_assault_loss_inputs_contract.py", pins)
    war = importlib.import_module("xar_autoplayer.bridge.war_contract")
    war.normalize_current_daily_assault_loss_inputs_v1 = strict.normalize_current_daily_assault_loss_inputs_v1
    load("xar_autoplayer.bridge.assault_eligible_contributors_12004",
         root / "continuation-38/assault_eligible_contributors_12004.py", pins)
    for module, relative in (
        ("bridge.sway_completion_causal_private_12004", "bridge/sway_completion_causal_private_12004.py"),
        ("bridge.active_scheme_sway_completion_execution_private_transport", "bridge/active_scheme_sway_completion_execution_private_transport.py"),
        ("bridge.active_scheme_sway_completion_termination_private_transport", "bridge/active_scheme_sway_completion_termination_private_transport.py"),
        ("sway_end_causal_consumer_12004", "sway_end_causal_consumer_12004.py"),
    ):
        load("xar_autoplayer." + module, root / "continuation-56/candidate" / base / relative, pins)
    service_module = load("xar_autoplayer.bridge.service",
                          root / "continuation-59/candidate" / base / "bridge/service.py", pins)
    from xar_autoplayer.bridge.version_identity import CK3_12004, CK3_12003
    from xar_autoplayer.bridge.driver import BridgeUnavailableError
    from xar_autoplayer.sway_formal_consumer import LEDGER_FILE, SCHEMA
    from xar_autoplayer.bridge.active_scheme_sway_completion_execution_private_transport import normalize_active_scheme_sway_completion_execution_v1
    from xar_autoplayer.bridge.active_scheme_sway_completion_termination_private_transport import normalize_active_scheme_sway_completion_termination_v1

    class Backend:
        allow_private_active_scheme_sway_completion_execution_query = True
        allow_private_active_scheme_sway_completion_termination_query = True

        def __init__(self, leaf, state_dir=None):
            self.leaf, self.calls, self.state_dir = leaf, [], state_dir
            self.build = CK3_12004

        def take_snapshot(self):
            return {"paused": True, "revision": 42, "native_revision": 7,
                    "date_raw": 10000, "snapshot_id": "new-native71-service-wire",
                    "backend_id": "pure-memory-wire-fixture",
                    "player_armies": [{"army_id": 11}], "active_wars": [],
                    "diagnostics": {"hello": {"expected_ck3_version": self.build.game_version,
                        "expected_ck3_sha256": self.build.executable_sha256}}}

        def capabilities(self):
            return {"action_steps": ["query-army-strengths-v1"]}

        def execute_step(self, step, *, expected_revision=None):
            self.calls.append((step, expected_revision))
            # Only the outer Army scope envelope is fixture data. The loss leaf
            # and its group selector are the unchanged actual new native wire.
            row = {"status": "available", "army_id": 11, "native_carmy_id": 12,
                   "scope_role": "player", "war_ids": [], "regiment_count": 0,
                   "current_soldiers": 160, "maximum_soldiers": 200,
                   "ai_base_power_raw": 0, "ai_base_power_scale": 100000,
                   "unavailable_reason": None,
                   "current_daily_assault_loss_inputs_v1": deepcopy(self.leaf)}
            return {"status": "available", "army_strengths": [row], "query_sequence": 59,
                    "native_readiness": {"current_strength": True, "full_monthly": False}}

        def query_active_scheme_sway_completion_execution_private_v1(self, **kwargs):
            self.calls.append(("execution", kwargs))
            return deepcopy(self.execution)

        def query_active_scheme_sway_completion_termination_private_v1(self, **kwargs):
            self.calls.append(("termination", kwargs))
            return deepcopy(self.termination)

    outputs = {}
    for name in ("present-group-scope", "unknown-group-scope", "empty-group-targets", "null-group-scope"):
        path = args.army_wire_dir / (name + ".json")
        pins.append(pin(path))
        leaf = json.loads(path.read_text(encoding="utf-8"))
        before = deepcopy(leaf)
        backend = Backend(leaf)
        result = service_module.GameplayBridgeService(backend).query_army_strengths([11], expected_revision=42)
        require(leaf == before, "Service mutated the actual native group wire")
        require(backend.calls == [("query-army-strengths-v1", 42)], "Army query issued extra reads")
        returned = result["army_strengths"][0]["current_daily_assault_loss_inputs_v1"]
        require(returned == strict.normalize_current_daily_assault_loss_inputs_v1(before), "raw native inputs changed")
        require(result["native_readiness"] == {"current_strength": True, "full_monthly": False}, "native readiness overwritten")
        current = result["same_query_conditional_assault_group_contributors_12004"][0]["projection"]
        stage = result["explicit_observed_army_stage_projections_12004"][0]["projection"]
        require(current["capture_id"] is None and not current["actual_stage_entry_observed"], "current input promoted to historical stage")
        require(stage["ordered_monthly_core"] is None and stage["daily_assault_numerical"] is None
                and stage["assault_group_release"] is None and stage["capture_id"] is None,
                "unobserved monthly stage manufactured")
        require(not current["full_monthly_ready"] and not stage["full_monthly_ready"], "full monthly readiness inferred")
        group = current["group_budget_outputs"][0]
        require(group["native_current_expected_loss"] == before["groups"][0]["native_current_expected_loss"], "native loss scalar changed")
        if name == "present-group-scope":
            require(group["ready"] is True, "emitted complete selector was not consumed")
            require([event["manager_stored_index"] for event in group["refresh_occurrences"]] == [0, 1], "original refresh order lost")
            require(group["refresh_occurrences"][1]["army_used_fallback"] is True, "fallback occurrence lost")
        if name == "unknown-group-scope":
            require(current["status"] == "partial" and group["ready"] is False, "unknown group selector became ready")
        if name == "empty-group-targets":
            require(group["ready"] is True and group["expected_loss"] == 0, "known empty became unknown")
        outputs[name] = {"current": current, "observed_stage": stage}

    present = json.loads((args.army_wire_dir / "present-group-scope.json").read_text(encoding="utf-8"))
    legacy = deepcopy(present)
    del legacy["groups"][0]["ordered_besieging_refill_inputs_v1"]
    legacy_result = service_module.GameplayBridgeService(Backend(legacy)).query_army_strengths([11], expected_revision=42)
    require(legacy_result["same_query_conditional_assault_group_contributors_12004"][0]["projection"]["status"] == "partial", "absent selector inferred")
    other_build = Backend(present)
    other_build.build = CK3_12003
    older_result = service_module.GameplayBridgeService(other_build).query_army_strengths([11], expected_revision=42)
    require(older_result["same_query_conditional_assault_group_contributors_12004"][0]["projection"]["status"] == "unavailable", "actual4 adapter crossed build boundary")
    malformed = deepcopy(present)
    malformed["groups"][0]["ordered_besieging_refill_inputs_v1"]["province_id"] = 8
    try:
        service_module.GameplayBridgeService(Backend(malformed)).query_army_strengths([11], expected_revision=42)
    except BridgeUnavailableError:
        pass
    else:
        raise AssertionError("strict new group Province mismatch accepted by Service")

    pins.append(pin(args.sway_wire))
    packet = json.loads(args.sway_wire.read_text(encoding="utf-8"))
    execution_envelope, termination_envelope = packet["execution"]["result"], packet["termination"]["result"]
    snapshot = {"played_character": {"character_id": 29829}}
    execution = normalize_active_scheme_sway_completion_execution_v1(
        execution_envelope["sway_completion_execution"], snapshot=snapshot,
        target_character_id=31900, scheme_instance_id=0x02000016)
    termination = normalize_active_scheme_sway_completion_termination_v1(
        termination_envelope["sway_completion_termination"], snapshot=snapshot,
        target_character_id=31900, scheme_instance_id=0x02000016)
    for read, envelope in ((execution, execution_envelope), (termination, termination_envelope)):
        read.update({key: envelope[key] for key in ("build_version", "executable_sha256")})
    args.output_dir.mkdir(parents=True, exist_ok=True)
    state_dir = args.output_dir / "sway-ledger"
    state_dir.mkdir()
    phase, material = {"next_turn_consumed": True, "source_sequence": 7}, {"material_effect_observed": False}
    resolved = {"action_id": "new-native71-service-wire-action", "postcondition_verified": True,
        "actor_character_id": 29829, "target_character_id": 31900,
        "exact_ck3_build": termination["exact_ck3_build"], "exe_sha256": termination["exe_sha256"],
        "native_receipt": {"scheme_instance_id": 0x02000016, "scheme_instance_generation": 2},
        "phase_intervention": phase, "material_intervention": material}
    ledger_path = state_dir / LEDGER_FILE
    ledger_path.write_text(json.dumps({"schema": SCHEMA, "pending": None, "resolved": resolved}), encoding="utf-8")
    backend = Backend(present, state_dir)
    backend.execution, backend.termination = execution, termination
    service = service_module.GameplayBridgeService(backend)
    arguments = {"expected_revision": 42, "target_character_id": 31900, "scheme_instance_id": 0x02000016, "after_sequence": 17}
    joined = service.query_active_scheme_sway_completion_execution_private_v1(**arguments)
    require(joined["records"] == execution["records"], "raw execution records filtered outward")
    require(joined["sway_end_cause_observed_12004"] is True, "new actual cause not consumed by Service")
    require(backend.calls == [("execution", arguments), ("termination", {**arguments, "after_sequence": 0})], "execution/end ring sequences conflated")
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    require(ledger["resolved"]["phase_intervention"] == phase, "completion100 entered phase consumer")
    require(ledger["resolved"]["material_intervention"] == material, "cause changed independent material")
    require(ledger["resolved"]["end_causal_observation"]["action_id"] == resolved["action_id"], "original action binding missing")
    ledger["resolved"]["terminal_intervention"]["next_turn_consumed"] = True
    ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
    backend.calls.clear()
    converse = service.query_active_scheme_sway_completion_termination_private_v1(**arguments)
    require(converse["records"] == termination["records"] and converse["sway_end_cause_observed_12004"], "converse Service route missed cause")
    require(backend.calls == [("termination", arguments), ("execution", {**arguments, "after_sequence": 0})], "termination/execution ring sequences conflated")
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    require(ledger["resolved"]["terminal_intervention"]["next_turn_consumed"] is True, "repeated cause rearmed terminal intervention")
    backend.termination = deepcopy(termination)
    backend.termination["records"][0]["cause_relation"] = None
    unattributed = service.query_active_scheme_sway_completion_termination_private_v1(**arguments)
    require(unattributed["sway_end_cause_observed_12004"] is False
            and unattributed["sway_end_causal_observation_12004"] is None,
            "retained status1 supplied an unobserved cause")
    outputs["sway"] = {"execution_cause": joined["sway_end_causal_observation_12004"],
                       "termination_cause": converse["sway_end_causal_observation_12004"],
                       "unmatched_cause": unattributed["sway_end_causal_observation_12004"]}
    receipt = {"schema": "native71-service-new-wire-compound-12004/1", "result": "GREEN",
        "completed_at_utc": datetime.now(timezone.utc).isoformat(), "argv": sys.argv,
        "pins": pins, "checks": ["actual38b-wire-to-strict-to-Service-current38",
            "native-scalars-and-readiness-preserved", "unknown-empty-legacy-build-and-Province-semantics",
            "unobserved-core-daily-release-not-inferred", "actual56-wire-to-strict-to-both-Service-routes",
            "original-action-ledger-and-consumption-preserved", "authored100-filtered-from-phase",
            "unmatched-status1-unattributed"],
        "old_source_focus_or_FIRST_replays": 0, "actual_gameplay_acceptance": False,
        "full_monthly_production_pipeline_ready": False}
    (args.output_dir / "OBSERVED-OUTPUTS.json").write_text(json.dumps(outputs, indent=2) + "\n", encoding="utf-8")
    (args.output_dir / "FOCUSED-VALIDATION.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"result": "GREEN", "checks": len(receipt["checks"])}))


if __name__ == "__main__":
    main()
