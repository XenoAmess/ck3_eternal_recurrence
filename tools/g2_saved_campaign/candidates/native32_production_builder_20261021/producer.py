"""Finite Native32 offline builder; importing this module performs no I/O.

The owner supplies an exact execution-card pin. This does not install, load,
inject, deploy, register an EXE, reconnect a provider, or issue a Game command.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
import re
import shutil
import struct
import subprocess
import time
from typing import Literal, Sequence, TypedDict


MACHINE = "xenoamess-full-tower-eb9d2c1186"
REPO = Path(__file__).resolve().parents[4]
N32 = REPO / "tools/g2_saved_campaign/candidates/native32_passive_journal_diagnostics_20261021"
OLD = Path("D:/codex-ck3-demos/2026-10-20-native31-passive-build01")
PREP = Path("D:/codex-ck3-demos/2026-10-20-native31-passive-prepare01/source/ck3_autonomous_player/native_bridge")
ROOT = Path("D:/codex-ck3-demos/2026-10-21-native32-passive-build01")
PLAN_NAME = "PLAN03.json"
MSVC = Path("C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231/bin/HostX64/x64")
DEADLINE = datetime(2026, 10, 21, 1, 0, tzinfo=timezone.utc)
HARD = 134217728
EXPECTED_EXPORTS = frozenset(("XarCk3BridgeIdentity", "XarCk3BridgePrepareStartup", "XarCk3BridgeStart", "XarCk3BridgeStartWithPipe", "XarCk3BridgeStop", "XarRefillCoreCarrier12004"))
TU_NAMES = ("bridge", "commands", "core", "install")
OBJECT_CAPS = (25165824, 65536, 262144, 65536)
SOURCE_PINS = {
    "bridge": (PREP / "src/bridge.cpp", 1606472, "661e73ca1002334e039ad234ae142937cd24f128d3399a9b0ad154adc1c11719"),
    "commands": (PREP / "src/ck3_12002_commands.cpp", 8431, "d5a18e67954b215d110cc256f26b5577bb7a0c2ea46b8f0122b817a120cc5c74"),
    "core": (N32 / "native/src/native_time_command_observer_12004.cpp", 16599, "5f8ee4ea50b3b2441978fea1e82a10792d5bcd59bd29fd39d7ff6229d57d0b5d"),
    "install": (PREP / "src/native_time_command_observer_12004_install.cpp", 9790, "95888a0ca45293704dedc8915edf817c5dabb12af42c93b4f536f080994ed545"),
    "header": (N32 / "native/include/xar_bridge/native_time_command_observer_12004.hpp", 4669, "e5534112bd49e9242f6d4ff6cbee7fcbbab38bb3628d006ffcd726c9baa6bf62"),
    "overlay": (PREP / "cmake/native30-runtime-source-macro-restore.cmake", 807, "e99511202bab46b24e37b9cf4b1e9d31eb6e9ce3612bf8f078dba131f05d2e02"),
    "manifest": (N32 / "MANIFEST.json", 2062, "71ec7f5a993ff60380dfeee0eace5226d89d6b5add53de2c4989914dbec595a4"),
    "qualification": (N32 / "QUALIFICATION.json", 4938, "72ec047242b58a066664066f4c987d68adbe85c0caa0869f97fa8c88f9e155e2"),
    "host_pass": (N32 / "build-host/HOST-QUALIFICATION02.json", 1480, "1854d63179c2cc9071afcdc5837be59ae991d3f5f7738e2cad98c4e1a656c74a"),
    "tool_cl": (MSVC / "cl.exe", 893288, "315a654ea116864516a1674858e587e535e3bc3045ff32ed2f2739a2c1ec5640"),
    "tool_link": (MSVC / "link.exe", 3701128, "610aae3d74a66fa5ef54cac5df8ea8bcbb1fdd2a3db9087eb92088bd395eaf34"),
    "tool_dumpbin": (MSVC / "dumpbin.exe", 23376, "ef58d7f394120709d84444296e534a17ee3f0decb493284568d81c0b96805169"),
}
COMMAND_PINS = {
    "bridge": (7259, "1714f4047bb0f84add4fe53339a021dbb5407531c0cb75453ce3e800ceea2031"),
    "commands": (6364, "d842a8f296a8b2bfbb28e135cf570bb5b2bb6e6cc2ef8ba1c5a1972f8a685b5d"),
    "core": (6323, "fb6818bbfd7ab3c343ef9a4ecf40c013793455c7f5a10c1a5b3104a1c3b64dbc"),
    "install": (6385, "b61ea2fdc2b93a9b2fbb39777bdd685d75674798dc6b2523edab29f69ce917b0"),
}
RSP_PIN = (51305, "8be74fa88475d642c588fe8f05a9c076fcb8f22118506114f4e06b759c626dbc")


class FilePin(TypedDict):
    path: str
    bytes: int
    sha256: str
    device: str
    file_id: str
    mtime_ns: str


class ExecutionAdmissionV1(TypedDict):
    schema: Literal["xar.native32.offline-production-execution/v1"]
    machine_id: str
    status: Literal["ADMITTED"]
    owner: Literal["Root"]
    build_root: str
    plan_sha256: str
    producer_sha256: str
    phase_hard_bytes: int
    review_at_utc: str
    root_direct_execution_release: Literal[True]
    four_TUs_sequential: Literal[True]
    Game_calls_allowed: Literal[False]
    DLL_loads_allowed: Literal[False]
    deployment_allowed: Literal[False]


@dataclass(frozen=True)
class CompileRecipe:
    name: str
    argv: tuple[str, ...]
    source: Path
    object_path: Path
    object_cap: int


@dataclass(frozen=True)
class BuildRecipe:
    compilation: tuple[CompileRecipe, ...]
    link_arguments: tuple[str, ...]
    reused_inputs: tuple[Path, ...]


@dataclass(frozen=True)
class Export:
    name: str
    rva: str
    executable: bool
    forwarded: bool


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def object_map(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("JSON object required")
    result: dict[str, object] = {}
    for key, item in value.items():
        if type(key) is not str:
            raise ValueError("string JSON keys required")
        result[key] = item
    return result


def string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        raise ValueError("array required")
    result: list[str] = []
    for item in value:
        if type(item) is not str:
            raise ValueError("string array required")
        result.append(item)
    return result


def read_object(path: Path) -> dict[str, object]:
    value: object = json.loads(path.read_bytes())
    return object_map(value)


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1048576), b""):
            hasher.update(block)
    return hasher.hexdigest()


def identity(path: Path) -> tuple[int, int, int, int]:
    stat = path.stat()
    return stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns


def pin(path: Path) -> FilePin:
    before = identity(path)
    sha = digest(path)
    require(identity(path) == before, "input changed while hashing: " + str(path))
    return FilePin(path=str(path), bytes=before[2], sha256=sha, device=str(before[0]), file_id=str(before[1]), mtime_ns=str(before[3]))


def checked_pin(path: Path, size: int, sha: str) -> FilePin:
    actual = pin(path)
    require(actual["bytes"] == size and actual["sha256"] == sha, "immutable input drift: " + str(path))
    return actual


def pinned_input_identities(inputs: Sequence[FilePin]) -> dict[Path, tuple[int, int, int, int]]:
    result: dict[Path, tuple[int, int, int, int]] = {}
    for item in inputs:
        for key in ("device", "file_id", "mtime_ns"):
            value = item[key]
            require(type(value) is str and re.fullmatch(r"0|[1-9][0-9]*", value) is not None, "canonical pinned identity required")
        require(type(item["bytes"]) is int and item["bytes"] >= 0, "exact pinned byte size required")
        expected = (int(item["device"]), int(item["file_id"]), item["bytes"], int(item["mtime_ns"]))
        path = Path(item["path"])
        require(path not in result and identity(path) == expected, "input drift after pin: " + str(path))
        result[path] = expected
    return result


def old_source(name: str) -> str:
    if name == "core":
        return str(OLD / "source/native_time_command_observer_12004.cpp")
    return str(SOURCE_PINS[name][0])


def adapt_compile(name: str, argv: Sequence[str], root: Path) -> CompileRecipe:
    require(name in TU_NAMES, "unknown TU")
    source = SOURCE_PINS[name][0]
    first_include = "/I" + str(PREP / "include")
    old_obj = "/Fo" + str(OLD / "obj" / ("native31-" + name + ".obj"))
    old_pdb = "/Fd" + str(OLD / "obj" / ("native31-" + name + ".pdb"))
    for expected in (first_include, old_obj, old_pdb, old_source(name), "/DXAR_CK3_ENABLE_NATIVE_TIME_OBSERVER31=1", "/c"):
        require(list(argv).count(expected) == 1, "missing/duplicate original compile argument: " + expected)
    require(not any(x.lower().startswith(("/zi", "/z7", "-zi", "-z7")) for x in argv), "debug output not admitted")
    obj = root / "obj" / ("native32-" + name + ".obj")
    result: list[str] = []
    for arg in argv:
        if arg == first_include:
            result.extend(("/I" + str(N32 / "native/include"), arg))
        elif arg == old_obj:
            result.append("/Fo" + str(obj))
        elif arg == old_pdb:
            result.append("/Fd" + str(obj.with_suffix(".pdb")))
        elif arg == old_source(name):
            result.append(str(source))
        else:
            result.append(arg)
    private = ("-DXAR_CK3_ENABLE_G2_PLAYER_RELIGION_CONTEXT_PRIVATE_QUERY_V1=1", "-DXAR_CK3_ENABLE_G2_PLAYER_RELIGION_PERSONAL_PARAMETERS_PRIVATE_QUERY_V1=1")
    require(all((flag in result) == (name == "bridge") for flag in private), "807-byte macro overlay scope drift")
    return CompileRecipe(name, tuple(result), source, obj, OBJECT_CAPS[TU_NAMES.index(name)])


def unquote(line: str) -> str:
    require("\n" not in line and "\r" not in line, "multiline response argument")
    if line.startswith('"'):
        require(line.endswith('"') and '"' not in line[1:-1], "unsupported response quoting")
        return line[1:-1]
    require('"' not in line, "unsupported embedded quote")
    return line


def adapt_link(lines: Sequence[str], root: Path) -> tuple[tuple[str, ...], tuple[Path, ...]]:
    args = [unquote(line) for line in lines]
    require(not any(x.upper().startswith(("/FORCE", "/WHOLEARCHIVE", "/LTCG")) for x in args), "unadmitted linker option")
    require(sum(x.lower().endswith(".obj") for x in args) == 339, "339 original objects required")
    result: list[str] = []
    for arg in args:
        replacement = arg
        for name in TU_NAMES:
            old_obj = str(OLD / "obj" / ("native31-" + name + ".obj"))
            if arg == old_obj:
                require(args.count(old_obj) == 1, "duplicate replacement object")
                replacement = str(root / "obj" / ("native32-" + name + ".obj"))
        if arg.startswith("/PDB:"):
            continue
        for prefix, suffix in (("/OUT:", ".dll"), ("/IMPLIB:", ".lib"), ("/MAP:", ".map")):
            if arg.startswith(prefix):
                require(arg == prefix + str(OLD / "bin" / ("xar_ck3_bridge" + suffix)), "unexpected original output")
                replacement = prefix + str(root / "bin" / ("xar_ck3_bridge" + suffix))
        result.append(replacement)
    for name in TU_NAMES:
        require(result.count(str(root / "obj" / ("native32-" + name + ".obj"))) == 1, "replacement object absent")
    require(not any(x.upper().startswith("/DEBUG") for x in result), "original debug mode drift")
    result.append("/DEBUG:NONE")
    reused = tuple(Path(x) for x in args if (x.lower().endswith(".obj") and not x.startswith(str(OLD))) or (x.lower().endswith(".lib") and PureWindowsPath(x).is_absolute()))
    require(sum(str(p).lower().endswith(".obj") for p in reused) == 335, "335 unchanged objects required")
    require(sum(str(p).lower().endswith(".lib") for p in reused) == 2, "two unchanged archives required")
    return tuple(result), reused


def recipe() -> BuildRecipe:
    compilation: list[CompileRecipe] = []
    for name in TU_NAMES:
        path = OLD / "commands" / ("native31-" + name + ".json")
        size, sha = COMMAND_PINS[name]
        checked_pin(path, size, sha)
        original = read_object(path)
        require(type(original.get("return_code")) is int and original["return_code"] == 0, "original compiler command failed")
        compilation.append(adapt_compile(name, string_list(original.get("command")), ROOT))
    rsp = OLD / "native31-link.rsp"
    checked_pin(rsp, *RSP_PIN)
    link_args, reused = adapt_link(rsp.read_text().splitlines(), ROOT)
    return BuildRecipe(tuple(compilation), link_args, reused)


def source_inputs() -> dict[str, FilePin]:
    return {name: checked_pin(*value) for name, value in SOURCE_PINS.items()}


def validate_admission(value: object, plan_sha: str, producer_sha: str) -> ExecutionAdmissionV1:
    """Validate the execution card's exact Native32_production_execution object."""
    raw = object_map(object_map(value).get("Native32_production_execution"))
    expected: ExecutionAdmissionV1 = {
        "schema": "xar.native32.offline-production-execution/v1", "machine_id": MACHINE,
        "status": "ADMITTED", "owner": "Root", "build_root": str(ROOT),
        "plan_sha256": plan_sha, "producer_sha256": producer_sha,
        "phase_hard_bytes": HARD, "review_at_utc": DEADLINE.isoformat(),
        "root_direct_execution_release": True, "four_TUs_sequential": True,
        "Game_calls_allowed": False, "DLL_loads_allowed": False, "deployment_allowed": False,
    }
    require(raw.keys() == expected.keys(), "execution scope fields differ")
    for key, item in expected.items():
        require(type(raw[key]) is type(item) and raw[key] == item, "execution scope differs: " + key)
    require(re.fullmatch(r"[0-9a-f]{64}", plan_sha) is not None and re.fullmatch(r"[0-9a-f]{64}", producer_sha) is not None, "canonical source/plan pins required")
    return expected


