"""One new behavior: exact .4 fast-domain qualification vs unknown fallback."""
from pathlib import Path
import copy,importlib.util,unittest
spec=importlib.util.spec_from_file_location('r09_exact_domain',Path(__file__).with_name('root_relay.py'))
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
def row(a,stock,weight,current):
 return {'army_id':a,'current_soldiers':current,'current_supply_raw':stock,'current_supply_scale':100000,
  'current_supply_capacity_raw':stock,'current_supply_capacity_scale':100000,
  'merge_supply_destination_weight_raw':weight,'merge_supply_destination_weight_scale':100000}
def packet(rows):return {'query':{'army_strengths':rows}}
class NativeDomain(unittest.TestCase):
 def test_fast_boundaries_pass_and_each_actual_fallback_operand_is_held(self):
  numerator=0x53E2D6238DA3;operand=0xB504F333
  before=packet([row(93,operand,numerator,1000000000),row(18,1,0,0)])
  after=packet([row(93,operand,0,1000000000)])
  value=r.compare_merge_supply(before,after,[93,18])
  self.assertTrue(value['weighted_supply_match']);self.assertFalse(value['upper_clamp_observed'])
  for mutation in ('Dweight','Sweight','stock'):
   changed=copy.deepcopy(before);d,s=changed['query']['army_strengths']
   if mutation=='Dweight':d['merge_supply_destination_weight_raw']=numerator+1
   if mutation=='Sweight':s['current_soldiers']=numerator//100000+1
   if mutation=='stock':d['current_supply_raw']=operand+1
   with self.subTest(mutation=mutation):
    result=r.compare_merge_supply(changed,after,[93,18])
    self.assertEqual(result['status'],'HOLD_NATIVE_FIXED_FALLBACK_BRANCH')
    self.assertFalse(result['upper_clamp_observed']);self.assertFalse(result['native_fallback_modelled'])
  # A zero-weight term is skipped by actual2C55F13/16, even if its stock is large.
  before['query']['army_strengths'][1]['current_supply_raw']=operand+1
  self.assertTrue(r.compare_merge_supply(before,after,[93,18])['weighted_supply_match'])
if __name__=='__main__':unittest.main()
