"""One new signed FullID semantic example; synthetic, no transport or old tests."""
from copy import deepcopy
from types import SimpleNamespace
import unittest
import strategy_a_stages as stages

def need(ok,message):
    if not ok:raise RuntimeError(message)

class SignedFullID(unittest.TestCase):
    def test_signed_fullid_stays_stable_while_current_changes_and_malformed_identity_refuses(self):
        h=SimpleNamespace(Live=object,need=need)
        c=SimpleNamespace(body=lambda q:q)
        Live=stages.make_live_class(h,c,None,None);v=Live.__new__(Live)
        actual={'player_character_id':7,'commander_id':10,'units':[{'army_id':1,'maximum_soldiers':50}]}
        record={'record_index':0,'persistent_regiment_id':-(1<<31),'chunk_index':0,
                'maximum_soldiers':50,'current_soldiers':50,'chunk_army_regiment_id':12}
        row={'army_regiment_id':12,'native_data_record_count':1,'records':[record]}
        query={'army_strengths':[{'army_id':1,'regiment_strengths':[{'army_regiment_id':12,'maximum_soldiers':50,
                  'current_soldiers':50}],'regiment_replenishment_records_v1':[row]}]}
        v.e=SimpleNamespace(json=lambda _:query);ep={'army_result':{'synthetic':True}}
        for full_id in (-(1<<31),-7,-1,0,(1<<31)-1):
            with self.subTest(valid_full_id=full_id):
                record['persistent_regiment_id']=full_id;record['current_soldiers']=50
                first=v.hold_signature(actual,ep)
                record['current_soldiers']=49;query['army_strengths'][0]['regiment_strengths'][0]['current_soldiers']=49
                self.assertEqual(v.hold_signature(actual,ep),first)
        for malformed in (-(1<<31)-1,1<<31,True,None):
            with self.subTest(invalid_full_id=malformed):
                record['persistent_regiment_id']=malformed
                with self.assertRaisesRegex(RuntimeError,'signed32 persistent FullID'):v.hold_signature(actual,ep)
        record['persistent_regiment_id']=-(1<<31)
        for key in ('record_index','chunk_index','maximum_soldiers'):
            previous=record[key]
            for malformed in (-1,1<<31,True,None):
                with self.subTest(field=key,invalid=malformed):
                    record[key]=malformed
                    with self.assertRaisesRegex(RuntimeError,'index/slot/max'):v.hold_signature(actual,ep)
            record[key]=previous
        before=v.hold_signature(actual,ep);record['persistent_regiment_id']+=1
        self.assertNotEqual(v.hold_signature(actual,ep),before)

if __name__=='__main__':unittest.main()
