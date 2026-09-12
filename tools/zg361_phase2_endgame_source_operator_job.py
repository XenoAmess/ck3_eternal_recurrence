#!/usr/bin/env python3
"""Managed, frozen-input operator for the bounded Phase-2 endgame source."""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib
import json
from pathlib import Path
import shutil
import sys
from typing import Mapping, Sequence

import zg361_phase2_af5_operator_job as base


CONTROLS = ["status", "run-source", "retry-source", "cleanup"]
JOB_ROLE = "phase2-endgame-source"
EXPECTED_OWNER_CHARACTER_ID = 32904


def _source_lineage_id(checkpoint_sha256: str, product_tree_sha256: str) -> str:
    payload = (
        checkpoint_sha256.upper() + ":" + product_tree_sha256.upper()
    ).encode("ascii")
    return "zg361-phase2-seed-" + hashlib.sha256(payload).hexdigest()


def validate_activation(
    activation_path: Path,
    *,
    require_empty_slot: bool,
) -> dict[str, object]:
    value = base.read_object(activation_path)
    if value.get("job_role") != JOB_ROLE:
        raise base.Af5JobError(f"activation job_role must be {JOB_ROLE}")
    route = base.mapping(value.get("source_route"), "source_route")
    owner = base.positive_int(
        route.get("expected_owner_character_id"),
        "source_route.expected_owner_character_id",
    )
    if owner != EXPECTED_OWNER_CHARACTER_ID:
        raise base.Af5JobError(
            f"source owner must be {EXPECTED_OWNER_CHARACTER_ID}"
        )
    expected_date = base.positive_int(
        route.get("expected_date_raw"), "source_route.expected_date_raw"
    )
    max_days = base.positive_int(
        route.get("max_advance_days"), "source_route.max_advance_days"
    )
    if max_days > 30:
        raise base.Af5JobError("source route exceeds the focused 30-day bound")
    timeout = route.get("timeout_seconds", 1800.0)
    if not isinstance(timeout, (int, float)) or timeout <= 0:
        raise base.Af5JobError("source_route.timeout_seconds must be positive")
    game_version = route.get("game_version")
    if not isinstance(game_version, str) or not game_version.strip():
        raise base.Af5JobError("source_route.game_version must be nonempty")
    bound = base.validate_activation(
        activation_path, require_empty_slot=require_empty_slot
    )
    prefix = base.checked_file(
        value.get("phase2_source_checkpoint_prefix"),
        "phase2_source_checkpoint_prefix",
    )
    expected = base.mapping(bound.get("expected_hashes"), "expected_hashes")
    seed_lineage_id = _source_lineage_id(
        str(expected["checkpoint_sha256"]),
        str(expected["product_tree_sha256"]),
    )
    lineage = {
        "schema_version": 1,
        "seed_lineage_id": seed_lineage_id,
        "evidence_class": "real_ck3",
        "fixture_used": False,
        "console_used": False,
        "mod_mount": {
            "kind": "product-only",
            "tree_sha256": str(expected["product_tree_sha256"]).upper(),
        },
        "game": {
            "version": game_version.strip(),
            "exe_sha256": str(expected["game_exe_sha256"]).upper(),
        },
        "input_checkpoint": base.file_record(Path(str(bound["checkpoint"]))),
        "source_code_commit": str(expected["code_commit"]),
    }
    capture_module = importlib.import_module(
        "zg361_phase2_cross_cycle_endgame_source_capture"
    )
    capture_module.preflight_endgame_source_capture_prefix(
        prefix, runtime_capture_lineage=lineage
    )
    bound.update(
        phase2_source_checkpoint_prefix=prefix,
        endgame_source_expected_owner_character_id=owner,
        endgame_source_expected_date_raw=expected_date,
        endgame_source_max_advance_days=max_days,
        endgame_source_timeout_seconds=float(timeout),
        endgame_source_runtime_capture_lineage=lineage,
    )
    return bound


