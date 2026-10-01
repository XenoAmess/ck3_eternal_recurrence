"""Read-only consumption of the authoritative 1.20 core clock ABI."""
from __future__ import annotations

import ctypes
import hashlib
from pathlib import Path
import re
import struct

NATIVE_ROOT = Path(__file__).resolve().parents[1] / "ck3_autonomous_player/native_bridge"
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010


def _one(pattern: str, text: str) -> str:
    matches = re.findall(pattern, text)
    if len(matches) != 1:
        raise RuntimeError("authoritative native clock source contract changed")
    return matches[0]


def source_contract(game_version: str = "1.20.0.2") -> dict:
    if game_version not in {"1.20.0.2", "1.20.0.3"}:
        raise RuntimeError("read-only clock requires an exact authoritative 1.20 build")
    header_path = NATIVE_ROOT / "include/xar_bridge/ck3_12002.hpp"
    source_path = NATIVE_ROOT / "src/ck3_12002.cpp"
    identity_header_path = NATIVE_ROOT / (
        "include/xar_bridge/ck3_12003.hpp" if game_version == "1.20.0.3"
        else "include/xar_bridge/ck3_12002.hpp"
    )
    header_bytes, source_bytes = header_path.read_bytes(), source_path.read_bytes()
    identity_header_bytes = identity_header_path.read_bytes()
    header, source = header_bytes.decode("utf-8-sig"), source_bytes.decode("utf-8-sig")
    contract = {"executable_sha256": _one(r'kExecutableSha256\[\]\s*=\s*"([A-F0-9]{64})"', identity_header_bytes.decode("utf-8-sig")),
                "game_version": game_version,
                "identity_header_path": identity_header_path.relative_to(NATIVE_ROOT).as_posix(),
                "identity_header_sha256": hashlib.sha256(identity_header_bytes).hexdigest(),
                "layout_header_path": header_path.relative_to(NATIVE_ROOT).as_posix(),
                "layout_source_path": source_path.relative_to(NATIVE_ROOT).as_posix(),
                "header_sha256": hashlib.sha256(header_bytes).hexdigest(),
                "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
                "reader_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    for key, name in (("jomini_slot", "kJominiStateSlotRva"), ("game_slot", "kGameStateSlotRva"),
                      ("player_manager", "kPlayerCharacterManagerOffset")):
        contract[key] = int(_one(rf"{name}\s*=\s*(0x[0-9A-Fa-f]+)", header), 16)
    contract["speed_offset"] = int(_one(r"&native_speed, game_state\.data\(\) \+ (0x[0-9A-Fa-f]+)", source), 16)
    contract["date_offset"] = int(_one(r"&output\.date_raw, game_state\.data\(\) \+ (0x[0-9A-Fa-f]+)", source), 16)
    contract["paused_offset"] = int(_one(r"output\.paused = jomini_state\[(0x[0-9A-Fa-f]+)\]", source), 16)
    # These are the same readiness reads used by ReadCoreSnapshot. Freeze
    # their production source expressions before using them outside the DLL.
    for expression in ("LoadAt<void *>(jomini_state, 0x18)", "LoadAt<std::int32_t>(players, 0x1F0)",
                       "LoadAt<void *>(game_state, 0xA0)", "LoadAt<void *>(manager, 0x58)",
                       "LoadAt<std::int32_t>(manager, 0x64)", "LoadAt<std::int32_t>(entry, 0xD8)",
                       "LoadAt<std::int32_t>(entry, 0xB0)", "native_speed < 0 || native_speed > 4",
                       "output.speed = native_speed + 1"):
        if expression not in source:
            raise RuntimeError("authoritative native campaign readiness contract changed")
    return contract


def decode_clock(game: bytes, jomini: bytes, contract: dict) -> dict:
    date_offset, speed_offset, paused_offset = (contract[key] for key in ("date_offset", "speed_offset", "paused_offset"))
    if len(game) < max(date_offset, speed_offset) + 4 or len(jomini) <= paused_offset:
        raise RuntimeError("native clock prefix is incomplete")
    raw_date = struct.unpack_from("<i", game, date_offset)[0]
    speed = struct.unpack_from("<i", game, speed_offset)[0]
    if raw_date <= 0 or not 0 <= speed <= 4:
        raise RuntimeError("native clock is not initialized or has an invalid speed")
    return {"date_raw": raw_date, "speed": speed + 1, "paused": jomini[paused_offset] != 0}


