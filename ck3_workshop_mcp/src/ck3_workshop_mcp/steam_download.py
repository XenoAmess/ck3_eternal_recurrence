"""Isolated, exact-target Workshop download using Steam manual callbacks.

DownloadItem returns a bool, not a SteamAPICall_t. This worker deliberately
uses ManualDispatch only, in a fresh process, and never subscribes or publishes.
"""

from __future__ import annotations

import argparse
import ctypes
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Sequence

from .steam_native import DEFAULT_APP_ID, ERESULT_OK, SteamNativeError, _bind, _open_client, symbols


SCHEMA = "ck3_workshop_mcp.steam_native.download.v1"
DOWNLOAD_ITEM_CALLBACK_ID = 3406
_STATE_BITS = {"subscribed": 1, "legacy": 2, "installed": 4, "needs_update": 8,
               "downloading": 16, "download_pending": 32}


class CallbackMsg(ctypes.Structure):
    """Valve CallbackMsg_t, default Win64 packing (24 bytes)."""

    _fields_ = (("steam_user", ctypes.c_int32), ("callback_id", ctypes.c_int32),
                ("parameter", ctypes.c_void_p), ("parameter_size", ctypes.c_int32))


class DownloadItemResult(ctypes.Structure):
    """Valve DownloadItemResult_t: app at 0, item at 8, result at 16."""

    _fields_ = (("app_id", ctypes.c_uint32), ("item_id", ctypes.c_uint64),
                ("result", ctypes.c_int32))


def _arguments(dll_path: str | Path, item_id: str, app_id: int,
               timeout_seconds: float, expected_cache_path: str | Path | None) -> dict[str, Any]:
    if not isinstance(item_id, str) or not item_id.isascii() or not item_id.isdecimal() or not 0 < int(item_id) < 2**64:
        raise SteamNativeError("INVALID_ITEM_ID", "item_id must be a nonzero uint64 decimal string")
    if isinstance(app_id, bool) or not isinstance(app_id, int) or not 0 < app_id < 2**32:
        raise SteamNativeError("INVALID_APP_ID", "app_id must be a nonzero uint32")
    if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float)) or not math.isfinite(timeout_seconds) or not 0 < timeout_seconds <= 3600:
        raise SteamNativeError("INVALID_TIMEOUT", "timeout_seconds must be greater than zero and at most 3600")
    item_id = str(int(item_id))
    expected = None
    if expected_cache_path is not None:
        path = Path(expected_cache_path).expanduser()
        if not path.is_absolute() or path.name != item_id:
            raise SteamNativeError("INVALID_CACHE_PATH", "expected_cache_path must be absolute and end with the exact item_id")
        expected = str(path.resolve())
    return {"dll_path": str(Path(dll_path).expanduser().resolve()), "item_id": item_id,
            "app_id": app_id, "timeout_seconds": float(timeout_seconds),
            "expected_cache_path": expected}


def _base(arguments: dict[str, Any]) -> dict[str, Any]:
    return {"schema": SCHEMA, "ok": False, "status": "failed", **arguments,
            "isolated_worker": True, "started": False, "callback": None,
            "state_flags": None, "download_info": None, "install_info": None,
            "ignored_callbacks": 0, "fresh_cache_requested": arguments["expected_cache_path"] is not None}


