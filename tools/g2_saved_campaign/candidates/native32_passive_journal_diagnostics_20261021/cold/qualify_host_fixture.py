"""Validate an explicitly admitted single-TU host fixture."""
from __future__ import annotations
import argparse
from pathlib import Path
from test_observer_journal_v1 import verify_host_fixture_v1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--executable", type=Path, required=True)
    args = parser.parse_args()
    print("HOST_PRODUCER_CONSUMER_FRAMES", verify_host_fixture_v1(args.executable))
    print("runtime_admission_granted=false Game_calls=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
