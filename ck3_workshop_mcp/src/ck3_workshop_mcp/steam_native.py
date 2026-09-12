"""Minimal Steamworks flat-API bridge for direct Workshop publication.

The metadata command parses the PE export table without loading the DLL.  The
``probe`` and ``publish`` entry points load ``steam_api64.dll`` and therefore
must only be called by an authorized operator in a valid Steam AppID context.

The ctypes declarations mirror Valve's public ISteamUGC, ISteamUtils, and
ISteamUser documentation.  Interface accessors are discovered from the exact
DLL instead of assuming an SDK version.
"""

from __future__ import annotations

import argparse
import contextlib
import ctypes
import hashlib
import json
import os
import re
import struct
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence


DEFAULT_APP_ID = 1_158_310
ERESULT_OK = 1
WORKSHOP_FILE_TYPE_COMMUNITY = 0
CREATE_ITEM_CALLBACK_ID = 3403
SUBMIT_ITEM_UPDATE_CALLBACK_ID = 3404
INVALID_API_CALL = 0
INVALID_UPDATE_HANDLE = (1 << 64) - 1
WORKSHOP_LEGAL_AGREEMENT_URL = (
    "https://steamcommunity.com/sharedfiles/workshoplegalagreement"
)

_ACCESSOR_PATTERNS = {
    "ugc": re.compile(r"^SteamAPI_SteamUGC_v(\d+)$"),
    "utils": re.compile(r"^SteamAPI_SteamUtils_v(\d+)$"),
    "user": re.compile(r"^SteamAPI_SteamUser_v(\d+)$"),
}

_REQUIRED_FLAT_EXPORTS = (
    "SteamAPI_Init",
    "SteamAPI_Shutdown",
    "SteamAPI_RunCallbacks",
    "SteamAPI_ISteamUtils_GetAppID",
    "SteamAPI_ISteamUtils_IsAPICallCompleted",
    "SteamAPI_ISteamUtils_GetAPICallResult",
    "SteamAPI_ISteamUser_BLoggedOn",
    "SteamAPI_ISteamUser_GetSteamID",
    "SteamAPI_ISteamUGC_CreateItem",
    "SteamAPI_ISteamUGC_StartItemUpdate",
    "SteamAPI_ISteamUGC_SetItemTitle",
    "SteamAPI_ISteamUGC_SetItemDescription",
    "SteamAPI_ISteamUGC_SetItemContent",
    "SteamAPI_ISteamUGC_SetItemPreview",
    "SteamAPI_ISteamUGC_SetItemVisibility",
    "SteamAPI_ISteamUGC_SetItemTags",
    "SteamAPI_ISteamUGC_SubmitItemUpdate",
)

_VISIBILITY = {
    "public": 0,
    "friends_only": 1,
    "friends-only": 1,
    "private": 2,
    "unlisted": 3,
}


class SteamNativeError(RuntimeError):
    """Stable error returned by the standalone Steamworks bridge."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        details: Mapping[str, object] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.details = dict(details or {})

    def as_dict(self) -> dict[str, object]:
        result: dict[str, object] = {"code": self.code, "message": str(self)}
        if self.details:
            result["details"] = self.details
        return result


class CreateItemResult(ctypes.Structure):
    """ABI layout of Valve's ``CreateItemResult_t`` on the 64-bit DLL."""

    _fields_ = (
        ("result", ctypes.c_int32),
        ("published_file_id", ctypes.c_uint64),
        ("needs_legal_agreement", ctypes.c_bool),
    )


class SubmitItemUpdateResult(ctypes.Structure):
    """ABI layout of Valve's ``SubmitItemUpdateResult_t``."""

    _fields_ = (
        ("result", ctypes.c_int32),
        ("needs_legal_agreement", ctypes.c_bool),
    )


class SteamParamStringArray(ctypes.Structure):
    """ABI layout of ``SteamParamStringArray_t``."""

    _fields_ = (
        ("strings", ctypes.POINTER(ctypes.c_char_p)),
        ("count", ctypes.c_int32),
    )


@dataclass(frozen=True, slots=True)
class _CreateResult:
    result: int
    item_id: int
    needs_legal_agreement: bool


@dataclass(frozen=True, slots=True)
class _SubmitResult:
    result: int
    needs_legal_agreement: bool


@dataclass(frozen=True, slots=True)
class _PreparedPlan:
    operation_id: str
    operation: str
    app_id: int
    target_item_id: int | None
    title: str
    description: str
    content_path: Path
    preview_path: Path | None
    visibility: int
    tags: tuple[str, ...]
    change_note: str
    legal_agreement_accepted: bool
    payload_sha256: str


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_c_string(data: bytes, offset: int) -> str:
    end = data.find(b"\0", offset)
    if end < 0:
        raise SteamNativeError("INVALID_PE", "unterminated PE export name")
    try:
        return data[offset:end].decode("ascii")
    except UnicodeDecodeError as exc:
        raise SteamNativeError("INVALID_PE", "non-ASCII PE export name") from exc


