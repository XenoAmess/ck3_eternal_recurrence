"""Portable focused retirement tests; no third-party test or desktop dependency."""
from contextlib import nullcontext
import ctypes
import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]

def load(name,relative):
    spec=importlib.util.spec_from_file_location(name,ROOT/relative)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class FakeWindowAPI:
    def __init__(self,classes):self.classes=classes
    def EnumWindows(self,callback,context):
        for hwnd in self.classes:
            if callback(hwnd,context)is not True:raise AssertionError('Enumeration unexpectedly stopped')
    def GetClassName(self,hwnd):return self.classes[hwnd]

class LegacyBluePanelRetirementTests(unittest.TestCase):
    def test_constructor_rejects_before_any_Win32_creation(self):
        module=load('retired_blue_window','tools/g2_saved_campaign/decision_overlay_window.py')
        with patch.object(ctypes,'WinDLL',create=True,side_effect=AssertionError('No Win32 allowed'))as api:
            with self.assertRaisesRegex(RuntimeError,'Legacy blue decision overlay is retired'):
                module.NativeOverlay()
            api.assert_not_called()

    def test_retired_cli_never_reads_a_session_or_launches_window(self):
        module=load('retired_blue_cli','tools/g2_saved_campaign/live_decision_overlay.py')
        with patch.object(module.Path,'read_text',side_effect=AssertionError('No session read allowed')):
            with patch.object(ctypes,'WinDLL',create=True,side_effect=AssertionError('No Win32 allowed'))as api:
                with self.assertRaisesRegex(SystemExit,'Legacy blue decision overlay is retired'):
                    module.main()
                api.assert_not_called()

    def test_exact_old_class_includes_hidden_owner_and_preserves_new_UI(self):
        module=load('recorder_blue_fingerprint','tools/ck3_mod_acceptance_recorder.py')
        windows=FakeWindowAPI({11:'XARG2DecisionOverlay_37',12:'CurrentDecisionUI_37',
            13:'XARG2DecisionOverlay_v2_37',14:'XARG2DecisionOverlay_37V2',15:'CrusaderKingsIII',
            16:'XARG2DecisionOverlay_0',17:'XARG2DecisionOverlay_１２'})
        self.assertEqual(module.legacy_blue_overlay_windows(windows),[
            {'hwnd':11,'class_name':'XARG2DecisionOverlay_37'}])

    def test_old_panel_rejects_before_output_geometry_and_recorder_job(self):
        module=load('recorder_blue_start','tools/ck3_mod_acceptance_recorder.py')
        with TemporaryDirectory()as temporary:
            root=Path(temporary);output=root/'new-take'
            recorder=module.BoundedScreenRecorder(root=root,output=output,
                keeper=SimpleNamespace(process_create_gate=lambda:nullcontext()),
                ffmpeg=root/'ffmpeg.exe',ffprobe=root/'ffprobe.exe',machine_id='synthetic-machine',
                admission_receipt=root/'admission.json')
            with patch.object(module.subprocess,'check_output',return_value='synthetic-machine\n'):
                with patch.object(module,'legacy_blue_overlay_windows',return_value=[
                    {'hwnd':11,'class_name':'XARG2DecisionOverlay_37'}]):
                    with patch.object(module.importlib.util,'spec_from_file_location',
                            side_effect=AssertionError('RecorderJob must not load')):
                        with self.assertRaisesRegex(RuntimeError,'Retired legacy blue decision panel is still present'):
                            recorder.start()
            self.assertFalse(output.exists())
            self.assertIsNone(recorder.recorder)
            self.assertEqual(recorder.streams,[])

    def test_recording_default_does_not_start_or_mount_the_old_panel(self):
        module=load('recorder_blue_default','tools/ck3_mod_acceptance_recorder.py')
        with patch.object(module,'legacy_blue_overlay_windows',return_value=[]):
            observed=module.require_no_legacy_blue_overlay()
        self.assertIs(observed['legacy_blue_overlay_retired'],True)
        self.assertEqual(observed['legacy_window_count_at_start'],0)
        self.assertIs(observed['starts_or_mounts_decision_overlay'],False)

    def test_service_can_retry_after_owner_closes_panel_without_a_game_restart(self):
        module=load('recorder_blue_service_retry','tools/ck3_mod_acceptance_recorder.py')
        with TemporaryDirectory()as temporary:
            root=Path(temporary)
            service=module.ScreenCaptureService.__new__(module.ScreenCaptureService)
            service._live=lambda unused:(root,{})
            service.recorder=None;service.capture_names=set();service.completed_takes=[]
            request={'schema':'ck3-mod-acceptance-recorder-request-v1','id':'first',
                'operation':'start','live_root':str(root),'capture_name':'fresh'}
            with patch.object(module,'legacy_blue_overlay_windows',return_value=[
                    {'hwnd':11,'class_name':'XARG2DecisionOverlay_37'}]):
                with self.assertRaisesRegex(RuntimeError,'Retired legacy blue decision panel is still present'):
                    service.handle(request)
            self.assertIsNone(service.recorder)
            self.assertEqual(service.capture_names,set())
            service.capture_root=root/'captures';service.repo=root;service.keeper=object()
            service.storage=root/'reservation.json'
            service.storage.write_text('{"reservations":[{"task":"synthetic-capture","peak_bytes":536870912}]}',encoding='utf-8')
            service.ffmpeg=root/'ffmpeg.exe';service.ffprobe=root/'ffprobe.exe'
            service.config={'reservation_task':'synthetic-capture','peak_bytes':536870912,
                'recorder_job':{},'ffmpeg':{},'ffprobe':{},'machine_id':'synthetic-machine',
                'max_seconds':120,'required_size':[2560,1440]}
            service.recorder_factory=lambda **kw:SimpleNamespace(output=kw['output'],terminal=None,
                start=lambda:{'state':'SYNTHETIC_NO_ACTUAL_RECORDING'})
            with patch.object(module,'legacy_blue_overlay_windows',return_value=[]):
                with patch.object(module,'_pin',return_value=root/'synthetic-pin'):
                    result=service.handle({**request,'id':'second'})
            self.assertEqual(result,{'state':'SYNTHETIC_NO_ACTUAL_RECORDING'})
            self.assertEqual(service.capture_names,{'fresh'})

    def test_decision_data_publication_survives_retiring_the_renderer(self):
        module=load('decision_data_publication','tools/g2_saved_campaign/live_decision_overlay.py')
        with TemporaryDirectory()as temporary:
            root=Path(temporary);target=root/'decision.txt'
            evidence=module.OverlayEvidence(root,99)
            text='现有决策数据仍可发布；不会创建旧蓝窗口。'
            self.assertTrue(module.publish_decision_payload(target,text.encode('utf-8'),evidence))
            self.assertEqual(target.read_text(encoding='utf-8'),text)
            self.assertIsNone(evidence.first_exception)

    def test_readback_formatting_keeps_queued_and_actual_camera_distinct(self):
        module=load('decision_data_formatting','tools/g2_saved_campaign/live_decision_overlay.py')
        camera={'display_mode':'realm','native_actual':{'status':'submitted'}}
        self.assertIn('等待稳定',module.camera_presentation_text(camera))
        camera['native_actual'].update(status='settled',camera_postcondition_verified=True)
        self.assertIn('原生位置已稳定',module.camera_presentation_text(camera))
        self.assertEqual(module.outcome_text({'status':'submitted'}),'已提交，等待读回')

if __name__=='__main__':unittest.main()