class _NativeDownloadApi:
    def __init__(self, client: Any) -> None:
        self.client = client
        library = client.library
        self._manual_init = _bind(library, "SteamAPI_ManualDispatch_Init", None, ())
        self._pipe = _bind(library, "SteamAPI_GetHSteamPipe", ctypes.c_int32, ())
        self._frame = _bind(library, "SteamAPI_ManualDispatch_RunFrame", None, (ctypes.c_int32,))
        self._next = _bind(library, "SteamAPI_ManualDispatch_GetNextCallback", ctypes.c_bool,
                           (ctypes.c_int32, ctypes.POINTER(CallbackMsg)))
        self._free = _bind(library, "SteamAPI_ManualDispatch_FreeLastCallback", None, (ctypes.c_int32,))
        self._download = _bind(library, "SteamAPI_ISteamUGC_DownloadItem", ctypes.c_bool,
                               (ctypes.c_void_p, ctypes.c_uint64, ctypes.c_bool))
        self._state = _bind(library, "SteamAPI_ISteamUGC_GetItemState", ctypes.c_uint32,
                            (ctypes.c_void_p, ctypes.c_uint64))
        self._progress = _bind(library, "SteamAPI_ISteamUGC_GetItemDownloadInfo", ctypes.c_bool,
                               (ctypes.c_void_p, ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(ctypes.c_uint64)))
        self._install = _bind(library, "SteamAPI_ISteamUGC_GetItemInstallInfo", ctypes.c_bool,
                              (ctypes.c_void_p, ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64),
                               ctypes.c_void_p, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32)))
        self._manual_init()
        self.pipe = int(self._pipe())
        if self.pipe <= 0:
            raise SteamNativeError("INVALID_STEAM_PIPE", "SteamAPI_GetHSteamPipe returned no active pipe")

    def start(self, item_id: int) -> bool:
        # High-priority true would suspend unrelated Steam downloads.
        return bool(self._download(self.client.ugc, item_id, False))

    def callbacks(self):
        self._frame(self.pipe)
        message = CallbackMsg()
        while self._next(self.pipe, ctypes.byref(message)):
            event = None
            try:
                if message.callback_id == DOWNLOAD_ITEM_CALLBACK_ID:
                    if message.parameter_size != ctypes.sizeof(DownloadItemResult) or not message.parameter:
                        raise SteamNativeError("DOWNLOAD_CALLBACK_ABI_MISMATCH", "DownloadItemResult_t has an unexpected size or null payload")
                    result = DownloadItemResult.from_buffer_copy(ctypes.string_at(message.parameter, message.parameter_size))
                    # Copy the fields before FreeLastCallback invalidates the payload.
                    event = {"callback_id": DOWNLOAD_ITEM_CALLBACK_ID, "app_id": int(result.app_id),
                             "item_id": str(result.item_id), "result": int(result.result)}
            finally:
                self._free(self.pipe)
            yield event

    def observe(self, item_id: int) -> tuple[dict[str, Any], dict[str, Any]]:
        state = int(self._state(self.client.ugc, item_id))
        flags = {"raw": state, **{name: bool(state & bit) for name, bit in _STATE_BITS.items()}}
        downloaded, total = ctypes.c_uint64(), ctypes.c_uint64()
        available = bool(self._progress(self.client.ugc, item_id, ctypes.byref(downloaded), ctypes.byref(total)))
        return flags, {"available": available, "downloaded_bytes": int(downloaded.value) if available else None,
                       "total_bytes": int(total.value) if available else None}

    def installation(self, item_id: int) -> dict[str, Any] | None:
        size, timestamp = ctypes.c_uint64(), ctypes.c_uint32()
        folder = ctypes.create_string_buffer(32768)
        available = self._install(self.client.ugc, item_id, ctypes.byref(size), folder,
                                  len(folder), ctypes.byref(timestamp))
        if not available:
            return None
        return {"path": folder.value.decode("utf-8"), "size_on_disk": int(size.value),
                "timestamp": int(timestamp.value)}


def _run_download(api: Any, arguments: dict[str, Any]) -> dict[str, Any]:
    report = _base(arguments)
    report["worker_pid"] = os.getpid()
    start = time.monotonic()
    deadline = start + arguments["timeout_seconds"]
    item = int(arguments["item_id"])
    expected = arguments["expected_cache_path"]
    if expected and os.path.lexists(expected):
        report["error"] = {"code": "CACHE_ALREADY_EXISTS", "message": "Caller must back up/move the exact expected cache before fresh download"}
        return report
    report["expected_cache_absent_before_start"] = True if expected else None
    # Once the call is attempted, an exception cannot prove that no download began.
    report["status"] = "unknown"
    report["started"] = None
    try:
        report["started"] = api.start(item)
        if not report["started"]:
            report.update(status="failed", error={"code": "DOWNLOAD_NOT_STARTED", "message": "DownloadItem returned false"})
            return report
        while time.monotonic() < deadline:
            for callback in api.callbacks():
                if callback is None or callback["app_id"] != arguments["app_id"] or callback["item_id"] != arguments["item_id"]:
                    report["ignored_callbacks"] += 1
                    continue
                report["callback"] = callback
            report["state_flags"], report["download_info"] = api.observe(item)
            callback = report["callback"]
            if callback is not None:
                if callback["result"] != ERESULT_OK:
                    report.update(status="failed", error={"code": "DOWNLOAD_FAILED", "message": f"DownloadItemResult returned EResult {callback['result']}"})
                    return report
                report["status"] = "partial"
                # Valve requires the matching download callback before this read.
                install = api.installation(item)
                report["install_info"] = install
                flags = report["state_flags"]
                if install is not None:
                    installed_path = Path(install["path"]).resolve()
                    if expected and installed_path != Path(expected):
                        report["error"] = {"code": "INSTALL_PATH_MISMATCH", "message": "Steam installation path differs from the exact caller-supplied cache"}
                        return report
                    if flags["installed"] and not any(flags[k] for k in ("needs_update", "downloading", "download_pending")) and installed_path.is_dir():
                        report.update(ok=True, status="complete")
                        return report
            time.sleep(min(0.1, max(0, deadline - time.monotonic())))
        report["error"] = {"code": "DOWNLOAD_TIMEOUT", "message": "Download completion remains unverified; inspect reported callback/state before any new operation"}
        return report
    except Exception as error:
        report["error"] = error.as_dict() if isinstance(error, SteamNativeError) else {"code": "DOWNLOAD_OBSERVATION_FAILED", "message": str(error)}
        return report
    finally:
        report["elapsed_seconds"] = round(time.monotonic() - start, 3)


