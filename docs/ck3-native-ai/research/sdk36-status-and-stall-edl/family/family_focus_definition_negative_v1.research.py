"""Bounded evidence reuse for an unavailable native education definition.

This is an in-memory transport optimization, never a legal/no-op verdict.
Native read failures and any changed game, actor, episode or bridge generation
keep the ordinary query path. A learned missing definition expires after 30
game days and is then read from Native again.
"""

from __future__ import annotations

from typing import Any

PERIOD_RAW = 30 * 24
_MISSING = "education_definition_missing"


def _process_birth_filetime(pid: int) -> int | None:
    """Read the kernel's full process creation FILETIME; fail closed."""
    import ctypes
    import sys

    if sys.platform != "win32":
        return None

    class FILETIME(ctypes.Structure):
        _fields_ = (("low", ctypes.c_ulong), ("high", ctypes.c_ulong))

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    open_process = kernel.OpenProcess
    open_process.argtypes = (ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong)
    open_process.restype = ctypes.c_void_p
    get_times = kernel.GetProcessTimes
    get_times.argtypes = (ctypes.c_void_p,) + (ctypes.POINTER(FILETIME),) * 4
    get_times.restype = ctypes.c_int
    close_handle = kernel.CloseHandle
    close_handle.argtypes = (ctypes.c_void_p,)
    close_handle.restype = ctypes.c_int
    handle = open_process(0x1000, 0, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
    if not handle:
        return None
    try:
        created, exited, kernel_time, user_time = (FILETIME() for _ in range(4))
        if not get_times(handle, ctypes.byref(created), ctypes.byref(exited),
                         ctypes.byref(kernel_time), ctypes.byref(user_time)):
            return None
        value = (int(created.high) << 32) | int(created.low)
        return value if value > 0 else None
    finally:
        close_handle(handle)


def scope(snapshot: dict[str, Any]) -> tuple[tuple[Any, ...], int] | None:
    diagnostics = snapshot.get("diagnostics")
    hello = diagnostics.get("hello") if isinstance(diagnostics, dict) else None
    actor = snapshot.get("played_character")
    if not isinstance(hello, dict) or not isinstance(actor, dict):
        return None
    pid = diagnostics.get("bridge_pid")
    generation = diagnostics.get("connection_generation")
    exe = hello.get("expected_ck3_sha256")
    version = hello.get("expected_ck3_version")
    adapter = hello.get("game_adapter_id")
    episode = snapshot.get("episode_run_id")
    actor_id = actor.get("character_id")
    date = snapshot.get("date_raw")
    native = snapshot.get("native_revision")
    public = snapshot.get("revision")
    snapshot_id = snapshot.get("snapshot_id")
    if (snapshot.get("paused") is not True
            or any(type(x) is not int or x <= 0 for x in
                   (pid, generation, actor_id, date, native, public))
            or not all(isinstance(x, str) and x for x in
                       (exe, version, adapter, episode, snapshot_id))):
        return None
    birth = _process_birth_filetime(pid)
    if type(birth) is not int or birth <= 0:
        return None
    return ((pid, birth, generation, exe, version, adapter, episode, actor_id), date)


def _source_matches(query: dict[str, Any], snapshot: dict[str, Any], target: str) -> bool:
    source = query.get("source_context")
    frame = query.get("source_frame")
    actor = snapshot["played_character"]["character_id"]
    hello = snapshot["diagnostics"]["hello"]
    request_id = query.get("request_id")
    request_suffix = (request_id.removeprefix("child-focus-query-")
                      if isinstance(request_id, str) else "")
    return (query.get("schema") == "child-education-focus-private-12004-v1"
            and query.get("kind") == "query"
            and isinstance(request_id, str)
            and request_id.startswith("child-focus-query-")
            and len(request_suffix) == 32
            and all(char in "0123456789abcdef" for char in request_suffix)
            and type(query.get("child_full_id")) is int
            and query["child_full_id"] > 0
            and query.get("status") == "unavailable"
            and query.get("unavailable_reason") == _MISSING
            and query.get("native_legal") is None
            and query.get("target_key") == target
            and query.get("source_public_revision") == snapshot["revision"]
            and isinstance(source, dict) and isinstance(frame, dict)
            and source.get("snapshot_id") == snapshot["snapshot_id"]
            and source.get("public_revision") == snapshot["revision"]
            and source.get("native_revision") == snapshot["native_revision"]
            and source.get("date_raw") == snapshot["date_raw"]
            and source.get("episode_run_id") == snapshot["episode_run_id"]
            and source.get("controller_full_id") == actor
            and source.get("paused") is True
            and source.get("exact_ck3_build") == hello["expected_ck3_version"]
            and source.get("exe_sha256") == hello["expected_ck3_sha256"]
            and frame.get("snapshot_id") == snapshot["snapshot_id"]
            and frame.get("native_revision") == snapshot["native_revision"]
            and frame.get("date_raw") == snapshot["date_raw"]
            and frame.get("controller_full_id") == actor
            and frame.get("episode_run_id") == snapshot["episode_run_id"]
            and frame.get("paused") is True)


def remember(cache: dict, snapshot: dict, target: str, query: dict) -> None:
    binding = scope(snapshot)
    if binding is None or not isinstance(target, str) or not target:
        return
    key = (binding[0], target)
    if not isinstance(query, dict) or not _source_matches(query, snapshot, target):
        cache.pop(key, None)
        return
    date = binding[1]
    prior = cache.get(key)
    if prior is None:
        cache[key] = {"count": 1, "last_date_raw": date, "until_date_raw": None,
                      "source_request_id": query["request_id"]}
    elif (prior["last_date_raw"] != date
          and prior["source_request_id"] != query["request_id"]):
        # First activation requires two distinct native reads. A qualified
        # expiry renews only after another real native missing-definition read.
        count = min(2, prior["count"] + 1)
        cache[key] = {"count": count, "last_date_raw": date,
                      "until_date_raw": date + PERIOD_RAW if count == 2 else None,
                      "source_request_id": query["request_id"]}


def cached_unavailable(cache: dict, snapshot: dict, target: str) -> dict | None:
    binding = scope(snapshot)
    if binding is None or not isinstance(target, str):
        return None
    item = cache.get((binding[0], target))
    if (not isinstance(item, dict) or item.get("count") != 2
            or type(item.get("until_date_raw")) is not int
            or not item["last_date_raw"] <= binding[1] < item["until_date_raw"]):
        return None
    return {"status": "technical_unavailable_cached", "target_key": target,
            "native_legal": None, "native_query_performed": False,
            "original_unavailable_reason": _MISSING,
            "source_request_id": item["source_request_id"],
            "source_date_raw": item["last_date_raw"],
            "expires_date_raw": item["until_date_raw"]}
