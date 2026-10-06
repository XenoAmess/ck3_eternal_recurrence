"""Read Cloud Files metadata without opening video content."""

import ctypes
import datetime
import json
import os
import sys
from ctypes import wintypes


class StandardInfo(ctypes.Structure):
    _fields_ = [
        ("on_disk", ctypes.c_longlong),
        ("validated", ctypes.c_longlong),
        ("modified", ctypes.c_longlong),
        ("properties", ctypes.c_longlong),
        ("pin_state", wintypes.DWORD),
        ("in_sync_state", wintypes.DWORD),
        ("file_id", ctypes.c_longlong),
        ("sync_root_file_id", ctypes.c_longlong),
        ("identity_length", wintypes.DWORD),
    ]


class AttributeTagInfo(ctypes.Structure):
    _fields_ = [("file_attributes", wintypes.DWORD), ("reparse_tag", wintypes.DWORD)]


kernel = ctypes.WinDLL("kernel32", use_last_error=True)
cloud = ctypes.WinDLL("CldApi", use_last_error=True)
kernel.GetFileAttributesW.argtypes = [wintypes.LPCWSTR]
kernel.GetFileAttributesW.restype = wintypes.DWORD
kernel.CreateFileW.argtypes = [
    wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p,
    wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE,
]
kernel.CreateFileW.restype = wintypes.HANDLE
kernel.CloseHandle.argtypes = [wintypes.HANDLE]
kernel.CloseHandle.restype = wintypes.BOOL
kernel.GetFileInformationByHandleEx.argtypes = [
    wintypes.HANDLE, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD,
]
kernel.GetFileInformationByHandleEx.restype = wintypes.BOOL
cloud.CfGetPlaceholderInfo.argtypes = [
    wintypes.HANDLE, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD),
]
cloud.CfGetPlaceholderInfo.restype = ctypes.c_long
cloud.CfGetSyncRootInfoByPath.argtypes = [
    wintypes.LPCWSTR, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD),
]
cloud.CfGetSyncRootInfoByPath.restype = ctypes.c_long
cloud.CfGetPlaceholderStateFromAttributeTag.argtypes = [wintypes.DWORD, wintypes.DWORD]
cloud.CfGetPlaceholderStateFromAttributeTag.restype = wintypes.DWORD


def query(path):
    result = {"path": path, "sample_utc": datetime.datetime.now(datetime.UTC).isoformat()}
    stat = os.stat(path, follow_symlinks=False)
    result.update(size=stat.st_size, mtime_ns=stat.st_mtime_ns)
    result["attributes_hex"] = f"0x{kernel.GetFileAttributesW(path):08X}"
    root_buffer = ctypes.create_string_buffer(4096)
    root_length = wintypes.DWORD()
    root_hr = cloud.CfGetSyncRootInfoByPath(
        path, 0, root_buffer, len(root_buffer), ctypes.byref(root_length)
    )
    result["sync_root_hresult"] = f"0x{root_hr & 0xFFFFFFFF:08X}"
    # READ_ATTRIBUTES, shared access, OPEN_EXISTING, OPEN_NO_RECALL|OPEN_REPARSE_POINT.
    handle = kernel.CreateFileW(path, 0x80, 7, None, 3, 0x300000, None)
    if handle == wintypes.HANDLE(-1).value:
        result["open_error"] = ctypes.get_last_error()
        return result
    try:
        tag_info = AttributeTagInfo()
        if kernel.GetFileInformationByHandleEx(handle, 9, ctypes.byref(tag_info), ctypes.sizeof(tag_info)):
            result["handle_attributes_hex"] = f"0x{tag_info.file_attributes:08X}"
            result["reparse_tag_hex"] = f"0x{tag_info.reparse_tag:08X}"
            state = cloud.CfGetPlaceholderStateFromAttributeTag(
                tag_info.file_attributes, tag_info.reparse_tag
            )
            result["cf_placeholder_state_hex"] = f"0x{state:08X}"
            result["cf_placeholder_state_flags"] = [
                name for bit, name in [
                    (1, "PLACEHOLDER"), (2, "SYNC_ROOT"), (4, "ESSENTIAL_PROP_PRESENT"),
                    (8, "IN_SYNC"), (16, "PARTIAL"), (32, "PARTIALLY_ON_DISK"),
                ] if state != 0xFFFFFFFF and state & bit
            ]
        else:
            result["attribute_tag_error"] = ctypes.get_last_error()
        buffer = ctypes.create_string_buffer(4096)
        returned = wintypes.DWORD()
        hr = cloud.CfGetPlaceholderInfo(handle, 1, buffer, len(buffer), ctypes.byref(returned))
        result["placeholder_hresult"] = f"0x{hr & 0xFFFFFFFF:08X}"
        result["placeholder_returned_bytes"] = returned.value
        if hr == 0:
            info = StandardInfo.from_buffer_copy(buffer)
            result.update(
                in_sync_state=info.in_sync_state,
                on_disk=info.on_disk,
                validated=info.validated,
                modified=info.modified,
                pin_state=info.pin_state,
                file_id=info.file_id,
                sync_root_file_id=info.sync_root_file_id,
            )
    finally:
        kernel.CloseHandle(handle)
    stat_after = os.stat(path, follow_symlinks=False)
    result["stable_size_mtime"] = (stat.st_size, stat.st_mtime_ns) == (
        stat_after.st_size, stat_after.st_mtime_ns
    )
    return result


for name in sys.argv[1:]:
    try:
        print(json.dumps(query(name), ensure_ascii=False))
    except OSError as exc:
        print(json.dumps({"path": name, "error": str(exc)}, ensure_ascii=False))
