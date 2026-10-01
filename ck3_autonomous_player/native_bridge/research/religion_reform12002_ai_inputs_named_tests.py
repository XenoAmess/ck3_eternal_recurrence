"""One actual named AI input case/two commands; frozen matrices never run."""
from datetime import datetime, timezone
import argparse
import json
import os
from pathlib import Path
import re
import subprocess

from religion_reform12002_query_mailbox_tests import SOURCES, sha, require
from religion_reform12002_ai_inputs_mailbox_tests import PROVIDERS, NEW, DEFINES, WIRE
from test_government_runtime_adapter_12002_standalone import run_batch
from test_government_runtime_adapter_bridge_binder_v1_standalone import visual_studio_developer_shell

NATIVE = Path(__file__).resolve().parent.parent
ROOT = NATIVE.parent.parent
CHANGED = ("main_thread_query_mailbox_v1.cpp", "ck3_12002_query_mailbox.cpp")
TEST = "religion_reform12002_ai_inputs_named_test.cpp"
NAMED = "permitted_executor_religion_ai_reform_inputs12002"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--generic-objects", type=Path, required=True)
    args = parser.parse_args()
    output = args.artifacts.resolve(); output.mkdir(parents=True, exist_ok=True)
    temporary = output / "temp"; temporary.mkdir(exist_ok=True)
    os.environ["TEMP"] = os.environ["TMP"] = str(temporary)
    cache = args.generic_objects.resolve()
    prior = json.loads((cache / "result.json").read_text(encoding="utf-8"))
    source_names = SOURCES + PROVIDERS + (NEW,)
    header = NATIVE / "include/xar_bridge/main_thread_query_mailbox_v1.hpp"
    paths = [NATIVE / "src" / name for name in source_names + (TEST,
             "religion_reform12002_ai_inputs_mailbox_test.cpp", "religion_reform12002_query_mailbox_test.cpp")]
    paths += [header, Path(__file__).resolve()]
    pins = {path.relative_to(ROOT).as_posix(): sha(path) for path in paths}
    reused = {}; objects = []
    for name in source_names:
        if name in CHANGED:
            objects.append(str(output / Path(name).with_suffix(".obj")))
            continue
        source = NATIVE / "src" / name
        require(sha(source) == prior["source_sha256"][source.relative_to(ROOT).as_posix()], "frozen source changed: " + name)
        obj = cache / Path(name).with_suffix(".obj") if name == NEW else Path(prior["reused_frozen_objects"][name]["path"])
        require(obj.is_file(), "frozen production object missing: " + name)
        if name != NEW:
            require(sha(obj) == prior["reused_frozen_objects"][name]["sha256"], "frozen production object changed: " + name)
        reused[name] = {"path": str(obj), "sha256": sha(obj)}; objects.append(str(obj))
    template = NATIVE / "src/religion_reform12002_ai_inputs_mailbox_test.cpp"
    text = template.read_text(encoding="utf-8-sig")
    signature = "int main(int argc, char **argv)"
    require(text.count(signature) == 1, "frozen generic AI caller has one outer main")
    helper = output / "religion_reform12002_ai_inputs_named_frozen_helpers.hpp"
    helper.write_text(text.replace(signature, "int FrozenAIInputsGenericMainNotExecuted(int argc, char **argv)", 1),
                      encoding="utf-8")
    fields = sorted(set(re.findall(r"MainThreadQueryExecutorV1 (permitted_executor\w*) = nullptr;",
                                  header.read_text(encoding="utf-8-sig"))))
    require(NAMED in fields and "permitted_executor" in fields, "actual dedicated field present")
    others = [name for name in fields if name != NAMED]
    permits_helper = output / "religion_reform12002_ai_inputs_named_other_permits.hpp"
    permits_helper.write_text(
        "inline void ClearOtherAIInputsPermits(api::MainThreadQueryMailboxV1 &mailbox) {\n" +
        "".join("  mailbox." + name + " = nullptr;\n" for name in others) + "}\n" +
        "inline bool AllOtherAIInputsPermitsNull(const api::MainThreadQueryMailboxV1 &mailbox) {\n  return " +
        " &&\n         ".join("mailbox." + name + " == nullptr" for name in others) + ";\n}\n", encoding="utf-8")
    compiler = ["cl.exe", "/nologo", "/std:c++20", "/EHsc", "/W4", "/WX", "/utf-8", "/DNOMINMAX", "/O2",
                *["/D" + define for define in DEFINES], "/I" + str(NATIVE / "include"),
                "/I" + str(NATIVE / "src"), "/I" + str(output)]
    shell = visual_studio_developer_shell()
    run_batch(command=compiler + ["/c", "/MP2"] + [str(NATIVE / "src" / name) for name in CHANGED],
              shell=shell, output=output, tag="changed-shared")
    executable = output / "religion-ai-reform-inputs-named.exe"
    run_batch(command=compiler + [str(NATIVE / "src" / TEST)] + objects + ["User32.lib", "/Fe:" + str(executable)],
              shell=shell, output=output, tag="named-only")
    wire_directory = output / "wire"; wire_directory.mkdir(exist_ok=True)
    completed = subprocess.run([str(executable), str(wire_directory)], cwd=output, capture_output=True,
                               text=True, encoding="utf-8", errors="replace", timeout=15)
    (output / "run.log").write_text(completed.stdout + completed.stderr, encoding="utf-8")
    require(completed.returncode == 0, "actual AI inputs named queue failed: " + str(output / "run.log"))
    wires = []
    require(sorted(path.name for path in wire_directory.glob("*.json")) == sorted(WIRE), "only two commands in one named case executed")
    for name in WIRE:
        wire = wire_directory / name; generic_wire = cache / "wire" / name
        require(wire.read_bytes() == generic_wire.read_bytes(), "actual named AI packet differs from frozen generic: " + name)
        packet = json.loads(wire.read_text(encoding="utf-8"))
        require(packet["type"] == "command_result" and packet["protocol_version"] == 1 and packet["ok"] is True and
                packet["result"]["step"] == "query-player-religion-ai-reform-inputs-v1", "complete actual native protocol")
        wires.append({"path": str(wire), "sha256": sha(wire), "same_bytes_as_generic_wire": str(generic_wire)})
    require(pins == {path.relative_to(ROOT).as_posix(): sha(path) for path in paths}, "named input changed during compile/run")
    receipt = {"schema": "xar.ck3.religion-ai-reform-inputs-named-queue-fixture/v1", "status": "GREEN",
        "time_utc": datetime.now(timezone.utc).isoformat(), "mode": "O2_W4_WX", "cases": 1, "queued_commands": 2,
        "stdout": completed.stdout.strip(), "source_sha256": pins, "defines": list(DEFINES),
        "compiled_shared_sources": list(CHANGED), "reused_frozen_objects": reused,
        "helper_template": str(template), "helper_template_sha256": sha(template),
        "helper_copy": str(helper), "helper_copy_sha256": sha(helper),
        "template_mutation": "artifact copy outer main renamed; frozen source unchanged",
        "other_permit_helper": str(permits_helper), "other_permit_helper_sha256": sha(permits_helper),
        "cleared_other_permits": others,
        "frozen_12_case_main_invoked": False, "frozen_generic_main_invoked": False,
        "ai_provider_matrix_repeated": False, "schedule_provider_matrix_repeated": False, "old_matrices_repeated": False,
        "named_permit": NAMED, "generic_permit_cleared": True, "actual_named_admission": True,
        "actual_owner_drain_finish_wait_reclaim": True, "install_environment_propagation_exercised": False,
        "raw_command_results": wires, "executable_sha256": sha(executable),
        "readiness": "static-ready readonly named AI inputs queue fixture", "ck3_accessed": False, "live_verified": False}
    result = output / "result.json"; result.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "GREEN", "result": str(result), "sha256": sha(result), "stdout": completed.stdout.strip()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
