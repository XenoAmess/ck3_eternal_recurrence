"""Source30 finite dual export/BASE preparation."""
from __future__ import annotations
from pathlib import Path
import re
import sys
from types import SimpleNamespace
from typing import Literal, TypedDict
sys.dont_write_bytecode = True
OWN = Path(__file__).resolve()
sys.path.insert(0, str(OWN.parent))
import write_source30_canonical_ref_v1 as WRITER
import write_source27_canonical_ref_v1 as W
import prepare_source29_export_base_v1 as PREVIOUS
import prepare_source28_export_base_v1 as RUNTIME

Doc = dict[str, object]
MACHINE, PARENT = WRITER.MACHINE, WRITER.PARENT
REPO, P, N = OWN.parents[2], WRITER.PREP, WRITER.P
SOURCE29_ROOT = N / "sdk-v20261019-candidate/src29"
SOURCE29_REFERENCE = N / "sdk-v20261019-candidate/src29-independent"
SRC = N / "sdk-v20261019-candidate/src30"
REFERENCE = N / "sdk-v20261019-candidate/src30-independent"
OUT = P / "immutable-source-export-source30"
BASE = P / "ROOT-FINAL-SDK-SOURCE30-BASE.json"
ANCHOR = P / "source30-canonical01/SOURCE30-CANONICAL-ANCHOR.json"
EXPORTER = OWN.parent / "export_immutable_sdk_views_v1.py"
BASE_HARD, META_HARD, FS_HARD, STAGE_HARD = 524288, 4194304, 262144, 12582912
PREVIOUS_PIN: W.Pin = {"bytes":21255,"sha256":"76120480882fd119175d120085b997c84418be01fe2614bd47d63c0f0f8ab2a0"}
EXPORTER_PIN: W.Pin = {"bytes":22964,"sha256":"8b6972ac2a82b30c92b531c640df0eb9aa6e43cc205ab9d7d23796d5739da432"}
W.require(W.pin(W.read(OWN.parent/"prepare_source29_export_base_v1.py",32768))==PREVIOUS_PIN,
          "original Source29 renderer changed")

class ViewBudget(TypedDict):
    changed_leaf_count: int
    independent_new_FileIDs: int
    unchanged_shared_FileIDs: int
    dual_changed_cluster_upper: int
    rich_JSON_including_FS_MFT: int
    separate_compact_BASE: int
    compact_target: str
    complete_export_BASE_hard_bytes: int

class Capacity(TypedDict):
    schema: Literal["xar.ck3.immutable-sdk-view-capacity/v1"]
    status: Literal["ADMITTED"]
    machine_id: str
    observed_at_utc: str
    review_at_utc: str
    business_source_commit: str
    runtime_source_commit: str
    base_freeze_sha256: str
    native_pin_sha256: str
    sdk_generation: str
    base_source_root: str
    source_destination: str
    reference_destination: str
    output_root: str
    approved_output_roots: list[str]
    metadata_reserve_bytes: int
    filesystem_metadata_reserve_bytes: int
    new_allocation_limit_bytes: int
    disk_reserve_bytes: int
    stage_aggregate_hard_bytes: int
    stage_admission: W.FileRef
    business_anchor_actual: W.FileRef
    source29_history: Doc
    sourcepins: dict[str,W.FileRef]
    view_budget: ViewBudget
    all_old_hard_holds_retained: bool
    physical_credit_bytes: int
    permission: str

class BASEReport(TypedDict):
    machine_id: str
    observed_at_utc: str
    status: Literal["RAM_BASE_COMPOSED_NOT_WRITTEN_NOT_LOADED"]
    compact_BASE: W.Pin
    source_file_count: int
    source_bytes: int
    complete_rows_JSON: W.Pin
    actual_new_FileIDs: int
    actual_shared_FileIDs: int
    inputs: Doc
    policy_added: bool
    outputs_created: int
    runtime_calls: int
    Git_mutations: int
    export_calls: int

