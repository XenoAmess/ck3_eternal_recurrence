#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any

from faction_gift_mitigation_paused_live_harness import (
    CANDIDATE_CONTRACT,
    CONTRACT,
    EXECUTABLE_SHA256,
    GAME_VERSION,
    GOLD_SCALE,
    RETRY_POLICY,
    RawStepResult,
    run_harness,
)


PLAYER_ID = 0x81000011
FACTION_ID = 0xA1000022
RECIPIENT_ID = 0xC1000033
DEFINITION_HASH = 0xE313B9C7D54A0211
COMMIT = "b" * 40


def check(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


class FakeTransport:
    def __init__(self, responses: dict[str, Any]) -> None:
        self.responses = responses
        self.calls: list[str] = []

    def call(self, step: str, request: dict[str, Any]) -> RawStepResult:
        self.calls.append(step)
        response = self.responses[step]
        if isinstance(response, RawStepResult):
            return response
        return RawStepResult(
            0,
            json.dumps(response, separators=(",", ":")).encode("utf-8"),
            b"fixture-stderr",
        )


def good_responses() -> dict[str, Any]:
    targeting = {
        "status": "ready",
        "paused": True,
        "red_flags": 0,
        "snapshot_revision": 700,
        "native_snapshot_revision": 1700,
        "date_raw": 90234,
        "player_character_id": PLAYER_ID,
        "source_faction_id": FACTION_ID,
        "recipient_character_id": RECIPIENT_ID,
        "membership_role": "character_member",
        "source_faction_targeting_player": True,
        "source_faction_at_war": False,
        "player_gold_raw": 50_000_000,
        "gift_preview": {
            "available": True,
            "definition_key": "gift_interaction",
            "definition_stable_hash": DEFINITION_HASH,
            "interaction_legal": True,
            "auto_accept": True,
            "gold_cost_raw": 5_000_000,
            "gold_scale": GOLD_SCALE,
            "opinion_delta": 40,
        },
    }
    gate = {
        "terminal": "ready",
        "red_flags": 0,
        "ready_for_single_submit": True,
        "action_callbacks_invoked": False,
        "snapshot_revision": 700,
        "native_snapshot_revision": 1700,
        "date_raw": 90234,
        "player_character_id": PLAYER_ID,
        "source_faction_id": FACTION_ID,
        "recipient_character_id": RECIPIENT_ID,
        "player_gold_raw": 50_000_000,
        "gift_gold_cost_raw": 5_000_000,
        "minimum_gold_reserve_raw": 45_000_000,
    }
    request_id = f"gift:700:{FACTION_ID:08x}:{RECIPIENT_ID:08x}"
    ack = {
        "status": "submitted_verification_pending",
        "verification_pending": True,
        "request_id": request_id,
        "pre_snapshot_revision": 700,
        "pre_native_snapshot_revision": 1700,
        "pre_observed_date_raw": 90234,
        "player_character_id": PLAYER_ID,
        "source_faction_id": FACTION_ID,
        "recipient_character_id": RECIPIENT_ID,
        "expected_gold_cost_raw": 5_000_000,
        "expected_opinion_delta": 40,
    }
    receipt = {
        "status": "mitigated",
        "request_id": request_id,
        "post_snapshot_revision": 701,
        "post_native_snapshot_revision": 1701,
        "post_observed_date_raw": 90234,
        "player_character_id": PLAYER_ID,
        "source_faction_id": FACTION_ID,
        "recipient_character_id": RECIPIENT_ID,
        "post_player_gold_raw": 45_000_000,
        "post_gift_opinion_present": True,
        "post_gift_opinion_modifier_value": 40,
        "source_faction_present": True,
        "recipient_still_in_source_faction": True,
        "mitigation_applied": True,
        "threat_resolved": False,
        "postcondition_verified": True,
    }
    return {
        "targeting": targeting,
        "gate": gate,
        "submit": ack,
        "receipt": receipt,
    }


def make_inputs(root: Path) -> tuple[Path, Path]:
    candidate_dir = root / "candidate"
    candidate_dir.mkdir()
    payload = b"hash-bound-faction-gift-candidate"
    (candidate_dir / "candidate.bin").write_bytes(payload)
    exact = {
        "game_version": GAME_VERSION,
        "executable_sha256": EXECUTABLE_SHA256,
    }
    candidate = {
        "schema_version": 1,
        "contract": CANDIDATE_CONTRACT,
        "candidate_id": "fixture-faction-gift-candidate",
        "commit": COMMIT,
        "exact_build": exact,
        "files": [
            {"path": "candidate.bin", "sha256": sha256(payload)},
        ],
    }
    candidate_path = candidate_dir / "candidate-manifest.json"
    candidate_raw = json.dumps(
        candidate, indent=2, sort_keys=True
    ).encode("utf-8") + b"\n"
    candidate_path.write_bytes(candidate_raw)
    runtime = {
        "schema_version": 1,
        "contract": CONTRACT,
        "raw_first": True,
        "launch_ck3": False,
        "retry_policy": RETRY_POLICY,
        "exact_build": exact,
        "candidate": {
            "candidate_id": candidate["candidate_id"],
            "commit": COMMIT,
            "manifest_sha256": sha256(candidate_raw),
        },
        "policy": {
            "gold_scale": GOLD_SCALE,
            "minimum_gold_reserve_raw": 45_000_000,
        },
        "transport_command": ["fixture-transport"],
        "transport_timeout_seconds": 10,
    }
    runtime_path = root / "runtime-config.json"
    runtime_path.write_text(
        json.dumps(runtime, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return runtime_path, candidate_path


def test_green_raw_first_receipt() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        runtime, candidate = make_inputs(root)
        transport = FakeTransport(good_responses())
        result = run_harness(
            runtime,
            candidate,
            root / "artifacts",
            state_dir=root / "state",
            transport=transport,
        )
        check(result.terminal == "green", "valid receipt must be GREEN")
        check(result.receipt_status == "mitigated", "receipt status lost")
        check(
            transport.calls == ["targeting", "gate", "submit", "receipt"],
            "OODA step order changed",
        )
        for ordinal, step in enumerate(transport.calls, 1):
            check(
                (root / "artifacts" / f"{ordinal:02d}-{step}.stdout.raw").is_file(),
                f"raw stdout missing for {step}",
            )
            check(
                (root / "artifacts" / f"{ordinal:02d}-{step}.stderr.raw").is_file(),
                f"raw stderr missing for {step}",
            )
        check(
            len(list((root / "state").glob("*.submit-claim.json"))) == 1,
            "single-submit ledger missing",
        )


def test_targeting_and_gate_red_stop_before_submit() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        runtime, candidate = make_inputs(root)
        responses = good_responses()
        responses["targeting"] = RawStepResult(0, b"not-json", b"raw-red")
        transport = FakeTransport(responses)
        result = run_harness(
            runtime,
            candidate,
            root / "artifacts-a",
            state_dir=root / "state-a",
            transport=transport,
        )
        check(result.red_type == "transport_red", "invalid raw needs transport RED")
        check(transport.calls == ["targeting"], "invalid targeting must stop")
        check(
            (root / "artifacts-a" / "01-targeting.stdout.raw").read_bytes()
            == b"not-json",
            "invalid raw was not preserved before parsing",
        )

        responses = good_responses()
        responses["gate"]["terminal"] = "red"
        responses["gate"]["red_flags"] = 64
        transport = FakeTransport(responses)
        result = run_harness(
            runtime,
            candidate,
            root / "artifacts-b",
            state_dir=root / "state-b",
            transport=transport,
        )
        check(result.red_type == "gate_red", "gate failure needs typed RED")
        check(
            transport.calls == ["targeting", "gate"],
            "gate RED must stop before submit",
        )


def test_ack_pending_only_and_no_candidate_retry() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        runtime, candidate = make_inputs(root)
        responses = good_responses()
        responses["submit"]["mitigation_applied"] = True
        first_transport = FakeTransport(responses)
        result = run_harness(
            runtime,
            candidate,
            root / "artifacts-a",
            state_dir=root / "state",
            transport=first_transport,
        )
        check(result.red_type == "submit_ack_red", "success-like ACK needs RED")
        check(
            first_transport.calls == ["targeting", "gate", "submit"],
            "invalid ACK must not enter receipt",
        )
        second_transport = FakeTransport(good_responses())
        result = run_harness(
            runtime,
            candidate,
            root / "artifacts-b",
            state_dir=root / "state",
            transport=second_transport,
        )
        check(
            result.red_type == "candidate_retry_forbidden_red",
            "same hash-bound candidate retry must remain RED",
        )
        check(second_transport.calls == [], "retry must stop before runtime calls")


def test_receipt_requires_fresh_requery() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        runtime, candidate = make_inputs(root)
        responses = good_responses()
        responses["receipt"]["post_snapshot_revision"] = 700
        transport = FakeTransport(responses)
        result = run_harness(
            runtime,
            candidate,
            root / "artifacts",
            state_dir=root / "state",
            transport=transport,
        )
        check(result.red_type == "receipt_red", "stale receipt needs typed RED")
        check(not result.postcondition_verified, "stale receipt cannot verify")
        check(
            transport.calls == ["targeting", "gate", "submit", "receipt"],
            "receipt path did not execute exactly once",
        )


def test_left_receipt_is_verified_without_causal_overclaim() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        runtime, candidate = make_inputs(root)
        responses = good_responses()
        responses["receipt"].update(
            {
                "status": "left",
                "source_faction_present": True,
                "recipient_still_in_source_faction": False,
                "recipient_left": True,
                "threat_resolved": True,
            }
        )
        result = run_harness(
            runtime,
            candidate,
            root / "artifacts",
            state_dir=root / "state",
            transport=FakeTransport(responses),
        )
        check(result.terminal == "green", "verified left receipt should be GREEN")
        check(result.receipt_status == "left", "left status was not retained")


def test_candidate_file_hash_red_precedes_runtime() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        runtime, candidate = make_inputs(root)
        (candidate.parent / "candidate.bin").write_bytes(b"mutated")
        transport = FakeTransport(good_responses())
        result = run_harness(
            runtime,
            candidate,
            root / "artifacts",
            state_dir=root / "state",
            transport=transport,
        )
        check(
            result.red_type == "candidate_file_hash_red",
            "candidate mutation needs hash RED",
        )
        check(transport.calls == [], "hash RED must precede runtime queries")


def main() -> int:
    tests = [
        test_green_raw_first_receipt,
        test_targeting_and_gate_red_stop_before_submit,
        test_ack_pending_only_and_no_candidate_retry,
        test_receipt_requires_fresh_requery,
        test_left_receipt_is_verified_without_causal_overclaim,
        test_candidate_file_hash_red_precedes_runtime,
    ]
    failures = 0
    for test in tests:
        try:
            test()
            print(f"PASS {test.__name__}")
        except Exception as error:
            failures += 1
            print(f"FAIL {test.__name__}: {error}")
    print(f"{len(tests) - failures}/{len(tests)} passed")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