def _pe_exports(path: Path) -> tuple[list[str], dict[str, object]]:
    """Return PE export names without calling LoadLibrary."""

    data = path.read_bytes()
    if len(data) < 0x40 or data[:2] != b"MZ":
        raise SteamNativeError("INVALID_PE", f"not a PE image: {path}")
    pe_offset = struct.unpack_from("<I", data, 0x3C)[0]
    if pe_offset + 24 > len(data) or data[pe_offset : pe_offset + 4] != b"PE\0\0":
        raise SteamNativeError("INVALID_PE", f"missing PE signature: {path}")

    machine, section_count = struct.unpack_from("<HH", data, pe_offset + 4)
    optional_size = struct.unpack_from("<H", data, pe_offset + 20)[0]
    optional_offset = pe_offset + 24
    if optional_offset + optional_size > len(data):
        raise SteamNativeError("INVALID_PE", "truncated PE optional header")
    magic = struct.unpack_from("<H", data, optional_offset)[0]
    if magic == 0x20B:
        data_directory_offset = optional_offset + 112
        bits = 64
    elif magic == 0x10B:
        data_directory_offset = optional_offset + 96
        bits = 32
    else:
        raise SteamNativeError(
            "INVALID_PE", f"unsupported PE optional-header magic 0x{magic:04x}"
        )
    if data_directory_offset + 8 > optional_offset + optional_size:
        raise SteamNativeError("INVALID_PE", "PE has no export data directory")
    export_rva, export_size = struct.unpack_from("<II", data, data_directory_offset)

    section_offset = optional_offset + optional_size
    sections: list[tuple[int, int, int, int]] = []
    for index in range(section_count):
        offset = section_offset + index * 40
        if offset + 40 > len(data):
            raise SteamNativeError("INVALID_PE", "truncated PE section table")
        virtual_size, virtual_address, raw_size, raw_offset = struct.unpack_from(
            "<IIII", data, offset + 8
        )
        sections.append((virtual_address, virtual_size, raw_offset, raw_size))

    def rva_to_offset(rva: int, length: int = 1) -> int:
        for virtual_address, virtual_size, raw_offset, raw_size in sections:
            span = max(virtual_size, raw_size)
            if virtual_address <= rva and rva + length <= virtual_address + span:
                result = raw_offset + (rva - virtual_address)
                if result < 0 or result + length > len(data):
                    break
                return result
        raise SteamNativeError(
            "INVALID_PE", f"RVA 0x{rva:x} is outside mapped sections"
        )

    names: list[str] = []
    if export_rva:
        export_offset = rva_to_offset(export_rva, 40)
        name_count = struct.unpack_from("<I", data, export_offset + 24)[0]
        names_rva = struct.unpack_from("<I", data, export_offset + 32)[0]
        if name_count > 100_000:
            raise SteamNativeError("INVALID_PE", "implausible PE export-name count")
        name_table_offset = rva_to_offset(names_rva, name_count * 4)
        for index in range(name_count):
            name_rva = struct.unpack_from("<I", data, name_table_offset + index * 4)[0]
            names.append(_read_c_string(data, rva_to_offset(name_rva)))

    metadata = {
        "machine": f"0x{machine:04x}",
        "bits": bits,
        "export_directory_size": export_size,
    }
    return sorted(set(names)), metadata


def _select_accessors(export_names: Sequence[str]) -> dict[str, str | None]:
    selected: dict[str, str | None] = {}
    for kind, pattern in _ACCESSOR_PATTERNS.items():
        candidates: list[tuple[int, str]] = []
        for name in export_names:
            match = pattern.fullmatch(name)
            if match:
                candidates.append((int(match.group(1)), name))
        selected[kind] = max(candidates)[1] if candidates else None
    return selected


def symbols(dll_path: str | Path) -> dict[str, object]:
    """Inspect Steam flat-API symbols without loading or initializing the DLL."""

    path = Path(dll_path).expanduser().resolve()
    if not path.is_file():
        raise SteamNativeError("DLL_NOT_FOUND", f"Steam API DLL not found: {path}")
    export_names, pe = _pe_exports(path)
    accessors = _select_accessors(export_names)
    export_set = set(export_names)
    missing = [name for name in _REQUIRED_FLAT_EXPORTS if name not in export_set]
    for kind, accessor in accessors.items():
        if accessor is None:
            missing.append(f"SteamAPI_Steam{kind.title()}_vNNN")
    return {
        "schema": "ck3_workshop_mcp.steam_native.symbols.v1",
        "ok": not missing,
        "dll_path": str(path),
        "size": path.stat().st_size,
        "sha256": _sha256_file(path),
        "pe": pe,
        "export_count": len(export_names),
        "accessors": accessors,
        "required_flat_exports": {
            name: name in export_set for name in _REQUIRED_FLAT_EXPORTS
        },
        "missing": missing,
        "abi": {
            "create_item_callback_id": CREATE_ITEM_CALLBACK_ID,
            "create_item_result_size": ctypes.sizeof(CreateItemResult),
            "submit_item_update_callback_id": SUBMIT_ITEM_UPDATE_CALLBACK_ID,
            "submit_item_update_result_size": ctypes.sizeof(SubmitItemUpdateResult),
            "pointer_size": ctypes.sizeof(ctypes.c_void_p),
        },
    }


