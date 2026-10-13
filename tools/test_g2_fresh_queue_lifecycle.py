"""Focused offline checks for an explicitly selected fresh SDK queue helper.

The queue module is loaded without calling its main, constructor or preflight.
Only unrelated custody, transport and file I/O are replaced. Lifecycle values come
from the repository's real canonical contract; no Game, pipe or SDK is opened.
"""

from __future__ import annotations

import argparse
import asyncio
import copy
from datetime import datetime, timezone
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import sys
import unittest
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPO_ROOT / "ck3_autonomous_player" / "src"
sys.path.insert(0, str(SOURCE_ROOT))
sys.path.insert(0, str(REPO_ROOT / "tools"))

from xar_autoplayer.bridge.succession_transition_contract import (  # noqa: E402
    ORDINARY_CAMPAIGN_SUCCESSION,
    ROGUE_ONE_LIFE,
    bind_succession_lifecycle_from_environment_v1,
    unknown_succession_lifecycle_binding_v1,
)


QUEUE_HELPER_PATH: Path | None = None
OUTPUT_LIMIT = 1024 * 1024


def _manifest(setting: str = "xar_off", digest: str = "1" * 64) -> dict:
    return {
        "environment_sha256": digest,
        "rules": {"profile": [{"rule": "xar_enabled", "setting": setting}]},
    }


def _ordinary_binding(digest: str = "1" * 64) -> dict:
    return bind_succession_lifecycle_from_environment_v1(
        _manifest(digest=digest),
        lifecycle=ORDINARY_CAMPAIGN_SUCCESSION,
        ordinary_campaign_no_pact=True,
    )


def _semantic(binding: object) -> dict:
    return {
        "snapshot_id": "native:12",
        "revision": 7,
        "native_revision": 12,
        "date_raw": 53_171_400,
        "paused": True,
        "map_ready": True,
        "played_character": {"character_id": 29829, "alive": True},
        "episode_run_id": "native-29829-fixture-fresh",
        "one_life_terminal": False,
        "succession_lifecycle": copy.deepcopy(binding),
        "active_event": None,
        "pending_character_interaction": None,
    }


def _checkpoint(binding: object) -> dict:
    return {
        "status": "saved",
        "date_raw": 53_171_400,
        "episode_run_id": "native-29829-fixture-fresh",
        "episode_character_id": 29829,
        "succession_lifecycle": copy.deepcopy(binding),
    }


class FreshQueueLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if QUEUE_HELPER_PATH is None:
            raise RuntimeError("an explicit --queue-helper is required")
        spec = importlib.util.spec_from_file_location(
            "g2_fresh_queue_lifecycle_under_test", QUEUE_HELPER_PATH
        )
        if spec is None or spec.loader is None:
            raise RuntimeError("cannot load the explicitly selected queue helper")
        cls.queue_module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = cls.queue_module
        spec.loader.exec_module(cls.queue_module)

    def setUp(self) -> None:
        self.expected = _ordinary_binding()
        self.queue = self.queue_module.FreshQueue.__new__(
            self.queue_module.FreshQueue
        )
        self.queue.expected_lifecycle_binding = copy.deepcopy(self.expected)
        self.queue.frontend_done = 3
        self.queue.semantic = None
        self.queue.initial_frame = None
        self.queue.initial_save = None
        self.queue.robert_key = "bookmark_rags_to_riches_duke_robert"
        self.mode_reads = 0

        def mode_read(path: Path, limit: int = 1024 * 1024) -> dict:
            self.assertEqual(
                path, self.queue_module.N / "ROOT-ACTUAL-DRIVER-MODE.json"
            )
            self.assertEqual(limit, 16384)
            self.mode_reads += 1
            return {
                "episode_projection": "one_life",
                "before_submit_observation": True,
            }

        patcher = mock.patch.object(self.queue_module, "read", mode_read)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _observe_valid_semantic(self) -> dict:
        semantic = _semantic(self.expected)
        self.queue.check_after(self.queue_module.SEMANTIC, {}, semantic)
        return semantic

    def _rejected_bindings(self) -> dict[str, object]:
        rogue = bind_succession_lifecycle_from_environment_v1(
            _manifest("xar_on"), lifecycle=ROGUE_ONE_LIFE
        )
        return {
            "legacy_string": ORDINARY_CAMPAIGN_SUCCESSION,
            "rogue": rogue,
            "unknown": unknown_succession_lifecycle_binding_v1(),
            "other_environment": _ordinary_binding("2" * 64),
        }

    def _reject_semantic(self, binding: object) -> None:
        semantic = _semantic(binding)
        with self.assertRaises(ValueError):
            self.queue_module.frame(
                semantic, semantic=True, expected_lifecycle=self.expected
            )
        with self.assertRaises(ValueError):
            self.queue.check_after(self.queue_module.SEMANTIC, {}, semantic)
        self.assertIsNone(self.queue.semantic)
        self.assertIsNone(self.queue.initial_frame)

    def test_real_canonical_binding_passes_initial_semantic_and_save(self) -> None:
        semantic = self._observe_valid_semantic()
        semantic_before = copy.deepcopy(semantic)
        arguments = {"expected_revision": semantic["revision"]}
        self.queue.check_before(self.queue_module.SAVE, arguments)
        saved = _checkpoint(self.expected)
        saved_before = copy.deepcopy(saved)
        self.queue.check_after(
            self.queue_module.SAVE, arguments, {"checkpoint": saved}
        )
        self.assertEqual(self.queue.initial_save, saved)
        self.assertEqual(self.queue.semantic, semantic_before)
        self.assertEqual(saved, saved_before)
        self.assertEqual(self.mode_reads, 2)

    def test_semantic_rejects_legacy_lifecycle_string(self) -> None:
        self._reject_semantic(ORDINARY_CAMPAIGN_SUCCESSION)

    def test_semantic_rejects_real_rogue_binding(self) -> None:
        self._reject_semantic(self._rejected_bindings()["rogue"])

    def test_semantic_rejects_real_unknown_binding(self) -> None:
        self._reject_semantic(self._rejected_bindings()["unknown"])

    def test_semantic_rejects_binding_to_another_environment(self) -> None:
        self._reject_semantic(_ordinary_binding("2" * 64))

    def test_semantic_requires_expected_manifest_binding(self) -> None:
        with self.assertRaises(ValueError):
            self.queue_module.frame(_semantic(self.expected), semantic=True)

    def test_save_rejects_string_or_different_lifecycle_binding(self) -> None:
        semantic = self._observe_valid_semantic()
        arguments = {"expected_revision": semantic["revision"]}
        for name, binding in self._rejected_bindings().items():
            with self.subTest(binding=name):
                with self.assertRaises(ValueError):
                    self.queue.check_after(
                        self.queue_module.SAVE,
                        arguments,
                        {"checkpoint": _checkpoint(binding)},
                    )
                self.assertIsNone(self.queue.initial_save)

    def test_save_request_revalidates_the_actual_semantic_binding(self) -> None:
        semantic = self._observe_valid_semantic()
        arguments = {"expected_revision": semantic["revision"]}
        for name, binding in self._rejected_bindings().items():
            with self.subTest(binding=name):
                self.queue.semantic = _semantic(binding)
                with self.assertRaises(ValueError):
                    self.queue.check_before(self.queue_module.SAVE, arguments)

    def test_periodic_full_loop_save_accepts_the_current_binding(self) -> None:
        initial = _semantic(self.expected)
        self.queue.initial_frame = self.queue_module.frame(
            initial, semantic=True, expected_lifecycle=self.expected
        )
        self.queue.initial_save = _checkpoint(self.expected)
        self.queue.loop_count = 0
        self.queue.next_sequence = 2
        turn_count = 0
        observed_tools = []
        receipts = {}

        def current_semantic() -> dict:
            semantic = _semantic(self.expected)
            semantic.update({
                "snapshot_id": f"native:{12 + turn_count}",
                "revision": 7 + turn_count,
                "native_revision": 12 + turn_count,
                "date_raw": 53_171_400 + 24 * turn_count,
            })
            return semantic

        async def generated(session, tool, arguments=None):
            nonlocal turn_count
            arguments = arguments or {}
            self.queue.check_before(tool, arguments)
            observed_tools.append(tool)
            semantic = current_semantic()
            if tool == self.queue_module.METRICS:
                body = {**semantic, "actor_character_id": 29829, "actor_alive": True}
            elif tool == self.queue_module.AUTO:
                turn_count += 1
                body = {"status": "executed", "result": {"accepted": True},
                        "plan": {"selected_step": "life-advance"}}
            elif tool == self.queue_module.SEMANTIC:
                body = semantic
            elif tool == self.queue_module.SAVE:
                saved = _checkpoint(self.expected)
                saved["date_raw"] = semantic["date_raw"]
                body = {"checkpoint": saved}
            else:
                raise AssertionError(f"unexpected fixture tool: {tool}")
            self.queue.check_after(tool, arguments, body)
            return body, Path(f"fixture-{len(observed_tools):03d}.json")

        def retain(path, value, **kwargs):
            receipts[path.name] = copy.deepcopy(value)

        with mock.patch.object(self.queue, "generated", generated), \
                mock.patch.object(self.queue, "guard"), \
                mock.patch.object(self.queue, "consume_sequence", return_value=1), \
                mock.patch.object(self.queue_module, "atomic", retain):
            result = asyncio.run(self.queue.full_loop(
                None, {"arguments": {"max_turns": 5}}, Path("fixture-control.json")
            ))
        self.assertEqual(result["actual_turns"], 5)
        self.assertEqual(result["actual_calendar_days"], 5)
        self.assertEqual(observed_tools.count(self.queue_module.SAVE), 1)
        self.assertEqual(observed_tools[-2:], [self.queue_module.SEMANTIC, self.queue_module.SAVE])
        self.assertEqual(receipts["LOOP-0001-SAVE-005.json"]["save_response"], "fixture-013.json")
        self.assertEqual(receipts["LOOP-0001-SAVE-005.json"]["checkpoint"]["succession_lifecycle"], self.expected)

    def test_terminal_semantic_still_stops_before_save(self) -> None:
        semantic = _semantic(self.expected)
        semantic["one_life_terminal"] = True
        with self.assertRaises(ValueError):
            self.queue.check_after(self.queue_module.SEMANTIC, {}, semantic)
        self.assertIsNone(self.queue.initial_frame)
        self.assertIsNone(self.queue.initial_save)


