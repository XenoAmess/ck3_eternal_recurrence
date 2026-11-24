"""Only private Saved-entry emission and declared input predicates; no engine emulation."""
from dataclasses import dataclass,field,replace
from pathlib import Path
import codecs,hashlib,importlib.util,json,os,tempfile,unittest
from extract_auto_upgrade_buildings import Block,parse_clausewitz

ROOT=Path(os.environ.get('XAR_AE2_REPO',Path(__file__).resolve().parents[1])).resolve()
SOURCE=Path(os.environ.get('XAR_AE2_PRODUCER_SOURCE',ROOT/'tools/prepare_zg361_ae2_fixture.py'))
spec=importlib.util.spec_from_file_location('ae2_saved_fixture_under_test',SOURCE)
ae2=importlib.util.module_from_spec(spec);spec.loader.exec_module(ae2)
IDENTITY={'game_version':'1.21.0.3','steam_build_id':'26785313','software_test_identity_only':True}
ORIGINAL=ROOT/'tools/fixtures/zg361_ae2_ui_payment'
STARTUP='common/on_action/zga_ae2_on_actions.txt'
GUI='common/scripted_guis/zga_ae2_saved_entry_guis.txt'
BRIDGES={GUI,'gui/zga_ae2_saved_entry_bridge.gui','gui/scripted_widgets/zga_ae2_saved_entry_widgets.txt'}
def child(body,key):
 rows=[e.value for e in body.entries if e.key==key]
 if len(rows)!=1 or not isinstance(rows[0],Block):raise AssertionError((key,rows))
 return rows[0]
def fields(body):return [(e.key,e.value) for e in body.entries]
@dataclass
class Inputs:
 history:str='1128';ai:bool=False;alive:bool=True;landed:bool=True;date:str='1066.9.15'
 rules:set[str]=field(default_factory=lambda:{'zg361_on'})
 flags:set[str]=field(default_factory=set)
def eligible(body,actual):
 for e in body.entries:
  if e.operator!='=':raise AssertionError(e)
  if e.key=='NOT' and isinstance(e.value,Block):ok=not eligible(e.value,actual)
  elif e.key=='this':ok=e.value=='character:'+actual.history
  elif e.key=='is_ai':ok=e.value==('yes' if actual.ai else 'no')
  elif e.key=='is_alive':ok=e.value==('yes' if actual.alive else 'no')
  elif e.key=='is_landed':ok=e.value==('yes' if actual.landed else 'no')
  elif e.key=='current_date':ok=e.value==actual.date
  elif e.key=='has_game_rule':ok=e.value in actual.rules
  elif e.key=='has_character_flag':ok=e.value in actual.flags
  else:raise AssertionError(('Unmodeled entry predicate',e))
  if not ok:return False
 return True
def inventory(root):return {p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()}

