"""Print a read-only pilot/evidence index, optionally intake real capture files."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from faith_power_promo.evidence import build_evidence_index


def observer():
    probe = [sys.executable, "-B", str(ROOT / "tools/ck3_live_run_id.py"), "machine"]
    machine_id = subprocess.run(probe, check=True, capture_output=True, text=True).stdout.strip()
    return {"machine_id": machine_id, "observed_at_utc": datetime.now(timezone.utc).isoformat(),
            "evidence_source": "tools/ck3_live_run_id.py machine; read-only file byte inspection"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=Path(__file__).resolve().parent.parent / "pilot-plan.json")
    parser.add_argument("--intake", type=Path, action="append", default=[])
    args = parser.parse_args()
    print(json.dumps(build_evidence_index(args.plan, args.intake, observer=observer()),
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
