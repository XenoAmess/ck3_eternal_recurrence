#!/usr/bin/env python3
"""MCP-owned Stage 10 player-subject run from a qualified player-manager save.

The process lifecycle and frozen-input admission come from the AF5 operator.
No launch occurs until the operator receives ``run-stage10``.  A failed action
is parked for evidence and cleanup; this operator deliberately exposes no
in-place retry control.
"""

from __future__ import annotations

import argparse
import copy
import importlib
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence

import zg361_phase2_af5_operator_job as base


CONTROLS = ["status", "run-stage10", "cleanup"]
JOB_ROLE = "stage10-player-subject"
SOURCE_RECEIPT_KIND = "zg361_stage10_player_publication_source_v5"
LIVE_SOURCE_KIND = "zg361_stage10_player_source_capture_v1"
NEAR_BOUNDARY_KIND = "zg361_phase2_stage10_player_subject_action_cell"
SCHEDULE_KIND = "ck3_scheduled_event_queue_offline_v1"


def _validate_source_receipt(
    value: object, bound: Mapping[str, object]
) -> dict[str, object]:
    receipt_path = base.checked_file(value, "stage10_source_receipt")
    receipt = base.read_object(receipt_path)
    checkpoint = base.mapping(receipt.get("checkpoint"), "source receipt checkpoint")
    bound_checkpoint = Path(str(bound["checkpoint"])).resolve()
    expected = base.mapping(bound.get("expected_hashes"), "expected hashes")
    topology = base.mapping(receipt.get("offline_topology"), "source topology")
    player_state = base.mapping(
        receipt.get("offline_player_state"), "source player state"
    )
    owner = base.positive_int(
        topology.get("immediate_liege_character_id"), "source owner"
    )
    manager = base.positive_int(
        topology.get("player_manager_character_id"), "source manager"
    )
    direct_subjects = topology.get("direct_landed_vassal_character_ids")
    player_tier = topology.get("player_primary_title_tier")
    played_records = player_state.get("played_character_records")
    current_players = player_state.get("currently_played_character_ids")
    live_path = base.checked_file(
        receipt.get("live_source_provenance"), "live source provenance"
    )
    live = base.read_object(live_path)
    live_checkpoint = base.mapping(
        live.get("target_checkpoint"), "live target checkpoint"
    )
    live_campaign = base.mapping(
        live.get("target_campaign_root"), "live target campaign root"
    )
    live_binding = base.mapping(
        live.get("target_binding"), "live target binding"
    )
    live_title = base.mapping(
        live_campaign.get("primary_title"), "live target primary title"
    )
    live_government = base.mapping(
        live_campaign.get("government"), "live target government"
    )
    live_flags = live_government.get("flags")
    near_path = base.checked_file(
        receipt.get("near_boundary_live_evidence"),
        "near-boundary live evidence",
    )
    near_wrapper = base.read_object(near_path)
    near = base.mapping(near_wrapper.get("evidence"), "near-boundary action evidence")
    near_progress = base.mapping(near.get("progress"), "near-boundary progress")
    near_initial = base.mapping(
        near_progress.get("initial_progress_observation"),
        "near-boundary initial progress",
    )
    near_binding = base.mapping(near.get("source_binding"), "near-boundary binding")
    extended_path = base.checked_file(
        receipt.get("extended_boundary_live_evidence"),
        "extended-boundary live evidence",
    )
    extended_wrapper = base.read_object(extended_path)
    extended = base.mapping(
        extended_wrapper.get("evidence"), "extended-boundary action evidence"
    )
    extended_progress = base.mapping(
        extended.get("progress"), "extended-boundary progress"
    )
    extended_initial = base.mapping(
        extended_progress.get("initial_progress_observation"),
        "extended-boundary initial progress",
    )
    extended_binding = base.mapping(
        extended.get("source_binding"), "extended-boundary binding"
    )
    schedule_path = base.checked_file(
        receipt.get("scheduled_event_evidence"), "scheduled-event evidence"
    )
    schedule = base.read_object(schedule_path)
    schedule_source = base.mapping(schedule.get("source"), "schedule source")
    scheduled = schedule.get("matches")
    expected_tail = receipt.get("fixed_tail_contract")
    if not (
        receipt.get("schema_version") == 1
        and receipt.get("kind") == SOURCE_RECEIPT_KIND
        and receipt.get("result") == "GREEN"
        and receipt.get("offline_topology_observed") is True
        and receipt.get("offline_single_player_observed") is True
        and receipt.get("fixture_used") is False
        and receipt.get("console_used") is False
        and receipt.get("selection_attempted") is False
        and manager != owner
        and receipt.get("source_container_header") == "SAV0101"
        and receipt.get("game_version") == "1.19.0.6"
        and player_state.get("meta_number_of_players") == 1
        and played_records
        == [{"character_id": manager, "player_id": 1}]
        and current_players == [manager]
        and isinstance(direct_subjects, list)
        and len(direct_subjects) >= 1
        and all(
            isinstance(value, int) and not isinstance(value, bool) and value > 0
            for value in direct_subjects
        )
        and isinstance(player_tier, int)
        and not isinstance(player_tier, bool)
        and player_tier >= 3
        and topology.get("player_government") == "celestial_government"
        and str(receipt.get("product_tree_sha256", "")).upper()
        == str(expected["product_tree_sha256"]).upper()
        and isinstance(checkpoint.get("path"), str)
        and Path(str(checkpoint["path"])).is_absolute()
        and Path(str(checkpoint["path"])).resolve() == bound_checkpoint
        and checkpoint.get("bytes") == bound_checkpoint.stat().st_size
        and str(checkpoint.get("sha256", "")).upper()
        == str(expected["checkpoint_sha256"]).upper()
        and live.get("schema_version") == 1
        and live.get("kind") == LIVE_SOURCE_KIND
        and live.get("result") == "GREEN"
        and live.get("production_live") is True
        and live.get("mcp_native_save") is True
        and live.get("fixture_used") is False
        and live.get("console_used") is False
        and str(live.get("product_tree_sha256", "")).upper()
        == str(expected["product_tree_sha256"]).upper()
        and isinstance(live_checkpoint.get("path"), str)
        and Path(str(live_checkpoint["path"])).resolve() == bound_checkpoint
        and live_checkpoint.get("bytes") == bound_checkpoint.stat().st_size
        and str(live_checkpoint.get("sha256", "")).upper()
        == str(expected["checkpoint_sha256"]).upper()
        and live_binding.get("player_character_id") == manager
        and live_binding.get("paused") is True
        and live_binding.get("map_ready") is True
        and live_campaign.get("status") == "available"
        and live_campaign.get("campaign_root_context_ready") is True
        and live_campaign.get("player_character_id") == manager
        and live_campaign.get("immediate_liege_character_id") == owner
        and live_campaign.get("independent") is False
        and isinstance(live_title.get("tier_raw"), int)
        and not isinstance(live_title.get("tier_raw"), bool)
        and live_title.get("tier_raw") >= 3
        and isinstance(live_flags, list)
        and "government_is_celestial" in live_flags
        and near_wrapper.get("result") == "RED"
        and near_wrapper.get("product_result") == "RED"
        and near_wrapper.get("red_preserved") is True
        and near.get("schema_version") == 2
        and near.get("kind") == NEAR_BOUNDARY_KIND
        and near.get("result") == "RED"
        and near.get("max_advance_days") == 30
        and near.get("expected_player_manager_character_id") == manager
        and near.get("expected_owner_character_id") == owner
        and near_binding.get("player_character_id") == manager
        and near_binding.get("date_raw") == live_binding.get("date_raw")
        and near_initial.get("date_raw") == live_binding.get("date_raw")
        and near_initial.get("review_now_eligible") is False
        and near_initial.get("b1_active") is True
        and near_initial.get("central_active") is False
        and near_initial.get("pp_active") is False
        and extended_wrapper.get("result") == "RED"
        and extended_wrapper.get("product_result") == "RED"
        and extended_wrapper.get("red_preserved") is True
        and extended.get("schema_version") == 2
        and extended.get("kind") == NEAR_BOUNDARY_KIND
        and extended.get("result") == "RED"
        and extended.get("max_advance_days") == 45
        and extended.get("expected_player_manager_character_id") == manager
        and extended.get("expected_owner_character_id") == owner
        and extended_binding.get("player_character_id") == manager
        and extended_binding.get("date_raw") == live_binding.get("date_raw")
        and extended_initial.get("date_raw") == live_binding.get("date_raw")
        and extended_initial.get("review_now_eligible") is False
        and extended_initial.get("b1_active") is True
        and extended_initial.get("central_active") is False
        and extended_initial.get("pp_active") is False
        and schedule.get("schema_version") == 1
        and schedule.get("kind") == SCHEDULE_KIND
        and schedule.get("result") == "GREEN"
        and schedule.get("event_prefix") == "zg361b1."
        and schedule.get("root_character_id") == manager
        and isinstance(scheduled, list)
        and any(
            isinstance(row, Mapping)
            and row.get("event") == "zg361b1.102"
            and row.get("root_character_id") == manager
            and row.get("days_from_current") == 1
            for row in scheduled
        )
        and schedule_source.get("bytes") == bound_checkpoint.stat().st_size
        and str(schedule_source.get("sha256", "")).upper()
        == str(expected["checkpoint_sha256"]).upper()
        and expected_tail
        == {
            "source_b1_stage": "D+299",
            "first_pending_event": "zg361b1.102",
            "first_pending_event_days": 1,
            "shadow_close_days": 30,
            "common_bank_close_latest_cycle_day": 335,
            "manager_calibration_latest_cycle_day": 336,
            "pending_watchdog_days": 31,
            "post_seal_reopen_days": 30,
            "player_publication_callback_days": 1,
            "manager_f_ticket_days": 5,
            "latest_stage10_cycle_day": 403,
            "maximum_required_tail_days": 104,
            "maximum_action_days": 120,
        }
    ):
        raise base.Af5JobError(
            "Stage 10 activation lacks a matching player-publication source receipt"
        )
    return {
        "path": receipt_path,
        "receipt": receipt,
        "live_source_provenance": live_path,
        "player_manager_character_id": manager,
        "owner_character_id": owner,
        "near_boundary_live_evidence": near_path,
        "extended_boundary_live_evidence": extended_path,
        "scheduled_event_evidence": schedule_path,
    }


