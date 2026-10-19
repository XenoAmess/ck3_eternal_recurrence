"""Source-bound C6 -> new-Game display qualification; no real process or RPC."""
from __future__ import annotations
import argparse,ast,contextlib,hashlib,io,json,shutil,sys,tempfile,unittest
from pathlib import Path
from types import ModuleType,SimpleNamespace
from unittest.mock import patch
from prepare_new_game_text_generation_v1 import emit,PINS

SOURCE=None
MACHINE=None


class GenerationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='new-Game-display-software-')
        self.root=Path(self.temp.name);self.target=self.root/'target';self.output=self.root/'review'
    def tearDown(self):self.temp.cleanup()
    def produce(self):
        return emit(SOURCE,self.target,self.output,generation='C91',machine_id=MACHINE)

    def test_current_provider_layout_retry_ordinal_and_capture_bytes_preserved(self):
        result=self.produce()
        for name in PINS:
            if name.startswith('presentation-c6/'):
                new='presentation-c91'+name[len('presentation-c6'):]
                self.assertEqual((self.output/new).read_bytes(),(SOURCE/name).read_bytes())
        for ref in result['files']:
            raw=(self.output/ref['relative_path']).read_bytes()
            self.assertEqual(len(raw),ref['bytes'])
            self.assertEqual(hashlib.sha256(raw).hexdigest(),ref['sha256'])
            if ref['relative_path'].endswith('.py'):compile(raw,ref['relative_path'],'exec')
        api=(self.output/'root_decision_text_api_c91.py').read_text(encoding='utf-8')
        self.assertNotIn('presentation-c6/',api)
        self.assertIn("getattr(api,'SHARED_IO_RETRY_VERSION',None)==1",api)
        self.assertIn('Foreign cached decision provider',api)
        feed=(self.output/'root_p37c91_compact_decision_feed.py').read_text(encoding='utf-8')
        self.assertIn("context['tool']!='ck3_auto_turn'",feed)
        self.assertIn('api.publish_callback_observation',feed)
        self.assertIn('ROOT-ACTUAL-GAME-LAUNCH-C91.json',feed)
        for name in ('root_p37c91_overlay_relay.py','root_p37c91_compact_decision_feed.py','root_continuous_segment_auto_c91.py','p51_decision_text_shutdown_c91.py'):
            tree=ast.parse((self.output/name).read_bytes())
            imports=[n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
            self.assertIn('root_decision_text_api_c91',imports)
            self.assertNotIn('root_decision_text_api_c6',imports)
        provider=json.loads((self.output/'ROOT-DECISION-TEXT-PROVIDER-C91.json').read_bytes())
        for name,ref in provider['sources'].items():
            self.assertEqual(Path(ref['path']),self.target/'presentation-c91/g2_saved_campaign'/(name+'.py'))
        self.assertFalse((SOURCE/'ROOT-DECISION-TEXT-PROVIDER-C91.json').exists())

    def test_output_existing_namespace_and_changed_source_fail_before_write(self):
        self.produce()
        with self.assertRaisesRegex(ValueError,'new external review'):
            self.produce()
        for gen in ('C6','../C11','c11'):
            output=self.root/('reject-'+str(len(gen)))
            with self.assertRaisesRegex(ValueError,'explicit unused generation'):
                emit(SOURCE,self.target,output,generation=gen,machine_id=MACHINE)
            self.assertFalse(output.exists())
        original=Path.read_bytes
        def corrupt(path):
            return b'changed source' if path==SOURCE/'root_decision_text_api_c6.py' else original(path)
        with patch.object(Path,'read_bytes',corrupt),self.assertRaisesRegex(ValueError,'frozen C6 source differs'):
            emit(SOURCE,self.target,self.root/'bad-review',generation='C92',machine_id=MACHINE)
        self.assertFalse((self.root/'bad-review').exists())

    def owner_fixture(self):
        result=self.produce();shutil.copytree(self.output,self.target)
        path=self.target/'presentation-c91/start_new_game_display.py'
        env={'__file__':str(path),'__name__':'_software_new_Game_owner'}
        exec(compile(path.read_bytes(),str(path),'exec'),env)
        spec=env['SPEC'];records=self.root/'records';records.mkdir()
        def metadata(pid,birth):
            (self.target/spec['launch']).write_text(json.dumps({'pid':pid,'creation_filetime':birth,'creation_date':'software-new-birth'}))
            (self.target/spec['placement']).write_text(json.dumps({'pid':pid,'creation_filetime':birth,
                'status':'GREEN','foreground_unchanged':True,'current_desktop_unchanged':True,
                'hwnd':301,'target_desktop_id':'software-desktop'}))
            (self.target/spec['profile']).write_text(json.dumps({'continuous':True,'recording_root':str(records)}))
        metadata(101,999)
        args=['owner','--game-launch',str(self.target/spec['launch']),'--placement',str(self.target/spec['placement']),
            '--obs-profile',str(self.target/spec['profile']),'--current-request',str(self.target/'CURRENT-REQUEST-P37.json'),
            '--job-root',str(records),'--ffprobe',str(self.root/'software-ffprobe'),'--game-pid','101','--game-birth','999']
        return env,spec,args,metadata

    def test_owner_new_tuple_then_publisher_then_new_UUID_no_pixels_claimed(self):
        env,spec,args,_=self.owner_fixture();events=[];holder={}
        def atomic(path,value,new=False):
            if new and path.exists():raise FileExistsError(path)
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(json.dumps(value))
        class FakeOwner:
            process=None
            def __init__(self,path):self.path=path
            def start(self):
                config=json.loads(self.path.read_text());self.assert_config=config
                assert config['game']['pid']==101 and config['game']['creation_filetime']==999
                assert config['state_root'].endswith('decision-text-publisher-c91')
                events.append('publisher_start');self.process=SimpleNamespace(wait=lambda:events.append('retained_wait'))
                self.ref={'path':str(Path(config['state_root'])/'STARTED.json')};atomic(Path(self.ref['path']),{'software':True},new=True)
                holder['ref']=self.ref
            def started(self):return self.ref
            def seal_binding(self,path):events.append('binding');atomic(path,{'software':True},new=True)
            def close(self):events.append('retained_close');return {'normal':True,'software_only':True}
        api=SimpleNamespace(SCHEMA='software-config',process_identity=lambda pid:{'creation_filetime':999},
            pin=lambda path:{'path':str(path)},atomic=atomic,PublisherOwner=FakeOwner)
        module=ModuleType(spec['api_module']);module.load_api=lambda root:api
        module.started_reference=lambda root,value:holder['ref']
        def recording(profile,root,pid,hwnd,old_overlay,**kw):
            assert pid==101 and hwnd==301 and old_overlay is None
            assert kw['decision_publisher_receipt']==Path(holder['ref']['path'])
            events.append('new_UUID_recording');return {'session_id':'software-new-UUID','root':str(root/'software-new-UUID')}
        provider=ModuleType('hotfix_provider')
        provider.capture=SimpleNamespace(decision_publisher_api=lambda:api,launch_recording=recording)
        with patch.dict(sys.modules,{spec['api_module']:module,'hotfix_provider':provider}),patch.object(sys,'argv',args),patch.object(sys,'path',list(sys.path)),contextlib.redirect_stdout(io.StringIO()) as output:
            env['main']()
        self.assertEqual(events,['publisher_start','binding','new_UUID_recording','retained_wait','retained_close'])
        report=json.loads(output.getvalue().splitlines()[0]);self.assertFalse(report['pixel_admitted'])
        request=json.loads((self.target/spec['requested']).read_text())
        self.assertFalse(request['map_ready_claimed']);self.assertEqual(request['capture_admission_stage'],'saved_map')
        self.assertEqual(request['generation'],'C91')

    def test_wrong_tuple_old_Game_and_existing_outputs_never_start_owner(self):
        env,spec,args,metadata=self.owner_fixture()
        with patch.object(sys,'argv',args):
            metadata(102,999)
            with self.assertRaisesRegex(ValueError,'actual new Game/placement tuple differs'):env['main']()
            previous=spec['previous_Game_tuple'];metadata(*previous)
            oldargs=args.copy();oldargs[oldargs.index('--game-pid')+1]=str(previous[0]);oldargs[oldargs.index('--game-birth')+1]=str(previous[1])
            with patch.object(sys,'argv',oldargs),self.assertRaisesRegex(ValueError,'old C6 hot identity'):env['main']()
            metadata(101,999);(self.target/spec['state']).mkdir()
            with self.assertRaisesRegex(ValueError,'new generation outputs required'):env['main']()


def main():
    global SOURCE,MACHINE
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-runtime',type=Path,required=True);parser.add_argument('--machine-id',required=True)
    args=parser.parse_args();SOURCE=args.source_runtime.resolve(strict=True);MACHINE=args.machine_id
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(GenerationTests))
    raise SystemExit(0 if result.wasSuccessful() else 1)


if __name__=='__main__':main()
