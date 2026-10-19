"""Pure exact Native30 +1.5 GiB overlay; old64 inputs and heads stay unchanged."""
from datetime import datetime
import hashlib
import json

GIB = 1073741824
ADDED = 3 * GIB // 2
ROOT = "D:/codex-ck3-demos/2026-10-19-robert-v20261019-native30-camera01"
CAPS = {"recordings": 40 * GIB, "SAVE": 8 * GIB, "Driver_log": 11 * GIB,
        "code_profile": 9 * GIB // 2, "monthly": 7 * GIB // 4, "research": GIB // 4}


def overlay(old_raw: bytes, supplement_raw: bytes, *, now,
            allow_draft_preview=False):
    """No filesystem, process, bus, mutation or permission-granting side effect.

    The old account must already conservatively include every old remaining
    commitment and other writer. Unknown or stale amounts are never zeroed.
    An approved immutable supplement still needs a separate exact child card.
    """
    old, sup = json.loads(old_raw), json.loads(supplement_raw)
    admitted = sup.get("status") == "ADMITTED"
    if not admitted and not allow_draft_preview:
        raise ValueError("unapproved supplement")
    if sup.get("independent_added_peak_bytes") != ADDED or sup.get("effective_stage_peak_bytes") != 64 * GIB + ADDED:
        raise ValueError("only exact +1.5GiB/effective65.5GiB is supported")
    if sup.get("original_stage_peak_bytes") != 64 * GIB or sup.get("effective_category_caps_bytes") != CAPS:
        raise ValueError("category allocation changed")
    if sup.get("native30_child_hard_limit_bytes") != ADDED or sup.get("native30_exact_output_root") != ROOT:
        raise ValueError("child root or hard limit changed")
    if admitted:
        sha = sup.get("native30_final_source_plan_sha256")
        if not isinstance(sha, str) or len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha) or not sup.get("Root_actual_approval_reference"):
            raise ValueError("signed supplement lacks final source/Root approval")
    if old.get("effective_stage_peak_bytes") != 64 * GIB or old.get("original_stage_peak_bytes") != 64 * GIB:
        raise ValueError("input must preserve original64 semantics")
    if old.get("reservation_id") != sup.get("reservation_id") or old.get("machine_id") != sup.get("machine_id"):
        raise ValueError("reservation or machine mismatch")
    age = (now - datetime.fromisoformat(old["observed_at_utc"])).total_seconds()
    if not 0 <= age <= 120:
        raise ValueError("old64 observation is not fresh")
    if sup.get("review_at_utc") != old.get("review_at_utc_unchanged") or not now < datetime.fromisoformat(sup["review_at_utc"]):
        raise ValueError("expiry mismatch or expired")
    keys = ("remaining_estimated_stage_peak_upper_bytes", "conservative_whole_volume_used_project_upper_bytes",
            "conservative_current_free_lower_bytes", "current_reconciled_quota_upper_bound_bytes",
            "current_reconciled_physical_required_free_bytes", "quota_bytes_unchanged",
            "retained_other_reservations_bytes_unchanged", "retained_old_OUT_bytes_unchanged")
    if any(type(old.get(k)) is not int or old[k] < 0 for k in keys):
        raise ValueError("unknown old64 amount")
    remaining = old[keys[0]]
    other = old[keys[6]] + old[keys[7]]
    if not 0 <= remaining <= 64 * GIB or old[keys[3]] != old[keys[1]] + remaining + other:
        raise ValueError("all old commitments must be included")
    reserves = (sup.get("system_growth_reserve_bytes"), sup.get("safety_margin_bytes"))
    if any(type(v) is not int or v < 0 for v in reserves) or old[keys[4]] != remaining + other + sum(reserves):
        raise ValueError("physical writer/system/safety calculation mismatch")
    quota = old[keys[3]] + ADDED
    required = old[keys[4]] + ADDED
    qm, pm = old[keys[5]] - quota, old[keys[2]] - required
    if min(qm, pm) <= 2 * GIB:
        raise ValueError("effective65.5 margins fail the strict2GiB floor")
    return {"schema": "xar.storage.independent-effective65p5-observation/v1",
            "machine_id": old["machine_id"], "observed_at_utc": now.isoformat(),
            "status": "INDEPENDENT65P5_CURRENT_ACCOUNT" if admitted else "DRAFT_PREVIEW_NO_BUILD",
            "old64_input_sha256": hashlib.sha256(old_raw).hexdigest(),
            "supplement_sha256": hashlib.sha256(supplement_raw).hexdigest(),
            "original_stage_peak_bytes_unchanged": 64 * GIB,
            "independent_added_peak_bytes": ADDED, "effective_stage_peak_bytes": 64 * GIB + ADDED,
            "effective_remaining_peak_upper_bytes": remaining + ADDED,
            "effective_category_caps_bytes": CAPS, "quota_upper_bound_bytes": quota,
            "quota_margin_bytes": qm, "physical_required_free_bytes": required,
            "physical_margin_bytes": pm, "two_GiB_floor_satisfied": True,
            "all_old_remaining_and_other_writers_included": True,
            "old64_or_pinned_files_mutated": 0, "physical_release_credit_bytes": 0,
            "original_review_at_utc": sup["review_at_utc"], "heavy_permission": False,
            "namespace": "NATIVE30-EFFECTIVE65P5-ACCOUNT / NATIVE30-EFFECTIVE65P5-HEAD only"}
