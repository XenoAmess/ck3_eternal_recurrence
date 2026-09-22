#!/usr/bin/env python3
"""Pin the exact-build R0118 surrender title visitor and resolve queue boundary.

Reads ck3.exe bytes only. Does not run CK3 or call any native function.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import struct

import pefile

from extract_defender_surrender_title_preview_abi import extract as extract_preview


IMAGE_BASE = 0x140000000


def extract(exe: Path) -> dict[str, object]:
    preview = extract_preview(exe)
    data = exe.read_bytes()
    image = pefile.PE(data=data, fast_load=True)

    def at(rva: int, expected_hex: str) -> str:
        expected = bytes.fromhex(expected_hex)
        offset = image.get_offset_from_rva(rva)
        actual = data[offset : offset + len(expected)]
        if actual != expected:
            raise ValueError(f"exact-build instruction mismatch at RVA 0x{rva:X}")
        return actual.hex().upper()

    def call(source: int, target: int) -> str:
        offset = image.get_offset_from_rva(source)
        opcode = data[offset : offset + 5]
        if len(opcode) != 5 or opcode[0] != 0xE8:
            raise ValueError(f"expected direct call at RVA 0x{source:X}")
        destination = source + 5 + struct.unpack_from("<i", opcode, 1)[0]
        if destination != target:
            raise ValueError(f"call target mismatch at RVA 0x{source:X}")
        return opcode.hex().upper()

    ui_call = call(0xF5C0FC, 0x2F0E2D0)
    ui_output = at(0xF5C0E9, "488D93701C0000")
    ui_cleanup_start = at(0xF5C102, "488B552F4885D2")
    ui_cleanup_end = at(0xF5C19A, "488B4DDF488B01")
    callback_title_insert = at(0x2F0DE69, "8B4308488D4F18")
    callback_tag = at(0x2F0DE4F, "81790868300000")
    ui_vector_copies = {
        "+0x18 -> UI+0x30": call(0x2F0E303, 0xBDBC10),
        "+0x30 -> UI+0x48": call(0x2F0E310, 0xBDBC10),
        "+0x48 -> UI+0x60": call(0x2F0E31D, 0xBDBC10),
    }

    queue_context = at(0x2EC4496, "488B88A0000000")
    queue_offset = at(0x2EC449D, "4881C180D20000")
    queue_append_direct = call(0x2EC44A7, 0x27CD6A0)
    queue_append_other = call(0x2EC4567, 0x27CD510)
    queue_remove_count = at(0x27CD701, "FF4B3C")
    queue_write = at(0x27CD75A, "48893CC8")
    queue_append_count = at(0x27CD7BE, "FF4354")
    preview_noop = at(0x7E9220, "B001C3")

    return {
        "schema": "xar.ck3.defender-surrender-actual-move-boundary.v1",
        "status": "NO_NONMUTATING_ACTUAL_MOVE_PRODUCER_PROVEN",
        "exact_build": preview["exact_build"],
        "absolute_outcome": "attacker_victory for played primary-defender surrender",
        "ui_title_visitor": {
            "source": "CB+0x968 -> WarOverview 0xF5BFD0",
            "preview_dispatch": "0xF5C09F -> 0x3380170",
            "visitor_callback": "0x2F0DE20",
            "one_typed_tag_compare_rva": "0x2F0DE4F",
            "one_typed_tag_compare_bytes": callback_tag,
            "one_title_id_insert_rva": "0x2F0DE69",
            "one_title_id_insert_bytes": callback_title_insert,
            "ui_consumer_call_rva": "0xF5C0FC",
            "ui_consumer_call_bytes": ui_call,
            "ui_output_rva": "0xF5C0E9",
            "ui_output_bytes": ui_output,
            "ui_output_offset": "WarOverview+0x1C70",
            "vector_copy_call_bytes": ui_vector_copies,
            "cleanup_first_rva": "0xF5C102",
            "cleanup_first_bytes": ui_cleanup_start,
            "cleanup_last_rva": "0xF5C19A",
            "cleanup_last_bytes": ui_cleanup_end,
            "scope": "temporary visitor vectors feed WarOverview presentation lists; five owned buffers are conditionally released before helper returns",
            "unknown": "callback tag to material title/liege result and equivalence to final actual moves",
        },
        "resolve_execute_queue": {
            "effect_execute_rva": "0x2EC43F0",
            "resolved_context_type_0x17": "0x2EC44A7 -> 0x27CD6A0",
            "resolved_context_other": "0x2EC4567 -> 0x27CD510 -> 0x27CD6A0",
            "global_context_rva": "0x2EC4496",
            "global_context_bytes": queue_context,
            "queue_offset_rva": "0x2EC449D",
            "queue_offset_bytes": queue_offset,
            "queue_append_direct_call_bytes": queue_append_direct,
            "queue_append_other_call_bytes": queue_append_other,
            "queue_mutations": {
                "remove_count_0x27CD701": queue_remove_count,
                "write_entry_0x27CD75A": queue_write,
                "append_count_0x27CD7BE": queue_append_count,
            },
            "boundary": "the effect execute path mutates a global change queue and is not a read-only terms query",
            "unknown": "downstream final operation materialization/serialization and old/new title holder or liege values",
        },
        "resolve_preview": {
            "rva": "0x7E9220",
            "bytes": preview_noop,
            "boundary": "returns true without visiting resolved title or vassal operations",
        },
        "readiness": {
            "private_live_observer": False,
            "final_title_holder_liege_moves": False,
            "material_resource_deltas": False,
            "automatic_defender_surrender": False,
        },
        "execution": {
            "ck3_launched": False,
            "native_effect_called": False,
            "gameplay_action_submitted": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = json.dumps(extract(args.exe), ensure_ascii=False, indent=2) + "\n"
    if args.output is None:
        print(result, end="")
    else:
        args.output.write_bytes(result.encode("utf-8"))
        print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
