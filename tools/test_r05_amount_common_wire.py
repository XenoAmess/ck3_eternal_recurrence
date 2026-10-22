"""One portable actual-R207 replay; no host, game, SDK or original-machine paths."""
from pathlib import Path
from decimal import Decimal
from types import SimpleNamespace
import argparse,copy,gzip,hashlib,importlib.util,json,os,sys,tempfile,unittest
from unittest import mock
from types import ModuleType
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
class ActualR207(unittest.TestCase):
    def test_actual_units_legacy_preservation_and_common_full(self):
        e=REPO/'docs/ck3-native-ai/acceptance/2026-10-18-r207-r05-initializer-units'
        index=json.loads((e/'source-index.actual.json').read_bytes())
        for ref in index['portable_sources']:
            p=REPO/ref['portable']['relative_path'];raw=p.read_bytes()
            self.assertEqual((len(raw),hashlib.sha256(raw).hexdigest()),(ref['portable']['bytes'],ref['portable']['sha256']))
            original=gzip.decompress(raw) if ref['compression']=='gzip' else raw
            self.assertEqual(hashlib.sha256(original).hexdigest(),ref['source']['sha256'])
        def read(name):
            raw=(e/name).read_bytes();return json.loads(gzip.decompress(raw) if name.endswith('.gz') else raw)
        before=read('public-before-snapshot.actual.json.gz')['rows'][0]['result']
        public=read('public-compact-query.actual.json.gz')['rows'][0]
        raw=read('native-wire-query-seq1-response.actual.jsonl.gz')['message']['result']
        outcome=read('initializer-outcome.actual.json.gz');claim=read('initializer-once-claim.actual.json.gz')
        from xar_autoplayer import bridge
        fixture=load('xar_autoplayer.bridge.r05_low_supply_fixture',REPO/'ck3_autonomous_player/src/xar_autoplayer/bridge/r05_low_supply_fixture.py')
        bridge.r05_low_supply_fixture=fixture
        full=load('ck3_mod_acceptance_full_army',REPO/'tools/ck3_mod_acceptance_full_army.py')
        from ck3_mod_acceptance_client import CaseClient
        run_id=index['run_id']
        class ReplayQueue(CaseClient):
            def __init__(self):
                self.selection=SimpleNamespace(run_dir=Path(run_id));self.report_path=Path('synthetic-wire-not-opened.json');self.output=Path('synthetic-output-not-created');self.saved=[]
            def validate_frame(self,frame,*args,**kwargs):return frame
            def native_wire_source(self):return {'path':str(self.report_path),'wire_evidence_codec':'plain','commit':None}
            def execute_plan(self,steps,name,timeout=None,reserve=90):
                step=steps[0];result=before if step['tool']=='ck3_take_snapshot' else public['result']
                return [{'id':step['id'],'ok':True,'result':result,'after_snapshot':public['after_snapshot']}]
            def checkpoint(self,name,value):self.saved.append((name,value))
        wire=SimpleNamespace(mark=lambda p,**kw:{'synthetic_queue_boundary':True},recover=lambda *a,**kw:(raw,{'actual_portable_native_wire':True,'complete_Driver_packet':False}))
        queue=ReplayQueue();wrapped=full.FullArmyResultClient(queue,wire,prefix='portable-replay')
        f=wrapped.snapshot();self.assertNotIn('episode_run_id',before);self.assertEqual(f['episode_run_id'],run_id)
        rows=wrapped.execute_plan([{'id':'strengths','tool':'ck3_query_army_strengths','args':{'army_ids':[0],'expected_revision':f['revision'],'profile':'observed_history_full_v1'}}],'strengths')
        self.assertEqual(rows[0]['id'],'strengths');self.assertEqual(rows[0]['continuation_public_step_id'],'portable-replay-strengths')
        witness=fixture.target_witness(f,rows[0]['result'],actor_id=33388,army_id=0,carmy_id=0,province_id=1506)
        self.assertEqual(witness['current_supply_raw'],11651751);self.assertEqual(len(wrapped.full_proofs),1)
        self.assertIs(full.ensure_common_full_army_client(wrapped),wrapped)
        self.assertIsInstance(full.ensure_common_full_army_client(queue),full.FullArmyResultClient)
        drift=dict(public['after_snapshot']);drift['revision']+=1
        old_after=public['after_snapshot'];public['after_snapshot']=drift
        failed=wrapped.execute_plan([{'id':'drift','tool':'ck3_query_army_strengths','args':{'army_ids':[0],'expected_revision':f['revision'],'profile':'observed_history_full_v1'}}],'drift')[0]
        from xar_autoplayer.bridge.r05_supply_observation_case import is_strength_revision_drift
        self.assertTrue(is_strength_revision_drift(failed));self.assertTrue(failed['derived_full_result_error'])
        self.assertTrue(failed['wire_full_result_proof']['original_public_row_ok'])
        public['after_snapshot']=old_after
        bad=dict(before);bad['episode_run_id']='other-run'
        with self.assertRaises(ValueError):full.bind_common_frame(bad,run_id)
        # The real negative case remains negative under the same production classifier.
        assessment=fixture.assess_initialization(claim['before'],outcome['independent_after'])
        self.assertEqual(assessment,outcome['assessment']);self.assertEqual(assessment['status'],'supply_changed_not_low_stock')
        self.assertEqual(11651751-11551851,99900);self.assertTrue(assessment['physical_soldiers_unchanged'])
        legacy=fixture.config(1506,'0.999');self.assertEqual(legacy,claim['config'])
        self.assertEqual(fixture.render_files(legacy)['common/decisions/xar_r05_low_supply_fixture.txt'],(e/'original-decision.actual.txt').read_bytes())
        new=fixture.config(1506,supply_loss_amount='116.51751')
        self.assertEqual(new['supply_loss_amount'],'116.51751');self.assertNotIn('supply_loss_fraction',new)
        decision=fixture.render_files(new)['common/decisions/xar_r05_low_supply_fixture.txt']
        self.assertIn(b'subtract_supply = 116.51751',decision);self.assertNotIn(b'deplete',decision)
        self.assertEqual(Decimal(new['supply_loss_amount'])*100000,witness['current_supply_raw'])
        for value in ('0','1.000001','1e2'):
            with self.assertRaises(ValueError):fixture.config(1506,supply_loss_amount=value)
        with self.assertRaises(ValueError):fixture.config(1506,'0.999',supply_loss_amount='116.51751')
        fixture.validate_fixture(e/'next-fixture-preview/fixture-manifest.json')

