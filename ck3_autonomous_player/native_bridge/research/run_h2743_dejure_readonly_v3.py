"""Exact H2743 defender de-jure baseline read; never submits a war action.

The default and --check-static modes do not create an attempt or start CK3.
--seal-no-launch creates a static-only v5 attempt without a child process or
ck3-screen lease. It is not a prepared state. --prepare-live-profile requires
a separately acquired screen lease to consume that seal. --run requires the
prepared state, human-reviewed fresh Steam offline evidence, and the lease.
The current-HEAD v5 live modes are hard-stopped until the shared task bus uses
pinned source/installed hashes and expected-sequence lease operations.
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import queue
import shutil
import subprocess
import sys
import threading
import time


REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "ck3_autonomous_player" / "src"))
BASE_ROOT = Path("D:/ck3-research-artifacts/war31-h2743-20260928")
ROOT = BASE_ROOT
SOURCE = ROOT / "source-verified-01"
PYTHON = Path("D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe")
GAME = Path("C:/SteamLibrary/steamapps/common/Crusader Kings III")
EXE = GAME / "binaries/ck3.exe"
DLL = ROOT / "build-title-prestate-001/xar_ck3_bridge.dll"
BASE_INJECTOR = Path("D:/ck3-research-artifacts/war31-live-20260927/source-verified-01/R0221-original-bridge/native/xar_ck3_bridge_injector.exe")
INJECTOR = BASE_INJECTOR
TASK_BUS = Path("D:/workspace/.codex-task-bus/bin/codex_task_bus.py")
PIPE = r"\\.\pipe\xar-g2-robert-1066-seed-66f926d"
EPISODE = "native-29829-2bc2d599f7f9"
QUERY = "query-defender-de-jure-exit-terms-v1-16777231"
BASE_QUERY = QUERY
OPTIONS_QUERY = "query-war-termination-options-16777231"
CLI_ENTRY = (f"import sys; sys.path.insert(0, r'{REPO / 'ck3_autonomous_player/src'}'); "
             "from xar_autoplayer.cli import main; raise SystemExit(main(sys.argv[1:]))")
MCP_ENTRY = (f"import sys; sys.path.insert(0, r'{REPO / 'ck3_autonomous_player/src'}'); "
             "from xar_autoplayer.bridge.mcp_server import main; raise SystemExit(main())")
SOURCE_HASHES = {
    "xar_checkpoint.ck3": "A5012030DA500A4352EF79D1EA10269D45DD5D19DAC508E22DD835663A5106E9",
    "driver-state.json": "F31460BAA126BAED289CBA20A6FEFF59AAF6EF87BA3B29943C892236B6D15069",
    "first-heir-marriage-formal-v1.json": "12D7B2B006E409DB69F7F442107B01B5D38D8C589A7F494B24519094024B5724",
    "xar_ck3_bridge.dll": "8C3A9523D14DEDB6C44AC04F748BFC9D086E983B2A973A956CBADD21F07A8A5C",
}
DLL_SHA = "6689ED3B3EB40F33157B028BD7067FF859F1C6ACDCFC02EDEB92A7D0F271B17E"
TRUCE_DLL = ROOT / "build-truce-inputs-002/xar_ck3_bridge.dll"
TRUCE_DLL_SHA = "1361FC0991D1FA09CB7272112D73F7F50736B7BBAD6A3656C33F9FB200CA1BAA"
STORAGE_DLL = ROOT / "build-war-storage-candidate-002/xar_ck3_bridge.dll"
STORAGE_DLL_SHA = "19C53611AEA499A37CF222A48A5395EC7B5BBA306ABC6065AB73C097CC85FB2B"
DEFAULT_CANDIDATE = "title-prestate-v3"
TRUCE_CANDIDATE = "partial-truce-inputs-v4"
STORAGE_CANDIDATE = "war-storage-candidate-v5"
HEAD_STORAGE_CANDIDATE = "war-storage-candidate-v5-head24c51"
HEAD_STORAGE_HEAD = "24c51a37d2facd2dcf24da2d54e5f0c4548833cb"
HEAD_STORAGE_BUILD_ROOT = Path("D:/ck3-research-artifacts/h2743-v5-build-20260930")
HEAD_STORAGE_DLL_ATTEMPT = HEAD_STORAGE_BUILD_ROOT / "attempt-03-head24c51"
HEAD_STORAGE_INJECTOR_ATTEMPT = HEAD_STORAGE_BUILD_ROOT / "attempt-04-injector-head24c51"
HEAD_STORAGE_DLL = HEAD_STORAGE_DLL_ATTEMPT / "build/xar_ck3_bridge.dll"
HEAD_STORAGE_DLL_SHA = "A73EBA509729D64E5DBC453791E48BEF8CF2DBCAE95C4F0BA2AA73D958B1C5EF"
HEAD_STORAGE_INJECTOR = HEAD_STORAGE_INJECTOR_ATTEMPT / "build/xar_ck3_bridge_injector.exe"
HEAD_STORAGE_INJECTOR_SHA = "3E9339B4C96A77AD96C8566D6707387DEBBB1C3E044B323DF2E0AD479F16A595"
HEAD_STORAGE_PAIR = HEAD_STORAGE_BUILD_ROOT / "pair-proposal-head24c51-unreviewed.json"
HEAD_STORAGE_PAIR_SHA = "183BF62461AE3C2B382F9367C657C923D5D412883ADE45FA7F24B7E31BC0E42C"
HEAD_STORAGE_SOURCE_MANIFEST_SHA = "3CC643CD3F73B63AC576361C5E99B34592F83B4DB0AE9875D4061325AB6611B3"
HEAD_STORAGE_DLL_RESULT_SHA = "8F2434DAF4801C26E43676A8BA98F913A0F50D86279CEACE19D9B58B436575F6"
HEAD_STORAGE_DLL_POSTCHECK_SHA = "B447421DC3A50A2F32E807463C1C197F39E5A258F8367F106CBF96183DD0DD30"
HEAD_STORAGE_INJECTOR_RESULT_SHA = "82A3A36B36AF1F0BE62564652A8555CADF6A4D3BDE27B687EC8451BB0309EC62"
HEAD_STORAGE_INJECTOR_POSTCHECK_SHA = "59175C992DD5C0A329454758444D9E278BFE323B5869EE686704C6DB54DBBB87"
EXISTING_TRUCE_CANDIDATE = "preaction-existing-truce-v1"
EXISTING_TRUCE_ROOT = Path("D:/ck3-research-artifacts/h2743-existing-truce-readonly-20260929")
EXISTING_TRUCE_BUILD = Path("D:/ck3-research-artifacts/h2743-existing-truce-release-20260930-attempt07/build")
EXISTING_TRUCE_DLL_SHA = "1176F8E531531285BE8EDAC258724A28B0CAF70B6FEDD21AA68AE75E0378A64D"
EXISTING_TRUCE_INJECTOR_SHA = "5F70ADED213D1A583C2DF9D880E4CEA1A30FC18A8E6C8CBA9C7B8ADB1FC07BBA"
EXISTING_TRUCE_MANIFEST = EXISTING_TRUCE_BUILD.parent / "candidate-manifest.json"
EXISTING_TRUCE_MANIFEST_SHA = "A768F6005E6E53D8CF89F2E2E99DA1AAC005A20BF3EA3AB79C627F91C5760689"
CANDIDATE = DEFAULT_CANDIDATE
LIVE_OUTPUT = "live-dejure-readonly-v3"
INJECTOR_SHA = "C89F1A919514A7E664AEE8FAF165B78C693ABA4EA2105289BDA2DB4BAC6A84FF"
BASE_INJECTOR_SHA = INJECTOR_SHA
EXE_SHA = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
WAR_VALUES = GAME / "game/common/script_values/00_war_values.txt"
WAR_VALUES_SHA = "ED1CDB6E8BC887CF1FFFE010F1E9CA642DFD6DAF241E81F23E6B4736F7AFDF3B"
READINESS_SECONDS = 1800
SESSION_SECONDS = 3000
FRAME_SECONDS = 1800
TOOL_SECONDS = 120
# The checked-in CLI can take over 30 seconds to import on the shared host.
# Keep this a bounded no-launch probe rather than treating a slow import as a
# source-identity failure.
STATIC_HELP_SECONDS = 90


def python_source_hashes() -> dict[str, str]:
    return {
        "runner": sha256(Path(__file__).resolve()),
        "native_driver": sha256(REPO / "ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py"),
        "existing_truce_contract": sha256(
            REPO / "ck3_autonomous_player/src/xar_autoplayer/bridge/h2743_preaction_existing_truce_v1.py"
        ),
    }


def select_candidate(name: str) -> None:
    """Bind a single exact DLL for this process before any attempt is prepared."""
    global CANDIDATE, ROOT, DLL, DLL_SHA, INJECTOR, INJECTOR_SHA, LIVE_OUTPUT, QUERY
    if name == DEFAULT_CANDIDATE:
        CANDIDATE = DEFAULT_CANDIDATE
        ROOT = BASE_ROOT
        INJECTOR = BASE_INJECTOR
        INJECTOR_SHA = BASE_INJECTOR_SHA
        QUERY = BASE_QUERY
        DLL = ROOT / "build-title-prestate-001/xar_ck3_bridge.dll"
        DLL_SHA = "6689ED3B3EB40F33157B028BD7067FF859F1C6ACDCFC02EDEB92A7D0F271B17E"
        LIVE_OUTPUT = "live-dejure-readonly-v3"
    elif name == TRUCE_CANDIDATE:
        CANDIDATE = TRUCE_CANDIDATE
        ROOT = BASE_ROOT
        INJECTOR = BASE_INJECTOR
        INJECTOR_SHA = BASE_INJECTOR_SHA
        QUERY = BASE_QUERY
        DLL = TRUCE_DLL
        DLL_SHA = TRUCE_DLL_SHA
        LIVE_OUTPUT = "live-dejure-partial-truce-v4"
    elif name == STORAGE_CANDIDATE:
        CANDIDATE = STORAGE_CANDIDATE
        ROOT = BASE_ROOT
        INJECTOR = BASE_INJECTOR
        INJECTOR_SHA = BASE_INJECTOR_SHA
        QUERY = BASE_QUERY
        DLL = STORAGE_DLL
        DLL_SHA = STORAGE_DLL_SHA
        LIVE_OUTPUT = "live-dejure-war-storage-v5"
    elif name == HEAD_STORAGE_CANDIDATE:
        CANDIDATE = HEAD_STORAGE_CANDIDATE
        ROOT = BASE_ROOT
        INJECTOR = HEAD_STORAGE_INJECTOR
        INJECTOR_SHA = HEAD_STORAGE_INJECTOR_SHA
        QUERY = BASE_QUERY
        DLL = HEAD_STORAGE_DLL
        DLL_SHA = HEAD_STORAGE_DLL_SHA
        LIVE_OUTPUT = "live-dejure-war-storage-v5-head24c51"
    elif name == EXISTING_TRUCE_CANDIDATE:
        CANDIDATE = EXISTING_TRUCE_CANDIDATE
        ROOT = EXISTING_TRUCE_ROOT
        DLL = EXISTING_TRUCE_BUILD / "xar_ck3_bridge.dll"
        DLL_SHA = EXISTING_TRUCE_DLL_SHA
        INJECTOR = EXISTING_TRUCE_BUILD / "xar_ck3_bridge_injector.exe"
        INJECTOR_SHA = EXISTING_TRUCE_INJECTOR_SHA
        QUERY = "query-h2743-preaction-existing-truce-v1"
        LIVE_OUTPUT = "live-preaction-existing-truce-v1"
    else:
        raise ValueError("unknown exact H2743 candidate")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def write_new(path: Path, value: object) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def valid_attempt_name(name: str) -> bool:
    prefix, suffix = "attempt-", "-dejure-baseline-no-launch"
    if not name.startswith(prefix) or not name.endswith(suffix):
        return False
    number = name[len(prefix):-len(suffix)]
    return bool(number) and number.isascii() and number.isdecimal() and not number.startswith("0")


def is_storage_candidate() -> bool:
    return CANDIDATE in (STORAGE_CANDIDATE, HEAD_STORAGE_CANDIDATE)


def candidate_manifest_sha256() -> str | None:
    if CANDIDATE == EXISTING_TRUCE_CANDIDATE:
        return EXISTING_TRUCE_MANIFEST_SHA
    if CANDIDATE == HEAD_STORAGE_CANDIDATE:
        return HEAD_STORAGE_PAIR_SHA
    return None


def provenance_source_hashes() -> dict[str, str] | None:
    if CANDIDATE in (EXISTING_TRUCE_CANDIDATE, HEAD_STORAGE_CANDIDATE):
        return python_source_hashes()
    return None


def pinned_json(path: Path, digest: str) -> dict[str, object]:
    if not path.is_file() or sha256(path) != digest:
        raise RuntimeError(f"exact H2743 provenance byte identity missing: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"H2743 provenance object malformed: {path}")
    return value


def verify_head_storage_pair() -> None:
    """Bind the new v5 pair to one frozen HEAD, source tree and toolchain."""
    pair = pinned_json(HEAD_STORAGE_PAIR, HEAD_STORAGE_PAIR_SHA)
    expected_sources = {
        name: {"path": str(SOURCE / name), "sha256": digest}
        for name, digest in SOURCE_HASHES.items()
    }
    if (pair.get("schema") != "xar.ck3.h2743.v5.current-head-static-pair-proposal.v1"
            or pair.get("status") != "UNREVIEWED_NO_LAUNCH_PAIR_PROPOSAL"
            or pair.get("candidate_identity_proposed") != HEAD_STORAGE_CANDIDATE
            or pair.get("head") != HEAD_STORAGE_HEAD
            or pair.get("source_quartet") != expected_sources
            or pair.get("shared_native_source_manifest_sha256") != HEAD_STORAGE_SOURCE_MANIFEST_SHA
            or pair.get("shared_toolchain_binaries_equal") is not True
            or pair.get("shared_selected_environment_equal") is not True
            or pair.get("candidate_macro") !=
            "XAR_CK3_ENABLE_H2743_PREACTION_EXISTING_TRUCE_CANDIDATE_V1=OFF"
            or pair.get("old_v5_attempt15_pair_preserved") is not True
            or pair.get("runner_modified") is not False
            or pair.get("official_no_launch_performed") is not False
            or pair.get("ck3_launched") is not False
            or pair.get("go_executed") is not False
            or pair.get("native_condition_observed") is not False
            or pair.get("stock_any_character_war_equivalence_proven") is not False):
        raise RuntimeError("new H2743 v5 pair proposal identity or boundary changed")

    expected = (
        ("dll", HEAD_STORAGE_DLL_ATTEMPT, HEAD_STORAGE_DLL, HEAD_STORAGE_DLL_SHA,
         HEAD_STORAGE_DLL_RESULT_SHA, HEAD_STORAGE_DLL_POSTCHECK_SHA,
         "GREEN_NO_LAUNCH_BUILD_AND_CTEST", "new_dll_sha256", "dll_path",
         ["xar_ck3_bridge", "xar_ck3_h2743_war_storage_candidate_v1_test"]),
        ("injector", HEAD_STORAGE_INJECTOR_ATTEMPT, HEAD_STORAGE_INJECTOR,
         HEAD_STORAGE_INJECTOR_SHA, HEAD_STORAGE_INJECTOR_RESULT_SHA,
         HEAD_STORAGE_INJECTOR_POSTCHECK_SHA, "GREEN_NO_LAUNCH_INJECTOR_BUILD",
         "new_injector_sha256", "injector_path", ["xar_ck3_bridge_injector"]),
    )
    toolchains = []
    for (kind, attempt, binary, binary_sha, result_sha, postcheck_sha,
         status, result_key, path_key, targets) in expected:
        if pair.get(kind) != {
            "path": str(binary), "sha256": binary_sha,
            "build_result": str(attempt / "result.json"),
            "build_result_sha256": result_sha,
            "postcheck": str(attempt / "postcheck.json"),
            "postcheck_sha256": postcheck_sha,
        }:
            raise RuntimeError(f"new H2743 {kind} pair entry changed")
        if not binary.is_file() or sha256(binary) != binary_sha:
            raise RuntimeError(f"new H2743 {kind} binary bytes changed")
        result = pinned_json(attempt / "result.json", result_sha)
        postcheck = pinned_json(attempt / "postcheck.json", postcheck_sha)
        if (result.get("status") != status
                or result.get("head") != HEAD_STORAGE_HEAD
                or result.get("source_inputs_unchanged") is not True
                or result.get(result_key) != binary_sha
                or result.get(path_key) != str(binary)
                or result.get("game_launched") is not False
                or result.get("go_executed") is not False
                or postcheck.get("head") != HEAD_STORAGE_HEAD
                or postcheck.get("clean") is not True
                or postcheck.get("source_rows_before") != 1564
                or postcheck.get("source_rows_after") != 1564
                or postcheck.get("source_file_lists_equal") is not True
                or postcheck.get(result_key) != binary_sha
                or postcheck.get("result_sha256") != result_sha
                or postcheck.get("source_before_sha256") != HEAD_STORAGE_SOURCE_MANIFEST_SHA
                or postcheck.get("source_after_sha256") != HEAD_STORAGE_SOURCE_MANIFEST_SHA
                or postcheck.get("tasklist_watch_matches") != []
                or postcheck.get("psutil_watch_matches") != []):
            raise RuntimeError(f"new H2743 {kind} build or postcheck changed")
        for name in ("source-native-tracked-before.json", "source-native-tracked-after.json"):
            if sha256(attempt / name) != HEAD_STORAGE_SOURCE_MANIFEST_SHA:
                raise RuntimeError(f"new H2743 {kind} source manifest changed")
        if sha256(attempt / "actual-dependencies.json") != postcheck.get("deps_sha256"):
            raise RuntimeError(f"new H2743 {kind} dependency evidence changed")
        toolchains.append(pinned_json(attempt / "toolchain.json", postcheck["toolchain_sha256"]))
        configured = json.loads((attempt / "configured-inputs.json").read_text(encoding="utf-8"))
        if (configured.get("macro") !=
                "XAR_CK3_ENABLE_H2743_PREACTION_EXISTING_TRUCE_CANDIDATE_V1=OFF"
                or sha256(attempt / "build/CMakeCache.txt") != configured.get("cmake_cache_sha256")
                or "XAR_CK3_ENABLE_H2743_PREACTION_EXISTING_TRUCE_CANDIDATE_V1:BOOL=OFF"
                not in (attempt / "build/CMakeCache.txt").read_text(encoding="utf-8")):
            raise RuntimeError(f"new H2743 {kind} configuration changed")
        argv = json.loads((attempt / "build-argv.json").read_text(encoding="utf-8"))
        if argv[3:] != ["--target", *targets, "--parallel", "2"]:
            raise RuntimeError(f"new H2743 {kind} build target scope changed")
        if (json.loads((attempt / "configure-result.json").read_text(encoding="utf-8")).get("exit_code") != 0
                or json.loads((attempt / "build-result.json").read_text(encoding="utf-8")).get("exit_code") != 0):
            raise RuntimeError(f"new H2743 {kind} build phase failed")
    if (toolchains[0].get("binaries") != toolchains[1].get("binaries")
            or toolchains[0].get("selected_environment") != toolchains[1].get("selected_environment")):
        raise RuntimeError("new H2743 v5 pair toolchains differ")
    ctest = json.loads((HEAD_STORAGE_DLL_ATTEMPT / "ctest-result.json").read_text(encoding="utf-8"))
    if (ctest.get("exit_code") != 0
            or "100% tests passed, 0 tests failed out of 1" not in
            (HEAD_STORAGE_DLL_ATTEMPT / "ctest-stdout.txt").read_text(encoding="utf-8")):
        raise RuntimeError("new H2743 v5 DLL focused CTest failed")


def check_static(*, static_only: bool = False) -> dict[str, object]:
    expected = {SOURCE / name: digest for name, digest in SOURCE_HASHES.items()}
    expected.update({DLL: DLL_SHA, INJECTOR: INJECTOR_SHA, EXE: EXE_SHA,
                     WAR_VALUES: WAR_VALUES_SHA})
    for path, digest in expected.items():
        if not path.is_file() or sha256(path) != digest:
            raise RuntimeError(f"exact byte identity missing or changed: {path}")
    if CANDIDATE == EXISTING_TRUCE_CANDIDATE:
        if (not EXISTING_TRUCE_MANIFEST.is_file()
                or sha256(EXISTING_TRUCE_MANIFEST) != EXISTING_TRUCE_MANIFEST_SHA):
            raise RuntimeError("exact H2743 candidate build manifest missing or changed")
        build = json.loads(EXISTING_TRUCE_MANIFEST.read_text(encoding="utf-8"))
        if (build.get("head") != "a6974801602c55cdc821cc7636ddeef60b525e4a"
                or build.get("configuration") != "Release"
                or build.get("candidate_option") !=
                "XAR_CK3_ENABLE_H2743_PREACTION_EXISTING_TRUCE_CANDIDATE_V1=ON"
                or build.get("dll", {}).get("sha256") != DLL_SHA
                or build.get("injector", {}).get("sha256") != INJECTOR_SHA
                or build.get("ck3_exe_sha256") != EXE_SHA):
            raise RuntimeError("H2743 candidate build manifest content differs")
    if CANDIDATE == HEAD_STORAGE_CANDIDATE:
        verify_head_storage_pair()
    required_tools = [PYTHON, REPO / "ck3_autonomous_player/src/xar_autoplayer/cli.py",
                      REPO / "ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py"]
    if not static_only:
        required_tools.append(TASK_BUS)
    for path in required_tools:
        if not path.is_file():
            raise RuntimeError(f"required local tool missing: {path}")
    if {item.name for item in SOURCE.iterdir() if item.name != "transfer-receipt.json"} != set(SOURCE_HASHES):
        raise RuntimeError("H2743 source set is no longer the exact four files")
    if not static_only:
        for module in ("mcp", "psutil"):
            if importlib.util.find_spec(module) is None:
                raise RuntimeError(f"selected interpreter lacks required dependency: {module}")
        import psutil
        own_maps = psutil.Process().memory_maps(grouped=False)
        if not own_maps or not any(getattr(item, "path", None) for item in own_maps):
            raise RuntimeError("selected interpreter cannot read its own process module map")
        for entry, help_args in ((CLI_ENTRY, ["--help"]),
                                 (CLI_ENTRY, ["native-session", "--help"]),
                                 (MCP_ENTRY, ["--help"])):
            probe = subprocess.run([str(PYTHON), "-c", entry, *help_args], cwd=REPO,
                                   capture_output=True, text=True, encoding="utf-8",
                                   timeout=STATIC_HELP_SECONDS)
            if probe.returncode != 0 or "usage:" not in probe.stdout.lower():
                raise RuntimeError(f"branch CLI help probe failed: {help_args}")
    return {"status": "static_bytes_verified_no_launch", "candidate_kind": CANDIDATE,
            "readiness_seconds": READINESS_SECONDS,
            "session_timeout_seconds": SESSION_SECONDS, "paths_sha256": {str(path): digest for path, digest in expected.items()},
            "allowed_query_steps": [QUERY, OPTIONS_QUERY],
            "python_source_sha256": provenance_source_hashes(),
            "candidate_build_manifest_sha256": candidate_manifest_sha256(),
            "process_module_map_probe": "not_run_static_only" if static_only else "self_readable",
            "cli_help_probes": "not_run_static_only" if static_only else "passed",
            "task_bus_file_checked": not static_only,
            "gameplay_action_submitted": False}


def screen_lease(task_id: str) -> None:
    if CANDIDATE == HEAD_STORAGE_CANDIDATE:
        raise RuntimeError("LIVE_STOP_CAS_MIGRATION_PENDING: current-HEAD v5 cannot "
                           "use legacy list/stale screen ownership")
    listed = subprocess.run([str(PYTHON), str(TASK_BUS), "list"], capture_output=True,
                            timeout=15, check=True)
    # Older task summaries can contain legacy local-codepage bytes. The bus
    # control keys and task IDs are ASCII; decode malformed summary text only
    # for routing, without letting a reader-thread Unicode error hide owners.
    bus = json.loads(listed.stdout.decode("utf-8-sig", errors="replace"))
    if bus.get("ok") is not True or not isinstance(bus.get("tasks"), list):
        raise RuntimeError("task bus unavailable")
    owners = [row.get("task_id") for row in bus["tasks"]
              if row.get("state") == "running" and "ck3-screen:acquired" in row.get("resources", [])
              and not row.get("stale", False)]
    if owners != [task_id]:
        raise RuntimeError(f"exclusive live CK3 screen lease absent: {owners}")


def renew_screen_lease(task_id: str) -> None:
    """Keep the exclusive screen lease fresh during a long CK3 cold start."""
    if CANDIDATE == HEAD_STORAGE_CANDIDATE:
        raise RuntimeError("LIVE_STOP_CAS_MIGRATION_PENDING: current-HEAD v5 cannot "
                           "use bare task-bus heartbeat")
    screen_lease(task_id)
    heartbeat = subprocess.run(
        [str(PYTHON), str(TASK_BUS), "heartbeat", "--task", task_id],
        capture_output=True, timeout=15, check=True,
    )
    receipt = json.loads(heartbeat.stdout.decode("utf-8-sig", errors="replace"))
    task = receipt.get("task")
    if (receipt.get("ok") is not True or not isinstance(task, dict)
            or task.get("task_id") != task_id or task.get("state") != "running"
            or "ck3-screen:acquired" not in task.get("resources", [])):
        raise RuntimeError("screen lease heartbeat did not preserve the running owner")
    screen_lease(task_id)


def live_gate(task_id: str, steam_gate_path: Path) -> dict[str, object]:
    gate = json.loads(steam_gate_path.read_text(encoding="utf-8"))
    if set(gate) != {"schema", "task_id", "reviewer", "reviewed_at_utc", "screenshot_path",
                     "screenshot_sha256", "fresh_frame_receipt_path", "steam_offline_visible"}:
        raise RuntimeError("fresh Steam gate schema mismatch")
    if (gate["schema"] != "xar.ck3.h2743.steam-offline-human-gate.v3"
            or gate["task_id"] != task_id or not gate["reviewer"]
            or gate["steam_offline_visible"] is not True):
        raise RuntimeError("fresh Steam offline human review missing")
    reviewed = datetime.fromisoformat(gate["reviewed_at_utc"].replace("Z", "+00:00"))
    age = (utc_now() - reviewed).total_seconds()
    if reviewed.tzinfo is None or not 0 <= age <= 600:
        raise RuntimeError("Steam offline review is not fresh")
    image = Path(gate["screenshot_path"])
    receipt = Path(gate["fresh_frame_receipt_path"])
    if not image.is_file() or sha256(image) != gate["screenshot_sha256"] or not receipt.is_file():
        raise RuntimeError("fresh Steam image or freshness receipt missing/changed")
    frame = json.loads(receipt.read_text(encoding="utf-8"))
    captured = datetime.fromisoformat(frame["captured_at_utc"].replace("Z", "+00:00"))
    if (frame.get("schema") != "ck3.steam_fresh_desktop_frame.v1"
            or frame.get("moving_edge_changed") is not True
            or Path(frame.get("moved_path", "")) != image
            or frame.get("moved_sha256", "").upper() != sha256(image)
            or captured.tzinfo is None or not 0 <= (reviewed - captured).total_seconds() <= 600):
        raise RuntimeError("Steam screenshot is not bound to a fresh moved-frame receipt")
    screen_lease(task_id)
    return {"steam_gate_path": str(steam_gate_path), "steam_gate_sha256": sha256(steam_gate_path),
            "fresh_frame_receipt_sha256": sha256(receipt), "task_id": task_id}


def prepared_state(attempt: Path) -> tuple[Path, dict[str, object]]:
    if attempt.resolve().parent != ROOT.resolve() or not valid_attempt_name(attempt.name):
        raise RuntimeError("prepared attempt is not a fresh named H2743 child directory")
    state = attempt / "state"
    ready = json.loads((attempt / "ready-summary.json").read_text(encoding="utf-8"))
    if (ready.get("status") != "no_launch_preflight_ready"
            or ready.get("candidate_kind", DEFAULT_CANDIDATE) != CANDIDATE
            or ready.get("source_hashes") != SOURCE_HASHES
            or ready.get("candidate_dll_sha256") != DLL_SHA
            or ready.get("injector_sha256") != INJECTOR_SHA
            or ready.get("ck3_launch_attempted") is not False
            or ready.get("gameplay_action_submitted") is not False):
        raise RuntimeError("new exact H2743 no-launch preflight READY absent")
    if any(ready.get(phase, {}).get("exit_code") != 0 for phase in ("prepare", "rebind", "preflight")):
        raise RuntimeError("new exact H2743 no-launch preflight phase failed")
    pair = json.loads((attempt / "source-pair.json").read_text(encoding="utf-8"))
    if (pair.get("candidate_kind", DEFAULT_CANDIDATE) != CANDIDATE
            or pair.get("candidate_dll") != str(DLL)
            or pair.get("candidate_dll_sha256") != DLL_SHA
            or pair.get("source_hashes") != SOURCE_HASHES
            or pair.get("ck3_launch_attempted") is not False
            or pair.get("gameplay_action_submitted") is not False):
        raise RuntimeError("prepared H2743 source pair belongs to another candidate")
    if CANDIDATE in (EXISTING_TRUCE_CANDIDATE, HEAD_STORAGE_CANDIDATE):
        if (pair.get("python_source_sha256") != python_source_hashes()
                or pair.get("candidate_build_manifest_sha256") != candidate_manifest_sha256()
                or ready.get("python_source_sha256") != python_source_hashes()):
            raise RuntimeError("prepared H2743 Python source or build manifest changed")
        if (CANDIDATE == HEAD_STORAGE_CANDIDATE
                and ready.get("candidate_build_manifest_sha256") != HEAD_STORAGE_PAIR_SHA):
            raise RuntimeError("prepared H2743 v5 HEAD pair manifest changed")
    placed = {"xar_checkpoint.ck3": state / "profile/save games/xar_checkpoint.ck3",
              "first-heir-marriage-formal-v1.json": state / "first-heir-marriage-formal-v1.json"}
    for name, path in placed.items():
        if sha256(path) != SOURCE_HASHES[name]:
            raise RuntimeError(f"prepared H2743 source byte mismatch: {name}")
    if sha256(state / "native-session/driver-state.json") != ready.get("derived_driver_sha256"):
        raise RuntimeError("prepared derived driver byte mismatch")
    return state, ready


def static_seal(attempt_name: str) -> None:
    """Seal exact v5 inputs without a lease, child process, profile or game."""
    if CANDIDATE != HEAD_STORAGE_CANDIDATE:
        raise RuntimeError("screen-free static seal is limited to the current-HEAD v5 pair")
    if not valid_attempt_name(attempt_name):
        raise RuntimeError("use a fresh literal attempt-N-dejure-baseline-no-launch name")
    verified = check_static(static_only=True)
    attempt = ROOT / attempt_name
    attempt.mkdir(exist_ok=False)
    write_new(attempt / "static-seal.json", {
        "schema": "xar.ck3.h2743.v5.static-no-launch-seal.v1",
        "status": "STATIC_SEALED_LIVE_PREPARE_PENDING",
        "candidate_kind": CANDIDATE,
        "head": HEAD_STORAGE_HEAD,
        "runner_sha256": sha256(Path(__file__).resolve()),
        "static_verification": verified,
        "source_hashes": SOURCE_HASHES,
        "candidate_dll_sha256": DLL_SHA,
        "injector_sha256": INJECTOR_SHA,
        "candidate_build_manifest_sha256": HEAD_STORAGE_PAIR_SHA,
        "screen_lease_checked": False,
        "child_process_started": False,
        "ck3_launch_attempted": False,
        "gameplay_action_submitted": False,
        "created_at_utc": utc_now().isoformat(),
    })
    print(json.dumps({"status": "STATIC_SEALED_LIVE_PREPARE_PENDING",
                      "attempt": str(attempt)}, ensure_ascii=False))


def verify_static_seal(attempt: Path) -> None:
    if (CANDIDATE != HEAD_STORAGE_CANDIDATE or attempt.resolve().parent != ROOT.resolve()
            or not valid_attempt_name(attempt.name)):
        raise RuntimeError("sealed attempt is not a current-HEAD v5 child")
    seal = json.loads((attempt / "static-seal.json").read_text(encoding="utf-8"))
    if (seal.get("schema") != "xar.ck3.h2743.v5.static-no-launch-seal.v1"
            or seal.get("status") != "STATIC_SEALED_LIVE_PREPARE_PENDING"
            or seal.get("candidate_kind") != CANDIDATE
            or seal.get("head") != HEAD_STORAGE_HEAD
            or seal.get("runner_sha256") != sha256(Path(__file__).resolve())
            or seal.get("source_hashes") != SOURCE_HASHES
            or seal.get("candidate_dll_sha256") != DLL_SHA
            or seal.get("injector_sha256") != INJECTOR_SHA
            or seal.get("candidate_build_manifest_sha256") != HEAD_STORAGE_PAIR_SHA
            or seal.get("screen_lease_checked") is not False
            or seal.get("child_process_started") is not False
            or seal.get("ck3_launch_attempted") is not False
            or seal.get("gameplay_action_submitted") is not False
            or seal.get("static_verification") != check_static(static_only=True)):
        raise RuntimeError("current-HEAD v5 static seal changed or is incomplete")
    if {entry.name for entry in attempt.iterdir()} != {"static-seal.json"}:
        raise RuntimeError("sealed attempt already contains preparation or unexpected files")


def require_live_bus_migration() -> None:
    """This v5 HEAD pair cannot use the legacy list/heartbeat screen lease."""
    if CANDIDATE == HEAD_STORAGE_CANDIDATE:
        raise RuntimeError("LIVE_STOP_CAS_MIGRATION_PENDING: H2743 v5 current-HEAD "
                           "requires pinned task-bus source/installed SHA and "
                           "expected-sequence lease operations before live preparation or run")


def call_profile_cli(attempt: Path, state: Path, name: str, arguments: list[str],
                     task_id: str | None) -> dict[str, object]:
    """Run one profile CLI; retain an unsafe marker after any interrupted wait."""
    require_live_bus_migration()
    argv = [str(PYTHON), "-c", CLI_ENTRY, "--state-dir", str(state), "--game-dir", str(GAME), *arguments]
    write_new(attempt / f"{name}-argv.json", {"argv": argv, "ck3_launch_attempted": False})
    with (attempt / f"{name}-stdout.txt").open("x", encoding="utf-8") as stdout, \
         (attempt / f"{name}-stderr.txt").open("x", encoding="utf-8") as stderr:
        completed = subprocess.Popen(argv, cwd=REPO, stdout=stdout, stderr=stderr)
        failure: BaseException | None = None
        try:
            deadline = time.monotonic() + 1200
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise RuntimeError(f"{name} timed out; partial logs preserved")
                try:
                    code = completed.wait(timeout=min(60, remaining))
                    break
                except subprocess.TimeoutExpired:
                    if task_id is not None:
                        renew_screen_lease(task_id)
        except BaseException as error:
            failure = error
            raise
        finally:
            if failure is not None:
                marker_error: BaseException | None = None
                try:
                    write_new(attempt / f"{name}-unsafe-cleanup.json", {
                        "status": "RED_PROFILE_CLI_INTERRUPTED", "pid": completed.pid,
                        "failure": f"{type(failure).__name__}: {failure}",
                        "process_tree_cleanup_proven": False,
                        "manual_recovery_required": True,
                        "at_utc": utc_now().isoformat()})
                except BaseException as error:
                    marker_error = error
                cleanup_errors: list[str] = []
                direct_child_reaped = False
                try:
                    if completed.poll() is None:
                        completed.terminate()
                    completed.wait(timeout=30)
                    direct_child_reaped = completed.poll() is not None
                except BaseException as error:
                    cleanup_errors.append(f"terminate/wait: {type(error).__name__}: {error}")
                    try:
                        if completed.poll() is None:
                            completed.kill()
                        completed.wait(timeout=30)
                        direct_child_reaped = completed.poll() is not None
                    except BaseException as fallback_error:
                        cleanup_errors.append(f"kill/wait: {type(fallback_error).__name__}: {fallback_error}")
                try:
                    write_new(attempt / f"{name}-cleanup-result.json", {
                        "pid": completed.pid, "direct_child_reaped": direct_child_reaped,
                        "returncode": completed.returncode, "cleanup_errors": cleanup_errors,
                        "process_tree_cleanup_proven": False,
                        "unsafe_marker_written": marker_error is None})
                except BaseException as error:
                    raise RuntimeError(f"{name} cleanup receipt unavailable; manual recovery required") from error
                if marker_error is not None or not direct_child_reaped:
                    raise RuntimeError(f"{name} cleanup unproven; manual recovery required") from failure
    if code != 0:
        raise RuntimeError(f"{name} failed: {code}; preserve this attempt")
    return {"exit_code": code, "stdout_sha256": sha256(attempt / f"{name}-stdout.txt"),
            "stderr_sha256": sha256(attempt / f"{name}-stderr.txt")}


def prepare_no_launch(attempt_name: str, task_id: str | None,
                      *, sealed_attempt: bool = False) -> None:
    """Screen-owned live profile preparation; legacy CLI remains available."""
    require_live_bus_migration()
    if not valid_attempt_name(attempt_name):
        raise RuntimeError("use a fresh literal attempt-N-dejure-baseline-no-launch name")
    attempt = ROOT / attempt_name
    if sealed_attempt:
        verify_static_seal(attempt)
    if task_id is None:
        if CANDIDATE != EXISTING_TRUCE_CANDIDATE:
            raise RuntimeError("offscreen no-launch preflight is limited to the new H2743 candidate")
    else:
        screen_lease(task_id)
    check_static()
    import psutil
    if any((item.info.get("name") or "").casefold() == "ck3.exe" for item in psutil.process_iter(["name"])):
        raise RuntimeError("CK3 is already running; defer no-launch profile work")
    state = attempt / "state"
    if not sealed_attempt:
        attempt.mkdir(exist_ok=False)
    write_new(attempt / "source-pair.json", {"schema": "xar.ck3.h2743.dejure-exit-read-port-no-launch.v3",
        "source_hashes": SOURCE_HASHES, "candidate_kind": CANDIDATE,
        "candidate_dll": str(DLL), "candidate_dll_sha256": DLL_SHA,
        "python_source_sha256": provenance_source_hashes(),
        "candidate_build_manifest_sha256": candidate_manifest_sha256(),
        "injector_sha256": INJECTOR_SHA, "ck3_launch_attempted": False, "gameplay_action_submitted": False})

    prepare = call_profile_cli(attempt, state, "prepare-profile", ["prepare-profile", "--xar-enabled", "xar_off",
                                        "--display-mode", "windowed"], task_id)
    destinations = {"xar_checkpoint.ck3": state / "profile/save games/xar_checkpoint.ck3",
                    "driver-state.json": state / "native-session/driver-state.json",
                    "first-heir-marriage-formal-v1.json": state / "first-heir-marriage-formal-v1.json"}
    for name, destination in destinations.items():
        destination.parent.mkdir(parents=True, exist_ok=True)
        with (SOURCE / name).open("rb") as source, destination.open("xb") as target:
            shutil.copyfileobj(source, target)
        if sha256(destination) != SOURCE_HASHES[name]:
            raise RuntimeError(f"prepared source byte mismatch: {name}")
    write_new(attempt / "input-placement.json", {name: str(path) for name, path in destinations.items()})
    rebind = call_profile_cli(attempt, state, "rebind", ["rebind-ordinary-seed-v1", "--expected-pipe", PIPE,
                             "--receipt", str(attempt / "ordinary-rebind-local.json")], task_id)
    derived = sha256(destinations["driver-state.json"])
    preflight = call_profile_cli(attempt, state, "preflight", ["--bridge-pipe", PIPE, "native-one-generation-preflight",
        "--expected-character-id", "29829", "--expected-episode-run-id", EPISODE,
        "--expected-checkpoint-sha256", SOURCE_HASHES["xar_checkpoint.ck3"],
        "--expected-driver-state-sha256", derived, "--xar-enabled", "xar_off",
        "--succession-lifecycle", "ordinary_campaign_succession", "--ordinary-campaign-no-pact"], task_id)
    ready_summary = {"status": "no_launch_preflight_ready",
        "source_hashes": SOURCE_HASHES, "candidate_kind": CANDIDATE,
        "candidate_dll_sha256": DLL_SHA,
        "python_source_sha256": provenance_source_hashes(),
        "injector_sha256": INJECTOR_SHA, "derived_driver_sha256": derived,
        "prepare": prepare, "rebind": rebind, "preflight": preflight,
        "ck3_launch_attempted": False, "gameplay_action_submitted": False}
    if CANDIDATE == HEAD_STORAGE_CANDIDATE:
        ready_summary["candidate_build_manifest_sha256"] = HEAD_STORAGE_PAIR_SHA
    write_new(attempt / "ready-summary.json", ready_summary)
    print(json.dumps({"status": "no_launch_preflight_ready", "attempt": str(attempt)}, ensure_ascii=False))


def require_snapshot(value: dict[str, object]) -> dict[str, object]:
    played = value.get("played_character")
    if (value.get("episode_run_id") != EPISODE or value.get("date_raw") != 53217264
            or not isinstance(played, dict)
            or type(played.get("character_id")) is not int
            or played.get("character_id") != 29829
            or value.get("paused") is not True):
        raise RuntimeError("H2743 paused snapshot identity differs")
    wars = [row for row in value.get("active_wars", []) if isinstance(row, dict)
            and type(row.get("war_id")) is int and row.get("war_id") == 16777231]
    if len(wars) != 1:
        raise RuntimeError("H2743 WarID is not unique and active")
    war = wars[0]
    if (war.get("player_side") != "defender" or war.get("player_is_primary_war_leader") is not True
            or type(war.get("primary_opponent_character_id")) is not int
            or war.get("primary_opponent_character_id") != 30097
            or type(war.get("player_relative_war_score")) is not int
            or war.get("player_relative_war_score") != -12
            or war.get("targeted_title_ids") != [2128]
            or type(war["targeted_title_ids"][0]) is not int):
        raise RuntimeError("H2743 primary defender war row differs")
    return war


def cold_map_snapshot_pending(value: dict[str, object]) -> bool:
    """Transport and map readiness may precede episode, actor and war binding."""
    ready = value.get("map_ready")
    if type(ready) is not bool:
        raise RuntimeError("H2743 map readiness field is missing or malformed")
    if not ready:
        return True
    date = value.get("date_raw")
    paused = value.get("paused")
    if date is not None and type(date) is not int:
        raise RuntimeError("H2743 date type is malformed")
    if paused is not None and type(paused) is not bool:
        raise RuntimeError("H2743 paused type is malformed")
    if (date is not None and date != 53217264) or paused is False:
        return False  # An explicit wrong date or running map is never loading.
    episode = value.get("episode_run_id")
    played = value.get("played_character")
    wars = value.get("active_wars")
    if episode is not None and episode != EPISODE:
        return False  # The strict identity gate rejects a different campaign.
    if played is not None:
        if not isinstance(played, dict):
            raise RuntimeError("H2743 played-character shape is malformed")
        actor = played.get("character_id")
        if actor is not None and type(actor) is not int:
            raise RuntimeError("H2743 played-character ID type is malformed")
        if actor is not None and actor != 29829:
            return False  # A real wrong actor must not be treated as loading.
    if not isinstance(wars, list):
        raise RuntimeError("H2743 active-war shape is malformed")
    return (date is None or paused is None or episode is None or played is None
            or played.get("character_id") is None or not wars)


FRAME_FIELDS = ("snapshot_id", "revision", "native_revision", "date_raw",
                "episode_run_id")


def frame_signature(snapshot: dict[str, object]) -> dict[str, object]:
    frame = {field: snapshot.get(field) for field in FRAME_FIELDS}
    diagnostics = snapshot.get("diagnostics")
    frame["connection_generation"] = (
        diagnostics.get("connection_generation") if isinstance(diagnostics, dict) else None)
    if (not isinstance(frame["snapshot_id"], str) or not frame["snapshot_id"]
            or frame["episode_run_id"] != EPISODE
            or any(type(frame[field]) is not int or frame[field] <= 0
                   for field in ("revision", "native_revision", "date_raw", "connection_generation"))):
        raise RuntimeError("H2743 six-field paused frame is incomplete")
    return frame


def existing_truce_query_arguments(before: dict[str, object],
                                   frame: dict[str, object]) -> dict[str, object]:
    from xar_autoplayer.bridge.h2743_preaction_existing_truce_v1 import (
        frame_claim_from_snapshot,
    )
    claim = frame_claim_from_snapshot(before)
    if (claim["revision"] != frame["revision"]
            or claim["native_revision"] != frame["native_revision"]
            or claim["snapshot_id"] != frame["snapshot_id"]
            or claim["connection_generation"] != frame["connection_generation"]):
        raise RuntimeError("H2743 explicit before frame differs")
    return {"step": QUERY, "expected_revision": claim["revision"],
            "expected_h2743_frame": claim}


def admit_ready_snapshot(snapshot: dict[str, object]) -> tuple[dict[str, object], dict[str, object], list[dict[str, object]]] | None:
    """Return identity evidence only after a fully loaded H2743 map frame."""
    if cold_map_snapshot_pending(snapshot):
        return None
    return require_snapshot(snapshot), frame_signature(snapshot), full_war_signature(snapshot)


def require_same_ready_frame(after: dict[str, object], war: dict[str, object],
                             frame: dict[str, object], expected_wars: list[dict[str, object]]) -> None:
    """Reject a post-query frame that lost the map even if other IDs remain cached."""
    admitted = admit_ready_snapshot(after)
    if admitted is None or admitted != (war, frame, expected_wars):
        raise RuntimeError("H2743 baseline changed within the paused frame")


def require_snapshot_bridge_pid(snapshot: dict[str, object], pid: int) -> None:
    diagnostics = snapshot.get("diagnostics")
    if (type(pid) is not int or pid <= 0 or not isinstance(diagnostics, dict)
            or type(diagnostics.get("bridge_pid")) is not int
            or diagnostics["bridge_pid"] != pid):
        raise RuntimeError("paused snapshot bridge PID differs from managed CK3 process")


def require_target_holder_prestate(baseline: dict[str, object]) -> None:
    """Require a typed current relation; never treat it as a surrender delta."""
    rows = baseline.get("target_title_holder_prestate")
    if (baseline.get("target_title_ids") != [2128]
            or not isinstance(rows, list) or len(rows) != 1
            or not isinstance(rows[0], dict)
            or set(rows[0]) != {"title_id", "holder_character_id",
                                "holder_immediate_liege_character_id"}):
        raise RuntimeError("H2743 target holder prestate is missing or malformed")
    row = rows[0]
    holder = row["holder_character_id"]
    liege = row["holder_immediate_liege_character_id"]
    if (row["title_id"] != 2128 or type(holder) is not int or holder <= 0
            or (liege is not None and (type(liege) is not int or liege <= 0
                                       or liege == holder))):
        raise RuntimeError("H2743 target holder prestate identity is invalid")


def require_partial_truce_inputs(baseline: dict[str, object]) -> None:
    """Keep partial inputs typed and never promote them to a term or action."""
    source = REPO / "ck3_autonomous_player/src"
    if str(source) not in sys.path:
        sys.path.insert(0, str(source))
    from xar_autoplayer.bridge.defender_dejure_exit_terms_v1 import _normalize_truce_inputs
    try:
        _normalize_truce_inputs(baseline.get("truce_inputs_v1"))
    except ValueError as error:
        raise RuntimeError("H2743 partial truce input wire is missing or malformed") from error
    if (baseline.get("material_complete") is not False
            or baseline.get("directed_truce") is not None
            or baseline.get("action_literal") is not None):
        raise RuntimeError("H2743 partial truce input was promoted to an exit term")


def require_storage_candidate(baseline: dict[str, object]) -> None:
    """Admit only typed storage evidence; stock border-raid remains unknown."""
    source = REPO / "ck3_autonomous_player/src"
    if str(source) not in sys.path:
        sys.path.insert(0, str(source))
    from xar_autoplayer.bridge.defender_dejure_exit_terms_v1 import (
        _normalize_border_raid_storage_candidate,
    )
    try:
        _normalize_border_raid_storage_candidate(
            baseline.get("border_raid_storage_candidate_v1"))
    except ValueError as error:
        raise RuntimeError("H2743 storage candidate missing or malformed") from error
    border = baseline["truce_inputs_v1"]["border_raid_pair"]
    if border != {"status": "unavailable", "value": None,
                  "unavailable_reason": "stock_condition_reader_unavailable"}:
        raise RuntimeError("storage candidate was promoted to the stock truce predicate")


WAR_SIGNATURE_FIELDS = ("war_id", "player_side", "player_is_primary_war_leader",
                        "primary_opponent_character_id", "player_relative_war_score",
                        "targeted_title_ids")


def full_war_signature(snapshot: dict[str, object]) -> list[dict[str, object]]:
    """Project every active war using the producer's sorted six-field signature."""
    wars = snapshot.get("active_wars")
    if not isinstance(wars, list) or not wars:
        raise RuntimeError("paused snapshot lacks a complete active-war list")
    signature = []
    seen = set()
    for war in wars:
        if not isinstance(war, dict):
            raise RuntimeError("paused snapshot has a malformed active-war row")
        row = {key: war.get(key) for key in WAR_SIGNATURE_FIELDS}
        war_id = row["war_id"]
        targets = row["targeted_title_ids"]
        if (type(war_id) is not int or war_id <= 0 or war_id in seen
                or row["player_side"] not in {"attacker", "defender"}
                or (row["player_is_primary_war_leader"] is not None
                    and type(row["player_is_primary_war_leader"]) is not bool)
                or (row["primary_opponent_character_id"] is not None
                    and (type(row["primary_opponent_character_id"]) is not int
                         or row["primary_opponent_character_id"] < 0))
                or type(row["player_relative_war_score"]) is not int
                or not isinstance(targets, list)
                or any(type(title) is not int or title < 0 for title in targets)):
            raise RuntimeError("paused snapshot active-war signature is malformed or duplicated")
        seen.add(war_id)
        signature.append({**row, "targeted_title_ids": list(targets)})
    return sorted(signature, key=lambda row: row["war_id"])


