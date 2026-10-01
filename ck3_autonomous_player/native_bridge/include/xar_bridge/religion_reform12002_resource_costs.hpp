#pragma once

#include "xar_bridge/religion_reform12002_costs.hpp"
#include <array>
#include <optional>
#include <string>

namespace xar::ck3_12002::religion_reform {

// Exact-build CCost: ten signed Q100000 slots. This is a draft base-fee
// quote, not execution or a prediction of post-action/event resource changes.
inline constexpr std::size_t kRiteCreationBaseCostSlotCount = 10;
inline constexpr std::size_t kRiteCreationBasePietySlot = 2;

struct BaseResourceCostQuote {
  CostQuote draft_quote;
  bool base_resource_cost_vector_observed = false;
  std::optional<std::array<std::int64_t, kRiteCreationBaseCostSlotCount>>
      native_base_fee_slots_raw;
  static constexpr bool actual_debit_observed = false;
  static constexpr bool post_action_net_resource_change_observed = false;
};

bool ReadCurrentRiteCreationBaseResourceCosts12002(
    const CostBindings &bindings, const CurrentDraftView &view,
    BaseResourceCostQuote &output) noexcept;
std::string SerializeCurrentRiteCreationBaseResourceCosts12002(
    const BaseResourceCostQuote &quote);

} // namespace xar::ck3_12002::religion_reform
