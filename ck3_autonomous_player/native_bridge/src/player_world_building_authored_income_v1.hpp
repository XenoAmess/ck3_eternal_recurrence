#pragma once

#include <array>
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

} // namespace xar::ck3_11906
