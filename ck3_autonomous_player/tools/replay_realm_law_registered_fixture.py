"""Replay Root-produced whole-service packets through the registered MCP tool.

This script is authored, not executed, by the realm-law Python child. The Root
owns DLL builds, native fixture production and this optional MCP SDK run.
It never opens a native pipe, starts CK3 or constructs a response envelope.
"""

from __future__ import annotations

import argparse
import asyncio
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys


TOOL = "ck3_query_realm_law_final_terms_private_v1"
STEP = "query-realm-law-final-terms-v1-private"
PACKETS = ("hello.json", "initial-state.json", "response.json", "final-state.json")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def load_object(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    require(isinstance(value, dict), f"JSON object required: {path}")
    return value


def load_bundle(directory: Path) -> dict[str, object]:
    receipt_path = directory / "producer-receipt.json"
    receipt = load_object(receipt_path)
    # A receipt is an input provenance declaration, not independent proof of
    # production execution. Root keeps its actual build/fixture log alongside it.
    require(receipt.get("status") == "GREEN", "Root producer receipt must be GREEN")
    require(receipt.get("packet_source") == "root-production-chain",
            "focused DTO/serializer output is not a whole-service packet source")
    require(receipt.get("production_entry") == "HandleNonwarPrivate12002",
            "expected existing central private route")
    require(receipt.get("query_step") == STEP, "producer step differs from registered query")
    packets = {name: load_object(directory / name) for name in PACKETS}
    for name, frame_type in zip(PACKETS, (
            "hello", "state_snapshot", "command_result", "state_snapshot"), strict=True):
        require(packets[name].get("type") == frame_type, f"wrong raw packet type in {name}")
        require(packets[name].get("protocol_version") == 1, f"wrong protocol in {name}")
    response = packets["response.json"]
    require(isinstance(response.get("request_id"), str) and bool(response["request_id"]),
            "producer response must retain a native request ID")
    require(response.get("ok") is True, "positive bundle must contain a successful native response")
    envelope = response.get("result")
    require(isinstance(envelope, dict) and envelope.get("step") == STEP,
            "positive bundle lacks the production result envelope")
    require(isinstance(envelope.get("realm_law_final_terms"), dict),
            "positive bundle lacks its native realm-law DTO")
    return {"directory": str(directory), "receipt_path": str(receipt_path),
            "receipt": receipt, "packets": packets}


def load_candidate_transport(candidate: Path | None) -> None:
    if candidate is None:
        return
    name = "xar_autoplayer.bridge.realm_law_paused_private_transport"
    spec = importlib.util.spec_from_file_location(name, candidate)
    require(spec is not None and spec.loader is not None, "candidate transport cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)


async def replay(args: argparse.Namespace) -> dict[str, object]:
    sys.path.insert(0, str(args.source_root / "ck3_autonomous_player" / "src"))
    from xar_autoplayer.bridge.mcp_server import create_server
    from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, NativeProtocolState

    load_candidate_transport(args.candidate_transport)
    from mcp import Client

    bundles = [load_bundle(path) for path in args.bundle]

    class PacketReplayDriver:
        # These are real unbound production methods; no private-query mirror.
        query_realm_law_final_terms_private_v1 = (
            NativeHeadlessGameplayDriver.query_realm_law_final_terms_private_v1
        )
        command_timeout_seconds = 30.0

        def __init__(self, enabled: bool) -> None:
            self.allow_private_realm_law_paused_query = enabled
            self.endpoint = self
            self.sent: list[dict[str, object]] = []
            self.bundle: dict[str, object] | None = None

        def select(self, bundle: dict[str, object], response: dict[str, object] | None = None) -> None:
            self.bundle = bundle
            self.packets = deepcopy(bundle["packets"])
            if response is not None:
                self.packets["response.json"] = deepcopy(response)
            self.state = NativeProtocolState("offline-root-realm-law-production-packets")
            require(self.state.ingest(self.packets["hello.json"]) == "hello", "hello ingest failed")
            require(self.state.ingest(self.packets["initial-state.json"]) == "state_snapshot",
                    "initial native packet was rejected")
            self.sent = []
            self.final_ingest: str | None = None

        def take_snapshot(self) -> dict[str, object]:
            return self.state.semantic_snapshot()

        def send(self, request: dict[str, object]) -> None:
            self.sent.append(deepcopy(request))
            require(len(self.sent) == 1, "read unexpectedly issued more than one native command")
            require(set(request) == {
                "type", "protocol_version", "request_id", "step", "expected_revision",
            }, "query changed its existing request shape")
            require(request["type"] == "execute_step" and request["protocol_version"] == 1,
                    "query did not use the existing native execute_step protocol")
            require(request["step"] == STEP, "query dispatched another step")
            require(request["expected_revision"] == self.packets["initial-state.json"]["revision"],
                    "query did not bind its native revision")
            response = deepcopy(self.packets["response.json"])
            # The only replay adaptation is request correlation. Envelope,
            # native DTO and post-state remain the producer's raw packets.
            response["request_id"] = request["request_id"]
            require(self.state.ingest(response) == "command_result", "response ingest failed")
            self.final_ingest = self.state.ingest(self.packets["final-state.json"])

    disabled = PacketReplayDriver(False)
    disabled.select(bundles[0])
    async with Client(create_server(disabled)) as client:
        names = {tool.name for tool in (await client.list_tools()).tools}
        require(TOOL not in names, "private query was registered with its enable flag false")
    require(disabled.sent == [], "default-off service emitted a native command")

    driver = PacketReplayDriver(True)
    driver.select(bundles[0])
    records: list[dict[str, object]] = []
    negative_records: list[dict[str, object]] = []
    async with Client(create_server(driver)) as client:
        tools = {tool.name: tool for tool in (await client.list_tools()).tools}
        require(TOOL in tools, "existing enabled private query was not registered")
        require(tools[TOOL].annotations is not None
                and tools[TOOL].annotations.read_only_hint is True,
                "registered private query lacks its real read-only annotation")
        for bundle in bundles:
            driver.select(bundle)
            before = driver.take_snapshot()
            result = await client.call_tool(TOOL, {"expected_revision": before["revision"]})
            require(result.is_error is False, f"registered replay failed: {result.content}")
            actual = result.structured_content
            native = bundle["packets"]["response.json"]["result"]["realm_law_final_terms"]
            require(isinstance(actual, dict), "registered result lacks structured content")
            require({key: actual.get(key) for key in native} == native,
                    "registered result changed or dropped native DTO fields")
            hello = bundle["packets"]["hello.json"]
            require(actual.get("exact_ck3_build") == hello["expected_ck3_version"],
                    "result lost the exact native build")
            if hello["expected_ck3_version"] != "1.19.0.6":
                require(actual.get("exe_sha256") == hello["expected_ck3_sha256"],
                        "result lost its hello-pinned executable identity")
            require(actual.get("queried_revision") == before["revision"]
                    and actual.get("queried_native_revision") == before["native_revision"]
                    and actual.get("queried_snapshot_id") == before["snapshot_id"],
                    "registered query lost its source frame")
            require(driver.final_ingest == "state_snapshot", "post packet was rejected")
            require(driver.state._command_results == {}, "query did not consume its command result")
            require(len(driver.sent) == 1, "registered replay did not emit exactly one query")
            records.append({
                "bundle": bundle["directory"], "producer_receipt": bundle["receipt_path"],
                "exact_ck3_build": actual["exact_ck3_build"],
                "queried_native_revision": actual["queried_native_revision"],
                "native_row_counts": [len(group["candidates"]) for group in native["groups"]],
                "profile_statuses": [row.get("succession_profile_status")
                                     for row in native["groups"][1]["candidates"]],
                "native_commands": len(driver.sent),
            })

        if args.validator_negatives:
            source = next((bundle for bundle in bundles
                           if bundle["packets"]["hello.json"].get("expected_ck3_version")
                           in {"1.20.0.3", "1.20.0.4"}
                           and any(row.get("succession_profile_status") == "available"
                                   for row in bundle["packets"]["response.json"]["result"]
                                   ["realm_law_final_terms"]["groups"][1]["candidates"])), None)
            require(source is not None, "validator negatives need one .3/.4 native available profile")
            base_response = source["packets"]["response.json"]
            row_index = next(index for index, row in enumerate(
                base_response["result"]["realm_law_final_terms"]["groups"][1]["candidates"]
            ) if row["succession_profile_status"] == "available")
            # All negative cases are explicitly local validator perturbations,
            # not new native/source or whole-service producer evidence.
            mutations = (
                ("boolean-as-integer", "profile", "create_primary_tier_titles", 1),
                ("boolean-as-share", "profile", "primary_heir_minimum_share_raw", True),
                ("share-outside-int64", "profile", "primary_heir_minimum_share_raw", 1 << 63),
                ("wrong-share-scale", "profile", "primary_heir_minimum_share_scale", 1000),
                ("unknown-selector", "profile", "division", "confederate_partition"),
                ("available-null-profile", "row", "succession_profile", None),
                ("absent-with-profile", "row", "succession_profile_status", "absent"),
                ("unknown-profile-status", "row", "succession_profile_status", "guessed"),
            )
            for label, owner, key, value in mutations:
                response = deepcopy(base_response)
                row = response["result"]["realm_law_final_terms"]["groups"][1]["candidates"][row_index]
                destination = row["succession_profile"] if owner == "profile" else row
                destination[key] = value
                driver.select(source, response)
                before = driver.take_snapshot()
                result = await client.call_tool(TOOL, {"expected_revision": before["revision"]})
                require(result.is_error is True, f"registered tool accepted validator negative: {label}")
                require(len(driver.sent) == 1 and driver.state._command_results == {},
                        f"negative did not use and consume the real command result: {label}")
                negative_records.append({"case": label, "source": "validator-negative",
                                         "rejected_by_registered_tool": True})

    return {
        "status": "GREEN", "boundary": "offline-registered-MCP-protocol-replay",
        "whole_service_packet_source": "root-production-chain",
        "source_root": str(args.source_root),
        "candidate_transport": str(args.candidate_transport) if args.candidate_transport else None,
        "default_off_registration_verified": True,
        "positive_replays": records, "validator_negatives": negative_records,
        "live_verified": False, "ck3_touched": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--candidate-transport", type=Path)
    parser.add_argument("--bundle", type=Path, action="append", required=True)
    parser.add_argument("--validator-negatives", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = asyncio.run(replay(args))
        exit_code = 0
    except Exception as error:
        report = {"status": "RED", "boundary": "offline-registered-MCP-protocol-replay",
                  "error_type": type(error).__name__, "error": str(error),
                  "live_verified": False, "ck3_touched": False}
        exit_code = 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
