"""RAM-only Source26 generic-export arguments and policy-free BASE renderer.

Root separately admits and invokes the unchanged generic exporter, then writes
the returned BASE bytes create-only. This module never exports, writes Git or
files, launches processes, or issues runtime calls. Source26 commit identity
must come from an actual Root anchor; native history comes from Source25 BASE.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
from types import SimpleNamespace

OWN = Path(__file__).resolve().parent
REPO = OWN.parents[1]
MACHINE = "xenoamess-full-tower-eb9d2c1186"
PARENT = "9b791aae9bb1314162aa5cab923e6cca2892e6d8"
REF26 = "refs/heads/campaign/robert-v20261019-source26-unified-cold-01"
N = Path("D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep")
O = N / "p51-fresh1066-v20261019-prepare01/c23-source23-native30-cold100"
HOST = N / "sdk-v20261019-candidate/host-checkout"
SRC = N / "sdk-v20261019-candidate/src21"
REFERENCE = N / "sdk-v20261019-candidate/reference-c23-a05/src"
OUT = O / "immutable-source-export-a05"
BASE = O / "ROOT-FINAL-SDK-SOURCE26-BASE.json"
ANCHOR = REPO / "_runtime/source26-integration17/SOURCE26-CANONICAL-ANCHOR.json"
BASE25 = O / "ROOT-FINAL-SDK-SOURCE25-BASE.json"
BASE25_PIN = (387834, "35d593c6eefcdd4d88d462f7967650c196a89a635b6aca9122c4b355f056fbf7")
EXPORTER = OWN / "export_immutable_sdk_views_v1.py"
EXPORTER_PIN = (22964, "8b6972ac2a82b30c92b531c640df0eb9aa6e43cc205ab9d7d23796d5739da432")
ROWS26_PIN = (375601, "e3285c759ff33b0ecb5d4488514b28b7ef5911cee1a1e8ae8a39c2c593ff61c3")
DLL = "39350bd933549ff11e7a79e1b1e0340664bf87ee129a2aa8cdb7b0e9be269f56"
LABEL = "Native30 continuous hotspot tracking and idle realm overview"
ROW_FIELDS = ("relative", "bytes", "sha256", "git_blob_sha1", "git_mode")
BASE_HARD = 524288
META_HARD = 4194304
FS_HARD = 262144
EXPORT_STAGE_HARD = 16777216


def require(ok, why):
    if not ok:
        raise ValueError("Source26 generic export/BASE denied: " + why)


def pin(raw):
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def encoded(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode()


def ref(path, limit=2 * 1024**2):
    path = Path(path).resolve(strict=True)
    with path.open("rb") as stream:
        raw = stream.read(limit + 1)
    require(0 < len(raw) <= limit, "bounded actual input required")
    return {"path": str(path), **pin(raw)}


def read_document(reference, limit=2 * 1024**2):
    require(type(reference) is dict and set(reference) == {"path", "bytes", "sha256"}
            and type(reference["path"]) is str and Path(reference["path"]).is_absolute()
            and type(reference["bytes"]) is int and 0 < reference["bytes"] <= limit
            and re.fullmatch("[0-9a-f]{64}", reference["sha256"] or "") is not None,
            "bounded exact absolute JSON reference required")
    with Path(reference["path"]).open("rb") as stream:
        raw = stream.read(limit + 1)
    require(pin(raw) == {key: reference[key] for key in ("bytes", "sha256")},
            "actual input SHA or length differs")
    value = json.loads(raw)
    require(type(value) is dict and value.get("source_fixture") is not True,
            "actual JSON object required; fixtures have no export authority")
    return value


def observation(value):
    stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(stamp.tzinfo is not None and stamp.utcoffset().total_seconds() == 0
            and -10 <= (datetime.now(timezone.utc) - stamp).total_seconds() <= 600,
            "current explicit UTC observation required")


def rows(manifest):
    original = manifest.get("files")
    require(type(original) is list and 0 < len(original) <= 2500,
            "complete ordinary file rows required")
    result = []
    for item in original:
        row = {key: item[key] for key in ROW_FIELDS}
        name = row["relative"]
        require(type(name) is str and "\\" not in name and ":" not in name
                and "\0" not in name and name == PurePosixPath(name).as_posix()
                and not PurePosixPath(name).is_absolute()
                and name not in ("", ".")
                and all(part not in (".", "..") for part in PurePosixPath(name).parts)
                and type(row["bytes"]) is int and row["bytes"] >= 0
                and row["git_mode"] in ("100644", "100755")
                and re.fullmatch("[0-9a-f]{64}", row["sha256"] or "") is not None
                and re.fullmatch("[0-9a-f]{40}", row["git_blob_sha1"] or "") is not None,
                "safe exact canonical row required")
        result.append(row)
    require(len({row["relative"].casefold() for row in result}) == len(result)
            and len(result) == manifest.get("source_file_count")
            and sum(row["bytes"] for row in result) == manifest.get("source_bytes"),
            "complete distinct row inventory/totals required")
    return sorted(result, key=lambda row: row["relative"])


def actual_source25_v1(source25_base_ref=None):
    """Read retained historical authority; never infer it from new generic rows."""
    base_ref = source25_base_ref or ref(BASE25, BASE_HARD)
    require(Path(base_ref["path"]).resolve() == BASE25.resolve()
            and (base_ref["bytes"], base_ref["sha256"]) == BASE25_PIN,
            "exact actual Source25 BASE source required")
    base = read_document(base_ref, BASE_HARD)
    refs = {"source": base["source_inventory_reference"],
            "reference": base["independent_reference"],
            "export": base["immutable_source_export"],
            "anchor": base["source25_canonical_anchor"]}
    history = {key: read_document(item) for key, item in refs.items()}
    require(base.get("machine_id") == MACHINE and base.get("status") == "FINAL_SOURCE_FROZEN"
            and base.get("business_source_commit") == PARENT
            and base.get("runtime_admitted") is False
            and "canonical_preload_policy" not in base
            and all(doc.get("machine_id") == MACHINE for doc in history.values()),
            "actual same-machine Source25 BASE and history required")
    anchor = history["anchor"]
    require(anchor.get("schema") == "xar.source25.canonical-git-anchor/v1"
            and anchor.get("status") == "CANONICAL_REF_CREATED_NOT_DEPLOYED"
            and anchor.get("commit") == PARENT and anchor.get("future_writes") == 0,
            "actual closed Source25 canonical authority required")
    base_rows = rows(base)
    require(base_rows == rows(history["source"]) == rows(history["reference"])
            and pin(canonical(base_rows)) == anchor.get("complete_rows_JSON")
            and history["export"].get("manifests") == [refs["source"], refs["reference"]]
            and all(doc.get("business_source_commit") == PARENT
                    for key, doc in history.items() if key != "anchor"),
            "complete Source25 historical row/export binding differs")
    transition = base.get("native_transition")
    require(type(transition) is dict
            and all(doc.get("native_transition") == transition
                    for key, doc in history.items() if key != "anchor")
            and transition.get("machine_id") == MACHINE
            and transition.get("build_chain") == "resume02_snapshot07_functional09_artifact11"
            and transition.get("runtime_admitted") is False
            and transition.get("actual_loaded_provider_issued") is False
            and transition.get("H") == "NOTRUN"
            and transition.get("build_chain_provenance", {}).get("functional09_status_preserved") == "FAILED"
            and transition["build_chain_provenance"].get("artifact11_status")
                == "OFFLINE_ARTIFACT_QUALIFIED_NOT_DEPLOYED"
            and base.get("native_dll_sha256") == DLL and base.get("native_build_label") == LABEL,
            "Source25 BASE and original three-party Native29/30/09/11 provenance differ")
    return base, {"source25_BASE": base_ref, **refs}


def actual_anchor_v1(anchor_ref):
    require(Path(anchor_ref["path"]).resolve() == ANCHOR.resolve(),
            "exact future Source26 anchor path required")
    value = read_document(anchor_ref, 16384)
    require(value.get("schema") == "xar.source26.canonical-git-anchor/v1"
            and value.get("machine_id") == MACHINE
            and value.get("status") == "CANONICAL_REF_CREATED_NOT_DEPLOYED"
            and value.get("parent") == PARENT and value.get("ref") == REF26
            and re.fullmatch("[0-9a-f]{40}", value.get("commit", "")) is not None
            and value.get("execution_owner") == "Root"
            and value.get("root_direct_execution_release") is True
            and value.get("future_writes") == 0
            and value.get("source_file_count") == 1462 and value.get("source_bytes") == 59253402
            and value.get("complete_rows_JSON") == dict(zip(("bytes", "sha256"), ROWS26_PIN))
            and value.get("all_Git_mode_blob_size_verified") is True
            and value.get("changed_SHA256_bodies_read_back") == 12
            and len(value.get("output_pins", [])) == 12,
            "actual complete Root Source26 anchor required; planned commits are refused")
    return value


def card_template_v1(*, anchor_ref, stage_admission_ref, review_at_utc,
                     disk_reserve_bytes, source25_base_ref=None):
    """RAM template only. Root/storage separately freezes and admits this card."""
    require(sys.dont_write_bytecode, "run Python with -B")
    base, history_refs = actual_source25_v1(source25_base_ref)
    anchor = actual_anchor_v1(anchor_ref)
    expiry = datetime.fromisoformat(review_at_utc.replace("Z", "+00:00"))
    require(expiry.tzinfo is not None and datetime.now(timezone.utc) < expiry
            and type(disk_reserve_bytes) is int and disk_reserve_bytes >= 0,
            "fresh coordinated review and full-holds reserve required")
    stage = read_document(stage_admission_ref, 32768)
    require(stage.get("machine_id") == MACHINE and stage.get("status") == "ADMITTED"
            and stage.get("review_at_utc") == review_at_utc,
            "actual compatible full stage admission required")
    data_upper = 2 * sum(((row["bytes"] + 4095) // 4096) * 4096
                         for row in anchor["output_pins"])
    require(data_upper == 5488640, "twelve changed Source26 leaf cluster quote differs")
    exporter_ref = ref(EXPORTER)
    require((exporter_ref["bytes"], exporter_ref["sha256"]) == EXPORTER_PIN,
            "unchanged generic exporter source differs")
    target_native = base["native_transition"]["target_native_pin"]
    native = read_document(target_native, 32768)
    require(native.get("machine_id") == MACHINE and native.get("native_dll_sha256") == DLL
            and native.get("native_build_label") == LABEL,
            "retained actual Native30 target metadata required")
    return dict(schema="xar.ck3.immutable-sdk-view-capacity/v1", status="ADMITTED",
        machine_id=MACHINE, observed_at_utc=datetime.now(timezone.utc).isoformat(),
        review_at_utc=review_at_utc, business_source_commit=anchor["commit"],
        runtime_source_commit=base["git_head"], base_freeze_sha256=history_refs["source25_BASE"]["sha256"],
        native_pin_sha256=target_native["sha256"], sdk_generation="P37C23",
        base_source_root=base["source_root"], source_destination=str(SRC),
        reference_destination=str(REFERENCE), output_root=str(OUT),
        approved_output_roots=list(map(str, (SRC, REFERENCE, OUT, O))),
        metadata_reserve_bytes=META_HARD, filesystem_metadata_reserve_bytes=FS_HARD,
        new_allocation_limit_bytes=data_upper + META_HARD, disk_reserve_bytes=disk_reserve_bytes,
        stage_aggregate_hard_bytes=EXPORT_STAGE_HARD, stage_admission=stage_admission_ref,
        business_anchor_actual=anchor_ref, source25_native_history=history_refs,
        sourcepins={"generic_exporter": exporter_ref, "RAM_plan_renderer": ref(__file__)},
        view_budget=dict(dual_changed_cluster_upper=data_upper,
            rich_JSON_including_FS_MFT=META_HARD, export_total=data_upper + META_HARD,
            separate_compact_BASE=BASE_HARD, compact_target=str(BASE),
            complete_export_BASE_hard_bytes=data_upper + META_HARD + BASE_HARD),
        permission="Root generic export and create-only BASE only; no runtime grant.",
        all_old_hard_holds_retained=True, physical_credit_bytes=0)


def export_args_v1(*, capacity_ref, anchor_ref):
    """Return args for original export_immutable_sdk_views_v1.export_views()."""
    card = read_document(capacity_ref, 65536)
    expected = card_template_v1(anchor_ref=anchor_ref,
        stage_admission_ref=card["stage_admission"], review_at_utc=card["review_at_utc"],
        disk_reserve_bytes=card["disk_reserve_bytes"],
        source25_base_ref=card["source25_native_history"]["source25_BASE"])
    require(all(card.get(key) == value for key, value in expected.items()
                if key != "observed_at_utc"), "concrete admitted generic export card differs")
    require(not BASE.exists(), "BASE is create-only")
    base, _ = actual_source25_v1(card["source25_native_history"]["source25_BASE"])
    return SimpleNamespace(business_source_repo=REPO, runtime_source_repo=HOST,
        business_source_commit=card["business_source_commit"],
        runtime_source_commit=card["runtime_source_commit"],
        base_freeze=BASE25, base_freeze_sha256=card["base_freeze_sha256"],
        native_pin=Path(base["native_transition"]["target_native_pin"]["path"]),
        native_pin_sha256=card["native_pin_sha256"], capacity_card=Path(capacity_ref["path"]),
        capacity_card_sha256=capacity_ref["sha256"], machine_id=MACHINE, sdk_generation="P37C23",
        source_destination=SRC, reference_destination=REFERENCE, output_root=OUT)


def _compose_values_v1(*, source, reference, complete, anchor, previous,
                       source_ref, reference_ref, export_ref, anchor_ref,
                       native_history_refs, observed_at_utc):
    """Pure payload checks/rendering; public entry reads every exact actual ref."""
    require(all(doc.get("machine_id") == MACHINE
                and doc.get("source_fixture") is not True
                for doc in (source, reference, complete, anchor, previous)),
            "same-machine actual inputs required")
    compact = rows(source)
    require(compact == rows(reference)
            and len(compact) == anchor["source_file_count"] == 1462
            and sum(row["bytes"] for row in compact) == anchor["source_bytes"] == 59253402
            and pin(canonical(compact)) == anchor["complete_rows_JSON"]
            == dict(zip(("bytes", "sha256"), ROWS26_PIN)),
            "all Source26 canonical compact rows differ")
    require(complete.get("schema") == "xar.ck3.immutable-sdk-view-export/v1"
            and complete.get("status") == "SOURCE_READY_NOT_LOADED"
            and complete.get("manifests") == [source_ref, reference_ref]
            and complete.get("old_content_write_operations") == 0
            and complete.get("game_sdk_native_obs_calls") == 0
            and complete.get("new_unique_file_count") == 24
            and set(complete.get("changed_relative_paths", []))
                == {row["relative"] for row in anchor["output_pins"]}
            and complete.get("logical_bytes_each") == anchor["source_bytes"],
            "actual completed twelve-leaf generic dual export required")
    require(source.get("source_root") == str(SRC.resolve())
            and reference.get("source_root") == str(REFERENCE.resolve())
            and source.get("source_root") != reference.get("source_root")
            and all(doc.get("business_source_commit") == anchor["commit"]
                    for doc in (source, reference, complete))
            and all(doc.get("status") == "FINAL_SOURCE_FROZEN"
                    and doc.get("sdk_generation") == "P37C23"
                    and doc.get("runtime_admitted") is False
                    and doc.get("base_freeze") == native_history_refs["source25_BASE"]
                    and doc.get("git_head") == previous["git_head"]
                    and doc.get("native_dll_sha256") == DLL
                    and doc.get("native_build_label") == LABEL
                    and "native_transition" not in doc
                    and "canonical_preload_policy" not in doc
                    for doc in (source, reference))
            and "native_transition" not in complete,
            "actual generic Source26 bindings required; native history is inherited separately")
    require(source.get("capacity_admission") == reference.get("capacity_admission")
            == complete.get("capacity"), "dual export capacity source differs")
    result = dict(source)
    result.update(schema="root.ck3.final-sdk-freeze/v1", files=compact,
        compact_at_utc=observed_at_utc, attempt_id="a05",
        immutable_ntfs_inventory=source_ref, immutable_source_export=export_ref,
        source_inventory_reference=source_ref, independent_reference=reference_ref,
        native_transition=previous["native_transition"],
        native_transition_inherited_from_actual_source25_BASE=True,
        native_transition_inheritance=dict(source26_generic_export_has_transition=False,
            source25_three_party_transition_equal_BASE=True, **native_history_refs),
        rich_manifest_campaign_flags_are_exporter_defaults_not_runtime_facts=True,
        clean_campaign=False, prior_campaign_state_or_credits_inherited=True,
        runtime_owner_generation="P37C23", same_Game_native29_continuation=False,
        physical_session_opening_date_raw=None, planned_saved_opening_date_raw=53274624,
        campaign_start_date_raw=53144328, campaign_endpoint_date_raw=53407128,
        continuation_basis=("SAVE10480 raw53274624/day5429/count74/cycles4753; original T0/end/allwall "
            "retained; A01/A02/A03/A04 failed attempts give zero campaign credit; "
            "new A05 cold Game and Native30 adoption NOTRUN."),
        war_daily_watch_enabled=False, contact_free_route_speed_trial_enabled=False,
        new_source_pair_created=True, driver_state_wal_writer_requested=True,
        driver_state_wal_constructor_actual_value="NOTRUN; require actual App env and natural journal append",
        clock_root_cause="UNKNOWN; LF copy reduction source qualified only; no measured throughput credit",
        actual_native_loaded=False, H="NOTRUN", os_qualification="UNKNOWN",
        defender_registration_pending=True, source26_canonical_anchor=anchor_ref,
        source26_parent_commit=PARENT)
    raw = encoded(result)
    require(len(raw) <= BASE_HARD and "canonical_preload_policy" not in result,
            "complete BASE must remain policy-free and within 512 KiB")
    return raw, dict(machine_id=MACHINE, observed_at_utc=observed_at_utc,
        status="RAM_BASE_COMPOSED_NOT_WRITTEN_NOT_LOADED", attempt_id="a05",
        source_file_count=len(compact), source_bytes=sum(row["bytes"] for row in compact),
        complete_rows_JSON=pin(canonical(compact)), compact_BASE=pin(raw),
        inputs=dict(source=source_ref, reference=reference_ref, export=export_ref,
            anchor=anchor_ref, native_history=native_history_refs),
        native_transition_source="actual Source25 BASE; original three-party equality checked",
        new_generic_transition_fields_claimed=False, policy_added=False,
        outputs_created=0, runtime_calls=0, Git_calls=0, export_calls=0)


def compose_compact_base_v1(*, source_ref, reference_ref, export_ref, anchor_ref,
                            observed_at_utc, source25_base_ref=None):
    """Read actual products, return complete BASE bytes/report, write nothing."""
    require(sys.dont_write_bytecode, "run Python with -B")
    observation(observed_at_utc)
    for item, path in ((source_ref, OUT / "SOURCE-FREEZE.json"),
                       (reference_ref, OUT / "REFERENCE-FREEZE.json"),
                       (export_ref, OUT / "COMPLETE.json")):
        require(Path(item["path"]).resolve() == path.resolve(), "actual A05 product path differs")
    previous, history_refs = actual_source25_v1(source25_base_ref)
    anchor = actual_anchor_v1(anchor_ref)
    return _compose_values_v1(source=read_document(source_ref),
        reference=read_document(reference_ref), complete=read_document(export_ref),
        anchor=anchor, previous=previous, source_ref=source_ref,
        reference_ref=reference_ref, export_ref=export_ref, anchor_ref=anchor_ref,
        native_history_refs=history_refs, observed_at_utc=observed_at_utc)


if __name__ == "__main__":
    print(json.dumps(dict(status="RAM_API_ONLY_NO_EXECUTION_ENTRY", machine_id=MACHINE,
        actual_anchor_required=str(ANCHOR), generic_exporter=str(EXPORTER),
        source_destination=str(SRC), reference_destination=str(REFERENCE), output_root=str(OUT),
        compact_BASE=str(BASE), compact_BASE_hard_bytes=BASE_HARD,
        Git_calls=0, export_calls=0, outputs_created=0, runtime_calls=0)))
