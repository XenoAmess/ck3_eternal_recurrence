"""Read Steam's intentional offline mode without screenshots or mode changes.

Only an already enabled, owned loopback CEF debugger is used. This tool never
starts Steam, enables debugging, invokes UI controls, initializes a game AppID,
reads account/auth keys, or substitutes cached preferences for live state.
Unavailable is a successful diagnostic result, not evidence of online mode.
"""
from __future__ import annotations

import argparse
import base64
import ctypes
from ctypes import wintypes
from datetime import datetime, timezone
import hashlib
import http.client
import json
import os
from pathlib import Path
import re
import secrets
import socket
import struct
import sys
import time
from urllib.parse import urlsplit
from typing import Literal

from steam_offline_state_contract import (
    EndpointIdentity, NativeEvidence, ObservationMethod, ProbeResult,
    ProcessIdentity, Reason, SourceIdentity, State,
    object_map, parse_getter, parse_native_evidence, parse_result, text,
)

_MAX_HTTP = 256 * 1024
_MAX_FRAME = 256 * 1024
_SOURCE_RELATIVE = Path("steamui/chunk~2dcc5aaf7.js")
_SOURCE_BYTES = 14382868
_SOURCE_SHA = "f9606b111203c9140dcdd6fc016a0ee00e4c8406aeb786187c42873f08d071fb"
_QUALIFIED_VERSION = "10.96.30.42"


class ProbeError(RuntimeError):
    """A bounded, safe failure to obtain a live observation."""


class _ProcessEntry(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD), ("th32DefaultHeapID", ctypes.c_size_t),
        ("th32ModuleID", wintypes.DWORD), ("cntThreads", wintypes.DWORD),
        ("th32ParentProcessID", wintypes.DWORD), ("pcPriClassBase", wintypes.LONG),
        ("dwFlags", wintypes.DWORD), ("szExeFile", wintypes.WCHAR * 260),
    ]


class _UnicodeString(ctypes.Structure):
    _fields_ = [("length", ctypes.c_ushort), ("maximum_length", ctypes.c_ushort),
                ("buffer", ctypes.c_void_p)]


class _FixedFileInfo(ctypes.Structure):
    _fields_ = [(name, wintypes.DWORD) for name in (
        "signature", "structure_version", "file_ms", "file_ls",
        "product_ms", "product_ls", "flags_mask", "flags", "os", "type",
        "subtype", "date_ms", "date_ls",
    )]


