"""AUTHOR_NOT_RUN: new relation wires through the existing private capture route.

The unique future joined qualifier supplies nine newly emitted production
wires. The full wire uses one software response through the existing driver
method/transport; no CK3 process or native method is called by this runner.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import patch

CASES = ("full", "empty", "current-ids", "generation-mismatch", "bookend-changed",
         "fallback", "negative-count", "after-changed", "completion-changed")
RELATION = "current_family_relation_v1"


def _pin(path: Path) -> dict:
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def _write(path: Path, value: object) -> None:
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")


def _load(name: str, candidate_src: Path):
    full_name = "xar_autoplayer.bridge." + name
    path = candidate_src / "xar_autoplayer/bridge" / (name + ".py")
    spec = importlib.util.spec_from_file_location(full_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[full_name] = module
    spec.loader.exec_module(module)
    return module


def _snapshot(wire: dict) -> dict:
    return {"snapshot_id": "new-current-relation-owned-wire-frame", "revision": 17,
        "native_revision": wire["native_revision"], "date_raw": wire["date_raw"],
        "paused": True, "map_ready": True,
        "played_character": {"character_id": wire["played_character_id"], "alive": True},
        "diagnostics": {"hello": {"expected_ck3_version": "1.20.0.4",
            "expected_ck3_sha256": wire["executable_sha256"]}}}


def _command(wire: dict) -> dict:
    # Only this surrounding transport envelope is a software fixture. Its
    # ordinary family result remains unavailable independently of new values.
    return {"type": "command_result", "protocol_version": 1,
        "request_id": wire["request_id"], "ok": True,
        "result": {"step": "query-current-first-heir-relationship-v1-private",
            "accepted": True, "private_build": True, "read_only": True,
            "advertised": False, "native_revision": wire["native_revision"],
            "subject_source": "public_campaign_root_primary_first_heir",
            "heir_character_id": wire["heir_character_id"], "status": "unavailable",
            "unavailable_reason": "owned_current_relation_fixture_family_response",
            "bilateral_verified": False, "betrothed_character_id": None,
            "primary_spouse_character_id": None, "spouse_character_ids": None}}


def _family(wire: dict) -> dict:
    return {"exact_ck3_build": "1.20.0.4", "exe_sha256": wire["executable_sha256"],
        "native_revision": wire["native_revision"],
        "heir_character_id": None if wire["heir_character_id"] == -1 else wire["heir_character_id"]}


def run_new_guardian_current_family_relation_same_job_v1(
    *, source_root: Path, candidate_src: Path, source_freeze: Path,
    wire_root: Path, output_directory: Path,
) -> dict:
    output_directory.mkdir(parents=True, exist_ok=False)
    freeze = json.loads(source_freeze.read_text("utf-8"))
    for item in freeze["other_named_source_and_reuse_metadata"]:
        if Path(item["path"]).name in {"native_driver.py", "current_first_heir_relationship_private_transport.py"}:
            assert _pin(Path(item["path"]))["sha256"] == item["sha256"]
    wires = {name: wire_root / ("family-relation-fixture-current-relation-" + name + ".json") for name in CASES}
    input_pins = {name: _pin(path) for name, path in wires.items()}
    native = {name: json.loads(path.read_text("utf-8")) for name, path in wires.items()}
    originals = deepcopy(native)
    sys.path.insert(0, str(source_root / "ck3_autonomous_player/src"))
    import xar_autoplayer.bridge
    from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
    from xar_autoplayer.bridge import current_first_heir_relationship_private_transport as transport
    decoder = _load("guardian_factory_create_inputs_contract_v1", candidate_src)
    capture = _load("guardian_factory_capture_private_v1", candidate_src)
    full = native["full"]
    snapshot, command = _snapshot(full), _command(full)

    class ExistingDriverFakeResponse:
        allow_private_current_first_heir_relationship_query = True
        query_current_first_heir_relationship_private_v1 = NativeHeadlessGameplayDriver.query_current_first_heir_relationship_private_v1

        def __init__(self):
            self.endpoint = self
            self.state = self
            self.sent = []
            self.waits = 0

        def diagnostics(self):
            return {"connected": True, "bridge_pid": 59079}

        def take_internal_semantic_snapshot(self):
            return deepcopy(snapshot)

        def _execute_campaign_root_context_v1_query(self, *, expected_revision):
            assert expected_revision == snapshot["revision"]
            return {"status": "available", "query_sequence": 1,
                "held_title_partition": [{"primary": True, "first_heir_character_id": full["heir_character_id"]}]}

        def send(self, request):
            assert not self.sent and request["request_id"] == full["request_id"]
            assert request["expected_revision"] == full["native_revision"] and request["step"] == transport.STEP
            self.sent.append(deepcopy(request))
            with Path(request["guardian_factory_sidecar_path"]).open("xb") as stream:
                stream.write(wires["full"].read_bytes())

        def wait_for_command_result(self, request_id, timeout):
            assert request_id == full["request_id"] and timeout == 1.0
            self.waits += 1
            return deepcopy(command)

    prefix = "family-relation-"
    assert full["request_id"].startswith(prefix)
    driver = ExistingDriverFakeResponse()
    capture_dir = output_directory / "one-new-response-capture"
    capture_dir.mkdir()
    with patch.object(transport.uuid, "uuid4", return_value=SimpleNamespace(hex=full["request_id"][len(prefix):])):
        receipt = capture.capture_with_connected_driver(driver, owned_game_pid=59079,
            output_directory=capture_dir, timeout_seconds=1.0)
    assert len(driver.sent) == driver.waits == 1
    assert receipt["native_factory_discovery_v1"] == full
    assert receipt[RELATION] == full[RELATION] and receipt["guardian_pair_ready"] is True
    assert receipt["guardian_membership_observed"] is False and receipt["G2_outcome_credit"] == 0
    ordinary = json.loads((capture_dir / "family-result.json").read_text("utf-8"))
    assert ordinary["status"] == "unavailable" and RELATION not in ordinary
    checks = ["one_actual_new_wire_through_existing_driver_transport_capture",
              "new_pair_readiness_keeps_ordinary_family_and_natural_invocation_independent"]
    decoded = {}
    for name, wire in native.items():
        value = decoder.validate_guardian_factory_create_inputs_v1(wire,
            command_result=_command(wire), snapshot=_snapshot(wire), family_result=_family(wire))
        assert value == wire and value is not wire
        decoded[name] = value
    for name in ("full", "current-ids", "fallback"):
        relation = decoded[name][RELATION]
        assert relation["ready"] is True and all(row["available"] is True and row["raw_value"] is True for row in relation["rows"])
    assert decoded["current-ids"][RELATION]["root_character_id"] != full[RELATION]["root_character_id"]
    assert decoded["current-ids"][RELATION]["target_character_id"] != full[RELATION]["target_character_id"]
    assert any(row["basis"] == "fallback_raw_equal" for row in decoded["fallback"][RELATION]["rows"])
    checks.append("three_new_source_true_wires_bind_current_ids_and_reached_fallback")
    empty = decoded["empty"][RELATION]
    assert empty["ready"] is True and all(row["available"] is True and row["raw_value"] is False
        and row["descriptor_reached"] is False and row["descriptor_raw"] is None for row in empty["rows"])
    assert decoded["empty"]["factories"][1][decoder.LEAF]["field_18_qword"]["available"] is False
    checks.append("known_false_ready_without_unreached_factory_descriptor")
    for name in ("generation-mismatch", "bookend-changed", "negative-count", "after-changed", "completion-changed"):
        relation = decoded[name][RELATION]
        assert relation["ready"] is False and all(row["available"] is False and row["raw_value"] is None for row in relation["rows"])
    assert any(row["peer_count_raw"] == -1 for row in decoded["negative-count"][RELATION]["rows"])
    for name in ("after-changed", "completion-changed"):
        assert decoded[name]["qualified"] is False
        assert decoded[name][RELATION]["root_address"] is None and decoded[name][RELATION]["target_address"] is None
    checks.append("five_new_partial_and_completion_wires_keep_unknown_and_full_generation")
    for wire in decoded.values():
        relation = wire[RELATION]
        assert relation["root_character_id"] == wire["played_character_id"] & 0xFFFFFFFF
        assert relation["target_character_id"] == wire["heir_character_id"] & 0xFFFFFFFF
        assert relation["native_trigger_invoked"] is False and relation["parsed_target_observed"] is False
    checks.append("nine_requested_full_id_pairs_and_no_parsed_trigger_promotion")

    def reject(name, changed):
        try:
            decoder.validate_guardian_factory_create_inputs_v1(changed,
                command_result=command, snapshot=snapshot, family_result=_family(full))
        except ValueError:
            checks.append("reject_new_relation_" + name)
        else:
            raise AssertionError("new relation corruption accepted: " + name)

    corruptions = {
        "direction": lambda v: v[RELATION].update(direction="heir_to_played"),
        "root_generation": lambda v: v[RELATION].update(root_character_id=v[RELATION]["root_character_id"] ^ 0x01000000),
        "target_generation": lambda v: v[RELATION].update(target_character_id=v[RELATION]["target_character_id"] ^ 0x01000000),
        "uint32_boolean": lambda v: v[RELATION].update(root_character_id=True),
        "ready_formula": lambda v: v[RELATION].update(ready=False),
        "missing_known_value": lambda v: v[RELATION]["rows"][0].update(raw_value=None),
        "row_order": lambda v: v[RELATION]["rows"].reverse(),
        "bool_width": lambda v: v[RELATION]["rows"][0].update(raw_value=1),
        "unknown_as_known": lambda v: v[RELATION]["rows"][0].update(available=False),
        "mode_boolean": lambda v: v[RELATION]["rows"][0].update(predicate_mode=False),
        "descriptor_binding": lambda v: v[RELATION]["rows"][0].update(descriptor_raw=v[RELATION]["rows"][0]["descriptor_raw"] ^ 1),
        "native_invocation": lambda v: v[RELATION].update(native_trigger_invoked=True),
        "unstable_known": lambda v: v[RELATION].update(sample_stable=False),
    }
    for name, mutate in corruptions.items():
        changed = deepcopy(full)
        mutate(changed)
        reject(name, changed)
    legacy = deepcopy(full)
    del legacy[RELATION]
    assert decoder.validate_guardian_factory_create_inputs_v1(legacy,
        command_result=command, snapshot=snapshot, family_result=_family(full)) == legacy
    checks.append("legacy_without_new_relation_retains_existing_raw_inputs")
    assert native == originals
    original_known_value = decoded["full"][RELATION]["rows"][0]["raw_value"]
    decoded["full"][RELATION]["rows"][0]["raw_value"] = False
    assert native == originals
    decoded["full"][RELATION]["rows"][0]["raw_value"] = original_known_value
    checks.append("new_decoder_preserves_original_wire_and_returns_owned_copy")
    result = {"status": "GREEN", "scope": "synthetic offline production-wire/software consumer only",
        "checks": checks, "check_count": len(checks), "actual_input_pins": input_pins,
        "new_native_queries": 0, "new_listeners": 0, "Game_calls": 0,
        "fake_response_count": 1, "old_59f_19_and_52f_5_cases_replayed": 0,
        "source_projection_only": True, "actual_Game_membership_observed": False}
    _write(output_directory / "FOCUSED-VALIDATION.json", result)
    _write(output_directory / "OBSERVED-OUTPUTS.json", {"capture": receipt, "decoded_new_wires": decoded})
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    for name in ("source-root", "candidate-src", "source-freeze", "wire-root", "output-directory"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    result = run_new_guardian_current_family_relation_same_job_v1(**vars(args))
    print(json.dumps({"status": result["status"], "check_count": result["check_count"]}))


if __name__ == "__main__":
    main()
