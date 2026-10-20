"""RAM-only Source28 generic dual-export card and compact policy-free BASE.

Root alone invokes the original exporter and writes create-only outputs.
Source27 BASE and Source25 Native history are retained immutable authorities.
"""
from __future__ import annotations

from datetime import datetime, timezone
import importlib.util
import hashlib
import json
from pathlib import Path
import re
import sys
from types import SimpleNamespace
from typing import TypeAlias, TypedDict

JSONValue: TypeAlias = str | int | float | bool | None | list["JSONValue"] | dict[str, "JSONValue"]
JSONObject: TypeAlias = dict[str, JSONValue]

sys.dont_write_bytecode = True
OWN = Path(__file__).resolve().parent
RENDERER27_PIN = (18550, "e0817763e8df1fd70e8e6b68a5dc374e9940637f18768a0b894e8b0323748de3")
OLD_PATH = OWN / "prepare_source27_export_base_v1.py"
OLD_RAW = OLD_PATH.read_bytes()
if (len(OLD_RAW), hashlib.sha256(OLD_RAW).hexdigest()) != RENDERER27_PIN:
    raise ValueError("Source28 export: original renderer preimage changed")
SPEC = importlib.util.spec_from_file_location("_source28_original_source27_renderer", OLD_PATH)
if SPEC is None or SPEC.loader is None:
    raise ValueError("Source28 export: original renderer loader unavailable")
OLD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(OLD)
MACHINE, REPO, N, O, HOST = OLD.MACHINE, OLD.REPO, OLD.N, OLD.O, OLD.HOST
PARENT = "4b0f3771b51d65af2cd6d576116535237aac7ef0"
REF28 = "refs/heads/campaign/robert-v20261020-source28-typed-diagnostics-01"
TREE28 = "7d83a2f5e28c602c70d1a9a8a6025802ebc985a2"
ROWS28 = {"bytes": 376075, "sha256":
    "27fd27a2024fc95614877c45ba435a4dbcb72ea2c8b7d45c40dd73a12e3fe63b"}
WRITER_PIN = (23916, "e5c806eee85e7e414fd7d49dccdd762f69f8b8b6024aae3acb1ebc027b6ce385")
BASE27 = O / "source27-a10-prep01/ROOT-FINAL-SDK-SOURCE27-BASE.json"
BASE27_PIN = (398331, "c93cc3e4d4d4996a7787d0f4b095ae67b8e4d145e725f2d7e288c8010b64a8fe")
P = O / "source28-a12-prep01"
SRC = N / "sdk-v20261019-candidate/src28"
REFERENCE = N / "sdk-v20261019-candidate/src28-independent"
OUT = P / "immutable-source-export-source28"
BASE = P / "ROOT-FINAL-SDK-SOURCE28-BASE.json"
ANCHOR = P / "source28-canonical01/SOURCE28-CANONICAL-ANCHOR.json"
BASE_HARD, META_HARD, FS_HARD, STAGE_HARD = 524288, 4194304, 262144, 12582912
pin, encoded, canonical = OLD.pin, OLD.encoded, OLD.canonical
ref, rows = OLD.ref, OLD.rows


def require(ok: object, why: str) -> None:
    if not ok:
        raise ValueError("Source28 generic export/BASE denied: " + why)


class ExactRef(TypedDict):
    path: str
    bytes: int
    sha256: str


def checked(item: ExactRef, limit: int = 4194304) -> JSONObject:
    require(type(item) is dict and set(item) == {"path", "bytes", "sha256"}
            and type(item["path"]) is str and Path(item["path"]).is_absolute()
            and type(item["bytes"]) is int and 0 <= item["bytes"] <= limit
            and type(item["sha256"]) is str
            and re.fullmatch("[0-9a-f]{64}", item["sha256"]) is not None,
            "strict exact ref required")
    return OLD.checked(item, limit)

def exact_int(value: object, wanted: int) -> bool:
    return type(value) is int and value == wanted


def checked_source() -> ExactRef:
    item = ref(OWN / "prepare_source27_export_base_v1.py")
    require((item["bytes"], item["sha256"]) == RENDERER27_PIN, "original RAM helpers changed")
    return item


