#include "xar_bridge/pending_character_interaction_context_v1.hpp"

#include <fstream>
#include <iostream>
#include <iterator>
#include <string>
#include <string_view>

namespace {

std::string ReadAll(const char *path) {
  std::ifstream input(path, std::ios::binary);
  return {std::istreambuf_iterator<char>(input),
          std::istreambuf_iterator<char>()};
}

bool Contains(std::string_view value, std::string_view token) {
  return value.find(token) != std::string_view::npos;
}

bool ContainsAll(std::string_view value,
                 std::initializer_list<std::string_view> tokens) {
  for (const auto token : tokens) {
    if (!Contains(value, token)) {
      std::cerr << "missing source-contract token: " << token << '\n';
      return false;
    }
  }
  return true;
}

} // namespace

int main(int argc, char **argv) {
  if (argc != 6) {
    std::cerr << "expected five source-contract paths\n";
    return 1;
  }
  const auto header = ReadAll(argv[1]);
  const auto reader = ReadAll(argv[2]);
  const auto serializer = ReadAll(argv[3]);
  const auto abi = ReadAll(argv[4]);
  const auto fixture = ReadAll(argv[5]);
  if (header.empty() || reader.empty() || serializer.empty() || abi.empty() ||
      fixture.empty()) {
    std::cerr << "source-contract input is unreadable\n";
    return 1;
  }

  using namespace xar::ck3_11906;
  if (kPendingCharacterInteractionContextV1Capability !=
          "game.command.query-pending-character-interaction-context-v1" ||
      kPendingCharacterInteractionContextV1Step !=
          "query-pending-character-interaction-context-v1" ||
      kPendingCharacterInteractionContextV1GameVersion != "1.19.0.6" ||
      kPendingCharacterInteractionContextV1ExecutableSha256 !=
          "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86" ||
      kPendingCharacterInteractionContextV1BackendId !=
          "ck3-1.19.0.6-native-pending-character-interaction-context-v1" ||
      kPendingInteractionStorageSlotV1Rva != 0x57BF1C8 ||
      kPendingInteractionCharacterStorageSlotV1Rva != 0x570C130 ||
      kPendingInteractionExpirationDaysV1Rva != 0x570F528 ||
      kPendingInteractionLocalRoutingV1Rva != 0x1266BA0 ||
      kPendingInteractionReplyValidatorV1Rva != 0x26B3540 ||
      kPendingInteractionTriggerEvaluatorV1Rva != 0x334C510 ||
      kPendingInteractionTargetTypeRegistryGetterV1Rva != 0x33C52B0 ||
      kPendingInteractionTargetTypeRegistryV1Rva != 0x4FFE290 ||
      kPendingInteractionTargetTypeFallbackEntryV1Rva != 0x5000AB0 ||
      kPendingInteractionScriptIdentifierNameV1Rva != 0x3B58970 ||
      kPendingInteractionReplyPrimaryVtableV1Rva != 0x4082930 ||
      kPendingInteractionReplySecondaryVtableV1Rva != 0x4082900 ||
      kPendingInteractionMaximumSendOptionsV1 != 256) {
    std::cerr << "compiled exact-build binding drifted\n";
    return 1;
  }

  if (!ContainsAll(
          header,
          {"PendingCharacterInteractionContextRequestV1",
           "expected_snapshot_revision", "pending_interaction_id",
           "played_character_id", "invoke_local_routing",
           "invoke_reply_validator", "invoke_trigger_evaluator",
           "invoke_target_type_registry", "invoke_script_identifier_name",
           "interaction_semantic_decision_ready"}) ||
      !ContainsAll(
          reader,
          {"kPendingDefinitionOffset = 0x18",
           "kPendingActorOffset = 0x2F0",
           "kPendingTargetEnvelopeOffset = 0x308",
           "kPendingSelectedOptionsDataOffset = 0x318",
           "kPendingAgeDaysOffset = 0x5B8",
           "kPendingRoutingKindOffset = 0x5C0",
           "kPendingAutoAcceptNotificationOffset = 0x5C6",
           "kDefinitionSendOptionRowsOffset = 0x2548",
           "kDefinitionAutoAcceptTriggerOffset = 0x2580",
           "kDefinitionAutoAcceptScalarOffset = 0x2A48",
           "kSendOptionValidTriggerOffset = 0xE0",
           "kSendOptionShownTriggerOffset = 0x00",
           "observed_id != full_id", "pending_generation_mismatch",
           "played_character_generation_mismatch",
           "pending_not_routed_to_played_character",
           "environment.module_base + kPendingInteractionTargetTypeRegistryV1Rva",
           "target_type_registry_drift", "type_index >=",
           "generic_scope_payload_identity_not_closed",
           "numeric_flag_identifier_string_mapping_not_closed",
           "selected_capacity < send_options.context_count",
           "second != first", "auto_accept_notification",
           "normal_reply_channel", "reply_validator_semantic_mismatch"}) ||
      !ContainsAll(
          serializer,
          {"\\\"schema\\\":\\\"pending-character-interaction-context-v1\\\"",
           "\\\"raw_type_index\\\"", "\\\"raw_16_bytes_hex\\\"",
           "\\\"type_key_status\\\"", "\\\"typed_identity_status\\\"",
           "\\\"canonical_flag_status\\\"", "\\\"legality\\\"",
           "\\\"structured_costs\\\"", "\\\"value\\\":null",
           "\\\"recipient_ai_acceptance_score\\\"",
           "\\\"interaction_semantic_decision_ready\\\"",
           "\\\"target_type_registry_rva\\\":\\\"0x4FFE290\\\""}) ||
      !ContainsAll(
          abi,
          {"\"exact_byte_spans\"",
           "contiguous_logic_span_across_three_pdata_runtime_functions",
           "leaf_thunk_without_pdata_runtime_function_row",
           "\"size_and_stride\": \"0x5C8\"",
           "\"generic_script_scope_type_registry_getter\"",
           "\"start_rva\": \"0x33C52B0\"",
           "8B7E4C67B9E772BBB75F303D7EE2444DBBF261D412FD0DCC97C99FC0C7297507",
           "B267CA32133ED15FE47468572C4B561E2A121B280BBEF8D653F56E4158CD1E6D",
           "55AC17937B11658E17C4884A9FD027FFA32BCD3B04EBC16B9D98F24BD9ECB02B",
           "\"generic_script_scope_type_registry\": \"0x4FFE290\"",
           "\"generic_script_scope_out_of_range_fallback_entry\": \"0x5000AB0\"",
           "\"generic_target_type_key_static_ready\": true",
           "\"ordinary_pending_query_live_ready\": true",
           "D20E339D56AFEFF8EB53F90FFD120AA8C42216AD214D38B7AC1B0EA9A2B8BC89",
           "enum 4 returns true before pending storage resolution",
           "\"auto_accept_notification_query_reachable\": false",
           "do not claim production ACK reachability"}) ||
      !ContainsAll(
          fixture,
          {"ordinary_recipient_request",
           "intermediary_request_uses_intermediary_route",
           "auto_accept_notification_is_ack_only",
           "stale_generation_is_not_actionable",
           "malformed_selected_option_count_fails_closed",
           "opaque_generic_target_preserves_legality_but_blocks_semantic_readiness",
           "\"type_key\": \"fixture_generic_target_type\"",
           "\"generic_target_type_key_static_ready\": true",
           "\"notification_ack_query_ready\": false"})) {
    return 1;
  }

  if (Contains(reader, "0x26B3480") ||
      Contains(reader, "pending_manager_response_transition") ||
      Contains(reader, "submit_command") ||
      Contains(reader, "SubmitCommand") ||
      Contains(reader, "WriteProcessMemory") ||
      Contains(reader, "notification-description") ||
      Contains(reader, "special_interaction virtual")) {
    std::cerr << "reader contains a mutator or unclosed semantic surface\n";
    return 1;
  }

  // The engine's send-option gate evaluates +0xE0 before +0x00. Keep the
  // standalone reader call sites in that same lexical order.
  const auto valid_position = reader.find("kSendOptionValidTriggerOffset");
  const auto shown_position = reader.find("kSendOptionShownTriggerOffset",
                                          valid_position + 1U);
  if (valid_position == std::string::npos || shown_position == std::string::npos ||
      valid_position >= shown_position) {
    std::cerr << "send-option trigger order drifted\n";
    return 1;
  }

  std::cout <<
      "pending-character-interaction-context-v1 source contract passed\n";
  return 0;
}
