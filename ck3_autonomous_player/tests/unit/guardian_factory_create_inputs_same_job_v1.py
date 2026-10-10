"""One joined software consumer of 52f's new production-serialized wires.

No listener, CK3 query or native entry call is made. The full wire goes through
the existing driver method/private transport once with one fake response.
The other four emitted wires exercise the decoder's independent raw failures.
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


def _pin(path: Path) -> dict:
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def _write(path: Path, value: object) -> None:
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.write("\n")


def _load_candidate(bridge_name: str, candidate_root: Path):
    name = "xar_autoplayer.bridge." + bridge_name
    path = candidate_root / "xar_autoplayer/bridge" / (bridge_name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _snapshot(wire: dict) -> dict:
    return {
        "snapshot_id": "guardian-new-owned-wire-frame", "revision": 17,
        "native_revision": wire["native_revision"], "date_raw": wire["date_raw"],
        "paused": True, "map_ready": True,
        "played_character": {"character_id": wire["played_character_id"], "alive": True},
        "diagnostics": {"hello": {
            "expected_ck3_version": "1.20.0.4",
            "expected_ck3_sha256": wire["executable_sha256"],
        }},
    }


def _command(wire: dict) -> dict:
    # This surrounding family envelope is a labeled software fixture. It makes
    # no relationship observation and leaves family availability independent.
    return {
        "type": "command_result", "protocol_version": 1,
        "request_id": wire["request_id"], "ok": True,
        "result": {
            "step": "query-current-first-heir-relationship-v1-private",
            "accepted": True, "private_build": True, "read_only": True,
            "advertised": False, "native_revision": wire["native_revision"],
            "subject_source": "public_campaign_root_primary_first_heir",
            "heir_character_id": wire["heir_character_id"],
            "status": "unavailable", "unavailable_reason": "owned_fixture_family_response",
            "bilateral_verified": False, "betrothed_character_id": None,
            "primary_spouse_character_id": None, "spouse_character_ids": None,
        },
    }


def _family_binding(wire: dict) -> dict:
    return {
        "exact_ck3_build": "1.20.0.4", "exe_sha256": wire["executable_sha256"],
        "native_revision": wire["native_revision"],
        "heir_character_id": None if wire["heir_character_id"] == -1 else wire["heir_character_id"],
    }


def run_new_guardian_factory_create_inputs_same_job_v1(
    *, source_root: Path, candidate_root: Path, source_freeze: Path,
    wires: dict[str, Path], output_directory: Path,
) -> dict:
    output_directory.mkdir(parents=True, exist_ok=False)
    freeze = json.loads(source_freeze.read_text("utf-8"))
    for item in freeze["inputs"]:
        if Path(item["path"]).name in {
            "native_driver.py", "current_first_heir_relationship_private_transport.py",
            "nonwar_private_build.py",
        }:
            assert _pin(Path(item["path"]))["sha256"] == item["sha256"]
    sys.path.insert(0, str(source_root / "ck3_autonomous_player/src"))
    import xar_autoplayer.bridge
    from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
    from xar_autoplayer.bridge import current_first_heir_relationship_private_transport as transport
    decoder = _load_candidate("guardian_factory_create_inputs_contract_v1", candidate_root)
    capture = _load_candidate("guardian_factory_capture_private_v1", candidate_root)
    input_pins = {name: _pin(path) for name, path in wires.items()}
    native = {name: json.loads(path.read_text("utf-8")) for name, path in wires.items()}
    full = native["full"]
    assert full["qualified"] is True
    assert full["factories"][0][decoder.LEAF]["field_18_qword"] == {
        "available": True, "raw_value": 0xFEDCBA9876543210,
    }
    assert full["factories"][1][decoder.LEAF]["field_18_qword"] == {
        "available": True, "raw_value": 0,
    }
    snapshot = _snapshot(full)
    command = _command(full)

    class ExistingDriverFakeResponse:
        allow_private_current_first_heir_relationship_query = True
        query_current_first_heir_relationship_private_v1 = (
            NativeHeadlessGameplayDriver.query_current_first_heir_relationship_private_v1
        )

        def __init__(self):
            self.endpoint = self
            self.state = self
            self.sent = []
            self.waits = 0

        def diagnostics(self):
            return {"connected": True, "bridge_pid": 59077}

        def take_internal_semantic_snapshot(self):
            return deepcopy(snapshot)

        def _execute_campaign_root_context_v1_query(self, *, expected_revision):
            assert expected_revision == snapshot["revision"]
            return {
                "status": "available", "query_sequence": 1,
                "held_title_partition": [{"primary": True,
                    "first_heir_character_id": full["heir_character_id"]}],
            }

        def send(self, request):
            assert not self.sent
            assert request["request_id"] == full["request_id"]
            assert request["expected_revision"] == full["native_revision"]
            assert request["step"] == transport.STEP
            self.sent.append(deepcopy(request))
            # Exact bytes came from the new native production serializer.
            with Path(request["guardian_factory_sidecar_path"]).open("xb") as stream:
                stream.write(wires["full"].read_bytes())

        def wait_for_command_result(self, request_id, timeout):
            assert request_id == full["request_id"] and timeout == 1.0
            self.waits += 1
            return deepcopy(command)

    prefix = "family-relation-"
    assert full["request_id"].startswith(prefix)
    driver = ExistingDriverFakeResponse()
    capture_dir = output_directory / "one-response-capture"
    capture_dir.mkdir()
    with patch.object(transport.uuid, "uuid4", return_value=SimpleNamespace(
        hex=full["request_id"][len(prefix):]
    )):
        receipt = capture.capture_with_connected_driver(
            driver, owned_game_pid=59077, output_directory=capture_dir,
            timeout_seconds=1.0,
        )
    assert len(driver.sent) == driver.waits == 1
    assert receipt["native_factory_discovery_v1"] == full
    assert receipt["guardian_membership_observed"] is False
    assert receipt["guardian_pair_ready"] is False and receipt["G2_outcome_credit"] == 0
    family = json.loads((capture_dir / "family-result.json").read_text("utf-8"))
    assert family["status"] == "unavailable" and "native_factory_discovery_v1" not in family
    assert family["unavailable_reason"] == "owned_fixture_family_response"
    checks = ["actual_new_high_qword_and_observed_zero_preserved",
        "existing_driver_transport_capture_one_fake_response",
        "ordinary_family_availability_and_business_credit_independent"]
    decoded = {}
    for name, wire in native.items():
        value = decoder.validate_guardian_factory_create_inputs_v1(
            wire, command_result=_command(wire), snapshot=_snapshot(wire),
            family_result=_family_binding(wire),
        )
        assert value == wire and value is not wire
        decoded[name] = value
    assert decoded["unreadable18"]["factories"][1][decoder.LEAF]["field_18_qword"] == {
        "available": False, "raw_value": None,
    }
    assert decoded["unreadable18"]["factories"][1]["status"] == "found"
    assert decoded["unreadable18"]["factories"][1][decoder.LEAF]["field_10_dword"]["available"] is True
    assert decoded["unreadable10"]["factories"][1][decoder.LEAF] == {
        "schema_version": 1,
        "field_10_dword": {"available": False, "raw_value": None},
        "field_18_qword": {"available": False, "raw_value": None},
    }
    for name in ("after_changed", "completion_changed"):
        assert decoded[name]["qualified"] is False
        assert all(row[decoder.LEAF]["field_10_dword"]["available"] is False
            and row[decoder.LEAF]["field_18_qword"]["available"] is False
            for row in decoded[name]["factories"])
    checks.append("four_actual_native_failure_wires_keep_independent_availability")
    legacy = deepcopy(full)
    for row in legacy["factories"]:
        del row[decoder.LEAF]
    assert decoder.validate_guardian_factory_create_inputs_v1(
        legacy, command_result=command, snapshot=snapshot, family_result=family
    ) is None
    checks.append("legacy_missing_inputs_remain_unknown")
    corruptions = {
        "request": lambda v: v.update(request_id="different-owned-request"),
        "revision": lambda v: v.update(native_revision=v["native_revision"] + 1),
        "date": lambda v: v.update(date_raw=v["date_raw"] + 1),
        "player": lambda v: v.update(played_character_id=v["played_character_id"] + 1),
        "key_order": lambda v: v["factories"].reverse(),
        "record_pair": lambda v: v["factories"][0][decoder.LEAF]["field_10_dword"].update(raw_value=0),
        "qword_boolean": lambda v: v["factories"][0][decoder.LEAF]["field_18_qword"].update(raw_value=True),
        "qword_width": lambda v: v["factories"][0][decoder.LEAF]["field_18_qword"].update(raw_value=2**64),
        "dword_width": lambda v: v["factories"][0][decoder.LEAF]["field_10_dword"].update(raw_value=2**32),
        "availability_null": lambda v: v["factories"][0][decoder.LEAF]["field_18_qword"].update(available=False),
        "factory_missing": lambda v: v["factories"][0].update(factory_address=0),
        "virtual_slot_join": lambda v: v["factories"][0]["virtual_slots"][0].update(rva=2**64 - 1),
        "mixed_version": lambda v: v["factories"][1].pop(decoder.LEAF),
    }
    for name, corrupt in corruptions.items():
        changed = deepcopy(full)
        corrupt(changed)
        try:
            decoder.validate_guardian_factory_create_inputs_v1(
                changed, command_result=command, snapshot=snapshot, family_result=family
            )
        except ValueError:
            checks.append("reject_copied_input_" + name)
        else:
            raise AssertionError("corrupted new input accepted: " + name)
    owned = receipt["native_factory_discovery_v1"]
    owned["factories"][0][decoder.LEAF]["field_18_qword"]["raw_value"] = 1
    assert native["full"]["factories"][0][decoder.LEAF]["field_18_qword"]["raw_value"] == 0xFEDCBA9876543210
    assert input_pins == {name: _pin(path) for name, path in wires.items()}
    checks.append("owned_copy_and_all_five_native_wire_bytes_unchanged")
    _write(output_directory / "OBSERVED-OUTPUTS.json", {
        "source": "new52f_native_production_serializer_owned_synthetic_fixture",
        "input_wires": input_pins, "decoded_native_families": decoded,
        "ordinary_family_result": family, "native_queries": 0,
        "fake_responses": 1, "Game_values_observed": False,
    })
    result = {
        "schema": "guardian-create-inputs-python-new-wire-proof-v1", "status": "GREEN",
        "checks": checks, "check_count": len(checks), "input_wires": input_pins,
        "source_freeze": _pin(source_freeze),
        "one_existing_driver_fake_response": 1, "native_queries": 0,
        "native_compile_or_fixture_repeats": 0, "old_Guardian_Battle_Army_QA": 0,
        "guardian_membership_observed": False, "guardian_pair_ready": False,
        "factory_Create_or_Evaluate_called": False, "Game_acceptance": False,
    }
    _write(output_directory / "FOCUSED-VALIDATION.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--source-freeze", type=Path, required=True)
    for name in ("full", "unreadable18", "unreadable10", "after-changed", "completion-changed"):
        parser.add_argument("--wire-" + name, type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    result = run_new_guardian_factory_create_inputs_same_job_v1(
        source_root=args.source_root, candidate_root=args.candidate_root,
        source_freeze=args.source_freeze, output_directory=args.output_dir,
        wires={name.replace("-", "_"): getattr(args, "wire_" + name.replace("-", "_"))
            for name in ("full", "unreadable18", "unreadable10", "after-changed", "completion-changed")},
    )
    print(json.dumps({"status": result["status"], "checks": result["check_count"]}))


if __name__ == "__main__":
    main()
