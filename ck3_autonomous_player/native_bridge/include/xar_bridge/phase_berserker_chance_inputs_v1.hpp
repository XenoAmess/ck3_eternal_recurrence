#pragma once

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

namespace xar::game {
inline constexpr std::array<std::string_view, 18> kPhaseBerserkerChanceTraitKeysV1{
    "wrathful", "giant", "impatient", "sadistic", "brave", "ambitious",
    "content", "compassionate", "temperate", "lazy", "patient",
    "wounded_1", "wounded_2", "wounded_3", "one_legged", "disfigured", "one_eyed", "maimed"};
struct PhaseBerserkerChanceBoolV1 {
  std::optional<bool> value;
  std::string unavailable_reason = "value_unavailable";
  friend bool operator==(const PhaseBerserkerChanceBoolV1 &, const PhaseBerserkerChanceBoolV1 &) = default;
};
struct PhaseBerserkerChancePerkV1 {
  std::optional<std::string> definition_key;
  PhaseBerserkerChanceBoolV1 presence;
  friend bool operator==(const PhaseBerserkerChancePerkV1 &, const PhaseBerserkerChancePerkV1 &) = default;
};
struct PhaseBerserkerChanceDynastyV1 {
  std::uint32_t raw_house_id = 0xFFFFFFFFU;
  std::optional<std::uint32_t> house_id;
  std::optional<std::uint32_t> raw_dynasty_id;
  std::optional<std::uint32_t> dynasty_id;
  std::string house_resolution = "unresolved";
  std::string dynasty_resolution = "unresolved";
  PhaseBerserkerChancePerkV1 warfare_legacy_3;
  friend bool operator==(const PhaseBerserkerChanceDynastyV1 &, const PhaseBerserkerChanceDynastyV1 &) = default;
};
struct PhaseBerserkerChanceAccoladeV1 {
  std::optional<std::uint32_t> raw_accolade_id;
  std::optional<std::uint32_t> accolade_id;
  std::string resolution = "unresolved";
  PhaseBerserkerChanceBoolV1 is_acclaimed;
  friend bool operator==(const PhaseBerserkerChanceAccoladeV1 &, const PhaseBerserkerChanceAccoladeV1 &) = default;
};
struct PhaseBerserkerChanceInputsV1 {
  std::uint32_t source_character_id = 0;
  PhaseBerserkerChanceBoolV1 is_ai;
  PhaseBerserkerChancePerkV1 stalwart;
  PhaseBerserkerChanceDynastyV1 dynasty;
  PhaseBerserkerChanceAccoladeV1 acclaimed;
  std::array<PhaseBerserkerChanceBoolV1, 18> traits;
  friend bool operator==(const PhaseBerserkerChanceInputsV1 &, const PhaseBerserkerChanceInputsV1 &) = default;
};
} // namespace xar::game
