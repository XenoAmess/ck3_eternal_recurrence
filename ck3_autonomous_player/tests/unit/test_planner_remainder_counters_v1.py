"""Pure counters and actual Service orchestration; no Driver or Game instance."""

import ast
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.bridge import planner_remainder_counters_v1 as counters
from xar_autoplayer.bridge.driver import PreSubmissionRevisionMismatchError
from xar_autoplayer.bridge.service import GameplayBridgeService


class Clock:
    def __init__(self):
        self.calls = 0

    def __call__(self):
        self.calls += 1
        return self.calls * 10


class PlannerRemainderCountersTests(unittest.TestCase):
    def test_default_and_missing_observer_do_not_clock_or_write(self):
        clock, seen, result = Clock(), [], object()

        def plan(counter):
            self.assertIsNone(counter)
            return result

        with patch("builtins.open", side_effect=AssertionError("unexpected I/O")):
            self.assertIs(counters.observe_planner_call_v1(
                plan, observer=seen.append, clock=clock), result)
            self.assertIs(counters.observe_planner_call_v1(
                plan, enabled=True, clock=clock), result)
        self.assertEqual(clock.calls, 0)
        self.assertEqual(seen, [])

    def test_arguments_result_counts_and_one_final_observation(self):
        clock, observed, argument, keyword, result = Clock(), [], object(), object(), object()
        calls = []

        def business(value, *, option):
            calls.append((value, option))
            return result

        def plan(counter):
            counter.note_attempt()
            self.assertIs(counter.measure("faction_gift", business,
                                          argument, option=keyword), result)
            return counter.measure("faction_gift", business, argument, option=keyword)

        with patch("builtins.open", side_effect=AssertionError("unexpected I/O")):
            self.assertIs(counters.observe_planner_call_v1(
                plan, enabled=True, observer=observed.append, clock=clock), result)
        self.assertEqual(calls, [(argument, keyword), (argument, keyword)])
        self.assertEqual(len(observed), 1)
        self.assertEqual(observed[0]["planning_attempts"], 1)
        self.assertEqual(observed[0]["counters"]["faction_gift"], [2, 2, 20])
        self.assertEqual(observed[0]["elapsed_ns"], 50)
        self.assertTrue(observed[0]["inclusive_durations"])

    def test_finish_is_once_even_when_observer_raises(self):
        seen = []

        def observer(payload):
            seen.append(payload)
            raise OSError("optional observer unavailable")

        counter = counters.PlannerRemainderCountersV1(observer, clock=Clock())
        counter.note_attempt()
        counter.finish()
        self.assertIsNone(counter.finish())
        self.assertEqual(len(seen), 1)
        self.assertEqual(seen[0]["observer_error_type"], "OSError")

    def test_clock_failure_does_not_replace_business_exception(self):
        values = iter([0, 10, OSError("clock"), 30])
        seen, error = [], RuntimeError("original business error")

        def clock():
            value = next(values)
            if isinstance(value, Exception):
                raise value
            return value

        def fail():
            raise error

        with self.assertRaises(RuntimeError) as caught:
            counters.observe_planner_call_v1(
                lambda counter: counter.measure("release", fail), enabled=True,
                observer=seen.append, clock=clock)
        self.assertIs(caught.exception, error)
        self.assertEqual(len(seen), 1)
        self.assertEqual(seen[0]["clock_failures"], 1)
        self.assertEqual(seen[0]["counters"]["release"], [1, 0, 0])


