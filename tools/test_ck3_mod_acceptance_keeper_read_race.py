"""Deterministic tests of the actual live_lease function and original checked_owner.

No real Git/bus/process/UI calls: only those unrelated boundaries are substituted.
Real checked_owner validates task/resources/state/HEAD/cleanliness/age in every test.
"""
import argparse
import ast
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from tempfile import TemporaryDirectory

REPO = Path(__file__).resolve().parents[1]
LEASE_SOURCE = REPO/'promo/ck3_native_war_ai/integration/screen_bus_lease.py'
SOURCE = REPO/'tools/ck3_mod_acceptance_keeper.py'
NOW = datetime.fromisoformat('2026-10-10T15:14:21+00:00')
TASK = 'test-exact-keeper'
HEAD = 'a'*40
SHA = 'B'*64


def functions(path,names,namespace):
    tree = ast.parse(path.read_bytes())
    selected = [node for node in tree.body if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name in names]
    if {node.name for node in selected} != set(names):
        raise RuntimeError('Actual source function absent')
    module = ast.Module(body=selected,type_ignores=[])
    exec(compile(module,str(path),'exec'),namespace)
    return namespace


OWNER = functions(LEASE_SOURCE,('require','checked_owner'),{'Path':Path,'datetime':datetime,'timezone':timezone,
    'SCHEMA':'codex.task_bus.v1','SCREEN':'ck3-screen:acquired','MAX_AGE_SECONDS':600,'MAX_FUTURE_SECONDS':10})


