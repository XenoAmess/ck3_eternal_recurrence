#pragma once
#include "xar_bridge/ck3_12002_prewar_muster.hpp"

namespace xar::ck3_12003 {
struct PlayerArmyReserveBindingsV1 {
  bool enabled = false;
  void *(*construct_empty)(void *) = nullptr;
  void (*initialize_owner)(void *, void *) = nullptr;
  std::int32_t (*count_all_unraised)(void *) = nullptr;
  void (*destroy_contents)(void *) = nullptr;
};
// Closed only for .3. Does not modify the unchanged .2 military binder.
PlayerArmyReserveBindingsV1 BindPlayerArmyReserveImageV1(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;
// Same current actor/date as the existing default-raise observation. Local
// native construction, complete aggregation and non-deleting cleanup; no GUI.
bool ReadPlayerUnraisedTroopsV1(const PlayerArmyReserveBindingsV1 &bindings,
    const ck3_12002::MilitaryWorldAccess &world,
    ck3_12002::PlayerDefaultRaiseObservationV1 &output) noexcept;
} // namespace xar::ck3_12003
