"""Bounded read-only retention inspection. This command never deletes assets.

Machine profile and asset ledger are explicit local inputs; the repository policy
is the shared authority. Scheduling this command does not install automatic GC.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

MAX_INPUT = 1024 * 1024
REPO = Path(__file__).resolve().parents[1]


def utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("An explicit UTC offset is required")
    return parsed.astimezone(timezone.utc)


def small_json(path: Path):
    if path.stat().st_size > MAX_INPUT:
        raise ValueError(f"Input exceeds 1 MiB: {path}")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def evaluate_asset(asset: dict, policy: dict, observed: datetime) -> dict:
    result = {"asset_id": asset.get("asset_id"), "replica_id": asset.get("replica_id")}
    if asset.get("availability") in ("deleted", "deleted_unavailable"):
        return {**result, "state": "already_unavailable"}
    category = asset.get("category")
    if category not in policy["defaults"]:
        return {**result, "state": "unknown", "reason": "Unknown asset category"}
    if not isinstance(asset.get("active_references"), list):
        return {**result, "state": "unknown", "reason": "Current references not recorded"}
    if asset["active_references"]:
        return {**result, "state": "current_use", "references": asset["active_references"]}
    protection = asset.get("protected_until_utc_or_null")
    if protection:
        until = utc(protection)
        if until > observed:
            approved = asset.get("protection_approved_at_utc")
            if not approved or until - utc(approved) > timedelta(hours=policy["lifecycle"]["protection_max_hours"]):
                return {**result, "state": "unknown", "reason": "Protection approval or duration is invalid"}
            return {**result, "state": "protected", "until_utc": until.isoformat()}
    closed = asset.get("closed_at_utc_or_null")
    used = asset.get("last_used_at_utc")
    if not closed or not used:
        return {**result, "state": "unknown", "reason": "Closure or actual last use is unknown"}
    if asset.get("state") not in ("closed", "superseded", "abandoned", "closed_and_superseded"):
        return {**result, "state": "unknown", "reason": "Task not explicitly closed or abandoned"}
    expires = max(utc(closed), utc(used)) + timedelta(hours=policy["defaults"][category]["ttl_hours"])
    reason = asset.get("early_reclamation_reason")
    due = observed >= expires or bool(reason)
    state = "review_due" if due else "within_retention"
    if category == "record" and due:
        state = "record_consolidation_review_due"
    return {**result, "state": state, "policy_expiry_utc": expires.isoformat(), "early_reclamation_reason": reason,
            "deletion_authorized": False, "next_action": "Review ownership, exact current paths, sources, protection, file identity and OS handles before any separate reclamation"}


@contextmanager
def local_lock(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as stream:
        stream.seek(0, 2)
        if stream.tell() == 0:
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == "nt":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def inspect(profile: dict, ledger: dict, policy: dict, machine: str, observed: datetime) -> dict:
    if profile["machine_id"] != machine or ledger["machine_id"] != machine:
        raise ValueError("Machine ID does not match actual execution machine")
    if profile["policy_version"] != policy["policy_version"] or ledger["policy_version"] != policy["policy_version"]:
        raise ValueError("Machine profile/ledger policy version differs")
    roots = {key: Path(value).resolve() for key, value in profile["project_root_map"].items()}
    groups = ledger["asset_groups"]
    if len(groups) > policy["execution"]["inventory_max_entries"]:
        raise ValueError("Asset count exceeds the shared bounded inspection limit")
    outcomes = []
    for asset in groups:
        if asset.get("machine_id") != machine:
            raise ValueError("Asset belongs to a different or unknown machine")
        root = roots.get(asset.get("root_id"))
        relative = Path(asset.get("relative_path", ""))
        if root is None or relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Asset path is outside the approved root map")
        full = root / relative
        # Resolve does not read file contents. Ancestor links cannot extend scope.
        if not full.resolve().is_relative_to(root):
            raise ValueError("Resolved asset escapes its approved root")
        outcomes.append(evaluate_asset(asset, policy, observed))
    volumes = {}
    for volume, inputs in profile["volume_map"].items():
        usage = shutil.disk_usage(volume)
        cap = policy["capacity"]
        safety = int(max(cap["safety_floor_bytes"], min(cap["safety_ceiling_bytes"], usage.total * cap["safety_volume_fraction"])))
        missing = [key for key in ("system_growth_reserve_bytes", "other_unspent_reservations_bytes", "current_project_usage_bytes", "effective_project_quota_bytes") if inputs.get(key) is None]
        volumes[volume] = {"total_bytes": usage.total, "free_bytes": usage.free, "safety_bytes": safety,
                           "budget_missing_inputs": missing, "heavy_write_admission": "NOT_GRANTED",
                           "low_space": None if inputs.get("system_growth_reserve_bytes") is None else usage.free < safety + inputs["system_growth_reserve_bytes"]}
    counts = {}
    for row in outcomes:
        counts[row["state"]] = counts.get(row["state"], 0) + 1
    return {"schema": "xar.storage-retention-inspection.v1", "machine_id": machine, "observed_at_utc": observed.isoformat(),
            "policy_version": policy["policy_version"], "asset_groups": len(groups), "counts": counts, "outcomes": outcomes,
            "volumes": volumes, "deletions": 0, "automatic_gc_deployed_by_this_tool": False,
            "boundary": "Only explicit ledger groups inspected; unlisted files/roots are UNKNOWN. No content scan, deletion, quota extension, capacity reservation, schedule installation or remote-machine claim."}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--ledger", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--trigger", choices=("daily", "low-space", "task-start", "before-heavy-write", "task-close"), default="daily")
    args = parser.parse_args(argv)
    policy = small_json(REPO / "docs/storage-retention-policy.json")
    profile, ledger = small_json(args.profile), small_json(args.ledger)
    probe_python = Path(sys.executable)
    if probe_python.name.lower() == "pythonw.exe":
        probe_python = probe_python.with_name("python.exe")
    probe = subprocess.run([str(probe_python), "-B", str(REPO / "tools/ck3_live_run_id.py"), "machine"], capture_output=True, text=True, check=True,
                           creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    machine = probe.stdout.strip()
    observed = datetime.now(timezone.utc)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with local_lock(args.output_dir / "inspection.lock"):
        state_path = args.output_dir / "daily-state.json"
        state = small_json(state_path) if state_path.exists() else {}
        if args.trigger == "daily" and state.get("machine_id") == machine and state.get("last_daily_date_utc") == observed.date().isoformat():
            print(json.dumps({"machine_id": machine, "state": "daily_inspection_already_recorded", "last_report": state.get("last_daily_report")}))
            return 0
        report = inspect(profile, ledger, policy, machine, observed)
        report["trigger"] = args.trigger
        report["input_pins"] = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (args.profile, args.ledger, REPO / "docs/storage-retention-policy.json")}
        encoded = (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        if len(encoded) > policy["execution"]["inventory_report_max_bytes"]:
            raise ValueError("Report exceeds the shared 1 MiB limit")
        out = args.output_dir / (observed.strftime("%Y%m%dT%H%M%S%fZ") + "-" + args.trigger + ".json")
        with out.open("xb") as stream:
            stream.write(encoded)
        if args.trigger == "daily":
            state = {"machine_id": machine, "last_daily_date_utc": observed.date().isoformat(), "last_daily_report": str(out)}
            state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"machine_id": machine, "report": str(out), "counts": report["counts"], "deletions": 0}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        # pythonw has no console; preserve a small, explicit failure receipt.
        if "--output-dir" in sys.argv:
            directory = Path(sys.argv[sys.argv.index("--output-dir") + 1])
            directory.mkdir(parents=True, exist_ok=True)
            observed = datetime.now(timezone.utc)
            failure = {"schema": "xar.storage-retention-inspection-failure.v1", "machine_id": "unknown",
                       "observed_at_utc": observed.isoformat(), "error": str(error), "deletions": 0,
                       "identity_boundary": "Inspection failed before a successful machine-bound result; no machine fact is certified."}
            with (directory / (observed.strftime("%Y%m%dT%H%M%S%fZ") + "-FAILED.json")).open("x", encoding="utf-8") as stream:
                json.dump(failure, stream, ensure_ascii=False, indent=2)
        if sys.stderr is not None:
            print(str(error), file=sys.stderr)
        raise SystemExit(1)
