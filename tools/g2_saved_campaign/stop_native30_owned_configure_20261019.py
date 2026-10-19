"""Single admitted CTRL_C/failed-Job teardown of this exact Native30 attempt."""
import ctypes as C
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import sys
import time

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def main():
    d = load("native30_owned_diag", HERE / "diagnose_native30_owned_configure_20261019.py")
    owner = load("native30_stop_owner", d.SOURCE)
    spec = owner.checked_spec(d.ROOT / "SPEC.json", d.SPEC_SHA)
    api = owner.Windows()
    owner.require_caller(spec, api.current())
    import win32api, win32con, win32job, pywintypes
    diag = owner.read(d.ROOT / "CONFIGURE-OWNED-DIAG01.json")
    prior = diag["owners"]["bootstrap"]["named_private_jobs"][0]
    expected = {row["pid"]: row for row in prior["member_identities"]}
    start = owner.read(d.ROOT / "STARTED.json")
    result = {"machine_id": spec["machine_id"], "utc": owner.now(), "spec_sha256": d.SPEC_SHA,
              "signal_sent_once": False, "forced_outer_job": False}
    first = owner.read(d.ROOT / "CONFIGURE-STOP-RESULT01.json")
    if first.get("signal_sent_once") or first.get("forced_outer_job") or "bounded bootstrap handle snapshot failed" not in first.get("error", ""):
        raise RuntimeError("first preflight did more than fail its read permission")
    owner.once(d.ROOT / "CONFIGURE-STOP-CLAIM02.json", result)
    nt = C.WinDLL("ntdll")
    nt.NtQueryInformationProcess.argtypes = [C.c_void_p, C.c_uint32, C.c_void_p, C.c_uint32, C.POINTER(C.c_uint32)]
    nt.NtQueryInformationProcess.restype = C.c_long
    nt.NtQueryObject.argtypes = [C.c_void_p, C.c_uint32, C.c_void_p, C.c_uint32, C.POINTER(C.c_uint32)]
    nt.NtQueryObject.restype = C.c_long
    k = api.k
    k.QueryInformationJobObject.argtypes = [C.c_void_p, C.c_uint32, C.c_void_p, C.c_uint32, C.POINTER(C.c_uint32)]
    k.QueryInformationJobObject.restype = C.c_int
    k.FreeConsole.restype = C.c_int
    k.AttachConsole.argtypes, k.AttachConsole.restype = [C.c_uint32], C.c_int
    k.SetConsoleCtrlHandler.argtypes, k.SetConsoleCtrlHandler.restype = [C.c_void_p, C.c_int], C.c_int
    k.GetConsoleProcessList.argtypes, k.GetConsoleProcessList.restype = [C.POINTER(C.c_uint32), C.c_uint32], C.c_uint32
    k.GenerateConsoleCtrlEvent.argtypes, k.GenerateConsoleCtrlEvent.restype = [C.c_uint32, C.c_uint32], C.c_int
    handles = []
    outer = None
    def exact(pid, previous, handle_table=False):
        h = win32api.OpenProcess(0x100000 | 0x1000 | 0x400 | 0x40, False, pid) if handle_table else api.open(pid)
        handles.append(h)
        actual = api.identity(h)
        if any(actual.get(key) != previous.get(key) for key in ("pid", "creation_filetime", "image", "image_file_id", "session")) or actual["wait0"] != 258:
            raise RuntimeError("fresh exact live identity differs")
        return h, actual
    def members(job):
        buf, needed = C.create_string_buffer(8 + 64 * 8), C.c_uint32()
        if not k.QueryInformationJobObject(int(job), 3, buf, len(buf), C.byref(needed)):
            raise C.WinError(C.get_last_error())
        assigned, listed = (C.c_uint32 * 2).from_buffer(buf)
        if listed > 64 or listed != assigned:
            raise RuntimeError("owned Job list incomplete")
        rows = []
        for pid in (C.c_size_t * listed).from_buffer(buf, 8):
            if pid not in expected:
                raise RuntimeError("new/foreign owned Job member; no stop")
            _, row = exact(pid, expected[pid])
            rows.append(row)
        return rows
    try:
        bootstrap, _ = exact(start["bootstrap"]["pid"], start["bootstrap"], handle_table=True)
        stage, result["fresh_stage"] = exact(start["child"]["pid"], start["child"])
        buf, needed = C.create_string_buffer(262144), C.c_uint32()
        if nt.NtQueryInformationProcess(int(bootstrap), 51, buf, len(buf), C.byref(needed)) < 0:
            raise RuntimeError("bounded bootstrap handle snapshot failed")
        count = C.c_size_t.from_buffer(buf).value
        if count > 4096 or 16 + count * C.sizeof(d.HandleEntry) > len(buf):
            raise RuntimeError("bootstrap handle bound")
        for row in (d.HandleEntry * count).from_buffer(buf, 16):
            duplicate = None
            try:
                duplicate = win32api.DuplicateHandle(bootstrap, int(row.value), win32api.GetCurrentProcess(), 0, False, win32con.DUPLICATE_SAME_ACCESS)
                win32job.QueryInformationJobObject(duplicate, win32job.JobObjectBasicAccountingInformation)
                namebuf = C.create_string_buffer(16384)
                if nt.NtQueryObject(int(duplicate), 1, namebuf, len(namebuf), C.byref(needed)) >= 0:
                    name = d.Unicode.from_buffer(namebuf)
                    text = C.wstring_at(name.buffer, name.length // 2) if name.buffer else ""
                    if text == prior["name"]:
                        outer, duplicate = duplicate, None
                        break
            except (OSError, pywintypes.error):
                pass
            finally:
                if duplicate is not None: duplicate.Close()
        if outer is None: raise RuntimeError("exact retained outer Job not found")
        result["fresh_members_before"] = members(outer)
        try:
            k.FreeConsole()
            if not k.AttachConsole(start["child"]["pid"]): raise C.WinError(C.get_last_error())
            if not k.SetConsoleCtrlHandler(None, True): raise C.WinError(C.get_last_error())
            pids = (C.c_uint32 * 64)()
            count = k.GetConsoleProcessList(pids, 64)
            result["console_members"] = list(pids[:count]) if 0 < count <= 64 else None
            allowed = {row["pid"] for row in result["fresh_members_before"]}
            if not 0 < count <= 64 or not set(pids[:count]) <= allowed | {win32api.GetCurrentProcessId()} or start["child"]["pid"] not in pids[:count]:
                raise RuntimeError("console membership differs")
            if not k.GenerateConsoleCtrlEvent(0, 0): raise C.WinError(C.get_last_error())
            result["signal_sent_once"] = True
            result["stage_wait_after_signal"] = api.w.WaitForSingleObject(int(stage), 10000)
        except (OSError, RuntimeError) as error:
            result["console_error"] = str(error)
        finally:
            k.FreeConsole()
        native_result = Path("D:/codex-ck3-demos/2026-10-19-robert-v20261019-native30-camera01/evidence/RESULT.json")
        responded = False
        if native_result.is_file() and native_result.stat().st_size <= 16384:
            body = owner.read(native_result)
            responded = body.get("status") == "FAILED"
            result["original_failed_result_error"] = body.get("error")
        if api.w.WaitForSingleObject(int(stage), 0) != 0 and not responded:
            result["fresh_members_before_forced_stop"] = members(outer)
            win32job.TerminateJobObject(outer, 73)
            result["forced_outer_job"] = True
            api.w.WaitForSingleObject(int(stage), 10000)
        result["stage_wait_final"] = api.w.WaitForSingleObject(int(stage), 0)
        result["stage_exit_code"] = api.w.GetExitCodeProcess(int(stage)) if result["stage_wait_final"] == 0 else None
        deadline = time.monotonic() + 10
        while win32job.QueryInformationJobObject(outer, win32job.JobObjectBasicAccountingInformation)["ActiveProcesses"] and time.monotonic() < deadline:
            time.sleep(.05)
        result["outer_active_final"] = win32job.QueryInformationJobObject(outer, win32job.JobObjectBasicAccountingInformation)["ActiveProcesses"]
    except BaseException as error:
        result["error"] = repr(error)
    finally:
        if outer is not None: outer.Close()
        for h in handles: api.close(h)
        result["end_utc"] = owner.now()
        owner.once(d.ROOT / "CONFIGURE-STOP-RESULT02.json", result)
        print(json.dumps(result))

if __name__ == "__main__": main()
