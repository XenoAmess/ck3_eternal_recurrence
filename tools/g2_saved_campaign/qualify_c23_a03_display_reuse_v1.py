"""RAM qualification of exact retained owner routing; no scratch or runtime writes."""
import copy
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1])]
import prepare_c23_a03_display_reuse_v1 as reuse

RUNTIME = Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/robert30-v20261019-campaign01/runtime')


class Qualification(unittest.TestCase):
    def fixture(self):
        full = RUNTIME / 'RAM-ONLY-FULL.json'
        final = RUNTIME / 'RAM-ONLY-FINAL.json'
        data = {full: reuse.encode({'schema': 'xar.robert30year.storage-admission.v1',
                    'canonical_compatibility_v1': {}, 'machine_id': reuse.MACHINE, 'status': 'ADMITTED',
                    'review_at_utc': '2026-10-20T06:30:00+00:00',
                    'approved_output_roots': [str(RUNTIME.parent)], 'disk_reserve_bytes': 123456}),
                final: reuse.encode({'machine_id': reuse.MACHINE, 'source': 'RAM only'})}
        data[RUNTIME / 'STORAGE-ADMISSION.json'] = data[full]
        original = Path.read_bytes
        with patch.object(Path, 'read_bytes', lambda p: data[p] if p in data else original(p)):
            values, proof = reuse.plan(RUNTIME, full, final,
                observed_at_utc='2026-10-20T04:00:00+00:00')
        data.update(values)
        return data, values, proof

    def test_actual_original_18_leaves_and_unrun_config_are_read_only(self):
        data, values, proof = self.fixture()
        self.assertEqual(proof['reused_source_leaves'], 18)
        self.assertEqual(proof['reused_source_bytes'], 278733)
        self.assertEqual(proof['prior_profile_recording_references'], 0)
        self.assertEqual(len(values), 4)
        self.assertLessEqual(sum(map(len, values.values())), 32768)
        self.assertTrue(all(not p.exists() for p in values))
        old = json.loads((RUNTIME / 'ROOT-OBS-PROFILE-C23.json').read_bytes())
        new = json.loads(values[RUNTIME / reuse.PROFILE_NAME])
        self.assertEqual(new['password'], old['password'])
        self.assertEqual(new['profile_name'], old['profile_name'])
        self.assertNotIn(old['password'], values[RUNTIME / reuse.REVIEW_NAME].decode())
        self.assertNotIn(old['password'], values[RUNTIME / reuse.SPEC_NAME].decode())
        self.assertFalse(proof['pixel_admitted'])

    def test_adapter_loads_exact_original_owner_with_only_two_spec_changes(self):
        data, values, proof = self.fixture()
        env = {'__name__': '_RAM_A03_adapter', '__file__': str(RUNTIME / reuse.WRAPPER_NAME)}
        exec(compile(values[RUNTIME / reuse.WRAPPER_NAME], env['__file__'], 'exec'), env)
        original = Path.read_bytes
        with patch.object(Path, 'read_bytes', lambda p: data[p] if p in data else original(p)):
            owner = env['load_owner']()
        old = reuse.source_spec((RUNTIME / 'presentation-c23/start_new_game_display.py').read_bytes())
        self.assertEqual(owner.SPEC, dict(old, generation='C23-A03', profile=reuse.PROFILE_NAME))
        self.assertEqual(owner.P, RUNTIME / 'presentation-c23')
        self.assertEqual(owner.N, RUNTIME)
        self.assertEqual(owner.__file__, env['__file__'])
        self.assertEqual(owner.main.__globals__['__file__'], env['__file__'])
        self.assertEqual(owner.child_import_preflight.__globals__['SPEC'], owner.SPEC)
        self.assertEqual(owner.main.__code__.co_filename,
                         str(RUNTIME / 'presentation-c23/start_new_game_display.py'))

    def test_runtime_rejects_changed_full_review_profile_source_and_spec(self):
        data, values, proof = self.fixture()
        meta = json.loads(values[RUNTIME / reuse.SPEC_NAME])
        refs = [meta[k] for k in ('full_admission', 'live_canonical', 'root_final', 'new_profile')]
        refs += [meta['retained_owner'], meta['unrun_portable_config'][0]]
        refs.append({'path': str(RUNTIME / reuse.SPEC_NAME)})
        real = Path.read_bytes
        for ref in refs:
            path = Path(ref['path'])
            changed = dict(data)
            changed[path] = changed.get(path, real(path) if path.exists() else b'') + b' '
            env = {'__name__': '_RAM_A03_reject', '__file__': str(RUNTIME / reuse.WRAPPER_NAME)}
            exec(compile(values[RUNTIME / reuse.WRAPPER_NAME], env['__file__'], 'exec'), env)
            with self.subTest(path=path.name), patch.object(Path, 'read_bytes',
                    lambda p: changed[p] if p in changed else real(p)):
                with self.assertRaisesRegex(ValueError, 'differs'):
                    env['load_owner']()
        env = {'__name__': '_RAM_A03_expired', '__file__': str(RUNTIME / reuse.WRAPPER_NAME)}
        exec(compile(values[RUNTIME / reuse.WRAPPER_NAME], env['__file__'], 'exec'), env)
        real_datetime = env['datetime']
        env['datetime'] = types.SimpleNamespace(fromisoformat=real_datetime.fromisoformat,
            now=lambda zone: real_datetime.fromisoformat('2026-10-20T07:00:00+00:00'))
        with patch.object(Path, 'read_bytes', lambda p: data[p] if p in data else real(p)):
            with self.assertRaisesRegex(ValueError, 'expired'):
                env['load_owner']()

    def test_original_owner_lifecycle_uses_adapter_child_and_retains_publisher(self):
        data, values, proof = self.fixture()
        wrapper = RUNTIME / reuse.WRAPPER_NAME
        env = {'__name__': '_RAM_A03_lifecycle', '__file__': str(wrapper)}
        exec(compile(values[wrapper], str(wrapper), 'exec'), env)
        original = Path.read_bytes
        with patch.object(Path, 'read_bytes', lambda p: data[p] if p in data else original(p)):
            owner = env['load_owner']()
        spec = owner.SPEC
        data[RUNTIME / spec['launch']] = reuse.encode(
            {'pid': 101, 'creation_filetime': 999, 'creation_date': 'RAM-only'})
        data[RUNTIME / spec['placement']] = reuse.encode(
            {'pid': 101, 'creation_filetime': 999, 'status': 'GREEN',
             'foreground_unchanged': True, 'current_desktop_unchanged': True,
             'hwnd': 301, 'target_desktop_id': 'RAM-only'})
        records = Path(json.loads(data[RUNTIME / reuse.PROFILE_NAME])['recording_root'])
        events, held = [], {}
        def atomic(path, value, new=False):
            if new and path in data:
                raise FileExistsError(path)
            data[path] = reuse.encode(value)
        class FakeOwner:
            process = None
            def __init__(self, path): self.path = path
            def start(self):
                self.process = types.SimpleNamespace(wait=lambda: events.append('retained_wait'))
                held['ref'] = {'path': str(RUNTIME / spec['state'] / 'STARTED.json')}
                events.append('new_publisher')
            def started(self): return held['ref']
            def seal_binding(self, path): atomic(path, {}, new=True)
            def close(self): events.append('retained_close'); return {'RAM_only': True}
        api = types.SimpleNamespace(SCHEMA='RAM-only', PublisherOwner=FakeOwner,
            process_identity=lambda pid: {'creation_filetime': 999}, atomic=atomic,
            pin=lambda p: {'path': str(p)})
        api_module = types.ModuleType(spec['api_module'])
        api_module.load_api = lambda root: api
        api_module.started_reference = lambda root, value: held['ref']
        capture = types.ModuleType('_RAM_capture')
        capture.__file__ = str(RUNTIME / 'presentation-c23/ck3_obs_capture_png_retry_c23.py')
        capture.decision_publisher_api = lambda: api
        capture._generation_helpers = lambda: events.append('helper_preflight')
        def recording(*args, **kwargs):
            self.assertEqual(args[0], RUNTIME / reuse.PROFILE_NAME)
            self.assertEqual(kwargs['decision_publisher_receipt'], Path(held['ref']['path']))
            events.append('new_recording_UUID')
            return {'session_id': 'RAM-only-UUID'}
        capture.launch_recording = recording
        def child_run(argv, **kwargs):
            self.assertEqual(argv, [sys.executable, str(wrapper), '--child-import-preflight'])
            self.assertEqual(kwargs['env']['PYTHONDONTWRITEBYTECODE'], '1')
            events.append('adapter_child_preflight')
            return types.SimpleNamespace(returncode=0, stderr=b'', stdout=reuse.encode(
                {'status': 'ACTUAL_CHILD_ENV_IMPORT_PREFLIGHT_PASS', 'machine_id': reuse.MACHINE,
                 'capture_path': capture.__file__,
                 'capture_sha256': '89e7d416bc03863b50e17a4946e77bcc35207081677b7f4f7d34374f1c97efa5',
                 'same_interpreter': str(Path(sys.executable).resolve()), 'bytecode_disabled': True}))
        args = ['owner', '--game-launch', str(RUNTIME / spec['launch']),
                '--placement', str(RUNTIME / spec['placement']), '--obs-profile',
                str(RUNTIME / reuse.PROFILE_NAME), '--current-request',
                str(RUNTIME / 'CURRENT-REQUEST-P37.json'), '--job-root', str(records),
                '--ffprobe', 'RAM-only-ffprobe', '--game-pid', '101', '--game-birth', '999']
        exists = Path.exists
        loader = types.SimpleNamespace(loader=types.SimpleNamespace(exec_module=lambda module: None))
        with patch.object(Path, 'read_bytes', lambda p: data[p] if p in data else original(p)), \
             patch.object(Path, 'exists', lambda p: p in data if p.is_relative_to(RUNTIME) else exists(p)), \
             patch.object(Path, 'read_text', lambda p, **kw: data[p].decode() if p in data else original(p).decode()), \
             patch.object(Path, 'is_dir', return_value=True), \
             patch.dict(sys.modules, {spec['api_module']: api_module}), \
             patch.object(importlib.util, 'spec_from_file_location', return_value=loader), \
             patch.object(importlib.util, 'module_from_spec', return_value=capture), \
             patch('subprocess.run', side_effect=child_run), \
             patch.object(sys, 'argv', args), patch.object(sys, 'path', list(sys.path)), \
             patch.dict(os.environ), contextlib.redirect_stdout(io.StringIO()):
            owner.main()
        self.assertEqual(events, ['helper_preflight', 'adapter_child_preflight',
            'new_publisher', 'new_recording_UUID', 'retained_wait', 'retained_close'])
        self.assertEqual(json.loads(data[RUNTIME / spec['requested']])['generation'], 'C23-A03')
        self.assertFalse(json.loads(data[RUNTIME / spec['requested']])['map_ready_claimed'])

    def test_first_use_collision_or_changed_original_graph_rejects_before_plan(self):
        real_exists = Path.exists
        collision = RUNTIME / 'ROOT-DECISION-TEXT-PUBLISHER-BINDING-C23.json'
        with patch.object(Path, 'exists', lambda p: True if p == collision else real_exists(p)):
            with self.assertRaisesRegex(ValueError, 'namespace'):
                reuse.existing_graph(RUNTIME)
        real_read = Path.read_bytes
        owner = RUNTIME / 'presentation-c23/start_new_game_display.py'
        with patch.object(Path, 'read_bytes', lambda p: real_read(p) + (b' ' if p == owner else b'')):
            with self.assertRaisesRegex(ValueError, 'pin differs'):
                reuse.existing_graph(RUNTIME)


if __name__ == '__main__':
    unittest.main(verbosity=2)
