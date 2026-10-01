#pragma once

#include "xar_bridge/religion_reform12002_window.hpp"
#include <optional>
#include <string>
#include <vector>

namespace xar::ck3_12002::religion_reform {

inline constexpr std::uintptr_t kTenetSourcesDatabaseGlobalRva = 0x5D1DEB8;
inline constexpr std::uintptr_t kTenetSourcesRiteStorageGlobalRva = 0x5D1E2F8;
inline constexpr std::uintptr_t kTenetSourcesFaithStorageGlobalRva = 0x5D1E300;
inline constexpr std::uintptr_t kTenetSourcesPerkDatabaseGlobalRva = 0x5C67128;
inline constexpr std::uintptr_t kTenetSourceNativeFilterRva = 0x14F2030;
inline constexpr std::uintptr_t kTenetSourceRawStatusRva = 0x24F88A0;
inline constexpr std::uintptr_t kTenetSourceActorFaithRawStatusRva = 0x24425B0;
inline constexpr std::uintptr_t kTenetSourceActorExtraCollectionRva = 0x28B0B60;
inline constexpr std::uintptr_t kTenetSourceActorPerksCollectionRva = 0x2919360;
inline constexpr std::uintptr_t kTenetSourceContainsRva = 0xA11CC0;
inline constexpr std::uintptr_t kTenetSourceTriggerRva = 0x372DF30;

using TenetSourcesFilter = bool (*)(const void *, const void *);
using TenetSourcesStatus = std::uint8_t (*)(void *, const void *);
using TenetSourcesCollection = const void *(*)(void *);
using TenetSourcesContains = bool (*)(const void *, const void *);
using TenetSourcesTrigger = bool (*)(const void *, const void *);

struct TenetSourcesBindings {
  bool enabled{};
  DraftWindowBindings window{};
  void *const *tenet_database_global{};
  void *const *rite_storage_global{};
  void *const *faith_storage_global{};
  void *const *perk_database_global{};
  TenetSourcesFilter source_filter{};
  TenetSourcesStatus source_main_rite_status{}, actor_faith_status{};
  TenetSourcesCollection actor_extra_collection{}, actor_perks_collection{};
  TenetSourcesContains contains{};
  TenetSourcesTrigger evaluate_trigger{};
};

struct DraftTenetSourceSlot {
  std::uint32_t slot_index{};
  std::string selected_tenet_key;
};
struct DraftTenetSource {
  std::uint32_t source_index{};
  std::string tenet_key;
  bool already_selected{}, duplicate_excluded{};
  bool source_can_materialize{}, filtered_out{};
  std::uint8_t native_status_raw{}, actor_faith_status_raw{};
  bool native_extra_knowledge{}, native_has_prophet{}, knowledge{};
  bool passed_shown{}, passed_selectable_trigger{}, native_can_pick{};
  bool final_selectable{};
};
struct DraftTenetSources {
  bool available{}, draft_observed{}, tenet_gates_complete{};
  std::string failure{"bindings_unavailable"};
  std::uint64_t capture_epoch{};
  std::int32_t date_raw{};
  std::uint32_t played_character_id{0xFFFFFFFFU};
  std::optional<std::uint32_t> source_rite_id, source_faith_id, source_main_rite_id;
  bool raw_category_exemption_present{};
  std::optional<std::string> raw_category_exemption_key;
  // All actual slots share this current-draft native source/final predicate.
  // They are not separate fabricated DoctrineCategoryWindow instances.
  std::vector<DraftTenetSourceSlot> slots;
  std::vector<DraftTenetSource> sources;
};

TenetSourcesBindings BindCurrentDraftTenetSources12002(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;
// Existing paused application-main owner only. Actual window/category/registry
// objects are read directly; no constructors, ShowWindow, selection or action.
bool ReadCurrentDraftTenetSources12002(const TenetSourcesBindings &bindings,
    std::uint64_t capture_epoch, DraftTenetSources &output) noexcept;
std::string SerializeCurrentDraftTenetSources12002(const DraftTenetSources &value);

} // namespace xar::ck3_12002::religion_reform
