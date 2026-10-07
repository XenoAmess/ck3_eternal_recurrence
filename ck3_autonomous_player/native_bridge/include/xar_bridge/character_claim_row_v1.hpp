#pragma once

#include "xar_bridge/game_contract.hpp"
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>

// Shared software layout and native optional decoder; image factories own RVAs.
// This leaf does not resolve, inspect, or require a CWar.
namespace xar::ck3_12002 {
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

template <typename T>
inline T ClaimRowLoadV1(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value));
  return value;
}

inline bool ReadCharacterClaimRowV1(ReadCharacterClaim12002 read_character_claim,
                                    std::uintptr_t character_claim_vtable, void *claimant,
                  void *title, std::int32_t title_id,
                  game::WarClaimSnapshot &output) noexcept {
  output = {};
  ClaimTermsStorage storage{};
  void *const claim = storage.bytes.data();
  void *const returned = read_character_claim(claim, claimant, title);
  const auto present = ClaimRowLoadV1<std::uint8_t>(claim, kClaimTermsPresentOffset);
  if (returned != claim || present > 1) {
    return false;
  }
  output.title_id = title_id;
  output.present = present != 0;
  if (!output.present) {
    output.state = "absent";
    return true;
  }
  auto **const vtable = ClaimRowLoadV1<void **>(claim, 0);
  if (reinterpret_cast<std::uintptr_t>(vtable) !=
          character_claim_vtable ||
      vtable == nullptr || vtable[0] == nullptr) {
    return false;
  }
  const auto strong = ClaimRowLoadV1<std::uint8_t>(claim, kClaimTermsStrongOffset);
  const auto implicit = ClaimRowLoadV1<std::uint8_t>(claim, kClaimTermsImplicitOffset);
  const bool valid = strong <= 1 && implicit <= 1 &&
                     ClaimRowLoadV1<std::int32_t>(claim, kClaimTermsTitleIdOffset) == title_id;
  if (valid) {
    output.strong = strong != 0;
    output.implicit = implicit != 0;
    output.state = output.strong
                       ? (output.implicit ? "strong_implicit" : "strong_explicit")
                       : (output.implicit ? "weak_implicit" : "weak_explicit");
  }
  // Native scalar destructor frees its object only when delete_flags & 1.
  // This is our stack temporary; it is destroyed with zero and never freed.
  using DestroyClaim = void *(*)(void *, std::int32_t);
  reinterpret_cast<DestroyClaim>(vtable[0])(
      claim, kClaimTermsDestructorDeleteFlags);
  return valid;
}
} // namespace xar::ck3_12002
