"""Original09+11 exporter wrapper; default OFF."""
from datetime import datetime, timezone
import hashlib
import importlib
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace

OWN=Path(__file__).resolve().parent
REPO=OWN.parents[1]
N=Path("D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep")
T=N/"robert30-v20261019-campaign01/runtime"
O=N/"p51-fresh1066-v20261019-prepare01/c23-source23-native30-cold100"
B=Path("D:/codex-ck3-demos/2026-10-19-robert-v20261019-storage01")
HOST=N/"sdk-v20261019-candidate/host-checkout"
SRC=N/"sdk-v20261019-candidate/src20"
REF=N/"sdk-v20261019-candidate/reference-c23-a03/src"
OUT=O/"immutable-source-export-a03"
BASE=O/"ROOT-FINAL-SDK-SOURCE25-BASE.json"
MACHINE="xenoamess-full-tower-eb9d2c1186"
OLD_CARD=B/"SOURCE24-COMBINED21MiB-NATIVE30-EXACT-EXPORTER-ADMITTED01.json"
OLD_CARD_SHA="d292e9efc7c28f20190b7d3d9b74fbb330bc87f7f154b49c9756193c708cc23f"
MODULE_PINS={
 "export_native30_functional_artifact_views_v1.py":"c414dde8b9557837feaa27591fab38f2ab2a606ef8792bc21e1731955b072d99",
 "native30_functional09_artifact11_transition_v1.py":"1df6088a521f2de2f9d72d6686d161a87a28cd74a6cb35bbc59e02013e0b4442",
 "native29_to30_export_contract_v1.py":"d348b59cdf68a2da0928ccfc4034006c0c42618fe341ad0ca1c7dac1bbfa7554",
 "export_native30_immutable_sdk_views_v1.py":"90ccd7a5c12d90101217391857d793715fdaebcb98a3e374e6a5d4b3776f9369",
 "native30_export_adapter_v1.py":"2d4074379371ed91bc38ff0fc532521e277ba2795faad1fd8e9c6dd2593c5298",
 "export_immutable_sdk_views_v1.py":"8b6972ac2a82b30c92b531c640df0eb9aa6e43cc205ab9d7d23796d5739da432",
 "native30_resume_fixture_chain_v1.py":"d9e5dc3c22f3b1fc58f1ab7b93de4f7ccb480c3ed938fdc6b2375d11a814f555",
 "prepare_source25_compact_base_v1.py":"cef3a22cedd37844bc09913148f0e2f49a351759fc7bdd9b162c8b793d23d15b"}
sys.path.insert(0,str(OWN.parent))
from g2_saved_campaign.prepare_source25_compact_base_v1 import read_document,require,pin


def ref(path):
    path=Path(path).resolve(strict=True)
    with path.open("rb") as stream:raw=stream.read(2097153)
    require(len(raw)<=2097152,"bounded source or JSON required")
    return {"path":str(path),**pin(raw)}


def checked_sources():
    result={}
    for name,digest in MODULE_PINS.items():
        row=ref(OWN/name);require(row["sha256"]==digest,"dependency differs: "+name)
        for alias in (Path(name).stem,"g2_saved_campaign."+Path(name).stem):
            mod=sys.modules.get(alias)
            require(mod is None or Path(mod.__file__).resolve()==(OWN/name).resolve(),"foreign cached exporter module")
        result[name]=row
    result[Path(__file__).name]=ref(__file__)
    return result


