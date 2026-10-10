#pragma once
#include "xar_bridge/army_natural_phase_scope_12004.hpp"
#include <cstdint>
#include <optional>

namespace xar::ck3_12004 {
// This token is owned by a naturally executing consumer on this thread.
// entry_event is the stage identity on the shared phase clock. Local journal
// ordinals are never stage identities. Children copy this exact value.
struct ArmyAssaultConsumerParent12004 {
  bool active = false;
  bool exact_post_date_parent = false;
  std::uintptr_t actual_entry_rva = 0;
  std::optional<std::uintptr_t> caller_return_rva;
  std::uintptr_t manager_identity = 0;
  ArmyNaturalPhaseEvent12004 entry_event;
  ArmyNaturalPhaseEvent12004 phase_entry_event;
  std::optional<std::uint64_t> date_raw;
  std::optional<std::uint32_t> absolute_day_raw;
};
// False outside original 2A97EB0 execution, including before/after copying.
// No query, native read, clock increment, allocation or native call occurs.
bool CopyActiveArmyAssaultConsumerParent12004(
    ArmyAssaultConsumerParent12004 &output) noexcept;
} // namespace xar::ck3_12004
