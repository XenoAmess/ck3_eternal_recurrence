#!/usr/bin/env python3
"""Freeze the exact-build de-jure title-scope resolver's dynamic call boundary.

This reads the executable on disk. It never calls CK3 functions or effects.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

import pefile


EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
EXE_SIZE = 95_206_008
IMAGE_BASE = 0x140000000


def extract(exe: Path) -> dict[str, object]:
    data = exe.read_bytes()
    digest = hashlib.sha256(data).hexdigest().upper()
    if len(data) != EXE_SIZE or digest != EXE_SHA256:
        raise ValueError("CK3 executable differs from frozen 1.19.0.6 build")
    image = pefile.PE(data=data, fast_load=True)
    if image.OPTIONAL_HEADER.ImageBase != IMAGE_BASE:
        raise ValueError("unexpected image base")

    def at(rva: int, size: int) -> bytes:
        offset = image.get_offset_from_rva(rva)
        value = data[offset : offset + size]
        if len(value) != size:
            raise ValueError(f"short read at RVA 0x{rva:X}")
        return value

    def exact(rva: int, expected: str) -> dict[str, str]:
        frozen = bytes.fromhex(expected)
        if at(rva, len(frozen)) != frozen:
            raise ValueError(f"instruction bytes differ at RVA 0x{rva:X}")
        return {"rva": f"0x{rva:X}", "bytes": frozen.hex().upper()}

    def direct_call(rva: int, target: int) -> dict[str, str]:
        code = at(rva, 5)
        if code[0] != 0xE8 or rva + 5 + struct.unpack_from("<i", code, 1)[0] != target:
            raise ValueError(f"direct call differs at RVA 0x{rva:X}")
        return {"rva": f"0x{rva:X}", "target_rva": f"0x{target:X}", "bytes": code.hex().upper()}

    # Existing RTTI evidence identifies setup effect+0x260 as the embedded
    # CJominiScriptScopeObject<CLandedTitle>. This receipt follows its resolver.
    effect_title_scope_input = exact(0x2E9FB8A, "48 8D 8B 60 02 00 00")
    effect_title_scope_resolver = direct_call(0x2E9FB98, 0x995CB0)
    execute_title_scope_input = exact(0x2E9F5AF, "48 8D 8E 60 02 00 00")
    execute_title_scope_resolver = direct_call(0x2E9F5B6, 0x995CB0)
    resolver_scope_offset = exact(0x995CCC, "48 83 C1 10")
    resolver_dynamic_evaluation = direct_call(0x995CD0, 0x336AB40)
    resolver_title_tag = exact(0x995CD5, "66 83 7C 24 30 05")
    resolver_title_identity = exact(0x995D1E, "41 39 40 10")
    scope_slot_30 = exact(0x336AC47, "FF 50 30")
    scope_slot_20 = exact(0x336AC8B, "FF 50 20")
    setup_count_producer = direct_call(0x2E9F70B, 0x2E9FF30)
    setup_count_load = exact(0x2E9F710, "48 63 85 40 23 00 00")
    setup_count_fixed_scale = exact(0x2E9F717, "48 69 D0 A0 86 01 00")
    setup_factor_writer = direct_call(0x2E9F722, 0x2E9F2C0)
    factor_writer_delegate = direct_call(0x2E9F319, 0x33590D0)

    return {
        "schema": "xar.ck3.dejure-title-scope-resolution-gate.v2",
        "status": "STATIC_DYNAMIC_DISPATCH_BOUNDARY_ONLY",
        "exact_build": {"version": "1.19.0.6-steam23530548", "exe_sha256": digest},
        "effect_title_scope_input": effect_title_scope_input,
        "effect_title_scope_resolver": effect_title_scope_resolver,
        "execute_title_scope_input": execute_title_scope_input,
        "execute_title_scope_resolver": execute_title_scope_resolver,
        "resolver": {
            "rva": "0x995CB0",
            "embedded_scope_payload_offset": resolver_scope_offset,
            "dynamic_scope_evaluation": resolver_dynamic_evaluation,
            "expected_landed_title_result_tag_5": resolver_title_tag,
            "resolved_title_generation_identity_check": resolver_title_identity,
        },
        "dynamic_scope_evaluator": {
            "rva": "0x336AB40",
            "scope_node_virtual_slot_30": scope_slot_30,
            "scope_node_virtual_slot_20": scope_slot_20,
            "transitive_write_set_proven": False,
        },
        "setup_factor_input_path": {
            "helper_count_producer": setup_count_producer,
            "helper_output_count_load": setup_count_load,
            "multiply_by_fixed_scale_100000": setup_count_fixed_scale,
            "factor_writer": setup_factor_writer,
            "factor_writer_delegate": factor_writer_delegate,
            "helper_count_semantics_proven": False,
            "final_cb_prestige_factor_observed": False,
        },
        "boundary": {
            "ck3_launched": False,
            "effect_or_preview_called": False,
            "runtime_scope_target_referent_observed": False,
            "resolver_safe_as_standalone_live_query": False,
            "reason": "The title resolver calls a dynamic scope evaluator with two indirect virtual dispatches. The transitive write set and valid effect/context lifetime are not proven. A tag-5 result shape does not establish this War's runtime target referent. The setup factor path scales one helper output count by 100000 before a context-writer call, but the helper's count semantics and final stored factor are unproven.",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--exe",
        type=Path,
        default=Path("C:/SteamLibrary/steamapps/common/Crusader Kings III/binaries/ck3.exe"),
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    rendered = json.dumps(extract(args.exe), ensure_ascii=False, indent=2) + "\n"
    if args.output is None:
        print(rendered, end="")
    else:
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