def checked(item: W.FileRef, limit: int = 4194304) -> Doc:
    strict = W.parse_ref(item)
    loaded: object = W.load(W.checked(strict, limit))
    if not isinstance(loaded,dict):raise TypeError("JSON object required")
    result: Doc = {}
    for key,value in loaded.items():
        if not isinstance(key,str):raise TypeError("JSON key required")
        result[key]=value
    return result

def rows(document: Doc) -> list[W.Row]:
    result: list[W.Row] = []
    for value in W.sequence(document["files"]):
        d = W.obj(value)
        name = W.string(d["relative"])
        W.require(not name.startswith(("/", "\\")) and "\\" not in name
                  and all(part not in ("", ".", "..") for part in name.split("/")), "unsafe SDK relative")
        result.append({"relative":name,"bytes":W.integer(d["bytes"]),"sha256":W.hexstr(d["sha256"],64),
            "git_blob_sha1":W.hexstr(d["git_blob_sha1"],40),"git_mode":W.string(d["git_mode"])})
    W.require(len(result)==len({r["relative"] for r in result})
              and len(result)==W.integer(document["source_file_count"])
              and sum(r["bytes"] for r in result)==W.integer(document["source_bytes"])
              and all(r["git_mode"]=="100644" for r in result), "complete ordinary SDK rows")
    return sorted(result, key=lambda r:r["relative"])

def output_rows(anchor: Doc) -> list[W.Row]:
    values=W.sequence(anchor["output_pins"])
    result=rows({"files":values,"source_file_count":4,
        "source_bytes":sum(W.integer(W.obj(v)["bytes"]) for v in values)})
    W.require({r["relative"] for r in result}==set(WRITER.SDK)
        and all({"bytes":r["bytes"],"sha256":r["sha256"]}==WRITER.POST_PINS[r["relative"]] for r in result),
        "exact Source30 four SDK output pins")
    return result

def actual_source29_v1() -> tuple[Doc,Doc,Doc]:
    """Authenticate the sealed immediate parent; historical ancestors stay historical."""
    base=checked(WRITER.SOURCE29_BASE,BASE_HARD)
    anchor=checked(WRITER.SOURCE29_ANCHOR,65536)
    W.require(base["schema"]=="root.ck3.final-sdk-freeze/v1"
        and base["machine_id"]==MACHINE and base["business_source_commit"]==PARENT
        and anchor["machine_id"]==MACHINE and anchor["commit"]==PARENT
        and anchor["schema"]=="xar.source29.canonical-git-anchor/v1"
        and anchor["status"]=="CANONICAL_REF_CREATED_NOT_DEPLOYED"
        and base["source29_canonical_anchor"]==WRITER.SOURCE29_ANCHOR
        and base["status"]=="FINAL_SOURCE_FROZEN" and base["runtime_admitted"] is False
        and "canonical_preload_policy" not in base,"sealed policy-free Source29")
    source_ref=W.parse_ref(base["source_inventory_reference"])
    reference_ref=W.parse_ref(base["independent_reference"])
    export_ref=W.parse_ref(base["immutable_source_export"])
    source,reference,complete=checked(source_ref),checked(reference_ref),checked(export_ref,16384)
    compact=rows(base)
    W.require(len(compact)==1464 and compact==rows(source)==rows(reference)
        and W.pin(W.canonical(compact))==anchor["complete_rows_JSON"]
        and complete["manifests"]==[source_ref,reference_ref]
        and W.integer(complete["old_content_write_operations"])==0
        and Path(W.string(source["source_root"])).resolve()==SOURCE29_ROOT.resolve()
        and Path(W.string(reference["source_root"])).resolve()==SOURCE29_REFERENCE.resolve()
        and source["source_root"]==base["source_root"]
        and all(d["business_source_commit"]==PARENT and d["machine_id"]==MACHINE for d in (source,reference,complete)),
        "complete actual Source29 inventories")
    history:Doc={"source29_BASE":WRITER.SOURCE29_BASE,"source29_anchor":WRITER.SOURCE29_ANCHOR,
        "source29_source_inventory":source_ref,"source29_independent_reference":reference_ref,
        "source29_immutable_export":export_ref,"inherited_native_history":base["native_transition_inheritance"]}
    return base,source,history

