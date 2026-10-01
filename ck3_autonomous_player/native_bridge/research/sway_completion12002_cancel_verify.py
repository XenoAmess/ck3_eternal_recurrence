"""Verify the reviewed CK3 1.20.0.2 Sway terminal/current-validity ABI offline.

This reads an executable file only. It neither attaches to CK3 nor invokes a
native function. A GREEN result is a static source proof, never a live fixture.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

EXPECTED_SHA = "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D"
EXPECTED_SIZE = 101039736


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--abi", type=Path, default=Path(__file__).with_name("sway_completion12002_cancel_abi.json"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest_raw = args.abi.read_bytes()
    abi = json.loads(manifest_raw)
    raw = args.exe.read_bytes()
    exe_sha = hashlib.sha256(raw).hexdigest().upper()
    checks: list[dict] = []
    def check(name: str, condition: bool, **detail) -> None:
        checks.append({"name": name, "passed": bool(condition), **detail})
        if not condition:
            raise ValueError("ABI verification failed: " + name)
    def write(error: str | None = None) -> int:
        result = {
            "schema": "xar.ck3.sway.completion-cancel.source-verification.v1",
            "result": "GREEN" if error is None else "RED",
            "read_only_file_research": True, "live_verified": False,
            "exe": str(args.exe), "exe_sha256": exe_sha, "exe_size": len(raw),
            "abi": str(args.abi), "abi_sha256": hashlib.sha256(manifest_raw).hexdigest(),
            "checks": checks, "error": error,
            "meaning": "Exact-build static native source contract; no game process or native call exercised.",
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"result": result["result"], "checks": len(checks), "output": str(args.output), "live_verified": False, "error": error}))
        return 0 if error is None else 1
    try:
        check("exact_executable", exe_sha == EXPECTED_SHA and len(raw) == EXPECTED_SIZE)
        check("manifest_build", abi["exe_sha256"] == EXPECTED_SHA and abi["exe_size"] == EXPECTED_SIZE)
        pe = pefile.PE(data=raw, fast_load=True)
        base = pe.OPTIONAL_HEADER.ImageBase
        check("image_base", base == int(abi["image_base"], 0))
        md = Cs(CS_ARCH_X86, CS_MODE_64)
        def payload(rva: int, size: int) -> bytes:
            at = pe.get_offset_from_rva(rva)
            return raw[at:at + size]
        pdata = next(s for s in pe.sections if s.Name.rstrip(b"\0") == b".pdata").get_data()
        ranges = {(a, b) for a, b, _ in struct.iter_unpack("<III", pdata[:len(pdata) // 12 * 12])}
        for span in abi["spans"]:
            first, last = int(span["first"], 0), int(span["last"], 0)
            check("span:" + span["name"], hashlib.sha256(payload(first, last - first)).hexdigest() == span["sha256"], first=span["first"], last=span["last"])
            if span["boundary"] == ".pdata":
                check("pdata:" + span["name"], (first, last) in ranges)
            for anchor in span["anchors"]:
                rva = int(anchor["rva"], 0)
                expected = bytes.fromhex(anchor["bytes"])
                actual = payload(rva, len(expected))
                ins = next(md.disasm(actual, rva), None)
                asm = None if ins is None else ins.mnemonic + " " + ins.op_str
                check("anchor:" + anchor["rva"], first <= rva < last and actual == expected and ins is not None and ins.size == len(expected) and asm == anchor["asm"], asm=asm)
        for table in abi["tables"]:
            actual = payload(int(table["rva"], 0), table["size"])
            check("table:" + table["name"], actual.hex() == table["bytes"] and hashlib.sha256(actual).hexdigest() == table["sha256"])
        for token in abi["tokens"]:
            number, pointer = struct.unpack("<QQ", payload(int(token["registry_rva"], 0), 16))
            key = token["key"].encode("ascii") + b"\0"
            check("token:" + token["key"], number == int(token["token"], 0) and pointer == base + int(token["literal_rva"], 0) and payload(int(token["literal_rva"], 0), len(key)) == key)
        for binding in abi["vtable_bindings"]:
            actual = struct.unpack("<Q", payload(int(binding["table_rva"], 0) + binding["slot"] * 8, 8))[0]
            check("vtable:" + binding["table_rva"] + ":" + str(binding["slot"]), actual == base + int(binding["function_rva"], 0))
        for binding in abi.get("rtti_bindings", []):
            descriptor, col, table = [int(binding[k], 0) for k in ("descriptor_rva", "col_rva", "vtable_rva")]
            fields = struct.unpack("<6I", payload(col, 24))
            name = binding["name"].encode("ascii") + b"\0"
            check("rtti:" + binding["name"], fields[0] == 1 and fields[1] == binding["secondary_offset"] and fields[3] == descriptor and fields[5] == col and struct.unpack("<Q", payload(table - 8, 8))[0] == base + col and payload(descriptor + 16, len(name)) == name)
        for literal in abi.get("literals", []):
            key = literal["key"].encode("ascii") + b"\0"
            check("literal:" + literal["key"], payload(int(literal["rva"], 0), len(key)) == key)
        check("status_enum_join", struct.unpack("<II", payload(0x4779528, 8)) == (0x2D1F, 0x2F8D))
        check("current_validity_register_contract", abi["contract"]["current_final_validity"]["registers"] == {"rcx": "resolved exact scheme", "edx": 1, "r8d": 1, "return": "AL boolean"})
        check("cause_scope", abi["contract"]["termination"]["cause_persisted_in_instance"] is False and abi["contract"]["retention"]["cold_snapshot_retention_proven"] is False)
        return write()
    except (ValueError, KeyError, StopIteration, struct.error, pefile.PEFormatError) as exc:
        return write(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
