#pragma once

#include "xar_bridge/ck3_12002_phase.hpp"
#include "xar_bridge/game_contract.hpp"

#include <cstring>

namespace xar::ck3_12002 {
struct BattleCurrentDynamicComponentBindings12003 {
  bool enabled = false;
  void **character_storage = nullptr;
  void **null_character = nullptr;
  PhaseRelationKind relation = nullptr;
  PhaseCommanderDynamic commander = nullptr;
  PhaseSideModifier side_aggregate = nullptr;
};
namespace current_components_detail {
template <typename T> T Load(const void *source, std::size_t offset) noexcept {
  T result{};
  std::memcpy(&result, static_cast<const std::byte *>(source) + offset, sizeof(result));
  return result;
}
inline void *Selected(const BattleCurrentDynamicComponentBindings12003 &b,
                      game::BattleCurrentDynamicComponentSideV1 &side) {
  if (!b.character_storage) {
    side.selection_unavailable_reason = "selected_character_storage_5C67568_unbound";
    return nullptr;
  }
  void *character = nullptr;
  const auto id = side.selected_character_id_raw;
  const auto index = static_cast<std::uint32_t>(id) & 0xFFFFFFU;
  void *storage = *b.character_storage;
  if (storage && index < Load<std::uint32_t>(storage, 0x2C)) {
    const void *rows = Load<const void *>(storage, 0x20);
    if (rows) character = Load<void *>(rows, static_cast<std::size_t>(index) * 16 + 8);
    if (character && Load<std::int32_t>(character, 0x18) != id) character = nullptr;
  }
  const bool fallback = character == nullptr;
  if (fallback) character = b.null_character ? *b.null_character : nullptr;
  if (!character) {
    side.selection_unavailable_reason = "selected_character_fallback_5C67570_unavailable";
    return nullptr;
  }
  side.resolved_character_id_raw = Load<std::int32_t>(character, 0x18);
  side.used_native_fallback = fallback;
  return character;
}
} // namespace current_components_detail

// Actual current groups from the same null-sink ABI used by258A470. Never
// select/populate/refresh or invoke the mutating258B510 wrapper.
inline game::BattleCurrentDynamicComponentsV1 ReadCurrentDynamicComponents12003(
    void *combat, const BattleCurrentDynamicComponentBindings12003 &b) {
  using current_components_detail::Load;
  game::BattleCurrentDynamicComponentsV1 result;
  for (std::size_t index = 0; index < result.sides.size(); ++index) {
    auto &side = result.sides[index];
    side.side_index = static_cast<std::int32_t>(index);
    side.current_roll_points = Load<std::int32_t>(combat, 0x6D0 + index * 4);
    side.selected_character_id_raw = Load<std::int32_t>(combat, 0x94 + index * 0x348);
    void *selected = current_components_detail::Selected(b, side);
    if (b.relation) side.relation_kind_raw = b.relation(combat, side.side_index);
    else side.relation_unavailable_reason = "current_relation_getter_2589810_unbound";
    if (!side.relation_kind_raw) {
      side.commander_unavailable_reason = "current_relation_getter_2589810_unavailable";
      side.side_aggregate_unavailable_reason = "current_relation_getter_2589810_unavailable";
      continue;
    }
    std::int64_t raw = 0;
    if (!selected) side.commander_unavailable_reason = side.selection_unavailable_reason;
    else if (!b.commander) side.commander_unavailable_reason = "current_commander_getter_2589E10_unbound";
    else if (b.commander(combat, &raw, selected, side.side_index, *side.relation_kind_raw, nullptr) != &raw)
      side.commander_unavailable_reason = "current_commander_getter_2589E10_output_unavailable";
    else side.commander_dynamic_raw = raw;
    raw = 0;
    void *aggregate = static_cast<std::byte *>(combat) + 0x130 + index * 0x348;
    if (!b.side_aggregate) side.side_aggregate_unavailable_reason = "current_side_aggregate_getter_25899C0_unbound";
    else if (b.side_aggregate(combat, &raw, aggregate, side.side_index, *side.relation_kind_raw, nullptr) != &raw)
      side.side_aggregate_unavailable_reason = "current_side_aggregate_getter_25899C0_output_unavailable";
    else side.side_aggregate_dynamic_raw = raw;
  }
  return result;
}
} // namespace xar::ck3_12002
