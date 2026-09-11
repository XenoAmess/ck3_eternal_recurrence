#!/usr/bin/env python3
"""Capture one MCP-native single-player source for the Stage 10 action."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence

import zg361_phase2_af5_operator_job as base


CONTROLS = ["status", "capture-source", "cleanup"]
JOB_ROLE = "stage10-player-source-capture"
TOPOLOGY_KIND = "ck3_save_player_topology_offline_v1"
LIVE_SOURCE_KIND = "zg361_stage10_player_source_capture_v1"


def _file_payload(value: object, label: str) -> tuple[Path, dict[str, object]]:
    path = base.checked_file(value, label)
    return path, base.read_object(path)


def _played_id(snapshot: Mapping[str, object]) -> object:
    played = snapshot.get("played_character")
    return played.get("character_id") if isinstance(played, Mapping) else None


def _binding(value: object, *, expected_player: int) -> dict[str, object]:
    snapshot = base.mapping(value, "source capture snapshot")
    diagnostics = base.mapping(snapshot.get("diagnostics"), "snapshot diagnostics")
    binding = {
        "snapshot_id": snapshot.get("snapshot_id"),
        "revision": snapshot.get("revision"),
        "native_revision": snapshot.get("native_revision"),
        "date_raw": snapshot.get("date_raw"),
        "paused": snapshot.get("paused"),
        "map_ready": snapshot.get("map_ready"),
        "player_character_id": _played_id(snapshot),
        "active_event": copy.deepcopy(snapshot.get("active_event")),
        "bridge_pid": diagnostics.get("bridge_pid"),
        "connection_generation": diagnostics.get("connection_generation"),
    }
    if not (
        binding["paused"] is True
        and binding["map_ready"] is True
        and binding["player_character_id"] == expected_player
        and binding["active_event"] is None
        and isinstance(binding["snapshot_id"], str)
        and bool(binding["snapshot_id"])
        and isinstance(binding["revision"], int)
        and not isinstance(binding["revision"], bool)
        and isinstance(binding["native_revision"], int)
        and not isinstance(binding["native_revision"], bool)
        and int(binding["native_revision"]) > 0
        and isinstance(binding["date_raw"], int)
        and not isinstance(binding["date_raw"], bool)
        and base.positive_int(binding["bridge_pid"], "bridge PID") > 0
        and base.positive_int(
            binding["connection_generation"], "connection generation"
        )
        > 0
    ):
        raise base.Af5JobError("Stage 10 source capture lacks a paused player binding")
    return binding


def _campaign(
    value: object, *, expected_player: int, expected_owner: int | None
) -> dict[str, object]:
    campaign = base.mapping(value, "campaign-root context")
    readiness = base.mapping(campaign.get("readiness"), "campaign readiness")
    rules = campaign.get("selected_game_rule_tokens")
    valid = (
        campaign.get("status") == "available"
        and campaign.get("campaign_root_context_ready") is True
        and readiness.get("ready") is True
        and campaign.get("player_character_id") == expected_player
        and campaign.get("player_character_alive") is True
        and isinstance(rules, list)
        and "zg361_on" in rules
    )
    if expected_owner is not None:
        title = base.mapping(campaign.get("primary_title"), "target primary title")
        government = base.mapping(campaign.get("government"), "target government")
        flags = government.get("flags")
        valid = valid and (
            campaign.get("independent") is False
            and campaign.get("immediate_liege_character_id") == expected_owner
            and isinstance(title.get("tier_raw"), int)
            and not isinstance(title.get("tier_raw"), bool)
            and int(title["tier_raw"]) >= 3
            and isinstance(flags, list)
            and "government_is_celestial" in flags
        )
    if not valid:
        raise base.Af5JobError(
            "Stage 10 source capture campaign-root qualification failed", campaign
        )
    return copy.deepcopy(dict(campaign))


def _validate_activation_inputs(
    value: Mapping[str, object], bound: Mapping[str, object]
) -> dict[str, object]:
    expected = base.mapping(bound.get("expected_hashes"), "expected hashes")
    checkpoint = Path(str(bound["checkpoint"])).resolve()
    source_player = base.positive_int(
        value.get("source_player_character_id"), "source player"
    )
    target = base.positive_int(
        value.get("target_player_manager_character_id"), "target player manager"
    )
    owner = base.positive_int(
        value.get("target_owner_character_id"), "target owner"
    )
    topology_path, topology = _file_payload(
        value.get("stage10_topology_report"), "Stage 10 topology report"
    )
    source = base.mapping(topology.get("source"), "topology source")
    candidates = topology.get("player_manager_candidates")
    candidate = candidates[0] if isinstance(candidates, list) and len(candidates) == 1 else None
    qualification_path, qualification = _file_payload(
        value.get("source_live_qualification"), "source live qualification"
    )
    provenance_path, provenance = _file_payload(
        value.get("source_checkpoint_provenance"), "source checkpoint provenance"
    )
    provenance_checkpoint = base.mapping(
        provenance.get("checkpoint"), "provenance checkpoint"
    )
    source_binding = base.mapping(
        provenance.get("source_contract_binding"), "source contract binding"
    )
    before = base.mapping(
        qualification.get("before_snapshot"), "qualification before snapshot"
    )
    if not (
        source_player != target
        and target != owner
        and topology.get("schema_version") == 1
        and topology.get("kind") == TOPOLOGY_KIND
        and topology.get("result") == "GREEN"
        and topology.get("authority")
        == "offline-prelaunch-only-live-exact-build-mcp-remains-authoritative"
        and topology.get("game_version") == "1.19.0.6"
        and topology.get("meta_number_of_players") == 1
        and topology.get("played_character_records")
        == [{"character_id": source_player, "player_id": 1}]
        and topology.get("currently_played_character_ids") == [source_player]
        and isinstance(candidate, Mapping)
        and candidate.get("player_manager_character_id") == target
        and candidate.get("immediate_liege_character_id") == owner
        and isinstance(candidate.get("player_primary_title_tier"), int)
        and not isinstance(candidate.get("player_primary_title_tier"), bool)
        and int(candidate["player_primary_title_tier"]) >= 3
        and candidate.get("player_government") == "celestial_government"
        and isinstance(candidate.get("direct_landed_vassal_count"), int)
        and int(candidate["direct_landed_vassal_count"]) >= 1
        and isinstance(source.get("path"), str)
        and Path(str(source["path"])).resolve() == checkpoint
        and source.get("bytes") == checkpoint.stat().st_size
        and str(source.get("sha256", "")).upper()
        == str(expected["checkpoint_sha256"]).upper()
        and qualification.get("result") == "GREEN"
        and qualification.get("game_time_advanced") is False
        and before.get("paused") is True
        and before.get("map_ready") is True
        and _played_id(before) == source_player
        and provenance.get("result") == "GREEN"
        and str(provenance_checkpoint.get("sha256", "")).upper()
        == str(expected["checkpoint_sha256"]).upper()
        and source_binding.get("played_manager_character_id") == source_player
    ):
        raise base.Af5JobError(
            "Stage 10 source capture activation lacks matching offline/live provenance"
        )
    return {
        "source_player_character_id": source_player,
        "target_player_manager_character_id": target,
        "target_owner_character_id": owner,
        "stage10_topology_report": topology_path,
        "source_live_qualification": qualification_path,
        "source_checkpoint_provenance": provenance_path,
    }


def validate_activation(path: Path, *, require_empty_slot: bool) -> dict[str, object]:
    value = base.read_object(path)
    if value.get("job_role") != JOB_ROLE:
        raise base.Af5JobError("activation does not target Stage 10 source capture")
    bound = base.validate_activation(path, require_empty_slot=require_empty_slot)
    bound.update(_validate_activation_inputs(value, bound))
    return bound


class Stage10PlayerSourceCaptureOperatorJob(base.Af5OperatorJob):
    def status(self) -> dict[str, object]:
        status = super().status()
        status.pop("af5_evidence", None)
        status.update(
            kind="zg361_stage10_player_source_capture_operator_status_v1",
            controls=CONTROLS,
            state=self.state.replace("AF5", "SOURCE"),
            source_result=self.product_result,
        )
        return status

    def start(self) -> dict[str, object]:
        response = super().start()
        response["control"] = "capture-source"
        return response

    def _run(self) -> None:
        """Revalidate with this job's source-specific activation contract."""

        try:
            bound = validate_activation(self.activation_path, require_empty_slot=True)
            with self.lock:
                self.bound = bound
            self._execute(bound)
        except BaseException as error:
            self._record_failure(error)
        finally:
            print(
                json.dumps(
                    {**self.status(), "notification": "capture-source-finished"},
                    ensure_ascii=False,
                ),
                flush=True,
            )

    def _execute_action(self, bound: Mapping[str, object]) -> None:
        if self.service is None or self.runner is None:
            raise base.Af5JobError("source capture runtime is not bound")
        service = self.service
        artifacts = Path(str(bound["artifact_directory"]))
        expected = base.mapping(bound["expected_hashes"], "expected hashes")
        source_player = int(bound["source_player_character_id"])
        target = int(bound["target_player_manager_character_id"])
        owner = int(bound["target_owner_character_id"])
        self.stage = "source_player_binding"
        before_snapshot = service.snapshot()
        before = _binding(before_snapshot, expected_player=source_player)
        source_campaign = _campaign(
            service.query_campaign_root_context_v1(
                expected_revision=int(before["revision"])
            ),
            expected_player=source_player,
            expected_owner=None,
        )
        current = _binding(service.snapshot(), expected_player=source_player)
        if any(
            current[key] != before[key]
            for key in (
                "date_raw",
                "player_character_id",
                "bridge_pid",
                "connection_generation",
                "active_event",
            )
        ):
            raise base.Af5JobError("source binding changed during qualification")

        self.stage = "target_player_rebind"
        switch = service.set_player_character_v1(
            target, expected_revision=int(current["revision"])
        )
        after = _binding(service.snapshot(), expected_player=target)
        if not (
            isinstance(switch, Mapping)
            and switch.get("accepted") is True
            and switch.get("status") == "switched"
            and switch.get("step") == f"set-played-character-v1-{target}"
            and switch.get("from_character_id") == source_player
            and switch.get("to_character_id") == target
            and switch.get("postcondition_verified") is True
            and switch.get("episode_rebind_performed") is True
            and switch.get("paused") is True
            and switch.get("map_ready") is True
            and before["date_raw"] == after["date_raw"]
            and before["bridge_pid"] == after["bridge_pid"]
            and before["connection_generation"] == after["connection_generation"]
        ):
            raise base.Af5JobError("native player rebind failed", switch)

        self.stage = "target_campaign_qualification"
        target_campaign = _campaign(
            service.query_campaign_root_context_v1(
                expected_revision=int(after["revision"])
            ),
            expected_player=target,
            expected_owner=owner,
        )
        target_binding = _binding(service.snapshot(), expected_player=target)
        if any(
            target_binding[key] != after[key]
            for key in (
                "date_raw",
                "player_character_id",
                "bridge_pid",
                "connection_generation",
                "active_event",
            )
        ):
            raise base.Af5JobError("target binding changed during qualification")

        self.stage = "target_checkpoint"
        saved = service.save_checkpoint(
            expected_revision=int(target_binding["revision"])
        )
        checkpoint = saved.get("checkpoint") if isinstance(saved, Mapping) else None
        if not (
            isinstance(saved, Mapping)
            and saved.get("accepted") is True
            and isinstance(checkpoint, Mapping)
            and checkpoint.get("status") == "saved"
        ):
            raise base.Af5JobError("target player checkpoint was not saved", saved)
        archived = self.runner._phase2_archive_checkpoint(
            checkpoint,
            artifacts / "stage10-player-manager-source.ck3",
            save_lineage_id=f"{bound['round']}.stage10.player-manager-source",
        )
        post_save = _binding(service.snapshot(), expected_player=target)
        if any(
            post_save[key] != target_binding[key]
            for key in (
                "date_raw",
                "player_character_id",
                "bridge_pid",
                "connection_generation",
                "active_event",
            )
        ):
            raise base.Af5JobError("native save changed the target binding")

        evidence = {
            "schema_version": 1,
            "kind": LIVE_SOURCE_KIND,
            "result": "GREEN",
            "round": bound["round"],
            "production_live": True,
            "mcp_native_save": True,
            "generic_character_rebind_used": True,
            "fixture_used": False,
            "console_used": False,
            "ocr_used": False,
            "coordinates_used": False,
            "game_time_advanced": False,
            "source_binding": before,
            "source_campaign_root": source_campaign,
            "player_switch_receipt": copy.deepcopy(dict(switch)),
            "target_binding": target_binding,
            "target_campaign_root": target_campaign,
            "native_save_receipt": copy.deepcopy(dict(saved)),
            "target_checkpoint": archived,
            "post_save_binding": post_save,
            "product_tree_sha256": expected["product_tree_sha256"],
            "code_commit": expected["code_commit"],
            "source_topology_report": base.file_record(
                Path(str(bound["stage10_topology_report"]))
            ),
            "source_live_qualification": base.file_record(
                Path(str(bound["source_live_qualification"]))
            ),
            "source_checkpoint_provenance": base.file_record(
                Path(str(bound["source_checkpoint_provenance"]))
            ),
            "video_lock_touched": False,
        }
        base.write_object(artifacts / "stage10-player-source-green.json", evidence)
        with self.lock:
            self.af5_evidence = evidence
            self.product_result = "GREEN"
            self.state = "AF5_GREEN_PARKED"
            self.stage = "source_verified_and_saved"
            self.failure_reason = None

    def _record_failure(self, error: BaseException) -> None:
        super()._record_failure(error)
        if self.bound is None:
            return
        artifacts = Path(str(self.bound["artifact_directory"]))
        base.write_object(
            artifacts / "stage10-player-source-red.json",
            copy.deepcopy(self.failure_evidence or {}),
        )
        (artifacts / "af5-red.json").unlink(missing_ok=True)

    def perform_cleanup(self) -> dict[str, object]:
        response = super().perform_cleanup()
        if self.bound is not None:
            artifacts = Path(str(self.bound["artifact_directory"]))
            old = artifacts / "af5-managed-cleanup.json"
            if old.exists():
                old.replace(artifacts / "stage10-player-source-managed-cleanup.json")
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
            elif command == "capture-source":
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
    args = parser.parse_args(argv)
    job = Stage10PlayerSourceCaptureOperatorJob(args.activation)
    if args.serve:
        return job.serve()
    bound = validate_activation(args.activation, require_empty_slot=True)
    print(json.dumps({"result": "GREEN", "bound": bound}, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
