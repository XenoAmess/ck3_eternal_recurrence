"""Finite functional09 metadata160 source amendment; old proof/ready stay exact."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[2]
FILES = ["tools/g2_saved_campaign/" + name + "_20261020.py" for name in
         ("native30_functional09", "test_native30_functional09", "seal_native30_functional09")]
FILES += ["docs/ck3-native-ai/evidence/native30-functional09-" + name + "-2026-10-20.json" for name in
          ("plan", "readonly-preflight", "source-ready", "metadata160-revision2")]
OLD_PROOF = "a9ffdac90a505a93503f233dad2ad4f1129cea55043ed38e79c4f8b2c7c3b811"
OLD_READY = "5850721f7ff43121e41398b0f943130b69f081326f39b5ddc3e89c2db3622d02"
OLD_PLAN = "7807026144c85e3fd93f66a5dd75edc45e62c8ce074f20b7a46539d28c396779"


def require(value, message):
    if not value:
        raise RuntimeError(message)


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def pin(path, data=None):
    path = Path(path)
    data = path.read_bytes() if data is None else data
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--source-card", type=Path, required=True)
    parser.add_argument("--source-card-sha256", required=True)
    parser.add_argument("--execute-source-seal", action="store_true")
    args = parser.parse_args()
    require(args.execute_source_seal, "explicit source amendment required")
    card_ref = pin(args.source_card)
    require(card_ref["sha256"] == args.source_card_sha256, "supplement SHA changed")
    card = json.loads(args.source_card.read_bytes())
    require(card["status"] == "SOURCE_AMENDMENT_ADMITTED_NOT_EXECUTION"
            and card["source_complete_hard_bytes"] == 73728 and card["additional_source_hold_bytes"] == 8192
            and card["new_functional09_metadata_charge_cap_bytes"] == 167772160,
            "Root-authorized complete72KiB/metadata160 amendment required")
    require(datetime.fromisoformat(card["review_at_utc"]) > datetime.now(timezone.utc), "source deadline expired")
    require(not (REPO / FILES[6]).exists(), "create-only v2 amendment")
    proof_ref, ready_ref, plan_ref = [pin(REPO / name) for name in FILES[4:6] + FILES[3:4]]
    require((proof_ref["sha256"], ready_ref["sha256"], plan_ref["sha256"]) == (OLD_PROOF, OLD_READY, OLD_PLAN),
            "first frozen proof/ready/plan pins changed")
    first = json.loads((REPO / FILES[5]).read_bytes())
    history = first["sources"] + [plan_ref, proof_ref, ready_ref]
    spec = importlib.util.spec_from_file_location("functional09_metadata160", REPO / FILES[0])
    F = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(F)
    plan = json.loads((REPO / FILES[3]).read_bytes())
    plan.update(metadata_revision=2, phase_metadata_cap_bytes=167772160, source_cap_bytes=73728,
                source_files=FILES, source_supplement=card_ref, producer=pin(REPO / FILES[0]))
    plan["execution_card_contract"]["metadata_charge_cap_bytes"] = 167772160
    plan["metadata160_contract"] = {
        "initial_readonly": "Unmodified borrowed Q.preflight retains stricter metadata128 plus16MiB reserve; failure grants no execution.",
        "actual_phase": "Independent FunctionalParentGuard160 replaces only new09 private state budget; its call never invokes old128. Complete root1.5GiB/source96/TEMP384 and new scope16MiB/owner64KiB unchanged.",
        "original08_metadata_quote_preserved": 131238080, "new09_complete_metadata_quote": 16777216,
        "combined_metadata_quote": 148015296, "phase_metadata_limit": 167772160}
    command = [sys.executable, "-B", str(REPO / FILES[1]),
        "Functional09Tests.test_metadata160_parent_boundaries_and_old128_are_independent",
        "Functional09Tests.test_new_metadata_includes_all_owner_files_and_uses_allocation"]
    tested = subprocess.run(command, cwd=REPO, capture_output=True, text=True)
    require(tested.returncode == 0, "targeted cap tests failed: " + tested.stderr)
    handles = []
    started = time.perf_counter()
    try:
        original = F.Q.finite_load(F.ROOT / "attempt08-build/RESULT.json")
        capacity_ref = original["admission"]
        require(pin(capacity_ref["path"]) == capacity_ref, "original inspection capacity changed")
        inspection = {**F.Q.finite_load(capacity_ref["path"]), "metadata_charge_cap_bytes": 167772160}
        state, snapshot, _, records, refs, _, bindings = F.collect_readonly(plan, inspection, handles)
        base = state["base"]
        require(card["machine_id"] == base.machine(), "same-machine amendment required")
        require(not F.STAGE.exists() and not F.OWNER.parent.exists(), "no functional/owner execution roots permitted")
        observed = {"machine_id": base.machine(), "utc": base.utc(), "seconds": time.perf_counter()-started,
            "source_count": len(state["rows"]), "selected_rows": len(state["current"]["selected_compile_rows"]),
            "targets": len(state["current"]["targets"]), "regen_inputs": len(state["manifest_inputs"]["inputs"]),
            "production_leases": len(state["pinned_outputs"]), "EXE_leases": len(bindings),
            "initial128_actual": state["initial_readonly_charges"], "private160_actual": state["budget"].last,
            "private160_guard": type(state["budget"]).__name__, "inspection_only_not_admission": True}
    finally:
        F.Q.close_handles(handles)
    plan_raw = encoded(plan)
    note = {"schema": "native30-functional09-metadata160-source-revision2-v1", "machine_id": observed["machine_id"],
        "observed_at_utc": observed["utc"], "status": "SOURCE_READY_ACTUAL_FIXTURES_NOTRUN", "source_card": card_ref,
        "first_six_frozen_refs": history,
        "history_rule": "First preflight/ready remain byte-identical. The other four source/plan paths now contain v2; first hashes are historical, not current byte pins. No Git archive or old source body availability is claimed.",
        "current_sources": [pin(REPO / name) for name in FILES[:3]], "plan": pin(REPO / FILES[3], plan_raw),
        "targeted_tests": {"command": command, "returncode": tested.returncode, "stderr": tested.stderr},
        "readonly160_reachability": observed, "initial128_more_restrictive_gate_preserved": True,
        "original08_sources_and_unknown_future_quote_unchanged": True, "prior_admin_future_writes": None,
        **F.FIELDS, "source_complete_hard_bytes": 73728, "first63702_charge_not_released": True,
        "future_source_writes": 0, "R_Task_UAC_settings_CPP_Game_or_EXE_execution": 0}
    note_raw = (json.dumps(note, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
    actual = sum((REPO / name).stat().st_size for name in FILES[:3] + FILES[4:6]) + len(plan_raw) + len(note_raw)
    charged = 63702 + sum(max(0, pin(REPO / name)["bytes"]-history[i]["bytes"]) for i,name in enumerate(FILES[:3]))
    charged += max(0,len(plan_raw)-plan_ref["bytes"]) + len(note_raw)
    require(max(actual,charged) <= 73728, "complete amended gross/retained charge exceeds72KiB: " + str((actual,charged)))
    (REPO / FILES[3]).write_bytes(plan_raw)
    with (REPO / FILES[6]).open("xb") as stream:
        stream.write(note_raw)
    require(pin(REPO / FILES[4]) == proof_ref and pin(REPO / FILES[5]) == ready_ref, "historical proof bytes changed")
    print(json.dumps({"actual_source_bytes": actual, "retained_charge_bytes": charged, "hard_bytes":73728,
        "files":[pin(REPO / name) for name in FILES], "future_source_writes":0, "actual_fixtures":0}))


if __name__ == "__main__":
    main()
