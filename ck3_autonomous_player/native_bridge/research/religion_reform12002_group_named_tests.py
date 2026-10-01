"""One actual named draft-groups queue case; frozen matrices are never run."""
from datetime import datetime, timezone
import argparse
import json
import os
from pathlib import Path
import subprocess

from religion_reform12002_query_mailbox_tests import SOURCES, sha, require
from religion_reform12002_group_mailbox_tests import NEW
from test_government_runtime_adapter_12002_standalone import run_batch
from test_government_runtime_adapter_bridge_binder_v1_standalone import visual_studio_developer_shell

NATIVE = Path(__file__).resolve().parent.parent
ROOT = NATIVE.parent.parent
CHANGED = ("main_thread_query_mailbox_v1.cpp", "ck3_12002_query_mailbox.cpp")
TEST = "religion_reform12002_group_named_test.cpp"
DEFINES = ("XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_GROUPS_PRIVATE_QUERY_V1=1",
           "XAR_REFORM_MAILBOX_STANDALONE_ADAPTER=1")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--group-objects", type=Path, required=True)
    parser.add_argument("--original-objects", type=Path, required=True)
    args = parser.parse_args()
    output = args.artifacts.resolve(); output.mkdir(parents=True, exist_ok=True)
    temporary = output / "temp"; temporary.mkdir(exist_ok=True)
    os.environ["TEMP"] = os.environ["TMP"] = str(temporary)
    group_cache = args.group_objects.resolve(); original_cache = args.original_objects.resolve()
    prior = json.loads((group_cache / "result.json").read_text(encoding="utf-8"))
    source_names = SOURCES + NEW
    paths = [NATIVE / "src" / name for name in source_names + (TEST, "religion_reform12002_group_mailbox_test.cpp",
                                                                "religion_reform12002_query_mailbox_test.cpp")]
    paths += [NATIVE / "include/xar_bridge/main_thread_query_mailbox_v1.hpp", Path(__file__).resolve()]
    pins = {path.relative_to(ROOT).as_posix():sha(path) for path in paths}
    reused = {}; objects = []
    group_owned_objects = NEW + ("ck3_12002_religion_context.cpp",)
    for name in source_names:
        if name in CHANGED:
            objects.append(str(output / Path(name).with_suffix(".obj")))
            continue
        source = NATIVE / "src" / name
        require(sha(source) == prior["source_sha256"][source.relative_to(ROOT).as_posix()], "frozen production source changed: " + name)
        obj = (group_cache if name in group_owned_objects else original_cache) / Path(name).with_suffix(".obj")
        require(obj.is_file(), "frozen production object missing: " + name)
        reused[name] = {"path":str(obj), "sha256":sha(obj)}; objects.append(str(obj))
    template = NATIVE / "src/religion_reform12002_group_mailbox_test.cpp"
    text = template.read_text(encoding="utf-8-sig")
    signature = "int main(int argc, char **argv)"
    require(text.count(signature) == 1, "frozen group matrix has one original main")
    # The group test already renames the nested 12-case main. Rename only its
    # own outer main in this artifact copy, avoiding nested macro redefinition.
    helper = output / "religion_reform12002_group_named_frozen_helpers.hpp"
    helper.write_text(text.replace(signature, "int FrozenDraftGroups4CaseMainNotExecuted(int argc, char **argv)", 1),
                      encoding="utf-8")
    compiler = ["cl.exe", "/nologo", "/std:c++20", "/EHsc", "/W4", "/WX", "/utf-8", "/DNOMINMAX", "/O2",
                *["/D"+define for define in DEFINES], "/I"+str(NATIVE / "include"),
                "/I"+str(NATIVE / "src"), "/I"+str(output)]
    shell = visual_studio_developer_shell()
    run_batch(command=compiler+["/c", "/MP2"]+[str(NATIVE / "src" / name) for name in CHANGED],
              shell=shell, output=output, tag="changed-shared")
    executable = output / "religion-draft-groups-named.exe"
    run_batch(command=compiler+[str(NATIVE / "src" / TEST)]+objects+["User32.lib", "/Fe:"+str(executable)],
              shell=shell, output=output, tag="named-only")
    wire_directory = output / "wire"; wire_directory.mkdir(exist_ok=True)
    completed = subprocess.run([str(executable), str(wire_directory)], cwd=output, capture_output=True,
                               text=True, encoding="utf-8", errors="replace", timeout=15)
    (output / "run.log").write_text(completed.stdout+completed.stderr, encoding="utf-8")
    require(completed.returncode == 0, "actual draft groups named queue failed: " + str(output / "run.log"))
    wire = wire_directory / "visible-multi-slots.json"
    require(list(wire_directory.glob("*.json")) == [wire], "only the new one-case named matrix executed")
    generic_wire = group_cache / "wire/visible-multi-slots.json"
    require(wire.read_bytes() == generic_wire.read_bytes(),
            "actual named caller complete wire differs from the frozen generic caller on the same native input")
    packet = json.loads(wire.read_text(encoding="utf-8"))
    require(packet["type"] == "command_result" and packet["protocol_version"] == 1 and packet["ok"] is True and
            packet["result"]["step"] == "query-player-religion-draft-groups-v1", "complete actual native protocol output")
    require(pins == {path.relative_to(ROOT).as_posix():sha(path) for path in paths}, "named fixture source changed during execution")
    receipt = {"schema":"xar.ck3.religion-draft-groups-named-queue-fixture/v1", "status":"GREEN",
        "time_utc":datetime.now(timezone.utc).isoformat(), "mode":"O2_W4_WX", "cases":1,
        "stdout":completed.stdout.strip(), "source_sha256":pins, "defines":list(DEFINES),
        "compiled_shared_sources":list(CHANGED), "reused_frozen_objects":reused,
        "helper_template":str(template), "helper_template_sha256":sha(template),
        "helper_copy":str(helper), "helper_copy_sha256":sha(helper),
        "template_mutation":"artifact copy outer main renamed; frozen source unchanged",
        "frozen_12_case_main_invoked":False, "frozen_4_case_main_invoked":False, "old_matrices_repeated":False,
        "named_permit":"permitted_executor_religion_draft_groups12002", "generic_permit_cleared":True,
        "actual_named_admission":True, "actual_owner_drain_finish_wait_reclaim":True,
        "install_environment_propagation_exercised":False,
        "wire":{"path":str(wire),"sha256":sha(wire),"same_bytes_as_generic_wire":str(generic_wire)},
        "executable_sha256":sha(executable), "readiness":"static-ready named queue fixture",
        "ck3_accessed":False,"live_verified":False}
    result = output / "result.json"; result.write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":"GREEN","result":str(result),"sha256":sha(result),"stdout":completed.stdout.strip()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
