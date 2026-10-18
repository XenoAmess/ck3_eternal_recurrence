"""One synthetic compound: actual new/legacy B baseline admission branches."""
from pathlib import Path
from copy import deepcopy
from types import SimpleNamespace as NS
from unittest.mock import Mock, patch
import argparse, json, sys, tempfile, unittest
p=argparse.ArgumentParser(add_help=False)
p.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[1])
p.add_argument('--comparison-overlay',type=Path)
a,rest=p.parse_known_args()
base=a.repo/'promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/comparison'
sys.path[:0]=[str(a.comparison_overlay or base),str(base)]
import strategy_b as b
import strategy_b_next as n
from strategy_b_stages import BStages
from test_strategy_b import BFixture
from test_strategy_b_stages import Root

class ReachedNativeBoundary(Exception):pass
class ColdBranch(unittest.TestCase):
    def test_new_cold_old_arm_and_wrong_save_runtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            f=BFixture(tmp);rt=f.rt;e=b.c.Evidence(f.f.root)
            cold={'schema':'xar.e04.r10.cold-arm-input.v1','label':'B','runtime':rt,
                  'loaded_save_sha256':f.arm['loaded_save_sha256'],'cold_start':f.arm['cold_start']}
            self.assertNotIn('disposition',cold)
            plan=Path(tmp)/'frozen-plan.json';plan.write_text(json.dumps(f.plan),encoding='utf-8')
            for mode in ('new','legacy','save','runtime'):
                arm=deepcopy(f.arm if mode=='legacy' else cold)
                if mode=='save':arm['loaded_save_sha256']='0'*64
                if mode=='runtime':arm['runtime']['pid']+=1
                case=Path(tmp)/mode;case.mkdir()
                bind={k:rt[v] for k,v in [('pid','pid'),('process_create_time_100ns','process_create_time_100ns'),
                    ('generation','connection_generation'),('actor','player_character_id'),('episode','episode')]}
                live=NS(case=case,meta={'machine_id':rt['machine_id'],'source_head':rt['source_head']},
                    binding=bind,a=NS(stage='baseline',attempt=mode,army_id=1),
                    baseline=Mock(side_effect=ReachedNativeBoundary))
                stage=BStages(Root,live,n,f.plan,plan_pin=Root.pin(plan),evidence=e,s0_arm=arm)
                with patch.object(b,'admit_cold',wraps=b.admit_cold) as admit,patch.object(b,'audit',wraps=b.audit) as audit:
                    with self.assertRaises(ReachedNativeBoundary if mode in ('new','legacy') else ValueError):
                        stage.baseline()
                    self.assertEqual(admit.call_count,0 if mode=='legacy' else 1)
                    self.assertEqual(audit.call_count,1 if mode=='legacy' else 0)
                self.assertEqual(live.baseline.call_count,1 if mode in ('new','legacy') else 0)

if __name__=='__main__':unittest.main(argv=[sys.argv[0],*rest])