def _storage_check(admission_path: Path, receipt_root: Path) -> dict:
    admission = json.loads(admission_path.read_text(encoding="utf-8-sig"))
    review = datetime.fromisoformat(admission["review_at_utc"].replace("Z", "+00:00"))
    if review.tzinfo is None or datetime.now(timezone.utc) >= review:
        raise RuntimeError("the original storage admission has expired")
    roots = [Path(value).resolve() for value in admission["approved_output_roots"]]
    if not any(receipt_root.is_relative_to(root) for root in roots):
        raise RuntimeError("receipt root is outside the existing admitted roots")
    volume_path = receipt_root
    while not volume_path.exists():
        volume_path = volume_path.parent
    volume = shutil.disk_usage(volume_path)
    required = sum(admission[key] for key in (
        "this_write_peak", "other_unspent_reservations", "system_growth_reserve",
        "safety_margin",
    ))
    if admission.get("status") != "ADMITTED" or volume.free < required:
        raise RuntimeError("the existing admission is not currently satisfied")
    return {
        "policy_version": admission["policy_version"],
        "review_at_utc_unchanged": admission["review_at_utc"],
        "original_peak_bytes_unchanged": admission["this_write_peak"],
        "actual_free_bytes": volume.free,
        "required_free_bytes": required,
        "lane_output_cap_bytes": OUTPUT_LIMIT,
    }


def main() -> int:
    global QUEUE_HELPER_PATH
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue-helper", type=Path, required=True)
    parser.add_argument("--receipt-root", type=Path, required=True)
    parser.add_argument("--storage-admission", type=Path, required=True)
    parser.add_argument("--test", action="append", default=[])
    args = parser.parse_args()
    QUEUE_HELPER_PATH = args.queue_helper.resolve(strict=True)
    receipt_root = args.receipt_root.resolve()
    storage = _storage_check(args.storage_admission.resolve(strict=True), receipt_root)
    receipt_root.mkdir(parents=True, exist_ok=True)
    if any(receipt_root.iterdir()):
        raise RuntimeError("focused test receipts require a new empty output directory")
    stream = io.StringIO()
    suite = (
        unittest.TestSuite(FreshQueueLifecycleTests(name) for name in args.test)
        if args.test else
        unittest.defaultTestLoader.loadTestsFromTestCase(FreshQueueLifecycleTests)
    )
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    log = stream.getvalue()
    contract_path = SOURCE_ROOT / "xar_autoplayer/bridge/succession_transition_contract.py"
    receipt = {
        "status": "passed" if result.wasSuccessful() else "failed",
        "ended_at_utc": datetime.now(timezone.utc).isoformat(),
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "queue_helper": str(QUEUE_HELPER_PATH),
        "queue_helper_sha256": hashlib.sha256(QUEUE_HELPER_PATH.read_bytes()).hexdigest(),
        "canonical_contract": str(contract_path),
        "canonical_contract_sha256": hashlib.sha256(contract_path.read_bytes()).hexdigest(),
        "test_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "storage_start": storage,
        "actual_free_bytes_at_close": shutil.disk_usage(receipt_root).free,
        "open_kaishek_precheck": {
            "status": "not-applicable",
            "reason": "Python queue lifecycle binding and SAVE frame checks; no CK3 script semantics",
        },
        "game_sdk_steam_window_activity": False,
    }
    receipt_text = json.dumps(receipt, ensure_ascii=False, indent=2) + "\n"
    if len(log.encode("utf-8")) + len(receipt_text.encode("utf-8")) > OUTPUT_LIMIT:
        raise RuntimeError("focused test output exceeds its existing lane budget")
    (receipt_root / "unittest.log").write_text(log, encoding="utf-8")
    (receipt_root / "result.json").write_text(receipt_text, encoding="utf-8")
    print(log, end="")
    print(json.dumps(receipt, ensure_ascii=False))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
