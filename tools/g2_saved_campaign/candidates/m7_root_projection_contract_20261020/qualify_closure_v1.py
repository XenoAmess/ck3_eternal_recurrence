"""One bounded RAM closure check; reuses prior Service/MCP qualification."""
import ast
from copy import deepcopy
from datetime import datetime, timezone
import difflib
import hashlib
import json
from pathlib import Path
import shutil

import qualify_v1 as prior
from transform_service_v1 import transform_service_v1, HELPER_TARGET
from transform_owner_epoch_v1 import transform_owner_epoch_v1, RELATIVE_HELPER


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def function(source, name):
    found = [node for node in ast.walk(ast.parse(source))
             if isinstance(node, ast.FunctionDef) and node.name == name]
    if len(found) != 1:
        raise ValueError("one source function required: " + name)
    return found[0]


def names(source):
    node = function(source, "owner_source_epoch_v1")
    return ast.literal_eval(next(item.value for item in node.body
        if isinstance(item, ast.Assign) and any(isinstance(target, ast.Name)
            and target.id == "names" for target in item.targets)))


def synthetic_epoch(source, bodies):
    class MemoryPath:
        def __init__(self, value):
            self.value = str(value)
        def resolve(self):
            return self
        @property
        def parent(self):
            return MemoryPath("synthetic-owner-root")
        def __truediv__(self, value):
            return MemoryPath(value)
        def read_bytes(self):
            return bodies[self.value]
    namespace = dict(Path=MemoryPath, __file__="synthetic-ledger.py", hashlib=hashlib, json=json)
    node = ast.Module(body=[function(source, "digest"), function(source, "owner_source_epoch_v1")], type_ignores=[])
    exec(compile(node, "<original-owner-epoch-RAM-synthetic>", "exec"), namespace)
    return namespace["owner_source_epoch_v1"]()


