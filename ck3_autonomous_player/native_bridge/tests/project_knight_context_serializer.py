"""Project literal production serializer functions for one offline native test.

The generated TU calls the current bridge.cpp function bodies rather than a
fixture reimplementation. It is not part of the bridge DLL or a game runtime.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def literal_function(source: str, name: str) -> str:
    start = source.index(name + "(")
    start = source.rfind("\n", 0, start) + 1
    position = source.index("{", start) + 1
    depth = 1
    quote = None
    while depth:
        character = source[position]
        if quote:
            if character == "\\":
                position += 2
                continue
            if character == quote:
                quote = None
        elif source.startswith("//", position):
            position = source.index("\n", position)
            continue
        elif source.startswith("/*", position):
            position = source.index("*/", position) + 2
            continue
        elif character in ('"', "'"):
            quote = character
        elif character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
        position += 1
    return source[start:position] + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    source_bytes = args.source.read_bytes()
    source = source_bytes.decode("utf-8-sig")
    names = ("SignedNumber", "AppendJsonString", "AppendUnavailableReason", "AppendCombatKnights")
    functions = {name: literal_function(source, name) for name in names}
    output = (
        '#include "xar_bridge/game_contract.hpp"\n'
        '#include <array>\n#include <charconv>\n#include <cstdint>\n'
        '#include <string>\n#include <string_view>\n#include <system_error>\n'
        'namespace knight_context_wire {\n' + "\n".join(functions.values()) +
        '\nstd::string SerializeKnights(const xar::game::CombatKnightsSnapshot &value) {\n'
        '  std::string result; AppendCombatKnights(result, value); return result;\n}\n}\n'
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(output, encoding="utf-8", newline="\n")
    receipt = {
        "schema": "knight_context_native_serializer_projection_v1",
        "source": str(args.source),
        "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "literal_function_sha256": {
            name: hashlib.sha256(body.encode("utf-8")).hexdigest()
            for name, body in functions.items()
        },
        "generated_source": str(args.output),
        "generated_sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(),
        "value_origin": "literal production serializer source; no CK3 operation",
    }
    args.receipt.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
