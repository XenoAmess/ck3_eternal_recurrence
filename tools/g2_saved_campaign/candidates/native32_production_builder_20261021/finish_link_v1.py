"""One authorized link-only continuation; preserve the failed producer and logs."""
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
from typing import Literal, TypedDict

import producer as base

PLAN = "metadata/LINK-CONTINUATION-PLAN01.json"
PARTIALS = tuple(base.ROOT / "bin" / ("xar_ck3_bridge" + x) for x in (".dll", ".map", ".lib", ".exp"))
DLL_CAP = 50331648
TMP_CAP = 8388608


class LinkAdmissionV1(TypedDict):
    schema: Literal["xar.native32.offline-link-continuation/v1"]
    machine_id: str
    status: Literal["ADMITTED"]
    owner: Literal["Root"]
    build_root: str
    plan_sha256: str
    producer_sha256: str
    phase_hard_bytes: int
    dll_leaf_cap_bytes: int
    temp_joint_cap_bytes: int
    review_at_utc: str
    root_direct_execution_release: Literal[True]
    link_attempts: Literal[1]
    recompile_allowed: Literal[False]
    overwrite_partial_outputs: Literal[True]
    Game_calls_allowed: Literal[False]
    DLL_loads_allowed: Literal[False]
    deployment_allowed: Literal[False]


def validate_admission(value: object, plan_sha: str, producer_sha: str) -> LinkAdmissionV1:
    raw = base.object_map(base.object_map(value).get("Native32_link_continuation"))
    expected: LinkAdmissionV1 = {
        "schema": "xar.native32.offline-link-continuation/v1", "machine_id": base.MACHINE,
        "status": "ADMITTED", "owner": "Root", "build_root": str(base.ROOT),
        "plan_sha256": plan_sha, "producer_sha256": producer_sha,
        "phase_hard_bytes": base.HARD, "dll_leaf_cap_bytes": DLL_CAP,
        "temp_joint_cap_bytes": TMP_CAP, "review_at_utc": base.DEADLINE.isoformat(),
        "root_direct_execution_release": True, "link_attempts": 1,
        "recompile_allowed": False, "overwrite_partial_outputs": True,
        "Game_calls_allowed": False, "DLL_loads_allowed": False, "deployment_allowed": False,
    }
    base.require(raw.keys() == expected.keys(), "link continuation fields differ")
    for key, item in expected.items():
        base.require(type(raw[key]) is type(item) and raw[key] == item, "link continuation differs: " + key)
    base.require(re.fullmatch(r"[0-9a-f]{64}", plan_sha) is not None and re.fullmatch(r"[0-9a-f]{64}", producer_sha) is not None, "canonical pins required")
    return expected


def enforce() -> int:
    caps = base.allowed_caps()
    caps["bin/xar_ck3_bridge.dll"] = DLL_CAP
    aggregate = {".msvc-temp": 0, "logs": 0, "metadata": 0, "commands": 0}
    total = 0
    for path in base.ROOT.rglob("*"):
        base.require(not path.is_symlink(), "output links not allowed")
        if not path.is_file():
            continue
        size = path.stat().st_size
        allocation = (size + 4095) // 4096 * 4096
        total += allocation
        rel = path.relative_to(base.ROOT).as_posix()
        if rel in caps:
            base.require(size <= caps[rel], "continuation leaf cap: " + rel)
        else:
            prefix = rel.split("/", 1)[0]
            if prefix in aggregate:
                aggregate[prefix] += allocation
            else:
                base.require(rel in ("PLAN01.json", "PLAN02.json", "PLAN03.json", "PLAN-QUALIFICATION01.json", "FAILED01.json", "FAILED02.json", "PRODUCTION-RESULT01.json"), "unexpected output: " + rel)
                aggregate["metadata"] += allocation
    base.require(aggregate[".msvc-temp"] <= TMP_CAP, "link temporary cap exceeded")
    base.require(aggregate["logs"] <= 917504, "joint logs cap exceeded")
    base.require(aggregate["metadata"] + aggregate["commands"] <= 524288, "joint metadata cap exceeded")
    base.require(total + 1048576 <= base.HARD, "phase cap exceeded")
    return total + 1048576


def compiled_inputs() -> tuple[list[base.FilePin], list[base.FilePin]]:
    objects: list[base.FilePin] = []
    receipts: list[base.FilePin] = []
    for item in base.recipe().compilation:
        path = base.ROOT / "commands" / ("native32-" + item.name + ".json")
        value = base.read_object(path)
        base.require(type(value.get("return_code")) is int and value["return_code"] == 0, "original compile not successful")
        base.require(base.string_list(value.get("command")) == list(item.argv), "original compile argv drift")
        objects.append(base.pin(item.object_path))
        receipts.append(base.pin(path))
    return objects, receipts


