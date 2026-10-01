"""One combined AI holder/schedule owning caller case, two actual queued commands."""
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
CHANGED = ("main_thread_query_mailbox_v1.cpp", "ck3_12002_query_mailbox.cpp")
NEW = "religion_reform12002_ai_inputs_mailbox.cpp"
PROVIDERS = ("religion_reform12002_ai_context.cpp", "religion_reform12002_schedule.cpp")
TEST = "religion_reform12002_ai_inputs_mailbox_test.cpp"
DEFINES = ("XAR_CK3_ENABLE_G2_PLAYER_RELIGION_AI_REFORM_INPUTS_PRIVATE_QUERY_V1=1",
           "XAR_REFORM_MAILBOX_STANDALONE_ADAPTER=1")
WIRE = ("multiple-controllers.json", "observed-no-ai.json")


def pointer_free(value):
    if isinstance(value, dict):
        require(not {"actual_ai", "pointer", "address"}.intersection(value), "whole command_result must omit internal pointers")
        for child in value.values():
            pointer_free(child)
    elif isinstance(value, list):
        for child in value:
            pointer_free(child)


def validate_wire(directory):
    pins = {}
    for name in WIRE:
        path = directory / name
        packet = json.loads(path.read_text(encoding="utf-8"))
        require(packet["type"] == "command_result" and packet["protocol_version"] == 1 and
                packet["ok"] is True and packet["request_id"] == 'ai-inputs"mailbox-fixture', "complete actual native protocol")
        result = packet["result"]; out = result["player_religion_ai_reform_inputs"]
        require(result["step"] == "query-player-religion-ai-reform-inputs-v1" and
                result["domain_key"] == "player_religion_ai_reform_inputs_v1" and
                result["backend_id"] == "ck3-1.20.0.2-native-player-religion-ai-reform-inputs-v1" and
                result["accepted"] is True and result["private_build"] is True and
                result["read_only"] is True and result["advertised"] is False and
                result["game_version"] == "1.20.0.2" and result["executable_sha256"] == EXE_SHA and
                result["snapshot_revision"] == 701 and result["date_raw"] == 53175816 and
                result["status"] == "observed", "actual AI caller metadata")
        require(out["schema"] == "ck3_12002_player_religion_ai_reform_inputs_v1" and
                out["available"] is True and out["unavailable_reason"] is None and
                out["played_character_id"] == ACTOR and out["date_raw"] == 53175816 and
                out["capture_epoch"] == 3 and out["gate_inputs_observation_complete"] is True,
                "actual combined observation identity/readiness")
        base = out["schedule_base"]
        require(base["status"] == "observed" and base["ai_status"] == "not_supplied" and
                base["current_actor"] == {"actor_id": ACTOR, "highest_tier": 2, "current_independent_ruler": False} and
                base["native_globals"] == {"reformation_enabled": False, "rare_period_prepare_ticks": 360} and
                base["actual_ai_cache"]["available"] is False and
                all(value is None for key, value in base["actual_ai_cache"].items() if key != "available") and
                base["actual_ai_timer"] == {"available": False, "rare_countdown_prepare_ticks": None,
                    "rare_selected_raw": None, "units": "prepare_invocations"},
                "actual base globals/current actor retains null no-AI caches/timers and legal false values")
        context = out["context"]; rows = out["controllers"]
        require(context["available"] is True and context["actor_id"] == ACTOR and
                context["schema"] == "ck3_12002_reform_ai_context_v1", "actual frozen context serializer")
        if name == "multiple-controllers.json":
            require(out["context_status"] == context["status"] == "observed_controllers" and
                    out["controller_count"] == 3 and context["actual_holder_count"] == 5 and
                    out["controller_absence"] is None and len(rows) == 3 and
                    [row["context_index"] for row in rows] == [0, 1, 2] and
                    [row["kind"] for row in rows] == ["ordinary", "player_special", "ordinary"] and
                    [row["active_raw"] for row in rows] == [1, 1, 0], "actual all-matching table members, no guessed priority/default")
            require([row["schedule"]["ai_status"] for row in rows] == ["observed", "gates_only", "observed"] and
                    [row["schedule"]["actual_ai_cache"]["handler_cache_gates_pass"] for row in rows] == [True, False, True] and
                    [row["schedule"]["actual_ai_timer"]["rare_countdown_prepare_ticks"] for row in rows] == [-4, None, 12] and
                    [row["schedule"]["actual_ai_timer"]["available"] for row in rows] == [True, False, True] and
                    rows[0]["schedule"]["actual_ai_timer"]["rare_selected_raw"] == 1 and
                    rows[1]["schedule"]["actual_ai_cache"]["ai_special_raw"] == 1 and
                    rows[2]["schedule"]["actual_ai_cache"]["ai_active_raw"] == 0,
                    "actual independent per-member schedules, negative countdown, special gates-only, inactive record")
        else:
            require(out["context_status"] == context["status"] == "observed_no_ai" and
                    out["controller_count"] == 0 and context["actual_holder_count"] == 2 and
                    out["controller_absence"] == "no_actual_controller" and rows == context["controllers"] == [],
                    "known actual controller absence retains observed no-AI status")
        pointer_free(packet)
        pins[name] = sha(path)
    require(len(list(directory.glob("*.json"))) == 2, "only two commands in one combined case executed")
    return pins


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--context-objects", type=Path, required=True)
    parser.add_argument("--caller-objects", type=Path, required=True)
    parser.add_argument("--original-objects", type=Path, required=True)
    args = parser.parse_args()
    output = args.artifacts.resolve(); output.mkdir(parents=True, exist_ok=True)
    temporary = output / "temp"; temporary.mkdir(exist_ok=True)
    os.environ["TEMP"] = os.environ["TMP"] = str(temporary)
    caller_cache = args.caller_objects.resolve(); original_cache = args.original_objects.resolve()
    provider_cache = args.context_objects.resolve()
    prior = json.loads((caller_cache / "result.json").read_text(encoding="utf-8"))
    provider_prior = json.loads((provider_cache / "result.json").read_text(encoding="utf-8"))
    paths = [NATIVE / "src" / name for name in SOURCES + PROVIDERS + (NEW, TEST, "religion_reform12002_query_mailbox_test.cpp")]
    paths += [NATIVE / "include/xar_bridge" / name for name in (
        "main_thread_query_mailbox_v1.hpp", "religion_reform12002_ai_context.hpp",
        "religion_reform12002_schedule.hpp", "religion_reform12002_ai_inputs_mailbox.hpp")]
    paths.append(Path(__file__).resolve())
    pins = {path.relative_to(ROOT).as_posix(): sha(path) for path in paths}
    reused = {}; objects = []
    for name in SOURCES + PROVIDERS:
        if name in CHANGED:
            objects.append(str(output / Path(name).with_suffix(".obj")))
            continue
        source = NATIVE / "src" / name
        reference = provider_prior if name in PROVIDERS else prior
        require(sha(source) == reference["source_sha256"][source.relative_to(ROOT).as_posix()], "frozen source changed: " + name)
        cache = provider_cache if name in PROVIDERS else caller_cache if name == "ck3_12002_religion_context.cpp" else original_cache
        obj = cache / Path(name).with_suffix(".obj")
        require(obj.is_file(), "frozen object missing: " + name)
        reused[name] = {"path": str(obj), "sha256": sha(obj)}; objects.append(str(obj))
    compiler = ["cl.exe", "/nologo", "/std:c++20", "/EHsc", "/W4", "/WX", "/utf-8", "/DNOMINMAX", "/O2",
                *["/D" + define for define in DEFINES], "/I" + str(NATIVE / "include")]
    shell = visual_studio_developer_shell()
    run_batch(command=compiler + ["/c", "/MP3"] + [str(NATIVE / "src" / name) for name in CHANGED + (NEW,)],
              shell=shell, output=output, tag="new-and-shared")
    executable = output / "religion-ai-reform-inputs-mailbox.exe"
    run_batch(command=compiler + [str(NATIVE / "src" / TEST)] + objects +
              [str(output / Path(NEW).with_suffix(".obj")), "User32.lib", "/Fe:" + str(executable)],
              shell=shell, output=output, tag="ai-inputs-only")
    wire = output / "wire"; wire.mkdir(exist_ok=True)
    completed = subprocess.run([str(executable), str(wire)], cwd=output, capture_output=True,
                               text=True, encoding="utf-8", errors="replace", timeout=20)
    (output / "run.log").write_text(completed.stdout + completed.stderr, encoding="utf-8")
    require(completed.returncode == 0, "actual combined AI caller failed: " + str(output / "run.log"))
    wires = validate_wire(wire)
    require(pins == {path.relative_to(ROOT).as_posix(): sha(path) for path in paths}, "AI wrapper input changed during compile/run")
    receipt = {"schema": "xar.ck3.religion-ai-reform-inputs-mailbox-fixture/v1", "status": "GREEN",
        "time_utc": datetime.now(timezone.utc).isoformat(), "mode": "O2_W4_WX", "cases": 1, "queued_commands": 2,
        "stdout": completed.stdout.strip(), "source_sha256": pins, "defines": list(DEFINES),
        "compiled_sources": list(CHANGED + (NEW,)), "reused_frozen_objects": reused,
        "actual_wire_sha256": wires, "executable_sha256": sha(executable),
        "actual_pipeline": "TrySubmit -> owner Drain -> actual Core/actor -> holder context -> per-controller schedule -> Finish -> Wait/Reclaim -> complete native command_result",
        "fixture_permit": "existing permitted_executor with exact AI inputs callback",
        "dedicated_production_registration_tested": False, "old_matrices_repeated": False,
        "frozen_12_case_main_invoked": False, "ai_provider_matrix_repeated": False,
        "schedule_provider_matrix_repeated": False, "whole_packets_pointer_free": True,
        "holder_controller_extensions_unchanged": True, "ck3_accessed": False, "live_verified": False,
        "readiness": "static-ready readonly combined AI input query wrapper"}
    result = output / "result.json"; result.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "GREEN", "result": str(result), "sha256": sha(result), "stdout": completed.stdout.strip()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
