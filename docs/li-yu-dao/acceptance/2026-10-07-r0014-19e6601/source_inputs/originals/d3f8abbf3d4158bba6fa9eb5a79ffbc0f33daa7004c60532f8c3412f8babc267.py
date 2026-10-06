from pathlib import Path
from copy import deepcopy
import sys,json,hashlib,importlib.util,unittest
sys.dont_write_bytecode=True
ROOT=Path(__file__).parents[1]
sys.path.insert(0,str(ROOT/'reader/dependencies'))
spec=importlib.util.spec_from_file_location('actual_shape_strict_reader',ROOT/'reader/i3b_checkpoint_reader.py')
reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
fixture=json.loads((ROOT/'tests/fixtures/ACTUAL-B1-present-numeric-zero.json').read_bytes())
NAME='lyd_i3b_was_elector'

class PresentNumericZeroTests(unittest.TestCase):
    def zero(self):return deepcopy(fixture['zero_row'])
    def test_actual_present_zero_matches_native_ineligible_and_preserves_raw(self):
        row=self.zero();before=json.dumps(row,sort_keys=True)
        member=fixture['native_member']
        eligible=member['alive'] and member['adult'] and not member['imprisoned'] and not member['incapable'] and member['effective_learning']>=15
        self.assertFalse(eligible);self.assertEqual(reader.number({NAME:row},NAME),int(eligible))
        self.assertEqual(json.dumps(row,sort_keys=True),before);self.assertIsNone(row['identity']);self.assertNotIn('number',row)
    def test_actual_positive_elector_preserved(self):
        self.assertEqual(reader.number({NAME:deepcopy(fixture['positive_actor_elector_row'])},NAME),1)
    def test_missing_variable_required_rejected_optional_remains_null(self):
        with self.assertRaises(reader.ReadbackError):reader.number({},NAME)
        self.assertIsNone(reader.number({},NAME,required=False))
    def test_wrong_type_or_not_present_rejected(self):
        for field,value in (('type','faith'),('type','boolean'),('present',False),('identity','0')):
            row=self.zero();row[field]=value
            with self.assertRaises(reader.ReadbackError):reader.number({NAME:row},NAME)
    def test_missing_or_empty_data_block_rejected(self):
        for entries in (None,[],[{'key':'identity','value':None}]):
            row=self.zero();row['entries']=entries
            with self.assertRaises(reader.ReadbackError):reader.number({NAME:row},NAME)
    def test_extra_data_identity_or_timestamp_is_not_default_zero(self):
        for extra in ({'key':'identity','value':None},{'key':'tick','value':'53144712'},{'key':'future_unknown','value':'0'}):
            row=self.zero();row['entries'].append(extra)
            with self.assertRaises(reader.ReadbackError):reader.number({NAME:row},NAME)
    def test_owner_expiry_timestamp_is_preserved_and_not_numeric_identity(self):
        row=self.zero();row['tick']='53145177';row['row_entries'].append({'key':'tick','value':'53145177'})
        before=json.dumps(row,sort_keys=True)
        self.assertEqual(reader.number({NAME:row},NAME),0)
        self.assertEqual(row['tick'],'53145177');self.assertEqual(json.dumps(row,sort_keys=True),before)
    def test_nonintegral_explicit_numeric_identity_is_rejected(self):
        row=self.zero();row.update(identity='53144712',number='531.44712',scale=100000);row['entries'].append({'key':'identity','value':'53144712'})
        with self.assertRaises(reader.ReadbackError):reader.number({NAME:row},NAME)
    def test_explicit_negative_vote_remains_negative_one(self):
        row=self.zero();row.update(identity='-100000',number='-1',scale=100000);row['entries'].append({'key':'identity','value':'-100000'})
        self.assertEqual(reader.number({'lyd_i3b_vote':row},'lyd_i3b_vote'),-1)

if __name__=='__main__':unittest.main(verbosity=2)