def _bind(
    library: Any,
    name: str,
    restype: Any,
    argtypes: Sequence[Any],
) -> Any:
    try:
        function = getattr(library, name)
    except AttributeError as exc:
        raise SteamNativeError("MISSING_EXPORT", f"DLL does not export {name}") from exc
    function.restype = restype
    function.argtypes = list(argtypes)
    return function


class _NativeClient:
    def __init__(self, dll_path: str | Path, expected_app_id: int) -> None:
        if os.name != "nt":
            raise SteamNativeError(
                "WINDOWS_REQUIRED", "Steam steam_api64.dll can only be loaded on Windows"
            )
        metadata = symbols(dll_path)
        if not metadata["ok"]:
            raise SteamNativeError(
                "INCOMPATIBLE_DLL",
                "Steam API DLL is missing required flat exports",
                details={"missing": metadata["missing"]},
            )
        self.metadata = metadata
        path = str(metadata["dll_path"])
        try:
            self.library = ctypes.WinDLL(path)  # type: ignore[attr-defined]
        except OSError as exc:
            raise SteamNativeError("DLL_LOAD_FAILED", f"could not load {path}: {exc}") from exc

        self._init = _bind(self.library, "SteamAPI_Init", ctypes.c_bool, ())
        self._shutdown = _bind(self.library, "SteamAPI_Shutdown", None, ())
        self._run_callbacks = _bind(
            self.library, "SteamAPI_RunCallbacks", None, ()
        )
        self._initialized = False
        if not bool(self._init()):
            raise SteamNativeError(
                "STEAM_INIT_FAILED",
                "SteamAPI_Init returned false; run in a supported Steam AppID context",
            )
        self._initialized = True

        accessors = metadata["accessors"]
        assert isinstance(accessors, dict)
        self.ugc = self._interface(accessors["ugc"])
        self.utils = self._interface(accessors["utils"])
        self.user = self._interface(accessors["user"])

        self._get_app_id = _bind(
            self.library,
            "SteamAPI_ISteamUtils_GetAppID",
            ctypes.c_uint32,
            (ctypes.c_void_p,),
        )
        self._is_call_completed = _bind(
            self.library,
            "SteamAPI_ISteamUtils_IsAPICallCompleted",
            ctypes.c_bool,
            (ctypes.c_void_p, ctypes.c_uint64, ctypes.POINTER(ctypes.c_bool)),
        )
        self._get_call_result = _bind(
            self.library,
            "SteamAPI_ISteamUtils_GetAPICallResult",
            ctypes.c_bool,
            (
                ctypes.c_void_p,
                ctypes.c_uint64,
                ctypes.c_void_p,
                ctypes.c_int32,
                ctypes.c_int32,
                ctypes.POINTER(ctypes.c_bool),
            ),
        )
        self._logged_on = _bind(
            self.library,
            "SteamAPI_ISteamUser_BLoggedOn",
            ctypes.c_bool,
            (ctypes.c_void_p,),
        )
        self._get_steam_id = _bind(
            self.library,
            "SteamAPI_ISteamUser_GetSteamID",
            ctypes.c_uint64,
            (ctypes.c_void_p,),
        )
        self._create_item = _bind(
            self.library,
            "SteamAPI_ISteamUGC_CreateItem",
            ctypes.c_uint64,
            (ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int32),
        )
        self._start_item_update = _bind(
            self.library,
            "SteamAPI_ISteamUGC_StartItemUpdate",
            ctypes.c_uint64,
            (ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint64),
        )
        self._set_title = self._bind_update_string("SetItemTitle")
        self._set_description = self._bind_update_string("SetItemDescription")
        self._set_content = self._bind_update_string("SetItemContent")
        self._set_preview = self._bind_update_string("SetItemPreview")
        self._set_visibility = _bind(
            self.library,
            "SteamAPI_ISteamUGC_SetItemVisibility",
            ctypes.c_bool,
            (ctypes.c_void_p, ctypes.c_uint64, ctypes.c_int32),
        )
        self._set_tags = _bind(
            self.library,
            "SteamAPI_ISteamUGC_SetItemTags",
            ctypes.c_bool,
            (
                ctypes.c_void_p,
                ctypes.c_uint64,
                ctypes.POINTER(SteamParamStringArray),
            ),
        )
        self._submit = _bind(
            self.library,
            "SteamAPI_ISteamUGC_SubmitItemUpdate",
            ctypes.c_uint64,
            (ctypes.c_void_p, ctypes.c_uint64, ctypes.c_char_p),
        )

        observed_app_id = self.app_id()
        if observed_app_id != expected_app_id:
            self.close()
            raise SteamNativeError(
                "APP_ID_MISMATCH",
                f"Steam context AppID {observed_app_id} does not match {expected_app_id}",
                details={"observed_app_id": observed_app_id, "expected_app_id": expected_app_id},
            )

    def _interface(self, export_name: object) -> ctypes.c_void_p:
        if not isinstance(export_name, str):
            raise SteamNativeError("MISSING_INTERFACE", "Steam interface accessor missing")
        accessor = _bind(self.library, export_name, ctypes.c_void_p, ())
        value = accessor()
        if not value:
            raise SteamNativeError(
                "MISSING_INTERFACE", f"{export_name} returned a null interface"
            )
        return ctypes.c_void_p(value)

    def _bind_update_string(self, suffix: str) -> Any:
        return _bind(
            self.library,
            f"SteamAPI_ISteamUGC_{suffix}",
            ctypes.c_bool,
            (ctypes.c_void_p, ctypes.c_uint64, ctypes.c_char_p),
        )

    def __enter__(self) -> "_NativeClient":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def close(self) -> None:
        if self._initialized:
            self._initialized = False
            self._shutdown()

    def app_id(self) -> int:
        return int(self._get_app_id(self.utils))

    def logged_on(self) -> bool:
        return bool(self._logged_on(self.user))

    def steam_id(self) -> int:
        return int(self._get_steam_id(self.user))

    def _wait_for_result(
        self,
        call_handle: int,
        result_type: type[ctypes.Structure],
        callback_id: int,
        *,
        timeout_seconds: float = 180.0,
    ) -> ctypes.Structure:
        if call_handle == INVALID_API_CALL:
            raise SteamNativeError(
                "INVALID_API_CALL", "Steamworks returned k_uAPICallInvalid"
            )
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            self._run_callbacks()
            call_failed = ctypes.c_bool(False)
            complete = bool(
                self._is_call_completed(
                    self.utils, call_handle, ctypes.byref(call_failed)
                )
            )
            if complete:
                if call_failed.value:
                    raise SteamNativeError(
                        "API_CALL_RESULT_UNKNOWN",
                        f"Steam API call {call_handle} completed with IO failure",
                    )
                result = result_type()
                io_failure = ctypes.c_bool(False)
                obtained = bool(
                    self._get_call_result(
                        self.utils,
                        call_handle,
                        ctypes.byref(result),
                        ctypes.sizeof(result),
                        callback_id,
                        ctypes.byref(io_failure),
                    )
                )
                if not obtained or io_failure.value:
                    raise SteamNativeError(
                        "API_CALL_RESULT_UNKNOWN",
                        f"Steam API call {call_handle} result could not be read",
                        details={
                            "callback_id": callback_id,
                            "get_result": obtained,
                            "io_failure": bool(io_failure.value),
                        },
                    )
                return result
            time.sleep(0.05)
        raise SteamNativeError(
            "API_CALL_RESULT_UNKNOWN",
            f"Steam API call {call_handle} did not complete before timeout",
            details={"callback_id": callback_id, "timeout_seconds": timeout_seconds},
        )

    def create_item(self, app_id: int) -> _CreateResult:
        handle = int(self._create_item(self.ugc, app_id, WORKSHOP_FILE_TYPE_COMMUNITY))
        raw = self._wait_for_result(handle, CreateItemResult, CREATE_ITEM_CALLBACK_ID)
        assert isinstance(raw, CreateItemResult)
        return _CreateResult(
            result=int(raw.result),
            item_id=int(raw.published_file_id),
            needs_legal_agreement=bool(raw.needs_legal_agreement),
        )

    def start_item_update(self, app_id: int, item_id: int) -> int:
        handle = int(self._start_item_update(self.ugc, app_id, item_id))
        if handle == INVALID_UPDATE_HANDLE:
            raise SteamNativeError(
                "INVALID_UPDATE_HANDLE", "StartItemUpdate returned an invalid handle"
            )
        return handle

    @staticmethod
    def _utf8(value: str) -> bytes:
        return value.encode("utf-8")

    def set_title(self, handle: int, value: str) -> bool:
        return bool(self._set_title(self.ugc, handle, self._utf8(value)))

    def set_description(self, handle: int, value: str) -> bool:
        return bool(self._set_description(self.ugc, handle, self._utf8(value)))

    def set_content(self, handle: int, value: Path) -> bool:
        return bool(self._set_content(self.ugc, handle, self._utf8(str(value))))

    def set_preview(self, handle: int, value: Path) -> bool:
        return bool(self._set_preview(self.ugc, handle, self._utf8(str(value))))

    def set_visibility(self, handle: int, value: int) -> bool:
        return bool(self._set_visibility(self.ugc, handle, value))

    def set_tags(self, handle: int, tags: Sequence[str]) -> bool:
        encoded = [tag.encode("utf-8") for tag in tags]
        array_type = ctypes.c_char_p * len(encoded)
        array = array_type(*encoded)
        parameters = SteamParamStringArray(array, len(encoded))
        return bool(self._set_tags(self.ugc, handle, ctypes.byref(parameters)))

    def submit_item_update(self, handle: int, change_note: str) -> _SubmitResult:
        call = int(self._submit(self.ugc, handle, self._utf8(change_note)))
        raw = self._wait_for_result(
            call, SubmitItemUpdateResult, SUBMIT_ITEM_UPDATE_CALLBACK_ID
        )
        assert isinstance(raw, SubmitItemUpdateResult)
        return _SubmitResult(
            result=int(raw.result),
            needs_legal_agreement=bool(raw.needs_legal_agreement),
        )