def write_json(name: str, value: object, cap: int = 131072) -> FilePin:
    body = (json.dumps(value, sort_keys=True, ensure_ascii=True, indent=2) + "\n").encode()
    require(len(body) <= cap, "metadata leaf cap exceeded: " + name)
    path = ROOT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(body)
    return pin(path)


def allowed_caps() -> dict[str, int]:
    caps = {"obj/native32-" + name + ".obj": cap for name, cap in zip(TU_NAMES, OBJECT_CAPS)}
    caps.update({"bin/xar_ck3_bridge.dll": 25165824, "bin/xar_ck3_bridge.map": 33554432, "bin/xar_ck3_bridge.lib": 8192, "bin/xar_ck3_bridge.exp": 8192, "native32-link.rsp": 65536})
    return caps


def enforce_budget() -> int:
    caps = allowed_caps()
    aggregate = {".msvc-temp": 0, "logs": 0, "metadata": 0, "commands": 0}
    allocated = 0
    for path in ROOT.rglob("*"):
        require(not path.is_symlink(), "unexpected output link")
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT).as_posix()
        size = path.stat().st_size
        allocated += (size + 4095) // 4096 * 4096
        if rel in caps:
            require(size <= caps[rel], "output leaf cap exceeded: " + rel)
        else:
            prefix = rel.split("/", 1)[0]
            if prefix in aggregate:
                aggregate[prefix] += (size + 4095) // 4096 * 4096
            else:
                require(rel in ("PLAN01.json", "PLAN02.json", PLAN_NAME, "PLAN-QUALIFICATION01.json", "PRODUCTION-RESULT01.json", "FAILED01.json"), "unexpected output: " + rel)
                aggregate["metadata"] += (size + 4095) // 4096 * 4096
    require(aggregate[".msvc-temp"] <= 33554432, "temporary cap exceeded")
    require(aggregate["logs"] <= 917504, "joint logs cap exceeded")
    require(aggregate["metadata"] + aggregate["commands"] <= 524288, "joint metadata cap exceeded")
    require(allocated + 1048576 <= HARD, "phase hard cap exceeded")
    return allocated + 1048576


