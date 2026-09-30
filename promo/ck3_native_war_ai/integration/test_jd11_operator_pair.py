"""Test sealed operator pair binding with small synthetic admission fixtures."""
from copy import deepcopy
import importlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[3]
INTEGRATION = Path(__file__).resolve().parent
EPISODE = INTEGRATION.parent / "episode-02-battle-second-half"
sys.path[:0] = [str(INTEGRATION), str(EPISODE)]
operator = importlib.import_module("remaining_live_step")
admission_module = importlib.import_module("d11_admission")
for module in (operator, admission_module):
    if not Path(module.__file__).resolve().is_relative_to(ROOT):
        raise RuntimeError(f"test must import this checkout: {module.__file__}")


def write_json(path, row):
    path.write_text(json.dumps(row), encoding="utf-8")


class Jd11OperatorPairTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="jd11-pair-test-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.output = self.base / "ck3-output"
        self.output.mkdir()
        for name in ("interactive-requests", "interactive-requests-responses"):
            (self.output / name).mkdir()
        self.lock = self.base / "admission.lock.json"
        write_json(self.lock, {"synthetic": True})
        self.original_tracks = deepcopy(operator.TRACKS)
        self.dll = self.descriptor("new-dll.fixture")
        self.injector = self.descriptor("new-injector.fixture")
        self.assertNotEqual(self.dll["sha256"], operator.JOIN_DLL)
        self.assertNotEqual(self.injector["sha256"], operator.JOIN_INJECTOR)
        spec = operator.TRACKS["e2-06-d11"]
        files = {
            "dll": self.dll, "injector": self.injector,
            "capture_script": self.descriptor("capture-script.fixture"),
            "save": self.descriptor("checkpoint.fixture", declared_sha=spec["save"]),
            "receipt": self.descriptor("sidecar.fixture", declared_sha=spec["receipt"]),
            "pair": self.descriptor("pair.fixture"),
        }
        self.admission = {"lock": operator.identity(self.lock), "binding": {
            "attempt": "synthetic-no-launch-attempt", "checkout_head": "1" * 40,
            "files": files,
        }}
        self.verifier = self.enterContext(mock.patch.object(admission_module, "verify_lock",
                                                           return_value=self.admission))
        self.enterContext(mock.patch("subprocess.Popen", side_effect=
                                     AssertionError("test attempted a real process")))
        self.enterContext(mock.patch("subprocess.run", side_effect=
                                     AssertionError("test attempted a real process")))

    def descriptor(self, name, declared_sha=None):
        path = self.base / name
        path.write_bytes(("synthetic " + name).encode())
        row = operator.identity(path)
        # Historical source pins are declared fixture data; verify_lock is
        # explicitly mocked. These fixtures are not actual admission evidence.
        if declared_sha is not None:
            row["sha256"] = declared_sha
        return row

    def fixtures(self, track, *, use_new_pair=False):
        spec = operator.TRACKS[track]
        source = {"save": {"sha256": spec["save"]},
                  "receipt": {"sha256": spec["receipt"]},
                  "actor": operator.ACTOR, "date_raw": spec["date"]}
        row = {"result": "READY_FOR_BOUNDED_LIVE_ATTEMPT", "checkpoint_source": source,
               "game": {"sha256": operator.EXE_SHA},
               "bridge_dll": self.dll if use_new_pair else {"sha256": spec["dll"]},
               "bridge_injector": self.injector if use_new_pair else {"sha256": spec["injector"]}}
        argv = ["--capture", "--enable-private-phase-trace"]
        if track == "e2-06-d11":
            binding, files = self.admission["binding"], self.admission["binding"]["files"]
            row["d11_admission"] = {
                "lock": self.admission["lock"], "no_launch_attempt": binding["attempt"],
                "checkout_head": binding["checkout_head"],
                "capture_script": files["capture_script"], "dll": files["dll"],
                "injector": files["injector"], "save": files["save"],
                "sidecar": files["receipt"], "pair": files["pair"],
            }
            argv += ["--d11-admission-lock", str(self.lock)]
        write_json(self.output / "preflight.json", row)
        write_json(self.output / "native-start-readback.json", {
            "postcondition_verified": True, "source_checkpoint": source})
        write_json(self.output / "command.json", {"argv": argv})
        return row

    def test_new_sealed_pair_is_used_only_in_cloned_d11_spec(self):
        self.fixtures("e2-06-d11", use_new_pair=True)
        binding = operator.bind_session(self.output, "e2-06-d11", self.lock)
        self.verifier.assert_called_once_with(self.lock)
        self.assertEqual(binding["spec"]["dll"], self.dll["sha256"])
        self.assertEqual(binding["spec"]["injector"], self.injector["sha256"])
        self.assertEqual(binding["admission"], self.admission["lock"])
        self.assertEqual(operator.TRACKS, self.original_tracks)
        self.assertIsNot(binding["spec"], operator.TRACKS["e2-06-d11"])

    def test_dll_mismatch_is_rejected_after_lock_verification(self):
        row = self.fixtures("e2-06-d11", use_new_pair=True)
        row["bridge_dll"] = {"sha256": operator.JOIN_DLL}
        write_json(self.output / "preflight.json", row)
        with self.assertRaisesRegex(ValueError, "bridge pair differs"):
            operator.bind_session(self.output, "e2-06-d11", self.lock)
        self.verifier.assert_called_once_with(self.lock)
        self.assertEqual(operator.TRACKS, self.original_tracks)

    def test_other_tracks_keep_old_pins_and_cannot_use_d11_lock(self):
        for track in ("e2-04-d05", "e2-05-d26"):
            with self.subTest(track=track):
                self.fixtures(track)
                binding = operator.bind_session(self.output, track)
                self.assertEqual(binding["spec"]["dll"], operator.KNIGHT_DLL)
                self.assertEqual(binding["spec"]["injector"], operator.KNIGHT_INJECTOR)
                self.assertIsNone(binding["admission"])
                with self.assertRaisesRegex(ValueError, "cannot authorize another track"):
                    operator.bind_session(self.output, track, self.lock)
                self.fixtures(track, use_new_pair=True)
                with self.assertRaisesRegex(ValueError, "bridge pair differs"):
                    operator.bind_session(self.output, track)
        self.verifier.assert_not_called()
        self.assertEqual(operator.TRACKS, self.original_tracks)


if __name__ == "__main__":
    unittest.main(verbosity=2)