def require_options_query(result: dict[str, object], frame: dict[str, object],
                          war: dict[str, object], expected_wars: list[dict[str, object]]) -> None:
    """Bind the exact war-options read to all six paused-frame fields and WarID."""
    context = result.get("termination_query_context")
    options = result.get("war_termination_options")
    if (result.get("step") != OPTIONS_QUERY or result.get("accepted") is not True
            or result.get("status") != "available" or not isinstance(context, dict)
            or not isinstance(options, dict)
            or type(result.get("query_sequence")) is not int
            or result["query_sequence"] <= 0
            or result.get("queried_snapshot_id") != frame["snapshot_id"]
            or result.get("queried_revision") != frame["revision"]
            or result.get("queried_native_revision") != frame["native_revision"]
            or result.get("queried_episode_run_id") != frame["episode_run_id"]
            or result.get("queried_connection_generation") != frame["connection_generation"]
            or context.get("queried_date_raw") != frame["date_raw"]
            or context.get("queried_connection_generation") != frame["connection_generation"]
            or context.get("queried_episode_run_id") != frame["episode_run_id"]
            or context.get("queried_character_id") != 29829
            or options.get("war_id") != 16777231
            or options.get("player_side") != "defender"
            or options.get("player_is_primary_war_leader") is not True
            or options.get("active_casus_belli_identity") != {
                "database_index": 17, "canonical_key": "individual_county_de_jure_cb"}
            or not isinstance(options.get("options"), dict)
            or set(options["options"]) != {"surrender", "white_peace", "victory"}):
        raise RuntimeError("war-options query is not bound to the exact H2743 paused frame")
    surrender = options["options"]["surrender"]
    if (not isinstance(surrender, dict)
            or surrender.get("outcome") != "attacker_victory"
            or surrender.get("native_validator_passed") is not True
            or surrender.get("available") is not True
            or not isinstance(surrender.get("recipient_response"), dict)
            or surrender["recipient_response"].get("would_accept_now") is not True):
        raise RuntimeError("H2743 surrender button legality or acceptance is unavailable")
    signatures = context.get("active_war_signature")
    targets = ([row for row in signatures if isinstance(row, dict)
                and row.get("war_id") == 16777231] if isinstance(signatures, list) else [])
    if (signatures != expected_wars or len(targets) != 1
            or targets[0] != {key: war.get(key) for key in WAR_SIGNATURE_FIELDS}):
        raise RuntimeError("war-options signature changed the full war set or target war")


