import importlib.util
from pathlib import Path
import tempfile
import unittest
import uuid
import json
from unittest import mock
from types import SimpleNamespace

spec=importlib.util.spec_from_file_location('ck3_obs_capture',Path(__file__).with_name('ck3_obs_capture.py'))
subject=importlib.util.module_from_spec(spec)
spec.loader.exec_module(subject)

class CaptureContractTests(unittest.TestCase):
    def job(self, root):
        return {'schema':subject.SCHEMA,'duration_seconds':45,'pid':123,'hwnd':456,
                'session_id':str(uuid.uuid4()),'recording_root':str(root),'receipt_root':str(root/'session')}

    def test_duration_and_binding_rejected_before_capture(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            for patch in [{'duration_seconds':3600},{'duration_seconds':45.0},{'pid':0},{'hwnd':None},
                          {'schema':'other'},{'receipt_root':str(root.parent/'escaped')},{'session_id':'caller-label'}]:
                with self.subTest(patch=patch),self.assertRaises((ValueError,TypeError)):
                    subject.validate_job({**self.job(root),**patch})
            subject.validate_job(self.job(root))

    def test_profile_is_local_authenticated_and_cannot_replace_user_config(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            exe=root/'obs/bin/64bit/obs64.exe'
            exe.parent.mkdir(parents=True)
            exe.write_bytes(b'fixture')
            profile=root/'profile.json'
            subject.prepare_profile(root/'obs',profile,root/'recordings')
            data=json.loads(profile.read_text(encoding='utf-8'))
            self.assertEqual(data['host'],'127.0.0.1')
            self.assertEqual(data['fps'],60)
            self.assertGreaterEqual(len(data['password']),32)
            original=profile.read_bytes()
            subject.prepare_profile(root/'obs',profile,root/'recordings')
            self.assertEqual(profile.read_bytes(),original)
            with self.assertRaises(FileExistsError):
                subject.prepare_profile(root/'obs',root/'different-profile.json',root/'recordings')

    def test_response_serialization_excludes_sdk_methods(self):
        value=type('Response',(),{'attrs':staticmethod(lambda:['fps_numerator']),
                                 'fps_numerator':60,'unrelated':object()})
        self.assertEqual(subject._response_data(value),{'fps_numerator':60})

    def test_stop_rejects_another_recording_session(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            receipt=root/'session';receipt.mkdir()
            job=self.job(root)
            profile=root/'engine.json'
            profile.write_text(json.dumps({'host':'127.0.0.1','port':4459,'password':'fixture'}))
            job['profile_path']=str(profile)
            (receipt/'job.json').write_text(json.dumps(job))
            client=mock.Mock()
            client.get_profile_parameter.return_value=SimpleNamespace(parameter_value='other-session')
            sdk=SimpleNamespace(ReqClient=mock.Mock(return_value=client))
            with mock.patch.dict('sys.modules',{'obsws_python':sdk}):
                with self.assertRaisesRegex(RuntimeError,'another session'):
                    subject.stop_session_recording(receipt)
            client.stop_record.assert_not_called()
            client.disconnect.assert_called_once()

    def test_reconnection_rechecks_output_ownership(self):
        old=mock.Mock();new=mock.Mock()
        new.get_profile_parameter.return_value=SimpleNamespace(parameter_value='other-session')
        sdk=SimpleNamespace(ReqClient=mock.Mock(return_value=new))
        with mock.patch.dict('sys.modules',{'obsws_python':sdk}):
            with self.assertRaisesRegex(RuntimeError,'ownership changed'):
                subject._reconnect_owned_output({'port':4459,'password':'fixture'},{'session_id':'expected'},old)
        old.disconnect.assert_called_once()
        new.disconnect.assert_called_once()

if __name__=='__main__': unittest.main()
