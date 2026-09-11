#!/usr/bin/env python3
"""MCP-owned continuation of the played Central owner's stages 9 and 11.

Reuse the AF5 operator's frozen-input activation and lifecycle. job_role marks
this specific consumer; its stage receipts and optional B1 proof remain separate.
The player-visible manager Stage 10 receipt uses an independent subject route.
No launch occurs until the operator sends run-stages.
"""
from __future__ import annotations

import argparse
import copy
import importlib
import json
from pathlib import Path
import shutil
import sys
import threading
from typing import Mapping, Sequence

import zg361_phase2_af5_operator_job as base

CONTROLS = ["status", "run-stages", "retry-stages", "cleanup"]
JOB_ROLE = "terminal-stages"
B1_CAPABILITY = "game.command.query-zhongguo-b1-cycle-snapshot-v1"
STAGE10_SOURCE_KIND = "zg361_stage10_player_subject_source_v1"
STAGE10_SOURCE_EVENT = "zg361cl.390"


# Preserves R390's observed final-survivor gate. Only the old seed's fixed
# cycle/case 8 selector is replaced by the current native cycle/case binding.
def value(frame: Mapping[str, object], group: str, field: str) -> object:
    group_value = frame.get(group)
    row = group_value.get(field) if isinstance(group_value, Mapping) else None
    return row.get("value") if isinstance(row, Mapping) and row.get("status") == "available" else None


def compact_b1(result: Mapping[str, object]) -> dict[str, object]:
    frame = result
    source = result.get("bridge_source")
    source = source if isinstance(source, Mapping) else {}
    quota = frame.get("quota")
    quota = quota if isinstance(quota, Mapping) else {}
    return {
        "status": result.get("status"),
        "snapshot_id": source.get("snapshot_id"),
        "revision": source.get("revision"),
        "native_revision": source.get("native_revision"),
        "connection_generation": source.get("connection_generation"),
        "date_raw": frame.get("date_raw"),
        "cycle": value(frame, "cycle", "cycle_serial"),
        "case": value(frame, "cycle", "case_serial"),
        "state": value(frame, "cycle", "state"),
        "active": value(frame, "cycle", "active"),
        "roster": value(frame, "roster", "subject_count"),
        "roster_amendment": value(frame, "roster", "amendment_count"),
        "roster_audit_version": value(frame, "roster", "audit_version"),
        "roster_reopen_required": value(frame, "roster", "reopen_required"),
        "processing": value(frame, "processing", "count"),
        "agenda": value(frame, "processing", "agenda_count"),
        "rebuild_generation": value(frame, "quota", "rebuild_generation"),
        "rebuild_generation_field": copy.deepcopy(
            quota.get("rebuild_generation")
        ),
        "built_case": value(frame, "quota", "built_case_serial"),
        "target": [value(frame, "quota", f"target_{x}") for x in ("top", "middle", "bottom")],
        "recount": [value(frame, "quota", f"recount_{x}") for x in ("top", "middle", "bottom")],
        "closure_state": value(frame, "closure", "state"),
        "calibration_finalized": value(frame, "closure", "calibration_finalized"),
        "rewards_issued": value(frame, "closure", "rewards_issued"),
        "pending_open": value(frame, "pending", "open_count"),
        "invariants": copy.deepcopy(frame.get("invariants")),
        "anomalies": copy.deepcopy(frame.get("anomalies")),
        "readiness": copy.deepcopy(frame.get("readiness")),
    }


