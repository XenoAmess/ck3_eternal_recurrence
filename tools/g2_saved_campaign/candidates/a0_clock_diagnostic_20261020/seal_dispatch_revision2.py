"""Append source-pin correction; preserve original PLAN/READY and 10-pass fact."""
from datetime import datetime, timezone
import json
from pathlib import Path

import seal_source as source

ROOT = Path(__file__).resolve().parent


def main():
    target = ROOT / "ERROR-DISPATCH-REVISION2.json"
    if target.exists():
        raise FileExistsError(target)
    document = {
        "schema": "xar.a0-exact-clock-error-dispatch-correction/v2",
        "status": "SOURCE_READY_NOT_ADOPTED", "machine_id": source.MACHINE,
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "prior_ready": source.ref(ROOT / "SOURCE-READY.json"),
        "prior_plan": source.ref(ROOT / "PLAN.json"),
        "reason": "Root/performance_python found schema/message matching did not explicitly require the actual StepPostconditionError and selected step.",
        "change": "Extractor now requires actual .driver.StepPostconditionError, selected_step life-advance-one-day and exactly the fixed DTO top-level keys; only that allowlist is isolated for MCP.",
        "unchanged": "Driver/MCP candidate bytes, original text/cause, call order, cleanup and every normal/other error route; current SDK/Queue not adopted or modified.",
        "updated_pins": [source.ref(ROOT / path) for path in (
            "xar_autoplayer/bridge/exact_clock_failure_diagnostic_v1.py", "test_candidate.py",
            "test_error_dispatch_revision2.py", "seal_dispatch_revision2.py")],
        "tests": {"command": "py -B tools/g2_saved_campaign/candidates/a0_clock_diagnostic_20261020/test_error_dispatch_revision2.py",
                  "passed": 2, "failed": 0, "unittest_duration_seconds": 0.0,
                  "actual_output": "exec fee2e9; command wall0.1241189s",
                  "cases": ["foreign actual BridgeUnavailableError rejected without mutation",
                            "wrong selected step rejected; expected typed object accepted/isolated; extra DTO key rejected"],
                  "prior_10_not_rerun": True},
        "original_10_pass_only_applies_to_prior_helper": True,
        "full_logical_bytes_including_this_addendum": 0, "hard_bytes": 2097152,
        "allocated_bytes": None, "future_writes": 0, "owned_children": 0,
        "Native_RPC_Game_SDK_adoption": "NOTRUN", "physical_credit_bytes": 0,
    }
    total = sum(p.stat().st_size for p in ROOT.rglob("*") if p.is_file())
    for _ in range(4):
        document["full_logical_bytes_including_this_addendum"] = total + len(source.encode(document))
    source.write_new(target, source.encode(document))
    print(json.dumps({"correction": source.ref(target), "full_logical_bytes": document["full_logical_bytes_including_this_addendum"],
                      "helper": document["updated_pins"][0], "future_writes": 0}, indent=2))


if __name__ == "__main__":
    main()