class Zg361SavedEntryFixtureTests(unittest.TestCase):
 def setUp(self):
  base=Path(os.environ.get('XAR_AE2_TEST_OUTPUT_ROOT',tempfile.gettempdir())).resolve();base.mkdir(parents=True,exist_ok=True)
  directory=tempfile.TemporaryDirectory(prefix='ae2-fixture-',dir=base);self.root=Path(directory.name).resolve()
  self.assertEqual(self.root.parent,base);self.assertTrue(self.root.name.startswith('ae2-fixture-'))
  self.addCleanup(directory.cleanup)
 def test_default_runtime_files_are_the_complete_original_bytes(self):
  out=self.root/'default';r=ae2.generate(ROOT,out,IDENTITY);expected=inventory(ORIGINAL)
  actual=inventory(out);actual.pop('setup-receipt.json')
  self.assertEqual(len(expected),7);self.assertEqual(actual,expected)
  self.assertFalse(r['saved_entry_bridge']);self.assertIsNone(r['saved_entry']);self.assertFalse(r['business_pass'])
 def test_saved_adds_only_three_bridges_omits_dispatcher_and_preserves_business(self):
  out=self.root/'saved';r=ae2.generate(ROOT,out,IDENTITY,saved_entry_bridge=True)
  before=inventory(ORIGINAL);after=inventory(out);after.pop('setup-receipt.json')
  self.assertEqual(before.keys()-after.keys(),{STARTUP});self.assertEqual(after.keys()-before.keys(),BRIDGES)
  self.assertEqual(len(after),9)
  for name in before.keys()&after.keys():
   if name=='descriptor.mod':
    old=before[name].decode('utf-8-sig');new=after[name].decode('utf-8-sig')
    self.assertEqual(new.replace('supported_version="1.21.0.3"','supported_version="1.20.0.4"'),old)
   else:self.assertEqual(after[name],before[name],name)
  for name in BRIDGES:self.assertTrue(after[name].startswith(codecs.BOM_UTF8))
  self.assertFalse(r['saved_entry']['newgame_dispatcher_mounted']);self.assertEqual(r['maximum_natural_days'],0)
 def test_both_actual_guard_asts_reject_wrong_inputs_or_either_consumed_once(self):
  gui=child(parse_clausewitz(ae2.saved_entry_files()[GUI]),'zga_ae2_saved_entry_gui')
  shown=child(gui,'is_shown');dispatch=child(child(gui,'effect'),'if');executed=child(dispatch,'limit')
  self.assertEqual(shown,executed);self.assertTrue(eligible(shown,Inputs()))
  changed=[replace(Inputs(),history='8052'),replace(Inputs(),ai=True),replace(Inputs(),alive=False),replace(Inputs(),landed=False),replace(Inputs(),date='1066.9.16'),replace(Inputs(),rules=set()),replace(Inputs(),flags={'zga_ae2_saved_entry_dispatched'}),replace(Inputs(),flags={'zga_ae2_setup_attempted'})]
  for actual in changed:self.assertFalse(eligible(shown,actual));self.assertFalse(eligible(executed,actual))
  self.assertEqual([e.key for e in dispatch.entries],['limit','add_character_flag','zga_ae2_prepare_effect'])
  self.assertEqual(fields(dispatch)[1:],[('add_character_flag','zga_ae2_saved_entry_dispatched'),('zga_ae2_prepare_effect','yes')])
  # Source changes between IsShown and Execute cannot bypass the second guard.
  self.assertFalse(eligible(executed,replace(Inputs(),flags={'zga_ae2_saved_entry_dispatched'})))
 def test_original_prepare_once_and_no_presentation_or_payment_in_new_bridge(self):
  original=child(parse_clausewitz((ORIGINAL/'common/scripted_effects/zga_ae2_fixture_effects.txt').read_text(encoding='utf-8-sig')),'zga_ae2_prepare_effect')
  first=child(original,'if');limit=child(first,'limit')
  self.assertEqual(fields(child(limit,'NOT')),[('has_character_flag','zga_ae2_setup_attempted')])
  self.assertEqual(fields(first)[1],('add_character_flag','zga_ae2_setup_attempted'))
  joined='\n'.join(ae2.saved_entry_files().values())
  for forbidden in ('zga_ae2_present_effect','zga_ae2_verify_payment_effect','trigger_event = zg361comp.1','add_treasury','add_gold','zg361_comp_portfolio_apply_stage_effect'):
   self.assertNotIn(forbidden,joined)
  window=parse_clausewitz(ae2.saved_entry_files()['gui/zga_ae2_saved_entry_bridge.gui'])
  self.assertTrue(window.entries);self.assertIn('alwaystransparent = yes',joined)
 def test_nonboolean_or_unbound_saved_engine_identity_refuses_before_output(self):
  for n,value in enumerate((None,0,1,'true')):
   out=self.root/f'bad-bool-{n}'
   with self.assertRaisesRegex(ValueError,'strict boolean'):ae2.generate(ROOT,out,IDENTITY,saved_entry_bridge=value)
   self.assertFalse(out.exists())
  for n,version in enumerate((None,'1.21.*','Florin',121003)):
   out=self.root/f'bad-version-{n}'
   with self.assertRaisesRegex(ValueError,'Exact numeric engine'):ae2.generate(ROOT,out,dict(game_version=version),saved_entry_bridge=True)
   self.assertFalse(out.exists())
 def test_fresh_output_replay_and_repo_output_refuse_without_rewriting(self):
  out=self.root/'once';ae2.generate(ROOT,out,IDENTITY,saved_entry_bridge=True);before=inventory(out)
  with self.assertRaisesRegex(ValueError,'Fresh output'):ae2.generate(ROOT,out,IDENTITY,saved_entry_bridge=True)
  self.assertEqual(inventory(out),before)
  with self.assertRaisesRegex(ValueError,'Fresh output'):ae2.generate(ROOT,ROOT,IDENTITY)
 def test_receipt_runtime_refs_are_complete_exact_unique_and_exclude_receipt(self):
  for saved in (False,True):
   out=self.root/str(saved);r=ae2.generate(ROOT,out,IDENTITY,saved_entry_bridge=saved)
   rows=r['fixture_files'];names=[row['relative_path'] for row in rows]
   self.assertEqual(len(names),len(set(names)));self.assertNotIn('setup-receipt.json',names)
   self.assertEqual(set(inventory(out)),set(names)|{'setup-receipt.json'})
   for row in rows:
    raw=(out/row['relative_path']).read_bytes();self.assertEqual(row['bytes'],len(raw));self.assertEqual(row['sha256'],hashlib.sha256(raw).hexdigest())
   self.assertTrue(r['receipt_excluded_from_runtime_manifest']);self.assertEqual(json.loads((out/'setup-receipt.json').read_bytes()),r)
   self.assertEqual(r['runtime_status'],'NOT_RUN');self.assertFalse(r['business_pass'])

if __name__=='__main__':unittest.main()
