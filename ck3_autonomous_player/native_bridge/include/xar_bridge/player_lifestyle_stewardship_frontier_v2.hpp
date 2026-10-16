#pragma once
#include "xar_bridge/player_lifestyle_stock_perk_legality_v1.hpp"
#include <array>
#include <optional>
#include <string_view>
#include <utility>

namespace xar::ck3_11906 {
inline constexpr std::string_view kStewardshipFullFrontierCapabilityV2 =
    "game.state.private-lifestyle-stewardship-frontier-v2";
// All 27 current vanilla stewardship perks. Domain follows the existing
// development policy, then wealth/duty preserve their authored file order.
inline constexpr std::array<std::string_view, 27> kStewardshipPerkPriorityV2{
    "cutting_corners_perk", "professional_workforce_perk",
    "centralization_perk", "tax_man_perk", "defensive_measures_perk",
    "organized_muster_rolls_perk", "popular_figurehead_perk",
    "divided_attention_perk", "architect_perk",
    "golden_obligations_perk", "heregeld_perk", "detailed_ledgers_perk",
    "war_profiteer_perk", "fearful_troops_perk", "it_is_my_domain_perk",
    "golden_aplomb_perk", "at_any_cost_perk", "avaricious_perk",
    "meritocracy_perk", "chains_of_loyalty_perk", "likable_perk",
    "positions_of_power_perk", "large_levies_perk", "soon_forgiven_perk",
    "toe_the_line_perk", "honored_to_serve_perk", "administrator_perk"};

inline bool StewardshipPerkAdmittedV2(std::string_view target) noexcept {
  for (const auto key : kStewardshipPerkPriorityV2)
    if (key == target) return true;
  return false;
}

// Every row uses the caller's genuine native double-read final validator.
// A missing/unavailable row never becomes a negative frontier proof. A later
// independently legal row can still be selected. Submit only rechecks the
// requested exact target; it never substitutes a new policy choice.
template <class Reader>
StockPerkLegalityResultV1 ReadLifestylePolicyPerkFrontierV2(
    bool submit, std::string_view action_target, bool stewardship_query,
    std::string_view legacy_target, Reader &&read) noexcept {
  if (submit) return read(action_target);
  if (!stewardship_query) return read(legacy_target);
  std::optional<StockPerkLegalityResultV1> first_unknown;
  StockPerkLegalityResultV1 last_illegal{};
  for (const auto key : kStewardshipPerkPriorityV2) {
    auto result = read(key);
    if (result.status == StockPerkLegalityStatusV1::observed_native_legal)
      return result;
    if (result.status == StockPerkLegalityStatusV1::observed_native_illegal)
      last_illegal = std::move(result);
    else if (!first_unknown) first_unknown = std::move(result);
  }
  return first_unknown ? std::move(*first_unknown) : std::move(last_illegal);
}
} // namespace xar::ck3_11906
