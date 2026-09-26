#!/usr/bin/env python3
"""Read-only, exact-build instruction gate for the day-05 physician scope path.

This proves only that the random-list hook can reach the inherited event-scope
pointer. It deliberately does not infer a physician identity, effective skill,
trait XP, or a before/after level-up state from that pointer.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_64, Cs
import pefile


EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"

# Exact CK3 1.19.0.6 bytes. The sequences are complete x64 instructions and
# carry the live register/stack relationship, not a guessed structure offset.
ANCHORS = {
    "event_scope_construct": (0x23C999A, "488d4c2440e8ec5745fe"),
    "event_scope_to_dispatch": (0x23C9B0C, "488d542440e8fa67fb00"),
    "dispatch_retains_scope": (0x3380322, "488bda488bf94c8bc1"),
    "dispatch_context_scope_slot": (0x3380357, "48895c2420"),
    "dispatch_context_call": (0x338038A, "488d542420488bcfe869060000"),
    "executor_parent_context": (0x3380A25, "4c8bf2488bf1"),
    "executor_child_scope_copy": (0x3380CCF, "498b0648894500"),
    "executor_child_rng_slot": (0x3380CE6, "488d858802000048894528"),
    "executor_effect_call": (0x3380CF1, "488b06488d5500488bceff90b0000000"),
    "random_list_passes_context": (0x2F08ACA, "4d8bc7488d5500e8aafcffff"),
    "picker_child_rng_slot": (0x2F087B1, "4c8b4f28"),
}


def verify(exe: Path) -> dict[str, object]:
    binary = exe.read_bytes()
    digest = hashlib.sha256(binary).hexdigest().upper()
    if digest != EXE_SHA256:
        raise ValueError(f"EXE SHA-256 mismatch: {digest}")
    image = pefile.PE(data=binary, fast_load=True)
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    rows: list[dict[str, object]] = []
    for name, (rva, expected_hex) in ANCHORS.items():
        expected = bytes.fromhex(expected_hex)
        offset = image.get_offset_from_rva(rva)
        actual = binary[offset : offset + len(expected)]
        if actual != expected:
            raise ValueError(f"{name} RVA {rva:#x}: instruction bytes mismatch")
        instructions = list(decoder.disasm(actual, image.OPTIONAL_HEADER.ImageBase + rva))
        if sum(len(row.bytes) for row in instructions) != len(expected):
            raise ValueError(f"{name} RVA {rva:#x}: incomplete instruction boundary")
        rows.append({"name": name, "rva": f"0x{rva:X}", "bytes": expected_hex.upper()})
    return {
        "status": "scope_pointer_path_static_only",
        "exe_sha256": digest,
        "anchors": rows,
        "physician_named_scope_identity_observed": False,
        "physician_effective_learning_observed": False,
        "physician_rankup_before_after_observed": False,
        "safe_to_enable_physician_field_hook": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.exe), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
