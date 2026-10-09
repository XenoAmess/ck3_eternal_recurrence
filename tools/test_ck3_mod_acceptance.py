"""Focused shared-selection and launch delegation boundaries; never starts CK3."""
from pathlib import Path
import copy
import importlib.util
import json
import sys
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('entry_under_test', Path(__file__).with_name('ck3_mod_acceptance.py'))
entry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(entry)


class SharedEntryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.locations = {name: self.root / name for name in ('repo', 'game', 'userdir', 'artifacts', 'source')}
        for path in self.locations.values(): path.mkdir()
        exe = self.locations['game'] / 'binaries/ck3.exe'
        exe.parent.mkdir(); exe.write_bytes(b'engine-test-only')
        self.host = self.root / 'one_shared_host.py'
        flags = ['--agent-source-root','--game-dir','--bridge-dll','--bridge-injector','--bridge-pipe',
                 '--output','--state-dir','--plan','--control-plan-dir', *entry.BUDGET_FLAGS.values(),
                  *entry.SAVED_FLAGS.values(), '--fixture-profile']
        self.host.write_text("import argparse\np=argparse.ArgumentParser()\n" +
                             ''.join('p.add_argument(' + repr(flag) + ')\n' for flag in flags) +
                             "raise RuntimeError('The host must never execute in these tests')\n")
        self.files = {}
        for key in ('source_index', 'native_source_index', 'dll', 'injector', 'save', 'inventory', 'initial'):
            path = self.root / (key + '.data'); path.write_bytes(b'{}')
            self.files[key] = path
        self.launcher = self.root / 'existing_reviewed_launcher.py'
        self.launcher.write_text("from pathlib import Path\nimport sys\n"
                                 "Path(sys.argv[sys.argv.index('--run-root')+1], 'delegated-only.txt').write_text('called')\n")
        self.paths = {'source_root': self.locations['source'], 'host': self.host,
                      **{key:self.files[key] for key in ('source_index','native_source_index','dll','injector')}}
        def row(key): return {'path_key':key, **{k:v for k,v in entry.pin(self.paths[key]).items() if k != 'path'}}
        self.manifest = {'schema':entry.MANIFEST_SCHEMA, 'source_root':{'path_key':'source_root'},
                         'host':row('host'), 'source_index':row('source_index'),
                         'native_source_index':row('native_source_index'),
                         'native':{'dll':row('dll'),'injector':row('injector')},
                         'game':{'version':'test-only','exe_sha256':entry.pin(exe)['sha256']},
                         'capabilities':{'ck3_take_snapshot':{'source_build_ready':True,'actual_live_qualified':False}}}
        self.manifest_path = self.root / 'manifest.json'; self.write(self.manifest_path, self.manifest)
        self.runtime = {'schema':entry.RUNTIME_SCHEMA, 'manifest':entry.pin(self.manifest_path),
                        'python':sys.executable, 'repo_root':str(self.locations['repo']),
                        'game_dir':str(self.locations['game']), 'userdir_root':str(self.locations['userdir']),
                        'artifacts_root':str(self.locations['artifacts']), 'paths':{k:str(v) for k,v in self.paths.items()},
                        'reviewed_launcher':entry.pin(self.launcher)}
        self.case = {'id':'core','status':'ready','startup':{'mode':'saved_campaign','state_dir':'{run_dir}/state',
                     'saved_campaign':{'save':str(self.files['save']),'bytes':2,
                     'sha256':entry.pin(self.files['save'])['sha256'],'player_id':1,'date_raw':10,
                     'product_inventory':str(self.files['inventory'])}},
                     'initial_plan':str(self.files['initial']), 'required_mcp_tools':['ck3_take_snapshot'],
                     'budgets':dict(command_timeout=300, readiness_timeout=900, timeout=4800,
                                    poll_interval=.05, hold_seconds=1800), 'phases':['original_assertions']}
        self.products = {'schema':entry.PRODUCTS_SCHEMA,'products':{key:{'cases':[copy.deepcopy(self.case)]}
                                                                  for key in ('xqol','reclaim-motherland','tributary-expansion-directives')}}
        self.runtime_path = self.root / 'runtime.json'; self.write(self.runtime_path, self.runtime)
        self.products_path = self.root / 'products.json'; self.write(self.products_path, self.products)

    def write(self, path, value): path.write_text(json.dumps(value), encoding='utf-8')
    def select(self, product='xqol', context=None):
        return entry.Selection(self.runtime_path, self.products_path, product, 'core', context)
    def context(self):
        run = self.locations['artifacts'] / 'actual-allocated-R0001'; run.mkdir()
        context_path = self.root / 'context.json'
        context = {'schema':entry.CONTEXT_SCHEMA,'run_id':run.name,'run_dir':str(run),
                   'keeper_root':str(self.root/'keeper'),'proof':str(self.root/'proof.json'),
                   'challenge':str(self.root/'challenge.json'),'observed_nonce':'test','reviewer':'test'}
        freeze = run / 'frozen-argv.json'
        self.write(freeze,{})
        context['frozen_argv'] = entry.pin(freeze); self.write(context_path, context)
        selected = self.select(context=context_path)
        self.write(freeze, {'run_id':run.name,'argv':selected.argv,'runtime_environment':selected.runtime_environment})
        context['frozen_argv'] = entry.pin(freeze); self.write(context_path,context)
        return context_path, run, freeze, context

    def test_three_products_select_one_host_source_and_native(self):
        selections=[self.select(key) for key in self.products['products']]
        self.assertEqual(len({item.argv[4] for item in selections}),1)
        self.assertEqual(len({item.argv[item.argv.index('--bridge-dll')+1] for item in selections}),1)
        for item in selections:
            result=item.preflight()
            self.assertEqual(result['blockers'],[])
            self.assertEqual(result['business_acceptance'],'NOT_ASSESSED')
            self.assertFalse(result['tool_status']['ck3_take_snapshot']['actual_live_qualified'])

    def test_product_cannot_override_runtime(self):
        original = copy.deepcopy(self.products)
        for location in ('product', 'case'):
            for key in ('host', 'source_root', 'source_index', 'native', 'dll', 'injector', 'engine', 'host_args'):
                with self.subTest(location=location, key=key):
                    self.products = copy.deepcopy(original)
                    target = self.products['products']['xqol']
                    if location == 'case': target = target['cases'][0]
                    target[key] = 'old-special-runtime'
                    self.write(self.products_path, self.products)
                    with self.assertRaisesRegex(ValueError, 'cannot select shared runtime'):
                        self.select()

    def test_all_canonical_products_and_cases_select_the_same_runtime(self):
        repo = Path(__file__).resolve().parents[1]
        canonical = {row['key']: row for row in entry.read_json(repo / 'workshop/products.json')['products']}
        registry_path = repo / 'tools/ck3_mod_acceptance_products.json'
        products = entry.read_json(registry_path)['products']
        self.assertEqual(set(products), set(canonical), 'Every player product must use the shared registry')
        runtime_choices = set()
        for key, product in products.items():
            self.assertEqual(product['workshop_item_id'], canonical[key]['workshop_item_id'])
            self.assertEqual(product['directory'], canonical[key]['directory'])
            self.assertEqual(product['builder'].removeprefix('{repo_root}/'), canonical[key]['builder'])
            self.assertTrue(product['cases'])
            self.assertEqual(len({case['id'] for case in product['cases']}), len(product['cases']))
            for case in product['cases']:
                with self.subTest(product=key, case=case['id']):
                    selected = entry.Selection(self.runtime_path, registry_path, key, case['id'])
                    argv = selected.argv
                    runtime_choices.add(tuple(argv[argv.index(flag) + 1] for flag in
                                              ('--agent-source-root', '--bridge-dll', '--bridge-injector')) + (argv[4],))
        self.assertEqual(len(runtime_choices), 1)

    def test_changed_shared_pin_blocks(self):
        self.host.write_text(self.host.read_text()+'#changed\n')
        self.assertTrue(any('Pinned input changed' in x for x in self.select().preflight()['blockers']))

    def test_unimplemented_host_cli_blocks(self):
        self.host.write_text('p.add_argument("--plan")\n')
        self.assertTrue(any('lacks declared CLI' in x for x in self.select().preflight()['blockers']))

    def test_missing_capability_blocks(self):
        self.products['products']['xqol']['cases'][0]['required_mcp_tools'].append('unimplemented')
        self.write(self.products_path,self.products)
        self.assertTrue(any('no shared build-ready' in x for x in self.select().preflight()['blockers']))

    def test_saved_binding_only_fills_null(self):
        context_path, _, _, context=self.context()
        context['saved_campaign']={'player_id':2}; self.write(context_path,context)
        with self.assertRaisesRegex(ValueError,'declared null'):self.select(context=context_path)

    def test_run_delegates_existing_launcher_without_executing_host(self):
        context_path,run,_,_=self.context()
        result=self.select(context=context_path).run()
        self.assertEqual(result['launcher_exit_code'],0)
        self.assertEqual((run/'delegated-only.txt').read_text(),'called')
        self.assertEqual(result['business_acceptance'],'NOT_ASSESSED')

    def test_frozen_mismatch_refuses_launcher(self):
        context_path,run,freeze,context=self.context()
        value=entry.read_json(freeze);value['argv'][4]='wrong-product-host.py';self.write(freeze,value)
        context['frozen_argv']=entry.pin(freeze);self.write(context_path,context)
        with self.assertRaisesRegex(ValueError,'frozen argv differs'):self.select(context=context_path).run()
        self.assertFalse((run/'delegated-only.txt').exists())

    def test_draft_and_case_pending_stay_blocked(self):
        self.products['products']['xqol']['cases'][0]['status']='blocked'
        self.write(self.products_path,self.products)
        self.assertTrue(any('explicitly blocked' in x for x in self.select().preflight()['blockers']))

    def test_shared_observer_admission_is_identical_for_all_products(self):
        self.manifest['host_features'] = {'succession_title_readonly': True}
        self.write(self.manifest_path, self.manifest)
        for key in self.products['products']:
            self.assertEqual(self.select(key).argv.count('--private-succession-title-readonly'), 1)
        self.products['products']['xqol']['cases'][0]['host_features'] = {'succession_title_readonly': False}
        self.write(self.products_path, self.products)
        with self.assertRaisesRegex(ValueError, 'cannot select shared runtime'):
            self.select()

    def test_unknown_or_coerced_shared_observer_feature_is_rejected(self):
        for features in ({'unreviewed_native_override': True}, {'succession_title_readonly': 1}, []):
            with self.subTest(features=features):
                self.manifest['host_features'] = features
                self.write(self.manifest_path, self.manifest)
                with self.assertRaises(ValueError): self.select()


if __name__ == '__main__': unittest.main(verbosity=2)
