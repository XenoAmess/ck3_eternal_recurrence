#pragma once
#include "xar_bridge/game_contract.hpp"
#include <string_view>

namespace xar::ck3_12002 { struct ArmyBindings; }
namespace xar::ck3_12003 {
struct OrderedBesiegingRefillBindings12003 {
  bool enabled = false;
  void **arrg_fallback_slot = nullptr;
};
OrderedBesiegingRefillBindings12003 BindOrderedBesiegingRefillInputs12003(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;
game::ArmyOrderedBesiegingRefillInputsV1 ReadOrderedBesiegingRefillInputs12003(
    const ck3_12002::ArmyBindings &, void *army, void *unit,
    const game::ArmyCurrentProvinceBesiegingContributorsV1 &);
} // namespace xar::ck3_12003
