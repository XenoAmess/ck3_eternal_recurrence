"""One generated owner lifecycle in memory, no process/OBS/Win32 calls."""
import contextlib, hashlib, importlib.util, io, json, os, sys, tempfile, types, unittest
from pathlib import Path
from unittest.mock import patch
from tools.g2_saved_campaign.prepare_new_game_recording_owner_v1 import plan

SOURCE=Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/robert30-v20261019-campaign01/runtime')
MACHINE='xenoamess-full-tower-eb9d2c1186'


class OwnerTests(unittest.TestCase):
    def test_actual_generated_owner_uses_only_patched_worker_and_retains_new_publisher(self):
        with tempfile.TemporaryDirectory(prefix='xar-owner-source-only-') as temporary:
            root=Path(temporary);target=root/'target';output=root/'review'
            values,_,review=plan(SOURCE,target,output,generation='C91',machine_id=MACHINE)
            data={target/name:raw for name,raw in values.items()}
            spec=review['spec'];p=target/'presentation-c91';owner_path=p/'start_new_game_display.py'
            metadata={spec['launch']:{'pid':101,'creation_filetime':999,'creation_date':'software-only'},
                spec['placement']:{'pid':101,'creation_filetime':999,'status':'GREEN','foreground_unchanged':True,
                    'current_desktop_unchanged':True,'hwnd':301,'target_desktop_id':'software-only'},
                spec['profile']:{'continuous':True,'recording_root':str(root/'records')}}
            data.update({target/name:json.dumps(row).encode() for name,row in metadata.items()})
            env={'__name__':'_qualified_owner_only','__file__':str(owner_path)}
            exec(compile(values['presentation-c91/start_new_game_display.py'],str(owner_path),'exec'),env)
            events=[];holder={}
            def atomic(path,value,new=False):
                if new and path in data:raise FileExistsError(path)
                data[path]=json.dumps(value).encode()
            class FakeOwner:
                process=None
                def __init__(self,path):self.path=path
                def start(self):
                    config=json.loads(data[self.path]);assert config['game']['pid']==101
                    assert config['game']['creation_filetime']==999
                    events.append('new_publisher_start')
                    self.process=types.SimpleNamespace(wait=lambda:events.append('original_owner_wait'))
                    holder['reference']={'path':str(target/spec['state']/'STARTED.json')}
                def started(self):return holder['reference']
                def seal_binding(self,path):events.append('new_binding');atomic(path,{},new=True)
                def close(self):events.append('original_owner_close');return {'software_only':True}
            api=types.SimpleNamespace(SCHEMA='software-only',process_identity=lambda pid:{'creation_filetime':999},
                pin=lambda path:{'path':str(path)},atomic=atomic,PublisherOwner=FakeOwner)
            api_module=types.ModuleType(spec['api_module']);api_module.load_api=lambda root:api
            api_module.started_reference=lambda root,value:holder['reference']
            capture=types.ModuleType('_patched_capture_fixture')
            capture.__file__=str(p/'ck3_obs_capture_png_retry_c91.py')
            capture.decision_publisher_api=lambda:api
            def helpers():
                assert 'tools/g2_saved_campaign' in os.environ['PYTHONPATH'].replace('\\','/')
                events.append('parent_child_helper_preflight')
            capture._generation_helpers=helpers
            def recording(*args,**kwargs):
                assert args[2:5]==(101,301,None)
                assert kwargs['decision_publisher_receipt']==Path(holder['reference']['path'])
                events.append('new_patched_capture_UUID');return {'session_id':'software-new-UUID'}
            capture.launch_recording=recording
            def capture_spec(name,path):
                self.assertEqual(Path(path),Path(capture.__file__))
                events.append('actual_patched_capture_import')
                return types.SimpleNamespace(loader=types.SimpleNamespace(exec_module=lambda module:None))
            def child_run(argv,**kwargs):
                self.assertEqual(argv,[sys.executable,str(owner_path),'--child-import-preflight'])
                self.assertEqual(kwargs['env']['PYTHONPATH'],os.environ['PYTHONPATH'])
                self.assertEqual(kwargs['env']['PYTHONDONTWRITEBYTECODE'],'1')
                self.assertEqual(kwargs['cwd'],str(target))
                events.append('same_env_child_preflight')
                return types.SimpleNamespace(returncode=0,stderr=b'',stdout=json.dumps({
                    'status':'ACTUAL_CHILD_ENV_IMPORT_PREFLIGHT_PASS','machine_id':MACHINE,
                    'capture_path':capture.__file__,'capture_sha256':review['actual_capture']['sha256'],
                    'same_interpreter':str(Path(sys.executable).resolve()),'bytecode_disabled':True}).encode())
            args=['owner','--game-launch',str(target/spec['launch']),'--placement',str(target/spec['placement']),
                '--obs-profile',str(target/spec['profile']),'--current-request',str(target/'CURRENT-REQUEST-P37.json'),
                '--job-root',str(root/'records'),'--ffprobe','software-ffprobe','--game-pid','101','--game-birth','999']
            original_read=Path.read_bytes;original_exists=Path.exists
            with patch.object(Path,'read_bytes',lambda path:data[path] if path in data else original_read(path)), \
                 patch.object(Path,'exists',lambda path:path in data if path.is_relative_to(target) else original_exists(path)), \
                 patch.object(Path,'read_text',lambda path,**kw:data[path].decode()), \
                 patch.object(Path,'is_dir',return_value=True), \
                 patch.dict(sys.modules,{spec['api_module']:api_module}), \
                 patch.object(importlib.util,'spec_from_file_location',side_effect=capture_spec), \
                 patch.object(importlib.util,'module_from_spec',return_value=capture), \
                 patch('subprocess.run',side_effect=child_run), \
                 patch.object(sys,'argv',args),patch.object(sys,'path',list(sys.path)),patch.dict(os.environ), \
                 contextlib.redirect_stdout(io.StringIO()) as stdout:
                env['main']()
            self.assertEqual(events,['actual_patched_capture_import','parent_child_helper_preflight',
                'same_env_child_preflight','new_publisher_start','new_binding','new_patched_capture_UUID','original_owner_wait','original_owner_close'])
            row=json.loads(stdout.getvalue().splitlines()[0]);self.assertIs(row['pixel_admitted'],False)
            self.assertIs(json.loads(data[target/spec['requested']])['map_ready_claimed'],False)
            self.assertFalse(target.exists());self.assertFalse(output.exists())


if __name__=='__main__':unittest.main()
