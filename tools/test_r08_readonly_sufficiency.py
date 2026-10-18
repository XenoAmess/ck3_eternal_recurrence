"""One compound: real retained .4 counterexample and no shortcut on equality."""
from pathlib import Path
from copy import deepcopy
from datetime import datetime,timezone
import argparse,importlib.util,json,sys,unittest
p=argparse.ArgumentParser(add_help=False)
p.add_argument('--repo-root',type=Path,default=Path(__file__).resolve().parents[1])
p.add_argument('--dependencies-root',type=Path)
p.add_argument('--receipt',type=Path)
o,rest=p.parse_known_args()
sys.path.insert(0,str((o.dependencies_root or o.repo_root)/'tools'))
from ck3_live_run_id import current_machine_id
path=o.repo_root/'ck3_autonomous_player/src/xar_autoplayer/bridge/war_payment_readonly_sufficiency_v1.py'
spec=importlib.util.spec_from_file_location('r08_readonly_pure',path)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class Compound(unittest.TestCase):
    def test_actual_readonly_counterexample_and_equal_values_do_not_grant_paid(self):
        evidence=o.repo_root/'docs/ck3-native-ai/evidence/episode04-r08-readonly-sufficiency-12004/actual-projection.json'
        v=json.loads(evidence.read_bytes());current=deepcopy(v['R213']['rates'])
        current['current_raw_context_v1']=deepcopy(v['R213']['current_raw_context_v1'])
        original=deepcopy(current);a=m.assess_readonly_maintenance_sufficiency_v1(current)
        self.assertTrue(a['raw_context_qualified']);self.assertEqual(a['raw_formula_net'],9818)
        self.assertEqual(a['getters']['net'],32540);self.assertEqual(a['raw_c_plus_d'],310999)
        self.assertEqual(a['getters']['current_military_gold'],386622)
        self.assertFalse(any(a['literal_value_equal'].values()));self.assertEqual(current,original)
        equal=deepcopy(current);raw=equal['current_raw_context_v1']['values']
        raw.update(value_28=386622,value_30=0,value_2c0=419162,value_2c8=0)
        b=m.assess_readonly_maintenance_sufficiency_v1(equal)
        self.assertTrue(b['literal_value_equal']['c_to_current_military'])
        self.assertTrue(b['literal_value_equal']['raw_formula_to_monthly_net'])
        for row in (a,b):
            self.assertFalse(row['may_substitute_c_or_c_plus_d_for_current_military'])
            self.assertFalse(row['may_substitute_four_raw_formula_for_monthly_net'])
            self.assertFalse(row['may_infer_paid_from_rate_or_net_or_owner'])
            self.assertIsNone(row['military_paid_raw']);self.assertIsNone(row['military_payer']);self.assertIsNone(row['cadence'])
        missing=deepcopy(current);missing.pop('current_raw_context_v1')
        c=m.assess_readonly_maintenance_sufficiency_v1(missing)
        self.assertFalse(c['raw_context_qualified']);self.assertIsNone(c['raw_formula_net'])
        self.assertTrue(all(v is None for v in c['literal_value_equal'].values()))
        facts={'machine_id':current_machine_id(),'observed_at_utc':datetime.now(timezone.utc).isoformat(),'source_record_machine_id':v['machine_id'],
            'actual_R213_projection_replayed':True,'source_only_tests':1,'actual_counterexample':'PASS',
            'equal_numbers_still_do_not_grant_paid':'PASS','missing_is_not_zero':'PASS','SDK_calls':0,'new_game_credit':False}
        if o.receipt:
            with o.receipt.open('x',encoding='utf-8',newline='\n') as f:json.dump(facts,f,indent=2);f.write('\n')
        print(json.dumps(facts))
if __name__=='__main__':unittest.main(argv=[sys.argv[0],*rest])
