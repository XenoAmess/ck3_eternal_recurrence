"""Queue one explicit recording request to the existing shared keeper process."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time


def pin(path):
    raw = Path(path).read_bytes()
    return {"path": str(Path(path).resolve()), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--keeper-root", type=Path, required=True)
    parser.add_argument("--live", type=Path, required=True)
    parser.add_argument("--id", required=True)
    parser.add_argument("--operation", choices=("start", "status", "mark", "finish", "abort"), required=True)
    parser.add_argument("--capture-name")
    parser.add_argument("--label")
    parser.add_argument("--native-receipt", type=Path)
    parser.add_argument("--timeout", type=float, default=30)
    parser.add_argument("--plan-only", action="store_true")
    args = parser.parse_args(argv)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,100}", args.id) or not 1 <= args.timeout <= 120:
        raise ValueError("Portable unique request ID and bounded wait required")
    request = {"schema": "ck3-mod-acceptance-recorder-request-v1", "id": args.id,
               "operation": args.operation, "live_root": str(args.live.resolve())}
    if args.capture_name: request["capture_name"] = args.capture_name
    if args.label: request["label"] = args.label
    if args.native_receipt: request["native_receipt"] = str(args.native_receipt.resolve())
    if args.plan_only:
        print(json.dumps({"status": "PLAN_ONLY_NO_SCREEN_ACTION", "request": request}, ensure_ascii=False, indent=2))
        return 0
    from ck3_mod_acceptance_keeper import live_lease, check_pin
    from ck3_mod_acceptance_launcher import frozen_run
    keeper = args.keeper_root.resolve()
    ready = json.loads((keeper / "recording-service-ready.json").read_text(encoding="utf-8"))
    check_pin(ready["configuration"]); check_pin(ready["service_source"])
    frozen, context = frozen_run(args.live, all_pins=True, input_phase="running")
    if Path(context["keeper_root"]).resolve() != keeper or ready["screen_task"] != frozen["screen_task"]:
        raise ValueError("Actual allocated keeper and recording service differ")
    live_lease(keeper, frozen)
    target = keeper / "recorder-requests" / (args.id + ".json")
    response = keeper / "recorder-responses" / target.name
    if target.exists() or response.exists():
        raise FileExistsError("Recorder request already consumed or its outcome is unknown; inspect existing response, never replay")
    pending = target.with_suffix(".pending")
    with pending.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(request, handle, ensure_ascii=False, indent=2)
        handle.write("\n"); handle.flush(); os.fsync(handle.fileno())
    pending.rename(target)
    deadline = time.monotonic() + args.timeout
    while not response.exists():
        if time.monotonic() >= deadline:
            print(json.dumps({"status": "OUTCOME_UNKNOWN_DO_NOT_REPLAY", "machine_id": ready["machine_id"],
                              "observed_at_utc": datetime.now(timezone.utc).isoformat(),
                              "evidence_source": "published exact recording request; response not observed before deadline",
                              "request": pin(target), "expected_response": str(response)}, ensure_ascii=False))
            return 2
        time.sleep(.1)
    answer = json.loads(response.read_text(encoding="utf-8"))
    if answer["request"] != pin(target):
        raise ValueError("Recorder response does not bind the exact original request")
    print(json.dumps(answer, ensure_ascii=False, indent=2))
    return 0 if answer.get("status") == "CALL_COMPLETED_ACK_NOT_CLEAN" else 2


if __name__ == "__main__":
    raise SystemExit(main())
