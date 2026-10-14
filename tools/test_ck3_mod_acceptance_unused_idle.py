"""Focused regression for an interrupted, never-launched allocation."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from ck3_mod_acceptance_allocate import wait_for_allocated_keeper


class UnusedIdle(unittest.TestCase):
    def test_expired_unused_stops_but_existing_launch_keeps_original_wait(self):
        with tempfile.TemporaryDirectory(prefix='unused-idle-') as temporary:
            root=Path(temporary);live=root/'unused';keeper=root/'keeper'
            live.mkdir();keeper.mkdir()
            child=Mock();child.poll.return_value=None;child.wait.return_value=0
            with patch('ck3_mod_acceptance_allocate.time.monotonic',side_effect=[0,601]), \
                 patch('psutil.process_iter',return_value=[]):
                self.assertEqual(wait_for_allocated_keeper(child,live,keeper),0)
            child.wait.assert_called_once_with()
            self.assertTrue((keeper/'stop.request').is_file())
            self.assertTrue((live/'allocation-unused-idle-timeout.json').is_file())
            launched=root/'launched';launched.mkdir()
            (launched/'launch-intent.json').touch()
            child=Mock();child.poll.return_value=None;child.wait.return_value=0
            with patch('ck3_mod_acceptance_allocate.time.monotonic',return_value=0):
                self.assertEqual(wait_for_allocated_keeper(child,launched,root/'unmodified-keeper'),0)
            child.wait.assert_called_once_with()
            self.assertFalse((root/'unmodified-keeper').exists())
            self.assertFalse((launched/'allocation-unused-idle-timeout.json').exists())


if __name__=='__main__':unittest.main()
