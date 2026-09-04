#!/usr/bin/env python3
"""Static contracts for the B3 frontend-first no-launch command builder."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parent))

import prepare_zg361_b3_exact_and_wrapper_frontend_first as prepare


class FrontendFirstPreparationTests(unittest.TestCase):
    def test_base_argv_adds_only_exact_frontend_first_contract(self) -> None:
        argv = prepare._base_argv(
            python=Path("python.exe"),
            runner=Path("run.py"),
            dll=Path("bridge.dll"),
            injector=Path("injector.exe"),
            pipe=r"\\.\pipe\xar_ck3_bridge_zg361_0123456789abcdef0123456789abcdef",
            seed_contract=Path("seed.json"),
            source=Path("product"),
            projection_manifest=Path("projection.json"),
        )
        self.assertEqual(argv.count("--phase2-frontend-first-load-save-name"), 1)
        self.assertEqual(argv.count("--phase2-frontend-first-timeout-seconds"), 1)
        self.assertEqual(
            argv[argv.index("--phase2-frontend-first-load-save-name") + 1],
            "autosave",
        )
        self.assertEqual(
            argv[argv.index("--phase2-frontend-first-timeout-seconds") + 1],
            "180",
        )
        self.assertIn("--phase2-live-batch", argv)
        self.assertNotIn("--preflight", argv)
        self.assertNotIn("--artifacts-dir", argv)


if __name__ == "__main__":
    unittest.main()
