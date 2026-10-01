#pragma once

#include "xar_bridge/ck3_12002.hpp"
#include <optional>
#include <string>
#include <vector>

namespace xar::ck3_12002::religion_conversion::faith {
inline constexpr std::uintptr_t kFaithStorageSlotRva = 0x5D1E300;
inline constexpr std::uintptr_t kCharacterFaithRva = 0x289E750;
inline constexpr std::uintptr_t kFaithMainRiteRva = 0x2444360;
inline constexpr std::uintptr_t kRiteFaithRva = 0x24FC560;
inline constexpr std::uintptr_t kFaithTagRva = 0xB801A0;
inline constexpr std::uintptr_t kFaithConversionRuleRva = 0x1D635E0;
inline constexpr std::size_t kWorldDataOffset = 0xA0;
inline constexpr std::size_t kWorldFaithsOffset = 0xD598;
inline constexpr std::size_t kWorldFaithCountOffset = 0xD5A4;
inline constexpr std::size_t kIdentityOffset = 0x08;
inline constexpr std::size_t kFaithMainRiteIdOffset = 0x98;
inline constexpr std::uint32_t kAbsentId = 0xFFFFFFFFu;

using ObjectGetter = void *(*)(void *);
using TagGetter = const void *(*)(void *);
// The native predicate includes same-Faith rejection and faith_conversion rules.
// It does not include command-level piety affordability or target-Rite rules.
using ConversionRule = bool (*)(void *, std::uint32_t, void *);
struct Bindings {
  bool enabled = false;
  CoreBindings core;
  void **faith_storage_slot = nullptr;
  ObjectGetter character_faith = nullptr;
  ObjectGetter faith_main_rite = nullptr;
  ObjectGetter rite_faith = nullptr;
  TagGetter faith_tag = nullptr;
  ConversionRule conversion_rule = nullptr;
};
struct Choice {
  std::uint32_t faith_id = kAbsentId;
  std::string faith_key;
  std::optional<std::uint32_t> main_rite_id;
  bool native_faith_rule_passes = false;
};
struct Choices {
  bool available = false;
  std::string unavailable_reason = "bindings_unavailable";
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::int32_t played_character_id = -1;
  std::optional<std::uint32_t> current_faith_id;
  std::vector<Choice> choices;
};

Bindings BindFaithConversionImage12002(std::uintptr_t image_base,
                                     std::string_view executable_sha256) noexcept;
// In-process, paused owning-thread consumer; no UI or command enqueue/execute.
// Lists the native world's Faith registry in its original order, not GUI sorting.
bool ReadPlayedFaithConversionChoices12002(const Bindings &, std::uint64_t capture_epoch,
                                         Choices &) noexcept;
std::string SerializePlayedFaithConversionChoices12002(const Choices &);
} // namespace xar::ck3_12002::religion_conversion::faith
