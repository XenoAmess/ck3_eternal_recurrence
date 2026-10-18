"""Provider/gate/recovery source tests. Every OBS/window dependency is substituted."""
import copy
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import decision_text_admission as admission
import automatic_continuity
import decision_text_publisher as publisher
import recording_text_recovery as recovery
import recording_recovery_adapter as historical
from recording_recovery_supervisor import Game, Cleanup, SdkGuard, Attach, Resume

TOOLS=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('new_obs_text_provider_source_test',TOOLS/'ck3_obs_capture.py')
obs=importlib.util.module_from_spec(spec);sys.modules[spec.name]=obs;spec.loader.exec_module(obs)

class ProviderTests(unittest.TestCase):
    def test_cold_loader_uses_exact_sibling_even_with_foreign_search_path(self):
        with TemporaryDirectory() as temp:
            foreign=Path(temp)/'decision_text_publisher.py'
            foreign.write_text("raise AssertionError('Foreign publisher executed')",encoding='utf-8')
            with patch.dict(sys.modules,{'decision_text_publisher':None}), patch.object(sys,'path',[temp]+list(sys.path)):
                actual=obs.decision_publisher_api()
                self.assertEqual(Path(actual.__file__).resolve(),Path(publisher.__file__).resolve())
                self.assertEqual(actual.source_pins(),publisher.source_pins())
                self.assertIs(obs.decision_publisher_api(),actual)

    def test_foreign_cached_publisher_refused_without_loading_or_replacing_it(self):
        foreign=SimpleNamespace(__file__=str(TOOLS/'foreign/decision_text_publisher.py'))
        with patch.dict(sys.modules,{'decision_text_publisher':foreign}):
            with patch.object(obs.importlib.util,'spec_from_file_location',side_effect=AssertionError('No replacement load')):
                with self.assertRaisesRegex(RuntimeError,'Foreign cached'):obs.decision_publisher_api()
            self.assertIs(sys.modules['decision_text_publisher'],foreign)

    def test_retired_window_refusal_precedes_profile_read_and_take_creation(self):
        with TemporaryDirectory() as temp:
            root=Path(temp);take=root/'must-not-exist'
            with patch.object(obs,'require_no_retired_decision_window',side_effect=RuntimeError('retired')):
                with patch.object(obs,'_read',side_effect=AssertionError('No profile/job read')):
                    with self.assertRaisesRegex(RuntimeError,'retired'):
                        obs.launch_recording(root/'profile',take,1,2,None,launch_receipt=root/'launch',ffprobe=root/'ffprobe')
            self.assertFalse(take.exists())

    def test_worker_guard_precedes_job_read_and_OBS_constructor(self):
        with patch.object(obs,'require_no_retired_decision_window',side_effect=RuntimeError('retired')):
            with patch.object(obs,'_read',side_effect=AssertionError('No job read')):
                with self.assertRaisesRegex(RuntimeError,'retired'):obs.run_worker('nonexistent-job')

    def test_old_overlay_receipt_cannot_start_a_new_job(self):
        with patch.object(obs,'require_no_retired_decision_window',return_value={}):
            with patch.object(obs,'_read',side_effect=AssertionError('No profile read')):
                with self.assertRaisesRegex(ValueError,'retired'):
                    obs.launch_recording('profile','output',1,2,None,overlay_receipt=Path('old'),launch_receipt=Path('launch'),ffprobe=Path('ffprobe'))

    def test_old_recovery_entry_refuses_before_legacy_helper_launch(self):
        instance=historical.ActualAdapter.__new__(historical.ActualAdapter)
        with self.assertRaisesRegex(RuntimeError,'retired'):instance.ensure_overlay(None,None,None)

    def fixture(self,root):
        jobroot=root/'recordings/new';jobroot.mkdir(parents=True)
        text=root/'decision.txt';text.write_text('智能体实时决策\n实际文本',encoding='utf-8')
        reference={'path':str(root/'publisher-started.json'),'bytes':10,'sha256':'a'*64}
        bound={'machine_id':'fixture','decision_text_file':str(text)}
        policy={'legacy_blue_overlay_retired':True,'legacy_window_count_at_start':0}
        launch={'pid':1,'creation_filetime':2,'creation_date':'birth','pipe':'fixture-pipe'}
        storage={'status':'ADMITTED','machine_id':'fixture','approved_output_roots':[str(root/'recordings')]}
        (root/'STORAGE-ADMISSION.json').write_text(json.dumps(storage),encoding='utf-8')
        store={'disk_reserve_bytes':1024,'admission_path':str(root/'STORAGE-ADMISSION.json'),
            'admission_sha256':publisher.pin(root/'STORAGE-ADMISSION.json')['sha256'],'approved_output_roots':storage['approved_output_roots']}
        job={'pid':1,'game_creation_filetime':2,'hwnd':3,'desktop_id':'fixture-desktop','launch':launch,'receipt_root':str(jobroot),
            'capture_mode':'game_decision_text','continuous':True,'overlay':None,'session_id':'new','recording_root':str(root/'recordings'),
            'decision_text_publisher_receipt':reference,'decision_text_publisher':bound,'decision_text_file':str(text),
            'decision_display_policy':policy,'storage':store}
        started={'state':'recording','at_utc':'2026-01-01T00:00:00+00:00','game_pid':1,'game_creation_filetime':2,
            'capture_mode':'game_decision_text','decision_source':True,'decision_text_publisher':bound,'decision_display_policy':policy,
            'decision_settings':{'read_from_file':True,'file':str(text)}}
        frame={'at_utc':'2026-01-01T00:00:01+00:00'}
        for key in ('game','scene'):
            path=jobroot/(key+'.png');path.write_bytes(b'synthetic-frame-pin-only-'+key.encode());frame[key]=publisher.pin(path)
        first={'schema':admission.FIRST_SCHEMA,'status':'GREEN','reviewer':'/root','machine_id':'fixture','at_utc':frame['at_utc'],
            'game_pid':1,'game_creation_filetime':2,'game_creation_date':'birth','recorder_session_id':'new','recording_job_root':str(jobroot),
            'publisher_started':reference,'before_selection_game_pixels_reviewed':True,'before_selection_decision_pixels_reviewed':True,
            'decision_text_visible':True,'legacy_blue_window_visible':False,'stage':'frontend','frontend_visible':True,'frame':frame}
        for name,row in (('job.json',job),('started.json',started),('first.json',first)):
            (jobroot/name).write_text(json.dumps(row),encoding='utf-8')
        return jobroot,launch,bound,first

    def verify(self,root,jobroot,launch,bound):
        def read(path,limit=1024*1024):return json.loads(Path(path).read_bytes())
        with patch.object(admission.publisher,'read_text_binding',return_value=bound):
            return admission.verify_segment(root,root,launch,jobroot,jobroot/'first.json',read,
                datetime.fromisoformat,lambda:datetime(2026,1,1,0,0,2,tzinfo=timezone.utc))

    def test_new_gate_requires_actual_new_source_root_pixels_and_machine(self):
        with TemporaryDirectory() as temp:
            root=Path(temp);jobroot,launch,bound,first=self.fixture(root)
            self.assertEqual(self.verify(root,jobroot,launch,bound)[2]['stage'],'frontend')
            for change in ({'reviewer':'automatic_continuity'},{'decision_text_visible':False},{'machine_id':'other'},
                           {'schema':'legacy-overlay-admission'},{'before_selection_decision_pixels_reviewed':False}):
                (jobroot/'first.json').write_text(json.dumps({**first,**change}),encoding='utf-8')
                with self.assertRaises(ValueError):self.verify(root,jobroot,launch,bound)

    def test_gate_rejects_replaced_reviewed_frame_and_terminal_capture(self):
        with TemporaryDirectory() as temp:
            root=Path(temp);jobroot,launch,bound,first=self.fixture(root)
            (jobroot/'capture_closed.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'terminal'):self.verify(root,jobroot,launch,bound)
            (jobroot/'capture_closed.json').unlink();(jobroot/'scene.png').write_bytes(b'replaced')
            with self.assertRaisesRegex(ValueError,'frame changed'):self.verify(root,jobroot,launch,bound)

class RecoveryTests(unittest.TestCase):
    def fake(self):
        game=Game(1,2,'birth','pipe');old=recovery.TextRecorder('old',game,{'pin':'new-publisher'},Path('old'),True,Cleanup('old',True,0,True,0))
        observed=recovery.TextObservation(game,True,old,True,SdkGuard(True,'RecordingPaused','full_loop','auto_verified',True))
        calls=[]
        segment=SimpleNamespace(session_id='new');frame=SimpleNamespace(receipt_path=Path('new-first'))
        adapter=SimpleNamespace(observe=lambda:observed,attempt=lambda rid:({},Path('.')),exclusive_controls=lambda:True,
            ensure_publisher=lambda *args:calls.append('publisher') or {'exact':'new'},
            launch_text_segment=lambda *args:calls.append('segment') or segment,
            admit_text_segment=lambda *args:calls.append('pixels') or frame,
            attach_recording_segment=lambda *args:calls.append('attach') or Attach('same_game_recording_segment_attached','old','new',game,0,False),
            resume_recording_pause=lambda *args:calls.append('resume') or Resume('recording_guard_pause_resumed',True,False),
            finish_continuation=lambda:calls.append('settle_original_once') or 'complete')
        return adapter,calls,observed

    def test_text_recovery_preserves_normal_cleanup_then_pixels_before_zero_RPC_attach(self):
        adapter,calls,_=self.fake()
        self.assertEqual(recovery.TextRecoverySupervisor(adapter).drive(),'complete')
        self.assertEqual(calls,['publisher','segment','pixels','attach','resume','settle_original_once'])

    def test_no_attach_or_resume_before_actual_pixels_and_no_replay_allowed(self):
        adapter,calls,observed=self.fake();adapter.admit_text_segment=lambda *args:None
        self.assertEqual(recovery.TextRecoverySupervisor(adapter).drive(),'waiting_actual_new_Game_text_pixels')
        self.assertNotIn('attach',calls)
        adapter,calls,observed=self.fake()
        adapter.attach_recording_segment=lambda *args:Attach('same_game_recording_segment_attached','old','new',observed.game,1,True)
        with self.assertRaisesRegex(ValueError,'zero-RPC'):recovery.TextRecoverySupervisor(adapter).drive()
        self.assertNotIn('resume',calls)

class TextPixelContinuityTests(unittest.TestCase):
    def test_real_synthetic_PNGs_bind_new_source_without_legacy_identity(self):
        from PIL import Image,ImageDraw
        with TemporaryDirectory() as temp:
            root=Path(temp);jobroot=root/'recordings/new';jobroot.mkdir(parents=True)
            text=root/'decision.txt';text.write_text('智能体实时决策\n合成像素资格',encoding='utf-8')
            bound={'machine_id':'fixture','at_utc':'2026-01-01T00:00:00+00:00','decision_text_file':str(text)}
            reference={'path':str(root/'STARTED.json'),'bytes':10,'sha256':'a'*64}
            job={'receipt_root':str(jobroot),'capture_mode':'game_decision_text','overlay':None,'continuous':True,
                'pid':1,'hwnd':3,'game_creation_filetime':2,'desktop_id':'fixture','decision_text_publisher_receipt':reference,
                'decision_text_publisher':bound,'decision_text_file':str(text),'launch':{'creation_date':'birth'},'session_id':'new'}
            started={'state':'recording','at_utc':'2026-01-01T00:00:01+00:00','capture_mode':'game_decision_text','game_pid':1,
                'game_creation_filetime':2,'decision_source':True,'decision_text_publisher':bound,
                'decision_settings':{'read_from_file':True,'file':str(text)}}
            game=Image.new('RGB',(800,450),(80,130,160));scene=game.copy()
            ImageDraw.Draw(scene).rectangle((550,10,790,440),fill=(10,20,30))
            frame={'at_utc':'2026-01-01T00:00:02+00:00','mutable_latest_frame':False}
            for key,image in (('game',game),('scene',scene)):
                path=jobroot/(key+'.png');image.save(path);frame[key]=publisher.pin(path)
            inputs=dict(job=job,started=started,frame=frame,session_root=root,now_utc=datetime(2026,1,1,0,0,3,tzinfo=timezone.utc))
            with patch.object(publisher,'read_text_binding',return_value=bound):
                proof=automatic_continuity.automatic_text_continuity_admission(**inputs)
                self.assertEqual(proof['reviewer'],'automatic_text_continuity')
                self.assertGreater(proof['scene_text_diff_fraction'],.005)
                self.assertNotIn('overlay_pid',proof)
                self.assertFalse(proof['exact_text_draw_ACK_claimed'])
                automatic_continuity.verify_automatic_text_continuity_receipt(receipt=proof,**inputs)
                with self.assertRaises(ValueError):
                    automatic_continuity.automatic_text_continuity_admission(**{**inputs,'job':{**job,'capture_mode':'game_decision'}})
                with self.assertRaisesRegex(ValueError,'stale'):
                    automatic_continuity.automatic_text_continuity_admission(**{**inputs,'now_utc':datetime(2026,1,1,1,tzinfo=timezone.utc)})
                same={**frame,'scene':frame['game']}
                with self.assertRaisesRegex(ValueError,'visible difference'):
                    automatic_continuity.automatic_text_continuity_admission(**{**inputs,'frame':same})

if __name__=='__main__':unittest.main()