def audit_loaded_binaries(pid: int, state: Path) -> dict[str, object]:
    """Bind mapped module paths to exact current disk files, not memory bytes."""
    import psutil
    if type(pid) is not int or pid <= 0:
        raise RuntimeError("session ready event has no CK3 PID")
    def same_disk_file(left: Path, right: Path) -> bool:
        try:
            return left.samefile(right)
        except OSError:
            return False
    process = psutil.Process(pid)
    actual_exe = Path(process.exe()).resolve()
    if not same_disk_file(actual_exe, EXE) or sha256(actual_exe) != EXE_SHA:
        raise RuntimeError("running CK3 EXE mapped path or current disk bytes differ")
    loaded = sorted({str(Path(mapping.path).resolve())
                     for mapping in process.memory_maps(grouped=False)
                     if Path(mapping.path).name.casefold() == "xar_ck3_bridge.dll"})
    if (not loaded or any(not same_disk_file(Path(path), DLL) or sha256(Path(path)) != DLL_SHA
                          for path in loaded)):
        raise RuntimeError("loaded bridge DLL mapped path or current disk bytes differ")
    return {"schema": "xar.ck3.h2743.readonly-loaded-path-disk-audit.v1",
            "ck3_pid": pid, "ck3_process_create_time": process.create_time(),
            "running_exe_path": str(actual_exe), "running_exe_disk_sha256": EXE_SHA,
            "loaded_bridge_paths": loaded, "loaded_bridge_disk_sha256": DLL_SHA,
            "candidate_injector_path": str(INJECTOR.resolve()),
            "candidate_injector_sha256": sha256(INJECTOR),
            "source_input_sha256": dict(SOURCE_HASHES),
            "derived_driver_sha256_at_query": sha256(state / "native-session/driver-state.json"),
            "loaded_module_path_and_disk_sha_verified": True,
            "loaded_in_memory_image_sha256": None}


