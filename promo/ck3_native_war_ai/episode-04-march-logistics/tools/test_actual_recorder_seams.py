"""Focused replay of the two R209 camera failures against canonical classes.

All screen, process and Job edges are isolated; no SDK/game/desktop action.
"""
from contextlib import contextmanager
from pathlib import Path
import hashlib
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

from PIL import Image

if "promo" in Path(__file__).parts:
    REPO = Path(__file__).resolve().parents[4]
else:
    if len(sys.argv) < 2:
        raise SystemExit("external candidate test requires explicit repository root argv")
    REPO = Path(sys.argv.pop(1)).resolve(strict=True)
sys.path[:0] = [str(REPO / "promo/ck3_native_war_ai/episode-04-march-logistics/tools"),
                str(REPO / "tools")]
import capture_recorder as canonical
from ck3_mod_acceptance_full_army import FullArmyResultClient
import window_take


class FakeJob:
    pid = 24680

    def poll(self):
        return None

    def finish(self, *, receipt, unsafe_marker, timeout):
        canonical.write(receipt, {"state": "NORMAL_TREE_EMPTY", "job_active_processes": 0,
                                  "returncode": 0, "error": None})
        return {"state": "NORMAL_TREE_EMPTY", "job_active_processes": 0,
                "returncode": 0, "error": None}

    def abort(self, *, receipt, unsafe_marker):
        raise AssertionError("normal fake Start must not abort")


class Keeper:
    task_id = "isolated-canonical-test"

    def require_live(self):
        return None

    @contextmanager
    def process_create_gate(self):
        yield


class SeenControls:
    def __init__(self):
        self.selection = types.SimpleNamespace(run_dir=Path("run-R210"))
        self.used = set()

    def execute_plan(self, rows, name, **_):
        key = (name, rows[0]["id"])
        if key in self.used:
            raise ValueError("Original control IDs already consumed; never replay")
        self.used.add(key)
        return [{"id": rows[0]["id"], "ok": True, "error": None,
                 "result": {"managed_campaign_run_binding": {"run_id": "run-R210"},
                            "revision": len(self.used)}}]

    def validate_frame(self, value, *_args, **_kwargs):
        return value


class ActualRecorderSeams(unittest.TestCase):
    def test_canonical_spawn_admission_and_fresh_public_control_namespace(self):
        with tempfile.TemporaryDirectory(prefix="e04-camera-seam-") as root:
            base = Path(root)
            work = base / "raw" / "take02"
            source = base / "original.png"
            Image.new("RGB", (640, 360), "#263443").save(source)
            ffmpeg = base / "ffmpeg-stub.exe"
            ffmpeg.write_bytes(b"isolated fake binary; spawn is patched")
            offline = base / "offline.json"
            offline.write_text("{}", encoding="utf-8")
            observed_workdir_exists = []

            spec = object.__new__(window_take.TakeSpec)
            spec.machine_id = "test-machine"
            spec.live = base / "run-R210"
            spec.record_seconds = 15
            spec.normal_close_reserve = 120
            spec.cleanup_reserve = 120

            def capacity():
                observed_workdir_exists.append(work.exists())
                return ({"capture_bounds": {"absolute_phase_deadline_utc": "2099-01-01T00:00:00Z"}},
                        {"path": str(base / "capacity.json"), "bytes": 1, "sha256": "test"})

            spec.capacity = capacity
            client = types.SimpleNamespace(remaining=lambda: 10000, guard=lambda **_: None)

            def spawn(_command, **kwargs):
                canonical.write(kwargs["start_receipt"], {"state": "ASSIGNED_AND_RESUMED", "pid": FakeJob.pid})
                return FakeJob()

            geometry = {"kind": canonical.CAPTURE_SOURCE, "owned_ck3_pid": 123,
                        "owned_ck3_create_time": 1.5, "hwnd": 77, "foreground_hwnd": 77,
                        "desktop": [640, 360], "client_screen_rect": [0, 0, 640, 360],
                        "occluding_windows": [], "output_size": [640, 360],
                        "direct_hwnd_capture": False, "window_border_included": False}
            pyautogui = types.ModuleType("pyautogui")
            pyautogui.size = lambda: (640, 360)
            pyautogui.screenshot = lambda: Image.new("RGB", (640, 360), "#263443")
            recorder_job = types.ModuleType("recorder_job")
            recorder_job.spawn = spawn
            recorder = canonical.OwnedRecorder(base, Keeper(), offline,
                {"assets_root": str(base), "machine_id": "test-machine",
                 "checkpoint": {"source": {"actor_id": 1}}},
                 start_admission=lambda seconds: spec.admission(seconds, client))
            with patch.dict(sys.modules, {"pyautogui": pyautogui, "recorder_job": recorder_job}), \
                 patch.object(canonical, "inspect_owned_client", return_value=geometry):
                ready = recorder.handle({"operation": "start", "workdir": str(work),
                    "ffmpeg": str(ffmpeg), "ffmpeg_sha256": hashlib.sha256(ffmpeg.read_bytes()).hexdigest(),
                    "target_pid": 123, "source_image": str(source), "seconds": 15},
                    {"map_ready": True, "paused": True, "played_character": {"character_id": 1}})
                self.assertEqual(ready["state"], "RECORDING")
                self.assertEqual(observed_workdir_exists, [False, True])
                self.assertTrue((work / "deadline-admission-at-spawn.json").is_file())
                self.assertEqual(recorder.finish()["state"], "NORMAL_TREE_EMPTY")
                recorder.close()

        shared = SeenControls()
        self.assertEqual(FullArmyResultClient(shared, prefix="take-a02").snapshot()["revision"], 1)
        with self.assertRaisesRegex(ValueError, "already consumed"):
            FullArmyResultClient(shared, prefix="take-a02").snapshot()
        self.assertEqual(FullArmyResultClient(shared, prefix="take-a04").snapshot()["revision"], 2)
        self.assertEqual(len(shared.used), 2)


if __name__ == "__main__":
    unittest.main()
