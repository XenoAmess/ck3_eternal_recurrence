#pragma once

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
inline constexpr std::size_t kClaimTermsClaimArrayStride = 0x18;
inline constexpr std::size_t kClaimTermsStorageSize = 0x20;
inline constexpr std::size_t kClaimTermsTitleIdOffset = 0x08;
inline constexpr std::size_t kClaimTermsTypeMarkerOffset = 0x0C;
inline constexpr std::size_t kClaimTermsPresentOffset = 0x18;
inline constexpr std::size_t kClaimTermsStrongOffset = 0x10;
inline constexpr std::size_t kClaimTermsImplicitOffset = 0x11;
inline constexpr std::int32_t kClaimTermsDestructorDeleteFlags = 0x00;

// Crozier added the four-byte runtime type marker at +0x0C. A CClaim is
// now 0x18 bytes and its optional return object is 0x20 bytes. The former
// 1.19 buffer and flag offsets must not be reused with this getter.
struct alignas(8) ClaimTermsStorage {
  std::array<std::byte, kClaimTermsStorageSize> bytes{};
};
static_assert(sizeof(ClaimTermsStorage) == kClaimTermsStorageSize);

using ReadCharacterClaim12002 = void *(*)(void *output, void *claimant,
                                         void *title);
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
