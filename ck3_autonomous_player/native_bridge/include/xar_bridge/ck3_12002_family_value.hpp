#pragma once

#include "xar_bridge/ck3_12002.hpp"

#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::ck3_12002::family_value {

inline constexpr std::uintptr_t kHouseStoreSlotRva = 0x5D1DAF0;
inline constexpr std::uintptr_t kHouseFallbackSlotRva = 0x5D1DAE8;
inline constexpr std::uintptr_t kDynastyStoreSlotRva = 0x5D1DE78;
inline constexpr std::uintptr_t kDynastyFallbackSlotRva = 0x5D1DE28;
inline constexpr std::size_t kCharacterAgeOffset = 0x68;
inline constexpr std::size_t kCharacterSexSelectorOffset = 0x1A1;
inline constexpr std::size_t kCharacterHouseOffset = 0x158;
inline constexpr std::size_t kHouseDynastyOffset = 0x2C;
inline constexpr std::size_t kCharacterCourtRelationOffset = 0x1B8;
inline constexpr std::size_t kCourtRelationEmployerOffset = 0xC8;
inline constexpr std::uintptr_t kFertilityGateRva = 0x28BB4E0;
inline constexpr std::size_t kFertilityExtensionOffset = 0x1B0;
inline constexpr std::size_t kFertilityRawOffset = 0x2E0;

using FertilityGate = bool (*)(void *character);

struct Lineage {
  std::int32_t house_id = -1;
  std::int32_t dynasty_id = -1;
  friend bool operator==(const Lineage &, const Lineage &) = default;
};

// This is CK3's stock eligibility gate and cached effective raw value. Native
// fixed-point calculations use denominator 100000; pair future probability is
// not an observation supplied by this individual current value.
struct FertilityRead {
  bool available = false;
  bool extension_present = false;
  bool native_gate_evaluated = false;
  bool native_gate_allows = false;
  std::int64_t effective_raw = 0;
  friend bool operator==(const FertilityRead &, const FertilityRead &) = default;
};

struct CharacterValue {
  std::int32_t character_id = -1;
  std::int16_t age_raw = 0;
  std::uint8_t sex_selector_raw = 0xFF;
  Lineage lineage{};
  std::int32_t employer_character_id = -1;
  FertilityRead fertility{};
  friend bool operator==(const CharacterValue &, const CharacterValue &) = default;
};

struct Bindings {
  bool enabled = false;
  CoreBindings core{};
  void **house_store = nullptr;
  void **house_fallback = nullptr;
  void **dynasty_store = nullptr;
  void **dynasty_fallback = nullptr;
  FertilityGate fertility_gate = nullptr;
  // Optional actual4 loaded producer-floor operand; older binders leave null.
  const std::int64_t *candidate_fertility_floor = nullptr;
};

// Address calculation only. Neither function discovers or attaches to a game.
Bindings BindImage(std::uintptr_t image_base,
                   std::string_view executable_sha256) noexcept;

// Owning application thread only; the caller's paused snapshot defines the
// frame. -1 is legitimate no-house/no-dynasty/no-employer, not a failed read.
bool ReadCharacterLineage(const Bindings &, const void *character,
                          Lineage &output,
                          std::string_view *reason = nullptr) noexcept;
bool ReadCharacterValue(const Bindings &, std::int32_t character_id,
                        CharacterValue &output, bool read_fertility = true,
                        std::string_view *reason = nullptr) noexcept;

} // namespace xar::ck3_12002::family_value
