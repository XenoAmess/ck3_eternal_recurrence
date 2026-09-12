#!/usr/bin/env python3
"""MCP-owned four-domain terminal cold restore on one admitted checkpoint."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
import sys
import threading
from typing import Mapping, Sequence

import zg361_phase2_af5_operator_job as base


CONTROLS = ["status", "run-cold-restore", "retry-policy", "retry-cold-restore", "cleanup"]
JOB_ROLE = "terminal-cold-restore"


def validate_activation(path: Path, *, require_empty_slot: bool) -> dict[str, object]:
    value = base.read_object(path)
    if value.get("job_role") != JOB_ROLE:
        raise base.Af5JobError("activation does not target terminal cold restore")
    bound = base.validate_activation(path, require_empty_slot=require_empty_slot)
    cold_round = value.get("cold_restore_round")
    match = base.ROUND_RE.fullmatch(cold_round) if isinstance(cold_round, str) else None
    gameplay_match = base.ROUND_RE.fullmatch(str(bound["round"]))
    if (
        match is None
        or gameplay_match is None
        or int(match.group(1)) != int(gameplay_match.group(1)) + 1
    ):
        raise base.Af5JobError(
            "cold_restore_round must immediately follow the gameplay round"
        )
    bound["cold_restore_round"] = cold_round
    return bound


class TerminalColdRestoreOperatorJob(base.Af5OperatorJob):
    """Load a terminal save, prove one lifecycle restore, then await cleanup."""

    def __init__(self, activation_path: Path) -> None:
        super().__init__(activation_path)
        self.terminal_save_result: dict[str, object] | None = None
        self.cold_evidence: dict[str, object] | None = None

    def status(self) -> dict[str, object]:
        status = super().status()
        status.pop("af5_evidence", None)
        status.update(
            kind="zg361_terminal_cold_restore_operator_status_v1",
            controls=CONTROLS,
            state=self.state.replace("AF5", "COLD_RESTORE"),
            cold_restore_result=self.product_result,
            cold_restore_round=(
                self.bound.get("cold_restore_round") if self.bound else None
            ),
        )
        if self.cold_evidence is not None:
            handoff = self.cold_evidence.get("cleanup_handoff")
            if isinstance(handoff, Mapping):
                status["bridge_pid"] = handoff.get("current_pid")
                status["connection_generation"] = handoff.get("current_generation")
        if self.bound:
            path = (
                Path(str(self.bound["artifact_directory"]))
                / "terminal-cold-restore-green.json"
            )
            status["cold_restore_evidence"] = (
                base.file_record(path) if path.is_file() else None
            )
        return status

    def start(self) -> dict[str, object]:
        response = super().start()
        response["control"] = "run-cold-restore"
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
                    {**self.status(), "notification": "run-cold-restore-finished"}
                ),
                flush=True,
            )

    def _execute_action(self, bound: Mapping[str, object]) -> None:
        root = Path(str(bound["repository_root"]))
        module = importlib.import_module("zg361_phase2_terminal_cold_restore")
        if not Path(str(module.__file__)).resolve().is_relative_to(root):
            raise base.Af5JobError(
                "terminal cold restore module is outside the frozen checkout"
            )
        artifacts = Path(str(bound["artifact_directory"]))
        service = self.service
        if service is None:
            raise base.Af5JobError("terminal cold restore lacks an admitted service")
        self.stage = "terminal_cold_restore"
        if self.terminal_save_result is None:
            snapshot = service.snapshot()
            if snapshot.get("paused") is not True or snapshot.get("map_ready") is not True:
                raise base.Af5JobError(
                    "terminal cold restore did not start on a paused map-ready frame"
                )
            save_result = service.save_checkpoint(
                expected_revision=int(snapshot["revision"])
            )
            self.terminal_save_result = dict(save_result)
            base.write_object(
                artifacts / "terminal-cold-restore-save.json",
                base.bootstrap_evidence_json_value(save_result),
            )
        evidence = dict(
            module.run_terminal_cold_restore(
                service,
                evidence_directory=artifacts / "cold-restore",
                request_nonce=(
                    f"{bound['round']}.{bound['cold_restore_round']}.terminal.cold"
                ),
                save_result=self.terminal_save_result,
            )
        )
        if evidence.get("result") != "GREEN":
            raise base.Af5JobError("terminal cold restore returned non-GREEN", evidence)
        handoff = base.mapping(evidence.get("cleanup_handoff"), "cleanup handoff")
        scenario = base.mapping(handoff.get("scenario_evidence"), "cleanup scenario")
        expected = base.mapping(bound["expected_hashes"], "expected hashes")
        activation = base.mapping(bound["activation"], "activation")
        lineage = base.mapping(evidence.get("save_restore_lineage"), "save/restore lineage")
        evidence.update(
            round=bound["round"],
            rounds={
                **dict(bound["rounds"]),
                "cold_restore": bound["cold_restore_round"],
            },
            restart_record={
                "old_round": bound["round"],
                "new_round": bound["cold_restore_round"],
                "reason": "representative_terminal_checkpoint_cold_restore",
                "old_pid": lineage.get("first_pid"),
                "new_pid": lineage.get("second_pid"),
                "old_connection_generation": lineage.get(
                    "first_connection_generation"
                ),
                "new_connection_generation": lineage.get(
                    "second_connection_generation"
                ),
                "old_code_commit": expected["code_commit"],
                "new_code_commit": expected["code_commit"],
                "old_product_tree_sha256": expected["product_tree_sha256"],
                "new_product_tree_sha256": expected["product_tree_sha256"],
                "game_exe_sha256": expected["game_exe_sha256"],
                "startup_parameters": {
                    "lifecycle_intent": "restore",
                    "checkpoint": self.terminal_save_result["checkpoint"],
                    "bridge_pipe": str(bound["bridge_pipe"]),
                },
                "known_red": base.bootstrap_evidence_json_value(
                    activation.get("known_red", [])
                ),
                "dll_or_game_files_changed": False,
                "startup_configuration_changed": False,
                "load_order_changed": False,
            },
            execution_identity={
                "repository_root": str(root),
                "code_commit": expected["code_commit"],
            },
            source_checkpoint=base.file_record(Path(str(bound["checkpoint"]))),
            product_tree_sha256=expected["product_tree_sha256"],
            bridge_dll=base.file_record(Path(str(bound["bridge_dll"]))),
            production_live=True,
            fixture_used=False,
            video_lock_touched=False,
        )
        base.write_object(artifacts / "terminal-cold-restore-green.json", evidence)
        self.cold_evidence = evidence
        # The existing cleanup proof consumes this exact lineage shape and the
        # original supervisor binding retained in self.binding.
        self.af5_evidence = dict(scenario)
        self.product_result = "GREEN"
        self.state = "AF5_GREEN_PARKED"
        self.stage = "terminal_cold_restore_verified"
        self.failure_reason = None

    def retry(self) -> dict[str, object]:
        with self.lock:
            if (
                self.state != "AF5_RED_PARKED"
                or self.stage != "terminal_cold_restore"
                or self.service is None
                or self.terminal_save_result is None
                or (self.worker is not None and self.worker.is_alive())
            ):
                return {
                    **self.status(),
                    "control": "retry-cold-restore",
                    "accepted": False,
                    "reason": "no completed retained cold-restore attempt",
                }
            self.state = "RUNNING_AF5"
            self.worker = threading.Thread(
                target=self._run_retry,
                name="terminal-cold-restore-retry",
                daemon=False,
            )
            self.worker.start()
            return {
                **self.status(),
                "control": "retry-cold-restore",
                "accepted": True,
            }

    def _run_retry(self) -> None:
        try:
            original = base.mapping(self.bound, "original activation")
            repaired = validate_activation(
                self.activation_path.with_name("retry-activation.json"),
                require_empty_slot=False,
            )
            if any(
                original["expected_hashes"][key]
                != repaired["expected_hashes"][key]
                for key in base.HASH_FIELDS
            ):
                raise base.Af5JobError("cold retry changed loaded game inputs")
            for key in (
                "game_directory",
                "product_root",
                "product_projection_manifest",
                "checkpoint",
                "bridge_dll",
                "bridge_injector",
                "state_directory",
                "artifact_directory",
                "bridge_pipe",
                "warmup_bridge_pipe",
                "rounds",
                "cold_restore_round",
            ):
                if original[key] != repaired[key]:
                    raise base.Af5JobError(
                        f"cold retry changed loaded session input: {key}"
                    )
            root = Path(str(repaired["repository_root"]))
            sys.path.insert(0, str(root / "tools"))
            module = importlib.reload(
                importlib.import_module("zg361_phase2_terminal_cold_restore")
            )
            if not Path(str(module.__file__)).resolve().is_relative_to(root):
                raise base.Af5JobError(
                    "repaired cold restore module is outside the frozen checkout"
                )
            self.attempt += 1
            self.bound = repaired
            self.failure_reason = None
            self.product_result = "PENDING"
            self._execute_action(repaired)
        except BaseException as error:
            self._record_failure(error)
        finally:
            print(
                json.dumps(
                    {
                        **self.status(),
                        "notification": "retry-cold-restore-finished",
                    }
                ),
                flush=True,
            )

    def perform_cleanup(self) -> dict[str, object]:
        response = super().perform_cleanup()
        if self.bound is not None:
            artifacts = Path(str(self.bound["artifact_directory"]))
            old = artifacts / "af5-managed-cleanup.json"
            if old.exists():
                old.replace(artifacts / "terminal-cold-restore-managed-cleanup.json")
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
            elif command == "run-cold-restore":
                response = self.start()
            elif command == "retry-cold-restore":
                response = self.retry()
            elif command == "retry-policy":
                response = self.retry_policy()
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
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--activation", required=True, type=Path)
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--preflight-output", type=Path)
    args = parser.parse_args(argv)
    if args.serve:
        return TerminalColdRestoreOperatorJob(args.activation).serve()
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
