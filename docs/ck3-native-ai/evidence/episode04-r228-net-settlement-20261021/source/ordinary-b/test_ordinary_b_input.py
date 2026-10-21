"""Two offline groups: retained real frame and legacy/schema counterexamples."""
from __future__ import annotations
import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import types
import unittest
from jsonschema import Draft202012Validator
import candidate_sources as build
import ordinary_campaign as ordinary

PACKET = Path('C:/ck3-e04-resume-20261020-a01/r15-complete-episode04-1030-a01/live-scene-r08-a02/driver-runs/desktop-3fevhd2-1c74096080--vanilla--R0228/hot-r08-repair-a02/r08-postload-common-packets/r08-postload-R228-repair02-14-independent-after.common-view.json')


def module(name: str, source: str) -> types.ModuleType:
    value = types.ModuleType(name)
    value.__file__ = str(Path(build.W) / build.PREFIX / (name + '.py'))
    sys.modules[name] = value
    exec(compile(source, value.__file__, 'exec'), value.__dict__)
    return value


OLD, NEW = build.sources()
C = module('r10_compare', build.blob('r10_compare.py'))
BASE = module('baseline_strategy_b', OLD['strategy_b.py'])
B = module('strategy_b', NEW['strategy_b.py'])
SCHEMA = json.loads(NEW['r10.schema.json'])


class Tests(unittest.TestCase):
    def real(self) -> dict:
        raw = PACKET.read_bytes()
        self.assertEqual((len(raw), hashlib.sha256(raw).hexdigest()),
            (30105, '2ada0e9f4112b50cbde05042d8db9e1fa670b1ecd9b454630137ffcd64fe69cb'))
        return json.loads(raw)

    def runtime(self, packet: dict) -> dict:
        body = packet['body']
        return {'machine_id': packet['machine_id'], 'started_at_utc': '2026-10-21T11:34:11Z',
            'pid': body['diagnostics']['bridge_pid'], 'connection_generation': 1,
            'process_create_time_100ns': 134370531135233564, 'episode': None,
            'player_character_id': 31254, 'source_head': '1' * 40,
            'native_dll_sha256': '2' * 64,
            'source_proof': {k: packet['common_original'][k] for k in ('path', 'bytes', 'sha256')},
            'managed_campaign_run_binding': deepcopy(body['managed_campaign_run_binding'])}

    def test_real_missing_episode_consumer_and_bracket(self) -> None:
        packet = self.real(); frame = packet['body']; rt = self.runtime(packet)
        self.assertNotIn('episode_run_id', frame)
        self.assertIs(C.frame(packet, rt), frame)
        with self.assertRaises(KeyError):
            BASE._frame_order({'snapshot': frame}, {'snapshot': frame}, same_day=True)
        B._frame_order({'snapshot': frame}, {'snapshot': frame}, same_day=True)
        B.check_runtime(frame, rt)
        self.assertIsNone(B.episode_value(frame))
        self.assertFalse(ordinary.episode_identity(frame).key_present)
        tree = ast.parse(NEW['strategy_b_next.py'])
        function = next(x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == '_scope_steps')
        scope_module = ast.Module(body=[function], type_ignores=[])
        ns = {'c': C, 'b': B, '_need': build.need}
        exec(compile(scope_module, 'actual_candidate_strategy_b_next.py', 'exec'), ns)
        class Evidence:
            def json(self, ref: dict) -> dict:
                if ref['path'] == 'caps':
                    return {'body': {'backend_id': 'native-headless', 'snapshot': True,
                        'diagnostics': frame['diagnostics'], 'action_steps': ['pause-map']}}
                return packet
        scope = {'before_snapshot': {'path': 'before'}, 'after_snapshot': {'path': 'after'},
                 'capabilities': {'path': 'caps'}}
        self.assertEqual(ns['_scope_steps'](scope, {'snapshot': frame}, Evidence(), rt), {'pause-map'})
        for key in ('run_id', 'state_dir', 'host_path', 'frozen_argv_sha256'):
            changed = deepcopy(frame)
            changed['managed_campaign_run_binding'][key] += 'x'
            with self.subTest(drift=key), self.assertRaises(ValueError):
                B._frame_order({'snapshot': frame}, {'snapshot': changed})
        for key in ('pid', 'connection_generation', 'player_character_id'):
            bad = deepcopy(rt); bad[key] += 1
            with self.subTest(runtime=key), self.assertRaises(ValueError):
                B.check_runtime(frame, bad)
        missing = deepcopy(frame); del missing['managed_campaign_run_binding']
        with self.assertRaises(ValueError):
            B.episode_value(missing)
        explicit = deepcopy(frame); explicit['episode_run_id'] = None
        self.assertTrue(ordinary.episode_identity(explicit).key_present)
        B._frame_order({'snapshot': frame}, {'snapshot': explicit})
        self.assertNotIn('episode_run_id', frame)
        self.real()
        print('REAL_FRAME: old KeyError; candidate B order+actual capability function PASS; raw original unchanged')

    def test_legacy_and_generated_schema(self) -> None:
        packet = self.real(); frame = deepcopy(packet['body']); rt = self.runtime(packet)
        frame['episode_run_id'] = 'old-one-life'; rt['episode'] = 'old-one-life'
        del frame['managed_campaign_run_binding']; del frame['episode_projection']
        del rt['managed_campaign_run_binding']
        BASE._frame_order({'snapshot': frame}, {'snapshot': frame})
        B._frame_order({'snapshot': frame}, {'snapshot': frame})
        B.check_runtime(frame, rt)
        changed = deepcopy(frame); changed['episode_run_id'] = 'other'
        with self.assertRaises(ValueError):
            B._frame_order({'snapshot': frame}, {'snapshot': changed})
        schema = {**SCHEMA, 'oneOf': [{'$ref': '#/$defs/runtime'}]}
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
        validator.validate(rt)
        ordinary_rt = self.runtime(packet); validator.validate(ordinary_rt)
        del ordinary_rt['managed_campaign_run_binding']
        self.assertTrue(list(validator.iter_errors(ordinary_rt)))
        candidate_schema = module('a10_schema_source', NEW['schema_source.py'])
        self.assertEqual(json.loads(json.dumps(candidate_schema.SCHEMA)), SCHEMA)
        print('LEGACY: nonnull path unchanged; ordinary-only binding required; schema generated from source equal')


if __name__ == '__main__':
    unittest.main()
