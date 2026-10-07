#pragma once

#include "xar_bridge/character_claim_row_v1.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12002_province.hpp"
#include "xar_bridge/player_claims_v1.hpp"

namespace xar::ck3_12004 {
struct PlayerClaimsBindingsV1 {
  bool enabled = false;
  CoreBindings core;
  ck3_12002::ProvinceBindings provinces;
  ck3_12002::ReadCharacterClaim12002 read_character_claim = nullptr;
  std::uintptr_t character_claim_vtable = 0;
};
// Pure exact-image binding; no WorldBindings or CWar dependency.
PlayerClaimsBindingsV1 BindPlayerClaimsImageV1(
    std::uintptr_t image_base, std::string_view executable_sha256,
    const CoreBindings &actual_core,
    const ck3_12002::ProvinceBindings &actual_provinces) noexcept;
// Owning-thread only: WorkerAdapter dispatches this through its existing mailbox.
game::ReadPlayerClaimsV1Result ReadPlayerClaimsV1(
    const PlayerClaimsBindingsV1 &bindings,
    std::span<const std::int32_t> title_ids, game::PlayerClaimsV1 &output) noexcept;
} // namespace xar::ck3_12004
