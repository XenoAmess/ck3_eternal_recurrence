"""Read-only admission of a sample inside a coordinator's combined grant."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import stat
import time


def _read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def _pin(path):
    path = Path(path).resolve()
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def _positive(value, label):
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(label + " must be a positive byte count")
    return value


def _allocated(root, allocation):
    """Bounded metadata scan of this sample only; no media hashing/decoding."""
    if not root.exists():
        return {"allocated_bytes": 0, "logical_bytes": 0, "files": 0, "entries": 0}
    total = logical = files = entries = 0
    stack = [root]
    started = time.monotonic()
    while stack:
        with os.scandir(stack.pop()) as items:
            for item in items:
                entries += 1
                if entries > 30000 or time.monotonic() - started > 45:
                    raise ValueError("Sample metadata scan exceeded its bound")
                observed = item.stat(follow_symlinks=False)
                if item.is_dir(follow_symlinks=False):
                    stack.append(Path(item.path))
                elif stat.S_ISREG(observed.st_mode):
                    info, error = allocation(Path(item.path))
                    if error is not None or info is None:
                        raise ValueError("Sample allocated size is unavailable: " + item.path)
                    total += max(observed.st_size, info["allocated"])
                    logical += observed.st_size
                    files += 1
                else:
                    raise ValueError("Sample scan encountered a nonregular entry")
    return {"allocated_bytes": total, "logical_bytes": logical, "files": files, "entries": entries}


def _admit(repo, ledger_path, package_root, output, machine, peak, allocation, provider_pin, *, now=None, disk_usage=None):
    now = now or datetime.now(timezone.utc)
    disk_usage = disk_usage or shutil.disk_usage
    ledger_path = Path(ledger_path).resolve()
    ledger = _read(ledger_path)
    if (ledger.get("schema") != "faith-e02-combined-production-admission-v1"
            or ledger.get("machine_id") != machine or ledger.get("active") is not True
            or datetime.fromisoformat(ledger["expires_at_utc"]) <= now):
        raise ValueError("An active same-machine combined production grant is required")
    root = Path(package_root).resolve()
    grant_root = Path(ledger["approved_root"]).resolve()
    target = Path(output).resolve()
    if root != grant_root / "sample" or not target.is_relative_to(root):
        raise ValueError("Sample root and output must match the coordinator grant")
    allocations = ledger["suballocations_bytes"]
    sample_cap = _positive(allocations["sample"], "Sample suballocation")
    combined_cap = _positive(ledger["this_write_peak_bytes"], "Combined grant")
    if (set(allocations) != {"native", "sample"}
            or sum(_positive(v, "Suballocation") for v in allocations.values()) != combined_cap):
        raise ValueError("Combined grant must preserve both named suballocations")
    peak = _positive(peak, "Concrete future render peak")
    used = _allocated(root, allocation)
    if used["allocated_bytes"] + peak > sample_cap:
        raise ValueError("Existing sample usage plus render peak exceeds its suballocation")
    policy_path = Path(repo) / "docs/storage-retention-policy.json"
    policy = _read(policy_path)
    if ledger["policy_version"] != policy["policy_version"]:
        raise ValueError("Grant and current common policy versions differ")
    disk = disk_usage(grant_root)
    cap = policy["capacity"]
    safety = math.ceil(max(cap["safety_floor_bytes"], min(cap["safety_ceiling_bytes"], disk.total * cap["safety_volume_fraction"])))
    other = ledger["other_unspent_reservations_upper_bytes"]
    system = _positive(ledger["system_growth_reserve_bytes"], "System growth reserve")
    if isinstance(other, bool) or not isinstance(other, int) or other < 0:
        raise ValueError("Other shared reservations must be a known byte count")
    if disk.total != ledger["volume_total_bytes"]:
        raise ValueError("Grant volume differs from the fresh volume observation")
    required = combined_cap + other + system + safety
    if disk.free < required:
        raise ValueError("Fresh shared free space cannot cover the complete concurrent grant")
    projected = ledger["project_usage_upper_bytes"] + combined_cap
    if projected > ledger["effective_project_quota_bytes"]:
        raise ValueError("Combined grant exceeds the project quota")
    return {
        "schema": "faith-e02-sample-shared-grant-admission-v1",
        "machine_id": machine, "observed_at_utc": now.isoformat(),
        "evidence_source": "Coordinator grant; current sample metadata and fresh shared-volume free space",
        "grant": _pin(ledger_path), "policy": _pin(policy_path), "allocation_reader": provider_pin,
        "package_root": str(root), "output": str(target), "sample_usage": used,
        "concrete_peak_new_bytes": peak, "sample_suballocation_bytes": sample_cap,
        "sample_remaining_after_render_peak_bytes": sample_cap - used["allocated_bytes"] - peak,
        "combined_grant_bytes": combined_cap, "other_unspent_reservations_upper_bytes": other,
        "system_growth_reserve_bytes": system, "safety_bytes": safety,
        "required_free_bytes": required, "disk": disk._asdict(),
        "projected_project_upper_bytes": projected, "effective_project_quota_bytes": ledger["effective_project_quota_bytes"],
        "capacity_passed": True, "quota_passed": True, "spent_refilled": False,
        "automatic_reservation_claimed": False, "render_started": False, "screen_or_game_access": False,
    }


def admit_v3(repo, ledger_path, package_root, output, machine, peak, allocation_reader):
    """Compatibility interface used by the existing formal renderer."""
    provider_path = Path(allocation_reader).resolve()
    spec = importlib.util.spec_from_file_location("faith_sample_allocation_reader", provider_path)
    provider = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(provider)
    return _admit(repo, ledger_path, package_root, output, machine, peak, provider.allocation, _pin(provider_path))