def card_template_v1(*,anchor_ref,review_at_utc,disk_reserve_bytes,stage_admission_ref):
    """RAM template; storage separately admits and writes the card."""
    require(sys.dont_write_bytecode,"run Python with -B")
    anchor=read_document(anchor_ref,65536)
    require(anchor.get("schema")=="xar.source25.canonical-git-anchor/v1"
        and anchor.get("machine_id")==MACHINE and anchor.get("parent")=="6b55531b1d3a44ee73ab13ea40132556030f682e"
        and anchor.get("status")=="CANONICAL_REF_CREATED_NOT_DEPLOYED"
        and anchor.get("source_file_count")==1460 and anchor.get("source_bytes")==59234989,
        "actual Source25 anchor required")
    oldref=ref(OLD_CARD);require(oldref["sha256"]==OLD_CARD_SHA,"original transition card source differs")
    old=read_document(oldref)
    require(type(disk_reserve_bytes) is int and disk_reserve_bytes>=0,"actual full-holds disk reserve required")
    deadline=datetime.fromisoformat(review_at_utc.replace("Z","+00:00"))
    require(deadline.tzinfo is not None and datetime.now(timezone.utc)<deadline,"capacity expired")
    value={key:old[key] for key in ("schema","status","runtime_source_commit","base_freeze_sha256",
        "native_pin_sha256","sdk_generation","base_source_root","native_transition","Native_transition_refs_actual")}
    value.update(machine_id=MACHINE,business_source_commit=anchor["commit"],
        observed_at_utc=datetime.now(timezone.utc).isoformat(),review_at_utc=review_at_utc,
        source_destination=str(SRC),reference_destination=str(REF),output_root=str(OUT),
        approved_output_roots=list(map(str,(SRC,REF,OUT,O))),
        metadata_reserve_bytes=4194304,filesystem_metadata_reserve_bytes=262144,
        new_allocation_limit_bytes=12271616,disk_reserve_bytes=disk_reserve_bytes,
        stage_aggregate_hard_bytes=20971520,stage_admission=stage_admission_ref,
        business_anchor_actual=anchor_ref,sourcepins=checked_sources(),
        view_budget={"dual_changed_cluster_upper":8077312,"rich_JSON_including_FS_MFT":4194304,
            "export_total":12271616,"separate_compact_freeze":524288,
            "compact_target":str(BASE),"native_session_upper":16384,
            "small_refs_upper":65536,"complete_export_hard_bytes":13631488},
        permission="Root export/BASE only; no runtime grant.",
        all_old_hard_holds_retained=True,physical_credit_bytes=0)
    return value


def export_args_v1(*,capacity_ref,anchor_ref):
    card=read_document(capacity_ref)
    expected=card_template_v1(anchor_ref=anchor_ref,review_at_utc=card["review_at_utc"],
        disk_reserve_bytes=card["disk_reserve_bytes"],stage_admission_ref=card["stage_admission"])
    require(all(card.get(k)==v for k,v in expected.items() if k!="observed_at_utc"),
        "concrete export card differs")
    require(card.get("status")=="ADMITTED","admitted card required")
    return SimpleNamespace(business_source_repo=REPO,runtime_source_repo=HOST,
        business_source_commit=card["business_source_commit"],runtime_source_commit=card["runtime_source_commit"],
        base_freeze=T/"ROOT-FINAL-SDK-FREEZE-P37C22.json",base_freeze_sha256=card["base_freeze_sha256"],
        native_pin=T/"ROOT-NATIVE29-NATIVE-PIN-C16.json",native_pin_sha256=card["native_pin_sha256"],
        capacity_card=Path(capacity_ref["path"]),capacity_card_sha256=capacity_ref["sha256"],
        machine_id=MACHINE,sdk_generation="P37C23",source_destination=SRC,reference_destination=REF,output_root=OUT)


def execute_v1(*,capacity_ref,anchor_ref,execute=False):
    if execute is not True:return {"status":"DISABLED","outputs_created":False}
    args=export_args_v1(capacity_ref=capacity_ref,anchor_ref=anchor_ref)
    require(not BASE.exists(),"compact BASE is create-only")
    wrapper=importlib.import_module("g2_saved_campaign.export_native30_functional_artifact_views_v1")
    wrapper.export_native30_views_v1(args,execute=True)
    from g2_saved_campaign.prepare_source25_compact_base_v1 import compose_compact_base_v1
    base,report=compose_compact_base_v1(source_ref=ref(OUT/"SOURCE-FREEZE.json"),
        reference_ref=ref(OUT/"REFERENCE-FREEZE.json"),export_ref=ref(OUT/"COMPLETE.json"),
        anchor_ref=anchor_ref,observed_at_utc=datetime.now(timezone.utc).isoformat())
    with BASE.open("xb") as stream:stream.write(base);stream.flush();os.fsync(stream.fileno())
    require(ref(BASE)["sha256"]==pin(base)["sha256"],"BASE actual readback differs")
    return {"machine_id":MACHINE,"status":"SOURCE25_DUAL_EXPORTED_BASE_CREATED_NOT_RUNTIME",
        "capacity":capacity_ref,"anchor":anchor_ref,"compact_BASE":ref(BASE),"report":report}

