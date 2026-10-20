"""Prepare a frozen, typed native Steam receipt guard for the A13 supervisor."""
from __future__ import annotations

import ast
import ctypes
from ctypes import wintypes
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys

_TOOLS = Path(__file__).resolve().parents[1]
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))
from steam_offline_state_contract import (
    ProbeResult, decimal, exact_int, object_map, parse_result, text,
)
from steam_offline_native_provider_v1 import (
    IMAGE_BYTES, IMAGE_SHA256, IMAGE_SIZE, PRODUCER, PRODUCER_RVA, STEAM_VERSION,
    TRAY_MANAGER_RVA, TRAY_OFFSET, VALUE_RVA,
)


@dataclass(frozen=True)
class CurrentSteamGeneration:
    pid: int
    birth_filetime: str
    exe: str


@dataclass(frozen=True)
class CurrentSteamSourceStat:
    bytes: int
    file_id: str
    mtime_ns: str


def steam_native_utc(value: str) -> datetime:
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None or result.utcoffset() != timezone.utc.utcoffset(result):
        raise ValueError("Steam observation requires explicit UTC")
    return result


def validate_steam_native_launch_document(
    value: object, *, machine_id: str, at_utc: datetime,
    current_steam: CurrentSteamGeneration,
    current_source_stat: CurrentSteamSourceStat, max_age_seconds: int = 600,
) -> ProbeResult:
    """Validate the shared V2 wire contract and fresh, current OS bindings."""
    exact_int(max_age_seconds, 1, 600)
    if at_utc.tzinfo is None or at_utc.utcoffset() != timezone.utc.utcoffset(at_utc):
        raise ValueError("launch clock requires explicit UTC")
    proof = parse_result(value)
    if (proof.status != "offline" or proof.reason != "observed" or
            proof.observation_method != "native_current_user_byte" or
            proof.machine_id != machine_id or proof.steam is None or
            proof.source is None or proof.native_evidence is None):
        raise ValueError("fresh native offline observation required")
    age = (at_utc - steam_native_utc(proof.observed_at_utc)).total_seconds()
    if not -10 <= age <= max_age_seconds:
        raise ValueError("native Steam observation expired or lies in the future")
    identity, source, evidence = proof.steam, proof.source, proof.native_evidence
    if (identity.file_version != STEAM_VERSION or source.bytes != IMAGE_BYTES or
            source.sha256 != IMAGE_SHA256 or evidence.module_size != IMAGE_SIZE or
            evidence.value_rva != str(VALUE_RVA) or
            evidence.producer_rva != str(PRODUCER_RVA) or
            evidence.producer_anchor_hex != PRODUCER.hex() or
            evidence.tray_manager_pointer_rva != str(TRAY_MANAGER_RVA) or
            evidence.tray_state_offset != str(TRAY_OFFSET)):
        raise ValueError("native Steam source registry does not match the qualified provider")
    pid = exact_int(current_steam.pid, 1, 2**32-1)
    birth = decimal(current_steam.birth_filetime, maximum=2**64-1)
    if (identity.pid != pid or identity.birth_filetime != birth or
            os.path.normcase(os.path.abspath(identity.exe)) !=
            os.path.normcase(os.path.abspath(text(current_steam.exe)))):
        raise ValueError("current Steam process generation differs from native observation")
    actual_stat = (
        exact_int(current_source_stat.bytes, 1, 2**53-1),
        decimal(current_source_stat.file_id),
        decimal(current_source_stat.mtime_ns, maximum=2**64-1),
    )
    if actual_stat != (source.bytes, source.file_id, source.mtime_ns):
        raise ValueError("current SteamUI file identity differs from native observation")
    return proof


def steam_native_require_running(wait_result: object) -> None:
    """Only a non-signaled process handle proves the generation is still running."""
    exact_int(wait_result, 258, 258)