def validate_activation(path: Path, *, require_empty_slot: bool) -> dict[str, object]:
    value = base.read_object(path)
    if value.get("job_role") != JOB_ROLE:
        raise base.Af5JobError("activation does not target Stage 10 player-subject")
    bound = base.validate_activation(path, require_empty_slot=require_empty_slot)
    source = _validate_source_receipt(value.get("stage10_source_receipt"), bound)
    bound["stage10_source_receipt"] = source["path"]
    bound["stage10_source"] = source["receipt"]
    bound["stage10_player_manager_character_id"] = source[
        "player_manager_character_id"
    ]
    bound["stage10_owner_character_id"] = source["owner_character_id"]
    return bound


def _archive_checkpoint(
    job: "Stage10PlayerSubjectOperatorJob",
    bound: Mapping[str, object],
    evidence: Mapping[str, object],
    *,
    result_key: str,
    filename: str,
    lineage_suffix: str,
) -> dict[str, object]:
    save_result = base.mapping(evidence.get(result_key), result_key)
    checkpoint = base.mapping(save_result.get("checkpoint"), f"{result_key} checkpoint")
    if save_result.get("accepted") is not True or checkpoint.get("status") != "saved":
        raise base.Af5JobError(f"{result_key} was not materialized", save_result)
    return job.runner._phase2_archive_checkpoint(
        checkpoint,
        Path(str(bound["artifact_directory"])) / filename,
        save_lineage_id=f"{bound['round']}.{lineage_suffix}",
    )


