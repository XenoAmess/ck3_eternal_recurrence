#!/usr/bin/env python3
"""Verify the private character-interaction proposal action core contract."""

from __future__ import annotations

import json
from pathlib import Path


EXPECTED_KEYS = [
    "gift_interaction",
    "recruit_guest_interaction",
    "invite_to_court_interaction",
    "offer_vassalization_interaction",
    "demand_payment_interaction",
    "educate_child_interaction",
    "offer_ward_interaction",
    "offer_guardianship_interaction",
    "grant_titles_interaction",
    "grant_vassal_interaction",
    "ransom_interaction",
]
EXPECTED_SHA = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def require_tokens(text: str, tokens: tuple[str, ...], label: str) -> None:
    missing = [token for token in tokens if token not in text]
    require(not missing, f"{label} missing tokens: {missing}")


def main() -> int:
    native_root = Path(__file__).resolve().parents[1]
    header = (
        native_root
        / "include/xar_bridge/character_interaction_proposal_action_core_v1.hpp"
    ).read_text(encoding="utf-8")
    source = (
        native_root / "src/character_interaction_proposal_action_core_v1.cpp"
    ).read_text(encoding="utf-8")
    test = (
        native_root / "src/character_interaction_proposal_action_core_v1_test.cpp"
    ).read_text(encoding="utf-8")
    abi = json.loads(
        (
            native_root
            / "research/character_interaction_proposal_action_core_v1_abi.json"
        ).read_text(encoding="utf-8")
    )

    require(abi["schema_version"] == 1, "schema version drifted")
    require(
        abi["private_key"] == "character_interaction_proposal_action_core_v1",
        "private key drifted",
    )
    require(
        abi["upstream"]["source_adapter_commit"]
        == "9de83033e8fd17767413ccb3beb8740e37a9bbae",
        "DIPLO3 baseline drifted",
    )
    require(
        abi["exact_build"]["executable_sha256"] == EXPECTED_SHA,
        "exact executable hash drifted",
    )
    require(
        [row["interaction_key"] for row in abi["first_allowlist"]]
        == EXPECTED_KEYS,
        "eleven-key allowlist drifted",
    )
    require(
        len({row["postcondition"] for row in abi["first_allowlist"]}) == 11,
        "postcondition mapping is not one-to-one",
    )
    require(
        abi["upstream"]["currently_source_reachable_keys"]
        == EXPECTED_KEYS[:5],
        "current DIPLO3 reachability drifted",
    )
    require(
        abi["upstream"]["typed_payload_source_pending_keys"]
        == EXPECTED_KEYS[5:],
        "typed payload pending set drifted",
    )
    require(
        all(value is False for value in abi["scope"].values()),
        "private scope claimed a forbidden integration",
    )
    readiness = abi["readiness"]
    require(
        all(
            readiness[key] is True
            for key in (
                "private_semantic_action_core_implemented",
                "eleven_key_semantic_allowlist_implemented",
                "budget_gate_implemented",
                "single_submit_state_implemented",
                "pending_ack_implemented",
                "interaction_specific_receipts_implemented",
            )
        ),
        "implemented readiness regressed",
    )
    require(
        readiness["native_submit_binding_registered"] is False
        and readiness["public_schema_registered"] is False
        and readiness["production_action_live"] is False,
        "unwired core was overstated",
    )

    require_tokens(
        header,
        (
            '"character_interaction_proposal_action_core_v1"',
            "submitted_verification_pending",
            "response_pending",
            "maximum_actor_spend_raw",
            "matching_pending_proposal",
            "interaction_specific_postcondition_verified",
            "submission_in_flight",
            "SubmitCharacterInteractionProposalOnceV1",
        ),
        "header",
    )
    require_tokens(
        source,
        tuple(f'{{"{key}",' for key in EXPECTED_KEYS)
        + (
            "constexpr std::array<AllowlistedInteraction, 11>",
            "payload.religious_option_selected",
            "preview.costs.raw[index] >",
            "!SameEnvelope(first, second)",
            "access.submit_once(access.context, request, second)",
            "AckStatus::submitted_verification_pending",
            "AppliedPostcondition(ack, post)",
            "post.matching_pending_proposal",
            "interaction_specific_postcondition_failed",
        ),
        "source",
    )
    require_tokens(
        test,
        (
            "TestAllElevenAllowlistedReceipts",
            "TestPreviewAndAllowlistGates",
            "TestCanSendAcceptanceAndBudgetGates",
            "TestEnvironmentAndSubmitSeamGates",
            "TestDoubleCaptureAndSingleSubmit",
            "TestAckRemainsPendingUntilSpecificReadback",
            "fixture.captures == 2 && fixture.submits == 1",
            "state.acknowledged_submission_count == 1",
        ),
        "native test",
    )

    cmake_text = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for path in native_root.rglob("CMakeLists.txt")
    )
    bridge_text = (native_root / "src/bridge.cpp").read_text(
        encoding="utf-8", errors="replace"
    )
    require(
        "character_interaction_proposal_action_core_v1" not in cmake_text,
        "private core was added to shared CMake",
    )
    require(
        "character_interaction_proposal_action_core_v1" not in bridge_text,
        "private core was registered in shared bridge",
    )
    print("character_interaction_proposal_action_core_v1 contract: GREEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
