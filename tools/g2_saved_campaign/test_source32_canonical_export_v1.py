"""Portable synthetic metadata contracts; no Game qualification."""
from __future__ import annotations
import json
import unittest
from unittest.mock import patch
from typing import Callable
from tools.g2_saved_campaign import write_source32_canonical_ref_v1 as S
from tools.g2_saved_campaign import prepare_source32_export_base_v1 as A

import write_source27_canonical_ref_v1 as W
COUNT, SHARED = S.SOURCE_FILE_COUNT, S.SOURCE_FILE_COUNT-len(S.SDK)
Doc = dict[str, object]

def ref(name: str) -> W.FileRef:
    return {"path":name,"bytes":2,"sha256":"0"*64}

def plan() -> S.Plan:
    return {"schema":"xar.source32.canonical-plan/v1","machine_id":S.MACHINE,
        "observed_at_utc":W.utc().isoformat(),"review_at_utc":"2099-01-01T00:00:00Z",
        "parent":S.PARENT,"ref":S.REF,"target_tree":"1"*40,"public_source_commit":"2"*40,
        "public_inputs":[{"relative":n,"pin":S.PUBLIC_PINS[n]} for n in S.PUBLIC],
        "source31_anchor":S.SOURCE31_ANCHOR,"source31_BASE":S.SOURCE31_BASE,
        "qualifications":[S.PARENT_QUAL,ref("q")],"source_file_count":COUNT,
        "source_bytes":59321251,"complete_rows_JSON":{"bytes":1,"sha256":"3"*64},
        "Git_object_quote":{"retained_upper":1,"largest_temporary_upper":1,"peak_upper":65538,"object_count":10}}

def qual_doc(p: S.Plan) -> Doc:
    return {"schema":"xar.source32.composition-qualification/v1","status":"OFFLINE_QUALIFIED_NOT_RUNTIME",
        "machine_id":S.MACHINE,"observed_at_utc":W.utc().isoformat(),"public_source_commit":p["public_source_commit"],
        "public_inputs":p["public_inputs"],"source31_anchor":S.SOURCE31_ANCHOR,"source31_BASE":S.SOURCE31_BASE,
        "parent_package_qualification":S.PARENT_QUAL,"complete_rows_JSON":p["complete_rows_JSON"],
        "target_tree":p["target_tree"],"source_file_count":COUNT,"epoch_count":S.EPOCH_COUNT,
        "runtime_calls":0,"new_campaign_credit":0,"RAM_composition_and_exact_pins_passed":True,
        "strict_and_strict_equality_passed":True,"clock_qualification_payload":S.QUALIFICATION_PIN,
        "clock_candidate_tests_passed":9,"M6_producer_consumer_passed":True,
        "M6_candidate_tests_passed":S.M6_CASE_COUNT,
        "output_pins":[{"relative":name,**S.POST_PINS[name]} for name in S.SDK]}

def row(name: str, size: int = 1, sha: str = "0"*64) -> W.Row:
    return {"relative":name,"bytes":size,"sha256":sha,"git_blob_sha1":"1"*40,"git_mode":"100644"}

def identity(index: int) -> Doc:
    return {"volume_serial":123,"file_id":f"{index:016x}","filesystem":"NTFS","directory":False}

