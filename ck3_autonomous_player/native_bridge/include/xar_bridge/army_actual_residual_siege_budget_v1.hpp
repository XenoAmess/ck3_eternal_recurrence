#pragma once
#include <charconv>
#include <cstdint>
#include <optional>
#include <string>

namespace xar::game {
// Optional leaf copied once at the existing residual continuation hook entry.
struct ArmyActualResidualSiegeBudgetV1 {
  std::optional<std::int32_t> original_siege_budget_soldiers;
  std::optional<std::int32_t> combined_siege_raid_budget_soldiers;
  std::uint32_t capture_failure_flags=0;
};
inline void AppendArmyActualResidualSiegeBudgetV1(std::string &out,
    const ArmyActualResidualSiegeBudgetV1 &v) {
  const auto number=[&](auto value){char b[32]{};const auto r=std::to_chars(b,b+sizeof b,value);out.append(b,r.ptr);};
  const auto optional=[&](auto value){if(value)number(*value);else out+="null";};
  out+="{\"source_callback_entry_rva\":38679568,\"source_allocator_return_rva\":38680499";
  out+=",\"return_slot_basis\":\"natural_residual_hook_incoming_return_address\"";
  out+=",\"original_siege_budget_soldiers\":";optional(v.original_siege_budget_soldiers);
  out+=",\"combined_siege_raid_budget_soldiers\":";optional(v.combined_siege_raid_budget_soldiers);
  out+=",\"capture_failure_flags\":";number(v.capture_failure_flags);out+='}';
}
}