def steam_native_current_generation(pid: int) -> CurrentSteamGeneration:
    """Query PID/birth/image only; no UI, focus, screenshot or process memory."""
    exact_int(pid, 1, 2**32-1)
    if os.name != "nt":
        raise ValueError("current Steam generation query requires Windows")
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.GetProcessTimes.argtypes = [
        wintypes.HANDLE, ctypes.POINTER(wintypes.FILETIME),
        ctypes.POINTER(wintypes.FILETIME), ctypes.POINTER(wintypes.FILETIME),
        ctypes.POINTER(wintypes.FILETIME),
    ]
    kernel.GetProcessTimes.restype = wintypes.BOOL
    kernel.QueryFullProcessImageNameW.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    kernel.QueryFullProcessImageNameW.restype = wintypes.BOOL
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.WaitForSingleObject.restype = wintypes.DWORD
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    handle = kernel.OpenProcess(0x00101000, False, pid)
    if not handle:
        raise ValueError("current Steam process cannot be queried")
    try:
        steam_native_require_running(kernel.WaitForSingleObject(handle, 0))
        birth, exit_time = wintypes.FILETIME(), wintypes.FILETIME()
        kernel_time, user_time = wintypes.FILETIME(), wintypes.FILETIME()
        if not kernel.GetProcessTimes(handle, ctypes.byref(birth),
                ctypes.byref(exit_time), ctypes.byref(kernel_time), ctypes.byref(user_time)):
            raise ValueError("current Steam creation time unavailable")
        output = ctypes.create_unicode_buffer(32768)
        length = wintypes.DWORD(len(output))
        if not kernel.QueryFullProcessImageNameW(handle, 0, output, ctypes.byref(length)):
            raise ValueError("current Steam image unavailable")
        created = (int(birth.dwHighDateTime) << 32) | int(birth.dwLowDateTime)
        result = CurrentSteamGeneration(pid, str(created), str(Path(output.value).resolve()))
        steam_native_require_running(kernel.WaitForSingleObject(handle, 0))
        return result
    finally:
        kernel.CloseHandle(handle)


def require_steam_native_launch_v1(
    path: Path, expected_ref: object, *, machine_id: str, at_utc: datetime,
    max_age_seconds: int = 600,
) -> ProbeResult:
    """Read the exact immutable artifact on every launch check, not a cached result."""
    reference = object_map(expected_ref)
    if set(reference) != {"path", "bytes", "sha256"}:
        raise ValueError("exact native Steam reference required")
    if path.resolve() != Path(text(reference["path"])).resolve():
        raise ValueError("native Steam input path differs from launch configuration")
    size = exact_int(reference["bytes"], 1, 8192)
    digest = text(reference["sha256"])
    before = path.stat()
    if before.st_size != size:
        raise ValueError("native Steam receipt size differs")
    payload = path.read_bytes()
    after = path.stat()
    if ((before.st_ino, before.st_mtime_ns, before.st_size) !=
            (after.st_ino, after.st_mtime_ns, after.st_size) or
            len(payload) != size or hashlib.sha256(payload).hexdigest() != digest):
        raise ValueError("native Steam receipt identity or bytes changed")
    raw: object = json.loads(payload)
    proof = parse_result(raw)
    if proof.steam is None or proof.source is None:
        raise ValueError("native Steam process/source missing")
    generation = steam_native_current_generation(proof.steam.pid)
    stat = Path(proof.source.path).stat()
    current_stat = CurrentSteamSourceStat(
        stat.st_size, str(stat.st_ino), str(stat.st_mtime_ns))
    return validate_steam_native_launch_document(
        raw, machine_id=machine_id, at_utc=at_utc,
        current_steam=generation, current_source_stat=current_stat,
        max_age_seconds=max_age_seconds,
    )


def _steam_replace_once(source: str, before: str, after: str) -> str:
    if source.count(before) != 1:
        raise ValueError("unknown or duplicate A12 Steam seam")
    return source.replace(before, after, 1)


def _steam_ast_source(source: str, name: str) -> str:
    nodes = [node for node in ast.parse(source).body
             if isinstance(node, (ast.ClassDef, ast.FunctionDef)) and node.name == name]
    if len(nodes) != 1:
        raise ValueError("missing unique typed native Steam source: " + name)
    node = nodes[0]
    first = node.lineno
    if node.decorator_list:
        first = min(first, *(item.lineno for item in node.decorator_list))
    return "\n".join(source.splitlines()[first-1:node.end_lineno])


