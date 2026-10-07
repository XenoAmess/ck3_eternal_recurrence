#pragma once

#include "xar_bridge/character_claim_row_v1.hpp"
#include "xar_bridge/ck3_12002_province.hpp"
#include "xar_bridge/ck3_12002_world.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::ck3_12002 {

inline constexpr std::uintptr_t kClaimTermsGetterRva = 0x2B9ECD0;
inline constexpr std::uintptr_t kClaimTermsClaimVtableRva = 0x44F17D8;
inline constexpr std::uintptr_t kClaimTermsDestructorRva = 0xDDC610;
struct ClaimTermsBindings {
  bool enabled = false;
  CoreBindings core;
  WorldBindings world;
  ProvinceBindings provinces;
  ReadCharacterClaim12002 read_character_claim = nullptr;
  std::uintptr_t character_claim_vtable = 0;
};

ClaimTermsBindings BindClaimTermsImage(std::uintptr_t image_base,
                                      std::string_view sha256) noexcept;

// In-process owning-thread reader. Only synthetic fixture objects have been
// exercised so far. The caller must provide the same paused execution boundary
// used by the new-build adapter's other native readers.
game::ReadWarTerminationTermsResult ReadWarTerminationTerms(
    const ClaimTermsBindings &bindings, std::int32_t war_id,
    game::WarTerminationTermsSnapshot &output) noexcept;

} // namespace xar::ck3_12002
