#pragma once

#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/ck3_12003_commander_assignment.hpp"
#include "xar_bridge/public_unit_id.hpp"

#include <charconv>
#include <string>
#include <string_view>

namespace xar::ck3_12003 {

inline constexpr std::string_view kArmyCommanderAssignmentCapability =
    "game.command.assign-army-commander-v1-army-N-to-character-N";
inline constexpr std::string_view kArmyCommanderAssignmentStepPrefix =
    "assign-army-commander-v1-army-";

inline bool ParseArmyCommanderAssignmentStep(
    std::string_view step, std::int32_t &army_id,
    std::int32_t &candidate_character_id) noexcept {
  army_id = -1;
  candidate_character_id = -1;
  if (!step.starts_with(kArmyCommanderAssignmentStepPrefix)) return false;
  const auto arguments = step.substr(kArmyCommanderAssignmentStepPrefix.size());
  constexpr std::string_view separator = "-to-character-";
  const auto at = arguments.find(separator);
  if (at == std::string_view::npos) return false;
  std::int32_t parsed_army = -1;
  if (!game::ParsePublicCUnitIdV1(arguments.substr(0, at), parsed_army)) {
    return false;
  }
  const auto character = arguments.substr(at + separator.size());
  if (character.empty() || (character.size() > 1 && character.front() == '0')) {
    return false;
  }
  for (const char c : character) {
    if (c < '0' || c > '9') return false;
  }
  std::int32_t parsed_character = -1;
  const auto result = std::from_chars(
      character.data(), character.data() + character.size(), parsed_character);
  if (result.ec != std::errc{} ||
      result.ptr != character.data() + character.size() || parsed_character < 0) {
    return false;
  }
  army_id = parsed_army;
  candidate_character_id = parsed_character;
  return true;
}

struct ArmyCommanderAssignmentMailboxContext {
  ck3_12002::QueryMailboxEnvelope envelope{};
  std::uintptr_t image_base = 0;
  std::int32_t army_id = -1;
  std::int32_t candidate_character_id = -1;
  CommanderAssignmentResult observation{};
  CommanderAssignmentStatus apply_result = CommanderAssignmentStatus::unavailable;
  bool completed = false;
};

bool ExecuteArmyCommanderAssignmentMailbox(
    void *opaque, const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept;

// Queue acceptance is distinct from a later independent commander readback.
std::string SerializeArmyCommanderAssignment(
    const CommanderAssignmentResult &observation,
    CommanderAssignmentStatus status, std::uint64_t command_sequence,
    std::uint64_t snapshot_revision, std::int32_t date_raw,
    std::string_view step);

} // namespace xar::ck3_12003