def make_plan() -> base.FilePin:
    base.require(not (base.ROOT / PLAN).exists(), "continuation plan already exists")
    objects, receipts = compiled_inputs()
    source = base.source_inputs()
    original = base.read_object(base.ROOT / "PLAN03.json")
    base.require(original.get("source_inputs") == source, "original source identities changed")
    input_value = base.read_object(base.ROOT / "metadata/INPUTS01.json")
    raw_inputs = input_value.get("reused_inputs")
    base.require(isinstance(raw_inputs, list), "reused input array required")
    # The original producer owns these typed, hashed records. Compare their
    # current stat against the canonical strings without refreshing a baseline.
    verify_reused(raw_inputs)
    plan = {
        "schema": "xar.native32.link-continuation-plan/v1", "machine_id": base.MACHINE,
        "observed_at_utc": base.now(), "review_at_utc": base.DEADLINE.isoformat(),
        "producer": base.pin(Path(__file__)), "original_producer": base.pin(Path(base.__file__)),
        "original_plan": base.pin(base.ROOT / "PLAN03.json"), "original_failure": base.pin(base.ROOT / "FAILED01.json"),
        "sources": source, "objects": objects, "compile_receipts": receipts,
        "reused_input_manifest": base.pin(base.ROOT / "metadata/INPUTS01.json"),
        "rsp": base.pin(base.ROOT / "native32-link.rsp"),
        "partial_preimages": [base.pin(path) for path in PARTIALS],
        "partial_bytes_unreadable_after_overwrite": True,
        "overwrite_exactly": [str(path) for path in PARTIALS],
        "DLL_cap": DLL_CAP, "TMP_cap": TMP_CAP, "MAP_cap": 33554432,
        "hard_bytes": base.HARD, "joint_leaf_upper_bytes": 120422400,
        "new_log": "logs/native32-link02.log", "new_receipt": "commands/native32-link02.json",
        "production_result": "PRODUCTION-RESULT01.json", "recompiles": 0,
        "Game_calls": 0, "DLL_loads": 0, "deployment_changes": 0,
    }
    return base.write_json(PLAN, plan, 16384)


def verify_reused(value: object) -> None:
    if not isinstance(value, list):
        raise ValueError("reused input array required")
    base.require(len(value) == 337, "337 reused inputs required")
    for item in value:
        raw = base.object_map(item)
        path = raw.get("path")
        size = raw.get("bytes")
        base.require(type(path) is str and type(size) is int and size >= 0, "invalid reused input")
        if not isinstance(path, str) or not isinstance(size, int):
            raise ValueError("invalid input types")
        numbers: list[int] = []
        for key in ("device", "file_id", "mtime_ns"):
            text = raw.get(key)
            if type(text) is not str or re.fullmatch(r"0|[1-9][0-9]*", text) is None:
                raise ValueError("invalid canonical input identity")
            numbers.append(int(text))
        base.require(base.identity(Path(path)) == (numbers[0], numbers[1], size, numbers[2]), "reused input drift: " + path)


def environment() -> dict[str, str]:
    for key in ("CL", "_CL_", "LINK"):
        base.require(not os.environ.get(key), "ambient tool option")
    env = dict(os.environ)
    temp = base.ROOT / ".msvc-temp"
    env.update(TMP=str(temp), TEMP=str(temp), VSLANG="1033", PYTHONDONTWRITEBYTECODE="1")
    captured = subprocess.run([env.get("COMSPEC", "cmd.exe"), "/d", "/u", "/c", str(temp / "capture-environment.cmd")], cwd=base.ROOT, env=env, capture_output=True, check=True, timeout=60)
    for line in captured.stdout.decode("utf-16-le").splitlines():
        if "=" in line and not line.startswith("="):
            key, item = line.split("=", 1)
            env[key.upper()] = item
    env.update(TMP=str(temp), TEMP=str(temp), VSLANG="1033")
    return env


