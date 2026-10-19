"""Five new cross-seam source cases; no old custody/timing matrix or children."""
import ast,copy,hashlib,json,sys,types,unittest
from datetime import datetime,timezone
from pathlib import Path

import prepare_c19_canonical_controls_v1 as producer

GRAPH,REPORT=producer._compose_source_candidate('Native30 UNQUALIFIED SOURCE-ONLY FIXTURE',full_timing=True)
HELPER=ast.parse(GRAPH['root_c19_canonical_outer.py'])
CLASS=next(n for n in HELPER.body if isinstance(n,ast.ClassDef) and n.name=='OuterBindingV1')


def subject_class():
    names={'child_env','revoke','close'}
    methods=[copy.deepcopy(n) for n in CLASS.body if isinstance(n,ast.FunctionDef) and n.name in names]
    init=next(n for n in CLASS.body if isinstance(n,ast.FunctionDef) and n.name=='__init__')
    pos=next(i for i,n in enumerate(init.body) if isinstance(n,ast.Assign)
             and any(isinstance(t,ast.Attribute) and t.attr=='wal_enabled' for t in n.targets))
    policy=ast.FunctionDef(name='set_policy',args=ast.arguments(posonlyargs=[],args=[ast.arg(arg='self'),ast.arg(arg='policy')],kwonlyargs=[],kw_defaults=[],defaults=[]),
        body=[ast.Assign(targets=[ast.Attribute(value=ast.Name(id='self',ctx=ast.Load()),attr='policy',ctx=ast.Store())],value=ast.Name(id='policy',ctx=ast.Load())),
              *copy.deepcopy(init.body[pos:pos+2])],decorator_list=[])
    source=ast.Module(body=[ast.ClassDef(name='Subject',bases=[],keywords=[],body=[policy,*methods],decorator_list=[])],type_ignores=[])
    scope={'require':producer.require}
    exec(compile(ast.fix_missing_locations(source),'actual-C19-helper-seams','exec'),scope)
    return scope['Subject']


Subject=subject_class()


class CrossSeams(unittest.TestCase):
    def test_01_true_creator_chain_survives_timing_and_final_pins(self):
        producer.assert_true_graph(GRAPH)
        queue=GRAPH['root_p37c19_sdk_queue.py'].decode()
        self.assertIn('@_full_rows_v1(enabled=True)',queue)
        self.assertIn('admission_getter=lambda queue: None',queue)
        self.assertNotIn("admission_getter=lambda queue: queue._normal_cold",queue)
        self.assertIn('_canonical.spawn_queue',GRAPH['launch_sdk_p37c19_owner.py'].decode())
        self.assertIn('canonical.factory.pre_native_resume',GRAPH['root_native30_supervisor_c19.py'].decode())
        self.assertIn('_canonical.install_service(service)',GRAPH['root_p37c19_mcp_entry.py'].decode())
        self.assertEqual(dict(REPORT['entry_source_pins_after_all_edits']),
                         {str(producer.T/name):producer.sha(raw) for name,raw in GRAPH.items()})
        self.assertEqual(REPORT['business_plan']['complete_files'],1454)
        self.assertEqual(REPORT['business_plan']['actual_H'],'unknown')
        normal=GRAPH['root_c19_normal_checkpoint_inputs.py'].decode()
        self.assertIn('EXACT_C18_NORMAL_CHECKPOINT_FOR_C19',normal)
        self.assertIn('134369092460097880',normal)
        self.assertIn('134369092487102977',normal)
        self.assertTrue(REPORT['unapplied_feeder_timing']['not_an_admitted_cold_feeder'])

    def test_02_false_graph_rejected_and_source_defaults_do_not_mint_custody(self):
        bad=dict(GRAPH);name='root_native30_supervisor_c19.py'
        old=b'prepare_supervisor(N, enabled=True)';self.assertEqual(bad[name].count(old),1)
        bad[name]=bad[name].replace(old,b'prepare_supervisor(N, enabled=False)',1)
        with self.assertRaises(ValueError):producer.assert_true_graph(bad)
        with self.assertRaises(ValueError):producer.build_sources(canonical_enabled=False)
        self.assertTrue(REPORT['source_fixture'])
        self.assertFalse(REPORT['control_probe_enabled'])
        # The old creator's public default stays OFF; only the exact emitted
        # real-supervisor/entry call sites use True. No generic default changed.
        self.assertIn(b'def prepare_supervisor(root, *, enabled=False):',GRAPH['root_c19_canonical_outer.py'])

    def test_03_explicit_WAL_policy_only_owned_child_environment(self):
        q=Subject();original={'KEEP':'same','XAR_CK3_ENABLE_DRIVER_STATE_WAL_V1':'1'}
        q.set_policy({});q.dependency_root='frozen-dependencies'
        result=q.child_env(original)
        self.assertNotIn('XAR_CK3_ENABLE_DRIVER_STATE_WAL_V1',result)
        self.assertEqual(original['XAR_CK3_ENABLE_DRIVER_STATE_WAL_V1'],'1')
        q.set_policy({'enable_driver_state_wal_v1':True})
        self.assertEqual(q.child_env({'KEEP':'same'})['XAR_CK3_ENABLE_DRIVER_STATE_WAL_V1'],'1')
        self.assertEqual(q.child_env({'KEEP':'same'})['KEEP'],'same')
        for value in (1,'1',None):
            with self.assertRaises(ValueError):q.set_policy({'enable_driver_state_wal_v1':value})
        task=(producer.OWN/'interactive_task_owner_v1.py').read_text(encoding='utf8')
        self.assertIn('s["role"] != "sdk_owner"',task)
        self.assertIn('enable_driver_state_wal and role != "sdk_owner"',task)

    def test_04_revoke_join_then_owned_close_borrowed_and_unknown_retained(self):
        def fixture(*,alive=False,revoke_error=False,join_error=False):
            events=[];q=Subject()
            class Origin:
                def revoke_before_close(self):
                    events.append('revoke')
                    if revoke_error:raise OSError('original revoke failed')
            class Thread:
                def join(self,timeout):
                    events.append(('join',timeout))
                    if join_error:raise OSError('original join failed')
                def is_alive(self):return alive
            class Factory:
                origin=Origin()
                def close(self):events.append('factory_close');return {'owned':0,'borrowed_closed':0}
            class Borrowed:
                def close(self):raise AssertionError('borrowed resource closed')
            q.factory=Factory();q.server_thread=Thread();q.plan=None;q.revoked=False
            q.borrowed=Borrowed()
            return q,events
        q,events=fixture();self.assertEqual(q.close(),{'owned':0,'borrowed_closed':0})
        self.assertEqual(events,['revoke',('join',10),'factory_close']);self.assertTrue(q.revoked)
        for kwargs in ({'alive':True},{'revoke_error':True},{'join_error':True}):
            q,events=fixture(**kwargs)
            with self.assertRaises((ValueError,OSError)):q.close()
            self.assertNotIn('factory_close',events);self.assertFalse(q.revoked)

    def test_05_unqualified_Native_and_placeholder_never_public_output(self):
        with self.assertRaises(ValueError):producer.build_sources()
        with self.assertRaises(ValueError):producer.build_sources(native_transition_inputs={'label':'Native30 PLACEHOLDER'})
        for fixture,label in ((True,'Native30 typed source fixture'),(False,'Native30 PLACEHOLDER')):
            with self.assertRaises(ValueError):
                producer._qualified_label(types.SimpleNamespace(source_fixture=fixture,target_native={'native_build_label':label}))
        self.assertFalse(REPORT['outputs_materialized'])
        # The private source fixture is deliberately not an actual Native/H
        # qualification, and never registers a Task or creates a process.
        self.assertEqual(REPORT['old_Game'],{'pid':30852,'creation_filetime':134368995759027619})
        self.assertEqual(REPORT['WAL_requested_policy'],{'enable_driver_state_wal_v1':True})
        self.assertFalse(REPORT['WAL_policy_default'])


