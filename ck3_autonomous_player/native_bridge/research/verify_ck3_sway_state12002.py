"""Verify the exact new Sway manager/storage/field mapping; frozen files only."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from scan_anchors import PeImage

SHA = "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D"
INSTRUCTIONS = (
    ("game_data_manager", 0x2ADC7F8, "498d9fc0a50000"),
    ("manager_vtable", 0x2ADC80B, "488d0526cdc901"),
    ("manager_storage_slot", 0x2ADC820, "488d4b20"),
    ("manager_construct_storage", 0x2ADC824, "e8a783f7ff"),
    ("storage_alloc_size", 0x2A54BEC, "b958000000"),
    ("storage_base_plus_eight", 0x2A54BFE, "488d5808"),
    ("block_table_zero", 0x2A54C0A, "4c892b"),
    ("slot_table_zero", 0x2A54C1C, "4c896b18"),
    ("active_count_zero", 0x2A54C36, "44896b34"),
    ("capacity_read", 0x2A54C51, "8b7b24"),
    ("slot_stride16", 0x2A54C84, "49c1e004"),
    ("slot_table_publish", 0x2A54CA7, "4c897b18"),
    ("capacity_publish", 0x2A54CE3, "894324"),
    ("block_stride_shift", 0x2A53B52, "c1e00a"),
    ("instance_identity_initialize", 0x2A53C4A, "488d4310"),
    ("block_1024", 0x2A53C4E, "b900040000"),
    ("instance_stride", 0x2A53C59, "488d8058030000"),
    ("storage_vtable", 0x2A54D9A, "488d05874ad201"),
    ("manager_storage_publish", 0x2A54DE4, "49893424"),
    ("instance_size", 0x2A491C9, "ba58030000"),
    ("scheme_type", 0x2A49208, "488b7120"),
    ("scheme_type_magic", 0x2A49215, "817e384f624447"),
    ("scheme_type_key", 0x2A49222, "4883c618"),
    ("owner", 0x2A49367, "8b572c"),
    ("target_kind", 0x2A493CA, "48634730"),
    ("target_id", 0x2A4945C, "8b5734"),
    ("exposed", 0x2A49746, "0fb6977c020000"),
    ("frozen", 0x2A49AD7, "80bfa802000001"),
    ("basic_definition", 0x2A46720, "0fb6814e0a0000"),
    ("progress", 0x2A46760, "8b4178"),
    ("progress_goal", 0x2A46770, "8b8150030000"),
)
VTABLES = {
    "manager": (0x4779538, [0x2A46E30, 0x3F7E2D0, 0x2A46E70, 0x3F7E350, 0x2A46ED0, 0x8522C0]),
    "storage": (0x4779828, [0x2A533B0, 0x3F7E2D0, 0x2A531F0, 0x2A52E40, 0x22C6010, 0x8522C0]),
    "instance": (0x47794E8, [0x2A491B0, 0x3F7E2D0, 0x2A491F0, 0x3F7E350, 0x2A49B50, 0x2A4A350]),
}
def require(value: bool, message: str) -> None:
    if not value: raise ValueError(message)
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = args.exe.read_bytes()
    require(len(data) == 101039736 and hashlib.sha256(data).hexdigest().upper() == SHA, "frozen exact EXE mismatch")
    pe = PeImage(data)
    md = Cs(CS_ARCH_X86, CS_MODE_64)
    rows = []
    for name, rva, hexbytes in INSTRUCTIONS:
        at = pe.rva_to_offset(rva); expected = bytes.fromhex(hexbytes)
        require(data[at:at + len(expected)] == expected, "native instruction mismatch: " + name)
        instruction = next(md.disasm(expected, rva))
        rows.append({"name": name, "rva": hex(rva), "bytes": hexbytes,
            "instruction": instruction.mnemonic + " " + instruction.op_str})
    for name, (rva, expected) in VTABLES.items():
        at = pe.rva_to_offset(rva)
        actual = [v - 0x140000000 for v in struct.unpack_from("<6Q", data, at)]
        require(actual == expected, "native vtable mismatch: " + name)
    native = Path(__file__).resolve().parents[1]
    header = (native / "include/xar_bridge/ck3_12002_sway_state.hpp").read_text(encoding="utf-8-sig")
    constants = {"kSwayManagerOffset12002": 0xA5C0, "kSwayManagerVtableRva12002": 0x4779538,
        "kSwayStorageVtableRva12002": 0x4779828, "kSwayInstanceVtableRva12002": 0x47794E8,
        "kSwayTypeVtableRva12002": 0x48B9F20}
    for key, value in constants.items():
        found = re.search(r"\b" + key + r"\s*=\s*(0x[0-9A-Fa-f]+)\s*;", header)
        require(found is not None and int(found.group(1), 0) == value, "provider binding mismatch: " + key)
    stock = args.exe.parent.parent / "game/common/schemes/scheme_types/sway_scheme.txt"
    text = stock.read_text(encoding="utf-8-sig")
    for semantic in ("target_type = character", "is_secret = no", "is_basic = yes", "base_progress_goal = 365"):
        require(semantic in text, "frozen Sway definition mismatch")
    result = {"status": "GREEN", "readiness": "static-ready", "game_version": "1.20.0.2",
        "executable_sha256": SHA, "instruction_count": len(rows), "instructions": rows,
        "vtable_count": len(VTABLES), "production_binding_count": len(constants),
        "stock_definition_sha256": hashlib.sha256(stock.read_bytes()).hexdigest(),
        "stock_native_tree": "target-character, basic, nonsecret; stock base goal365; native goal is read",
        "source_contract": "manager/storage constructors plus instance serializer and native leaf getters",
        "provider_fixture_required": True, "live_verified": False, "ck3_touched": False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"PASS Sway state ABI: {len(rows)} instructions, {len(VTABLES)} vtables, {len(constants)} provider bindings")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
