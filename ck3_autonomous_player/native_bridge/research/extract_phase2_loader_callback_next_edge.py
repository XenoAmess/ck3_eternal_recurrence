#!/usr/bin/env python3
"""Extract the exact post-callback next-node edge from one pinned CK3 function.

This is deliberately narrower than a loader disassembler.  It verifies the
fixed vector setup, callback continuation, and final iterator edge in
``[0x3B9AB00, 0x3B9ACED)``.  It never starts or attaches to CK3.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
from typing import Any

import pefile


EXPECTED_SHA256 = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
EXPECTED_SIZE = 95_206_008
EXPECTED_IMAGE_BASE = 0x140000000

FUNCTION_RVA = 0x3B9AB00
FUNCTION_END_RVA = 0x3B9ACED
CALLBACK_CALL_RVA = 0x3B9AB90
CALLBACK_CONTINUATION_RVA = 0x3B9AB93
NODE_LOAD_RVA = 0x3B9AB50
NODE_LOADED_STOP_RVA = 0x3B9AB53
CALLBACK_GATE_BRANCH_RVA = 0x3B9AB5B
NEXT_ADVANCE_RVA = 0x3B9ACB7
NEXT_COMPARE_RVA = 0x3B9ACBB
NEXT_BRANCH_RVA = 0x3B9ACBE
LOOP_EXIT_RVA = 0x3B9ACC4

VECTOR_SETUP = bytes.fromhex(
    "48 8B 41 08 48 8B 58 70 48 63 40 7C 48 8D 3C C3 48 3B DF "
    "0F 84 88 01 00 00"
)
NODE_LOAD_AND_GATE = bytes.fromhex(
    "48 8B 33 48 83 BE 88 00 00 00 00 74 36"
)
POST_CALLBACK_WINDOW_SHA256 = (
    "D624CA70C1CAE6E3178AAB95D6369CFF96FD9CED8CD87B6BBEB2EB1CBA2B234D"
)
NEXT_EDGE = bytes.fromhex("48 83 C3 08 48 3B DF 0F 85 8C FE FF FF")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def bytes_at(data: bytes, image: pefile.PE, rva: int, size: int) -> bytes:
    try:
        offset = image.get_offset_from_rva(rva)
    except pefile.PEFormatError as exc:
        raise ValueError(f"RVA 0x{rva:X} is outside the image") from exc
    value = data[offset : offset + size]
    if len(value) != size:
        raise ValueError(f"short read at RVA 0x{rva:X}")
    return value


def verify_exact(
    data: bytes, image: pefile.PE, rva: int, expected: bytes, label: str
) -> str:
    actual = bytes_at(data, image, rva, len(expected))
    if actual != expected:
        raise ValueError(
            f"{label} changed at 0x{rva:X}: "
            f"{actual.hex().upper()} != {expected.hex().upper()}"
        )
    return actual.hex().upper()


def extract(exe: Path) -> dict[str, Any]:
    source = exe.resolve()
    data = source.read_bytes()
    digest = sha256(data)
    if len(data) != EXPECTED_SIZE or digest != EXPECTED_SHA256:
        raise ValueError(
            "source executable is not the pinned CK3 1.19.0.6 build: "
            f"size={len(data)} sha256={digest}"
        )

    image = pefile.PE(str(source), fast_load=True)
    if int(image.OPTIONAL_HEADER.ImageBase) != EXPECTED_IMAGE_BASE:
        raise ValueError("unexpected PE image base")

    vector_setup_hex = verify_exact(
        data, image, 0x3B9AB23, VECTOR_SETUP, "vector setup"
    )
    node_gate_hex = verify_exact(
        data, image, NODE_LOAD_RVA, NODE_LOAD_AND_GATE, "node load/gate"
    )
    next_edge_hex = verify_exact(
        data, image, NEXT_ADVANCE_RVA, NEXT_EDGE, "next-node edge"
    )

    callback_bytes = bytes_at(data, image, CALLBACK_CALL_RVA, 3)
    if callback_bytes != bytes.fromhex("FF 50 10"):
        raise ValueError("callback call changed")
    continuation_bytes = bytes_at(data, image, CALLBACK_CONTINUATION_RVA, 7)
    if continuation_bytes != bytes.fromhex("4C 8B 8E 98 00 00 00"):
        raise ValueError("callback continuation changed")

    post_window = bytes_at(
        data,
        image,
        CALLBACK_CONTINUATION_RVA,
        LOOP_EXIT_RVA - CALLBACK_CONTINUATION_RVA,
    )
    post_window_sha256 = sha256(post_window)
    if post_window_sha256 != POST_CALLBACK_WINDOW_SHA256:
        raise ValueError(
            "post-callback window changed: "
            f"{post_window_sha256} != {POST_CALLBACK_WINDOW_SHA256}"
        )

    branch = NEXT_EDGE[7:]
    displacement = struct.unpack("<i", branch[2:6])[0]
    branch_target = NEXT_BRANCH_RVA + len(branch) + displacement
    branch_fallthrough = NEXT_BRANCH_RVA + len(branch)
    if branch_target != NODE_LOAD_RVA or branch_fallthrough != LOOP_EXIT_RVA:
        raise ValueError("next-node branch targets changed")

    callback_skip = NODE_LOAD_AND_GATE[-2:]
    skip_displacement = struct.unpack("<b", callback_skip[1:2])[0]
    skip_target = CALLBACK_GATE_BRANCH_RVA + 2 + skip_displacement
    if skip_target != CALLBACK_CONTINUATION_RVA:
        raise ValueError("null callback gate target changed")

    return {
        "contract": "phase2-loader-callback-next-edge-extract-v1",
        "status": "static-stop-point-bound",
        "read_only": True,
        "production_installed": False,
        "production_abi_changed": False,
        "readiness_promotion": False,
        "source": {
            "path": str(source),
            "product_version": "1.19.0.6",
            "sha256": digest,
            "size_bytes": len(data),
            "image_base": f"0x{EXPECTED_IMAGE_BASE:X}",
        },
        "bounded_function": {
            "rva": f"0x{FUNCTION_RVA:X}",
            "end_rva_exclusive": f"0x{FUNCTION_END_RVA:X}",
            "vector_setup": {
                "rva": "0x3B9AB23",
                "end_rva_exclusive": "0x3B9AB3C",
                "bytes_hex": vector_setup_hex,
                "owner_load": "RAX=[RCX+0x08]",
                "begin_load": "RBX=[owner+0x70]",
                "signed_count_load": "RAX=sign_extend([owner+0x7C])",
                "end_compute": "RDI=RBX+count*8",
            },
            "callback": {
                "call_rva": f"0x{CALLBACK_CALL_RVA:X}",
                "continuation_rva": f"0x{CALLBACK_CONTINUATION_RVA:X}",
                "continuation_bytes_hex": continuation_bytes.hex().upper(),
                "return_value_consumed": False,
                "first_post_return_operation": "R9=[RSI+0x98]",
            },
            "post_callback_window": {
                "rva": f"0x{CALLBACK_CONTINUATION_RVA:X}",
                "end_rva_exclusive": f"0x{LOOP_EXIT_RVA:X}",
                "length_bytes": len(post_window),
                "bytes_sha256": post_window_sha256,
                "opaque_direct_call_rvas": [
                    "0x3B9AC2C",
                    "0x3B9AC45",
                    "0x3B9AC6E",
                    "0x3B9ACB2",
                ],
            },
            "next_node_edge": {
                "rva": f"0x{NEXT_ADVANCE_RVA:X}",
                "end_rva_exclusive": f"0x{LOOP_EXIT_RVA:X}",
                "bytes_hex": next_edge_hex,
                "bytes_sha256": sha256(NEXT_EDGE),
                "advance": "RBX=RBX+8",
                "compare": "RBX versus RDI",
                "next_exists_branch_rva": f"0x{NEXT_BRANCH_RVA:X}",
                "next_exists_target_rva": f"0x{branch_target:X}",
                "exhausted_fallthrough_rva": f"0x{branch_fallthrough:X}",
            },
            "node_entry": {
                "load_rva": f"0x{NODE_LOAD_RVA:X}",
                "loaded_stop_rva": f"0x{NODE_LOADED_STOP_RVA:X}",
                "bytes_hex": node_gate_hex,
                "state_at_stop": "RSI=[RBX] is the current node; [RSI+0x88] has not yet been gated",
                "callback_field_offset": "0x88",
                "null_callback_branch_rva": f"0x{CALLBACK_GATE_BRANCH_RVA:X}",
                "null_callback_target_rva": f"0x{skip_target:X}",
                "reached_for_every_nonempty_iteration": True,
            },
        },
        "observable_stop_point": {
            "rva": f"0x{NODE_LOADED_STOP_RVA:X}",
            "role": "next-node-loaded-before-callback-null-gate",
            "read_current_node_from": "RSI",
            "read_node_name_pointer_from": "[RSI+0x08]",
            "read_callback_receiver_from": "[RSI+0x88]",
            "why_it_closes_the_previous_gap": (
                "it is reached before the nullable callback gate, so it observes nodes "
                "that the callback-call breakpoint cannot see"
            ),
            "supporting_exit_discriminator_rva": f"0x{LOOP_EXIT_RVA:X}",
        },
        "wait_edge_boundary": {
            "status": "no-unique-wait-edge-in-bounded-function",
            "last_deterministic_advance_rva": f"0x{NEXT_ADVANCE_RVA:X}",
            "opaque_post_return_call_rvas": [
                "0x3B9AC2C",
                "0x3B9AC45",
                "0x3B9AC6E",
                "0x3B9ACB2",
            ],
            "claim": (
                "the iterator edge is exact; the opaque helpers are not assigned "
                "wait semantics without source symbols or runtime evidence"
            ),
        },
        "limits": [
            "the stop point identifies a node before its callback gate, not loader readiness",
            "the four post-return direct calls retain opaque business and wait semantics",
            "the loop exit does not identify which of eight external callers invoked this function",
            "no CK3 process was started and no public bridge or production loader changed",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = extract(args.exe)
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