def b1_green_checks(
    row: Mapping[str, object], before: Mapping[str, object]
) -> dict[str, bool]:
    inv = row.get("invariants") if isinstance(row.get("invariants"), Mapping) else {}
    ready = row.get("readiness") if isinstance(row.get("readiness"), Mapping) else {}
    target = row.get("target")
    recount = row.get("recount")
    typed_target = (
        target
        if isinstance(target, list)
        and len(target) == 3
        and all(isinstance(item, int) and not isinstance(item, bool) for item in target)
        else []
    )
    typed_recount = (
        recount
        if isinstance(recount, list)
        and len(recount) == 3
        and all(isinstance(item, int) and not isinstance(item, bool) for item in recount)
        else []
    )
    after_generation = row.get("rebuild_generation")
    return {
        "available": row.get("status") == "available",
        "rebuild_generation_visible": isinstance(after_generation, int)
        and not isinstance(after_generation, bool),
        "rebuild_generation_materialized": isinstance(after_generation, int) and not isinstance(after_generation, bool) and after_generation >= 1,
        "current_cycle_case_bound": isinstance(row.get("cycle"), int) and not isinstance(row.get("cycle"), bool) and row["cycle"] > 0 and row.get("cycle") == row.get("case") == row.get("built_case"),
        "closed_state_8": row.get("state") == 8 and row.get("active") is False,
        "closure_4": row.get("closure_state") == 4,
        "calibration_finalized": row.get("calibration_finalized") is True,
        "rewards_issued": row.get("rewards_issued") is True,
        "roster_bounded": isinstance(row.get("roster"), int) and 1 <= row["roster"] <= 80,
        "processing_matches_roster": row.get("processing") == row.get("roster"),
        "agenda_matches_processing": row.get("agenda") == row.get("processing"),
        "target_three_bands_conserved": bool(typed_target) and sum(typed_target) == row.get("processing"),
        "recount_three_bands_conserved": bool(typed_recount) and sum(typed_recount) == row.get("processing"),
        "target_equals_recount": bool(typed_target) and typed_target == typed_recount,
        # A final-callback loss is stochastic.  The live gate must accept both
        # a compacted survivor domain and an intact domain; the observable
        # contract is the same closed, conserved domain in either branch.
        "final_survivor_domain_consistent": (
            row.get("roster") == row.get("processing") == row.get("agenda")
            and bool(typed_target)
            and bool(typed_recount)
            and sum(typed_target) == row.get("processing")
            and typed_target == typed_recount
        ),
        "final_survivor_receipt_visible": (
            isinstance(row.get("roster_amendment"), int)
            and not isinstance(row.get("roster_amendment"), bool)
            and row.get("roster_amendment") >= 0
            and isinstance(row.get("roster_audit_version"), int)
            and not isinstance(row.get("roster_audit_version"), bool)
            and row.get("roster_audit_version") >= 0
        ),
        "roster_reopen_closed": row.get("roster_reopen_required") is False,
        "active_matches_state": inv.get("active_matches_state") is True,
        "closed_state_coherent": inv.get("closed_state_coherent") is True,
        "target_conserved": inv.get("quota_target_conserved") is True,
        "recount_conserved": inv.get("quota_recount_conserved") is True,
        "target_matches_recount": inv.get("quota_target_matches_recount") is True,
        "processing_within_roster": inv.get("processing_within_roster") is True,
        "counts_nonnegative": inv.get("counts_nonnegative") is True,
        "portable_ready": ready.get("ready") is True,
        "no_anomalies": row.get("anomalies") == [],
    }


def validate_activation(path: Path, *, require_empty_slot: bool) -> dict[str, object]:
    value = base.read_object(path)
    if value.get("job_role") != JOB_ROLE:
        raise base.Af5JobError("activation does not target terminal stages")
    bound = base.validate_activation(path, require_empty_slot=require_empty_slot)
    source_route = value.get("source_route")
    if isinstance(source_route, Mapping):
        if "max_advance_days" in source_route:
            max_advance_days = source_route["max_advance_days"]
            if (
                isinstance(max_advance_days, bool)
                or not isinstance(max_advance_days, int)
                or max_advance_days <= 0
            ):
                raise base.Af5JobError(
                    "source_route.max_advance_days must be a positive integer"
                )
            bound["terminal_stages_max_advance_days"] = max_advance_days
        if "start_stage" in source_route:
            start_stage = source_route["start_stage"]
            if isinstance(start_stage, bool) or start_stage not in (9, 11):
                raise base.Af5JobError("source_route.start_stage must be 9 or 11")
            bound["terminal_stages_start_stage"] = start_stage
    return bound


