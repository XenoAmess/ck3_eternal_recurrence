"""One new source-shaped MAA baseline to final consumer qualification."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import importlib.util
import json
from pathlib import Path
import sys
import time
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))


class MaaSourceBaseline12003Test(unittest.TestCase):
    def test_actual_callback_filters_combined_extra_selector_and_accolade_stages(self):
        from xar_autoplayer.simulation.battle_first_contact_final_stat_refresh_12003 import EntrySixStatCache12003 as Cache,PersonStatStage12003
        from xar_autoplayer.simulation.battle_maa_source_stages_12003 import (
            MaaCultureContribution12003 as Row,MaaExtraSourceStage12003 as Extra,
            add_maa_culture_contributions_12003,construct_maa_baseline_stage_12003,
            apply_maa_accolade_aggregate_stage_12003)
        from xar_autoplayer.simulation.battle_maa_regiment_stats_12003 import (
            finish_maa_environment_stage_12003,maa_six_stats_to_final_stat_input_12003)

        def context(properties):
            keys=sorted(properties)
            return {'aggregate_properties':{'count':len(keys),'keys_u16':keys,
                'values_q64':[properties[key] for key in keys]}}

        culture=add_maa_culture_contributions_12003(Cache(100,100000,200000,300000,400000,500000),
            selected_type_class=5,stage='actual_type_plus_loaded_culture_rows',
            government_rows=(Row(False,None,-1,Cache(2,10,20,30,40,50)),
                Row(True,False,None,None),Row(True,True,7,None)),
            global_rows=(Row(True,True,5,Cache(3,90,180,270,360,450)),))
        self.assertTrue(culture.ready)
        self.assertEqual(tuple(asdict(culture.stat_cache).values()),(105,100100,200200,300300,400400,500500))
        person=PersonStatStage12003(71,'explicit_selected_Character_changed_stage',
            context({0x1BF:900,0x1B8:50000,0x1BA:50000}),None)
        extra=Extra('actual_extra120_named_context',context({0x1C1:-200,0x1C5:-400400,
            0x1CB:10000,0x1CC:-10000,0x900:-1000}),2,
            (0xFFFF,0xFFFF,0xFFFF,0xFFFF,0x900),(0xFFFF,)*5,
            {'source_title_full_id':101,'native_holder_full_id':72})
        args=dict(person_stage=person,class_row_present=True,class_add_keys_u16=(0xFFFF,)*6,
            class_mult_keys_u16=(0xFFFF,)*6,extra_source=extra,selector_mode=True,
            selected_government_byte_4d6=5,selected_script_value_4e_q64=50000)
        baseline=construct_maa_baseline_stage_12003(culture,stage='explicit_full_baseline',**args)
        self.assertTrue(baseline.ready)
        self.assertEqual(tuple(asdict(baseline.stat_cache).values()),(105,50500,170000,195195,0,249750))
        # Damage1.5+extra.2 combines to1.7 before selector.5, not1.5*1.2.
        self.assertEqual(baseline.ledger['selector_factor_q64'],50000)
        self.assertFalse(baseline.ledger['person_preparation_performed'])
        accolade=PersonStatStage12003(71,'actual_ordered_accolade_aggregate_context',context({0x1B7:30000}),None)
        after=apply_maa_accolade_aggregate_stage_12003(baseline,accolade_person_stage=accolade,
            class_row_present=True,class_add_keys_u16=(0xFFFF,)*6,class_mult_keys_u16=(0xFFFF,)*6,
            stage='explicit_after_baseline_and_accolade')
        self.assertTrue(after.ready)
        self.assertEqual(after.stat_cache.effective_damage_raw,200000)
        zero=Cache(0,0,0,0,0,0)
        end=finish_maa_environment_stage_12003(after,stage='explicit_full_MAA_getter_end',
            definition620_present=False,components={key:zero for key in ('type_terrain','type_province','linked_terrain','linked_province')},
            source_province_id=900,linked_character_full_ids=(71,71))
        final=maa_six_stats_to_final_stat_input_12003(end,side_index=0,bucket_index=1,
            native_carmy_id=1012,regiment_id=31,target_province_id=900)
        self.assertEqual(final.stat_cache,end.stat_cache)
        self.assertEqual((final.bucket,final.call_site),('men_at_arms','247AB32'))
        self.assertFalse(end.full_entry_ready)
        negative_args=dict(args,selected_script_value_4e_q64=-1)
        negative=construct_maa_baseline_stage_12003(culture,stage='negative_script_factor',**negative_args)
        self.assertTrue(negative.ready)
        self.assertEqual(tuple(asdict(negative.stat_cache).values()),(105,0,0,0,0,0))
        missing=construct_maa_baseline_stage_12003(culture,stage='missing_script_factor',
            **dict(args,selected_script_value_4e_q64=None))
        self.assertFalse(missing.ready)
        self.assertIsNone(missing.stat_cache)
        absent_class=construct_maa_baseline_stage_12003(culture,stage='actual_absent_class_skip_extra',
            **dict(args,class_row_present=False,class_add_keys_u16=None,class_mult_keys_u16=None,
                   extra_source=None,selector_mode=False,selected_government_byte_4d6=None,selected_script_value_4e_q64=None))
        self.assertTrue(absent_class.ready)
        self.assertEqual(absent_class.stat_cache.effective_damage_raw,300300)
        missing_rows=add_maa_culture_contributions_12003(zero,selected_type_class=5,
            government_rows=None,global_rows=(),stage='missing_actual_government_rows')
        self.assertFalse(missing_rows.ready)
        empty_rows=add_maa_culture_contributions_12003(zero,selected_type_class=5,
            government_rows=(),global_rows=(),stage='actual_empty_rows')
        self.assertTrue(empty_rows.ready)
        self.assertEqual(empty_rows.stat_cache,zero)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--consumer-source',type=Path)
    parser.add_argument('--artifacts',type=Path,required=True)
    args=parser.parse_args()
    if args.consumer_source:
        name='xar_autoplayer.simulation.battle_first_contact_final_stat_refresh_12003'
        spec=importlib.util.spec_from_file_location(name,args.consumer_source)
        module=importlib.util.module_from_spec(spec)
        sys.modules[name]=module
        spec.loader.exec_module(module)
    start=time.perf_counter()
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(MaaSourceBaseline12003Test))
    elapsed=time.perf_counter()-start
    args.artifacts.mkdir(exist_ok=False,parents=True)
    (args.artifacts/'RESULT.json').write_text(json.dumps({'status':'GREEN' if result.wasSuccessful() else 'RED',
        'tests_run':result.testsRun,'errors':len(result.errors),'failures':len(result.failures),'elapsed_seconds':elapsed,
        'old_cases_rerun':0,'game_operations':0,'native_builds':0,
        'qualification':'Actual callback matching, combined context/extra/piety source stages, selector five factors and accolade stage to existing final consumer; conditional operands, no native/live Entry claim'},indent=2)+'\n',encoding='utf-8')
    return 0 if result.wasSuccessful() else 1


if __name__=='__main__':
    raise SystemExit(main())
