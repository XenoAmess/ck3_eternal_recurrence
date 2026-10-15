"""One source-bound endpoint adapter compound; all fixture values synthetic."""
from pathlib import Path
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'comparison'))
import strategy_c as c
import r10_compare as compare
from test_r10_compare import Fixture


class ReaderCompound(unittest.TestCase):
    def test_exact_pinned_native_shape_reaches_guard_and_bad_join_or_missing_identity_fails(self):
        with tempfile.TemporaryDirectory(prefix='SYNTHETIC-e04-C-') as folder:
            f = Fixture(folder)
            arm = f.results['arms'][2]
            record = arm['cold_start']
            def add_position(v):
                v['body']['player_armies'][0].update(controllable=True, in_combat=False,
                    retreating=False, move_target_observable=False)
            record['snapshot'] = f.edit(record['snapshot'], add_position)
            record['army_result'] = f.edit(record['army_result'],
                lambda v: v['army_strengths'][0].update(native_carmy_id=99))
            evidence = compare.Evidence(folder)
            observation = c.read_observation(f.plan, arm['runtime'], record, evidence)
            state = c.start(f.plan, observation)
            self.assertEqual(state['binding']['native_carmy_id'], 99)
            self.assertEqual(state['army_id'], 1)
            original = record['army_result']
            record['army_result'] = f.edit(original,
                lambda v: v.update(queried_revision=999))
            with self.assertRaisesRegex(ValueError, 'frame differs'):
                c.read_observation(f.plan, arm['runtime'], record, evidence)
            record['army_result'] = f.edit(original,
                lambda v: v['army_strengths'][0].pop('native_carmy_id'))
            missing = c.read_observation(f.plan, arm['runtime'], record, evidence)
            with self.assertRaisesRegex(ValueError, 'native_carmy_id'):
                c.start(f.plan, missing)


if __name__ == '__main__':
    unittest.main()
