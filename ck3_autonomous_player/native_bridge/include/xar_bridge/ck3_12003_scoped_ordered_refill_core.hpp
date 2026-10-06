#pragma once
#include "xar_bridge/army_scoped_ordered_refill_inputs_v1.hpp"
#include "xar_bridge/ck3_12003_army_replenishment_records.hpp"
#include <span>
#include <string_view>

namespace xar::ck3_12002 { struct ArmyBindings; }
namespace xar::ck3_12003 {
struct ScopedOrderedRefillBindings12003 {
  bool enabled = false;
  void **persistent_fallback_slot = nullptr, **army_fallback_slot = nullptr;
  void **character_storage_slot = nullptr, **character_fallback_slot = nullptr;
  void **unit_position_province_fallback_slot = nullptr;
  void *(*resolve_arrg_reference)(const void *) = nullptr;
  void *(*resolve_unit_reference)(const void *) = nullptr;
  bool (*is_army_in_combat)(void *) = nullptr;
  bool (*is_unit_position_eligible)(void *) = nullptr;
  std::int32_t *(*read_province_holder)(void *, std::int32_t *) = nullptr;
};
ScopedOrderedRefillBindings12003 BindScopedOrderedRefillInputs12003(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;
game::ArmyScopedOrderedRefillInputsV1 ReadScopedOrderedRefillInputs12003(
    const ck3_12002::ArmyBindings &, void *army, void *unit,
    std::span<const game::ArmyRegimentReplenishmentRecordsSnapshotV1> data);
} // namespace xar::ck3_12003
