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

// Exact .4 unconditional province income for nineteen economic upgrade chains.
// Tier2..8 declarations match the frozen stock script-values source.
inline constexpr std::array<std::pair<std::string_view, int>, 133>
    kAuthoredEconomicBuildingIncomeHundredths12004{{
        {"farm_estates_02", 115},
        {"farm_estates_03", 160},
        {"farm_estates_04", 205},
        {"farm_estates_05", 250},
        {"farm_estates_06", 295},
        {"farm_estates_07", 340},
        {"farm_estates_08", 385},
        {"common_tradeport_02", 55},
        {"common_tradeport_03", 75},
        {"common_tradeport_04", 95},
        {"common_tradeport_05", 115},
        {"common_tradeport_06", 135},
        {"common_tradeport_07", 155},
        {"common_tradeport_08", 175},
        {"pastures_02", 55},
        {"pastures_03", 75},
        {"pastures_04", 95},
        {"pastures_05", 115},
        {"pastures_06", 135},
        {"pastures_07", 155},
        {"pastures_08", 175},
        {"orchards_02", 55},
        {"orchards_03", 75},
        {"orchards_04", 95},
        {"orchards_05", 115},
        {"orchards_06", 135},
        {"orchards_07", 155},
        {"orchards_08", 175},
        {"hunting_grounds_02", 40},
        {"hunting_grounds_03", 55},
        {"hunting_grounds_04", 70},
        {"hunting_grounds_05", 85},
        {"hunting_grounds_06", 100},
        {"hunting_grounds_07", 115},
        {"hunting_grounds_08", 130},
        {"plantations_02", 40},
        {"plantations_03", 55},
        {"plantations_04", 70},
        {"plantations_05", 85},
        {"plantations_06", 100},
        {"plantations_07", 115},
        {"plantations_08", 130},
        {"caravanserai_02", 115},
        {"caravanserai_03", 160},
        {"caravanserai_04", 205},
        {"caravanserai_05", 250},
        {"caravanserai_06", 295},
        {"caravanserai_07", 340},
        {"caravanserai_08", 385},
        {"watermills_02", 115},
        {"watermills_03", 160},
        {"watermills_04", 205},
        {"watermills_05", 250},
        {"watermills_06", 295},
        {"watermills_07", 340},
        {"watermills_08", 385},
        {"windmills_02", 115},
        {"windmills_03", 160},
        {"windmills_04", 205},
        {"windmills_05", 250},
        {"windmills_06", 295},
        {"windmills_07", 340},
        {"windmills_08", 385},
        {"murex_farm_02", 55},
        {"murex_farm_03", 75},
        {"murex_farm_04", 95},
        {"murex_farm_05", 115},
        {"murex_farm_06", 135},
        {"murex_farm_07", 155},
        {"murex_farm_08", 175},
        {"spice_plantation_02", 55},
        {"spice_plantation_03", 75},
        {"spice_plantation_04", 95},
        {"spice_plantation_05", 115},
        {"spice_plantation_06", 135},
        {"spice_plantation_07", 155},
        {"spice_plantation_08", 175},
        {"logging_camps_02", 55},
        {"logging_camps_03", 75},
        {"logging_camps_04", 95},
        {"logging_camps_05", 115},
        {"logging_camps_06", 135},
        {"logging_camps_07", 155},
        {"logging_camps_08", 175},
        {"peat_quarries_02", 55},
        {"peat_quarries_03", 75},
        {"peat_quarries_04", 95},
        {"peat_quarries_05", 115},
        {"peat_quarries_06", 135},
        {"peat_quarries_07", 155},
        {"peat_quarries_08", 175},
        {"hill_farms_02", 55},
        {"hill_farms_03", 75},
        {"hill_farms_04", 95},
        {"hill_farms_05", 115},
        {"hill_farms_06", 135},
        {"hill_farms_07", 155},
        {"hill_farms_08", 175},
        {"elephant_pens_02", 55},
        {"elephant_pens_03", 75},
        {"elephant_pens_04", 95},
        {"elephant_pens_05", 115},
        {"elephant_pens_06", 135},
        {"elephant_pens_07", 155},
        {"elephant_pens_08", 175},
        {"qanats_02", 40},
        {"qanats_03", 55},
        {"qanats_04", 70},
        {"qanats_05", 85},
        {"qanats_06", 100},
        {"qanats_07", 115},
        {"qanats_08", 130},
        {"quarries_02", 40},
        {"quarries_03", 55},
        {"quarries_04", 70},
        {"quarries_05", 85},
        {"quarries_06", 100},
        {"quarries_07", 115},
        {"quarries_08", 130},
        {"paddy_fields_02", 80},
        {"paddy_fields_03", 110},
        {"paddy_fields_04", 140},
        {"paddy_fields_05", 170},
        {"paddy_fields_06", 200},
        {"paddy_fields_07", 230},
        {"paddy_fields_08", 260},
        {"cereal_fields_02", 80},
        {"cereal_fields_03", 110},
        {"cereal_fields_04", 140},
        {"cereal_fields_05", 170},
        {"cereal_fields_06", 200},
        {"cereal_fields_07", 230},
        {"cereal_fields_08", 260},
    }};

[[nodiscard]] inline std::optional<int> AuthoredExistingIncomeHundredths12004(
    std::string_view key) noexcept {
  for (const auto &[building_key, income] :
       kAuthoredEconomicBuildingIncomeHundredths12004) {
    if (building_key == key) return income;
  }
  return AuthoredExistingIncomeHundredths(key);
}

// This is authored province income, not observed tax or completion credit.
[[nodiscard]] inline int AuthoredTargetIncomeHundredths12004(
    std::string_view key) noexcept {
  for (const auto &[building_key, income] :
       kAuthoredEconomicBuildingIncomeHundredths12004) {
    if (building_key == key) return income;
  }
  return AuthoredIncomeHundredths(key);
}

} // namespace xar::ck3_11906
