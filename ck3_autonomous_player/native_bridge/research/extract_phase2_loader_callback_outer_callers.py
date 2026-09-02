#!/usr/bin/env python3
"""Verify the eight direct outer callers of the pinned loader callback loop.

The extractor is intentionally limited to the exact direct call instructions,
their immediate RCX setup and continuation, plus the callee's normal epilogue.
It never starts or attaches to CK3.
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
CALLEE_RVA = 0x3B9AB00
NORMAL_RETURN_RVA = 0x3B9ACE0
EPILOGUE_RVA = 0x3B9ACC4
EPILOGUE_BYTES = bytes.fromhex(
    "4C8D9C24F0020000498B5B28498B7330498B7B38498BE3415F415E5DC3"
)

CALLERS = (
    (0x0821E45, "E8B68C3703", 0x0821E40, "488D4C2430", 0x0821E4A,
     "488B0D97D7EE04", 0x0821A10, 0x0821F5C, 0x4C3F188),
    (0x088B5DC, "E81FF53003", 0x088B5D7, "488D4C2430", 0x088B5E1,
     "90", 0x088B480, 0x088B649, 0x4C42814),
    (0x1B3984D, "E8AE120602", 0x1B39848, "488D4C2420", 0x1B39852,
     "90", 0x1B397B0, 0x1B398D1, 0x4D057D8),
    (0x1E18C56, "E8A51ED801", 0x1E18C52, "488D4D90", 0x1E18C5B,
     "90", 0x1E18A10, 0x1E18CC9, 0x4D31F18),
    (0x1E21CD3, "E8288ED701", 0x1E21CCF, "488D4D80", 0x1E21CD8,
     "90", 0x1E219D0, 0x1E21D59, 0x4D32A7C),
    (0x203FF96, "E865ABB501", 0x203FF92, "488D4D10", 0x203FF9B,
     "EB0D", 0x203FE30, 0x20403FB, 0x4D562E8),
    (0x2041D8C, "E86F8DB501", 0x2041D87, "488D4C2420", 0x2041D91,
     "90", 0x2041C20, 0x2041E18, 0x4D564E8),
    (0x3B9AEF4, "E807FCFFFF", 0x3B9AEEF, "488D4C2420", 0x3B9AEF9,
     "90", 0x3B9ACF0, 0x3B9AF3D, 0x4F0FE60),
)


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


def direct_calls_to(image: pefile.PE, target_rva: int) -> list[int]:
    text = next(
        section
        for section in image.sections
        if section.Name.rstrip(b"\0") == b".text"
    )
    raw = text.get_data()
    base = int(text.VirtualAddress)
    hits: list[int] = []
    for offset in range(len(raw) - 4):
        if raw[offset] != 0xE8:
            continue
        displacement = struct.unpack_from("<i", raw, offset + 1)[0]
        if base + offset + 5 + displacement == target_rva:
            hits.append(base + offset)
    return hits


def extract(exe: Path) -> dict[str, Any]:
    source = exe.resolve()
    data = source.read_bytes()
    digest = sha256(data)
    if len(data) != EXPECTED_SIZE or digest != EXPECTED_SHA256:
        raise ValueError(
            "source executable is not the pinned CK3 1.19.0.6 build: "
            f"size={len(data)} sha256={digest}"
        )
    image = pefile.PE(str(source), fast_load=False)
    if int(image.OPTIONAL_HEADER.ImageBase) != EXPECTED_IMAGE_BASE:
        raise ValueError("unexpected PE image base")

    epilogue = bytes_at(data, image, EPILOGUE_RVA, len(EPILOGUE_BYTES))
    if epilogue != EPILOGUE_BYTES or epilogue[-1] != 0xC3:
        raise ValueError("normal return epilogue changed")

    expected_calls = [row[0] for row in CALLERS]
    actual_calls = direct_calls_to(image, CALLEE_RVA)
    if actual_calls != expected_calls:
        raise ValueError(f"direct caller set changed: {actual_calls!r}")

    pdata = {
        int(entry.struct.BeginAddress): (
            int(entry.struct.EndAddress), int(entry.struct.UnwindData)
        )
        for entry in image.DIRECTORY_ENTRY_EXCEPTION
    }
    records: list[dict[str, Any]] = []
    for (
        call_rva,
        call_hex,
        setup_rva,
        setup_hex,
        continuation_rva,
        continuation_hex,
        function_rva,
        function_end_rva,
        unwind_rva,
    ) in CALLERS:
        call = bytes.fromhex(call_hex)
        setup = bytes.fromhex(setup_hex)
        continuation = bytes.fromhex(continuation_hex)
        if bytes_at(data, image, call_rva, len(call)) != call:
            raise ValueError(f"call bytes changed at 0x{call_rva:X}")
        if bytes_at(data, image, setup_rva, len(setup)) != setup:
            raise ValueError(f"RCX setup changed at 0x{setup_rva:X}")
        if bytes_at(data, image, continuation_rva, len(continuation)) != continuation:
            raise ValueError(f"continuation changed at 0x{continuation_rva:X}")
        target = call_rva + 5 + struct.unpack("<i", call[1:])[0]
        if target != CALLEE_RVA or continuation_rva != call_rva + 5:
            raise ValueError(f"call edge changed at 0x{call_rva:X}")
        if pdata.get(function_rva) != (function_end_rva, unwind_rva):
            raise ValueError(f"PDATA owner changed at 0x{call_rva:X}")
        records.append(
            {
                "callsite_rva": f"0x{call_rva:X}",
                "call_bytes_hex": call_hex,
                "target_rva": f"0x{target:X}",
                "rcx_setup_rva": f"0x{setup_rva:X}",
                "rcx_setup_bytes_hex": setup_hex,
                "argument_shape": "address of caller-local 16-byte pair",
                "continuation_rva": f"0x{continuation_rva:X}",
                "continuation_bytes_hex": continuation_hex,
                "owner_function_rva": f"0x{function_rva:X}",
                "owner_function_end_rva_exclusive": f"0x{function_end_rva:X}",
                "owner_unwind_rva": f"0x{unwind_rva:X}",
                "runtime_node_identity_encoded": False,
            }
        )

    return {
        "contract": "phase2-loader-callback-outer-callers-extract-v1",
        "status": "static-caller-ambiguous-no-go",
        "read_only": True,
        "production_installed": False,
        "production_abi_changed": False,
        "readiness_promotion": False,
        "source": {
            "path": str(source),
            "product_version": "1.19.0.6",
            "sha256": digest,
            "size_bytes": len(data),
        },
        "callee": {
            "function_rva": f"0x{CALLEE_RVA:X}",
            "normal_return_rva": f"0x{NORMAL_RETURN_RVA:X}",
            "epilogue_rva": f"0x{EPILOGUE_RVA:X}",
            "epilogue_bytes_hex": epilogue.hex().upper(),
            "epilogue_bytes_sha256": sha256(epilogue),
            "return_address_at_normal_return": "[RSP]",
        },
        "direct_callers": {
            "count": len(records),
            "records": records,
            "unique_continuation_count": len(
                {record["continuation_rva"] for record in records}
            ),
        },
        "selection": {
            "target_runtime_sequence": 2,
            "target_node_name": "CJominiLoadScreenDatabase",
            "candidate_count_before": 8,
            "candidate_count_after": 8,
            "selected_continuation_rva": None,
            "result": "NO-GO",
            "reason": (
                "the direct call instructions and caller-local RCX setup encode no "
                "runtime node or concrete callback identity"
            ),
        },
        "next_observable_entry": {
            "rva": f"0x{NORMAL_RETURN_RVA:X}",
            "read": "[RSP] exact return address before RET",
            "mapping": "match against the eight verified continuation RVAs",
            "live_authorized": False,
        },
        "limits": [
            "the eight callsites belong to eight distinct PDATA functions",
            "no callsite continuation consumes a callee return value",
            "runtime vector contents are not encoded in the direct callsite",
            "no CK3 process was started and no public bridge or readiness changed",
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
