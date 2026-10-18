"""One actual-shaped production UI method regression; no SDK or native requests."""
from __future__ import annotations
import argparse
import copy
import importlib.util
from pathlib import Path
import sys
import unittest

REPO = Path(__file__).resolve().parents[1]
CANDIDATE_METHOD = None

class QueryOwnerRecheckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("ui_managed_support", REPO / "tools/test_ingame_ui_managed_binding.py")
        support = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(support)
        support.REPO = REPO
        support.ManagedUiBindingTests.setUpClass()
        cls.support = support
        cls.functions = support.ManagedUiBindingTests.functions.copy()
        if CANDIDATE_METHOD:
            cls.functions = support.actual_functions(CANDIDATE_METHOD, {"_ingame_ui_v1"}, cls.functions)

    def test_query_rechecks_only_transient_ending_owner_without_primitive_replay(self):
        support = self.support
        helper = support.ManagedUiBindingTests()
        before = helper.snapshot()
        before.update(revision=3, native_revision=2, snapshot_id="native:2", date_raw=53147376)
        before["played_character"]["character_id"] = 33388
        before["diagnostics"]["last_heartbeat"]["main_thread_query_mailbox_v1"]["date_raw"] = 53147376
        raw = helper.raw()
        raw.update(native_revision=2, played_character_id=33388, owner_character_id=33388,
                   date_raw=53147376, native_army_id=0)
        transient = copy.deepcopy(before)
        transient["diagnostics"]["last_heartbeat"]["main_thread_query_mailbox_v1"]["owner_verified_pump_epochs"] -= 1

        class SequenceFixture(support.Fixture):
            def __init__(self, method, snapshots):
                super().__init__(method, snapshots[0], raw)
                self.snapshots = snapshots
            def take_snapshot(self):
                self.reads += 1
                if self.reads > len(self.snapshots):
                    raise AssertionError("unexpected extra snapshot or primitive replay")
                return copy.deepcopy(self.snapshots[self.reads - 1])

        def fixture(snapshots):
            return SequenceFixture(self.functions["_ingame_ui_v1"], snapshots)
        def query(driver, operation="query"):
            return driver._ingame_ui_v1(operation, "army", 0, expected_revision=3)
        def refused(name, snapshots, reads, calls, operation="query"):
            driver = fixture(snapshots)
            with self.subTest(case=name), self.assertRaises((ValueError, support.ManagedUiBindingTests.frame_error)):
                query(driver, operation)
            self.assertEqual(driver.reads, reads)
            self.assertEqual(len(driver.calls), calls)
            if calls:
                self.assertFalse(driver.records[-1][1]["ok"])
                self.assertEqual(driver.records[-1][1]["result"]["raw_native_ui_result"], raw)

        driver = fixture([before, transient, before])
        result = query(driver)
        self.assertEqual(driver.reads, 3)
        self.assertEqual(len(driver.calls), 1)
        self.assertTrue(driver.records[-1][1]["ok"])
        self.assertEqual(result["queried_revision"], 3)
        self.assertEqual(result["played_character_id"], 33388)

        refused("persistent ending owner", [before, transient, transient], 3, 1)
        refused("starting owner never dispatches", [transient], 1, 0)
        refused("navigation is never retried", [before, transient], 2, 1, "select_army")
        changed = copy.deepcopy(transient)
        changed["date_raw"] += 24
        changed["diagnostics"]["last_heartbeat"]["main_thread_query_mailbox_v1"]["date_raw"] = changed["date_raw"]
        refused("changed first ending date", [before, changed], 2, 1)
        changed = copy.deepcopy(before)
        changed["native_revision"] += 1
        refused("changed second ending frame", [before, transient, changed], 3, 1)
        changed = copy.deepcopy(transient)
        changed["diagnostics"]["last_heartbeat"]["main_thread_query_mailbox_v1"]["owner_tid"] += 1
        refused("changed owner identity", [before, changed], 2, 1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO)
    parser.add_argument("--candidate-method", type=Path)
    args, rest = parser.parse_known_args()
    REPO = args.repo_root.resolve()
    CANDIDATE_METHOD = args.candidate_method.resolve() if args.candidate_method else None
    unittest.main(argv=[sys.argv[0], *rest])
