"""Read new same-run d26/d27 native checkpoints; never launch CK3 or close old a02."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

SOURCE_SHA = "C1276153435766A875B0984F1A3AD426CB3AFCFB6EC33061CEE6650538CFFD2B"
SOURCE_RECEIPT_SHA = "78931511D31E8400334D28DAD276F4CCDFBB342A901FC00B0BAFDCDEDA29584C"
RAKALY_SHA = "E154AF990AAED2C2F44284946772188C9749AD3F6B641B41F6C23456A6F1633D"
TARGET, ACTOR, BEFORE, AFTER = 33437, 29829, 53146848, 53146872
NEW_RUN_PARENT = Path("C:/Users/1/AppData/Local/ck3-capture-preparation")
NEW_RUN_PREFIX = "episode02-e2-05-d26-nextday-live-"

def identity(p):
    p = Path(p).resolve()
    with p.open("rb") as stream:
        sha = hashlib.file_digest(stream, "sha256").hexdigest().upper()
    return {"path": str(p), "bytes": p.stat().st_size, "sha256": sha}

def read(p):
    return json.loads(Path(p).read_text(encoding="utf-8-sig"))

def require(ok, reason):
    if not ok:
        raise ValueError(reason)

def classify_life_state(state):
    alive, dead = state.get("alive_data_present"), state.get("dead_data_present")
    require(type(alive) is bool and type(dead) is bool and alive != dead,
            "After-state has no unique alive_data XOR dead_data; status remains UNKNOWN")
    return "DEAD" if dead else "ALIVE"

def body(p):
    row = read(p)
    require(row.get("result") == "CALL_COMPLETED" and isinstance(row.get("body"), dict),
            f"Incomplete native response: {p}")
    return row, row["body"]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("new-run-root", "source-save", "source-receipt", "preflight", "readback",
                 "before-save", "before-save-receipt", "before-snapshot",
                 "after-save", "after-save-receipt", "after-snapshot", "rakaly-exe", "parser-source", "output"):
        parser.add_argument("--" + name, required=True, type=Path)
    parser.add_argument("--parser-sha256", required=True)
    parser.add_argument("--expected-episode-run-id", required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    receipt = {"schema": "ck3.new-run.knight-saved-nextday-status.v1",
               "created_at_utc": datetime.now(timezone.utc).isoformat(),
               "status": "UNKNOWN", "live_targeted_query": False, "old_a02_status": "UNKNOWN",
               "ck3_launches": 0, "desktop_inputs": 0, "target_character_id": TARGET,
               "interpreter": {"path": sys.executable, "version": sys.version}}
    try:
        root = args.new_run_root.resolve()
        # Only this newly named capture root may supply run evidence. All old
        # historical material and failed a02 keep their original conclusions.
        require(root.parent == NEW_RUN_PARENT.resolve() and root.name.startswith(NEW_RUN_PREFIX)
                and all(not path.is_symlink() for path in (root, *root.parents)),
                "Use the new admitted e2-05-d26 nextday capture root named by capture-nextday-plan.json")
        for name in ("preflight", "readback", "before_save", "before_save_receipt", "before_snapshot",
                     "after_save", "after_save_receipt", "after_snapshot"):
            p = getattr(args, name).resolve()
            require(p.is_relative_to(root), f"Foreign/old run evidence supplied as {name}: {p}")
        require(identity(args.source_save)["sha256"] == SOURCE_SHA and
                identity(args.source_receipt)["sha256"] == SOURCE_RECEIPT_SHA, "Different frozen d26 source pair")
        preflight, readback = read(args.preflight), read(args.readback)
        for key, src in (("preflight", preflight.get("checkpoint_source", {})),
                         ("readback", readback.get("source_checkpoint", {}))):
            require(src.get("save", {}).get("sha256", "").upper() == SOURCE_SHA and
                    src.get("receipt", {}).get("sha256", "").upper() == SOURCE_RECEIPT_SHA and
                    src.get("actor") == ACTOR and src.get("date_raw") == BEFORE, f"Unbound {key} input identity")
        require(preflight.get("result") == "READY_FOR_BOUNDED_LIVE_ATTEMPT" and
                readback.get("postcondition_verified") is True, "Source native load not confirmed")
        before_row, before = body(args.before_save_receipt)
        after_row, after = body(args.after_save_receipt)
        for label, val, save, date in (("before", before, args.before_save, BEFORE),
                                      ("after", after, args.after_save, AFTER)):
            checkpoint = val.get("checkpoint", {})
            require(val.get("accepted") is True and checkpoint.get("status") == "saved" and
                    checkpoint.get("date_raw") == date and checkpoint.get("episode_character_id") == ACTOR and
                    checkpoint.get("episode_run_id") == args.expected_episode_run_id,
                    f"{label} checkpoint is not the declared new same-run actor/date")
            actual = identity(save)
            require(actual["bytes"] == checkpoint.get("size") and
                    actual["sha256"] == checkpoint.get("sha256", "").upper(), f"{label} immutable bytes differ from native receipt")
        before_snap_row, before_snap = body(args.before_snapshot)
        after_snap_row, after_snap = body(args.after_snapshot)
        for label, snap, save_row, date in (("before", before_snap, before_row, BEFORE),
                                           ("after", after_snap, after_row, AFTER)):
            require(snap.get("paused") is True and snap.get("date_raw") == date and
                    snap.get("played_character", {}).get("character_id") == ACTOR and
                    isinstance(snap.get("revision"), int), f"{label} snapshot is not a paused target date")
            req = read(save_row["request"]["path"])
            require(req.get("tool") == "ck3_save_checkpoint" and
                    req.get("arguments", {}).get("expected_revision") == snap["revision"],
                    f"{label} save request is not bound to paused snapshot revision")
        drivers = [r.get("driver_state", {}) for r in (before_row, after_row, before_snap_row, after_snap_row)]
        tokens = [tuple(d.get(k) for k in ("pipe_name", "connection_generation", "bridge_pid")) for d in drivers]
        require(all(all(x is not None for x in token) for token in tokens) and len(set(tokens)) == 1,
                "Before/after receipts are not one native connection/PID")
        require(identity(args.rakaly_exe)["sha256"] == RAKALY_SHA, "Rakaly differs from pinned 0.8.19 bytes")
        require(identity(args.parser_source)["sha256"] == args.parser_sha256.upper(), "Frozen parser source changed")
        spec = importlib.util.spec_from_file_location("frozen_phase_save_reader", args.parser_source)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        states = []
        for label, source in (("before", args.before_save), ("after", args.after_save)):
            melted = out / f"{label}-melted.ck3"
            argv = [str(args.rakaly_exe), "melt", str(source), "--unknown-key", "stringify", "--format", "ck3", "--out", str(melted)]
            (out / f"{label}-melt-command.json").write_text(json.dumps({"argv": argv}, indent=2), encoding="utf-8")
            with (out / f"{label}-melt.stdout.log").open("wb") as stdout, (out / f"{label}-melt.stderr.log").open("wb") as stderr:
                completed = subprocess.run(argv, stdout=stdout, stderr=stderr, check=False)
            require(completed.returncode == 0 and melted.is_file(), f"{label} pinned Rakaly failed; process materials retained")
            state = module._character_snapshot(melted.read_text(encoding="utf-8-sig"), TARGET)
            states.append({"save": identity(source), "melted": identity(melted), "state": state})
        require(states[0]["state"]["alive_data_present"] is True and
                states[0]["state"]["dead_data_present"] is False, "New d26 target before-state is not uniquely alive")
        status = classify_life_state(states[1]["state"])
        receipt.update(status="SAVED_NEXTDAY_STATUS_OBSERVED", saved_nextday_status=status,
                       states=states, native_connection=tokens[0], expected_episode_run_id=args.expected_episode_run_id,
                       source_input={"save":identity(args.source_save), "receipt":identity(args.source_receipt)},
                       evidence={name:identity(getattr(args, name)) for name in (
                           "preflight", "readback", "before_save_receipt", "before_snapshot", "after_save_receipt", "after_snapshot")},
                       parser=identity(args.parser_source), rakaly=identity(args.rakaly_exe),
                       limits=["saved-state reading; not a same-frame live CharacterID query", "does not establish selector choice or sole death causation", "does not overwrite failed a02"])
        code = 0
    except Exception as exc:
        receipt.update(error=f"{type(exc).__name__}: {exc}")
        code = 2
    with (out / "saved-status-receipt.json").open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(receipt, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"receipt": str(out / "saved-status-receipt.json"), "status": receipt["status"], "error": receipt.get("error")}, ensure_ascii=False))
    return code

if __name__ == "__main__":
    raise SystemExit(main())