class LeaseRead(unittest.TestCase):
    def scenario(self,mode):
        temporary = TemporaryDirectory(prefix='ck3-keeper-read-'+mode+'-')
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        inputs = {'repo':str(root/'checkout'),'checkout_head':HEAD,'task_id':TASK,'bus_cli_sha256':SHA,
                  'source_cli':str(root/'source-cli.py'),'bus_dir':str(root/'bus'),'lease_module':{'path':str(LEASE_SOURCE)}}
        ready = {'inputs':{'path':str(root/'inputs.json')},'lease':{'task_id':TASK,'checkout_head':HEAD}}
        for name,value in (('inputs.json',inputs),('ready.json',ready)):
            (root/name).write_text(json.dumps(value),encoding='utf-8')
        lease = {'task_id':TASK,'checkout_head':HEAD,'cli_sha256':SHA,'sequence':10}
        def journal(value):
            (root/'journal.jsonl').write_text(json.dumps(value)+'\n',encoding='utf-8')
        journal({'result':'OWNED_CAS','lease':lease})
        calls = {'list':0,'sleep':0,'clock':0.0,'clock_reads':0,'sleep_values':[]}
        owner = {'schema':'codex.task_bus.v1','task_id':TASK,'state':'running','resources':['ck3-screen:acquired'],
                 'last_sequence':11,'repo':inputs['repo'],'git':{'head':HEAD,'dirty_entries':0},
                 'updated_at_utc':NOW.isoformat(),'stale':False}
        if mode == 'fresh':
            owner['last_sequence'] = 10
        elif mode == 'released':
            owner['state'] = 'done'
            owner['resources'] = []
        elif mode == 'changed-head':
            owner['git']['head'] = 'c'*40
        elif mode == 'stale':
            owner['updated_at_utc'] = '2026-10-10T14:00:00+00:00'
        elif mode == 'foreign-resource':
            owner['resources'].append('unrelated-resource')
        def call_bus(*args,**kwargs):
            calls['list'] += 1
            if mode == 'already-journaled' and calls['list'] == 1:
                journal({'result':'OWNED_CAS','lease':{**lease,'sequence':11}})
            return {'tasks':[copy.deepcopy(owner)]}
        def monotonic():
            calls['clock_reads'] += 1
            # Deadline creation=0, while condition=0, next read crosses it.
            if mode == 'deadline-crossing' and calls['clock_reads'] >= 3:
                calls['clock'] = 3.1
            return calls['clock']
        def sleep(seconds):
            if seconds < 0:
                raise RuntimeError('Negative read wait')
            calls['sleep_values'].append(seconds)
            calls['sleep'] += 1
            calls['clock'] += seconds
            if mode == 'lag' and calls['sleep'] == 2:
                journal({'result':'OWNED_CAS','lease':{**lease,'sequence':11}})
            elif mode == 'stop' and calls['sleep'] == 1:
                (root/'STOP').write_bytes(b'')
            elif mode == 'lost-journal' and calls['sleep'] == 1:
                journal({'result':'LOST_OR_UNCERTAIN_STOP','error':'real renewal failed'})
        module = SimpleNamespace(checkout_head=lambda repo:HEAD,call_bus=call_bus,checked_owner=OWNER['checked_owner'])
        namespace = functions(SOURCE,('require','live_lease'),{'Path':Path,'json':json,
            'read_json':lambda path:json.loads(path.read_bytes()),'check_pin':lambda row:None,
            'load_lease_module':lambda repo:module,'utc':lambda:NOW.isoformat(),
            'time':SimpleNamespace(monotonic=monotonic,sleep=sleep)})
        return lambda:namespace['live_lease'](root,now=NOW),calls

    def test_journal_lags_committed_same_owner_heartbeat(self):
        run,calls = self.scenario('lag')
        result = run()
        self.assertEqual(result['lease']['sequence'],11)
        self.assertEqual(calls['list'],2)
        self.assertEqual(calls['sleep'],2)

    def test_fresh_exact_owner_unchanged(self):
        run,calls = self.scenario('fresh')
        self.assertEqual(run()['lease']['sequence'],10)
        self.assertEqual(calls['sleep'],0)

    def test_existing_journal_advance_retry_preserved(self):
        run,calls = self.scenario('already-journaled')
        self.assertEqual(run()['lease']['sequence'],11)
        self.assertEqual(calls['list'],2)
        self.assertEqual(calls['sleep'],0)

    def test_newer_packet_without_receipt_never_accepted(self):
        run,calls = self.scenario('no-journal')
        with self.assertRaisesRegex(RuntimeError,'exact running CAS owner'):
            run()
        self.assertAlmostEqual(calls['clock'],3.0)
        self.assertEqual(calls['list'],1)

    def test_stop_during_wait_rejected(self):
        run,calls = self.scenario('stop')
        with self.assertRaisesRegex(ValueError,'stopped during ownership read'):
            run()
        self.assertEqual(calls['sleep'],1)

    def test_failed_renewal_journal_rejected(self):
        run,calls = self.scenario('lost-journal')
        with self.assertRaisesRegex(ValueError,'no longer owns the screen'):
            run()
        self.assertEqual(calls['list'],1)

    def test_released_owner_rejected_without_wait(self):
        run,calls = self.scenario('released')
        with self.assertRaisesRegex(RuntimeError,'screen resource is absent'):
            run()
        self.assertEqual(calls['sleep'],0)

    def test_changed_head_rejected_without_wait(self):
        run,calls = self.scenario('changed-head')
        with self.assertRaisesRegex(RuntimeError,'HEAD or cleanliness differs'):
            run()
        self.assertEqual(calls['sleep'],0)

    def test_stale_owner_rejected_without_wait(self):
        run,calls = self.scenario('stale')
        with self.assertRaisesRegex(RuntimeError,'heartbeat is stale'):
            run()
        self.assertEqual(calls['sleep'],0)

    def test_extra_resource_rejected_without_wait(self):
        run,calls = self.scenario('foreign-resource')
        with self.assertRaisesRegex(RuntimeError,'exact running CAS owner'):
            run()
        self.assertEqual(calls['sleep'],0)

    def test_deadline_crossed_between_loop_check_and_sleep_rejected_without_negative_sleep(self):
        run,calls = self.scenario('deadline-crossing')
        with self.assertRaisesRegex(RuntimeError,'exact running CAS owner'):
            run()
        self.assertGreaterEqual(calls['clock_reads'],3)
        self.assertTrue(all(seconds >= 0 for seconds in calls['sleep_values']))
        self.assertGreaterEqual(calls['clock'],3.0)
        self.assertEqual(calls['list'],1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source',type=Path,default=SOURCE)
    parser.add_argument('--baseline',action='store_true')
    parser.add_argument('--case',action='append')
    args = parser.parse_args()
    SOURCE = args.source
    suite = unittest.TestSuite([LeaseRead('test_journal_lags_committed_same_owner_heartbeat')]) if args.baseline else unittest.defaultTestLoader.loadTestsFromTestCase(LeaseRead)
    if args.case:
        suite = unittest.TestSuite([LeaseRead(name) for name in args.case])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
