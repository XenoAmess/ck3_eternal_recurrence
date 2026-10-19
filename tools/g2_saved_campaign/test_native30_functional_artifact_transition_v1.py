"""Six finite RAM protocol checks; no Native binary, Task or runtime calls."""
import copy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest import mock

TOOLS = Path(__file__).resolve().parents[1]
if str(TOOLS) not in sys.path: sys.path.insert(0, str(TOOLS))
from g2_saved_campaign import native30_functional09_artifact11_transition_v1 as contract
from g2_saved_campaign import export_native30_functional_artifact_views_v1 as entry
from g2_saved_campaign import native30_export_adapter_v1 as adapter
from g2_saved_campaign.test_native30_two_stage_export_contract_v1 import two_stage_corpus
from g2_saved_campaign.test_native30_resume_fixture_chain_v1 import at, phase
from g2_saved_campaign.test_native30_export_transition_v1 import document, MACHINE, NOW

ROOT = "Z:/native30"
REPO = "Z:/repo"


def model(change=None):
    base, old, previous, old_card, args = two_stage_corpus()
    freeze = previous["source_freeze"].value
    native_plan = previous["build_plan"].value
    target = previous["target_native_pin"].value
    target.update(defender_registration_pending=True, os_qualification="UNKNOWN")
    built = previous["build_only_result"].value
    manifest = previous["project_exe_manifest"].value
    failed_admin = {"machine_id": MACHINE, "status": "FAILED_OR_UNKNOWN", "settings_success": False, "future_writes": None}
    # Model source vocabulary, never an actual mutation/requalification of08.
    nine = json.loads(json.dumps(previous["build_result"].value).replace("/attempt08-run", "/attempt09-functional"))
    nine.update(schema="native30-functional-qualification-v1", status="FAILED", stage="functional_test_only",
        run_id="native30-functional09", error={"type": "RuntimeError", "text": "five exports"},
        prior_admin_future_writes=None, defender_registration_pending=True, defender_effective_settings_known=False,
        os_qualification="UNKNOWN", UAC_calls=0, system_settings_operations=0)
    nine["phases"] = nine["phases"][:-1]
    nine["command_attempts"] = nine["command_attempts"][:-1]
    plans, specs, closes, unregs = {}, {}, {}, {}
    for prefix, number, hour, code in (("build08", "8", 12, 0), ("functional09", "9", 14, 1), ("artifact11", "b", 15, 0)):
        nonce = number * 32
        owner = ROOT + "/owner-" + prefix + "/owner-spec"
        spec = copy.deepcopy(previous["build_owner_spec"].value)
        spec.update(nonce=nonce, task_name="XARG2ManagedOwner-" + nonce, root=owner)
        closed = copy.deepcopy(previous["build_owner_closed"].value)
        closed.update(nonce=nonce, child_exit_code=code, bootstrap_exit_code=code,
            utc="2026-10-19T%02d:10:01Z" % hour)
        closed["child"]["creation_filetime"] = str(134368900000000009 + hour)
        unreg = {"machine_id": MACHINE, "utc": "2026-10-19T%02d:10:02Z" % hour,
            "operation": "unregister", "task_name": spec["task_name"],
            "actual": {"sid": contract.OWNER_SID, "instances": 0, "last_result": code, "absent_after": True}}
        if prefix in contract.PRODUCERS:
            filename, sha = contract.PRODUCERS[prefix]
            spec.update(stage=REPO + "/tools/g2_saved_campaign/" + filename, stage_sha256=sha)
            schema = "native30-functional09-plan-v1" if prefix == "functional09" else "native30-artifact-postcheck11-plan-v1"
            plans[prefix] = {"schema": schema, "machine_id": MACHINE, "source_commit": contract.SOURCE,
                "producer": {"path": spec["stage"], "sha256": sha}, "fixtures": native_plan["fixtures"], "source_fixture": True}
        specs[prefix], closes[prefix], unregs[prefix] = spec, closed, unreg
    delivery = previous["production_delivery"].value
    delivery.update(qualification_kind="artifact_plus_closed09_functional_only", nine_functional_runs_reused_from_failed09=True,
        Game_camera_H="NOTRUN", defender_registration_pending=True, os_qualification="UNKNOWN")
    components = []
    for i, relative in enumerate(("ck3_autonomous_player/native_bridge/src/ck3_12004_player_heir_candidate_v1.cpp",
        "ck3_autonomous_player/native_bridge/src/campaign_player_heir_candidate_component12004_v1.cpp",
        "ck3_autonomous_player/native_bridge/src/campaign_player_heir_candidate_component12004_v1_serializer.cpp"), 1):
        freeze["files"].append({"path": relative, "bytes": 10, "sha256": str(i)*64, "git_blob": "a"*40})
        components.append({"source": {"path": ROOT + "/source/" + relative, "bytes": 10, "sha256": str(i)*64},
            "object": {"path": ROOT + "/build/obj%d.obj" % i, "bytes": 20, "sha256": str(i+3)*64},
            "payload": {"name": "obj%d.obj" % i, "bytes": 20, "sha256": str(i+3)*64}})
    delivery["component_objects"] = components
    names = ["XarCk3BridgeIdentity", "XarCk3BridgePrepareStartup", "XarCk3BridgeStart", "XarCk3BridgeStartWithPipe", "XarCk3BridgeStop", "XarRefillCoreCarrier12004"]
    export = {"machine_id": MACHINE, "exports": [{"name": name, "rva": 100+i if i<5 else 2000} for i,name in enumerate(names)],
        "DATA_is_not_callable": True, "data_section": {"name": ".data", "rva": 1000, "size": 2000},
        "map_public_row": "XarRefillCoreCarrier12004 army_regular_core_passive_12004.cpp.obj",
        "map_sha256": delivery["map"]["sha256"]}
    phases, journals = [], []
    for i,(argv,log) in enumerate(((nine["phases"][0]["argv"], "production-no-work.log"),
        (["Z:/tools/lib.exe", "/LIST", delivery["runtime_archive"]["path"]], "runtime-members.log"))):
        row,state = phase(argv,log,i+1)
        time = datetime(2026,10,19,15,tzinfo=timezone.utc)+timedelta(seconds=2*i)
        for value in (row,state): value.update(start_utc=time.isoformat(),end_utc=(time+timedelta(seconds=1)).isoformat())
        row["log"]["path"] = ROOT + "/attempt11-artifact-postcheck/" + log
        phases.append(row);journals.append(state)
    artifact = {"schema": "native30-artifact-postcheck-v1", "status": "OFFLINE_ARTIFACT_QUALIFIED_NOT_DEPLOYED",
        "machine_id": MACHINE, "source_commit": contract.SOURCE, "phase": "artifact_postcheck_only",
        "start_utc": "2026-10-19T15:00:00Z", "end_utc": "2026-10-19T15:10:00Z",
        "phases": phases, "command_attempts": journals, "project_EXE_executions": 0, "fixture_builds": 0,
        "fixture_runs_reused": 9, "production_recompiled": False, "UAC_calls": 0, "system_settings_operations": 0,
        "Game_calls": 0, "owned_active_after": 0, "future_writes": 0, "deployed": False,
        "defender_registration_pending": True, "os_qualification": "UNKNOWN", "exe_bindings": copy.deepcopy(nine["exe_bindings"]),
        "snapshot": copy.deepcopy(nine["snapshot"])}
    raw = {"nine": nine, "artifact": artifact, "delivery": delivery, "export": export, "built": built,
        "manifest": manifest, "admin": failed_admin, "freeze": freeze, "plans": plans, "specs": specs,
        "closes": closes, "unregs": unregs, "target": target, "native_plan": native_plan}
    if change: change(raw)
    docs = {"target_native_pin": document("target0911", target), "source_freeze": at(ROOT + "/source-freeze.json",freeze),
        "native_plan": document("native-plan0911",native_plan), "build08_result": at(ROOT + "/attempt08-build/RESULT.json",built),
        "build08_manifest": previous["project_exe_manifest"], "prior08_admin_launch": at(ROOT + "/attempt08-admin/LAUNCH-RESULT.json",failed_admin),
        "exports_and_data": at(ROOT + "/attempt11-artifact-postcheck/exports-and-data.json",export)}
    path07="docs/ck3-native-ai/evidence/native30-fixture07-snapshot-plan-2026-10-20.json"
    docs["snapshot07_plan"]=document("snapshot07-plan-source",{"schema":"native30-fixture07-snapshot-plan-v1",
        "source_commit":contract.SOURCE,"prior_pins":[docs["source_freeze"].reference],
        "helper_pins":{"docs/ck3-native-ai/evidence/native30-wholeclean-producer-plan-2026-10-19.json":docs["native_plan"].sha256}})
    docs["native_readonly_plan"]=document("readonly-native-plan",{"schema":"native30-08B-two-stage-plan-v1",
        "source_commit":contract.SOURCE,"base_readonly_plan":{**docs["snapshot07_plan"].reference,"path":path07},
        "helper_pins":{path07:docs["snapshot07_plan"].sha256}})
    plans["functional09"]["base_plan"]=docs["native_readonly_plan"].reference
    for prefix in ("build08","functional09","artifact11"):
        if prefix in plans:
            docs[prefix + "_plan"] = document(prefix + "-plan",plans[prefix])
            result = nine if prefix == "functional09" else artifact
            result["plan"] = docs[prefix + "_plan"].reference
            specs[prefix]["stage_args"] = ["--plan",result["plan"]["path"],"--admission",result["admission"]["path"] if "admission" in result else "Z:/artifact11card.json",
                "--admission-sha256",result["admission"]["sha256"] if "admission" in result else "a"*64,"--execute"]
            result["admission"] = {"path": specs[prefix]["stage_args"][3],"bytes":10,"sha256":specs[prefix]["stage_args"][5]}
        docs[prefix+"_spec"] = document(prefix+"-spec",specs[prefix])
        closes[prefix]["spec_sha256"] = docs[prefix+"_spec"].sha256
        docs[prefix+"_closed"] = document(prefix+"-closed",closes[prefix])
        docs[prefix+"_unregister"] = document(prefix+"-unregister",unregs[prefix])
    for key,name in contract.BUILD_KEYS.items(): nine[key] = docs[name].reference
    docs["functional09_result"] = at(ROOT+"/attempt09-functional/RESULT.json",nine)
    summary9 = {"machine_id": MACHINE,"status":"FAILED",**{k:docs["functional09"+v].reference for k,v in
        (("result","_result"),("spec","_spec"),("outer_closed","_closed"),("unregister","_unregister"))}}
    docs["functional09_summary"] = document("summary09",summary9)
    artifact["original_build"] = {key:docs[name].reference for key,name in contract.BUILD_KEYS.items()}
    for value in (artifact,delivery): value["reused09"] = {key:docs[name].reference for key,name in contract.REUSED_KEYS.items()}
    delivery["exports_and_data"] = docs["exports_and_data"].reference
    docs["artifact11_delivery"] = at(ROOT+"/attempt11-artifact-postcheck/production-delivery.json",delivery)
    artifact["delivery"] = docs["artifact11_delivery"].reference
    docs["artifact11_result"] = at(ROOT+"/attempt11-artifact-postcheck/RESULT.json",artifact)
    summary11 = {"machine_id":MACHINE,"status":artifact["status"],"delivery":docs["artifact11_delivery"].reference,
        **{k:docs["artifact11"+v].reference for k,v in (("result","_result"),("spec","_spec"),("outer_closed","_closed"),("unregister","_unregister"))}}
    docs["artifact11_summary"] = document("summary11",summary11)
    target_binding = previous["target_exe_binding"].value
    target_binding.update(native_pin=docs["target_native_pin"].reference,source_freeze=docs["source_freeze"].reference)
    docs["target_exe_binding"] = document("target-exe0911",target_binding)
    docs["base_exe_binding"] = previous["base_exe_binding"]
    compatible = {"schema":"xar.ck3.native29-to30-compatibility/v1","machine_id":MACHINE,
        **{k:docs[k].reference for k in ("base_exe_binding","target_exe_binding","source_freeze","artifact11_result","artifact11_delivery","functional09_result")}}
    docs["compatibility"] = document("compatible0911",compatible)
    card = old_card.value
    card["native_transition"] = {"schema":contract.TRANSITION_SCHEMA,"from_generation":29,"to_generation":30,
        "build_chain":contract.CHAIN,"source_commit":contract.SOURCE,"target_native_build_label":contract.NATIVE30_BUILD_LABEL,
        **{key:doc.reference for key,doc in docs.items()}}
    card = document("export-card0911",card)
    args.capacity_card,args.capacity_card_sha256 = card.path,card.sha256
    return base,old,docs,card,args


