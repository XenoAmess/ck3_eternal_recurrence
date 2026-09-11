#!/usr/bin/env python3
"""Offline continuation tests; synthetic native frames are never live evidence."""

from __future__ import annotations

import copy
import hashlib
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
        self.saved_ok = True
        self.fail_save_call = None
        self.source_selector_ready = True
        self.fail_entry_once = None
        self.visits = []
        self.actions = []
        self.progress_inputs = []
        self.entry_kwargs = []
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
        self.entry_kwargs.append(copy.deepcopy(kwargs))
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
        if self.current_stage == 11:
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
        accepted = self.saved_ok and len(self.saves) != self.fail_save_call
        return {"accepted": accepted,
                "checkpoint": {"status": "saved" if accepted else "failed",
                               "path": "synthetic-stage11.ck3"}}

    def query_zhongguo_manager_subordinate_selector_v1(
        self, nonce: str, *, expected_revision: int
    ) -> dict[str, object]:
        if expected_revision != self.revision:
            raise AssertionError("selector bound a stale frame")
        return {
            "status": "available" if self.source_selector_ready else "unavailable",
            "provider_observed": self.source_selector_ready,
            "request_nonce": nonce,
            "readiness": {"ready": self.source_selector_ready},
            "selection": (
                {
                    "manager_character_id": SUBJECT,
                    "subordinate_character_id": SUBJECT + 1,
                }
                if self.source_selector_ready
                else None
            ),
        }


