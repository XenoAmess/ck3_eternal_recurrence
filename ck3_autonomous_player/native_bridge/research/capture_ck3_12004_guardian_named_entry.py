"""Root-only finite HasGuardian literal locator, using retained PE metadata.

This discovers a named source entry. It does not qualify a callback, read a
running process, import bridge code, or compute a new executable hash.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import struct


def offsets(data: bytes, needle: bytes):
    position = 0
    while (position := data.find(needle, position)) >= 0:
        yield position
        position += 1


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True, type=Path)
    parser.add_argument("--pe-metadata", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    metadata = json.loads(args.pe_metadata.read_text(encoding="utf-8-sig"))
    section = next(row for row in metadata["sections"] if row["name"] == ".rdata")
    file_start = section["PointerToRawData"]
    size = section["SizeOfRawData"]
    rva_start = section["VirtualAddress"]
    image_base = metadata["optional_header"]["ImageBase"]
    with args.image.open("rb") as image:
        image.seek(file_start)
        data = image.read(size)
    if len(data) != size:
        raise RuntimeError("short retained .rdata source-locator read")
    hits = []
    for offset in offsets(data, b"HasGuardian\0"):
        rva = rva_start + offset
        references = []
        for ref in offsets(data, struct.pack("<Q", image_base + rva)):
            start, end = max(0, ref - 32), min(len(data), ref + 40)
            references.append({
                "rva": rva_start + ref, "file_offset": file_start + ref,
                "neighbor_begin_rva": rva_start + start,
                "neighbor_hex": data[start:end].hex(),
            })
        hits.append({
            "rva": rva, "rva_hex": hex(rva), "file_offset": file_start + offset,
            "standalone_cstring_start": offset == 0 or data[offset - 1] == 0,
            "name_context_begin_rva": rva_start + max(0, offset - 32),
            "name_context_hex": data[max(0, offset - 32):offset + 12].hex(),
            "same_section_va64_references": references,
        })
    packet = {
        "first_id": "actual4_child_has_guardian_named_entry34_FIRST0",
        "target_source": "game/gui/shared/lists.gui:1591 Character.HasGuardian",
        "image": str(args.image), "pe_metadata": str(args.pe_metadata),
        "section": {"name": ".rdata", "rva": rva_start,
                    "file_offset": file_start, "bytes": size},
        "target_literal": "HasGuardian", "hits": hits,
        "cost": {"game_image_reads": 1, "game_image_bytes_read": len(data),
                 "game_image_hashes": 0, "new_pe_parses": 0},
        "callback_qualified": False, "guardian_observed": False,
        "next": "Use actual hit references and cached function metadata for a precise callback pin; do not guess a Character layout or invoke a GUI wrapper",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "literal_hit_count": len(hits),
                      "bytes_read": len(data), "callback_qualified": False}))


if __name__ == "__main__":
    main()
