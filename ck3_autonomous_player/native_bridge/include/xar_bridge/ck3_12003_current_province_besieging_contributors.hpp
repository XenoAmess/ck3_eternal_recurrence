#pragma once
#include "xar_bridge/game_contract.hpp"

namespace xar::ck3_12002 { struct ArmyBindings; }
namespace xar::ck3_12003 {
struct CurrentProvinceBesiegingBindings12003 {
  bool enabled = false;
  void **unit_fallback_slot = nullptr;
  void **army_fallback_slot = nullptr;
  void **province_fallback_slot = nullptr;
  void **siege_storage_slot = nullptr;
  std::uint8_t (*army_excluded)(void *) = nullptr;
  std::uint8_t (*army_province_eligible)(void *, void *) = nullptr;
  std::int32_t (*besieging_strength)(void *) = nullptr;
  std::int32_t (*assault_expected_loss)(void *) = nullptr;
  const std::int32_t *casualty_percentage_count = nullptr;
  const std::int64_t **casualty_percentage_table_slot = nullptr;
};

game::ArmyCurrentProvinceBesiegingContributorsV1 ReadCurrentProvinceBesiegingContributors12003(
    const ck3_12002::ArmyBindings &, void *current_province);
} // namespace xar::ck3_12003
