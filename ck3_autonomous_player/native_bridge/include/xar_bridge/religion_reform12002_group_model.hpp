#pragma once
#include "xar_bridge/religion_reform12002_choices.hpp"
namespace xar::ck3_12002::religion_reform {
inline constexpr std::size_t kDraftSelectedSlotsOffset = 0x790;
inline constexpr std::size_t kActualDraftSlotStride = 0x48;
inline constexpr std::size_t kGroupDefinitionSourcesOffset = 0x140;
inline constexpr std::size_t kCurrentCategorySlotOffset = 0x50;
struct DraftSlotSource {
  std::uint32_t selected_array_index{};
  std::string selected_definition_key, group_key;
  std::vector<std::string> group_source_definition_keys;
};
struct MaterializedTenetGate {
  std::string tenet_key;
  std::uint32_t popup_group_index{}, popup_item_index{};
  std::uint8_t native_pick_source{};
  bool final_can_pick{};
};
struct DraftGroupModel {
  bool available{}, draft_observed{}, category_materialized{}, current_tenet_gate_complete{};
  std::string failure{"bindings_unavailable"};
  std::uint64_t capture_epoch{};
  std::int32_t date_raw{}, current_category_slot{-1};
  std::uint32_t played_character_id{0xFFFFFFFFU}, founder_character_id{0xFFFFFFFFU};
  std::optional<std::uint32_t> source_rite_id;
  std::optional<std::string> current_group_key, current_selected_definition_key;
  std::uint32_t current_doctrine_cache_count{}, current_tenet_source_count{}, current_tenet_group_count{};
  std::vector<DraftSlotSource> selected_slots;
  std::vector<MaterializedTenetGate> current_tenet_choices;
};
// Actual selected-slot group sources, plus the current materialized caches.
// Source definitions are not constructed items or all-group legality results.
bool ReadCurrentDraftGroupModel12002(const DraftChoiceBindings &bindings,
    std::uint64_t capture_epoch, DraftGroupModel &output) noexcept;
std::string SerializeCurrentDraftGroupModel12002(const DraftGroupModel &value);
} // namespace xar::ck3_12002::religion_reform
