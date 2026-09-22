from __future__ import annotations

import copy
import contextlib
import importlib.util
import io
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
RUNNER = (
    ROOT / "native_bridge" / "research"
    / "run_minor_religious_war_defenders_readback.py"
)
SPEC = importlib.util.spec_from_file_location(
    "minor_religious_war_defenders_readback", RUNNER
)
assert SPEC is not None and SPEC.loader is not None
SUBJECT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SUBJECT)


def _snapshot() -> dict[str, object]:
    return {
        "snapshot_id": "r0142-frame",
        "revision": 14,
        "native_revision": 49,
        "date_raw": 53_144_328,
        "episode_run_id": "native-29829-test",
        "episode_character_id": 29_829,
        "paused": True,
        "map_ready": True,
        "played_character": {"character_id": 29_829, "alive": True},
        "active_wars": [],
        "native_command_history": [
            {"index": 1, "command": "restore-checkpoint", "ok": True}
        ],
    }


class _Service:
    def snapshot(self) -> dict[str, object]:
        return copy.deepcopy(_snapshot())


def _response(target_character_id: int) -> dict[str, object]:
    return {
        "advertised": False,
        "read_only": True,
        "minor_religious_war_defenders": {
            "status": "available",
            "actor_character_id": 29_829,
            "declaration": {
                "target_character_id": target_character_id,
                "casus_belli_key": "minor_religious_war",
            },
        },
    }


class MinorReligiousWarDefendersReadbackRunnerTest(unittest.TestCase):
    def test_frozen_source_copy_is_writable_without_mutating_source(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "frozen-driver.json"
            target = root / "candidate" / "driver-state.json"
            target.parent.mkdir()
            original = b'{"format_version": 2}\n'
            source.write_bytes(original)
            source.chmod(0o444)
            try:
                SUBJECT.copy_frozen_bytes_to_candidate(source, target)
                with target.open("ab") as output:
                    output.write(b"derived")
                self.assertEqual(source.read_bytes(), original)
                self.assertEqual(target.read_bytes(), original + b"derived")
            finally:
                source.chmod(0o666)

    def test_modes_are_explicit_and_live_is_never_default(self) -> None:
        args = SUBJECT.parser().parse_args([
            "--candidate-dir", "Z:/candidate", "--preflight-only"
        ])
        self.assertTrue(args.preflight_only)
        self.assertFalse(args.live)
        self.assertEqual(args.target_character_id, 31_549)
        self.assertEqual(
            SUBJECT.requested_target_character_ids(args), [31_549]
        )
        batch = SUBJECT.parser().parse_args([
            "--candidate-dir", "Z:/candidate", "--preflight-only",
            "--target-character-ids", "31551", "31549", "31550",
        ])
        self.assertEqual(
            SUBJECT.requested_target_character_ids(batch),
            [31_551, 31_549, 31_550],
        )
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                SUBJECT.parser().parse_args(["--candidate-dir", "Z:/candidate"])

    def test_one_query_stays_same_frame_and_has_zero_gameplay(self) -> None:
        response = _response(31_549)
        manifest = {
            "expected_actor_id": 29_829,
            "expected_date_raw": 53_144_328,
            "target_character_id": 31_549,
        }
        with mock.patch.object(
            SUBJECT,
            "_ck3_query_minor_religious_war_defenders_private_v1",
            return_value=response,
        ) as query:
            result = SUBJECT.query_one(_Service(), manifest)
        self.assertEqual(query.call_count, 1)
        called_service, target, revision = query.call_args.args
        self.assertIsInstance(called_service, _Service)
        self.assertEqual((target, revision), (31_549, 14))
        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "green_read_only")
        self.assertEqual(result["gameplay_actions"], 0)
        self.assertFalse(result["date_advanced"])

    def test_manifest_accepts_legacy_single_and_bounded_ordered_batch(self) -> None:
        self.assertEqual(
            SUBJECT.manifest_target_character_ids({
                "target_character_id": 31_549,
            }),
            [31_549],
        )
        self.assertEqual(
            SUBJECT.manifest_target_character_ids({
                "target_character_ids": [31_551, 31_549, 31_550],
            }),
            [31_551, 31_549, 31_550],
        )
        invalid = (
            [],
            list(range(1, 10)),
            [31_549, 31_549],
            [0],
            [-1],
            [True],
        )
        for value in invalid:
            with self.subTest(value=value):
                with self.assertRaises(RuntimeError):
                    SUBJECT.normalize_target_character_ids(value)

    def test_batch_queries_manifest_order_on_one_unchanged_frame(self) -> None:
        target_character_ids = [31_551, 31_549, 31_550]
        manifest = {
            "expected_actor_id": 29_829,
            "expected_date_raw": 53_144_328,
            "target_character_ids": target_character_ids,
        }

        def query(
            service: object, target_character_id: int, revision: int
        ) -> dict[str, object]:
            self.assertIsInstance(service, _Service)
            self.assertEqual(revision, 14)
            return _response(target_character_id)

        with mock.patch.object(
            SUBJECT,
            "_ck3_query_minor_religious_war_defenders_private_v1",
            side_effect=query,
        ) as private_query:
            results = SUBJECT.query_targets(_Service(), manifest)
        self.assertEqual(
            [call.args[1] for call in private_query.call_args_list],
            target_character_ids,
        )
        self.assertEqual(
            [row["target_character_id"] for row in results],
            target_character_ids,
        )
        self.assertTrue(all(row["readback"]["read_only"] for row in results))
        self.assertTrue(all(row["gameplay_actions"] == 0 for row in results))
        self.assertTrue(all(row["date_advanced"] is False for row in results))

    def test_batch_rejects_frame_drift_before_next_target(self) -> None:
        class DriftingService:
            def __init__(self) -> None:
                self.calls = 0

            def snapshot(self) -> dict[str, object]:
                self.calls += 1
                result = _snapshot()
                if self.calls >= 4:
                    result["date_raw"] = 53_144_352
                return copy.deepcopy(result)

        manifest = {
            "expected_actor_id": 29_829,
            "expected_date_raw": 53_144_328,
            "target_character_ids": [31_549, 31_550],
        }
        with mock.patch.object(
            SUBJECT,
            "_ck3_query_minor_religious_war_defenders_private_v1",
            side_effect=lambda _service, target, _revision: _response(target),
        ) as private_query:
            with self.assertRaisesRegex(RuntimeError, "initial paused frame"):
                SUBJECT.query_targets(DriftingService(), manifest)
        self.assertEqual(private_query.call_count, 1)

    def test_live_requires_round_ledger_and_evidence(self) -> None:
        args = SimpleNamespace(round_ledger=None, evidence=None)
        with self.assertRaisesRegex(RuntimeError, "round ledger"):
            SUBJECT.live(args, {}, SimpleNamespace())


if __name__ == "__main__":
    unittest.main()