class WindowsReader:
    """Narrow ctypes boundary. Each native result is validated before use."""

    def __init__(self) -> None:
        if os.name != "nt":
            raise ProbeError("Windows required")
        self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        self.ntdll = ctypes.WinDLL("ntdll")
        self.iphlp = ctypes.WinDLL("iphlpapi")
        self.version = ctypes.WinDLL("version", use_last_error=True)
        self.kernel.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
        self.kernel.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
        for name in ("Process32FirstW", "Process32NextW"):
            function = getattr(self.kernel, name)
            function.argtypes = [wintypes.HANDLE, ctypes.POINTER(_ProcessEntry)]
            function.restype = wintypes.BOOL
        self.kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        self.kernel.OpenProcess.restype = wintypes.HANDLE
        self.kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        self.kernel.CloseHandle.restype = wintypes.BOOL
        self.kernel.GetProcessTimes.argtypes = [
            wintypes.HANDLE, ctypes.POINTER(wintypes.FILETIME),
            ctypes.POINTER(wintypes.FILETIME), ctypes.POINTER(wintypes.FILETIME),
            ctypes.POINTER(wintypes.FILETIME),
        ]
        self.kernel.GetProcessTimes.restype = wintypes.BOOL
        self.kernel.QueryFullProcessImageNameW.argtypes = [
            wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR,
            ctypes.POINTER(wintypes.DWORD),
        ]
        self.kernel.QueryFullProcessImageNameW.restype = wintypes.BOOL
        self.ntdll.NtQueryInformationProcess.argtypes = [
            wintypes.HANDLE, wintypes.ULONG, ctypes.c_void_p, wintypes.ULONG,
            ctypes.POINTER(wintypes.ULONG),
        ]
        self.ntdll.NtQueryInformationProcess.restype = wintypes.LONG
        self.iphlp.GetExtendedTcpTable.argtypes = [
            ctypes.c_void_p, ctypes.POINTER(wintypes.ULONG), wintypes.BOOL,
            wintypes.ULONG, ctypes.c_int, wintypes.ULONG,
        ]
        self.iphlp.GetExtendedTcpTable.restype = wintypes.ULONG
        self.version.GetFileVersionInfoSizeW.argtypes = [
            wintypes.LPCWSTR, ctypes.POINTER(wintypes.DWORD)]
        self.version.GetFileVersionInfoSizeW.restype = wintypes.DWORD
        self.version.GetFileVersionInfoW.argtypes = [
            wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p]
        self.version.GetFileVersionInfoW.restype = wintypes.BOOL
        self.version.VerQueryValueW.argtypes = [
            ctypes.c_void_p, wintypes.LPCWSTR, ctypes.POINTER(ctypes.c_void_p),
            ctypes.POINTER(wintypes.UINT)]
        self.version.VerQueryValueW.restype = wintypes.BOOL

    def processes(self) -> dict[int, tuple[int, str]]:
        handle = self.kernel.CreateToolhelp32Snapshot(2, 0)
        if handle in (None, ctypes.c_void_p(-1).value):
            raise ProbeError("process snapshot unavailable")
        result: dict[int, tuple[int, str]] = {}
        try:
            entry = _ProcessEntry()
            entry.dwSize = ctypes.sizeof(entry)
            success = self.kernel.Process32FirstW(handle, ctypes.byref(entry))
            while success:
                result[int(entry.th32ProcessID)] = (
                    int(entry.th32ParentProcessID), str(entry.szExeFile))
                success = self.kernel.Process32NextW(handle, ctypes.byref(entry))
                if len(result) > 32768:
                    raise ProbeError("process snapshot limit exceeded")
        finally:
            self.kernel.CloseHandle(handle)
        return result

    def file_version(self, path: str) -> str:
        ignored = wintypes.DWORD()
        length = int(self.version.GetFileVersionInfoSizeW(path, ctypes.byref(ignored)))
        if not 1 <= length <= 1024 * 1024:
            raise ProbeError("file version unavailable")
        data = ctypes.create_string_buffer(length)
        if not self.version.GetFileVersionInfoW(path, 0, length, data):
            raise ProbeError("file version read failed")
        pointer = ctypes.c_void_p()
        count = wintypes.UINT()
        if not self.version.VerQueryValueW(data, "\\", ctypes.byref(pointer),
                                           ctypes.byref(count)):
            raise ProbeError("file version query failed")
        if not pointer.value or count.value < ctypes.sizeof(_FixedFileInfo):
            raise ProbeError("invalid fixed file version")
        fixed = _FixedFileInfo.from_address(pointer.value)
        if fixed.signature != 0xFEEF04BD:
            raise ProbeError("invalid fixed file version signature")
        return ".".join(str(part) for part in (
            fixed.file_ms >> 16, fixed.file_ms & 65535,
            fixed.file_ls >> 16, fixed.file_ls & 65535,
        ))

    def identity(self, pid: int) -> ProcessIdentity:
        handle = self.kernel.OpenProcess(0x1000, False, pid)
        if not handle:
            raise ProbeError("process identity access failed")
        try:
            created, exited = wintypes.FILETIME(), wintypes.FILETIME()
            kernel, user = wintypes.FILETIME(), wintypes.FILETIME()
            if not self.kernel.GetProcessTimes(handle, ctypes.byref(created),
                    ctypes.byref(exited), ctypes.byref(kernel), ctypes.byref(user)):
                raise ProbeError("process creation time unavailable")
            buffer = ctypes.create_unicode_buffer(32768)
            length = wintypes.DWORD(len(buffer))
            if not self.kernel.QueryFullProcessImageNameW(handle, 0, buffer,
                                                          ctypes.byref(length)):
                raise ProbeError("process image unavailable")
            birth = (int(created.dwHighDateTime) << 32) | int(created.dwLowDateTime)
            path = str(Path(buffer.value).resolve())
            return ProcessIdentity(pid, str(birth), path, self.file_version(path))
        finally:
            self.kernel.CloseHandle(handle)

    def debug_ports(self, pid: int) -> tuple[int, ...]:
        """Read only the bounded command line; never retain or print its secrets."""
        handle = self.kernel.OpenProcess(0x1000, False, pid)
        if not handle:
            raise ProbeError("process command line access failed")
        try:
            size = wintypes.ULONG()
            self.ntdll.NtQueryInformationProcess(handle, 60, None, 0, ctypes.byref(size))
            if not ctypes.sizeof(_UnicodeString) <= size.value <= 65536:
                raise ProbeError("process command line size unavailable")
            buffer = ctypes.create_string_buffer(size.value)
            status = int(self.ntdll.NtQueryInformationProcess(
                handle, 60, buffer, len(buffer), ctypes.byref(size)))
            if status < 0:
                raise ProbeError("process command line unavailable")
            value = _UnicodeString.from_buffer(buffer)
            address = value.buffer
            base = ctypes.addressof(buffer)
            if (not address or value.length % 2 or
                    not base <= address <= address + value.length <= base + len(buffer)):
                raise ProbeError("invalid process command line buffer")
            command = ctypes.wstring_at(address, value.length // 2)
            values = re.findall(
                r"(?:^|\s)--remote-debugging-port(?:=|\s+)([0-9]{1,5})(?=\s|$)",
                command,
            )
            return tuple(sorted({int(port) for port in values
                                 if 1 <= int(port) <= 65535}))
        finally:
            self.kernel.CloseHandle(handle)

    def loopback_listeners(self) -> frozenset[tuple[int, int]]:
        size = wintypes.ULONG()
        self.iphlp.GetExtendedTcpTable(None, ctypes.byref(size), False, 2, 3, 0)
        if not 4 <= size.value <= 16 * 1024 * 1024:
            raise ProbeError("TCP owner table unavailable")
        buffer = ctypes.create_string_buffer(size.value)
        status = int(self.iphlp.GetExtendedTcpTable(
            buffer, ctypes.byref(size), False, 2, 3, 0))
        if status != 0:
            raise ProbeError("TCP owner table read failed")
        count = struct.unpack_from("<I", buffer)[0]
        if 4 + count * 24 > len(buffer):
            raise ProbeError("invalid TCP owner table")
        result: set[tuple[int, int]] = set()
        for index in range(count):
            state, local, port, _, _, pid = struct.unpack_from(
                "<6I", buffer, 4 + index * 24)
            address = socket.inet_ntoa(struct.pack("<I", local))
            if state == 2 and address == "127.0.0.1":
                result.add((pid, socket.ntohs(port & 65535)))
        return frozenset(result)


def qualified_source(steam: ProcessIdentity) -> SourceIdentity:
    path = Path(steam.exe).parent / _SOURCE_RELATIVE
    before = path.stat()
    if before.st_size != _SOURCE_BYTES or steam.file_version != _QUALIFIED_VERSION:
        raise ProbeError("installed Steam source/version not qualified")
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    after = path.stat()
    if ((before.st_ino, before.st_mtime_ns, before.st_size) !=
            (after.st_ino, after.st_mtime_ns, after.st_size) or
            digest.hexdigest() != _SOURCE_SHA):
        raise ProbeError("installed Steam source changed or not qualified")
    return SourceIdentity(str(path.resolve()), after.st_size, digest.hexdigest(),
                          str(after.st_ino), str(after.st_mtime_ns))


def getter_expression(nonce: str) -> str:
    return """(() => {
const app = globalThis.App;
if (!app || typeof app.GetCurrentUser !== "function" ||
    typeof app.BIsOfflineMode !== "function") throw Error("no Steam App");
const user = app.GetCurrentUser();
if (!user) throw Error("no current Steam user");
return {nonce: """ + json.dumps(nonce) + """,
 direct: user.bIsOfflineMode, method: app.BIsOfflineMode()};
})()"""


def http_json(port: int, path: str, timeout: float) -> object:
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=timeout)
    try:
        connection.request("GET", path, headers={"Host": "127.0.0.1"})
        response = connection.getresponse()
        if response.status != 200:
            raise ProbeError("CDP discovery unavailable")
        payload = response.read(_MAX_HTTP + 1)
        if len(payload) > _MAX_HTTP:
            raise ProbeError("CDP discovery response limit exceeded")
        value: object = json.loads(payload)
        return value
    finally:
        connection.close()


