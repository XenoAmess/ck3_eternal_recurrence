"""Construction-only process identity cache with a fresh kernel proof per read.

The WMI spelling remains evidence. The cache never substitutes a formatted
timestamp and never authorizes a PID from a previous process generation.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import os
from typing import Callable, Mapping

from ..environment import process_creation_utc
from .driver import BridgeUnavailableError
from .normal_exit_process_observer_v1 import (
    PROCESS_QUERY_LIMITED_INFORMATION, SYNCHRONIZE, WAIT_TIMEOUT,
    Win32ProcessApi,
)


@dataclass(frozen=True)
class _KernelIdentity:
    pid: int
    creation_filetime: int
    executable: str


@dataclass(frozen=True)
class _ConstructionIdentityPin:
    kernel: _KernelIdentity
    creation_date: str


def _kernel_process_identity(pid: int) -> _KernelIdentity:
    """Read live PID, full 100ns birth and image from one original handle."""
    import ctypes
    from ctypes import wintypes

    api = Win32ProcessApi()
    handle = api.open_process(SYNCHRONIZE | PROCESS_QUERY_LIMITED_INFORMATION, pid)
    try:
        actual_pid = api.process_id(handle)
        creation = api.creation_filetime(handle)
        query_image = api._kernel.QueryFullProcessImageNameW
        query_image.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR,
                                ctypes.POINTER(wintypes.DWORD)]
        query_image.restype = wintypes.BOOL
        image = ctypes.create_unicode_buffer(32768)
        length = wintypes.DWORD(len(image))
        if not query_image(handle, 0, image, ctypes.byref(length)):
            raise ctypes.WinError(ctypes.get_last_error())
        if actual_pid != pid or creation <= 0 or not image.value:
            raise ValueError("construction process handle identity is incomplete")
        if api.wait(handle, 0) != WAIT_TIMEOUT:
            raise ValueError("construction process is not proven running")
        return _KernelIdentity(actual_pid, creation,
                               os.path.normcase(os.path.abspath(image.value)))
    finally:
        api.close(handle)


def _try_kernel_identity(pid: int) -> _KernelIdentity | None:
    try:
        return _kernel_process_identity(pid)
    except Exception:
        # Access/platform/observation failure preserves the original WMI path.
        return None


def _matches_wmi(identity: Mapping[str, object], kernel: _KernelIdentity) -> bool:
    if type(identity.get("pid")) is not int or identity["pid"] != kernel.pid:
        return False
    image = identity.get("executable")
    creation = identity.get("creation_date")
    if not isinstance(image, str) or not image or not isinstance(creation, str):
        return False
    if os.path.normcase(os.path.abspath(image)) != kernel.executable:
        return False
    try:
        # WMI records microseconds; retain the full FILETIME in the pin.
        utc = datetime(1601, 1, 1, tzinfo=timezone.utc) + timedelta(
            microseconds=kernel.creation_filetime // 10)
        return process_creation_utc(creation) == utc
    except (TypeError, ValueError, OverflowError):
        return False


def read_construction_process_identity_v1(
        driver: object, pid: int,
        identity_reader: Callable[[int], Mapping[str, object] | None],
) -> Mapping[str, object] | None:
    """Return original creation bytes only after rechecking this live birth."""
    pin = getattr(driver, "_construction_process_identity_pin_v1", None)
    before = _try_kernel_identity(pid)
    if isinstance(pin, _ConstructionIdentityPin) and before == pin.kernel:
        return {"pid": pid, "creation_date": pin.creation_date}
    if (isinstance(pin, _ConstructionIdentityPin) and before is not None
            and before.pid == pin.kernel.pid):
        # A proven new birth/image at this PID is not an observation failure.
        # WMI has only microseconds and could conceal a 100ns birth change.
        raise BridgeUnavailableError("construction process generation or image changed")

    # A cache miss/change always uses the original identity producer. No
    # startup process discovery, command line or executable checks are changed.
    identity = identity_reader(pid)
    if (before is not None and isinstance(identity, Mapping)
            and _matches_wmi(identity, before)
            and _try_kernel_identity(pid) == before):
        try:
            setattr(driver, "_construction_process_identity_pin_v1",
                    _ConstructionIdentityPin(before, identity["creation_date"]))
        except (AttributeError, TypeError):
            pass  # Slot-only fixture/driver retains original WMI behavior.
    return identity
