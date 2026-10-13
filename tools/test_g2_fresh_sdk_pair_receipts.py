"""Focused fresh supervisor receipt tests; no process or desktop APIs.

Run with explicit coordinator-owned supervisor and admitted artifact paths::

    python -B tools/test_g2_fresh_sdk_pair_receipts.py --supervisor-source PATH --artifact-root PATH

The supervisor source is external execution tooling. These tests exercise its
pure pair/pin validators and its file observation wrapper, without launching
the supervisor, SDK, game, Steam, or any desktop operation.
"""

from __future__ import annotations

import argparse
import copy
import ctypes
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


SUPERVISOR_SOURCE: Path | None = None
ARTIFACT_ROOT: Path | None = None
PAIR = [
    {"role": "sdk_queue", "pid": 4101, "creation_filetime": 134363025952867701,
     "executable": r"C:\isolated-sdk\python.exe"},
    {"role": "sdk_application", "pid": 4102, "creation_filetime": 134363025952867702,
     "executable": r"C:\isolated-sdk\python.exe"},
]


def exited_pair(queue_code: int = 0, application_code: int = 0):
    rows = copy.deepcopy(PAIR)
    for row, code in zip(rows, (queue_code, application_code)):
        row.update(kernel_exit_observed=True, wait_result=0, exit_code=code,
                   observation_error=None)
    return rows