def actual_source27_v1() -> tuple[JSONObject, JSONObject, JSONObject]:
    """Actual Source27 BASE, inventories and unchanged Native history authority."""
    checked_source()
    previous26, _, history26 = OLD.actual_source26_v1()
    item = ref(BASE27, BASE_HARD)
    require((item["bytes"], item["sha256"]) == BASE27_PIN, "actual Source27 BASE differs")
    base = checked(item, BASE_HARD)
    require(base["machine_id"] == MACHINE and base["business_source_commit"] == PARENT
            and base["status"] == "FINAL_SOURCE_FROZEN" and base["runtime_admitted"] is False
            and "canonical_preload_policy" not in base
            and base["native_transition"] == previous26["native_transition"],
            "actual policy-free Source27/native inheritance")
    anchor_ref = base["source27_canonical_anchor"]
    require((anchor_ref["bytes"], anchor_ref["sha256"]) ==
            (9235, "390e368a1101d6ab6ac4c311aba0f453859d51276dc825ed352d6340a3378d38"), "actual Source27 anchor pin")
    anchor = OLD.actual_anchor_v1(anchor_ref)
    source_ref, reference_ref = base["source_inventory_reference"], base["independent_reference"]
    source, reference = checked(source_ref), checked(reference_ref)
    complete_ref = base["immutable_source_export"]
    complete = checked(complete_ref, 16384)
    compact = rows(base)
    require(len(compact) == 1462 and compact == rows(source) == rows(reference)
            and anchor["complete_rows_JSON"] == pin(canonical(compact))
            and complete["manifests"] == [source_ref, reference_ref]
            and exact_int(complete["old_content_write_operations"], 0)
            and source["source_root"] == base["source_root"]
            and source["business_source_commit"] == reference["business_source_commit"]
            == complete["business_source_commit"] == PARENT,
            "actual complete Source27 rows and dual-export lineage")
    return base, source, {"source27_BASE": item, "source27_anchor": anchor_ref,
        "source27_source_inventory": source_ref, "source27_independent_reference": reference_ref,
        "source27_immutable_export": complete_ref,
        "inherited_native_history": base["native_transition_inheritance"], "source26_history": history26}



def actual_anchor_v1(anchor_ref: ExactRef) -> JSONObject:
    anchor = checked(anchor_ref, 65536)
    require(Path(anchor_ref["path"]).resolve() == ANCHOR.resolve()
            and anchor["schema"] == "xar.source28.canonical-git-anchor/v1"
            and anchor["machine_id"] == MACHINE
            and anchor["status"] == "CANONICAL_REF_CREATED_NOT_DEPLOYED"
            and anchor["execution_owner"] == "Root"
            and anchor["root_direct_execution_release"] is True
            and anchor["parent"] == PARENT and anchor["ref"] == REF28
            and anchor["tree"] == TREE28 and exact_int(anchor["future_writes"], 0)
            and type(anchor["commit"]) is str and re.fullmatch("[0-9a-f]{40}", anchor["commit"]) is not None and anchor["commit"] != PARENT
            and exact_int(anchor["source_file_count"], 1464) and exact_int(anchor["source_bytes"], 59279032)
            and anchor["complete_rows_JSON"] == ROWS28
            and len(anchor["output_pins"]) == 14
            and len(anchor["canonical_patch_rows"]) == 28
            and all(exact_int(anchor[name], 0) for name in ("runtime_calls", "SDK_export_calls",
                "push_calls", "index_or_tracked_worktree_mutations")),
            "actual complete Source28 Root anchor required")
    writer_ref = ref(OWN / "write_source28_canonical_ref_v1.py")
    require((writer_ref["bytes"], writer_ref["sha256"]) == WRITER_PIN
            and anchor["writer"] == writer_ref, "actual Source28 writer pin differs")
    _, _, history = actual_source27_v1()
    require(anchor["actual_Source27_anchor"] == history["source27_anchor"]
            and anchor["actual_Source27_BASE"] == history["source27_BASE"],
            "Source28 actual Source27 parent provenance")
    changed = rows({"files": anchor["output_pins"], "source_file_count": 14,
                    "source_bytes": sum(row["bytes"] for row in anchor["output_pins"])})
    require(len({row["relative"] for row in changed}) == 14, "fourteen distinct Source28 SDK deltas")
    return anchor


