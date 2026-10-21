"""Exact source pairs for public background supervisor refusal closures."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypedDict

from ck3_mod_acceptance_background_types import FilePin, file_pin, json_object

LauncherProtocolVersionV1 = Literal["background-offline-v1", "background-keyed-pins-v2"]
LauncherProtocolSchemaV1 = Literal["ck3-mod-acceptance-launcher-source-protocol-v1"]


class LauncherProtocolV1(TypedDict):
    schema: LauncherProtocolSchemaV1
    version: LauncherProtocolVersionV1


@dataclass(frozen=True)
class LauncherSourcePairV1:
    version: LauncherProtocolVersionV1
    launcher_bytes: int
    launcher_sha256: str
    gate_bytes: int
    gate_sha256: str


LEGACY_CLOSURE_SCHEMA_V1 = "ck3-mod-acceptance-background-supervisor-refused-closure-v1"
CURRENT_CLOSURE_SCHEMA_V1 = "ck3-mod-acceptance-background-supervisor-refused-closure-v2"
BACKGROUND_CLOSURE_SCHEMAS_V1 = (LEGACY_CLOSURE_SCHEMA_V1, CURRENT_CLOSURE_SCHEMA_V1)
LAUNCHER_PROTOCOL_SCHEMA_V1: LauncherProtocolSchemaV1 = "ck3-mod-acceptance-launcher-source-protocol-v1"

# These names preserve the historical reviewed pair, independent of current source.
GATE_PROTOCOL_SHA256 = "a17c9cea468c3700925ec651cd9881596c642edbe3725c642842001d07332274"
LAUNCHER_PROTOCOL_SHA256 = "e223c5efea10a51618a676ef991485540a2856f32f159a3ed8f2f82a7e749b24"
LEGACY_BACKGROUND_PROTOCOL_V1 = LauncherSourcePairV1(
    "background-offline-v1", 16572, LAUNCHER_PROTOCOL_SHA256, 6023, GATE_PROTOCOL_SHA256)
CURRENT_BACKGROUND_PROTOCOL_V1 = LauncherSourcePairV1(
    "background-keyed-pins-v2", 16552, "5ab63dbc61a45df968c2a556a5624ff429845acdadd49c174f8b415f7f125187", 6023, "a17c9cea468c3700925ec651cd9881596c642edbe3725c642842001d07332274")
# Reviewed public fresh-machine bootstrap source; protocol fields remain keyed v2.
FRESH_MACHINE_BOOTSTRAP_PROTOCOL_V1 = LauncherSourcePairV1(
    "background-keyed-pins-v2", 17182,
    "e9df84ebc0e31fa65fcb82210efdd4f39d28976c82b4f7def517a7968eb773ce",
    6023, "a17c9cea468c3700925ec651cd9881596c642edbe3725c642842001d07332274")
# Reviewed launcher using the shared producer/consumer sibling module registry.
# Earlier identities above remain valid historical pairs with their original bytes.
SIBLING_QUEUE_SOURCE_PROTOCOL_V1 = LauncherSourcePairV1(
    "background-keyed-pins-v2", 16864,
    "9ebb997e5496d430fa018348b65f6fe3eb59949bfe00e623482aeba58a9f55df",
    6023, "a17c9cea468c3700925ec651cd9881596c642edbe3725c642842001d07332274")
LAUNCHER_PROTOCOL_REGISTRY_V1 = (
    LEGACY_BACKGROUND_PROTOCOL_V1, CURRENT_BACKGROUND_PROTOCOL_V1,
    FRESH_MACHINE_BOOTSTRAP_PROTOCOL_V1,
    SIBLING_QUEUE_SOURCE_PROTOCOL_V1,
)


def _source_pin(value: object) -> FilePin:
    row = json_object(value)
    if set(row) != {"path", "bytes", "sha256"}:
        raise ValueError("Exact launcher protocol source pin fields required")
    return file_pin(row)


def _source_pair(launcher_source: object, gate_source: object) -> LauncherSourcePairV1:
    launcher, gate = _source_pin(launcher_source), _source_pin(gate_source)
    for pair in LAUNCHER_PROTOCOL_REGISTRY_V1:
        if (launcher["bytes"] == pair.launcher_bytes
                and launcher["sha256"] == pair.launcher_sha256
                and gate["bytes"] == pair.gate_bytes
                and gate["sha256"] == pair.gate_sha256):
            return pair
    raise ValueError("Unknown or crossed launcher/gate protocol source pair")


def build_launcher_protocol_v1(launcher_source: object, gate_source: object) -> LauncherProtocolV1:
    pair = _source_pair(launcher_source, gate_source)
    return LauncherProtocolV1(schema=LAUNCHER_PROTOCOL_SCHEMA_V1, version=pair.version)


def verify_closure_protocol_v1(bundle: object) -> LauncherProtocolV1:
    row = json_object(bundle)
    protocol = build_launcher_protocol_v1(row.get("launcher_source"), row.get("steam_gate_source"))
    schema = row.get("schema")
    if schema == LEGACY_CLOSURE_SCHEMA_V1:
        if "launcher_protocol" in row or protocol["version"] != "background-offline-v1":
            raise ValueError("Legacy closure requires its original source pair and absent launcher_protocol")
        return protocol
    if schema != CURRENT_CLOSURE_SCHEMA_V1:
        raise ValueError("Unknown background refusal closure schema")
    descriptor = json_object(row.get("launcher_protocol"))
    if (set(descriptor) != {"schema", "version"}
            or descriptor.get("schema") != LAUNCHER_PROTOCOL_SCHEMA_V1
            or descriptor.get("version") != protocol["version"]):
        raise ValueError("Closure launcher_protocol must exactly describe its source pair")
    return protocol
