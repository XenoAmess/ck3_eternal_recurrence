#pragma once
#include <cstdint>
#include <optional>
#include <string>

namespace xar::game {
// One naturally reached 2C09620 entry/return under the current P stage.
// sampled_* are guarded entry-time reads, never observations of OR callees.
struct ArmyCountyRelationInputsV1 {
  bool available = false;
  std::uint32_t call_count = 0;
  std::optional<std::uint64_t> actual_bridge_caller_return_rva;
  bool argument_identity_matched = false, same_thread = false;
  std::optional<bool> identity_before_after_match;
  std::optional<std::uint32_t> receiver_full_id, actor_full_id;
  std::optional<std::uint64_t> auxiliary_identity;
  std::optional<bool> returned;
  bool sampled_relation_available = false;
  std::optional<std::uint64_t> sampled_relation_identity;
  std::optional<std::int32_t> sampled_relation_full_war_id;
  std::optional<std::uint64_t> sampled_selected_war_identity;
  std::optional<bool> sampled_selected_war_used_fallback;
  std::optional<std::uint8_t> sampled_selected_war_byte_358_u8;
  std::optional<bool> sampled_direct_war_matches_aux, sampled_direct_war_gate;
  bool unknown_or_inputs = true;
  std::string unavailable_reason = "county_relation_entry_return_unavailable";
  std::string sampled_relation_unavailable_reason = "county_relation_inputs_not_sampled";
  friend bool operator==(const ArmyCountyRelationInputsV1 &,
                         const ArmyCountyRelationInputsV1 &) = default;
};
}
