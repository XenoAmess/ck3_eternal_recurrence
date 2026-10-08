#pragma once

#include "xar_bridge/marriage_character_fertility_v1.hpp"

#include <cstdint>
#include <optional>
#include <string_view>
#include <vector>

namespace xar::ck3_11906 {

struct CurrentCharacterPregnancyReadV1 {
  std::string_view status = "unavailable";
  std::string_view unavailable_reason = "native_pregnancy_binding_unavailable";
  std::optional<bool> is_pregnant{};
};

struct CurrentFirstHeirReproductiveRowV1 {
  std::int32_t character_id = -1;
  std::vector<std::string_view> roles{};
  bool available = false;
  std::string_view unavailable_reason = "current_household_value_unavailable";
  std::optional<std::int16_t> age_measure_raw{};
  std::optional<std::uint8_t> sex_selector_raw{};
  bridge::MarriageCharacterFertilityReadV1 fertility{};
  CurrentCharacterPregnancyReadV1 native_pregnancy{};
};

struct CurrentFirstHeirReproductiveInputsV1 {
  std::string_view status = "unavailable";
  std::string_view unavailable_reason = "current_household_binding_unavailable";
  std::int32_t played_character_id = -1;
  std::int32_t heir_character_id = -1;
  std::optional<std::int32_t> date_raw{};
  std::vector<CurrentFirstHeirReproductiveRowV1> rows{};
};

} // namespace xar::ck3_11906