def make_plan() -> FilePin:
    require(not ROOT.exists() or set(path.name for path in ROOT.iterdir()) <= {"PLAN01.json", "PLAN02.json", "PLAN-QUALIFICATION01.json"}, "new build root may hold only superseded plan metadata")
    sources = source_inputs()
    build = recipe()
    checked_pin(Path(__file__), Path(__file__).stat().st_size, digest(Path(__file__)))
    arguments = tuple(dict.fromkeys(arg for item in build.compilation for arg in item.argv))
    plan = {
        "schema": "xar.native32.offline-production-plan/v1", "machine_id": MACHINE,
        "observed_at_utc": now(), "review_at_utc": DEADLINE.isoformat(), "hard_bytes": HARD,
        "root": str(ROOT), "producer": pin(Path(__file__)), "source_inputs": sources,
        "argv_string_table": arguments,
        "compilation": [{"name": r.name, "argv_indices": [arguments.index(arg) for arg in r.argv], "source": str(r.source), "object": str(r.object_path), "object_cap": r.object_cap} for r in build.compilation],
        "link_arguments_sha256": hashlib.sha256(json.dumps(build.link_arguments, separators=(",", ":")).encode()).hexdigest(),
        "reused_input_count": len(build.reused_inputs),
        "link_derivation": "adapt_link(exact original_rsp.splitlines(), fixed root); substitute four Native31 objects once, preserve other arguments except fixed output paths, remove PDB, append DEBUG:NONE",
        "original_rsp": pin(OLD / "native31-link.rsp"), "joint_leaf_upper": 120422400,
        "leaf_caps": allowed_caps(), "TMP_cap": 33554432, "logs_cap": 917504, "metadata_cap": 524288,
        "Game_calls": 0, "DLL_loads": 0, "runtime_qualified": False, "drain_fence": False,
        "compile_release_required": True, "original_producer_reused": False,
    }
    ROOT.mkdir(exist_ok=True)
    return write_json(PLAN_NAME, plan, 24576)


