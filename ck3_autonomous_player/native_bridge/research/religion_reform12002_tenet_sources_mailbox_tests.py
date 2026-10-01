"""One new O2 actual Tenet source owning-queue packet; no CK3 or old matrix."""
from datetime import datetime, timezone
import argparse
import json
import os
from pathlib import Path
import subprocess

from religion_reform12002_query_mailbox_tests import EXE_SHA, ACTOR, sha, require
from test_government_runtime_adapter_12002_standalone import run_batch
from test_government_runtime_adapter_bridge_binder_v1_standalone import visual_studio_developer_shell

NATIVE = Path(__file__).resolve().parent.parent
ROOT = NATIVE.parent.parent
REUSED = ("ck3_12002.cpp", "religion_reform12002_window.cpp",
          "religion_doctrine12002_tenet_rows.cpp", "religion_reform12002_tenet_sources.cpp")
COMPILED = ("main_thread_query_mailbox_v1.cpp", "ck3_12002_query_mailbox.cpp", "protocol.cpp",
            "religion_reform12002_tenet_sources_mailbox.cpp")
TEST = "religion_reform12002_tenet_sources_mailbox_test.cpp"
BACKING = "religion_reform12002_tenet_sources_test.cpp"
HEADERS = ("main_thread_query_mailbox_v1.hpp", "ck3_12002_query_mailbox.hpp",
           "religion_reform12002_tenet_sources.hpp", "religion_reform12002_tenet_sources_mailbox.hpp")
DEFINES = ("XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_TENET_CHOICES_PRIVATE_QUERY_V1=1",)
WIRE = "actual-multiple-sources.json"


