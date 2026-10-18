"""One new actual-cut/production-contract compound. No SDK or old matrix."""
from pathlib import Path
from copy import deepcopy
import argparse,hashlib,importlib.util,json,sys,unittest
ROOT=Path(__file__).resolve().parents[3] if 'ck3_autonomous_player' in str(Path(__file__).resolve()) else Path('D:/workspace/ck3_eternal_recurrence')
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT/'ck3_autonomous_player/src'),str(ROOT)]
ARGS=argparse.Namespace(candidate=None, evidence_root=ROOT/'docs/ck3-native-ai/evidence/episode04-r213-regular-core-null-export-12004')
class CaptureWindow(unittest.TestCase):
    def test_actual_null_and_window_readback_are_distinct(self):
        if ARGS.candidate:
            name='xar_autoplayer.bridge.army_regular_core_capture_status_12004'
            spec=importlib.util.spec_from_file_location(name,ARGS.candidate)
            module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
        from xar_autoplayer.bridge.army_regular_core_capture_status_12004 import classify_regular_core_capture_window_12004 as classify,CORE
        from xar_autoplayer.bridge.army_observed_phase_contract_12004 import FAMILIES,normalize_army_observed_phase_family_12004
        from xar_autoplayer.bridge.army_strengths_profile_contract import validate_army_strengths_profile_coverage
        facts=json.loads((ARGS.evidence_root/'ACTUAL-TINY-FACTS.json').read_bytes())
        for item in facts['queries']:
            ref=item['response_prefix_file'];raw=(ARGS.evidence_root/ref['relative_path']).read_bytes()
            self.assertEqual((len(raw),hashlib.sha256(raw).hexdigest()),(ref['bytes'],ref['sha256']))
            self.assertEqual(raw.count(item['literal'].encode()),1)
            # Synthetic minimal profile wrapper; each null value is separately
            # witnessed in the actual immutable native prefix, not guessed.
            for key in FAMILIES:self.assertIn(('"'+key+'": null').encode(),raw)
        row=dict(army_id=0,native_carmy_id=0,status='available',**{key:None for key in FAMILIES})
        validate_army_strengths_profile_coverage(dict(army_strengths_profile='observed_history_full_v1',army_observed_phase_coverage='exported_retained',army_strengths=[row]),expected_profile='observed_history_full_v1')
        self.assertIsNone(normalize_army_observed_phase_family_12004(CORE,row[CORE],expected_carmy_id=0))
        before=facts['before_sampling']
        actual=classify(row,profile='observed_history_full_v1',before_sampling=before,after_sampling=None)
        self.assertEqual(actual['field_state'],'explicit_null')
        self.assertEqual(actual['status'],'sampling_window_readback_missing')
        self.assertFalse(actual['callback_execution_claim']);self.assertFalse(actual['physical_ADD_claim'])
        after=deepcopy(before)
        self.assertEqual(classify(row,profile='observed_history_full_v1',before_sampling=before,after_sampling=after)['status'],'no_retained_core_in_enabled_window')
        after['army_observer_research_sampling_v1']['regular_core']['retained_records']=1
        self.assertEqual(classify(row,profile='observed_history_full_v1',before_sampling=before,after_sampling=after)['status'],'retained_core_without_qualified_entry_return')
        state=after['army_observer_research_sampling_v1']['regular_core'];state.update(qualified_records=1,readiness='retained_observation')
        self.assertEqual(classify(row,profile='observed_history_full_v1',before_sampling=before,after_sampling=after)['status'],'no_exported_event_for_requested_carmy')
        cleared=deepcopy(before);cleared['army_observer_research_sampling_v1']['regular_core'].update(capture_enabled=False,clear_completed=True,status='disabled',readiness='off')
        self.assertEqual(classify(row,profile='observed_history_full_v1',before_sampling=before,after_sampling=cleared)['status'],'not_a_completed_enabled_window')
        missing=deepcopy(row);missing.pop(CORE)
        with self.assertRaisesRegex(ValueError,'omitted'):classify(missing,profile='observed_history_full_v1',before_sampling=before,after_sampling=after)
        ordinary={key:value for key,value in row.items() if key not in FAMILIES}
        self.assertEqual(classify(ordinary,profile='ordinary_core_v1',before_sampling=None)['status'],'not_requested')
        print(json.dumps(dict(status='PASS_ONE_ACTUAL_CUT_PRODUCTION_CONTRACT_COMPOUND',actual_R213_after_status_reconstructed=False,
            production_profile_and_family_and_sampling_consumers=True,synthetic_window_counterexamples=True,SDK_calls=0,native_calls=0)))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path);p.add_argument('--evidence-root',type=Path,required=True);ARGS=p.parse_args()
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(CaptureWindow))
    raise SystemExit(0 if result.wasSuccessful() else 1)
