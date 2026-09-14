#!/usr/bin/env python3
"""Read-only verifier for the frozen CK3 1.19.0.6 realm-law mutation ABI."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path
from typing import Any


class VerificationError(RuntimeError):
    pass


def parse_integer(value: Any) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value, 0)
    raise VerificationError(f"expected integer, got {value!r}")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as reader:
        for block in iter(lambda: reader.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


class PeImage:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.data = path.read_bytes()
        if len(self.data) < 0x100:
            raise VerificationError("file is too small to be a PE image")
        if self.data[:2] != b"MZ":
            raise VerificationError("DOS signature mismatch")
        pe_offset = self._u32(0x3C)
        if self._slice(pe_offset, 4) != b"PE\0\0":
            raise VerificationError("PE signature mismatch")
        coff = pe_offset + 4
        self.machine = self._u16(coff)
        section_count = self._u16(coff + 2)
        optional_size = self._u16(coff + 16)
        optional = coff + 20
        if self._u16(optional) != 0x20B:
            raise VerificationError("expected a PE32+ optional header")
        self.image_base = self._u64(optional + 24)
        self.image_size = self._u32(optional + 56)
        self.headers_size = self._u32(optional + 60)
        directory_count = self._u32(optional + 108)
        if directory_count <= 3:
            raise VerificationError("PE exception directory is absent")
        directories = optional + 112
        self.exception_rva = self._u32(directories + 3 * 8)
        self.exception_size = self._u32(directories + 3 * 8 + 4)
        section_table = optional + optional_size
        self.sections: list[tuple[int, int, int, int]] = []
        for index in range(section_count):
            entry = section_table + index * 40
            virtual_size = self._u32(entry + 8)
            virtual_address = self._u32(entry + 12)
            raw_size = self._u32(entry + 16)
            raw_pointer = self._u32(entry + 20)
            self.sections.append(
                (virtual_address, max(virtual_size, raw_size), raw_pointer, raw_size)
            )

    def _slice(self, offset: int, size: int) -> bytes:
        if offset < 0 or size < 0 or offset + size > len(self.data):
            raise VerificationError(
                f"file range out of bounds: offset={offset:#x} size={size:#x}"
            )
        return self.data[offset : offset + size]

    def _u16(self, offset: int) -> int:
        return struct.unpack_from("<H", self._slice(offset, 2))[0]

    def _u32(self, offset: int) -> int:
        return struct.unpack_from("<I", self._slice(offset, 4))[0]

    def _u64(self, offset: int) -> int:
        return struct.unpack_from("<Q", self._slice(offset, 8))[0]

    def read_rva(self, rva: int, size: int) -> bytes:
        if rva < 0 or size < 0 or rva + size > self.image_size:
            raise VerificationError(
                f"image range out of bounds: rva={rva:#x} size={size:#x}"
            )
        if rva < self.headers_size:
            return self._slice(rva, size)
        for virtual_address, mapped_size, raw_pointer, raw_size in self.sections:
            if virtual_address <= rva and rva + size <= virtual_address + mapped_size:
                relative = rva - virtual_address
                if relative + size > raw_size:
                    raise VerificationError(
                        f"RVA range has no complete on-disk backing: {rva:#x}+{size:#x}"
                    )
                return self._slice(raw_pointer + relative, size)
        raise VerificationError(f"RVA is not mapped by a PE section: {rva:#x}")

    def runtime_functions(self) -> set[tuple[int, int, int]]:
        if self.exception_size % 12 != 0:
            raise VerificationError("exception directory is not an array of RUNTIME_FUNCTION")
        data = self.read_rva(self.exception_rva, self.exception_size)
        return {
            struct.unpack_from("<III", data, offset)
            for offset in range(0, len(data), 12)
        }


def verify(executable: Path, manifest_path: Path) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("contract") != "realm_law_enact_mutation_v1_abi":
        raise VerificationError("manifest contract name mismatch")
    build = manifest["build"]
    actual_file_size = executable.stat().st_size
    expected_file_size = parse_integer(build["file_size"])
    if actual_file_size != expected_file_size:
        raise VerificationError(
            f"file size mismatch: {actual_file_size} != {expected_file_size}"
        )
    actual_file_hash = file_sha256(executable)
    expected_file_hash = str(build["sha256"]).upper()
    if actual_file_hash != expected_file_hash:
        raise VerificationError(
            f"executable SHA-256 mismatch: {actual_file_hash} != {expected_file_hash}"
        )

    image = PeImage(executable)
    if image.machine != parse_integer(build["machine"]):
        raise VerificationError(f"PE machine mismatch: {image.machine:#x}")
    if image.image_base != parse_integer(build["preferred_image_base"]):
        raise VerificationError(f"preferred image base mismatch: {image.image_base:#x}")
    if image.image_size != parse_integer(build["image_size"]):
        raise VerificationError(f"image size mismatch: {image.image_size:#x}")

    runtime_functions = image.runtime_functions()
    span_count = 0
    runtime_function_count = 0
    for span in manifest["instruction_spans"]:
        rva = parse_integer(span["rva"])
        end_rva = parse_integer(span["end_rva"])
        size = parse_integer(span["size"])
        if end_rva - rva != size:
            raise VerificationError(f"{span['name']}: inconsistent span size")
        actual_hash = hashlib.sha256(image.read_rva(rva, size)).hexdigest().upper()
        expected_hash = str(span["sha256"]).upper()
        if actual_hash != expected_hash:
            raise VerificationError(
                f"{span['name']}: span SHA-256 mismatch at {rva:#x}"
            )
        for runtime_function in span["runtime_functions"]:
            triple = tuple(parse_integer(item) for item in runtime_function)
            if len(triple) != 3 or triple not in runtime_functions:
                raise VerificationError(
                    f"{span['name']}: RUNTIME_FUNCTION entry mismatch: {triple!r}"
                )
            runtime_function_count += 1
        span_count += 1

    relative_edge_count = 0
    for edge in manifest["relative_edges"]:
        instruction_rva = parse_integer(edge["instruction_rva"])
        instruction_size = parse_integer(edge["instruction_size"])
        displacement_offset = parse_integer(edge["displacement_offset"])
        displacement_bytes = image.read_rva(
            instruction_rva + displacement_offset, 4
        )
        displacement = struct.unpack("<i", displacement_bytes)[0]
        actual_target = instruction_rva + instruction_size + displacement
        expected_target = parse_integer(edge["target_rva"])
        if actual_target != expected_target:
            raise VerificationError(
                f"{edge['name']}: relative target {actual_target:#x} != {expected_target:#x}"
            )
        relative_edge_count += 1

    absolute_pointer_count = 0
    for edge in manifest["absolute_pointer_edges"]:
        pointer_rva = parse_integer(edge["pointer_rva"])
        actual_pointer = struct.unpack("<Q", image.read_rva(pointer_rva, 8))[0]
        expected_pointer = image.image_base + parse_integer(edge["target_rva"])
        if actual_pointer != expected_pointer:
            raise VerificationError(
                f"{edge['name']}: pointer {actual_pointer:#x} != {expected_pointer:#x}"
            )
        absolute_pointer_count += 1

    ascii_count = 0
    for evidence in manifest["ascii_evidence"]:
        expected = str(evidence["value"]).encode("ascii") + b"\0"
        actual = image.read_rva(parse_integer(evidence["rva"]), len(expected))
        if actual != expected:
            raise VerificationError(f"{evidence['name']}: ASCII evidence mismatch")
        ascii_count += 1

    uint64_count = 0
    for evidence in manifest["uint64_evidence"]:
        actual = struct.unpack(
            "<Q", image.read_rva(parse_integer(evidence["rva"]), 8)
        )[0]
        expected = parse_integer(evidence["value"])
        if actual != expected:
            raise VerificationError(
                f"{evidence['name']}: uint64 value {actual:#x} != {expected:#x}"
            )
        uint64_count += 1

    return {
        "status": "GREEN",
        "contract": manifest["contract"],
        "game_version": build["game_version"],
        "executable_sha256": actual_file_hash,
        "instruction_spans_verified": span_count,
        "runtime_function_entries_verified": runtime_function_count,
        "relative_edges_verified": relative_edge_count,
        "absolute_pointer_edges_verified": absolute_pointer_count,
        "ascii_anchors_verified": ascii_count,
        "uint64_evidence_verified": uint64_count,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", required=True, type=Path)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path(__file__).with_name("realm_law_enact_mutation_v1_abi.json"),
    )
    arguments = parser.parse_args()
    try:
        result = verify(arguments.exe, arguments.manifest)
    except (OSError, KeyError, ValueError, json.JSONDecodeError, VerificationError) as error:
        print(json.dumps({"status": "RED", "reason": str(error)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
