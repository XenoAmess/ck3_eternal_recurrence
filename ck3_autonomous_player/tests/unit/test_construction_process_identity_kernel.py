"""Portable construction-only identity tests; synthetic Windows metadata."""
from datetime import datetime, timezone
from types import SimpleNamespace
import os
import unittest
from unittest.mock import Mock, patch

from xar_autoplayer.bridge import construction_process_identity_v1 as module
from xar_autoplayer.bridge import domain_construction_private_transport_v1 as transport
from xar_autoplayer.bridge.driver import BridgeUnavailableError


class ConstructionProcessIdentityKernelTest(unittest.TestCase):
    def setUp(self):
        self.driver = SimpleNamespace(_session_bridge_pid=226540)
        self.raw = "20261015043736.520398+000"
        self.local_raw = "20261015123736.520398+480"
        self.image = os.path.abspath("fixture/ck3.exe")
        self.kernel = module._KernelIdentity(226540, 134365126565203982,
                                             os.path.normcase(self.image))
        self.wmi = {"pid": 226540, "creation_date": self.raw,
                    "executable": self.image, "command_line": "original CLI"}

    def read(self, reader):
        return module.read_construction_process_identity_v1(self.driver, 226540, reader)

    def test_each_read_rechecks_kernel_and_preserves_original_local_spelling(self):
        identity = {**self.wmi, "creation_date": self.local_raw}
        reader = Mock(return_value=identity)
        original = dict(identity)
        with patch.object(module, "_kernel_process_identity", return_value=self.kernel) as kernel:
            self.assertEqual(self.read(reader), identity)
            for _ in range(5):
                self.assertEqual(self.read(reader)["creation_date"], self.local_raw)
            self.assertEqual(kernel.call_count, 7)  # before+after seed, then every read
        reader.assert_called_once_with(226540)
        self.assertEqual(identity, original)

    def test_full_filetime_change_in_same_microsecond_cannot_hit_cache(self):
        reader = Mock(return_value=self.wmi)
        changed = module._KernelIdentity(226540, self.kernel.creation_filetime + 1,
                                         self.kernel.executable)
        with patch.object(module, "_kernel_process_identity", return_value=self.kernel):
            self.read(reader)
        with patch.object(module, "_kernel_process_identity", return_value=changed):
            with self.assertRaises(BridgeUnavailableError):
                self.read(reader)
        self.assertEqual(reader.call_count, 1)

    def test_changed_image_cannot_hit_cache(self):
        reader = Mock(return_value=self.wmi)
        with patch.object(module, "_kernel_process_identity", return_value=self.kernel):
            self.read(reader)
        changed = module._KernelIdentity(226540, self.kernel.creation_filetime, self.image + ".other")
        with patch.object(module, "_kernel_process_identity", return_value=changed):
            with self.assertRaises(BridgeUnavailableError):
                self.read(reader)
        self.assertEqual(reader.call_count, 1)

    def test_unknown_or_denied_kernel_falls_back_and_does_not_use_pin(self):
        reader = Mock(return_value=self.wmi)
        with patch.object(module, "_kernel_process_identity", return_value=self.kernel):
            self.read(reader)
        with patch.object(module, "_kernel_process_identity", side_effect=PermissionError("denied")):
            self.assertEqual(self.read(reader), self.wmi)
        self.assertEqual(reader.call_count, 2)

    def test_wmi_pid_image_stamp_mismatch_never_learns_fast_pin(self):
        for difference in ({"pid": 226541}, {"executable": self.image + ".other"},
                           {"creation_date": "20261015043736.520399+000"},
                           {"creation_date": "malformed"}, {"creation_date": "20261015043736.520398+999"}):
            with self.subTest(difference=difference):
                self.driver = SimpleNamespace(_session_bridge_pid=226540)
                reader = Mock(return_value={**self.wmi, **difference})
                with patch.object(module, "_kernel_process_identity", return_value=self.kernel):
                    self.read(reader)
                    self.read(reader)
                self.assertEqual(reader.call_count, 2)
                self.assertFalse(hasattr(self.driver, "_construction_process_identity_pin_v1"))

    def test_kernel_race_while_wmi_runs_does_not_learn_pin(self):
        changed = module._KernelIdentity(226540, self.kernel.creation_filetime + 100,
                                         self.kernel.executable)
        with patch.object(module, "_kernel_process_identity", side_effect=[self.kernel, changed]):
            self.read(Mock(return_value=self.wmi))
        self.assertFalse(hasattr(self.driver, "_construction_process_identity_pin_v1"))

    def test_old_transport_error_and_invalid_pid_behavior_preserved(self):
        with patch.object(module, "_kernel_process_identity", side_effect=OSError("gone")), \
             patch.object(transport, "_process_identity", return_value=None):
            with self.assertRaises(BridgeUnavailableError):
                transport._identity(self.driver)
        self.driver._session_bridge_pid = True
        with patch.object(module, "_kernel_process_identity") as kernel, \
             patch.object(transport, "_process_identity") as wmi:
            with self.assertRaises(BridgeUnavailableError):
                transport._identity(self.driver)
            kernel.assert_not_called()
            wmi.assert_not_called()

    def test_actual_transport_returns_same_tuple_and_original_exceptions(self):
        with patch.object(module, "_kernel_process_identity", return_value=self.kernel), \
             patch.object(transport, "_process_identity", return_value=self.wmi) as reader:
            self.assertEqual(transport._identity(self.driver), (226540, self.raw))
            self.assertEqual(transport._identity(self.driver), (226540, self.raw))
            reader.assert_called_once()
        self.driver = SimpleNamespace(_session_bridge_pid=226540)
        with patch.object(module, "_kernel_process_identity", return_value=self.kernel), \
             patch.object(transport, "_process_identity", side_effect=RuntimeError("original WMI error")):
            with self.assertRaisesRegex(RuntimeError, "original WMI error"):
                transport._identity(self.driver)


if __name__ == "__main__":
    unittest.main()
