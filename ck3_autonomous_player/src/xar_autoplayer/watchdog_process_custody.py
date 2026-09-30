from __future__ import annotations

from datetime import timezone
import json
from pathlib import Path
from typing import Callable


class WatchdogProcessCustody:
    def __init__(self, identity: Callable[[int], dict[str, object] | None]) -> None:
        self._identity = identity
        self._processes: dict[int, dict[str, object]] = {}
        self.defer_close = False

    def retain(self, process_id: int) -> None:
        import win32api
        import win32con
        import win32process

        if process_id in self._processes:
            return
        entry: dict[str, object] = {"pid": process_id, "handle_retained": False}
        self._processes[process_id] = entry
        handle = None
        try:
            handle = win32api.OpenProcess(
                win32con.SYNCHRONIZE | win32con.PROCESS_QUERY_INFORMATION
                | win32con.PROCESS_QUERY_LIMITED_INFORMATION | win32con.PROCESS_VM_READ,
                False, process_id,
            )
            entry["handle"] = handle
            entry["handle_retained"] = True
            times = win32process.GetProcessTimes(handle)
            entry["creation_utc"] = times["CreationTime"].astimezone(timezone.utc).isoformat()
            entry["executable"] = win32process.GetModuleFileNameEx(handle, 0)
            identity = self._identity(process_id)
            entry["identity_while_alive"] = identity
            command = str(identity.get("command_line", "")) if identity else ""
            entry["argv_while_alive"] = win32api.CommandLineToArgv(command) if command else None
        except Exception as error:
            entry["identity_error"] = f"{type(error).__name__}: {error}"

    def retain_early_receipt(self, path: Path, parent_pid: int, nonce: str) -> None:
        try:
            receipt = json.loads(path.read_text(encoding="utf-8"))
            if (
                isinstance(receipt, dict)
                and receipt.get("schema") == "xar.watchdog-early-start.v1"
                and receipt.get("nonce") == nonce
                and receipt.get("parent_pid") == parent_pid
                and type(receipt.get("watchdog_pid")) is int
                and receipt["watchdog_pid"] > 0
            ):
                self.retain(receipt["watchdog_pid"])
        except (OSError, ValueError):
            pass

    def snapshot(self) -> list[dict[str, object]]:
        import win32event
        import win32process

        results = []
        for entry in self._processes.values():
            handle = entry.get("handle")
            if handle is not None:
                try:
                    entry["held_handle_wait_status"] = int(win32event.WaitForSingleObject(handle, 0))
                    entry["held_handle_returncode"] = int(win32process.GetExitCodeProcess(handle))
                except Exception as error:
                    entry["handle_observation_error"] = f"{type(error).__name__}: {error}"
            results.append({key: value for key, value in entry.items() if key != "handle"})
        return results

    def close(self) -> None:
        import win32api

        self.snapshot()
        for entry in self._processes.values():
            handle = entry.get("handle")
            if handle is not None:
                try:
                    win32api.CloseHandle(handle)
                except Exception as error:
                    entry["handle_close_error"] = f"{type(error).__name__}: {error}"
                entry["handle"] = None
