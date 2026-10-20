"""Version-bound, read-only SteamUI current-user offline-mode observation.

No Steam interfaces are loaded/called. Only the installed qualified image and
an existing Steam process are read. Code changes and tray transitions fail shut.

Qualified SteamUI 10.96.30.42: producer 616d0c emits bIsOfflineMode from
1123627. Caller 6869df passes object 1123440 to 5d39b0, whose private
GetOfflineMode result writes +1e7. Tray dispatcher 6158e4 selects state 4 with the offline icon. Native zero
is not qualified as online. This observes the native byte,
not an executed App JavaScript getter or network connectivity.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import struct
from typing import Literal, Protocol

from steam_offline_state_contract import (
    NativeEvidence, ProcessIdentity, SourceIdentity, decimal, exact_int, text,
)

IMAGE_SHA256 = "cb387adefbbac64a3c1490d4275d00daf3a1e0219b4580726ef7681db7429278"
IMAGE_BYTES = 18962584
IMAGE_SIZE = 19238912
STEAM_VERSION = "10.96.30.42"
VALUE_RVA = 0x1123627
TRAY_MANAGER_RVA = 0x1121AA0
TRAY_OFFSET = 0x154
PRODUCER_RVA = 0x616D0C
PRODUCER = bytes.fromhex("440fb60513c9b000488d157d3b7400488bcbe81d9e3b00")
# Exact instruction anchors, tied to the full image digest above. In order:
# current-user JSON producer, mode getter writer, global-object refresh caller,
# offline tray-state branch, tray-state compare and store.
ANCHORS: tuple[tuple[int, bytes], ...] = (
    (PRODUCER_RVA, PRODUCER),
    (0x5D39B0, bytes.fromhex(
        "40534883ec20488bd9e852d8f2ff488bc8488b10ff92880000008883e70100004883c4205bc3")),
    (0x6869DF, bytes.fromhex("488d0d5acaa900e8c5cff4ff")),
    (0x6158E4, bytes.fromhex("803d3cddb000007419488b0dacc1b0004533c0ba04000000e81fc7f6ff")),
    (0x582038, bytes.fromhex("8bfa4c8bf1490f45f03b9154010000")),
    (0x582071, bytes.fromhex("4189be54010000")),
)
NativeReason = Literal[
    "unsupported_platform", "invalid_input", "source_not_qualified",
    "steam_instance_changed", "module_changed", "anchor_mismatch",
    "tray_state_unavailable", "native_online_not_qualified", "state_changed", "native_query_failed",
]


class IdentityReader(Protocol):
    def identity(self, pid: int) -> ProcessIdentity: ...
    def file_version(self, path: str) -> str: ...


@dataclass(frozen=True)
class NativeObserved:
    status: Literal["observed"]
    offline_mode: Literal[True]
    steam: ProcessIdentity
    source: SourceIdentity
    evidence: NativeEvidence


@dataclass(frozen=True)
class NativeUnavailable:
    status: Literal["unavailable"]
    reason: NativeReason
    detail: str


NativeProviderResult = NativeObserved | NativeUnavailable


@dataclass(frozen=True)
class Module:
    base: int
    size: int
    path: str


class Backend(Protocol):
    def source(self, path: str) -> SourceIdentity: ...
    def module(self, pid: int, path: str) -> Module: ...
    def open(self, pid: int) -> None: ...
    def read(self, address: int, count: int) -> bytes: ...
    def close(self) -> None: ...


class _ModuleEntry(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD), ("th32ModuleID", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD), ("GlblcntUsage", wintypes.DWORD),
        ("ProccntUsage", wintypes.DWORD), ("modBaseAddr", ctypes.c_void_p),
        ("modBaseSize", wintypes.DWORD), ("hModule", wintypes.HMODULE),
        ("szModule", wintypes.WCHAR * 256), ("szExePath", wintypes.WCHAR * 260),
    ]


def _stamp(path: Path) -> tuple[int, int, int, int, int]:
    value = path.stat()
    return (value.st_size, value.st_mtime_ns, value.st_ctime_ns,
            value.st_ino, value.st_dev)


def _qualified_source(path: str) -> SourceIdentity:
    source_path = Path(path).resolve(strict=True)
    before = _stamp(source_path)
    if before[0] != IMAGE_BYTES:
        raise ValueError("SteamUI size is not qualified")
    with source_path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
        if digest != IMAGE_SHA256:
            raise ValueError("SteamUI digest is not qualified")
        stream.seek(0x3C)
        pe = struct.unpack("<I", stream.read(4))[0]
        stream.seek(pe)
        header = stream.read(24)
        if header[:4] != b"PE\0\0" or struct.unpack_from("<H", header, 4)[0] != 0x8664:
            raise ValueError("expected x64 PE image")
        section_count = struct.unpack_from("<H", header, 6)[0]
        optional_size = struct.unpack_from("<H", header, 20)[0]
        if not 1 <= section_count <= 32 or optional_size < 64:
            raise ValueError("invalid PE shape")
        optional = stream.read(optional_size)
        if (struct.unpack_from("<H", optional)[0] != 0x20B
                or struct.unpack_from("<I", optional, 56)[0] != IMAGE_SIZE):
            raise ValueError("unexpected image layout")
        sections = [struct.unpack("<8sIIIIIIHHI", stream.read(40))
                    for _ in range(section_count)]
        for rva, expected in ANCHORS:
            matched = False
            for section in sections:
                virtual, raw_size, raw_offset = section[2], section[3], section[4]
                if virtual <= rva and rva + len(expected) <= virtual + raw_size:
                    offset = raw_offset + rva - virtual
                    if offset + len(expected) > IMAGE_BYTES:
                        raise ValueError("anchor outside raw file")
                    stream.seek(offset)
                    if stream.read(len(expected)) != expected:
                        raise ValueError("file instruction anchor mismatch")
                    matched = True
                    break
            if not matched:
                raise ValueError("instruction anchor has no raw bytes")
    if before != _stamp(source_path):
        raise ValueError("SteamUI changed while qualifying")
    return SourceIdentity(str(source_path), before[0], digest, str(before[3]), str(before[1]))


class WindowsBackend:
    """Narrow Win32 boundary: module snapshots and bounded ReadProcessMemory."""
    def __init__(self) -> None:
        self._kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        self._kernel.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
        self._kernel.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
        self._kernel.Module32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(_ModuleEntry)]
        self._kernel.Module32FirstW.restype = wintypes.BOOL
        self._kernel.Module32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(_ModuleEntry)]
        self._kernel.Module32NextW.restype = wintypes.BOOL
        self._kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        self._kernel.OpenProcess.restype = wintypes.HANDLE
        self._kernel.ReadProcessMemory.argtypes = [
            wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_size_t),
        ]
        self._kernel.ReadProcessMemory.restype = wintypes.BOOL
        self._kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        self._kernel.CloseHandle.restype = wintypes.BOOL
        self._handle: int | None = None

    def source(self, path: str) -> SourceIdentity:
        return _qualified_source(path)

    def module(self, pid: int, path: str) -> Module:
        snapshot = self._kernel.CreateToolhelp32Snapshot(0x18, pid)
        if snapshot is None or int(snapshot) == ctypes.c_void_p(-1).value:
            raise OSError(ctypes.get_last_error(), "module snapshot failed")
        matches: list[Module] = []
        try:
            entry = _ModuleEntry()
            entry.dwSize = ctypes.sizeof(entry)
            more = self._kernel.Module32FirstW(snapshot, ctypes.byref(entry))
            while more:
                observed_path = str(entry.szExePath)
                if Path(observed_path).resolve() == Path(path).resolve():
                    base = entry.modBaseAddr
                    if base is None:
                        raise ValueError("null module base")
                    matches.append(Module(int(base), int(entry.modBaseSize), observed_path))
                more = self._kernel.Module32NextW(snapshot, ctypes.byref(entry))
            if ctypes.get_last_error() not in (0, 18):
                raise OSError(ctypes.get_last_error(), "module enumeration failed")
        finally:
            self._kernel.CloseHandle(snapshot)
        if len(matches) != 1:
            raise ValueError("expected exactly one loaded SteamUI")
        return matches[0]

    def open(self, pid: int) -> None:
        if self._handle is not None:
            raise ValueError("process handle already open")
        result = self._kernel.OpenProcess(0x1010, False, pid)
        if result is None:
            raise OSError(ctypes.get_last_error(), "read-only process open failed")
        self._handle = int(result)

    def read(self, address: int, count: int) -> bytes:
        exact_int(address, 0x10000, 0x7FFFFFFFFFFF)
        exact_int(count, 1, 1024)
        if self._handle is None:
            raise ValueError("process handle is not open")
        buffer = ctypes.create_string_buffer(count)
        returned = ctypes.c_size_t()
        ok = self._kernel.ReadProcessMemory(
            self._handle, address, buffer, count, ctypes.byref(returned))
        if not ok or returned.value != count:
            raise OSError(ctypes.get_last_error(), "bounded process read failed")
        return bytes(buffer.raw)

    def close(self) -> None:
        if self._handle is not None:
            self._kernel.CloseHandle(self._handle)
            self._handle = None


def _validated_identity(value: ProcessIdentity) -> None:
    if not isinstance(value, ProcessIdentity):
        raise ValueError("expected ProcessIdentity")
    exact_int(value.pid, 1, 2**32 - 1)
    if int(decimal(value.birth_filetime)) <= 0:
        raise ValueError("invalid birth time")
    text(value.exe)
    if value.file_version != STEAM_VERSION:
        raise ValueError("Steam version is not qualified")
    if Path(value.exe).name.lower() != "steam.exe":
        raise ValueError("expected steam.exe")


def _state(raw: int, tray: int) -> Literal[True]:
    exact_int(raw, 0, 1)
    exact_int(tray, 0, 6)
    if (raw, tray) != (1, 4):
        raise ValueError("native positive offline mode requires the current offline tray state")
    return True


def _probe_bound(machine_id: str, nonce: str, steam: ProcessIdentity,
                 reader: IdentityReader, backend: Backend) -> NativeProviderResult:
    stage: NativeReason = "invalid_input"
    try:
        text(machine_id)
        text(nonce)
        _validated_identity(steam)
        stage = "steam_instance_changed"
        before = reader.identity(steam.pid)
        if before != steam:
            return NativeUnavailable("unavailable", stage, "Steam incarnation changed before read")
        stage = "source_not_qualified"
        expected_path = str(Path(steam.exe).parent / "steamui.dll")
        source_before = backend.source(expected_path)
        if (source_before.bytes != IMAGE_BYTES or source_before.sha256 != IMAGE_SHA256
                or Path(source_before.path).resolve() != Path(expected_path).resolve()):
            return NativeUnavailable("unavailable", stage, "source binding is not qualified")
        if reader.file_version(source_before.path) != STEAM_VERSION:
            return NativeUnavailable("unavailable", stage, "SteamUI version is not qualified")
        stage = "module_changed"
        module_before = backend.module(steam.pid, expected_path)
        if (type(module_before.base) is not int or not 0x10000 <= module_before.base <= 0x7FFFFFFFFFFF - IMAGE_SIZE
                or type(module_before.size) is not int or module_before.size != IMAGE_SIZE
                or Path(module_before.path).resolve() != Path(expected_path).resolve()):
            return NativeUnavailable("unavailable", stage, "loaded SteamUI layout differs")
        backend.open(steam.pid)
        stage = "anchor_mismatch"
        for rva, expected in ANCHORS:
            if backend.read(module_before.base + rva, len(expected)) != expected:
                return NativeUnavailable("unavailable", stage, "loaded instruction anchor differs")
        stage = "tray_state_unavailable"
        raw_values: list[int] = []
        tray_values: list[int] = []
        manager_values: list[int] = []
        for _ in range(2):
            manager = int(struct.unpack("<Q", backend.read(module_before.base + TRAY_MANAGER_RVA, 8))[0])
            if not 0x10000 <= manager <= 0x7FFFFFFFFFFF - TRAY_OFFSET - 4 or manager % 8:
                return NativeUnavailable("unavailable", stage, "invalid current tray manager")
            raw = backend.read(module_before.base + VALUE_RVA, 1)[0]
            tray = int(struct.unpack("<I", backend.read(manager + TRAY_OFFSET, 4))[0])
            if raw == 0:
                return NativeUnavailable("unavailable", "native_online_not_qualified",
                                         "native zero does not qualify current online mode")
            _state(raw, tray)
            manager_values.append(manager)
            raw_values.append(raw)
            tray_values.append(tray)
        stage = "state_changed"
        if (raw_values[0] != raw_values[1] or tray_values[0] != tray_values[1]
                or manager_values[0] != manager_values[1]):
            return NativeUnavailable("unavailable", stage, "mode or tray state changed during read")
        # Recheck code, mapping, file identity and exact process birth after data.
        stage = "anchor_mismatch"
        for rva, expected in ANCHORS:
            if backend.read(module_before.base + rva, len(expected)) != expected:
                return NativeUnavailable("unavailable", stage, "loaded code changed during read")
        stage = "module_changed"
        if backend.module(steam.pid, expected_path) != module_before:
            return NativeUnavailable("unavailable", stage, "loaded module changed during read")
        stage = "source_not_qualified"
        source_after = backend.source(expected_path)
        if source_after != source_before:
            return NativeUnavailable("unavailable", stage, "source changed during read")
        stage = "steam_instance_changed"
        after = reader.identity(steam.pid)
        if after != before:
            return NativeUnavailable("unavailable", stage, "Steam incarnation changed during read")
        observed_at = datetime.now(timezone.utc).isoformat()
        evidence = NativeEvidence(
            machine_id=machine_id, observed_at_utc=observed_at, nonce=nonce,
            module_base=str(module_before.base), module_size=module_before.size,
            value_rva=str(VALUE_RVA), value_address=str(module_before.base + VALUE_RVA),
            producer_rva=str(PRODUCER_RVA), producer_anchor_hex=PRODUCER.hex(),
            producer_anchor_sha256=hashlib.sha256(PRODUCER).hexdigest(),
            raw_samples=(raw_values[0], raw_values[1]),
            steam_before=before, steam_after=after,
            source_before=source_before, source_after=source_after,
            tray_manager_pointer_rva=str(TRAY_MANAGER_RVA),
            tray_manager_address=str(manager_values[0]), tray_state_offset=str(TRAY_OFFSET),
            tray_state_samples=(tray_values[0], tray_values[1]),
        )
        return NativeObserved("observed", _state(raw_values[0], tray_values[0]),
                              steam, source_before, evidence)
    except (OSError, ValueError, struct.error, IndexError) as error:
        return NativeUnavailable("unavailable", stage, str(error)[:240])
    finally:
        backend.close()


def probe_native_offline_mode(machine_id: str, nonce: str, *,
                              steam: ProcessIdentity,
                              reader: IdentityReader) -> NativeProviderResult:
    """Observe an existing exact-version client; never start, attach IPC or inject."""
    if os.name != "nt" or ctypes.sizeof(ctypes.c_void_p) != 8:
        return NativeUnavailable("unavailable", "unsupported_platform", "64-bit Windows required")
    return _probe_bound(machine_id, nonce, steam, reader, WindowsBackend())