def actual_anchor_v1(anchor_ref: W.FileRef) -> Doc:
    anchor=checked(anchor_ref,65536)
    W.require(Path(anchor_ref["path"]).resolve()==ANCHOR.resolve()
        and anchor["schema"]=="xar.source30.canonical-git-anchor/v1"
        and anchor["machine_id"]==MACHINE and anchor["status"]=="CANONICAL_REF_CREATED_NOT_DEPLOYED"
        and anchor["execution_owner"]=="Root" and anchor["root_direct_execution_release"] is True
        and anchor["parent"]==PARENT and anchor["ref"]==WRITER.REF
        and W.integer(anchor["future_writes"])==0
        and all(W.integer(anchor[n])==0 for n in ("runtime_calls","SDK_export_calls","push_calls",
            "index_or_tracked_worktree_mutations")),"actual finite Source30 Root anchor")
    W.require(W.parse_ref(anchor["writer"])==W.file_ref(OWN.parent/"write_source30_canonical_ref_v1.py")
        and anchor["actual_Source29_anchor"]==WRITER.SOURCE29_ANCHOR
        and anchor["actual_Source29_BASE"]==WRITER.SOURCE29_BASE,"writer and immediate parent")
    plan=WRITER.parse_plan(W.load(W.checked(W.parse_ref(anchor["source_plan"]))))
    W.require(plan["machine_id"]==MACHINE and plan["parent"]==PARENT and plan["ref"]==WRITER.REF
        and plan["source29_anchor"]==WRITER.SOURCE29_ANCHOR and plan["source29_BASE"]==WRITER.SOURCE29_BASE
        and plan["source_file_count"]==W.integer(anchor["source_file_count"])==1465
        and plan["source_bytes"]==W.integer(anchor["source_bytes"])==59299236
        and plan["target_tree"]==W.hexstr(anchor["tree"],40)
        and plan["complete_rows_JSON"]==W.parse_pin(anchor["complete_rows_JSON"])
        and plan["Git_object_quote"]==anchor["Git_object_quote"]
        and plan["public_source_commit"]==anchor["public_source_commit"]
        and plan["public_inputs"]==anchor["public_inputs"]
        and plan["qualifications"]==anchor["qualifications"] and W.integer(anchor["source_epoch_count"])==39,
        "source plan single contract")
    changed=output_rows(anchor)
    W.require(anchor["canonical_patch_rows"]==WRITER.canonical_patch_rows_v1(plan),"four typed patch rows")
    git=W.Git(REPO,P/"source30-canonical01")
    commit=W.hexstr(anchor["commit"],40)
    W.require(commit!=PARENT and git.get("rev-parse",WRITER.REF).strip().decode()==commit
        and git.get("rev-parse",commit+"^{tree}").strip().decode()==plan["target_tree"]
        and git.get("rev-list","--parents","-n","1",commit).strip().decode().split()==[commit,PARENT],
        "actual canonical Git commit/tree/parent/ref")
    inventory={v.decode() for v in git.get("diff-tree","--no-commit-id","--name-only","-r","-z",PARENT,commit).split(b"\0") if v}
    W.require(inventory=={WRITER.PREFIX+r["relative"] for r in changed},"actual four delta Git paths")
    return anchor

