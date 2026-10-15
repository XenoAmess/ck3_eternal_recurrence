"""Two offline regressions: late proof publication and explicit evidence quota.

All process, actor, hello and SDK values below are synthetic. These tests never
open a native pipe, launch a process, access a desktop or allocate the quota.
"""
from __future__ import annotations

import asyncio
import copy
import importlib.util
import json
from pathlib import Path
import sys
from unittest import mock

import pytest


TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
SPEC = importlib.util.spec_from_file_location(
    "episode04_runtime_evidence_bootstrap_test_subject",
    TOOLS / "capture_bootstrap.py",
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("repository capture bootstrap is absent")
bootstrap = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = bootstrap
SPEC.loader.exec_module(bootstrap)


def test_proof_may_be_published_after_run_reservation_before_recording_start(tmp_path):
    proof_path = tmp_path / "later-runtime-proof.json"
    assert not proof_path.exists()

    # Startup and ordinary requests must not read or hash a future proof.
    with mock.patch.object(
        bootstrap, "identity", side_effect=AssertionError("proof pinned before recording start")
    ):
        reservation = bootstrap.reserve_runtime_actor_identity_receipt(proof_path)
        assert reservation == {
            "path": str(proof_path), "status": "unverified-until-recording-start"
        }
        assert bootstrap.capture_runtime_actor_identity_receipt(
            reservation, None, {"version": "1.20.0.4"}
        ) is None
        ordinary_sdk = mock.AsyncMock(return_value={"fixture_snapshot": "available"})
        assert asyncio.run(ordinary_sdk("ck3_take_snapshot", {})) == {
            "fixture_snapshot": "available"
        }
        ordinary_sdk.assert_awaited_once_with("ck3_take_snapshot", {})
    assert not proof_path.exists()
    with pytest.raises(FileNotFoundError):
        bootstrap.capture_runtime_actor_identity_receipt(
            reservation, "start", {"version": "1.20.0.4"}
        )

    machine = "synthetic-review02-test-machine"
    actor, pid, generation = 43210, 9876, 4
    episode = "native-synthetic-review02-43210"
    target = bootstrap.game_target("1.20.0.4")
    prepared = {
        "machine_id": machine,
        "profile_dir": str(tmp_path / "profile"),
        "state_dir": str(tmp_path / "state"),
        "pipe_name": "synthetic-pipe-never-opened",
        "target_build": target,
        "game": {"sha256": target["exe_sha256"]},
        "bridge_dll": {"sha256": "a" * 64},
        "succession_lifecycle": {"lifecycle": "ordinary_campaign_succession"},
        "checkpoint": None,
        "character_intent": dict(bootstrap.ROBERT_INTENT),
    }
    unchanged_prepared = copy.deepcopy(prepared)
    prepared_path = tmp_path / "prepared.json"
    prepared_path.write_text(json.dumps(prepared), encoding="utf-8")
    proof = {
        "schema": "xar.e04.robert-identity-source-chain.actual.v1",
        "machine_id": machine,
        "source_head": "f" * 40,
        "recorded_at_utc": "2026-10-15T00:00:00+00:00",
        "stable_character_intent": {
            "bookmark_character_name_key": bootstrap.ROBERT_INTENT["character_name_key"],
            "historical_id": bootstrap.ROBERT_INTENT["history_id"],
            "historical_title_key": bootstrap.ROBERT_INTENT["history_title_key"],
        },
        "actual_runtime_character_full_id": actor,
        "pid": pid,
        "connection_generation": generation,
        "episode_run_id": episode,
        "initial_date_raw": 53144000,
        "proof_chain": [
            {"layer": "source-controlled-flow"},
            {"layer": "independent-live-reads-produced-by-root"},
            {"layer": "normal-save-materialization-and-bounded-header-read"},
        ],
        "superseded_prelaunch_numeric_expectation": {
            "prepared": bootstrap.identity(prepared_path),
            "old_expected_character_id": None,
        },
    }
    # Synthetic Root publication happens only after the reservation/ordinary SDK.
    proof_path.write_text(json.dumps(proof), encoding="utf-8")
    published_bytes = proof_path.read_bytes()
    receipt_pin = bootstrap.capture_runtime_actor_identity_receipt(
        reservation, "start", target
    )
    assert receipt_pin == bootstrap.identity(proof_path)
    snapshot = {
        "played_character": {"character_id": actor, "alive": True},
        "episode_character_id": actor,
        "episode_run_id": episode,
        "paused": True,
        "date_raw": 53144000,
        "snapshot_id": "synthetic-snapshot",
        "native_revision": 2,
        "diagnostics": {"bridge_pid": pid, "connection_generation": generation},
    }
    diagnostics = {
        "connected": True,
        "bridge_pid": pid,
        "connection_generation": generation,
        "hello": {
            "pid": pid,
            "ck3_build_match": True,
            "game_adapter_status": "ready",
            "game_adapter_id": "ck3-1.20.0.4-msvc-x64",
            "expected_ck3_version": "1.20.0.4",
            "expected_ck3_sha256": target["exe_sha256"],
        },
    }
    with mock.patch.object(bootstrap, "current_machine_id", return_value=machine):
        binding = bootstrap.require_capture_context(
            prepared, snapshot, diagnostics, {"operation": "start", "target_pid": pid},
            runtime_actor_receipt=receipt_pin,
        )
    assert binding["expected_character_id"] == actor
    assert binding["identity_receipt"] == receipt_pin
    assert prepared == unchanged_prepared
    assert proof_path.read_bytes() == published_bytes


def test_explicit_512MiB_budget_is_accepted_but_larger_budget_is_rejected():
    limit = 512 * 1024 * 1024
    assert bootstrap.validate_army_history_limit(limit) == limit
    with pytest.raises(ValueError, match="512MiB"):
        bootstrap.validate_army_history_limit(limit + 1)
    arguments = [
        "run", "--prepared", "prepared", "--run-dir", "run",
        "--steam-offline-receipt", "offline", "--screen-cli", "screen",
        "--task-bus", "bus", "--screen-repo", "repository",
        "--screen-task-id", "synthetic-task", "--screen-expected-sequence", "1",
        "--screen-cli-sha256", "0" * 64,
    ]
    assert bootstrap.parser().parse_args(arguments).army_history_sidecar_limit_bytes == 0