class EndgameSourceOperatorJob(base.Af5OperatorJob):
    def status(self) -> dict[str, object]:
        status = super().status()
        status.pop("af5_evidence", None)
        status.update(
            kind="zg361_phase2_endgame_source_operator_status_v1",
            controls=CONTROLS,
            state=self.state.replace("AF5", "SOURCE"),
            source_result=self.product_result,
        )
        if self.bound:
            target = (
                Path(str(self.bound["artifact_directory"]))
                / "endgame-source-green.json"
            )
            status["source_evidence"] = (
                base.file_record(target) if target.is_file() else None
            )
        return status

    def start(self) -> dict[str, object]:
        response = super().start()
        response["control"] = "run-source"
        return response

    def retry(self) -> dict[str, object]:
        """Reload only the Python capture policy on the retained live pipe."""

        with self.lock:
            artifacts = (
                Path(str(self.bound["artifact_directory"]))
                if self.bound is not None
                else None
            )
            receipt_exists = bool(
                artifacts is not None
                and (artifacts / "source" / "endgame-source-receipt.json").exists()
            )
            if (
                self.state != "AF5_RED_PARKED"
                or self.stage != "bounded_endgame_source_action"
                or self.service is None
                or self.binding is None
                or receipt_exists
                or (self.worker is not None and self.worker.is_alive())
            ):
                return {
                    **self.status(),
                    "control": "retry-source",
                    "accepted": False,
                    "reason": (
                        "no completed pre-save source failure on a retained session"
                    ),
                }
            self.state = "RUNNING_AF5"
            self.worker = base.threading.Thread(
                target=self._run_retry,
                name="endgame-source-hot-retry",
                daemon=False,
            )
            self.worker.start()
            return {
                **self.status(),
                "control": "retry-source",
                "accepted": True,
            }

    def _run_retry(self) -> None:
        try:
            original = base.mapping(self.bound, "original activation")
            artifacts = Path(str(original["artifact_directory"]))
            for name in (
                "af5-red.json",
                "endgame-source-red.json",
                "source/endgame-source-action.json",
                "source/endgame-source-production-entry.json",
            ):
                source = artifacts / name
                if source.is_file():
                    destination = source.with_name(
                        f"{source.stem}-attempt-{self.attempt:02d}{source.suffix}"
                    )
                    if destination.exists():
                        raise base.Af5JobError(
                            f"source retry archive already exists: {destination}"
                        )
                    shutil.copy2(source, destination)
            repaired = validate_activation(
                self.activation_path.with_name("retry-activation.json"),
                require_empty_slot=False,
            )
            old_hashes = base.mapping(
                original["expected_hashes"], "original hashes"
            )
            new_hashes = base.mapping(
                repaired["expected_hashes"], "repaired hashes"
            )
            if any(
                old_hashes[key] != new_hashes[key]
                for key in base.HASH_FIELDS
            ):
                raise base.Af5JobError("source hot retry changed loaded game inputs")
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
            ):
                if original[key] != repaired[key]:
                    raise base.Af5JobError(
                        f"source hot retry changed loaded session input: {key}"
                    )
            before = self._retained_binding()
            self._reload_source_modules(
                Path(str(repaired["repository_root"]))
            )
            after = self._retained_binding()
            if before != after:
                raise base.Af5JobError(
                    "paused source session changed while reloading Python"
                )
            self.attempt += 1
            base.write_object(
                artifacts / f"endgame-source-retry-attempt-{self.attempt:02d}.json",
                {
                    "schema_version": 1,
                    "result": "GREEN",
                    "same_process_retained": True,
                    "before": before,
                    "after": after,
                    "original_code_commit": old_hashes["code_commit"],
                    "repaired_code_commit": new_hashes["code_commit"],
                    "activation": repaired["activation_record"],
                },
            )
            self.bound = repaired
            self.failure_reason = None
            self.product_result = "PENDING"
            self._execute_action(repaired)
        except BaseException as error:
            self._record_failure(error)
        finally:
            print(
                json.dumps(
                    {**self.status(), "notification": "retry-source-finished"},
                    ensure_ascii=False,
                ),
                flush=True,
            )

    @staticmethod
    def _reload_source_modules(root: Path) -> None:
        sys.path.insert(0, str(root / "tools"))
        importlib.invalidate_caches()
        for name in (
            "zhongguo_phase2_source_checkpoint_provider",
            "zg361_phase2_cross_cycle_endgame_source_capture",
            "zg361_phase2_endgame_source_action_cell",
        ):
            module = importlib.reload(importlib.import_module(name))
            if not Path(str(module.__file__)).resolve().is_relative_to(root):
                raise base.Af5JobError(
                    f"repaired source module loaded outside frozen checkout: {name}"
                )

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
                    {**self.status(), "notification": "run-source-finished"},
                    ensure_ascii=False,
                ),
                flush=True,
            )

    def _execute_action(self, bound: Mapping[str, object]) -> None:
        root = Path(str(bound["repository_root"]))
        module = importlib.import_module("zg361_phase2_endgame_source_action_cell")
        if not Path(str(module.__file__)).resolve().is_relative_to(root):
            raise base.Af5JobError(
                "endgame source action is outside the frozen checkout"
            )
        artifacts = Path(str(bound["artifact_directory"]))
        self.stage = "bounded_endgame_source_action"
        evidence = dict(
            module.run_endgame_source_capture(
                self.service,
                evidence_directory=artifacts / "source",
                prefix_manifest=Path(
                    str(bound["phase2_source_checkpoint_prefix"])
                ),
                expected_owner_character_id=int(
                    bound["endgame_source_expected_owner_character_id"]
                ),
                expected_date_raw=int(bound["endgame_source_expected_date_raw"]),
                runtime_capture_lineage=deepcopy(
                    dict(bound["endgame_source_runtime_capture_lineage"])
                ),
                request_nonce=f"{bound['round']}.phase2-endgame-source",
                max_advance_days=int(bound["endgame_source_max_advance_days"]),
                timeout_seconds=float(bound["endgame_source_timeout_seconds"]),
            )
        )
        if not (
            evidence.get("result") == "GREEN"
            and evidence.get("source_checkpoint_captured") is True
        ):
            raise base.Af5JobError(
                "bounded endgame source action returned RED", evidence
            )
        expected = base.mapping(bound["expected_hashes"], "expected_hashes")
        binding = base.mapping(self.binding, "native binding")
        evidence.update(
            round=bound["round"],
            bridge_pid=binding["bridge_pid"],
            connection_generation=binding["connection_generation"],
            execution_identity={
                "repository_root": str(root),
                "code_commit": expected["code_commit"],
            },
            input_checkpoint=base.file_record(Path(str(bound["checkpoint"]))),
            product_tree_sha256=expected["product_tree_sha256"],
            bridge_dll=base.file_record(Path(str(bound["bridge_dll"])),),
            production_live=True,
            fixture_used=False,
            console_used=False,
            video_lock_touched=False,
        )
        base.write_object(artifacts / "endgame-source-green.json", evidence)
        self.af5_evidence = evidence
        self.product_result = "GREEN"
        self.state = "AF5_GREEN_PARKED"
        self.stage = "endgame_source_captured_and_registered"
        self.failure_reason = None

    def _record_failure(self, error: BaseException) -> None:
        super()._record_failure(error)
        if self.bound is None:
            return
        artifacts = Path(str(self.bound["artifact_directory"]))
        generic = artifacts / "af5-red.json"
        if generic.is_file():
            shutil.copy2(generic, artifacts / "endgame-source-red.json")

    def perform_cleanup(self) -> dict[str, object]:
        response = super().perform_cleanup()
        if self.bound is not None:
            artifacts = Path(str(self.bound["artifact_directory"]))
            generic = artifacts / "af5-managed-cleanup.json"
            if generic.exists():
                generic.replace(artifacts / "endgame-source-managed-cleanup.json")
        return response

    def serve(self) -> int:
        self.bound = validate_activation(
            self.activation_path, require_empty_slot=False
        )
        print(json.dumps(self.status(), ensure_ascii=False), flush=True)
        while not self.stop_requested.is_set():
            line = sys.stdin.readline()
            if line == "":
                self.stop_requested.wait(5.0)
                continue
            command = line.strip().casefold()
            if command == "status":
                response = self.status()
            elif command == "run-source":
                response = self.start()
            elif command == "retry-source":
                response = self.retry()
            elif command == "cleanup":
                response = self.perform_cleanup()
            else:
                response = {
                    "result": "RED",
                    "error": "unknown control",
                    "controls": CONTROLS,
                }
            print(json.dumps(response, ensure_ascii=False), flush=True)
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
        return EndgameSourceOperatorJob(args.activation).serve()
    bound = validate_activation(args.activation, require_empty_slot=False)
    result = {
        "result": "GREEN",
        "launch_requested": False,
        "job_role": JOB_ROLE,
        "activation": bound["activation_record"],
    }
    if args.preflight_output is not None:
        base.write_object(args.preflight_output, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
