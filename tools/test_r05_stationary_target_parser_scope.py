"""One focused case for actual stationary siege/null gathering and parse-only ABI."""
from pathlib import Path
import argparse,copy,importlib.util,json,sys,tempfile,unittest

def load(name,p):
    s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m

class TargetParserContract(unittest.TestCase):
    def test_stationary_siege_and_exact_parse_only(self):
        f,q=I.inputs();row=f['player_armies'][0];a=q['army_strengths'][0]
        row.update(army_state='sieging',army_state_code=3)
        a.update(gathering_days_left=None,gathering_days_status='not_gathering',monthly_loss_budget_inputs_v1={
            'ready':True,'unit_native_170_raw':0,'native_unit_in_combat':False,'native_unit_gathering':False,'army_gathering_count_raw':0})
        def witness(f=f,q=q):return M.target_witness(f,q,actor_id=42,army_id=18,carmy_id=85,province_id=2644)
        w=witness();self.assertEqual(w['army_state_code'],3);self.assertEqual(w['gathering_days_status'],'not_gathering')
        for field,value in (('unit_native_170_raw',3),('native_unit_gathering',True),('native_unit_in_combat',True),('army_gathering_count_raw',1)):
            bad=copy.deepcopy(q);bad['army_strengths'][0]['monthly_loss_budget_inputs_v1'][field]=value
            with self.assertRaises(ValueError):witness(f,bad)
        moved=copy.deepcopy(f);moved['player_armies'][0].update(route_read_status='complete',route_source_count=1,route_province_ids=[2645])
        with self.assertRaises(ValueError):witness(moved,q)
        after=copy.deepcopy(w);after['current_supply_raw']=1
        self.assertEqual(M.assess_initialization(w,after)['status'],'prepared_low_stock')
        after['army_state']='regular';after['army_state_code']=1
        with self.assertRaises(ValueError):M.assess_initialization(w,after)
        with tempfile.TemporaryDirectory(dir=TEMP) as t:
            root=Path(t);parsed=root/'parse.json';prior=root/'prior.json'
            parsed.write_text(json.dumps({'status':'PARSED','bytes':836,'diagnostics':[],'roundTrip':True}))
            prior.write_text(json.dumps({'status':'INVALID','semanticCodes':['UNKNOWN_OPCODE']*15}))
            package={'files':[{'relative_path':'common/decisions/test.txt','bytes':836,'sha256':'a'*64}]}
            receipt=dict(machine_id=MACHINE,corpus_sha256={'common/decisions/test.txt':'a'*64},ck3_exe_sha256=M.EXE_SHA,
                open_kaishek_commit='1'*40,profile_version='parse-only; no .4 profile',actual_command=['real-cli','parse'],
                unsupported_semantics=['current .4 native semantics unsupported'],status='PARSER_SYNTAX_ONLY_EXACT_CORPUS',
                actual_parse_report=M.pin(parsed),actual_exit_code=0,parsed_relative_path='common/decisions/test.txt',
                source_decision_sha256='a'*64,prior_unsupported_validation=M.pin(prior),
                semantic_validation_current_corpus='NOT_RUN_UNSUPPORTED_PROFILE_12004')
            scope=A.script_preflight_scope(receipt,package,M,MACHINE);self.assertIn('UNSUPPORTED',scope)
            bad=copy.deepcopy(receipt);bad['source_decision_sha256']='b'*64
            with self.assertRaises(ValueError):A.script_preflight_scope(bad,package,M,MACHINE)
            if RECEIPT:RECEIPT.write_text(json.dumps({'machine_id':MACHINE,'status':'PASS','test':'stationary_siege_and_exact_parse_only','SDK_calls':0,'R05_pass':False})+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--repo-root',type=Path,required=True);p.add_argument('--candidate-root',type=Path)
    p.add_argument('--temp-root',type=Path,required=True);p.add_argument('--receipt',type=Path);a=p.parse_args()
    R=a.repo_root.resolve();C=(a.candidate_root or R).resolve();TEMP=a.temp_root;TEMP.mkdir(parents=True,exist_ok=True);RECEIPT=a.receipt
    sys.path[:0]=[str(R/'ck3_autonomous_player/src'),str(R/'tools')]
    from ck3_live_run_id import current_machine_id
    MACHINE=current_machine_id()
    M=load('xar_autoplayer.bridge.r05_low_supply_fixture',C/'ck3_autonomous_player/src/xar_autoplayer/bridge/r05_low_supply_fixture.py')
    I=load('r05_existing_fixture_factory',R/'tools/test_r05_low_supply_fixture.py');I.M=M
    A=load('r05_actual_target_adapter',C/'tools/ck3_mod_acceptance_cases/r05_low_supply_adapter.py')
    unittest.main(argv=[__file__],verbosity=2)