def render_supervisor_patch(
    source: bytes, contract_source: bytes, provider_source: bytes,
) -> bytes:
    """Finite A12-template transform; preserve the historical A05 failure record."""
    code = source.decode("utf-8")
    contract = contract_source.decode("utf-8")
    provider = provider_source.decode("utf-8")
    if hashlib.sha256(contract_source).hexdigest() != "148ae6aaed58b54d69c2d618d31ed1ab9e8499e057ab4c1f2657b05c7e54170b":
        raise ValueError("shared Steam contract source not qualified")
    if hashlib.sha256(provider_source).hexdigest() != "b1c02586f60d4ba1a4b32aa26d695b22dd2a3ce647f7a66e0994afb92ff9e50a":
        raise ValueError("native Steam registry source not qualified")
    old = """    confirmation = screen.get("offline_confirmation") or {}
    attested = False
    pixels = (screen.get("personally_reviewed_offline_pixels") is True
              and screen.get("fresh_window_pixel_change_verified") is True)
    if (screen.get("status") != "ACQUIRED" or screen.get("git_head") != head
            or Path(screen["repo"]).resolve() != repo or type(screen.get("sequence")) is not int or screen["sequence"] <= 0
            or not pixels):
        raise ValueError("Root actual fresh offline/screen CAS admission is incomplete")
    def guard(*, screen_pixels=False):"""
    new = """    if (screen.get("status") != "ACQUIRED" or screen.get("git_head") != head
            or Path(screen["repo"]).resolve() != repo or type(screen.get("sequence")) is not int or screen["sequence"] <= 0):
        raise ValueError("Root Game/capture resource CAS admission is incomplete")
    def guard(*, steam_native_state=False):"""
    code = _steam_replace_once(code, old, new)
    code = _steam_replace_once(code,
        """        if screen_pixels and pixels and not -10 <= (now() - stamp(screen["at_utc"])).total_seconds() <= 600:
            raise RuntimeError("actual offline pixels expired before Game launch; no automatic retry")""",
        """        if steam_native_state:
            require_steam_native_launch_v1(args.steam_native_state,
                config["steam_native_state"], machine_id=MACHINE, at_utc=now())""")
    if code.count("guard(screen_pixels=True)") != 4:
        raise ValueError("unknown native Steam prelaunch guard count")
    code = code.replace("guard(screen_pixels=True)", "guard(steam_native_state=True)")
    code = _steam_replace_once(code,
        """        "offline_basis": "user_attestation" if attested else "reviewed_fresh_pixels",
        "offline_confirmation": confirmation if attested else None,
        "fresh_offline_pixels_confirmed": pixels,""",
        """        "offline_basis": "native_current_user_byte",
        "steam_native_state": config["steam_native_state"],
        "screen_admission_role": "Game_and_recording_resource_lease",""")
    code = _steam_replace_once(code,
        '("clean-source-freeze", "screen-admission", "launch-config")',
        '("clean-source-freeze", "screen-admission", "launch-config", "steam-native-state")')
    # Explicitly keep the pre-existing receipt scope limited to those three files;
    # the external native probe has its own exact launch-config reference.
    contract = _steam_replace_once(contract, "from __future__ import annotations\n", "")
    registry_names = {
        "IMAGE_BYTES", "IMAGE_SHA256", "IMAGE_SIZE", "PRODUCER", "PRODUCER_RVA",
        "STEAM_VERSION", "TRAY_MANAGER_RVA", "TRAY_OFFSET", "VALUE_RVA",
    }
    registry: list[str] = []
    for node in ast.parse(provider).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            if node.targets[0].id in registry_names:
                part = ast.get_source_segment(provider, node)
                if part is None: raise ValueError("incomplete native Steam registry")
                registry.append(part)
    if len(registry) != len(registry_names):
        raise ValueError("incomplete native Steam registry")
    own = Path(__file__).read_text(encoding="utf-8")
    names = (
        "CurrentSteamGeneration", "CurrentSteamSourceStat", "steam_native_utc",
        "validate_steam_native_launch_document", "steam_native_require_running",
        "steam_native_current_generation",
        "require_steam_native_launch_v1",
    )
    runtime = (
        "from __future__ import annotations\nimport ctypes,hashlib,json,os\n"
        "from ctypes import wintypes\nfrom datetime import datetime,timezone\n"
        "from pathlib import Path\n" + contract + "\n" +
        "\n".join(registry) + "\n" +
        "\n\n".join(_steam_ast_source(own, name) for name in names) + "\n")
    # The old preparation loader does not register host modules. Own a separate
    # registered namespace so dataclasses work there and in the actual Task.
    identity = hashlib.sha256(runtime.encode("utf-8")).hexdigest()
    module_name = "_xar_frozen_steam_launch_" + identity[:16]
    injected = (
        "\nimport types as _steam_launch_types\n"
        "_steam_launch_module = _steam_launch_types.ModuleType(" + repr(module_name) + ")\n"
        "sys.modules[" + repr(module_name) + "] = _steam_launch_module\n"
        "exec(compile(" + repr(runtime) + ", '<frozen-native-steam-launch>', 'exec', "
        "dont_inherit=True), _steam_launch_module.__dict__)\n"
        "require_steam_native_launch_v1 = _steam_launch_module.require_steam_native_launch_v1\n")
    if "require_steam_native_launch_v1" in source.decode("utf-8"):
        raise ValueError("native Steam guard already present")
    code = _steam_replace_once(code, "def main(args):", injected + "\ndef main(args):")
    historical = "expired offline pixels"
    if code.count(historical) != source.decode("utf-8").count(historical):
        raise ValueError("historical A05 Steam failure evidence changed")
    compile(code, "root_native30_supervisor_c23.py", "exec")
    return code.encode("utf-8")
