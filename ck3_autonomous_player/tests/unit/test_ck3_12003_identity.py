"""Build identity and private provenance only; no ABI or gameplay qualification."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.bridge.nonwar_private_build import private_native_provenance, private_native_readback_matches
from xar_autoplayer.bridge.version_identity import CK3_11906, CK3_12002, CK3_12003, require_exact_native_backend, require_exact_native_build


class Ck3_12003IdentityTests(unittest.TestCase):
    def test_new_exact_pair_preserves_prior_builds_and_rejects_mixed_pairs(self):
        self.assertEqual(CK3_12003.game_version, "1.20.0.3")
        self.assertEqual(CK3_12003.executable_sha256, "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6")
        for build in (CK3_11906, CK3_12002, CK3_12003):
            with self.subTest(version=build.game_version):
                self.assertEqual(require_exact_native_build(build.game_version, build.executable_sha256.lower()), build)
        for other in (CK3_11906, CK3_12002):
            with self.subTest(old_version=other.game_version):
                with self.assertRaises(ValueError):
                    require_exact_native_build(CK3_12003.game_version, other.executable_sha256)
                with self.assertRaises(ValueError):
                    require_exact_native_build(other.game_version, CK3_12003.executable_sha256)

    def test_backend_and_private_readback_remain_bound_to_the_new_hello(self):
        backend = CK3_12003.backend_id("campaign-root-context-v1")
        self.assertEqual(require_exact_native_backend(CK3_12003.game_version, CK3_12003.executable_sha256, backend, suffix="campaign-root-context-v1"), CK3_12003)
        with self.assertRaises(ValueError):
            require_exact_native_backend(CK3_12003.game_version, CK3_12003.executable_sha256, CK3_12002.backend_id("campaign-root-context-v1"), suffix="campaign-root-context-v1")
        snapshot = {"diagnostics": {"hello": {
            "expected_ck3_version": CK3_12003.game_version,
            "expected_ck3_sha256": CK3_12003.executable_sha256.lower(),
        }}}
        provenance = private_native_provenance(snapshot)
        self.assertEqual(provenance, {"exact_ck3_build": "1.20.0.3", "exe_sha256": CK3_12003.executable_sha256})
        self.assertTrue(private_native_readback_matches(snapshot, provenance))
        self.assertFalse(private_native_readback_matches(snapshot, {"exact_ck3_build": "1.20.0.2", "exe_sha256": CK3_12002.executable_sha256}))
        self.assertEqual(private_native_provenance({}), {"exact_ck3_build": "1.19.0.6"})


if __name__ == "__main__":
    unittest.main()
