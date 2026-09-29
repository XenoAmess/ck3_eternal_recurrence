"""Focused no-launch/live admission tests; never launches CK3 or OBS."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from capture_session import d11_live_admission
from d11_admission import (CAPTURE_SCRIPT, D11_SAVE_SHA, CHECKOUT,
                           no_launch_binding, verify_live_admission)


OLD_A06 = Path("D:/workspace/ck3_native_war_ai_promo_work/episode02-e2-06-d11-recap-preflight-20260929-a06-final")


def set_value(argv: list[str], flag: str, replacement: str) -> None:
    argv[argv.index(flag) + 1] = replacement


class D11AdmissionTest(unittest.TestCase):
    def test_capture_entry_is_default_closed_for_d11_only(self) -> None:
        source = {"save": {"sha256": D11_SAVE_SHA}}
        args = argparse.Namespace(capture=True, d11_admission_lock=None)
        with self.assertRaisesRegex(ValueError, "requires an admission lock"):
            d11_live_admission(args, source, [])
        self.assertIsNone(d11_live_admission(args, {"save": {"sha256": "OTHER"}}, []))
        args.d11_admission_lock = Path("unreviewed-lock.json")
        with self.assertRaisesRegex(RuntimeError, "only for the exact d11"):
            d11_live_admission(args, {"save": {"sha256": "OTHER"}}, [])
        args.capture = False
        with self.assertRaisesRegex(RuntimeError, "only for the exact d11"):
            d11_live_admission(args, source, [])

    @unittest.skipUnless(OLD_A06.is_dir(), "historical a06 is not installed")
    def test_old_a06_cannot_be_sealed_against_current_head(self) -> None:
        old = json.loads((OLD_A06 / "run-argv.json").read_text(encoding="utf-8"))
        self.assertNotEqual(old["checkout_head"],
                            __import__("subprocess").run(
                                ["git", "-C", str(CHECKOUT), "rev-parse", "HEAD"],
                                check=True, capture_output=True, text=True).stdout.strip())
        with self.assertRaisesRegex(ValueError, "current checkout/script/pair"):
            no_launch_binding(OLD_A06)

    @unittest.skipUnless(OLD_A06.is_dir(), "historical a06 is not installed")
    def test_live_args_reject_pair_change_and_reused_workdir(self) -> None:
        frozen = json.loads((OLD_A06 / "run-argv.json").read_text(encoding="utf-8"))["argv"]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            lock = root / "admission-lock.json"
            offline = root / "steam-offline-reviewed.json"
            offline.write_text("{}", encoding="utf-8")
            live = frozen[2:].copy()
            set_value(live, "--state-dir", str(root / "live" / "ck3-state"))
            set_value(live, "--output-dir", str(root / "live" / "ck3-output"))
            set_value(live, "--pipe-name", "fresh-d11-live-pipe")
            live += ["--steam-offline-receipt", str(offline),
                     "--d11-admission-lock", str(lock), "--capture"]
            files = {name: {"path": name} for name in
                     ("capture_script", "dll", "injector", "save", "receipt", "pair")}
            binding = {"attempt": str(OLD_A06), "checkout_head": "current",
                       "run_argv": [sys.executable, str(CAPTURE_SCRIPT), *frozen[2:]],
                       "files": files}
            with patch("d11_admission.verify_lock", return_value={
                "lock": {"path": str(lock)}, "binding": binding}):
                admitted = verify_live_admission(lock, live)
                self.assertFalse(admitted["recording_authorized"])
                self.assertFalse(admitted["date_action_authorized"])
                changed = live.copy()
                set_value(changed, "--bridge-dll", "different.dll")
                with self.assertRaisesRegex(ValueError, "argv differs"):
                    verify_live_admission(lock, changed)
                reused = live.copy()
                set_value(reused, "--output-dir", str(OLD_A06 / "ck3-output"))
                with self.assertRaisesRegex(ValueError, "fresh live root"):
                    verify_live_admission(lock, reused)
                with self.assertRaisesRegex(ValueError, "flags are not explicit"):
                    verify_live_admission(lock, live[:-1])


if __name__ == "__main__":
    unittest.main()
