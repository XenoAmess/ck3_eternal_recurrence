#!/usr/bin/env python3
"""Run the hardware-breakpoint sampler against a disposable Python child.

This never starts or attaches to CK3. It retains every attempt artifact.
"""

from __future__ import annotations

import argparse
import ctypes
import json
import os
from pathlib import Path
import subprocess
import sys
import time


PAGE_READWRITE = 0x04
PAGE_EXECUTE_READ = 0x20
MEM_COMMIT = 0x1000
MEM_RESERVE = 0x2000


def child(metadata: Path, trigger: Path) -> int:
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.VirtualAlloc.argtypes = [ctypes.c_void_p, ctypes.c_size_t,
                                    ctypes.c_ulong, ctypes.c_ulong]
    kernel.VirtualAlloc.restype = ctypes.c_void_p
    kernel.VirtualProtect.argtypes = [ctypes.c_void_p, ctypes.c_size_t,
                                      ctypes.c_ulong, ctypes.POINTER(ctypes.c_ulong)]
    kernel.VirtualProtect.restype = ctypes.c_int
    # push rsi; mov rax,rcx; mov rsi,rax; pop rsi; ret
    first = bytes.fromhex("56 48 8B C1 48 8B F0 5E C3")
    # mov rax,rcx; cmp dword ptr [rax+0x268],0x17; ret
    second = bytes.fromhex("48 8B C1 83 B8 68 02 00 00 17 C3")
    block = kernel.VirtualAlloc(None, 4096, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE)
    if not block:
        raise RuntimeError(f"VirtualAlloc failed: {ctypes.get_last_error()}")
    ctypes.memmove(block, first, len(first))
    ctypes.memmove(block + 32, second, len(second))
    old = ctypes.c_ulong()
    if not kernel.VirtualProtect(block, 4096, PAGE_EXECUTE_READ, ctypes.byref(old)):
        raise RuntimeError(f"VirtualProtect failed: {ctypes.get_last_error()}")
    change = ctypes.create_string_buffer(0x300)
    ctypes.c_uint32.from_buffer(change, 0x268).value = 0x17
    metadata.write_text(json.dumps({"pid": os.getpid(),
                                    "site0": hex(block + 4),
                                    "site1": hex(block + 35),
                                    "change_pointer": hex(ctypes.addressof(change))}) + "\n",
                        encoding="utf-8")
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline and not trigger.exists():
        time.sleep(0.02)
    if not trigger.exists():
        raise RuntimeError("fixture trigger timeout")
    function = ctypes.CFUNCTYPE(None, ctypes.c_void_p)
    function(block)(ctypes.addressof(change))
    function(block + 32)(ctypes.addressof(change))
    return 0


def wait_for(path: Path, process: subprocess.Popen[bytes], seconds: float) -> None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if path.exists():
            return
        if process.poll() is not None:
            raise RuntimeError(f"process exited before {path.name}: {process.returncode}")
        time.sleep(0.02)
    raise RuntimeError(f"timeout waiting for {path.name}")


def run(probe: Path, attempt: Path, expect_timeout: bool = False) -> int:
    if attempt.exists():
        raise ValueError("fixture attempt directory already exists")
    attempt.mkdir(parents=True)
    meta, trigger = attempt / "fixture-meta.json", attempt / "trigger"
    raw, ready = attempt / "raw.ndjson", attempt / "probe-ready.json"
    with (attempt / "fixture-stdout.txt").open("wb") as stdout, \
         (attempt / "fixture-stderr.txt").open("wb") as stderr:
        fixture = subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()), "--child",
             "--metadata", str(meta), "--trigger", str(trigger)],
            stdout=stdout, stderr=stderr,
        )
        try:
            wait_for(meta, fixture, 10)
            identity = json.loads(meta.read_text(encoding="utf-8"))
            command = [str(probe), "--fixture-pid", str(identity["pid"]),
                       "--site0", identity["site0"], "--site1", identity["site1"],
                       "--timeout-ms", "1500" if expect_timeout else "15000",
                       "--raw", str(raw),
                       "--ready", str(ready)]
            with (attempt / "probe-stdout.txt").open("wb") as probe_out, \
                 (attempt / "probe-stderr.txt").open("wb") as probe_err:
                sampler = subprocess.Popen(command, stdout=probe_out, stderr=probe_err)
                try:
                    wait_for(ready, sampler, 10)
                    if not expect_timeout:
                        trigger.write_text("run\n", encoding="utf-8")
                    sampler_result = sampler.wait(timeout=20)
                except BaseException:
                    trigger.write_text("run\n", encoding="utf-8")
                    try:
                        sampler.wait(timeout=20)
                    except subprocess.TimeoutExpired:
                        sampler.terminate()
                        sampler.wait(timeout=5)
                    raise
            if expect_timeout:
                trigger.write_text("run\n", encoding="utf-8")
            fixture_result = fixture.wait(timeout=10)
            events = [json.loads(line) for line in raw.read_text(encoding="utf-8").splitlines()]
            hits = [event for event in events if event.get("kind") == "sample"]
            final = events[-1]
            cleanup_ok = final.get("debug_registers_cleared") is True and final.get("detached") is True
            if expect_timeout:
                ok = (sampler_result == 1 and fixture_result == 0 and not hits
                      and final.get("status") == "red"
                      and final.get("reason") == "timeout_before_unique_pair"
                      and cleanup_ok)
            else:
                ok = (sampler_result == 0 and fixture_result == 0 and len(hits) == 2
                      and final.get("status") == "paired" and cleanup_ok
                      and [hit["site_rva"] for hit in hits] == ["0x2E9F746", "0x2EC4410"]
                      and all(hit["change_type_dword"] == 0x17 for hit in hits)
                      and all(hit["rax_change_pointer"] == identity["change_pointer"].upper().replace("0X", "0x") for hit in hits))
            report = {"schema": "xar.ck3.war31.hwprobe_fixture_test.v1",
                      "status": "green" if ok else "red", "ck3_launched": False,
                      "fixture_exit": fixture_result, "sampler_exit": sampler_result,
                      "expect_timeout": expect_timeout,
                      "raw": str(raw), "ready": str(ready), "events": events}
            (attempt / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
            print(json.dumps({"status": report["status"], "report": str(attempt / "report.json")}))
            return 0 if ok else 1
        finally:
            if fixture.poll() is None:
                trigger.write_text("run\n", encoding="utf-8")
                try:
                    fixture.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    fixture.terminate()
                    fixture.wait(timeout=5)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--metadata", type=Path)
    parser.add_argument("--trigger", type=Path)
    parser.add_argument("--probe", type=Path)
    parser.add_argument("--attempt", type=Path)
    parser.add_argument("--expect-timeout", action="store_true")
    args = parser.parse_args()
    if args.child:
        if args.metadata is None or args.trigger is None:
            parser.error("child requires metadata and trigger")
        return child(args.metadata, args.trigger)
    if args.probe is None or args.attempt is None:
        parser.error("probe and attempt are required")
    return run(args.probe, args.attempt, args.expect_timeout)


if __name__ == "__main__":
    raise SystemExit(main())
