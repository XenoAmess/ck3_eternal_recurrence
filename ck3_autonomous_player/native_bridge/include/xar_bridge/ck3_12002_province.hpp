#pragma once

#include "xar_bridge/ck3_12002.hpp"
#include "xar_bridge/game_contract.hpp"

#include <cstdint>
#include <span>
#include <vector>

namespace xar::ck3_12002 {

inline constexpr std::uintptr_t kProvinceSiegeStorageSlotRva = 0x5D1EC88;
inline constexpr std::uintptr_t kProvinceUnitStorageSlotRva = 0x5D1E380;
inline constexpr std::uintptr_t kObjectiveTitleStorageSlotRva = 0x5D1DAF8;
inline constexpr std::size_t kObjectiveTitleTemplateOffset = 0x48;
inline constexpr std::size_t kObjectiveTitleTemplateTierOffset = 0x64;
inline constexpr std::size_t kObjectiveTitleChildrenOffset = 0x110;
inline constexpr std::size_t kObjectiveProvinceArrayOffset = 0x140;
inline constexpr std::size_t kObjectiveProvinceCountOffset = 0x14C;
inline constexpr std::size_t kObjectiveProvinceOccupationIdOffset = 0x73C;
inline constexpr std::size_t kObjectiveProvinceActiveSiegeIdOffset = 0x788;
inline constexpr std::size_t kObjectiveProvinceFortLevelOffset = 0x850;
inline constexpr std::size_t kObjectiveProvinceMagicOffset = 0x85C;
inline constexpr std::size_t kObjectiveSiegeProvinceOffset = 0x200;
inline constexpr std::size_t kObjectiveSiegeArmyIdOffset = 0x208;
inline constexpr std::size_t kObjectiveSiegeCurrentWorkOffset = 0x3D0;
inline constexpr std::size_t kObjectiveSiegeBreachOffset = 0x3D8;
inline constexpr std::size_t kObjectiveSiegeAssaultOffset = 0x44C;

using ProvinceOccupiedGetter = bool (*)(void *);
using ProvinceIntGetter = std::int32_t (*)(void *);
using SiegeFixedGetter = std::int64_t *(*)(void *, std::int64_t *);
using SiegeDailyAssaultGetter = std::int64_t *(*)(void *, std::int64_t *, std::int32_t);
using SiegeAssaultValidator = bool (*)(std::int32_t, std::int32_t, std::int32_t, void *);
using ObjectiveTitleProvinceGetter = void *(*)(void *);

struct ProvinceBindings {
  bool enabled = false;
  void **game_state_slot = nullptr;
  void **character_storage_slot = nullptr;
  void **unit_storage_slot = nullptr;
  void **siege_storage_slot = nullptr;
  void **landed_title_storage_slot = nullptr;
  ObjectiveTitleProvinceGetter title_province = nullptr;
  ProvinceOccupiedGetter is_occupied = nullptr;
  ProvinceIntGetter fort_level = nullptr;
  ProvinceIntGetter garrison_size = nullptr;
  ProvinceIntGetter besieging_strength = nullptr;
  SiegeFixedGetter siege_progress = nullptr;
  SiegeFixedGetter siege_total_work = nullptr;
  ProvinceIntGetter siege_days_left = nullptr;
  SiegeDailyAssaultGetter assault_daily_progress = nullptr;
  ProvinceIntGetter assault_daily_casualties = nullptr;
  SiegeAssaultValidator validate_start_assault = nullptr;
  SiegeAssaultValidator validate_stop_assault = nullptr;
};

ProvinceBindings BindProvinceImage(std::uintptr_t image_base,
                                   std::string_view executable_sha256) noexcept;
void *ResolveObjectiveProvince(const ProvinceBindings &, std::int32_t province_id) noexcept;
void *ResolveObjectiveSiege(const ProvinceBindings &, std::int32_t siege_id) noexcept;
void *ResolveObjectiveTitle(const ProvinceBindings &, std::int32_t title_id) noexcept;
bool CollectObjectiveProvinceIds(const ProvinceBindings &,
                                std::span<const std::int32_t> targeted_title_ids,
                                std::vector<std::int32_t> &province_ids) noexcept;

// The runtime caller must execute on the owning thread. Rich subgraph getters
// require its paused snapshot; false reads only the occupation/fort scalars.
game::WarObjectiveProvinceState ReadObjectiveProvince(
    const ProvinceBindings &, std::int32_t province_id,
    const std::vector<game::ArmySnapshot> &armies,
    std::int32_t played_character_id = -1,
    bool include_paused_details = true) noexcept;

} // namespace xar::ck3_12002