class TerminalStagesTests(unittest.TestCase):
    def test_terminal_portfolio_waits_when_central_callback_is_not_yet_published(self) -> None:
        frame = json.loads(
            (
                cell.ROOT
                / "ck3_autonomous_player/tests/fixtures/zhongguo_workforce_owner_snapshot_v1.json"
            ).read_text()
        )["frames"]["not_applicable_without_m360_source"]
        frame["workforce"]["central"]["stage11_status"] = {
            "status": "unavailable",
            "value": None,
            "unavailable_reason": "variable_absent",
        }
        self.assertIs(frame["terminal"], True)
        self.assertEqual(frame["terminal_kind"], "not_applicable")
        self.assertIsNone(cell._stage11_terminal(frame))

    def test_stage10_source_archive_is_byte_bound_and_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "native.ck3"
            source.write_bytes(b"stage10-source")
            digest = hashlib.sha256(source.read_bytes()).hexdigest().upper()
            save_result = {
                "accepted": True,
                "checkpoint": {
                    "status": "saved",
                    "path": str(source.resolve()),
                    "size": source.stat().st_size,
                    "sha256": digest,
                },
            }
            target = root / "archive.ck3"
            first = cell._archive_checkpoint(save_result, target)
            second = cell._archive_checkpoint(save_result, target)
            self.assertEqual(first, second)
            self.assertEqual(target.read_bytes(), source.read_bytes())

            target.write_bytes(b"drift")
            with self.assertRaisesRegex(ValueError, "different bytes"):
                cell._archive_checkpoint(save_result, target)

    def run_cell(self, service: Service, directory: Path) -> dict[str, object]:
        archived = {
            "path": str(directory / "stage10-player-subject-source.ck3"),
            "bytes": 3,
            "sha256": "A" * 64,
        }
        with patch.object(cell.entry, "enter_promotion_source_checkpoint_v1", side_effect=service.enter), \
             patch.object(cell, "_archive_checkpoint", return_value=archived):
            with self.assertRaises(cell.TerminalStagesError) as raised:
                cell.run_terminal_stages(service, evidence_directory=directory,
                                         request_nonce="synthetic.terminal")
        return raised.exception.evidence

    def test_independent_stage_receipts_then_owner_view_park(self) -> None:
        service = Service()
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            result = self.run_cell(service, directory)
            self.assertEqual(service.visits, [9, 11])
            self.assertEqual(
                [row["progress_sample_interval_days"] for row in service.entry_kwargs],
                [cell.NAVIGATION_PROGRESS_SAMPLE_DAYS] * 2,
            )
            self.assertEqual(service.actions, [(9, 1)])
            receipts = result["p1_acceptance_evidence"]["central_stage_terminals"]
            self.assertEqual(set(receipts), {"9"})
            row = receipts["9"]
            self.assertEqual((row["result"], row["stage"], row["event_definition_key"]),
                             ("GREEN", 9, cell.EVENTS[9]))
            self.assertIs(row["provider_observed"], True)
            self.assertIs(row["terminal_postcondition_verified"], True)
            self.assertIs(row["action_ack_is_business_postcondition"], False)
            self.assertIs(row["acknowledgement"]["old_event_instance_removed"], True)
            self.assertEqual(result["owned_stage_sequence"], [9, 11])
            self.assertIs(result["independent_stage10_required"], True)
            self.assertEqual(result["independent_stage10_event_definition_key"],
                             cell.INDEPENDENT_STAGE10_EVENT)
            self.assertEqual(result["result"], "RED")
            self.assertIn("owner-view Workforce", result["failure_reason"])
            self.assertEqual(result["stage11_park"]["subject_character_id"], SUBJECT)
            self.assertIs(result["stage11_park"]["selection_attempted"], False)
            self.assertIs(result["missing_observation"]["player_switch_attempted"], False)
            self.assertIs(result["af5_same_slice_required"], False)
            self.assertEqual(len(service.saves), 2)
            source = result["stage10_source"]
            self.assertEqual(source["result"], "GREEN")
            self.assertEqual(source["source_event_definition_key"], cell.EVENTS[9])
            self.assertEqual(source["selected_manager_character_id"], SUBJECT)
            self.assertIs(source["selection_attempted"], False)
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

    def test_player_visible_manager_summary_is_not_part_of_owned_sequence(self) -> None:
        service = Service()
        with tempfile.TemporaryDirectory() as temporary:
            result = self.run_cell(service, Path(temporary))
        self.assertEqual(set(result["p1_acceptance_evidence"]["central_stage_terminals"]), {"9"})
        self.assertEqual(service.actions, [(9, 1)])
        self.assertNotIn(10, service.visits)
        self.assertNotIn("10", result["stage_observations"])
        self.assertIn("owner-view Workforce", result["failure_reason"])

    def test_retry_retains_horizon_progress_completed_receipt_and_failed_attempt(self) -> None:
        service = Service()
        service.fail_entry_once = 11
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            first = self.run_cell(service, directory)
            first_bytes = (directory / "attempt-001.json").read_bytes()
            second = self.run_cell(service, directory)
            self.assertEqual(service.visits, [9, 11, 11])
            self.assertEqual(service.actions, [(9, 1)])
            self.assertEqual(service.progress_inputs[2], first["progress_out"])
            self.assertEqual(first["progress_out"]["absolute_end_date_raw"],
                             second["progress_out"]["absolute_end_date_raw"])
            self.assertEqual(first["p1_acceptance_evidence"]["central_stage_terminals"]["9"],
                             second["p1_acceptance_evidence"]["central_stage_terminals"]["9"])
            self.assertEqual((directory / "attempt-001.json").read_bytes(), first_bytes)
            self.assertEqual(second["attempt"], 2)
            self.assertTrue((directory / "attempt-002.json").is_file())

    def test_explicit_game_day_bound_is_persisted_and_cannot_change_on_retry(self) -> None:
        service = Service()
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            archived = {
                "path": str(directory / "stage10-player-subject-source.ck3"),
                "bytes": 3,
                "sha256": "A" * 64,
            }
            with patch.object(
                cell.entry,
                "enter_promotion_source_checkpoint_v1",
                side_effect=service.enter,
            ), patch.object(cell, "_archive_checkpoint", return_value=archived):
                with self.assertRaises(cell.TerminalStagesError) as raised:
                    cell.run_terminal_stages(
                        service,
                        evidence_directory=directory,
                        request_nonce="synthetic.bounded",
                        max_advance_days=17,
                    )
                with self.assertRaisesRegex(
                    ValueError, "retry changed its game-day bound"
                ):
                    cell.run_terminal_stages(
                        service,
                        evidence_directory=directory,
                        request_nonce="synthetic.bounded",
                        max_advance_days=18,
                    )
            state = raised.exception.evidence
            self.assertEqual(state["configured_max_advance_days"], 17)
            self.assertEqual(
                state["progress_out"]["absolute_end_date_raw"],
                100000 + 17 * 24,
            )

    def test_failed_park_save_is_reported_as_checkpoint_failure(self) -> None:
        service = Service()
        service.fail_save_call = 2
        with tempfile.TemporaryDirectory() as temporary:
            result = self.run_cell(service, Path(temporary))
        self.assertIn("parked checkpoint was not saved", result["failure_reason"])
        self.assertEqual(service.actions, [(9, 1)])

    def test_ineligible_stage10_source_does_not_block_owned_stages(self) -> None:
        service = Service()
        service.source_selector_ready = False
        with tempfile.TemporaryDirectory() as temporary:
            result = self.run_cell(service, Path(temporary))
        self.assertEqual(service.actions, [(9, 1)])
        self.assertEqual(result["stage10_source"]["result"], "INELIGIBLE")
        self.assertNotIn("checkpoint", result["stage10_source"])


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
        self.transient_query_error_once = None
        self.callback_reads = []
        self.stage11_direct_kwargs = []
        self._frames = json.loads((cell.ROOT / "ck3_autonomous_player/tests/fixtures/zhongguo_workforce_owner_snapshot_v1.json").read_text())["frames"]

    def query_zhongguo_workforce_owner_snapshot_v1(self, nonce: str, *, expected_revision: int) -> dict[str, object]:
        if self.transient_query_error_once is not None:
            error = self.transient_query_error_once
            self.transient_query_error_once = None
            self.revision += 1
            raise cell.BridgeUnavailableError(
                f"native gameplay step failed: {error}"
            )
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
        self.stage11_direct_kwargs.append(copy.deepcopy(kwargs))
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
        archived = {
            "path": str(directory / "stage10-player-subject-source.ck3"),
            "bytes": 3,
            "sha256": "A" * 64,
        }
        with patch.object(cell.entry, "enter_promotion_source_checkpoint_v1", side_effect=service.enter), \
             patch.object(cell, "_archive_checkpoint", return_value=archived), \
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
                self.assertEqual(service.actions, [(9, 1), (11, 1)])
                self.assertEqual((row["provider_domain"], row["terminal_state"], row["terminal_kind"]),
                                 ("workforce", "closed", kind))
                self.assertIs(row["player_switch_attempted"], False)
                self.assertEqual(row["provider_observation"]["subject_character_id"], SUBJECT)
                self.assertIn((True, False, True), service.callback_reads)
                self.assertIn((True, True, True), service.callback_reads)
                self.assertEqual(len(service.saves), 3)

    def test_stage11_only_source_does_not_replay_stage9_or_claim_its_receipt(self) -> None:
        service = OwnerService()
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            with patch.object(
                cell.entry,
                "enter_promotion_source_checkpoint_v1",
                side_effect=service.enter,
            ), patch("zhongguo_phase2_workforce_action.time.sleep", return_value=None):
                result = cell.run_terminal_stages(
                    service,
                    evidence_directory=directory,
                    request_nonce="synthetic.stage11-only",
                    start_stage=11,
                )
        self.assertEqual(result["result"], "GREEN")
        self.assertEqual(result["configured_start_stage"], 11)
        self.assertEqual(result["owned_stage_sequence"], [11])
        self.assertIs(result["independent_stage10_required"], False)
        self.assertEqual(service.visits, [11, 11])
        self.assertEqual(service.actions, [(11, 1)])
        self.assertEqual(
            set(result["p1_acceptance_evidence"]["central_stage_terminals"]),
            {"11"},
        )
        self.assertNotIn("stage10_source", result)

    def test_retry_cannot_change_starting_stage(self) -> None:
        service = OwnerService()
        service.fail_after_action_once = True
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            with patch.object(
                cell.entry,
                "enter_promotion_source_checkpoint_v1",
                side_effect=service.enter,
            ), patch("zhongguo_phase2_workforce_action.time.sleep", return_value=None):
                with self.assertRaises(cell.TerminalStagesError):
                    cell.run_terminal_stages(
                        service,
                        evidence_directory=directory,
                        request_nonce="synthetic.stage11-retry",
                        start_stage=11,
                    )
                with self.assertRaisesRegex(
                    ValueError, "retry changed its starting stage"
                ):
                    cell.run_terminal_stages(
                        service,
                        evidence_directory=directory,
                        request_nonce="synthetic.stage11-retry",
                        start_stage=9,
                    )

    def test_owner_query_revision_race_rebinds_without_restarting_or_input(self) -> None:
        errors = (
            "ZhongGuo workforce owner revision is stale",
            "ZhongGuo workforce owner snapshot changed or is not ready",
        )
        for error in errors:
            with self.subTest(error=error), tempfile.TemporaryDirectory() as temporary:
                service = OwnerService()
                service.transient_query_error_once = error
                result = self.run_cell(service, Path(temporary))
                self.assertEqual(result["result"], "GREEN")
                self.assertEqual(result["stage11_consecutive_query_rebinds"], 0)
                self.assertEqual(len(result["stage11_query_rebinds"]), 1)
                rebind = result["stage11_query_rebinds"][0]
                self.assertIn(error, rebind["error"])
                self.assertIs(rebind["state_mutation_submitted"], False)
                self.assertEqual(service.actions, [(9, 1), (11, 1)])

    def test_na_without_m360_event_or_source_returns_the_na_terminal(self) -> None:
        service = OwnerService(early_na=True)
        with tempfile.TemporaryDirectory() as temporary:
            result = self.run_cell(service, Path(temporary))
        self.assertEqual(service.actions, [(9, 1)])
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
        self.assertEqual(service.actions, [(9, 1)])

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
        self.assertEqual(
            [row["progress_sample_interval_days"] for row in service.entry_kwargs],
            [cell.NAVIGATION_PROGRESS_SAMPLE_DAYS] * 2,
        )
        self.assertEqual(
            [row["progress_sample_interval_days"] for row in service.stage11_direct_kwargs],
            [
                cell.NAVIGATION_PROGRESS_SAMPLE_DAYS,
                cell.POST_M360_PROGRESS_SAMPLE_DAYS,
                cell.POST_M360_PROGRESS_SAMPLE_DAYS,
            ],
        )


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
