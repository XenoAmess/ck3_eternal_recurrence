"""Bounded publisher I/O on local Windows files; no Game, OBS or SDK process."""
import ctypes
import errno
import hashlib
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import threading
import time
import unittest
from unittest.mock import patch

import decision_text_publisher as pub
from migrate_p51_decision_text_v20261019 import API


def kernel():
    value=ctypes.WinDLL('kernel32',use_last_error=True)
    value.CreateFileW.argtypes=[ctypes.c_wchar_p,ctypes.c_uint32,ctypes.c_uint32,
        ctypes.c_void_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p]
    value.CreateFileW.restype=ctypes.c_void_p
    value.CloseHandle.argtypes=[ctypes.c_void_p];value.CloseHandle.restype=ctypes.c_int
    return value


class SharedIoTests(unittest.TestCase):
    @unittest.skipUnless(os.name=='nt','Actual local Windows sharing test')
    def test_read_retries_real_sharing_violation_then_reads_exact_json(self):
        with TemporaryDirectory() as temporary:
            path=Path(temporary)/'CURRENT-INPUT.json';path.write_text('{"exact":286}')
            k=kernel();handle=k.CreateFileW(str(path),0x80000000,0,None,3,0x80,None)
            self.assertNotIn(handle,(None,ctypes.c_void_p(-1).value))
            original=pub._shared_read_once;failures=[];release=[None]
            def observed(source,limit):
                try:return original(source,limit)
                except OSError as error:
                    failures.append(error.winerror)
                    if release[0] is None:
                        release[0]=threading.Timer(.06,lambda:k.CloseHandle(handle));release[0].start()
                    raise
            try:
                with patch.object(pub,'_shared_read_once',side_effect=observed):
                    self.assertEqual(pub.read(path),{'exact':286})
            finally:
                if release[0] is None:k.CloseHandle(handle)
                else:release[0].join()
            self.assertTrue(failures);self.assertTrue(set(failures)<={5,32,33})

    @unittest.skipUnless(os.name=='nt','Actual local Windows sharing test')
    def test_own_reader_shares_delete_and_closes_before_metadata_replace(self):
        with TemporaryDirectory() as temporary:
            path=Path(temporary)/'CURRENT-INPUT.json';path.write_text('{"version":1}')
            fdopen=os.fdopen;delete_access=[];k=kernel()
            def while_reader_is_open(descriptor,*args,**kwargs):
                handle=k.CreateFileW(str(path),0x10000,7,None,3,0x80,None)
                self.assertNotIn(handle,(None,ctypes.c_void_p(-1).value))
                k.CloseHandle(handle);delete_access.append(True)
                return fdopen(descriptor,*args,**kwargs)
            with patch.object(pub.os,'fdopen',side_effect=while_reader_is_open):
                self.assertEqual(pub.read(path),{'version':1})
            self.assertEqual(delete_access,[True])
            pub.atomic(path,{'version':2})
            self.assertEqual(pub.read(path),{'version':2})

    @unittest.skipUnless(os.name=='nt','Actual local Windows sharing test')
    def test_metadata_replace_retries_same_temp_after_real_reader_releases(self):
        with TemporaryDirectory() as temporary:
            path=Path(temporary)/'CURRENT-INPUT.json';path.write_text('{"version":1}')
            k=kernel();handle=k.CreateFileW(str(path),0x80000000,3,None,3,0x80,None)
            self.assertNotIn(handle,(None,ctypes.c_void_p(-1).value))
            replace=os.replace;attempts=[];failures=[];release=[None]
            def observed(source,destination):
                attempts.append((str(source),Path(source).read_bytes()))
                try:return replace(source,destination)
                except OSError as error:
                    failures.append(error.winerror)
                    if release[0] is None:
                        release[0]=threading.Timer(.06,lambda:k.CloseHandle(handle));release[0].start()
                    raise
            try:
                with patch.object(pub.os,'replace',side_effect=observed):pub.atomic(path,{'version':2})
            finally:
                if release[0] is None:k.CloseHandle(handle)
                else:release[0].join()
            self.assertTrue(failures);self.assertTrue(set(failures)<={5,32,33})
            self.assertGreater(len(attempts),1)
            self.assertEqual(len({item[0] for item in attempts}),1)
            self.assertEqual(len({item[1] for item in attempts}),1)
            self.assertEqual(pub.read(path),{'version':2})
            self.assertEqual(list(path.parent.glob('*.pending')),[])

    def test_parent_to_child_exact_input_text_ack_and_new_api_delegation(self):
        with TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();state=root/'publisher';state.mkdir();feed=root/'responses';feed.mkdir()
            current=root/'CURRENT.json';current.write_text(json.dumps({'sequence':286,'tool':'metrics'}))
            config={'schema':pub.SCHEMA,'machine_id':'explicit-local-software-fixture','session':str(root),
                'state_root':str(state),'decision_text_file':str(root/'decision.txt'),
                'current_request_path':str(current),'feed_root':str(feed),'qualification_only':True,
                'game':{'pid':99,'creation_date':'explicit-fixture-not-game'}}
            config_path=root/'config.json';pub.atomic(config_path,config,new=True)
            origin=root/'original/0286-1-result.json';origin.parent.mkdir();origin.write_text('{"immutable":286}')
            projection=feed/'original-0286-1-result.json'
            pub.atomic(projection,{'request':{'sequence':286,'tool':'metrics'},'source_ref':str(origin),
                'source_namespace':'original','result':{'is_error':False,'structured_content':{'status':'observed'}}},new=True)
            errors=[]
            def run():
                try:pub.run(config_path)
                except BaseException as error:errors.append(error)
            worker=threading.Thread(target=run,name='explicit-local-publisher-fixture');worker.start()
            end=time.monotonic()+3
            while not (state/'STARTED.json').exists() and time.monotonic()<end:time.sleep(.005)
            try:
                reference=pub.pin(state/'STARTED.json')
                ack=pub.wait_text_published(projection,reference,recording=False)
                self.assertEqual(ack['source_observation'],pub.pin(projection))
                self.assertEqual(ack['text_sha256'],hashlib.sha256((root/'decision.txt').read_bytes()).hexdigest())
                self.assertFalse(ack['OBS_draw_ack']);self.assertFalse(ack['business_submission_or_outcome_inferred'])
                self.assertEqual(json.loads(origin.read_text()),{'immutable':286})
                namespace={};exec(API,namespace)
                original_atomic=pub.atomic
                self.assertIs(namespace['_install_current_input_replace_retry'](pub,root),pub)
                self.assertIs(pub.atomic,original_atomic)
            finally:
                pub.atomic(state/'STOP',{'fixture_only':True},new=True)
                worker.join(3)
            self.assertFalse(worker.is_alive());self.assertEqual(errors,[])
            self.assertIsNone(pub.read(state/'CLOSED.json')['first_error'])

    def test_errno13_permanent_failure_and_shared_publication_deadline(self):
        clock=[0.0]
        def sleep(seconds):clock[0]+=seconds
        def transient():raise PermissionError(errno.EACCES,'explicit permanent read-denial fixture')
        with patch.object(pub.time,'monotonic',side_effect=lambda:clock[0]), \
                patch.object(pub.time,'sleep',side_effect=sleep):
            with self.assertRaises(PermissionError):pub._retry_windows_io(transient)
            self.assertLessEqual(clock[0],.5)
            clock[0]=0.0
            with pub._io_budget():
                for _ in range(12):
                    calls=[0]
                    def delayed_success():
                        calls[0]+=1
                        if calls[0]<8:raise PermissionError(errno.EACCES,'explicit transient fixture')
                        return b'exact'
                    try:pub._retry_windows_io(delayed_success)
                    except PermissionError:break
                else:self.fail('Nested I/O calls reset their shared publication budget')
            self.assertLessEqual(clock[0],4.0)
        with TemporaryDirectory() as temporary:
            path=Path(temporary)/'corrupt.json';path.write_text('{bad')
            with patch.object(pub,'_shared_read_once',wraps=pub._shared_read_once) as read:
                with self.assertRaises(json.JSONDecodeError):pub.read(path)
            self.assertEqual(read.call_count,1)
            path.write_text('{"value":1}');reference=pub.pin(path)
            with patch.object(pub,'_shared_read_once',wraps=pub._shared_read_once) as read:
                self.assertEqual(pub.checked(reference),{'value':1})
            self.assertEqual(read.call_count,1)


if __name__=='__main__':unittest.main()
