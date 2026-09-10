#!/usr/bin/env python3
"""Offline continuation tests; synthetic native frames are never live evidence."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import zg361_phase2_terminal_stages_action_cell as cell


PLAYER = 33596113
SUBJECT = 202


def typed(value: object) -> dict[str, object]:
    return {"status": "available", "value": value, "unavailable_reason": None}


def saved(name: str, character: int) -> dict[str, object]:
    return {"name": name, "scope": {"typed_identity": {
        "status": "available", "kind": "character", "character_id": character,
    }}}


class Service:
    def __init__(self) -> None:
        self.revision = 1
        self.date = 100000
        self.current_stage = None
        self.retain_ack_event = False
        self.manager_terminal = True
        self.saved_ok = True
        self.fail_entry_once = None
        self.visits = []
        self.actions = []
        self.progress_inputs = []
        self.manager_queries = []
        self.saves = []

    def snapshot(self) -> dict[str, object]:
        return {
            "revision": self.revision, "date_raw": self.date,
            "paused": True, "map_ready": True,
            "diagnostics": {"bridge_pid": 700, "connection_generation": 2},
            "played_character": {"character_id": PLAYER},
            "active_event": None if self.current_stage is None else {
                "instance_id": 100 + self.current_stage,
                "option_count": 3 if self.current_stage == 11 else 1,
            },
        }

    def enter(self, service: object, **kwargs: object) -> dict[str, object]:
        self.assert_same(service)
        stage = next(stage for stage, key in cell.EVENTS.items()
                     if key == kwargs["pause_on_event_definition_key"])
        self.visits.append(stage)
        progress = kwargs["evidence_out"]
        self.progress_inputs.append(copy.deepcopy(progress))
        progress["timeline_interrupt_drains"].append({"synthetic_progress_to_stage": stage})
        if self.fail_entry_once == stage:
            self.fail_entry_once = None
            self.date += 24
            raise TimeoutError("synthetic entry timeout after preserved progress")
        self.current_stage = stage
        self.revision += 1
        return {"result": "GREEN"}

    def assert_same(self, service: object) -> None:
        if service is not self:
            raise AssertionError("entry used a different bound service")

    def query_current_event_window_context_v1(self, event_instance_id: int, *, expected_revision: int) -> dict[str, object]:
        if event_instance_id != 100 + self.current_stage or expected_revision != self.revision:
            raise AssertionError("event context query did not bind the current frame")
        scopes = []
        if self.current_stage == 10:
            scopes = [saved("zg361_mg_f_ticket_owner", SUBJECT),
                      saved("zg361_mg_f_ticket_subject", PLAYER)]
        elif self.current_stage == 11:
            scopes = [saved("zg361_we_al_owner", PLAYER),
                      saved("zg361_we_al_subject", SUBJECT)]
        return {"status": "available", "current_event_window_context": {
            "current_event_instance_id": event_instance_id,
            "event_definition_key": cell.EVENTS[self.current_stage],
            "root_scope": {"typed_identity": {
                "status": "available", "kind": "character", "character_id": PLAYER,
            }},
            "readiness": {name: True for name in (
                "event_definition_identity_ready", "root_scope_ready",
                "saved_scopes_ready", "option_presentation_ready",
            )},
            "saved_scopes": scopes,
            "options": [{"native_option_index": index, "shown": True, "enabled": True}
                        for index in range(3 if self.current_stage == 11 else 1)],
        }}

    def query_zhongguo_manager_governance_snapshot_v1(self, nonce: str, **kwargs: object) -> dict[str, object]:
        self.manager_queries.append((nonce, kwargs))
        if kwargs != {"expected_revision": self.revision,
                      "owner_character_id": SUBJECT, "subject_character_id": PLAYER}:
            raise AssertionError("manager observation did not bind the saved F-case")
        return {"status": "available", "readiness": {"ready": True}, "f_case": {
            "owner_character_id": typed(SUBJECT), "subject_character_id": typed(PLAYER),
            "state": typed(5 if self.manager_terminal else 3),
            "active": typed(not self.manager_terminal),
        }}

    def select_event_option(self, option_number: int, *, event_instance_id: int, expected_revision: int) -> dict[str, object]:
        if expected_revision != self.revision or event_instance_id != 100 + self.current_stage:
            raise AssertionError("selection did not bind the current event")
        self.actions.append((self.current_stage, option_number))
        if not self.retain_ack_event:
            self.current_stage = None
            self.revision += 1
        return {"accepted": True, "status": "submitted"}

    def save_checkpoint(self, *, expected_revision: int) -> dict[str, object]:
        if expected_revision != self.revision:
            raise AssertionError("checkpoint revision is stale")
        self.saves.append(self.snapshot())
        return {"accepted": self.saved_ok,
                "checkpoint": {"status": "saved" if self.saved_ok else "failed",
                               "path": "synthetic-stage11.ck3"}}


class TerminalStagesTests(unittest.TestCase):
    def run_cell(self, service: Service, directory: Path) -> dict[str, object]:
        with patch.object(cell.entry, "enter_promotion_source_checkpoint_v1", side_effect=service.enter):
            with self.assertRaises(cell.TerminalStagesError) as raised:
                cell.run_terminal_stages(service, evidence_directory=directory,
                                         request_nonce="synthetic.terminal")
        return raised.exception.evidence

    def test_independent_stage_receipts_then_owner_view_park(self) -> None:
        service = Service()
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            result = self.run_cell(service, directory)
            self.assertEqual(service.visits, [9, 10, 11])
            self.assertEqual(service.actions, [(9, 1), (10, 1)])
            self.assertEqual(service.manager_queries[0][0], "synthetic.terminal.10")
            receipts = result["p1_acceptance_evidence"]["central_stage_terminals"]
            self.assertEqual(set(receipts), {"9", "10"})
            for stage in (9, 10):
                row = receipts[str(stage)]
                self.assertEqual((row["result"], row["stage"], row["event_definition_key"]),
                                 ("GREEN", stage, cell.EVENTS[stage]))
                self.assertIs(row["provider_observed"], True)
                self.assertIs(row["terminal_postcondition_verified"], True)
                self.assertIs(row["action_ack_is_business_postcondition"], False)
                self.assertIs(row["acknowledgement"]["old_event_instance_removed"], True)
            self.assertEqual(result["result"], "RED")
            self.assertIn("owner-view Workforce", result["failure_reason"])
            self.assertEqual(result["stage11_park"]["subject_character_id"], SUBJECT)
            self.assertIs(result["stage11_park"]["selection_attempted"], False)
            self.assertIs(result["missing_observation"]["player_switch_attempted"], False)
            self.assertIs(result["af5_same_slice_required"], False)
            self.assertEqual(len(service.saves), 1)
            self.assertEqual(json.loads((directory / "terminal-stages.json").read_text()), result)
            self.assertEqual(json.loads((directory / "attempt-001.json").read_text()), result)

    def test_ack_alone_does_not_make_terminal_receipt(self) -> None:
        service = Service()
        service.retain_ack_event = True
        with tempfile.TemporaryDirectory() as temporary:
            result = self.run_cell(service, Path(temporary))
        self.assertEqual(result["p1_acceptance_evidence"]["central_stage_terminals"], {})
        self.assertIn("snapshot did not verify", result["failure_reason"])
        self.assertEqual(service.visits, [9])

    def test_manager_summary_without_native_terminal_is_not_acknowledged(self) -> None:
        service = Service()
        service.manager_terminal = False
        with tempfile.TemporaryDirectory() as temporary:
            result = self.run_cell(service, Path(temporary))
        self.assertEqual(set(result["p1_acceptance_evidence"]["central_stage_terminals"]), {"9"})
        self.assertEqual(service.actions, [(9, 1)])
        self.assertIn("F-case has not reached", result["failure_reason"])
        self.assertEqual(result["stage_observations"]["10"]["provider"]["f_case"]["state"]["value"], 3)

    def test_retry_retains_horizon_progress_completed_receipt_and_failed_attempt(self) -> None:
        service = Service()
        service.fail_entry_once = 10
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            first = self.run_cell(service, directory)
            first_bytes = (directory / "attempt-001.json").read_bytes()
            second = self.run_cell(service, directory)
            self.assertEqual(service.visits, [9, 10, 10, 11])
            self.assertEqual(service.actions, [(9, 1), (10, 1)])
            self.assertEqual(service.progress_inputs[2], first["progress_out"])
            self.assertEqual(first["progress_out"]["absolute_end_date_raw"],
                             second["progress_out"]["absolute_end_date_raw"])
            self.assertEqual(first["p1_acceptance_evidence"]["central_stage_terminals"]["9"],
                             second["p1_acceptance_evidence"]["central_stage_terminals"]["9"])
            self.assertEqual((directory / "attempt-001.json").read_bytes(), first_bytes)
            self.assertEqual(second["attempt"], 2)
            self.assertTrue((directory / "attempt-002.json").is_file())

    def test_failed_park_save_is_reported_as_checkpoint_failure(self) -> None:
        service = Service()
        service.saved_ok = False
        with tempfile.TemporaryDirectory() as temporary:
            result = self.run_cell(service, Path(temporary))
        self.assertIn("parked checkpoint was not saved", result["failure_reason"])
        self.assertEqual(service.actions, [(9, 1), (10, 1)])


class OwnerService(Service):
    """Distinct played owner and product-owned subject; independent native query."""

    def __init__(self, *, terminal_kind: str = "history_accruing", early_na: bool = False) -> None:
        super().__init__()
        self.terminal_kind = terminal_kind
        self.early_na = early_na
        self.workforce_selected = False
        self.callback_complete = False
        self.owner_ready = True
        self.fail_after_action_once = False
        self.callback_reads = []
        self._frames = json.loads((cell.ROOT / "ck3_autonomous_player/tests/fixtures/zhongguo_workforce_owner_snapshot_v1.json").read_text())["frames"]

    def query_zhongguo_workforce_owner_snapshot_v1(self, nonce: str, *, expected_revision: int) -> dict[str, object]:
        if expected_revision != self.revision:
            raise AssertionError("owner query bound a stale frame")
        key = "not_applicable_without_m360_source" if self.early_na else (
            self.terminal_kind if self.workforce_selected else "pre_action"
        )
        frame = copy.deepcopy(self._frames[key])
        frame.update(player_character_id=PLAYER, subject_character_id=SUBJECT,
                     request_nonce=nonce, snapshot_revision=self.revision, date_raw=self.date)
        for group in frame["workforce"].values():
            for name in ("owner_character_id", "subject_character_id"):
                if name in group and group[name]["status"] == "available":
                    group[name]["value"] = PLAYER if name == "owner_character_id" else SUBJECT
        frame["readiness"]["ready"] = self.owner_ready
        if self.workforce_selected and self.callback_complete:
            frame["workforce"]["central"]["stage11_status"] = typed(2)
        self.callback_reads.append((self.workforce_selected, self.callback_complete, frame["terminal"]))
        return frame

    def enter(self, service: object, **kwargs: object) -> dict[str, object]:
        if kwargs["pause_on_event_definition_key"] != cell.EVENTS[11]:
            return super().enter(service, **kwargs)
        probe = kwargs["terminal_observation_probe"]
        result = probe(self.snapshot())
        if result is not None:
            self.visits.append(11)
            return {"result": "GREEN", "terminal_observation": result}
        if self.workforce_selected:
            self.visits.append(11)
            if self.fail_after_action_once:
                self.fail_after_action_once = False
                raise TimeoutError("synthetic interruption waiting for the Central callback")
            # Unit orchestration model; the separate timeline test below runs
            # actual production map-control/date advancement through this seam.
            self.date += 48
            self.revision += 1
            self.callback_complete = True
            result = probe(self.snapshot())
            if result is None:
                raise AssertionError("terminal remained false after the callback")
            return {"result": "GREEN", "terminal_observation": result}
        return super().enter(service, **kwargs)

    def select_event_option(self, option_number: int, **kwargs: object) -> dict[str, object]:
        stage = self.current_stage
        result = super().select_event_option(option_number, **kwargs)
        if stage == 11:
            self.workforce_selected = True
        return result


class OwnerTerminalTests(unittest.TestCase):
    def run_cell(self, service: OwnerService, directory: Path) -> dict[str, object]:
        with patch.object(cell.entry, "enter_promotion_source_checkpoint_v1", side_effect=service.enter), \
             patch("zhongguo_phase2_workforce_action.time.sleep", return_value=None):
            return cell.run_terminal_stages(service, evidence_directory=directory,
                                           request_nonce="synthetic.owner")

    def test_m360_observation_waits_for_the_independent_central_callback(self) -> None:
        for kind in ("history_accruing", "success"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temporary:
                service = OwnerService(terminal_kind=kind)
                result = self.run_cell(service, Path(temporary))
                row = result["p1_acceptance_evidence"]["central_stage_terminals"]["11"]
                self.assertEqual(result["result"], "GREEN")
                self.assertEqual(service.actions, [(9, 1), (10, 1), (11, 1)])
                self.assertEqual((row["provider_domain"], row["terminal_state"], row["terminal_kind"]),
                                 ("workforce", "closed", kind))
                self.assertIs(row["player_switch_attempted"], False)
                self.assertEqual(row["provider_observation"]["subject_character_id"], SUBJECT)
                self.assertIn((True, False, True), service.callback_reads)
                self.assertIn((True, True, True), service.callback_reads)
                self.assertEqual(len(service.saves), 2)

    def test_na_without_m360_event_or_source_returns_the_na_terminal(self) -> None:
        service = OwnerService(early_na=True)
        with tempfile.TemporaryDirectory() as temporary:
            result = self.run_cell(service, Path(temporary))
        self.assertEqual(service.actions, [(9, 1), (10, 1)])
        row = result["p1_acceptance_evidence"]["central_stage_terminals"]["11"]
        self.assertEqual(row["terminal_state"], "terminal_na")
        self.assertIsNone(row["m360_action"])
        self.assertNotIn("stage11_park", result)

    def test_unready_owner_query_parks_without_selecting_m360(self) -> None:
        service = OwnerService()
        service.owner_ready = False
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(cell.TerminalStagesError) as raised:
                self.run_cell(service, Path(temporary))
        self.assertIn("observation is missing", str(raised.exception))
        self.assertEqual(service.actions, [(9, 1), (10, 1)])

    def test_retry_after_m360_waits_without_replaying_the_choice(self) -> None:
        service = OwnerService()
        service.fail_after_action_once = True
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            with self.assertRaises(cell.TerminalStagesError) as raised:
                self.run_cell(service, directory)
            self.assertIsNotNone(raised.exception.evidence["stage11_action"])
            first = (directory / "attempt-001.json").read_bytes()
            result = self.run_cell(service, directory)
            self.assertEqual((directory / "attempt-001.json").read_bytes(), first)
        self.assertEqual(result["result"], "GREEN")
        self.assertEqual(service.actions.count((11, 1)), 1)


class ProductionTerminalTimelineTests(unittest.TestCase):
    def test_actual_driver_advances_to_callback_and_stops_without_m360_event(self) -> None:
        from test_zg361_phase2_af5_timeline import ScheduledCompensationService

        class DelayedCallbackService(ScheduledCompensationService):
            def __init__(self, *, already_na: bool) -> None:
                super().__init__()
                self.active_instance = None
                self.active_indices = ()
                self.already_na = already_na
                self.observed_stages = []

            def query_zhongguo_workforce_owner_snapshot_v1(self, nonce: str, *, expected_revision: int) -> dict[str, object]:
                self._require_revision(expected_revision)
                if not self.paused:
                    raise AssertionError("owner observation requires a paused frame")
                stage = 3 if self.already_na else (2 if self.running_days >= 2 else 1)
                self.observed_stages.append(stage)
                return {
                    "status": "available", "readiness": {"ready": True},
                    "terminal": True,
                    "terminal_kind": "not_applicable" if self.already_na else "history_accruing",
                    "player_character_id": 32904, "subject_character_id": 361,
                    "workforce": {"central": {"stage11_status": typed(stage)}},
                }

        for already_na in (False, True):
            with self.subTest(already_na=already_na):
                service = DelayedCallbackService(already_na=already_na)

                def probe(snapshot: dict[str, object]) -> dict[str, object] | None:
                    response = service.query_zhongguo_workforce_owner_snapshot_v1(
                        "synthetic.driver", expected_revision=snapshot["revision"],
                    )
                    return response if cell._stage11_terminal(response) else None

                result = cell.entry.enter_promotion_source_checkpoint_v1(
                    service, timeout_seconds=3.0, prefer_natural_cycle=True,
                    pause_on_event_definition_key="zg361we.360",
                    terminal_observation_probe=probe,
                    clock=lambda: service.elapsed, sleeper=service.sleep,
                )
                self.assertEqual(result["result"], "GREEN")
                self.assertEqual(result["readiness"], "paused-independent-terminal-observation")
                self.assertIsNone(result["target_binding"])
                self.assertEqual(service.running_days, 0 if already_na else 2)
                self.assertTrue(service.paused)
                self.assertFalse(service.event_queries)
                self.assertFalse(any(action.startswith("select") for action in service.actions))
                if already_na:
                    self.assertEqual(service.actions, [])
                else:
                    self.assertIn(1, service.observed_stages)
                    self.assertEqual(service.observed_stages[-1], 2)
                    self.assertIn("resume-map", service.actions)
                    self.assertIn("pause-map", service.actions)


if __name__ == "__main__":
    unittest.main()