def require_lease_watchdog_healthy(failures: list[str]) -> None:
    if failures:
        raise RuntimeError(f"screen lease watchdog failed: {failures[0]}")


async def read_frame(state: Path, output: Path, lease_failures: list[str]) -> dict[str, object]:
    from mcp.client.session import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client

    command = ["-c", MCP_ENTRY]
    args = ["--driver", "native-headless", "--transport", "stdio", "--state-dir", str(state),
            "--pipe-name", PIPE, "--environment-manifest", str(state / "profile/xar-autoplayer-environment.json"),
            "--succession-lifecycle", "ordinary_campaign_succession", "--ordinary-campaign-no-pact"]
    write_new(output / "mcp-plan.json", {"python": str(PYTHON), "command": command, "args": args,
                                         "allowed_execute_steps": [QUERY, OPTIONS_QUERY],
                                         "gameplay_action_submitted": False})
    async def call(session: ClientSession, name: str, arguments: dict[str, object], stem: str) -> dict[str, object]:
        require_lease_watchdog_healthy(lease_failures)
        write_new(output / f"{stem}-request.json", {"tool": name, "arguments": arguments})
        response = await asyncio.wait_for(session.call_tool(name, arguments), timeout=TOOL_SECONDS)
        require_lease_watchdog_healthy(lease_failures)
        write_new(output / f"{stem}-envelope.json", response.model_dump(mode="json", by_alias=True))
        if response.is_error or not isinstance(response.structured_content, dict):
            raise RuntimeError(f"{name} failed; envelope preserved")
        write_new(output / f"{stem}-payload.json", response.structured_content)
        return response.structured_content

    with (output / "mcp-stderr.txt").open("x", encoding="utf-8") as stderr:
        params = StdioServerParameters(command=str(PYTHON), args=command + args, cwd=str(REPO))
        async with stdio_client(params, errlog=stderr) as (reader, writer):
            async with ClientSession(reader, writer) as session:
                await asyncio.wait_for(session.initialize(), timeout=TOOL_SECONDS)
                deadline = time.monotonic() + FRAME_SECONDS
                count = 0
                while True:
                    require_lease_watchdog_healthy(lease_failures)
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise RuntimeError(f"H2743 paused MCP frame not ready within {FRAME_SECONDS} seconds")
                    count += 1
                    response = await asyncio.wait_for(session.call_tool("ck3_take_snapshot", {}),
                                                      timeout=min(TOOL_SECONDS, remaining))
                    require_lease_watchdog_healthy(lease_failures)
                    write_new(output / f"readiness-{count:03d}.json", response.model_dump(mode="json", by_alias=True))
                    if not response.is_error and isinstance(response.structured_content, dict):
                        candidate = response.structured_content
                        admitted = admit_ready_snapshot(candidate)
                        if admitted is not None:
                            if time.monotonic() >= deadline:
                                raise RuntimeError(f"H2743 paused MCP frame not ready within {FRAME_SECONDS} seconds")
                            war, frame, expected_wars = admitted
                            before = candidate
                            write_new(output / "before-payload.json", before)
                            break
                    if time.monotonic() >= deadline:
                        raise RuntimeError(f"H2743 paused MCP frame not ready within {FRAME_SECONDS} seconds")
                    await asyncio.sleep(min(15, deadline - time.monotonic()))
                ready = json.loads((output / "session-ready.json").read_text(encoding="utf-8"))
                require_snapshot_bridge_pid(before, ready.get("pid"))
                write_new(output / "binary-audit-live.json", audit_loaded_binaries(ready.get("pid"), state))
                if CANDIDATE == EXISTING_TRUCE_CANDIDATE:
                    from xar_autoplayer.bridge.h2743_preaction_existing_truce_v1 import (
                        OUTER_KEYS, normalize_result,
                    )
                    query_arguments = existing_truce_query_arguments(before, frame)
                    truce_results = []
                    for number in (1, 2):
                        result = await call(session, "ck3_execute_step", query_arguments,
                                            f"existing-truce-query-{number}")
                        if not OUTER_KEYS.issubset(result):
                            raise RuntimeError("H2743 existing-truce result fields missing")
                        wire = normalize_result(
                            {key: result[key] for key in OUTER_KEYS},
                            native_revision=before["native_revision"],
                        )
                        if (result.get("h2743_preaction_existing_truce_proof") != wire
                                or wire["status"] == "unavailable"):
                            raise RuntimeError("H2743 existing-truce slot is unavailable or proof differs")
                        truce_results.append((result, wire))
                        if number == 1:
                            options_result = await call(session, "ck3_execute_step",
                                                        {"step": OPTIONS_QUERY,
                                                         "expected_revision": query_arguments["expected_revision"]},
                                                        "war-options-query")
                            require_options_query(options_result, frame, war, expected_wars)
                    after = await call(session, "ck3_take_snapshot", {}, "after-snapshot")
                    require_snapshot_bridge_pid(after, ready["pid"])
                    require_same_ready_frame(after, war, frame, expected_wars)
                    if (truce_results[0][1] != truce_results[1][1]
                            or truce_results[1][0]["query_sequence"] !=
                            truce_results[0][0]["query_sequence"] + 1):
                        raise RuntimeError("H2743 existing-truce slot changed within paused frame")
                    return {
                        "status": "preaction_existing_truce_readonly",
                        "candidate_kind": CANDIDATE, "war_id": 16777231,
                        "frame": frame, "date_raw": before["date_raw"],
                        "source_save_sha256": SOURCE_HASHES["xar_checkpoint.ck3"],
                        "before_snapshot_sha256": sha256(output / "before-payload.json"),
                        "query_1_sha256": sha256(output / "existing-truce-query-1-payload.json"),
                        "query_2_sha256": sha256(output / "existing-truce-query-2-payload.json"),
                        "war_options_payload_sha256": sha256(output / "war-options-query-payload.json"),
                        "binary_audit_live_sha256": sha256(output / "binary-audit-live.json"),
                        "after_snapshot_sha256": sha256(output / "after-snapshot-payload.json"),
                        "preaction_status": truce_results[0][1]["status"],
                        "preaction_existing_expiry_date_raw": truce_results[0][1]["preaction_existing_expiry_date_raw"],
                        "post_surrender_actual_expiry_date_raw": None,
                        "effect_projection_complete": False,
                        "material_complete": False,
                        "comparison_status": "unavailable",
                        "action_literal": None,
                        "gameplay_action_submitted": False,
                    }
                results = []
                for number in (1, 2):
                    result = await call(session, "ck3_execute_step", {"step": QUERY}, f"baseline-query-{number}")
                    baseline = result.get("defender_de_jure_exit_terms_v1")
                    if (result.get("step") != QUERY or result.get("accepted") is not True
                            or result.get("status") != "baseline_only" or not isinstance(baseline, dict)
                            or baseline.get("material_complete") is not False
                            or baseline.get("title_vassal_delta") is not None
                            or baseline.get("signed_resource_delta") is not None
                            or baseline.get("directed_truce") is not None
                            or len(baseline.get("primary_resource_balances", [])) != 14
                            or len(baseline.get("primary_monthly_gold_income", [])) != 2):
                        raise RuntimeError("baseline query unavailable, malformed or falsely material-complete")
                    require_target_holder_prestate(baseline)
                    if CANDIDATE == TRUCE_CANDIDATE or is_storage_candidate():
                        require_partial_truce_inputs(baseline)
                    if is_storage_candidate():
                        require_storage_candidate(baseline)
                    results.append(result)
                    if number == 1:
                        options_result = await call(session, "ck3_execute_step",
                                                    {"step": OPTIONS_QUERY}, "war-options-query")
                        require_options_query(options_result, frame, war, expected_wars)
                after = await call(session, "ck3_take_snapshot", {}, "after-snapshot")
                require_snapshot_bridge_pid(after, ready["pid"])
                require_same_ready_frame(after, war, frame, expected_wars)
                if results[0]["defender_de_jure_exit_terms_v1"] != results[1]["defender_de_jure_exit_terms_v1"]:
                    raise RuntimeError("H2743 baseline changed within the paused frame")
                summary = {"status": "baseline_only_material_unavailable", "war_id": 16777231,
                           "candidate_kind": CANDIDATE,
                           "frame": frame, "date_raw": before["date_raw"],
                           "native_revision": before.get("native_revision"),
                           "source_save_sha256": SOURCE_HASHES["xar_checkpoint.ck3"],
                           "before_snapshot_sha256": sha256(output / "before-payload.json"),
                           "query_1_sha256": sha256(output / "baseline-query-1-payload.json"),
                           "query_2_sha256": sha256(output / "baseline-query-2-payload.json"),
                           "war_options_request_sha256": sha256(output / "war-options-query-request.json"),
                           "war_options_envelope_sha256": sha256(output / "war-options-query-envelope.json"),
                           "war_options_payload_sha256": sha256(output / "war-options-query-payload.json"),
                           "war_options_query_sequence": options_result["query_sequence"],
                           "binary_audit_live_sha256": sha256(output / "binary-audit-live.json"),
                           "after_snapshot_sha256": sha256(output / "after-snapshot-payload.json"),
                           "missing_for_exit_comparison": ["runtime_target_scope", "title_vassal_delta",
                                "cb_prestige_factor", "signed_resource_delta_14_rows",
                                "conditional_resource_effects", "directed_truce_duration",
                                "same_frame_continuation_risk"],
                           "comparison_status": "unavailable", "action_literal": None,
                           "gameplay_action_submitted": False}
                if is_storage_candidate():
                    summary["border_raid_storage_candidate_v1"] = results[0][
                        "defender_de_jure_exit_terms_v1"
                    ]["border_raid_storage_candidate_v1"]
                    summary["stock_border_raid_pair_observed"] = False
                return summary