class Stage10PlayerSubjectOperatorJob(base.Af5OperatorJob):
    """Run one bounded Stage 10 attempt, park it, then await cleanup."""

    def status(self) -> dict[str, object]:
        status = super().status()
        status.pop("af5_evidence", None)
        status.update(
            kind="zg361_stage10_player_subject_operator_status_v1",
            controls=CONTROLS,
            state=self.state.replace("AF5", "STAGE10"),
            stage10_result=self.product_result,
        )
        if self.bound:
            path = (
                Path(str(self.bound["artifact_directory"]))
                / "stage10-player-subject-green.json"
            )
            status["stage10_evidence"] = (
                base.file_record(path) if path.is_file() else None
            )
        return status

    def start(self) -> dict[str, object]:
        response = super().start()
        response["control"] = "run-stage10"
        return response

    def _run(self) -> None:
        try:
            self.bound = validate_activation(
                self.activation_path, require_empty_slot=True
            )
            self._execute(self.bound)
        except BaseException as error:
            self._record_failure(error)
        finally:
            print(
                json.dumps(
                    {**self.status(), "notification": "run-stage10-finished"}
                ),
                flush=True,
            )

    def _execute_action(self, bound: Mapping[str, object]) -> None:
        root = Path(str(bound["repository_root"]))
        module = importlib.import_module(
            "zg361_phase2_stage10_player_subject_action_cell"
        )
        if not Path(str(module.__file__)).resolve().is_relative_to(root):
            raise base.Af5JobError(
                "Stage 10 action module is outside the frozen checkout"
            )
        artifacts = Path(str(bound["artifact_directory"]))
        expected = base.mapping(bound["expected_hashes"], "expected hashes")
        binding = base.mapping(self.binding, "native binding")
        self.stage = "stage10_player_subject_action"
        evidence = dict(
            module.run_stage10_player_subject(
                self.service,
                evidence_directory=artifacts / "stage10",
                request_nonce=f"{bound['round']}.stage10.player-subject",
                expected_player_manager_character_id=bound[
                    "stage10_player_manager_character_id"
                ],
                expected_owner_character_id=bound["stage10_owner_character_id"],
            )
        )
        gate = evidence.get("p1_acceptance_evidence")
        gate = gate.get("central_stage_10_terminal") if isinstance(gate, Mapping) else None
        if not (
            evidence.get("result") == "GREEN"
            and isinstance(gate, Mapping)
            and gate.get("result") == "GREEN"
            and gate.get("provider_observed") is True
            and gate.get("terminal_postcondition_verified") is True
            and gate.get("action_ack_is_business_postcondition") is False
        ):
            raise base.Af5JobError(
                "Stage 10 action or independent provider returned RED", evidence
            )
        with self.lock:
            self.af5_evidence = evidence
            self.product_result = "GREEN"
        source_archive = _archive_checkpoint(
            self,
            bound,
            evidence,
            result_key="source_checkpoint",
            filename="stage10-player-manager-source.ck3",
            lineage_suffix="stage10.player-manager-source",
        )
        terminal_archive = _archive_checkpoint(
            self,
            bound,
            evidence,
            result_key="terminal_checkpoint",
            filename="stage10-player-subject-terminal.ck3",
            lineage_suffix="stage10.player-subject-terminal",
        )
        evidence.update(
            round=bound["round"],
            execution_identity={
                "repository_root": str(root),
                "code_commit": expected["code_commit"],
            },
            bridge_pid=binding["bridge_pid"],
            connection_generation=binding["connection_generation"],
            input_checkpoint={
                "path": str(Path(str(bound["checkpoint"]))),
                "bytes": Path(str(bound["checkpoint"])).stat().st_size,
                "sha256": expected["checkpoint_sha256"],
            },
            source_qualification_receipt=base.file_record(
                Path(str(bound["stage10_source_receipt"]))
            ),
            product_tree_sha256=expected["product_tree_sha256"],
            bridge_dll=base.file_record(Path(str(bound["bridge_dll"]))),
            archived_source_checkpoint=source_archive,
            archived_terminal_checkpoint=terminal_archive,
            production_live=True,
            fixture_used=False,
            video_lock_touched=False,
        )
        base.write_object(artifacts / "stage10-player-subject-green.json", evidence)
        self.state = "AF5_GREEN_PARKED"
        self.stage = "stage10_player_subject_verified_and_saved"
        self.failure_reason = None

    def _record_failure(self, error: BaseException) -> None:
        base.Af5OperatorJob._record_failure(self, error)
        if self.bound is None:
            return
        artifacts = Path(str(self.bound["artifact_directory"]))
        partial = copy.deepcopy(self.failure_evidence or {})
        action = partial.get("evidence")
        if isinstance(action, Mapping) and isinstance(
            action.get("source_checkpoint"), Mapping
        ):
            try:
                partial["archived_source_checkpoint"] = _archive_checkpoint(
                    self,
                    self.bound,
                    action,
                    result_key="source_checkpoint",
                    filename=f"stage10-player-manager-source-attempt-{self.attempt:02d}.ck3",
                    lineage_suffix=f"stage10.player-manager-source.{self.attempt}",
                )
            except Exception as archive_error:
                partial["source_archive_error"] = (
                    f"{type(archive_error).__name__}: {archive_error}"
                )
        self.failure_evidence = partial
        base.write_object(artifacts / "stage10-player-subject-red.json", partial)
        base.write_object(
            artifacts / f"stage10-player-subject-red-attempt-{self.attempt:02d}.json",
            partial,
        )
        (artifacts / "af5-red.json").unlink(missing_ok=True)

    def perform_cleanup(self) -> dict[str, object]:
        response = super().perform_cleanup()
        if self.bound is not None:
            artifacts = Path(str(self.bound["artifact_directory"]))
            old = artifacts / "af5-managed-cleanup.json"
            if old.exists():
                old.replace(artifacts / "stage10-player-subject-managed-cleanup.json")
        return response

    def serve(self) -> int:
        self.bound = validate_activation(
            self.activation_path, require_empty_slot=False
        )
        print(json.dumps(self.status()), flush=True)
        while not self.stop_requested.is_set():
            line = sys.stdin.readline()
            if line == "":
                self.stop_requested.wait(5.0)
                continue
            command = line.strip().casefold()
            if command == "status":
                response = self.status()
            elif command == "run-stage10":
                response = self.start()
            elif command == "cleanup":
                response = self.perform_cleanup()
            else:
                response = {
                    "result": "RED",
                    "error": "unknown control",
                    "controls": CONTROLS,
                }
            print(json.dumps(response), flush=True)
        if self.worker is not None:
            self.worker.join()
        return self.exit_code()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--activation", required=True, type=Path)
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--preflight-output", type=Path)
    args = parser.parse_args(argv)
    if args.serve:
        return Stage10PlayerSubjectOperatorJob(args.activation).serve()
    bound = validate_activation(args.activation, require_empty_slot=False)
    result = {
        "result": "GREEN",
        "launch_requested": False,
        "job_role": JOB_ROLE,
        "activation": bound["activation_record"],
    }
    if args.preflight_output is not None:
        base.write_object(args.preflight_output, result)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
