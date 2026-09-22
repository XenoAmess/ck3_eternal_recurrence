"""Bind selected peace-policy extraction bytes and script identity; never run CK3."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct

import pefile

from war_film_peace_extract import EXPECTED_SHA


RANGES = [
    (0x183DEF6, 0x183DF62), (0x1881419, 0x1881499),
    (0x18815D1, 0x1881686), (0x1881A32, 0x1881A7E), (0x1881B00, 0x1881B2C),
    (0x1880B80, 0x1880C20), (0x1880F50, 0x188100C), (0x1881048, 0x1881064),
    (0x18811AE, 0x188125C), (0x1880B0C, 0x1880B62), (0x18BB040, 0x18BB09C),
    (0x2C390CA, 0x2C391AB), (0x2C39350, 0x2C3937F), (0x2C3968D, 0x2C396B8),
    (0x2C3A6C7, 0x2C3A70C), (0x2C3A852, 0x2C3A863),
    (0x2C3AA62, 0x2C3AAEA), (0x2C3B2A1, 0x2C3B2C0),
    (0x2C43B40, 0x2C43C43), (0x2C43DC1, 0x2C43EF6),
    (0x2C44320, 0x2C44389), (0x2C44410, 0x2C4445F),
    (0x26B30A0, 0x26B30F2), (0x26B3175, 0x26B3213), (0x26B32D0, 0x26B32F8),
    (0xD9D5FB, 0xD9D621), (0x28FA1A0, 0x28FA229),
]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--extract", type=Path, required=True)
    parser.add_argument("--war-script", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    raw = args.exe.read_bytes()
    if digest(raw) != EXPECTED_SHA:
        raise ValueError("Wrong executable bytes")
    pe = pefile.PE(data=raw, fast_load=True)
    base = pe.OPTIONAL_HEADER.ImageBase
    extract_raw = args.extract.read_bytes()
    source = json.loads(extract_raw)
    if source["exe"]["sha256"] != EXPECTED_SHA:
        raise ValueError("Extraction build differs")
    selected = []
    all_instructions = {}
    functions = []
    for function in source["functions"]:
        start, end = int(function["start_rva"], 16), int(function["end_rva"], 16)
        if digest(pe.get_data(start, end - start)) != function["sha256"]:
            raise ValueError("Captured pdata span no longer matches executable")
        functions.append({k: v for k, v in function.items() if k != "instructions"})
        for instruction in function["instructions"]:
            rva = int(instruction["rva"], 16)
            value = bytes.fromhex(instruction["bytes"])
            if pe.get_data(rva, len(value)) != value:
                raise ValueError("Captured instruction differs from executable")
            all_instructions[rva] = instruction
            if any(lo <= rva < hi for lo, hi in RANGES):
                selected.append(instruction)
    expected = {
        0x2C43E1D: "4885c0", 0x2C43E20: "0f8e87000000",
        0x1881631: "48f7f9", 0x1881637: "0f8570010000",
        0x1881006: "7e04", 0x26B31DC: "4885db", 0x26B31DF: "410f9fc1",
        0x26B32EF: "e8acfdffff", 0x2C3A852: "498d57d8", 0x2C3AAD9: "498d57d5",
    }
    for rva, value in expected.items():
        if all_instructions.get(rva, {}).get("bytes") != value:
            raise ValueError(f"Missing/different critical instruction {rva:#x}")
    tokens = []
    for name, string_rva, token in [
        ("ai_frequency", 0x4292290, 0x770),
        ("ai_frequency_by_tier", 0x42AD2A0, 0x3C29),
        ("ai_maybe", 0x429FE10, 0x3168),
        ("ai_accept_negotiation", 0x429FF18, 0x326A),
    ]:
        if pe.get_data(string_rva, len(name) + 1) != name.encode() + b"\0":
            raise ValueError("Token string mismatch")
        rows = []
        for match in re.finditer(re.escape(struct.pack("<Q", base + string_rva)), raw):
            offset = match.start()
            if offset >= 8 and struct.unpack_from("<I", raw, offset - 8)[0] == token:
                rows.append({"id_rva": hex(pe.get_rva_from_offset(offset - 8)),
                             "pointer_rva": hex(pe.get_rva_from_offset(offset)),
                             "bytes": raw[offset - 8:offset + 8].hex()})
        if not rows:
            raise ValueError("Token-name table binding missing")
        tokens.append({"name": name, "token": hex(token), "string_rva": hex(string_rva), "table_rows": rows})
    jump_rows = []
    for name, token, subtract, byte_table, target_table, expected_target in [
        ("ai_maybe", 0x3168, 0x3168, 0x2C3B61C, 0x2C3B5DC, 0x2C3A852),
        ("ai_accept_negotiation", 0x326A, 0x3267, 0x2C3B730, 0x2C3B714, 0x2C3AAD9),
    ]:
        index = pe.get_data(byte_table + token - subtract, 1)[0]
        target = struct.unpack("<I", pe.get_data(target_table + index * 4, 4))[0]
        if target != expected_target:
            raise ValueError("Parser jump-table binding differs")
        jump_rows.append({"name": name, "byte_table_rva": hex(byte_table), "index": index,
                          "target_table_rva": hex(target_table), "target_rva": hex(target)})
    command = []
    for vtable in (0x40829C8, 0x40829F8):
        col = struct.unpack("<Q", pe.get_data(vtable - 8, 8))[0] - base
        td = struct.unpack("<I", pe.get_data(col + 12, 4))[0]
        name = pe.get_data(td + 16, 128).split(b"\0")[0].decode("ascii")
        if name != ".?AVCSendCharacterInteractionCommand@@":
            raise ValueError("Command RTTI differs")
        command.append({"vtable_rva": hex(vtable), "complete_object_locator_rva": hex(col),
                        "type_descriptor_rva": hex(td), "type_name": name,
                        "first_six_slots": [hex(struct.unpack("<Q", pe.get_data(vtable + i * 8, 8))[0] - base) for i in range(6)]})
    script = args.war_script.read_bytes()
    lines = script.decode("utf-8-sig").splitlines()
    key = "end_war_attacker_white_peace_interaction"
    start = next(i for i, line in enumerate(lines) if re.match(r"^" + key + r"\s*=\s*\{", line))
    depth = 0
    fields = []
    end = None
    for i in range(start, len(lines)):
        # Strip comments and quoted strings before counting braces in this script block.
        lexical = re.sub(r'"(?:\\.|[^"\\])*"|#[^\n]*', '""', lines[i])
        if depth == 1:
            match = re.match(r"\s*(\w+)\s*=", lexical)
            if match:
                fields.append({"key": match[1], "line": i + 1, "source": lines[i].strip()})
        depth += lexical.count("{") - lexical.count("}")
        if depth == 0:
            end = i
            break
    if end is None:
        raise ValueError("Unclosed white-peace block")
    block = "\n".join(lines[start:end + 1]) + "\n"
    for absent in ("ai_maybe", "ai_accept_negotiation", "auto_accept", "send_option", "ai_intermediary_accept"):
        if any(item["key"] == absent for item in fields):
            raise ValueError(f"Previously absent field now present: {absent}")
    report = {
        "schema": "xar.war-film-peace-byte-summary.v1", "build": "1.19.0.6",
        "result": "selected-byte-and-script-bindings-match",
        "semantic_correctness_automatically_verified": False, "live_execution": False,
        "exe": {"sha256": EXPECTED_SHA, "bytes": len(raw), "image_base": hex(base)},
        "extract": {"path": str(args.extract.resolve()), "sha256": digest(extract_raw),
                    "args": source["args"], "python": source["python"], "versions": source["versions"]},
        "summarizer_sha256": digest(Path(__file__).read_bytes()),
        "pdata_spans": functions, "selected_instructions": sorted(selected, key=lambda row: int(row["rva"], 16)),
        "token_bindings": tokens, "parser_jumps": jump_rows, "command_rtti": command,
        "reader_vbtable": {"rva": "0x43f5998", "signed_dwords": list(struct.unpack("<ii", pe.get_data(0x43F5998, 8)))},
        "intermediary_status_combination_table": {"rva": "0x4403a98", "bytes": pe.get_data(0x4403A98, 4).hex()},
        "explicit_code_windows": source["explicit_code_windows"], "data_windows": source["data_windows"],
        "white_peace_script": {"path": str(args.war_script.resolve()), "sha256": digest(script),
                               "key": key, "line_start": start + 1, "line_end": end + 1,
                               "normalized_block_sha256": digest(block.encode()), "top_level_fields": fields,
                               "frequency_source_lines": [{"line": i + 1, "text": lines[i]} for i in range(start, end + 1) if 1010 <= i + 1 <= 1021]},
        "limitations": ["Byte checks do not execute the scheduler, evaluate a live score, prove reachability in a particular save, or observe peace.",
                        "pdata records can be split fragments and contain jump-table data; linear decoding does not make every decoded byte reachable code.",
                        "Explicit code windows are bounded locators, not asserted complete function boundaries."]
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as stream:
        stream.write((json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode())
    print(json.dumps({"output": str(args.output), "sha256": digest(args.output.read_bytes()),
                      "pdata_spans": len(functions), "selected_instructions": len(selected), "script_lines": [start + 1, end + 1]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
