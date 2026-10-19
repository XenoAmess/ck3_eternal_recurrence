"""Fixture-only direct Python launch; never normalize a production command.

Windows venv python.exe may be a forwarding launcher with another returned PID.
Owned custody fixtures require the actual interpreter as the direct child and
retain the caller's dependency search paths explicitly. Peer checks stay exact.
"""
import os
from pathlib import Path
import sys


def _loaded_image_v1():
    if os.name != "nt":
        raise OSError("owned direct launch qualification is Windows-only")
    import ctypes
    from ctypes import wintypes as w
    kernel=ctypes.WinDLL("kernel32",use_last_error=True)
    read=kernel.GetModuleFileNameW
    read.argtypes,read.restype=[w.HMODULE,w.LPWSTR,w.DWORD],w.DWORD
    buffer=ctypes.create_unicode_buffer(32768)
    size=read(None,buffer,len(buffer))
    if not size or size>=len(buffer):
        raise OSError("actual current interpreter image unavailable")
    return buffer.value


def owned_python_launch_v1():
    """Return this interpreter's exact direct image and explicit fixture env.

    No PATH lookup, PID substitution, shell/launcher following or child adoption.
    A production caller must separately qualify its real command as direct;
    this fixture selector does not grant venv forwarding commands that property.
    """
    actual=_loaded_image_v1()
    base=getattr(sys,"_base_executable",None)
    if not base or not os.path.samefile(actual,base):
        raise ValueError("actual interpreter image differs from declared base executable")
    paths=[]
    for value in (*sys.path,*os.environ.get("PYTHONPATH","").split(os.pathsep)):
        if value:
            absolute=str(Path(value).resolve())
            if absolute not in paths:paths.append(absolute)
    env=dict(os.environ)
    env["PYTHONPATH"]=os.pathsep.join(paths)
    return str(Path(actual).resolve()),env
