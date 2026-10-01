#include "xar_bridge/religion_reform12002_resource_costs.hpp"

namespace xar::ck3_12002::religion_reform {
namespace {
std::string Slots(const BaseResourceCostQuote &q) {
  if (!q.native_base_fee_slots_raw) return "null";
  std::string text = "[";
  for (std::size_t i = 0; i < q.native_base_fee_slots_raw->size(); ++i) {
    if (i) text += ',';
    text += std::to_string((*q.native_base_fee_slots_raw)[i]);
  }
  return text + "]";
}
std::string Mode(const CostQuote &q) {
  if (!q.editing_owned_current_rite) return "null";
  return *q.editing_owned_current_rite ? "\"edit_owned_current_rite\""
                                      : "\"create_rite_or_faith\"";
}
} // namespace

bool ReadCurrentRiteCreationBaseResourceCosts12002(
    const CostBindings &bindings, const CurrentDraftView &view,
    BaseResourceCostQuote &output) noexcept {
  output = {};
  if (!ReadCurrentRiteCreationCosts12002(bindings, view, output.draft_quote))
    return false;
  // Native command validators initialize all 0x50 CCost bytes to zero and
  // overwrite only slot 2 using this same native draft piety calculation.
  std::array<std::int64_t, kRiteCreationBaseCostSlotCount> slots{};
  slots[kRiteCreationBasePietySlot] = *output.draft_quote.piety_cost_raw;
  output.native_base_fee_slots_raw = slots;
  output.base_resource_cost_vector_observed = true;
  return true;
}

std::string SerializeCurrentRiteCreationBaseResourceCosts12002(
    const BaseResourceCostQuote &q) {
  return "{\"schema\":\"ck3_12002_rite_creation_base_resource_costs_v1\","
      "\"scope\":\"native_command_draft_base_fee_quote\","
      "\"quote_source\":\"native_piety_getter_plus_exact_CCost_initialization\","
      "\"game_version\":\"1.20.0.2\",\"executable_sha256\":\"" +
      std::string(kExecutableSha256) + "\",\"available\":" +
      (q.base_resource_cost_vector_observed ? "true" : "false") +
      ",\"base_resource_cost_vector_observed\":" +
      (q.base_resource_cost_vector_observed ? "true" : "false") +
      ",\"draft_kind\":" + Mode(q.draft_quote) +
      ",\"raw_scale\":100000,\"resource_slot_names\":[\"gold\",\"prestige\","
      "\"piety\",null,null,null,null,null,null,null],"
      "\"native_base_fee_slots_raw\":" + Slots(q) +
      ",\"actual_debit_observed\":false,"
      "\"post_action_net_resource_change_observed\":false,"
      "\"draft_quote\":" + SerializeCurrentRiteCreationCosts12002(q.draft_quote) + "}";
}
} // namespace xar::ck3_12002::religion_reform
