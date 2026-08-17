"""Restore acceptance-test user files when the runner process exits.

This is intentionally a separate process: a forced runner termination cannot
skip restoration of presets.txt/tutorial.txt.
"""

import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

import win32api
import win32con
import win32event


def main():
    parent_pid = int(sys.argv[1])
    ck3_pid_file = Path(sys.argv[2])
    pairs = list(zip(sys.argv[3::2], sys.argv[4::2]))
    try:
        handle = win32api.OpenProcess(win32con.SYNCHRONIZE, False, parent_pid)
        win32event.WaitForSingleObject(handle, win32event.INFINITE)
    except Exception:
        pass

    # CK3 can rewrite both files while shutting down, so stop only the process
    # launched by this runner before restoring the user's originals.
    try:
        ck3_pid = int(ck3_pid_file.read_text(encoding="ascii").strip())
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(ck3_pid)],
                       capture_output=True)
    except (OSError, ValueError):
        pass

    for source, destination in pairs:
        try:
            source = Path(source)
            destination = Path(destination)
            temporary = destination.with_name(destination.name + ".xar_restore_tmp")
            shutil.copy2(source, temporary)
            os.replace(temporary, destination)
            if hashlib.sha256(source.read_bytes()).digest() != hashlib.sha256(destination.read_bytes()).digest():
                raise OSError(f"restore verification failed: {destination}")
        except OSError:
            pass


if __name__ == "__main__":
    main()
