#pragma once

#include "xar_bridge/ck3_12003_commander.hpp"
#include "xar_bridge/ck3_12002_commands.hpp"

#include <cstdint>
#include <string_view>

namespace xar::ck3_12003 {

// CSetCommanderCommand's actual player GUI channel. The generic command
// helper default (7) is not this command's reviewed channel.
inline constexpr std::uint32_t kCommanderAssignmentChannelFlags = 0x0E;

enum class CommanderAssignmentStatus {
  unavailable,
  rejected,
  submitted,
  already_assigned,
};

struct CommanderAssignmentResult {
  std::int32_t army_id = -1;
  std::int32_t native_carmy_id = -1;
  std::int32_t owner_character_id = -1;
  std::int32_t requested_commander_character_id = -1;
  std::int32_t prior_commander_character_id = -1;
  bool final_eligibility_observable = false;
  bool can_assign = false;
  bool native_command_validation_observable = false;
  bool native_command_valid = false;
  bool command_submitted = false;
  bool verification_pending = false;
  std::string_view unavailable_reason = "assignment_not_attempted";
};

struct CommanderAssignmentBindings {
  bool enabled = false;
  CommanderBindings commanders{};
  ck3_12002::CommandBindings commands{};
  void *(*create_default)() = nullptr;
  bool (*validate_source)(const void *, void *) = nullptr;
};

CommanderAssignmentBindings BindCommanderAssignmentImage(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;

// Owning application-main thread only. A successful native owned queue ACK
// remains verification_pending until a separate commander query reads it back.
CommanderAssignmentStatus ApplyArmyCommanderAssignment(
    const CommanderAssignmentBindings &bindings,
    const game::Snapshot &paused_scope, std::int32_t army_id,
    std::int32_t candidate_character_id,
    CommanderAssignmentResult &output) noexcept;

} // namespace xar::ck3_12003
