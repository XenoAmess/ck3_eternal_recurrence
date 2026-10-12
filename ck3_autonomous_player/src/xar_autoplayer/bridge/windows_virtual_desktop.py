"""Read public Windows virtual-desktop metadata without changing user focus."""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import uuid


class _Guid(ctypes.Structure):
    _fields_ = [("data1", wintypes.DWORD), ("data2", wintypes.WORD),
                ("data3", wintypes.WORD), ("data4", ctypes.c_ubyte * 8)]

    @classmethod
    def from_string(cls, value: str) -> "_Guid":
        return cls.from_buffer_copy(uuid.UUID(value).bytes_le)


def window_virtual_desktop(hwnd: int) -> dict[str, object]:
    """Query membership and DWM cloaking; never switch, move or activate windows."""
    ole = ctypes.WinDLL("ole32")
    ole.CoUninitialize.argtypes = []
    ole.CoUninitialize.restype = None
    ole.CoInitializeEx.argtypes = [ctypes.c_void_p, wintypes.DWORD]
    ole.CoInitializeEx.restype = ctypes.c_long
    ole.CoCreateInstance.argtypes = [ctypes.POINTER(_Guid), ctypes.c_void_p,
                                   wintypes.DWORD, ctypes.POINTER(_Guid),
                                   ctypes.POINTER(ctypes.c_void_p)]
    ole.CoCreateInstance.restype = ctypes.c_long
    manager = ctypes.c_void_p()
    initialized = ole.CoInitializeEx(None, 2)
    if initialized < 0 and initialized != -2147417850:  # RPC_E_CHANGED_MODE
        raise OSError(f"CoInitializeEx HRESULT {initialized:#x}")
    try:
        clsid = _Guid.from_string("AA509086-5CA9-4C25-8F95-589D3C07B48A")
        iid = _Guid.from_string("A5CD92FF-29BE-454C-8D04-D82879FB3F1B")
        hr = ole.CoCreateInstance(ctypes.byref(clsid), None, 1,
                                 ctypes.byref(iid), ctypes.byref(manager))
        if hr < 0:
            raise OSError(f"VirtualDesktopManager HRESULT {hr:#x}")
        table = ctypes.cast(manager, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
        current = wintypes.BOOL()
        hr = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, wintypes.HWND,
                               ctypes.POINTER(wintypes.BOOL))(table[3])(
            manager, hwnd, ctypes.byref(current))
        if hr < 0:
            raise OSError(f"IsWindowOnCurrentVirtualDesktop HRESULT {hr:#x}")
        desktop = _Guid()
        hr = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, wintypes.HWND,
                               ctypes.POINTER(_Guid))(table[4])(
            manager, hwnd, ctypes.byref(desktop))
        if hr < 0:
            raise OSError(f"GetWindowDesktopId HRESULT {hr:#x}")
        dwm = ctypes.WinDLL("dwmapi")
        dwm.DwmGetWindowAttribute.argtypes = [wintypes.HWND, wintypes.DWORD,
                                            ctypes.c_void_p, wintypes.DWORD]
        dwm.DwmGetWindowAttribute.restype = ctypes.c_long
        cloaked = wintypes.DWORD()
        hr = dwm.DwmGetWindowAttribute(hwnd, 14, ctypes.byref(cloaked), ctypes.sizeof(cloaked))
        if hr < 0:
            raise OSError(f"DWMWA_CLOAKED HRESULT {hr:#x}")
        return {"window_hwnd": hwnd, "on_current_virtual_desktop": bool(current.value),
                "desktop_id": str(uuid.UUID(bytes_le=bytes(desktop))),
                "dwm_cloaked_flags": cloaked.value}
    finally:
        if manager.value:
            table = ctypes.cast(manager, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
            ctypes.WINFUNCTYPE(wintypes.ULONG, ctypes.c_void_p)(table[2])(manager)
        if initialized >= 0:
            ole.CoUninitialize()


def move_own_window_to_desktop(hwnd: int, desktop_id: str) -> dict[str, object]:
    """Move only this process's window and verify its assigned desktop."""
    import os
    user = ctypes.WinDLL("user32")
    user.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user.GetWindowThreadProcessId.restype = wintypes.DWORD
    pid = wintypes.DWORD()
    if not user.GetWindowThreadProcessId(hwnd, ctypes.byref(pid)) or pid.value != os.getpid():
        raise ValueError("virtual-desktop move is restricted to this process's own window")
    target = _Guid.from_string(desktop_id)
    ole = ctypes.WinDLL("ole32")
    ole.CoUninitialize.argtypes = []
    ole.CoUninitialize.restype = None
    ole.CoInitializeEx.argtypes = [ctypes.c_void_p, wintypes.DWORD]
    ole.CoInitializeEx.restype = ctypes.c_long
    ole.CoCreateInstance.argtypes = [ctypes.POINTER(_Guid), ctypes.c_void_p,
                                   wintypes.DWORD, ctypes.POINTER(_Guid),
                                   ctypes.POINTER(ctypes.c_void_p)]
    ole.CoCreateInstance.restype = ctypes.c_long
    manager = ctypes.c_void_p()
    initialized = ole.CoInitializeEx(None, 2)
    if initialized < 0 and initialized != -2147417850:
        raise OSError(f"CoInitializeEx HRESULT {initialized:#x}")
    try:
        clsid = _Guid.from_string("AA509086-5CA9-4C25-8F95-589D3C07B48A")
        iid = _Guid.from_string("A5CD92FF-29BE-454C-8D04-D82879FB3F1B")
        hr = ole.CoCreateInstance(ctypes.byref(clsid), None, 1,
                                 ctypes.byref(iid), ctypes.byref(manager))
        if hr < 0:
            raise OSError(f"VirtualDesktopManager HRESULT {hr:#x}")
        table = ctypes.cast(manager, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
        hr = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, wintypes.HWND,
                               ctypes.POINTER(_Guid))(table[5])(
            manager, hwnd, ctypes.byref(target))
        if hr < 0:
            raise OSError(f"MoveWindowToDesktop HRESULT {hr:#x}")
    finally:
        if manager.value:
            table = ctypes.cast(manager, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
            ctypes.WINFUNCTYPE(wintypes.ULONG, ctypes.c_void_p)(table[2])(manager)
        if initialized >= 0:
            ole.CoUninitialize()
    actual = window_virtual_desktop(hwnd)
    if actual["desktop_id"] != str(uuid.UUID(desktop_id)):
        raise OSError("overlay desktop assignment was not confirmed")
    return actual
