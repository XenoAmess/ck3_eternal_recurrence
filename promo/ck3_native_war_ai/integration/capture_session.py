"""Bounded vanilla map session through the existing managed session and MCP.

Desktop debug recording is opt-in; the default produces timestamped observations,
not footage. Optional raw media is not AI-causality evidence,
an adapter-certified clean span, or a human approval. Existing attempts are kept.
The live branch requires a separate successful run; a no-launch preflight only
checks environment and transport availability, never actual game behavior.
"""
from __future__ import annotations

import argparse
import asyncio
from contextlib import ExitStack, closing
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import runpy
import xml.etree.ElementTree as ET
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time

from recorder_job import RecorderJob, spawn as spawn_recorder
from screen_bus_lease import ScreenLeaseKeeper, checked_cli_pair, renew_once

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))
sys.path.insert(0, str(ROOT / "tools"))
EXACT_SHA = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
BOOKMARK_KEYS = (
    "bookmark_rags_to_riches_duke_robert",
    "bookmark_rags_to_riches_petty_king_murchad",
)
CHECKPOINT_LOAD_NAME = "war_film_checkpoint"
AI_REENTRY_STEP = "query-ai-terminal-reentry-dispatch-v1-16777231-16777218"
AI_REENTRY_CAPABILITY = "game.command.query-ai-terminal-reentry-dispatch-v1-private"


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def identity(path: Path) -> dict:
    with path.open("rb") as source:
        digest = hashlib.file_digest(source, "sha256").hexdigest().upper()
    return {"path": str(path.resolve()), "bytes": path.stat().st_size, "sha256": digest}


A04_UI_SETTINGS_BYTES = 6891
A04_UI_SETTINGS_SHA256 = "E6AD4D44435F17B77C6A5BD6554AB812FBF396D9A27370DB7CF9B56D658FDF7D"
A04_UI_GUI_BLOCK_SHA256 = "F5172E8A9DC92E8998957B5F443575608D04AC44342CE085DF23370CDA26F593"
A04_UI_GUI_BLOCK_START = 6642
A04_UI_GUI_BLOCK_END = 6696
A04_UI_GUI_BLOCK_BYTES = (b'"GUI"={\r\n\t"scale"={\r\n\t\tversion=1\r\n'
                          b'\t\tvalue="1"\r\n\t}\r\n}\r\n')
A04_UI_PRESERVATION_SHA256 = "69F4535E4FDA428E910CBE6F3B44C70E352853535A2D546CB71AA09CEA941779"
A04_UI_HOT_READBACK_SHA256 = "D3F1837AB33FD5541CA2696FF51DD27A114FEACFD332431D2CAC48691D68D337"
A04_UI_IMAGE_IDENTITIES = {
    "graphics-tab-click-a01.png": (3005761, "F02C92BFE223D3BCD24873F61588536B9D3EF055AFCA8AA4B5D74872F82E8363"),
    "scale-dropdown-click-a01.png": (2984451, "6DA98F13104402525BEBFE678839F143F16E17F4981B30145F2DC5EC07EB365E"),
    "scale-100-select-a01.png": (3070090, "5BFDC23C7A598678768BDCADA550765DC468D1DA90337B29C8D0A7E0125C046F"),
    "scale-save-close-a01.png": (3610940, "BEB4268D0E3C4915BD05C0CADDD64C77E0A789339ABD65DA535F6E926909A793"),
    "ui-after-save-a01.png": (4050867, "CE2620160563D24B0569FEDA0C0CA3E39DC7C85AB89D11474061FDE217CD596B"),
}

# Project-specific admission for importing the reviewed a04 SaveAndClose GUI
# block.  An identical checkpoint copied to a different attempt is not an
# authority to turn on the native literal-"1" parser gate for another track.
A04_UI_TARGETS = {
    "e2-04-d05": {
        "save": ("episode01-paired-counter-trace-attempt-010/d05-immutable.ck3", 52172645,
                 "695F1FDE17457004EB8D060C1F21146C3605374806DABACF6FB5FAB386882885"),
        "receipt": ("episode01-paired-counter-trace-attempt-010/ck3-output/interactive-requests-responses/d05-save.json",
                    13437, "6650C0DB79D063E066AB72402735C22FAE9FCB5D458A56CE1C10B9545CD1F3C7"),
        "actor": 29829, "date_raw": 53146344,
        "source_episode_run_id": "native-29829-78c0d8f4b8a2",
        "attempt_prefix": "episode02-e2-04-d05-",
    },
    "e2-04-d06": {
        "save": ("episode02-e2-04-d05-live-20260929-a08/e2-04-d06-postframe-preservation-a01/d06-immutable.ck3",
                 52185337, "F05A48A0839E76DD05D053FACBA524405FD547DD0A6CA07396ADB8ABE42A0B5A"),
        "receipt": ("episode02-e2-04-d05-live-20260929-a08/ck3-output/interactive-requests-responses/e2-04-d05-postframe-save.json",
                    13437, "85C226E247AF4D32E246DCCF9F4C7323106D3A6BD0F12FCB883ABE843D3B785B"),
        "actor": 29829, "date_raw": 53146368,
        "source_episode_run_id": "native-29829-0a9929135691",
        "attempt_prefix": "episode02-e2-04-d06-",
    },
    "e2-05-d26": {
        "save": ("episode01-paired-counter-trace-attempt-010/d26-immutable.ck3", 52880496,
                 "C1276153435766A875B0984F1A3AD426CB3AFCFB6EC33061CEE6650538CFFD2B"),
        "receipt": ("episode01-paired-counter-trace-attempt-010/ck3-output/interactive-requests-responses/d26-save.json",
                    13452, "78931511D31E8400334D28DAD276F4CCDFBB342A901FC00B0BAFDCDEDA29584C"),
        "actor": 29829, "date_raw": 53146848,
        "source_episode_run_id": "native-29829-78c0d8f4b8a2",
        "attempt_prefix": "episode02-e2-05-d26-",
    },
    "e2-06-d11": {
        "save": ("episode01-full-edge-attempt-004/trace-d11-immutable.ck3", 52408560,
                 "3F4B2FDAAE1AA2ED4D94958673DDADF4DCDF4A4F49073594B9AE32E782BB6953"),
        "receipt": ("episode01-full-edge-attempt-004/ck3-output/interactive-requests-responses/trace-d11-save.json",
                    13397, "DD986180C7E9C4B42D43FC634884F5294387D18CF8F798012FAD621B37E9E4A5"),
        "actor": 29829, "date_raw": 53146488,
        "source_episode_run_id": "native-29829-7ea6523df43e",
        "attempt_prefix": "episode02-e2-06-d11-",
    },
}
A04_UI_SOURCE_ROOT = Path("D:/workspace/ck3_native_war_ai_promo_work")
BATTLE_CONTROL_PAIR_SCHEMA = "xar.promo.battle-control-pair/v1"
BATTLE_CONTROL_WIRE_MARKERS = (
    b"side_0_selected_commander_next_roll_bounds",
    b"side_1_selected_commander_next_roll_bounds",
    b"battle_side_mapping",
)
PRIVATE_PHASE_TRACE_CMAKE_OPTION = "XAR_CK3_ENABLE_EXPERIMENTAL_COMBAT_PHASE_TRACE_MANAGED_V1"
PRIVATE_PHASE_TRACE_WIRE_MARKERS = (
    b"experimental-combat-phase-event-trace-begin-v1",
    b"experimental-combat-phase-event-trace-finish-v1",
    b"capture_runtime_counter_output",
    b"capture_runtime_advantage_components",
    b"native_cache_0x2308d50_original_calls",
)


def write_new(path: Path, value: object) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as target:
        json.dump(value, target, ensure_ascii=False, indent=2)
        target.write("\n")


