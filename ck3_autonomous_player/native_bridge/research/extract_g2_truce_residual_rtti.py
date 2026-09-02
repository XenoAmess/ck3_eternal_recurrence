#!/usr/bin/env python3
"""Resolve the final G2 residual vtables and correlate the frozen script tree.

This is a read-only exact-build extractor.  It validates MSVC RTTI and the
container-walk instructions for the two residual live vtables, then parses the
frozen stock scripts to recover the ordered top-level on_defeat/scripted-effect
structure.  It never starts CK3 or accesses a live process.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import struct
from typing import Any

import pefile


EXPECTED_EXE_SHA256 = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
EXPECTED_EXE_SIZE = 95_206_008
EXPECTED_IMAGE_BASE = 0x140000000


@dataclass(frozen=True)
class ResidualContract:
    vtable_rva: int
    col_rva: int
    type_descriptor_rva: int
    class_hierarchy_rva: int
    type_name: str
    base_names: tuple[str, ...]
    deleting_destructor_rva: int
    delete_size_instruction_rva: int
    object_size: int
    common_walk_rva: int
    common_walk_anchor: bytes
    live_position: str
    scope_walk_rva: int | None = None
    scope_walk_anchor: bytes = b""


RESIDUALS = (
    ResidualContract(
        0x44D1D50,
        0x4B4FC98,
        0x5655F78,
        0x4B4F590,
        ".?AVCShowAsTooltipEffect@@",
        (".?AVCShowAsTooltipEffect@@", ".?AVCJominiEffect@@"),
        0x2E77F30,
        0x2E77F49,
        0x60,
        0x3380980,
        bytes.fromhex(
            "48895C240848896C2410488974241848897C242041564883EC20"
            "488B5940498BF14863414C418BE84C8BF2488D3CC3"
        ),
        "index10.default.child0.context.child3.common.child0",
    ),
    ResidualContract(
        0x44D27B8,
        0x4B50238,
        0x5655EF8,
        0x4B4F548,
        ".?AVCJominiContextEffect@@",
        (".?AVCJominiContextEffect@@", ".?AVCJominiEffect@@"),
        0x33894C0,
        0x33894D9,
        0x100,
        0x3389790,
        bytes.fromhex(
            "48896C2410488974241848897C242041564883EC70458BF0488BF2"
            "4C8BC2498BE9488D542420488BF9"
        ),
        "index10.default.child0.context.child5.common.child1",
        0x3389610,
        bytes.fromhex(
            "40534883EC2083796C00488BDA750F0F57C0488BC20F11024883C4205BC3"
            "488B4160488B08488B01FF5030"
        ),
    ),
)

SOURCE_CONTRACTS = {
    "common/casus_belli_types/00_event_war.txt":
        "BD202AE41EBA3A0E1E7E4277D09ED1E8D8C7E66B378308BB417D974331F9C707",
    "common/scripted_effects/00_war_effects.txt":
        "A936E09F448EF715580A918165EAB89A9368AD2D3014E425C998CD9D4F0E8D7D",
    "common/scripted_effects/07_dlc_ep3_scripted_effects.txt":
        "D2F5FE80E7BC000A749642CD26BDE1626DBEA7409C39314B8583547AE43DB43D",
    "common/scripted_effects/tgp_mandala_scripted_effects.txt":
        "10B2C2C0E317D66F13237069064BC98267EBC7D75928F1AAD4E15397D2383A1B",
}

EXPECTED_ON_DEFEAT_KEYS = (
    "scope:attacker",
    "scope:defender",
    "every_in_list",
    "if",
    "scope:attacker",
    "setup_claim_cb",
    "modify_all_participants_fame_values",
    "add_truce_attacker_defeat_effect",
    "scope:attacker",
    "on_lost_aggression_war_discontent_loss",
    "laamp_as_mercenary_payout_tooltip_effect",
    "mandala_war_defeat_effects",
)

EXPECTED_SCRIPTED_SHAPES = {
    "add_truce_attacker_defeat_effect": (
        "scope:attacker",
        "hidden_effect",
        "scope:defender",
        "bp2_hostage_war_end_tooltip_effect",
    ),
    "on_lost_aggression_war_discontent_loss": ("scope:loser",),
    "laamp_as_mercenary_payout_tooltip_effect": ("show_as_tooltip",),
    "mandala_war_defeat_effects": ("scope:attacker", "scope:defender"),
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def bytes_at(data: bytes, image: pefile.PE, rva: int, size: int) -> bytes:
    offset = image.get_offset_from_rva(rva)
    value = data[offset : offset + size]
    if len(value) != size:
        raise ValueError(f"short read at RVA 0x{rva:X}")
    return value


def u32(data: bytes, image: pefile.PE, rva: int) -> int:
    return struct.unpack("<I", bytes_at(data, image, rva, 4))[0]


def u64(data: bytes, image: pefile.PE, rva: int) -> int:
    return struct.unpack("<Q", bytes_at(data, image, rva, 8))[0]


def rtti_name(data: bytes, image: pefile.PE, type_rva: int) -> str:
    start = image.get_offset_from_rva(type_rva) + 16
    end = data.find(b"\0", start, start + 1024)
    if end < 0:
        raise ValueError(f"unterminated RTTI name at RVA 0x{type_rva:X}")
    return data[start:end].decode("ascii")


def extract_residual(
    data: bytes, image: pefile.PE, contract: ResidualContract
) -> dict[str, Any]:
    col_rva = u64(data, image, contract.vtable_rva - 8) - EXPECTED_IMAGE_BASE
    if col_rva != contract.col_rva:
        raise ValueError(f"COL changed for 0x{contract.vtable_rva:X}")
    signature, offset, cd_offset, type_rva, hierarchy_rva, self_rva = struct.unpack(
        "<6I", bytes_at(data, image, col_rva, 24)
    )
    if (signature, offset, cd_offset, self_rva) != (1, 0, 0, col_rva):
        raise ValueError(f"invalid primary x64 COL for 0x{contract.vtable_rva:X}")
    if (type_rva, hierarchy_rva) != (
        contract.type_descriptor_rva,
        contract.class_hierarchy_rva,
    ):
        raise ValueError(f"RTTI pointers changed for 0x{contract.vtable_rva:X}")
    if rtti_name(data, image, type_rva) != contract.type_name:
        raise ValueError(f"RTTI name changed for 0x{contract.vtable_rva:X}")

    hierarchy = struct.unpack("<4I", bytes_at(data, image, hierarchy_rva, 16))
    base_count, base_array_rva = hierarchy[2], hierarchy[3]
    base_names = tuple(
        rtti_name(data, image, u32(data, image, u32(data, image, base_array_rva + i * 4)))
        for i in range(base_count)
    )
    if base_names != contract.base_names:
        raise ValueError(f"base hierarchy changed for 0x{contract.vtable_rva:X}")

    slots = [
        u64(data, image, contract.vtable_rva + i * 8) - EXPECTED_IMAGE_BASE
        for i in range(16)
    ]
    if slots[0] != contract.deleting_destructor_rva:
        raise ValueError(f"destructor changed for 0x{contract.vtable_rva:X}")
    delete_size = bytes_at(data, image, contract.delete_size_instruction_rva, 5)
    if delete_size[0] != 0xBA or struct.unpack("<I", delete_size[1:])[0] != contract.object_size:
        raise ValueError(f"object size changed for 0x{contract.vtable_rva:X}")
    walk = bytes_at(data, image, contract.common_walk_rva, len(contract.common_walk_anchor))
    if walk != contract.common_walk_anchor:
        raise ValueError(f"common-vector walk changed for 0x{contract.vtable_rva:X}")

    result = {
        "vtable_rva": f"0x{contract.vtable_rva:X}",
        "complete_object_locator": {
            "rva": f"0x{col_rva:X}",
            "signature": signature,
            "object_offset": offset,
            "constructor_displacement": cd_offset,
            "self_rva": f"0x{self_rva:X}",
        },
        "type_descriptor_rva": f"0x{type_rva:X}",
        "class_hierarchy_rva": f"0x{hierarchy_rva:X}",
        "rtti_type_name": contract.type_name,
        "base_types": list(base_names),
        "deleting_destructor_rva": f"0x{slots[0]:X}",
        "object_size": f"0x{contract.object_size:X}",
        "first_sixteen_slot_rvas": [f"0x{x:X}" for x in slots],
        "common_effect_vector": {
            "pointer_offset": "0x40",
            "count_offset": "0x4C",
            "walk_rva": f"0x{contract.common_walk_rva:X}",
            "walk_anchor_sha256": sha256(walk),
            "child_dispatch_vtable_offset": "0x58",
        },
        "live_position": contract.live_position,
    }
    if contract.scope_walk_rva is not None:
        scope_walk = bytes_at(
            data, image, contract.scope_walk_rva, len(contract.scope_walk_anchor)
        )
        if scope_walk != contract.scope_walk_anchor:
            raise ValueError(f"scope-vector walk changed for 0x{contract.vtable_rva:X}")
        result["separate_scope_storage"] = {
            "pointer_offset": "0x60",
            "count_offset": "0x6C",
            "first_scope_walk_rva": f"0x{contract.scope_walk_rva:X}",
            "walk_anchor_sha256": sha256(scope_walk),
            "classification": "scope/configuration storage, distinct from common effect children",
        }
    return result


TOKEN_RE = re.compile(r'"(?:\\.|[^"\\])*"|[{}=]|[^\s{}=]+')


def tokens(source: str) -> list[str]:
    stripped = "\n".join(line.split("#", 1)[0] for line in source.splitlines())
    return TOKEN_RE.findall(stripped)


def find_block(items: list[str], name: str, start: int = 0) -> tuple[int, int]:
    for i in range(start, len(items) - 2):
        if items[i : i + 3] == [name, "=", "{"]:
            depth = 1
            for j in range(i + 3, len(items)):
                if items[j] == "{":
                    depth += 1
                elif items[j] == "}":
                    depth -= 1
                    if depth == 0:
                        return i + 3, j
    raise ValueError(f"block not found: {name}")


def child_assignment_keys(items: list[str], begin: int, end: int) -> tuple[str, ...]:
    result: list[str] = []
    depth = 0
    i = begin
    while i < end:
        if items[i] == "{":
            depth += 1
        elif items[i] == "}":
            depth -= 1
        elif depth == 0 and i + 1 < end and items[i + 1] == "=":
            result.append(items[i])
        i += 1
    return tuple(result)


def named_children(source: str, outer: str, inner: str | None = None) -> tuple[str, ...]:
    items = tokens(source)
    begin, end = find_block(items, outer)
    if inner is not None:
        begin, end = find_block(items, inner, begin)
    return child_assignment_keys(items, begin, end)


def extract(exe: Path, game_root: Path) -> dict[str, Any]:
    exe_data = exe.read_bytes()
    digest = sha256(exe_data)
    if len(exe_data) != EXPECTED_EXE_SIZE or digest != EXPECTED_EXE_SHA256:
        raise ValueError(f"unexpected executable: size={len(exe_data)} sha256={digest}")
    image = pefile.PE(data=exe_data, fast_load=True)
    if int(image.OPTIONAL_HEADER.ImageBase) != EXPECTED_IMAGE_BASE:
        raise ValueError("unexpected image base")
    residuals = [extract_residual(exe_data, image, item) for item in RESIDUALS]

    source_text: dict[str, str] = {}
    source_rows: list[dict[str, str]] = []
    for relative, expected in SOURCE_CONTRACTS.items():
        data = (game_root / relative).read_bytes()
        actual = sha256(data)
        if actual != expected:
            raise ValueError(f"stock source changed: {relative}: {actual}")
        source_text[relative] = data.decode("utf-8-sig")
        source_rows.append({"path": relative, "sha256": actual})

    cb_source = source_text["common/casus_belli_types/00_event_war.txt"]
    on_defeat = named_children(cb_source, "raiktor_claim_cb", "on_defeat")
    if on_defeat != EXPECTED_ON_DEFEAT_KEYS:
        raise ValueError(f"raiktor on_defeat order changed: {on_defeat!r}")

    scripted_shapes: dict[str, list[str]] = {}
    for name, expected in EXPECTED_SCRIPTED_SHAPES.items():
        if name == "laamp_as_mercenary_payout_tooltip_effect":
            relative = "common/scripted_effects/07_dlc_ep3_scripted_effects.txt"
        elif name == "mandala_war_defeat_effects":
            relative = "common/scripted_effects/tgp_mandala_scripted_effects.txt"
        else:
            relative = "common/scripted_effects/00_war_effects.txt"
        actual = named_children(source_text[relative], name)
        if actual != expected:
            raise ValueError(f"scripted effect shape changed for {name}: {actual!r}")
        scripted_shapes[name] = list(actual)

    return {
        "schema": "xar.ck3.g2_truce_residual_rtti.extract.v1",
        "result": "GREEN",
        "read_only": True,
        "ck3_started": False,
        "exact_build": {
            "product_version": "1.19.0.6",
            "sha256": digest,
            "file_size": len(exe_data),
            "image_base": f"0x{EXPECTED_IMAGE_BASE:X}",
        },
        "residual_types": residuals,
        "stock_sources": source_rows,
        "raiktor_on_defeat_top_level": [
            {"index": i, "key": key} for i, key in enumerate(on_defeat)
        ],
        "scripted_effect_top_level_shapes": scripted_shapes,
        "correlation": {
            "index6": "modify_all_participants_fame_values: eight call arguments; live selector_count=8",
            "index7": "add_truce_attacker_defeat_effect: four top-level children; live default count=4",
            "index9": "on_lost_aggression_war_discontent_loss: one top-level Context child; live default count=1 and TargetingFactionsDiscontent descendant",
            "index10": "laamp_as_mercenary_payout_tooltip_effect: one ShowAsTooltip child; live default count=1 and exact 0x44D1D50 descendant",
            "index11": "mandala_war_defeat_effects: two Context children; live default count=2",
            "unique_truce_scripted_effect_index": 7,
            "unique_next_read_only_path": (
                "root index7 default common child1 (hidden_effect) -> its common child0 "
                "(scope:attacker Context) -> its common child0 (expected CAddTruceEffect<0>)"
            ),
            "residual_index10_branch_is_truce": False,
        },
        "cif_0x258_closure": {
            "captured_parent_objects_null": 3,
            "captured_positions": [
                "index9.default.child0",
                "index10.default.child0.context.child4",
                "index10.default.child0.context.child5",
            ],
            "recursive_child_object_sampled": False,
            "correction": (
                "null applies only to the three captured parent CIf objects; it must not be "
                "propagated to the distinct recursive CIf child. Source correlation removes "
                "the entire index9/index10 branches from the truce search."
            ),
        },
        "boundaries": {
            "public_abi_changed": False,
            "readiness_changed": False,
            "production_shape_contract_changed": False,
            "mutation_sent": False,
            "next_path_requires_live_validation": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", required=True, type=Path)
    parser.add_argument("--game-root", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    payload = extract(args.exe.resolve(), args.game_root.resolve())
    rendered = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.resolve().parent.mkdir(parents=True, exist_ok=True)
        args.output.resolve().write_text(rendered, encoding="utf-8", newline="\n")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