def require_clean_session_exit(receipt: dict[str, object], *, require_read_audit: bool = True) -> None:
    """A baseline result is publishable only after the managed game has exited."""
    if (receipt.get("returncode") != 0
            or receipt.get("ck3_pids_after") != []
            or receipt.get("stdout_reader_alive_after") is not False
            or receipt.get("source_sha256_after") != SOURCE_HASHES
            or receipt.get("candidate_dll_sha256_after") != DLL_SHA
            or receipt.get("injector_sha256_after") != INJECTOR_SHA
            or receipt.get("exe_sha256_after") != EXE_SHA
            or (require_read_audit and (not isinstance(receipt.get("binary_audit_live_sha256"), str)
                or len(receipt["binary_audit_live_sha256"]) != 64))
            or receipt.get("prepared_save_sha256_after") != SOURCE_HASHES["xar_checkpoint.ck3"]
            or receipt.get("prepared_sidecar_sha256_after") != SOURCE_HASHES["first-heir-marriage-formal-v1.json"]):
        raise RuntimeError("managed H2743 session exit, process cleanup or exact inputs are RED")


def run(attempt: Path, steam_gate: Path, task_id: str) -> None:
    require_live_bus_migration()
    check_static()
    state, ready = prepared_state(attempt)
    gate = live_gate(task_id, steam_gate)
    import psutil
    if any((item.info.get("name") or "").casefold() == "ck3.exe" for item in psutil.process_iter(["name"])):
        raise RuntimeError("CK3 is already running; do not join or disturb another owner")
    renew_screen_lease(task_id)
    output = attempt / LIVE_OUTPUT
    output.mkdir(exist_ok=False)
    argv = [str(PYTHON), "-c", CLI_ENTRY, "--state-dir", str(state), "--game-dir", str(GAME),
            "--bridge-mode", "native-headless", "--bridge-pipe", PIPE,
            "--bridge-dll", str(DLL), "--bridge-injector", str(INJECTOR),
            "native-session", "--cold-start-checkpoint", "--xar-enabled", "xar_off",
            "--timeout", str(SESSION_SECONDS)]
    write_new(output / "launch-plan.json", {"argv": argv, "source_pair": SOURCE_HASHES,
             "candidate_kind": CANDIDATE, "candidate_dll_sha256": DLL_SHA,
             "ready_summary_sha256": sha256(attempt / "ready-summary.json"), "gate": gate,
             "readiness_seconds": READINESS_SECONDS, "session_timeout_seconds": SESSION_SECONDS,
             "allowed_query_steps": [QUERY, OPTIONS_QUERY],
             "allowed_gameplay_steps": [], "started_at_utc": utc_now().isoformat()})
    lines: queue.Queue[str] = queue.Queue()
    with (output / "session-stderr.txt").open("x", encoding="utf-8") as error_log, \
         (output / "session-stdout.jsonl").open("x", encoding="utf-8") as stdout_log:
        process = subprocess.Popen(argv, cwd=REPO, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=error_log, text=True, encoding="utf-8", errors="replace", bufsize=1)
        def consume() -> None:
            assert process.stdout is not None
            for line in process.stdout:
                stdout_log.write(line)
                stdout_log.flush()
                lines.put(line)
        thread = threading.Thread(target=consume, daemon=True)
        thread.start()
        try:
            deadline = time.monotonic() + READINESS_SECONDS
            next_heartbeat = time.monotonic()
            while time.monotonic() < deadline:
                if time.monotonic() >= next_heartbeat:
                    renew_screen_lease(task_id)
                    next_heartbeat = time.monotonic() + 60
                if process.poll() is not None:
                    raise RuntimeError(f"native session exited before ready: {process.returncode}")
                try:
                    event = json.loads(lines.get(timeout=5))
                except (queue.Empty, json.JSONDecodeError):
                    continue
                if event.get("type") == "native_session_ready":
                    write_new(output / "session-ready.json", event)
                    break
            else:
                raise RuntimeError("native session not ready within 1800 seconds")
            renew_screen_lease(task_id)
            lease_failures: list[str] = []
            watchdog_stop = threading.Event()
            with (output / "lease-heartbeats.jsonl").open("x", encoding="utf-8", newline="\n") as lease_log:
                def lease_watchdog() -> None:
                    while not watchdog_stop.wait(60):
                        try:
                            renew_screen_lease(task_id)
                            row = {"at_utc": utc_now().isoformat(), "status": "renewed"}
                        except BaseException as error:
                            lease_failures.append(f"{type(error).__name__}: {error}")
                            row = {"at_utc": utc_now().isoformat(), "status": "failed",
                                   "reason": lease_failures[-1]}
                        lease_log.write(json.dumps(row, ensure_ascii=False) + "\n")
                        lease_log.flush()
                        if lease_failures:
                            return
                watchdog_thread = threading.Thread(target=lease_watchdog, daemon=True)
                watchdog_thread.start()
                try:
                    summary = asyncio.run(read_frame(state, output, lease_failures))
                    require_lease_watchdog_healthy(lease_failures)
                    if not watchdog_thread.is_alive():
                        raise RuntimeError("screen lease watchdog exited before paused read completed")
                finally:
                    watchdog_stop.set()
                    watchdog_thread.join(timeout=20)
                    if watchdog_thread.is_alive():
                        lease_failures.append("watchdog did not stop after paused read")
            require_lease_watchdog_healthy(lease_failures)
        except BaseException as error:
            write_new(output / "failure.json", {"type": type(error).__name__, "message": str(error),
                         "at_utc": utc_now().isoformat(), "gameplay_action_submitted": False})
            raise
        finally:
            try:
                # Even a failed read must release the CK3 process. A lost lease is
                # recorded after cleanup, never used as a reason to skip cleanup.
                lease_error = None
                try:
                    renew_screen_lease(task_id)
                except BaseException as error:
                    lease_error = error
                if process.poll() is None:
                    if process.stdin is None:
                        raise RuntimeError("native session stop pipe is absent")
                    try:
                        process.stdin.write("stop\n")
                        process.stdin.flush()
                    except (BrokenPipeError, OSError):
                        pass  # The supervisor may have exited between poll and write.
                    try:
                        process.wait(timeout=180)
                    except subprocess.TimeoutExpired as error:
                        raise RuntimeError("native session stop timed out; manual recovery required") from error
                thread.join(timeout=5)
                receipt = {"returncode": process.returncode,
                    "supervisor_pid": process.pid,
                    "stdout_reader_alive_after": thread.is_alive(),
                    "source_sha256_after": {name: sha256(SOURCE / name) for name in SOURCE_HASHES},
                    "candidate_dll_sha256_after": sha256(DLL),
                    "injector_sha256_after": sha256(INJECTOR),
                    "exe_sha256_after": sha256(EXE),
                    "binary_audit_live_sha256": (sha256(output / "binary-audit-live.json")
                        if (output / "binary-audit-live.json").is_file() else None),
                    "prepared_save_sha256_after": sha256(state / "profile/save games/xar_checkpoint.ck3"),
                    "prepared_sidecar_sha256_after": sha256(state / "first-heir-marriage-formal-v1.json"),
                    "derived_driver_sha256_after": sha256(state / "native-session/driver-state.json"),
                    "ck3_pids_after": [item.pid for item in psutil.process_iter(["name"])
                        if (item.info.get("name") or "").casefold() == "ck3.exe"]}
                write_new(output / "session-exit.json", receipt)
                require_clean_session_exit(receipt, require_read_audit="summary" in locals())
                if "summary" in locals() and receipt["binary_audit_live_sha256"] != summary["binary_audit_live_sha256"]:
                    raise RuntimeError("loaded binary audit changed between paused read and managed exit")
                if lease_error is not None:
                    raise RuntimeError("screen lease lost before managed session exit") from lease_error
            except BaseException as error:
                write_new(output / "cleanup-red.json", {"reason": str(error),
                    "supervisor_pid": process.pid, "at_utc": utc_now().isoformat(),
                    "manual_recovery_required": process.poll() is None,
                    "gameplay_action_submitted": False})
                raise
    summary = {**summary, "session_exit_sha256": sha256(output / "session-exit.json"),
               "cleanup_proven": True}
    write_new(output / "read-only-result.json", summary)
    print(json.dumps(summary, ensure_ascii=False), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", choices=(DEFAULT_CANDIDATE, TRUCE_CANDIDATE,
                                                STORAGE_CANDIDATE, HEAD_STORAGE_CANDIDATE,
                                                EXISTING_TRUCE_CANDIDATE),
                        default=DEFAULT_CANDIDATE,
                        help="exact pinned read-only DLL; default preserves the v3 reader")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check-static", action="store_true", help="hash exact inputs; no profile or CK3 launch")
    mode.add_argument("--seal-no-launch", action="store_true",
                      help="new v5 static seal; no screen lease or child process")
    mode.add_argument("--prepare-live-profile", action="store_true",
                      help="screen-owned profile/preflight from a static seal; current-HEAD v5 live STOP")
    mode.add_argument("--prepare-no-launch", action="store_true",
                      help="legacy screen-owned profile/preflight in a fresh attempt")
    parser.add_argument("--attempt-name", help="fresh attempt-N-dejure-baseline-no-launch")
    mode.add_argument("--run", action="store_true", help="consume a separately prepared exact attempt")
    parser.add_argument("--prepared-attempt", type=Path)
    parser.add_argument("--steam-gate", type=Path)
    parser.add_argument("--task-id")
    args = parser.parse_args()
    select_candidate(args.candidate)
    if args.run:
        if not all((args.prepared_attempt, args.steam_gate, args.task_id)):
            parser.error("--run requires --prepared-attempt, --steam-gate and --task-id")
        if args.prepare_no_launch or args.attempt_name:
            parser.error("--run cannot also prepare a profile")
        run(args.prepared_attempt, args.steam_gate, args.task_id)
    elif args.seal_no_launch:
        if not args.attempt_name or args.prepared_attempt or args.steam_gate or args.task_id:
            parser.error("--seal-no-launch requires only --attempt-name")
        static_seal(args.attempt_name)
    elif args.prepare_live_profile:
        if (not args.prepared_attempt or not args.task_id or args.attempt_name
                or args.steam_gate):
            parser.error("--prepare-live-profile requires --prepared-attempt and --task-id only")
        if args.prepared_attempt.resolve().parent != ROOT.resolve():
            parser.error("--prepared-attempt must be a direct child of the selected candidate root")
        prepare_no_launch(args.prepared_attempt.name, args.task_id, sealed_attempt=True)
    elif args.prepare_no_launch:
        if (not args.attempt_name or args.prepared_attempt or args.steam_gate
                or (not args.task_id and args.candidate != EXISTING_TRUCE_CANDIDATE)):
            parser.error("--prepare-no-launch requires --attempt-name; old candidates also require --task-id")
        prepare_no_launch(args.attempt_name, args.task_id)
    elif args.prepared_attempt or args.steam_gate or args.task_id or args.attempt_name:
        parser.error("attempt, gate and task ID are only used with --run")
    else:
        print(json.dumps(check_static(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
