#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace xar::ck3_12002 { struct BattleBindings; }

namespace xar::game {
// E-prefix predicate for one actual owner-matched activity context.
// This value does not observe the dispatcher choosing its E wrapper.
struct BattleNativeActivityContextMatchV1 {
  std::string collection;
  std::string prefix_kind = "e_1a781a0";
  std::int32_t stored_index = -1;
  std::int32_t actor_character_id = -1;
  std::string status = "unavailable";
  std::string unavailable_reason = "e_prefix_operands_unavailable";
  std::optional<bool> e_prefix_admitted;
  std::optional<std::int32_t> context_state_raw;
  std::optional<std::uint8_t> context_16_raw;
  std::optional<std::uint8_t> context_2e_raw;
  std::optional<std::uint64_t> government_flags_40_raw;
  std::optional<std::uint16_t> plin_flags_2f0_raw;

  friend bool operator==(const BattleNativeActivityContextMatchV1 &,
                         const BattleNativeActivityContextMatchV1 &) = default;
};

struct BattleNativeActivityContextV1 {
  std::int32_t schema_version = 1;
  std::string status = "unavailable";
  std::string unavailable_reason = "native_activity_context_unavailable";
  bool membership_observed = false;
  std::vector<BattleNativeActivityContextMatchV1> matched_contexts_in_native_order;

  friend bool operator==(const BattleNativeActivityContextV1 &,
                         const BattleNativeActivityContextV1 &) = default;
};
} // namespace xar::game

namespace xar::ck3_12003 {
// Pure raw reads of both native collections and the exact .3 E-prefix operands.
// The existing paused ForUnits/transition publishers attach this owner leaf.
game::BattleNativeActivityContextV1 ReadOwnerNativeActivityContextInputsV1(
    const ck3_12002::BattleBindings &, std::int32_t owner_id) noexcept;
} // namespace xar::ck3_12003

