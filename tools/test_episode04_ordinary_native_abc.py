"""Synthetic owner compatibility through real T0, schema and C constructors.

No SDK or game is connected. Existing native-shaped fixtures supply complete
military inputs; only OS/transport seams in the existing C fixture are mocked.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import ModuleType
import unittest

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('--candidate-root', type=Path)
parser.add_argument('--dependency-repo', type=Path)
parser.add_argument('--scratch-root', type=Path)
options, remaining = parser.parse_known_args()
sys.argv = [sys.argv[0], *remaining]
ROOT = (options.candidate_root or Path(__file__).resolve().parents[1]).resolve()
DEPENDENCIES = (options.dependency_repo or ROOT).resolve()
sys.path.insert(0, str(DEPENDENCIES / 'ck3_autonomous_player/src'))
BASE = ROOT / 'promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02'


def load(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError('exact module cannot load: ' + str(path))
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


ready = load(ROOT / 'ck3_autonomous_player/src/xar_autoplayer/bridge/episode04_ready_t0_12004.py',
             'xar_autoplayer.bridge.ordinary_abc_ready_subject')
ready_fixture = load(ROOT / 'ck3_autonomous_player/tests/test_episode04_ready_t0_12004.py',
                     'ordinary_abc_existing_military_fixture')
guard_fixture = load(BASE / 'tests/test_runtime_binding.py', 'ordinary_abc_existing_guard_fixture')
c_fixture = load(BASE / 'strategy_c/test_operation_root_relay.py', 'ordinary_abc_existing_C_fixture')
phased_fixture = load(BASE / 'strategy_c/test_phased_relay_explicit_bindings.py',
                     'ordinary_abc_existing_phased_fixture')


class OrdinaryNativeABC(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix='ordinary-abc-', dir=options.scratch_root)
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)

    def test_complete_ready_t0_accepts_native_null_and_legacy_episode(self) -> None:
        for episode in (None, 'synthetic-episode'):
            with self.subTest(episode=episode):
                values = ready_fixture.fixture()
                for frame in (values['before'], values['after']):
                    frame['episode_run_id'] = episode
                values['source_binding']['episode_run_id'] = episode
                result = ready.evaluate_episode04_ready_t0_12004(**values)
                self.assertTrue(result['military_t0_frame_ready'], result)
                self.assertFalse(result['normal_t0_saved'])  # no Save was supplied or submitted
                self.assertFalse(result['r01_research_core_closed'])

    def test_null_is_not_missing_or_permission_to_drop_native_owner(self) -> None:
        for field in ('episode_run_id', 'pid', 'process_creation_filetime_100ns',
                      'connection_generation', 'actor_id', 'normal_robert_source_receipt_sha256'):
            values = ready_fixture.fixture()
            for frame in (values['before'], values['after']):
                frame['episode_run_id'] = None
            values['source_binding']['episode_run_id'] = None
            del values['source_binding'][field]
            self.assertFalse(ready.evaluate_episode04_ready_t0_12004(**values)['military_t0_frame_ready'], field)
        values = ready_fixture.fixture()
        values['source_binding']['episode_run_id'] = None
        values['before']['episode_run_id'] = None
        del values['after']['episode_run_id']
        self.assertFalse(ready.evaluate_episode04_ready_t0_12004(**values)['military_t0_frame_ready'])

    def test_real_operation_guard_preserves_null_and_normal_save_binding(self) -> None:
        fixture = guard_fixture.Fixture(self.directory)
        fixture.runtime['episode'] = None
        fixture.binding['runtime']['episode'] = None
        result = fixture.validate()
        self.assertIsNone(result['runtime']['episode'])
        with self.assertRaises(ValueError):
            fixture.validate(normal_save_sha256='c' * 64)
        for field in ('pid', 'process_create_time_100ns', 'generation', 'actor'):
            changed = deepcopy(fixture.binding)
            changed['runtime'][field] += 1
            with self.subTest(field=field), self.assertRaises(ValueError):
                fixture.validate(changed)
        with self.assertRaises(ValueError):
            guard_fixture.g.proof_runtime({'episode': None})
        with self.assertRaises(ValueError):
            guard_fixture.g.arm_runtime({})

    def test_actual_C_constructor_accepts_null_without_transport_or_lifetime_weakening(self) -> None:
        fixture = c_fixture.Fixture(self.directory)
        fixture.proof['episode_run_id'] = None
        fixture.document['runtime']['episode'] = None
        fixture.flush()
        live = fixture.construct()
        self.assertIsNone(live.binding['episode'])
        self.assertFalse(fixture.calls)
        self.assertFalse(live.meta['fresh_C_arm_qualified'])
        with self.assertRaisesRegex(RuntimeError, 'PID/create-time'):
            fixture.construct(process_value=134000000000000124)
        fixture.prepared['checkpoint']['source']['save']['sha256'] = 'c' * 64
        fixture.flush()
        with self.assertRaisesRegex(RuntimeError, 'normal prepared save'):
            fixture.construct()

    def test_C_bundle_real_source_binding_accepts_explicit_null_but_not_absence(self) -> None:
        phased_fixture.fixture_args.scratch_root = self.directory
        fixture = phased_fixture.BindingCases('test_explicit_c499_pins_prepare_and_forward_real_sequence')
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.modify('runtime_proof', lambda value: value.update(episode_run_id=None))
        result = phased_fixture.c.runtime_binding(fixture.b)
        self.assertEqual(result['run_sequence'], 278)
        fixture.modify('runtime_proof', lambda value: value.pop('episode_run_id'))
        with self.assertRaisesRegex(ValueError, 'episode missing'):
            phased_fixture.c.runtime_binding(fixture.b)

    def test_runtime_schema_supports_null_and_legacy_but_requires_the_field(self) -> None:
        from jsonschema import Draft202012Validator
        schema = json.loads((BASE / 'comparison/r10.schema.json').read_bytes())
        validator = Draft202012Validator({'$schema': schema['$schema'], '$defs': schema['$defs'],
                                         '$ref': '#/$defs/runtime'})
        runtime = {'machine_id': 'SYNTHETIC', 'started_at_utc': '2031-01-01T00:00:00Z',
                   'pid': 1234, 'process_create_time_100ns': 134000000000000123,
                   'connection_generation': 1, 'episode': None, 'player_character_id': 42,
                   'source_head': 'a' * 40, 'native_dll_sha256': 'b' * 64,
                   'source_proof': {'path': 'proof.json', 'bytes': 123, 'sha256': 'c' * 64}}
        validator.validate(runtime)
        runtime['episode'] = 'legacy-synthetic-episode'
        validator.validate(runtime)
        for value in ('', False, 0):
            runtime['episode'] = value
            self.assertTrue(list(validator.iter_errors(runtime)))
        del runtime['episode']
        self.assertTrue(list(validator.iter_errors(runtime)))


if __name__ == '__main__':
    unittest.main()
