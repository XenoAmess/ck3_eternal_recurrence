"""One deterministic compound for the actual inventory/rebind production path."""
from collections import Counter
import ctypes
import sys
from types import SimpleNamespace

import pytest

from xar_autoplayer import environment, ordinary_seed_rebinder, windows_process
from xar_autoplayer.errors import AgentError


class _Function:
    def __init__(self, callback):
        self.callback = callback

    def __call__(self, *args):
        return self.callback(*args)


def test_signaled_ck3_process_inventory_shared_production_paths(monkeypatch):
    # Image/time queries deliberately succeed even for the signaled object.
    # Its exit code is irrelevant: no GetExitCodeProcess API is supplied.
    states = {101: 0, 102: 0x102, 103: 0xFFFFFFFF, 104: None}
    entries = [{"pid": pid, "parent_pid": 4, "name": "ck3.exe"} for pid in states]
    opened, closed, image_queries = [], [], []

    def open_process(rights, inherit, pid):
        assert inherit is False
        assert rights in (0x00100000, 0x00001000)
        if rights == 0x00100000 and states[pid] is None:
            return 0  # Access denied: keep this PID blocking.
        handle = pid * 2 + (rights == 0x00001000)
        opened.append(handle)
        return handle

    def wait(handle, milliseconds):
        assert milliseconds == 0 and handle % 2 == 0
        return states[handle // 2]

    def image_name(handle, flags, buffer, length):
        assert flags == 0
        image_queries.append(handle // 2)
        buffer.value = r"C:\fixture\ck3.exe"
        length._obj.value = len(buffer.value)
        return True

    def process_times(handle, creation, exit_time, kernel_time, user_time):
        ticks = 116444736000000000 + 10000000
        creation._obj.dwHighDateTime = ticks >> 32
        creation._obj.dwLowDateTime = ticks & 0xFFFFFFFF
        return True

    def close(handle):
        closed.append(handle)
        return True

    kernel32 = SimpleNamespace(
        OpenProcess=_Function(open_process),
        WaitForSingleObject=_Function(wait),
        QueryFullProcessImageNameW=_Function(image_name),
        GetProcessTimes=_Function(process_times),
        CloseHandle=_Function(close),
    )
    monkeypatch.setattr(ctypes, "WinDLL", lambda *args, **kwargs: kernel32, raising=False)
    monkeypatch.setattr(windows_process, "os", SimpleNamespace(name="nt"))
    monkeypatch.setattr(environment, "os", SimpleNamespace(name="nt"))
    monkeypatch.setattr(environment, "_toolhelp_process_entries", lambda: list(entries))

    def tasklist(*args, **kwargs):
        assert args[0] == ["tasklist", "/FO", "CSV", "/NH"]
        rows = ['"System","4","Services","0","1 K"']
        rows.extend(f'"ck3.exe","{entry["pid"]}","Console","1","1 K"'
                    for entry in entries)
        return SimpleNamespace(returncode=0, stdout="\n".join(rows), stderr="")

    monkeypatch.setattr(environment.subprocess, "run", tasklist)

    def process_iter(attributes):
        assert attributes == ["pid", "name"]
        return [SimpleNamespace(info=dict(entry)) for entry in entries]

    monkeypatch.setitem(sys.modules, "psutil", SimpleNamespace(process_iter=process_iter))
    excluded = set()
    assert windows_process.active_process_pids("CK3.EXE", signaled_dead_pids=excluded) == [102, 103, 104]
    assert excluded == {101}
    inventory = environment.ck3_process_inventory()
    assert inventory["tasklist_pids"] == inventory["native_pids"] == [102, 103, 104]
    assert [item["pid"] for item in inventory["processes"]] == [102, 103, 104]
    assert 101 not in image_queries
    assert set(image_queries) == {102, 103, 104}
    with pytest.raises(AgentError, match="observed 3"):
        ordinary_seed_rebinder._zero_ck3_inventory()

    # With only a retained signaled object, the existing zero-process gate
    # succeeds and tasklist/native reconciliation excludes that same PID.
    entries[:] = [entries[0]]
    assert windows_process.active_process_pids("ck3.exe") == []
    zero = ordinary_seed_rebinder._zero_ck3_inventory()
    assert zero["tasklist_pids"] == zero["native_pids"] == zero["processes"] == []
    assert Counter(opened) == Counter(closed)