def initialize_environment() -> dict[str, str]:
    for key in ("CL", "_CL_", "LINK"):
        require(not os.environ.get(key), "ambient compiler option: " + key)
    temp = ROOT / ".msvc-temp"
    temp.mkdir()
    vcvars = Path("C:/Program Files/Microsoft Visual Studio/18/Community/VC/Auxiliary/Build/vcvars64.bat")
    script = temp / "capture-environment.cmd"
    script.write_bytes((f'@echo off\r\ncall "{vcvars}" >nul\r\nif errorlevel 1 exit /b %errorlevel%\r\nset\r\n').encode())
    env = dict(os.environ)
    env.update(TMP=str(temp), TEMP=str(temp), VSLANG="1033", PYTHONDONTWRITEBYTECODE="1")
    captured = subprocess.run([env.get("COMSPEC", "cmd.exe"), "/d", "/u", "/c", str(script)], cwd=ROOT, env=env, capture_output=True, check=True, timeout=60)
    for line in captured.stdout.decode("utf-16-le").splitlines():
        if "=" in line and not line.startswith("="):
            key, value = line.split("=", 1)
            env[key.upper()] = value
    env.update(TMP=str(temp), TEMP=str(temp), VSLANG="1033")
    return env


def run_command(name: str, argv: Sequence[str], env: dict[str, str]) -> dict[str, object]:
    require(datetime.now(timezone.utc) < DEADLINE, "execution review deadline reached")
    enforce_budget()
    path = ROOT / "logs" / (name + ".log")
    path.parent.mkdir(exist_ok=True)
    start = now()
    peak = 0
    with path.open("xb") as log:
        process = subprocess.Popen(list(argv), cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
        try:
            while process.poll() is None:
                peak = max(peak, enforce_budget())
                require(datetime.now(timezone.utc) < DEADLINE, "execution review deadline reached")
                time.sleep(0.1)
            rc = process.wait()
        except BaseException:
            process.kill()
            process.wait()
            raise
    peak = max(peak, enforce_budget())
    result: dict[str, object] = {"command": list(argv), "start": start, "end": now(), "return_code": rc, "peak_sampled_upper_bytes": peak, "log": pin(path)}
    write_json("commands/" + name + ".json", result, 16384)
    require(rc == 0, name + " returned " + str(rc))
    return result


def pe_exports(path: Path) -> tuple[list[Export], int]:
    data = path.read_bytes()
    require(data[:2] == b"MZ", "DOS header missing")
    nt = struct.unpack_from("<I", data, 60)[0]
    require(data[nt:nt + 4] == b"PE\0\0", "PE header missing")
    machine, sections, _, _, _, opt_size, characteristics = struct.unpack_from("<HHIIIHH", data, nt + 4)
    optional = nt + 24
    require(machine == 0x8664 and struct.unpack_from("<H", data, optional)[0] == 0x20B and bool(characteristics & 0x2000), "x64 DLL required")
    flags = struct.unpack_from("<H", data, optional + 70)[0]
    require(flags & 0x160 == 0x160, "ASLR/NX/high entropy flags missing")
    table: list[tuple[int, int, int, int]] = []
    for index in range(sections):
        section = optional + opt_size + index * 40
        virtual_size, rva, raw_size, raw = struct.unpack_from("<IIII", data, section + 8)
        protection = struct.unpack_from("<I", data, section + 36)[0]
        table.append((rva, max(virtual_size, raw_size), raw, protection))
    def offset(rva: int) -> int:
        for start, size, raw, _ in table:
            if start <= rva < start + size:
                result = raw + rva - start
                require(result < len(data), "PE RVA outside file")
                return result
        raise ValueError("PE RVA unmapped")
    def cstring(rva: int) -> str:
        start = offset(rva)
        end = data.index(b"\0", start, min(start + 256, len(data)))
        return data[start:end].decode("ascii")
    export_rva, export_size = struct.unpack_from("<II", data, optional + 112)
    export = offset(export_rva)
    _, _, _, _, _, _, function_count, name_count, functions, names, ordinals = struct.unpack_from("<IIHHIIIIIII", data, export)
    require(name_count == 6 and function_count == 6, "exact six exports required")
    result: list[Export] = []
    for index in range(name_count):
        name = cstring(struct.unpack_from("<I", data, offset(names) + index * 4)[0])
        ordinal = struct.unpack_from("<H", data, offset(ordinals) + index * 2)[0]
        require(ordinal < function_count, "export ordinal outside table")
        rva = struct.unpack_from("<I", data, offset(functions) + ordinal * 4)[0]
        execute = any(start <= rva < start + size and bool(protection & 0x20000000) for start, size, _, protection in table)
        result.append(Export(name, hex(rva), execute, export_rva <= rva < export_rva + export_size))
    require(frozenset(x.name for x in result) == EXPECTED_EXPORTS, "export names differ")
    require(all(not x.forwarded and x.executable == (x.name != "XarRefillCoreCarrier12004") for x in result), "export section/forwarder mismatch")
    return result, flags


def core_link_proof(core: Path, dll: Path, map_text: str) -> list[dict[str, object]]:
    """Bind essential compiled core COMDAT bytes and relocations to linked DLL.

    This qualifies artifact inclusion, not runtime execution or queue draining.
    """
    obj = core.read_bytes()
    image = dll.read_bytes()
    machine, count, _, symbols_at, symbol_count, opt, _ = struct.unpack_from("<HHIIIHH", obj, 0)
    require(machine == 0x8664 and opt == 0, "ordinary x64 COFF object required")
    strings_at = symbols_at + symbol_count * 18
    sections = [struct.unpack_from("<8sIIIIIIHHI", obj, 20 + i * 40) for i in range(count)]
    symbols: list[tuple[str, int, int]] = []
    symbols = [("", 0, 0)] * symbol_count
    index = 0
    while index < symbol_count:
        raw, value, section, _, _, auxiliaries = struct.unpack_from("<8sIhHBB", obj, symbols_at + index * 18)
        if raw[:4] == b"\0" * 4:
            start = strings_at + struct.unpack_from("<I", raw, 4)[0]
            name = obj[start:obj.index(b"\0", start)].decode("ascii", errors="replace")
        else:
            name = raw.rstrip(b"\0").decode("ascii", errors="replace")
        symbols[index] = (name, value, section)
        index += 1 + auxiliaries
    nt = struct.unpack_from("<I", image, 60)[0]
    opt_at = nt + 24
    section_count = struct.unpack_from("<H", image, nt + 6)[0]
    opt_size = struct.unpack_from("<H", image, nt + 20)[0]
    image_base = struct.unpack_from("<Q", image, opt_at + 24)[0]
    def image_offset(rva: int) -> int:
        for i in range(section_count):
            at = opt_at + opt_size + i * 40
            virtual_size, start, raw_size, raw = struct.unpack_from("<IIII", image, at + 8)
            if start <= rva < start + max(virtual_size, raw_size):
                return int(raw) + rva - int(start)
        raise ValueError("linked function RVA unmapped")
    mapped: dict[str, int] = {}
    for line in map_text.splitlines():
        match = re.match(r"\s+[0-9A-Fa-f]+:[0-9A-Fa-f]+\s+(\S+)\s+([0-9A-Fa-f]{16})\s", line)
        if match:
            mapped[match[1]] = int(match[2], 16) - image_base
    records: list[dict[str, object]] = []
    for simple in ("ForwardExecute", "ForwardAppend", "Enter", "DiagnosticFrame"):
        matches = [(name, value, section) for name, value, section in symbols if name.startswith("?" + simple + "@time_observer31@") and section > 0]
        require(len(matches) == 1, "core symbol missing/ambiguous: " + simple)
        name, value, section_number = matches[0]
        require(name in mapped, "core symbol not linked: " + simple)
        section = sections[section_number - 1]
        raw_size, raw_at, rel_at, relocations = section[3], section[4], section[5], section[7]
        require(value == 0 and raw_size > 0, "expected function COMDAT layout")
        body = bytearray(obj[raw_at:raw_at + raw_size])
        linked_at = image_offset(mapped[name])
        linked = bytearray(image[linked_at:linked_at + raw_size])
        verified = 0
        for index in range(relocations):
            address, target_index, kind = struct.unpack_from("<IIH", obj, rel_at + index * 10)
            require(kind in (1, 2, 3, 4, 5, 6, 7, 8, 9) and address + (8 if kind == 1 else 4) <= raw_size, "unsupported COFF relocation")
            width = 8 if kind == 1 else 4
            target, target_value, _ = symbols[target_index]
            if target in mapped and 4 <= kind <= 9:
                addend = int.from_bytes(body[address:address + 4], "little", signed=True)
                actual = int.from_bytes(linked[address:address + 4], "little", signed=True)
                expected = mapped[target] + addend - (mapped[name] + address + 4 + kind - 4)
                require(actual == expected, "linked relocation target differs: " + target)
                verified += 1
            body[address:address + width] = b"\0" * width
            linked[address:address + width] = b"\0" * width
        require(body == linked, "linked core function bytes differ: " + simple)
        require(verified > 0, "no linked relocation verified: " + simple)
        records.append({"function": simple, "symbol": name, "bytes": raw_size, "normalized_sha256": hashlib.sha256(body).hexdigest(), "linked_rva": str(mapped[name]), "verified_target_relocations": verified, "all_nonrelocation_bytes_equal": True})
    return records


def execute(admission: Path, admission_sha: str) -> FilePin:
    require(re.fullmatch(r"[0-9a-f]{64}", admission_sha) is not None, "exact execution-card SHA required")
    card = pin(admission)
    require(card["sha256"] == admission_sha, "execution-card pin differs")
    scope = validate_admission(read_object(admission), digest(ROOT / PLAN_NAME), digest(Path(__file__)))
    require(datetime.now(timezone.utc) < DEADLINE, "execution review deadline reached")
    source = source_inputs()
    build = recipe()
    plan = read_object(ROOT / PLAN_NAME)
    require(plan.get("machine_id") == MACHINE and plan.get("root") == str(ROOT), "plan machine/root differs")
    require(plan.get("source_inputs") == source, "plan source input drift")
    actual_plan = object_map(plan.get("producer"))
    require(actual_plan.get("sha256") == digest(Path(__file__)), "producer differs from plan")
    require(not (ROOT / "obj").exists() and not (ROOT / "bin").exists(), "build is not create-only fresh")
    inputs = [pin(path) for path in build.reused_inputs]
    before = pinned_input_identities(inputs)
    write_json("metadata/INPUTS01.json", {"machine_id": MACHINE, "observed_at_utc": now(), "reused_inputs": inputs}, 196608)
    env = initialize_environment()
    compiler = Path(build.compilation[0].argv[0])
    require(shutil.which("cl.exe", path=env.get("PATH")) == str(compiler), "vcvars selected a different compiler")
    linker = compiler.with_name("link.exe")
    tools = [pin(compiler), pin(linker), pin(compiler.with_name("dumpbin.exe"))]
    receipts: list[dict[str, object]] = []
    for item in build.compilation:
        item.object_path.parent.mkdir(exist_ok=True)
        receipts.append(run_command("native32-" + item.name, item.argv, env))
        require(item.object_path.is_file(), "compiler object missing")
    rsp = ROOT / "native32-link.rsp"
    with rsp.open("xb") as handle:
        handle.write(("\n".join(subprocess.list2cmdline([x]) for x in build.link_arguments) + "\n").encode())
    (ROOT / "bin").mkdir()
    receipts.append(run_command("native32-link", (str(linker), "/nologo", "@" + str(rsp)), env))
    for path, original in before.items():
        require(identity(path) == original, "reused input changed during build: " + str(path))
    require(source_inputs() == source, "source changed during build")
    text = (ROOT / "bin/xar_ck3_bridge.map").read_text(errors="strict")
    require(all("native32-" + name + ".obj" in text for name in TU_NAMES), "new direct TU missing from MAP")
    log = (ROOT / "logs/native32-link.log").read_text(errors="strict")
    pattern = r"xar_ck3_12002_runtime(?:\.lib)?[:(]ck3_12002_commands"
    require(re.search(pattern, text, re.I) is None and re.search(pattern, log, re.I) is None, "old commands archive member extracted")
    dll = ROOT / "bin/xar_ck3_bridge.dll"
    exports, flags = pe_exports(dll)
    proof = core_link_proof(ROOT / "obj/native32-core.obj", dll, text)
    require(not list(ROOT.rglob("*.pdb")) and not list(ROOT.rglob("*.ilk")), "unadmitted debug output")
    output = {
        "schema": "xar.native32.offline-production-result/v1", "machine_id": MACHINE,
        "observed_at_utc": now(), "status": "OFFLINE_ARTIFACT_QUALIFIED_NOT_DEPLOYED",
        "producer": pin(Path(__file__)), "plan": pin(ROOT / PLAN_NAME), "execution_card": card, "execution_scope": scope,
        "sources": source, "tools": tools, "commands": receipts, "inputs": pin(ROOT / "metadata/INPUTS01.json"),
        "objects": [pin(item.object_path) for item in build.compilation],
        "outputs": [pin(ROOT / "bin" / ("xar_ck3_bridge" + suffix)) for suffix in (".dll", ".map", ".lib", ".exp")],
        "exports": [asdict(item) for item in exports], "PE_DLL_characteristics": hex(flags),
        "core_link_proof": proof, "original_807_overlay_preserved": True,
        "reused_inputs_before_after_stat_equal": True, "all_four_header_consumers_recompiled": True,
        "original_producer_reused": False, "old_commands_archive_member_extracted": False,
        "sampled_upper_before_result_receipt_bytes": enforce_budget(), "hard_bytes": HARD,
        "runtime_qualified": False, "Game_calls": 0, "DLL_loads": 0,
        "deployment_changes": 0, "drain_fence": False, "performance_goal_qualified": False,
    }
    result = write_json("PRODUCTION-RESULT01.json", output, 65536)
    enforce_budget()
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("plan", "build"))
    parser.add_argument("--admission", type=Path)
    parser.add_argument("--admission-sha256")
    args = parser.parse_args()
    if args.phase == "plan":
        print(json.dumps(make_plan(), sort_keys=True))
        return 0
    require(isinstance(args.admission, Path) and isinstance(args.admission_sha256, str), "build requires owner-supplied exact execution-card pin")
    try:
        print(json.dumps(execute(args.admission, args.admission_sha256), sort_keys=True))
    except BaseException as error:
        if ROOT.is_dir() and not (ROOT / "FAILED01.json").exists():
            write_json("FAILED01.json", {"machine_id": MACHINE, "observed_at_utc": now(), "error_type": type(error).__name__, "error": str(error), "runtime_qualified": False, "original_failure_preserved": True}, 8192)
        raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