def card_template_v1(*, anchor_ref: W.FileRef, stage_admission_ref: W.FileRef,
                     review_at_utc: str, disk_reserve_bytes: int) -> Capacity:
    W.require(sys.dont_write_bytecode,"Python -B required")
    base, _, history = actual_source29_v1()
    anchor = actual_anchor_v1(anchor_ref)
    stage = checked(stage_admission_ref,65536)
    expiry = W.date(review_at_utc)
    offset = expiry.utcoffset()
    W.require(stage["machine_id"]==MACHINE and stage["status"]=="ADMITTED"
        and expiry==W.date(stage["review_at_utc"]) and offset is not None
        and offset.total_seconds()==0 and W.utc()<expiry
        and type(disk_reserve_bytes) is int and disk_reserve_bytes>=0, "finite actual stage/floor")
    roots = [Path(W.string(v)).resolve() for v in W.sequence(stage["approved_output_roots"])]
    W.require(all(any(path.resolve()==root or path.resolve().is_relative_to(root) for root in roots)
        for path in (SRC,REFERENCE,OUT,BASE)), "finite export approved roots")
    exporter = W.file_ref(EXPORTER)
    W.require({"bytes":exporter["bytes"],"sha256":exporter["sha256"]}==EXPORTER_PIN,"original exporter changed")
    count = len(output_rows(anchor))
    data = 2*sum(((r["bytes"]+4095)//4096)*4096 for r in output_rows(anchor))
    total = data+META_HARD+BASE_HARD
    W.require(total<=STAGE_HARD,"dual export and BASE exceed 12 MiB")
    transition = W.obj(base["native_transition"])
    native_ref = W.parse_ref(transition["target_native_pin"])
    native = checked(native_ref,32768)
    W.require(native["machine_id"]==MACHINE and native["native_dll_sha256"]==base["native_dll_sha256"]
        and native["native_build_label"]==base["native_build_label"],"inherited Native30 export authority")
    return {"schema":"xar.ck3.immutable-sdk-view-capacity/v1","status":"ADMITTED","machine_id":MACHINE,
        "observed_at_utc":W.utc().isoformat(),"review_at_utc":W.string(stage["review_at_utc"]),
        "business_source_commit":W.hexstr(anchor["commit"],40),"runtime_source_commit":W.hexstr(base["git_head"],40),
        "base_freeze_sha256":WRITER.SOURCE29_BASE["sha256"],"native_pin_sha256":native_ref["sha256"],
        "sdk_generation":"P37C23","base_source_root":W.string(base["source_root"]),
        "source_destination":str(SRC.resolve()),"reference_destination":str(REFERENCE.resolve()),
        "output_root":str(OUT.resolve()),"approved_output_roots":[str(p.resolve()) for p in (SRC,REFERENCE,OUT,P)],
        "metadata_reserve_bytes":META_HARD,"filesystem_metadata_reserve_bytes":FS_HARD,
        "new_allocation_limit_bytes":data+META_HARD,"disk_reserve_bytes":disk_reserve_bytes,
        "stage_aggregate_hard_bytes":STAGE_HARD,"stage_admission":stage_admission_ref,
        "business_anchor_actual":anchor_ref,"source29_history":history,
        "sourcepins":{"generic_exporter":exporter,"RAM_plan_renderer":W.file_ref(OWN),
            "Source30_writer":W.file_ref(OWN.parent/"write_source30_canonical_ref_v1.py"),
            "original_Source29_renderer":W.file_ref(OWN.parent/"prepare_source29_export_base_v1.py")},
        "view_budget":{"changed_leaf_count":count,"independent_new_FileIDs":2*count,"unchanged_shared_FileIDs":1465-count,
            "dual_changed_cluster_upper":data,"rich_JSON_including_FS_MFT":META_HARD,
            "separate_compact_BASE":BASE_HARD,"compact_target":str(BASE.resolve()),
            "complete_export_BASE_hard_bytes":total},
        "all_old_hard_holds_retained":True,"physical_credit_bytes":0,
        "permission":"Root dual export/create-only BASE; no runtime grant"}

def export_args_v1(*, capacity_ref: W.FileRef, anchor_ref: W.FileRef) -> SimpleNamespace:
    card = checked(capacity_ref,65536)
    expected = card_template_v1(anchor_ref=anchor_ref,stage_admission_ref=W.parse_ref(card["stage_admission"]),
        review_at_utc=W.string(card["review_at_utc"]),disk_reserve_bytes=W.integer(card["disk_reserve_bytes"]))
    W.require(all(card.get(k)==v for k,v in expected.items() if k!="observed_at_utc"),"exact export card")
    W.require(not BASE.exists(),"BASE create-only")
    base, _, _ = actual_source29_v1()
    native_ref = W.parse_ref(W.obj(base["native_transition"])["target_native_pin"])
    host: object = RUNTIME.HOST
    if not isinstance(host,Path):
        raise TypeError("original runtime source host Path required")
    return SimpleNamespace(business_source_repo=REPO,runtime_source_repo=host,
        business_source_commit=W.string(card["business_source_commit"]),
        runtime_source_commit=W.string(card["runtime_source_commit"]),
        base_freeze=Path(WRITER.SOURCE29_BASE["path"]),base_freeze_sha256=WRITER.SOURCE29_BASE["sha256"],
        native_pin=Path(native_ref["path"]),native_pin_sha256=native_ref["sha256"],
        capacity_card=Path(capacity_ref["path"]),capacity_card_sha256=capacity_ref["sha256"],
        machine_id=MACHINE,sdk_generation="P37C23",source_destination=SRC,reference_destination=REFERENCE,output_root=OUT)

def file_id(row: Doc) -> tuple[int,str]:
    identity = W.obj(row["file_identity"])
    volume = W.integer(identity["volume_serial"])
    opaque = W.string(identity["file_id"])
    W.require(identity["filesystem"]=="NTFS" and identity["directory"] is False and 0<volume<=4294967295
        and re.fullmatch("[0-9a-f]{16,32}",opaque) is not None,"opaque exact NTFS identity")
    return volume,opaque

def rich_rows(document: Doc) -> dict[str,Doc]:
    return {W.string(r["relative"]):r for r in (W.obj(v) for v in W.sequence(document["files"]))}

def compose_compact_base_v1(*, source_ref: W.FileRef, reference_ref: W.FileRef,
        export_ref: W.FileRef, anchor_ref: W.FileRef, observed_at_utc: str) -> tuple[bytes,BASEReport]:
    W.require(abs((W.utc()-W.date(observed_at_utc)).total_seconds())<=600,"fresh actual observation")
    previous, old_source, history = actual_source29_v1()
    anchor = actual_anchor_v1(anchor_ref)
    for item,path in ((source_ref,OUT/"SOURCE-FREEZE.json"),(reference_ref,OUT/"REFERENCE-FREEZE.json"),
                      (export_ref,OUT/"COMPLETE.json")):
        W.require(Path(item["path"]).resolve()==path.resolve(),"actual output path")
    source, reference, complete = checked(source_ref),checked(reference_ref),checked(export_ref,16384)
    compact = rows(source)
    W.require(compact==rows(reference) and len(compact)==1465
        and sum(r["bytes"] for r in compact)==W.integer(anchor["source_bytes"])
        and W.pin(W.canonical(compact))==anchor["complete_rows_JSON"],"complete Source30 SDK rows")
    changed = {r["relative"] for r in output_rows(anchor)}
    count = len(changed)
    old_rows, new_rows = ({r["relative"]:r for r in rows(previous)},{r["relative"]:r for r in compact})
    W.require(set(new_rows)-set(old_rows)=={WRITER.SDK[2]} and set(old_rows)<=set(new_rows)
        and {n for n in new_rows if old_rows.get(n)!=new_rows[n]}==changed
        and all(new_rows[r["relative"]]==r for r in output_rows(anchor)), "only exact changed SDK leaves")
    W.require(complete["schema"]=="xar.ck3.immutable-sdk-view-export/v1"
        and complete["status"]=="SOURCE_READY_NOT_LOADED" and complete["machine_id"]==MACHINE
        and complete["manifests"]==[source_ref,reference_ref]
        and all(W.integer(complete[n])==0 for n in ("old_content_write_operations","game_sdk_native_obs_calls"))
        and W.integer(complete["new_unique_file_count"])==2*count
        and W.integer(complete["existing_shared_unique_file_count"])==1465-count
        and {W.string(v) for v in W.sequence(complete["changed_relative_paths"])}==changed
        and W.integer(complete["logical_bytes_each"])==W.integer(anchor["source_bytes"]), "actual dual receipt")
    W.require(source["source_root"]==str(SRC.resolve()) and reference["source_root"]==str(REFERENCE.resolve())
        and all(d["business_source_commit"]==anchor["commit"] for d in (source,reference,complete))
        and all(d["machine_id"]==MACHINE and d["status"]=="FINAL_SOURCE_FROZEN"
            and d["base_freeze"]==WRITER.SOURCE29_BASE and d["git_head"]==previous["git_head"]
            and d["sdk_generation"]=="P37C23" and d["runtime_admitted"] is False
            and d["native_dll_sha256"]==previous["native_dll_sha256"]
            and d["native_build_label"]==previous["native_build_label"]
            and "native_transition" not in d and "canonical_preload_policy" not in d for d in (source,reference))
        and source["capacity_admission"]==reference["capacity_admission"]==complete["capacity"],
        "generic export and historical native provenance")
    original = rich_rows(old_source)
    old_ids = {file_id(r) for r in original.values()}
    new_ids: set[tuple[int,str]] = set()
    shared: set[tuple[int,str]] = set()
    for document in (source,reference):
        for name,row in rich_rows(document).items():
            key = file_id(row)
            if name in changed:
                W.require(row["storage_mode"]=="independent_new_blob" and key not in old_ids
                    and key not in new_ids,"changed blob FileID alias")
                new_ids.add(key)
            else:
                hardlink = W.obj(row["hardlink_source"])
                W.require(row["storage_mode"]=="existing_frozen_hardlink" and key==file_id(original[name])
                    and hardlink["freeze_sha256"]==WRITER.SOURCE29_BASE["sha256"]
                    and Path(W.string(hardlink["path"])).resolve()==Path(W.string(previous["source_root"]))/name,
                    "unchanged leaf Source29 FileID")
                shared.add(key)
    W.require(len(new_ids)==2*count and len(shared)==1465-count,"physical identity closure")
    result: Doc = dict(source)
    result.update(schema="root.ck3.final-sdk-freeze/v1",files=compact,compact_at_utc=observed_at_utc,
        immutable_ntfs_inventory=source_ref,source_inventory_reference=source_ref,
        independent_reference=reference_ref,immutable_source_export=export_ref,
        native_transition=previous["native_transition"],native_transition_inherited_from_actual_source29_BASE=True,
        native_transition_inheritance={"source30_generic_export_has_transition":False,**history},
        clean_campaign=False,prior_campaign_state_or_credits_inherited=True,
        source29_canonical_anchor=WRITER.SOURCE29_ANCHOR,source30_canonical_anchor=anchor_ref,
        source30_parent_commit=PARENT,source30_canonical_patch_rows=anchor["canonical_patch_rows"],
        source30_output_pins=anchor["output_pins"],runtime_owner_generation="P37C23",actual_native_loaded=False,
        H="NOTRUN",runtime_admitted=False,source30_natural_runtime="NOTRUN",new_campaign_credit=0,
        campaign_start_date_raw=53144328,campaign_endpoint_date_raw=53407128,
        planned_saved_opening_date_raw=53274624,
        continuation_basis="SAVE10480/cycles4753/day5429; original T0/end/wall retained; no Source30 live credit")
    body = W.canonical(result)+b"\n"
    W.require(len(body)<=BASE_HARD and "canonical_preload_policy" not in result,"policy-free BASE 512 KiB")
    report: BASEReport = {"machine_id":MACHINE,"observed_at_utc":observed_at_utc,
        "status":"RAM_BASE_COMPOSED_NOT_WRITTEN_NOT_LOADED","compact_BASE":W.pin(body),
        "source_file_count":1465,"source_bytes":W.integer(anchor["source_bytes"]),
        "complete_rows_JSON":W.parse_pin(anchor["complete_rows_JSON"]),"actual_new_FileIDs":2*count,
        "actual_shared_FileIDs":1465-count,"inputs":{"source":source_ref,"reference":reference_ref,
            "export":export_ref,"anchor":anchor_ref,"native_history":history},"policy_added":False,
        "outputs_created":0,"runtime_calls":0,"Git_mutations":0,"export_calls":0}
    return body,report

