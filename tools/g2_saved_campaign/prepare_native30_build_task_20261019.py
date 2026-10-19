"""Prepare one source-pinned Native30 Task spec; never register/run Scheduler."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[2]
OWNER_ROOT = Path("D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/p51-fresh1066-v20261019-prepare01/native30-build-owner01")
NATIVE_ROOT = Path("D:/codex-ck3-demos/2026-10-19-robert-v20261019-native30-camera01")
PRODUCER = REPO / "tools/g2_saved_campaign/build_native30_wholeclean_20261019.py"
PLAN = REPO / "docs/ck3-native-ai/evidence/native30-wholeclean-producer-plan-2026-10-19.json"
BOOT = REPO / "tools/g2_saved_campaign/interactive_task_owner_v1.py"
BOOT_SHA = "c0d76a7064996cafd7412f8f39ba2bb5c5cb6271627246b84e946c00bafb864f"
PRODUCER_SHA = "db51b7e5b37083cf803f4b1611dd714dec197f4e0c559a688d22781f2ef07c00"
PLAN_SHA = "d9a44fc874bd253425626712eb17131f6986de5db17b74c5200b53cea3932bdb"
COMMIT = "704bdd3362bdc282ed5f5f8cf31fd3f50b90d747"

def require(value, message):
    if not value: raise RuntimeError(message)
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--admission", type=Path, required=True)
    parser.add_argument("--admission-sha256", required=True)
    args = parser.parse_args()
    admission = args.admission.resolve()
    require(sha(admission) == args.admission_sha256, "admission SHA")
    card = json.loads(admission.read_bytes())
    machine = subprocess.check_output([sys.executable, "-B", str(REPO / "tools/ck3_live_run_id.py"),
                                       "machine"], text=True, timeout=15).strip()
    require(card["status"] == "ADMITTED" and card["machine_id"] == machine, "ADMITTED same machine")
    require(Path(card["root"]).resolve() == NATIVE_ROOT.resolve() and not NATIVE_ROOT.exists(), "Native root must remain absent")
    require(card["source_commit"] == COMMIT and card["hard_bytes"] == 1610612736 and
            card["source_charge_cap_bytes"] == 100663296, "exact final commit/caps")
    require(card["producer_sha256"] == PRODUCER_SHA == sha(PRODUCER) and
            card["plan_sha256"] == PLAN_SHA == sha(PLAN), "producer/plan source pins")
    require(sha(BOOT) == BOOT_SHA and not OWNER_ROOT.exists(), "bootstrap/owner create-only")
    spec = importlib.util.spec_from_file_location("native30_interactive_task_owner", BOOT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    OWNER_ROOT.mkdir(exist_ok=False)
    frozen = OWNER_ROOT / BOOT.name
    with frozen.open("xb") as output: output.write(BOOT.read_bytes())
    require(sha(frozen) == BOOT_SHA, "frozen bootstrap differs")
    stage_args = ["--plan", str(PLAN.resolve()), "--admission", str(admission),
                  "--admission-sha256", args.admission_sha256, "--execute"]
    result = module.prepare_spec(root=OWNER_ROOT / "owner-spec", role="native_build",
        stage=PRODUCER, stage_sha256=PRODUCER_SHA, bootstrap_path=frozen,
        cwd=REPO, machine_id=machine, stage_args=stage_args,
        admission_path=admission, admission_sha256=args.admission_sha256)
    result.update(source_commit=COMMIT, bootstrap_sha256=BOOT_SHA,
        prepared_utc=datetime.now(timezone.utc).isoformat(),
        Native_root_absent=not NATIVE_ROOT.exists(), registered=False, started=False)
    module.once(OWNER_ROOT / "PREPARED.json", result)
    print(json.dumps(result))

if __name__ == "__main__": main()