def _open_client(dll_path: str | Path, app_id: int) -> _NativeClient:
    return _NativeClient(dll_path, app_id)


def probe(dll_path: str | Path, app_id: int = DEFAULT_APP_ID) -> dict[str, object]:
    """Initialize Steamworks, then read and verify the active user/AppID context."""

    if not isinstance(app_id, int) or isinstance(app_id, bool) or app_id <= 0:
        raise SteamNativeError("INVALID_PLAN", "app_id must be a positive integer")
    with _open_client(dll_path, app_id) as client:
        observed_app_id = client.app_id()
        logged_on = client.logged_on()
        steam_id = client.steam_id()
        if not logged_on:
            raise SteamNativeError(
                "STEAM_USER_OFFLINE", "Steam user interface reports BLoggedOn=false"
            )
        if steam_id == 0:
            raise SteamNativeError(
                "STEAM_USER_UNAVAILABLE", "Steam user interface returned SteamID 0"
            )
        return {
            "schema": "ck3_workshop_mcp.steam_native.probe.v1",
            "ok": True,
            "app_id": observed_app_id,
            "logged_on": logged_on,
            "steam_id64": str(steam_id),
            "dll_path": client.metadata["dll_path"],
            "dll_sha256": client.metadata["sha256"],
            "accessors": client.metadata["accessors"],
        }


