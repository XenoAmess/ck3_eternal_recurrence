#!/usr/bin/env python3
"""Read-only disassembly of exact CK3 1.19.0.6 active advantage helpers."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import struct

from capstone import Cs, CS_ARCH_X86, CS_MODE_64
import pefile


EXPECTED_EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
FUNCTIONS = {
    "resolve": (0x2308D50, 0x2308DE0),
    "side_total": (0x2307CB0, 0x2307F20),
    "commander": (0x2307680, 0x2307920),
    "side_modifier": (0x2307230, 0x23075B0),
    "main_tick": (0x2309E80, 0x230A010),
    "damage_advantage": (0x23053B0, 0x2305580),
    "side_primary_refresh": (0x23CBC20, 0x23CBCE0),
    "manager_refresh_pass_a": (0x27FB280, 0x27FB4C9),
    "phase_event_schedule_head": (0x27FB4D0, 0x27FB53B),
    "phase_event_schedule_loop": (0x27FB53B, 0x27FB5BA),
    "daily_dispatch": (0x27FB5D0, 0x27FB780),
    # Counter helper safety audit: the original side caller, damage wrapper,
    # class resolver, and per-entry current-chunk reader.
    "counter_side_caller": (0x23CB1D0, 0x23CB435),
    "counter_damage_wrapper": (0x23CAE70, 0x23CB1D0),
    "counter_class_resolver": (0x23CF1B0, 0x23CF96D),
    "counter_current_chunk": (0x23D2B90, 0x23D2CDE),
}


def disassemble(exe: Path, name: str, calls_to: list[int] | None = None) -> list[str]:
    data = exe.read_bytes()
    sha = hashlib.sha256(data).hexdigest().upper()
    if sha != EXPECTED_EXE_SHA256:
        raise ValueError(f"unexpected executable SHA-256: {sha}")
    image = pefile.PE(data=data, fast_load=True)
    if name == "callers":
        image.parse_data_directories(
            directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_EXCEPTION"]]
        )
        if not calls_to:
            raise ValueError("--calls-to required for callers")
        targets = set(calls_to)
        callers = []
        for section in image.sections:
            if not section.Characteristics & 0x20000000:
                continue
            section_rva = int(section.VirtualAddress)
            code = section.get_data()
            for i in range(len(code) - 4):
                if code[i] != 0xE8:
                    continue
                destination = section_rva + i + 5 + struct.unpack_from("<i", code, i + 1)[0]
                if destination in targets:
                    caller = section_rva + i
                    owner = next(
                        (
                            (int(row.struct.BeginAddress), int(row.struct.EndAddress))
                            for row in image.DIRECTORY_ENTRY_EXCEPTION
                            if int(row.struct.BeginAddress) <= caller < int(row.struct.EndAddress)
                        ),
                        None,
                    )
                    callers.append(f"{caller:08X} -> {destination:08X}; owner={owner}")
        return callers
    start, end = FUNCTIONS[name]
    code = image.get_data(start, end - start)
    if len(code) != end - start:
        raise ValueError("short executable read")
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    return [
        f"{instruction.address:08X}  {instruction.mnemonic:<8} {instruction.op_str}"
        for instruction in decoder.disasm(code, start)
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", required=True, type=Path)
    parser.add_argument("--function", required=True, choices=sorted(FUNCTIONS) + ["callers"])
    parser.add_argument("--calls-to", action="append", type=lambda value: int(value, 0))
    args = parser.parse_args()
    print("\n".join(disassemble(args.exe, args.function, args.calls_to)))


if __name__ == "__main__":
    main()
