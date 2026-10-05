#pragma once

#include <array>
#include <cstdint>
#include <optional>
#include <string>

namespace xar::game {
struct BattleCurrentOwnModifierAmountV1 {
  std::optional<std::int64_t> amount_raw;
  std::string unavailable_reason;
  friend bool operator==(const BattleCurrentOwnModifierAmountV1 &,
                         const BattleCurrentOwnModifierAmountV1 &) = default;
};
struct BattleCurrentOwnModifierSideV1 {
  std::int32_t side_index = 0;
  std::int32_t selected_character_id_raw = -1;
  std::optional<std::int32_t> resolved_character_id_raw;
  std::optional<bool> used_native_fallback;
  std::string selection_unavailable_reason;
  BattleCurrentOwnModifierAmountV1 combat_side_aggregate;
  BattleCurrentOwnModifierAmountV1 selected_character_aggregate;
  friend bool operator==(const BattleCurrentOwnModifierSideV1 &,
                         const BattleCurrentOwnModifierSideV1 &) = default;
};
struct BattleCurrentOwnNestedModifierV1 {
  std::array<BattleCurrentOwnModifierSideV1, 2> sides;
  friend bool operator==(const BattleCurrentOwnNestedModifierV1 &,
                         const BattleCurrentOwnNestedModifierV1 &) = default;
};
} // namespace xar::game
