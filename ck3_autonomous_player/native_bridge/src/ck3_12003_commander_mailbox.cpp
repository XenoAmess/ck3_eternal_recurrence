#include "xar_bridge/ck3_12003_commander_mailbox.hpp"
#include "xar_bridge/ck3_12004_combat.hpp"
#include "xar_bridge/ck3_12004_army.hpp"
#include "xar_bridge/ck3_12004_province.hpp"

#include "xar_bridge/ck3_12003_adapter.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12004_army_support.hpp"
#include "xar_bridge/ck3_12003_commander_target_roll_serializer.hpp"
#include "xar_bridge/ck3_12003_commander_target_roll.hpp"
#include "xar_bridge/ck3_12003_current_commander_martial_serializer.hpp"
#include "xar_bridge/ck3_12004_current_commander_base_quality.hpp"
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

std::string NullableInteger(const std::optional<std::int32_t> &value) {
  return value ? std::to_string(*value) : "null";
}

std::string_view RouteReadStatus(game::ArmyRouteReadStatus value) noexcept {
  switch (value) {
  case game::ArmyRouteReadStatus::not_attempted: return "not_attempted";
  case game::ArmyRouteReadStatus::complete_empty: return "complete_empty";
  case game::ArmyRouteReadStatus::complete_nonempty: return "complete_nonempty";
  case game::ArmyRouteReadStatus::target_only: return "target_only";
  case game::ArmyRouteReadStatus::invalid_header: return "invalid_header";
  case game::ArmyRouteReadStatus::unresolved_entry: return "unresolved_entry";
  }
  return "not_attempted";
}

std::string SerializeMovementRate(const NativeMovementRateSnapshot &rate,
                                  std::string_view native_getter_rva) {
  return "{\"status\":" + Quote(rate.status) +
      ",\"raw\":" +
      (rate.status == "available" && rate.raw
           ? std::to_string(*rate.raw) : std::string("null")) +
      ",\"scale\":" + std::to_string(rate.scale) +
      ",\"unavailable_reason\":" + NullableReason(rate.unavailable_reason) +
      ",\"native_getter_rva\":" + Quote(native_getter_rva) + '}';
}

std::string SerializeCurrentMovementSpeed(
    const ArmyCurrentMovementSpeedSnapshot &movement,
    std::uint64_t snapshot_revision, std::int32_t date_raw) {
  const bool observed = movement.context_observable;
  return "{\"schema\":\"ck3_12003_army_current_movement_speed_v1\","
      "\"source\":\"native_selected_cunit_movement_rates\","
      "\"context_observable\":" + std::string(observed ? "true" : "false") +
      ",\"snapshot_revision\":" + std::to_string(snapshot_revision) +
      ",\"date_raw\":" + std::to_string(date_raw) +
      ",\"public_cunit_id\":" +
      (observed ? NullableId(movement.public_cunit_id) : std::string("null")) +
      ",\"native_carmy_id\":" +
      (observed ? NullableId(movement.native_carmy_id) : std::string("null")) +
      ",\"owner_character_id\":" +
      (observed ? NullableId(movement.owner_character_id) : std::string("null")) +
      ",\"current_commander_character_id\":" +
      (observed ? NullableId(movement.current_commander_character_id)
                : std::string("null")) +
      ",\"current_province_id\":" +
      (observed ? NullableInteger(movement.current_province_id)
                : std::string("null")) +
      ",\"move_target_province_id\":" +
      (observed ? NullableInteger(movement.move_target_province_id)
                : std::string("null")) +
      ",\"route_source_count\":" +
      (observed ? NullableInteger(movement.route_source_count)
                : std::string("null")) +
      ",\"army_state_code\":" +
      (observed ? std::to_string(movement.army_state_code)
                : std::string("null")) +
      ",\"army_state\":" +
      (observed ? Quote(movement.army_state) : std::string("null")) +
      ",\"in_combat\":" +
      (observed ? std::string(movement.in_combat ? "true" : "false")
                : std::string("null")) +
      ",\"retreating\":" +
      (observed ? std::string(movement.retreating ? "true" : "false")
                : std::string("null")) +
      ",\"route_read_status\":" + Quote(RouteReadStatus(movement.route_read_status)) +
      ",\"land\":" + SerializeMovementRate(movement.land, "0x24AA940") +
      ",\"naval\":" + SerializeMovementRate(movement.naval, "0x24AAC00") +
      ",\"current_edge\":" +
      SerializeMovementRate(movement.current_edge, "0x24AB5C0") + '}';
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
  if (envelope != &query.envelope || query.completed) {
    return false;
  }
  const bool actual4 = game::IsCk3_12004Descriptor(envelope->game->descriptor());
  if (!actual4 && !game::IsCk3_12003Descriptor(envelope->game->descriptor()))
    return false;
  const auto bindings = actual4
      ? ck3_12004::BindCommanderImage12004(
            query.image_base, envelope->game->descriptor().executable_sha256)
      : BindCommanderImage(
            query.image_base, envelope->game->descriptor().executable_sha256);
  query.read_result = ReadArmyCommanderCandidates(
      bindings, envelope->expected_snapshot, query.army_id,
      query.observation);
  if (query.target_province_id.has_value()) {
    const auto target_bindings = actual4
        ? ck3_12004::BindCommanderTargetRollImage12004(
              query.image_base, envelope->game->descriptor().executable_sha256,
              ck3_12004::BindProvinceImage12004(
                  query.image_base, envelope->game->descriptor().executable_sha256,
                  ck3_12004::BindArmyImage12004(
                      query.image_base, envelope->game->descriptor().executable_sha256)),
              ck3_12004::BindCombatImage12004(
                  query.image_base, envelope->game->descriptor().executable_sha256))
        : BindCommanderTargetRollImage(
              query.image_base, envelope->game->descriptor().executable_sha256);
    ReadArmyCommanderCandidateTargetRollBounds(
        target_bindings, *query.target_province_id, query.observation);
  }
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
      (observation.target_province_id
           ? ",\"target_province_id\":" +
                 std::to_string(*observation.target_province_id)
           : std::string{}) +
      ",\"eligibility_mode\":" + std::to_string(observation.eligibility_mode) +
      ",\"collection_filter_now\":false,\"collection_allow_guests\":true,"
      "\"current_commander\":{\"status\":" +
      Quote(observation.current_commander_status) +
      ",\"character_id\":" +
      NullableId(observation.current_commander_character_id) +
      ",\"unavailable_reason\":" +
      NullableReason(observation.current_commander_unavailable_reason) +
      (observation.current_total_martial
           ? ",\"current_total_martial\":" +
                 SerializeCurrentCommanderTotalMartial(
                     *observation.current_total_martial)
           : std::string{}) +
      (observation.current_native_ai_base_quality
           ? ",\"current_native_ai_base_quality\":" +
                 ck3_12004::SerializeCurrentCommanderNativeBaseQuality(
                     *observation.current_native_ai_base_quality)
           : std::string{}) +
      "},\"current_movement_speed\":" +
      SerializeCurrentMovementSpeed(observation.current_movement_speed,
                                    snapshot_revision, date_raw) +
      ",\"candidate_collection_complete\":" +
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
        NullableReason(candidate.unavailable_reason);
    if (candidate.target_roll_bounds) {
      out += ",\"target_roll_bounds\":" +
          SerializeCommanderCandidateTargetRollBounds(*candidate.target_roll_bounds);
    }
    out += '}';
  }
  out += "],\"unavailable_reason\":" +
      NullableReason(observation.unavailable_reason) + "}}";
  return out;
}

} // namespace xar::ck3_12003
