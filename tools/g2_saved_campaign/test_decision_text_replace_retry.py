"""Narrow child-output regression: real local Windows sharing, no Game/OBS."""
import ctypes
import hashlib
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import threading
import unittest
from unittest.mock import patch

import decision_text_publisher as pub


def denied(code=5):
    error=PermissionError('explicit replacement fixture')
    error.winerror=code
    return error


class TextReplaceRetryTests(unittest.TestCase):
    @unittest.skipUnless(os.name=='nt','Real Windows file-sharing fixture')
    def test_real_local_reader_releases_and_same_atomic_text_succeeds(self):
        with TemporaryDirectory() as temporary:
            target=Path(temporary)/'decision.txt';old=pub.TITLE+'\nold'
            target.write_text(old,encoding='utf-8')
            kernel=ctypes.WinDLL('kernel32',use_last_error=True)
            kernel.CreateFileW.argtypes=[ctypes.c_wchar_p,ctypes.c_uint32,ctypes.c_uint32,
                ctypes.c_void_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p]
            kernel.CreateFileW.restype=ctypes.c_void_p
            kernel.CloseHandle.argtypes=[ctypes.c_void_p];kernel.CloseHandle.restype=ctypes.c_int
            handle=kernel.CreateFileW(str(target),0x80000000,3,None,3,0x80,None)
            self.assertNotIn(handle,(None,ctypes.c_void_p(-1).value))
            release=[None]
            real_replace=os.replace;attempts=[];errors=[];new=pub.TITLE+'\nnew exact publication'
            def observed_replace(source,destination):
                attempts.append((Path(source),Path(source).read_bytes()))
                try:return real_replace(source,destination)
                except PermissionError as error:
                    errors.append(error.winerror)
                    self.assertEqual(target.read_text(encoding='utf-8'),old)
                    if release[0] is None:
                        release[0]=threading.Timer(.12,lambda:kernel.CloseHandle(handle))
                        release[0].start()
                    raise
            try:
                with patch.object(pub.os,'replace',side_effect=observed_replace):
                    digest=pub.publish_text(target,new)
            finally:
                if release[0] is None:kernel.CloseHandle(handle)
                else:release[0].join()
            self.assertTrue(errors);self.assertEqual(set(errors),{5})
            self.assertGreater(len(attempts),1)
            self.assertEqual(len({item[0] for item in attempts}),1)
            self.assertTrue(all(item[1]==new.encode() for item in attempts))
            self.assertEqual(target.read_bytes(),new.encode())
            self.assertEqual(digest,hashlib.sha256(new.encode()).hexdigest())
            self.assertEqual(list(target.parent.glob('*.pending')),[])

    def test_permanent_win5_is_bounded_and_does_not_replace_old_text(self):
        with TemporaryDirectory() as temporary:
            target=Path(temporary)/'decision.txt';target.write_bytes(b'old retained text')
            elapsed=[0.0];attempts=[]
            def fail(source,destination):
                attempts.append((Path(source),Path(source).read_bytes()))
                raise denied()
            with patch.object(pub.os,'replace',side_effect=fail), \
                    patch.object(pub.time,'monotonic',side_effect=lambda:elapsed[0]), \
                    patch.object(pub.time,'sleep',side_effect=lambda seconds:elapsed.__setitem__(0,elapsed[0]+seconds)):
                with self.assertRaises(PermissionError):pub.publish_text(target,pub.TITLE+'\nnew')
            self.assertEqual(len(attempts),8);self.assertLessEqual(elapsed[0],2)
            self.assertEqual(len({item[0] for item in attempts}),1)
            self.assertEqual(len({item[1] for item in attempts}),1)
            self.assertEqual(target.read_bytes(),b'old retained text')
            self.assertEqual(list(target.parent.glob('*.pending')),[])

    def test_other_permission_error_is_not_retried(self):
        with TemporaryDirectory() as temporary:
            target=Path(temporary)/'decision.txt';target.write_bytes(b'old')
            with patch.object(pub.os,'replace',side_effect=denied(32)) as replace, \
                    patch.object(pub.time,'sleep') as sleep:
                with self.assertRaises(PermissionError):pub.publish_text(target,pub.TITLE+'\nnew')
            self.assertEqual(replace.call_count,1);sleep.assert_not_called()
            self.assertEqual(target.read_bytes(),b'old')


if __name__=='__main__':unittest.main()
