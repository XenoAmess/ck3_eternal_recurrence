"""SOURCE_ONLY guard regression using preserved R14 context subsets.

This model checks authored effect conditions and value reads. It does not emulate
CK3's tooltip renderer and cannot award native preview or business acceptance.
"""
from pathlib import Path
import argparse, hashlib, importlib.util, json, sys, unittest

SOURCE=Path(__file__).resolve().parents[1]
FIELDS=('lyd_i3b_serial','lyd_i3b_nonce','lyd_i3b_phase')
HELPER='lyd_i3b_bind_event_effect'

class UndefinedRead(Exception):pass

def definition(tree,name):return next(e.value for e in tree.entries if e.key==name)

def evaluate_effect(block,values):
    saved={};reads=[]
    def run(body):
        for e in body.entries:
            if e.key=='save_scope_as':saved[e.value]='actual_actor'
            elif e.key=='if':
                limit=e.value.entries[0]
                assert limit.key=='limit'
                assert all(c.key=='has_variable' for c in limit.value.entries)
                if all(c.value in values for c in limit.value.entries):run(Block(e.value.entries[1:]))
            elif e.key=='save_scope_value_as':
                parts={x.key:x.value for x in e.value.entries}
                assert parts['value'].startswith('var:')
                var=parts['value'][4:]
                if var not in values:raise UndefinedRead(var)
                reads.append(var);saved[parts['name']]=values[var]
            else:raise AssertionError('Model does not handle '+str(e.key))
    run(block);return saved,reads

class ActualContextContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture=json.loads((SOURCE/'tools/fixtures/i3b_event_bind_actual_r14.json').read_bytes())
        cls.contexts={x['name']:x for x in cls.fixture['contexts']}
        cls.actual=parse_clausewitz((SOURCE/'common/scripted_effects/lyd_i3b_setup_effects.txt').read_text('utf-8-sig'))
        cls.new=definition(cls.actual,HELPER)
        cls.old=parse_clausewitz(cls.fixture['baseline_helper_text']).entries[0].value
    def test_actual_prebegin_old_undefined_candidate_skips_numeric_binding(self):
        c=self.contexts['B0-before-first-begin'];self.assertEqual(c['missing_fields'],list(FIELDS))
        with self.assertRaisesRegex(UndefinedRead,'^lyd_i3b_serial$'):evaluate_effect(self.old,c['values'])
        self.assertEqual(evaluate_effect(self.new,c['values']),({'lyd_i3b_actor':'actual_actor'},[]))
    def test_actual_cancel_old_phase_undefined_candidate_skips_atomic_binding(self):
        c=self.contexts['round1-cancel-before-second-begin'];self.assertEqual(c['missing_fields'],['lyd_i3b_phase'])
        with self.assertRaisesRegex(UndefinedRead,'^lyd_i3b_phase$'):evaluate_effect(self.old,c['values'])
        self.assertEqual(evaluate_effect(self.new,c['values']),({'lyd_i3b_actor':'actual_actor'},[]))
    def test_actual_first_live_round_preserves_numeric_context(self):
        c=self.contexts['round1-B1-actual-live'];self.assertEqual(c['missing_fields'],[])
        self.assertEqual(evaluate_effect(self.new,c['values']),evaluate_effect(self.old,c['values']))
        self.assertEqual(evaluate_effect(self.new,c['values'])[1],list(FIELDS))
    def test_actual_second_live_round_preserves_numeric_context(self):
        c=self.contexts['round2-B1-actual-live'];self.assertEqual(c['missing_fields'],[])
        self.assertEqual(evaluate_effect(self.new,c['values']),evaluate_effect(self.old,c['values']))
        self.assertEqual(evaluate_effect(self.new,c['values'])[1],list(FIELDS))
    def test_exact_guard_and_all_original_business_AST_preserved(self):
        self.assertEqual(len(self.new.entries),2)
        guarded=self.new.entries[1];self.assertEqual(guarded.key,'if')
        limit=guarded.value.entries[0];self.assertEqual(limit.key,'limit')
        self.assertEqual([(e.key,e.operator,e.value) for e in limit.value.entries],[('has_variable','=',f) for f in FIELDS])
        projected=Block((self.new.entries[0],)+guarded.value.entries[1:])
        self.assertEqual(projected,self.old)
        original=Block(tuple(Entry(e.key,e.operator,projected if e.key==HELPER else e.value) for e in self.actual.entries))
        self.assertEqual(hashlib.sha256(repr(original).encode('utf-8')).hexdigest(),self.fixture['baseline_complete_setup_AST_sha256'])
    def test_generator_owns_exact_candidate_setup_bytes(self):
        sys.path.insert(0,str(SOURCE/'tools'))
        spec=importlib.util.spec_from_file_location('candidate_institution_present_test',SOURCE/'tools/gen_institution.py')
        gen=importlib.util.module_from_spec(spec);spec.loader.exec_module(gen)
        sys.path.insert(0,str(CATALOGUE.parent))
        catalogue_spec=importlib.util.spec_from_file_location('actual_catalogue_for_event_bind_test',CATALOGUE)
        catalogue=importlib.util.module_from_spec(catalogue_spec);sys.modules[catalogue_spec.name]=catalogue;catalogue_spec.loader.exec_module(catalogue)
        outputs=gen.build_outputs(catalogue)
        self.assertEqual(outputs['common/scripted_effects/lyd_i3b_setup_effects.txt'],(SOURCE/'common/scripted_effects/lyd_i3b_setup_effects.txt').read_bytes())

def main():
    global SOURCE,Block,Entry,parse_clausewitz,CATALOGUE
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-root',type=Path,default=SOURCE)
    p.add_argument('--parser-root',type=Path)
    p.add_argument('--catalogue',type=Path)
    p.add_argument('--report',type=Path,required=True)
    a=p.parse_args();SOURCE=a.source_root.resolve()
    parser_root=(a.parser_root or SOURCE.parent/'tools').resolve()
    CATALOGUE=(a.catalogue or SOURCE/'tools/content_data.py').resolve()
    spec=importlib.util.spec_from_file_location('actual_frozen_clausewitz_parser',parser_root/'extract_auto_upgrade_buildings.py')
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    Block,Entry,parse_clausewitz=module.Block,module.Entry,module.parse_clausewitz
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(ActualContextContract)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    report={'schema':'lyd.i3b.actual-context-present-guard-offline-test.v1','status':'PASS_SOURCE_ONLY' if result.wasSuccessful() else 'FAIL_SOURCE_ONLY',
      'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),
      'parser':{'path':str(parser_root/'extract_auto_upgrade_buildings.py'),'sha256':hashlib.sha256((parser_root/'extract_auto_upgrade_buildings.py').read_bytes()).hexdigest()},
      'candidate_source_root':str(SOURCE),'fixtures':'Preserved actual R14 parsed context subsets; no fresh savebody read.',
      'old_undefined_read_mutants':['actual B0 missing serial','actual cancellation missing phase'],
      'engine_effect_if_preview_semantics':'UNPROVEN_NEXT_COLD_REQUIRED','live_preview_pass':None,'new_native_or_business_credit':None,'old_preview_test_rerun':False}
    if a.report.exists():raise FileExistsError(a.report)
    a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2));return 0 if result.wasSuccessful() else 1
if __name__=='__main__':raise SystemExit(main())
