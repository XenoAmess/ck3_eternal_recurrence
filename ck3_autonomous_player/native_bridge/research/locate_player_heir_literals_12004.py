"""Read only PE headers and fixed exact-.4 literals in .rdata, with hit caps.

No process access, executable copying, code/xref scan, dependency or game call.
The caller first freezes and checks its source plan. Existing source proof,
not this locator, supplies the whole executable hash and its actual use.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import mmap
from pathlib import Path
import struct

SHA = "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518"
NAMES = ("GetPlayerHeir", "IsPlayerHeir", "CanContinue", "player_heir")


def fingerprint(plan):
    path = Path(plan["pe_discovery"]["exe_path"])
    before, started = path.stat(), datetime.now(timezone.utc).isoformat()
    digest, size = hashlib.sha256(), 0
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
            size += len(chunk)
    after = path.stat()
    stable = (before.st_size, before.st_mtime_ns, before.st_ino) == (after.st_size, after.st_mtime_ns, after.st_ino)
    return {"schema": "xar.player-heir12004.exact-file-identity.v1", "machine_id": plan["machine_id"],
            "started_at_utc": started, "ended_at_utc": datetime.now(timezone.utc).isoformat(),
            "exe_path": str(path), "expected_sha256": SHA, "actual_sha256": digest.hexdigest(),
            "status": "MATCH" if stable and size == before.st_size and digest.hexdigest() == SHA else "MISMATCH",
            "bytes_streamed": size, "chunk_bytes": 1024 * 1024, "stat_stable": stable,
            "stat_before": {"bytes": before.st_size, "mtime_ns": before.st_mtime_ns, "file_id": before.st_ino},
            "stat_after": {"bytes": after.st_size, "mtime_ns": after.st_mtime_ns, "file_id": after.st_ino},
            "whole_file_copied": False, "process_memory_reads": 0, "Game_RPC_calls": 0}


def locate(plan):
    if plan["build"]["version"] != "1.20.0.4" or plan["build"]["exe_sha256"].lower() != SHA:
        raise ValueError("only the frozen actual .4 identity is admitted")
    scope = plan["pe_discovery"]
    if scope["sections"] != [".rdata"] or scope["literals"] != list(NAMES) or scope["max_hits_per_name"] != 10:
        raise ValueError("fixed source discovery bounds changed")
    path = Path(scope["exe_path"])
    before = path.stat()
    with path.open("rb") as handle, mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ) as image:
        def checked(offset, size):
            if offset < 0 or size < 0 or offset + size > len(image):
                raise ValueError("PE range outside the frozen file")
            return image[offset:offset + size]

        if checked(0, 2) != b"MZ":
            raise ValueError("DOS signature missing")
        pe = struct.unpack("<I", checked(0x3C, 4))[0]
        if checked(pe, 4) != b"PE\0\0":
            raise ValueError("PE signature missing")
        machine, count, timestamp, _, _, optional_size, _ = struct.unpack("<HHIIIHH", checked(pe + 4, 20))
        optional = pe + 24
        if machine != 0x8664 or count > 32 or struct.unpack("<H", checked(optional, 2))[0] != 0x20B:
            raise ValueError("unsupported PE layout")
        base = struct.unpack("<Q", checked(optional + 24, 8))[0]
        sections = []
        for index in range(count):
            row = struct.unpack("<8sIIIIIIHHI", checked(optional + optional_size + index * 40, 40))
            name = row[0].rstrip(b"\0").decode("ascii")
            if name == ".rdata":
                start, size = row[4], row[3]
                if start + size > len(image):
                    raise ValueError("section outside file")
                sections.append({"name": name, "rva": row[2], "file_offset": start, "raw_bytes": size})
        if len(sections) != 1:
            raise ValueError("one exact .rdata section required")
        section = sections[0]
        start, end = section["file_offset"], section["file_offset"] + section["raw_bytes"]
        hits = {}
        for name in NAMES:
            needle, cursor, rows = name.encode("ascii") + b"\0", start, []
            while len(rows) < 10:
                offset = image.find(needle, cursor, end)
                if offset < 0:
                    break
                context_start = max(start, offset - 8)
                context = checked(context_start, min(end - context_start, len(needle) + 16))
                rows.append({"rva": section["rva"] + offset - start, "file_offset": offset,
                             "va": base + section["rva"] + offset - start,
                             "context_file_offset": context_start, "context_hex": context.hex(),
                             "context_sha256": hashlib.sha256(context).hexdigest()})
                cursor = offset + len(needle)
            hits[name] = {"exact_ascii_nul_hits": rows, "more_than_hit_cap": len(rows) == 10 and image.find(needle, cursor, end) >= 0}
    after = path.stat()
    if (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
        raise ValueError("executable changed during bounded discovery")
    return {"schema": "xar.player-heir12004.fixed-literal-locator.v1", "machine_id": plan["machine_id"],
            "observed_at_utc": datetime.now(timezone.utc).isoformat(), "exe_path": str(path),
            "exe_sha256_from_frozen_prior_proof": SHA, "whole_file_hash_recomputed": False,
            "file_stat": {"bytes": before.st_size, "mtime_ns": before.st_mtime_ns, "file_id": before.st_ino},
            "pe_timestamp": timestamp, "image_base": base, "sections_searched": sections, "hits": hits,
            "proof_layer": "locator_only", "registration_or_callback_semantics_verified": False,
            "code_section_scans": 0, "process_memory_reads": 0, "Game_RPC_calls": 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--fingerprint-only", action="store_true")
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    result = fingerprint(plan) if args.fingerprint_only else locate(plan)
    result["plan_sha256"] = hashlib.sha256(args.plan.read_bytes()).hexdigest()
    result["locator_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    encoded = (json.dumps(result, indent=2) + "\n").encode("utf-8")
    if len(encoded) > 16 * 1024:
        raise ValueError("bounded locator output exceeded16KiB")
    with args.output.open("xb") as output:
        output.write(encoded)
    print(json.dumps({"output": str(args.output), "bytes": len(encoded), "sha256": hashlib.sha256(encoded).hexdigest()}))
    return 2 if result.get("status") == "MISMATCH" else 0


if __name__ == "__main__":
    raise SystemExit(main())
