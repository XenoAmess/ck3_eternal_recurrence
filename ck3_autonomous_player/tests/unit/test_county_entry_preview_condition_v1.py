"""Four focused offline cases through the candidate production preview Driver.

The endpoint and DTO are authored fixtures. No game, SDK, native EXE or pipe is used.
This runner supports an external minimal-diff candidate without copying native_driver.
"""
from __future__ import annotations
from copy import deepcopy
from datetime import datetime, timezone
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import types

sys.dont_write_bytecode = True


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def pin(path):
    data = path.read_bytes()
    return {"path": path.as_posix(), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def load_candidate(source, candidate_root):
    sys.path.insert(0, str(source / "ck3_autonomous_player/src"))
    # Import the actual package before installing one optional candidate child.
    import xar_autoplayer.bridge
    name = "xar_autoplayer.bridge.army_county_entry_preview_condition_contract"
    path = candidate_root / "ck3_autonomous_player/src/xar_autoplayer/bridge/army_county_entry_preview_condition_contract.py"
    spec = importlib.util.spec_from_file_location(name, path)
    contract = importlib.util.module_from_spec(spec)
    sys.modules[name] = contract
    spec.loader.exec_module(contract)
    original = source / "ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py"
    text = original.read_text(encoding="utf-8-sig")
    seams = [
        ("from .army_captured_target_land_supply_inputs_contract import (",
         "from .army_county_entry_preview_condition_contract import (\n    normalize_county_entry_condition_in_route_preview,\n)\nfrom .army_captured_target_land_supply_inputs_contract import ("),
        ('            current = self.take_internal_semantic_snapshot()\n            if not _same_paused_native_frame(starting, current):\n                raise BridgeUnavailableError(\n                    "native move preview crossed a snapshot revision"',
         '            try:\n                route_preview = normalize_county_entry_condition_in_route_preview(route_preview)\n            except ValueError as error:\n                raise BridgeUnavailableError(\n                    f"native preview county-entry condition is malformed: {error}"\n                ) from error\n            current = self.take_internal_semantic_snapshot()\n            if not _same_paused_native_frame(starting, current):\n                raise BridgeUnavailableError(\n                    "native move preview crossed a snapshot revision"'),
    ]
    if "from .army_county_entry_preview_condition_contract import (" not in text:
        for before, after in seams:
            require(text.count(before) == 1, "real Driver has the pinned unique preview seam")
            text = text.replace(before, after, 1)
    module = types.ModuleType("xar_autoplayer.bridge._county_preview_candidate_driver")
    module.__package__ = "xar_autoplayer.bridge"
    module.__file__ = str(original)
    sys.modules[module.__name__] = module
    exec(compile(text, str(original), "exec"), module.__dict__)
    return module.NativeHeadlessGameplayDriver, contract, hashlib.sha256(text.encode()).hexdigest()


def child():
    return {"schema_version": 1,
            "source": "native_preview_first_edge_county_entry_condition",
            "input_basis": "current_unit_and_preview_first_remaining_province",
            "predicate_rva": 0x24E2230, "status": "available", "unavailable_reason": None,
            "subject_army_id": 18, "requested_target_province_id": 2646,
            "source_province_id": 2635, "target_province_id": 2645,
            "native_carmy_id": 18, "actor_character_id": 31254, "mode": 1,
            "army_1d4_raw": 0, "source_definition_1b_u8": 1, "target_definition_1b_u8": 1,
            "source_county_present": True, "target_county_present": True,
            "county_objects_differ": True, "source_county_identity": "native:1000",
            "target_county_identity": "native:2000", "target_county_magic_3e0_u32": 0x436F4461,
            "inputs_observation_ready": True, "native_condition_called": True,
            "native_condition_passes": False, "identity_before_after_match": True,
            "internal_subpredicates_observed": False, "actual_loss_observed": False}


def query(Driver, county):
    from xar_autoplayer.bridge.version_identity import CK3_12004
    from xar_autoplayer.bridge.war_contract import preview_move_army_step
    step = preview_move_army_step(18, 2646)
    route = {"status": "available", "army_id": 18, "origin_province_id": 2635,
             "target_province_id": 2646, "route_province_ids": [2635, 2645, 2646]}
    if county is not ...:
        route["county_entry_condition_v1"] = deepcopy(county)
    armies = [{"army_id": 18, "owner_character_id": 31254, "soldiers": 1184,
               "current_province_id": 2635, "move_target_province_id": None,
               "controllable": True, "route_province_ids": [], "combat_id": None,
               "retreating": False}]

    class Endpoint:
        pipe_name = r"\\.\pipe\offline-county-preview-fixture"
        on_frame = None
        def __init__(self): self.requests = []
        def start(self, on_frame, on_disconnect): self.on_frame = on_frame
        def publish(self, frame): self.on_frame(deepcopy(frame))
        def send(self, request):
            self.requests.append(deepcopy(request))
            if request.get("type") == "execute_step":
                require(request["step"] == step, "only existing preview primitive is requested")
                self.publish({"type": "command_result", "protocol_version": 1,
                              "request_id": request["request_id"], "ok": True,
                              "result": {"step": step, "accepted": True, "status": "available",
                                         "route_preview": deepcopy(route)}})
        def transport_error(self): return None
        def close(self): pass

    endpoint = Endpoint()
    driver = Driver(endpoint.pipe_name, endpoint=endpoint, command_timeout_seconds=1.0)
    endpoint.publish({"type": "hello", "protocol_version": 1, "bridge_version": "0.1.0",
                      "pid": 4242, "session_generation": 0,
                      "expected_ck3_version": CK3_12004.game_version,
                      "expected_ck3_sha256": CK3_12004.executable_sha256,
                      "capabilities": ["game.state.snapshot", "game.state.war-objectives",
                                       "game.state.army-routes", "game.command.preview-move-army-N-to-N"]})
    endpoint.publish({"type": "state_snapshot", "protocol_version": 1,
                      "snapshot_id": "native:40", "revision": 40,
                      "state": {"phase": "map_hud", "date": "fixture-only", "date_raw": 53147472,
                                "speed": 1, "paused": True, "map_ready": True, "history": [],
                                "active_event": None, "pending_character_interaction": None,
                                "played_character": {"character_id": 31254, "alive": True},
                                "player_armies": deepcopy(armies),
                                "active_wars": [{"war_id": 61, "player_side": "attacker",
                                                 "primary_opponent_character_id": 31255,
                                                 "player_is_primary_war_leader": True,
                                                 "player_relative_war_score": 0,
                                                 "allied_armies": deepcopy(armies), "enemy_armies": [],
                                                 "war_objective_province_ids": [2646],
                                                 "objective_province_states": [], "targeted_title_ids": []}]}})
    before = driver.take_snapshot()
    try:
        require(step in driver.capabilities()["action_steps"], "existing preview capability admits target")
        result = driver.execute_step(step, expected_revision=before["revision"])
        after = driver.take_snapshot()
        require(before["player_armies"] == after["player_armies"]
                and before["date_raw"] == after["date_raw"], "read-only preview leaves retained frame intact")
        require(len([r for r in endpoint.requests if r.get("type") == "execute_step"]) == 1,
                "one existing preview request with no retry")
        return result
    finally:
        driver.close()


def run(source, candidate_root):
    Driver, contract, driver_sha = load_candidate(source, candidate_root)
    checks = []
    result = query(Driver, child())
    observed = result["route_preview"]["county_entry_condition_v1"]
    require(observed["native_condition_passes"] is False and observed["status"] == "available",
            "observed false is available and remains false")
    require(result["route_preview"]["route_province_ids"] == [2635, 2645, 2646],
            "route survives first-edge child")
    checks.append("available native false survives real Driver preview with first-hop identity")

    unavailable = child()
    unavailable.update(status="unavailable", unavailable_reason="preview_county_actor_army_or_province_unresolved",
                       inputs_observation_ready=False, native_condition_called=False,
                       identity_before_after_match=False, native_condition_passes=None,
                       native_carmy_id=None, actor_character_id=None, mode=None,
                       army_1d4_raw=None, source_definition_1b_u8=None, target_definition_1b_u8=None,
                       source_county_present=None, target_county_present=None,
                       county_objects_differ=None, source_county_identity=None,
                       target_county_identity=None, target_county_magic_3e0_u32=None)
    result = query(Driver, unavailable)
    require(result["accepted"] is True and result["route_preview"]["county_entry_condition_v1"]["native_condition_passes"] is None,
            "unavailable child keeps route available and native result unknown")
    checks.append("unresolved actor/reader child preserves available route and unknown native result")

    wrong = child()
    wrong["target_province_id"] = 2646
    try:
        query(Driver, wrong)
    except Exception as error:
        require(type(error).__name__ == "BridgeUnavailableError" and "first-edge" in str(error),
                "real Driver rejects final-target identity masquerading as first hop")
    else:
        raise AssertionError("wrong first-hop child was accepted")
    checks.append("actual Driver rejects multi-hop final-target child instead of first remaining hop")

    legacy = query(Driver, ...)
    require("county_entry_condition_v1" not in legacy["route_preview"], "legacy optional absence preserved")
    malformed = child()
    malformed["native_condition_passes"] = None
    try:
        contract.normalize_county_entry_preview_condition_v1(malformed)
    except ValueError:
        pass
    else:
        raise AssertionError("available child without actual bool was accepted")
    checks.append("legacy absence stays valid; available without actual bool is rejected")
    return {"status": "GREEN", "focused_case_count": 4, "checks": checks,
            "candidate_driver_text_sha256_without_bom": driver_sha,
            "actual_driver_requests": 4, "new_mcp_tools": 0,
            "game_sdk_calls": 0, "native_builds": 0, "native_executions": 0,
            "fixture_boundary": "Authored DTO and hello/state/transport endpoint; production Driver branch and strict normalizer execute. No native collector/serializer or actual game positive is credited.",
            "sample_result": result}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--candidate-root", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = run(args.source_root, args.candidate_root)
        code = 0
    except Exception as error:
        import traceback
        result = {"status": "RED", "error": str(error), "traceback": traceback.format_exc()}
        code = 1
    result.update(machine_id="desktop-3fevhd2-1c74096080",
                  observed_at_utc=datetime.now(timezone.utc).isoformat(),
                  test_source=pin(Path(__file__)), run_exit=code)
    args.receipt.write_bytes((json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode())
    print(json.dumps({k: result.get(k) for k in ("status", "focused_case_count", "error", "run_exit")}))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
