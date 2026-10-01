"""One actual full Doctrine choices owning caller; no old/provider matrices or CK3."""
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
NEW = ("religion_reform12002_fullchoices.cpp", "religion_reform12002_fullchoices_mailbox.cpp")
CHANGED = ("main_thread_query_mailbox_v1.cpp", "ck3_12002_query_mailbox.cpp", "ck3_12002_religion_context.cpp")
TEST = "religion_reform12002_fullchoices_mailbox_test.cpp"
DEFINES = ("XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_DOCTRINE_CHOICES_PRIVATE_QUERY_V1=1",
           "XAR_REFORM_MAILBOX_STANDALONE_ADAPTER=1")
WIRE = "visible-four-slots.json"


def validate_wire(directory):
    path = directory / WIRE
    packet = json.loads(path.read_text(encoding="utf-8"))
    require(packet["type"] == "command_result" and packet["protocol_version"] == 1 and
            packet["ok"] is True and packet["request_id"] == 'draft-doctrines"mailbox-fixture',
            "complete actual native protocol wrapper")
    result = packet["result"]; out = result["player_religion_draft_doctrine_choices"]
    require(result["step"] == "query-player-religion-draft-doctrine-choices-v1" and
            result["domain_key"] == "player_religion_draft_doctrine_choices_v1" and
            result["backend_id"] == "ck3-1.20.0.2-native-player-religion-draft-doctrine-choices-v1" and
            result["accepted"] is True and result["private_build"] is True and
            result["read_only"] is True and result["advertised"] is False and
            result["game_version"] == "1.20.0.2" and result["executable_sha256"] == EXE_SHA and
            result["snapshot_revision"] == 701 and result["date_raw"] == 53175816 and
            result["status"] == "observed", "actual full Doctrine caller metadata")
    require(out["schema"] == "ck3_12002_current_draft_full_doctrine_choices_v1" and
            out["scope"] == "actual_current_draft_selected_slot_group_sources" and
            out["game_version"] == "1.20.0.2" and out["executable_sha256"] == EXE_SHA and
            out["available"] is True and out["unavailable_reason"] is None and
            out["played_character_id"] == ACTOR and out["date_raw"] == 53175816 and
            out["capture_epoch"] == 3 and out["source_rite_id"] == 0x80000000 and
            out["draft_observed"] is True and out["doctrine_gates_complete"] is True,
            "actual full Doctrine provider identity and readiness")
    slots = out["slots"]
    require(len(slots) == 4 and [len(slot["sources"]) for slot in slots] == [6, 6, 3, 0] and
            [slot["slot_index"] for slot in slots] == [0, 1, 2, 3] and
            [slot["selected_doctrine_key"] for slot in slots] == ["doctrine_a", "doctrine_b", "doctrine_g", "doctrine_j"] and
            [slot["group_key"] for slot in slots] == ["group_a", "group_a", "group_g", "group_zero"],
            "actual selected slots and per-slot group sources")
    first = slots[0]["sources"]
    require(first[0]["currently_selected"] is True and first[0]["final_selectable"] is True and
            first[1]["duplicate_excluded"] is True and first[1]["passed_shown"] is None and
            first[1]["native_can_pick"] is None and first[1]["final_selectable"] is False and
            first[2]["passed_shown"] is False and first[2]["native_can_pick"] is False and
            first[2]["native_knows_doctrine"] is None and first[2]["final_selectable"] is False and
            first[3]["passed_shown"] is True and first[3]["native_can_pick"] is False and
            first[4]["native_knows_doctrine"] is False and first[4]["native_has_prophet"] is False and
            first[4]["final_selectable"] is False and first[5]["final_selectable"] is True,
            "actual duplicate exclusion and native gate false/null short-circuit distinctions")
    require(sum(row["final_selectable"] for slot in slots for row in slot["sources"]) == 5,
            "actual five final selectable source rows")
    require(len(list(directory.glob("*.json"))) == 1, "only one new actual wrapper case executed")
    return {WIRE: sha(path)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--frozen-objects", type=Path, required=True)
    args = parser.parse_args()
    output = args.artifacts.resolve(); output.mkdir(parents=True, exist_ok=True)
    temporary = output / "temp"; temporary.mkdir(exist_ok=True)
    os.environ["TEMP"] = os.environ["TMP"] = str(temporary)
    cache = args.frozen_objects.resolve()
    old = json.loads((cache.parent / "result.json").read_text(encoding="utf-8"))
    paths = [NATIVE / "src" / name for name in SOURCES + NEW + (TEST, "religion_reform12002_query_mailbox_test.cpp")]
    paths += [NATIVE / "include/xar_bridge" / name for name in (
        "main_thread_query_mailbox_v1.hpp", "religion_reform12002_group_model.hpp",
        "religion_reform12002_fullchoices.hpp", "religion_reform12002_fullchoices_mailbox.hpp")]
    paths.append(Path(__file__).resolve())
    pins = {path.relative_to(ROOT).as_posix(): sha(path) for path in paths}
    reused = {}
    for name in SOURCES:
        if name in CHANGED:
            continue
        source = NATIVE / "src" / name
        require(sha(source) == old["source_sha256"][source.relative_to(ROOT).as_posix()], "frozen source changed: " + name)
        obj = cache / Path(name).with_suffix(".obj")
        require(obj.is_file(), "frozen object missing: " + name)
        reused[name] = {"path": str(obj), "sha256": sha(obj)}
    compiler = ["cl.exe", "/nologo", "/std:c++20", "/EHsc", "/W4", "/WX", "/utf-8", "/DNOMINMAX", "/O2",
                *["/D" + define for define in DEFINES], "/I" + str(NATIVE / "include")]
    shell = visual_studio_developer_shell()
    run_batch(command=compiler + ["/c", "/MP5"] + [str(NATIVE / "src" / name) for name in CHANGED + NEW],
              shell=shell, output=output, tag="new-and-changed")
    objects = [str((output if name in CHANGED else cache) / Path(name).with_suffix(".obj")) for name in SOURCES]
    objects += [str(output / Path(name).with_suffix(".obj")) for name in NEW]
    executable = output / "religion-full-doctrine-choices-mailbox.exe"
    run_batch(command=compiler + [str(NATIVE / "src" / TEST)] + objects + ["User32.lib", "/Fe:" + str(executable)],
              shell=shell, output=output, tag="fullchoices-only")
    wire = output / "wire"; wire.mkdir(exist_ok=True)
    completed = subprocess.run([str(executable), str(wire)], cwd=output, capture_output=True,
                               text=True, encoding="utf-8", errors="replace", timeout=20)
    (output / "run.log").write_text(completed.stdout + completed.stderr, encoding="utf-8")
    require(completed.returncode == 0, "actual new full Doctrine caller failed: " + str(output / "run.log"))
    wires = validate_wire(wire)
    require(pins == {path.relative_to(ROOT).as_posix(): sha(path) for path in paths}, "wrapper input changed during compile/run")
    receipt = {"schema": "xar.ck3.religion-full-doctrine-choices-mailbox-fixture/v1", "status": "GREEN",
        "time_utc": datetime.now(timezone.utc).isoformat(), "mode": "O2_W4_WX", "cases": 1,
        "stdout": completed.stdout.strip(), "source_sha256": pins, "defines": list(DEFINES),
        "compiled_sources": list(CHANGED + NEW), "reused_frozen_objects": reused,
        "actual_wire_sha256": wires, "executable_sha256": sha(executable),
        "actual_pipeline": "TrySubmit -> owner Drain -> actual full Doctrine reader -> Finish -> Wait/Reclaim -> complete native command_result -> Python decoder",
        "fixture_permit": "existing permitted_executor with exact full Doctrine callback",
        "dedicated_production_registration_tested": False, "old_matrices_repeated": False,
        "frozen_12_case_main_invoked": False, "provider_matrix_repeated": False,
        "ck3_accessed": False, "live_verified": False, "readiness": "static-ready query wrapper"}
    result = output / "result.json"; result.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "GREEN", "result": str(result), "sha256": sha(result), "stdout": completed.stdout.strip()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
