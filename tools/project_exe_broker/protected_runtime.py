"""Isolated protected-only runtime setup; no COM activation or OS settings."""
from pathlib import Path
import ctypes
import importlib.abc
import os
import sys
_DLL_HANDLES=[]
class DenyGeneratedCode(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname in {"sitecustomize","usercustomize","win32com.client.gencache","win32com.client.makepy","win32com.client.genpy"} or fullname.startswith("win32com.gen_py"):
            raise ImportError("Untrusted/generated COM code disabled: " + fullname)
        return None
def activate_sealed_paths(root):
    root=Path(root)
    runtime=root/"runtime"
    allowed=[runtime/"Lib",runtime/"DLLs",root/"deps",root/"deps/win32",root/"deps/win32/lib",root]
    if not (runtime/"python314._pth").is_file():raise RuntimeError("Missing sealed Python path file")
    kernel=ctypes.WinDLL("kernel32",use_last_error=True)
    kernel.SetDefaultDllDirectories.argtypes=[ctypes.c_uint32];kernel.SetDefaultDllDirectories.restype=ctypes.c_int
    kernel.SetDllDirectoryW.argtypes=[ctypes.c_wchar_p];kernel.SetDllDirectoryW.restype=ctypes.c_int
    if not kernel.SetDefaultDllDirectories(0x1000) or not kernel.SetDllDirectoryW(""):
        raise ctypes.WinError(ctypes.get_last_error())
    for path in (runtime,runtime/"DLLs",root/"deps/pywin32_system32",root/"deps/win32"):
        _DLL_HANDLES.append(os.add_dll_directory(str(path)))
    sys.path[:]=[str(p) for p in allowed]
    sys.dont_write_bytecode=True
    sys.meta_path.insert(0,DenyGeneratedCode())
    return root
def require_fixed_protected_root(root):
    import ntpath
    if ntpath.normcase(str(Path(root)))!=ntpath.normcase(r"C:\Program Files\XAR CK3 Project EXE Broker"):
        raise RuntimeError("Refuse actual broker run outside fixed protected installation")
