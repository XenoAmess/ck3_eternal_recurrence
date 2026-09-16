#pragma once

#include "xar_bridge/prewar_scope_v1.hpp"

#include <cstdint>
#include <string>
#include <vector>

namespace xar::ck3_11906 {

// Exact-build current supply operand for already-raised declaration-primary
// armies. This is a read-only source module, not a prewar forecast or bridge
// capability. Combat's stock selector reads CArmy+0x180 at Q100000 scale.
inline constexpr std::uintptr_t kM5PrimaryArmySupplyStorageSlotRva =
    0x570C730;

enum class M5PrimaryArmySupplyStatusV1 : std::uint8_t {
  available = 0,
  invalid_scope = 1,
  requires_paused = 2,
  unavailable = 3,
};

struct M5PrimaryArmySupplyRowV1 {
  std::int32_t army_id = -1; // full-generation public CUnitID
  std::int32_t native_carmy_id = -1; // full-generation CArmyID
  std::int32_t owner_character_id = -1;
  PrewarSideV1 side = PrewarSideV1::attacker;
  std::int64_t current_supply_raw = 0;
  std::int32_t current_supply_scale = 100'000;

  friend bool operator==(const M5PrimaryArmySupplyRowV1 &,
                         const M5PrimaryArmySupplyRowV1 &) = default;
};

struct M5PrimaryArmySupplyObservationV1 {
  M5PrimaryArmySupplyStatusV1 status =
      M5PrimaryArmySupplyStatusV1::unavailable;
  std::string failure_stage;
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  std::vector<M5PrimaryArmySupplyRowV1> rows;
};

// The caller supplies the exact CArmy singleton slot and the already
// authenticated prewar primary scope from the same paused native revision.
// Zero raised armies is an available empty current observation, not a supply
// forecast for unraised armies. No CK3 native function is called.
M5PrimaryArmySupplyStatusV1 ReadM5PrimaryArmySupplyV1(
    void **carmy_storage_slot, bool exact_build, bool paused,
    const PrewarScopeObservationV1 &primary_scope,
    M5PrimaryArmySupplyObservationV1 &output) noexcept;

} // namespace xar::ck3_11906