def main(output):
    result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(CrossSeams))
    if not result.wasSuccessful():raise SystemExit(1)
    paths=[Path(producer.__file__),Path(__file__)]
    proof=dict(schema='xar.C19-true-canonical-controls-source-qualification/v1',machine_id=producer.MACHINE,
        observed_at_utc=datetime.now(timezone.utc).isoformat(),status='SOURCE_READY_TRUE_GRAPH_NATIVE30_ACTUAL_REFS_REQUIRED',
        files={str(p.resolve()):{'bytes':p.stat().st_size,'sha256':producer.sha(p.read_bytes())} for p in paths},
        in_memory_graph={n:{'bytes':len(raw),'sha256':producer.sha(raw)} for n,raw in GRAPH.items()},
        new_cross_seam_tests=result.testsRun,old_57_custody_or_12_timing_matrix_repeated=False,
        report={key:value for key,value in REPORT.items() if key!='entry_source_pins_after_all_edits'},
        final_entry_pins_count=len(REPORT['entry_source_pins_after_all_edits']),
        final_entry_pins_sha256=producer.sha(json.dumps(REPORT['entry_source_pins_after_all_edits'],separators=(',',':')).encode()),
        source_input_pins=producer.PINS,native_transition_tool_pins=producer.NATIVE_TOOLS,
        target_Native30_qualified=False,actual_H='unknown',outputs_materialized=False,
        scratch_files=0,Game_Native_MCP_Task_calls=0,external_writes=0,
        limitations=['future Native30 real qualified references required by public producer; current FAILED/0fixture is not qualified',
          'future C19 cold feeder actual admission/launcher remains then-actual finite attachment; timing-only candidate is separate',
          'C16 API/record/score algorithms retained as source; new Game/record/Root pixels must bind actual new identities',
          'source epoch model is business-source proof only; no runtime custody or elapsed savings claimed'])
    mode='x'
    if output.exists():
        prior=output.read_bytes()
        if producer.sha(prior)!='52520412824b1eb85fd41cda22ea71d20e76e7929a4b0c0bededa637dfbedb63':
            raise FileExistsError('only the exact unpublished WIP proof may be finalized once')
        proof['unpublished_WIP_finalized_once']={'bytes':len(prior),'sha256':producer.sha(prior),
            'old_bytes_retained':False,'first_pending_qualification_retained':'_runtime/c19-canonical-controls-qualification01.json'}
        mode='w'
    with output.open(mode,encoding='utf8',newline='\n') as f:json.dump(proof,f,indent=2);f.write('\n')
    print(json.dumps({'status':proof['status'],'tests':result.testsRun,'source_bytes':sum(p.stat().st_size for p in paths),
                      'in_memory_output_bytes':sum(map(len,GRAPH.values()))}))


if __name__=='__main__':main(Path(sys.argv[1]))
