"""One bounded read-only handle snapshot of the exact Native30 Task processes."""
import ctypes as C
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[2]
ROOT = Path("D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/p51-fresh1066-v20261019-prepare01/native30-build-owner01/owner-spec")
SOURCE = REPO / "tools/g2_saved_campaign/interactive_task_owner_v1.py"
SHA = "c0d76a7064996cafd7412f8f39ba2bb5c5cb6271627246b84e946c00bafb864f"
SPEC_SHA = "14f9ef19709a710a298f3275df61a2288b2beaf5c55ec5e1aa000fc799156152"

class HandleEntry(C.Structure):
    _fields_ = [("value", C.c_void_p), ("handles", C.c_size_t), ("pointers", C.c_size_t),
                ("access", C.c_uint32), ("type_index", C.c_uint32),
                ("attributes", C.c_uint32), ("reserved", C.c_uint32)]

class Unicode(C.Structure):
    _fields_ = [("length", C.c_uint16), ("maximum", C.c_uint16), ("buffer", C.c_void_p)]

def main():
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != SHA:
        raise RuntimeError("owner source pin")
    ms = importlib.util.spec_from_file_location("native30_diag_owner", SOURCE)
    owner = importlib.util.module_from_spec(ms)
    ms.loader.exec_module(owner)
    spec = owner.checked_spec(ROOT / "SPEC.json", SPEC_SHA)
    api = owner.Windows()
    owner.require_caller(spec, api.current())
    import win32api, win32con, win32job, pywintypes
    nt = C.WinDLL("ntdll")
    nt.NtQueryInformationProcess.argtypes = [C.c_void_p, C.c_uint32, C.c_void_p, C.c_uint32, C.POINTER(C.c_uint32)]
    nt.NtQueryInformationProcess.restype = C.c_long
    nt.NtQueryObject.argtypes = [C.c_void_p, C.c_uint32, C.c_void_p, C.c_uint32, C.POINTER(C.c_uint32)]
    nt.NtQueryObject.restype = C.c_long
    api.k.QueryInformationJobObject.argtypes = [C.c_void_p, C.c_uint32, C.c_void_p, C.c_uint32, C.POINTER(C.c_uint32)]
    api.k.QueryInformationJobObject.restype = C.c_int

    def object_name(handle):
        buf = C.create_string_buffer(16384)
        needed = C.c_uint32()
        status = nt.NtQueryObject(int(handle), 1, buf, len(buf), C.byref(needed))
        if status < 0:
            return None
        name = Unicode.from_buffer(buf)
        return C.wstring_at(name.buffer, name.length // 2) if name.buffer else ""

    def identity(pid):
        h = api.open(pid)
        try:
            return api.identity(h)
        finally:
            api.close(h)

    start = owner.read(ROOT / "STARTED.json")
    result = {"machine_id": spec["machine_id"], "utc": datetime.now(timezone.utc).isoformat(),
              "scope": "only exact STARTED bootstrap/stage handle tables; named private Jobs only", "owners": {}}
    for label in ("bootstrap", "child"):
        expected = start[label]
        process = win32api.OpenProcess(0x100000 | 0x1000 | 0x400 | 0x40, False, expected["pid"])
        try:
            actual = api.identity(process)
            if any(actual.get(k) != expected.get(k) for k in ("pid", "creation_filetime", "image", "image_file_id", "session")):
                raise RuntimeError("exact STARTED identity changed")
            buf = C.create_string_buffer(262144)
            needed = C.c_uint32()
            status = nt.NtQueryInformationProcess(int(process), 51, buf, len(buf), C.byref(needed))
            if status < 0:
                raise RuntimeError("bounded process handle snapshot NTSTATUS " + hex(status & 0xffffffff))
            count = C.c_size_t.from_buffer(buf).value
            if count > 4096 or 16 + count * C.sizeof(HandleEntry) > len(buf):
                raise RuntimeError("handle snapshot bound")
            rows = (HandleEntry * count).from_buffer(buf, 16)
            jobs, process_handles = [], []
            for row in rows:
                try:
                    duplicate = win32api.DuplicateHandle(process, int(row.value), win32api.GetCurrentProcess(),
                                                        0, False, win32con.DUPLICATE_SAME_ACCESS)
                except (OSError, pywintypes.error):
                    continue  # The live owner may already have closed this sampled handle.
                try:
                    try:
                        account = win32job.QueryInformationJobObject(duplicate, win32job.JobObjectBasicAccountingInformation)
                    except (OSError, pywintypes.error):
                        pid = api.k.GetProcessId(int(duplicate))
                        if pid:
                            try:
                                process_handles.append(api.identity(duplicate))
                            except OSError as error:
                                wait = api.w.WaitForSingleObject(int(duplicate), 0)
                                process_handles.append({"pid": pid, "identity_error": str(error),
                                    "wait0": wait, "exit_code": api.w.GetExitCodeProcess(int(duplicate)) if wait == 0 else None})
                        continue
                    name = object_name(duplicate)
                    if not name or not any(token in name for token in ("XARG2OwnerJob-", "XAR-Native30-")):
                        continue
                    listing = C.create_string_buffer(8 + 1024 * C.sizeof(C.c_size_t))
                    if not api.k.QueryInformationJobObject(int(duplicate), 3, listing, len(listing), C.byref(needed)):
                        raise C.WinError(C.get_last_error())
                    assigned, listed = (C.c_uint32 * 2).from_buffer(listing)
                    if listed > 1024 or listed != assigned:
                        raise RuntimeError("owned Job member listing bound/incomplete")
                    pids = (C.c_size_t * listed).from_buffer(listing, 8)
                    members = []
                    for pid in pids:
                        try:
                            members.append(identity(pid))
                        except OSError as error:
                            members.append({"pid": pid, "read_error": str(error)})
                    jobs.append({"name": name, "accounting": account, "member_identities": members})
                finally:
                    duplicate.Close()
            result["owners"][label] = {"identity": actual, "snapshot_handles": count,
                "named_private_jobs": jobs, "retained_process_handles": process_handles}
        finally:
            process.Close()
    result["end_utc"] = datetime.now(timezone.utc).isoformat()
    body = json.dumps(result, indent=2).encode()
    if len(body) > 16384:
        raise RuntimeError("diagnostic output bound")
    owner.once(ROOT / "CONFIGURE-OWNED-DIAG01.json", result)
    print(body.decode())

if __name__ == "__main__":
    main()
