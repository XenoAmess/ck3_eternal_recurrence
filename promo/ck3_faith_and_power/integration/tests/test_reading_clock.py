"""Reading holds pass through the real formal consumer without changing speech."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from faith_power_promo.reading_clock import selected_reading_clock, checked_reading_hold_total
from faith_power_promo import full_episode as common
import test_mechanism_full_contract as mechanism_tests
from test_value_v3_formal import native_project


class ReadingClockTests(unittest.TestCase):
    def test_actual_consumer_retains_voice_and_extends_selected_clock(self) -> None:
        helper = mechanism_tests.MechanismFullContractTests()
        with tempfile.TemporaryDirectory() as name:
            document, voices, evidence, _ = helper.fixture(Path(name))
            original = deepcopy(voices)
            row = document['cues'][0]
            base = row['duration_seconds']
            row.update(reading_hold_seconds=10, duration_seconds=base+10)
            result = helper.consume(document, voices, evidence)
            self.assertEqual(result['reading_hold_seconds'], 10)
            self.assertAlmostEqual(result['seconds'], 2*base+10)
            self.assertEqual(original, voices)
            self.assertEqual(common.subtitle_groups(row)[-1]['end_seconds'], row['speech_duration_seconds'])
            self.assertFalse(result['ready_to_build'])

    def test_actual_consumer_rejects_clock_drift_and_bad_hold_types(self) -> None:
        helper = mechanism_tests.MechanismFullContractTests()
        for hold, extra in [(True, 1), (None, 0), (float('inf'), 0), (float('nan'), 0),
                            (-1, -1), (21, 21), (.01, .01), (5, 4)]:
            with self.subTest(hold=hold), tempfile.TemporaryDirectory() as name:
                document, voices, evidence, _ = helper.fixture(Path(name))
                row=document['cues'][0]
                row.update(reading_hold_seconds=hold,duration_seconds=row['duration_seconds']+extra)
                with self.assertRaises(ValueError):
                    helper.consume(document, voices, evidence)

    def test_source_voice_clock_cannot_be_changed_with_the_hold(self) -> None:
        helper=mechanism_tests.MechanismFullContractTests()
        with tempfile.TemporaryDirectory() as name:
            document, voices, evidence, _=helper.fixture(Path(name))
            row=document['cues'][0]
            row.update(reading_hold_seconds=5,duration_seconds=row['duration_seconds']+5,
                       speech_duration_seconds=row['speech_duration_seconds']+5)
            with self.assertRaisesRegex(ValueError,'speech_duration_seconds'):
                helper.consume(document,voices,evidence)

    def test_actual_consumer_enforces_full_episode_total(self) -> None:
        helper=mechanism_tests.MechanismFullContractTests()
        with tempfile.TemporaryDirectory() as name:
            document, voices, evidence, _=helper.fixture(Path(name))
            template=deepcopy(document['cues'][0])
            claim=deepcopy(evidence['claims'][0])
            rows=[];voice_rows=[];annotations=[];claims=[]
            for index in range(7):
                source={**deepcopy(template),'id':f'cue-{index}','claim_ids':[f'claim-{index}']}
                voice_rows.append(deepcopy(source))
                rows.append({**source,'reading_hold_seconds':20,'duration_seconds':source['duration_seconds']+20})
                annotations.append({'id':source['id'],'claim_ids':source['claim_ids'],'shot_ids':[],'source_refs':[]})
                claims.append({**deepcopy(claim),'id':f'claim-{index}'})
            document.update(cues=rows,sequence=[row['id'] for row in rows])
            voices.update(cues=voice_rows,cue_count=7)
            evidence.update(cues=annotations,claims=claims)
            project=Path(document['project_config']['path'])
            project.write_text(json.dumps(native_project(rows)),encoding='utf-8')
            document['project_config']=common.pin(project)
            with self.assertRaisesRegex(ValueError,'exceed 120'):
                helper.consume(document,voices,evidence)

    def test_legacy_clock_and_json_roundtrip(self) -> None:
        source={'duration_seconds':2.1333333333333333}
        clock=selected_reading_clock(source,source,enabled=False)
        self.assertEqual(clock.render_duration_seconds,source['duration_seconds'])
        self.assertEqual(checked_reading_hold_total([clock]),0)
        selected={'duration_seconds':source['duration_seconds']+1,'reading_hold_seconds':1}
        expected=selected_reading_clock(selected,source,enabled=True)
        self.assertEqual(expected,selected_reading_clock(json.loads(json.dumps(selected)),json.loads(json.dumps(source)),enabled=True))
        with self.assertRaisesRegex(ValueError,'source-mechanism-full'):
            selected_reading_clock(selected,source,enabled=False)
        with self.assertRaisesRegex(ValueError,'source field changed'):
            selected_reading_clock({'duration_seconds':3},source,enabled=False)


if __name__=='__main__':
    unittest.main()
