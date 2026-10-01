"""Pin new Tenet source/filter leaves; reuse frozen model/final/scope proof.

This reads a frozen EXE and proof files only. It neither contacts CK3 nor
constructs native categories/items, publishes a provider, or performs actions.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct

from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from scan_anchors import PeImage


def verify(exe: Path, output: Path, source_root: Path, evidence_root: Path) -> dict:
    contract = json.loads(Path(__file__).with_name(
        "religion_reform12002_tenet_sources_abi.json").read_text(encoding="utf-8"))
    data = exe.read_bytes()
    assert len(data) == contract["executable_size"]
    assert hashlib.sha256(data).hexdigest() == contract["executable_sha256"]
    pe = PeImage(data)
    md = Cs(CS_ARCH_X86, CS_MODE_64)
    opt = struct.unpack_from("<I", data, 0x3C)[0] + 24
    pd_rva, pd_size = struct.unpack_from("<II", data, opt + 112 + 3 * 8)
    pd_offset = pe.rva_to_offset(pd_rva)
    pdata = {(start, end) for start, end, _ in struct.iter_unpack(
        "<III", data[pd_offset:pd_offset + pd_size])}
    output.mkdir(parents=True, exist_ok=True)
    result = {"executable_sha256": contract["executable_sha256"],
              "new_spans": [], "new_anchors": [], "reused_proofs": [],
              "readiness": "research", "native_tree": "static-confirmed",
              "provider_implemented": False, "live_verified": False,
              "local_ck3_touched": False}
    for pin in contract["reused_proofs"]:
        root = source_root if pin["root"] == "source" else evidence_root
        path = root / pin["path"]
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest == pin["sha256"], (str(path), digest)
        result["reused_proofs"].append({"path": str(path), "sha256": digest,
                                        "executable_spans_reverified": False})
    for pin in contract["new_native_spans"]:
        start, end = int(pin["start_rva"], 0), int(pin["end_exclusive_rva"], 0)
        if pin["boundary"] == "PE_exception_directory":
            assert (start, end) in pdata, pin["name"]
        offset = pe.rva_to_offset(start)
        body = data[offset:offset + end - start]
        assert hashlib.sha256(body).hexdigest() == pin["sha256"], pin["name"]
        instructions = list(md.disasm(body, start))
        assert instructions and instructions[-1].address + instructions[-1].size == end
        (output / (pin["name"] + ".txt")).write_text("\n".join(
            f"{i.address:X} {i.bytes.hex()} {i.mnemonic} {i.op_str}"
            for i in instructions) + "\n", encoding="utf-8")
        result["new_spans"].append(pin)
    for pin in contract["new_semantic_anchors"]:
        rva = int(pin["rva"], 0)
        offset = pe.rva_to_offset(rva)
        instruction = next(md.disasm(data[offset:offset + 15], rva))
        actual = f"{instruction.mnemonic} {instruction.op_str}"
        assert actual == pin["instruction"], (pin["name"], actual)
        result["new_anchors"].append(dict(pin, bytes=instruction.bytes.hex()))
    result["status"] = "GREEN"
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n",
                                        encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.exe, args.output_dir, args.source_root, args.evidence_root)
    print(f"GREEN Tenet source tree: {len(result['new_spans'])} new spans, "
          f"{len(result['new_anchors'])} new anchors, "
          f"{len(result['reused_proofs'])} frozen proof pins reused; no CK3")


if __name__ == "__main__":
    main()
