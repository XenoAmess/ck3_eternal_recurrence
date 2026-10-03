#include "xar_bridge/ck3_12003_commander_mailbox.hpp"

#include "xar_bridge/ck3_12003_adapter.hpp"
#include "xar_bridge/public_unit_id.hpp"

namespace xar::ck3_12003 {
namespace {

std::string Quote(std::string_view value) {
  constexpr char hex[] = "0123456789abcdef";
  std::string out = "\"";
  for (const unsigned char byte : value) {
    if (byte == '"' || byte == '\\') {
      out += '\\';
      out += static_cast<char>(byte);
    } else if (byte < 0x20) {
      out += "\\u00";
      out += hex[byte >> 4];
      out += hex[byte & 15];
    } else {
      out += static_cast<char>(byte);
    }
  }
  return out + '"';
}

std::string NullableId(std::int32_t value) {
  return value < 0 ? "null" : std::to_string(value);
}

std::string NullableReason(std::string_view value) {
  return value.empty() ? "null" : Quote(value);
}

std::string_view ReadStatus(CommanderCandidatesReadResult value) noexcept {
  switch (value) {
  case CommanderCandidatesReadResult::available: return "available";
  case CommanderCandidatesReadResult::partial: return "partial";
  case CommanderCandidatesReadResult::unavailable: return "unavailable";
  }
  return "unavailable";
}

} // namespace

bool ExecuteArmyCommanderCandidatesMailbox(
    void *opaque, const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *envelope = static_cast<ck3_12002::QueryMailboxEnvelope *>(opaque);
  if (envelope == nullptr || envelope->typed_context == nullptr ||
      !ck3_12002::EnterQueryMailbox(
          *envelope, stamp, &ExecuteArmyCommanderCandidatesMailbox)) {
    return false;
  }
  auto &query =
      *static_cast<ArmyCommanderMailboxContext *>(envelope->typed_context);
  if (envelope != &query.envelope || query.completed ||
      !game::IsCk3_12003Descriptor(envelope->game->descriptor())) {
    return false;
  }
  const auto bindings = BindCommanderImage(
      query.image_base, envelope->game->descriptor().executable_sha256);
  query.read_result = ReadArmyCommanderCandidates(
      bindings, envelope->expected_snapshot, query.army_id,
      query.observation);
  // An unavailable native result is a completed read, not a transport fault.
  query.completed = true;
  return ck3_12002::FinishQueryMailbox(*envelope);
}

std::string SerializeArmyCommanderCandidates(
    const ArmyCommanderCandidatesSnapshot &observation,
    CommanderCandidatesReadResult read_result, std::uint64_t query_sequence,
    std::uint64_t snapshot_revision, std::int32_t date_raw,
    std::string_view step) {
  std::string out = "{\"step\":" + Quote(step) +
      ",\"accepted\":true,\"status\":\"completed\",\"read_only\":true,"
      "\"query_sequence\":" + std::to_string(query_sequence) +
      ",\"snapshot_revision\":" + std::to_string(snapshot_revision) +
      ",\"date_raw\":" + std::to_string(date_raw) +
      ",\"army_commander_candidates\":{"
      "\"schema\":\"ck3_12003_army_commander_candidates_v1\",\"status\":" +
      Quote(ReadStatus(read_result)) +
      ",\"snapshot_revision\":" + std::to_string(snapshot_revision) +
      ",\"date_raw\":" + std::to_string(date_raw) +
      ",\"army_id\":" + NullableId(observation.army_id) +
      ",\"native_carmy_id\":" + NullableId(observation.native_carmy_id) +
      ",\"owner_character_id\":" + NullableId(observation.owner_character_id) +
      ",\"eligibility_mode\":" + std::to_string(observation.eligibility_mode) +
      ",\"collection_filter_now\":false,\"collection_allow_guests\":true,"
      "\"current_commander\":{\"status\":" +
      Quote(observation.current_commander_status) +
      ",\"character_id\":" +
      NullableId(observation.current_commander_character_id) +
      ",\"unavailable_reason\":" +
      NullableReason(observation.current_commander_unavailable_reason) +
      "},\"candidate_collection_complete\":" +
      (observation.candidate_collection_complete ? "true" : "false") +
      ",\"candidate_source_count\":" +
      std::to_string(observation.candidate_source_count) +
      ",\"candidates\":[";
  bool first = true;
  for (const auto &candidate : observation.candidates) {
    if (!first) out += ',';
    first = false;
    out += "{\"character_id\":" + NullableId(candidate.character_id) +
        ",\"available\":" + (candidate.available ? "true" : "false") +
        ",\"final_eligibility_observable\":" +
        (candidate.final_eligibility_observable ? "true" : "false") +
        ",\"can_assign\":" +
        (candidate.final_eligibility_observable
             ? std::string(candidate.can_assign ? "true" : "false")
             : std::string("null")) +
        ",\"quality_observable\":" +
        (candidate.quality_observable ? "true" : "false") +
        ",\"native_ai_base_quality\":" +
        (candidate.quality_observable
             ? std::to_string(candidate.native_ai_base_quality) : "null") +
        ",\"generic_advantage_points\":" +
        (candidate.quality_observable
             ? std::to_string(candidate.generic_advantage_points) : "null") +
        ",\"siege_phase_time_modifier_raw\":" +
        (candidate.siege_phase_time_modifier_observable
             ? std::to_string(candidate.siege_phase_time_modifier_raw) : "null") +
        ",\"unavailable_reason\":" +
        NullableReason(candidate.unavailable_reason) + '}';
  }
  out += "],\"unavailable_reason\":" +
      NullableReason(observation.unavailable_reason) + "}}";
  return out;
}

} // namespace xar::ck3_12003