def execute(card_path: Path, card_sha: str) -> base.FilePin:
    card = base.pin(card_path)
    base.require(card["sha256"] == card_sha, "continuation card pin differs")
    scope = validate_admission(base.read_object(card_path), base.digest(base.ROOT / PLAN), base.digest(Path(__file__)))
    plan = base.read_object(base.ROOT / PLAN)
    base.require(plan.get("sources") == base.source_inputs(), "source identities changed")
    objects, receipts = compiled_inputs()
    base.require(plan.get("objects") == objects and plan.get("compile_receipts") == receipts, "compiled inputs changed")
    base.require(plan.get("partial_preimages") == [base.pin(path) for path in PARTIALS], "partial preimage drift")
    reused = base.read_object(base.ROOT / "metadata/INPUTS01.json").get("reused_inputs")
    verify_reused(reused)
    build = base.recipe()
    rsp = base.ROOT / "native32-link.rsp"
    base.require(plan.get("rsp") == base.pin(rsp), "response file changed")
    log_path = base.ROOT / "logs/native32-link02.log"
    base.require(not log_path.exists() and not (base.ROOT / "PRODUCTION-RESULT01.json").exists(), "continuation already consumed")
    env = environment()
    argv = [str(Path(build.compilation[0].argv[0]).with_name("link.exe")), "/nologo", "@" + str(rsp)]
    start = base.now()
    peak = enforce()
    with log_path.open("xb") as output:
        process = subprocess.Popen(argv, cwd=base.ROOT, env=env, stdout=output, stderr=subprocess.STDOUT)
        try:
            while process.poll() is None:
                peak = max(peak, enforce())
                base.require(datetime.now(timezone.utc) < base.DEADLINE, "review deadline reached")
                time.sleep(0.1)
            rc = process.wait()
        except BaseException:
            process.kill()
            process.wait()
            raise
    command = base.write_json("commands/native32-link02.json", {"command": argv, "start": start, "end": base.now(), "return_code": rc, "log": base.pin(log_path), "sampled_upper_bytes": max(peak, enforce())}, 8192)
    base.require(rc == 0, "link continuation failed")
    base.require(compiled_inputs() == (objects, receipts), "objects/receipts changed during link")
    verify_reused(reused)
    base.require(plan.get("sources") == base.source_inputs(), "source identities changed during link")
    text = (base.ROOT / "bin/xar_ck3_bridge.map").read_bytes().decode("ascii", errors="surrogateescape")
    log = log_path.read_bytes().decode("ascii", errors="surrogateescape")
    base.require(all("native32-" + name + ".obj" in text for name in base.TU_NAMES), "new objects absent from MAP")
    pattern = r"xar_ck3_12002_runtime(?:\.lib)?[:(]ck3_12002_commands"
    base.require(re.search(pattern, text, re.I) is None and re.search(pattern, log, re.I) is None, "old commands member extracted")
    exports, flags = base.pe_exports(PARTIALS[0])
    proof = base.core_link_proof(base.ROOT / "obj/native32-core.obj", PARTIALS[0], text)
    base.require(not list(base.ROOT.rglob("*.pdb")) and not list(base.ROOT.rglob("*.ilk")), "debug output not admitted")
    result = {
        "schema": "xar.native32.offline-production-result/v1", "machine_id": base.MACHINE,
        "observed_at_utc": base.now(), "status": "OFFLINE_ARTIFACT_QUALIFIED_NOT_DEPLOYED",
        "producer": base.pin(Path(base.__file__)), "continuation_producer": base.pin(Path(__file__)),
        "plan": base.pin(base.ROOT / "PLAN03.json"), "continuation_plan": base.pin(base.ROOT / PLAN),
        "execution_card": card, "execution_scope": scope, "original_failure": base.pin(base.ROOT / "FAILED01.json"),
        "original_production_attempt_failed": True, "qualification_mode": "link_only_continuation_after_transient_leaf_cap",
        "partial_preimages": plan["partial_preimages"], "partial_bytes_unreadable_after_overwrite": True,
        "sources": plan["sources"], "objects": objects, "compile_receipts": receipts, "continuation_link_receipt": command,
        "outputs": [base.pin(path) for path in PARTIALS], "exports": [asdict(item) for item in exports],
        "PE_DLL_characteristics": hex(flags), "core_link_proof": proof,
        "original_807_overlay_preserved": True, "all_four_header_consumers_recompiled": True,
        "reused_inputs_before_after_stat_equal": True, "old_commands_archive_member_extracted": False,
        "sampled_upper_before_result_receipt_bytes": enforce(), "hard_bytes": base.HARD,
        "runtime_qualified": False, "Game_calls": 0, "DLL_loads": 0, "deployment_changes": 0,
        "drain_fence": False, "performance_goal_qualified": False, "recompiles_in_continuation": 0,
    }
    ref = base.write_json("PRODUCTION-RESULT01.json", result, 32768)
    enforce()
    return ref


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("plan", "link"))
    parser.add_argument("--admission", type=Path)
    parser.add_argument("--admission-sha256")
    args = parser.parse_args()
    if args.phase == "plan":
        print(json.dumps(make_plan(), sort_keys=True))
        return 0
    base.require(isinstance(args.admission, Path) and isinstance(args.admission_sha256, str), "exact admission pin required")
    try:
        print(json.dumps(execute(args.admission, args.admission_sha256), sort_keys=True))
    except BaseException as error:
        if not (base.ROOT / "FAILED02.json").exists():
            base.write_json("FAILED02.json", {"machine_id": base.MACHINE, "observed_at_utc": base.now(), "error_type": type(error).__name__, "error": str(error), "original_failed01_preserved": True, "production_qualified": False}, 8192)
        raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