def _worker(arguments: dict[str, Any]) -> dict[str, Any]:
    report = _base(arguments)
    try:
        metadata = symbols(arguments["dll_path"])
        if metadata["download_missing"]:
            raise SteamNativeError("MISSING_DOWNLOAD_EXPORTS", "Steam API DLL lacks native download exports", details={"missing": metadata["download_missing"]})
        if ctypes.sizeof(ctypes.c_void_p) != 8 or metadata["pe"]["bits"] != 64:
            raise SteamNativeError("UNSUPPORTED_DOWNLOAD_ABI", "Download worker requires the 64-bit Steam DLL and Python")
        with _open_client(arguments["dll_path"], arguments["app_id"]) as client:
            if not client.logged_on():
                raise SteamNativeError("STEAM_NOT_LOGGED_ON", "An existing authorized online Steam session is required")
            report = _run_download(_NativeDownloadApi(client), arguments)
        report["dll_sha256"] = metadata["sha256"]
        return report
    except Exception as error:
        report["ok"] = False
        if report.get("started"):
            report["status"] = "partial" if report.get("callback") else "unknown"
        report["error"] = error.as_dict() if isinstance(error, SteamNativeError) else {"code": "DOWNLOAD_WORKER_FAILED", "message": str(error)}
        return report


def download(dll_path: str | Path, item_id: str, app_id: int = DEFAULT_APP_ID,
             timeout_seconds: float = 300, expected_cache_path: str | Path | None = None) -> dict[str, Any]:
    """Spawn a fresh callback owner. This function never loads Steam in the caller."""
    arguments = _arguments(dll_path, item_id, app_id, timeout_seconds, expected_cache_path)
    command = [sys.executable, "-m", "ck3_workshop_mcp.steam_download", "--worker",
               "--dll", arguments["dll_path"], "--item-id", arguments["item_id"],
               "--app-id", str(app_id), "--timeout-seconds", str(arguments["timeout_seconds"])]
    if arguments["expected_cache_path"]:
        command.extend(("--expected-cache-path", arguments["expected_cache_path"]))
    try:
        process = subprocess.run(command, capture_output=True, text=True, encoding="utf-8",
                                 timeout=arguments["timeout_seconds"] + 15, check=False)
        result = json.loads(process.stdout)
        if not isinstance(result, dict) or result.get("schema") != SCHEMA or result.get("item_id") != arguments["item_id"] or result.get("app_id") != app_id:
            raise ValueError("worker response does not match the exact requested target")
        result["worker_exit_code"] = process.returncode
        if process.returncode and result.get("ok"):
            raise ValueError("worker claimed success despite a nonzero process exit")
        return result
    except (subprocess.TimeoutExpired, ValueError, OSError) as error:
        # subprocess.run kills only its own worker on timeout. Steam can continue
        # the download; neither worker failure nor missing JSON authorizes retry.
        report = _base(arguments)
        report.update(status="unknown", started=None,
                      error={"code": "DOWNLOAD_WORKER_RESULT_UNKNOWN", "message": str(error)})
        return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dll", required=True)
    parser.add_argument("--item-id", required=True)
    parser.add_argument("--app-id", type=int, default=DEFAULT_APP_ID)
    parser.add_argument("--timeout-seconds", type=float, default=300)
    parser.add_argument("--expected-cache-path")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    try:
        arguments = _arguments(args.dll, args.item_id, args.app_id, args.timeout_seconds, args.expected_cache_path)
        result = _worker(arguments) if args.worker else download(**arguments)
    except SteamNativeError as error:
        result = {"ok": False, "status": "failed", "error": error.as_dict()}
    sys.stdout.write(json.dumps(result, ensure_ascii=False, sort_keys=True) + "\n")
    return 0 if result.get("ok") else 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
