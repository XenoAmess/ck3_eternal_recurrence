#!/usr/bin/env python3
"""Verify current stock GOV identities against the file-only frozen inputs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

from verify_government_runtime_adapter_1_19_0_6 import extract_registry


def verify(game_root: Path) -> dict[str, object]:
    research = Path(__file__).resolve().parent
    contract = json.loads(
        (research / "government_runtime_adapter_1_20_0_2.json").read_text(encoding="utf-8")
    )
    for relative, identity in contract["source_files"].items():
        raw = (game_root / relative).read_bytes()
        if len(raw) != identity["size"] or hashlib.sha256(raw).hexdigest().upper() != identity["sha256"]:
            raise ValueError(f"current stock government source changed: {relative}")
    actual = extract_registry(game_root)
    if actual != contract["government_registry"]:
        raise ValueError("current stock government identity/AI inputs changed")
    if len(actual) != 18 or sum(len(row["flags"]) for row in actual) != 171:
        raise ValueError("current stock government identity cardinality changed")
    source = (research.parent / "src/government_runtime_adapter_observer_v1.cpp").read_text(encoding="utf-8")
    for index, row in enumerate(actual):
        match = re.search(rf"constexpr std::array kGovernmentFlags12002_{index}\{{(.*?)\n\}};", source, re.DOTALL)
        if match is None:
            raise ValueError(f"current GOV flag identity row missing: {row['key']}")
        flags = re.findall(r'std::string_view\{"([^\"]+)"\}', match.group(1))
        if flags != row["flags"]:
            raise ValueError(f"current GOV flag identity row differs: {row['key']}")
        if f'{{"{row["key"]}", kGovernmentFlags12002_{index},' not in source:
            raise ValueError(f"current GOV key/flags pairing differs: {row['key']}")
    return {
        "status": "GREEN",
        "game_version": "1.20.0.2",
        "stock_government_rows": 18,
        "flag_declarations": 171,
        "ck3_launched": False,
        "process_attached": False,
        "native_abi_evidence": "ck3_1_20_0_2_campaign.json (existing frozen proof reused)",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-root", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.game_root), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
