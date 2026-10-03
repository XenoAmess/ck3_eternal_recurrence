"""Subscribe one exact Workshop item and verify its call result and state.

Uses the existing Steam session. Steam may automatically download subscribed
content; a subscribed result does not prove installation or file integrity.
"""

from __future__ import annotations

import ctypes
import math
from pathlib import Path
import time
from typing import Any

from .steam_native import DEFAULT_APP_ID, ERESULT_OK, SteamNativeError, _bind, _open_client, symbols

SCHEMA = "ck3_workshop_mcp.steam_native.subscribe.v1"
SUBSCRIBE_CALLBACK_ID = 1313
SUBSCRIBED_BIT = 1


class SubscribeItemResult(ctypes.Structure):
    """Valve RemoteStorageSubscribePublishedFileResult_t, Win64 layout."""

    _fields_ = (("result", ctypes.c_int32), ("item_id", ctypes.c_uint64))


def _run_subscribe(client: Any, item_id: int, timeout_seconds: float) -> dict[str, Any]:
    report: dict[str, Any] = {"schema": SCHEMA, "ok": False, "status": "failed",
        "item_id": str(item_id), "app_id": client.app_id(), "started": False,
        "callback": None, "state_raw": None, "subscribed": None,
        "installation_verified": False, "content_verified": False}
    start = time.monotonic()
    try:
        subscribe_item = _bind(client.library, "SteamAPI_ISteamUGC_SubscribeItem", ctypes.c_uint64,
                               (ctypes.c_void_p, ctypes.c_uint64))
        get_state = _bind(client.library, "SteamAPI_ISteamUGC_GetItemState", ctypes.c_uint32,
                          (ctypes.c_void_p, ctypes.c_uint64))
        report.update(status="unknown", started=None)
        handle = int(subscribe_item(client.ugc, item_id))
        report["api_call_handle"] = str(handle)
        if handle == 0:
            report.update(status="failed", started=False,
                          error={"code": "SUBSCRIBE_NOT_STARTED", "message": "SubscribeItem returned k_uAPICallInvalid"})
            return report
        report["started"] = True
        raw = client._wait_for_result(handle, SubscribeItemResult, SUBSCRIBE_CALLBACK_ID,
                                      timeout_seconds=timeout_seconds)
        if not isinstance(raw, SubscribeItemResult):
            raise SteamNativeError("SUBSCRIBE_CALLBACK_ABI_MISMATCH", "Unexpected SubscribeItem call result structure")
        callback = {"callback_id": SUBSCRIBE_CALLBACK_ID, "item_id": str(raw.item_id),
                    "result": int(raw.result)}
        report["callback"] = callback
        if int(raw.item_id) != item_id:
            raise SteamNativeError("SUBSCRIBE_CALLBACK_ITEM_MISMATCH", "SubscribeItem call result differs from exact requested item")
        if int(raw.result) != ERESULT_OK:
            report.update(status="failed", error={"code": "SUBSCRIBE_FAILED", "message": f"SubscribeItem returned EResult {raw.result}"})
            return report
        report["status"] = "partial"
        deadline = start + timeout_seconds
        while True:
            state = int(get_state(client.ugc, item_id))
            report.update(state_raw=state, subscribed=bool(state & SUBSCRIBED_BIT))
            if report["subscribed"]:
                report.update(ok=True, status="complete")
                return report
            if time.monotonic() >= deadline:
                report["error"] = {"code": "SUBSCRIPTION_STATE_UNVERIFIED", "message": "Successful exact callback but subscribed state was not observed before timeout"}
                return report
            time.sleep(min(0.05, max(0, deadline - time.monotonic())))
    except Exception as error:
        report["error"] = error.as_dict() if isinstance(error, SteamNativeError) else {"code": "SUBSCRIBE_OBSERVATION_FAILED", "message": str(error)}
        return report
    finally:
        report["elapsed_seconds"] = round(time.monotonic() - start, 3)


def subscribe(dll_path: str | Path, item_id: str, app_id: int = DEFAULT_APP_ID,
              timeout_seconds: float = 180) -> dict[str, Any]:
    """Initiate at most one subscription; never publish, launch, or retry."""
    if not isinstance(item_id, str) or not item_id.isascii() or not item_id.isdecimal() or not 0 < int(item_id) < 2**64:
        raise SteamNativeError("INVALID_ITEM_ID", "item_id must be a nonzero uint64 decimal string")
    if isinstance(app_id, bool) or not isinstance(app_id, int) or not 0 < app_id < 2**32:
        raise SteamNativeError("INVALID_APP_ID", "app_id must be a nonzero uint32")
    if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float)) or not math.isfinite(timeout_seconds) or not 0 < timeout_seconds <= 3600:
        raise SteamNativeError("INVALID_TIMEOUT", "timeout_seconds must be greater than zero and at most 3600")
    metadata = symbols(dll_path)
    if metadata["subscription_missing"]:
        raise SteamNativeError("MISSING_SUBSCRIPTION_EXPORTS", "Steam DLL lacks subscription exports", details={"missing": metadata["subscription_missing"]})
    if ctypes.sizeof(ctypes.c_void_p) != 8 or metadata["pe"]["bits"] != 64:
        raise SteamNativeError("UNSUPPORTED_SUBSCRIPTION_ABI", "Subscription requires 64-bit Python and Steam DLL")
    with _open_client(dll_path, app_id) as client:
        if not client.logged_on():
            raise SteamNativeError("STEAM_NOT_LOGGED_ON", "An existing authorized online Steam session is required")
        result = _run_subscribe(client, int(item_id), float(timeout_seconds))
    result["dll_sha256"] = metadata["sha256"]
    return result
