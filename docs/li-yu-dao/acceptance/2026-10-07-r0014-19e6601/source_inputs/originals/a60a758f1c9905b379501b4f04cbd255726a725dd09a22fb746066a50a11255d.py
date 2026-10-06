from pathlib import Path
from copy import deepcopy
import json,unittest
from test_present_numeric_zero import reader,ROOT
fixture=json.loads((ROOT/'tests/fixtures/ACTUAL-B1-uint64-signed-vote.json').read_bytes())
NAME='lyd_i3b_vote'

class ActualSignedValueTests(unittest.TestCase):
    def vote(self):return deepcopy(fixture['actual_vote_row'])
    def test_actual_unsigned_bit_pattern_decodes_source_pending_minus_one_without_rewrite(self):
        row=self.vote();before=json.dumps(row,sort_keys=True)
        self.assertEqual(int(row['identity']),2**64-100000)
        self.assertEqual(reader.number({NAME:row},NAME),fixture['source_declared_vote'])
        self.assertEqual(json.dumps(row,sort_keys=True),before)
    def test_optional_present_numeric_routes_same_signed_decode_and_missing_remains_null(self):
        self.assertEqual(reader.number({NAME:self.vote()},NAME,required=False),-1)
        self.assertIsNone(reader.number({},NAME,required=False))
    def test_actual_positive_serial_keeps_one(self):
        self.assertEqual(reader.number({'lyd_i3b_serial':deepcopy(fixture['actual_serial_row'])},'lyd_i3b_serial'),1)
    def test_uint64_overflow_wrong_scale_nonvalue_and_highbit_fraction_rejected(self):
        for field,value in (('identity',str(2**64)),('identity',str(2**63)),('identity',str(2**64-1)),('scale',1000),('type','char'),('identity','1e5'),('identity',str(-(2**63)-1))):
            row=self.vote();row[field]=value
            with self.assertRaises(reader.ReadbackError):reader.number({NAME:row},NAME)
    def test_entity_full_id_uses_reference_binding_without_numeric_signed_decode(self):
        variables={'lyd_i3b_result_head_title':{'type':'synthetic_saved_title_discriminator','identity':str(0xF1000001)}}
        # The primitive scalar ID path stays an unsigned reference, independently
        # of signed fixed-point values. No entity is passed through number().
        self.assertEqual(reader.scalar_id(variables['lyd_i3b_result_head_title']['identity'],'actual Title'),0xF1000001)

if __name__=='__main__':unittest.main(verbosity=2)
