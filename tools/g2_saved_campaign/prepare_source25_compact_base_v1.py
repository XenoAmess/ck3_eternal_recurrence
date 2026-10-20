"""Render the Source25 compact BASE from actual immutable export products.

All functions are RAM-only. Export remains the unchanged Native29 to Native30
09+11 validator and exact frozen exporter. Runtime adds its actual A03 policy
reference later, once, while creating a new final freeze.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

MACHINE = "xenoamess-full-tower-eb9d2c1186"
PARENT = "6b55531b1d3a44ee73ab13ea40132556030f682e"
ROW_FIELDS = ("relative", "bytes", "sha256", "git_blob_sha1", "git_mode")
NATIVE_BINDING_COMMIT = "adfeb53fd2dfa9b93e389002ba30ae3479add47c"
NATIVE_BINDING_PATH = "_runtime/prepare_c23_native_binding100.py"
NATIVE_BINDING_BYTES = 7355
NATIVE_BINDING_SHA256 = "5a1fbdbeeffe09cf916c3d299971357a267215eee64e649c05f98ea50633941e"
NATIVE_DLL_SHA256 = "39350bd933549ff11e7a79e1b1e0340664bf87ee129a2aa8cdb7b0e9be269f56"
LABEL = "Native30 continuous hotspot tracking and idle realm overview"


def require(ok, why):
    if not ok:
        raise ValueError("Source25 compact BASE denied: " + why)


def pin(raw):
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def encoded(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def read_document(reference, limit=2 * 1024**2):
    require(isinstance(reference, dict) and set(reference) == {"path", "bytes", "sha256"}
            and type(reference["path"]) is str and Path(reference["path"]).is_absolute()
            and type(reference["bytes"]) is int and 0 < reference["bytes"] <= limit,
            "bounded exact absolute JSON reference required")
    with Path(reference["path"]).open("rb") as stream:
        raw = stream.read(limit + 1)
    require(pin(raw) == {key: reference[key] for key in ("bytes", "sha256")},
            "actual input SHA or length differs")
    value = json.loads(raw)
    require(isinstance(value, dict), "JSON object required")
    require(value.get("source_fixture") is not True, "synthetic input refused")
    return value


def utc_observation(value):
    require(type(value) is str, "explicit actual UTC observation required")
    stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(stamp.tzinfo is not None and stamp.utcoffset().total_seconds() == 0
            and -10 <= (datetime.now(timezone.utc) - stamp).total_seconds() <= 600,
            "current UTC observation required")
    return stamp


def compact_rows(manifest):
    original = manifest.get("files")
    require(isinstance(original, list) and original, "complete actual rows required")
    rows = [{key: row[key] for key in ROW_FIELDS} for row in original]
    require(len({row["relative"].casefold() for row in rows}) == len(rows)
            and all(type(row["relative"]) is str and type(row["bytes"]) is int
                    and row["bytes"] >= 0 and row["git_mode"] in ("100644", "100755")
                    and len(row["sha256"]) == 64 and len(row["git_blob_sha1"]) == 40
                    for row in rows), "complete ordinary distinct rows required")
    require(len(rows) == manifest.get("source_file_count")
            and sum(row["bytes"] for row in rows) == manifest.get("source_bytes"),
            "manifest totals differ from actual rows")
    return rows


def compose_compact_base_v1(*, source_ref, reference_ref, export_ref,
                            anchor_ref, observed_at_utc):
    """Derive compact bytes/report, without creating or modifying any output."""
    utc_observation(observed_at_utc)
    source, reference, complete, anchor = [
        read_document(ref) for ref in (source_ref, reference_ref, export_ref, anchor_ref)]
    require(all(value.get("machine_id") == MACHINE
                for value in (source, reference, complete, anchor)),
            "actual same-machine evidence required")
    require(anchor.get("schema") == "xar.source25.canonical-git-anchor/v1"
            and anchor.get("status") == "CANONICAL_REF_CREATED_NOT_DEPLOYED"
            and anchor.get("parent") == PARENT
            and anchor.get("root_direct_execution_release") is True
            and anchor.get("execution_owner") == "Root",
            "actual Root single-parent Source25 canonical anchor required")
    require(complete.get("schema") == "xar.ck3.immutable-sdk-view-export/v1"
            and complete.get("status") == "SOURCE_READY_NOT_LOADED"
            and complete.get("manifests") == [source_ref, reference_ref]
            and complete.get("old_content_write_operations") == 0
            and complete.get("game_sdk_native_obs_calls") == 0,
            "actual completed dual export required")
    rows = compact_rows(source)
    twin_rows = compact_rows(reference)
    require(rows == twin_rows and source.get("source_root") != reference.get("source_root")
            and source.get("status") == reference.get("status") == "FINAL_SOURCE_FROZEN"
            and source.get("sdk_generation") == reference.get("sdk_generation") == "P37C23"
            and source.get("runtime_admitted") is reference.get("runtime_admitted") is False
            and source.get("business_source_commit") == reference.get("business_source_commit")
            == complete.get("business_source_commit") == anchor.get("commit")
            and source.get("source_file_count") == anchor.get("source_file_count")
            and source.get("source_bytes") == anchor.get("source_bytes")
            == complete.get("logical_bytes_each"),
            "complete actual Source25 source and reference bindings differ")
    inventory = canonical(sorted(rows, key=lambda row: row["relative"]))
    require(pin(inventory) == anchor.get("complete_rows_JSON"),
            "all compact rows differ from actual canonical Source25 rows")
    transition = source.get("native_transition")
    require(isinstance(transition, dict)
            and transition == reference.get("native_transition") == complete.get("native_transition")
            and transition.get("build_chain") == "resume02_snapshot07_functional09_artifact11"
            and transition.get("machine_id") == MACHINE
            and transition.get("runtime_admitted") is False
            and transition.get("actual_loaded_provider_issued") is False
            and transition.get("H") == "NOTRUN"
            and transition.get("build_chain_provenance", {}).get("functional09_status_preserved")
            == "FAILED"
            and source.get("native_build_label") == reference.get("native_build_label") == LABEL
            and source.get("native_dll_sha256") == reference.get("native_dll_sha256")
            == NATIVE_DLL_SHA256,
            "original Native29 plus closed09/artifact11 transition must be preserved")
    require("canonical_preload_policy" not in source
            and "canonical_preload_policy" not in reference,
            "rich inputs cannot carry a planned or old policy")
    value = dict(source)
    value.update(
        schema="root.ck3.final-sdk-freeze/v1", files=rows,
        compact_at_utc=observed_at_utc, attempt_id="a03",
        immutable_ntfs_inventory=source_ref, immutable_source_export=export_ref,
        source_inventory_reference=source_ref, independent_reference=reference_ref,
        rich_manifest_campaign_flags_are_exporter_defaults_not_runtime_facts=True,
        clean_campaign=False, prior_campaign_state_or_credits_inherited=True,
        runtime_owner_generation="P37C23", same_Game_native29_continuation=False,
        physical_session_opening_date_raw=None, planned_saved_opening_date_raw=53274624,
        campaign_start_date_raw=53144328, campaign_endpoint_date_raw=53407128,
        continuation_basis=(
            "SAVE10480 raw53274624/day5429/count74/cycles4753; original T0/end/allwall "
            "retained; A01/A02 failed closed attempts give zero campaign credit; "
            "new cold Game and Native30 adoption NOTRUN."),
        war_daily_watch_enabled=False, contact_free_route_speed_trial_enabled=False,
        new_source_pair_created=True, driver_state_wal_writer_requested=True,
        driver_state_wal_constructor_actual_value=(
            "NOTRUN; require actual App env and natural journal append"),
        clock_root_cause="UNKNOWN; wait progress diagnostic B only; no performance credit",
        actual_native_loaded=False, H="NOTRUN", os_qualification="UNKNOWN",
        defender_registration_pending=True, source25_canonical_anchor=anchor_ref,
        source25_parent_commit=PARENT,
    )
    raw = encoded(value)
    require(len(raw) <= 524288 and "canonical_preload_policy" not in value,
            "bounded policy-free compact BASE required")
    return raw, {
        "machine_id": MACHINE, "observed_at_utc": observed_at_utc,
        "status": "RAM_BASE_COMPOSED_NOT_WRITTEN_NOT_LOADED",
        "attempt_id": "a03", "source_file_count": len(rows),
        "source_bytes": sum(row["bytes"] for row in rows),
        "complete_rows_JSON": pin(inventory), "compact_BASE": pin(raw),
        "inputs": {"source": source_ref, "reference": reference_ref,
                   "export": export_ref, "anchor": anchor_ref},
        "policy_added": False, "outputs_created": 0, "runtime_calls": 0,
    }


def compose_native_session_v1(*, repository, capacity_ref, observed_at_utc):
    """Reuse the exact frozen native composer blob in RAM, without materializing it."""
    utc_observation(observed_at_utc)
    repository = Path(repository).resolve(strict=True)
    raw = subprocess.check_output([
        "git", "-C", str(repository), "cat-file", "blob",
        NATIVE_BINDING_COMMIT + ":" + NATIVE_BINDING_PATH])
    require(pin(raw) == {"bytes": NATIVE_BINDING_BYTES,
                        "sha256": NATIVE_BINDING_SHA256},
            "original native binding Git blob differs")
    namespace = {"__name__": "_source25_exact_original_native_binding",
                 "__file__": str(repository / NATIVE_BINDING_PATH)}
    exec(compile(raw, NATIVE_BINDING_COMMIT + ":" + NATIVE_BINDING_PATH, "exec"), namespace)
    result, report = namespace["compose"](
        capacity_ref=capacity_ref, observed_at_utc=observed_at_utc)
    value = json.loads(result)
    require(value.get("machine_id") == MACHINE
            and value.get("actual_runtime_loaded") is False
            and value.get("actual_loaded_provider_issued") is False
            and value.get("native_dll_sha256") == NATIVE_DLL_SHA256
            and value.get("storage_admission") == capacity_ref,
            "actual new capacity native session binding differs")
    return result, {
        **report, "status": "EXACT_GIT_COMPOSER_REUSED_RAM_ONLY",
        "original_report": report, "target": None,
        "new_target_to_be_bound_by_A03_runtime": True,
        "frozen_original_composer": {
            "commit": NATIVE_BINDING_COMMIT, "path": NATIVE_BINDING_PATH,
            "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()},
    }

