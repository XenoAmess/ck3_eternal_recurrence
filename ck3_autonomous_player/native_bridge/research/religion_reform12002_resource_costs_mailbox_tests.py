"""One actual resource-cost worker/owner/provider/wire case; no CK3 or old matrices."""
from datetime import datetime, timezone
import argparse
import json
import os
from pathlib import Path
import subprocess

from religion_reform12002_query_mailbox_tests import SOURCES, EXE_SHA, ACTOR, sha, require
from test_government_runtime_adapter_12002_standalone import run_batch
from test_government_runtime_adapter_bridge_binder_v1_standalone import visual_studio_developer_shell

NATIVE = Path(__file__).resolve().parent.parent
ROOT = NATIVE.parent.parent
CHANGED = ("main_thread_query_mailbox_v1.cpp", "ck3_12002_query_mailbox.cpp",
           "ck3_12002_religion_context.cpp")
NEW = "religion_reform12002_resource_costs_mailbox.cpp"
PROVIDER = "religion_reform12002_resource_costs.cpp"
TEST = "religion_reform12002_resource_costs_mailbox_test.cpp"
DEFINES = ("XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_RESOURCE_COSTS_PRIVATE_QUERY_V1=1",
           "XAR_REFORM_MAILBOX_STANDALONE_ADAPTER=1")


