"""One actual reform named-slot O2 case; frozen matrices are never invoked."""
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
TEST = "religion_reform12002_query_named_test.cpp"
SHARED = ("main_thread_query_mailbox_v1.cpp", "ck3_12002_query_mailbox.cpp",
          "ck3_12002_religion_context.cpp")
DEFINES = ("XAR_CK3_ENABLE_G2_PLAYER_RELIGION_REFORM_CONTEXT_PRIVATE_QUERY_V1=1",
           "XAR_REFORM_MAILBOX_STANDALONE_ADAPTER=1")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--frozen-objects", type=Path, required=True)
    args = parser.parse_args()
    output = args.artifacts.resolve(); output.mkdir(parents=True, exist_ok=True)
    temporary = output / "temp"; temporary.mkdir(exist_ok=True)
    os.environ["TEMP"] = os.environ["TMP"] = str(temporary)
    cache = args.frozen_objects.resolve()
    old_receipt = json.loads((cache.parent / "result.json").read_text(encoding="utf-8"))
    paths = [NATIVE / "src" / name for name in SOURCES + (TEST, "religion_reform12002_query_mailbox_test.cpp")]
    paths += [NATIVE / "include/xar_bridge/main_thread_query_mailbox_v1.hpp", Path(__file__).resolve()]
    pins = {path.relative_to(ROOT).as_posix(): sha(path) for path in paths}
    reused = {}
    for name in SOURCES:
        if name in SHARED:
            continue
        path = NATIVE / "src" / name
        require(sha(path) == old_receipt["source_sha256"][path.relative_to(ROOT).as_posix()],
                "frozen production source changed: " + name)
        obj = cache / Path(name).with_suffix(".obj")
        require(obj.is_file(), "frozen O2 object missing: " + name)
        reused[name] = {"object": str(obj), "object_sha256": sha(obj), "source_sha256": sha(path)}
    shell = visual_studio_developer_shell()
    compiler = ["cl.exe", "/nologo", "/std:c++20", "/EHsc", "/W4", "/WX", "/utf-8", "/DNOMINMAX", "/O2",
                *["/D" + define for define in DEFINES], "/I" + str(NATIVE / "include")]
    run_batch(command=compiler + ["/c", "/MP2"] + [str(NATIVE / "src" / name) for name in SHARED],
              shell=shell, output=output, tag="changed-shared")
    objects = [str((output if name in SHARED else cache) / Path(name).with_suffix(".obj")) for name in SOURCES]
    executable = output / "reform-query-named.exe"
    run_batch(command=compiler + [str(NATIVE / "src" / TEST)] + objects + ["User32.lib", "/Fe:" + str(executable)],
              shell=shell, output=output, tag="named-only")
    wire_directory = output / "wire"; wire_directory.mkdir(exist_ok=True)
    completed = subprocess.run([str(executable), str(wire_directory)], cwd=output, capture_output=True,
                               text=True, encoding="utf-8", errors="replace", timeout=15)
    (output / "run.log").write_text(completed.stdout + completed.stderr, encoding="utf-8")
    require(completed.returncode == 0, "named queue case failed: " + str(output / "run.log"))
    wire = wire_directory / "visible-create.json"
    packet = json.loads(wire.read_text(encoding="utf-8"))
    result = packet["result"]; observed = result["player_religion_reform_context"]
    require(packet["type"] == "command_result" and packet["protocol_version"] == 1 and packet["ok"] is True and
            packet["request_id"] == 'reform"mailbox-fixture', "actual complete protocol wire")
    require(result["step"] == "query-player-religion-reform-context-v1" and result["accepted"] is True and
            result["private_build"] is True and result["read_only"] is True and result["advertised"] is False and
            result["snapshot_revision"] == 701 and result["date_raw"] == 53175816 and result["game_version"] == "1.20.0.2" and
            result["executable_sha256"] == EXE_SHA and result["domain_key"] == "player_religion_reform_context_v1" and
            result["backend_id"] == "ck3-1.20.0.2-native-player-religion-reform-context-v1", "actual caller metadata")
    require(observed["available"] is True and observed["played_character_id"] == ACTOR and observed["capture_epoch"] != 701 and
            observed["current_creation_window"]["draft_observed"] is True and
            observed["current_draft_eligibility"]["can_create_rite"] is True and
            observed["current_draft_costs"]["piety_cost_raw"] == 9000000 and
            observed["current_doctrine_selection"]["selectable_doctrine_keys"] == ["doctrine_a"], "actual single visible-create observation")
    require(list(wire_directory.glob("*.json")) == [wire], "only one case executed")
    require(pins == {path.relative_to(ROOT).as_posix(): sha(path) for path in paths}, "named fixture input changed during execution")
    receipt = {"schema": "xar.ck3.religion-reform-named-queue-fixture/v1", "status": "GREEN",
        "time_utc": datetime.now(timezone.utc).isoformat(), "mode": "O2_W4_WX", "cases": 1,
        "stdout": completed.stdout.strip(), "source_sha256": pins, "defines": list(DEFINES),
        "compiled_shared_sources": list(SHARED), "reused_frozen_objects": reused,
        "new_test": TEST, "frozen_12_case_main_renamed": "FrozenReform12CaseMainNotExecuted",
        "frozen_12_case_main_invoked": False, "old_matrices_repeated": False,
        "named_permit": "permitted_executor_religion_reform12002", "generic_permit_cleared": True,
        "actual_named_admission": True, "actual_owner_drain_finish_wait_reclaim": True,
        "install_environment_propagation_exercised": False,
        "wire": {"path": str(wire), "sha256": sha(wire)}, "executable_sha256": sha(executable),
        "readiness": "static-ready named queue fixture", "ck3_accessed": False, "live_verified": False}
    receipt_path = output / "result.json"
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "GREEN", "result": str(receipt_path), "result_sha256": sha(receipt_path), "stdout": completed.stdout.strip()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
