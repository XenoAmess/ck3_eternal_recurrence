#!/usr/bin/env python3
"""Verify pending-character-interaction-context-v1 exact-build evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

from scan_anchors import PeImage


HERE = Path(__file__).resolve().parent
REPOSITORY_ROOT = HERE.parents[2]
DEFAULT_CONTRACT = HERE / "pending_character_interaction_context_v1_abi.json"
DEFAULT_FIXTURE = (
    HERE
    / "fixtures"
    / "pending_character_interaction_context_v1_source_contract.json"
)
DEFAULT_EXE = REPOSITORY_ROOT / "Crusader Kings III" / "binaries" / "ck3.exe"
DEFAULT_HEADER = (
    HERE.parent
    / "include"
    / "xar_bridge"
    / "pending_character_interaction_context_v1.hpp"
)
DEFAULT_READER = HERE.parent / "src" / "pending_character_interaction_context_v1.cpp"
DEFAULT_SERIALIZER = (
    HERE.parent / "src" / "pending_character_interaction_context_v1_serializer.cpp"
)
DEFAULT_MAILBOX = (
    HERE.parent / "src" / "pending_character_interaction_context_v1_mailbox.cpp"
)
DEFAULT_BRIDGE = HERE.parent / "src" / "bridge.cpp"
DEFAULT_CK3_SOURCE = HERE.parent / "src" / "ck3_11906.cpp"


def integer(value: object) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value, 0)
    raise TypeError(f"expected integer or integer string, found {value!r}")


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
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    parser.add_argument("--header", type=Path, default=DEFAULT_HEADER)
    parser.add_argument("--reader", type=Path, default=DEFAULT_READER)
    parser.add_argument("--serializer", type=Path, default=DEFAULT_SERIALIZER)
    parser.add_argument("--mailbox", type=Path, default=DEFAULT_MAILBOX)
    parser.add_argument("--bridge", type=Path, default=DEFAULT_BRIDGE)
    parser.add_argument("--ck3-source", type=Path, default=DEFAULT_CK3_SOURCE)
    arguments = parser.parse_args()

    failures: list[str] = []
    executable_data = arguments.exe.resolve().read_bytes()
    image = PeImage(executable_data)
    contract = json.loads(arguments.contract.resolve().read_text(encoding="utf-8"))
    fixture = json.loads(arguments.fixture.resolve().read_text(encoding="utf-8"))

    executable_sha = hashlib.sha256(executable_data).hexdigest().upper()
    expected_executable_sha = contract["ck3_exe_sha256"].upper()
    if executable_sha != expected_executable_sha:
        failures.append(
            "executable SHA mismatch: "
            f"expected {expected_executable_sha}, found {executable_sha}"
        )

    pdata_ranges = runtime_function_ranges(executable_data, image)
    spans = contract["source_contract"]["exact_byte_spans"]
    for span in spans:
        start = integer(span["start_rva"])
        end = integer(span["end_rva"])
        span_kind = span.get("span_kind", "single_pdata_runtime_function")
        if span_kind == "leaf_thunk_without_pdata_runtime_function_row":
            if (start, end) in pdata_ranges:
                failures.append(
                    f"{span['name']}: declared leaf thunk unexpectedly has that .pdata row"
                )
        else:
            declared_regions = span.get("runtime_function_regions")
            if declared_regions:
                regions = []
                for region in declared_regions:
                    begin_text, finish_text = region.split("..", maxsplit=1)
                    regions.append((integer(begin_text), integer(finish_text)))
            else:
                regions = [(start, end)]
            for begin, finish in regions:
                if (begin, finish) not in pdata_ranges:
                    failures.append(
                        f"{span['name']}: 0x{begin:X}..0x{finish:X} "
                        "is not an exact .pdata runtime-function extent"
                    )

        expected_length = integer(span["byte_length"])
        actual_length = end - start
        if actual_length != expected_length:
            failures.append(
                f"{span['name']}: declared length 0x{expected_length:X}, "
                f"RVA range length 0x{actual_length:X}"
            )
            continue
        offset = image.rva_to_offset(start)
        blob = executable_data[offset : offset + actual_length]
        actual_sha = hashlib.sha256(blob).hexdigest().upper()
        expected_sha = span["sha256"].upper()
        if len(blob) != actual_length:
            failures.append(f"{span['name']}: range is not fully file-backed")
        elif actual_sha != expected_sha:
            failures.append(
                f"{span['name']}: expected {expected_sha}, found {actual_sha}"
            )
        else:
            print(
                f"OK {span['name']} RVA=0x{start:X}..0x{end:X} "
                f"bytes=0x{actual_length:X} SHA256={actual_sha}"
            )

    for relative_path, expected_sha in contract["source_contract"][
        "source_files"
    ].items():
        source_path = REPOSITORY_ROOT / Path(relative_path)
        try:
            actual_sha = hashlib.sha256(source_path.read_bytes()).hexdigest().upper()
        except OSError as error:
            failures.append(f"source file {relative_path}: cannot read: {error}")
            continue
        if actual_sha != expected_sha.upper():
            failures.append(
                f"source file {relative_path}: expected {expected_sha}, found {actual_sha}"
            )

    source_contracts = {
        "header": (
            arguments.header,
            (
                "kPendingInteractionCostEvaluatorV1Rva",
                "NativePendingInteractionCostEvaluatorV1",
                "invoke_cost_evaluator",
                "generic_costs_ready",
                "kPendingInteractionCommonWarRelationV1Rva",
                "invoke_common_war_relation",
                "resolve_active_war",
                "special_war_binding_ready",
                "special_outcome_terms_ready",
                "kPendingInteractionWarTargetTypeIndexV1",
                "kPendingInteractionWarTargetWarIdOffsetV1",
                "kPendingInteractionCallAllyDefinitionKeyV1",
            ),
        ),
        "reader": (
            arguments.reader,
            (
                "kDefinitionCostBlockOffset = 0x38",
                "treasury_or_gold",
                "pending_payment_state = \"already_applied\"",
                "ReadSpecialWarBinding",
                "special_interaction_identity_mismatch",
                "native_common_war_relation",
                "second != first",
                "is_exact_call_ally_war_target",
                "war_target_identity_unavailable",
                "resolved_war_id == war_id",
            ),
        ),
        "serializer": (
            arguments.serializer,
            (
                '\\"payer_role\\"',
                '\\"application_timing\\"',
                '\\"pending_payment_state\\"',
                '\\"cost_evaluator_rva\\"',
                '\\"special_war_binding\\"',
                '\\"common_war_relation_rva\\"',
                '\\"special_outcome_terms_ready\\"',
                "ValidTargetEnvelope",
                "kExpectedRawEnvelopeBytes",
            ),
        ),
        "mailbox": (
            arguments.mailbox,
            (
                "ProxyInvokeCostEvaluator",
                "ProxyInvokeCommonWarRelation",
                "ProxyResolveActiveWar",
                "IsExecutingExactMailboxSlot",
            ),
        ),
        "bridge": (
            arguments.bridge,
            (
                "InvokePendingCharacterInteractionCostEvaluatorDirectV1",
                "InvokePendingCharacterInteractionCommonWarRelationDirectV1",
            ),
        ),
        "ck3_source": (
            arguments.ck3_source,
            (
                "ResolvePendingCharacterInteractionActiveWarV1",
                "ResolveWar(bindings, game_state, war_id)",
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
        "0x26B3480",
        "0x3380410",
        "SubmitCommand",
        "WriteProcessMemory",
        "notification-description",
    ):
        if forbidden in reader_source:
            failures.append(f"reader: forbidden executor token {forbidden!r}")

    expected_cost_mapping = [
        (0, "gold", "GOLD_COST", "0x2875"),
        (1, "prestige", "PRESTIGE_COST", "0x0001"),
        (2, "piety", "PIETY_COST", "0x2B26"),
        (3, "renown", "DYNASTY_PRESTIGE_COST", "0x2B27"),
        (4, "influence", "INFLUENCE_COST", "0x318D"),
        (5, "herd", "HERD_COST", "0x29F5"),
        (6, "treasury", "TREASURY_COST", "0x3B32"),
        (
            7,
            "treasury_or_gold",
            "TREASURY_COST or GOLD_COST by actor treasury predicate",
            "0x3D24",
        ),
        (8, "merit", "MERIT_COST", "0x3E42"),
        (9, "barter_goods", "BARTER_GOODS_COST", "0x3D30"),
    ]
    actual_cost_mapping = [
        (
            row.get("slot"),
            row.get("resource_key"),
            row.get("formatter_key"),
            row.get("serializer_token_id"),
        )
        for row in contract.get("generic_authored_costs", {}).get("mapping", [])
        if isinstance(row, dict)
    ]
    if actual_cost_mapping != expected_cost_mapping:
        failures.append("contract: exact ten-slot generic cost mapping drifted")

    payment = contract.get("generic_authored_costs", {}).get(
        "pending_wire_semantics"
    )
    expected_payment = {
        "payer_role": "actor",
        "application_timing": "on_send",
        "pending_payment_state": "already_applied",
    }
    if payment != expected_payment:
        failures.append("contract: pending generic-cost payment semantics drifted")

    fixture_costs = fixture.get("defaults", {}).get("generic_authored_costs", {})
    fixture_entries = fixture_costs.get("entries", [])
    if (
        fixture.get("synthetic") is not True
        or fixture.get("not_live_evidence") is not True
        or fixture_costs.get("raw_scale") != 100_000
        or {
            key: fixture_costs.get(key)
            for key in (
                "payer_role",
                "application_timing",
                "pending_payment_state",
            )
        }
        != expected_payment
        or [
            row.get("resource_key") if isinstance(row, dict) else None
            for row in fixture_entries
        ]
        != [row[1] for row in expected_cost_mapping]
        or not any(
            isinstance(row.get("raw"), int) and row["raw"] < 0
            for row in fixture_entries
            if isinstance(row, dict)
        )
    ):
        failures.append("fixture: signed ten-key generic-cost contract drifted")

    special = contract.get("special_war_binding", {})
    expected_special_pairs = [
        (
            "end_war_attacker_victory_interaction",
            "0x428EEA8",
            "end_war_attacker_victory_interaction",
            "attacker_victory",
        ),
        (
            "end_war_attacker_white_peace_interaction",
            "0x428EF88",
            "end_war_white_peace_interaction",
            "white_peace",
        ),
        (
            "end_war_attacker_defeat_interaction",
            "0x428EF18",
            "end_war_attacker_defeat_interaction",
            "attacker_defeat",
        ),
    ]
    actual_special_pairs = [
        (
            row.get("definition_key"),
            row.get("vtable_rva"),
            row.get("special_interaction_kind"),
            row.get("absolute_outcome"),
        )
        for row in special.get("exact_pairs", [])
        if isinstance(row, dict)
    ]
    if (
        special.get("contract")
        != "pending-character-interaction-special-war-binding-v1"
        or actual_special_pairs != expected_special_pairs
        or special.get("binding_source") != "native_common_war_relation"
        or special.get("typed_unavailable")
        != [
            "special_war_binding_not_applicable",
            "special_interaction_subtype_opaque",
            "special_interaction_identity_mismatch",
            "special_war_binding_unavailable",
            "special_war_roles_mismatch",
        ]
        or "known war-exit definition with null special_data is "
        "special_interaction_identity_mismatch"
        not in special.get("presence_identity_gate", "")
        or special.get("production_wired") is not True
        or special.get("live_validated") is not False
    ):
        failures.append("contract: exact ordinary special-war binding drifted")
    fixture_vectors = {
        row.get("name"): row
        for row in fixture.get("vectors", [])
        if isinstance(row, dict)
    }
    required_special_vectors = {
        "ordinary_white_peace_exact_special_war_binding",
        "ordinary_victory_exact_special_war_binding",
        "ordinary_defeat_exact_special_war_binding",
        "owner_deferred_religious_special_subtype_stays_opaque",
        "known_definition_vptr_mismatch_is_unavailable",
        "known_definition_missing_special_data_is_identity_mismatch",
        "active_war_generation_or_role_failure_is_unavailable",
    }
    if not required_special_vectors.issubset(fixture_vectors):
        failures.append("fixture: special-war source vectors are incomplete")
    religious_vector = fixture_vectors.get(
        "owner_deferred_religious_special_subtype_stays_opaque", {}
    )
    if (
        religious_vector.get("expected", {}).get(
            "common_war_relation_invoked"
        )
        is not False
    ):
        failures.append("fixture: owner-deferred subtype crossed relation lookup")
    missing_special_vector = fixture_vectors.get(
        "known_definition_missing_special_data_is_identity_mismatch", {}
    )
    if not (
        missing_special_vector.get("expected", {}).get("reason")
        == "special_interaction_identity_mismatch"
        and missing_special_vector.get("expected", {}).get(
            "common_war_relation_invoked"
        )
        is False
    ):
        failures.append("fixture: known war definition accepted null special data")

    required_target_vectors = {
        "call_ally_war_target_full_id_resolves",
        "call_ally_war_target_resolver_failure_stays_unavailable",
        "call_ally_war_target_full_id_mismatch_stays_unavailable",
        "non_call_ally_type16_war_stays_generic",
    }
    if not required_target_vectors.issubset(fixture_vectors):
        failures.append("fixture: call-ally typed-target source vectors are incomplete")
    else:
        exact_target = fixture_vectors["call_ally_war_target_full_id_resolves"]
        exact_target_override = exact_target.get("overrides", {}).get("target", {})
        exact_target_expected = exact_target.get("expected", {})
        if not (
            exact_target.get("overrides", {})
            .get("definition", {})
            .get("canonical_key")
            == "call_ally_interaction"
            and exact_target_override.get("raw_scope_type_index") == 16
            and exact_target_override.get("type_key") == "war"
            and exact_target_override.get("raw_16_bytes_hex")
            == "10000000000000005200000400000000"
            and exact_target_override.get("typed_status") == "available"
            and exact_target_override.get("typed_identity") == "war:67108946"
            and exact_target_expected.get("target_typed_status") == "available"
            and exact_target_expected.get("target_typed_identity")
            == "war:67108946"
            and exact_target_expected.get("target_typed_identity_ready") is True
            and exact_target_expected.get("resolver_invoked_twice") is True
        ):
            failures.append("fixture: exact call-ally war target vector drifted")

        resolver_failure = fixture_vectors[
            "call_ally_war_target_resolver_failure_stays_unavailable"
        ]
        resolver_failure_expected = resolver_failure.get("expected", {})
        if not (
            resolver_failure.get("overrides", {})
            .get("definition", {})
            .get("canonical_key")
            == "call_ally_interaction"
            and resolver_failure.get("overrides", {})
            .get("target", {})
            .get("typed_status")
            == "unavailable"
            and resolver_failure.get("overrides", {})
            .get("target", {})
            .get("unavailable_reason")
            == "war_target_identity_unavailable"
            and resolver_failure_expected.get("target_typed_identity_ready") is False
            and resolver_failure_expected.get("reason")
            == "war_target_identity_unavailable"
        ):
            failures.append("fixture: call-ally resolver-failure vector drifted")

        mismatch = fixture_vectors[
            "call_ally_war_target_full_id_mismatch_stays_unavailable"
        ]
        mismatch_expected = mismatch.get("expected", {})
        if not (
            mismatch.get("overrides", {})
            .get("definition", {})
            .get("canonical_key")
            == "call_ally_interaction"
            and mismatch.get("overrides", {})
            .get("target", {})
            .get("typed_status")
            == "unavailable"
            and mismatch.get("overrides", {})
            .get("target", {})
            .get("unavailable_reason")
            == "war_target_identity_unavailable"
            and mismatch_expected.get("target_typed_identity_ready") is False
            and mismatch_expected.get("reason")
            == "war_target_identity_unavailable"
        ):
            failures.append("fixture: call-ally full-ID mismatch vector drifted")

        generic_target = fixture_vectors["non_call_ally_type16_war_stays_generic"]
        generic_target_expected = generic_target.get("expected", {})
        if not (
            generic_target.get("overrides", {})
            .get("definition", {})
            .get("canonical_key")
            == "request_contract_assistance_interaction"
            and generic_target.get("overrides", {})
            .get("target", {})
            .get("raw_scope_type_index")
            == 16
            and generic_target.get("overrides", {})
            .get("target", {})
            .get("type_key")
            == "war"
            and generic_target.get("overrides", {})
            .get("target", {})
            .get("typed_status")
            == "unavailable"
            and generic_target.get("overrides", {})
            .get("target", {})
            .get("unavailable_reason")
            == "generic_scope_payload_identity_not_closed"
            and generic_target.get("overrides", {})
            .get("target", {})
            .get("resolver", {})
            .get("invoked")
            is False
            and generic_target_expected.get("target_typed_identity_ready") is False
            and generic_target_expected.get("reason")
            == "generic_scope_payload_identity_not_closed"
            and generic_target_expected.get("resolver_invoked") is False
        ):
            failures.append("fixture: non-call-ally generic target vector drifted")
    external_live = fixture.get("external_live_evidence", {})
    if not (
        isinstance(external_live, dict)
        and external_live.get("contract")
        == "../pending_character_interaction_context_v1_abi.json#live_validation"
        and external_live.get("artifact_sha256")
        == contract.get("live_validation", {}).get("artifact_sha256")
    ):
        failures.append("fixture: historical external live evidence drifted")
    signed_live = contract.get("signed_pending_id_live_validation", {})
    fixture_signed_live = fixture.get("signed_pending_id_live_evidence", {})
    if not (
        isinstance(signed_live, dict)
        and signed_live.get("status") == "production-live loop"
        and signed_live.get("source_commit")
        == "c21c096263325e1d8a13a4b01eebaa38ac88d2dd"
        and signed_live.get("run_id")
        == "20260827T191804Z-one-generation-8c116e3e"
        and signed_live.get("artifact_sha256")
        == "3980E4A2CD7F140A98488184C2095B3B41EF92EC80505B837177200705DD3973"
        and signed_live.get("run_outcome") == "bounded_incomplete"
        and signed_live.get("requested_turns") == 12
        and signed_live.get("successful_turns") == 12
        and signed_live.get("pending_interaction_id") == -2013265918
        and signed_live.get("query_step")
        == "query-pending-character-interaction-context-v1"
        and signed_live.get("reply_step")
        == "reject-pending-character-interaction"
        and signed_live.get("reply_status") == "rejected"
        and signed_live.get("old_id_absent_after_reply") is True
        and signed_live.get("continued_after_reply") is True
        and signed_live.get("checkpoints_saved") == 2
        and signed_live.get("cleanup_proven") is True
        and signed_live.get("semantic_decision_ready") is False
    ):
        failures.append("contract: signed-negative live evidence boundary drifted")
    if not (
        isinstance(fixture_signed_live, dict)
        and fixture_signed_live.get("contract")
        == "../pending_character_interaction_context_v1_abi.json#signed_pending_id_live_validation"
        and fixture_signed_live.get("artifact_sha256")
        == signed_live.get("artifact_sha256")
        and fixture_signed_live.get("pending_interaction_id")
        == signed_live.get("pending_interaction_id")
        and fixture_signed_live.get("query_step") == signed_live.get("query_step")
        and fixture_signed_live.get("reply_step") == signed_live.get("reply_step")
        and fixture_signed_live.get("reply_status") == signed_live.get("reply_status")
        and fixture_signed_live.get("old_id_absent_after_reply") is True
    ):
        failures.append("fixture: signed-negative live evidence drifted")
    if fixture.get("source_hashes") != contract.get("source_contract", {}).get(
        "source_files"
    ):
        failures.append("fixture: exact source-hash contract drifted")

    readiness = contract.get("readiness", {})
    fixture_readiness = fixture.get("expected_readiness", {})
    if readiness.get("generic_costs_live_ready") is not False:
        failures.append("contract: static-only cost slice cannot claim live readiness")
    if fixture_readiness.get("generic_costs_live_ready") is not False:
        failures.append("fixture: synthetic cost slice cannot claim live readiness")
    if not (
        readiness.get("special_war_binding_static_ready") is True
        and readiness.get("special_war_binding_query_ready") is True
        and readiness.get("special_war_binding_live_ready") is False
        and readiness.get("special_outcome_terms_ready") is False
        and fixture_readiness.get("special_war_binding_static_ready") is True
        and fixture_readiness.get("special_war_binding_query_ready") is True
        and fixture_readiness.get("special_war_binding_live_ready") is False
        and fixture_readiness.get("special_outcome_terms_ready") is False
    ):
        failures.append("contract: special-war readiness boundary drifted")
    if not (
        readiness.get("ordinary_pending_query_live_ready") is True
        and readiness.get("production_live_ready") is True
        and fixture_readiness.get("ordinary_pending_query_live_ready") is True
        and fixture_readiness.get("production_live_ready") is True
    ):
        failures.append("contract: historical ordinary live readiness drifted")
    if not (
        readiness.get("call_ally_war_target_query_ready") is True
        and readiness.get("call_ally_war_target_live_ready") is False
        and fixture_readiness.get("call_ally_war_target_query_ready") is True
        and fixture_readiness.get("call_ally_war_target_live_ready") is False
    ):
        failures.append("contract: call-ally typed-target readiness boundary drifted")
    if not (
        readiness.get("signed_pending_id_contract_ready") is True
        and readiness.get("negative_signed_pending_id_live_ready") is True
        and fixture_readiness.get("signed_pending_id_contract_ready") is True
        and fixture_readiness.get("negative_signed_pending_id_live_ready") is True
    ):
        failures.append("contract: signed-negative readiness boundary drifted")
    for source, label in (
        (readiness.get("production_live_scope"), "contract"),
        (fixture_readiness.get("production_live_scope"), "fixture"),
    ):
        if not (
            isinstance(source, str)
            and "historical ordinary" in source
            and "signed-negative" in source
            and "generic cost" in source
            and "special war binding" in source
            and "notification ACK" in source
            and "intermediary" in source
            and "semantic decision" in source
        ):
            failures.append(f"{label}: production live scope is not explicit")
    if not (
        contract.get("live_validated") is True
        and contract.get("live_validated_scope")
        == "historical ordinary nonreligious recipient pending identity, roles, route, deadline and reply legality plus one signed-negative arrange-marriage query/reject lifecycle"
        and isinstance(contract.get("not_live_validated_scope"), str)
        and "generic authored cost" in contract["not_live_validated_scope"]
        and "typed call_ally war target" in contract["not_live_validated_scope"]
        and "special war binding" in contract["not_live_validated_scope"]
        and "notification ACK" in contract["not_live_validated_scope"]
        and "intermediary" in contract["not_live_validated_scope"]
        and "semantic decision" in contract["not_live_validated_scope"]
    ):
        failures.append("contract: top-level historical live scope drifted")
    if not {"religion", "faith", "holy_war"}.issubset(
        contract["owner_deferred_domains"]
    ):
        failures.append("contract: owner-deferred religion boundary was lost")

    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        return 1
    print(
        f"PASS spans={len(spans)} exact_build=1 source_hashes=1 "
        "cost_mapping=10 special_war_pairs=3 read_only=1 "
        "signed_negative_live=1 call_ally_live_pending=1"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