def observe_b1(service: object, nonce: str) -> dict[str, object]:
    """An optional read; unavailable or unfinished B1 does not stop stage work."""
    report: dict[str, object] = {"schema_version": 1, "result": "PENDING", "fix_verified": False,
                              "production_live": False, "product_red": False}
    try:
        query = getattr(service, "query_zhongguo_b1_cycle_snapshot_v1", None)
        capabilities = service.capabilities().get("bridge_capabilities", [])
        if not callable(query) or B1_CAPABILITY not in capabilities:
            report["reason"] = "native_b1_query_not_available"
            return report
        snapshot = service.snapshot()
        if snapshot.get("paused") is not True:
            report["reason"] = "current_snapshot_not_paused"
            return report
        frame = query(nonce, expected_revision=snapshot["revision"])
        row = compact_b1(frame)
        report.update(query_receipt=frame, before=snapshot, after=service.snapshot())
        if row.get("status") != "available" or row.get("state") != 8:
            report["reason"] = "b1_closure_lifecycle_not_reached"
            return report
        checks = b1_green_checks(row, row)
        green = all(checks.values())
        report.update(result="GREEN" if green else "RED", fix_verified=green,
                      production_live=True, product_red=not green, check_receipt=checks)
    except Exception as error:
        report["reason"] = f"native_b1_observation_unavailable: {type(error).__name__}: {error}"
    return report


