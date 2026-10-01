#pragma once

#include "xar_bridge/ck3_12002.hpp"

#include <optional>
#include <string>

namespace xar::ck3_12002::religion {

inline constexpr std::uintptr_t kCharacterRiteRva = 0x28D2F90;
inline constexpr std::uintptr_t kCharacterFaithRva = 0x289E750;
inline constexpr std::uintptr_t kRiteFaithRva = 0x24FC560;
inline constexpr std::uintptr_t kFaithReligionRva = 0x2443D40;
inline constexpr std::uintptr_t kFaithMainRiteRva = 0x2444360;
inline constexpr std::uintptr_t kFaithFervorRva = 0x243EA90;
inline constexpr std::uintptr_t kCharacterSpiritualFulfillmentRva = 0x28BCE40;
inline constexpr std::uintptr_t kFaithTagRva = 0xB801A0;
inline constexpr std::size_t kCharacterRiteIdOffset = 0xB4;
inline constexpr std::size_t kRiteFaithIdOffset = 0x4B8;
inline constexpr std::size_t kFaithReligionIdOffset = 0x8C;
inline constexpr std::size_t kFaithMainRiteIdOffset = 0x98;
inline constexpr std::size_t kReligionDefinitionPointerOffset = 0x20;
inline constexpr std::size_t kReligionDefinitionTagOffset = 0x18;
inline constexpr std::size_t kReferenceIdentityOffset = 0x08;
inline constexpr std::uint32_t kAbsentReference = 0xFFFFFFFFU;

using ObjectGetter = void *(*)(void *);
using FixedPointGetter = std::int64_t *(*)(void *, std::int64_t *);
using TagGetter = const void *(*)(void *);

struct Bindings {
  bool enabled = false;
  CoreBindings core{};
  ObjectGetter character_rite = nullptr;
  ObjectGetter character_faith = nullptr;
  ObjectGetter rite_faith = nullptr;
  ObjectGetter faith_religion = nullptr;
  ObjectGetter faith_main_rite = nullptr;
  FixedPointGetter faith_fervor = nullptr;
  FixedPointGetter character_spiritual_fulfillment = nullptr;
  TagGetter faith_tag = nullptr;
  TagGetter religion_tag = nullptr;
};

enum class Failure {
  none,
  bindings_unavailable,
  played_character_unavailable,
  frame_not_paused,
  rite_unavailable,
  faith_unavailable,
  religion_unavailable,
  main_rite_unavailable,
  tag_unavailable,
  fervor_unavailable,
  spiritual_fulfillment_unavailable,
  state_changed,
};

struct Context {
  bool available = false;
  Failure failure = Failure::bindings_unavailable;
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::int32_t played_character_id = -1;
  // Full-generation native references. Religion.GetID's +0x10 integer is a
  // different value and is deliberately not substituted into this identity.
  std::optional<std::uint32_t> rite_id;
  std::optional<std::uint32_t> faith_id;
  std::optional<std::uint32_t> religion_id;
  std::optional<std::uint32_t> faith_main_rite_id;
  std::optional<std::string> faith_key;
  std::optional<std::string> religion_key;
  std::optional<std::int64_t> faith_fervor_raw;
  std::optional<std::int64_t> spiritual_fulfillment_raw;
  static constexpr std::int64_t raw_scale = 100'000;
};

Bindings BindReligionContextImage12002(std::uintptr_t module_base,
                                      std::string_view executable_sha256) noexcept;

// Called by an existing paused application-main owner. No process discovery,
// command, conversion, doctrine/tenet interpretation or policy lives here.
bool ReadPlayedReligionContext12002(const Bindings &bindings,
                                   std::uint64_t capture_epoch,
                                   Context &output) noexcept;
std::string SerializePlayedReligionContext12002(const Context &context);
const char *ReligionContextFailureKey(Failure failure) noexcept;

} // namespace xar::ck3_12002::religion
