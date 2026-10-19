"""Finite pure checks; no Game, D-root reads, UAC, WMI, Task or compiler."""
import ast
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest
from types import SimpleNamespace
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
MACHINE = "synthetic-machine"
def module(name):
    spec = importlib.util.spec_from_file_location(name,HERE/(name+".py"))
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value
Q = module("native30_two_stage_qualification_20261020")
A = module("native30_two_stage_admin_20261020")

def data():
    fixtures = [{"target":"project_test_"+str(i),"artifact":"project_test_%d.exe"%i} for i in range(9)]
    manifest = {"files":[{"path":str((Q.ROOT/"build"/f["artifact"]).resolve()),"target":f["target"],"size":123,"sha256":"a"*64}
                         for f in fixtures]}
    raw = json.dumps(manifest).encode()
    before = {"ExclusionPath":["C:/prior/project.exe"],"ExclusionExtension":[],"ExclusionProcess":["existing"]}
    after = copy.deepcopy(before)
    after["ExclusionPath"] += [r["path"] for r in manifest["files"]]
    build = {"path":"synthetic/result.json","bytes":100,"sha256":"b"*64}
    receipt = {"schema":"native30-exact-nine-admin-registration-v1","machine_id":MACHINE,"status":"verified","actual_admin":True,
        "actual_sid":Q.OWNER_SID,"build_result":build,"manifest_sha256":hashlib.sha256(raw).hexdigest(),
        "before_settings":before,"after_settings":after,"verified_requested_paths":[r["path"] for r in manifest["files"]],
        "helper_receipt":{"status":"verified","admin_token":True,"observed_prior_settings_preserved":True,"files":manifest["files"]},
        "exe_bindings":[{} for _ in range(9)]}
    return fixtures,manifest,raw,receipt,build

