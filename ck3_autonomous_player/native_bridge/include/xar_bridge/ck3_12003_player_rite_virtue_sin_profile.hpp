#pragma once

#include "xar_bridge/ck3_12002_religion_context.hpp"
#include "xar_bridge/ck3_12003_adapter.hpp"

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace xar::ck3_12002::religion::rite_virtue_sin_profile12003 {

inline constexpr std::uintptr_t kTraitDatabaseRva = 0x89E5B0;
inline constexpr std::uintptr_t kTraitLookupRva = 0xC85E80;
inline constexpr std::uintptr_t kCharacterRiteRva = 0x28D2F90;
inline constexpr std::uintptr_t kTraitClassificationRva = 0x2BD84A0;
inline constexpr std::size_t kCharacterTraitRowsOffset = 0xF8;
inline constexpr std::size_t kCharacterTraitCountOffset = 0x104;
inline constexpr std::size_t kRiteEffectiveTraitMapOffset = 0x950;

using TraitDatabase = void *(*)();
using TraitLookup = void *(*)(void *, std::int32_t);
using CharacterRite = void *(*)(void *);
using TraitClassification = std::int32_t (*)(void *, void *, void **);

struct Bindings {
  bool enabled = false;
  TraitDatabase trait_database = nullptr;
  TraitLookup trait_lookup = nullptr;
  CharacterRite character_rite = nullptr;
  TraitClassification trait_classification = nullptr;
};

struct TraitRow {
  std::int32_t trait_id = -1;
  // Exact native effective current-Rite result: 0 neutral, 1 virtue, 2 sin.
  std::int32_t classification = 0;
  std::optional<std::int64_t> opinion_weight_input_raw;
  std::optional<std::int64_t> owner_modifier_scale_input_raw;
};

struct Profile {
  bool available = false;
  std::string unavailable_reason = "bindings_unavailable";
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0, played_character_id = -1;
  std::optional<std::uint32_t> rite_id;
  std::optional<std::int32_t> trait_count, num_virtuous_traits, num_sinful_traits;
  std::vector<TraitRow> traits;
};

Bindings BindPlayerRiteVirtueSinProfileImage12003(
    std::uintptr_t module_base, const game::AdapterDescriptor &) noexcept;
// Same paused owner/frame, actual played Character only. No trait or modifier
// mutation, trigger reconstruction, religion list recreation or total opinion.
bool ReadPlayerRiteVirtueSinProfile12003(const Bindings &, void *actual_played_character,
    const religion::Context &current, Profile &) noexcept;
std::string SerializePlayerRiteVirtueSinProfile12003(const Profile &);

} // namespace xar::ck3_12002::religion::rite_virtue_sin_profile12003
