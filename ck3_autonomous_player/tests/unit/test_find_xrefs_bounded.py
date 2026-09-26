"""The research xref scanner must preserve references across decode chunks."""

import struct
import sys
from pathlib import Path

RESEARCH = Path(__file__).parents[2] / "native_bridge/research"
sys.path.insert(0, str(RESEARCH))

import find_xrefs  # noqa: E402


def test_rip_reference_crossing_chunk_boundary_is_reported_once(monkeypatch):
    monkeypatch.setattr(find_xrefs, "DECODE_CHUNK_BYTES", 32)
    base = 0x140000000
    source_start = 0x1000
    target_rva = 0x2000
    instruction_offset = 30
    displacement = target_rva - (source_start + instruction_offset + 7)
    code = b"\x90" * instruction_offset + b"\x48\x8d\x05" + struct.pack("<i", displacement)
    code += b"\x90" * 38 + b"\xc3"
    refs = list(find_xrefs.iter_code_refs(code, source_start, base, {target_rva}))
    assert refs == [f"lea  source=0x{source_start + instruction_offset:X} target=0x{target_rva:X}"]


def test_direct_call_candidate_is_found_without_full_section_disassembly(monkeypatch):
    monkeypatch.setattr(find_xrefs, "DECODE_CHUNK_BYTES", 32)
    source_start = 0x1000
    target_rva = 0x2200
    offset = 35
    displacement = target_rva - (source_start + offset + 5)
    code = b"\x90" * offset + b"\xe8" + struct.pack("<i", displacement) + b"\xc3"
    refs = list(find_xrefs.iter_code_refs(
        code, source_start, 0x140000000, {target_rva}, direct_only=True
    ))
    assert refs == [f"call source=0x{source_start + offset:X} target=0x{target_rva:X}"]
