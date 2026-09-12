#!/usr/bin/env python3
"""Render the GEN-034 repository strategy budget or one operator override."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys


RESEARCH_ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = RESEARCH_ROOT.parents[2]
PACKAGE_ROOT = REPOSITORY_ROOT / "ck3_autonomous_player" / "src"
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from xar_autoplayer.simulation.raiktor_owner_budget_profile_provider import (  # noqa: E402
    provide_raiktor_owner_budget_profile,
)


OUTPUT_SCHEMA = "xar.ck3.g2_strategy_budget_profile_receipt.v1"


def render_receipt(source_path: Path | None) -> dict[str, object]:
    provider = provide_raiktor_owner_budget_profile(source_path)
    return {
        "schema": OUTPUT_SCHEMA,
        "status": "GREEN",
        "ok": True,
        "provider_result": provider,
        "boundaries": {
            "ck3_started_or_attached": False,
            "bridge_queried": False,
            "mutation_commands": [],
            "campaign_evidence_supplied": False,
            "white_peace_evidence_supplied": False,
            "action_authorized": False,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        help="complete versioned operator override; omit for repository default",
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    output = args.output.resolve()
    if output.exists():
        parser.error(f"output already exists: {output}")
    try:
        receipt = render_receipt(args.source)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + ".tmp")
    temporary.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, output)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