def validate_wire(directory, provider):
    path = directory / WIRE
    packet = json.loads(path.read_text(encoding="utf-8"))
    require(packet["type"] == "command_result" and packet["protocol_version"] == 1 and
            packet["ok"] is True and packet["request_id"] == 'draft-tenets"mailbox-fixture',
            "complete actual native protocol packet")
    result = packet["result"]
    require(result["step"] == "query-player-religion-draft-tenet-choices-v1" and
            result["domain_key"] == "player_religion_draft_tenet_choices_v1" and
            result["backend_id"] == "ck3-1.20.0.2-native-player-religion-draft-tenet-choices-v1" and
            result["accepted"] is True and result["private_build"] is True and
            result["read_only"] is True and result["advertised"] is False and
            result["game_version"] == "1.20.0.2" and result["executable_sha256"] == EXE_SHA and
            result["snapshot_revision"] == 701 and result["date_raw"] == 53175816 and
            result["status"] == "observed", "actual Tenet caller metadata")
    out = result["player_religion_draft_tenet_choices"]
    require(out["schema"] == "ck3_12002_current_draft_tenet_sources_v1" and
            out["available"] is True and out["played_character_id"] == ACTOR and
            out["capture_epoch"] != 701 and out["tenet_gates_complete"] is True,
            "actual Tenet reader identity and final-gate readiness")
    reference = provider / WIRE
    original = json.loads(reference.read_text(encoding="utf-8"))
    require({k: v for k, v in out.items() if k != "capture_epoch"} ==
            {k: v for k, v in original.items() if k != "capture_epoch"},
            "all actual provider fields unchanged through complete owner wire")
    require(len(list(directory.glob("*.json"))) == 1,
            "only one new multi-source query case executed")
    return {WIRE: sha(path)}, {"path": str(reference), "sha256": sha(reference)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--provider-objects", type=Path, required=True)
    args = parser.parse_args()
    output = args.artifacts.resolve(); output.mkdir(parents=True, exist_ok=True)
    temporary = output / "temp"; temporary.mkdir(exist_ok=True)
    os.environ["TEMP"] = os.environ["TMP"] = str(temporary)
    provider = args.provider_objects.resolve()
    frozen_result = provider / "result.json"
    old = json.loads(frozen_result.read_text(encoding="utf-8"))
    require(old["status"] == "GREEN" and old["actual_provider"] is True and
            old["actual_serializer"] is True, "frozen provider proof")
    paths = [NATIVE / "src" / name for name in REUSED + COMPILED + (TEST, BACKING)]
    paths += [NATIVE / "include/xar_bridge" / name for name in HEADERS]
    paths.append(Path(__file__).resolve())
    pins = {path.relative_to(ROOT).as_posix(): sha(path) for path in paths}
    reused = {}
    for name in REUSED + (BACKING,):
        source = NATIVE / "src" / name
        require(sha(source) == old["source_sha256"][str(source)], "frozen provider source changed: " + name)
        if name == BACKING:
            continue
        obj = provider / Path(name).with_suffix(".obj")
        require(obj.is_file(), "frozen provider object missing: " + name)
        reused[name] = {"path": str(obj), "sha256": sha(obj)}
    compiler = ["cl.exe", "/nologo", "/std:c++20", "/EHsc", "/W4", "/WX", "/utf-8",
                "/DNOMINMAX", "/O2", *["/D" + define for define in DEFINES],
                "/I" + str(NATIVE / "include")]
    shell = visual_studio_developer_shell()
    run_batch(command=compiler + ["/c", "/MP4"] + [str(NATIVE / "src" / name) for name in COMPILED],
              shell=shell, output=output, tag="new-tenet-queue")
    objects = [str(provider / Path(name).with_suffix(".obj")) for name in REUSED]
    objects += [str(output / Path(name).with_suffix(".obj")) for name in COMPILED]
    executable = output / "religion-draft-tenet-sources-mailbox.exe"
    run_batch(command=compiler + [str(NATIVE / "src" / TEST)] + objects +
              ["User32.lib", "/Fe:" + str(executable)],
              shell=shell, output=output, tag="tenet-single-case")
    wire = output / "wire"; wire.mkdir(exist_ok=True)
    completed = subprocess.run([str(executable), str(wire)], cwd=output, capture_output=True,
                               text=True, encoding="utf-8", errors="replace", timeout=20)
    (output / "run.log").write_text(completed.stdout + completed.stderr, encoding="utf-8")
    require(completed.returncode == 0, "actual Tenet queue fixture failed: " + str(output / "run.log"))
    wires, reference = validate_wire(wire, provider)
    require(pins == {path.relative_to(ROOT).as_posix(): sha(path) for path in paths},
            "actual Tenet wrapper compiled input changed")
    receipt = {"schema": "xar.ck3.religion-draft-tenet-sources-mailbox-fixture/v1", "status": "GREEN",
        "time_utc": datetime.now(timezone.utc).isoformat(), "mode": "O2_W4_WX", "cases": 1,
        "checks": 7, "complete_packets": 1, "stdout": completed.stdout.strip(),
        "source_sha256": pins, "defines": list(DEFINES), "compiled_sources": list(COMPILED),
        "reused_frozen_objects": reused, "frozen_provider_result": {
            "path": str(frozen_result), "sha256": sha(frozen_result)},
        "actual_provider_reference_wire": reference, "actual_wire_sha256": wires,
        "executable_sha256": sha(executable),
        "actual_pipeline": "TrySubmit -> owner Drain -> actual Tenet source reader/key copier -> Finish -> Wait/Reclaim -> complete native command_result -> JSON decoder",
        "fixture_permit": "existing permitted_executor with exact typed Tenet source callback",
        "native_functions_stubbed": True, "dedicated_production_registration_tested": False,
        "old_matrices_repeated": False, "frozen_provider_main_invoked": False,
        "dto_fabricated": False, "metadata_supplemented": False, "ck3_accessed": False,
        "live_verified": False, "readiness": "static-ready actual query wrapper"}
    result = output / "result.json"
    result.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "GREEN", "result": str(result), "sha256": sha(result),
                      "stdout": completed.stdout.strip()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
