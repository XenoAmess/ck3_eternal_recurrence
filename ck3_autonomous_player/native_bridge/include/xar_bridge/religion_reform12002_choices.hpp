#pragma once

#include "xar_bridge/religion_reform12002_window.hpp"
#include "xar_bridge/religion_doctrine12002_choices.hpp"
#include <vector>

namespace xar::ck3_12002::religion_reform {
inline constexpr std::size_t kDraftTopScopeOffset = 0xD0;
inline constexpr std::size_t kDraftDoctrineCategoryOffset = 0x888;
inline constexpr std::size_t kCategoryDoctrineArrayOffset = 0x20;
inline constexpr std::size_t kDoctrineItemStride = 0x48;
inline constexpr std::size_t kDraftTenetGroupArrayOffset = 0x7A8;
inline constexpr std::size_t kTenetGroupStride = 0x20;
inline constexpr std::size_t kGroupTenetArrayOffset = 8;
inline constexpr std::size_t kTenetItemStride = 0x70;
inline constexpr std::size_t kChoiceDefinitionOffset = 0x28;
inline constexpr std::size_t kTenetPickSourceOffset = 0x24;
inline constexpr std::uintptr_t kTenetItemCanPickRva = 0xEE0AD0;
inline constexpr std::uintptr_t kChoiceTriggerEvalRva = 0x372DF30;
inline constexpr std::uintptr_t kChoiceHasPerkRva = 0x2919070;
inline constexpr std::uintptr_t kChoicePerkDatabaseGlobalRva = 0x5C67128;
inline constexpr std::size_t kProphetPerkCacheOffset = 0xEF0;

using ChoiceTriggerEval = bool (*)(const void *, const void *);
using TenetItemCanPick = bool (*)(const void *, void *, const void *);
using ChoiceHasPerk = bool (*)(void *, const void *);
struct DraftChoiceBindings {
  DraftWindowBindings window{};
  religion::doctrine12002::NativeKnowsDoctrine knows_doctrine = nullptr;
  ChoiceTriggerEval evaluate_trigger = nullptr;
  TenetItemCanPick tenet_can_pick = nullptr;
  ChoiceHasPerk has_perk = nullptr;
  void *const *perk_database_global = nullptr;
};
struct DraftDoctrineChoice {
  std::string doctrine_key, group_key;
  std::uint32_t popup_index = 0;
  bool native_can_pick = false;
  std::optional<bool> native_knows_doctrine, native_has_prophet;
  bool button_enabled = false;
};
struct DraftTenetChoice {
  std::string tenet_key;
  std::uint32_t popup_group_index = 0, popup_item_index = 0;
  std::uint8_t native_pick_source = 0;
  bool native_can_pick = false;
};
struct DraftChoices {
  bool available = false, draft_observed = false;
  std::string failure = "bindings_unavailable";
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::uint32_t played_character_id = 0xFFFFFFFFU;
  std::optional<std::uint32_t> source_rite_id;
  std::vector<DraftDoctrineChoice> doctrines;
  std::vector<DraftTenetChoice> tenets;
};
DraftChoiceBindings BindCurrentDraftChoices12002(std::uintptr_t module_base,
    std::string_view executable_sha256) noexcept;
// Existing paused owner only. Reads already-materialized current popup arrays;
// never generates candidates, opens a window, selects a row, or creates a Rite.
bool ReadCurrentDraftChoices12002(const DraftChoiceBindings &bindings,
    std::uint64_t capture_epoch, DraftChoices &output) noexcept;
std::string SerializeCurrentDraftChoices12002(const DraftChoices &value);
} // namespace xar::ck3_12002::religion_reform
