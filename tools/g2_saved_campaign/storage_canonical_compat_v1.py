"""Pure compatibility composition for one complete runtime storage admission.

The coordinator supplies explicit current capacity and full-hold provenance.
This helper neither measures capacity nor grants storage or runtime authority.
Prepare-only cards never replace the immutable running canonical admission.
"""
from __future__ import annotations

import copy
from datetime import datetime, timedelta
from decimal import Decimal
import hashlib
import json
from pathlib import PureWindowsPath

SCHEMA = "xar.robert30year.storage-admission.v1"
LIMIT = 32768  # actual frozen Game supervisor's bounded reader
CAPACITY_KEYS = (
    "volume", "volume_identity", "disk", "current_project_usage_upper_bound", "usage_basis",
    "new_reservation_bytes", "estimated_incremental_peak_bytes", "this_write_peak",
    "reservation_id", "reservation_state", "retained_other_reservations", "retained_old_first30_OUT",
    "other_unspent_reservations", "system_growth_reserve_bytes", "safety_margin_bytes",
    "physical_required_free", "physical_margin_bytes", "effective_project_quota", "quota_override",
    "quota_reserved_upper_bound", "quota_margin_bytes", "disk_reserve_bytes",
    "physical_disk_reserve_bytes", "quota_derived_disk_reserve_bytes",
)
CURRENT_KEYS = CAPACITY_KEYS + ("machine_id", "policy_version", "status", "observed_at_utc", "at_utc",
    "review_at_utc", "approved_output_roots", "machine_profile", "all_old_reservations_retained")


def require(ok, message):
    if not ok:
        raise ValueError("canonical storage admission: " + message)