_HOST: ModuleType | None = None


def actual_host() -> ModuleType:
    global _HOST
    if _HOST is None:
        _HOST = load("actual_wire_host_under_test",
            REPO / "ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py")
        _HOST.configure_wire_evidence(argparse.Namespace(
            wire_evidence_codec="gzip-members", agent_source_root=REPO))
    return _HOST


def actual_r207_inputs() -> tuple[dict[str, object], dict[str, object], dict[str, object], str]:
    from ck3_mod_acceptance_native_day import obj
    evidence = REPO / "docs/ck3-native-ai/acceptance/2026-10-18-r207-r05-initializer-units"
    def read(name: str) -> dict[str, object]:
        data = (evidence / name).read_bytes()
        return obj(json.loads(gzip.decompress(data) if name.endswith(".gz") else data), "portable JSON")
    def row(name: str) -> dict[str, object]:
        rows = read(name).get("rows")
        if not isinstance(rows, list) or len(rows) != 1:
            raise ValueError("One actual portable row required")
        return obj(rows[0], "portable row")
    run_id = read("source-index.actual.json").get("run_id")
    if not isinstance(run_id, str) or not run_id:
        raise ValueError("Actual portable run ID required")
    message = obj(read("native-wire-query-seq1-response.actual.jsonl.gz").get("message"), "native message")
    return (obj(row("public-before-snapshot.actual.json.gz").get("result"), "before frame"),
            row("public-compact-query.actual.json.gz"), obj(message.get("result"), "native result"), run_id)


