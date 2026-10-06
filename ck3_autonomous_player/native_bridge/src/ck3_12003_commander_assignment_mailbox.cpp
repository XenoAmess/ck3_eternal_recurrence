#include "xar_bridge/ck3_12003_commander_assignment_mailbox.hpp"

#include "xar_bridge/ck3_12003_adapter.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12004_army_support.hpp"
#include "xar_bridge/ck3_12004_commander_assignment.hpp"
#include "xar_bridge/ck3_12004_commands.hpp"

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

std::string_view StatusName(CommanderAssignmentStatus status) noexcept {
  switch (status) {
  case CommanderAssignmentStatus::submitted: return "submitted_verification_pending";
  case CommanderAssignmentStatus::already_assigned: return "already_assigned";
  case CommanderAssignmentStatus::rejected: return "rejected";
  case CommanderAssignmentStatus::unavailable: return "unavailable";
  }
  return "unavailable";
}

std::string Boolean(bool value) {
  return value ? "true" : "false";
}

} // namespace

bool ExecuteArmyCommanderAssignmentMailbox(
    void *opaque, const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *envelope = static_cast<ck3_12002::QueryMailboxEnvelope *>(opaque);
  if (envelope == nullptr || envelope->typed_context == nullptr ||
      !ck3_12002::EnterQueryMailbox(
          *envelope, stamp, &ExecuteArmyCommanderAssignmentMailbox)) {
    return false;
  }
  auto &action = *static_cast<ArmyCommanderAssignmentMailboxContext *>(
      envelope->typed_context);
  const bool actual4 = game::IsCk3_12004Descriptor(envelope->game->descriptor());
  if (envelope != &action.envelope || action.completed ||
      (!actual4 && !game::IsCk3_12003Descriptor(envelope->game->descriptor()))) {
    return false;
  }
  const auto sha = envelope->game->descriptor().executable_sha256;
  const auto bindings = actual4
      ? ck3_12004::BindCommanderAssignmentImage12004(
            action.image_base, sha,
            ck3_12004::BindCommanderImage12004(action.image_base, sha),
            ck3_12004::BindCommandImage12004(action.image_base, sha))
      : BindCommanderAssignmentImage(action.image_base, sha);
  action.apply_result = ApplyArmyCommanderAssignment(
      bindings, envelope->expected_snapshot, action.army_id,
      action.candidate_character_id, action.observation);
  // Native owned queue submission does not imply the commander is applied.
  action.completed = true;
  return ck3_12002::FinishQueryMailbox(*envelope);
}

std::string SerializeArmyCommanderAssignment(
    const CommanderAssignmentResult &observation,
    CommanderAssignmentStatus status, std::uint64_t command_sequence,
    std::uint64_t snapshot_revision, std::int32_t date_raw,
    std::string_view step) {
  const bool accepted = status == CommanderAssignmentStatus::submitted ||
      status == CommanderAssignmentStatus::already_assigned;
  const auto wire_status = StatusName(status);
  const auto native_status = status == CommanderAssignmentStatus::submitted
      ? std::string_view("submitted") : wire_status;
  std::string out = "{\"step\":" + Quote(step) +
      ",\"accepted\":" + Boolean(accepted) +
      ",\"status\":" + Quote(wire_status) +
      ",\"read_only\":false,\"command_sequence\":" +
      std::to_string(command_sequence) +
      ",\"snapshot_revision\":" + std::to_string(snapshot_revision) +
      ",\"date_raw\":" + std::to_string(date_raw) +
      ",\"army_commander_assignment\":{"
      "\"schema\":\"ck3_12003_army_commander_assignment_v1\",\"status\":" +
      Quote(native_status) +
      ",\"snapshot_revision\":" + std::to_string(snapshot_revision) +
      ",\"date_raw\":" + std::to_string(date_raw) +
      ",\"army_id\":" + NullableId(observation.army_id) +
      ",\"native_carmy_id\":" + NullableId(observation.native_carmy_id) +
      ",\"owner_character_id\":" + NullableId(observation.owner_character_id) +
      ",\"requested_commander_character_id\":" +
      NullableId(observation.requested_commander_character_id) +
      ",\"prior_commander_character_id\":" +
      NullableId(observation.prior_commander_character_id) +
      ",\"final_eligibility_observable\":" +
      Boolean(observation.final_eligibility_observable) +
      ",\"can_assign\":" + (observation.final_eligibility_observable
          ? Boolean(observation.can_assign) : std::string("null")) +
      ",\"native_command_validation_observable\":" +
      Boolean(observation.native_command_validation_observable) +
      ",\"native_command_valid\":" +
      (observation.native_command_validation_observable
          ? Boolean(observation.native_command_valid) : std::string("null")) +
      ",\"command_submitted\":" + Boolean(observation.command_submitted) +
      ",\"verification_pending\":" + Boolean(observation.verification_pending) +
      ",\"unavailable_reason\":" +
      NullableReason(observation.unavailable_reason) + "}}";
  return out;
}

} // namespace xar::ck3_12003
