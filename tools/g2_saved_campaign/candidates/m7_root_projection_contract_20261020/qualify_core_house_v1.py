"""Qualify two pure DTO guards; preserve old bytes."""
import ctypes
from ctypes import wintypes as w
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import types

import qualify_v1 as prior


def allocated(root):
    class Info(ctypes.Structure):
        _fields_ = [("allocation", ctypes.c_longlong), ("size", ctypes.c_longlong),
                    ("links", w.DWORD), ("deleted", w.BYTE), ("directory", w.BYTE)]
    api = ctypes.WinDLL("kernel32", use_last_error=True)
    api.CreateFileW.argtypes = [w.LPCWSTR,w.DWORD,w.DWORD,ctypes.c_void_p,w.DWORD,w.DWORD,w.HANDLE]
    api.CreateFileW.restype = w.HANDLE
    api.GetFileInformationByHandleEx.argtypes = [w.HANDLE,ctypes.c_int,ctypes.c_void_p,w.DWORD]
    api.GetFileInformationByHandleEx.restype = w.BOOL
    api.CloseHandle.argtypes = [w.HANDLE]
    api.CloseHandle.restype = w.BOOL
    total = 0
    for path in [root, *root.rglob("*")]:
        if path.is_symlink():
            raise ValueError("owned lane contains link")
        handle = api.CreateFileW(str(path),0x80,7,None,3,0x02000000,None)
        if handle == ctypes.c_void_p(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            info = Info()
            if not api.GetFileInformationByHandleEx(handle,1,ctypes.byref(info),ctypes.sizeof(info)):
                raise ctypes.WinError(ctypes.get_last_error())
            total += info.allocation
        finally:
            if not api.CloseHandle(handle):
                raise ctypes.WinError(ctypes.get_last_error())
    return total


def main():
    started = prior.now()
    card = prior.BUDGET.parent / "G2-M7-SOURCE-EXTRA16KiB0630-ADMITTED01.json"
    if prior.pin(card)["sha256"] != "2e18a9ee68c4bd2faa8a0dd9907fcb771e2f2698bd8455107f9a816a5f0e0979":
        raise ValueError("exact corrective budget differs")
    admission = json.loads(card.read_bytes())
    if (admission["machine_id"] != prior.MACHINE or admission["source_hard_bytes"] != 81920
            or admission["artifact_hard_bytes"] != 196608
            or datetime.now(timezone.utc) >= datetime.fromisoformat(admission["review_at_utc"])):
        raise ValueError("budget invalid/expired")
    before_alloc = {"Z":allocated(prior.HERE), "D":allocated(prior.ARTIFACT)}
    if before_alloc["Z"] + 4096 > 81920 or before_alloc["D"] + 12288 > 196608:
        raise ValueError("no lane room")
    base_card = json.loads(prior.BUDGET.read_bytes())
    if any(shutil.disk_usage(v+":/").free < base_card["volumes"][v]["prior_allholds_floor"] + cap
           for v,cap in (("D",196608),("Z",81920))):
        raise ValueError("capacity floor")
    helper = prior.HERE / "player_heir_projection_service_contract_v1.py"
    old = helper.read_bytes()
    if hashlib.sha256(old).hexdigest() != "c1d1d5170d7ce116e99a0516d62ff8a49b10d34b2d3f8bf06f04f62daa46323c":
        raise ValueError("old helper changed")
    archive = prior.ARTIFACT / "HELPER-before-core-house-source-ready.py"
    with archive.open("xb") as stream:
        stream.write(old);stream.flush();os.fsync(stream.fileno())
    if archive.read_bytes() != old:
        raise ValueError("archive readback differs")
    text = old.decode()
    anchor = "                 and observation.before == observation.after\n"
    changed = text.replace("    ROBERT_V20261019_T0_ANCHOR,\n",
        "    ROBERT_V20261019_T0_ANCHOR, _valid_core,\n").replace(anchor, anchor +
        "                 and _valid_core(observation.before) and _valid_core(observation.after)\n"
        "                 and observation.candidate_lineage.house_id != -1\n").encode()
    if len(changed) != 6225 or hashlib.sha256(changed).hexdigest() != "7a4c8c737bbc942dec396b9f60aa7eb50f8301d8a2782231de730a568d1b3454":
        raise ValueError("delta differs")
    with helper.open("r+b") as stream:
        stream.write(changed);stream.truncate();stream.flush();os.fsync(stream.fileno())
    if helper.read_bytes() != changed:
        raise ValueError("new helper readback differs")
    sys.path[:0] = [str(prior.BASE), str(prior.REPO / "ck3_autonomous_player/tests/unit")]
    new_module = types.ModuleType("fixed_helper")
    exec(compile(changed,"<core-house-helper>","exec"),new_module.__dict__)
    import test_player_heir_candidate_component_v1 as native
    import test_player_heir_fixed_dynasty_projection_v1 as model
    from xar_autoplayer.bridge.driver import BridgeUnavailableError
    root = native.native_result()["campaign_root_context"]
    value = asdict(model.project_fixed_dynasty_candidate_v1(**model.fixture()))
    result = dict(query_sequence=11,queried_snapshot_id="native:7",queried_revision=8,queried_native_revision=7)
    value.update(candidate_character_id=root[native.leaf.COMPONENT]["observation"]["candidate_character_id"],
        machine_id="synthetic-m7-review",game_identity=dict(pid=123,creation_date="synthetic-birth",executable="synthetic/ck3.exe"),
        native_provider_sha256="a"*64,owner_source_epoch="b"*64,query_id="synthetic-query",native_query_sequence=11,
        capture_epoch_basis="original_root_query_sequence",**{k:result[k] for k in result if k!="query_sequence"})
    new_module.validate_player_heir_projection_service_v1(value,root=root,result=result)
    cases = ["paused","map_ready","has_played_character","played_character_alive","house_id"]
    for field in cases:
        altered = deepcopy(root);observation = altered[native.leaf.COMPONENT]["observation"]
        if field == "house_id":
            observation["candidate_lineage"]["house_id"] = -1
        else:
            for side in ("before","after"):
                observation[side][field] = False
        try:
            new_module.validate_player_heir_projection_service_v1(value,root=altered,result=result)
        except BridgeUnavailableError:
            continue
        raise AssertionError("accepted " + field)
    new_module.validate_player_heir_projection_service_v1(
        native.leaf._unknown("trusted_loaded_Native_DLL_custody_unavailable"),root=root,result=result)
    proof = dict(schema="xar.m7.root-projection-core-house-corrective/v1",status="PASS_SOURCE_ONLY",
        machine_id=prior.MACHINE,started_at_utc=started,observed_at_utc=prior.now(),budget=prior.pin(card),
        old_helper_exact_backup=prior.pin(archive),new_helper=prior.pin(helper),qualifier=prior.pin(Path(__file__)),
        prior_Service_MCP_qualification=prior.pin(prior.HERE/"SOURCE-READY.json"),
        previous_three_leaf_recipe=prior.pin(prior.HERE/"SOURCE-CLOSURE-REVIEW.json"),
        recipe_override="New helper pin only; Service transform and epoch append unchanged",
        checks=dict(valid_positive_and_unknown=True,new_rejects=cases,old_acceptance_RAM_tool="d909e0",Service_MCP_tests_repeated=0),
        actual_H="NOTRUN",M7="in_progress",G2="6/8",runtime_adoption=False,
        actions=dict(Game_Native_Task_desktop_MCP_calls=0,SDK_frozen_source_writes=0),
        allocation_correction="Old logical-as-allocated figures invalid. Actual prior FileStandardInfo=69632 incl dir, over65536 by4096; explicit16KiB supplement.",
        allocation_before_proof=before_alloc,allocation_method="GetFileInformationByHandleEx FileStandardInfo",
        retention=dict(policy_version="1.0.0",review_at_utc="2026-10-27T06:30:00Z",reason="Current candidate and earlier bytes until integration"))
    encoded = (json.dumps(proof,ensure_ascii=False,indent=2)+"\n").encode()
    if len(encoded)>4096 or allocated(prior.HERE)+4096>81920 or allocated(prior.ARTIFACT)+4096>196608:
        raise ValueError("proof cap")
    for root_path in (prior.HERE,prior.ARTIFACT):
        prior.write_new(root_path/"CORE-HOUSE-QUALIFIED.json",proof)
    print(json.dumps(dict(status=proof["status"],proof=prior.pin(prior.HERE/"CORE-HOUSE-QUALIFIED.json"),
        new_helper=prior.pin(helper),source_allocated=allocated(prior.HERE),artifact_allocated=allocated(prior.ARTIFACT),
        temporary_entries=len(list((prior.ARTIFACT/"tmp").iterdir()))),ensure_ascii=False))


if __name__ == "__main__":
    main()