def fixture() -> tuple[Doc,Doc,Doc,Doc,Doc,Doc,dict[str,W.FileRef]]:
    old = [row(f"xar_autoplayer/fixture/leaf{n}.py") for n in range(SHARED)]
    old += [row(n) for n in S.SDK if n not in S.NEW_LEAVES]
    old_rich = [{**v,"file_identity":identity(i+1)} for i,v in enumerate(old)]
    old_by = {W.string(v["relative"]):v for v in old_rich}
    changed = {n:row(n,S.POST_PINS[n]["bytes"],S.POST_PINS[n]["sha256"]) for n in S.SDK}
    compact = sorted([row(f"xar_autoplayer/fixture/leaf{n}.py") for n in range(SHARED)]
        +list(changed.values()),key=lambda v:v["relative"])
    previous:Doc = {"files":old,"source_file_count":1466,"source_bytes":sum(v["bytes"] for v in old),
        "source_root":str(A.SOURCE31_ROOT.resolve()),"git_head":"4"*40,
        "native_dll_sha256":"5"*64,"native_build_label":"historical-native-only",
        "native_transition":{"target_native_pin":ref("historical")} }
    old_source:Doc = {"files":old_rich}
    refs = {"source":ref(str(A.OUT/"SOURCE-FREEZE.json")),"reference":ref(str(A.OUT/"REFERENCE-FREEZE.json")),
        "export":ref(str(A.OUT/"COMPLETE.json")),"anchor":ref(str(A.ANCHOR))}
    docs:list[Doc] = []
    for side,root in enumerate((A.SRC,A.REFERENCE)):
        rich:list[Doc] = []
        for v in compact:
            n = v["relative"]
            if n in changed:
                rich.append({**v,"file_identity":identity(10000+side*100+S.SDK.index(n)),
                    "storage_mode":"independent_new_blob"})
            else:
                rich.append({**v,"file_identity":old_by[n]["file_identity"],"storage_mode":"existing_frozen_hardlink",
                    "hardlink_source":{"path":str(A.SOURCE31_ROOT.resolve()/n),
                        "freeze_sha256":S.SOURCE31_BASE["sha256"]}})
        docs.append({"files":rich,"source_file_count":COUNT,"source_bytes":sum(v["bytes"] for v in compact),
            "source_root":str(root.resolve()),"schema":"root.ck3.final-sdk-freeze/v1","status":"FINAL_SOURCE_FROZEN",
            "machine_id":S.MACHINE,"business_source_commit":"6"*40,"base_freeze":S.SOURCE31_BASE,
            "git_head":previous["git_head"],"sdk_generation":"P37C23","runtime_admitted":False,
            "native_dll_sha256":previous["native_dll_sha256"],"native_build_label":previous["native_build_label"],
            "capacity_admission":ref("capacity")})
    complete:Doc = {"schema":"xar.ck3.immutable-sdk-view-export/v1","status":"SOURCE_READY_NOT_LOADED",
        "machine_id":S.MACHINE,"manifests":[refs["source"],refs["reference"]],
        "business_source_commit":"6"*40,"old_content_write_operations":0,"game_sdk_native_obs_calls":0,
        "new_unique_file_count":2*len(S.SDK),"existing_shared_unique_file_count":SHARED,"changed_relative_paths":list(S.SDK),
        "logical_bytes_each":sum(v["bytes"] for v in compact),"capacity":ref("capacity")}
    anchor:Doc = {"commit":"6"*40,"source_bytes":sum(v["bytes"] for v in compact),
        "complete_rows_JSON":W.pin(W.canonical(compact)),"output_pins":list(changed.values()),
        "canonical_patch_rows":[]}
    return previous,old_source,docs[0],docs[1],complete,anchor,refs

