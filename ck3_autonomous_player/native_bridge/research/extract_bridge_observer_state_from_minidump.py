#!/usr/bin/env python3
"""Extract private bridge observer state from an MSVC MAP and minidump.

The bridge must be compiled with /Z7 and linked with /DEBUG:FULL plus /MAP so
that anonymous-namespace static symbols appear in the MAP's ``Static symbols``
section.  This tool is intentionally read-only and uses only the Python standard
library.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


MINIDUMP_SIGNATURE = b"MDMP"
MODULE_LIST_STREAM = 4
MEMORY_LIST_STREAM = 5
MEMORY64_LIST_STREAM = 9


def _u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def _u64(data: bytes, offset: int) -> int:
    return struct.unpack_from("<Q", data, offset)[0]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


@dataclass(frozen=True)
class Module:
    name: str
    base: int
    size: int


@dataclass(frozen=True)
class MemoryRange:
    address: int
    size: int
    file_offset: int


class Minidump:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.data = path.read_bytes()
        if len(self.data) < 32 or self.data[:4] != MINIDUMP_SIGNATURE:
            raise ValueError(f"not a minidump: {path}")
        stream_count = _u32(self.data, 8)
        directory_rva = _u32(self.data, 12)
        directories: dict[int, tuple[int, int]] = {}
        for index in range(stream_count):
            offset = directory_rva + index * 12
            stream_type, data_size, rva = struct.unpack_from(
                "<III", self.data, offset
            )
            directories[stream_type] = (rva, data_size)
        self.modules = self._parse_modules(directories.get(MODULE_LIST_STREAM))
        self.memory_ranges = self._parse_memory_ranges(directories)

    def _parse_modules(self, location: tuple[int, int] | None) -> list[Module]:
        if location is None:
            raise ValueError("minidump has no ModuleListStream")
        rva, _ = location
        count = _u32(self.data, rva)
        modules: list[Module] = []
        cursor = rva + 4
        for _ in range(count):
            base, size = struct.unpack_from("<QI", self.data, cursor)
            name_rva = _u32(self.data, cursor + 20)
            byte_length = _u32(self.data, name_rva)
            raw_name = self.data[name_rva + 4 : name_rva + 4 + byte_length]
            modules.append(Module(raw_name.decode("utf-16le"), base, size))
            cursor += 108
        return modules

    def _parse_memory_ranges(
        self, directories: dict[int, tuple[int, int]]
    ) -> list[MemoryRange]:
        ranges: list[MemoryRange] = []
        if MEMORY_LIST_STREAM in directories:
            rva, _ = directories[MEMORY_LIST_STREAM]
            count = _u32(self.data, rva)
            cursor = rva + 4
            for _ in range(count):
                address, size, file_rva = struct.unpack_from(
                    "<QII", self.data, cursor
                )
                ranges.append(MemoryRange(address, size, file_rva))
                cursor += 16
        if MEMORY64_LIST_STREAM in directories:
            rva, _ = directories[MEMORY64_LIST_STREAM]
            count, file_rva = struct.unpack_from("<QQ", self.data, rva)
            cursor = rva + 16
            for _ in range(count):
                address, size = struct.unpack_from("<QQ", self.data, cursor)
                ranges.append(MemoryRange(address, size, file_rva))
                file_rva += size
                cursor += 16
        if not ranges:
            raise ValueError("minidump has no supported memory stream")
        return sorted(ranges, key=lambda item: item.address)

    def module(self, basename: str) -> Module:
        wanted = basename.casefold()
        matches = [
            module
            for module in self.modules
            if Path(module.name).name.casefold() == wanted
        ]
        if len(matches) != 1:
            raise ValueError(
                f"expected one module named {basename!r}, found {len(matches)}"
            )
        return matches[0]

    def read(self, address: int, size: int) -> bytes:
        for memory_range in self.memory_ranges:
            relative = address - memory_range.address
            if 0 <= relative and relative + size <= memory_range.size:
                start = memory_range.file_offset + relative
                return self.data[start : start + size]
        raise ValueError(
            f"memory 0x{address:X}..0x{address + size:X} is absent from dump"
        )


@dataclass(frozen=True)
class MapSymbol:
    name: str
    image_address: int
    rva: int


def parse_linker_map(path: Path) -> tuple[int, list[MapSymbol]]:
    preferred_base: int | None = None
    symbols: list[MapSymbol] = []
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if line.startswith("Preferred load address is "):
            preferred_base = int(line.rsplit(" ", 1)[-1], 16)
            continue
        columns = line.split()
        if (
            len(columns) >= 3
            and ":" in columns[0]
            and len(columns[2]) == 16
            and all(character in "0123456789abcdefABCDEF" for character in columns[2])
        ):
            try:
                image_address = int(columns[2], 16)
            except ValueError:
                continue
            symbols.append(MapSymbol(columns[1], image_address, 0))
    if preferred_base is None:
        raise ValueError(f"MAP has no preferred load address: {path}")
    return preferred_base, [
        MapSymbol(symbol.name, symbol.image_address, symbol.image_address - preferred_base)
        for symbol in symbols
        if symbol.image_address >= preferred_base
    ]


def _string_observation(data: bytes, offset: int) -> dict[str, object]:
    word0 = _u64(data, offset + 0x20)
    word1 = _u64(data, offset + 0x28)
    preview = word0.to_bytes(8, "little") + word1.to_bytes(8, "little")
    return {
        "object": f"0x{_u64(data, offset):016X}",
        "effective_data": f"0x{_u64(data, offset + 8):016X}",
        "length": _u64(data, offset + 0x10),
        "capacity": _u64(data, offset + 0x18),
        "word0": f"0x{word0:016X}",
        "word1": f"0x{word1:016X}",
        "preview_hex": preview.hex().upper(),
        "preview_text": preview.rstrip(b"\0").decode("utf-8", errors="replace"),
        "null_result": bool(_u32(data, offset + 0x30)),
        "read_fault": bool(_u32(data, offset + 0x34)),
    }


def decode_cold_map(data: bytes) -> dict[str, object]:
    return {
        "installed": bool(_u32(data, 0)),
        "installed_mask": _u32(data, 4),
        "failure_flags": _u32(data, 8),
        "ctor": {
            "count": _u64(data, 0x10),
            "descriptor": f"0x{_u64(data, 0x18):016X}",
            "data": f"0x{_u64(data, 0x20):016X}",
            "length": _u32(data, 0x28),
            "flag": _u32(data, 0x2C),
            "word0": f"0x{_u64(data, 0x30):016X}",
            "word1": f"0x{_u64(data, 0x38):016X}",
        },
        "variant": {
            "count": _u64(data, 0x40),
            "address": f"0x{_u64(data, 0x48):016X}",
            "tag": _u32(data, 0x50),
            "payload": f"0x{_u64(data, 0x58):016X}",
            "length": _u32(data, 0x60),
            "capacity": _u32(data, 0x64),
            "word0": f"0x{_u64(data, 0x68):016X}",
            "word1": f"0x{_u64(data, 0x70):016X}",
        },
        "poll": {
            "count": _u64(data, 0x78),
            "object": f"0x{_u64(data, 0x80):016X}",
            "state": _u32(data, 0x88),
            "aux_state": _u32(data, 0x8C),
            "variant_tag": _u32(data, 0x90),
            "payload": f"0x{_u64(data, 0x98):016X}",
            "length": _u32(data, 0xA0),
            "capacity": _u32(data, 0xA4),
            "word0": f"0x{_u64(data, 0xA8):016X}",
            "word1": f"0x{_u64(data, 0xB0):016X}",
        },
        "module_base": f"0x{_u64(data, 0xB8):016X}",
        "variant_move_target": f"0x{_u64(data, 0xC0):016X}",
    }


def decode_named_path(data: bytes) -> dict[str, object]:
    slots: list[dict[str, object]] = []
    for index in range(16):
        offset = 0x50 + index * 0x138
        published = _u64(data, offset)
        pre_seen = _u32(data, offset + 0xC)
        post_seen = _u32(data, offset + 0x10)
        resolver_object = _u64(data, offset + 0x20)
        if not (published or pre_seen or post_seen or resolver_object):
            continue
        slots.append(
            {
                "index": index,
                "published_sequence": published,
                "thread_id": _u32(data, offset + 8),
                "move_pre_seen": bool(pre_seen),
                "move_post_seen": bool(post_seen),
                "move_result": f"0x{_u64(data, offset + 0x18):016X}",
                "resolver": _string_observation(data, offset + 0x20),
                "temporary_before": _string_observation(data, offset + 0x58),
                "root_before": _string_observation(data, offset + 0x90),
                "temporary_after": _string_observation(data, offset + 0xC8),
                "root_after": _string_observation(data, offset + 0x100),
            }
        )
    return {
        "installed": bool(_u32(data, 0)),
        "installed_mask": _u32(data, 4),
        "failure_flags": _u32(data, 8),
        "next_sequence": _u64(data, 0x10),
        "resolver_count": _u64(data, 0x18),
        "move_pre_count": _u64(data, 0x20),
        "move_post_count": _u64(data, 0x28),
        "correlation_miss_count": _u64(data, 0x30),
        "last_resolver_sequence": _u64(data, 0x38),
        "last_move_pre_sequence": _u64(data, 0x40),
        "last_move_post_sequence": _u64(data, 0x48),
        "slots": slots,
        "module_base": f"0x{_u64(data, 0x13D0):016X}",
    }


def _table_observation(data: bytes, offset: int) -> dict[str, object]:
    return {
        "map": f"0x{_u64(data, offset):016X}",
        "rows": f"0x{_u64(data, offset + 8):016X}",
        "count": _u64(data, offset + 0x10),
        "mask": _u32(data, offset + 0x18),
        "max_probe": _u32(data, offset + 0x1C),
        "id_583_present": bool(_u32(data, offset + 0x20)),
        "id_583_row": f"0x{_u64(data, offset + 0x28):016X}",
        "read_fault": bool(_u32(data, offset + 0x30)),
    }


def _lookup_observation(data: bytes, offset: int) -> dict[str, object]:
    return {
        "pre_count": _u64(data, offset),
        "return_count": _u64(data, offset + 8),
        "raw_result": f"0x{_u64(data, offset + 0x10):016X}",
        "null_result": bool(_u32(data, offset + 0x18)),
        "thread_id": _u32(data, offset + 0x1C),
        "sequence": _u64(data, offset + 0x20),
    }


def decode_pdx_paths(data: bytes) -> dict[str, object]:
    return {
        "installed": bool(_u32(data, 0)),
        "installed_mask": _u32(data, 4),
        "failure_flags": _u32(data, 8),
        "next_sequence": _u64(data, 0x10),
        "task_enter_count": _u64(data, 0x18),
        "task_thread_id": _u32(data, 0x20),
        "task_sequence": _u64(data, 0x28),
        "task_table": _table_observation(data, 0x30),
        "paths_lookup": _lookup_observation(data, 0x68),
        "checksummed_lookup": _lookup_observation(data, 0x90),
        "paths_parser_enter_count": _u64(data, 0xB8),
        "checksummed_parser_enter_count": _u64(data, 0xC0),
        "other_parser_enter_count": _u64(data, 0xC8),
        "parser_source": _u64(data, 0xD0),
        "parser_thread_id": _u32(data, 0xD8),
        "parser_sequence": _u64(data, 0xE0),
        "insert_call_count": _u64(data, 0xE8),
        "key_583_insert_pre_count": _u64(data, 0xF0),
        "key_583_insert_post_count": _u64(data, 0xF8),
        "key_read_fault_count": _u64(data, 0x100),
        "last_key": _u32(data, 0x108),
        "last_hash": f"0x{_u32(data, 0x10C):08X}",
        "insert_thread_id": _u32(data, 0x110),
        "insert_sequence": _u64(data, 0x118),
        "rhs_string": f"0x{_u64(data, 0x120):016X}",
        "result_pair": f"0x{_u64(data, 0x128):016X}",
        "native_result": f"0x{_u64(data, 0x130):016X}",
        "result_row": f"0x{_u64(data, 0x138):016X}",
        "result_inserted": bool(_u32(data, 0x140)),
        "result_pair_null": bool(_u32(data, 0x144)),
        "result_read_fault": bool(_u32(data, 0x148)),
        "table_before": _table_observation(data, 0x150),
        "table_after": _table_observation(data, 0x188),
        "module_base": f"0x{_u64(data, 0x1C0):016X}",
    }


def _vfs_manager_observation(data: bytes, offset: int) -> dict[str, object]:
    return {
        "manager": f"0x{_u64(data, offset):016X}",
        "head": f"0x{_u64(data, offset + 0x08):016X}",
        "ready_flag": _u32(data, offset + 0x10),
        "read_fault": bool(_u32(data, offset + 0x14)),
    }


def _vfs_path_observation(data: bytes, offset: int) -> dict[str, object]:
    preview_length = _u32(data, offset + 0x08)
    bounded_length = min(preview_length, 64)
    preview = data[offset + 0x18 : offset + 0x18 + 64]
    return {
        "pointer": f"0x{_u64(data, offset):016X}",
        "preview_length": preview_length,
        "terminated": bool(_u32(data, offset + 0x0C)),
        "null_pointer": bool(_u32(data, offset + 0x10)),
        "read_fault": bool(_u32(data, offset + 0x14)),
        "preview_hex": preview[:bounded_length].hex().upper(),
        "preview_text": preview[:bounded_length].decode("utf-8", errors="replace"),
    }


def _vfs_publisher_slot(
    data: bytes, offset: int, index: int
) -> dict[str, object]:
    return {
        "index": index,
        "published_ordinal": _u64(data, offset),
        "entry_sequence": _u64(data, offset + 0x08),
        "return_sequence": _u64(data, offset + 0x10),
        "entry_thread_id": _u32(data, offset + 0x18),
        "return_thread_id": _u32(data, offset + 0x1C),
        "return_seen": bool(_u32(data, offset + 0x20)),
        "raw_result": _u32(data, offset + 0x24),
        "raw_rcx": f"0x{_u64(data, offset + 0x28):016X}",
        "backend": f"0x{_u64(data, offset + 0x30):016X}",
        "insert_mode": _u32(data, offset + 0x38),
        "path": _vfs_path_observation(data, offset + 0x40),
        "manager_before": _vfs_manager_observation(data, offset + 0x98),
        "manager_after": _vfs_manager_observation(data, offset + 0xB0),
    }


def _vfs_lookup_observation(data: bytes, offset: int) -> dict[str, object]:
    return {
        "count": _u64(data, offset),
        "path_view": f"0x{_u64(data, offset + 0x08):016X}",
        "path_data": f"0x{_u64(data, offset + 0x10):016X}",
        "path_length": _u32(data, offset + 0x18),
        "path_flag": _u32(data, offset + 0x1C),
        "thread_id": _u32(data, offset + 0x20),
        "read_fault": bool(_u32(data, offset + 0x24)),
        "sequence": _u64(data, offset + 0x28),
        "manager": _vfs_manager_observation(data, offset + 0x30),
    }


def decode_vfs_mount_lifecycle(data: bytes) -> dict[str, object]:
    expected_size = 0x33F8
    if len(data) < expected_size:
        raise ValueError(
            f"VFS mount lifecycle state is 0x{len(data):X} bytes; "
            f"expected at least 0x{expected_size:X}"
        )
    publisher_slots: list[dict[str, object]] = []
    for index in range(64):
        offset = 0x88 + index * 0xC8
        published_ordinal = _u64(data, offset)
        entry_sequence = _u64(data, offset + 0x08)
        return_sequence = _u64(data, offset + 0x10)
        if not (published_ordinal or entry_sequence or return_sequence):
            continue
        publisher_slots.append(_vfs_publisher_slot(data, offset, index))

    hooks: list[dict[str, object]] = []
    for index in range(4):
        offset = 0x3350 + index * 0x20
        hooks.append(
            {
                "index": index,
                "patch_target": f"0x{_u64(data, offset):016X}",
                "patch_size": _u64(data, offset + 0x08),
                "original_hex": data[offset + 0x10 : offset + 0x18].hex().upper(),
                "installed_patch_hex": data[
                    offset + 0x18 : offset + 0x20
                ].hex().upper(),
            }
        )

    return {
        "installed": bool(_u32(data, 0)),
        "installed_mask": _u32(data, 4),
        "failure_flags": _u32(data, 8),
        "next_sequence": _u64(data, 0x10),
        "core_init": {
            "count": _u64(data, 0x18),
            "raw_al": _u32(data, 0x20),
            "thread_id": _u32(data, 0x24),
            "sequence": _u64(data, 0x28),
            "manager": _vfs_manager_observation(data, 0x30),
        },
        "publisher": {
            "entry_count": _u64(data, 0x48),
            "return_count": _u64(data, 0x50),
            "success_count": _u64(data, 0x58),
            "failure_count": _u64(data, 0x60),
            "correlation_miss_count": _u64(data, 0x68),
            "slot_overwrite_count": _u64(data, 0x70),
            "last_entry_sequence": _u64(data, 0x78),
            "last_return_sequence": _u64(data, 0x80),
            "slots": publisher_slots,
        },
        "paths_lookup": _vfs_lookup_observation(data, 0x3288),
        "checksummed_lookup": _vfs_lookup_observation(data, 0x32D0),
        "lookup_classification_fault_count": _u64(data, 0x3318),
        "module_base": f"0x{_u64(data, 0x3320):016X}",
        "core_init_target": f"0x{_u64(data, 0x3328):016X}",
        "publisher_entry_continue": f"0x{_u64(data, 0x3330):016X}",
        "publisher_return_continue": f"0x{_u64(data, 0x3338):016X}",
        "settings_lookup_continue": f"0x{_u64(data, 0x3340):016X}",
        "manager_address": f"0x{_u64(data, 0x3348):016X}",
        "hooks": hooks,
        "stub_allocation": f"0x{_u64(data, 0x33D0):016X}",
        "memory_context": f"0x{_u64(data, 0x33D8):016X}",
        "virtual_free": f"0x{_u64(data, 0x33E0):016X}",
        "virtual_protect": f"0x{_u64(data, 0x33E8):016X}",
        "flush_instruction_cache": f"0x{_u64(data, 0x33F0):016X}",
    }


ObserverDecoder = Callable[[bytes], dict[str, object]]


OBSERVERS: dict[str, tuple[str, int, ObserverDecoder]] = {
    "cold_map_vfs_observer_v1": (
        "g_cold_map_vfs_observer_v1",
        0x1A8,
        decode_cold_map,
    ),
    "named_path_583_root_observer_v1": (
        "g_named_path_583_root_observer_v1",
        0x1468,
        decode_named_path,
    ),
    "pdx_paths_583_producer_observer_v1": (
        "g_pdx_paths_583_producer_observer_v1",
        0x290,
        decode_pdx_paths,
    ),
    "vfs_mount_lifecycle_observer_v1": (
        "g_vfs_mount_lifecycle_observer_v1",
        0x33F8,
        decode_vfs_mount_lifecycle,
    ),
}


def _parse_rva_overrides(values: list[str]) -> dict[str, int]:
    result: dict[str, int] = {}
    for value in values:
        try:
            name, raw_rva = value.split("=", 1)
            result[name] = int(raw_rva, 0)
        except (ValueError, TypeError) as error:
            raise ValueError(f"invalid --symbol-rva {value!r}") from error
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dump", type=Path, required=True)
    parser.add_argument("--map", dest="map_path", type=Path)
    parser.add_argument("--module", default="xar_ck3_bridge.dll")
    parser.add_argument(
        "--observer", action="append", choices=sorted(OBSERVERS), required=True
    )
    parser.add_argument(
        "--symbol-rva",
        action="append",
        default=[],
        metavar="OBSERVER=RVA",
        help="explicit RVA for legacy dumps whose build omitted /Z7",
    )
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()

    overrides = _parse_rva_overrides(arguments.symbol_rva)
    preferred_base = None
    map_symbols: list[MapSymbol] = []
    if arguments.map_path is not None:
        preferred_base, map_symbols = parse_linker_map(arguments.map_path)
    dump = Minidump(arguments.dump)
    module = dump.module(arguments.module)

    extracted: dict[str, object] = {}
    for observer_name in arguments.observer:
        symbol_fragment, size, decoder = OBSERVERS[observer_name]
        if observer_name in overrides:
            rva = overrides[observer_name]
            rva_source = "explicit_legacy_override"
            map_symbol_name = None
        else:
            matches = [
                symbol for symbol in map_symbols if symbol_fragment in symbol.name
            ]
            if len(matches) != 1:
                raise ValueError(
                    f"expected one MAP symbol containing {symbol_fragment!r}, "
                    f"found {len(matches)}"
                )
            rva = matches[0].rva
            rva_source = "msvc_map_static_symbol"
            map_symbol_name = matches[0].name
        if rva < 0 or rva + size > module.size:
            raise ValueError(
                f"{observer_name} RVA 0x{rva:X} size 0x{size:X} is outside "
                f"module size 0x{module.size:X}"
            )
        address = module.base + rva
        raw_state = dump.read(address, size)
        extracted[observer_name] = {
            "provenance": "decoded_direct_minidump_bytes",
            "rva_source": rva_source,
            "map_symbol": map_symbol_name,
            "rva": f"0x{rva:X}",
            "runtime_address": f"0x{address:016X}",
            "size": size,
            "state_bytes_sha256": hashlib.sha256(raw_state).hexdigest().upper(),
            "decoded": decoder(raw_state),
        }

    report = {
        "schema": "xar.bridge_observer_minidump_extract.v1",
        "evidence_boundary": {
            "artifact_evidence": "module mapping, MAP RVA, raw bytes and decoded scalar fields",
            "inference": "none; behavioral interpretation is intentionally out of scope",
        },
        "dump": {
            "path": str(arguments.dump.resolve()),
            "sha256": _sha256(arguments.dump),
        },
        "map": None
        if arguments.map_path is None
        else {
            "path": str(arguments.map_path.resolve()),
            "sha256": _sha256(arguments.map_path),
            "preferred_load_address": f"0x{preferred_base:016X}",
        },
        "module": {
            "name": module.name,
            "runtime_base": f"0x{module.base:016X}",
            "size": module.size,
        },
        "observers": extracted,
    }
    serialized = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if arguments.output is None:
        print(serialized, end="")
    else:
        arguments.output.write_text(serialized, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
