"""AUTHORED_NOTRUN: ordinary Crown retry consumes Native58 whole observations.

The four already qualified native calendar packets stay unchanged. New formal
quotes, baseline priorities and timeline frames are explicit source fixtures.
The registered MCP/Service planner, strict transports, state consumer and real
NativeDriver timeline/progress implementation execute without a game or pipe.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
import inspect
import json
from pathlib import Path
import re
import sys
from threading import RLock
from types import SimpleNamespace
import unittest
from unittest.mock import patch


FILES = (
    "single-match-timed-suffix.json", "double-match-odd-remaining.json",
    "known-not-member.json", "manager-read-unavailable.json",
)
NATIVE_RECEIPT_SCHEMA = (
    "xar.ck3.crown-authority-cooldown-calendar-deadline-native-whole-fixture12004/v1"
)
SELECTED_METHOD = "test_calendar_retry_reaches_registered_plan_and_actual_advance"
LAW = "crown_authority_1"
BASE_DATE = 53169072
BASELINE = {"policy": "ordinary-source-fixture", "phase": "life_advance",
            "selected_step": "life-advance"}


def load_object(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path}")
    return value


class CrownCalendarRetryRegisteredPlanTest(unittest.IsolatedAsyncioTestCase):
    args: argparse.Namespace
    observations: list[dict[str, object]]
    evidence: dict[str, object]

    async def test_calendar_retry_reaches_registered_plan_and_actual_advance(self) -> None:
        if not hasattr(self, "args"):
            self.skipTest("Use Root's standalone FIRST launcher with existing Native58 wires")
        sys.path.insert(0, str(self.args.source_root / "ck3_autonomous_player" / "src"))
        from mcp import Client
        from xar_autoplayer import crown_authority_formal_consumer_v1 as consumer
        from xar_autoplayer.bridge import native_driver as native
        from xar_autoplayer.bridge import realm_law_formal_private_transport as formal
        from xar_autoplayer.bridge import realm_law_paused_private_transport as paused
        from xar_autoplayer.bridge.mcp_server import create_server
        from xar_autoplayer.bridge.service import GameplayBridgeService
        from xar_autoplayer.bridge.version_identity import CK3_12004
        from xar_autoplayer.environment import write_json_atomic

        receipt = load_object(self.args.native_wire_dir / "fixture-receipt.json")
        self.assertEqual(receipt["schema"], NATIVE_RECEIPT_SCHEMA)
        self.assertEqual(receipt["status"], "GREEN")
        self.assertEqual(receipt["cases"], 4)
        self.assertEqual(receipt["whole_wire_files"], list(FILES))
        self.assertIs(receipt["live"], False)
        self.assertEqual(receipt["old_cases_executed"], 0)
        self.assertEqual(receipt["law_action_calls"], 0)
        frame = receipt["frame"]
        self.assertEqual(frame, {
            "public_revision": 2, "native_revision": 9, "date_raw": BASE_DATE,
            "actor_character_id": 29829, "paused": True, "map_ready": True,
        })
        packets = {name: load_object(self.args.native_wire_dir / name) for name in FILES}
        originals = deepcopy(packets)
        self.evidence.update(
            native_receipt=receipt,
            dispatch_path=("real registered ck3_plan_turn -> GameplayBridgeService -> "
                "Crown consumer -> actual formal/strict calendar transports -> "
                "NativeProtocolState ingest/wait; real NativeDriver._execute_life_advance"),
            production_source_files={
                "registration": inspect.getsourcefile(create_server),
                "ordinary_service": inspect.getsourcefile(GameplayBridgeService.plan_turn),
                "crown_consumer": inspect.getsourcefile(consumer.plan_crown_authority_private_v1),
                "horizon_consumer": inspect.getsourcefile(consumer.crown_authority_retry_horizon_days_v1),
                "actual_life_advance": inspect.getsourcefile(native.NativeHeadlessGameplayDriver._execute_life_advance),
                "actual_progress": inspect.getsourcefile(native._life_advance_progressed),
                "strict_calendar_transport": inspect.getsourcefile(paused.query_realm_law_final_terms_private_v1),
            },
            fixture_seams=["ordinary baseline choice", "new source-shaped formal quote envelope",
                "outer paused/timeline frames", "speed/resume/pause external primitives"],
        )
        test_case = self

        class OrdinaryCalendarDriver:
            query_realm_law_crown_action_private_v1 = (
                native.NativeHeadlessGameplayDriver.query_realm_law_crown_action_private_v1
            )
            query_realm_law_final_terms_private_v1 = (
                native.NativeHeadlessGameplayDriver.query_realm_law_final_terms_private_v1
            )
            _execute_life_advance = native.NativeHeadlessGameplayDriver._execute_life_advance
            allow_private_realm_law_action = True
            allow_private_realm_law_paused_query = True
            nonwar_only = False
            command_timeout_seconds = 1.0
            life_advance_timeout_seconds = 30.0
            _session_bridge_pid = 881

            def __init__(self, name: str, packet: dict[str, object]) -> None:
                self.state_dir = test_case.args.output_dir / "state" / name
                self.packet = packet
                self.endpoint = self
                self.state = native.NativeProtocolState("offline-fixture:m7-calendar-retry-FIRST")
                self.state.ingest({
                    "type": "hello", "protocol_version": 1, "bridge_version": "0.1.0",
                    "pid": self._session_bridge_pid, "session_generation": 0,
                    "capabilities": ["game.state.snapshot", "game.command.pause-map",
                        "game.command.resume-map", *[
                            f"game.command.set-speed-{speed}" for speed in range(1, 6)]],
                })
                self.sent: list[dict[str, object]] = []
                self.ingested_types: list[str] = []
                self.formal_source_envelopes: list[dict[str, object]] = []
                self.formal_ready = False
                self._history_lock = RLock()
                self._command_history: list[dict[str, object]] = []
                self.frame = {
                    "snapshot_id": "source-fixture-native:9", "revision": frame["public_revision"],
                    "native_revision": frame["native_revision"], "date_raw": frame["date_raw"],
                    "paused": True, "map_ready": True, "speed": 1,
                    "episode_run_id": "m7-calendar-retry-source-fixture12004",
                    "phase": "map_hud", "active_event": None,
                    "pending_character_interaction": None, "active_wars": [],
                    "player_armies": [], "native_command_history": [],
                    "played_character": {"character_id": frame["actor_character_id"], "alive": True},
                    "diagnostics": {"hello": {
                        "expected_ck3_version": CK3_12004.game_version,
                        "expected_ck3_sha256": CK3_12004.executable_sha256,
                    }},
                }
                self.timeline_actions: list[str] = []
                self.timeline_days: list[int] = []
                self.expected_timeline_days = 0

            def take_snapshot(self) -> dict[str, object]:
                return deepcopy(self.frame)

            take_internal_semantic_snapshot = take_snapshot
            take_snapshot_without_native_command_history = take_snapshot

            def capabilities(self) -> dict[str, object]:
                return {"backend_id": "native-headless", "action_steps": [
                    "life-advance", "query-army-strengths-v1", "resume-map", "pause-map",
                    *[f"set-speed-{speed}" for speed in range(1, 6)]], "bridge_capabilities": []}

            def send(self, request: dict[str, object]) -> None:
                self.sent.append(deepcopy(request))
                if request["step"] == paused.STEP:
                    # Correlation was chosen before dispatch. The complete compiled
                    # packet is ingested unchanged, including its original request ID.
                    test_case.assertEqual(request["request_id"], self.packet["request_id"])
                    test_case.assertEqual(request["expected_revision"], frame["native_revision"])
                    response = deepcopy(self.packet)
                else:
                    test_case.assertEqual(request["step"], formal.QUERY_STEP)
                    test_case.assertEqual(request["expected_revision"], self.frame["native_revision"])
                    test_case.assertEqual(request["expected_date_raw"], self.frame["date_raw"])
                    test_case.assertEqual(request["expected_player_character_id"], 29829)
                    # This is an explicitly authored new formal-query input, not
                    # a repaired/relabelled historical native result or enactment.
                    observation = {
                        "available": True, "paused": True,
                        "snapshot_revision": self.frame["native_revision"],
                        "native_snapshot_revision": self.frame["native_revision"],
                        "proof_epoch": self.frame["native_revision"],
                        "date_raw": self.frame["date_raw"], "player_character_id": 29829,
                        "group_key": "crown_authority", "active_law_key": "crown_authority_0",
                        "title_successors": {"primary_title_id": 16777217, "held_titles": [{
                            "title_id": 16777217, "primary": True,
                            "successor_character_ids": [29830]}]},
                        "resources": [{"currency_key": currency,
                            "amount_raw": 50000000 if currency == "prestige" else 0}
                            for currency in formal.CURRENCIES],
                        "candidates": [{"law_key": f"crown_authority_{level}",
                            "is_active": level == 0, "engine_final_only": False,
                            "can_enact": self.formal_ready and level == 1,
                            "blocked_reason": "" if self.formal_ready and level == 1
                                else "source_fixture_native_final_blocked",
                            "costs": [{"currency_key": "prestige", "cost_raw": 20000000}]
                                if level == 1 else []} for level in range(4)],
                    }
                    response = {"type": "command_result", "protocol_version": 1,
                        "request_id": request["request_id"], "ok": True, "result": {
                            "step": formal.QUERY_STEP, "accepted": True, "private_build": True,
                            "advertised": False, "backend_id": "native-headless",
                            "game_version": CK3_12004.game_version,
                            "executable_sha256": CK3_12004.executable_sha256,
                            "read_only": True, "status": "available", "ack": None,
                            "receipt": None, "observation": observation}}
                    self.formal_source_envelopes.append(deepcopy(response))
                self.ingested_types.append(self.state.ingest(response))

            def _h3937_date_hold_active(self, _snapshot: dict[str, object]) -> bool:
                # No war/hold state exists in this explicit peace frame fixture.
                return False

            def _execute_composite_primitive(self, step: str, _starting: object) -> dict[str, object]:
                test_case.assertTrue(step.startswith("set-speed-"))
                self.frame["speed"] = int(step.removeprefix("set-speed-"))
                self.timeline_actions.append(step)
                return {"step": step, "accepted": True, "fixture_external_primitive": True}

            def _wait_for_life_advance_snapshot(self, current, predicate, *, timeout_seconds):
                test_case.assertTrue(predicate(current))
                return current

            def _resume_life_advance(self, _current, actions):
                self.timeline_start = self.frame["date_raw"]
                self.timeline_days = []
                self.frame["paused"] = False
                self.timeline_actions.append("resume-map")
                actions.append({"step": "resume-map", "fixture_external_primitive": True})
                return self.take_snapshot()

            def _wait_for_life_advance_change(self, revision, *, timeout_seconds):
                test_case.assertEqual(revision, self.frame["revision"])
                day = len(self.timeline_days) + 1
                # A missing production horizon/progress connection fails here;
                # the fixture cannot silently finish at the old thirty-day bound.
                test_case.assertLessEqual(day, self.expected_timeline_days)
                self.timeline_days.append(day)
                self.frame.update(date_raw=self.timeline_start + day * 24,
                    revision=self.frame["revision"] + 1,
                    native_revision=self.frame["native_revision"] + 1,
                    snapshot_id=f"source-fixture-timeline:{day}")
                return self.take_snapshot()

            def _pause_life_advance(self, _current, actions):
                self.frame["paused"] = True
                self.timeline_actions.append("pause-map")
                actions.append({"step": "pause-map", "fixture_external_primitive": True})
                return self.take_snapshot()

        async def plan(client, driver: OrdinaryCalendarDriver) -> dict[str, object]:
            token = driver.packet["request_id"].removeprefix("realm-law-read-")
            with patch("xar_autoplayer.bridge.realm_law_paused_private_transport.uuid.uuid4",
                       return_value=SimpleNamespace(hex=token)):
                result = await client.call_tool("ck3_plan_turn", {})
            self.assertIs(result.is_error, False, str(result.content))
            self.assertIsInstance(result.structured_content, dict)
            return result.structured_content

        def advance(driver: OrdinaryCalendarDriver, expected_days: int) -> dict[str, object]:
            driver.expected_timeline_days = expected_days
            progress_rows: list[dict[str, object]] = []
            real_progress = native._life_advance_progressed

            def observed_progress(current, starting, **kwargs):
                actual = real_progress(current, starting, **kwargs)
                progress_rows.append({"date_raw": current["date_raw"],
                    "paused": current["paused"], "horizon_days_override": kwargs.get("horizon_days_override"),
                    "progressed": actual})
                return actual

            starting_date = driver.frame["date_raw"]
            with patch.object(native, "_life_advance_timeline_policy",
                              wraps=native._life_advance_timeline_policy) as timeline, \
                    patch.object(native, "_life_advance_progressed", side_effect=observed_progress):
                result = driver._execute_life_advance(expected_revision=driver.frame["revision"])
            self.assertEqual(timeline.call_count, 1)
            self.assertEqual(timeline.call_args.kwargs["horizon_days"], expected_days)
            self.assertEqual(result["requested_horizon_days"], expected_days)
            self.assertEqual(result["elapsed_days"], expected_days)
            self.assertEqual(result["ending_date_raw"], starting_date + expected_days * 24)
            self.assertEqual(result["progress_status"], "postcondition")
            self.assertIs(result["paused"], True)
            self.assertEqual(driver.timeline_days, list(range(1, expected_days + 1)))
            self.assertTrue(all(row["horizon_days_override"] == expected_days for row in progress_rows))
            self.assertTrue(all(row["paused"] is False for row in progress_rows))
            self.assertTrue(all(row["progressed"] is False for row in progress_rows[:-1]))
            self.assertIs(progress_rows[-1]["progressed"], True)
            return {"actual_driver_result": result, "actual_progress_calls": progress_rows,
                "external_primitive_steps": deepcopy(driver.timeline_actions)}

        def save_state(driver, *, retry=None, pending=None):
            write_json_atomic(driver.state_dir / "crown-authority-formal-v1.json",
                              {"pending": pending, "resolved": None, "retry": retry})

        positive_driver = None
        positive_retry = None
        with patch("xar_autoplayer.bridge.service.choose_one_life_turn", return_value=BASELINE), \
                patch.object(GameplayBridgeService, "plan_nonwar_turn",
                             side_effect=AssertionError("ordinary Crown must use normal planner")):
            for index, filename in enumerate(FILES):
                driver = OrdinaryCalendarDriver(filename.removesuffix(".json"), packets[filename])
                following = None
                async with Client(create_server(driver)) as client:
                    observed = await plan(client, driver)
                    if index < 2:
                        # The same ordinary fallback refreshes formal permission,
                        # while a future same-actor retry consumes its saved hint.
                        following = await plan(client, driver)
                fields = observed["plan"]
                self.assertEqual(fields["selected_step"], "life-advance")
                self.assertEqual(fields["crown_decision"]["status"], "native_blocked")
                self.assertEqual(fields["crown_decision"]["law_key"], LAW)
                native_value = packets[filename]["result"]["realm_law_final_terms"]
                readback = fields["crown_cooldown_readback"]
                self.assertEqual({key: readback[key] for key in native_value}, native_value)
                self.assertEqual(readback["queried_revision"], frame["public_revision"])
                self.assertEqual(readback["queried_native_revision"], frame["native_revision"])
                clock = fields["crown_cooldown_clock"]
                self.assertIs(clock["calendar_deadline_ready"], index < 2)
                retry = fields["crown_calendar_retry"]
                expected_days = (20, 11, 30, 30)[index]
                if index < 2:
                    self.assertEqual(retry, {
                        "source_context": {"bridge_pid": 881,
                            "episode_run_id": driver.frame["episode_run_id"]},
                        "actor_character_id": 29829, "law_key": LAW,
                        "observed_date_raw": BASE_DATE,
                        "retry_date_raw": (53169552, 53169336)[index],
                    })
                    self.assertEqual(consumer.read_crown_authority_state_v1(driver.state_dir)["retry"], retry)
                    self.assertEqual(fields["crown_calendar_retry_source"], "current_query")
                    self.assertEqual(following["plan"]["crown_calendar_retry"], retry)
                    self.assertEqual(following["plan"]["crown_calendar_retry_source"], "reused_hint")
                    self.assertEqual(following["plan"]["crown_decision"]["status"], "native_blocked")
                    self.assertNotIn("crown_cooldown_readback", following["plan"])
                else:
                    self.assertIsNone(retry)
                record = {"scene": filename.removesuffix(".json"), "registered_plan": observed,
                    "following_registered_plan": following,
                    "native_requests": deepcopy(driver.sent),
                    "formal_quotes_source_shaped": deepcopy(driver.formal_source_envelopes),
                    **advance(driver, expected_days)}
                expected_steps = [formal.QUERY_STEP, paused.STEP]
                if index < 2:
                    expected_steps.append(formal.QUERY_STEP)
                self.assertEqual([row["step"] for row in driver.sent], expected_steps)
                self.assertEqual(driver.ingested_types, ["command_result"] * len(expected_steps))
                self.assertEqual(driver.state._command_results, {})
                self.observations.append(record)
                if index == 0:
                    positive_driver, positive_retry = driver, deepcopy(retry)

            # This due frame is a new explicitly source-shaped formal quote.
            # No future native permission, submission or material success is claimed.
            driver = positive_driver
            driver.formal_ready = True
            prior_count = len(driver.sent)
            self.assertEqual(driver.frame["date_raw"], positive_retry["retry_date_raw"])
            async with Client(create_server(driver)) as client:
                due = await plan(client, driver)
            self.assertEqual(due["plan"]["selected_step"], formal.SUBMIT_STEP)
            self.assertEqual(due["plan"]["crown_decision"]["status"], "ready")
            self.assertEqual(dict(due["plan"]["crown_decision"]["budgets_raw"]), {"prestige": 20000000})
            self.assertEqual(due["plan"]["crown_readback"]["date_raw"], driver.frame["date_raw"])
            self.assertEqual(due["plan"]["crown_readback"]["queried_native_revision"], driver.frame["native_revision"])
            self.assertIsNone(due["plan"]["crown_calendar_retry"])
            self.assertIsNone(consumer.read_crown_authority_state_v1(driver.state_dir)["retry"])
            self.assertEqual([row["step"] for row in driver.sent[prior_count:]], [formal.QUERY_STEP])
            self.observations.append({"scene": "due-fresh-source-shaped-native-final-quote",
                "registered_plan": due, "native_requests": deepcopy(driver.sent[prior_count:]),
                "formal_quote_source_shaped": deepcopy(driver.formal_source_envelopes[-1]),
                "action_submitted": False, "future_native_permission_qualified": False})

            pending_driver = OrdinaryCalendarDriver("pending", packets[FILES[0]])
            pending = {"stage": "receipt_pending", "action_id": "source-fixture-pending-crown",
                "law_key": LAW, "source_context": positive_retry["source_context"],
                "actor_character_id": 29829}
            save_state(pending_driver, retry=positive_retry, pending=pending)
            async with Client(create_server(pending_driver)) as client:
                pending_plan = await plan(client, pending_driver)
            self.assertEqual(pending_plan["plan"]["selected_step"], formal.RECEIPT_STEP)
            self.assertEqual(pending_plan["plan"]["crown_pending_action"], pending)
            self.assertEqual(pending_driver.sent, [])
            self.assertEqual(consumer.crown_authority_retry_horizon_days_v1(
                pending_driver, pending_driver.take_snapshot(), 30), 30)
            self.observations.append({"scene": "pending-independent-receipt-priority",
                "registered_plan": pending_plan, "native_requests": []})

            disabled = OrdinaryCalendarDriver("readonly-disabled", packets[FILES[0]])
            disabled.allow_private_realm_law_paused_query = False
            save_state(disabled, retry=positive_retry)
            async with Client(create_server(disabled)) as client:
                disabled_plan = await plan(client, disabled)
            self.assertEqual(disabled_plan["plan"]["selected_step"], "life-advance")
            self.assertIsNone(disabled_plan["plan"]["crown_calendar_retry"])
            self.assertEqual(disabled_plan["plan"]["crown_cooldown_unavailable_reason"],
                             "private_realm_law_paused_query_disabled")
            self.assertIsNone(consumer.read_crown_authority_state_v1(disabled.state_dir)["retry"])
            self.assertEqual([row["step"] for row in disabled.sent], [formal.QUERY_STEP])
            self.observations.append({"scene": "readonly-opt-in-disabled-original-horizon",
                "registered_plan": disabled_plan, "native_requests": deepcopy(disabled.sent),
                **advance(disabled, 30)})

            urgent = OrdinaryCalendarDriver("urgent", packets[FILES[0]])
            save_state(urgent, retry=positive_retry)
            urgent_baseline = {**BASELINE, "phase": "native_war_army_query",
                               "selected_step": "query-army-strengths-v1"}
            with patch("xar_autoplayer.bridge.service.choose_one_life_turn", return_value=urgent_baseline):
                async with Client(create_server(urgent)) as client:
                    urgent_plan = await plan(client, urgent)
            self.assertEqual(urgent_plan["plan"]["selected_step"], "query-army-strengths-v1")
            self.assertEqual(urgent.sent, [])
            self.assertEqual(consumer.read_crown_authority_state_v1(urgent.state_dir)["retry"], positive_retry)
            self.observations.append({"scene": "urgent-selection-priority",
                "registered_plan": urgent_plan, "native_requests": []})

        self.assertEqual(packets, originals)
        self.assertEqual(len(self.observations), 8)
        self.evidence.update(cases=8, actual_registered_ordinary_plan=True,
            actual_native_driver_advance_cases=5, actual_progress_predicate=True,
            scheduled_positive_horizon_days=[20, 11], unprojected_horizon_days=[30, 30],
            disabled_horizon_days=30, whole_native_packets_unchanged=True,
            formal_quotes_source_shaped=True, due_fresh_quote_consumed=True,
            law_action_calls=0, material_receipt_claims=0, live=False, m7_complete=False)


def main() -> int:
    if not __debug__:
        raise RuntimeError("FIRST consumer requires Python without -O")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--native-wire-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if re.fullmatch(r"[0-9a-fA-F]{40}", args.source_sha) is None:
        parser.error("--source-sha must be Root's complete 40-hex source qualification pin")
    args.output_dir.mkdir(parents=True, exist_ok=False)
    observations: list[dict[str, object]] = []
    evidence: dict[str, object] = {}
    CrownCalendarRetryRegisteredPlanTest.args = args
    CrownCalendarRetryRegisteredPlanTest.observations = observations
    CrownCalendarRetryRegisteredPlanTest.evidence = evidence
    suite = unittest.TestSuite([CrownCalendarRetryRegisteredPlanTest(SELECTED_METHOD)])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    successful = result.wasSuccessful() and result.testsRun == 1 and not result.skipped
    report = {
        "schema": "xar.ck3.crown-authority-calendar-retry-registered-plan12004/v1",
        "status": "GREEN" if successful else "RED",
        "scope": "M7 existing Native58 calendar retry ordinary plan and actual advance FIRST",
        "source_root": str(args.source_root), "source_sha": args.source_sha,
        "source_pin_owner": "Root qualification; author performs no Git or hash",
        "native_wire_dir": str(args.native_wire_dir), "whole_wire_files": list(FILES),
        "selected_method": SELECTED_METHOD, "tests_run": result.testsRun, "compound_methods": 1,
        "scenes_attempted": len(observations), "old_cases_replayed": 0,
        "native_producer_runs": 0, "whole_native_packets_constructed": False,
        "whole_native_packets_repaired": False, "whole_native_request_ids_relabelled": False,
        "pipe_operations": 0, "game_operations": 0, "game_actions": 0,
        "new_exe_bytes": 0, "live": False,
        "failures": [trace for _, trace in result.failures],
        "errors": [trace for _, trace in result.errors], **evidence,
    }
    for name, value in (("OBSERVED.json", observations), ("RESULT.json", report)):
        with (args.output_dir / name).open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if successful else 1


if __name__ == "__main__":
    raise SystemExit(main())
