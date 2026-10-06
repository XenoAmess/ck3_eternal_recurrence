#pragma once

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace xar::game {
struct PhaseBerserkerCultureV1 {
  bool available = false;
  std::uint32_t raw_culture_id = 0xFFFFFFFFU;
  std::optional<std::uint32_t> culture_id;
  std::string resolution = "unresolved";
  std::optional<std::vector<std::string>> selected_pillar_keys;
  std::optional<bool> heritage_north_germanic;
  std::string unavailable_reason = "culture_unavailable";
  friend bool operator==(const PhaseBerserkerCultureV1 &, const PhaseBerserkerCultureV1 &) = default;
};
struct PhaseBerserkerReligionV1 {
  bool available = false;
  std::uint32_t raw_adopted_rite_id = 0xFFFFFFFFU;
  std::optional<std::uint32_t> rite_id;
  std::optional<std::uint32_t> raw_faith_id;
  std::optional<std::uint32_t> faith_id;
  std::optional<std::uint32_t> raw_religion_id;
  std::optional<std::uint32_t> religion_id;
  std::string resolution = "unresolved";
  std::optional<std::string> religion_key;
  std::optional<bool> germanic;
  std::string unavailable_reason = "religion_unavailable";
  friend bool operator==(const PhaseBerserkerReligionV1 &, const PhaseBerserkerReligionV1 &) = default;
};
struct PhaseBerserkerTraitV1 {
  std::optional<bool> value;
  std::string unavailable_reason = "trait_unavailable";
  friend bool operator==(const PhaseBerserkerTraitV1 &, const PhaseBerserkerTraitV1 &) = default;
};
struct PhaseBerserkerValidityInputsV1 {
  std::uint32_t source_character_id = 0;
  PhaseBerserkerCultureV1 culture;
  PhaseBerserkerReligionV1 religion;
  // Actual authored NOR order, never numeric trait IDs.
  std::array<PhaseBerserkerTraitV1, 3> traits;
  friend bool operator==(const PhaseBerserkerValidityInputsV1 &, const PhaseBerserkerValidityInputsV1 &) = default;
};
} // namespace xar::game