class TwoStage(unittest.TestCase):
    def test_exact_nine_declared_targets(self):
        fixtures,manifest,*_ = data()
        Q.exact_fixture_set(manifest,fixtures)
        for change in (lambda m:m["files"].pop(),lambda m:m["files"].append(m["files"][0]),
            lambda m:m["files"][0].update(target="other"),lambda m:m["files"][0].update(path="C:/Python/python.exe")):
            changed = copy.deepcopy(manifest)
            change(changed)
            with self.assertRaises(RuntimeError): Q.exact_fixture_set(changed,fixtures)

    def test_full_admin_receipt(self):
        _,manifest,raw,receipt,build = data()
        with patch.object(Path,"read_bytes",return_value=raw): Q.verify_admin(receipt,manifest,build,MACHINE)

    def test_admin_unknown_or_partial_reject(self):
        _,manifest,raw,receipt,build = data()
        changes = [lambda r:r.update(machine_id="other"),lambda r:r.update(actual_admin=False),lambda r:r.update(actual_sid="S-1-5-18"),
            lambda r:r.update(status="settings_failed"),lambda r:r.update(manifest_sha256="wrong"),
            lambda r:r.update(build_result={}),lambda r:r.update(exe_bindings=[]),
            lambda r:r["helper_receipt"].update(files=[]),lambda r:r["helper_receipt"].update(admin_token=False),
            lambda r:r["after_settings"].update(ExclusionProcess=["changed"]),
            lambda r:r["after_settings"].update(ExclusionExtension=[".exe"]),
            lambda r:r["after_settings"].update(ExclusionPath=[]),lambda r:r.update(verified_requested_paths=[]),
            lambda r:r.update(before_settings=None),lambda r:r["after_settings"].pop("ExclusionProcess")]
        with patch.object(Path,"read_bytes",return_value=raw):
            for number,change in enumerate(changes):
                candidate = copy.deepcopy(receipt)
                change(candidate)
                with self.subTest(number=number), self.assertRaises(RuntimeError): Q.verify_admin(candidate,manifest,build,MACHINE)

    def test_same_file_id_and_bytes(self):
        value = {"path":str(Q.ROOT/"build/a.exe"),"bytes":12,"sha256":"a","file_id":{"volume_serial":"1","file_id":"2"}}
        self.assertTrue(Q.same_file(value,copy.deepcopy(value)))
        for key,replacement in (("path",str(Q.ROOT/"build/b.exe")),("bytes",13),("sha256","b"),("file_id",{})):
            changed = {**value,key:replacement}
            self.assertFalse(Q.same_file(value,changed))

    def test_three_arrays_one_client(self):
        before = {"ExclusionPath":["prior"],"ExclusionExtension":[],"ExclusionProcess":[]}
        class Client:
            def __init__(self): self.value=copy.deepcopy(before); self.reads=0; self.adds=[]
            def read_settings(self): self.reads+=1; return copy.deepcopy(self.value)
            def add_path(self,path): self.adds.append(path); self.value["ExclusionPath"].append(path); return None
        client = Client()
        adapter = A.FullSettingsClient(client)
        self.assertIs(adapter.client,client)
        self.assertIsNone(adapter.add_path("exact"))
        self.assertEqual(adapter.read_paths(),["prior","exact"])
        self.assertEqual((client.reads,client.adds),(2,["exact"]))
        self.assertEqual(adapter.before,before)
        client.value["ExclusionProcess"] = ["wrong"]
        with self.assertRaises(RuntimeError): adapter.read_paths()
        self.assertEqual(client.adds,["exact"])

    def test_admin_missing_settings_never_adds(self):
        class Client:
            def read_settings(self): return {"ExclusionPath":[]}
            def add_path(self,path): raise AssertionError("must not Add")
        with self.assertRaises(RuntimeError): A.FullSettingsClient(Client())

    def test_path_loss_rejects(self):
        class Client:
            def __init__(self): self.count=0
            def read_settings(self):
                self.count+=1
                return {"ExclusionPath":["old"] if self.count==1 else [],"ExclusionExtension":[],"ExclusionProcess":[]}
        value = A.FullSettingsClient(Client())
        with self.assertRaises(RuntimeError): value.read_paths()

    def test_build_branch_cannot_execute_project_exe(self):
        tree = ast.parse((HERE/"native30_two_stage_qualification_20261020.py").read_text())
        branch = next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=="args.phase == 'build'"
                      and any(isinstance(x,ast.For) for x in n.body))
        calls = [n for top in branch.body for n in ast.walk(top) if isinstance(n,ast.Call) and ast.unparse(n.func)=="run_command"]
        self.assertEqual(len(calls),2) # frozen initializer and explicit Ninja target builds.
        self.assertEqual({ast.unparse(n.args[0].elts[0]) for n in calls},{"sys.executable","state['tools']['ninja']"})
        for n in calls:
            if ast.unparse(n.args[0].elts[0]) == "state['tools']['ninja']": self.assertIn("'-f'",ast.unparse(n.args[0]))

    def test_admin_is_one_explicit_consent_not_broker_install(self):
        text = (HERE/"native30_two_stage_admin_20261020.py").read_text()
        tree = ast.parse(text)
        calls = [n for n in ast.walk(tree) if isinstance(n,ast.Call) and ast.unparse(n.func)=="shell.ShellExecuteEx"]
        self.assertEqual(len(calls),1)
        self.assertIn('lpVerb="runas"',text)
        self.assertNotIn("RegisterTaskDefinition",text)
        self.assertNotIn("TerminateProcess",text)

    def test_run_revalidates_before_stage_write(self):
        tree = ast.parse((HERE/"native30_two_stage_qualification_20261020.py").read_text())
        node = next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="execute")
        calls = [(n.lineno,ast.unparse(n.func)) for n in ast.walk(node) if isinstance(n,ast.Call)]
        mkdir = next(line for line,name in calls if name=="stage.mkdir")
        for name in ("preflight","build_closed","run_handoff"):
            self.assertLess(next(line for line,value in calls if value==name),mkdir)
        self.assertLess(next(line for line,name in calls if name=="run_handoff"),
                        next(line for line,name in calls if name=="preflight"))

    def test_launch_closure_rejects_timeout_even_with_verified_child(self):
        build,admin = {"sha256":"build"},{"sha256":"admin"}
        value = {"schema":"native30-exact-nine-admin-launch-v1","machine_id":MACHINE,"status":"VERIFIED",
            "settings_success":True,"UAC_calls":1,"actual_exit_code":0,"future_writes":0,
            "build_result":build,"admin_result":admin}
        Q.verify_launch(value,build,admin,MACHINE)
        for key,replacement in (("machine_id","other"),("schema","other"),("status","FAILED_OR_UNKNOWN"),
            ("settings_success",False),("UAC_calls",0),("UAC_calls",True),("actual_exit_code",None),
            ("actual_exit_code",1),("actual_exit_code",False),("future_writes",None),("future_writes",1),
            ("build_result",{}),("admin_result",{})):
            with self.subTest(key=key,value=replacement), self.assertRaises(RuntimeError):
                Q.verify_launch({**value,key:replacement},build,admin,MACHINE)

    def test_run_late_child_does_not_bypass_parent_unknown(self):
        _,manifest,raw,receipt,build = data()
        receipt["future_writes"] = 0
        base = SimpleNamespace(MIB=1024**2,machine=lambda:MACHINE,pin=lambda path:build if path==Q.BUILD/"RESULT.json"
            else {"sha256":"admin"})
        def load(path,*args):
            return receipt if path.name=="RESULT.json" else {"machine_id":MACHINE,"status":"FAILED_OR_UNKNOWN"}
        with patch.object(Q,"build_records",return_value=({},manifest)),patch.object(Q,"finite_load",side_effect=load),\
             patch.object(Path,"read_bytes",return_value=raw), self.assertRaisesRegex(RuntimeError,"known successful"):
            Q.run_handoff(base,SimpleNamespace(admin_receipt_sha256="admin"))

    def test_build_result_and_owner_machine_are_explicit(self):
        base = SimpleNamespace(machine=lambda:MACHINE,digest=lambda path:"manifest")
        result = {"machine_id":MACHINE,"schema":Q.SCHEMA,"protocol_version":1,"stage":"build_only",
            "status":"BUILD_READY_FOR_ADMIN","owned_active_after":0,"future_writes":0,"fixture_executions":0,
            "fixture_builds":[{"returncode":0,"owned_active_after":0} for _ in range(9)],
            "project_exe_manifest":{"sha256":"manifest"}}
        owner = {"machine_id":MACHINE,"child_exit_code":0,"bootstrap_exit_code":0,"job_active_after_stage":0,
            "forced_remaining_cleanup":False}
        def load(path): return owner if path.name=="CLOSED.json" else result if path.name=="RESULT.json" else {}
        with patch.object(Q,"finite_load",side_effect=load):
            Q.build_records(base)
            result["machine_id"]="other"
            with self.assertRaisesRegex(RuntimeError,"build result machine"): Q.build_records(base)
            result["machine_id"]=MACHINE
            owner["machine_id"]="other"
            with self.assertRaisesRegex(RuntimeError,"Task machine"): Q.build_records(base)

    def test_failed_after_validation_keeps_actual_three_arrays(self):
        class Client:
            def __init__(self): self.value={"ExclusionPath":["old"],"ExclusionExtension":[],"ExclusionProcess":[]}
            def read_settings(self): return copy.deepcopy(self.value)
        client=Client()
        adapter=A.FullSettingsClient(client)
        client.value["ExclusionProcess"]=["unexpected"]
        result={"status":"settings_failed","after_settings":None}
        A.preserve_final_settings(result,adapter)
        self.assertEqual(result["after_settings"],client.value)
        self.assertIn("final_read_error",result)
        self.assertEqual(result["status"],"settings_failed")

    def test_started_requires_real_owned_directory_and_create_only(self):
        import sys
        identity={"pid":1,"creation_filetime":"134369147039553883","sid":Q.OWNER_SID}
        base=SimpleNamespace(machine=lambda:MACHINE,utc=lambda:"synthetic",pin=lambda path:{"sha256":"started"})
        security=SimpleNamespace(OWNER_SECURITY_INFORMATION=1,GetFileSecurity=lambda *a:SimpleNamespace(GetSecurityDescriptorOwner=lambda:1),
            ConvertSidToStringSid=lambda value:Q.OWNER_SID)
        with patch.dict(sys.modules,{"win32security":security}),patch.object(Path,"is_dir",return_value=False):
            with self.assertRaisesRegex(RuntimeError,"actual administrator directory"): A.begin_admin(base,identity,{},"manifest")
        with patch.dict(sys.modules,{"win32security":security}),patch.object(Path,"is_dir",return_value=True),\
             patch.object(Path,"lstat",return_value=SimpleNamespace(st_file_attributes=0)),\
             patch.object(Path,"exists",return_value=False),patch.object(Path,"open",side_effect=FileExistsError("started exists")) as opened:
            with self.assertRaises(FileExistsError): A.begin_admin(base,identity,{},"manifest")
            self.assertEqual(opened.call_args.args,("x",))
        for birth in (None,2,False,"","0","01","-1","not-decimal"):
            with self.subTest(birth=birth),patch.dict(sys.modules,{"win32security":security}),\
                 patch.object(Path,"is_dir",return_value=True),\
                 patch.object(Path,"lstat",return_value=SimpleNamespace(st_file_attributes=0)),\
                 patch.object(Path,"exists",return_value=False),patch.object(Path,"open") as opened:
                with self.assertRaisesRegex(RuntimeError,"process identity"):
                    A.begin_admin(base,{**identity,"creation_filetime":birth},{},"manifest")
                opened.assert_not_called()
        security.ConvertSidToStringSid=lambda value:"other"
        with patch.dict(sys.modules,{"win32security":security}),patch.object(Path,"is_dir",return_value=True),\
             patch.object(Path,"lstat",return_value=SimpleNamespace(st_file_attributes=0)):
            with self.assertRaisesRegex(RuntimeError,"directory owner"): A.begin_admin(base,identity,{},"manifest")

    def test_started_precedes_wmi_construction(self):
        tree=ast.parse((HERE/"native30_two_stage_admin_20261020.py").read_text())
        node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="elevated")
        calls={ast.unparse(n.func):n.lineno for n in ast.walk(node) if isinstance(n,ast.Call)}
        self.assertLess(calls["begin_admin"],calls["SameAdminDefenderClient"])

if __name__ == "__main__": unittest.main()
