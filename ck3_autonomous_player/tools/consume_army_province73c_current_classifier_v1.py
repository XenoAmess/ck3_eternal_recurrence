"""Run the sole FIRST compound against five future compiled whole result files."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wire-dir", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    project = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(project / "src"))
    sys.path.insert(0, str(project / "tests" / "unit"))
    from test_army_province73c_current_classifier_service import run_compound
    run_compound(args.wire_dir, args.receipt)
    print("GREEN: one FIRST compound, five compiled whole Army results, five production Service queries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