def _require_string(data: Mapping[str, object], name: str) -> str:
    value = data.get(name)
    if not isinstance(value, str) or not value.strip():
        raise SteamNativeError("INVALID_PLAN", f"{name} must be a non-empty string")
    return value


def _read_description(data: Mapping[str, object]) -> tuple[str, dict[str, object]]:
    inline = data.get("description")
    source = data.get("description_path")
    if inline is not None and source is not None:
        raise SteamNativeError(
            "INVALID_PLAN", "provide description or description_path, not both"
        )
    if isinstance(inline, str):
        encoded = inline.encode("utf-8")
        return inline, {
            "source": "inline",
            "size": len(encoded),
            "sha256": hashlib.sha256(encoded).hexdigest(),
        }
    if not isinstance(source, str) or not source:
        raise SteamNativeError(
            "INVALID_PLAN", "description or description_path is required"
        )
    path = Path(source).expanduser().resolve()
    if not path.is_file():
        raise SteamNativeError(
            "INVALID_PLAN", f"description_path is not a file: {path}"
        )
    try:
        value = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        raise SteamNativeError(
            "INVALID_PLAN", f"description_path is not valid UTF-8: {path}"
        ) from exc
    return value, {
        "source": "file",
        "path": str(path),
        "size": path.stat().st_size,
        "sha256": _sha256_file(path),
    }


def _content_manifest(root: Path) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for path in sorted((item for item in root.rglob("*") if item.is_file()), key=str):
        result.append(
            {
                "path": path.relative_to(root).as_posix(),
                "size": path.stat().st_size,
                "sha256": _sha256_file(path),
            }
        )
    if not result:
        raise SteamNativeError("INVALID_PLAN", "content_path contains no files")
    return result


def _parse_item_id(value: object, *, required: bool) -> int | None:
    if value is None and not required:
        return None
    if isinstance(value, bool):
        parsed = 0
    elif isinstance(value, int):
        parsed = value
    elif isinstance(value, str) and value.isdecimal():
        parsed = int(value)
    else:
        parsed = 0
    if parsed <= 0:
        qualifier = "a positive Workshop item ID" if required else "null"
        raise SteamNativeError("INVALID_PLAN", f"target_item_id must be {qualifier}")
    return parsed