class Source32ContractTests(unittest.TestCase):
    def rejected(self, call: Callable[[],object]) -> None:
        with self.assertRaises((ValueError,TypeError,KeyError,RuntimeError)):
            call()

    def test_plan_roundtrip(self) -> None:
        p=plan()
        self.assertEqual(S.parse_plan(json.loads(W.canonical(p))),p)

    def test_exact_fields(self) -> None:
        for mutation in ("extra","missing","ref-extra","ref-missing"):
            with self.subTest(mutation=mutation):
                d=W.obj(json.loads(W.canonical(plan())))
                if mutation=="extra":d["alias"]=None
                if mutation=="missing":del d["parent"]
                if mutation=="ref-extra":d["source31_BASE"]={**W.obj(d["source31_BASE"]),"extra":0}
                if mutation=="ref-missing":
                    r=W.obj(d["source31_BASE"]);del r["path"];d["source31_BASE"]=r
                self.rejected(lambda:S.parse_plan(d))

    def test_numbers(self) -> None:
        for bad in (True,float(COUNT),None,2**53):
            for key in ("source_file_count","source_bytes"):
                with self.subTest(key=key,bad=bad):
                    d=W.obj(json.loads(W.canonical(plan())));d[key]=bad
                    self.rejected(lambda:S.parse_plan(d))

    def test_public_inputs(self) -> None:
        valid=plan()["public_inputs"]
        for values in (valid[:1],valid+valid[:1],[valid[0],valid[0]],
                [{"relative":S.SDK[0],"pin":S.POST_PINS[S.SDK[0]]},valid[1]]):
            self.rejected(lambda:S.parse_inputs(values))
        wrong=W.sequence(json.loads(W.canonical(valid)))
        r=W.obj(wrong[0]);r["pin"]={**W.obj(r["pin"]),"bytes":True};wrong[0]=r
        self.rejected(lambda:S.parse_inputs(wrong))

    def validate(self, value: Doc) -> None:
        payload=W.canonical(value)
        def checked(item: W.FileRef) -> bytes:
            return b"{}" if item==S.PARENT_QUAL else payload
        with patch.object(W,"checked",checked):
            S.validate_qualifications_v1(plan())

    def test_qual_roundtrip(self) -> None:
        self.validate(W.obj(json.loads(W.canonical(qual_doc(plan())))))

    def test_bad_qual(self) -> None:
        for key,bad in (("status","PASS"),("machine_id","foreign"),("clock_candidate_tests_passed",True),
                ("clock_candidate_tests_passed",9.0),("M6_candidate_tests_passed",True),
                ("M6_producer_consumer_passed",False),("epoch_count",41),("runtime_calls",1),
                ("clock_qualification_payload",None),("source31_BASE",None)):
            with self.subTest(key=key):
                d=qual_doc(plan());d[key]=bad
                self.rejected(lambda:self.validate(d))
        d=qual_doc(plan());del d["clock_candidate_tests_passed"]
        self.rejected(lambda:self.validate(d))

    def test_qual_outputs(self) -> None:
        d=qual_doc(plan());rows=W.sequence(d["output_pins"])
        d["output_pins"]=rows+rows[:1]
        self.rejected(lambda:self.validate(d))
        d=qual_doc(plan());values=W.sequence(d["output_pins"])
        values[0]={**W.obj(values[0]),"bytes":True};d["output_pins"]=values
        self.rejected(lambda:self.validate(d))

    def test_new_roots(self) -> None:
        self.assertEqual(A.SOURCE31_ROOT,S.P/"sdk-v20261019-candidate/src31")
        self.assertEqual(A.SRC,S.P/"sdk-v20261019-candidate/src32")
        self.assertEqual(A.REFERENCE,S.P/"sdk-v20261019-candidate/src32-independent")
        self.assertNotEqual(A.SRC,A.SOURCE31_ROOT)

    def test_only_production_in_sdk(self) -> None:
        self.assertEqual(len(S.SDK),8)
        self.assertEqual(len(set(S.SDK)),8)
        self.assertEqual(set(S.POST_PINS),set(S.SDK))
        self.assertIn("xar_autoplayer/bridge/route_window_clock_v1.py",S.SDK)
        self.assertFalse(any(v.startswith("qualification/") for v in S.SDK))

    def test_epoch_ast_domain(self) -> None:
        self.assertEqual(S.epoch_names(b"def owner_source_epoch_v1():\n names=('a','b')\n"),("a","b"))
        for value in ("['a']","('a',True)","('a',1.0)","None"):
            self.rejected(lambda:S.epoch_names(("def owner_source_epoch_v1():\n names="+value+"\n").encode()))

    def test_output_rows(self) -> None:
        anchor:Doc={"output_pins":[row(n,S.POST_PINS[n]["bytes"],S.POST_PINS[n]["sha256"]) for n in S.SDK]}
        self.assertEqual(len(A.output_rows(anchor)),8)
        values=W.sequence(anchor["output_pins"]);values[0]={**W.obj(values[0]),"bytes":True}
        anchor["output_pins"]=values
        self.rejected(lambda:A.output_rows(anchor))

    def compose(self, fixture: tuple[Doc,Doc,Doc,Doc,Doc,Doc,dict[str,W.FileRef]]) -> tuple[bytes,A.BASEReport]:
        previous,old,source,reference,complete,anchor,refs=fixture
        def checked(item: W.FileRef, limit: int=4194304) -> Doc:
            return {"source":source,"reference":reference,"export":complete}[
                next(k for k in ("source","reference","export") if refs[k]==item)]
        with patch.object(A,"actual_source31_v1",return_value=(previous,old,{})), \
             patch.object(A,"actual_anchor_v1",return_value=anchor),patch.object(A,"checked",checked):
            result:tuple[bytes,A.BASEReport] = A.compose_compact_base_v1(source_ref=refs["source"],reference_ref=refs["reference"],
                export_ref=refs["export"],anchor_ref=refs["anchor"],observed_at_utc=W.utc().isoformat())
            return result

    def test_base_no_credit(self) -> None:
        body,report=self.compose(fixture())
        result=W.obj(W.load(body))
        self.assertEqual(len(A.rows(result)),COUNT)
        self.assertEqual(report["actual_new_FileIDs"],2*len(S.SDK))
        self.assertEqual(report["actual_shared_FileIDs"],SHARED)
        self.assertIs(result["runtime_admitted"],False)
        self.assertIs(result["actual_native_loaded"],False)
        self.assertEqual(result["new_campaign_credit"],0)
        self.assertNotIn("planned_saved_opening_date_raw",result)
        self.assertNotIn("canonical_preload_policy",result)

    def test_base_rejects_alias_duplicate(self) -> None:
        f=fixture();source=f[2];rich=W.sequence(source["files"])
        index=next(i for i,v in enumerate(rich) if W.obj(v)["relative"]==S.SDK[0])
        rich[index]={**W.obj(rich[index]),"file_identity":identity(1)};source["files"]=rich
        self.rejected(lambda:self.compose(f))
        f=fixture();values=W.sequence(f[3]["files"]);values.append(values[0]);f[3]["files"]=values
        self.rejected(lambda:self.compose(f))

if __name__=="__main__":
    unittest.main()
