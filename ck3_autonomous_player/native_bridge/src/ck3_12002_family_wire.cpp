#include "xar_bridge/ck3_12002_family_wire.hpp"

#include <algorithm>
#include <array>
#include <charconv>

namespace xar::ck3_12002 {
#if defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)
namespace {
std::string Number(std::uint64_t value) {
  std::array<char, 32> buffer{};
  const auto result =
      std::to_chars(buffer.data(), buffer.data() + buffer.size(), value);
  if (result.ec != std::errc{}) {
    return "0";
  }
  return std::string(buffer.data(), result.ptr);
}

std::string SignedNumber(std::int64_t value) {
  std::array<char, 32> buffer{};
  const auto result =
      std::to_chars(buffer.data(), buffer.data() + buffer.size(), value);
  if (result.ec != std::errc{}) {
    return "0";
  }
  return std::string(buffer.data(), result.ptr);
}

void AppendJsonString(std::string &result, std::string_view value) {
  constexpr char hex[] = "0123456789ABCDEF";
  result += '"';
  for (const unsigned char character : value) {
    if (character == '"' || character == '\\') {
      result += '\\';
      result += static_cast<char>(character);
    } else if (character < 0x20U) {
      result += "\\u00";
      result += hex[(character >> 4U) & 0x0FU];
      result += hex[character & 0x0FU];
    } else {
      result += static_cast<char>(character);
    }
  }
  result += '"';
}

std::string_view MarriageCandidateAlliancePrivateFailureKeyV1(
    xar::ck3_11906::MarriageCandidateAlliancePrivateFailureV1 failure) {
  using Failure = xar::ck3_11906::MarriageCandidateAlliancePrivateFailureV1;
  switch (failure) {
  case Failure::none: return "none";
  case Failure::binding_unavailable: return "binding_unavailable";
  case Failure::frame_changed: return "frame_changed";
  case Failure::identity_changed: return "identity_changed";
  case Failure::role_changed: return "role_changed";
  case Failure::final_legality_changed: return "final_legality_changed";
  case Failure::projection_unavailable: return "projection_unavailable";
  case Failure::outcome_unavailable: return "outcome_unavailable";
  case Failure::heir_relationship_unavailable:
    return "heir_relationship_unavailable";
  case Failure::lineage_unavailable: return "lineage_unavailable";
  case Failure::sex_selector_unavailable: return "sex_selector_unavailable";
  case Failure::selected_option_unavailable:
    return "selected_option_unavailable";
  case Failure::generic_cost_unavailable:
    return "generic_cost_unavailable";
  }
  return "unknown";
}

std::string_view MarriageCandidateAllianceCoreFailureKeyV1(
    xar::bridge::MarriageCandidateAllianceProjectionFailureV1 failure) {
  using Failure = xar::bridge::MarriageCandidateAllianceProjectionFailureV1;
  switch (failure) {
  case Failure::none: return "none";
  case Failure::exact_build_not_admitted: return "exact_build_not_admitted";
  case Failure::binding_unavailable: return "binding_unavailable";
  case Failure::signature_mismatch: return "signature_mismatch";
  case Failure::invalid_input: return "invalid_input";
  case Failure::context_roles_mismatch: return "context_roles_mismatch";
  case Failure::option_id_unavailable: return "option_id_unavailable";
  case Failure::native_vector_invalid: return "native_vector_invalid";
  case Failure::row_identity_mismatch: return "row_identity_mismatch";
  }
  return "unknown";
}

std::string_view MarriageCandidateOutcomeFailureKeyV1(
    xar::bridge::MarriageNativeOutcomeClassifierFailureV1 failure) {
  using Failure = xar::bridge::MarriageNativeOutcomeClassifierFailureV1;
  switch (failure) {
  case Failure::none: return "none";
  case Failure::exact_build_not_admitted: return "exact_build_not_admitted";
  case Failure::binding_mismatch: return "binding_mismatch";
  case Failure::signature_mismatch: return "signature_mismatch";
  case Failure::memory_reader_unavailable: return "memory_reader_unavailable";
  case Failure::invalid_input: return "invalid_input";
  case Failure::secondary_pair_identity_mismatch:
    return "secondary_pair_identity_mismatch";
  case Failure::runtime_threshold_unavailable:
    return "runtime_threshold_unavailable";
  case Failure::option_identifier_unavailable:
    return "option_identifier_unavailable";
  case Failure::outcome_sample_drift: return "outcome_sample_drift";
  }
  return "unknown";
}

} // namespace

std::string SerializeFamilyAllianceFrameV1(std::string_view request_id,
    std::uint64_t revision, std::uint64_t legality_query_sequence,
    std::span<const FamilyAllianceWireRowV1> rows, std::string_view step) {
  std::string result =
      "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":";
  AppendJsonString(result, request_id);
  result += ",\"ok\":true,\"result\":{\"step\":";
  AppendJsonString(result, step);
  result += ",\"accepted\":true,\"private_build\":true,\"read_only\":true,"
            "\"advertised\":false,\"native_revision\":";
  result += Number(revision);
  result += ",\"legality_query_sequence\":";
  result += Number(legality_query_sequence);
  result += ",\"status\":";
  const bool all_available = std::all_of(
      rows.begin(), rows.end(),
      [](const auto &row) {
        return row.read.failure == xar::ck3_11906::
                                  MarriageCandidateAlliancePrivateFailureV1::none;
      });
  AppendJsonString(result, all_available ? "available" : "unavailable");
  result += ",\"rows\":[";
  for (std::size_t index = 0; index < rows.size(); ++index) {
    if (index != 0) result += ',';
    const auto &observed = rows[index].observed;
    const auto &read = rows[index].read;
    result += "{\"actor_character_id\":";
    result += SignedNumber(observed.played_character_id);
    result += ",\"heir_character_id\":";
    result += SignedNumber(observed.subject_character_id);
    result += ",\"candidate_character_id\":";
    result += SignedNumber(observed.candidate_character_id);
    result += ",\"recipient_character_id\":";
    result += SignedNumber(observed.recipient_matchmaker_character_id);
    result += ",\"status\":";
    const bool available = read.failure == xar::ck3_11906::
                                               MarriageCandidateAlliancePrivateFailureV1::none;
    AppendJsonString(result, available ? "available" : "unavailable");
    result += ",\"requested_matrilineal_option\":";
    result += read.requested_matrilineal_option ? "true" : "false";
    result += ",\"selected_option_readback\":";
    result += read.requested_matrilineal_option
                  ? (read.selected_option_readback ? "true" : "false")
                  : "null";
    result += ",\"final_legality_sampled\":";
    result += read.final_legality_sampled ? "true" : "false";
    result += ",\"complete_can_send\":";
    result += read.final_legality_sampled
                  ? (read.complete_can_send ? "true" : "false") : "null";
    result += ",\"recipient_ai_accept_raw\":";
    result += read.final_legality_sampled && read.recipient_acceptance_ready
                  ? SignedNumber(read.recipient_ai_accept_raw) : "null";
    result += ",\"recipient_answer_status_raw\":";
    result += read.final_legality_sampled && read.recipient_acceptance_ready
                  ? Number(read.recipient_answer_status_raw) : "null";
    result += ",\"generic_costs\":";
    if (!available) {
      result += "null";
    } else {
      constexpr std::array<std::string_view, 10> keys{
          "gold_raw", "prestige_raw", "piety_raw", "renown_raw",
          "influence_raw", "herd_raw", "treasury_raw",
          "treasury_or_gold_raw", "merit_raw", "barter_goods_raw"};
      result += "{\"raw_scale\":100000,\"payer_role\":\"actor\","
                "\"application_timing\":\"on_send\"";
      for (std::size_t slot = 0; slot < keys.size(); ++slot) {
        result += ",\"";
        result += keys[slot];
        result += "\":";
        result += SignedNumber(read.generic_cost_raw[slot]);
      }
      result += '}';
    }
    result += ",\"failure\":";
    AppendJsonString(result,
                     MarriageCandidateAlliancePrivateFailureKeyV1(read.failure));
    result += ",\"projection_failure\":";
    AppendJsonString(result,
                     MarriageCandidateAllianceCoreFailureKeyV1(
                         read.projection_failure));
    result += ",\"outcome_failure\":";
    AppendJsonString(result,
                     MarriageCandidateOutcomeFailureKeyV1(
                         read.outcome_failure));
    result += ",\"predicted_outcome_if_accepted\":";
    if (!available) {
      result += "null";
    } else {
      AppendJsonString(
          result, read.predicted_outcome ==
                          xar::bridge::MarriagePredictedOutcomeV1::marriage
                      ? "marriage"
                      : "betrothal");
    }
    result += ",\"heir_is_adult\":";
    result += available ? (read.heir_is_adult ? "true" : "false") : "null";
    result += ",\"candidate_is_adult\":";
    result += available ? (read.candidate_is_adult ? "true" : "false") : "null";
    result += ",\"heir_adult_measure_raw\":";
    result += available ? SignedNumber(read.heir_adult_measure_raw) : "null";
    result += ",\"candidate_adult_measure_raw\":";
    result += available ? SignedNumber(read.candidate_adult_measure_raw) : "null";
    result += ",\"heir_adult_threshold_raw\":";
    result += available ? SignedNumber(read.heir_adult_threshold_raw) : "null";
    result += ",\"candidate_adult_threshold_raw\":";
    result += available ? SignedNumber(read.candidate_adult_threshold_raw) : "null";
    if (step == kFamilyChildValueWireStepV1 ||
        step == kFamilyAllianceProjectionWireStepV1) {
      const auto append_fertility = [&](std::string_view key,
                                        const auto &fertility) {
        result += ",\"";
        result += key;
        result += "\":";
        if (!available || !fertility.available) {
          result += "null";
        } else {
          result += "{\"source\":\"native_marriage_fertility_input\","
                    "\"extension_present\":";
          result += fertility.extension_present ? "true" : "false";
          result += ",\"native_gate_evaluated\":";
          result += fertility.native_gate_evaluated ? "true" : "false";
          result += ",\"native_gate_allows\":";
          result += fertility.native_gate_evaluated
                        ? (fertility.native_gate_allows ? "true" : "false")
                        : "null";
          result += ",\"effective_raw\":";
          result += SignedNumber(fertility.effective_raw);
          result += '}';
        }
      };
      append_fertility("heir_native_fertility", read.heir_fertility);
      append_fertility("candidate_native_fertility", read.candidate_fertility);
    }
    result += ",\"grand_wedding_option_selected\":";
    result += available ? (read.grand_wedding_option_selected ? "true" : "false")
                        : "null";
    result += ",\"heir_betrothed_character_id\":";
    if (available && read.heir_relationship.betrothed_character_id > 0) {
      result += SignedNumber(
          read.heir_relationship.betrothed_character_id);
    } else {
      result += "null";
    }
    result += ",\"heir_primary_spouse_character_id\":";
    if (available &&
        read.heir_relationship.primary_spouse_character_id > 0) {
      result += SignedNumber(
          read.heir_relationship.primary_spouse_character_id);
    } else {
      result += "null";
    }
    result += ",\"heir_spouse_character_ids\":";
    if (!available) {
      result += "null";
    } else {
      result += '[';
      for (std::size_t spouse_index = 0;
           spouse_index < read.heir_relationship.spouse_character_ids.size();
           ++spouse_index) {
        if (spouse_index != 0) result += ',';
        result += SignedNumber(
            read.heir_relationship.spouse_character_ids[spouse_index]);
      }
      result += ']';
    }
    result += ",\"candidate_betrothed_character_id\":";
    if (available &&
        read.candidate_relationship.betrothed_character_id > 0)
      result += SignedNumber(
          read.candidate_relationship.betrothed_character_id);
    else
      result += "null";
    result += ",\"candidate_primary_spouse_character_id\":";
    if (available &&
        read.candidate_relationship.primary_spouse_character_id > 0)
      result += SignedNumber(
          read.candidate_relationship.primary_spouse_character_id);
    else
      result += "null";
    result += ",\"candidate_spouse_character_ids\":";
    if (!available) {
      result += "null";
    } else {
      result += '[';
      for (std::size_t spouse_index = 0;
           spouse_index < read.candidate_relationship.spouse_character_ids.size();
           ++spouse_index) {
        if (spouse_index != 0) result += ',';
        result += SignedNumber(
            read.candidate_relationship.spouse_character_ids[spouse_index]);
      }
      result += ']';
    }
    result += ",\"played_house_id\":";
    result += available && read.played_lineage.house_id >= 0
                  ? SignedNumber(read.played_lineage.house_id) : "null";
    result += ",\"played_dynasty_id\":";
    result += available && read.played_lineage.dynasty_id >= 0
                  ? SignedNumber(read.played_lineage.dynasty_id) : "null";
    result += ",\"heir_house_id\":";
    result += available && read.heir_lineage.house_id >= 0
                  ? SignedNumber(read.heir_lineage.house_id) : "null";
    result += ",\"heir_dynasty_id\":";
    result += available && read.heir_lineage.dynasty_id >= 0
                  ? SignedNumber(read.heir_lineage.dynasty_id) : "null";
    result += ",\"candidate_house_id\":";
    result += available && read.candidate_lineage.house_id >= 0
                  ? SignedNumber(read.candidate_lineage.house_id) : "null";
    result += ",\"candidate_dynasty_id\":";
    result += available && read.candidate_lineage.dynasty_id >= 0
                  ? SignedNumber(read.candidate_lineage.dynasty_id) : "null";
    result += ",\"heir_sex_selector_raw\":";
    result += available ? Number(read.heir_sex_selector_raw) : "null";
    result += ",\"candidate_sex_selector_raw\":";
    result += available ? Number(read.candidate_sex_selector_raw) : "null";
    result += ",\"effective_matrilineal_if_accepted\":";
    result += available
                  ? (read.effective_matrilineal_if_accepted ? "true" : "false")
                  : "null";
    result += ",\"matrilineal_option_selected\":";
    result += available
                  ? (read.projection.matrilineal_option_selected ? "true" : "false")
                  : "null";
    result += ",\"possible_alliance_pairs\":[";
    if (available) {
      for (std::uint32_t pair_index = 0;
           pair_index < read.projection.pair_count; ++pair_index) {
        if (pair_index != 0) result += ',';
        const auto &pair = read.projection.pairs[pair_index];
        result += "{\"first_character_id\":";
        result += Number(pair.first_character_id);
        result += ",\"second_character_id\":";
        result += Number(pair.second_character_id);
        result += ",\"already_allied\":";
        result += pair.already_allied ? "true" : "false";
        result += ",\"both_have_realm_data\":";
        result += pair.both_have_realm_data ? "true" : "false";
        result += ",\"would_attempt_if_accepted\":";
        result += pair.would_attempt_if_accepted ? "true" : "false";
        result += '}';
      }
    }
    result += "]}";
  }
  result += "]}}";
  return result;
}
#endif
} // namespace xar::ck3_12002
