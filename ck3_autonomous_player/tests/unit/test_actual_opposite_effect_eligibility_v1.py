from __future__ import annotations

import copy
from dataclasses import FrozenInstanceError
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
sys.path.insert(0,str(Path(__file__).resolve().parent))
from test_retained_constructor_geometry_v1 import load_fixture,service_query
from test_actual_stored_advantage_sources_v1 import stored_sources
from xar_autoplayer.bridge.battle_stored_effect_flags_contract import normalize_stored_effect_flags_v1
from xar_autoplayer.bridge.battle_stored_advantage_sources_contract import normalize_stored_advantage_sources_v1
from xar_autoplayer.simulation.battle_actual_opposite_effect_eligibility import (
    adapt_actual_opposite_effect_eligibility,evaluate_actual_opposite_effect_eligibility,
)


def flagged_sources():
    stored=stored_sources()
    for side,flags in zip(stored['sides'],(((0,0),(0,255),(2,0)),((2,0),(0,3)))):
        for row,(raw88,raw89) in zip(side['rows'],flags):
            row['effect_flags_v1']={'status':'available','flag88_raw':raw88,'flag89_raw':raw89,'unavailable_reason':None}
    return stored


class ActualOppositeEffectEligibilityTests(unittest.TestCase):
    def test_ordered_current_raw_membership_uses_retained_amounts_and_independent_status(self):
        for scenario in ('observed-eligibility','empty-opposite','missing-flags','owned'):
            with self.subTest(scenario=scenario):
                frame=load_fixture('owned-available.json' if scenario=='owned' else 'foreign-available.json')
                stored=flagged_sources()
                if scenario=='empty-opposite':
                    stored['sides'][0]['rows']=[]
                elif scenario=='missing-flags':
                    stored['sides'][1]['rows'][1]['effect_flags_v1'].update(
                        status='unavailable',flag88_raw=None,flag89_raw=None,
                        unavailable_reason='stored_effect_flags_88_89_effect_pointer_unavailable')
                frame['actual_geography_v1']['stored_advantage_sources_v1']=stored
                result=service_query(frame)
                diagnostic=result['opposite_effect_eligibility_v1']
                inputs=adapt_actual_opposite_effect_eligibility(diagnostic)
                output=evaluate_actual_opposite_effect_eligibility(inputs)
                self.assertEqual(output,diagnostic['current_eligibility'])
                own0,own1=output['sides']
                self.assertEqual(own0['opposite_side_index'],1)
                self.assertEqual(own1['opposite_side_index'],0)
                self.assertEqual(own0['eligible_contribution_sum_raw'],None if scenario=='missing-flags' else -862654)
                self.assertEqual(own1['eligible_contribution_sum_raw'],0 if scenario=='empty-opposite' else -333333)
                self.assertEqual(own0['ready'],scenario!='missing-flags')
                self.assertTrue(own1['ready'])
                self.assertIsNone(own0['ordered_opposite_rows'][1]['effect_key'])
                self.assertEqual(own0['ordered_opposite_rows'][1]['retained_contribution_raw'],-987654)
                self.assertIs(own0['ordered_opposite_rows'][1]['eligible'],None if scenario=='missing-flags' else True)
                self.assertEqual(own1['eligible_native_ledger_indices'],[] if scenario=='empty-opposite' else [1,2])
                self.assertTrue(result['battle_control_ready' if scenario=='owned' else 'battle_transition_ready'])
                self.assertFalse(output['nested_19F_contribution_ready'])
                self.assertFalse(output['current_effect_points_used_as_amount'])
                self.assertFalse(output['constructor_clamp_reconstructed'])
                with self.assertRaises(FrozenInstanceError):
                    inputs.sides[1].rows[1].flag89_raw=0
                diagnostic['stored_inputs']['sides'][1]['rows'][1]['contribution_raw']=9
                self.assertEqual(inputs.sides[1].rows[1].contribution_raw,-987654)
        stored=flagged_sources()
        # Unknown membership on a retained zero stays unknown, while its sum is
        # exactly determined. No unread raw flag is replaced with zero.
        stored['sides'][0]['rows'][1].pop('effect_flags_v1')
        diagnostic={'current_frame_qualified':True,'source':{'combat_id':1,'province_id':2,
                     'snapshot_revision':2,'observed_date_raw':3},
                    'stored_inputs':normalize_stored_advantage_sources_v1(stored,field='stored')}
        output=evaluate_actual_opposite_effect_eligibility(adapt_actual_opposite_effect_eligibility(diagnostic))
        own1=output['sides'][1]
        self.assertTrue(own1['ready'])
        self.assertFalse(own1['membership_ready'])
        self.assertIsNone(own1['ordered_opposite_rows'][1]['eligible'])
        self.assertIsNone(own1['ordered_opposite_rows'][1]['flag89_raw'])
        self.assertEqual(own1['eligible_contribution_sum_raw'],-333333)
        malformed=copy.deepcopy(flagged_sources()['sides'][0]['rows'][0]['effect_flags_v1'])
        malformed['flag88_raw']=False
        with self.assertRaises(ValueError):
            normalize_stored_effect_flags_v1(malformed,field='flags')


if __name__=='__main__':
    unittest.main()
