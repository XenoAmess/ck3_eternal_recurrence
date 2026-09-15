#!/usr/bin/env python3
"""Verify the Council23 shared application-main source and ABI boundary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


class VerificationError(RuntimeError):
    pass


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def require_token(source: str, token: str, label: str) -> None:
    if token not in source:
        raise VerificationError(f"{label} missing token: {token}")


def verify(arguments: argparse.Namespace) -> dict[str, object]:
    manifest = json.loads(arguments.manifest.read_text(encoding="utf-8"))
    if manifest.get("contract") != "council_application_main_v1_source_contract":
        raise VerificationError("manifest contract mismatch")
    if manifest.get("advertised_by_default") is not False:
        raise VerificationError("Council runtime must remain unadvertised by default")

    header = read(arguments.header)
    implementation = read(arguments.implementation)
    bridge = read(arguments.bridge)
    mailbox_header = read(arguments.mailbox_header)
    mailbox_source = read(arguments.mailbox_source)
    action_header = read(arguments.action_header)

    for key in ("envelope_schema", "query_step", "action_step", "receipt_step"):
        require_token(header, str(manifest[key]), "Council application-main header")
    require_token(
        header,
        "kCouncilApplicationMainAdvertisedByDefaultV1 = false",
        "Council application-main header",
    )

    cursor = -1
    for token in manifest["application_main_sequence"]:
        next_cursor = implementation.find(token, cursor + 1)
        if next_cursor < 0:
            raise VerificationError(f"application-main sequence missing: {token}")
        if next_cursor <= cursor:
            raise VerificationError(f"application-main sequence out of order: {token}")
        cursor = next_cursor

    for token in manifest["action_recheck_gates"]:
        require_token(action_header, token, "Council22 semantic action contract")
    for token in manifest["wire_payload_keys"]:
        require_token(implementation, f'\\"{token}\\"', "Council wire serializer")

    slot = str(manifest["mailbox_slot"])
    require_token(mailbox_header, slot, "mailbox typed registry")
    require_token(mailbox_source, slot, "mailbox typed admission")
    require_token(bridge, slot, "bridge mailbox installation")
    require_token(bridge, "ExecuteCouncilApplicationMainV1", "bridge mailbox installation")
    if "SerializeCouncilApplicationMainResultEnvelopeV1" in bridge:
        raise VerificationError("Council runtime was registered on the worker bridge")
    if str(manifest["query_step"]) in bridge or str(manifest["action_step"]) in bridge:
        raise VerificationError("Council worker capability was advertised before real bindings")

    for token in (
        "kCouncilAssignCouncillorSendInteractionHelperRvaV1 = 0x1056C00",
        "kCouncilAssignCouncillorConfirmationCanConfirmRvaV1 = 0x105C770",
        "queue_acceptance_observed = false",
        "verification_pending = true",
    ):
        source = action_header if "RvaV1" in token else read(arguments.action_source)
        require_token(source, token, "Council22 ABI/ACK contract")

    return {
        "status": "GREEN",
        "contract": manifest["contract"],
        "game_version": manifest["game_version"],
        "executable_sha256": manifest["executable_sha256"],
        "application_main_steps_verified": len(manifest["application_main_sequence"]),
        "action_gates_verified": len(manifest["action_recheck_gates"]),
        "wire_keys_verified": len(manifest["wire_payload_keys"]),
        "advertised": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--header", required=True, type=Path)
    parser.add_argument("--implementation", required=True, type=Path)
    parser.add_argument("--bridge", required=True, type=Path)
    parser.add_argument("--mailbox-header", required=True, type=Path)
    parser.add_argument("--mailbox-source", required=True, type=Path)
    parser.add_argument("--action-header", required=True, type=Path)
    parser.add_argument("--action-source", required=True, type=Path)
    arguments = parser.parse_args()
    try:
        result = verify(arguments)
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError,
            VerificationError) as error:
        print(json.dumps({"status": "RED", "reason": str(error)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
