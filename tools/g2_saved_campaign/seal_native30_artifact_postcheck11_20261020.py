"""Seal only the three-test RAM repair. No prior full preflight or R writes."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

import native30_artifact_postcheck11_20261020 as wrapper

REPO = wrapper.REPO
DOC = REPO / "docs/ck3-native-ai/evidence"
PLAN = DOC / "native30-artifact-postcheck11-plan-2026-10-20.json"
READY = DOC / "native30-artifact-postcheck11-source-ready-2026-10-20.json"
CARD = Path("D:/codex-ck3-demos/2026-10-19-robert-v20261019-storage01/C22-RUNTIME12MiB-BUDGET-CI8KiB-NATIVE11-SOURCE32KiB-ADMITTED01.json")
ROOT = Path("D:/codex-ck3-demos/2026-10-19-robert-v20261019-native30-camera01")
FILES = ["tools/g2_saved_campaign/" + name for name in (
    "native30_artifact_postcheck11_20261020.py", "test_native30_artifact_postcheck11_20261020.py",
    "seal_native30_artifact_postcheck11_20261020.py")] + [p.relative_to(REPO).as_posix() for p in (PLAN, READY)]


def pin(path):
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def encode(body):
    return (json.dumps(body, indent=2) + "\n").encode()


def create(path, body):
    data = encode(body)
    current = sum((REPO / p).stat().st_size for p in FILES if (REPO / p).exists())
    if current + len(data) > 32768:
        raise ValueError("complete source32KiB")
    with path.open("xb") as output:
        output.write(data)


def main():
    if PLAN.exists() or READY.exists():
        raise FileExistsError("source seal already consumed")
    if pin(CARD)["sha256"] != "5e693d1218b8dc121500ce53584e48a1b861a837b3695375a5b2a642b7131f71":
        raise ValueError("source card pin")
    machine = subprocess.check_output(["py", "-B", str(REPO / "tools/ck3_live_run_id.py"), "machine"], text=True).strip()
    if machine != "xenoamess-full-tower-eb9d2c1186":
        raise ValueError("machine mismatch")
    before, generated = wrapper.base_bytes(), wrapper.generated_bytes()
    compile(generated, str(Path(wrapper.__file__).resolve()), "exec")
    if wrapper.transform(generated, reverse=True) != before:
        raise ValueError("full inverse")
    if (ROOT / "attempt11-artifact-postcheck").exists() or (ROOT / "owner11-artifact").exists():
        raise FileExistsError("new actual roots must stay absent")
    closed10 = ROOT / "owner10-artifact/FINAL-CLOSED-SUMMARY.json"
    if pin(closed10)["sha256"] != "489b4c51601afd63bca331fac105643f251e49249d39637076647ecde7a01f0a":
        raise ValueError("old10 FAILED closure binding")
    base_plan = DOC / "native30-artifact-postcheck10-plan-revision2-2026-10-20.json"
    old_plan = json.loads(base_plan.read_bytes())
    if pin(base_plan)["sha256"] != "f305087ccb481960ebce8c7c13b8179b48629979787515e006077a428d97045d":
        raise ValueError("old plan")
    now = datetime.now(timezone.utc).isoformat()
    plan = {"schema": "native30-artifact-postcheck11-plan-v1", "status": "SOURCE_ONLY_NOT_EXECUTION_ADMISSION",
        "machine_id": machine, "observed_at_utc": now, "source_commit": "704bdd3362bdc282ed5f5f8cf31fd3f50b90d747",
        "producer": pin(Path(wrapper.__file__)), "source_files": FILES, "source_card": pin(CARD),
        "base_contract": pin(base_plan), "original10_FAILED": pin(closed10),
        "base_input": {"git_commit": wrapper.BASE_COMMIT, "git_path": wrapper.BASE_PATH,
                       "bytes": len(before), "sha256": wrapper.BASE_SHA, "disk_copy_written": False},
        "RAM_generated": {"bytes": len(generated), "sha256": hashlib.sha256(generated).hexdigest(),
                          "full_inverse_to_original10": True, "hunks": list(wrapper.EDITS)},
        "identity_contract": "The actual c0 stage is the wrapper with its own file SHA/FileID. RAM source is compiled under this real wrapper path and separate namespace. No fake Path, source file, shared-module or guard monkeypatch.",
        "change_scope": "Only namespace stage/owner/plan/module10 to11 and owned+reserve<=8MiB to owned<=8MiB. Same latest=budget(reserve) and all Native10 artifact/source/9closed-fact checks retained byte-for-byte.",
        "units": {"parent_reserve": "run_owned default64MiB remains solely in aggregate1.5GiB and free-floor checks",
                  "local8MiB": "new stage+whole owner outputs charged max(EOF,AllocationSize), no extra parent slack added"},
        "roots": {"aggregate": str(ROOT), "postcheck": str(ROOT / "attempt11-artifact-postcheck"),
                  "owner": str(ROOT / "owner11-artifact/owner-spec")},
        "caps": {"source_complete": 32768, "aggregate": 1610612736, "sourceR": 100663296,
                 "metadata": 167772160, "TEMP": 402653184, "new_metadata_including_owner": 8388608, "owner": 65536},
        "metadata_quote": {"old08_full": 131238080, "old08_admin_future_writes": None,
            "old09_full": 16777216, "old10_full": 8388608, "new11_full": 8388608, "combined": 164792512},
        "future_stage_args": ["--plan", str(PLAN), "--admission", "<new exact card>", "--admission-sha256", "<fullSHA>", "--execute"],
        "ledger_facts": {"10_outer_failed_normally_Job0_Task_absent": True,
            "10_inner_owned_and_future": None, "10_commands_journal": "[{}], no command started",
            "10_failure": "Parent64MiB guard passed; incorrect repeated64MiB addition into local8MiB rejected before OwnedJob.",
            "10_before_failure_local_counter": None},
        "software_tests": {"passed": 3, "failed": 0, "unittest_seconds": 0.275, "output": "67cb4b",
            "cases": ["64MiB parent reserve preserved and small local accepted", "local>8MiB rejected", "parent error same object/full RAM inverse"]},
        "no_repeated_work": ["no09nineEXE", "no full input preflight rerun", "no old6/other matrix", "no build/UAC/Game/SDK"],
        "qualification": "Same independent artifact-only Native10 protocol;09/10 FAILED stay FAILED; Defender_pending/OSunknown/GameH NOTRUN/deployedfalse.",
        "future_writes": 0, "allocated_bytes": None, "physical_credit_bytes": 0}
    create(PLAN, plan)
    refs = [pin(REPO / p) for p in FILES if p != READY.relative_to(REPO).as_posix()]
    ready = {"schema": "native30-artifact-postcheck11-source-ready-v1", "machine_id": machine,
        "observed_at_utc": now, "status": "SOURCE_READY_NOT_EXECUTED", "plan": pin(PLAN),
        "files_excluding_this_ready": refs, "full_logical_bytes": 0, "hard_bytes": 32768,
        "tests": plan["software_tests"], "full_inverse": True, "generated_syntax": True,
        "future_writes": 0, "allocated_bytes": None, "owned_children": 0, "physical_credit_bytes": 0}
    for _ in range(4):
        ready["full_logical_bytes"] = sum(v["bytes"] for v in refs) + len(encode(ready))
    create(READY, ready)
    print(json.dumps({"plan": pin(PLAN), "ready": pin(READY), "RAM_generated": plan["RAM_generated"]["sha256"],
                      "full_logical_bytes": ready["full_logical_bytes"], "future_writes": 0}, indent=2))


if __name__ == "__main__":
    main()