def _receive_exact(stream: socket.socket, size: int, deadline: float) -> bytes:
    result = bytearray()
    while len(result) < size:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise ProbeError("CDP receive deadline exceeded")
        stream.settimeout(remaining)
        part = stream.recv(size - len(result))
        if not part:
            raise ProbeError("CDP connection ended")
        result.extend(part)
    return bytes(result)


def _send_frame(stream: socket.socket, payload: bytes, opcode: int = 1) -> None:
    if len(payload) > _MAX_FRAME:
        raise ProbeError("CDP request limit exceeded")
    mask = secrets.token_bytes(4)
    size = len(payload)
    header = bytes((0x80 | opcode, 0x80 | size)) if size < 126 else (
        bytes((0x80 | opcode, 0xFE)) + struct.pack("!H", size) if size < 65536
        else bytes((0x80 | opcode, 0xFF)) + struct.pack("!Q", size))
    stream.sendall(header + mask + bytes(value ^ mask[i % 4]
                                        for i, value in enumerate(payload)))


def cdp_evaluate(websocket_url: str, port: int, nonce: str,
                 timeout: float) -> object:
    """Bounded RFC6455 client; one fixed, side-effect-checked Runtime.evaluate."""
    url = urlsplit(websocket_url)
    if (url.scheme != "ws" or url.hostname not in ("localhost", "127.0.0.1")
            or url.port != port or url.username is not None or url.password is not None
            or url.query or url.fragment or
            re.fullmatch(r"/devtools/page/[A-Za-z0-9_-]{1,128}", url.path) is None):
        raise ProbeError("untrusted CDP websocket endpoint")
    deadline = time.monotonic() + timeout
    with socket.create_connection(("127.0.0.1", port), timeout=timeout) as stream:
        key = base64.b64encode(secrets.token_bytes(16)).decode("ascii")
        request = (f"GET {url.path} HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\n"
                   "Upgrade: websocket\r\nConnection: Upgrade\r\n"
                   f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n")
        stream.sendall(request.encode("ascii"))
        header = bytearray()
        while not header.endswith(b"\r\n\r\n"):
            if len(header) > 8192:
                raise ProbeError("CDP handshake limit exceeded")
            header.extend(_receive_exact(stream, 1, deadline))
        lines = bytes(header).decode("iso-8859-1").split("\r\n")
        expected = base64.b64encode(hashlib.sha1(
            (key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode("ascii")
        ).digest()).decode("ascii")
        fields: dict[str, str] = {}
        for line in lines[1:]:
            if ":" in line:
                name, header_value = line.split(":", 1)
                fields[name.lower()] = header_value.strip()
        if (not lines[0].startswith("HTTP/1.1 101 ") or
                fields.get("sec-websocket-accept") != expected or
                fields.get("upgrade", "").lower() != "websocket"):
            raise ProbeError("CDP handshake rejected")
        _send_frame(stream, json.dumps({
            "id": 1, "method": "Runtime.evaluate",
            "params": {"expression": getter_expression(nonce), "returnByValue": True,
                       "throwOnSideEffect": True, "disableBreaks": True,
                       "timeout": int(timeout * 1000)},
        }, separators=(",", ":")).encode("utf-8"))
        for _ in range(32):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ProbeError("CDP evaluation deadline exceeded")
            stream.settimeout(remaining)
            first, second = _receive_exact(stream, 2, deadline)
            if first & 0x70 or not first & 0x80 or second & 0x80:
                raise ProbeError("unsupported CDP websocket frame")
            opcode = first & 15
            size = second & 127
            if size == 126: size = struct.unpack("!H", _receive_exact(stream, 2, deadline))[0]
            elif size == 127: size = struct.unpack("!Q", _receive_exact(stream, 8, deadline))[0]
            if size > _MAX_FRAME:
                raise ProbeError("CDP response limit exceeded")
            payload = _receive_exact(stream, size, deadline)
            if opcode == 9:
                _send_frame(stream, payload, 10)
                continue
            if opcode != 1:
                raise ProbeError("CDP response not text")
            value: object = json.loads(payload)
            message = object_map(value)
            if "id" not in message:
                continue
            if type(message["id"]) is not int or message["id"] != 1:
                raise ProbeError("unexpected CDP response ID")
            if "error" in message:
                raise ProbeError("CDP evaluation rejected")
            result = object_map(message.get("result"))
            if "exceptionDetails" in result:
                raise ProbeError("Steam App getter unavailable")
            remote = object_map(result.get("result"))
            if remote.get("type") != "object" or "value" not in remote:
                raise ProbeError("CDP did not return getter JSON")
            return remote["value"]
        raise ProbeError("CDP event limit exceeded")


def target_candidates(port: int, timeout: float) -> tuple[tuple[str, str, str], ...]:
    version = object_map(http_json(port, "/json/version", timeout))
    if (not text(version.get("Browser")).lower().startswith(("chrome/", "chromium/"))
            or not text(version.get("Protocol-Version")).startswith("1.")):
        raise ProbeError("not a qualified Chromium debugger")
    values = http_json(port, "/json/list", timeout)
    if not isinstance(values, list) or len(values) > 128:
        raise ProbeError("invalid CDP target list")
    result: list[tuple[str, str, str]] = []
    for value in values:
        item = object_map(value)
        if item.get("type") != "page":
            continue
        target_url = text(item.get("url"))
        # Reject auth-bearing URLs and bind discovery ID to the queried target.
        parsed = urlsplit(target_url)
        shared = target_url == "about:blank" and item.get("title") == "SharedJSContext"
        if not shared and (parsed.scheme != "https" or
                parsed.hostname != "steamloopback.host" or parsed.query or
                parsed.fragment or parsed.username is not None):
            continue
        target_id, websocket = text(item.get("id")), text(item.get("webSocketDebuggerUrl"))
        if urlsplit(websocket).path != "/devtools/page/" + target_id:
            continue
        result.append((target_id, target_url, websocket))
    return tuple(result)


def _descendants(rows: dict[int, tuple[int, str]], steam_pid: int) -> frozenset[int]:
    result = {steam_pid}
    for _ in range(32):
        additions = {pid for pid, (parent, _) in rows.items() if parent in result}
        if additions <= result:
            break
        result.update(additions)
    return frozenset(result)


def run_probe(machine_id: str, timeout: float = 2.0) -> ProbeResult:
    stamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    nonce = secrets.token_hex(16)
    steam: ProcessIdentity | None = None
    source: SourceIdentity | None = None
    endpoint: EndpointIdentity | None = None
    method: ObservationMethod | None = None
    native_evidence: NativeEvidence | None = None
    diagnostics: list[str] = []
    def result(status: State, reason: Reason) -> ProbeResult:
        return ProbeResult(machine_id, stamp, nonce, status, reason,
                           steam, source, endpoint, tuple(diagnostics), method, native_evidence)
    if os.name != "nt":
        return result("unavailable", "unsupported_platform")
    try:
        native = WindowsReader()
        rows = native.processes()
        steam_pids = [pid for pid, (_, name) in rows.items()
                      if name.casefold() == "steam.exe"]
        if not steam_pids:
            return result("unavailable", "steam_not_found")
        if len(steam_pids) != 1:
            return result("unavailable", "ambiguous_steam")
        steam = native.identity(steam_pids[0])
        root = Path(steam.exe).parent
        # The native provider reads only the qualified producer's backing byte.
        # Its distinct provenance never claims that CEF App getters ran.
        try:
            from steam_offline_native_provider_v1 import probe_native_offline_mode
        except ModuleNotFoundError as missing:
            if missing.name != "steam_offline_native_provider_v1":
                raise
            diagnostics.append("native_provider_not_installed")
        else:
            native_value = probe_native_offline_mode(
                machine_id, nonce, steam=steam, reader=native)
            if native_value.status == "observed":
                if type(native_value.offline_mode) is not bool:
                    raise ProbeError("native provider returned nonboolean mode")
                evidence = parse_native_evidence(native_value.evidence.to_wire())
                if (native_value.steam != steam or evidence.machine_id != machine_id or
                        evidence.nonce != nonce or
                        evidence.steam_before != steam or
                        evidence.source_before != native_value.source or
                        bool(evidence.raw_samples[0]) != native_value.offline_mode):
                    raise ProbeError("native provider/CLI binding mismatch")
                source = native_value.source
                native_evidence = evidence
                stamp = evidence.observed_at_utc
                method = "native_current_user_byte"
                return result("offline", "observed")
            diagnostics.append("native_provider_unavailable=" + native_value.reason)
        try:
            source = qualified_source(steam)
        except (OSError, ProbeError):
            return result("unavailable", "source_not_qualified")
        descendants = _descendants(rows, steam.pid)
        cef: list[ProcessIdentity] = []
        for pid in sorted(descendants):
            if rows[pid][1].casefold() != "steamwebhelper.exe":
                continue
            try:
                candidate = native.identity(pid)
                if (root not in Path(candidate.exe).parents or
                        candidate.file_version != steam.file_version or
                        int(candidate.birth_filetime) < int(steam.birth_filetime)):
                    continue
                cef.append(candidate)
            except (OSError, ProbeError):
                diagnostics.append("webhelper_identity_unavailable")
        listeners = native.loopback_listeners()
        endpoints: list[tuple[ProcessIdentity, int]] = []
        saw_port_flag = False
        for owner in cef:
            try:
                ports = native.debug_ports(owner.pid)
            except (OSError, ProbeError):
                diagnostics.append("webhelper_commandline_unavailable")
                continue
            saw_port_flag = saw_port_flag or bool(ports)
            endpoints.extend((owner, port) for port in ports
                             if (owner.pid, port) in listeners)
        diagnostics.append("checked_webhelpers=" + str(len(cef)))
        diagnostics.append("owned_debugger_candidates=" + str(len(endpoints)))
        if not endpoints:
            if native.identity(steam.pid) != steam:
                return result("unavailable", "steam_instance_changed")
            return result("unavailable", "cdp_not_owned" if saw_port_flag
                          else "cdp_not_enabled")
        # A fixed total deadline bounds discovery across all helper contexts.
        deadline = time.monotonic() + timeout
        observations: list[LiteralObservation] = []
        for owner, port in endpoints[:4]:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            try:
                targets = target_candidates(port, remaining)
                for target_id, target_url, websocket_url in targets[:8]:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        break
                    raw = cdp_evaluate(websocket_url, port, nonce, remaining)
                    state = parse_getter(raw, nonce)
                    current = EndpointIdentity(owner.pid, owner.birth_filetime,
                                               port, target_id, target_url)
                    if (native.identity(owner.pid) != owner or
                            (owner.pid, port) not in native.loopback_listeners()):
                        return result("unavailable", "steam_instance_changed")
                    observations.append((state, current))
            except (OSError, ValueError, ProbeError, http.client.HTTPException):
                diagnostics.append("debugger_or_context_query_unavailable")
        if native.identity(steam.pid) != steam:
            return result("unavailable", "steam_instance_changed")
        if not observations:
            return result("unavailable", "context_unavailable")
        states = {state for state, _ in observations}
        if len(states) != 1:
            return result("unavailable", "invalid_observation")
        observed_state, endpoint = observations[0]
        method = "cef_app_getters"
        return result(observed_state, "observed")
    except (OSError, ValueError, ProbeError):
        return result("unavailable", "native_query_failed")


# Explicit shared internal tuple model; JSON endpoints are encoded by the DTO.
LiteralObservation = tuple[Literal["offline", "online"], EndpointIdentity]


def current_machine_id() -> str:
    # Existing machine identity implementation is the sole authority.
    from ck3_live_run_id import current_machine_id as resolve
    return text(resolve())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path,
                        help="create-only JSON output; no parent directories created")
    parser.add_argument("--timeout", type=float, default=2.0)
    arguments = parser.parse_args()
    timeout = arguments.timeout
    if type(timeout) is not float or not 0.1 <= timeout <= 10.0:
        parser.error("--timeout must be between 0.1 and 10 seconds")
    value = run_probe(current_machine_id(), timeout)
    wire = value.to_wire()
    payload = (json.dumps(wire, ensure_ascii=True, indent=2) + "\n").encode("utf-8")
    # Validate the actual wire representation, including JSON array conversion.
    if parse_result(json.loads(payload)) != value:
        raise ProbeError("receipt serialization round trip failed")
    receipt: object = arguments.receipt
    if receipt is not None:
        if not isinstance(receipt, Path):
            raise ProbeError("invalid receipt path")
        with receipt.open("xb") as output:
            output.write(payload)
            output.flush()
            os.fsync(output.fileno())
        if receipt.read_bytes() != payload:
            raise ProbeError("receipt readback mismatch")
    sys.stdout.buffer.write(payload)
    # Both observed states are successful observations; callers inspect status.
    return 2 if value.status == "unavailable" else 0


if __name__ == "__main__":
    raise SystemExit(main())