def _prepare_plan(data: Mapping[str, object]) -> _PreparedPlan:
    operation_id = _require_string(data, "operation_id")
    operation = _require_string(data, "operation").lower()
    if operation not in {"create", "update"}:
        raise SteamNativeError("INVALID_PLAN", "operation must be create or update")
    raw_app_id = data.get("app_id", data.get("consumer_app_id", DEFAULT_APP_ID))
    if not isinstance(raw_app_id, int) or isinstance(raw_app_id, bool) or raw_app_id <= 0:
        raise SteamNativeError("INVALID_PLAN", "app_id must be a positive integer")
    target_item_id = _parse_item_id(
        data.get("target_item_id"), required=operation == "update"
    )
    if operation == "create" and target_item_id is not None:
        raise SteamNativeError(
            "INVALID_PLAN", "create operation must not have target_item_id"
        )

    title = _require_string(data, "title")
    description, description_identity = _read_description(data)
    content_value = data.get("content_path", data.get("staging_dir"))
    if not isinstance(content_value, str) or not content_value:
        raise SteamNativeError("INVALID_PLAN", "content_path is required")
    content_path = Path(content_value).expanduser().resolve()
    if not content_path.is_dir() or not content_path.is_absolute():
        raise SteamNativeError(
            "INVALID_PLAN", f"content_path is not an absolute directory: {content_path}"
        )
    content_manifest = _content_manifest(content_path)

    preview_path: Path | None = None
    preview_identity: dict[str, object] | None = None
    preview_value = data.get("preview_path")
    if preview_value is not None:
        if not isinstance(preview_value, str) or not preview_value:
            raise SteamNativeError("INVALID_PLAN", "preview_path must be a file path")
        preview_path = Path(preview_value).expanduser().resolve()
        if not preview_path.is_file() or not preview_path.is_absolute():
            raise SteamNativeError(
                "INVALID_PLAN", f"preview_path is not an absolute file: {preview_path}"
            )
        preview_identity = {
            "path": str(preview_path),
            "size": preview_path.stat().st_size,
            "sha256": _sha256_file(preview_path),
        }

    raw_visibility = data.get("visibility", "private")
    if isinstance(raw_visibility, str):
        visibility = _VISIBILITY.get(raw_visibility.lower(), -1)
    elif isinstance(raw_visibility, int) and not isinstance(raw_visibility, bool):
        visibility = raw_visibility
    else:
        visibility = -1
    if visibility not in range(4):
        raise SteamNativeError("INVALID_PLAN", "visibility must be 0..3 or a known name")

    raw_tags = data.get("tags", [])
    if not isinstance(raw_tags, list) or not all(
        isinstance(tag, str) and tag for tag in raw_tags
    ):
        raise SteamNativeError("INVALID_PLAN", "tags must be an array of non-empty strings")
    tags = tuple(raw_tags)
    change_note = data.get("change_note", "")
    if not isinstance(change_note, str):
        raise SteamNativeError("INVALID_PLAN", "change_note must be a string")
    legal_accepted = data.get("workshop_legal_agreement_accepted", False)
    if not isinstance(legal_accepted, bool):
        raise SteamNativeError(
            "INVALID_PLAN", "workshop_legal_agreement_accepted must be boolean"
        )

    payload_identity = {
        "operation_id": operation_id,
        "operation": operation,
        "app_id": raw_app_id,
        "target_item_id": target_item_id,
        "title": title,
        "description": description_identity,
        "content_path": str(content_path),
        "content_manifest": content_manifest,
        "preview": preview_identity,
        "visibility": visibility,
        "tags": list(tags),
        "change_note": change_note,
    }
    payload_sha256 = hashlib.sha256(
        json.dumps(
            payload_identity,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return _PreparedPlan(
        operation_id=operation_id,
        operation=operation,
        app_id=raw_app_id,
        target_item_id=target_item_id,
        title=title,
        description=description,
        content_path=content_path,
        preview_path=preview_path,
        visibility=visibility,
        tags=tags,
        change_note=change_note,
        legal_agreement_accepted=legal_accepted,
        payload_sha256=payload_sha256,
    )


def _load_plan(plan_file: str | Path) -> _PreparedPlan:
    path = Path(plan_file).expanduser().resolve()
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise SteamNativeError("PLAN_NOT_FOUND", f"plan file not found: {path}") from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SteamNativeError("INVALID_PLAN", f"plan file is not valid UTF-8 JSON: {path}") from exc
    if not isinstance(data, dict):
        raise SteamNativeError("INVALID_PLAN", "plan JSON must be an object")
    return _prepare_plan(data)


def _load_receipt(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SteamNativeError(
            "INVALID_RECEIPT", f"receipt is unreadable or invalid JSON: {path}"
        ) from exc
    if not isinstance(data, dict):
        raise SteamNativeError("INVALID_RECEIPT", "receipt JSON must be an object")
    return data


def _fsync_directory(path: Path) -> None:
    if os.name == "nt":
        return
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _write_receipt(path: Path, receipt: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    encoded = (
        json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")
    try:
        with temporary.open("xb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        _fsync_directory(path.parent)
    finally:
        with contextlib.suppress(FileNotFoundError):
            temporary.unlink()


def _new_receipt(plan: _PreparedPlan, stage: str, item_id: int | None) -> dict[str, object]:
    return {
        "schema": "ck3_workshop_mcp.steam_native.receipt.v1",
        "operation_id": plan.operation_id,
        "operation": plan.operation,
        "app_id": plan.app_id,
        "payload_sha256": plan.payload_sha256,
        "stage": stage,
        "item_id": str(item_id) if item_id is not None else None,
        "created_at": _utc_now(),
        "updated_at": _utc_now(),
    }


def _updated(receipt: Mapping[str, object], **changes: object) -> dict[str, object]:
    result = dict(receipt)
    result.update(changes)
    result["updated_at"] = _utc_now()
    return result


def _validate_receipt(plan: _PreparedPlan, receipt: Mapping[str, object]) -> None:
    expected = {
        "operation_id": plan.operation_id,
        "operation": plan.operation,
        "app_id": plan.app_id,
        "payload_sha256": plan.payload_sha256,
    }
    mismatches = {
        key: {"receipt": receipt.get(key), "plan": value}
        for key, value in expected.items()
        if receipt.get(key) != value
    }
    if mismatches:
        raise SteamNativeError(
            "RECEIPT_PLAN_MISMATCH",
            "receipt is bound to a different publication payload",
            details=mismatches,
        )
    receipt_item = receipt.get("item_id")
    if (
        plan.operation == "update"
        and receipt_item is not None
        and str(receipt_item) != str(plan.target_item_id)
    ):
        raise SteamNativeError(
            "RECEIPT_ITEM_MISMATCH", "receipt item ID differs from target_item_id"
        )


def _item_id_from_receipt(receipt: Mapping[str, object]) -> int:
    value = receipt.get("item_id")
    if not isinstance(value, str) or not value.isdecimal() or int(value) <= 0:
        raise SteamNativeError("INVALID_RECEIPT", "receipt has no valid item_id")
    return int(value)


def _terminal_receipt_result(
    receipt: Mapping[str, object], receipt_path: Path
) -> dict[str, object] | None:
    stage = receipt.get("stage")
    if stage == "complete":
        return {
            "schema": "ck3_workshop_mcp.steam_native.publish.v1",
            "ok": True,
            "status": "complete",
            "item_id": receipt.get("item_id"),
            "receipt_file": str(receipt_path),
            "replayed_receipt": True,
        }
    if stage == "complete_eula_required":
        return {
            "schema": "ck3_workshop_mcp.steam_native.publish.v1",
            "ok": False,
            "status": "eula_required",
            "item_id": receipt.get("item_id"),
            "receipt_file": str(receipt_path),
            "legal_agreement_url": WORKSHOP_LEGAL_AGREEMENT_URL,
            "submitted": True,
            "replayed_receipt": True,
        }
    if stage == "create_intent":
        raise SteamNativeError(
            "UNKNOWN_CREATE_RESULT",
            "a prior CreateItem may have reached Steam; automatic retry is forbidden",
            details={"receipt_file": str(receipt_path)},
        )
    if stage == "submit_intent":
        raise SteamNativeError(
            "UNKNOWN_SUBMIT_RESULT",
            "a prior SubmitItemUpdate may have reached Steam; automatic retry is forbidden",
            details={"receipt_file": str(receipt_path)},
        )
    if stage in {"create_failed", "submit_failed"}:
        raise SteamNativeError(
            "RECORDED_STEAM_FAILURE",
            "the prior Steam call returned a known failure; use a new reviewed operation",
            details={"receipt_file": str(receipt_path), "receipt": dict(receipt)},
        )
    return None


def _require_set(ok: bool, field: str) -> None:
    if not ok:
        raise SteamNativeError(
            "SET_ITEM_FIELD_FAILED", f"Steamworks rejected {field} before submit"
        )


def publish(
    dll_path: str | Path,
    plan_file: str | Path,
    receipt_file: str | Path,
) -> dict[str, object]:
    """Create or update one item, durably refusing ambiguous automatic retries."""

    plan = _load_plan(plan_file)
    receipt_path = Path(receipt_file).expanduser().resolve()
    receipt = _load_receipt(receipt_path)
    if receipt is not None:
        _validate_receipt(plan, receipt)
        terminal = _terminal_receipt_result(receipt, receipt_path)
        if terminal is not None:
            return terminal

    if plan.operation == "update" and receipt is None:
        assert plan.target_item_id is not None
        receipt = _new_receipt(plan, "item_id_recorded", plan.target_item_id)
        _write_receipt(receipt_path, receipt)

    if (
        receipt is not None
        and receipt.get("stage") == "eula_required_before_submit"
        and not plan.legal_agreement_accepted
    ):
        return {
            "schema": "ck3_workshop_mcp.steam_native.publish.v1",
            "ok": False,
            "status": "eula_required",
            "item_id": receipt.get("item_id"),
            "receipt_file": str(receipt_path),
            "legal_agreement_url": WORKSHOP_LEGAL_AGREEMENT_URL,
            "submitted": False,
        }

    with _open_client(dll_path, plan.app_id) as client:
        if not client.logged_on():
            raise SteamNativeError(
                "STEAM_USER_OFFLINE", "Steam user interface reports BLoggedOn=false"
            )

        if receipt is None:
            receipt = _new_receipt(plan, "create_intent", None)
            _write_receipt(receipt_path, receipt)
            create_result = client.create_item(plan.app_id)
            if create_result.result != ERESULT_OK or create_result.item_id <= 0:
                receipt = _updated(
                    receipt,
                    stage="create_failed",
                    steam_result=create_result.result,
                    legal_agreement_required=create_result.needs_legal_agreement,
                )
                _write_receipt(receipt_path, receipt)
                raise SteamNativeError(
                    "CREATE_ITEM_FAILED",
                    f"CreateItem returned EResult {create_result.result}",
                    details={"steam_result": create_result.result},
                )
            receipt = _updated(
                receipt,
                stage=(
                    "eula_required_before_submit"
                    if create_result.needs_legal_agreement
                    else "item_id_recorded"
                ),
                item_id=str(create_result.item_id),
                create_result=create_result.result,
                legal_agreement_required=create_result.needs_legal_agreement,
            )
            _write_receipt(receipt_path, receipt)
            if (
                create_result.needs_legal_agreement
                and not plan.legal_agreement_accepted
            ):
                return {
                    "schema": "ck3_workshop_mcp.steam_native.publish.v1",
                    "ok": False,
                    "status": "eula_required",
                    "item_id": str(create_result.item_id),
                    "receipt_file": str(receipt_path),
                    "legal_agreement_url": WORKSHOP_LEGAL_AGREEMENT_URL,
                    "submitted": False,
                }

        assert receipt is not None
        item_id = _item_id_from_receipt(receipt)
        update_handle = client.start_item_update(plan.app_id, item_id)
        _require_set(client.set_title(update_handle, plan.title), "title")
        _require_set(
            client.set_description(update_handle, plan.description), "description"
        )
        _require_set(client.set_content(update_handle, plan.content_path), "content")
        if plan.preview_path is not None:
            _require_set(
                client.set_preview(update_handle, plan.preview_path), "preview"
            )
        _require_set(
            client.set_visibility(update_handle, plan.visibility), "visibility"
        )
        _require_set(client.set_tags(update_handle, plan.tags), "tags")

        receipt = _updated(receipt, stage="submit_intent")
        _write_receipt(receipt_path, receipt)
        submit_result = client.submit_item_update(update_handle, plan.change_note)
        if submit_result.result != ERESULT_OK:
            receipt = _updated(
                receipt,
                stage="submit_failed",
                steam_result=submit_result.result,
                legal_agreement_required=submit_result.needs_legal_agreement,
            )
            _write_receipt(receipt_path, receipt)
            raise SteamNativeError(
                "SUBMIT_ITEM_UPDATE_FAILED",
                f"SubmitItemUpdate returned EResult {submit_result.result}",
                details={"steam_result": submit_result.result, "item_id": str(item_id)},
            )
        receipt = _updated(
            receipt,
            stage=(
                "complete_eula_required"
                if submit_result.needs_legal_agreement
                else "complete"
            ),
            steam_result=submit_result.result,
            legal_agreement_required=submit_result.needs_legal_agreement,
            submitted_at=_utc_now(),
        )
        _write_receipt(receipt_path, receipt)
        return {
            "schema": "ck3_workshop_mcp.steam_native.publish.v1",
            "ok": not submit_result.needs_legal_agreement,
            "status": (
                "eula_required"
                if submit_result.needs_legal_agreement
                else "complete"
            ),
            "item_id": str(item_id),
            "receipt_file": str(receipt_path),
            "legal_agreement_url": (
                WORKSHOP_LEGAL_AGREEMENT_URL
                if submit_result.needs_legal_agreement
                else None
            ),
            "submitted": True,
        }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m ck3_workshop_mcp.steam_native",
        description="Direct Steamworks flat-API metadata, probe, and publish bridge",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    symbols_parser = subparsers.add_parser(
        "symbols", help="read PE exports without loading Steamworks"
    )
    symbols_parser.add_argument("--dll", required=True)

    probe_parser = subparsers.add_parser(
        "probe", help="initialize Steamworks and read the active AppID/user"
    )
    probe_parser.add_argument("--dll", required=True)
    probe_parser.add_argument("--app-id", type=int, default=DEFAULT_APP_ID)

    publish_parser = subparsers.add_parser(
        "publish", help="create or update a Workshop item from a reviewed plan"
    )
    publish_parser.add_argument("--dll", required=True)
    publish_parser.add_argument("--plan-file", required=True)
    publish_parser.add_argument("--receipt-file", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        if arguments.command == "symbols":
            result = symbols(arguments.dll)
        elif arguments.command == "probe":
            result = probe(arguments.dll, arguments.app_id)
        else:
            result = publish(
                arguments.dll, arguments.plan_file, arguments.receipt_file
            )
    except SteamNativeError as exc:
        result = {"ok": False, "error": exc.as_dict()}
        exit_code = 2
    except Exception as exc:  # pragma: no cover - last-resort JSON CLI envelope
        result = {
            "ok": False,
            "error": {"code": "UNEXPECTED_ERROR", "message": str(exc)},
        }
        exit_code = 3
    else:
        exit_code = 0 if result.get("ok") else 2
    sys.stdout.write(json.dumps(result, ensure_ascii=False, sort_keys=True) + "\n")
    return exit_code


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