class TerminalStagesOperatorJob(base.Af5OperatorJob):
    def __init__(self, activation_path: Path) -> None:
        super().__init__(activation_path)
        self.b1_evidence: dict[str, object] = {"result": "PENDING", "fix_verified": False}

    def status(self) -> dict[str, object]:
        status = super().status()
        status.pop("af5_evidence", None)
        status.update(kind="zg361_terminal_stages_operator_status_v1", controls=CONTROLS,
                      state=self.state.replace("AF5", "STAGES"),
                      stages_result=self.product_result, b1_result=self.b1_evidence.get("result", "PENDING"))
        if self.bound:
            path = Path(str(self.bound["artifact_directory"])) / "terminal-stages-green.json"
            status["stages_evidence"] = base.file_record(path) if path.is_file() else None
        return status

    def start(self) -> dict[str, object]:
        response = super().start()
        response["control"] = "run-stages"
        return response

    def _run(self) -> None:
        try:
            self.bound = validate_activation(self.activation_path, require_empty_slot=True)
            self._execute(self.bound)
        except BaseException as error:
            self._record_failure(error)
        finally:
            print(json.dumps({**self.status(), "notification": "run-stages-finished"}), flush=True)

    def _sample_b1(self, bound: Mapping[str, object], label: str) -> None:
        report = observe_b1(self.service, f"{bound['round']}.b1.{label}.{self.attempt}")
        report["product_tree_sha256"] = bound["expected_hashes"]["product_tree_sha256"]
        artifacts = Path(str(bound["artifact_directory"]))
        base.write_object(artifacts / f"b1-{label}-attempt-{self.attempt:02d}.json", report)
        if report["result"] in {"GREEN", "RED"} or self.b1_evidence.get("result") != "GREEN":
            self.b1_evidence = report
        base.write_object(artifacts / "b1-observation.json", self.b1_evidence)

    def _publish_stage10_source(
        self, bound: Mapping[str, object], action: object
    ) -> dict[str, object] | None:
        evidence = action if isinstance(action, Mapping) else {}
        source = evidence.get("stage10_source")
        if not isinstance(source, Mapping) or source.get("result") != "GREEN":
            return None
        artifacts = Path(str(bound["artifact_directory"])).resolve()
        checkpoint = base.mapping(source.get("checkpoint"), "Stage 10 source checkpoint")
        checkpoint_path = base.checked_file(checkpoint, "Stage 10 source checkpoint")
        if not checkpoint_path.is_relative_to(artifacts / "stages"):
            raise base.Af5JobError("Stage 10 source archive is outside stage artifacts")
        context = base.mapping(source.get("source_event_context"), "Stage 10 source event")
        root_scope = base.mapping(context.get("root_scope"), "Stage 10 source root")
        root_identity = base.mapping(
            root_scope.get("typed_identity"), "Stage 10 source root identity"
        )
        selector = base.mapping(source.get("selector"), "Stage 10 source selector")
        readiness = base.mapping(selector.get("readiness"), "Stage 10 source readiness")
        selection = base.mapping(selector.get("selection"), "Stage 10 source selection")
        owner = base.positive_int(source.get("owner_character_id"), "Stage 10 source owner")
        player = base.positive_int(source.get("player_character_id"), "Stage 10 source player")
        manager = base.positive_int(
            source.get("selected_manager_character_id"), "Stage 10 source manager"
        )
        if not (
            source.get("kind") == STAGE10_SOURCE_KIND
            and source.get("source_event_definition_key") == STAGE10_SOURCE_EVENT
            and context.get("event_definition_key") == STAGE10_SOURCE_EVENT
            and source.get("source_event_instance_id")
            == context.get("current_event_instance_id")
            and owner == player
            and root_identity.get("status") == "available"
            and root_identity.get("kind") == "character"
            and root_identity.get("character_id") == owner
            and manager != owner
            and selector.get("status") == "available"
            and selector.get("provider_observed") is True
            and readiness.get("ready") is True
            and selection.get("manager_character_id") == manager
            and source.get("selection_attempted") is False
        ):
            raise base.Af5JobError("Stage 10 source receipt is not a qualified .390 frame")
        binding = base.mapping(self.binding, "native binding")
        expected = base.mapping(bound.get("expected_hashes"), "expected hashes")
        receipt = copy.deepcopy(dict(source))
        input_checkpoint = Path(str(bound["checkpoint"]))
        receipt.update(
            result="GREEN",
            production_live=True,
            fixture_used=False,
            console_used=False,
            round=bound["round"],
            bridge_pid=binding["bridge_pid"],
            connection_generation=binding["connection_generation"],
            source_code_commit=expected["code_commit"],
            product_tree_sha256=expected["product_tree_sha256"],
            input_checkpoint={
                "path": str(input_checkpoint),
                "bytes": input_checkpoint.stat().st_size,
                "sha256": expected["checkpoint_sha256"],
            },
            bridge_dll=base.file_record(Path(str(bound["bridge_dll"]))),
            checkpoint=copy.deepcopy(dict(checkpoint)),
            video_lock_touched=False,
        )
        target = artifacts / "stage10-player-subject-source.json"
        base.write_object(target, receipt)
        return base.file_record(target)

    def _execute_action(self, bound: Mapping[str, object]) -> None:
        module = importlib.import_module("zg361_phase2_terminal_stages_action_cell")
        root = Path(str(bound["repository_root"]))
        if not Path(str(module.__file__)).resolve().is_relative_to(root):
            raise base.Af5JobError("terminal stage action is outside the frozen checkout")
        artifacts = Path(str(bound["artifact_directory"]))
        self.stage = "terminal_stages_action"
        self._sample_b1(bound, "before")
        try:
            action_arguments: dict[str, object] = {
                "evidence_directory": artifacts / "stages",
                "request_nonce": f"{bound['round']}.terminal-stages",
            }
            if "terminal_stages_max_advance_days" in bound:
                action_arguments["max_advance_days"] = bound[
                    "terminal_stages_max_advance_days"
                ]
            if "terminal_stages_start_stage" in bound:
                action_arguments["start_stage"] = bound[
                    "terminal_stages_start_stage"
                ]
            evidence = dict(
                module.run_terminal_stages(self.service, **action_arguments)
            )
        finally:
            self._sample_b1(bound, "after")
        if evidence.get("result") != "GREEN":
            raise base.Af5JobError("terminal stage action returned RED", evidence)
        stage10_source_receipt = self._publish_stage10_source(bound, evidence)
        evidence.update(round=bound["round"], product_tree_sha256=bound["expected_hashes"]["product_tree_sha256"],
                        execution_identity={"repository_root": str(root), "code_commit": bound["expected_hashes"]["code_commit"]},
                        source_checkpoint=base.file_record(Path(str(bound["checkpoint"]))),
                        bridge_dll=base.file_record(Path(str(bound["bridge_dll"]))),
                        stage10_source_receipt=stage10_source_receipt,
                        production_live=True, fixture_used=False, video_lock_touched=False)
        base.write_object(artifacts / "terminal-stages-green.json", evidence)
        self.af5_evidence = evidence  # Reused lifecycle's scenario receipt slot.
        self.product_result = "GREEN"
        self.stage = "terminal_checkpoint_archive"
        save_result = base.mapping(evidence.get("save_result"), "stages terminal save")
        checkpoint = base.mapping(save_result.get("checkpoint"), "stages terminal checkpoint")
        if save_result.get("accepted") is not True or checkpoint.get("status") != "saved":
            raise base.Af5JobError("stages terminal save was not materialized", evidence)
        owned_stages = evidence.get("owned_stage_sequence")
        lineage_suffix = "-and-".join(str(stage) for stage in owned_stages)
        archive = self.runner._phase2_archive_checkpoint(
            checkpoint, artifacts / "representative-terminal.ck3",
            save_lineage_id=f"{bound['round']}.central-stages-{lineage_suffix}",
        )
        base.write_object(artifacts / "representative-terminal-checkpoint.json", {
            "schema_version": 1, "result": "GREEN", "checkpoint": archive,
            "terminal_evidence": base.file_record(artifacts / "terminal-stages-green.json"),
            "af5_same_slice_required": False,
        })
        if self.b1_evidence.get("result") == "GREEN":
            self.b1_evidence["checkpoint_receipt"] = copy.deepcopy(dict(save_result))
            base.write_object(artifacts / "b1-fix-live.json", self.b1_evidence)
        base.write_object(artifacts / "terminal-stages-park.json", {
            "result": "PARKED", "snapshot": self.service.snapshot(), "checkpoint": archive,
            "stage_receipts": evidence.get("p1_acceptance_evidence"), "b1_result": self.b1_evidence.get("result"),
        })
        self.state = "AF5_GREEN_PARKED"
        self.stage = "terminal_stages_verified_and_saved"
        self.failure_reason = None

    def _record_failure(self, error: BaseException) -> None:
        super()._record_failure(error)
        if self.bound is None:
            return
        artifacts = Path(str(self.bound["artifact_directory"]))
        partial = copy.deepcopy(self.failure_evidence)
        try:
            partial["stage10_source_receipt"] = self._publish_stage10_source(
                self.bound, partial.get("evidence")
            )
        except Exception as source_error:
            partial["stage10_source_receipt_error"] = (
                f"{type(source_error).__name__}: {source_error}"
            )
        snapshot = partial.get("failure_snapshot")
        if self.service is not None and isinstance(snapshot, Mapping) and snapshot.get("paused") is True:
            try:
                saved = self.service.save_checkpoint(expected_revision=snapshot["revision"])
                partial["checkpoint_save"] = saved
                checkpoint = base.mapping(saved.get("checkpoint"), "partial checkpoint")
                if saved.get("accepted") is True and checkpoint.get("status") == "saved":
                    partial["archived_checkpoint"] = self.runner._phase2_archive_checkpoint(
                        checkpoint, artifacts / f"terminal-partial-attempt-{self.attempt:02d}.ck3",
                        save_lineage_id=f"{self.bound['round']}.terminal-partial.{self.attempt}",
                    )
            except Exception as save_error:
                partial["checkpoint_error"] = f"{type(save_error).__name__}: {save_error}"
        self.failure_evidence = partial
        base.write_object(artifacts / "terminal-stages-red.json", partial)
        base.write_object(artifacts / f"terminal-stages-red-attempt-{self.attempt:02d}.json", partial)
        (artifacts / "af5-red.json").unlink(missing_ok=True)

    def retry(self) -> dict[str, object]:
        with self.lock:
            if self.state != "AF5_RED_PARKED" or self.stage not in {"terminal_stages_action", "terminal_checkpoint_archive"} or self.service is None or self.binding is None or (
                self.worker is not None and self.worker.is_alive()
            ):
                return {**self.status(), "control": "retry-stages", "accepted": False,
                        "reason": "no completed retained stage attempt"}
            self.state = "RUNNING_AF5"
            self.worker = threading.Thread(target=self._run_stage_retry, name="terminal-stages-hot-retry", daemon=False)
            self.worker.start()
            return {**self.status(), "control": "retry-stages", "accepted": True}

    def _run_stage_retry(self) -> None:
        try:
            original = base.mapping(self.bound, "original activation")
            repaired = validate_activation(self.activation_path.with_name("retry-activation.json"), require_empty_slot=False)
            if any(original["expected_hashes"][key] != repaired["expected_hashes"][key] for key in base.HASH_FIELDS):
                raise base.Af5JobError("stage retry changed loaded game inputs")
            for key in ("game_directory", "product_root", "product_projection_manifest", "checkpoint", "bridge_dll",
                        "bridge_injector", "state_directory", "artifact_directory", "bridge_pipe", "warmup_bridge_pipe", "rounds"):
                if original[key] != repaired[key]:
                    raise base.Af5JobError(f"stage retry changed loaded session input: {key}")
            if original.get("terminal_stages_max_advance_days") != repaired.get(
                "terminal_stages_max_advance_days"
            ):
                raise base.Af5JobError("stage retry changed the game-day bound")
            before = self._retained_binding()
            base.Af5OperatorJob._reload_action_modules(Path(str(repaired["repository_root"])))
            stage_module = importlib.import_module("zg361_phase2_terminal_stages_action_cell")
            importlib.reload(stage_module)
            if self._retained_binding() != before:
                raise base.Af5JobError("retained stage session changed while reloading Python")
            self.attempt += 1
            self.bound = repaired
            base.write_object(Path(str(repaired["artifact_directory"])) / f"terminal-stages-retry-{self.attempt:02d}.json", {
                "result": "GREEN", "same_process_retained": True, "binding": before,
                "activation": repaired["activation_record"], "code_commit": repaired["expected_hashes"]["code_commit"],
            })
            self.failure_reason = None
            self.product_result = "PENDING"
            self._execute_action(repaired)
        except BaseException as error:
            self._record_failure(error)
        finally:
            print(json.dumps({**self.status(), "notification": "retry-stages-finished"}), flush=True)

    def perform_cleanup(self) -> dict[str, object]:
        response = super().perform_cleanup()
        if self.bound is not None:
            artifacts = Path(str(self.bound["artifact_directory"]))
            old = artifacts / "af5-managed-cleanup.json"
            if old.exists():
                old.replace(artifacts / "terminal-stages-managed-cleanup.json")
        return response

    def serve(self) -> int:
        self.bound = validate_activation(self.activation_path, require_empty_slot=False)
        print(json.dumps(self.status()), flush=True)
        while not self.stop_requested.is_set():
            line = sys.stdin.readline()
            if line == "":
                self.stop_requested.wait(5.0)
                continue
            command = line.strip().casefold()
            if command == "status":
                response = self.status()
            elif command == "run-stages":
                response = self.start()
            elif command == "retry-stages":
                response = self.retry()
            elif command == "cleanup":
                response = self.perform_cleanup()
            else:
                response = {"result": "RED", "error": "unknown control", "controls": CONTROLS}
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
        return TerminalStagesOperatorJob(args.activation).serve()
    bound = validate_activation(args.activation, require_empty_slot=False)
    result = {"result": "GREEN", "launch_requested": False, "job_role": JOB_ROLE,
              "activation": bound["activation_record"]}
    if args.preflight_output is not None:
        base.write_object(args.preflight_output, result)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