def append(path: Path, value: object) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as target:
        target.write(json.dumps(value, ensure_ascii=False) + "\n")
        target.flush()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def validate_d11_battle_control_pair(
    checkpoint: dict | None, manifest_path: Path | None,
    dll_path: Path, injector_path: Path,
) -> dict | None:
    """Reject an unpaired d11 DLL before CK3 is launched.

    Static wire markers reject the known R0107 legacy producer. The immutable
    build/test report and exact source hashes are still independently reviewed;
    this gate does not turn a static check into a native query result.
    """
    d11_sha = A04_UI_TARGETS["e2-06-d11"]["save"][2]
    is_d11 = checkpoint is not None and checkpoint["save"]["sha256"] == d11_sha
    if not is_d11:
        require(manifest_path is None,
                "Battle-control pair manifest is only for the exact d11 checkpoint")
        return None
    require(manifest_path is not None and manifest_path.is_file(),
            "D11 battle-control pair manifest is required before launch")
    pair = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_keys = {
        "schema", "build_status", "build_report", "source_fingerprint_sha256",
        "native_serializer_sha256", "python_contract_sha256", "dll_sha256",
        "injector_sha256", "battle_control_ctest_passed",
    }
    require(isinstance(pair, dict) and set(pair) == expected_keys and
            pair["schema"] == BATTLE_CONTROL_PAIR_SCHEMA and
            pair["build_status"] == "READY" and
            pair["battle_control_ctest_passed"] is True,
            "D11 battle-control pair manifest is incomplete or untested")
    report_ref = pair["build_report"]
    require(isinstance(report_ref, dict) and set(report_ref) == {"path", "sha256"} and
            isinstance(report_ref["path"], str) and isinstance(report_ref["sha256"], str),
            "D11 battle-control build report reference is malformed")
    report_path = Path(report_ref["path"])
    require(report_path.is_absolute() and report_path.is_file() and
            identity(report_path)["sha256"] == report_ref["sha256"],
            "D11 battle-control build report bytes changed")
    checkout = Path(__file__).resolve().parents[3]
    native_root = checkout / "ck3_autonomous_player" / "native_bridge"
    serializer = native_root / "src" / "battle_control_snapshot_v1_mailbox.cpp"
    helper = native_root / "tools" / "build_fresh.py"
    fingerprint = runpy.run_path(str(helper))[
        "native_bridge_source_fingerprint"
    ](native_root)
    from xar_autoplayer.bridge import battle_control_contract
    contract = Path(battle_control_contract.__file__).resolve()
    expected_contract = (checkout / "ck3_autonomous_player" / "src" /
                         "xar_autoplayer" / "bridge" / "battle_control_contract.py").resolve()
    require(contract == expected_contract,
            "D11 battle-control Python contract loaded from another checkout")
    expected = {
        "source_fingerprint_sha256": fingerprint,
        "native_serializer_sha256": identity(serializer)["sha256"],
        "python_contract_sha256": identity(contract)["sha256"],
        "dll_sha256": identity(dll_path)["sha256"],
        "injector_sha256": identity(injector_path)["sha256"],
    }
    require(all(pair[key] == value for key, value in expected.items()),
            "D11 battle-control native/Python source pair differs from the exact build")
    build = json.loads(report_path.read_text(encoding="utf-8"))
    required_build_keys = {
        "status", "build_status", "head", "build_dir", "configuration",
        "source_fingerprint_sha256", "native_serializer_sha256",
        "python_contracts_sha256", "dll", "injector", "dll_sha256",
        "injector_sha256", "tests_ran", "test_scope", "dependency_gate",
        "dependency_receipt_path", "dependency_receipt_sha256",
        "source_before_path", "source_before_sha256", "source_after_path",
        "source_after_sha256", "configure_argv_path", "configure_argv_sha256",
        "configure_result_path", "configure_result_sha256", "build_argv_path",
        "build_argv_sha256", "build_result_path", "build_result_sha256",
        "ctest_name", "ctest_argv_path", "ctest_argv_sha256",
        "ctest_result_path", "ctest_result_sha256", "ctest_stdout_path",
        "ctest_stdout_sha256", "ctest_junit_path", "ctest_junit_sha256",
        "build_script_sha256", "cmake_cache_path", "cmake_cache_sha256", "tests",
    }
    require(isinstance(build, dict) and required_build_keys <= set(build),
            "D11 focused build report lacks required provenance")
    build_dir = Path(build["build_dir"])
    build_script = report_path.parent / "build_release_candidate.py"
    cmake_cache = Path(build["cmake_cache_path"])
    require(build["status"] == "STATIC_RELEASE_CANDIDATE_NO_CK3_LAUNCH" and
            build["build_status"] == "READY" and
            build["configuration"] == "Release" and
            build["tests_ran"] is True and
            build["test_scope"] == "current-battle-knight-mailbox-and-python-port" and
            build["dependency_gate"] == "ck3_11906.hpp-recorded" and
            build_dir.is_absolute() and build_dir.resolve() == dll_path.resolve().parent and
            build_dir.resolve() == injector_path.resolve().parent and
            build_script.is_file() and
            identity(build_script)["sha256"] == build["build_script_sha256"] and
            cmake_cache.is_file() and cmake_cache.resolve() ==
            (build_dir / "CMakeCache.txt").resolve() and
            identity(cmake_cache)["sha256"] == build["cmake_cache_sha256"] and
            "CMAKE_BUILD_TYPE:STRING=Release" in
            cmake_cache.read_text(encoding="utf-8", errors="replace").splitlines() and
            f"{PRIVATE_PHASE_TRACE_CMAKE_OPTION}:BOOL=ON" in
            cmake_cache.read_text(encoding="utf-8", errors="replace").splitlines(),
            "D11 focused build status or directory is not admissible")
    require(build["source_fingerprint_sha256"] == fingerprint and
            build["native_serializer_sha256"] == expected["native_serializer_sha256"] and
            isinstance(build["python_contracts_sha256"], dict) and
            build["python_contracts_sha256"].get("battle_control_contract.py") ==
            expected["python_contract_sha256"],
            "D11 focused build source fingerprint differs")
    for name, path, digest in (
        ("dll", dll_path, expected["dll_sha256"]),
        ("injector", injector_path, expected["injector_sha256"]),
    ):
        artifact = build[name]
        require(isinstance(artifact, dict) and
                artifact.get("path") == str(path.resolve()) and
                artifact.get("bytes") == path.stat().st_size and
                artifact.get("sha256") == digest and
                build[f"{name}_sha256"] == digest,
                f"D11 focused build {name} artifact differs from loaded bytes")

    def bound(name: str) -> Path:
        path = Path(build[f"{name}_path"])
        require(path.is_absolute() and path.is_file() and
                identity(path)["sha256"] == build[f"{name}_sha256"],
                f"D11 focused build {name} receipt bytes changed")
        return path

    dependency = json.loads(bound("dependency_receipt").read_text(encoding="utf-8"))
    dependency_objects = runpy.run_path(str(helper))["DEPENDENCY_OBJECTS"]
    rows = dependency.get("objects")
    require(dependency.get("schema") == "xar.promo.e204-native-dependency/v1" and
            dependency.get("source_fingerprint_sha256") == fingerprint and
            isinstance(rows, list) and len(rows) == len(dependency_objects) and
            {row.get("object") for row in rows if isinstance(row, dict)} ==
            set(dependency_objects),
            "D11 focused native dependency receipt differs from source")
    for row in rows:
        def dependency_bound(kind: str) -> Path:
            path = Path(row[f"{kind}_path"])
            require(path.is_absolute() and path.is_file() and
                    identity(path)["sha256"] == row[f"{kind}_sha256"],
                    f"D11 focused dependency {kind} bytes changed")
            return path

        argv = json.loads(dependency_bound("argv").read_text(encoding="utf-8"))["argv"]
        result = json.loads(dependency_bound("result").read_text(encoding="utf-8"))
        stdout = dependency_bound("stdout").read_text(encoding="utf-8", errors="replace")
        dependency_bound("stderr")
        require(isinstance(argv, list) and len(argv) == 6 and
                Path(argv[argv.index("-C") + 1]).resolve() == build_dir.resolve() and
                argv[argv.index("-t") + 1] == "deps" and
                argv[-1] == row["object"] and
                result.get("exit_code") == 0 and
                re.search(r"#deps\s+[1-9][0-9]*", stdout) is not None and
                "ck3_11906.hpp" in stdout and
                row.get("ck3_11906_header_recorded") is True and
                row.get("positive_dependency_count") is True,
                "D11 focused Ninja dependency evidence is not valid")

    source_evidence = {}
    for name in ("source_before", "source_after"):
        source = json.loads(bound(name).read_text(encoding="utf-8"))
        require(source.get("source_fingerprint_sha256") == fingerprint and
                source.get("native_bridge_fingerprint_sha256") == fingerprint and
                (source.get("build_fresh_helper") or {}).get("sha256") ==
                identity(helper)["sha256"] and source.get("head") == build["head"] and
                source.get("build_script_sha256") == build["build_script_sha256"] and
                source.get("configuration") == "Release",
                f"D11 focused build {name} source changed")
        source_evidence[name] = source
    require(source_evidence["source_after"].get("tracked_status") == "",
            "D11 focused builder checkout has tracked source changes")
    configure_argv = json.loads(bound("configure_argv").read_text(encoding="utf-8"))["argv"]
    configure_result = json.loads(bound("configure_result").read_text(encoding="utf-8"))
    build_argv = json.loads(bound("build_argv").read_text(encoding="utf-8"))["argv"]
    build_result = json.loads(bound("build_result").read_text(encoding="utf-8"))
    require(isinstance(configure_argv, list) and
            "-S" in configure_argv and "-B" in configure_argv and
            Path(configure_argv[configure_argv.index("-S") + 1]).name == "native_bridge" and
            Path(configure_argv[configure_argv.index("-B") + 1]).resolve() ==
            build_dir.resolve() and
            "-DCMAKE_BUILD_TYPE=Release" in configure_argv and
            f"-D{PRIVATE_PHASE_TRACE_CMAKE_OPTION}=ON" in configure_argv and
            configure_result.get("exit_code") == 0,
            "D11 focused configure did not use the current Release source")
    builder_root = Path(configure_argv[configure_argv.index("-S") + 1]).resolve()
    builder_head = subprocess.run(
        ["git", "-C", str(builder_root), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    require(builder_root.is_dir() and
            builder_head == build["head"] and
            runpy.run_path(str(helper))["native_bridge_source_fingerprint"](builder_root) ==
            fingerprint and
            all(Path(source_evidence[name]["build_fresh_helper"]["path"]).resolve() ==
                builder_root / "tools" / "build_fresh.py"
                for name in ("source_before", "source_after")),
            "D11 focused builder source changed after compilation")
    require(isinstance(build_argv, list) and
            str(build_dir.resolve()) in build_argv and
            all(target in build_argv for target in (
                "xar_ck3_bridge", "xar_ck3_bridge_injector",
                "xar_ck3_battle_control_snapshot_v1_mailbox_test")) and
            build_result.get("exit_code") == 0,
            "D11 focused build did not complete the required targets")

    ctest_name = "xar_ck3_native_bridge_battle_control_snapshot_v1_mailbox"
    ctest_argv = json.loads(bound("ctest_argv").read_text(encoding="utf-8"))["argv"]
    ctest_result_path = bound("ctest_result")
    ctest_result = json.loads(ctest_result_path.read_text(encoding="utf-8"))
    ctest_stdout = bound("ctest_stdout").read_text(encoding="utf-8", errors="replace")
    ctest_junit_path = bound("ctest_junit")
    require(build["ctest_name"] == ctest_name and
            isinstance(ctest_argv, list) and "--output-on-failure" in ctest_argv and
            "--test-dir" in ctest_argv and
            Path(ctest_argv[ctest_argv.index("--test-dir") + 1]).resolve() ==
            build_dir.resolve() and
            "-R" in ctest_argv and
            ctest_argv[ctest_argv.index("-R") + 1] == f"^{ctest_name}$" and
            "--output-junit" in ctest_argv and
            Path(ctest_argv[ctest_argv.index("--output-junit") + 1]).resolve() ==
            ctest_junit_path.resolve() and
            ctest_result.get("exit_code") == 0 and
            ctest_result.get("returncode") == 0 and
            ctest_name in ctest_stdout and "100% tests passed" in ctest_stdout,
            "D11 focused battle-control CTest command or result is not GREEN")
    junit = ET.parse(ctest_junit_path).getroot()
    cases = junit.findall(".//testcase")
    if junit.tag == "testsuite":
        cases = junit.findall("testcase")
    require(len(cases) == 1 and cases[0].get("name") == ctest_name and
            all(not cases[0].findall(tag) for tag in ("failure", "error", "skipped")) and
            junit.get("tests") == "1" and junit.get("failures") == "0" and
            junit.get("errors", "0") == "0" and junit.get("skipped", "0") == "0",
            "D11 focused battle-control JUnit testcase is not passing")
    tests = build["tests"]
    require(isinstance(tests, dict) and
            {"ctest", "python-normal", "python-optimized"} <= set(tests) and
            tests["ctest"] == {"result_path": str(ctest_result_path),
                               "result_sha256": identity(ctest_result_path)["sha256"]},
            "D11 focused test receipt map differs")
    for name in ("python-normal", "python-optimized"):
        row = tests[name]
        require(isinstance(row, dict) and set(row) == {"result_path", "result_sha256"},
                f"D11 focused {name} receipt reference is malformed")
        result_path = Path(row["result_path"])
        require(result_path.is_absolute() and result_path.is_file() and
                identity(result_path)["sha256"] == row["result_sha256"] and
                json.loads(result_path.read_text(encoding="utf-8")).get("exit_code") == 0,
                f"D11 focused {name} tests are not GREEN")
    dll = dll_path.read_bytes()
    require(dll.startswith(b"MZ") and
            all(marker in dll for marker in BATTLE_CONTROL_WIRE_MARKERS) and
            all(marker in dll for marker in PRIVATE_PHASE_TRACE_WIRE_MARKERS),
            "D11 DLL lacks current battle-control or managed phase-trace wire fields")
    return {"manifest": identity(manifest_path), "build_report": identity(report_path),
            "source_fingerprint_sha256": fingerprint,
            "python_contract_sha256": expected["python_contract_sha256"],
            "wire_markers_present": True,
            "private_phase_trace_static_ready": True,
            "native_query_verified": False}


def private_ai_reentry_readback(request: dict, *, driver) -> dict:
    """Use the existing owner connection for one exact read-only paused query."""
    require(set(request) == {"action", "step", "expected_revision"},
            "Private AI reentry request fields differ from the fixed contract")
    require(request["action"] == "private_ai_terminal_reentry"
            and request["step"] == AI_REENTRY_STEP,
            "Only the fixed AI winner reentry readback is permitted")
    revision = request["expected_revision"]
    require(type(revision) is int and revision > 0,
            "Private AI reentry needs a positive public revision")
    snapshot = driver.take_snapshot()
    require(snapshot.get("paused") is True and snapshot.get("revision") == revision,
            "Private AI reentry needs a stable paused snapshot at the requested revision")
    capabilities = driver.capabilities()
    require(AI_REENTRY_CAPABILITY in capabilities.get("bridge_capabilities", []),
            "Private AI reentry DLL capability is not advertised")
    result = driver._execute_primitive_step(
        AI_REENTRY_STEP, expected_revision=revision,
        required_capability=AI_REENTRY_CAPABILITY, timeout_seconds=90,
    )
    require(result.get("step") == AI_REENTRY_STEP
            and result.get("accepted") is True
            and result.get("schema_version") == 1
            and isinstance(result.get("observer"), dict),
            "Private AI reentry readback result is malformed")
    return result


def checkpoint_source(save: Path | None, receipt_path: Path | None) -> dict | None:
    """Read the actual saved checkpoint receipt; never manufacture driver history."""
    require((save is None) == (receipt_path is None), "Checkpoint save and receipt must be supplied together")
    if save is None:
        return None
    require(save.is_file() and save.suffix.lower() == ".ck3", "Checkpoint must be an existing .ck3 file")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8-sig"))
    require(receipt.get("result") == "CALL_COMPLETED", "Checkpoint MCP call did not complete")
    body = receipt.get("body") or {}
    saved = body.get("checkpoint") or {}
    require(body.get("step") == "save-checkpoint" and body.get("accepted") is True
            and saved.get("status") == "saved", "Receipt does not attest a materialized native checkpoint")
    actual = identity(save)
    require(actual["bytes"] == saved.get("size") and actual["sha256"].lower() == str(saved.get("sha256")).lower(),
            "Checkpoint bytes differ from native save receipt")
    lifecycle = saved.get("succession_lifecycle") or {}
    require(lifecycle.get("lifecycle") == "ordinary_campaign_succession"
            and lifecycle.get("xar_enabled") == "xar_off"
            and lifecycle.get("pact_contract") == "absent_by_fresh_campaign_xar_off_contract"
            and lifecycle.get("source") == "pure-vanilla-enabled-mods-empty",
            "Checkpoint is not from this producer's pure-vanilla ordinary campaign")
    hello = (receipt.get("driver_state") or {}).get("hello") or {}
    require(hello.get("ck3_build_match") is True and
            str(hello.get("expected_ck3_sha256", "")).upper() == EXACT_SHA,
            "Checkpoint receipt lacks matching exact-build native hello")
    actor, date = saved.get("episode_character_id"), saved.get("date_raw")
    require(type(actor) is int and actor > 0 and type(date) is int,
            "Checkpoint receipt lacks actual saved actor/date")
    return {"save": actual, "receipt": identity(receipt_path), "actor": actor, "date_raw": date,
            "source_episode_run_id": saved.get("episode_run_id"), "source_lifecycle": lifecycle,
            "exact_build_hello": hello, "load_save_name": CHECKPOINT_LOAD_NAME,
            "driver_history_copied": False, "managed_load_path": "frontend_first_load_save_name"}


def copy_checkpoint(source: dict, profile_dir: Path, output_dir: Path) -> dict:
    """Preserve source receipt and copy only exact save bytes into the new profile."""
    target = profile_dir / "save games" / f"{CHECKPOINT_LOAD_NAME}.ck3"
    require(not target.exists(), "Checkpoint destination must be new")
    with Path(source["save"]["path"]).open("rb") as src, target.open("xb") as dst:
        shutil.copyfileobj(src, dst)
    copied = identity(target)
    require((copied["bytes"], copied["sha256"]) == (source["save"]["bytes"], source["save"]["sha256"]),
            "Checkpoint copy differs from frozen native receipt")
    receipt_copy = output_dir / "checkpoint-source-receipt.json"
    with Path(source["receipt"]["path"]).open("rb") as src, receipt_copy.open("xb") as dst:
        shutil.copyfileobj(src, dst)
    copied_receipt = identity(receipt_copy)
    require((copied_receipt["bytes"], copied_receipt["sha256"]) ==
            (source["receipt"]["bytes"], source["receipt"]["sha256"]), "Checkpoint receipt changed")
    record = {"source": source, "profile_copy": copied, "receipt_copy": copied_receipt,
              "old_attempt_modified": False, "driver_history_created": False}
    write_new(output_dir / "checkpoint-copy.json", record)
    return record


async def wait_checkpoint_map(*, call, source: dict, stopped: threading.Event,
                              timeout_seconds: float, stable_seconds: float = 1.0,
                              poll_interval_seconds: float = 1.0) -> dict:
    """Observe the existing loader's result; no New Game, native load, or restore command."""
    deadline = time.monotonic() + timeout_seconds
    stable_key = None
    stable_since = None
    baseline_pump = None
    last_reason = "native map has not been published"
    while time.monotonic() < deadline and not stopped.is_set():
        snapshot = await call("ck3_take_snapshot", tolerate=True)
        played = snapshot.get("played_character") or {}
        actor, date = played.get("character_id"), snapshot.get("date_raw")
        complete_identity = (snapshot.get("map_ready") is True and type(actor) is int
                             and actor > 0 and type(date) is int and date > 0)
        if complete_identity:
            require(actor == source["actor"] and date == source["date_raw"],
                    "Loaded checkpoint actor/date differs from saved native receipt")
        if complete_identity and snapshot.get("paused") is True:
            diagnostics = snapshot.get("diagnostics") or {}
            hello = diagnostics.get("hello") or {}
            require(hello.get("ck3_build_match") is True and
                    str(hello.get("expected_ck3_sha256", "")).upper() == EXACT_SHA,
                    "Loaded checkpoint native build readback differs")
            mailbox = (diagnostics.get("last_heartbeat") or {}).get("main_thread_query_mailbox_v1") or {}
            pump = mailbox.get("pump_epochs")
            key = (diagnostics.get("bridge_pid"), diagnostics.get("connection_generation"), actor, date,
                   snapshot.get("snapshot_id"), snapshot.get("revision"), snapshot.get("native_revision"))
            now = time.monotonic()
            if key != stable_key or baseline_pump is None:
                stable_key, stable_since = key, now
                baseline_pump = pump if type(pump) is int and pump >= 0 else None
            elif (type(pump) is int and pump > baseline_pump and mailbox.get("ready") is True
                  and stable_since is not None and now - stable_since >= stable_seconds):
                return snapshot
            last_reason = "valid paused identity awaits stability and a later application-main pump"
        else:
            stable_key = stable_since = baseline_pump = None
            last_reason = "map/paused state or played-character/date publication is still incomplete"
        await asyncio.sleep(poll_interval_seconds)
    raise RuntimeError("Loaded checkpoint did not produce a verified stable paused map within the bounded wait: " + last_reason)


def session_outcome(*, session_ok: bool, debug_recording_enabled: bool, recording_ok: bool) -> str:
    if not session_ok or (debug_recording_enabled and not recording_ok):
        return "RED"
    return ("RAW_CAPTURE_COMPLETE_PENDING_VISUAL_REVIEW" if debug_recording_enabled
            else "ENVIRONMENT_SESSION_COMPLETE_NO_VIDEO")


def prioritize_supervisor_failure(worker: dict, supervisor_error: str) -> None:
    """Keep the map observer error, but report the failed native session first."""
    observer_error = worker.get("error")
    if observer_error is not None and observer_error != supervisor_error:
        worker["observer_error"] = observer_error
    worker["error"] = supervisor_error


def record_observer_failure(worker: dict, observer_error: str, *, supervisor_error: str | None) -> None:
    """A late observer exit must not overwrite the native session failure."""
    worker["observer_error" if supervisor_error is not None else "error"] = observer_error


def private_phase_trace_call(request: dict, *, enabled: bool, driver) -> dict:
    """Forward only the bounded private trace fields to the native driver."""
    require(enabled, "Private phase trace requires explicit capture opt-in")
    step = request.get("step")
    require(step in {
        "experimental-combat-phase-event-trace-begin-v1",
        "experimental-combat-phase-event-trace-finish-v1",
    }, "Only the bounded phase trace command pair is permitted")
    expected_revision = request.get("expected_revision")
    combat_id = request.get("combat_id")
    token = request.get("managed_daily_sequence_token")
    require(type(expected_revision) is int and expected_revision > 0,
            "Private phase trace needs a positive revision")
    require(type(combat_id) is int and combat_id > 0,
            "Private phase trace needs a positive CombatID")
    require(type(token) is int and token > 0,
            "Private phase trace needs a positive sequence token")
    fields = {"combat_id": combat_id,
              "managed_daily_sequence_token": token}
    allowed = {"action", "step", "expected_revision",
               "combat_id", "managed_daily_sequence_token"}
    if step.endswith("-begin-v1"):
        checkpoint_sequence = request.get("checkpoint_sequence")
        require(type(checkpoint_sequence) is int and checkpoint_sequence > 0,
                "Begin requires a materialized checkpoint sequence")
        fields["checkpoint_sequence"] = checkpoint_sequence
        allowed.add("checkpoint_sequence")
        if "candidate_joining_army_id" in request:
            candidate_id = request["candidate_joining_army_id"]
            require(type(candidate_id) is int and 0 < candidate_id < 2**31,
                    "Candidate joiner needs a positive full ArmyID")
            fields["candidate_joining_army_id"] = candidate_id
            allowed.add("candidate_joining_army_id")
        if "capture_runtime_random_list_weights" in request:
            capture_weights = request["capture_runtime_random_list_weights"]
            require(type(capture_weights) is bool,
                    "Runtime random-list weight capture flag must be bool")
            fields["capture_runtime_random_list_weights"] = capture_weights
            allowed.add("capture_runtime_random_list_weights")
        if "capture_runtime_join_width" in request:
            capture_join_width = request["capture_runtime_join_width"]
            require(type(capture_join_width) is bool,
                    "Runtime join-width capture flag must be bool")
            require("candidate_joining_army_id" in request,
                    "Join-width capture needs a frozen candidate ArmyID")
            fields["capture_runtime_join_width"] = capture_join_width
            allowed.add("capture_runtime_join_width")
        if "capture_runtime_join_full_entries" in request:
            capture_full_entries = request["capture_runtime_join_full_entries"]
            require(type(capture_full_entries) is bool,
                    "Runtime join full-entry capture flag must be bool")
            require(not capture_full_entries or
                    fields.get("capture_runtime_join_width") is True,
                    "Join full-entry capture needs enabled join-width capture")
            fields["capture_runtime_join_full_entries"] = capture_full_entries
            allowed.add("capture_runtime_join_full_entries")
        if "capture_runtime_counter_output" in request:
            capture_counter_output = request["capture_runtime_counter_output"]
            require(type(capture_counter_output) is bool,
                    "Runtime counter-output capture flag must be bool")
            fields["capture_runtime_counter_output"] = capture_counter_output
            allowed.add("capture_runtime_counter_output")
        if "capture_runtime_advantage_components" in request:
            capture_advantage = request["capture_runtime_advantage_components"]
            require(type(capture_advantage) is bool,
                    "Runtime advantage-component capture flag must be bool")
            fields["capture_runtime_advantage_components"] = capture_advantage
            allowed.add("capture_runtime_advantage_components")
    require(set(request) == allowed,
            "Private phase trace request fields differ from the bounded contract")
    return driver._execute_primitive_step(
        step, expected_revision=expected_revision,
        required_capability="game.command.experimental-combat-phase-event-trace-managed-v1",
        request_fields=fields, timeout_seconds=90,
    )


async def service_requests(directory: Path, *, call, stopped: threading.Event,
                           seconds: float, state_reader, private_phase_call=None,
                           private_ai_reentry_call=None, gui_scale_readback=None) -> None:
    """Keep the one owning MCP connection available for bounded hot diagnosis.

    Requests are explicit local JSON files, never inferred retries of StartGame.
    Each request and response is preserved. A failed initial attempt remains RED.
    """
    directory.mkdir(exist_ok=False)
    responses = directory.parent / (directory.name + "-responses")
    responses.mkdir(exist_ok=False)
    deadline = time.monotonic() + seconds
    write_new(responses / "service.json", {
        "started_at": utc(), "timeout_seconds": seconds,
        "request_schema": {"action": "mcp", "tool": "ck3_take_snapshot", "arguments": {}},
        "finish_schema": {"action": "finish"},
        "same_driver_connection": True, "automatic_mutating_retry": False,
    })
    processed: set[str] = set()
    while time.monotonic() < deadline and not stopped.is_set():
        for source in sorted(directory.glob("*.json")):
            if source.name in processed:
                continue
            # Writers must atomically rename a completed request into this folder.
            processed.add(source.name)
            row = {"request": identity(source), "at": utc(), "result": "RED"}
            finish = False
            try:
                request = json.loads(source.read_text(encoding="utf-8"))
                require(isinstance(request, dict), "Request must be an object")
                if request.get("action") == "finish":
                    row["result"] = "SERVICE_FINISHED"
                    finish = True
                elif request.get("action") == "private_phase_trace":
                    require(private_phase_call is not None,
                            "Private phase trace is not enabled for this capture")
                    row["body"] = private_phase_call(request)
                    row["result"] = "CALL_COMPLETED"
                elif request.get("action") == "private_ai_terminal_reentry":
                    require(private_ai_reentry_call is not None,
                            "Private AI reentry is not enabled for this capture")
                    row["body"] = private_ai_reentry_call(request)
                    row["result"] = "CALL_COMPLETED"
                elif request.get("action") == "gui_scale_disk_readback":
                    require(set(request) == {"action"}, "GUI scale readback takes no arguments")
                    require(gui_scale_readback is not None,
                            "GUI scale readback requires an explicit --gui-scale capture")
                    row["body"] = gui_scale_readback()
                    row["result"] = ("DISK_MATCH_REQUIRES_VISUAL_REVIEW"
                                     if row["body"]["disk_gate_passed"] else "RED")
                else:
                    require(request.get("action") == "mcp", "Unknown request action")
                    name = request.get("tool")
                    require(isinstance(name, str) and name.startswith("ck3_"), "Explicit MCP tool required")
                    row["body"] = await call(name, request.get("arguments") or {})
                    row["result"] = "CALL_COMPLETED"
            except Exception as error:
                row["error"] = repr(error)
            try:
                row["driver_state"] = state_reader()
            except Exception as error:
                row["state_error"] = repr(error)
            write_new(responses / source.name, row)
            if finish:
                return
        await asyncio.sleep(0.25)
    write_new(responses / "service-ended.json", {
        "at": utc(), "reason": "owner_stopped" if stopped.is_set() else "bounded_timeout",
    })


def bind_a04_ui_target(args: argparse.Namespace, checkpoint: dict) -> dict:
    """Bind one exact checkpoint pair to this attempt's actual isolated userdir."""
    require(isinstance(checkpoint, dict), "A04 UI import needs a verified checkpoint source")
    save = checkpoint.get("save") or {}
    receipt = checkpoint.get("receipt") or {}
    matched = []
    for track, spec in A04_UI_TARGETS.items():
        expected_save = A04_UI_SOURCE_ROOT / spec["save"][0]
        expected_receipt = A04_UI_SOURCE_ROOT / spec["receipt"][0]
        if (str(Path(save.get("path", "")).resolve()).casefold() ==
                str(expected_save.resolve()).casefold() and
                (save.get("bytes"), save.get("sha256")) == spec["save"][1:] and
                str(Path(receipt.get("path", "")).resolve()).casefold() ==
                str(expected_receipt.resolve()).casefold() and
                (receipt.get("bytes"), receipt.get("sha256")) == spec["receipt"][1:] and
                checkpoint.get("actor") == spec["actor"] and
                checkpoint.get("date_raw") == spec["date_raw"] and
                checkpoint.get("source_episode_run_id") == spec["source_episode_run_id"]):
            matched.append(track)
    require(len(matched) == 1,
            "A04 UI import checkpoint is not an exact allowed track/source pair")
    track = matched[0]
    state_arg = getattr(args, "state_dir", None)
    output_arg = getattr(args, "output_dir", None)
    require(isinstance(state_arg, Path) and isinstance(output_arg, Path),
            "A04 UI import needs actual state/output directories")
    state = state_arg.resolve()
    output = output_arg.resolve()
    root = state.parent
    require(state.name == "ck3-state" and output.name == "ck3-output" and
            output.parent == root and root.parent == A04_UI_SOURCE_ROOT.resolve() and
            root.name.startswith(A04_UI_TARGETS[track]["attempt_prefix"]) and
            all(not path.is_symlink() for path in (root, *root.parents, state, output)),
            "A04 UI import userdir/state/output does not match the source track")
    return {"track": track, "source_checkpoint": checkpoint,
            "state_dir": str(state), "output_dir": str(output),
            "userdir": str(state / "profile")}


def validate_a04_ui_gui_source_binding(args: argparse.Namespace,
                                       checkpoint: dict | None = None) -> dict | None:
    """Bind reviewed a04 UI bytes to one exact track and new session userdir.

    This only admits project-frozen disk bytes; runtime geometry still needs a
    fresh game readback and original image review.
    """
    enabled = getattr(args, "import_a04_ui_gui_100", False)
    snapshot_path = getattr(args, "a04_ui_settings_snapshot", None)
    preservation_path = getattr(args, "a04_ui_preservation_receipt", None)
    require(type(enabled) is bool, "A04 UI import opt-in must be boolean")
    if not enabled:
        require(snapshot_path is None and preservation_path is None,
                "A04 UI source paths require --import-a04-ui-gui-100")
        return None
    require(getattr(args, "gui_scale", None) == "1.0",
            "A04 UI import requires explicit --gui-scale 1.0")
    require(getattr(args, "checkpoint_save", None) is not None and
            getattr(args, "checkpoint_receipt", None) is not None,
            "A04 UI import requires a source-bound checkpoint pair")
    require(not getattr(args, "record_debug_desktop", False),
            "A04 UI import cannot start a debug recorder before visual review")
    require(isinstance(snapshot_path, Path) and isinstance(preservation_path, Path),
            "A04 UI import needs both frozen source and preservation receipt paths")
    target = bind_a04_ui_target(
        args, checkpoint if checkpoint is not None else
        checkpoint_source(args.checkpoint_save, args.checkpoint_receipt))
    for path in (snapshot_path, preservation_path):
        require(all(not part.is_symlink() for part in (path, *path.parents)),
                "A04 UI evidence paths must not contain symlinks")
        require(path.is_file(), "A04 UI evidence file is missing")
    source = identity(snapshot_path)
    require((source["bytes"], source["sha256"]) ==
            (A04_UI_SETTINGS_BYTES, A04_UI_SETTINGS_SHA256),
            "A04 UI settings differ from the frozen full snapshot")
    source_bytes = snapshot_path.read_bytes()
    gui_block = source_bytes[A04_UI_GUI_BLOCK_START:A04_UI_GUI_BLOCK_END]
    require(len(source_bytes) == A04_UI_SETTINGS_BYTES and
            hashlib.sha256(source_bytes).hexdigest().upper() == A04_UI_SETTINGS_SHA256 and
            source_bytes.count(b'"GUI"=') == 1 and
            len(gui_block) == A04_UI_GUI_BLOCK_END - A04_UI_GUI_BLOCK_START and
            gui_block == A04_UI_GUI_BLOCK_BYTES and
            hashlib.sha256(gui_block).hexdigest().upper() == A04_UI_GUI_BLOCK_SHA256,
            "A04 UI exact GUI block differs from the frozen 54-byte source")
    preservation = identity(preservation_path)
    require(preservation["sha256"] == A04_UI_PRESERVATION_SHA256,
            "A04 UI preservation receipt differs from the reviewed bytes")
    receipt = json.loads(preservation_path.read_text(encoding="utf-8"))
    require(receipt.get("schema") == "xar.war-promo.native-ui-settings-preservation/v1" and
            receipt.get("source_stable_before_and_after_copy") is True and
            receipt.get("whole_settings_copy_used_as_new_profile") is False and
            receipt.get("gui_import_requires_separate_review") is True and
            receipt.get("a04_capture_status") == "RED",
            "A04 UI preservation contract is missing or changed")
    require(receipt.get("preserved") == source,
            "A04 UI preserved settings reference differs from supplied source")
    original_source = receipt.get("source") or {}
    require((original_source.get("bytes"), original_source.get("sha256")) ==
            (A04_UI_SETTINGS_BYTES, A04_UI_SETTINGS_SHA256),
            "A04 UI original settings identity differs")

    hot = receipt.get("hot_readback") or {}
    hot_path = Path(hot.get("path", ""))
    require(all(not part.is_symlink() for part in (hot_path, *hot_path.parents)),
            "A04 UI hot readback path contains a symlink")
    hot_identity = identity(hot_path)
    require(hot_identity == hot and hot_identity["sha256"] == A04_UI_HOT_READBACK_SHA256,
            "A04 UI hot readback differs from the reviewed receipt")
    hot_result = json.loads(hot_path.read_text(encoding="utf-8"))
    body = hot_result.get("body") or {}
    settings = body.get("settings") or {}
    require(hot_result.get("result") == "RED" and
            body.get("phase") == "hot-service-after-native-UI-save" and
            body.get("requested_scale") == "1.0" and
            body.get("observed_scale") == "1" and
            body.get("disk_gate_passed") is False and
            (settings.get("bytes"), settings.get("sha256")) ==
            (A04_UI_SETTINGS_BYTES, A04_UI_SETTINGS_SHA256),
            "A04 UI hot readback does not bind the native 100% setting")

    image_rows = receipt.get("original_ui_images")
    require(isinstance(image_rows, list) and len(image_rows) == len(A04_UI_IMAGE_IDENTITIES),
            "A04 UI original screenshot set is missing or ambiguous")
    images = {}
    for row in image_rows:
        require(isinstance(row, dict) and isinstance(row.get("path"), str),
                "A04 UI screenshot identity is malformed")
        path = Path(row["path"])
        name = path.name
        require(name in A04_UI_IMAGE_IDENTITIES and name not in images,
                "A04 UI screenshot name is unexpected or repeated")
        require(all(not part.is_symlink() for part in (path, *path.parents)),
                "A04 UI screenshot path contains a symlink")
        actual = identity(path)
        require(actual == row and (actual["bytes"], actual["sha256"]) ==
                A04_UI_IMAGE_IDENTITIES[name],
                "A04 UI original screenshot bytes differ")
        images[name] = actual
    require(set(images) == set(A04_UI_IMAGE_IDENTITIES),
            "A04 UI screenshot set is incomplete")
    return {"schema": "war-film-a05-a04-ui-source-binding/v1",
            "opt_in": True, "source_snapshot": source,
            "target": target,
            "expected_source_sha256": A04_UI_SETTINGS_SHA256,
            "expected_gui_block_sha256": A04_UI_GUI_BLOCK_SHA256,
            "preservation_receipt": preservation, "hot_readback": hot_identity,
            "original_ui_images": images,
            "a04_capture_status": "RED", "a05_runtime_scale_proven": False,
            "a05_visual_geometry_reviewed": False,
            "recording_authorized_by_this_binding": False}


def d11_live_admission(args: argparse.Namespace, checkpoint: dict | None,
                       argv: list[str]) -> dict | None:
    from d11_admission import D11_SAVE_SHA, verify_live_admission

    is_d11 = checkpoint is not None and checkpoint["save"]["sha256"] == D11_SAVE_SHA
    admission_lock = getattr(args, "d11_admission_lock", None)
    capture_requested = getattr(args, "capture", False)
    require(admission_lock is None or (capture_requested and is_d11),
            "d11 admission lock is only for the exact d11 live checkpoint")
    return (verify_live_admission(admission_lock, argv)
            if capture_requested and is_d11 else None)


def preflight(args: argparse.Namespace) -> dict:
    from xar_autoplayer.environment import ck3_process_inventory, make_spec
    from xar_autoplayer.runtime import NativeBridgeLaunchConfig, validate_native_bridge_launch_config
    from xar_autoplayer.bridge import frontend_gui_route_contract as front
    from xar_autoplayer.bridge.mcp_server import create_server
    from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
    from mcp import Client

    require(os.name == "nt", "Windows interactive desktop required")
    versions = {key: importlib.metadata.version(key) for key in ("mcp", "pywin32", "Pillow", "psutil")}
    require(versions["mcp"] == "2.0.0", "MCP SDK must be 2.0.0")
    spec = make_spec(state_dir=args.state_dir, game_dir=args.game_dir)
    checkpoint = checkpoint_source(args.checkpoint_save, args.checkpoint_receipt)
    d11_admission = d11_live_admission(args, checkpoint, sys.argv[1:])
    a04_ui_binding = validate_a04_ui_gui_source_binding(args, checkpoint)
    executable = identity(spec.game_exe)
    require(executable["sha256"] == EXACT_SHA, "Exact CK3 build mismatch")
    validate_native_bridge_launch_config(NativeBridgeLaunchConfig(
        mode="native-headless", pipe_name=args.pipe_name,
        dll_path=args.bridge_dll, injector_path=args.bridge_injector,
    ))
    battle_control_pair = validate_d11_battle_control_pair(
        checkpoint, getattr(args, "battle_control_pair_manifest", None),
        args.bridge_dll, args.bridge_injector,
    )
    binary = args.bridge_dll.read_bytes()
    required_capabilities = [
        front.QUERY_FRONTEND_GUI_ROUTE_V1_CAPABILITY,
        front.ACTIVATE_FRONTEND_NEW_GAME_V1_CAPABILITY,
        front.PROBE_FRONTEND_BOOKMARK_MODEL_V1_CAPABILITY,
        front.ACTIVATE_FRONTEND_SELECT_SUPPORTED_1066_CHARACTER_V1_CAPABILITY,
        front.ACTIVATE_FRONTEND_START_SELECTED_BOOKMARK_V1_CAPABILITY,
    ]
    if checkpoint is not None:
        required_capabilities = ["game.state.snapshot", "game.state.map-ready", "game.state.played-character"]
    if args.enable_private_phase_trace:
        required_capabilities += [
            "experimental-combat-phase-event-trace-begin-v1",
            "experimental-combat-phase-event-trace-finish-v1",
        ]
    if args.enable_private_ai_reentry_observer:
        require(identity(args.bridge_dll)["sha256"] ==
                args.private_ai_reentry_dll_sha256.upper(),
                "Private AI reentry DLL SHA-256 mismatch")
        required_capabilities += [AI_REENTRY_CAPABILITY, AI_REENTRY_STEP]
    strings = {key: key.encode() in binary for key in required_capabilities}
    write_new(args.output_dir / "static-capability-strings.json", strings)
    require(all(strings.values()), "Existing DLL lacks static strings: " + ", ".join(key for key, found in strings.items() if not found))
    bookmarks = [key for key in BOOKMARK_KEYS if key.encode() in binary]
    if checkpoint is None:
        require(len(bookmarks) == 1, "Existing DLL bookmark binding is missing or ambiguous")
    processes = ck3_process_inventory()
    require(not processes["processes"], "An existing CK3 process blocks capture")
    if args.record_debug_desktop:
        require(shutil.which(args.ffmpeg) is not None, "FFmpeg missing for opt-in debug recording")
        require(shutil.which(args.ffprobe) is not None, "ffprobe missing for opt-in debug recording")
    require(not args.state_dir.exists(), "State directory must be new")
    if args.shader_cache_source is not None:
        require(args.shader_cache_source.is_dir() and args.shader_cache_source.name == "shadercache",
                "Cache reuse requires an explicitly named existing shadercache directory")
    from xar_autoplayer.environment import ensure_state_path_safe
    ensure_state_path_safe(args.state_dir)

    async def listing() -> list[str]:
        # Listing creates the real pipe endpoint too. Release it before the
        # live observer creates its single owning driver for this pipe name.
        with closing(NativeHeadlessGameplayDriver(args.pipe_name, state_dir=args.state_dir)) as driver:
            async with Client(create_server(driver, profile_dir=spec.profile_dir)) as client:
                result = await client.list_tools()
                return [tool.name for tool in result.tools]

    tools = asyncio.run(listing())
    required_tools = [
        "ck3_query_frontend_gui_route_v1", "ck3_activate_frontend_new_game_v1",
        "ck3_activate_frontend_start_1066_bookmark_character_v1",
        "ck3_take_snapshot",
    ]
    if checkpoint is not None:
        required_tools = ["ck3_take_snapshot"]
    require(set(required_tools) <= set(tools), "MCP tool listing lacks capture methods")
    return {
        "schema": "ck3-native-war-ai-capture-preflight/v1", "observed_at": utc(),
        "result": "READY_FOR_BOUNDED_LIVE_ATTEMPT", "ck3_started": False,
        "python": {"path": sys.executable, "version": sys.version, "packages": versions},
        "game": executable, "bridge_dll": identity(args.bridge_dll),
        "bridge_injector": identity(args.bridge_injector),
        "static_capability_strings": strings, "runtime_capabilities_verified": False,
        # The public selected-candidate query is a Python projection of the
        # native bookmark model probe, not its own DLL command capability.
        "selected_candidate_provider": front.PROBE_FRONTEND_BOOKMARK_MODEL_V1_CAPABILITY,
        "official_mcp_tools_listed_without_game": required_tools,
        "bookmark_candidate_from_binary": bookmarks[0] if len(bookmarks) == 1 else None,
        "bookmark_identity_requires_live_readback": checkpoint is None,
        "checkpoint_source": checkpoint,
        "launch_mode": "managed-frontend-first-checkpoint" if checkpoint else "fresh-1066-bookmark",
        "record_debug_desktop": args.record_debug_desktop,
        "gui_scale_requested": args.gui_scale,
        "a04_ui_gui_source_binding": a04_ui_binding,
        "d11_battle_control_pair": battle_control_pair,
        "d11_admission": d11_admission,
        "process_inventory": processes, "state_dir": str(args.state_dir),
        "pipe_name": args.pipe_name,
        "codex_global_registration_required": False,
        "mcp_transport": "official-Client-create_server-in-process",
        "native_ai_causality_proven": False,
    }


def render_profile_settings(base: str, gui_scale: str | None) -> str:
    if gui_scale is None:
        return base
    require(gui_scale == "1.0", "Only the reviewed 1.0 GUI scale is supported")
    require('"GUI"=' not in base, "Base settings already define GUI; refuse duplicate")
    return base.rstrip("\n") + '\n"GUI"={\n\t"scale"={ version=1 value="1.0" }\n}\n'


def write_profile_settings(settings_path: Path, base: str, gui_scale: str | None) -> dict:
    settings_text = render_profile_settings(base, gui_scale)
    expected_utf8 = settings_text.encode("utf-8")
    if gui_scale is None:
        # Preserve the existing default Windows newline behavior byte for byte.
        settings_path.write_text(settings_text, encoding="utf-8")
    else:
        with settings_path.open("xb") as stream:
            stream.write(expected_utf8)
    actual = settings_path.read_bytes()
    require(gui_scale is None or actual == expected_utf8,
            "Prepared GUI settings disk bytes differ from the frozen UTF-8 render")
    require(settings_path.read_text(encoding="utf-8") == settings_text,
            "Prepared GUI settings text readback differs")
    settings_identity = identity(settings_path)
    require(settings_identity["sha256"] == hashlib.sha256(actual).hexdigest().upper(),
            "Prepared GUI settings identity differs from disk bytes")
    return {
        "requested_scale": gui_scale,
        "settings": settings_identity,
        "expected_utf8_sha256": hashlib.sha256(expected_utf8).hexdigest().upper() if gui_scale else None,
        "exact_utf8_disk_match": actual == expected_utf8 if gui_scale else None,
        "text_readback_matches": True,
    }


def import_ui_saved_gui_block(settings_path: Path, vanilla_settings: str,
                              source_snapshot: Path, expected_source_sha256: str,
                              output_dir: Path, *, expected_gui_block_sha256: str,
                              requested_scale: str) -> dict:
    """Prepare one fresh profile from vanilla bytes plus an exact UI-saved GUI block.

    The a05 CLI may call this only after binding the frozen source, UI images,
    and hot readback.  The caller must also prove its state directory is new.
    """
    receipt_path = output_dir / "gui-settings-ui-block-import.json"
    require(output_dir.is_dir() and not output_dir.is_symlink() and
            not receipt_path.exists() and not receipt_path.is_symlink(),
            "Import receipt directory must exist without an old receipt")
    row = {
        "schema": "war-film-ui-saved-gui-block-import/v1", "at": utc(),
        "source_snapshot_path": str(source_snapshot.absolute()),
        "target_settings_path": str(settings_path.absolute()),
        "expected_source_sha256": expected_source_sha256,
        "expected_gui_block_sha256": expected_gui_block_sha256,
        "requested_scale": requested_scale, "native_ui_serialized_scale": None,
        "source_snapshot": None, "source_gui_block": None,
        "vanilla_non_gui_template": None, "staging_settings": None,
        "prepared_snapshot": None,
        "prepared_settings": None, "atomic_exclusive_publish": False,
        "exact_source_gui_block_preserved": False,
        "non_gui_bytes_equal_vanilla_template": False,
        "runtime_scale_proven": False, "visual_geometry_reviewed": False,
        "recording_authorized_by_this_receipt": False,
        "status": "RED",
    }
    primary_error = None
    try:
        require(requested_scale == "1.0",
                "UI GUI import needs the explicit 1.0 capture request")
        require(re.fullmatch(r"[0-9A-Fa-f]{64}", expected_source_sha256) is not None,
                "UI snapshot needs an explicit SHA-256")
        require(re.fullmatch(r"[0-9A-Fa-f]{64}", expected_gui_block_sha256) is not None,
                "UI GUI block needs an independent explicit SHA-256")
        require(settings_path.name == "pdx_settings.txt", "Target must be pdx_settings.txt")
        require(settings_path.parent.is_dir(), "Fresh profile directory is missing")
        require(not settings_path.exists() and not settings_path.is_symlink(),
                "Target settings already exist")
        for path in (source_snapshot, settings_path, output_dir):
            require(all(not part.is_symlink() for part in (path, *path.parents)),
                    "GUI import paths must not contain symlinks")
        require(source_snapshot.is_file(), "UI-saved full settings snapshot is missing")
        require(source_snapshot.resolve() != settings_path.resolve(),
                "Source snapshot and target must be different files")

        before = source_snapshot.stat()
        source = source_snapshot.read_bytes()
        after = source_snapshot.stat()
        source_sha = hashlib.sha256(source).hexdigest().upper()
        require((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
                (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) and
                len(source) == after.st_size, "UI snapshot changed during read")
        require(source_sha == expected_source_sha256.upper(), "UI snapshot SHA-256 differs")
        require(len(source) <= 1024 * 1024, "UI snapshot exceeds reviewed size limit")
        source.decode("utf-8")
        declarations = list(re.finditer(rb'(?m)^[ \t]*"GUI"\s*=\s*\{', source))
        # CK3's reviewed UI SaveAndClose serializes displayed 100% as "1".
        # Accept exactly this native value for the explicit 1.0 request.
        # The closing line break is part of the imported bytes, including CRLF.
        blocks = list(re.finditer(
            rb'(?m)^"GUI"[ \t]*=[ \t]*\{[ \t\r\n]*'
            rb'"scale"[ \t]*=[ \t]*\{[ \t\r\n]*version[ \t]*=[ \t]*1[ \t\r\n]+'
            rb'value[ \t]*=[ \t]*"1"[ \t\r\n]*\}[ \t\r\n]*\}[ \t]*(?:\r?\n|$)',
            source))
        require(len(declarations) == len(blocks) == 1 and
                declarations[0].start() == blocks[0].start(),
                "UI snapshot has missing, ambiguous, extra-key or unreviewed GUI syntax")
        block = blocks[0].group()
        row["native_ui_serialized_scale"] = "1"
        block_sha = hashlib.sha256(block).hexdigest().upper()
        require(block_sha == expected_gui_block_sha256.upper(),
                "UI GUI block SHA-256 differs from independently frozen expectation")
        non_gui_source = source[:blocks[0].start()] + source[blocks[0].end():]
        require(re.search(rb'(?m)^"[A-Za-z_][A-Za-z0-9_]*"[ \t]*=[ \t]*\{',
                          non_gui_source) is not None,
                "UI snapshot must contain full non-GUI settings, not only a GUI fragment")
        template = vanilla_settings.encode("utf-8")
        require(re.search(rb'(?m)^[ \t]*"GUI"\s*=', template) is None,
                "Vanilla template already defines GUI")
        require(template.endswith(b"\n"), "Vanilla template must end with a line break")
        prepared = template + block
        row["source_snapshot"] = {"path": str(source_snapshot.resolve()),
                                  "bytes": len(source), "sha256": source_sha}
        row["source_gui_block"] = {"bytes": len(block),
                                   "sha256": block_sha}
        row["vanilla_non_gui_template"] = {"bytes": len(template),
                                           "sha256": hashlib.sha256(template).hexdigest().upper()}
        require(source_snapshot.stat().st_mtime_ns == after.st_mtime_ns and
                source_snapshot.read_bytes() == source,
                "UI snapshot changed before target creation")
        prepared_snapshot_path = output_dir / "gui-settings-ui-import-prepared.pdx.txt"
        with prepared_snapshot_path.open("xb") as snapshot:
            snapshot.write(prepared)
            snapshot.flush()
            os.fsync(snapshot.fileno())
        require(prepared_snapshot_path.read_bytes() == prepared,
                "Prepared immutable evidence snapshot differs")
        row["prepared_snapshot"] = identity(prepared_snapshot_path)
        descriptor, staging_name = tempfile.mkstemp(
            prefix=".pdx_settings.ui_import-", suffix=".tmp", dir=settings_path.parent)
        staging_path = Path(staging_name)
        row["staging_path"] = str(staging_path.resolve())
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(prepared)
            stream.flush()
            os.fsync(stream.fileno())
        require(staging_path.read_bytes() == prepared,
                "Staged GUI settings disk bytes differ")
        row["staging_settings"] = identity(staging_path)
        require(source_snapshot.stat().st_mtime_ns == after.st_mtime_ns and
                source_snapshot.read_bytes() == source,
                "UI snapshot changed before atomic publication")
        # A same-directory hard link creates the target atomically and fails if
        # another writer created it. The separate evidence snapshot remains.
        os.link(staging_path, settings_path)
        row["atomic_exclusive_publish"] = True
        staging_path.unlink()
        row["staging_unlinked_after_publish"] = True
        actual = settings_path.read_bytes()
        require(actual == prepared, "Prepared GUI settings disk bytes differ")
        require(actual[:len(template)] == template and actual[len(template):] == block,
                "Prepared GUI settings changed outside the imported block")
        row["prepared_settings"] = identity(settings_path)
        require(row["prepared_settings"]["bytes"] == len(prepared) and
                row["prepared_settings"]["sha256"] == hashlib.sha256(prepared).hexdigest().upper(),
                "Prepared GUI settings identity differs")
        row["exact_source_gui_block_preserved"] = True
        row["non_gui_bytes_equal_vanilla_template"] = True
        row["status"] = "GREEN_DISK_ONLY"
    except Exception as error:
        row["error"] = repr(error)
        primary_error = error
    finally:
        write_new(receipt_path, row)
    if primary_error is not None:
        raise primary_error.with_traceback(primary_error.__traceback__)
    return row


GUI_SCALE_DECIMAL = re.compile(r"(?:0|[1-9][0-9]*)(?:\.[0-9]+)?\Z", re.ASCII)


def normalize_gui_scale_ratio(serialized: str) -> str | None:
    """Normalize a quoted fixed decimal without float rounding or loose parsing."""
    if (not isinstance(serialized, str) or len(serialized) > 32 or
            GUI_SCALE_DECIMAL.fullmatch(serialized) is None):
        return None
    integer, separator, fraction = serialized.partition(".")
    fraction = fraction.rstrip("0") if separator else ""
    if integer == "0" and not fraction:
        return None
    return integer + ("." + fraction if fraction else "")


def gui_scale_disk_readback(settings_path: Path, requested_scale: str, phase: str,
                            *, allow_native_ui_one: bool = False,
                            require_native_a04_gui_block: bool = False) -> dict:
    """Read the isolated profile's persisted GUI setting without claiming runtime state."""
    require(requested_scale == "1.0", "Only the reviewed 1.0 GUI scale is supported")
    require(type(allow_native_ui_one) is bool, "Native UI one opt-in must be boolean")
    require(type(require_native_a04_gui_block) is bool and
            (not require_native_a04_gui_block or allow_native_ui_one),
            "Exact a04 GUI block gate needs native UI one opt-in")
    requested_ratio = normalize_gui_scale_ratio(requested_scale)
    require(requested_ratio is not None, "Requested GUI scale is not a fixed decimal ratio")
    row = {"schema": "war-film-gui-scale-disk-gate/v2", "observed_at": utc(),
           "phase": phase, "requested_scale": requested_scale,
           "requested_scale_ratio": requested_ratio,
           "settings_path": str(settings_path.resolve()), "settings": None,
           "observed_scale": None, "observed_scale_serialized": None,
           "observed_scale_token": None,
           "observed_scale_ratio": None, "native_ui_one_opt_in": allow_native_ui_one,
           "ratio_equivalent_to_request": False, "admission": None,
           "disk_gate_passed": False,
           "runtime_scale_proven": False, "visual_geometry_reviewed": False,
           "recording_authorized_by_this_gate": False}
    try:
        before = settings_path.stat()
        raw = settings_path.read_bytes()
        after = settings_path.stat()
        content_sha = hashlib.sha256(raw).hexdigest().upper()
        disk_identity = identity(settings_path)
        require(before.st_mtime_ns == after.st_mtime_ns and
                before.st_size == after.st_size == len(raw) and
                disk_identity["bytes"] == len(raw) and
                disk_identity["sha256"] == content_sha,
                "GUI settings changed during readback")
        row["settings"] = {**disk_identity, "mtime_ns": after.st_mtime_ns}
        gui_declarations = re.findall(rb'(?m)^[ \t]*"GUI"\s*=', raw)
        known_gui_block = re.findall(
            rb'(?ms)^"GUI"\s*=\s*\{\s*"scale"\s*=\s*\{\s*'
            rb'version\s*=\s*1\s*value\s*=\s*"([^"\r\n]*)"\s*\}\s*\}', raw)
        if len(gui_declarations) == 1 and len(known_gui_block) == 1:
            serialized = known_gui_block[0].decode("ascii")
            ratio = normalize_gui_scale_ratio(serialized)
            row["observed_scale"] = serialized
            row["observed_scale_serialized"] = serialized
            row["observed_scale_token"] = f'value="{serialized}"'
            row["observed_scale_ratio"] = ratio
            row["ratio_equivalent_to_request"] = ratio == requested_ratio
            if serialized == requested_scale:
                row["admission"] = "requested_literal"
            elif allow_native_ui_one and serialized == "1":
                row["admission"] = "explicit_native_ui_one"
            row["disk_gate_passed"] = row["admission"] is not None
            if ratio is None:
                row["reason"] = "noncanonical_numeric_gui_scale"
            elif row["admission"] is None and ratio == requested_ratio:
                row["reason"] = "ratio_equal_but_literal_not_admitted"
        else:
            row["reason"] = "missing_ambiguous_or_unrecognized_GUI_block"
        if require_native_a04_gui_block:
            pinned = (len(A04_UI_GUI_BLOCK_BYTES) == A04_UI_GUI_BLOCK_END - A04_UI_GUI_BLOCK_START
                      and hashlib.sha256(A04_UI_GUI_BLOCK_BYTES).hexdigest().upper() ==
                      A04_UI_GUI_BLOCK_SHA256)
            exact = pinned and len(gui_declarations) == 1 and raw.count(A04_UI_GUI_BLOCK_BYTES) == 1
            row["native_a04_gui_block_required"] = True
            row["native_a04_gui_block_sha256"] = A04_UI_GUI_BLOCK_SHA256
            row["native_a04_gui_block_passed"] = exact
            if not exact:
                row["disk_gate_passed"] = False
                row["reason"] = "exact_native_a04_gui_block_missing_or_ambiguous"
    except (OSError, UnicodeError, RuntimeError) as error:
        row["reason"] = repr(error)
    return row


def require_gui_scale_disk_gate(settings_path: Path, requested_scale: str | None,
                                phase: str, receipt_path: Path,
                                *, allow_native_ui_one: bool = False,
                                require_native_a04_gui_block: bool = False) -> None:
    if requested_scale is None:
        require(allow_native_ui_one is False and require_native_a04_gui_block is False,
                "Native UI one opt-in requires an explicit requested GUI scale")
        return
    receipt = gui_scale_disk_readback(settings_path, requested_scale, phase,
                                      allow_native_ui_one=allow_native_ui_one,
                                      require_native_a04_gui_block=require_native_a04_gui_block)
    write_new(receipt_path, receipt)
    require(receipt["disk_gate_passed"],
            f"GUI.scale disk gate failed at {phase}; see {receipt_path}")


def reseed_gui_scale_after_warmup(settings_path: Path, requested_scale: str,
                                  output_dir: Path,
                                  *, allow_native_ui_one: bool = False) -> None:
    """Restore the isolated profile after warm-up has exited, before final launch.

    The warm-up's RED readback and full settings bytes remain separate evidence.
    Only the value in the one recognized GUI.scale block may change.  The final
    game's post-map gate still has to pass; this does not prove runtime geometry.
    """
    require(requested_scale == "1.0", "Only the reviewed 1.0 GUI scale is supported")
    before_path = output_dir / "gui-settings-before-final-launch.json"
    snapshot_path = output_dir / "gui-settings-warmup-before-reseed.pdx.txt"
    reseed_path = output_dir / "gui-settings-warmup-reseed.json"
    after_path = output_dir / "gui-settings-after-reseed-before-final-launch.json"
    before = gui_scale_disk_readback(settings_path, requested_scale,
                                     "after-warmup-before-final-launch",
                                     allow_native_ui_one=allow_native_ui_one)
    write_new(before_path, before)
    row = {"schema": "war-film-gui-scale-warmup-reseed/v1", "at": utc(),
           "requested_scale": requested_scale, "before_readback": str(before_path.resolve()),
           "before_disk_gate_passed": before["disk_gate_passed"],
           "before_observed_scale": before["observed_scale"],
           "before_observed_scale_ratio": before["observed_scale_ratio"],
           "source_snapshot": None, "replacement_performed": False,
           "atomic_same_directory_replace": False, "after_readback": str(after_path.resolve()),
           "runtime_scale_proven": False, "visual_geometry_reviewed": False,
           "recording_authorized_by_this_receipt": False, "status": "RED"}
    temp_path = None
    primary_error = None
    cleanup_error = None
    receipt_error = None
    try:
        require(not settings_path.is_symlink(), "GUI settings path must not be a symlink")
        require(before["settings"] is not None, "Warm-up GUI settings identity unavailable")
        source_stat = settings_path.stat()
        source = settings_path.read_bytes()
        require(source_stat.st_mtime_ns == before["settings"]["mtime_ns"] and
                source_stat.st_size == before["settings"]["bytes"] == len(source) and
                hashlib.sha256(source).hexdigest().upper() == before["settings"]["sha256"],
                "Warm-up GUI settings changed after RED readback")
        with snapshot_path.open("xb") as snapshot:
            snapshot.write(source)
            snapshot.flush()
            os.fsync(snapshot.fileno())
        row["source_snapshot"] = identity(snapshot_path)
        require(row["source_snapshot"]["sha256"] == before["settings"]["sha256"],
                "Warm-up settings snapshot differs from readback")

        declarations = list(re.finditer(rb'(?m)^[ \t]*"GUI"\s*=', source))
        blocks = list(re.finditer(
            rb'(?ms)^"GUI"\s*=\s*\{\s*"scale"\s*=\s*\{\s*'
            rb'version\s*=\s*1\s*value\s*=\s*"(?P<value>[^"\r\n]*)"\s*\}\s*\}',
            source))
        require(len(declarations) == len(blocks) == 1,
                "Warm-up GUI block is missing, ambiguous or not the reviewed syntax")
        observed = blocks[0].group("value").decode("ascii")
        require(observed == before["observed_scale"],
                "Warm-up GUI block differs from RED readback")
        require(observed == "1.3" or before["disk_gate_passed"],
                "Warm-up GUI scale is outside the reviewed 100%/130% values")
        row["source_settings"] = {**before["settings"]}
        native_block = None
        native_match = None
        if allow_native_ui_one:
            native_block = A04_UI_GUI_BLOCK_BYTES
            require(len(native_block) == A04_UI_GUI_BLOCK_END - A04_UI_GUI_BLOCK_START and
                    hashlib.sha256(native_block).hexdigest().upper() == A04_UI_GUI_BLOCK_SHA256,
                    "Frozen a04 native GUI block constant differs from reviewed SHA")
            candidates = list(re.finditer(
                rb'(?m)^"GUI"[ \t]*=[ \t]*\{[ \t\r\n]*'
                rb'"scale"[ \t]*=[ \t]*\{[ \t\r\n]*version[ \t]*=[ \t]*1[ \t\r\n]+'
                rb'value[ \t]*=[ \t]*"(?P<value>[^"\r\n]*)"[ \t\r\n]*\}'
                rb'[ \t\r\n]*\}[ \t]*(?:\r?\n|$)', source))
            require(len(candidates) == 1 and candidates[0].start() == blocks[0].start() and
                    candidates[0].group("value").decode("ascii") == observed,
                    "Warm-up native GUI block is missing, ambiguous or has unreviewed syntax")
            native_match = candidates[0]
            row["native_a04_gui_block_sha256"] = A04_UI_GUI_BLOCK_SHA256
            row["warmup_gui_block"] = {"bytes": len(native_match.group()),
                                       "sha256": hashlib.sha256(native_match.group()).hexdigest().upper()}
            require(observed in ("1.3", "1"),
                    "A05 final launch requires the native 1 literal or reviewed 1.3 warm-up value")
        if observed == "1.3":
            if allow_native_ui_one:
                target = source[:native_match.start()] + native_block + source[native_match.end():]
                row["non_gui_bytes_unchanged"] = (
                    target.replace(native_block, b"", 1) ==
                    source[:native_match.start()] + source[native_match.end():])
                require(row["non_gui_bytes_unchanged"],
                        "A05 warm-up reseed changed non-GUI bytes")
            else:
                target = source[:blocks[0].start("value")] + b"1.0" + source[blocks[0].end("value"):]
            row["expected_target"] = {"bytes": len(target),
                                      "sha256": hashlib.sha256(target).hexdigest().upper()}
            # The native-session callback runs only after verified warm-up shutdown.
            # Recheck its exact bytes immediately before same-directory replacement.
            require(settings_path.stat().st_mtime_ns == source_stat.st_mtime_ns and
                    settings_path.read_bytes() == source,
                    "Warm-up GUI settings changed before reseed")
            descriptor, temp_name = tempfile.mkstemp(
                prefix=".pdx_settings.gui_reseed-", suffix=".tmp", dir=settings_path.parent)
            temp_path = Path(temp_name)
            with os.fdopen(descriptor, "wb") as staging:
                staging.write(target)
                staging.flush()
                os.fsync(staging.fileno())
            require(temp_path.read_bytes() == target,
                    "GUI settings temporary bytes differ before replace")
            require(settings_path.stat().st_mtime_ns == source_stat.st_mtime_ns and
                    settings_path.read_bytes() == source,
                    "Warm-up GUI settings changed while staging reseed")
            os.replace(temp_path, settings_path)
            temp_path = None
            row["replacement_performed"] = True
            row["atomic_same_directory_replace"] = True
            require(settings_path.read_bytes() == target,
                    "GUI settings bytes differ after atomic replace")
        else:
            if allow_native_ui_one:
                require(native_match.group() == native_block,
                        "A05 warm-up 100% block differs from the exact native UI bytes")
            row["expected_target"] = {"bytes": len(source),
                                      "sha256": hashlib.sha256(source).hexdigest().upper()}
        row["after_settings"] = {**identity(settings_path),
                                 "mtime_ns": settings_path.stat().st_mtime_ns}
        require(row["after_settings"]["bytes"] == row["expected_target"]["bytes"] and
                row["after_settings"]["sha256"] == row["expected_target"]["sha256"],
                "GUI settings target identity differs after reseed")
        require_gui_scale_disk_gate(settings_path, requested_scale,
                                    "after-reseed-before-final-launch", after_path,
                                    allow_native_ui_one=allow_native_ui_one,
                                    require_native_a04_gui_block=allow_native_ui_one)
        if allow_native_ui_one:
            row["final_native_gui_block_exact"] = True
        row["status"] = "GREEN_DISK_ONLY"
    except Exception as error:
        row["error"] = repr(error)
        primary_error = error
    finally:
        if temp_path is not None:
            try:
                temp_path.unlink(missing_ok=True)
            except Exception as error:
                cleanup_error = error
                row["cleanup_error"] = repr(error)
                row["cleanup_path"] = str(temp_path.resolve())
                row["status"] = "RED"
        try:
            write_new(reseed_path, row)
        except Exception as error:
            receipt_error = error
    if primary_error is not None:
        raise primary_error.with_traceback(primary_error.__traceback__)
    if cleanup_error is not None:
        raise RuntimeError(f"GUI reseed temporary cleanup failed; see {reseed_path}") from cleanup_error
    if receipt_error is not None:
        raise receipt_error.with_traceback(receipt_error.__traceback__)


def prepare_a05_ui_settings(settings_path: Path, vanilla_settings: str,
                            output_dir: Path, binding: dict) -> dict:
    """Publish one bound profile's settings using the frozen a04 GUI block."""
    target = binding.get("target") or {}
    require(binding.get("schema") == "war-film-a05-a04-ui-source-binding/v1" and
            binding.get("expected_source_sha256") == A04_UI_SETTINGS_SHA256 and
            binding.get("expected_gui_block_sha256") == A04_UI_GUI_BLOCK_SHA256 and
            binding.get("source_snapshot", {}).get("sha256") == A04_UI_SETTINGS_SHA256 and
            binding.get("preservation_receipt", {}).get("sha256") == A04_UI_PRESERVATION_SHA256 and
            binding.get("hot_readback", {}).get("sha256") == A04_UI_HOT_READBACK_SHA256,
            "Profile lacks the reviewed a04 UI source and evidence binding")
    require(target.get("track") in A04_UI_TARGETS and
            target.get("userdir") == str(settings_path.parent.resolve()) and
            target.get("state_dir") == str(settings_path.parent.parent.resolve()) and
            target.get("output_dir") == str(output_dir.resolve()) and
            isinstance(target.get("source_checkpoint"), dict),
            "A04 UI target userdir/output differs from its exact checkpoint binding")
    source_path = Path(binding["source_snapshot"]["path"])
    imported = import_ui_saved_gui_block(
        settings_path, vanilla_settings, source_path,
        A04_UI_SETTINGS_SHA256, output_dir,
        expected_gui_block_sha256=A04_UI_GUI_BLOCK_SHA256,
        requested_scale="1.0")
    prepared = (output_dir / "gui-settings-ui-import-prepared.pdx.txt").read_bytes()
    require(settings_path.read_bytes() == prepared and
            imported["prepared_settings"]["sha256"] ==
            hashlib.sha256(prepared).hexdigest().upper(),
            "A05 imported profile differs from frozen prepared bytes")
    result = {
        "requested_scale": "1.0", "settings": imported["prepared_settings"],
        "expected_utf8_sha256": imported["prepared_settings"]["sha256"],
        "exact_utf8_disk_match": True,
        "text_readback_matches": settings_path.read_bytes().decode("utf-8") ==
                                 prepared.decode("utf-8"),
        "profile_settings_origin": "reviewed_a04_ui_gui_block_only",
        "target": target,
        "ui_import_receipt": identity(output_dir / "gui-settings-ui-block-import.json"),
        "ui_source_preservation_receipt": binding["preservation_receipt"],
        "runtime_scale_proven": False, "visual_geometry_reviewed": False,
        "recording_authorized_by_prelaunch": False,
    }
    require(result["text_readback_matches"], "Imported settings text readback differs")
    return result


def prepare_profile(args: argparse.Namespace, checkpoint: dict | None = None,
                    a04_ui_binding: dict | None = None) -> tuple[object, dict]:
    from xar_autoplayer.environment import make_spec, render_settings
    from xar_autoplayer.rules import declared_vanilla_rule_defaults, render_presets
    from xar_autoplayer.bridge.succession_transition_contract import (
        ORDINARY_CAMPAIGN_SUCCESSION, SUCCESSION_LIFECYCLE_BINDING_V1_SCHEMA,
        normalize_succession_lifecycle_binding_v1,
    )
    spec = make_spec(state_dir=args.state_dir, game_dir=args.game_dir)
    for relative in ("mod", "logs", "save games", "player/game_rules"):
        (spec.profile_dir / relative).mkdir(parents=True, exist_ok=False)
    write_new(spec.profile_dir / "dlc_load.json", {"enabled_mods": [], "disabled_dlcs": []})
    rules = declared_vanilla_rule_defaults(spec.vanilla_rules)
    presets = render_presets({"profile": [{"rule": r, "setting": s} for r, s in rules], "ironman": False})
    (spec.profile_dir / "player/game_rules/presets.txt").write_text(presets, encoding="utf-8")
    settings_path = spec.profile_dir / "pdx_settings.txt"
    if a04_ui_binding is None:
        settings_prelaunch = write_profile_settings(settings_path, render_settings(), args.gui_scale)
    else:
        require(args.gui_scale == "1.0" and
                a04_ui_binding["target"]["source_checkpoint"] == checkpoint,
                "A04 UI profile needs the same exact checkpoint and 1.0 request")
        settings_prelaunch = prepare_a05_ui_settings(
            settings_path, render_settings(), args.output_dir, a04_ui_binding)
    write_new(args.output_dir / "gui-settings-prelaunch.json", settings_prelaunch)
    (spec.profile_dir / "tutorial.txt").write_text('last_lesson_chain="reactive_advice"\ncompleted_lessons={\n}\n', encoding="utf-8")
    if args.shader_cache_source is not None:
        source_cache = args.shader_cache_source.resolve()
        target_cache = spec.profile_dir / "shadercache"
        target_cache.mkdir(exist_ok=False)
        copied = []
        for source in sorted(source_cache.rglob("*")):
            require(not source.is_symlink(), "Shader cache must not contain symbolic links")
            if not source.is_file():
                continue
            target = target_cache / source.relative_to(source_cache)
            target.parent.mkdir(parents=True, exist_ok=True)
            before = identity(source)
            shutil.copyfile(source, target)
            after = identity(target)
            require(before["bytes"] == after["bytes"] and before["sha256"] == after["sha256"],
                    "Shader cache copy mismatch")
            copied.append({"source": before, "copy": after})
        write_new(args.output_dir / "shader-cache-reuse.json", {
            "source": str(source_cache), "destination": str(target_cache),
            "files": copied, "semantic_profile_files_copied": False,
        })
    profile = {
        "kind": "vanilla-observational-map-capture-profile", "enabled_mods": [],
        "profile_dir": str(spec.profile_dir), "game": identity(spec.game_exe),
        "files": [identity(spec.profile_dir / p) for p in (
            "dlc_load.json", "pdx_settings.txt", "player/game_rules/presets.txt", "tutorial.txt")],
    }
    if checkpoint is not None:
        profile["checkpoint_copy"] = copy_checkpoint(checkpoint, spec.profile_dir, args.output_dir)
        profile["kind"] = "vanilla-observational-checkpoint-profile"
    write_new(args.output_dir / "profile-source.json", profile)
    digest = hashlib.sha256(json.dumps(profile, sort_keys=True).encode()).hexdigest()
    lifecycle = normalize_succession_lifecycle_binding_v1({
        "schema": SUCCESSION_LIFECYCLE_BINDING_V1_SCHEMA,
        "lifecycle": ORDINARY_CAMPAIGN_SUCCESSION, "xar_enabled": "xar_off",
        "pact_contract": "absent_by_fresh_campaign_xar_off_contract",
        "source": "pure-vanilla-enabled-mods-empty", "environment_sha256": digest,
    })
    return spec, lifecycle


def require_native_bridge_tree_proof() -> None:
    """Stop live video until injector integration and recorder cleanup are reviewed."""
    require(False,
        "native bridge and recorder end-to-end process-tree admission is not reviewed; "
        "screen-gated capture remains stopped before any child process"
    )


def capture(args: argparse.Namespace, checked: dict, screen_lease: dict) -> dict:
    require_native_bridge_tree_proof()
    from ck3_live_run_id import allocate_live_run_id, write_identity_receipt, record_live_run_status
    from xar_autoplayer.native_session import native_session
    from xar_autoplayer.runtime import NativeBridgeLaunchConfig
    from xar_autoplayer.environment import ck3_process_inventory
    from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
    from xar_autoplayer.bridge.mcp_server import create_server
    from mcp import Client

    require(args.steam_offline_receipt is not None, "Capture requires a reviewed Steam offline UI receipt")
    receipt = json.loads(args.steam_offline_receipt.read_text(encoding="utf-8"))
    require(receipt.get("current_offline_ui_observed") is True, "Steam offline UI not observed")
    screenshot = Path(receipt["screenshot"]["path"])
    require(identity(screenshot) == receipt["screenshot"], "Steam screenshot identity changed")
    observed = datetime.fromisoformat(receipt["observed_at"])
    require(0 <= (datetime.now(timezone.utc) - observed).total_seconds() <= 900, "Steam offline receipt stale")
    a04_ui_binding = checked.get("a04_ui_gui_source_binding")
    current_checkpoint = checkpoint_source(args.checkpoint_save, args.checkpoint_receipt)
    require(current_checkpoint == checked.get("checkpoint_source"),
            "Checkpoint source changed after no-launch preflight")
    require(validate_a04_ui_gui_source_binding(
        args, current_checkpoint) == a04_ui_binding,
            "A04 UI source or evidence changed after no-launch preflight")
    require(validate_d11_battle_control_pair(
        current_checkpoint, getattr(args, "battle_control_pair_manifest", None),
        args.bridge_dll, args.bridge_injector,
    ) == checked.get("d11_battle_control_pair"),
            "D11 battle-control source pair changed after no-launch preflight")
    allow_native_ui_one = a04_ui_binding is not None
    run = allocate_live_run_id("vanilla")
    write_identity_receipt(args.output_dir, (run,))
    checkpoint = checked.get("checkpoint_source")
    try:
        spec, lifecycle = prepare_profile(args, checkpoint, a04_ui_binding)
    except Exception as error:
        record_live_run_status(run, "completed-red", reason=str(error))
        raise
    settings_path = spec.profile_dir / "pdx_settings.txt"
    try:
        require_gui_scale_disk_gate(
            settings_path, args.gui_scale, "before-native-session",
            args.output_dir / "gui-settings-before-native-session.json",
            allow_native_ui_one=allow_native_ui_one,
            require_native_a04_gui_block=allow_native_ui_one)
    except Exception as error:
        record_live_run_status(run, "completed-red", reason=str(error))
        raise
    stopped = threading.Event()
    recorder: RecorderJob | None = None
    recorder_cleanup: dict | None = None
    recorder_lock = threading.Lock()

    def abort_debug_recorder() -> None:
        nonlocal recorder_cleanup
        with recorder_lock:
            if recorder is None:
                return
            row = recorder.abort(
                receipt=args.output_dir / "ffmpeg-abort.json",
                unsafe_marker=args.output_dir / "unsafe-ffmpeg-cleanup.json")
            if row["state"] != "ALREADY_TREE_EMPTY":
                recorder_cleanup = row

    def finish_debug_recorder() -> None:
        nonlocal recorder_cleanup
        if recorder is None or recorder_cleanup is not None:
            return
        try:
            row = recorder.finish(
                receipt=args.output_dir / "ffmpeg-finish.json",
                unsafe_marker=args.output_dir / "unsafe-ffmpeg-cleanup.json")
            with recorder_lock:
                if recorder_cleanup is None:
                    recorder_cleanup = row
        except BaseException:
            # A failed finish must still stop the Job before keeper shutdown.
            try:
                abort_debug_recorder()
            finally:
                raise

    lease_keeper = ScreenLeaseKeeper(
        source=ROOT / "tools" / "codex_task_bus.py",
        bus_dir=Path("D:/workspace/.codex-task-bus"),
        expected_sha=args.screen_cli_sha256,
        task_id=args.screen_task_id,
        sequence=screen_lease["sequence"], repo=ROOT,
        journal=args.output_dir / "screen-lease-journal.jsonl",
        abort=stopped, audit_dir=args.output_dir / "screen-bus-commands",
        on_abort=abort_debug_recorder,
    )
    worker: dict = {"ok": False, "error": None, "marks": []}
    origin = time.monotonic()
    raw = args.output_dir / "raw-desktop.mkv"
    command = [shutil.which(args.ffmpeg), "-n", "-hide_banner", "-loglevel", "warning",
               "-f", "gdigrab", "-framerate", "30", "-draw_mouse", "0", "-i", "desktop",
               "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18", "-pix_fmt", "yuv420p", "-an", str(raw)] if args.record_debug_desktop else None
    write_new(args.output_dir / "recording-policy.json", {
        "debug_desktop_enabled": args.record_debug_desktop,
        "default": "no-background-desktop-recorder",
        "scope": "optional startup/debug evidence; never a certified gameplay recording",
        "gameplay_recorder_owned_by_this_script": False,
    })
    if command is not None:
        write_new(args.output_dir / "ffmpeg-command.json", command)
    session_result: dict = {}

    async def observe() -> None:
        driver = NativeHeadlessGameplayDriver(
            args.pipe_name, state_dir=args.state_dir, save_dir=spec.profile_dir / "save games",
            frontend_transition_timeout_seconds=args.frontend_timeout,
            succession_lifecycle_binding=lifecycle,
        )
        with closing(driver):
            async with Client(create_server(driver, profile_dir=spec.profile_dir)) as client:
                async def call(name: str, arguments: dict | None = None, tolerate: bool = False) -> dict:
                    row = {"tool": name, "arguments": arguments or {}, "at": utc(), "seconds": time.monotonic() - origin}
                    try:
                        result = await client.call_tool(name, arguments or {})
                        row.update({"is_error": bool(result.is_error), "body": result.structured_content,
                                    "content": [item.model_dump(mode="json") for item in result.content]})
                    except Exception as error:
                        row.update({"is_error": True, "error": repr(error)})
                    append(args.output_dir / "mcp-calls.jsonl", row)
                    if not tolerate:
                        require(not row["is_error"], f"MCP call failed: {name}; inspect journal")
                    return row.get("body") or {}

                async def start_fresh_campaign() -> dict:
                    deadline = time.monotonic() + args.frontend_timeout
                    next_progress = 0.0
                    route = {}
                    while time.monotonic() < deadline and not stopped.is_set():
                        route = await call("ck3_query_frontend_gui_route_v1", tolerate=True)
                        if time.monotonic() >= next_progress:
                            import psutil
                            diagnostic = driver.state.diagnostics()
                            progress = {"at": utc(), "seconds": time.monotonic() - origin,
                                        "route": route, "bridge": diagnostic, "process": None}
                            pid = diagnostic.get("bridge_pid")
                            if isinstance(pid, int):
                                try:
                                    process = psutil.Process(pid)
                                    progress["process"] = {"pid": pid, "created_at": process.create_time(),
                                                           "rss": process.memory_info().rss,
                                                           "cpu_seconds": process.cpu_times()._asdict()}
                                except psutil.Error as error:
                                    progress["process_error"] = repr(error)
                            append(args.output_dir / "frontend-progress.jsonl", progress)
                            next_progress = time.monotonic() + 30
                        if route.get("route") == "main_menu":
                            break
                        await asyncio.sleep(1)
                    require(route.get("route") == "main_menu", "Responsive main menu was not observed")
                    opened = await call("ck3_activate_frontend_new_game_v1")
                    require(opened.get("postcondition_verified") is True, "New Game route unverified")
                    started = await call("ck3_activate_frontend_start_1066_bookmark_character_v1",
                                         {"character_name_key": checked["bookmark_candidate_from_binary"]})
                    require(started.get("postcondition_verified") is True, "Bookmark/map identity unverified")
                    return started

                async def initial_capture() -> None:
                    if checkpoint is None:
                        started = await start_fresh_campaign()
                        snapshot = await call("ck3_take_snapshot")
                    else:
                        snapshot = await wait_checkpoint_map(call=call, source=checkpoint, stopped=stopped,
                                                             timeout_seconds=2 * args.frontend_timeout)
                        started = {"schema": "war-film-managed-checkpoint-load/v1",
                            "postcondition_verified": True, "source_checkpoint": checkpoint,
                            "snapshot": snapshot, "loader": "native_session.frontend_first_load_save_name",
                            "warmup_then_load_are_separate_serial_processes": True,
                            "driver_history_copied": False, "new_game_called": False,
                            "readiness": "complete stable paused identity and later application-main pump",
                            "hud_visual_review": "pending actual image review; map_ready alone is not HUD proof"}
                    write_new(args.output_dir / "native-start-readback.json", started)
                    require(snapshot.get("map_ready") is True and snapshot.get("paused") is True, "Map is not ready and paused")
                    write_new(args.output_dir / "initial-snapshot.json", snapshot)
                    require_gui_scale_disk_gate(
                        settings_path, args.gui_scale, "postmap-before-capture",
                        args.output_dir / "gui-settings-postmap.json",
                        allow_native_ui_one=allow_native_ui_one,
                        require_native_a04_gui_block=allow_native_ui_one)
                    load = json.loads((spec.profile_dir / "dlc_load.json").read_text(encoding="utf-8"))
                    require(load == {"enabled_mods": [], "disabled_dlcs": []}, "Vanilla load profile changed")
                    from PIL import ImageGrab
                    ImageGrab.grab().save(args.output_dir / "map-start.png")
                    worker["marks"].append({"kind": "paused-map-start", "at": utc(), "seconds": time.monotonic() - origin,
                                              "snapshot_id": snapshot.get("snapshot_id"), "revision": snapshot.get("revision")})
                    await asyncio.sleep(args.hold_seconds)
                    final = await call("ck3_take_snapshot")
                    write_new(args.output_dir / "final-snapshot.json", final)
                    require_gui_scale_disk_gate(
                        settings_path, args.gui_scale, "posthold-before-service",
                        args.output_dir / "gui-settings-posthold.json",
                        allow_native_ui_one=allow_native_ui_one,
                        require_native_a04_gui_block=allow_native_ui_one)
                    ImageGrab.grab().save(args.output_dir / "map-end.png")
                    worker["marks"].append({"kind": "paused-map-end", "at": utc(), "seconds": time.monotonic() - origin,
                                              "snapshot_id": final.get("snapshot_id"), "revision": final.get("revision")})
                    worker["ok"] = True

                failed = False
                try:
                    await initial_capture()
                except Exception as error:
                    failed = True
                    record_observer_failure(worker, repr(error), supervisor_error=supervisor_error)
                    failure = {"at": utc(), "error": repr(error), "bridge": driver.diagnostics()}
                    try:
                        failure["snapshot"] = driver.take_snapshot()
                    except Exception as snapshot_error:
                        failure["snapshot_error"] = repr(snapshot_error)
                    write_new(args.output_dir / "hot-failure-state.json", failure)
                    from PIL import ImageGrab
                    ImageGrab.grab().save(args.output_dir / "hot-failure-desktop.png")
                duration = args.recovery_seconds if failed else args.interactive_seconds
                if duration > 0 and not stopped.is_set():
                    def private_phase_call(request: dict) -> dict:
                        return private_phase_trace_call(
                            request, enabled=args.enable_private_phase_trace,
                            driver=driver)

                    await service_requests(
                        args.output_dir / ("recovery-requests" if failed else "interactive-requests"),
                        call=call, stopped=stopped, seconds=duration, state_reader=driver.diagnostics,
                        private_phase_call=private_phase_call if args.enable_private_phase_trace else None,
                        private_ai_reentry_call=(lambda request: private_ai_reentry_readback(
                            request, driver=driver)) if args.enable_private_ai_reentry_observer else None,
                        gui_scale_readback=(lambda: gui_scale_disk_readback(
                            settings_path, args.gui_scale, "hot-service-after-native-UI-save",
                            allow_native_ui_one=allow_native_ui_one,
                            require_native_a04_gui_block=allow_native_ui_one))
                            if args.gui_scale is not None else None,
                    )

    def worker_main() -> None:
        try:
            asyncio.run(observe())
        except BaseException as error:
            record_observer_failure(worker, repr(error), supervisor_error=supervisor_error)
        finally:
            stopped.set()

    thread = threading.Thread(target=worker_main, daemon=True)
    supervisor_error = None
    try:
        with ExitStack() as resources:
            lease_keeper.start()
            resources.callback(lease_keeper.stop)
            lease_keeper.refresh()  # CAS immediately before any recorder or CK3 child.
            output = resources.enter_context((args.output_dir / "session.jsonl").open("x", encoding="utf-8"))
            if command is not None:
                err = resources.enter_context((args.output_dir / "ffmpeg.stderr.txt").open("xb"))
                with lease_keeper.process_create_gate():
                    with recorder_lock:
                        lease_keeper.require_live()
                        recorder = spawn_recorder(
                            command, stderr=err,
                            unsafe_marker=args.output_dir / "unsafe-ffmpeg-cleanup.json",
                            failure_receipt=args.output_dir / "ffmpeg-spawn-failure.json")
                resources.callback(finish_debug_recorder)  # LIFO: before lease_keeper.stop.
                time.sleep(1)
                require(recorder.poll() is None, "Debug recorder exited before game launch")
            thread.start()
            lease_keeper.require_live()
            before_final_launch = (
                lambda current_spec: reseed_gui_scale_after_warmup(
                    current_spec.profile_dir / "pdx_settings.txt", args.gui_scale,
                    args.output_dir, allow_native_ui_one=allow_native_ui_one)
            ) if checkpoint is not None and args.gui_scale is not None else None
            lease_keeper.refresh()  # Final CAS immediately before native_session can launch CK3.
            record_live_run_status(run, "launch-started", reason="Bounded vanilla map capture; no strategic player actions")
            args.native_session_invoked = True
            session_result = native_session(
                # Startup, map publication and post-ready pump have separate waits.
                spec, timeout_seconds=3 * args.frontend_timeout + args.hold_seconds + max(args.recovery_seconds, args.interactive_seconds) + 90,
                native_bridge=NativeBridgeLaunchConfig(mode="native-headless", pipe_name=args.pipe_name,
                                                       dll_path=args.bridge_dll, injector_path=args.bridge_injector),
                input_stream=None, output_stream=output, stop_event=stopped,
                verify_prepared_profile=False, prepared_xar_enabled="xar_off",
                frontend_first_load_save_name=CHECKPOINT_LOAD_NAME if checkpoint is not None else None,
                frontend_first_timeout_seconds=args.frontend_timeout,
                frontend_first_before_final_launch=before_final_launch,
                before_process_create=lease_keeper.process_create_gate,
            )
    except BaseException as error:
        supervisor_error = repr(error)
        worker["error"] = worker["error"] or repr(error)
    finally:
        stopped.set()
        if thread.ident is not None:
            thread.join(timeout=5)
        if supervisor_error is not None:
            prioritize_supervisor_failure(worker, supervisor_error)
        processes = ck3_process_inventory()
    write_new(args.output_dir / "session-result.json", session_result)
    write_new(args.output_dir / "observation-marks.json", worker["marks"])
    result = {
        "schema": "ck3-native-war-ai-raw-capture/v1", "run_id": run.run_id,
        "finished_at": utc(), "ck3_launch_attempted": args.native_session_invoked,
        "worker": worker, "cleanup_process_inventory": processes,
        "recorder_returncode": recorder.returncode if recorder is not None else None,
        "recorder_tree": recorder_cleanup,
        "raw_video": identity(raw) if args.record_debug_desktop and raw.is_file() else None,
        "record_debug_desktop": args.record_debug_desktop,
        "recording_complete": False,
        "clean_spans": [], "adapter_bundle_validated": False,
        "native_ai_causality_proven": False, "human_1x_review_performed": False,
        "classification": ("debug-desktop-including-startup-not-clean-gameplay" if args.record_debug_desktop
                           else "paused-vanilla-map-environment-session-no-video"),
        "launch_mode": checked["launch_mode"],
        "checkpoint_source": checkpoint,
        "screen_lease": lease_keeper.report(),
    }
    probe = None
    if args.record_debug_desktop and raw.is_file() and raw.stat().st_size > 0:
        probe = subprocess.run([args.ffprobe, "-v", "error", "-show_format", "-show_streams",
                                "-of", "json", str(raw)], capture_output=True, text=True)
        write_new(args.output_dir / "ffprobe.json", {
            "returncode": probe.returncode, "stdout": probe.stdout, "stderr": probe.stderr,
        })
    result["ffprobe_returncode"] = probe.returncode if probe is not None else None
    shutdown = session_result.get("shutdown") or {}
    session_good = (worker["ok"] and worker["error"] is None and not thread.is_alive()
            and lease_keeper.failure is None
            and session_result.get("ok") is True and shutdown.get("cleanup_proven") is True
            and not processes["processes"])
    recording_good = (args.record_debug_desktop and recorder is not None and recorder.returncode == 0
            and recorder_cleanup is not None and recorder_cleanup.get("state") == "NORMAL_TREE_EMPTY"
            and raw.is_file() and raw.stat().st_size > 0 and probe is not None and probe.returncode == 0)
    result["recording_complete"] = recording_good
    result["environment_session_complete"] = session_good
    result["result"] = session_outcome(session_ok=session_good,
        debug_recording_enabled=args.record_debug_desktop, recording_ok=recording_good)
    good = result["result"] != "RED"
    record_live_run_status(run, "completed-green" if good else "completed-red",
                           reason=("Environment session and cleanup only; no video recorded" if not args.record_debug_desktop else
                                   "Debug raw capture and cleanup only; no clean gameplay, AI-causality or human signoff claim")
                           if good else str(worker["error"]))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-dir", type=Path, required=True)
    parser.add_argument("--bridge-dll", type=Path, required=True)
    parser.add_argument("--bridge-injector", type=Path, required=True)
    parser.add_argument("--battle-control-pair-manifest", type=Path,
                        help="Required for exact d11 checkpoint: fresh native/Python source pair and CTest evidence")
    parser.add_argument("--d11-admission-lock", type=Path,
                        help="Exact external no-launch byte seal; required before a d11 --capture launch")
    parser.add_argument("--state-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--pipe-name", required=True)
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--ffprobe", default="ffprobe")
    parser.add_argument("--record-debug-desktop", action="store_true",
                        help="Opt in to a separate startup/debug desktop recorder; default off to avoid parallel gameplay recording")
    parser.add_argument("--checkpoint-save", type=Path, help="Exact .ck3 source copied into a new isolated vanilla profile")
    parser.add_argument("--checkpoint-receipt", type=Path, help="Actual MCP save-checkpoint response with byte, actor/date and build evidence")
    parser.add_argument("--frontend-timeout", type=float, default=360,
                        help="Per frontend readiness wait; checkpoint map wait is twice this value")
    parser.add_argument("--gui-scale", choices=("1.0",),
                        help="Set only this new isolated capture profile's CK3 GUI scale before launch")
    parser.add_argument("--import-a04-ui-gui-100", action="store_true",
                        help="Explicit source-bound opt-in: import only the reviewed a04 UI-saved GUI block into a new profile")
    parser.add_argument("--a04-ui-settings-snapshot", type=Path,
                        help="Frozen full a04 UI SaveAndClose settings copy; project SHA is fixed in this adapter")
    parser.add_argument("--a04-ui-preservation-receipt", type=Path,
                        help="Frozen a04 UI screenshot and hot-readback preservation receipt; project SHA is fixed")
    parser.add_argument("--hold-seconds", type=float, default=60)
    parser.add_argument("--shader-cache-source", type=Path, help="Reuse only a prior exact-build shadercache")
    parser.add_argument("--recovery-seconds", type=float, default=1800, help="Keep the same MCP owner available after Python failure")
    parser.add_argument("--interactive-seconds", type=float, default=1800,
                        help="Keep the loaded campaign available for explicit MCP requests; use 3600 for a bounded one-hour work session")
    parser.add_argument("--steam-offline-receipt", type=Path)
    parser.add_argument("--screen-task-id", help="Existing unique ck3-screen task ID; required for --capture")
    parser.add_argument("--screen-expected-sequence", type=int,
                        help="Fresh task.last_sequence from the reviewed screen registration")
    parser.add_argument("--screen-cli-sha256",
                        help="Uppercase SHA-256 of identical source and installed CAS bus CLI")
    parser.add_argument("--enable-private-phase-trace", action="store_true",
                        help="Allow only the research BEGIN/FINISH trace pair in explicit local requests")
    parser.add_argument("--enable-private-ai-reentry-observer", action="store_true",
                        help="Allow only the fixed passive AI winner dispatch readback through the owner driver")
    parser.add_argument("--private-ai-reentry-dll-sha256",
                        help="Expected SHA-256 of the explicit private observer DLL")
    parser.add_argument("--capture", action="store_true", help="Explicitly launch CK3 after preflight; default is no launch")
    args = parser.parse_args()
    args.native_session_invoked = False
    require(30 <= args.hold_seconds <= 90, "Hold must be 30..90 seconds")
    require(30 <= args.frontend_timeout <= 1500, "Frontend timeout must be 30..1500 seconds")
    require(0 <= args.recovery_seconds <= 3600 and 0 <= args.interactive_seconds <= 3600, "Hot service must be 0..3600 seconds")
    require(not args.enable_private_ai_reentry_observer or
            (isinstance(args.private_ai_reentry_dll_sha256, str)
             and len(args.private_ai_reentry_dll_sha256) == 64
             and all(character in "0123456789abcdefABCDEF"
                     for character in args.private_ai_reentry_dll_sha256)),
            "Private AI reentry needs an explicit 64-digit DLL SHA-256")
    require(args.enable_private_ai_reentry_observer or
            args.private_ai_reentry_dll_sha256 is None,
            "Private AI reentry DLL SHA-256 requires the private opt-in")
    args.output_dir.mkdir(parents=True, exist_ok=False)
    write_new(args.output_dir / "command.json", {"python": sys.executable, "argv": sys.argv, "started_at": utc()})
    try:
        if args.capture:
            # This precedes CAS subprocesses, observer threads and optional
            # FFmpeg. The current injector cannot prove descendant cleanup.
            require_native_bridge_tree_proof()
            require(args.screen_task_id is not None and
                    args.screen_expected_sequence is not None and
                    args.screen_cli_sha256 is not None,
                    "--capture requires screen task ID, expected sequence and CLI SHA-256")
            checked_cli_pair(ROOT / "tools" / "codex_task_bus.py",
                             Path("D:/workspace/.codex-task-bus/bin/codex_task_bus.py"),
                             args.screen_cli_sha256)
        checked = preflight(args)
        write_new(args.output_dir / "preflight.json", checked)
        if not args.capture:
            print(json.dumps(checked, ensure_ascii=False))
            return 0
        screen_lease = renew_once(
            source=ROOT / "tools" / "codex_task_bus.py",
            bus_dir=Path("D:/workspace/.codex-task-bus"),
            expected_sha=args.screen_cli_sha256,
            task_id=args.screen_task_id,
            expected_sequence=args.screen_expected_sequence,
            repo=ROOT,
            audit_dir=args.output_dir / "screen-bus-commands",
        )
        write_new(args.output_dir / "screen-lease-admission.json", screen_lease)
        result = capture(args, checked, screen_lease)
        write_new(args.output_dir / "capture-report.json", result)
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result["result"] != "RED" else 1
    except Exception as error:
        failure = {"result": "RED", "error": repr(error),
                   "ck3_started_by_preflight": False,
                   "native_session_invoked": args.native_session_invoked,
                   "ck3_process_created": "unknown" if args.native_session_invoked else False,
                   "at": utc()}
        write_new(args.output_dir / "entry-failure.json", failure)
        print(json.dumps(failure))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