def qualify(values, fixture=True):
    base,old,evidence,card,_ = values
    return contract.validate_functional_artifact_transition_v1(base_freeze=base,base_native_pin=old,
        evidence=evidence,capacity=card,machine_id=MACHINE,source_fixture=fixture,now=NOW)


class FunctionalArtifactTransitionTests(unittest.TestCase):
    def test_public_reader_binds_complete_native_source_provenance(self):
        def read_recipe(values):
            base,old,evidence,card,_=values
            lookup={d.path:d for d in [base,old,card,*evidence.values()]}
            def read(ref):
                doc=lookup[ref["path"]];self.assertEqual(doc.reference,ref);return doc
            with mock.patch.object(entry,"_read_document",side_effect=read):
                return entry.read_native_transition_v1(base_freeze_ref=base.reference,base_native_ref=old.reference,
                    capacity_ref=card.reference,machine_id=MACHINE,source_fixture=True)
        self.assertTrue(read_recipe(model()).source_fixture)
        for name,message in (("source_freeze","complete native source freeze provenance"),("native_plan","native whole plan provenance")):
            base,old,evidence,card,args=model();body=evidence[name].value;body["unrelated_manifest"]=True
            evidence[name]=at(evidence[name].path,body)
            # Repair every old compatibility/card backlink. Only the newly
            # bound original source-plan lineage should reject this substitution.
            if name=="source_freeze":
                target=evidence["target_exe_binding"].value;target["source_freeze"]=evidence[name].reference
                evidence["target_exe_binding"]=at(evidence["target_exe_binding"].path,target)
                compat=evidence["compatibility"].value
                compat.update(source_freeze=evidence[name].reference,target_exe_binding=evidence["target_exe_binding"].reference)
                evidence["compatibility"]=at(evidence["compatibility"].path,compat)
            changed=card.value;changed["native_transition"].update({k:d.reference for k,d in evidence.items()});card=at(card.path,changed)
            with self.subTest(name=name),self.assertRaisesRegex(ValueError,message):
                read_recipe((base,old,evidence,card,args))

    def test_complete_protocol_keeps_failed09_and_unknown_OS(self):
        values=model(); before={k:v.raw for k,v in values[2].items()}
        result=qualify(values); audit=result.manifest_metadata["build_chain_provenance"]
        self.assertEqual(audit["functional09_status_preserved"],"FAILED")
        self.assertEqual(audit["functional09_parent_exit_preserved"],1)
        self.assertEqual(audit["closed09_fixture_nodes"],9)
        self.assertEqual(audit["artifact11_parent_exit"],0)
        self.assertEqual(result.manifest_metadata["os_qualification"],"UNKNOWN")
        self.assertFalse(result.manifest_metadata["actual_loaded_provider_issued"])
        self.assertEqual(before,{k:v.raw for k,v in values[2].items()})
        with self.assertRaises(ValueError): qualify(values,False)
        with self.assertRaises(ValueError): adapter.FrozenExporterAdapterV1().prepare(values[4],{},result)

    def test_09_subfacts_are_not_arbitrary_failed_or_whole_PASS(self):
        changes=[lambda r:r["nine"].update(status="OFFLINE_FUNCTIONAL_PASS_NOT_DEPLOYED"),
            lambda r:r["nine"].update(error={"type":"RuntimeError","text":"other failure"}),
            lambda r:r["nine"]["fixture_runs"][0].update(returncode=1),
            lambda r:r["closes"]["functional09"].update(child_exit_code=0),
            lambda r:r["admin"].update(future_writes=0)]
        for i,change in enumerate(changes):
            with self.subTest(i=i),self.assertRaises(ValueError): qualify(model(change))

    def test_11_parent_identity_and_archive_boundaries(self):
        changes=[lambda r:r["artifact"].update(status="FAILED"),
            lambda r:r["closes"]["artifact11"].update(job_active_after_stage=1),
            lambda r:r["unregs"]["artifact11"]["actual"].update(absent_after=False),
            lambda r:r["artifact"]["exe_bindings"][0]["file_id"].update(file_id="f"*32),
            lambda r:r["delivery"]["component_objects"][0]["payload"].update(sha256="f"*64),
            lambda r:r["export"].update(DATA_is_not_callable=False)]
        for i,change in enumerate(changes):
            with self.subTest(i=i),self.assertRaises(ValueError): qualify(model(change))

    def test_base29_and_same_EXE_contract_remain_required(self):
        base,old,ev,card,args=model()
        for name,field,value in (("target_native_pin","os_qualification","VERIFIED"),
            ("target_exe_binding","native_layout_id","different-build")):
            copied=dict(ev); body=copied[name].value;body[field]=value;copied[name]=document("bad",body)
            c=card.value;c["native_transition"][name]=copied[name].reference;c=document("bad-card",c)
            with self.subTest(name=name),self.assertRaises(ValueError): qualify((base,old,copied,c,args))

    def test_independent_four_refs_loader_and_default_OFF(self):
        values=model();base,old,ev,card,_=values
        lookup={doc.path:doc for doc in [base,old,card,*ev.values()]}
        def read(ref):
            doc=lookup[ref["path"]];self.assertEqual(doc.reference,ref);return doc
        with mock.patch.object(entry,"_read_document",side_effect=read):
            recipe=entry.read_native_transition_v1(base_freeze_ref=base.reference,base_native_ref=old.reference,
                capacity_ref=card.reference,machine_id=MACHINE,source_fixture=True)
        self.assertTrue(recipe.source_fixture)
        with mock.patch.object(entry,"_read_document",side_effect=AssertionError("disabled did I/O")):
            self.assertEqual(entry.export_native30_views_v1(None)["status"],"DISABLED")

    def test_legacy_files_and_actual_producer_pins_are_unchanged(self):
        root=TOOLS/"g2_saved_campaign"
        frozen={"native30_two_stage_export_contract_v1.py":"a854db9bf02ac98f5b1eb0b1b498cc4c93ca4e0a48597bc09c22b05e7c5d5c17",
            "native29_to30_export_contract_v1.py":"d348b59cdf68a2da0928ccfc4034006c0c42618fe341ad0ca1c7dac1bbfa7554",
            "export_native30_immutable_sdk_views_v1.py":"90ccd7a5c12d90101217391857d793715fdaebcb98a3e374e6a5d4b3776f9369",
            "native30_export_adapter_v1.py":"2d4074379371ed91bc38ff0fc532521e277ba2795faad1fd8e9c6dd2593c5298",
            "export_immutable_sdk_views_v1.py":"8b6972ac2a82b30c92b531c640df0eb9aa6e43cc205ab9d7d23796d5739da432"}
        for filename,sha in frozen.items(): self.assertEqual(hashlib.sha256((root/filename).read_bytes()).hexdigest(),sha)
        for filename,sha in contract.PRODUCERS.values(): self.assertEqual(hashlib.sha256((root/filename).read_bytes()).hexdigest(),sha)


if __name__=="__main__":unittest.main()
