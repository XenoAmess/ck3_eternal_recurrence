#include "xar_bridge/ck3_12003_commander_assignment.hpp"
#include "xar_bridge/ck3_12003.hpp"

#include <algorithm>
#include <cstring>

namespace xar::ck3_12003 {
namespace {

struct NativeOwnedSource {
  void *value = nullptr;
  ~NativeOwnedSource() { ck3_12002::DestroyOwnedCommand(value); }
};

void StoreId(void *packet, std::size_t offset, std::int32_t value) noexcept {
  std::memcpy(static_cast<std::byte *>(packet) + offset, &value, sizeof value);
}

} // namespace

CommanderAssignmentBindings BindCommanderAssignmentImage(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept {
  CommanderAssignmentBindings bindings{};
  if (image_base == 0 || executable_sha256 != kExecutableSha256) {
    return bindings;
  }
  bindings.commanders = BindCommanderImage(image_base, executable_sha256);
  // The .3 core review already binds this byte-identical command manager,
  // hidden-result clone and owned submit path through the existing adapter.
  bindings.commands = ck3_12002::BindCommandImage(
      image_base, ck3_12002::kExecutableSha256);
  bindings.create_default = reinterpret_cast<decltype(bindings.create_default)>(
      image_base + 0x297BB00);
  bindings.validate_source =
      reinterpret_cast<decltype(bindings.validate_source)>(
          image_base + 0x2971480);
  bindings.enabled = bindings.commanders.enabled && bindings.commands.enabled;
  return bindings;
}

CommanderAssignmentStatus ApplyArmyCommanderAssignment(
    const CommanderAssignmentBindings &bindings,
    const game::Snapshot &paused_scope, std::int32_t army_id,
    std::int32_t candidate_character_id,
    CommanderAssignmentResult &output) noexcept {
  output = {};
  output.army_id = army_id;
  output.requested_commander_character_id = candidate_character_id;
  if (!bindings.enabled || !bindings.commands.enabled ||
      bindings.create_default == nullptr ||
      bindings.validate_source == nullptr) {
    output.unavailable_reason = "commander_assignment_bindings_unavailable";
    return CommanderAssignmentStatus::unavailable;
  }
  ArmyCommanderCandidatesSnapshot current{};
  const auto read = ReadArmyCommanderCandidates(
      bindings.commanders, paused_scope, army_id, current);
  output.native_carmy_id = current.native_carmy_id;
  output.owner_character_id = current.owner_character_id;
  output.prior_commander_character_id = current.current_commander_character_id;
  if (read == CommanderCandidatesReadResult::unavailable ||
      !current.candidate_collection_complete) {
    output.unavailable_reason = current.unavailable_reason;
    return CommanderAssignmentStatus::unavailable;
  }
  const auto candidate = std::find_if(
      current.candidates.begin(), current.candidates.end(),
      [candidate_character_id](const auto &row) {
        return row.character_id == candidate_character_id && row.available &&
            row.final_eligibility_observable;
      });
  if (candidate != current.candidates.end()) {
    output.final_eligibility_observable = true;
    output.can_assign = candidate->can_assign;
  }
  // This is a real current commander observation, not a command ACK. A
  // currently assigned character may no longer pass the replacement rule.
  if (current.current_commander_status == "available" &&
      current.current_commander_character_id == candidate_character_id) {
    output.unavailable_reason = {};
    return CommanderAssignmentStatus::already_assigned;
  }
  if (candidate == current.candidates.end()) {
    output.unavailable_reason = "candidate_not_observed_in_native_collection";
    return CommanderAssignmentStatus::rejected;
  }
  if (!output.can_assign) {
    output.unavailable_reason = "native_final_commander_eligibility_false";
    return CommanderAssignmentStatus::rejected;
  }
  NativeOwnedSource source{bindings.create_default()};
  if (source.value == nullptr) {
    output.unavailable_reason = "native_commander_factory_unavailable";
    return CommanderAssignmentStatus::unavailable;
  }
  // Only caller-owned native command storage is written. The factory supplied
  // both interfaces and metadata. CSetCommanderCommand uses internal CArmy ID,
  // not the public CUnit ID carried by the typed request.
  StoreId(source.value, 0x20, 1);
  StoreId(source.value, 0x24, candidate_character_id);
  StoreId(source.value, 0x28, current.native_carmy_id);
  output.native_command_validation_observable = true;
  output.native_command_valid = bindings.validate_source(source.value, nullptr);
  if (!output.native_command_valid) {
    output.unavailable_reason = "native_commander_command_validator_false";
    return CommanderAssignmentStatus::rejected;
  }
  const auto submitted = ck3_12002::SubmitCommandCopy(
      bindings.commands, source.value, kCommanderAssignmentChannelFlags);
  if (submitted != ck3_12002::CommandSubmitResult::submitted) {
    output.unavailable_reason =
        submitted == ck3_12002::CommandSubmitResult::rejected
            ? "native_commander_queue_rejected"
            : "native_commander_queue_unavailable";
    return submitted == ck3_12002::CommandSubmitResult::rejected
        ? CommanderAssignmentStatus::rejected
        : CommanderAssignmentStatus::unavailable;
  }
  output.command_submitted = true;
  output.verification_pending = true;
  output.unavailable_reason = {};
  return CommanderAssignmentStatus::submitted;
}

} // namespace xar::ck3_12003
