"""Persistent regression for the actual default CAS completion path."""
from copy import deepcopy
import unittest
from ck3_mod_acceptance_background_types import JsonObject, JsonValue
from ck3_mod_acceptance_unrun import _release_stages

def member(row: JsonObject, key: str) -> JsonObject:
    value=row.get(key)
    if not isinstance(value,dict):raise AssertionError('Fixture object required')
    return value

class ReleaseStagesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.keeper: JsonObject={'task_id':'idle','thread_exited':True,'last_sequence':10}
        self.cas: JsonObject={'ok':True,'event':{'task_id':'idle','resources':[],
            'sequence':11,'kind':'completed'},'task':{'task_id':'idle','state':'done',
            'resources':[],'last_sequence':11}}
        self.done=deepcopy(self.cas)
        member(self.done,'event')['sequence']=12
        member(self.done,'task')['last_sequence']=12

    def test_idle_actual_completed_then_administrative_completion(self) -> None:
        self.assertEqual(_release_stages(self.keeper,self.cas,self.done,{}, {},self.done,'idle'),
            'completed-then-admin-completed')

    def test_json_round_trip_preserves_release_contract(self) -> None:
        import json
        from ck3_mod_acceptance_background_types import json_object
        cas=json_object(json.loads(json.dumps(self.cas)))
        done=json_object(json.loads(json.dumps(self.done)))
        self.assertEqual(_release_stages(self.keeper,cas,done,{}, {},done,'idle'),
            'completed-then-admin-completed')

    def test_crossed_original_task_and_resources_are_rejected(self) -> None:
        cases: list[tuple[str,JsonValue]]=[('task_id','other'),('state','waiting'),
            ('resources',['ck3-screen:acquired']),('last_sequence',12)]
        for key,bad in cases:
            cas=deepcopy(self.cas);member(cas,'task')[key]=bad
            with self.assertRaises(ValueError):
                _release_stages(self.keeper,cas,self.done,{}, {},self.done,'idle')

    def test_sequence_types_missing_fields_and_order_are_rejected(self) -> None:
        bad_values: list[JsonValue]=[True,11.0,None,[],{},10,13]
        for bad in bad_values:
            cas=deepcopy(self.cas);member(cas,'event')['sequence']=bad
            with self.assertRaises(ValueError):
                _release_stages(self.keeper,cas,self.done,{}, {},self.done,'idle')
        cas=deepcopy(self.cas);del member(cas,'event')['sequence']
        with self.assertRaises(ValueError):
            _release_stages(self.keeper,cas,self.done,{}, {},self.done,'idle')

if __name__=='__main__':unittest.main()