class ServiceCounterOrchestrationTests(unittest.TestCase):
    def service(self, body, observer=None, enabled=False):
        service = object.__new__(GameplayBridgeService)
        service._plan_turn_internal_without_readonly_retry_v1 = body
        service._planner_remainder_timing_enabled_v1 = enabled
        service._planner_remainder_observer_v1 = observer
        return service

    def test_disabled_service_preserves_original_private_signature(self):
        seen, result = [], object()

        def body(*, allow_prewar_force_query, allow_war_overview_query):
            seen.append((allow_prewar_force_query, allow_war_overview_query))
            return result

        service = self.service(body, observer=lambda _: self.fail("observer called"))
        with patch.object(counters, "observe_planner_call_v1",
                          side_effect=AssertionError("counter entered while off")):
            self.assertIs(service._plan_turn_internal(
                allow_prewar_force_query=False, allow_war_overview_query=False), result)
        self.assertEqual(seen, [(False, False)])

    def test_existing_readonly_retry_shares_one_observation(self):
        observed, attempts = [], []

        def body(*, allow_prewar_force_query, allow_war_overview_query,
                 _planner_remainder_v1=None):
            attempts.append(_planner_remainder_v1)
            _planner_remainder_v1.note_attempt()
            _planner_remainder_v1.measure("commander_quality", lambda: None)
            if len(attempts) == 1:
                raise PreSubmissionRevisionMismatchError(
                    "campaign-root revision mismatch: expected 7, current 8")
            return {"snapshot_id": "fresh", "revision": 8, "plan": {"selected_step": "query"}}

        service = self.service(body, observed.append, True)
        with patch.object(counters, "perf_counter_ns", Clock()):
            result = service._plan_turn_internal()
        self.assertIs(attempts[0], attempts[1])
        self.assertEqual(len(observed), 1)
        self.assertEqual(observed[0]["planning_attempts"], 2)
        self.assertEqual(observed[0]["counters"]["commander_quality"][:2], [2, 2])
        self.assertEqual(result["readonly_planning_replan_v1"]["fresh_replans"], 1)
        self.assertEqual(result["plan"], {"selected_step": "query"})

    def test_recursive_replan_forwards_counter_without_another_observer(self):
        observed, attempts, result = [], [], object()

        def body(*, allow_prewar_force_query, allow_war_overview_query,
                 _planner_remainder_v1=None):
            attempts.append(_planner_remainder_v1)
            _planner_remainder_v1.note_attempt()
            if len(attempts) == 1:
                return service._plan_turn_internal(
                    allow_prewar_force_query=allow_prewar_force_query,
                    allow_war_overview_query=allow_war_overview_query,
                    _planner_remainder_v1=_planner_remainder_v1)
            return result

        service = self.service(body, observed.append, True)
        with patch.object(counters, "perf_counter_ns", Clock()):
            self.assertIs(service._plan_turn_internal(), result)
        self.assertIs(attempts[0], attempts[1])
        self.assertEqual(len(observed), 1)
        self.assertEqual(observed[0]["planning_attempts"], 2)

    def test_business_exception_survives_failed_observer_once(self):
        observed, error = [], RuntimeError("business failure")

        def observer(payload):
            observed.append(payload)
            raise OSError("optional receiver failure")

        def body(*, allow_prewar_force_query, allow_war_overview_query,
                 _planner_remainder_v1=None):
            _planner_remainder_v1.note_attempt()
            raise error

        service = self.service(body, observer, True)
        with patch.object(counters, "perf_counter_ns", Clock()):
            with self.assertRaises(RuntimeError) as caught:
                service._plan_turn_internal()
        self.assertIs(caught.exception, error)
        self.assertEqual(len(observed), 1)
        self.assertEqual(observed[0]["planning_attempts"], 1)

    def test_hook_argument_pairs_are_identical_after_removing_counter(self):
        path = Path(__file__).resolve().parents[2] / "src/xar_autoplayer/bridge/service.py"
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        hooks = 0
        for node in ast.walk(tree):
            if not isinstance(node, ast.IfExp) or ast.unparse(node.test) != (
                    "_planner_remainder_v1 is not None"):
                continue
            measured = node.body
            if ast.unparse(measured.func) == "_planner_remainder_v1.measure":
                call = ast.Call(func=measured.args[1], args=measured.args[2:],
                                keywords=measured.keywords)
            else:
                call = ast.Call(func=measured.func, args=measured.args,
                                keywords=[kw for kw in measured.keywords
                                          if kw.arg != "_planner_remainder_v1"])
            self.assertEqual(ast.dump(call, include_attributes=False),
                             ast.dump(node.orelse, include_attributes=False))
            hooks += 1
        self.assertGreater(hooks, 0)


if __name__ == "__main__":
    unittest.main()
