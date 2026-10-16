"""B production CLI wiring and existing Relay guard; no native requests."""
from datetime import datetime, timezone
from pathlib import Path
import io
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import strategy_b_stages as B
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'split_merge'))
import root_relay as R


class Tests(unittest.TestCase):
 def test_real_cli_budget_precedes_relay_then_binds_before_stage_and_partial_refuses(self):
  events=[]; calls=[]; live=SimpleNamespace()
  def factory(options,**kwargs):
   calls.append((dict(options),kwargs));events.append('factory')
   return SimpleNamespace(bind_live=lambda obj,**kw:events.append(('bind',obj,kw)))
  root=SimpleNamespace(MACHINE=R.MACHINE,DEADLINE=R.DEADLINE,
   pin=lambda path:{'path':str(path),'sha256':'a'*64},
   load=lambda path:{'build':{'source_head':'b'*40}} if str(path).endswith('plan.json') else {'status':'UNIT_BINDING_ONLY'},
   Relay=lambda args:(events.append('Relay') or live))
  adapter=SimpleNamespace(b=SimpleNamespace(c=SimpleNamespace(Evidence=lambda *a,**kw:object(),runtime_total_budget=factory),recipe=lambda *a:None))
  class Stage:
   def __init__(self,*args,**kwargs):events.append('stage')
   def run(self,stage):return {'path':'unit-result'}
  argv=['route','--repo','unitrepo','--context','unit-scene/context.json','--runtime-proof','runtime.json',
   '--request-helper','request.py','--root-relay','relay.py','--next-adapter','next.py','--plan','plan.json',
   '--evidence-root','evidence','--run-id','unit','--case-id','unit','--attempt','unit','--army-id','93']
  for key in ('self','context','runtime-proof','request-helper','root-relay','next-adapter','plan'):
   argv+=['--'+key+'-sha256','a'*64]
  with patch.object(B,'reviewed_module',side_effect=lambda path,*args:root if str(path)=='relay.py' else adapter),patch.object(B,'BStages',Stage),patch('sys.stdout',new=io.StringIO()):
   for extra,total,admit,rawmax in [([],512*1024*1024,None,16*1024*1024),
     (['--max-runtime-total-bytes','805306368','--runtime-capacity-admission','actual-capacity.json','c'*64,'--max-evidence-file-bytes','33554432'],805306368,['actual-capacity.json','c'*64],33554432)]:
    events.clear();self.assertEqual(B.main(argv+extra),0)
    options,kwargs=calls[-1]
    self.assertEqual(options['max_runtime_total_bytes'],total)
    self.assertEqual(options['runtime_capacity_admission'],admit)
    self.assertEqual(kwargs,{'scene_root':Path('unit-scene/context.json').resolve().parent,'source_head':'b'*40,'machine_id':R.MACHINE,'deadline_utc':R.DEADLINE})
    self.assertEqual(events,['factory','Relay',('bind',live,{'raw_file_max':rawmax}),'stage'])
   before=len(calls)
   with patch('sys.stderr',new=io.StringIO()),self.assertRaises(SystemExit):
    B.main(argv+['--runtime-capacity-admission','missing-sha.json'])
   self.assertEqual(len(calls),before)

 def test_actual_relay_guard_keeps_legacy_default_and_honors_bound_limit(self):
  class ReachedTransport(Exception):pass
  with tempfile.TemporaryDirectory(dir=getattr(sys,'_B_budget_scratch',None)) as temp:
   root=Path(temp);run=root/'run';case=root/'case'
   (run/'requests').mkdir(parents=True);(run/'responses').mkdir();case.mkdir()
   live=R.Relay.__new__(R.Relay)
   live.a=SimpleNamespace(attempt='budget');live.serial=0;live.run=run;live.case=case
   live.check_process=lambda:None
   live.transport=SimpleNamespace(request=Mock(side_effect=ReachedTransport))
   with patch.object(R,'MAX_PACKET',512*1024*1024),patch.object(R,'datetime') as clock:
    clock.now.return_value=datetime(2026,10,16,tzinfo=timezone.utc)
    clock.fromisoformat.side_effect=datetime.fromisoformat
    with self.assertRaisesRegex(RuntimeError,'admitted run/relay budget'):
     live.request('default','unit-no-native',{})
    live.transport.request.assert_not_called()
    live.runtime_total_budget_bytes=768*1024*1024
    with self.assertRaises(ReachedTransport):live.request('bound','unit-no-native',{})
    live.transport.request.assert_called_once()

if __name__=='__main__':unittest.main(verbosity=2)