def _object(raw):
    require(type(raw) is bytes and 0 < len(raw) <= 65536, "bounded original JSON bytes required")
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "duplicate JSON key: " + key)
            result[key] = value
        return result
    value = json.loads(raw, object_pairs_hook=pairs, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
    require(type(value) is dict, "JSON object required")
    return value


def _stamp(value):
    require(type(value) is str, "explicit timezone-aware UTC timestamp required")
    stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(stamp.tzinfo is not None and stamp.utcoffset() == timedelta(0), "timestamp must explicitly be UTC")
    return stamp


def _pin(value):
    require(type(value) is dict and set(value) == {"path", "bytes", "sha256"}, "complete exact source pin required")
    require(type(value["path"]) is str and PureWindowsPath(value["path"]).is_absolute()
            and type(value["bytes"]) is int and value["bytes"] > 0
            and type(value["sha256"]) is str and len(value["sha256"]) == 64
            and all(c in "0123456789abcdef" for c in value["sha256"]), "invalid source pin")


def _integer(value, name, *, positive=False):
    require(type(value) is int and value >= (1 if positive else 0), "explicit integer required: " + name)


def _roots(roots):
    require(type(roots) is list and bool(roots) and len(roots) <= 32, "nonempty bounded approved roots required")
    require(all(type(p) is str and PureWindowsPath(p).is_absolute() for p in roots), "absolute approved roots required")
    require(len({str(PureWindowsPath(p)).casefold() for p in roots}) == len(roots), "duplicate approved root")


def validate_current_capacity(current, *, machine_id, policy, now_utc):
    """Validate explicit coordinator fields; never infer missing holds or values."""
    require(type(current) is dict and set(current) == set(CURRENT_KEYS), "complete current-capacity field set required")
    require(current["machine_id"] == machine_id and current["policy_version"] == policy["policy_version"]
            and current["status"] == "ADMITTED" and current["all_old_reservations_retained"] is True,
            "same-machine/policy complete capacity input required")
    require(_stamp(current["observed_at_utc"]) <= _stamp(now_utc) < _stamp(current["review_at_utc"])
            and current["at_utc"] == current["observed_at_utc"], "current observation/review window differs")
    _pin(current["machine_profile"])
    _roots(current["approved_output_roots"])
    disk = current["disk"]
    require(type(disk) is dict and set(disk) == {"total", "used", "free"}, "exact disk observation required")
    for key in disk:
        _integer(disk[key], "disk." + key, positive=key == "total")
    require(disk["used"] + disk["free"] == disk["total"], "disk tuple is inconsistent")
    require(type(current["volume"]) is str and PureWindowsPath(current["volume"]).is_absolute()
            and type(current["volume_identity"]) is dict and bool(current["volume_identity"]), "actual volume identity required")
    for key in CAPACITY_KEYS:
        if key not in ("volume", "volume_identity", "disk", "usage_basis", "reservation_id", "reservation_state", "quota_override"):
            _integer(current[key], key, positive=key in ("system_growth_reserve_bytes", "safety_margin_bytes", "effective_project_quota", "disk_reserve_bytes"))
    for key in ("usage_basis", "reservation_id", "reservation_state"):
        require(type(current[key]) is str and bool(current[key]), "explicit " + key + " required")
    quota = current["quota_override"]
    require(type(quota) is dict and all(k in quota for k in ("owner", "reason", "max_project_bytes", "approved_at_utc", "review_at_utc")), "complete quota authority required")
    require(type(quota["owner"]) is str and bool(quota["owner"]) and type(quota["reason"]) is str and bool(quota["reason"]), "quota owner/reason required")
    require(type(quota["max_project_bytes"]) is int and quota["max_project_bytes"] == current["effective_project_quota"]
            and _stamp(quota["approved_at_utc"]) <= _stamp(current["observed_at_utc"])
            and _stamp(current["review_at_utc"]) <= _stamp(quota["review_at_utc"])
            and _stamp(quota["review_at_utc"]) - _stamp(quota["approved_at_utc"]) <= timedelta(hours=policy["capacity"]["quota_override_max_hours"]),
            "quota amount or finite authority window differs")
    pc = policy["capacity"]
    safety = max(pc["safety_floor_bytes"], min(pc["safety_ceiling_bytes"], int(Decimal(str(pc["safety_volume_fraction"])) * disk["total"])))
    require(current["safety_margin_bytes"] == safety, "single-policy safety formula differs")
    require(current["other_unspent_reservations"] == current["retained_other_reservations"] + current["retained_old_first30_OUT"], "full other-hold coverage is inconsistent")
    physical = current["this_write_peak"] + current["other_unspent_reservations"] + current["system_growth_reserve_bytes"] + safety
    require(current["physical_disk_reserve_bytes"] == current["physical_required_free"] == physical, "complete remaining-peak physical reserve differs")
    require(current["quota_derived_disk_reserve_bytes"] == disk["total"] - current["effective_project_quota"] + current["this_write_peak"] + current["other_unspent_reservations"] + pc["safety_floor_bytes"], "quota-derived disk floor differs")
    require(current["disk_reserve_bytes"] == max(current["physical_disk_reserve_bytes"], current["quota_derived_disk_reserve_bytes"]), "canonical max reserve differs")
    require(current["physical_margin_bytes"] == disk["free"] - current["physical_required_free"], "physical margin differs")
    require(current["quota_margin_bytes"] == current["effective_project_quota"] - current["quota_reserved_upper_bound"]
            and current["quota_reserved_upper_bound"] == current["current_project_usage_upper_bound"] + current["this_write_peak"] + current["other_unspent_reservations"]
            and current["current_project_usage_upper_bound"] >= disk["used"], "quota upper/margin differs")
    require(disk["free"] > current["disk_reserve_bytes"] and current["physical_margin_bytes"] >= 0
            and disk["used"] + current["retained_other_reservations"] <= current["effective_project_quota"]
            and current["quota_margin_bytes"] >= 0, "actual capacity does not satisfy frozen runtime guard")


def compose_canonical_storage_v1(legacy_raw, coordinator_raw, *, legacy_pin, coordinator_pin, policy_raw, now_utc):
    """Return immutable candidate bytes; no reads, writes, reservations or grants."""
    legacy, coordinator, policy = _object(legacy_raw), _object(coordinator_raw), _object(policy_raw)
    _pin(legacy_pin)
    _pin(coordinator_pin)
    require(legacy_pin["bytes"] == len(legacy_raw) and legacy_pin["sha256"] == hashlib.sha256(legacy_raw).hexdigest(), "legacy provenance differs")
    require(coordinator_pin["bytes"] == len(coordinator_raw) and coordinator_pin["sha256"] == hashlib.sha256(coordinator_raw).hexdigest(), "coordinator provenance differs")
    require(legacy.get("schema") == SCHEMA and policy.get("schema") == "xar-storage-retention-policy-v1"
            and legacy["policy_version"] == policy["policy_version"], "complete canonical schema and single policy required")
    require(coordinator["schema"] == "xar.storage.coordinator-current-capacity-input.v1"
            and coordinator["status"] == "AUTHORITATIVE_INPUT_ONLY_NOT_LIVE_ADOPTION"
            and coordinator["machine_id"] == legacy["machine_id"], "explicit full coordinator input required")
    current_capacity = coordinator["current_capacity"]
    require(coordinator["observed_at_utc"] == current_capacity["observed_at_utc"]
            and coordinator["review_at_utc"] == current_capacity["review_at_utc"], "coordinator observation/review differs")
    for key in ("account_source", "active_holds_source", "new_Source23_fullhold"):
        _pin(coordinator[key])
    validate_current_capacity(current_capacity, machine_id=legacy["machine_id"], policy=policy, now_utc=now_utc)
    result = copy.deepcopy(legacy)
    for key in CURRENT_KEYS:
        result[key] = copy.deepcopy(current_capacity[key])
    result["canonical_compatibility_v1"] = {
        "legacy_source": copy.deepcopy(legacy_pin),
        "coordinator_input": copy.deepcopy(coordinator_pin),
        "current_source_account": copy.deepcopy(coordinator["account_source"]),
        "current_active_holds": copy.deepcopy(coordinator["active_holds_source"]),
        "new_Source23_fullhold": copy.deepcopy(coordinator["new_Source23_fullhold"]),
        "runtime_adoption_granted_by_composer": False,
        "old_noncapacity_scope_fields": "historical preserved fields, not new runtime or launch authority",
        "runtime_freeze_rule": "before cold launch bind review and full SHA across keeper/launch/profile/job; no prepare-only card replaces active canonical",
    }
    require(set(legacy) <= set(result) and result["schema"] == legacy["schema"], "legacy schema fields were lost")
    raw = (json.dumps(result, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")
    require(len(raw) <= LIMIT, "candidate exceeds actual frozen 32768-byte reader")
    return raw


def storage_binding_v1(canonical_raw, *, canonical_path):
    """Exact same binding for new profile/job; no regeneration of old evidence."""
    doc = _object(canonical_raw)
    require(doc["schema"] == SCHEMA and doc["status"] == "ADMITTED"
            and type(doc.get("canonical_compatibility_v1")) is dict, "complete compatible canonical candidate required")
    require(type(canonical_path) is str and PureWindowsPath(canonical_path).is_absolute(), "absolute canonical path required")
    _roots(doc["approved_output_roots"])
    _integer(doc["disk_reserve_bytes"], "disk_reserve_bytes", positive=True)
    return {"approved_output_roots": copy.deepcopy(doc["approved_output_roots"]),
            "disk_reserve_bytes": doc["disk_reserve_bytes"], "admission_path": canonical_path,
            "admission_sha256": hashlib.sha256(canonical_raw).hexdigest()}


def validate_new_bundle_v1(canonical_raw, *, canonical_path, profile_storage, job_storage, launch_review, keeper_review):
    binding = storage_binding_v1(canonical_raw, canonical_path=canonical_path)
    doc = _object(canonical_raw)
    require(profile_storage == binding and job_storage == binding, "profile/job/canonical full SHA or storage binding differs")
    require(launch_review == keeper_review == doc["review_at_utc"], "launch/keeper/canonical review differs")
    return {"admission_sha256": binding["admission_sha256"], "review_at_utc": doc["review_at_utc"], "compatible_only_not_runtime_grant": True}
