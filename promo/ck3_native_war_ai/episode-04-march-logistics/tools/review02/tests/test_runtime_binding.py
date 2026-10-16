"""Synthetic Root operation guards; never start CK3 or a real request helper."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('e04_runtime_guard_test', ROOT/'runtime_binding.py')
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)


class Fixture:
    def __init__(self, root):
        self.root = root
        self.now = datetime(2030, 1, 1, 12, tzinfo=timezone.utc)
        self.machine, self.source = 'SYNTHETIC-other-machine', 'a'*40
        self.run = self.machine+'--vanilla--R0901'
        self.runtime = dict(pid=99, process_create_time_100ns=134000000000000123,
                            generation=1, actor=42, episode='synthetic-42-new')
        self.context = {'machine_id': self.machine, 'source_head': self.source,
                        'identity': {'machine_id': self.machine, 'mod_key': 'vanilla',
                                     'sequence': 901, 'run_id': self.run}}
        deadline = (self.now+timedelta(hours=1)).isoformat()
        self.capacity = {'admitted': True, 'machine_id': self.machine, 'source_head': self.source,
                         'run_id': self.run, 'scene_root': str(root), 'policy_version': '1.0.0',
                         'source_binding': {'new_clean_integrated_source_head': self.source},
                         'root_atomic_adoption_required': False,
                         'root_adopted_at_utc': (self.now-timedelta(minutes=1)).isoformat(),
                         'quota_review_at_utc': deadline,
                         'component_ceiling_bytes': {'driver': 128*1024*1024},
                         'new_scene_aggregate_bytes': 256*1024*1024}
        self.capacity_pin = self.put('capacity.json', self.capacity)
        self.context['capacity_admission'] = self.capacity_pin['path']
        self.binding = {'schema': g.SCHEMA, 'operation_id': 'SYNTHETIC-NEW-ABC-A',
                        'machine_id': self.machine, 'source_head': self.source,
                        'scene_root': str(root), 'run_id': self.run, 'run_sequence': 901,
                        'runtime': deepcopy(self.runtime), 'normal_save_sha256': 'b'*64,
                        'created_at_utc': self.now.isoformat(), 'deadline_utc': deadline,
                        'max_runtime_total_bytes': 64*1024*1024,
                        'capacity_admission': self.capacity_pin,
                        'guard_sha256': hashlib.sha256((ROOT/'runtime_binding.py').read_bytes()).hexdigest()}
        self.binding_pin = self.put('binding.json', self.binding)

    def put(self, name, value):
        p = self.root/name
        raw = (json.dumps(value, ensure_ascii=False)+'\n').encode()
        p.write_bytes(raw)
        return {'path': str(p.resolve()), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

    def options(self):
        return dict(scene_root=self.root, source_head=self.source, machine_id=self.machine,
                    run_id=self.run, max_runtime_total_bytes=64*1024*1024,
                    normal_save_sha256='b'*64, deadline_utc=self.binding['deadline_utc'])

    def validate(self, binding=None, capacity=None, **options):
        args = {**self.options(), 'now_utc': self.now, **options}
        return g.validate_operation(binding or self.binding, capacity or self.capacity,
                                    self.context, self.runtime, **args)

    def guard(self, **kwargs):
        return g.OperationGuard(self.binding_pin['path'], self.binding_pin['sha256'],
                                context=self.context, runtime=self.runtime,
                                clock=lambda: self.now, **{**self.options(), **kwargs})


class PureBindingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.f = Fixture(Path(self.temp.name))

    def test_new_machine_source_and_deadline_are_explicit_not_historical_defaults(self):
        value = self.f.validate()
        self.assertEqual(value['machine_id'], 'SYNTHETIC-other-machine')
        self.assertEqual(value['run_sequence'], 901)
        self.assertEqual(value['runtime']['process_create_time_100ns'], 134000000000000123)

    def test_wrong_machine_scene_run_source_or_lifetime_refused(self):
        for key, value in [('machine_id','other'), ('source_head','d'*40),
                           ('run_id','other--vanilla--R0901'), ('run_sequence',902),
                           ('scene_root',str(self.f.root/'other'))]:
            changed = deepcopy(self.f.binding)
            changed[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.f.validate(changed)
        for key, value in [('pid',100), ('process_create_time_100ns',134000000000000124),
                           ('generation',2), ('actor',43), ('episode','old-episode')]:
            changed = deepcopy(self.f.binding)
            changed['runtime'][key] = value
            with self.subTest(runtime=key), self.assertRaisesRegex(ValueError,'lifetime|identities|differs'):
                self.f.validate(changed)

    def test_no_null_zero_bool_or_partial_runtime_admission(self):
        for value in [None, 0, True]:
            changed = deepcopy(self.f.binding)
            changed['runtime']['generation'] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.f.validate(changed)
        changed = deepcopy(self.f.binding)
        del changed['runtime']['episode']
        with self.assertRaises(ValueError):
            self.f.validate(changed)

    def test_expired_exact_boundary_future_creation_and_over_seven_days_refused(self):
        deadline = g.timestamp(self.f.binding['deadline_utc'])
        with self.assertRaises(ValueError):
            self.f.validate(now_utc=deadline)
        with self.assertRaises(ValueError):
            self.f.validate(now_utc=self.f.now-timedelta(seconds=1))
        changed = deepcopy(self.f.binding)
        changed['deadline_utc'] = (self.f.now+timedelta(days=8)).isoformat()
        with self.assertRaises(ValueError):
            self.f.validate(changed)
        changed = deepcopy(self.f.binding)
        changed['deadline_utc'] = changed['deadline_utc'][:-6]
        with self.assertRaises(ValueError):
            self.f.validate(changed)

    def test_candidate_old_scene_wrong_source_or_insufficient_capacity_refused(self):
        changes = [('admitted',False), ('root_atomic_adoption_required',True),
                   ('root_adopted_at_utc',None), ('machine_id','other'),
                   ('run_id','other-run'), ('source_head','c'*40),
                   ('scene_root',str(self.f.root/'old')), ('policy_version',None),
                   ('quota_review_at_utc',(self.f.now+timedelta(hours=2)).isoformat()),
                   ('new_scene_aggregate_bytes',1), ('source_binding',{}),
                   ('component_ceiling_bytes',{'driver':1})]
        for key, value in changes:
            capacity = deepcopy(self.f.capacity)
            capacity[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.f.validate(capacity=capacity)

    def test_changed_normal_seed_budget_or_conflicting_aggregate_refused(self):
        with self.assertRaises(ValueError):
            self.f.validate(normal_save_sha256='c'*64)
        with self.assertRaises(ValueError):
            self.f.validate(max_runtime_total_bytes=65*1024*1024)
        changed = deepcopy(self.f.capacity)
        changed['aggregate_scene_ceiling_bytes'] = 1
        with self.assertRaises(ValueError):
            self.f.validate(capacity=changed)

    def test_both_binding_arguments_or_neither_and_runtime_options_use_exact_pin(self):
        self.assertIsNone(g.optional_guard(None,None))
        for path, sha in [(self.f.binding_pin['path'],None),(None,'a'*64)]:
            with self.assertRaises(ValueError):
                g.optional_guard(path,sha)
        guard = self.f.guard()
        options = g.runtime_options({'max_runtime_total_bytes':64*1024*1024},guard)
        self.assertEqual(options['runtime_capacity_admission'],
                         [self.f.capacity_pin['path'],self.f.capacity_pin['sha256']])
        with self.assertRaises(ValueError):
            g.runtime_options({'max_runtime_total_bytes':64*1024*1024,
                               'runtime_capacity_admission':['other.json','f'*64]},guard)

    def test_each_request_guard_rechecks_deadline_and_original_capacity_bytes(self):
        guard = self.f.guard()
        guard.check()
        self.f.now += timedelta(hours=1)
        with self.assertRaises(ValueError):
            guard.check()
        self.f.now -= timedelta(hours=1)
        p = Path(self.f.capacity_pin['path'])
        original = p.read_bytes()
        p.write_bytes(original.replace(b'"admitted": true',b'"admitted": null'))
        with self.assertRaises(ValueError):
            guard.check()

    def test_binding_guard_source_pin_and_duplicate_keys_refused(self):
        changed = deepcopy(self.f.binding)
        changed['guard_sha256'] = '0'*64
        pin = self.f.put('wrong-guard.json',changed)
        with self.assertRaises(ValueError):
            g.OperationGuard(pin['path'],pin['sha256'],context=self.f.context,runtime=self.f.runtime,
                             clock=lambda:self.f.now,**self.f.options())
        p = self.f.root/'duplicate.json'
        p.write_bytes(b'{"schema":"a","schema":"b"}')
        with self.assertRaises(ValueError):
            g._read_pinned(p,hashlib.sha256(p.read_bytes()).hexdigest())


class LiveEntryBoundaryTests(unittest.TestCase):
    setUp = PureBindingTests.setUp
    def source(self, relative, name):
        spec=importlib.util.spec_from_file_location(name,ROOT/relative)
        value=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(value)
        return value

    def test_R09_request_expiry_stops_before_process_or_transport(self):
        root=self.source('split_merge/root_relay.py','guarded_R09_entry_test')
        guard=self.f.guard()
        self.f.now += timedelta(hours=1)
        fake=SimpleNamespace(live_operation_guard=guard)
        with self.assertRaisesRegex(ValueError,'expired'):
            root.Relay.request(fake,'snapshot','ck3_take_snapshot',{})

    def test_A_request_expiry_stops_before_inherited_transport(self):
        entry=self.source('comparison/strategy_a_stages.py','guarded_A_entry_test')
        base=SimpleNamespace(Live=object)
        cls=entry.make_live_class(base,None,None,None)
        guard=self.f.guard()
        self.f.now += timedelta(hours=1)
        fake=SimpleNamespace(live_operation_guard=guard)
        with self.assertRaisesRegex(ValueError,'expired'):
            cls.request(fake,'snapshot','ck3_take_snapshot',{})

    def test_C_new_binding_rejects_legacy_API_before_calling_constructor(self):
        entry=self.source('strategy_c/phased_relay.py','guarded_C_entry_test')
        path=self.f.root/'synthetic_legacy_relay.py'
        for api in (None,'xar.e04.C.unknown-constructor.v0'):
            # Real exact-pinned source import is allowed. A legacy constructor
            # must never run merely because the new operation was qualified.
            text=('' if api is None else 'OPERATION_BINDING_API='+repr(api)+'\n')
            text+='class Live:\n    def __init__(self,args):\n        raise AssertionError("legacy constructor called")\n'
            path.write_text(text,encoding='utf-8')
            bundle={'modules':{'root_relay':entry.pin(path)}}
            with (self.subTest(api=api),
                  patch.object(entry,'prepare',return_value={'status':'SOURCE-COMPOSITION-PREPARED'}),
                  patch.object(entry,'runtime_binding',return_value={}),
                  patch.object(entry,'operation_guard',return_value=(g,self.f.guard()))):
                with self.assertRaisesRegex(ValueError,'NO_GO_LEGACY_LOCKED_CONSTRUCTOR'):
                    entry.provider(bundle,SimpleNamespace())


if __name__ == '__main__':
    unittest.main()