def validate_wire(directory):
    path = directory / "visible-base-fee.json"
    packet = json.loads(path.read_text(encoding="utf-8"))
    require(packet["type"] == "command_result" and packet["protocol_version"] == 1 and
            packet["ok"] is True and packet["request_id"] == 'draft-resource-costs"mailbox-fixture',
            "complete native command-result packet")
    result = packet["result"]
    require(result["step"] == "query-player-religion-draft-resource-costs-v1" and
            result["domain_key"] == "player_religion_draft_resource_costs_v1" and
            result["backend_id"] == "ck3-1.20.0.2-native-player-religion-draft-resource-costs-v1" and
            result["accepted"] is True and result["private_build"] is True and
            result["read_only"] is True and result["advertised"] is False and
            result["game_version"] == "1.20.0.2" and result["executable_sha256"] == EXE_SHA and
            result["snapshot_revision"] == 701 and result["date_raw"] == 53175816 and
            result["status"] == "observed", "actual resource-cost caller metadata")
    out = result["player_religion_draft_resource_costs"]
    require(out["schema"] == "ck3_12002_player_religion_draft_resource_costs_query_v1" and
            out["available"] is True and out["window_present"] is True and out["draft_observed"] is True and
            out["failure"] is None and out["played_character_id"] == ACTOR and
            out["date_raw"] == 53175816 and out["capture_epoch"] != 701,
            "actual current-window query identity")
    window = out["current_draft_window"]
    require(window["schema"] == "ck3_12002_current_rite_creation_window_v1" and
            window["available"] is True and window["present"] is True and window["visible"] is True and
            window["draft_observed"] is True and window["source_rite_id"] == 0x80000000 and
            window["played_character_id"] == ACTOR and window["date_raw"] == out["date_raw"] and
            window["capture_epoch"] == out["capture_epoch"], "unmodified actual window DTO")
    quote = out["base_resource_cost_quote"]
    require(quote["schema"] == "ck3_12002_rite_creation_base_resource_costs_v1" and
            quote["scope"] == "native_command_draft_base_fee_quote" and
            quote["quote_source"] == "native_piety_getter_plus_exact_CCost_initialization" and
            quote["available"] is True and quote["base_resource_cost_vector_observed"] is True and
            quote["draft_kind"] == "create_rite_or_faith" and quote["raw_scale"] == 100000 and
            quote["resource_slot_names"] == ["gold", "prestige", "piety"] + [None] * 7 and
            quote["native_base_fee_slots_raw"] == [0, 0, 9000000] + [0] * 7 and
            quote["actual_debit_observed"] is False and
            quote["post_action_net_resource_change_observed"] is False,
            "exact native base-fee vector with honest quote-only scope")
    piety = quote["draft_quote"]
    require(piety["schema"] == "ck3_12002_rite_creation_costs_v1" and piety["available"] is True and
            piety["piety_cost_raw"] == 9000000 and piety["piety_missing_signed_raw"] == -2500000 and
            piety["has_enough_piety"] is True and piety["source_rite_id"] == 0x80000000 and
            piety["played_character_id"] == ACTOR and piety["date_raw"] == out["date_raw"] and
            piety["capture_epoch"] == out["capture_epoch"] and
            piety["other_resource_costs_observed"] is False,
            "original piety quote retained byte-for-value without widening its contract")
    require(len(list(directory.glob("*.json"))) == 1, "sole new case executed")
    return {path.name: sha(path)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--frozen-objects", type=Path, required=True)
    parser.add_argument("--resource-provider", type=Path, required=True)
    args = parser.parse_args()
    output = args.artifacts.resolve()
    output.mkdir(parents=True, exist_ok=True)
    temporary = output / "temp"
    temporary.mkdir(exist_ok=True)
    os.environ["TEMP"] = os.environ["TMP"] = str(temporary)
    cache = args.frozen_objects.resolve()
    original = json.loads((cache.parent / "result.json").read_text(encoding="utf-8"))
    provider_directory = args.resource_provider.resolve()
    provider_result = json.loads((provider_directory / "result.json").read_text(encoding="utf-8"))
    provider_delivery = json.loads((provider_directory.parent / "delivery-result.json").read_text(encoding="utf-8"))
    require(provider_result["status"] == "GREEN", "provider O2 receipt required")
    provider_sources = {key.replace("\\", "/"): value
                        for key, value in provider_result["source_sha256"].items()}
    provider_objects = {Path(item["path"]).name: item["sha256"]
                        for item in provider_delivery["provider_O2_objects"]}
    paths = [NATIVE / "src" / name for name in SOURCES + (NEW, PROVIDER, TEST,
             "religion_reform12002_query_mailbox_test.cpp")]
    paths += [NATIVE / "include/xar_bridge" / name for name in (
        "main_thread_query_mailbox_v1.hpp", "ck3_12002_query_mailbox.hpp",
        "religion_reform12002_window.hpp", "religion_reform12002_costs.hpp",
        "religion_reform12002_resource_costs.hpp", "religion_reform12002_resource_costs_mailbox.hpp")]
    paths.append(Path(__file__).resolve())
    pins = {path.relative_to(ROOT).as_posix(): sha(path) for path in paths}
    reused = {}
    objects = []
    for name in SOURCES:
        if name in CHANGED:
            objects.append(output / Path(name).with_suffix(".obj"))
            continue
        source = NATIVE / "src" / name
        require(sha(source) == original["source_sha256"][source.relative_to(ROOT).as_posix()],
                "frozen source changed: " + name)
        obj = (provider_directory if name == "religion_reform12002_costs.cpp" else cache) / Path(name).with_suffix(".obj")
        require(obj.is_file(), "frozen object missing: " + name)
        if name == "religion_reform12002_costs.cpp":
            require(sha(obj) == provider_objects[obj.name], "provider original cost object changed")
        reused[name] = {"path": str(obj), "sha256": sha(obj)}
        objects.append(obj)
    provider_source = NATIVE / "src" / PROVIDER
    require(sha(provider_source) == provider_sources[provider_source.relative_to(ROOT).as_posix()],
            "frozen new provider source changed")
    provider_obj = provider_directory / Path(PROVIDER).with_suffix(".obj")
    require(sha(provider_obj) == provider_objects[provider_obj.name], "frozen provider object changed")
    reused[PROVIDER] = {"path": str(provider_obj), "sha256": sha(provider_obj)}
    objects += [provider_obj, output / Path(NEW).with_suffix(".obj")]
    compiler = ["cl.exe", "/nologo", "/std:c++20", "/EHsc", "/W4", "/WX", "/utf-8",
                "/DNOMINMAX", "/O2", *["/D" + value for value in DEFINES],
                "/I" + str(NATIVE / "include")]
    shell = visual_studio_developer_shell()
    run_batch(command=compiler + ["/c", "/MP4"] + [str(NATIVE / "src" / name) for name in CHANGED + (NEW,)],
              shell=shell, output=output, tag="new-and-current-mailbox")
    executable = output / "religion-draft-resource-costs-mailbox.exe"
    run_batch(command=compiler + [str(NATIVE / "src" / TEST)] + [str(obj) for obj in objects] +
              ["User32.lib", "/Fe:" + str(executable)], shell=shell, output=output, tag="resource-only")
    wire = output / "wire"
    wire.mkdir(exist_ok=True)
    completed = subprocess.run([str(executable), str(wire)], cwd=output, capture_output=True,
                               text=True, encoding="utf-8", errors="replace", timeout=20)
    (output / "run.log").write_text(completed.stdout + completed.stderr, encoding="utf-8")
    require(completed.returncode == 0, "actual one-case resource mailbox failed: " + str(output / "run.log"))
    wires = validate_wire(wire)
    require(pins == {path.relative_to(ROOT).as_posix(): sha(path) for path in paths},
            "resource mailbox input changed during compile/run")
    receipt = {"schema": "xar.ck3.religion-draft-resource-costs-mailbox-fixture/v1", "status": "GREEN",
        "time_utc": datetime.now(timezone.utc).isoformat(), "mode": "O2_W4_WX", "cases": 1,
        "stdout": completed.stdout.strip(), "source_sha256": pins, "defines": list(DEFINES),
        "compiled_sources": list(CHANGED + (NEW,)), "reused_frozen_objects": reused,
        "provider_fixture_receipt": {"path": str(provider_directory / "result.json"),
                                     "sha256": sha(provider_directory / "result.json")},
        "actual_wire_sha256": wires, "executable_sha256": sha(executable),
        "actual_pipeline": "TrySubmit -> owner Drain -> actual window and base-resource-cost providers -> Finish -> Wait/Reclaim -> complete native command_result -> Python decoder",
        "fixture_permit": "existing permitted_executor with exact resource-cost callback",
        "dedicated_production_registration_tested": False, "old_matrices_repeated": False,
        "frozen_12_case_main_invoked": False, "ck3_accessed": False, "live_verified": False,
        "readiness": "static-ready query wrapper", "scope": "native_command_draft_base_fee_quote",
        "actual_debit_observed": False, "post_action_net_resource_change_observed": False}
    result = output / "result.json"
    result.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "GREEN", "result": str(result), "sha256": sha(result),
                      "stdout": completed.stdout.strip(), "wire_sha256": wires}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