def main():
    started = prior.now()
    budget = json.loads(prior.BUDGET.read_bytes())
    if datetime.now(timezone.utc) >= datetime.fromisoformat(budget["review_at_utc"]):
        raise ValueError("m7 lane review expired")
    capacities = {v:shutil.disk_usage(v+":/").free for v in ("D", "Z")}
    if any(capacities[v] < budget["volumes"][v]["prior_allholds_floor"] + cap
           for v,cap in (("D",196608),("Z",65536))):
        raise ValueError("retained floors plus original lane cap not available")
    old_proof_path = prior.HERE / "SOURCE-READY.json"
    old_proof = json.loads(old_proof_path.read_bytes())
    if old_proof["status"] != "PASS" or old_proof["machine_id"] != prior.MACHINE:
        raise ValueError("prior exact Service/MCP qualification missing")
    for pin in old_proof["source_files"]:
        if prior.pin(Path(pin["path"])) != pin:
            raise ValueError("qualified candidate source changed")
    service = prior.SERVICE.read_bytes()
    if digest(service) != old_proof["source_Service"]["sha256"]:
        raise ValueError("Source25 Service input changed")
    service_after = transform_service_v1(service.decode()).encode()
    if digest(service_after) != old_proof["transformed_Service_sha256"]:
        raise ValueError("Service transform differs from prior tested result")
    ledger_path = prior.BASE / "xar_autoplayer/successor_ui_pending_ledger_v1.py"
    ledger = ledger_path.read_bytes()
    ledger_after = transform_owner_epoch_v1(ledger.decode()).encode()
    old_names, new_names = names(ledger.decode()), names(ledger_after.decode())
    if new_names != old_names + (RELATIVE_HELPER,) or len(new_names) != len(set(new_names)):
        raise ValueError("epoch names did not preserve complete original tuple")
    if any(not (prior.BASE / "xar_autoplayer" / name).is_file() for name in old_names):
        raise ValueError("Source25 original closure leaf absent")
    if ast.dump(function(ledger.decode(), "_checked"), include_attributes=False) != ast.dump(
            function(ledger_after.decode(), "_checked"), include_attributes=False):
        raise ValueError("original successor ledger _checked changed")
    # Exercise the original epoch function with a bounded RAM path facade.
    # No source tree or synthetic file copies are produced for these probes.
    bodies = {name:("synthetic:"+name).encode() for name in new_names}
    first = synthetic_epoch(ledger_after.decode(), bodies)
    changed = dict(bodies)
    changed[RELATIVE_HELPER] += b"changed-validator-byte"
    second = synthetic_epoch(ledger_after.decode(), changed)
    if first == second:
        raise ValueError("new helper bytes did not affect original epoch")
    helper_path = prior.HERE / Path(HELPER_TARGET).name
    helper = helper_path.read_bytes()
    compile(helper, HELPER_TARGET, "exec")
    diff = "".join(difflib.unified_diff(ledger.decode().splitlines(keepends=True),
        ledger_after.decode().splitlines(keepends=True),
        fromfile="a/ck3_autonomous_player/src/xar_autoplayer/successor_ui_pending_ledger_v1.py",
        tofile="b/ck3_autonomous_player/src/xar_autoplayer/successor_ui_pending_ledger_v1.py"))
    with (prior.HERE / "owner_epoch.diff").open("xb") as stream:
        stream.write(diff.encode())
    review = {
        "schema":"xar.m7.root-projection-three-leaf-source-closure/v1",
        "machine_id":prior.MACHINE,"observed_at_utc":prior.now(),"started_at_utc":started,
        "status":"SOURCE_CLOSURE_READY_NOT_ADOPTED", "budget":prior.pin(prior.BUDGET),
        "prior_Service_MCP_qualification":prior.pin(old_proof_path),
        "test_scope":"Original epoch function with synthetic in-memory source bodies; no Service/MCP test repeated",
        "checks":{"original_Service_result_reproduced_in_RAM":True,
            "all_original_epoch_leaves_exist":True,"original_epoch_order_preserved":True,
            "only_new_validator_appended":True,"new_helper_byte_changes_epoch":True,
            "original_checked_AST_unchanged":True,"complete_sources_compile":True},
        "original_epoch_leaf_count":len(old_names),"result_epoch_leaf_count":len(new_names),
        "changes":[
            {"target":"xar_autoplayer/bridge/service.py","kind":"modify_original_method",
             "input":old_proof["source_Service"],"output_bytes":len(service_after),
             "output_sha256":digest(service_after),"transform":prior.pin(prior.HERE/"transform_service_v1.py"),
             "diff":prior.pin(prior.HERE/"service.diff")},
            {"target":HELPER_TARGET,"kind":"new_exact_leaf","input":prior.pin(helper_path),
             "output_bytes":len(helper),"output_sha256":digest(helper)},
            {"target":"xar_autoplayer/successor_ui_pending_ledger_v1.py","kind":"append_one_epoch_leaf",
             "input":prior.pin(ledger_path),"output_bytes":len(ledger_after),
             "output_sha256":digest(ledger_after),"transform":prior.pin(prior.HERE/"transform_owner_epoch_v1.py"),
             "diff":prior.pin(prior.HERE/"owner_epoch.diff")}
        ],
        "qualifier":prior.pin(Path(__file__)),"capacity_at_start_free_bytes":capacities,
        "actions":{"Game_Native_MCP_Task_desktop":0,"frozen_source_runtime_and_SDK_writes":0},
        "adoption":{"source26_assembly":False,"actual_H":"NOTRUN","M7":"in_progress","G2":"6/8"},
        "retention":{"policy_version":"1.0.0","review_at_utc":"2026-10-27T06:30:00Z",
                     "reason":"Current exact three-leaf integration recipe until Root source26 assembly"}}
    encoded = (json.dumps(review,ensure_ascii=False,indent=2)+"\n").encode()
    reserve = ((len(encoded)+4095)//4096)*4096
    if prior.allocation(prior.HERE)+reserve>65536 or prior.allocation(prior.ARTIFACT)+reserve>196608:
        raise ValueError("source closure proof would exceed original m7 cap")
    prior.write_new(prior.ARTIFACT/"SOURCE-CLOSURE-REVIEW.json",review)
    prior.write_new(prior.HERE/"SOURCE-CLOSURE-REVIEW.json",review)
    print(json.dumps({"status":review["status"],"machine_id":prior.MACHINE,
        "source_review":prior.pin(prior.HERE/"SOURCE-CLOSURE-REVIEW.json"),
        "artifact_review":prior.pin(prior.ARTIFACT/"SOURCE-CLOSURE-REVIEW.json"),
        "source_allocation":prior.allocation(prior.HERE),"artifact_allocation":prior.allocation(prior.ARTIFACT),
        "all_temporary_entries":len(list((prior.ARTIFACT/"tmp").iterdir()))},ensure_ascii=False))


if __name__ == "__main__":
    main()
