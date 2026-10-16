"""CLI-to-real-Relay binding regressions; no game, SDK or relay requests."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True


def option(name, default):
    if name not in sys.argv:
        return default
    index = sys.argv.index(name)
    value = sys.argv[index + 1]
    del sys.argv[index:index + 2]
    return Path(value)


REPO = option('--repository', Path(__file__).resolve().parents[6])
SCRATCH = option('--scratch-root', None)
COMPARISON = Path(__file__).resolve().parent
RELAY_PATH = REPO / 'promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/split_merge/root_relay.py'
HEAD = 'c4992c304d196135d9590799d69ffb3c9f5510e6'
MACHINE = 'desktop-3fevhd2-1c74096080'
sys.path.insert(0, str(REPO / 'ck3_autonomous_player/src'))


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


B = load_module(COMPARISON / 'strategy_b_stages.py', 'B_explicit_binding_subject')
ROOT = load_module(RELAY_PATH, 'B_explicit_binding_real_relay')


class Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=SCRATCH)
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.repo = self.base / 'repo'
        self.repo.mkdir()
        self.assets = self.base / 'assets'
        self.assets.mkdir()
        self.run_id = MACHINE + '--vanilla--R0188'
        self.run = self.assets / self.run_id
        self.run.mkdir()
        self.capacity = self.put(self.assets / 'capacity.json', {
            'machine_id': MACHINE, 'admitted': True,
            'shared_child_limit_bytes': 512 * 1024 * 1024,
            'quota_review_at_utc': ROOT.DEADLINE})
        self.context = self.put(self.assets / 'context.json', {
            'machine_id': MACHINE, 'source_head': HEAD,
            'identity': {'machine_id': MACHINE, 'run_id': self.run_id,
                         'sequence': 188, 'mod_key': 'vanilla'},
            'capacity_admission': str(self.capacity)})
        self.proof = self.put(self.assets / 'runtime.json', {
            'machine_id': MACHINE, 'run_id': self.run_id, 'source_head': HEAD,
            'stable_character_intent': {'historical_id': 1128,
                'bookmark_character_name_key': 'bookmark_rags_to_riches_duke_robert'},
            'pid': 101, 'process_creation_filetime_100ns': 202,
            'connection_generation': 303, 'actual_runtime_character_full_id': 404,
            'episode_run_id': 'unit-only-no-game'})
        self.request_helper = self.put(self.assets / 'request_helper.py', '# unused; injected transport\n')
        self.next_adapter = self.put(self.assets / 'next_adapter.py', '# unit-only policy stand-in\n')
        self.plan = self.put(self.assets / 'plan.json', {'build': {'source_head': HEAD}})
        # Same required producer file set, with tiny unit fixtures. No large
        # native source, save or EXE body is read or copied by this regression.
        template = ROOT.load(RELAY_PATH.with_name('MODULES.pins.json'))
        files = {}
        for relative in template['repository_files']:
            item = self.put(self.repo / relative, 'unit fixture for ' + relative + '\n')
            files[relative] = ROOT.pin(item)['sha256']
        self.pins = self.put(self.assets / 'module-pins.json', {
            'source_head': HEAD, 'repository_files': files,
            'split_consumer_sha256': ROOT.pin(RELAY_PATH.with_name('army_split_transfer_assertions_12004.py'))['sha256']})
        self.argv = ['baseline', '--repo', str(self.repo), '--context', str(self.context),
            '--runtime-proof', str(self.proof), '--request-helper', str(self.request_helper),
            '--root-relay', str(RELAY_PATH), '--next-adapter', str(self.next_adapter),
            '--plan', str(self.plan), '--evidence-root', str(self.assets),
            '--run-id', self.run_id, '--case-id', 'Bbinding', '--attempt', 'first', '--army-id', '93']
        for name, path in (('self', Path(B.__file__)), ('context', self.context),
                           ('runtime-proof', self.proof), ('request-helper', self.request_helper),
                           ('root-relay', RELAY_PATH), ('next-adapter', self.next_adapter), ('plan', self.plan)):
            self.argv += ['--' + name + '-sha256', ROOT.pin(path)['sha256']]
        self.explicit = ['--source-head', HEAD, '--run-sequence', '188',
                         '--module-pins', str(self.pins), '--module-pins-sha256', ROOT.pin(self.pins)['sha256']]
        self.evidence_options = []
        def evidence(path, **options):
            self.evidence_options.append(options)
            return object()
        self.adapter = SimpleNamespace(b=SimpleNamespace(recipe=lambda plan, evidence: None,
            c=SimpleNamespace(Evidence=evidence,
                runtime_total_budget=lambda options, **binding: SimpleNamespace(
                    bind_live=lambda live, **limits: None))))
        self.transport = SimpleNamespace(RUN=self.run, ASSETS=self.assets, CONTEXT=ROOT.load(self.context))
        self.real_relay = ROOT.Relay
        self.seen = []

    @staticmethod
    def put(path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value) if not isinstance(value, str) else value, encoding='utf-8')
        return path

    def relay(self, args):
        self.seen.append(deepcopy(args))
        return self.real_relay(args, transport=self.transport, process_probe=lambda pid: 202)

    def invoke(self, extra):
        owner = self

        class NoActionStage:
            def __init__(self, root, live, adapter, plan, **kwargs):
                self.live = live

            def run(self, stage):
                return ROOT.write_new(self.live.attempt / 'binding-unit-result.json', {
                    'status': 'BINDING_ONLY_NO_GAME_QUALIFICATION', 'source_head': self.live.source,
                    'sequence': self.live.sequence, 'binding': self.live.binding,
                    'module_pins': self.live.meta['module_pins']})

        def reviewed(path, name, expected):
            owner.assertEqual(ROOT.pin(path)['sha256'], expected)
            return ROOT if Path(path) == RELAY_PATH else owner.adapter

        with patch.object(B, 'reviewed_module', side_effect=reviewed), \
             patch.object(B, 'BStages', NoActionStage), \
             patch.object(ROOT, 'Relay', side_effect=self.relay), \
             patch.object(ROOT.subprocess, 'check_output', return_value=HEAD + '\n'):
            return B.main(self.argv + extra)

    def test_historical_defaults_still_reject_c499(self):
        self.assertEqual(ROOT.SOURCE, 'dcda9fde1afa1effb75d46fe99bba4bcd9aeabcb')
        with self.assertRaisesRegex(RuntimeError, 'reviewed actual checkout changed'):
            self.invoke([])
        self.assertFalse(hasattr(self.seen[0], 'source_head'))
        self.assertFalse((self.assets / 'r09-split-merge-relay-a01').exists())

    def test_explicit_c499_bindings_reach_actual_relay_admission(self):
        self.assertEqual(self.invoke(self.explicit), 0)
        self.assertEqual(self.evidence_options[0]['max_file_bytes'], 16 * 1024**2)
        self.assertEqual(self.evidence_options[0]['capacity_admissions'], [])
        self.assertEqual(self.evidence_options[0]['expected_source_head'], HEAD)
        self.assertEqual(self.evidence_options[0]['expected_machine_ids'], {ROOT.MACHINE})
        args = self.seen[0]
        self.assertEqual((args.source_head, args.run_sequence), (HEAD, 188))
        self.assertEqual(args.module_pins, self.pins)
        self.assertEqual(args.module_pins_sha256, ROOT.pin(self.pins)['sha256'])
        self.assertEqual(args.context_sha256, ROOT.pin(self.context)['sha256'])
        self.assertEqual(args.runtime_proof_sha256, ROOT.pin(self.proof)['sha256'])
        result = ROOT.load(self.assets / 'r09-split-merge-relay-a01/Bbinding/first/binding-unit-result.json')
        self.assertEqual(result['binding'], {'pid': 101, 'process_create_time_100ns': 202,
            'generation': 303, 'actor': 404, 'episode': 'unit-only-no-game'})
        self.assertEqual(result['source_head'], HEAD)
        self.assertEqual(result['module_pins'], ROOT.pin(self.pins))

    def test_partial_new_binding_is_rejected_before_relay(self):
        for index in range(0, len(self.explicit), 2):
            with self.subTest(missing=self.explicit[index]):
                partial = self.explicit[:index] + self.explicit[index + 2:]
                with self.assertRaisesRegex(RuntimeError, 'requires source-head, run-sequence, module-pins and module-pins-sha256 together'):
                    self.invoke(partial)
        self.assertEqual(self.seen, [])
        self.assertFalse((self.assets / 'r09-split-merge-relay-a01').exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
