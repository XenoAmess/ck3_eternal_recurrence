"""Pure prepared/ready scope checks; never start a process or read a ready file."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
MODULE = ROOT/'ck3_autonomous_player/native_bridge/research/refill_add_live_12004/launch_live_refill_add.py'
spec = importlib.util.spec_from_file_location('carrier_launcher_candidate', MODULE)
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)


def prepared(*, legacy=False):
    module = str(ROOT/'synthetic/xar_ck3_bridge.dll')
    value = {'schema': 'xar.ck3.refill_ADD_12004.prepared_live_argv.v1' if legacy else
                      'xar.ck3.refill_ADD_12004.prepared_live_argv.v2',
             'machine_id': 'synthetic-machine', 'observer_launched': False, 'actual_ADD_observed': False,
             'native_argv': [str(ROOT/'refill_add_hwprobe_12004.exe'), '--enable',
                 '--pid', '123', '--thread', '456', '--regiment', '50001', '--slot', '0',
                 '--created', '134000000000000001', '--timeout-ms', '30000',
                 '--raw', str(ROOT/'synthetic.raw'), '--ready', str(ROOT/'synthetic.ready'),
                 '--machine-id', 'synthetic-machine'],
             'consume_argv': ['python', 'consume_live_refill_add.py'],
             'ready_must_match': {'schema': 'xar.ck3.refill_ADD_12004.hwprobe_ready.v2' if legacy else
                                           'xar.ck3.refill_ADD_12004.hwprobe_ready.v3',
                 'machine_id': 'synthetic-machine', 'pid': 123, 'thread_id': 456,
                 'regi_full_id_u32': 50001, 'physical_slot': 0,
                 'process_created_filetime': 134000000000000001,
                 'site_0': '0x2A98B88', 'site_1': '0x2A98B8B'}}
    if not legacy:
        value.update(carrier_module_path=module, carrier_source_epoch=20261018,
                     consume_argv_requires_core_observation=True,
                     consume_core_observation_argument_name='--core-observation')
        value['ready_must_match'].update(carrier_module_path=module, carrier_source_epoch=20261018)
    return value


class LauncherReadyScopeTests(unittest.TestCase):
    def test_v3_explicit_scope_and_legacy_v2_pass_without_mutation(self):
        for legacy in (False, True):
            value = prepared(legacy=legacy); before = deepcopy(value)
            argv, consume, expected, values = launcher.validate_prepared_ready_scope(value)
            self.assertEqual(value, before)
            self.assertEqual(argv, before['native_argv'])
            self.assertEqual(consume, before['consume_argv'])
            self.assertEqual(expected, before['ready_must_match'])
            self.assertEqual(values['--created'], '134000000000000001')
            self.assertNotIn('--core-observation', consume)

    def test_v3_carrier_missing_wrong_type_epoch_path_or_schema_rejected(self):
        for change in ('missing-path', 'missing-epoch', 'relative', 'basename', 'bool', 'wrong-epoch',
                       'ready-path', 'ready-epoch', 'ready-bool', 'old-prepared', 'old-ready'):
            value = prepared(); ready = value['ready_must_match']
            if change == 'missing-path': value.pop('carrier_module_path')
            if change == 'missing-epoch': value.pop('carrier_source_epoch')
            if change == 'relative': value['carrier_module_path'] = 'xar_ck3_bridge.dll'
            if change == 'basename': value['carrier_module_path'] = str(ROOT/'other.dll')
            if change == 'bool': value['carrier_source_epoch'] = True
            if change == 'wrong-epoch': value['carrier_source_epoch'] = 20261019
            if change == 'ready-path': ready['carrier_module_path'] = str(ROOT/'other/xar_ck3_bridge.dll')
            if change == 'ready-epoch': ready['carrier_source_epoch'] = 20261019
            if change == 'ready-bool': ready['carrier_source_epoch'] = True
            if change == 'old-prepared': value['schema'] = 'xar.ck3.refill_ADD_12004.prepared_live_argv.v1'
            if change == 'old-ready': ready['schema'] = 'xar.ck3.refill_ADD_12004.hwprobe_ready.v2'
            with self.subTest(change=change), self.assertRaises(ValueError):
                launcher.validate_prepared_ready_scope(value)

    def test_existing_owner_and_nine_field_argv_guards_still_reject(self):
        for change in ('pid', 'created-type', 'machine', 'timeout', 'flag', 'extra-argument'):
            value = prepared()
            if change == 'pid': value['ready_must_match']['pid'] += 1
            if change == 'created-type': value['ready_must_match']['process_created_filetime'] = 134000000000000001.0
            if change == 'machine': value['ready_must_match']['machine_id'] = 'other-machine'
            if change == 'timeout': value['native_argv'][13] = '30001'
            if change == 'flag': value['native_argv'][2] = '--other-pid'
            if change == 'extra-argument': value['native_argv'].extend(['--core-observation', 'not-a-native-arg'])
            with self.subTest(change=change), self.assertRaises(ValueError):
                launcher.validate_prepared_ready_scope(value)


if __name__ == '__main__': unittest.main()