def card_template_v1(*, anchor_ref: ExactRef, stage_admission_ref: ExactRef,
                     review_at_utc: str, disk_reserve_bytes: int) -> JSONObject:
    require(sys.dont_write_bytecode, "Python -B required")
    base, _, history = actual_source27_v1()
    anchor = actual_anchor_v1(anchor_ref)
    stage = checked(stage_admission_ref, 32768)
    expiry = datetime.fromisoformat(review_at_utc.replace("Z", "+00:00"))
    stage_expiry = datetime.fromisoformat(stage["review_at_utc"].replace("Z", "+00:00"))
    require(stage["machine_id"] == MACHINE and stage["status"] == "ADMITTED"
            and expiry == stage_expiry and expiry.tzinfo is not None
            and expiry.utcoffset().total_seconds() == 0 and datetime.now(timezone.utc) < expiry
            and type(disk_reserve_bytes) is int and disk_reserve_bytes >= 0,
            "actual finite stage admission and coordinated floor")
    approved = [Path(path).resolve() for path in stage["approved_output_roots"]]
    require(all(any(path.resolve() == root or path.resolve().is_relative_to(root) for root in approved)
                for path in (SRC, REFERENCE, OUT, BASE)), "finite stage approved roots differ")
    exporter_ref = ref(OLD.OLD.EXPORTER)
    require((exporter_ref["bytes"], exporter_ref["sha256"]) == OLD.OLD.EXPORTER_PIN,
            "original generic exporter changed")
    data = 2 * sum(((row["bytes"] + 4095) // 4096) * 4096 for row in anchor["output_pins"])
    total = data + META_HARD + BASE_HARD
    require(total <= STAGE_HARD, "complete dual export and BASE exceed 12 MiB")
    native_ref = base["native_transition"]["target_native_pin"]
    native = checked(native_ref, 32768)
    require(native["machine_id"] == MACHINE and native["native_dll_sha256"] == OLD.OLD.DLL
            and native["native_build_label"] == OLD.OLD.LABEL, "same inherited Native30 authority")
    return dict(schema="xar.ck3.immutable-sdk-view-capacity/v1", status="ADMITTED",
        machine_id=MACHINE, observed_at_utc=datetime.now(timezone.utc).isoformat(),
        review_at_utc=stage["review_at_utc"], business_source_commit=anchor["commit"],
        runtime_source_commit=base["git_head"], base_freeze_sha256=history["source27_BASE"]["sha256"],
        native_pin_sha256=native_ref["sha256"], sdk_generation="P37C23",
        base_source_root=base["source_root"], source_destination=str(SRC.resolve()),
        reference_destination=str(REFERENCE.resolve()), output_root=str(OUT.resolve()),
        approved_output_roots=[str(path.resolve()) for path in (SRC, REFERENCE, OUT, P)],
        metadata_reserve_bytes=META_HARD, filesystem_metadata_reserve_bytes=FS_HARD,
        new_allocation_limit_bytes=data + META_HARD, disk_reserve_bytes=disk_reserve_bytes,
        stage_aggregate_hard_bytes=STAGE_HARD, stage_admission=stage_admission_ref,
        business_anchor_actual=anchor_ref, source27_history=history,
        sourcepins={"generic_exporter": exporter_ref, "RAM_plan_renderer": ref(__file__),
                    "original_Source27_renderer": checked_source()},
        view_budget=dict(changed_leaf_count=14, independent_new_FileIDs=28,
            unchanged_shared_FileIDs=1450, dual_changed_cluster_upper=data,
            rich_JSON_including_FS_MFT=META_HARD, separate_compact_BASE=BASE_HARD,
            compact_target=str(BASE.resolve()), complete_export_BASE_hard_bytes=total),
        all_old_hard_holds_retained=True, physical_credit_bytes=0,
        permission="Root exact generic dual export and create-only BASE; no runtime grant")


def export_args_v1(*, capacity_ref: ExactRef, anchor_ref: ExactRef) -> SimpleNamespace:
    card = checked(capacity_ref, 65536)
    expected = card_template_v1(anchor_ref=anchor_ref,
        stage_admission_ref=card["stage_admission"], review_at_utc=card["review_at_utc"],
        disk_reserve_bytes=card["disk_reserve_bytes"])
    require(all(card.get(k) == v for k, v in expected.items() if k != "observed_at_utc"),
            "actual exact export card changed")
    require(not BASE.exists(), "compact BASE create-only")
    base, _, _ = actual_source27_v1()
    native_ref = base["native_transition"]["target_native_pin"]
    return SimpleNamespace(business_source_repo=REPO, runtime_source_repo=HOST,
        business_source_commit=card["business_source_commit"],
        runtime_source_commit=card["runtime_source_commit"],
        base_freeze=BASE27, base_freeze_sha256=card["base_freeze_sha256"],
        native_pin=Path(native_ref["path"]), native_pin_sha256=native_ref["sha256"],
        capacity_card=Path(capacity_ref["path"]), capacity_card_sha256=capacity_ref["sha256"],
        machine_id=MACHINE, sdk_generation="P37C23",
        source_destination=SRC, reference_destination=REFERENCE, output_root=OUT)


def file_id(row: JSONObject) -> tuple[int, str]:
    identity = row["file_identity"]
    require(identity["filesystem"] == "NTFS" and identity["directory"] is False
            and type(identity["volume_serial"]) is int and identity["volume_serial"] > 0
            and type(identity["file_id"]) is str
            and re.fullmatch("[0-9a-f]{16,32}", identity["file_id"]) is not None,
            "actual ordinary NTFS file identity required")
    return identity["volume_serial"], identity["file_id"]


def compose_compact_base_v1(*, source_ref: ExactRef, reference_ref: ExactRef,
                            export_ref: ExactRef, anchor_ref: ExactRef,
                            observed_at_utc: str) -> tuple[bytes, JSONObject]:
    OLD.OLD.observation(observed_at_utc)
    previous, old_source, history = actual_source27_v1()
    anchor = actual_anchor_v1(anchor_ref)
    for item, path in ((source_ref, OUT / "SOURCE-FREEZE.json"),
                       (reference_ref, OUT / "REFERENCE-FREEZE.json"),
                       (export_ref, OUT / "COMPLETE.json")):
        require(Path(item["path"]).resolve() == path.resolve(), "actual export output path")
    source, reference = checked(source_ref), checked(reference_ref)
    complete = checked(export_ref, 16384)
    compact = rows(source)
    require(compact == rows(reference) and len(compact) == 1464
            and sum(row["bytes"] for row in compact) == 59279032
            and pin(canonical(compact)) == anchor["complete_rows_JSON"] == ROWS28,
            "complete Source28 SDK rows differ")
    changed = {row["relative"] for row in anchor["output_pins"]}
    old_rows = {row["relative"]: row for row in rows(previous)}
    new_rows = {row["relative"]: row for row in compact}
    require(set(old_rows) < set(new_rows)
            and set(new_rows) - set(old_rows) == {"xar_autoplayer/bridge/tactical_clock_diagnostics_v1.py", "xar_autoplayer/bridge/mcp_tool_result_contract_v1.py"}
            and {name for name in new_rows if old_rows.get(name) != new_rows[name]} == changed
            and all(new_rows[row["relative"]] == row for row in anchor["output_pins"]),
            "only fourteen exact Source28 canonical SDK leaves may change")
    require(complete["schema"] == "xar.ck3.immutable-sdk-view-export/v1"
            and complete["status"] == "SOURCE_READY_NOT_LOADED"
            and complete["machine_id"] == MACHINE
            and complete["manifests"] == [source_ref, reference_ref]
            and all(exact_int(complete[name], 0) for name in ("old_content_write_operations", "game_sdk_native_obs_calls"))
            and exact_int(complete["new_unique_file_count"], 28)
            and exact_int(complete["existing_shared_unique_file_count"], 1450)
            and set(complete["changed_relative_paths"]) == changed
            and complete["logical_bytes_each"] == 59279032, "actual fourteen-leaf dual export receipt")
    require(source["source_root"] == str(SRC.resolve())
            and reference["source_root"] == str(REFERENCE.resolve())
            and all(doc["business_source_commit"] == anchor["commit"]
                    for doc in (source, reference, complete))
            and all(doc["machine_id"] == MACHINE and doc["status"] == "FINAL_SOURCE_FROZEN"
                    and doc["base_freeze"] == history["source27_BASE"]
                    and doc["git_head"] == previous["git_head"]
                    and doc["sdk_generation"] == "P37C23" and doc["runtime_admitted"] is False
                    and doc["native_dll_sha256"] == OLD.OLD.DLL and doc["native_build_label"] == OLD.OLD.LABEL
                    and "native_transition" not in doc and "canonical_preload_policy" not in doc
                    for doc in (source, reference))
            and source["capacity_admission"] == reference["capacity_admission"] == complete["capacity"],
            "actual generic provenance and inherited native contract")
    original = {row["relative"]: row for row in old_source["files"]}
    new_ids, shared = set(), set()
    old_ids = {file_id(row) for row in original.values()}
    for document in (source, reference):
        for row in document["files"]:
            name, key = row["relative"], file_id(row)
            if name in changed:
                require(row["storage_mode"] == "independent_new_blob"
                        and key not in old_ids and key not in new_ids, "changed blob identity alias")
                new_ids.add(key)
            else:
                require(row["storage_mode"] == "existing_frozen_hardlink"
                        and key == file_id(original[name])
                        and row["hardlink_source"]["freeze_sha256"] == history["source27_BASE"]["sha256"]
                        and Path(row["hardlink_source"]["path"]).resolve()
                        == Path(previous["source_root"]).resolve() / name,
                        "unchanged leaf must preserve Source27 FileID")
                shared.add(key)
    require(len(new_ids) == 28 and len(shared) == 1450, "physical identity closure differs")
    result = dict(source)
    result.update(schema="root.ck3.final-sdk-freeze/v1", files=compact,
        compact_at_utc=observed_at_utc, attempt_id="a12",
        immutable_ntfs_inventory=source_ref, source_inventory_reference=source_ref,
        independent_reference=reference_ref, immutable_source_export=export_ref,
        native_transition=previous["native_transition"],
        native_transition_inherited_from_actual_source27_BASE=True,
        native_transition_inheritance={"source28_generic_export_has_transition": False, **history},
        rich_manifest_campaign_flags_are_exporter_defaults_not_runtime_facts=True,
        clean_campaign=False, prior_campaign_state_or_credits_inherited=True,
        source27_canonical_anchor=history["source27_anchor"], source28_canonical_anchor=anchor_ref,
        source28_parent_commit=PARENT, source28_canonical_patch_rows=anchor["canonical_patch_rows"],
        source28_output_pins=anchor["output_pins"], runtime_owner_generation="P37C23",
        actual_native_loaded=False, H="NOTRUN", runtime_admitted=False,
        source28_natural_runtime="NOTRUN", new_campaign_credit=0,
        campaign_start_date_raw=53144328, campaign_endpoint_date_raw=53407128,
        planned_saved_opening_date_raw=53274624,
        continuation_basis="SAVE10480/cycles4753/day5429; original T0/end/wall retained; no Source28 live credit")
    raw = encoded(result)
    require(len(raw) <= BASE_HARD and "canonical_preload_policy" not in result, "policy-free BASE 512 KiB")
    return raw, dict(machine_id=MACHINE, observed_at_utc=observed_at_utc,
        status="RAM_BASE_COMPOSED_NOT_WRITTEN_NOT_LOADED", compact_BASE=pin(raw),
        source_file_count=1464, source_bytes=59279032, complete_rows_JSON=ROWS28,
        actual_new_FileIDs=28, actual_shared_FileIDs=1450,
        inputs=dict(source=source_ref, reference=reference_ref, export=export_ref,
                    anchor=anchor_ref, native_history=history),
        policy_added=False, outputs_created=0, runtime_calls=0, Git_calls=0, export_calls=0)
