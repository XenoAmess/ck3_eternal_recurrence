#pragma once

#include <array>
#include <optional>
#include <string_view>
#include <utility>

namespace xar::ck3_11906 {

// Exact 1.19.0.6 vanilla tier-one unconditional province monthly_income.
// This is authored province value, not realized character tax after building.
inline constexpr std::array<std::pair<std::string_view, int>, 19>
    kAuthoredBuildingIncomeHundredthsV1{{
        {"caravanserai_01", 70}, {"watermills_01", 70},
        {"windmills_01", 70}, {"farm_estates_01", 70},
        {"paddy_fields_01", 50}, {"cereal_fields_01", 50},
        {"murex_farm_01", 35}, {"spice_plantation_01", 35},
        {"common_tradeport_01", 35}, {"pastures_01", 35},
        {"orchards_01", 35}, {"logging_camps_01", 35},
        {"peat_quarries_01", 35}, {"hill_farms_01", 35},
        {"elephant_pens_01", 35}, {"qanats_01", 25},
        {"hunting_grounds_01", 25}, {"plantations_01", 25},
        {"quarries_01", 25},
    }};

[[nodiscard]] inline int AuthoredIncomeHundredths(
    std::string_view key) noexcept {
  for (const auto &[building_key, income] : kAuthoredBuildingIncomeHundredthsV1) {
    if (building_key == key) return income;
  }
  return 0;
}

// Retained exact .3/.4 completed-slot values from the SDK. These keys value
// an existing occupant. Only the explicit .4 target lookup below also uses
// the two economic upgrade keys; legacy lookup remains tier-one only.
inline constexpr std::array<std::pair<std::string_view, int>, 5>
    kAuthoredExistingOnlyBuildingIncomeHundredthsV1{{
        {"farm_estates_02", 115}, {"common_tradeport_02", 55},
        {"curtain_walls_01", 25}, {"monastic_schools_01", 25},
        {"military_camps_01", 0},
    }};

[[nodiscard]] inline std::optional<int> AuthoredExistingIncomeHundredths(
    std::string_view key) noexcept {
  for (const auto &[building_key, income] : kAuthoredBuildingIncomeHundredthsV1) {
    if (building_key == key) return income;
  }
  for (const auto &[building_key, income] :
       kAuthoredExistingOnlyBuildingIncomeHundredthsV1) {
    if (building_key == key) return income;
  }
  // A known zero-income occupant is usable; an unknown key is not zero.
  return std::nullopt;
}

// Actual .4 stock content reuses these two retained unconditional values.
// This is authored province income, not observed tax or completion credit.
[[nodiscard]] inline int AuthoredTargetIncomeHundredths12004(
    std::string_view key) noexcept {
  if (key == "farm_estates_02" || key == "common_tradeport_02") {
    return AuthoredExistingIncomeHundredths(key).value_or(0);
  }
  return AuthoredIncomeHundredths(key);
}

} // namespace xar::ck3_11906
