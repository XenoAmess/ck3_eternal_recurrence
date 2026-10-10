#pragma once
#include "xar_bridge/army_regular_core_readonly_access_12004.hpp"
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace xar::ck3_12004 {
struct ArmyPositionOperandFailure12004 {
  std::string field;
  std::string reason;
};

// Widths and order are from the complete actual 2C09280..2C0935C body.
// R8 is an optional native War identity, with zero meaning no pointer filter.
struct ArmyPositionWarOperands12004 {
  std::int32_t full_war_id = -1;
  std::uintptr_t optional_war_identity = 0;
  std::optional<std::uintptr_t> manager_identity;
  std::optional<std::uint32_t> capacity;
  std::optional<std::uintptr_t> table_identity;
  std::optional<std::uintptr_t> row_war_identity;
  std::optional<std::uint32_t> row_full_war_id;
  std::optional<bool> fallback_used;
  std::optional<std::uintptr_t> fallback_war_identity;
  std::optional<std::uintptr_t> resolved_war_identity;
  std::optional<std::uint8_t> ended_byte;
  std::vector<ArmyPositionOperandFailure12004> failures;
};

ArmyPositionWarOperands12004 ReadArmyPositionWarOperands12004(
    const ArmyRegularCoreReadonlyAccess12004 &, std::int32_t full_war_id,
    std::uintptr_t optional_war_identity = 0) noexcept;
ArmyRegularCoreReadonlyPredicate12004 EvaluateArmyPositionWarGate12004(
    const ArmyPositionWarOperands12004 &) noexcept;
ArmyRegularCoreReadonlyPredicate12004 ReadArmyPositionWarGate12004(
    const ArmyRegularCoreReadonlyAccess12004 &, std::int32_t full_war_id,
    std::uintptr_t optional_war_identity = 0) noexcept;

struct ArmyPosition2C09280Operands12004 {
  std::uintptr_t original_actor_identity = 0;
  std::uintptr_t holder_identity = 0;
  std::uintptr_t optional_war_identity = 0;
  std::optional<bool> criterion_result;
  std::optional<std::uintptr_t> selected_actor_identity;
  std::optional<std::uint32_t> selected_actor_tag;
  std::optional<std::uint32_t> selected_actor_full_id;
  std::optional<std::uint32_t> holder_full_id;
  std::optional<std::uintptr_t> relation_identity;
  std::optional<std::int32_t> relation_full_war_id;
  std::optional<ArmyPositionWarOperands12004> war;
  std::vector<ArmyPositionOperandFailure12004> failures;
};

ArmyPosition2C09280Operands12004 ReadArmyPosition2C09280Operands12004(
    const ArmyRegularCoreReadonlyAccess12004 &, std::uintptr_t actor,
    std::uintptr_t holder, std::uintptr_t optional_war_identity = 0) noexcept;
ArmyRegularCoreReadonlyPredicate12004 EvaluateArmyPosition2C0928012004(
    const ArmyPosition2C09280Operands12004 &) noexcept;
ArmyRegularCoreReadonlyPredicate12004 ReadArmyPosition2C0928012004(
    const ArmyRegularCoreReadonlyAccess12004 &, std::uintptr_t actor,
    std::uintptr_t holder, std::uintptr_t optional_war_identity = 0) noexcept;
} // namespace xar::ck3_12004
