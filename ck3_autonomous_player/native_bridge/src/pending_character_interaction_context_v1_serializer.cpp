#include "xar_bridge/pending_character_interaction_context_v1.hpp"

#include <array>
#include <charconv>
#include <cstdint>
#include <cstring>
#include <string>
#include <string_view>

namespace xar::ck3_11906 {
namespace {

constexpr std::array<std::string_view,
                     game::kPendingCharacterInteractionCostResourceCountV1>
    kCostResourceKeys{"gold",        "prestige",         "piety",
                      "renown",      "influence",        "herd",
                      "treasury",    "treasury_or_gold", "merit",
                      "barter_goods"};

std::string Number(std::uint64_t value) {
  std::array<char, 32> buffer{};
  const auto result =
      std::to_chars(buffer.data(), buffer.data() + buffer.size(), value);
  return result.ec == std::errc{} ? std::string(buffer.data(), result.ptr)
                                  : std::string{};
}

std::string SignedNumber(std::int64_t value) {
  std::array<char, 32> buffer{};
  const auto result =
      std::to_chars(buffer.data(), buffer.data() + buffer.size(), value);
  return result.ec == std::errc{} ? std::string(buffer.data(), result.ptr)
                                  : std::string{};
}

void AppendJsonString(std::string &output, std::string_view value) {
  constexpr char hex[] = "0123456789ABCDEF";
  output.push_back('"');
  for (const unsigned char character : value) {
    if (character == '"' || character == '\\') {
      output.push_back('\\');
      output.push_back(static_cast<char>(character));
    } else if (character < 0x20U) {
      output += "\\u00";
      output.push_back(hex[(character >> 4U) & 0x0FU]);
      output.push_back(hex[character & 0x0FU]);
    } else {
      output.push_back(static_cast<char>(character));
    }
  }
  output.push_back('"');
}

std::string_view
StatusName(game::PendingCharacterInteractionContextStatusV1 status) noexcept {
  switch (status) {
  case game::PendingCharacterInteractionContextStatusV1::available:
    return "available";
  case game::PendingCharacterInteractionContextStatusV1::invalid:
    return "invalid";
  case game::PendingCharacterInteractionContextStatusV1::unavailable:
  default:
    return "unavailable";
  }
}

std::string_view SemanticStatusName(
    game::PendingCharacterInteractionSemanticStatusV1 status) noexcept {
  switch (status) {
  case game::PendingCharacterInteractionSemanticStatusV1::available:
    return "available";
  case game::PendingCharacterInteractionSemanticStatusV1::absent:
    return "absent";
  case game::PendingCharacterInteractionSemanticStatusV1::unavailable:
  default:
    return "unavailable";
  }
}

bool ValidFailureLegality(
    const game::PendingCharacterInteractionLegalityV1 &legality,
    std::string_view reason) noexcept {
  return legality.status ==
             game::PendingCharacterInteractionSemanticStatusV1::unavailable &&
         !legality.allowed && legality.reason == reason;
}

bool ValidFailure(
    const game::PendingCharacterInteractionContextV1 &context) noexcept {
  const auto &ready = context.readiness;
  return !context.reason.empty() && !context.definition.has_value() &&
         !context.roles.has_value() && !context.target.has_value() &&
         !context.send_options.has_value() && !context.routing.has_value() &&
         !context.deadline.has_value() && !context.auto_accept.has_value() &&
         !context.terms.has_value() &&
         ValidFailureLegality(context.legality.accept, context.reason) &&
         ValidFailureLegality(context.legality.reject, context.reason) &&
         ValidFailureLegality(context.legality.block, context.reason) &&
         ValidFailureLegality(context.legality.acknowledge, context.reason) &&
         !ready.stable_definition_ready && !ready.roles_ready &&
         !ready.target_type_key_ready && !ready.target_typed_identity_ready &&
         !ready.send_options_ready && !ready.routing_ready &&
         !ready.deadline_ready && !ready.auto_accept_ready &&
         !ready.reply_legality_ready && !ready.generic_costs_ready &&
         !ready.special_war_binding_ready &&
         !ready.special_outcome_terms_ready && !ready.structured_terms_ready &&
         !ready.same_frame_ready &&
         !ready.interaction_semantic_decision_ready &&
         ready.not_ready_reasons.size() == 1 &&
         ready.not_ready_reasons.front() == context.reason;
}

bool ValidAvailableLegality(
    const game::PendingCharacterInteractionLegalityV1 &legality) noexcept {
  return legality.status ==
             game::PendingCharacterInteractionSemanticStatusV1::available &&
         (legality.allowed ? legality.reason.empty()
                           : !legality.reason.empty());
}

bool ValidUnavailableTerm(
    const game::PendingCharacterInteractionUnavailableTermV1 &term,
    std::string_view reason) noexcept {
  return term.status ==
             game::PendingCharacterInteractionSemanticStatusV1::unavailable &&
         term.reason == reason;
}

bool ValidTargetEnvelope(
    const game::PendingCharacterInteractionTargetV1 &target) noexcept {
  constexpr std::size_t kExpectedRawEnvelopeBytes = 16;
  if (target.raw_envelope.size() != kExpectedRawEnvelopeBytes) {
    return false;
  }
  std::uint16_t raw_type_index = 0;
  std::memcpy(&raw_type_index, target.raw_envelope.data(),
              sizeof(raw_type_index));
  return raw_type_index == target.raw_type_index;
}

bool ValidTypedWarTarget(
    const game::PendingCharacterInteractionTargetV1 &target,
    std::string_view definition_key) noexcept {
  constexpr std::size_t kExpectedRawEnvelopeBytes = 16;
  static_assert(kPendingInteractionWarTargetWarIdOffsetV1 +
                    sizeof(std::int32_t) <= kExpectedRawEnvelopeBytes);
  if (!ValidTargetEnvelope(target)) {
    return false;
  }
  if (definition_key != kPendingInteractionCallAllyDefinitionKeyV1 ||
      target.raw_type_index != kPendingInteractionWarTargetTypeIndexV1 ||
      target.type_key_status !=
          game::PendingCharacterInteractionSemanticStatusV1::available ||
      !target.type_key.has_value() || *target.type_key != "war" ||
      !target.type_key_reason.empty() ||
      target.typed_identity_status !=
          game::PendingCharacterInteractionSemanticStatusV1::available ||
      !target.typed_identity.has_value() ||
      !target.typed_identity_reason.empty()) {
    return false;
  }
  const auto identity = std::string_view(*target.typed_identity);
  const auto prefix = kPendingInteractionWarTargetIdentityPrefixV1;
  if (identity.size() <= prefix.size() ||
      identity.compare(0, prefix.size(), prefix) != 0) {
    return false;
  }
  const auto decimal = identity.substr(prefix.size());
  std::int32_t parsed_id = 0;
  const auto parsed = std::from_chars(
      decimal.data(), decimal.data() + decimal.size(), parsed_id, 10);
  if (parsed.ec != std::errc{} || parsed.ptr != decimal.data() + decimal.size() ||
      parsed_id <= 0 || std::to_string(parsed_id) != decimal) {
    return false;
  }
  std::int32_t raw_id = 0;
  std::memcpy(&raw_id,
              target.raw_envelope.data() +
                  kPendingInteractionWarTargetWarIdOffsetV1,
              sizeof(raw_id));
  return raw_id == parsed_id;
}

bool ValidUnavailableTarget(
    const game::PendingCharacterInteractionTargetV1 &target,
    std::string_view definition_key) noexcept {
  if (!ValidTargetEnvelope(target) ||
      target.typed_identity_status !=
          game::PendingCharacterInteractionSemanticStatusV1::unavailable ||
      target.typed_identity.has_value() ||
      target.typed_identity_reason.empty()) {
    return false;
  }
  if (target.typed_identity_reason ==
      "generic_scope_payload_identity_not_closed") {
    // The exact allowlisted call_ally/war tuple must use the dedicated
    // resolver-failure reason; accepting the generic reason here would let a
    // malformed typed tuple silently bypass its identity contract.
    return definition_key != kPendingInteractionCallAllyDefinitionKeyV1 ||
           target.raw_type_index != kPendingInteractionWarTargetTypeIndexV1 ||
           !target.type_key.has_value() || *target.type_key != "war";
  }
  return definition_key == kPendingInteractionCallAllyDefinitionKeyV1 &&
         target.raw_type_index == kPendingInteractionWarTargetTypeIndexV1 &&
         target.type_key.has_value() && *target.type_key == "war" &&
         target.typed_identity_reason == "war_target_identity_unavailable";
}

bool ValidStructuredCosts(
    const game::PendingCharacterInteractionStructuredCostsV1 &costs) noexcept {
  if (costs.status !=
          game::PendingCharacterInteractionSemanticStatusV1::available ||
      costs.raw_scale != game::kPendingCharacterInteractionCostRawScaleV1 ||
      costs.payer_role != "actor" || costs.application_timing != "on_send" ||
      costs.pending_payment_state != "already_applied" ||
      !costs.reason.empty()) {
    return false;
  }
  for (std::size_t index = 0; index < costs.entries.size(); ++index) {
    if (costs.entries[index].resource_key != kCostResourceKeys[index]) {
      return false;
    }
  }
  return true;
}

bool ValidSpecialWarBinding(
    const game::PendingCharacterInteractionSpecialWarBindingV1 &binding,
    std::string_view definition_key, bool special_data_present) noexcept {
  const bool known_definition =
      definition_key == "end_war_attacker_victory_interaction" ||
      definition_key == "end_war_attacker_white_peace_interaction" ||
      definition_key == "end_war_attacker_defeat_interaction";
  if (binding.status ==
      game::PendingCharacterInteractionSemanticStatusV1::unavailable) {
    const bool known_reason =
        binding.reason == "special_war_binding_not_applicable" ||
        binding.reason == "special_interaction_subtype_opaque" ||
        binding.reason == "special_interaction_identity_mismatch" ||
        binding.reason == "special_war_binding_unavailable" ||
        binding.reason == "special_war_roles_mismatch";
    const bool reason_matches_presence =
        (binding.reason == "special_war_binding_not_applicable" &&
         !special_data_present && !known_definition) ||
        (binding.reason == "special_interaction_subtype_opaque" &&
         special_data_present && !known_definition) ||
        (binding.reason == "special_interaction_identity_mismatch" &&
         (special_data_present || known_definition)) ||
        binding.reason == "special_war_binding_unavailable" ||
        (binding.reason == "special_war_roles_mismatch" &&
         special_data_present && known_definition);
    return known_reason && reason_matches_presence &&
           binding.special_interaction_kind.empty() &&
           binding.absolute_outcome.empty() && binding.war_id == -1 &&
           binding.actor_war_role.empty() &&
           binding.recipient_war_role.empty() && binding.binding_source.empty();
  }
  if (binding.status !=
          game::PendingCharacterInteractionSemanticStatusV1::available ||
      !special_data_present || binding.war_id <= 0 || !binding.reason.empty() ||
      binding.binding_source != "native_common_war_relation" ||
      !((binding.actor_war_role == "primary_attacker" &&
         binding.recipient_war_role == "primary_defender") ||
        (binding.actor_war_role == "primary_defender" &&
         binding.recipient_war_role == "primary_attacker"))) {
    return false;
  }
  return (definition_key == "end_war_attacker_victory_interaction" &&
          binding.special_interaction_kind ==
              "end_war_attacker_victory_interaction" &&
          binding.absolute_outcome == "attacker_victory") ||
         (definition_key == "end_war_attacker_white_peace_interaction" &&
          binding.special_interaction_kind ==
              "end_war_white_peace_interaction" &&
          binding.absolute_outcome == "white_peace") ||
         (definition_key == "end_war_attacker_defeat_interaction" &&
          binding.special_interaction_kind ==
              "end_war_attacker_defeat_interaction" &&
          binding.absolute_outcome == "attacker_defeat");
}

bool ValidAvailable(
    const game::PendingCharacterInteractionContextV1 &context) noexcept {
  if (!context.reason.empty() || !context.definition.has_value() ||
      !context.roles.has_value() || !context.target.has_value() ||
      !context.send_options.has_value() || !context.routing.has_value() ||
      !context.deadline.has_value() || !context.auto_accept.has_value() ||
      !context.terms.has_value()) {
    return false;
  }
  const auto &definition = *context.definition;
  const auto &target = *context.target;
  const auto &options = *context.send_options;
  const auto &routing = *context.routing;
  const auto &deadline = *context.deadline;
  const auto &auto_accept = *context.auto_accept;
  const auto &terms = *context.terms;
  const auto &ready = context.readiness;
  if (definition.canonical_key.empty() || definition.runtime_ordinal < 0 ||
      options.definition_count < 0 ||
      options.definition_count > kPendingInteractionMaximumSendOptionsV1 ||
      options.context_count != options.definition_count ||
      options.rows.size() !=
          static_cast<std::size_t>(options.definition_count) ||
      !routing.local_route || routing.played_character_id <= 0 ||
      (routing.current_responder_role != "recipient" &&
       routing.current_responder_role != "intermediary") ||
      (routing.reply_execution_channel != "recipient" &&
       routing.reply_execution_channel != "intermediary") ||
      deadline.age_days < 0 || deadline.expiration_days <= 0 ||
      deadline.remaining_days !=
          (deadline.age_days >= deadline.expiration_days
               ? 0
               : deadline.expiration_days - deadline.age_days) ||
      auto_accept.status !=
          game::PendingCharacterInteractionSemanticStatusV1::available ||
      !auto_accept.reason.empty() ||
      !ValidAvailableLegality(context.legality.accept) ||
      !ValidAvailableLegality(context.legality.reject) ||
      !ValidAvailableLegality(context.legality.block) ||
      !ValidAvailableLegality(context.legality.acknowledge) ||
      !ValidStructuredCosts(terms.structured_costs) ||
      !ValidSpecialWarBinding(terms.special_war_binding,
                              definition.canonical_key,
                              terms.special_data_present) ||
      !ValidUnavailableTerm(terms.structured_exchanges,
                            "structured_exchanges_unavailable") ||
      !ValidUnavailableTerm(terms.structured_effect_preview,
                            "structured_effect_preview_unavailable") ||
      !ValidUnavailableTerm(terms.recipient_ai_acceptance_score,
                            "recipient_ai_acceptance_score_unavailable") ||
      !ValidUnavailableTerm(terms.recipient_ai_final_decision,
                            "recipient_ai_final_decision_unavailable")) {
    return false;
  }
  if (target.present) {
    if (!ValidTargetEnvelope(target) || target.raw_type_index == 0 ||
        target.type_key_status !=
            game::PendingCharacterInteractionSemanticStatusV1::available ||
        !target.type_key.has_value() || target.type_key->empty() ||
        !target.type_key_reason.empty() ||
        (!ValidTypedWarTarget(target, definition.canonical_key) &&
         !ValidUnavailableTarget(target, definition.canonical_key))) {
      return false;
    }
  } else if (!ValidTargetEnvelope(target) || target.raw_type_index != 0 ||
             target.type_key_status !=
                 game::PendingCharacterInteractionSemanticStatusV1::absent ||
             target.type_key.has_value() || !target.type_key_reason.empty() ||
             target.typed_identity_status !=
                 game::PendingCharacterInteractionSemanticStatusV1::absent ||
             target.typed_identity.has_value() ||
             !target.typed_identity_reason.empty()) {
    return false;
  }
  std::int32_t selected_count = 0;
  for (std::size_t index = 0; index < options.rows.size(); ++index) {
    const auto &row = options.rows[index];
    if (row.native_index != static_cast<std::int32_t>(index) ||
        row.numeric_flag_identifier < 0 ||
        row.canonical_flag_status !=
            game::PendingCharacterInteractionSemanticStatusV1::unavailable ||
        row.canonical_flag_key.has_value() ||
        row.canonical_flag_reason !=
            "numeric_flag_identifier_string_mapping_not_closed") {
      return false;
    }
    selected_count += row.selected ? 1 : 0;
  }
  if (options.exclusive && selected_count > 1) {
    return false;
  }
  if (routing.auto_accept_notification) {
    if (context.legality.accept.allowed || context.legality.reject.allowed ||
        context.legality.block.allowed ||
        !context.legality.acknowledge.allowed) {
      return false;
    }
  } else if (context.legality.acknowledge.allowed) {
    return false;
  }
  std::size_t reason_index = 0;
  const bool target_typed_identity_ready =
      !target.present ||
      target.typed_identity_status ==
          game::PendingCharacterInteractionSemanticStatusV1::available;
  if (target.present && !target_typed_identity_ready &&
      (ready.not_ready_reasons.empty() ||
       ready.not_ready_reasons[reason_index++] !=
           (target.typed_identity_reason ==
                    "generic_scope_payload_identity_not_closed"
                ? "target_generic_scope_payload_identity_not_closed"
                : target.typed_identity_reason))) {
    return false;
  }
  const bool special_binding_available =
      terms.special_war_binding.status ==
      game::PendingCharacterInteractionSemanticStatusV1::available;
  if (!special_binding_available &&
      (ready.not_ready_reasons.size() <= reason_index ||
       ready.not_ready_reasons[reason_index++] !=
           terms.special_war_binding.reason)) {
    return false;
  }
  const bool exact_reasons =
      ready.not_ready_reasons.size() == reason_index + 3U &&
      ready.not_ready_reasons[reason_index] ==
          "special_outcome_terms_unavailable" &&
      ready.not_ready_reasons[reason_index + 1U] ==
          "structured_exchanges_unavailable" &&
      ready.not_ready_reasons[reason_index + 2U] ==
          "structured_effect_preview_unavailable";
  return exact_reasons && ready.stable_definition_ready && ready.roles_ready &&
         ready.target_type_key_ready &&
         ready.target_typed_identity_ready == target_typed_identity_ready &&
         ready.send_options_ready && ready.routing_ready &&
         ready.deadline_ready && ready.auto_accept_ready &&
         ready.reply_legality_ready && ready.generic_costs_ready &&
         ready.special_war_binding_ready == special_binding_available &&
         !ready.special_outcome_terms_ready && !ready.structured_terms_ready &&
         ready.same_frame_ready && !ready.interaction_semantic_decision_ready;
}

void AppendOptionalString(std::string &output,
                          const std::optional<std::string> &value) {
  if (value.has_value()) {
    AppendJsonString(output, *value);
  } else {
    output += "null";
  }
}

void AppendOptionalReason(std::string &output, std::string_view value) {
  if (value.empty()) {
    output += "null";
  } else {
    AppendJsonString(output, value);
  }
}

void AppendLegality(
    std::string &output,
    const game::PendingCharacterInteractionLegalityV1 &legality) {
  output += "{\"status\":";
  AppendJsonString(output, SemanticStatusName(legality.status));
  output += ",\"allowed\":";
  output += legality.allowed ? "true" : "false";
  output += ",\"reason\":";
  AppendOptionalReason(output, legality.reason);
  output.push_back('}');
}

void AppendUnavailableTerm(
    std::string &output,
    const game::PendingCharacterInteractionUnavailableTermV1 &term) {
  output += "{\"status\":";
  AppendJsonString(output, SemanticStatusName(term.status));
  output += ",\"value\":null,\"reason\":";
  AppendOptionalReason(output, term.reason);
  output.push_back('}');
}

void AppendStructuredCosts(
    std::string &output,
    const game::PendingCharacterInteractionStructuredCostsV1 &costs) {
  output += "{\"status\":";
  AppendJsonString(output, SemanticStatusName(costs.status));
  output += ",\"value\":{\"raw_scale\":";
  output += SignedNumber(costs.raw_scale);
  output += ",\"payer_role\":";
  AppendJsonString(output, costs.payer_role);
  output += ",\"application_timing\":";
  AppendJsonString(output, costs.application_timing);
  output += ",\"pending_payment_state\":";
  AppendJsonString(output, costs.pending_payment_state);
  output += ",\"entries\":[";
  for (std::size_t index = 0; index < costs.entries.size(); ++index) {
    if (index != 0) {
      output.push_back(',');
    }
    output += "{\"resource_key\":";
    AppendJsonString(output, costs.entries[index].resource_key);
    output += ",\"raw\":";
    output += SignedNumber(costs.entries[index].raw);
    output.push_back('}');
  }
  output += "]},\"reason\":null}";
}

void AppendSpecialWarBinding(
    std::string &output,
    const game::PendingCharacterInteractionSpecialWarBindingV1 &binding) {
  output += "{\"status\":";
  AppendJsonString(output, SemanticStatusName(binding.status));
  output += ",\"value\":";
  if (binding.status !=
      game::PendingCharacterInteractionSemanticStatusV1::available) {
    output += "null,\"reason\":";
    AppendOptionalReason(output, binding.reason);
    output.push_back('}');
    return;
  }
  output += "{\"special_interaction_kind\":";
  AppendJsonString(output, binding.special_interaction_kind);
  output += ",\"absolute_outcome\":";
  AppendJsonString(output, binding.absolute_outcome);
  output += ",\"war_id\":";
  output += SignedNumber(binding.war_id);
  output += ",\"actor_war_role\":";
  AppendJsonString(output, binding.actor_war_role);
  output += ",\"recipient_war_role\":";
  AppendJsonString(output, binding.recipient_war_role);
  output += ",\"binding_source\":";
  AppendJsonString(output, binding.binding_source);
  output += "},\"reason\":null}";
}

std::string TargetEnvelopeHex(const std::array<std::uint8_t, 16> &bytes) {
  constexpr char hex[] = "0123456789abcdef";
  std::string output;
  output.resize(bytes.size() * 2U);
  for (std::size_t index = 0; index < bytes.size(); ++index) {
    output[index * 2U] = hex[(bytes[index] >> 4U) & 0x0FU];
    output[index * 2U + 1U] = hex[bytes[index] & 0x0FU];
  }
  return output;
}

} // namespace

std::string SerializePendingCharacterInteractionContextV1(
    const game::PendingCharacterInteractionContextV1 &context) {
  if (context.snapshot_revision == 0) {
    return {};
  }
  const bool available =
      context.status ==
      game::PendingCharacterInteractionContextStatusV1::available;
  if ((available && !ValidAvailable(context)) ||
      (!available && !ValidFailure(context))) {
    return {};
  }

  std::string output;
  output.reserve(8'192);
  output += "{\"schema\":\"pending-character-interaction-context-v1\","
            "\"schema_version\":1,\"status\":";
  AppendJsonString(output, StatusName(context.status));
  output += ",\"snapshot_revision\":";
  output += Number(context.snapshot_revision);
  output += ",\"date_raw\":";
  output += SignedNumber(context.date_raw);
  output += ",\"pending_interaction_id\":";
  output += SignedNumber(context.pending_interaction_id);
  output += ",\"reason\":";
  AppendOptionalReason(output, context.reason);
  output +=
      ",\"build\":{\"version\":\"1.19.0.6\","
      "\"exe_sha256\":"
      "\"2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86\"},"
      "\"definition\":";
  if (!available) {
    output += "null,\"roles\":null,\"target\":null,"
              "\"send_options\":null,\"routing\":null,"
              "\"deadline\":null,\"auto_accept\":null";
  } else {
    const auto &definition = *context.definition;
    output += "{\"canonical_key\":";
    AppendJsonString(output, definition.canonical_key);
    output += ",\"deterministic_key_hash\":";
    output += Number(definition.deterministic_key_hash);
    output += ",\"runtime_ordinal\":";
    output += SignedNumber(definition.runtime_ordinal);
    output += "},\"roles\":{";
    const auto &roles = *context.roles;
    output += "\"actor_character_id\":";
    output += SignedNumber(roles.actor_character_id);
    output += ",\"recipient_character_id\":";
    output += SignedNumber(roles.recipient_character_id);
    output += ",\"secondary_actor_character_id\":";
    output += SignedNumber(roles.secondary_actor_character_id);
    output += ",\"secondary_recipient_character_id\":";
    output += SignedNumber(roles.secondary_recipient_character_id);
    output += ",\"intermediary_character_id\":";
    output += SignedNumber(roles.intermediary_character_id);
    output += "},\"target\":{";
    const auto &target = *context.target;
    output += "\"present\":";
    output += target.present ? "true" : "false";
    output += ",\"raw_type_index\":";
    output += Number(target.raw_type_index);
    output += ",\"raw_16_bytes_hex\":";
    AppendJsonString(output, TargetEnvelopeHex(target.raw_envelope));
    output += ",\"type_key_status\":";
    AppendJsonString(output, SemanticStatusName(target.type_key_status));
    output += ",\"type_key\":";
    AppendOptionalString(output, target.type_key);
    output += ",\"type_key_reason\":";
    AppendOptionalReason(output, target.type_key_reason);
    output += ",\"typed_identity_status\":";
    AppendJsonString(output, SemanticStatusName(target.typed_identity_status));
    output += ",\"typed_identity\":";
    AppendOptionalString(output, target.typed_identity);
    output += ",\"typed_identity_reason\":";
    AppendOptionalReason(output, target.typed_identity_reason);
    output += "},\"send_options\":{";
    const auto &options = *context.send_options;
    output += "\"exclusive\":";
    output += options.exclusive ? "true" : "false";
    output += ",\"definition_count\":";
    output += SignedNumber(options.definition_count);
    output += ",\"context_count\":";
    output += SignedNumber(options.context_count);
    output += ",\"rows\":[";
    for (std::size_t index = 0; index < options.rows.size(); ++index) {
      if (index != 0) {
        output.push_back(',');
      }
      const auto &row = options.rows[index];
      output += "{\"native_index\":";
      output += SignedNumber(row.native_index);
      output += ",\"numeric_flag_identifier\":";
      output += SignedNumber(row.numeric_flag_identifier);
      output += ",\"selected\":";
      output += row.selected ? "true" : "false";
      output += ",\"is_shown\":";
      output += row.is_shown ? "true" : "false";
      output += ",\"is_valid\":";
      output += row.is_valid ? "true" : "false";
      output += ",\"canonical_flag_status\":";
      AppendJsonString(output, SemanticStatusName(row.canonical_flag_status));
      output += ",\"canonical_flag_key\":";
      AppendOptionalString(output, row.canonical_flag_key);
      output += ",\"canonical_flag_reason\":";
      AppendOptionalReason(output, row.canonical_flag_reason);
      output.push_back('}');
    }
    output += "]},\"routing\":{";
    const auto &routing = *context.routing;
    output += "\"kind\":";
    output += SignedNumber(routing.kind);
    output += ",\"played_character_id\":";
    output += SignedNumber(routing.played_character_id);
    output += ",\"current_responder_role\":";
    AppendJsonString(output, routing.current_responder_role);
    output += ",\"reply_execution_channel\":";
    AppendJsonString(output, routing.reply_execution_channel);
    output += ",\"local_route\":";
    output += routing.local_route ? "true" : "false";
    output += ",\"auto_accept_notification\":";
    output += routing.auto_accept_notification ? "true" : "false";
    output += "},\"deadline\":{";
    const auto &deadline = *context.deadline;
    output += "\"age_days\":";
    output += SignedNumber(deadline.age_days);
    output += ",\"expiration_days\":";
    output += SignedNumber(deadline.expiration_days);
    output += ",\"remaining_days\":";
    output += SignedNumber(deadline.remaining_days);
    output += ",\"expiry_boundary_status\":";
    AppendJsonString(output, deadline.expiry_boundary_status);
    output += "},\"auto_accept\":{";
    const auto &auto_accept = *context.auto_accept;
    output += "\"status\":";
    AppendJsonString(output, SemanticStatusName(auto_accept.status));
    output += ",\"value\":";
    output += auto_accept.value ? "true" : "false";
    output += ",\"reason\":";
    AppendOptionalReason(output, auto_accept.reason);
    output.push_back('}');
  }

  output += ",\"legality\":{\"accept\":";
  AppendLegality(output, context.legality.accept);
  output += ",\"reject\":";
  AppendLegality(output, context.legality.reject);
  output += ",\"block\":";
  AppendLegality(output, context.legality.block);
  output += ",\"acknowledge\":";
  AppendLegality(output, context.legality.acknowledge);
  output += "},\"terms\":";
  if (!available) {
    output += "null";
  } else {
    const auto &terms = *context.terms;
    output += "{\"special_data_present\":";
    output += terms.special_data_present ? "true" : "false";
    output += ",\"special_war_binding\":";
    AppendSpecialWarBinding(output, terms.special_war_binding);
    output += ",\"structured_costs\":";
    AppendStructuredCosts(output, terms.structured_costs);
    output += ",\"structured_exchanges\":";
    AppendUnavailableTerm(output, terms.structured_exchanges);
    output += ",\"structured_effect_preview\":";
    AppendUnavailableTerm(output, terms.structured_effect_preview);
    output += ",\"recipient_ai_acceptance_score\":";
    AppendUnavailableTerm(output, terms.recipient_ai_acceptance_score);
    output += ",\"recipient_ai_final_decision\":";
    AppendUnavailableTerm(output, terms.recipient_ai_final_decision);
    output.push_back('}');
  }
  const auto &ready = context.readiness;
  output += ",\"readiness\":{\"stable_definition_ready\":";
  output += ready.stable_definition_ready ? "true" : "false";
  output += ",\"roles_ready\":";
  output += ready.roles_ready ? "true" : "false";
  output += ",\"target_type_key_ready\":";
  output += ready.target_type_key_ready ? "true" : "false";
  output += ",\"target_typed_identity_ready\":";
  output += ready.target_typed_identity_ready ? "true" : "false";
  output += ",\"send_options_ready\":";
  output += ready.send_options_ready ? "true" : "false";
  output += ",\"routing_ready\":";
  output += ready.routing_ready ? "true" : "false";
  output += ",\"deadline_ready\":";
  output += ready.deadline_ready ? "true" : "false";
  output += ",\"auto_accept_ready\":";
  output += ready.auto_accept_ready ? "true" : "false";
  output += ",\"reply_legality_ready\":";
  output += ready.reply_legality_ready ? "true" : "false";
  output += ",\"generic_costs_ready\":";
  output += ready.generic_costs_ready ? "true" : "false";
  output += ",\"special_war_binding_ready\":";
  output += ready.special_war_binding_ready ? "true" : "false";
  output += ",\"special_outcome_terms_ready\":";
  output += ready.special_outcome_terms_ready ? "true" : "false";
  output += ",\"structured_terms_ready\":";
  output += ready.structured_terms_ready ? "true" : "false";
  output += ",\"same_frame_ready\":";
  output += ready.same_frame_ready ? "true" : "false";
  output += ",\"interaction_semantic_decision_ready\":";
  output += ready.interaction_semantic_decision_ready ? "true" : "false";
  output += ",\"not_ready_reasons\":[";
  for (std::size_t index = 0; index < ready.not_ready_reasons.size(); ++index) {
    if (index != 0) {
      output.push_back(',');
    }
    AppendJsonString(output, ready.not_ready_reasons[index]);
  }
  output += "]},\"provenance\":{"
            "\"backend_id\":\"ck3-1.19.0.6-native-pending-character-"
            "interaction-context-v1\","
            "\"pending_storage_slot_rva\":\"0x57BF1C8\","
            "\"character_storage_slot_rva\":\"0x570C130\","
            "\"expiration_days_rva\":\"0x570F528\","
            "\"local_routing_predicate_rva\":\"0x1266BA0\","
            "\"reply_validator_rva\":\"0x26B3540\","
            "\"auto_accept_trigger_evaluator_rva\":\"0x334C510\","
            "\"cost_evaluator_rva\":\"0x2CDB7B0\","
            "\"common_war_relation_rva\":\"0x2610840\","
            "\"target_type_registry_getter_rva\":\"0x33C52B0\","
            "\"target_type_registry_rva\":\"0x4FFE290\","
            "\"script_identifier_name_rva\":\"0x3B58970\","
            "\"reply_primary_vtable_rva\":\"0x4082930\","
            "\"reply_secondary_vtable_rva\":\"0x4082900\","
            "\"war_victory_special_vtable_rva\":\"0x428EEA8\","
            "\"war_white_peace_special_vtable_rva\":\"0x428EF88\","
            "\"war_defeat_special_vtable_rva\":\"0x428EF18\"}}";
  return output;
}

} // namespace xar::ck3_11906
