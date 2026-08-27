#!/usr/bin/env python3
"""Verify pinned CK3 event-window-context byte spans without starting CK3."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

from scan_anchors import PeImage


HERE = Path(__file__).resolve().parent
DEFAULT_CONTRACT = HERE / "event_window_context_1_19_0_6_abi.json"
DEFAULT_EXE = HERE.parents[2] / "Crusader Kings III" / "binaries" / "ck3.exe"
DEFAULT_READER = HERE.parent / "src" / "event_window_context_v1.cpp"
DEFAULT_MAILBOX = HERE.parent / "src" / "event_window_context_v1_mailbox.cpp"
DEFAULT_SERIALIZER = HERE.parent / "src" / "event_window_context_v1_serializer.cpp"
DEFAULT_BINDINGS = HERE.parent / "src" / "ck3_11906.cpp"
DEFAULT_BRIDGE = HERE.parent / "src" / "bridge.cpp"
DEFAULT_EVENT_HEADER = (
    HERE.parent / "include" / "xar_bridge" / "event_window_context_v1.hpp"
)
DEFAULT_WIRE_CONTRACT = (
    HERE.parents[1]
    / "src"
    / "xar_autoplayer"
    / "bridge"
    / "event_window_context_contract.py"
)


def integer(value: object) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value, 0)
    raise TypeError(f"expected integer or integer string, found {value!r}")


def signed_int32(value: object) -> bool:
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and -(2**31) <= value < 2**31
    )


def runtime_function_ranges(data: bytes, image: PeImage) -> set[tuple[int, int]]:
    pe_offset = struct.unpack_from("<I", data, 0x3C)[0]
    optional = pe_offset + 24
    if struct.unpack_from("<H", data, optional)[0] != 0x20B:
        raise ValueError("expected PE32+ optional header")
    exception_rva, exception_size = struct.unpack_from(
        "<II", data, optional + 112 + 3 * 8
    )
    if exception_size % 12:
        raise ValueError("malformed AMD64 exception directory")
    offset = image.rva_to_offset(exception_rva)
    return {
        struct.unpack_from("<II", data, offset + delta)
        for delta in range(0, exception_size, 12)
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, default=DEFAULT_EXE)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--reader", type=Path, default=DEFAULT_READER)
    parser.add_argument("--mailbox", type=Path, default=DEFAULT_MAILBOX)
    parser.add_argument("--serializer", type=Path, default=DEFAULT_SERIALIZER)
    parser.add_argument("--bindings", type=Path, default=DEFAULT_BINDINGS)
    parser.add_argument("--bridge", type=Path, default=DEFAULT_BRIDGE)
    parser.add_argument("--event-header", type=Path, default=DEFAULT_EVENT_HEADER)
    parser.add_argument(
        "--wire-contract", type=Path, default=DEFAULT_WIRE_CONTRACT
    )
    arguments = parser.parse_args()

    executable = arguments.exe.resolve()
    contract_path = arguments.contract.resolve()
    data = executable.read_bytes()
    image = PeImage(data)
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    failures: list[str] = []

    executable_sha = hashlib.sha256(data).hexdigest().upper()
    expected_executable_sha = contract["executable_sha256"].upper()
    if executable_sha != expected_executable_sha:
        failures.append(
            "executable SHA mismatch: "
            f"expected {expected_executable_sha}, found {executable_sha}"
        )

    pdata_ranges = runtime_function_ranges(data, image)
    source_contract = contract["source_contract"]
    function_spans = source_contract["exact_function_spans"]
    for span in function_spans:
        declared_regions = span.get("runtime_function_regions")
        if declared_regions:
            regions = []
            for region in declared_regions:
                start_text, end_text = region.split("..", maxsplit=1)
                regions.append((integer(start_text), integer(end_text)))
        else:
            regions = [(integer(span["start_rva"]), integer(span["end_rva"]))]
        for begin, end in regions:
            if (begin, end) not in pdata_ranges:
                failures.append(
                    f"{span['name']}: 0x{begin:X}..0x{end:X} "
                    "is not an exact .pdata runtime-function extent"
                )

        start = integer(span["start_rva"])
        end = integer(span["end_rva"])
        expected_length = integer(span["byte_length"])
        actual_length = end - start
        if actual_length != expected_length:
            failures.append(
                f"{span['name']}: declared length 0x{expected_length:X}, "
                f"RVA range length 0x{actual_length:X}"
            )
            continue
        offset = image.rva_to_offset(start)
        blob = data[offset : offset + actual_length]
        if len(blob) != actual_length:
            failures.append(f"{span['name']}: range is not fully file-backed")
            continue
        actual_sha = hashlib.sha256(blob).hexdigest().upper()
        expected_sha = span["sha256"].upper()
        if actual_sha != expected_sha:
            failures.append(
                f"{span['name']}: expected {expected_sha}, found {actual_sha}"
            )
            continue
        print(
            f"OK {span['name']} RVA=0x{start:X}..0x{end:X} "
            f"bytes=0x{actual_length:X} SHA256={actual_sha}"
        )

    additional_spans = [
        *source_contract.get("exact_semantic_spans", []),
        *source_contract.get("exact_data_spans", []),
    ]
    for span in additional_spans:
        start = integer(span["start_rva"])
        end = integer(span["end_rva"])
        expected_length = integer(span["byte_length"])
        actual_length = end - start
        if actual_length != expected_length:
            failures.append(
                f"{span['name']}: declared length 0x{expected_length:X}, "
                f"RVA range length 0x{actual_length:X}"
            )
            continue
        offset = image.rva_to_offset(start)
        blob = data[offset : offset + actual_length]
        if len(blob) != actual_length:
            failures.append(f"{span['name']}: range is not fully file-backed")
            continue
        actual_sha = hashlib.sha256(blob).hexdigest().upper()
        expected_sha = span["sha256"].upper()
        if actual_sha != expected_sha:
            failures.append(
                f"{span['name']}: expected {expected_sha}, found {actual_sha}"
            )
            continue
        print(
            f"OK {span['name']} RVA=0x{start:X}..0x{end:X} "
            f"bytes=0x{actual_length:X} SHA256={actual_sha}"
        )

    expected_scope_spans = {
        "ActiveEvent_default_constructor": (
            0x2707F60,
            0x2707FD8,
            "387C833D2D134CFC89CA6258F4F158B4B3A6372D28799F502B71B32D92B51331",
        ),
        "ActiveEvent_copy_or_relocation_path": (
            0x2707E50,
            0x2707F55,
            "4A541021F8227E03006D1699D15DA0769B0D28763D503CF2BAD92EF2B80E594A",
        ),
        "ActiveEvent_serializer": (
            0x2350640,
            0x235082B,
            "0B7910443CA157A79B16A885782C6A69FAC80A471288F869FF3A7ADEFD23AC4A",
        ),
        "EventTargetScope_constructor": (
            0x81F190,
            0x81F24A,
            "E119B49AA2F41C1E491435E90877DEB8F0DF42906226AAC2977F51A561443FA7",
        ),
        "EventTargetScope_copy_constructor_path": (
            0x3358EF0,
            0x3358FC9,
            "3F3D5AAACCAC5C72C0C9A194E3B39F4CC0B38350DA8AF8F029B6C2F61C51A0E3",
        ),
        "EventTargetScope_copy_assignment_path": (
            0x3359030,
            0x33590CE,
            "4E82B1166529FE5376859DEBD00D0166700255BC87A7F531B4C6EE97A1C4D4C9",
        ),
        "EventTargetScope_serializer": (
            0x20D8330,
            0x20D84C0,
            "3A36FF4554A2B6BA2B9E02DA5252C8F0C6E5231F4F92A8CBA5932E3AFE65A428",
        ),
        "EventTargetScope_named_vector_serializer_wrapper": (
            0x2539DA0,
            0x2539DF8,
            "985F396569F9FEEDCCC8DCD85A15FB36A834156E48354F3AB69E1BEBE90B777E",
        ),
        "EventTargetScope_named_row_serializer": (
            0x253BD00,
            0x253BE92,
            "8E407B2889993C0DDBC994EA40905FF221A168D62BF57A273C56EAF352EACA39",
        ),
        "EventTargetScope_named_vector_copy": (
            0x335A370,
            0x335A4EE,
            "5D8570E0C3268732AC8A1A666D4C800DB39DD305E498AE9B1297160B11572613",
        ),
        "generic_event_target_serializer": (
            0x81D880,
            0x81DA06,
            "B267CA32133ED15FE47468572C4B561E2A121B280BBEF8D653F56E4158CD1E6D",
        ),
        "generic_event_target_type_registry_getter": (
            0x33C52B0,
            0x33C535B,
            "8B7E4C67B9E772BBB75F303D7EE2444DBBF261D412FD0DCC97C99FC0C7297507",
        ),
        "generic_event_target_type_name_consumer": (
            0x2011400,
            0x2011623,
            "55AC17937B11658E17C4884A9FD027FFA32BCD3B04EBC16B9D98F24BD9ECB02B",
        ),
        "generic_event_target_type_name_resolver": (
            0x3B58970,
            0x3B58A94,
            "54E7EAF6CE4CEDBD229DA3D63C69C8691E9291EECE17F07AE1F1C75C2DA9FAB4",
        ),
        "script_identifier_table_getter": (
            0x3B971A0,
            0x3B97273,
            "A8A82597116A8C4E4A77A143AD3A581B12E6678F5E8E6839D02F234AB260329C",
        ),
        "script_identifier_lookup_only": (
            0x3B97020,
            0x3B9708D,
            "5AD84C93E642050B4397F1DF278A8163C0AEB41E187A648D6FB7EA39A38C55FE",
        ),
        "script_identifier_id_to_entry": (
            0x3B97090,
            0x3B9719F,
            "723937CA06967EDF2A3757AD5EE8C3453C3E13E10A97F9135847C85BA8944A11",
        ),
        "generic_event_target_object_resolver": (
            0x33299E0,
            0x3329A37,
            "CDC09A1F335F7F80C8966325B1B7B3A07AACCD0FF36048BBD7D8F34ABD2D1036",
        ),
        "character_event_target_object_resolver": (
            0x201AD30,
            0x201ADB2,
            "092646A8272A7E2926D3865A6AF301AAEEC8A004932F1BF60AE6EA40C9DC19E7",
        ),
    }
    scope_span_rows: dict[str, dict[str, object]] = {}
    for span in function_spans:
        name = span["name"]
        if name in expected_scope_spans:
            if name in scope_span_rows:
                failures.append(f"contract: duplicate scope span {name}")
            scope_span_rows[name] = span
    for name, (expected_start, expected_end, expected_sha) in (
        expected_scope_spans.items()
    ):
        span = scope_span_rows.get(name)
        if span is None:
            failures.append(f"contract: missing scope span {name}")
            continue
        if (
            integer(span["start_rva"]) != expected_start
            or integer(span["end_rva"]) != expected_end
            or span["sha256"].upper() != expected_sha
        ):
            failures.append(f"contract: scope span {name} drifted")

    active_scope = contract.get("ActiveEventScope", {})
    root_scope = active_scope.get("root_generic_target", {})
    named_scope = active_scope.get("named_target_vector", {})
    named_identity = active_scope.get("named_key_identity", {})
    type_identity = active_scope.get("generic_type_identity", {})
    character_identity = active_scope.get("character_payload_identity", {})
    production_scope_wire = active_scope.get("production_wire", {})
    if not (
        active_scope.get("evidence_status")
        == "static-confirmed-production-wire-not-live"
        and "ActiveEvent+0x00" in active_scope.get("embedding", "")
        and "0x168-byte EventTargetScope" in active_scope.get("embedding", "")
        and root_scope.get("type_index")
        == "+0x00 uint16 generic type-registry index; zero is absent"
        and root_scope.get("payload")
        == (
            "+0x08 type-specific 8-byte payload; never publish it as a "
            "pointer or universal component ID"
        )
        and named_scope.get("header")
        == (
            "EventTargetScope+0x18 data pointer, +0x20 int32 capacity, "
            "+0x24 signed int32 count, +0x28 allocator pointer"
        )
        and named_scope.get("row_stride") == "0x18"
        and named_scope.get("row_name_identifier")
        == (
            "+0x00 full signed int32 generation-bearing script-identifier "
            "ID; preserve the complete value including negative IDs; +0x04 "
            "remains opaque and is not published"
        )
        and named_scope.get("row_target")
        == "+0x08 inline 0x10-byte generic event-target token"
        and named_identity.get("table_getter_rva") == "0x3B971A0"
        and named_identity.get("lookup_only_rva") == "0x3B97020"
        and named_identity.get("id_to_entry_rva") == "0x3B97090"
        and named_identity.get("id_to_entry_signature")
        == (
            "const std::string* (void* script_identifier_table, "
            "int32 identifier)"
        )
        and "table+0x3C" in named_identity.get("id_to_entry_layout", "")
        and "index*0x20" in named_identity.get("id_to_entry_layout", "")
        and named_identity.get("id_to_entry_fallback")
        == "module+0x585F218; reject before copying"
        and "complete signed int32 generation ID"
        in named_identity.get("read_rule", "")
        and "exact full-ID/string round-trip"
        in named_identity.get("read_rule", "")
        and type_identity.get("registry_getter_rva") == "0x33C52B0"
        and type_identity.get("registry_address") == "module+0x4FFE290"
        and type_identity.get("registry_layout")
        == (
            "+0x00 data pointer, +0x0C signed int32 count, entry stride "
            "0x50"
        )
        and type_identity.get("stable_name_identifier")
        == "entry+0x00 int32 identifier"
        and type_identity.get("stable_name_resolver_rva") == "0x3B58970"
        and type_identity.get("registry_fallback_entry_rva") == "0x5000AB0"
        and "type_index >= count"
        in type_identity.get("registry_fallback_entry_role", "")
        and "never enter it"
        in type_identity.get("registry_fallback_entry_role", "")
        and type_identity.get("resolver_name_fallback_rva") == "0x585F058"
        and type_identity.get("binding_expected_pointer")
        == (
            "Bindings::generic_value_type_name_fallback = "
            "module+0x585F058"
        )
        and type_identity.get("resolver_fallback_rejection")
        == (
            "Reject native_name == "
            "bindings.generic_value_type_name_fallback before copying or "
            "publishing the type key"
        )
        and "module+0x5000AB0 registry fallback row"
        in type_identity.get("read_rule", "")
        and "kGenericValueTypeNameFallbackRva = 0x585F058"
        in type_identity.get("read_rule", "")
        and "distinct fallbacks and must never be aliased"
        in type_identity.get("read_rule", "")
        and character_identity.get("status")
        == "static-confirmed-only-not-current-event-live"
        and character_identity.get("type_index") == 4
        and character_identity.get("payload")
        == "+0x08 zero-extended full-generation int32 CharacterID"
        and active_scope.get("noncharacter_payload_identity", "").startswith(
            "Production wire publishes"
        )
        and production_scope_wire.get("status")
        == "implemented-static-not-live"
        and production_scope_wire.get("static_ready") is True
        and production_scope_wire.get("live_ready") is False
        and production_scope_wire.get("query")
        == "game.command.query-current-event-window-context-v1"
        and production_scope_wire.get("root_scope_fields")
        == [
            "status",
            "raw_type_index",
            "type_key",
            "subtype",
            "typed_identity",
        ]
        and production_scope_wire.get("saved_scope_fields")
        == ["name", "name_identifier", "scope"]
        and production_scope_wire.get("name_identifier_wire")
        == {
            "type": "full signed int32 generation ID",
            "minimum": -(2**31),
            "maximum": 2**31 - 1,
            "round_trip": (
                "preserve and compare the complete signed value, including "
                "negative generation-bearing IDs; process-local only"
            ),
        }
        and production_scope_wire.get("character_typed_identity_fields")
        == ["status", "kind", "character_id"]
        and production_scope_wire.get("noncharacter_typed_identity_fields")
        == ["status", "reason"]
        and production_scope_wire.get("noncharacter_reason")
        == "generic_scope_payload_identity_not_closed"
        and production_scope_wire.get("readiness")
        == {
            "root_scope_ready": True,
            "saved_scopes_ready": True,
            "effect_preview_ready": False,
            "semantic_decision_ready": False,
        }
        and production_scope_wire.get("process_local_only")
        == ["saved_scopes[].name_identifier"]
        and production_scope_wire.get("forbidden_fields")
        == ["raw_16_bytes_hex", "raw_payload", "engine_pointer"]
        and active_scope.get("live_validation")
        == (
            "not performed; no paused current-event root or named-scope "
            "artifact exists"
        )
        and active_scope.get("semantic_decision_ready") is False
    ):
        failures.append("contract: ActiveEvent scope static/wire ABI drifted")

    source_contracts = {
        "reader": (
            arguments.reader,
            (
                "bindings.jomini_state_slot",
                "bindings.game_state_slot",
                "bindings.event_manager_offset == 0",
                "bindings.get_current_event",
                "kActiveEventDataOffset",
                "kEventDataCalculatedIdOffset",
                "kEventDataRuntimeStatsOrdinalOffset",
                "kEventDataDefinitionKeyOffset",
                "kEventDataAuthoredOptionDataOffset",
                "kEventDataAuthoredOptionCapacityOffset",
                "kEventDataAuthoredOptionCountOffset",
                "kEventScopeRootOffset = 0x00",
                "kEventScopeNamedDataOffset = 0x18",
                "kEventScopeNamedCapacityOffset = 0x20",
                "kEventScopeNamedCountOffset = 0x24",
                "kEventScopeNamedRowStride = 0x18",
                "kEventScopeNamedRowIdentifierOffset = 0x00",
                "kEventScopeNamedRowTokenOffset = 0x08",
                "kEventScopeTokenPayloadOffset = 0x08",
                "kGenericValueTypeRegistryEntryStride = 0x50",
                "kCharacterScopeTypeIndex = 4",
                "generic_scope_payload_identity_not_closed",
                "kEventOptionDefinitionIsCancelOffset",
                "kIdlerFromOwnerOffset",
                "bindings.ingame_interface_idler_vtable",
                "kManagerFromIdlerOffset",
                "bindings.event_window_primary_vtable",
                "expected_event_instance_id",
                "before.active_event_instance_id",
                "after != before",
                "kOptionOwnerOffset",
                "kOptionEffectDataOffset",
                "kOptionEffectCapacityOffset",
                "kOptionEffectCountOffset",
                "kEffectIndicatorStride",
                "bindings.trait_database_slot",
                "kTraitNativeIdOffset",
                "kTraitStableKeyOffset",
                "bindings.scheme_type_database_slot",
                "bindings.scheme_type_fallback_slot",
                "bindings.scheme_type_primary_vtable",
                "bindings.hash_stable_key",
                "bindings.hash_stable_key(\n      database",
                "bindings.lookup_scheme_type",
                "kSchemeTypeStableKeyOffset",
                "option.native_option_index >= authored_count",
                "is_cancel > 1",
                "option.cancel = is_cancel != 0",
                "ReadMatchingWindow(bindings, identity_before.event_data",
                "ReadNativeString",
                "identity_after != identity_before",
                "registry != bindings.expected_generic_value_type_registry",
                "bindings.resolve_generic_value_type_name(identifier)",
                "ResolveCharacterScopeIdentity",
                (
                    "raw_payload != "
                    "static_cast<std::uint64_t>(raw_character_id)"
                ),
                (
                    "LoadAt<std::int32_t>(character, kCharacterIdOffset) "
                    "== character_id"
                ),
                "bindings.resolve_script_identifier_name(table, identifier)",
                "native_name == bindings.script_identifier_name_fallback",
                "roundtrip_identifier != identifier",
                "ReadEventScopeInventory(bindings, identity_before.active_event",
                "ReadEventScopeInventory(bindings, identity_after.active_event",
                "scope_after != scope_before",
                "SetUnavailable(output, \"event_scope_changed\")",
                "candidate.root_scope = std::move(scope_before.root_scope)",
                "candidate.saved_scopes = std::move(scope_before.saved_scopes)",
                "candidate.event_definition_identity_ready = true",
                "candidate.root_scope_ready = true",
                "candidate.saved_scopes_ready = true",
                "candidate.effect_indicators_ready = true",
            ),
        ),
        "mailbox": (
            arguments.mailbox,
            (
                "GetCurrentThreadId() != stamp.thread_id",
                "ExecuteEventWindowContextMailboxQueryV1",
                "snapshot != query->expected_snapshot",
                "snapshot.active_event_instance_id",
                "ReadEventWindowContextV1(",
                "event_definition_identity_ready",
                "query->result.root_scope.has_value()",
                "query->result.saved_scopes.empty()",
                "query->result.root_scope_ready",
                "query->result.saved_scopes_ready",
                "effect_indicators_ready",
            ),
        ),
        "serializer": (
            arguments.serializer,
            (
                "played-character-event-icon-indicators-1.19.0.6-v1",
                "indicator_subset_has_no_completeness_signal",
                "resource_deltas",
                "relationship_deltas",
                "AppendScope",
                "ValidSavedScopes",
                "raw_type_index",
                "type_key",
                "subtype",
                "typed_identity",
                "name_identifier",
                "generic_scope_payload_identity_not_closed",
                "root_scope_ready",
                "saved_scopes_ready",
                "effect_indicators_ready",
                "semantic_decision_ready",
            ),
        ),
        "bindings": (
            arguments.bindings,
            (
                "kSchemeTypePrimaryVtableRva = 0x44081E8",
                "kTraitDatabaseSlotRva = 0x570C0F8",
                "kSchemeTypeDatabaseSlotRva = 0x570BD98",
                "kSchemeTypeFallbackSlotRva = 0x570CB58",
                "kHashStableKeyRva = 0x3B8B000",
                "kLookupSchemeTypeRva = 0x0A48C70",
                "kGetGenericValueTypeRegistryRva = 0x33C52B0",
                "kGenericValueTypeRegistryRva = 0x4FFE290",
                "kResolveGenericValueTypeNameRva = 0x3B58970",
                "kGenericValueTypeNameFallbackRva = 0x585F058",
                "kResolveScriptIdentifierNameRva = 0x3B97090",
                "kScriptIdentifierNameFallbackRva = 0x585F218",
                "result.scheme_type_primary_vtable",
                "result.trait_database_slot",
                "result.scheme_type_database_slot",
                "result.scheme_type_fallback_slot",
                "result.hash_stable_key",
                "result.lookup_scheme_type",
                "result.expected_generic_value_type_registry",
                "result.generic_value_type_name_fallback",
                "result.script_identifier_name_fallback",
                "module + kGenericValueTypeNameFallbackRva",
                "result.get_generic_value_type_registry",
                "result.resolve_generic_value_type_name",
                "result.resolve_script_identifier_name",
            ),
        ),
        "event_header": (
            arguments.event_header,
            (
                "struct EventScopeTypedIdentityV1",
                "std::optional<std::int32_t> character_id",
                "struct EventScopeV1",
                "std::uint16_t raw_type_index",
                "std::uint16_t subtype",
                "struct EventSavedScopeV1",
                "std::int32_t name_identifier",
                "std::optional<EventScopeV1> root_scope",
                "std::vector<EventSavedScopeV1> saved_scopes",
                "bool root_scope_ready",
                "bool saved_scopes_ready",
            ),
        ),
        "wire_contract": (
            arguments.wire_contract,
            (
                '"root_scope_ready"',
                '"saved_scopes_ready"',
                '"raw_type_index"',
                '"type_key"',
                '"subtype"',
                '"typed_identity"',
                '"name_identifier"',
                '"generic_scope_payload_identity_not_closed"',
                "_event_scope(frame[\"root_scope\"]",
                "current event saved_scopes must be a bounded list",
                '"root_scope_ready": True',
                '"saved_scopes_ready": True',
                "frame[\"root_scope\"] is not None",
                "frame[\"saved_scopes\"] is not None",
            ),
        ),
        "bridge": (
            arguments.bridge,
            (
                "permitted_executor_duodenary",
                "kEventWindowContextV1Step",
                "ParseEventWindowContextRequestV1",
                "current_snapshot.active_event_instance_id",
                "ExecuteEventWindowContextMailboxQueryV1",
                "EventWindowContextResultFrame",
            ),
        ),
    }
    for name, (path, required_tokens) in source_contracts.items():
        try:
            source = path.resolve().read_text(encoding="utf-8")
        except OSError as error:
            failures.append(f"{name}: cannot read source contract: {error}")
            continue
        for token in required_tokens:
            if token not in source:
                failures.append(f"{name}: missing source-contract token {token!r}")
    reader_source = arguments.reader.resolve().read_text(encoding="utf-8")
    for forbidden in (
        "SubmitSelectEventOption",
        "select_event_option",
        "loaded_effect_executor",
        "0x3380410",
        "construct_effect_preview_collector",
        "traverse_loaded_effect",
        "kDataCancelOptionIndexOffset",
        "option.native_option_index == cancel_index",
        "bindings.resolve_event_target_object",
        "bindings.is_event_target_valid",
    ):
        if forbidden in reader_source:
            failures.append(f"reader: forbidden executor token {forbidden!r}")

    def reader_region(begin: str, end: str) -> str:
        start = reader_source.find(begin)
        stop = reader_source.find(end, start + len(begin))
        return "" if start < 0 or stop < 0 else reader_source[start:stop]

    generic_type_region = reader_region(
        "bool ReadGenericValueTypeKey", "bool ResolveCharacterScopeIdentity"
    )
    character_region = reader_region(
        "bool ResolveCharacterScopeIdentity", "bool ReadEventScopeToken"
    )
    target_region = reader_region(
        "bool ReadEventScopeToken", "bool ReadSavedScopeName"
    )
    saved_name_region = reader_region(
        "bool ReadSavedScopeName", "bool ReadEventScopeInventory"
    )
    generic_bounds_index = generic_type_region.find(
        "type_index >= static_cast<std::uint32_t>(count)"
    )
    generic_entry_index = generic_type_region.find("const auto entry_offset")
    generic_resolve_index = generic_type_region.find(
        "bindings.resolve_generic_value_type_name(identifier)"
    )
    if not (
        "resolve_generic_value_type_name" in generic_type_region
        and "native_name != bindings.generic_value_type_name_fallback"
        in generic_type_region
        and 0 <= generic_bounds_index < generic_entry_index
        and generic_entry_index < generic_resolve_index
        and "resolve_script_identifier_name" not in generic_type_region
        and "lookup_script_identifier_id" not in generic_type_region
    ):
        failures.append("reader: generic target type-name domain drifted")

    bindings_source = arguments.bindings.resolve().read_text(encoding="utf-8")
    if "kGenericValueTypeNameFallbackRva = 0x5000AB0" in bindings_source:
        failures.append(
            "bindings: registry fallback entry aliased as resolver string"
        )
    if not (
        "resolve_script_identifier_name" in saved_name_region
        and "lookup_script_identifier_id" in saved_name_region
        and "script_identifier_name_fallback" in saved_name_region
        and "resolve_script_identifier_name(table, identifier)"
        in saved_name_region
        and "roundtrip_identifier != identifier" in saved_name_region
        and "identifier < 0" not in saved_name_region
        and "resolve_generic_value_type_name" not in saved_name_region
    ):
        failures.append("reader: named script-identifier domain drifted")
    if not (
        "kEventScopeTokenPayloadOffset" in character_region
        and "kEventScopeTokenPayloadOffset" not in target_region
        and "ResolveCharacterScopeIdentity" in target_region
        and "output.raw_type_index == kCharacterScopeTypeIndex"
        in target_region
    ):
        failures.append("reader: character-only scope payload boundary drifted")

    scope_wire_sources: dict[str, str] = {}
    for label, path in (
        ("event_header", arguments.event_header),
        ("serializer", arguments.serializer),
        ("wire_contract", arguments.wire_contract),
    ):
        source = path.resolve().read_text(encoding="utf-8")
        scope_wire_sources[label] = source
        for forbidden in ("raw_16_bytes_hex", "raw_payload", "engine_pointer"):
            if forbidden in source:
                failures.append(
                    f"{label}: forbidden scope wire token {forbidden!r}"
                )

    serializer_source = scope_wire_sources["serializer"]
    if (
        "scope.name_identifier < 0" in serializer_source
        or "saved.name_identifier < 0" in serializer_source
    ):
        failures.append(
            "serializer: name_identifier must preserve full signed int32"
        )

    wire_contract_source = scope_wire_sources["wire_contract"]
    saved_wire_start = wire_contract_source.find(
        'saved["name_identifier"]'
    )
    saved_wire_stop = wire_contract_source.find(
        "if name in saved_names", saved_wire_start
    )
    saved_wire_region = (
        ""
        if saved_wire_start < 0 or saved_wire_stop < 0
        else wire_contract_source[saved_wire_start:saved_wire_stop]
    )
    if not (
        "-(2**31)" in saved_wire_region
        and "2**31 - 1" in saved_wire_region
    ):
        failures.append(
            "wire_contract: name_identifier signed-int32 range drifted"
        )

    locator = contract["locator_chain"]
    query_contract = contract["production_query"]
    if not locator["root_to_idler_static_ready"]:
        failures.append("contract: stable root-to-idler is not closed")
    if query_contract["capability"] != (
        "game.command.query-current-event-window-context-v1"
    ):
        failures.append("contract: production capability drifted")
    readiness = contract["readiness"]
    if not readiness["stable_event_definition_key_published"]:
        failures.append("contract: stable event definition key is not published")
    if not readiness["event_definition_identity_wire_ready"]:
        failures.append("contract: event definition identity wire is not ready")
    if not readiness["effect_indicator_wire_ready"]:
        failures.append("contract: effect indicator wire is not ready")
    if not (
        readiness.get("current_event_scope_layout_static_ready") is True
        and readiness.get(
            "current_event_scope_character_payload_identity_static_ready"
        )
        is True
        and readiness.get(
            "current_event_scope_noncharacter_payload_identity_static_ready"
        )
        is False
        and readiness.get("current_event_scope_product_static_ready") is True
        and readiness.get("current_event_scope_wire_ready") is True
        and readiness.get("current_event_scope_live_ready") is False
        and readiness.get("stable_scopes_ready") is False
        and readiness.get("semantic_decision_ready") is False
    ):
        failures.append("contract: current-event scope readiness drifted")
    published_identity = set(
        query_contract.get("published_event_definition_fields", [])
    )
    if published_identity != {
        "event_definition_key",
        "calculated_event_id",
        "runtime_stats_ordinal",
    }:
        failures.append("contract: published event definition fields drifted")
    if published_identity & set(query_contract["explicitly_unavailable"]):
        failures.append("contract: published event identity remains unavailable")
    published_scopes = query_contract.get("published_scope_fields", {})
    if not (
        published_scopes.get("root_scope")
        == [
            "status",
            "raw_type_index",
            "type_key",
            "subtype",
            "typed_identity",
        ]
        and published_scopes.get("saved_scope")
        == ["name", "name_identifier", "scope"]
        and published_scopes.get("readiness")
        == ["root_scope_ready", "saved_scopes_ready"]
        and query_contract.get("explicitly_unavailable")
        == ["full_effect_preview"]
    ):
        failures.append("contract: published scope wire fields drifted")
    published_options = set(query_contract["published_option_fields"])
    required_indicator_fields = {
        "effect_indicators",
        "effect_preview_unavailable",
        "resource_deltas_unavailable",
        "relationship_deltas_unavailable",
    }
    if not required_indicator_fields <= published_options:
        failures.append("contract: effect indicator wire fields are incomplete")
    live = contract.get("live_validation", {})
    if not (
        contract.get("live_validated") is True
        and contract.get("game_process_started") is True
        and readiness.get("bridge_query_ready") is True
        and readiness.get("current_event_window_context_fixture_live_ready")
        is True
        and readiness.get("empty_effect_indicator_surface_live_ready") is True
        and readiness.get("bounded_nonempty_effect_indicator_rows_live_ready")
        is True
        and readiness.get("nonempty_effect_indicator_kinds_live_ready") is False
        and readiness.get("event_window_lifecycle_live_ready") is False
        and readiness.get("semantic_decision_ready") is False
        and readiness.get("live_validated") is True
    ):
        failures.append("contract: scoped live readiness drifted")
    if not (
        live.get("evidence_classification") == "fixture-scoped-live-confirmed"
        and live.get("artifact_size") == 130779
        and live.get("artifact_sha256")
        == "690EB5EA188B0903281E5F5DFDA343DA795117EE0FB1C83C3FCDC7F572170B7B"
        and live.get("frozen_source_commit")
        == "cea30a067b1e112596d70532b98fa068b2102ebf"
        and live.get("full_event_instance_id") == 17
        and live.get("canonical_event_definition_key")
        == "xar_event_window_live_fixture.1"
        and signed_int32(live.get("seed_calculated_event_id"))
        and signed_int32(live.get("cold_calculated_event_id"))
        and signed_int32(live.get("seed_runtime_stats_ordinal"))
        and signed_int32(live.get("cold_runtime_stats_ordinal"))
        and live.get("materialized_native_option_indices") == [0, 1, 3]
        and live.get("cancel_native_option_indices") == [3]
        and live.get("effect_indicator_rows_per_option") == [0, 0, 0]
        and live.get("adjacent_cold_frames_equal") is True
        and live.get("fixture_bytes_equal_across_stages") is True
        and live.get("no_event_option_selected") is True
        and live.get("managed_process_cleanup") is True
        and live.get("nonce_root_removed") is True
        and live.get("no_ck3_processes_after") is True
    ):
        failures.append("contract: Attempt4 fixture-live evidence drifted")
    bounded_nonempty = contract.get(
        "bounded_nonempty_effect_indicator_live_validation", {}
    )
    if not (
        bounded_nonempty.get("evidence_classification")
        == "fixture-scoped-live-confirmed"
        and bounded_nonempty.get("artifact_size") == 136947
        and bounded_nonempty.get("artifact_sha256")
        == "1DE73B16CBD90FE05112D60A7F09274E95FE1BAC8D18D79C2AF8A8A2BC8249C3"
        and bounded_nonempty.get("implementation_commit")
        == "06bde70d63af209f23feaeb290a57431de59be57"
        and bounded_nonempty.get("frozen_source_commit")
        == "cea30a067b1e112596d70532b98fa068b2102ebf"
        and bounded_nonempty.get("wrapper_size") == 17299
        and bounded_nonempty.get("wrapper_sha256")
        == "05563518839C6D715AB93E936E73E252A2724EAC92D31418F9E7C695D9DC7638"
        and bounded_nonempty.get("seed_bridge_pid") == 23632
        and bounded_nonempty.get("cold_bridge_pid") == 35364
        and bounded_nonempty.get("full_event_instance_id") == 17
        and bounded_nonempty.get("canonical_event_definition_key")
        == "xar_event_indicator_live_fixture.1"
        and signed_int32(bounded_nonempty.get("seed_calculated_event_id"))
        and signed_int32(bounded_nonempty.get("cold_calculated_event_id"))
        and signed_int32(bounded_nonempty.get("seed_runtime_stats_ordinal"))
        and signed_int32(bounded_nonempty.get("cold_runtime_stats_ordinal"))
        and bounded_nonempty.get("materialized_native_option_indices")
        == [0, 1, 3]
        and bounded_nonempty.get("effect_indicator_rows_per_option")
        == [0, 1, 2]
        and bounded_nonempty.get("exact_nonempty_rows")
        == [
            "trait/add brave native_id=64",
            (
                "stress/increase magnitude=unavailable "
                "affected_by_trait=false critical=false"
            ),
            "death/played_character direction=not_applicable",
        ]
        and bounded_nonempty.get("adjacent_cold_frames_equal") is True
        and bounded_nonempty.get("fixture_bytes_equal_across_stages") is True
        and bounded_nonempty.get("full_effect_set_claimed") is False
        and bounded_nonempty.get("effect_preview_ready") is False
        and bounded_nonempty.get("semantic_decision_ready") is False
        and bounded_nonempty.get("visual_gui_icon_render_verified") is False
        and bounded_nonempty.get("no_event_option_selected") is True
        and bounded_nonempty.get("managed_process_cleanup") is True
        and bounded_nonempty.get("nonce_root_removed") is True
        and bounded_nonempty.get("no_ck3_processes_after") is True
    ):
        failures.append(
            "contract: bounded nonempty fixture-live evidence drifted"
        )
    live_acceptance = query_contract.get("live_acceptance", {})
    if not (
        isinstance(live_acceptance, dict)
        and "Attempt4" in live_acceptance.get("completed", "")
        and "nonempty Attempt1" in live_acceptance.get("completed", "")
        and "remaining nonempty" in live_acceptance.get("remaining", "")
    ):
        failures.append("contract: live acceptance boundary drifted")
    typed_context = contract.get("typed_context_proposal", {})
    if not (
        typed_context.get("status")
        == (
            "definition_identity_presentation_and_bounded_nonempty_effect_"
            "indicator_surface_fixture_live_plus_current_event_scope_wire_"
            "static"
        )
        and "Attempt4" in typed_context.get("live_scope", "")
        and "nonempty Attempt1" in typed_context.get("live_scope", "")
        and "Production current-event-window-context-v1" in typed_context.get(
            "static_scope_wire", ""
        )
        and "no paused scope artifact" in typed_context.get(
            "static_scope_wire", ""
        )
        and "remaining nonempty" in typed_context.get(
            "remaining_live_scope", ""
        )
        and "semantic choice" in typed_context.get(
            "remaining_live_scope", ""
        )
    ):
        failures.append("contract: typed context live scope drifted")

    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        return 1
    print(
        f"PASS spans={len(function_spans) + len(additional_spans)} "
        "pdata=1 exact_build=1 read_only=1 "
        "source_contract=1 fixture_live=1 scope_static=1 scope_wire=1 "
        "scope_live=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
