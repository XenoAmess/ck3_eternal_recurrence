"""Offline exact-build literal locator for retreat-score role research.

Literal matches are locator evidence only, not verified function semantics.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

import pefile

EXPECTED = "2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--needle", action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = args.exe.read_bytes()
    if hashlib.sha256(data).hexdigest() != EXPECTED:
        raise ValueError("exact EXE mismatch")
    pe = pefile.PE(data=data, fast_load=True)
    needles = [value.encode("ascii") for value in args.needle]
    rows = []
    for match in re.finditer(rb"[\x20-\x7e]{4,}\x00", data):
        value = match.group()[:-1]
        if any(needle in value for needle in needles):
            rows.append({"rva": hex(pe.get_rva_from_offset(match.start())),
                         "file_offset": match.start(), "literal": value.decode("ascii")})
    result = {"schema": "xar.war-film-retreat-score-literals.v1", "proof_layer": "exact-build-literal-locator",
              "exe_sha256": EXPECTED, "exe": str(args.exe.resolve()), "argv": sys.argv,
              "live_execution_performed": False, "semantic_correctness_verified": False, "literals": rows}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, indent=2); stream.write("\n")
    print(json.dumps({"output": str(args.output), "literal_count": len(rows),
                      "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest()}, indent=2))


if __name__ == "__main__":
    main()
