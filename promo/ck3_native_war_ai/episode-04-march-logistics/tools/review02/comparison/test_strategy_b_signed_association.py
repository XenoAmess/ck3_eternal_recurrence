"""One new semantic counterexample for the existing signed DATA association."""
from copy import deepcopy
from pathlib import Path
import argparse,importlib.util,sys,types,unittest
p=argparse.ArgumentParser();p.add_argument('--candidate-builder',type=Path)
args,rest=p.parse_known_args()
if args.candidate_builder:
    spec=importlib.util.spec_from_file_location('signed_builder',args.candidate_builder)
    builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
    h=types.ModuleType('signed_candidate');exec(compile(builder.build_source(),'signed-helper-candidate','exec'),h.__dict__)
else:
    sys.path.insert(0,str(Path(__file__).parent))
    import strategy_b_common_horizon as h
class Tests(unittest.TestCase):
    def test_signed_association_identity_and_separate_index_bounds(self):
        view={'rows':{1:{'native_carmy_id':18,'regiment_strengths':[{'army_regiment_id':-(2**31),'maximum_soldiers':2}],
            'regiment_replenishment_records_v1':[{'army_regiment_id':-(2**31),'native_data_record_count':1,
                'records':[{'record_index':0,'persistent_regiment_id':-(2**31),'chunk_index':0,
                    'maximum_soldiers':2,'chunk_army_regiment_id':-(2**31),'current_soldiers':1}]}]}},
            'endpoint':{'commander_id':1,'player_character_id':2,'cohort_maximum':2,'loaded_features':[],'war_state':[]}}
        first=h.signature(view)
        row=view['rows'][1]['regiment_replenishment_records_v1'][0]['records'][0]
        row['current_soldiers']=2;self.assertEqual(first,h.signature(view))
        row['chunk_army_regiment_id']=-7;self.assertNotEqual(first,h.signature(view))
        for bad in (-(2**31)-1,2**31,True,None):
            row['chunk_army_regiment_id']=bad
            with self.assertRaises(ValueError):h.signature(view)
        row['chunk_army_regiment_id']=-(2**31)
        for key in ('record_index','chunk_index','maximum_soldiers'):
            saved=row[key];row[key]=-1
            with self.assertRaises(ValueError):h.signature(view)
            row[key]=saved
if __name__=='__main__':unittest.main(argv=[sys.argv[0],*rest],verbosity=2)
