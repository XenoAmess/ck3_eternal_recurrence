"""Focused offline checkpoint and no-video result checks; never start CK3/media."""
import argparse
import asyncio
import io
import json
from pathlib import Path
import threading
import unittest

from capture_session import (EXACT_SHA, checkpoint_source, copy_checkpoint, identity,
                             session_outcome, wait_checkpoint_map, write_new)

OUTPUT = None


class CheckpointSessionTests(unittest.TestCase):
    def setUp(self):
        self.root = OUTPUT / self._testMethodName
        self.root.mkdir()

    def source(self):
        save = self.root / "synthetic.ck3"
        save.write_bytes(b"synthetic opaque save fixture; never loaded in CK3")
        actual = identity(save)
        receipt = {"result": "CALL_COMPLETED", "body": {"step": "save-checkpoint", "accepted": True,
            "checkpoint": {"status": "saved", "size": actual["bytes"], "sha256": actual["sha256"].lower(),
                "episode_character_id": 29829, "date_raw": 53144328,
                "succession_lifecycle": {"lifecycle": "ordinary_campaign_succession", "xar_enabled": "xar_off",
                    "pact_contract": "absent_by_fresh_campaign_xar_off_contract", "source": "pure-vanilla-enabled-mods-empty"}}},
            "driver_state": {"hello": {"ck3_build_match": True, "expected_ck3_sha256": EXACT_SHA}}}
        path = self.root / "synthetic-receipt.json"
        write_new(path, receipt)
        return save, path

    def test_copy_exact_save_without_driver_history(self):
        save, path = self.source()
        source = checkpoint_source(save, path)
        profile = self.root / "new-profile"
        (profile / "save games").mkdir(parents=True)
        out = self.root / "evidence"
        out.mkdir()
        result = copy_checkpoint(source, profile, out)
        self.assertEqual(result["profile_copy"]["sha256"], source["save"]["sha256"])
        self.assertFalse(result["driver_history_created"])
        self.assertEqual(sorted(p.relative_to(profile).as_posix() for p in profile.rglob("*") if p.is_file()),
                         ["save games/war_film_checkpoint.ck3"])
        with self.assertRaisesRegex(RuntimeError, "must be new"):
            copy_checkpoint(source, profile, out)

    def test_changed_save_or_unpaired_input_rejected(self):
        save, path = self.source()
        with self.assertRaisesRegex(RuntimeError, "together"):
            checkpoint_source(save, None)
        save.write_bytes(b"changed synthetic save")
        with self.assertRaisesRegex(RuntimeError, "bytes differ"):
            checkpoint_source(save, path)

    def test_checkpoint_readback_uses_only_snapshot_and_requires_saved_identity(self):
        calls = []
        state = {"map_ready": True, "paused": True, "played_character": {"character_id": 29829},
            "date_raw": 53144328, "diagnostics": {"hello": {"ck3_build_match": True, "expected_ck3_sha256": EXACT_SHA}}}
        async def call(tool, **kwargs):
            calls.append(tool)
            return state
        kwargs = {"call": call, "source": {"actor": 29829, "date_raw": 53144328},
                  "stopped": threading.Event(), "timeout_seconds": 1}
        self.assertEqual(asyncio.run(wait_checkpoint_map(**kwargs)), state)
        state["date_raw"] += 1
        with self.assertRaisesRegex(RuntimeError, "actor/date differs"):
            asyncio.run(wait_checkpoint_map(**kwargs))
        self.assertEqual(calls, ["ck3_take_snapshot", "ck3_take_snapshot"])

    def test_no_recorder_never_reports_video_completion(self):
        self.assertEqual(session_outcome(session_ok=True, debug_recording_enabled=False, recording_ok=False),
                         "ENVIRONMENT_SESSION_COMPLETE_NO_VIDEO")
        self.assertEqual(session_outcome(session_ok=True, debug_recording_enabled=True, recording_ok=False), "RED")
        self.assertEqual(session_outcome(session_ok=True, debug_recording_enabled=True, recording_ok=True),
                         "RAW_CAPTURE_COMPLETE_PENDING_VISUAL_REVIEW")
        self.assertEqual(session_outcome(session_ok=False, debug_recording_enabled=False, recording_ok=False), "RED")


def main():
    global OUTPUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    OUTPUT = args.output.resolve()
    OUTPUT.mkdir(parents=True, exist_ok=False)
    log = io.StringIO()
    result = unittest.TextTestRunner(stream=log, verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(CheckpointSessionTests))
    (OUTPUT / "unittest.txt").write_bytes(log.getvalue().encode("utf-8"))
    import capture_session
    write_new(OUTPUT / "verification-index.json", {"result": "PASS" if result.wasSuccessful() else "FAIL",
        "test_count": result.testsRun, "scope": "synthetic offline helpers; no live checkpoint restore",
        "ck3_started": False, "media_process_started": False,
        "source": identity(Path(capture_session.__file__)), "tests": identity(Path(__file__)),
        "log": identity(OUTPUT / "unittest.txt")})
    print(log.getvalue())
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