def read_bound_clock(reader, contract: dict) -> dict:
    def pointer(address: int) -> int:
        value = struct.unpack("<Q", reader.read(address, 8))[0]
        if value == 0:
            raise RuntimeError("native campaign pointer is null")
        return value
    def integer(address: int) -> int:
        return struct.unpack("<i", reader.read(address, 4))[0]
    base = reader.image_base
    game = pointer(base + contract["game_slot"])
    jomini = pointer(base + contract["jomini_slot"])
    players = pointer(jomini + 0x18)
    local_player_id = integer(players + 0x1F0)
    if local_player_id < 0:
        raise RuntimeError("native local player is not initialized")
    data = pointer(game + 0xA0)
    manager = data + contract["player_manager"]
    entries, count = pointer(manager + 0x58), integer(manager + 0x64)
    if not 0 < count <= 1024:
        raise RuntimeError("native played-character collection is not initialized")
    played_id = None
    for index in range(count):
        entry = struct.unpack("<Q", reader.read(entries + index * 8, 8))[0]
        if entry != 0 and integer(entry + 0xD8) == local_player_id:
            played_id = integer(entry + 0xB0)
            break
    if played_id is None or played_id < 0:
        raise RuntimeError("native campaign has no bound played character")
    previous = None
    for _ in range(3):
        game_bytes = reader.read(game, max(contract["date_offset"], contract["speed_offset"]) + 4)
        jomini_bytes = reader.read(jomini, contract["paused_offset"] + 1)
        current = decode_clock(game_bytes, jomini_bytes, contract)
        if previous == current:
            if (pointer(base + contract["game_slot"]) != game
                    or pointer(base + contract["jomini_slot"]) != jomini
                    or integer(players + 0x1F0) != local_player_id):
                raise RuntimeError("native campaign changed during clock read")
            return {**current, "local_player_id": local_player_id, "played_character_id": played_id,
                    "clock_prefix_sha256": hashlib.sha256(game_bytes + jomini_bytes).hexdigest(),
                    "source_contract": contract, "process_access": PROCESS_QUERY_INFORMATION | PROCESS_VM_READ,
                    "calendar_projection": "unbound_requires_independent_save_date", "raw_units_per_day": 24}
        previous = current
    raise RuntimeError("native clock did not stabilize within the bounded read")


class WindowsReadOnlyMemory:
    def __init__(self, pid: int, executable: str) -> None:
        import win32process
        self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        self.kernel.OpenProcess.argtypes = [ctypes.c_uint32, ctypes.c_bool, ctypes.c_uint32]
        self.kernel.OpenProcess.restype = ctypes.c_void_p
        self.kernel.ReadProcessMemory.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
                                                 ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
        self.kernel.ReadProcessMemory.restype = ctypes.c_bool
        self.kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        self.kernel.CloseHandle.restype = ctypes.c_bool
        self.handle = self.kernel.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            modules = win32process.EnumProcessModules(self.handle)
            if not modules or Path(win32process.GetModuleFileNameEx(self.handle, modules[0])).resolve() != Path(executable).resolve():
                raise RuntimeError("native main module does not match the frozen executable")
            self.image_base = int(modules[0])
        except Exception:
            self.close()
            raise

    def read(self, address: int, size: int) -> bytes:
        buffer = ctypes.create_string_buffer(size)
        read_size = ctypes.c_size_t()
        if not self.kernel.ReadProcessMemory(self.handle, address, buffer, size, ctypes.byref(read_size)) or read_size.value != size:
            raise RuntimeError("native read failed or returned incomplete bytes")
        return buffer.raw

    def close(self) -> None:
        if self.handle is not None:
            self.kernel.CloseHandle(self.handle)
            self.handle = None


def read_live_clock(pid: int, executable: str, executable_sha256: str, game_version: str) -> dict:
    contract = source_contract(game_version)
    if executable_sha256.upper() != contract["executable_sha256"]:
        raise RuntimeError("read-only clock requires the exact authoritative native build")
    reader = WindowsReadOnlyMemory(pid, executable)
    try:
        return read_bound_clock(reader, contract)
    finally:
        reader.close()