class ClosedWireMembers(unittest.TestCase):
    def test_actual_writer_caseclient_fullarmy_and_recover(self) -> None:
        import ck3_mod_acceptance_client as client_module
        import ck3_mod_acceptance_full_army as full
        from ck3_mod_acceptance_background_types import wire_evidence_path
        host = actual_host()
        before, public, native, run_id = actual_r207_inputs()
        for codec, legacy in (("plain", True), ("plain", False), ("gzip-members", False)):
            with self.subTest(codec=codec, legacy=legacy), tempfile.TemporaryDirectory(prefix="wire-e2e-") as temp:
                root = Path(temp); live = root / run_id; live.mkdir()
                report_path = live / "native-report.json"
                # A deliberately different actual name catches suffix guessing.
                native_path = live / ("actual-selected-native.gz" if codec == "gzip-members" else "actual-selected-native.log")
                if codec == "gzip-members":
                    # The actual host's report-sidecar reader uses its allocated
                    # path. Rename the report, rather than invent a sidecar.
                    report_path = live / "native-report.json"
                    native_path = wire_evidence_path(report_path, "native-wire", codec)
                writer = host.JsonLines(native_path, codec)
                writer.write("fixture-boundary", {"synthetic_endpoint": True})
                queue = root / "once-queue.py"; queue.write_text("# transport boundary only\n", encoding="utf-8")
                frame = copy.deepcopy(before); row_source = copy.deepcopy(public)
                frame["managed_campaign_run_binding"] = {"run_id": run_id}
                row_source["after_snapshot"]["managed_campaign_run_binding"] = {"run_id": run_id}
                hello = frame["diagnostics"]["hello"]
                state = root / "state"
                reports = {"state_dir": str(state), "agent_source_root": str(REPO),
                    "native_wire": str(native_path), "mcp_wire": str(wire_evidence_path(report_path, "mcp-wire", codec)),
                    "mcp_calls": str(wire_evidence_path(report_path, "mcp-calls", codec)), "steps": []}
                if not legacy:
                    reports["wire_evidence_codec"] = codec
                def publish() -> None:
                    if codec == "gzip-members":
                        reports["wire_evidence_commits"] = host.wire_evidence_commits(report_path)
                    host.write_atomic_report(report_path, reports)
                publish()
                selected = SimpleNamespace(run_dir=live, runtime_path=root / "runtime.json",
                    runtime={"control_queue": {"path": str(queue), "bytes": queue.stat().st_size,
                                               "sha256": hashlib.sha256(queue.read_bytes()).hexdigest()}},
                    locations={"python": Path(sys.executable), "repo_root": REPO},
                    runtime_environment={}, manifest_path_key=lambda value: Path(value).resolve())
                class OriginalClient(client_module.CaseClient):
                    def __init__(self) -> None:
                        self.selection=selected;self.live=live;self.state=state
                        self.report_path=report_path;self.output=live/"case-output";self.output.mkdir()
                        self.manifest={"source_root":str(REPO), "game":{"version":hello["expected_ck3_version"],
                            "exe_sha256":hello["expected_ck3_sha256"]}, "host_features":{} if legacy else {"wire_evidence_codec":codec}}
                        self._report_stat=None;self._report=None;self._hold=None;self._binding=None
                        self.frozen={};self._seq=0;self.completed=[]
                    def guard(self, reserve=90, *, failure_shutdown=False):
                        return self.read_report()
                    def remaining(self) -> int:
                        return 600
                    def await_steps(self, steps, timeout, reserve):
                        return copy.deepcopy(self.completed)
                client = OriginalClient(); queries = []
                def enqueue(live_path: Path, plan_path: Path, name: str, *, deadline: float) -> dict[str, object]:
                    self.assertEqual(live_path, live)
                    step = json.loads(plan_path.read_bytes())["steps"][0]
                    if step["tool"] == "ck3_take_snapshot":
                        result = {"id": step["id"], "ok": True, "result": copy.deepcopy(frame)}
                    else:
                        queries.append(copy.deepcopy(step))
                        request = {"type": "execute_step", "protocol_version": 1, "request_id": "r207-original",
                            "step": "query-army-strengths-v1", "expected_revision": frame["native_revision"],
                            "army_ids": step["args"]["army_ids"], "army_strengths_profile": step["args"]["profile"]}
                        response = {"type": "command_result", "protocol_version": 1, "request_id": "r207-original",
                            "ok": True, "result": copy.deepcopy(native)}
                        writer.write("python-to-dll", request);writer.write("dll-to-python", response)
                        result = {**copy.deepcopy(row_source), "id": step["id"]}
                    client.completed=[result]
                    reports["steps"].append({**copy.deepcopy(result), "finished_at": "synthetic-completed"})
                    publish()
                    return {"status": "QUEUED", "synthetic_transport_only": True}
                transport=SimpleNamespace(enqueue=enqueue, enqueue_deadline=lambda: None)
                wrapped=full.FullArmyResultClient(client, prefix="production-chain")
                with mock.patch.object(client_module, "load_pinned_control_queue", return_value={"module":transport}):
                    actual_frame=wrapped.snapshot()
                    result=wrapped.execute_plan([{"id":"query", "tool":"ck3_query_army_strengths",
                        "args":{"army_ids":[0], "expected_revision":actual_frame["revision"],
                                "profile":"observed_history_full_v1"}}], "query")[0]
                self.assertTrue(result["ok"]);self.assertEqual(len(queries),1)
                self.assertEqual(result["result"]["queried_native_revision"],frame["native_revision"])
                proof=result["wire_full_result_proof"]
                self.assertEqual(proof["wire_evidence_codec"],codec)
                self.assertEqual(proof["native_request_id"],"r207-original")
                self.assertEqual(proof["query_sequence"],native["query_sequence"])
                self.assertEqual(json.loads(json.dumps(proof)),proof)
                self.assertFalse(proof["query_reissued"]);self.assertFalse(proof["complete_Driver_packet"])
                self.assertEqual(proof["file_identity_at_read"]["provider"],
                                 "win32-file-id-info" if os.name=="nt" else "posix-fstat")
                logical=proof["logical_range"];physical=proof["physical_range"]
                selected_bytes=native_path.read_bytes()[int(physical["begin"]):int(physical["end"])]
                logical_bytes=gzip.decompress(selected_bytes) if codec=="gzip-members" else selected_bytes
                self.assertEqual(hashlib.sha256(selected_bytes).hexdigest(),physical["sha256"])
                self.assertEqual(hashlib.sha256(logical_bytes).hexdigest(),logical["sha256"])
                self.assertEqual(len(logical_bytes),logical["bytes"])
                queue_result=json.loads((client.output/"production-chain-query.queue-result.json").read_bytes())
                self.assertEqual(queue_result["execution_mode"],"IN_PROCESS_PINNED_QUEUE_LIBRARY")

    def test_closed_member_ranges_crc_scope_and_json_boundaries(self) -> None:
        import ck3_mod_acceptance_army_wire as wire
        from ck3_mod_acceptance_background_types import (
            wire_evidence_codec, wire_evidence_commit, wire_evidence_source, wire_evidence_path,
            wire_file_identity_value)
        host=actual_host()
        summary={"step":wire.STEP,"accepted":True,"status":"available","query_sequence":7,
            "army_strengths_profile":"observed_history_full_v1","army_observed_phase_coverage":{}}
        request={"type":"execute_step","protocol_version":1,"request_id":"original-once","step":wire.STEP,
            "expected_revision":12,"army_ids":[0],"army_strengths_profile":"observed_history_full_v1"}
        response={"type":"command_result","protocol_version":1,"request_id":"original-once","ok":True,"result":summary}
        for codec in ("plain","gzip-members"):
            with self.subTest(codec=codec),tempfile.TemporaryDirectory(prefix="wire-ranges-") as temp:
                report=Path(temp)/"native-report.json";path=wire_evidence_path(report,"native-wire",codec)
                writer=host.JsonLines(path,codec);writer.write("seed",{"before":True})
                initial=writer._commit if codec=="gzip-members" else None
                mark=wire.mark(path,codec=codec,commit=initial)
                bookmark=json.loads(json.dumps(mark))
                writer.write("python-to-dll",request);writer.write("dll-to-python",response)
                commit=copy.deepcopy(writer._commit) if codec=="gzip-members" else None
                pristine=path.read_bytes()
                raw,proof=wire.recover(bookmark,summary,native_revision=12,army_ids=[0],
                    profile="observed_history_full_v1",end_commit=commit)
                self.assertEqual(raw,summary);self.assertEqual(json.loads(json.dumps(proof)),proof)
                with path.open("ab") as stream:stream.write(b"unpublished partial tail")
                again,_=wire.recover(bookmark,summary,native_revision=12,army_ids=[0],
                    profile="observed_history_full_v1",end_commit=commit)
                self.assertEqual(again,summary)
                path.write_bytes(pristine)
                for key,bad in (("query_sequence",True),("query_sequence",7.0),("query_sequence",8),
                                ("army_strengths_profile","ordinary_core_v1"),("accepted",1)):
                    wrong={**summary,key:bad}
                    with self.subTest(wrong=key,value=bad),self.assertRaises(ValueError):
                        wire.recover(bookmark,wrong,native_revision=12,army_ids=[0],
                            profile="observed_history_full_v1",end_commit=commit)
                for ids in ([False],[0.0],[0,0],[-1]):
                    with self.subTest(ids=ids),self.assertRaises(ValueError):
                        wire.recover(bookmark,summary,native_revision=12,army_ids=ids,
                            profile="observed_history_full_v1",end_commit=commit)
                with self.assertRaises(ValueError):
                    wire.recover(bookmark,summary,native_revision=True,army_ids=[0],
                        profile="observed_history_full_v1",end_commit=commit)
                if codec=="plain":
                    legacy={"path":str(path),"file_identity":[path.stat().st_dev,path.stat().st_ino],
                            "offset":int(bookmark["physical_offset"])}
                    _,oldproof=wire.recover(json.loads(json.dumps(legacy)),summary,native_revision=12,
                        army_ids=[0],profile="observed_history_full_v1")
                    self.assertEqual(oldproof["identity_binding"],"legacy-fstat")
                else:
                    self.assertIsNotNone(commit)
                    for key,value in (("stream_id","f"*32),("logical_bytes",str(int(commit["logical_bytes"])+1)),
                            ("record_count",commit["record_count"]+1),("last_member_sha256","0"*64)):
                        changed={**commit,key:value}
                        with self.subTest(commit_field=key),self.assertRaises(ValueError):
                            wire.recover(bookmark,summary,native_revision=12,army_ids=[0],
                                profile="observed_history_full_v1",end_commit=changed)
                    # Corrupt the request member, while the last response and
                    # its published SHA remain intact: each member CRC matters.
                    damaged=bytearray(pristine);damaged[int(bookmark["physical_offset"])+12]^=1
                    path.write_bytes(damaged)
                    with self.assertRaises(ValueError):
                        wire.recover(bookmark,summary,native_revision=12,army_ids=[0],
                            profile="observed_history_full_v1",end_commit=commit)
                    path.write_bytes(pristine[:-1])
                    with self.assertRaises(ValueError):
                        wire.recover(bookmark,summary,native_revision=12,army_ids=[0],
                            profile="observed_history_full_v1",end_commit=commit)
                    path.write_bytes(pristine)
                    meta={"native_wire":str(path),"mcp_wire":str(wire_evidence_path(report,"mcp-wire",codec)),
                        "mcp_calls":str(wire_evidence_path(report,"mcp-calls",codec)),
                        "wire_evidence_codec":codec,"wire_evidence_commits":host.wire_evidence_commits(report)}
                    self.assertEqual(wire_evidence_source(meta,report,codec)["commit"],commit)
                    for mutation in ("missing","null","roles","path","type","file-id"):
                        changed=copy.deepcopy(meta)
                        if mutation=="missing":changed.pop("wire_evidence_codec")
                        elif mutation=="null":changed["wire_evidence_codec"]=None
                        elif mutation=="roles":changed["wire_evidence_commits"].pop("mcp-calls")
                        elif mutation=="path":changed["native_wire"]=str(Path(temp).parent/"outside.gz")
                        elif mutation=="type":changed["wire_evidence_commits"]["native-wire"]["record_count"]=True
                        else:changed["wire_evidence_commits"]["native-wire"]["file_identity"]["inode"]="01"
                        with self.subTest(metadata=mutation),self.assertRaises(ValueError):
                            wire_evidence_source(changed,report,codec)
                    for key,value in (("record_count",False),("logical_bytes",1),("completed_physical_offset","01")):
                        with self.assertRaises(ValueError):wire_evidence_commit({**commit,key:value})
                    no_member={**meta,"wire_evidence_commits":{k:None for k in ("native-wire","mcp-wire","mcp-calls")}}
                    with self.assertRaises(ValueError):wire_evidence_source(no_member,report,codec)
                    wrong_identity={**bookmark,"file_identity":{**bookmark["file_identity"],"inode":"1"}}
                    with self.assertRaises(ValueError):
                        wire.recover(wrong_identity,summary,native_revision=12,army_ids=[0],
                            profile="observed_history_full_v1",end_commit=commit)
        for value in (None,False,0,"gzip","GZIP-members"):
            with self.subTest(codec=value),self.assertRaises(ValueError):wire_evidence_codec(value)
        for value in (None,{"provider":"win32-file-id-info","device":"0","inode":"0"},
                      {"provider":"posix-fstat","device":False,"inode":"1"}):
            with self.assertRaises(ValueError):wire_file_identity_value(value)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--repo-root',type=Path,default=ROOT);p.add_argument('--dependencies-root',type=Path)
    p.add_argument('-v','--verbose',action='store_true')
    p.add_argument('--receipt',type=Path);a=p.parse_args();REPO=a.repo_root.resolve();deps=(a.dependencies_root or REPO).resolve()
    sys.path[:0]=[str(REPO/'tools'),str(deps/'tools'),str(deps/'ck3_autonomous_player/src')]
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    if a.receipt:
        from ck3_live_run_id import current_machine_id
        v={'machine_id':current_machine_id(),'status':'PASS' if result.wasSuccessful() else 'RED','tests':result.testsRun,
            'scope':'portable R207 replay; actual shared writer to original CaseClient/full Army recovery for plain and closed gzip members; field, CRC and truncation guards',
            'source_evidence_machine_id':'desktop-3fevhd2-1c74096080','SDK_calls':0,'new_amount_live_qualified':False,'R05_positive':False}
        with a.receipt.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,indent=2);f.write('\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
