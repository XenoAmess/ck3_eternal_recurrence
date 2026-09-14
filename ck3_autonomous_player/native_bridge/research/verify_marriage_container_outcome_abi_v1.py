"""Verify M6 marriage exact-build spans without importing third-party modules."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
from pathlib import Path


HERE = Path(__file__).resolve().parent
CONTRACT = HERE / "fixtures" / "marriage_container_outcome_abi_v1_source_contract.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def parse_integer(value: object) -> int:
    if isinstance(value, int):
        return value
    require(isinstance(value, str), f"not an integer: {value!r}")
    return int(value, 0)


class PeImage:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.data = path.read_bytes()
        require(self.data[:2] == b"MZ", "missing MZ header")
        pe_offset = struct.unpack_from("<I", self.data, 0x3C)[0]
        require(self.data[pe_offset : pe_offset + 4] == b"PE\0\0", "missing PE header")
        section_count = struct.unpack_from("<H", self.data, pe_offset + 6)[0]
        optional_size = struct.unpack_from("<H", self.data, pe_offset + 20)[0]
        section_offset = pe_offset + 24 + optional_size
        self.sections: list[tuple[int, int, int, int]] = []
        for index in range(section_count):
            entry = section_offset + index * 40
            virtual_size, virtual_address, raw_size, raw_offset = struct.unpack_from(
                "<IIII", self.data, entry + 8
            )
            self.sections.append(
                (virtual_address, max(virtual_size, raw_size), raw_offset, raw_size)
            )

    def read_rva(self, rva: int, size: int) -> bytes:
        for virtual_address, span, raw_offset, raw_size in self.sections:
            if virtual_address <= rva and rva + size <= virtual_address + span:
                delta = rva - virtual_address
                require(delta + size <= raw_size, f"RVA 0x{rva:X} is not file-backed")
                return self.data[raw_offset + delta : raw_offset + delta + size]
        raise ValueError(f"RVA span 0x{rva:X}+0x{size:X} is outside sections")


def default_executable() -> Path:
    configured = os.environ.get("CK3_EXE")
    if configured:
        return Path(configured)
    return HERE.parents[3] / "Crusader Kings III" / "binaries" / "ck3.exe"


def verify(executable: Path) -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    image = PeImage(executable)
    expected = contract["exact_build"]
    require(len(image.data) == expected["executable_size"], "executable size drifted")
    require(
        hashlib.sha256(image.data).hexdigest().upper()
        == expected["executable_sha256"],
        "executable SHA-256 drifted",
    )
    for span in contract["native_spans"]:
        start = parse_integer(span["rva_start"])
        end = parse_integer(span["rva_end_exclusive"])
        require(end > start, f"{span['name']}: empty span")
        body = image.read_rva(start, end - start)
        actual = hashlib.sha256(body).hexdigest().upper()
        require(actual == span["sha256"], f"{span['name']}: SHA-256 drifted: {actual}")
    layout = contract["layout_assertions"]
    require(layout["ranked_header_size"] == 0x18, "ranked header layout drifted")
    require(layout["candidate_storage_size"] == 0x428, "candidate storage drifted")
    require(layout["scored_storage_size"] == 0x228, "scored storage drifted")
    require(layout["scored_row_stride"] == 0x10, "scored row drifted")
    require(layout["alliance_row_stride"] == 0x480, "alliance row drifted")
    require(layout["pending_object_size"] == 0x5C8, "pending object drifted")
    require(layout["pending_context_offset"] == 0x18, "pending context drifted")
    require(layout["pending_role_offsets"] == [0x2F0, 0x2F4, 0x2F8, 0x2FC, 0x300], "pending roles drifted")
    mode = "normal" if __debug__ else "optimized"
    print(f"marriage container/outcome ABI v1 {mode} GREEN spans={len(contract['native_spans'])}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", type=Path, default=default_executable())
    args = parser.parse_args()
    verify(args.exe.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
