#pragma once
#include "xar_bridge/religion_reform12002_choices.hpp"
#include <optional>
#include <string>
#include <vector>

namespace xar::ck3_12002::religion_reform {
struct DraftDoctrineSourceChoice {
  std::uint32_t source_index{};
  std::string doctrine_key;
  bool currently_selected{}, duplicate_excluded{};
  // Null means this native short-circuit branch was not evaluated.
  std::optional<bool> passed_shown, native_can_pick, native_knows_doctrine, native_has_prophet;
  bool final_selectable{};
};
struct DraftDoctrineChoiceSlot {
  std::uint32_t slot_index{};
  std::string group_key, selected_doctrine_key;
  std::vector<DraftDoctrineSourceChoice> sources;
};
struct DraftFullDoctrineChoices {
  bool available{}, draft_observed{}, doctrine_gates_complete{};
  std::string failure="not_bound";
  std::uint64_t capture_epoch{};
  std::int32_t date_raw{};
  std::uint32_t played_character_id{};
  std::optional<std::uint32_t> source_rite_id;
  std::vector<DraftDoctrineChoiceSlot> slots;
};
bool ReadCurrentDraftFullDoctrineChoices12002(const DraftChoiceBindings &bindings,
  std::uint64_t capture_epoch, DraftFullDoctrineChoices &output) noexcept;
std::string SerializeCurrentDraftFullDoctrineChoices12002(const DraftFullDoctrineChoices &value);
} // namespace xar::ck3_12002::religion_reform
