"""Verify new Execute slots using the previously frozen native source proof.

This deliberately reuses the prior 170-check artifact, rather than repeating
its matrix. New checks cover exact vtable slot bindings and used-input pins.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

import pefile


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--previous-proof", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    abi_path = Path(__file__).with_name("sway_completion12002_termination_abi.json")
    abi = json.loads(abi_path.read_text(encoding="utf-8"))
    previous_raw = args.previous_proof.read_bytes()
    previous = json.loads(previous_raw)
    raw = args.exe.read_bytes()
    sha = hashlib.sha256(raw).hexdigest().upper()
    assert sha == abi["exe_sha256"] and len(raw) == abi["exe_size"]
    assert hashlib.sha256(previous_raw).hexdigest() == abi["previous_proof_sha256"]
    assert previous["result"] == "GREEN" and previous["exe_sha256"] == sha
    pe = pefile.PE(data=raw, fast_load=True)
    base = pe.OPTIONAL_HEADER.ImageBase
    checks = []
    def payload(rva, size):
        at = pe.get_offset_from_rva(rva)
        return raw[at:at + size]
    for source in abi["execution_sources"]:
        slot = int(source["slot_rva"], 0)
        execute = int(source["execute_rva"], 0)
        assert struct.unpack("<Q", payload(slot, 8))[0] == base + execute
        checks.append({"source": source["class"], "slot_rva": source["slot_rva"], "execute_rva": source["execute_rva"], "passed": True})
        for pin in source["used_input_pins"]:
            assert payload(int(pin["rva"], 0), len(bytes.fromhex(pin["bytes"]))).hex() == pin["bytes"]
            checks.append({"source": source["class"], "rva": pin["rva"], "asm": pin["asm"], "passed": True})
    result = {"schema": "xar.ck3.sway.termination-source-verification.v1", "result": "GREEN",
        "read_only_file_research": True, "live_verified": False, "checks": checks,
        "exe_sha256": sha, "abi_sha256": hashlib.sha256(abi_path.read_bytes()).hexdigest(),
        "reused_previous_proof_sha256": hashlib.sha256(previous_raw).hexdigest(),
        "previous_matrix_repeated": False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"result": "GREEN", "new_checks": len(checks), "output": str(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
