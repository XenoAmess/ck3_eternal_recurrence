from __future__ import annotations

from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "native_bridge" / "tools"))

from verify_private_combat_trace_dll import MARKERS, OPTION, verify


class PrivateCombatTraceDllGateTest(unittest.TestCase):
    def test_rejects_disabled_private_dispatch_and_missing_markers(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            dll = root / "xar_ck3_bridge.dll"
            cache = root / "CMakeCache.txt"
            dll.write_bytes(b"MZ" + b"\0".join(MARKERS))
            cache.write_text(f"{OPTION}:BOOL=OFF\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                verify(dll, cache)
            cache.write_text(f"{OPTION}:BOOL=ON\n", encoding="utf-8")
            self.assertTrue(verify(dll, cache)["ready"])
            dll.write_bytes(b"MZ" + b"\0".join(MARKERS[:-1]))
            with self.assertRaises(ValueError):
                verify(dll, cache)


if __name__ == "__main__":
    unittest.main()