def load_supervisor(path: Path):
    name = "g2_pair_receipt_supervisor_under_test"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError("an actual supervisor Python source is required")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class FreshSdkPairReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if SUPERVISOR_SOURCE is None or ARTIFACT_ROOT is None:
            raise unittest.SkipTest("explicit external source/artifact paths required")
        # Import must remain passive. The same guards cover every test body.
        cls.guards = [
            mock.patch.object(ctypes, "WinDLL", create=True,
                              side_effect=AssertionError("native APIs forbidden")),
            mock.patch.object(subprocess, "Popen",
                              side_effect=AssertionError("process launch forbidden")),
        ]
        for guard in cls.guards:
            guard.start()
            cls.addClassCleanup(guard.stop)
        cls.supervisor = load_supervisor(SUPERVISOR_SOURCE)

    def test_identity_pair_keeps_original_rows_and_ignores_role_order(self):
        identities = copy.deepcopy(PAIR)
        original = copy.deepcopy(identities)
        actual = self.supervisor.validate_sdk_process_pair(identities[::-1])
        self.assertEqual(set(actual), {"sdk_queue", "sdk_application"})
        self.assertIs(actual["sdk_queue"], identities[0])
        self.assertIs(actual["sdk_application"], identities[1])
        self.assertEqual(identities, original)

    def test_identity_pair_rejects_missing_duplicate_wrong_or_malformed_roles(self):
        scenes = [None, {}, [], [PAIR[0]], PAIR + [PAIR[0]],
                  [None, PAIR[1]], [False, PAIR[1]],
                  [PAIR[0], PAIR[0]],
                  [PAIR[0], {**PAIR[1], "role": "wrapper"}],
                  [PAIR[0], {key: value for key, value in PAIR[1].items() if key != "role"}]]
        for scene in scenes:
            with self.subTest(scene=scene), self.assertRaises(ValueError):
                self.supervisor.validate_sdk_process_pair(copy.deepcopy(scene))

    def test_identity_fields_reject_bool_nonpositive_and_blank_values(self):
        changes = {
            "pid": (None, True, False, 0, -1, 1.5, "4102", 114680),
            "creation_filetime": (None, True, False, 0, -1, 1.5, "134363025952867702"),
            "executable": (None, True, 1, "", " ", "\t"),
        }
        for role_index in (0, 1):
            for key, values in changes.items():
                for value in values:
                    identities = copy.deepcopy(PAIR)
                    identities[role_index][key] = value
                    with self.subTest(role=role_index, key=key, value=value), self.assertRaises(ValueError):
                        self.supervisor.validate_sdk_process_pair(identities)
                identities = copy.deepcopy(PAIR)
                del identities[role_index][key]
                with self.subTest(role=role_index, missing=key), self.assertRaises(ValueError):
                    self.supervisor.validate_sdk_process_pair(identities)

    def test_pair_requires_two_distinct_process_ids(self):
        identities = copy.deepcopy(PAIR)
        identities[1]["pid"] = identities[0]["pid"]
        with self.assertRaises(ValueError):
            self.supervisor.validate_sdk_process_pair(identities)

    def test_actual_two_zero_exits_are_normal_and_keep_original_observations(self):
        observations = exited_pair()
        original = copy.deepcopy(observations)
        result = self.supervisor.validate_sdk_process_pair(copy.deepcopy(PAIR), observations[::-1])
        self.assertEqual(result["status"], "ACTUAL_BOTH_SDK_EXITS_OBSERVED")
        self.assertIs(result["normal"], True)
        self.assertEqual(result["processes"], observations[::-1])
        self.assertEqual(observations, original)

    def test_queue_zero_never_invents_application_zero(self):
        for queue_code, app_code in ((0, 1), (0, 259), (0, 0xFFFFFFFF), (1, 0)):
            observations = exited_pair(queue_code, app_code)
            with self.subTest(queue_code=queue_code, application_code=app_code):
                result = self.supervisor.validate_sdk_process_pair(copy.deepcopy(PAIR), observations)
                self.assertEqual(result["status"], "ACTUAL_BOTH_SDK_EXITS_OBSERVED")
                self.assertIs(result["normal"], False)
                self.assertEqual(result["processes"][1]["exit_code"], app_code)
        with self.assertRaises(ValueError):
            self.supervisor.validate_sdk_process_pair(copy.deepcopy(PAIR), [exited_pair()[0]])

    def test_exit_identity_mismatch_or_boolean_fields_are_rejected(self):
        for scene in ({}, [], [exited_pair()[0]], [None, exited_pair()[1]],
                      [exited_pair()[0], exited_pair()[0]], exited_pair() + [exited_pair()[0]]):
            with self.subTest(exit_shape=scene), self.assertRaises(ValueError):
                self.supervisor.validate_sdk_process_pair(copy.deepcopy(PAIR), scene)
        changes = {"pid": 9001, "creation_filetime": PAIR[1]["creation_filetime"] + 1,
                   "executable": r"C:\replacement\python.exe", "role": "wrapper"}
        for key, value in changes.items():
            observations = exited_pair()
            observations[1][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.supervisor.validate_sdk_process_pair(copy.deepcopy(PAIR), observations)
        # bool compares equal to 1; exact integer validation must still reject it.
        for key in ("pid", "creation_filetime"):
            identities = copy.deepcopy(PAIR)
            identities[1][key] = 1
            observations = exited_pair()
            observations[1][key] = True
            with self.subTest(boolean_key=key), self.assertRaises(ValueError):
                self.supervisor.validate_sdk_process_pair(identities, observations)

    def test_exit_needs_independent_true_signal_and_uint32_exit_code(self):
        for role_index in (0, 1):
            for signal in (None, False, 0, 1, "true"):
                observations = exited_pair()
                observations[role_index]["kernel_exit_observed"] = signal
                with self.subTest(role=role_index, signal=signal), self.assertRaises(ValueError):
                    self.supervisor.validate_sdk_process_pair(copy.deepcopy(PAIR), observations)
            observations = exited_pair()
            del observations[role_index]["kernel_exit_observed"]
            with self.subTest(role=role_index, missing_signal=True), self.assertRaises(ValueError):
                self.supervisor.validate_sdk_process_pair(copy.deepcopy(PAIR), observations)
            for code in (None, True, False, -1, 0x100000000, 0.0, "0"):
                observations = exited_pair()
                observations[role_index]["exit_code"] = code
                with self.subTest(role=role_index, exit_code=code), self.assertRaises(ValueError):
                    self.supervisor.validate_sdk_process_pair(copy.deepcopy(PAIR), observations)

    def test_pin_requires_exact_retained_pair_status_generation_and_executable(self):
        acknowledgement = {"status": "SDK_PAIR_HANDLES_RETAINED", "processes": copy.deepcopy(PAIR)}
        self.assertIs(self.supervisor.validate_sdk_pin(copy.deepcopy(PAIR), acknowledgement), True)
        for key, value in (("pid", 9001), ("creation_filetime", PAIR[1]["creation_filetime"] + 1),
                           ("executable", r"C:\replacement\python.exe"), ("role", "wrapper")):
            wrong = copy.deepcopy(acknowledgement)
            wrong["processes"][1][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.supervisor.validate_sdk_pin(copy.deepcopy(PAIR), wrong)
        for status in (None, False, "", "SDK_PAIR_IDENTITIES_WRITTEN", "INITIALIZED"):
            wrong = copy.deepcopy(acknowledgement)
            wrong["status"] = status
            with self.subTest(status=status), self.assertRaises(ValueError):
                self.supervisor.validate_sdk_pin(copy.deepcopy(PAIR), wrong)
        for key, value in (("pid", True), ("pid", 0), ("pid", 114680),
                           ("creation_filetime", True), ("creation_filetime", 0),
                           ("executable", ""), ("executable", " ")):
            wrong = copy.deepcopy(acknowledgement)
            wrong["processes"][1][key] = value
            with self.subTest(pin_key=key, pin_value=value), self.assertRaises(ValueError):
                self.supervisor.validate_sdk_pin(copy.deepcopy(PAIR), wrong)

    def test_pin_rejects_incomplete_acknowledgement_without_mutating_input(self):
        identities = copy.deepcopy(PAIR)
        original = copy.deepcopy(identities)
        scenes = [None, [], {}, {"status": "SDK_PAIR_HANDLES_RETAINED"},
                  {"status": "SDK_PAIR_HANDLES_RETAINED", "processes": [PAIR[0]]},
                  {"status": "SDK_PAIR_HANDLES_RETAINED", "processes": [PAIR[0], PAIR[0]]}]
        for scene in scenes:
            with self.subTest(scene=scene), self.assertRaises(ValueError):
                self.supervisor.validate_sdk_pin(identities, copy.deepcopy(scene))
        self.assertEqual(identities, original)

    def test_file_wrapper_does_not_call_sdk_started_until_argv_exists(self):
        with tempfile.TemporaryDirectory(dir=ARTIFACT_ROOT, prefix="pair-lifecycle-") as folder:
            root = Path(folder)
            with mock.patch.object(self.supervisor, "N", root):
                self.assertEqual(self.supervisor.sdk_exit_observation(),
                                 {"status": "SDK_NOT_STARTED", "normal": True})
                (root / "sdk-session01").mkdir()
                (root / "sdk-session01/ROOT-FRESH-SDK-ARGV.json").write_text("{}", encoding="utf-8")
                self.assertIsNone(self.supervisor.sdk_exit_observation())
                (root / "ROOT-ACTUAL-SDK-PROCESS-GENERATIONS.json").write_text(
                    json.dumps({"processes": PAIR}), encoding="utf-8")
                self.assertIsNone(self.supervisor.sdk_exit_observation())

    def test_file_wrapper_consumes_exact_two_actual_exit_receipts(self):
        with tempfile.TemporaryDirectory(dir=ARTIFACT_ROOT, prefix="pair-lifecycle-") as folder:
            root = Path(folder)
            (root / "sdk-session01").mkdir()
            (root / "sdk-session01/ROOT-FRESH-SDK-ARGV.json").write_text("{}", encoding="utf-8")
            (root / "ROOT-ACTUAL-SDK-PROCESS-GENERATIONS.json").write_text(
                json.dumps({"processes": PAIR}), encoding="utf-8")
            exit_path = root / "ROOT-ACTUAL-SDK-PROCESSES-EXITED.json"
            exit_path.write_text(json.dumps({"processes": exited_pair(0, 1)}), encoding="utf-8")
            with mock.patch.object(self.supervisor, "N", root):
                result = self.supervisor.sdk_exit_observation()
                self.assertEqual(result["status"], "ACTUAL_BOTH_SDK_EXITS_OBSERVED")
                self.assertIs(result["normal"], False)
                exit_path.write_text(json.dumps({"processes": exited_pair()}), encoding="utf-8")
                self.assertIs(self.supervisor.sdk_exit_observation()["normal"], True)
                invalid = exited_pair()
                invalid[1]["creation_filetime"] += 1
                exit_path.write_text(json.dumps({"processes": invalid}), encoding="utf-8")
                with self.assertRaises(ValueError):
                    self.supervisor.sdk_exit_observation()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--supervisor-source", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    args, remaining = parser.parse_known_args()
    SUPERVISOR_SOURCE = args.supervisor_source.resolve(strict=True)
    ARTIFACT_ROOT = args.artifact_root.resolve(strict=True)
    unittest.main(argv=[sys.argv[0], *remaining])
