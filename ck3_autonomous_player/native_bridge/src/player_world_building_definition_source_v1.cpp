#include "player_world_building_definition_source_v1.hpp"
#include "player_world_building_authored_income_v1.hpp"

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <string>
#include <unordered_set>
#include <utility>
#include <vector>

namespace xar::ck3_11906 {
namespace {

// Stock county construction iterator 0x1922C52 calls the CBuildingType
// manager getter 0x864750, then reads its +0x68/+0x74 definition vector.
// 0xC8CE80/0x57BFFF8 is the peer CCourtTypeSetting registry (R735).
constexpr std::uintptr_t kWorldBuildingManagerSlotRva = 0x570C108;
constexpr std::uintptr_t kBuildingTypePrimaryVtableRva = 0x44046C0;
constexpr std::uintptr_t kExactExeImageSize = 0x5C2D000;
constexpr std::uintptr_t kGameStateSlotRva = 0x570E068;
constexpr std::uintptr_t kCharacterStorageSlotRva = 0x570C130;
constexpr std::uintptr_t kCharacterFallbackSlotRva = 0x570C138;
constexpr std::uintptr_t kGuiPlayerCharacterIdRva = 0x4FE7EE0;
constexpr std::size_t kGameDataOffset = 0xA0;
constexpr std::size_t kProvinceArrayOffset = 0x140;
constexpr std::size_t kProvinceCountOffset = 0x14C;
constexpr std::size_t kProvinceIdentityOffset = 0x10;
constexpr std::size_t kProvinceSlotsOffset = 0x620;
constexpr std::size_t kProvinceSlotCountOffset = 0x24;
// Stock player final-legality 0x295CD60 walks the mode-0 slot array at
// slots+0x18, in 0x10-byte records, comparing each record's first pointer
// with the candidate CBuildingType*. The active queue lives at +0x70.
constexpr std::size_t kProvinceBuiltSlotsDataOffset = 0x18;
constexpr std::size_t kProvinceBuiltSlotStride = 0x10;
// Stock building command executor 0x26CD290 calls 0x21F6860; that routine
// writes the in-progress CBuildingType* at slots+0x70, selected slot at
// slots+0x78, and initiating CharacterID at slots+0xE0.
constexpr std::size_t kProvinceActiveBuildingOffset = 0x70;
constexpr std::size_t kProvinceActiveSlotOffset = 0x78;
constexpr std::size_t kProvinceActiveInitiatorOffset = 0xE0;
constexpr std::size_t kRegistryDataOffset = 0x68;
constexpr std::size_t kRegistryCapacityOffset = 0x70;
constexpr std::size_t kRegistryCountOffset = 0x74;
constexpr std::size_t kBuildingTypeIdentityOffset = 0x10;
// Exact CBuildingType RTTI includes CGameDatabaseObject. Its MSVC string key
// follows ordinal +0x10 and hash +0x14, as in the stock database-object ABI.
constexpr std::size_t kBuildingKeyOffset = 0x18;
constexpr std::size_t kMsvcStringSizeOffset = 0x10;
constexpr std::size_t kMsvcStringCapacityOffset = 0x18;
constexpr std::size_t kMaxBuildingKeyBytes = 127;
constexpr std::size_t kCharacterIdentityOffset = 0x18;
constexpr std::size_t kCharacterExtensionOffset = 0x1A8;
constexpr std::size_t kCharacterGoldOffset = 0x100;
constexpr std::size_t kStorageDataOffset = 0x20;
constexpr std::size_t kStorageCapacityOffset = 0x2C;
constexpr std::int32_t kMaxWorldDefinitions = 16'384;
constexpr std::int32_t kMaxProvinceSlots = 64;
constexpr std::int32_t kMaxProvinceCount = 1'000'000;
constexpr std::int32_t kMaxCharacterStorageCapacity = 4'194'304;

bool Add(std::uintptr_t base, std::size_t offset,
         std::uintptr_t &out) noexcept {
  if (base == 0 ||
      offset > std::numeric_limits<std::uintptr_t>::max() - base) {
    return false;
  }
  out = base + offset;
  return true;
}

template <typename T>
bool Read(const CampaignRootAccessV1 &access, std::uintptr_t base,
          std::size_t offset, T &out) noexcept {
  std::uintptr_t address = 0;
  return Add(base, offset, address) && access.read_memory != nullptr &&
         access.read_memory(access.context,
                            reinterpret_cast<const void *>(address),
                            &out, sizeof(out));
}

bool ReadBuildingKey(const CampaignRootAccessV1 &access,
                     std::uintptr_t definition, std::string &out) {
  std::uintptr_t native_string = 0;
  std::size_t size = 0;
  std::size_t capacity = 0;
  if (!Add(definition, kBuildingKeyOffset, native_string) ||
      !Read(access, native_string, kMsvcStringSizeOffset, size) ||
      !Read(access, native_string, kMsvcStringCapacityOffset, capacity) ||
      size == 0 || size > capacity || size > kMaxBuildingKeyBytes) {
    return false;
  }
  std::uintptr_t bytes = native_string;
  if (capacity > 15 &&
      (!Read(access, native_string, 0, bytes) || bytes == 0)) {
    return false;
  }
  out.resize(size);
  if (!access.read_memory(access.context,
                          reinterpret_cast<const void *>(bytes),
                          out.data(), size) ||
      !std::all_of(out.begin(), out.end(), [](char value) {
        return (value >= 'a' && value <= 'z') ||
               (value >= '0' && value <= '9') || value == '_';
      })) {
    out.clear();
    return false;
  }
  return true;
}

bool ReadWorldDefinitions(const CampaignRootAccessV1 &access,
                          std::uintptr_t module,
                          std::vector<std::pair<std::int32_t,
                                                std::uintptr_t>> &out,
                          std::int32_t &count,
                          PlayerWorldBuildingFailureV1 &failure,
                          PlayerWorldDefinitionIdentityDiagnosticV1 &diagnostic) {
  failure = PlayerWorldBuildingFailureV1::registry_source;
  std::uintptr_t manager = 0;
  std::uintptr_t data = 0;
  std::int32_t capacity = 0;
  count = 0;
  if (!Read(access, module, kWorldBuildingManagerSlotRva, manager) ||
      manager == 0 || !Read(access, manager, kRegistryDataOffset, data) ||
      !Read(access, manager, kRegistryCapacityOffset, capacity) ||
      !Read(access, manager, kRegistryCountOffset, count) ||
      capacity < 0 || count < 0 || count > capacity ||
      count > kMaxWorldDefinitions || (count > 0 && data == 0)) {
    return false;
  }
  diagnostic.registry_count = count;
  out.reserve(static_cast<std::size_t>(count));
  std::unordered_set<std::int32_t> seen_ids;
  seen_ids.reserve(static_cast<std::size_t>(count));
  failure = PlayerWorldBuildingFailureV1::definition_identity;
  for (std::int32_t index = 0; index < count; ++index) {
    std::uintptr_t definition = 0;
    std::uintptr_t vtable = 0;
    std::int32_t building_type_id = -1;
    diagnostic.failed_index = index;
    if (!Read(access, data,
              static_cast<std::size_t>(index) * sizeof(definition),
              definition)) {
      diagnostic.stage = PlayerWorldDefinitionIdentityStageV1::element_read;
      return false;
    }
    if (definition == 0) {
      diagnostic.stage = PlayerWorldDefinitionIdentityStageV1::element_null;
      return false;
    }
    if (!Read(access, definition, 0, vtable)) {
      diagnostic.stage = PlayerWorldDefinitionIdentityStageV1::vtable_read;
      return false;
    }
    if (vtable >= module && vtable - module < kExactExeImageSize) {
      diagnostic.has_observed_vtable_rva = true;
      diagnostic.observed_vtable_rva =
          static_cast<std::uint64_t>(vtable - module);
    }
    if (vtable != module + kBuildingTypePrimaryVtableRva) {
      diagnostic.stage = PlayerWorldDefinitionIdentityStageV1::vtable_mismatch;
      return false;
    }
    if (!Read(access, definition, kBuildingTypeIdentityOffset,
              building_type_id)) {
      diagnostic.stage =
          PlayerWorldDefinitionIdentityStageV1::building_type_id_read;
      return false;
    }
    diagnostic.has_observed_building_type_id = true;
    diagnostic.observed_building_type_id = building_type_id;
    if (building_type_id < 0) {
      diagnostic.stage =
          PlayerWorldDefinitionIdentityStageV1::building_type_id_negative;
      return false;
    }
    if (!seen_ids.insert(building_type_id).second) {
      diagnostic.stage =
          PlayerWorldDefinitionIdentityStageV1::building_type_id_duplicate;
      return false;
    }
    out.emplace_back(building_type_id, definition);
    diagnostic.failed_index = -1;
    diagnostic.has_observed_vtable_rva = false;
    diagnostic.has_observed_building_type_id = false;
  }
  failure = PlayerWorldBuildingFailureV1::none;
  return true;
}

bool ReadProvinceSlots(const CampaignRootAccessV1 &access,
                       std::uintptr_t module, std::int32_t province_id,
                       std::int32_t &slot_count,
                       std::uintptr_t &province_pointer) noexcept {
  std::uintptr_t game_state = 0;
  std::uintptr_t game_data = 0;
  std::uintptr_t provinces = 0;
  std::uintptr_t province = 0;
  std::int32_t province_count = 0;
  std::int32_t observed_id = -1;
  slot_count = 0;
  province_pointer = 0;
  return Read(access, module, kGameStateSlotRva, game_state) &&
         game_state != 0 &&
         Read(access, game_state, kGameDataOffset, game_data) &&
         game_data != 0 &&
         Read(access, game_data, kProvinceArrayOffset, provinces) &&
         Read(access, game_data, kProvinceCountOffset, province_count) &&
         provinces != 0 && province_id > 0 &&
         province_count > 0 && province_count <= kMaxProvinceCount &&
         province_id < province_count &&
         Read(access, provinces,
              static_cast<std::size_t>(province_id) * sizeof(province),
              province) && province != 0 &&
         Read(access, province, kProvinceIdentityOffset, observed_id) &&
         observed_id == province_id &&
         Read(access, province,
              kProvinceSlotsOffset + kProvinceSlotCountOffset,
              slot_count) &&
         slot_count >= 0 && slot_count <= kMaxProvinceSlots &&
         (province_pointer = province) != 0;
}

bool ReadPlayedCharacterGold(const CampaignRootAccessV1 &access,
                             std::uintptr_t module,
                             std::int32_t played_character_id,
                             std::int64_t &gold_raw) noexcept {
  gold_raw = 0;
  if (played_character_id <= 0) return false;
  std::uintptr_t storage = 0;
  std::uintptr_t fallback = 0;
  std::uintptr_t data = 0;
  std::uintptr_t character = 0;
  std::uintptr_t extension = 0;
  std::int32_t capacity = 0;
  std::int32_t observed_id = -1;
  if (!Read(access, module, kCharacterStorageSlotRva, storage) ||
      !Read(access, module, kCharacterFallbackSlotRva, fallback) ||
      storage == 0 || !Read(access, storage, kStorageDataOffset, data) ||
      !Read(access, storage, kStorageCapacityOffset, capacity) ||
      data == 0 || capacity <= 0 ||
      capacity > kMaxCharacterStorageCapacity) {
    return false;
  }
  const auto index = static_cast<std::uint32_t>(played_character_id) &
                     0x00FFFFFFU;
  if (index >= static_cast<std::uint32_t>(capacity) ||
      !Read(access, data, static_cast<std::size_t>(index) * 0x10 + 8,
            character) ||
      character == 0 || character == fallback ||
      !Read(access, character, kCharacterIdentityOffset, observed_id) ||
      observed_id != played_character_id ||
      !Read(access, character, kCharacterExtensionOffset, extension)) {
    return false;
  }
  // The exact stock GetGold/war-finance source treats a missing extension
  // as legitimate zero. A failed memory read is unavailable instead.
  return extension == 0 ||
         Read(access, extension, kCharacterGoldOffset, gold_raw);
}

PlayerWorldBuildingSourceResultV1 Failed(
    PlayerWorldBuildingFailureV1 failure,
    PlayerWorldDefinitionIdentityDiagnosticV1 diagnostic = {}) noexcept {
  PlayerWorldBuildingSourceResultV1 result{};
  result.failure = failure;
  result.definition_identity_diagnostic = diagnostic;
  return result;
}

} // namespace

PlayerWorldBuildingSourceResultV1
ReadPlayerWorldBuildingDefinitionSourcesV1(
    std::uintptr_t module_base, bool exact_build_admitted,
    const PlayerWorldBuildingSourceAccessV1 &access,
    const PlayerWorldBuildingSourceRequestV1 &request) noexcept {
  const auto &campaign = access.campaign;
  if (module_base == 0 || !exact_build_admitted) {
    return Failed(PlayerWorldBuildingFailureV1::exact_build);
  }
  if (campaign.is_main_thread == nullptr ||
      !campaign.is_main_thread(campaign.context)) {
    return Failed(PlayerWorldBuildingFailureV1::application_main);
  }
  if (campaign.capture_frame == nullptr || campaign.read_memory == nullptr ||
      request.max_native_checks < 0 || request.max_native_checks > 4096 ||
      request.max_legal_samples < 0 || request.max_legal_samples > 64) {
    return Failed(PlayerWorldBuildingFailureV1::paused_frame);
  }
  game::CampaignRootFrameV1 before{};
  if (!campaign.capture_frame(campaign.context, before) ||
      before.snapshot_revision != request.expected_snapshot_revision ||
      !before.paused || !before.map_ready ||
      !before.has_played_character || !before.played_character_alive ||
      before.played_character_id <= 0) {
    return Failed(PlayerWorldBuildingFailureV1::paused_frame);
  }
  try {
    PlayerWorldBuildingSourceResultV1 result{};
    const auto held = ReadPlayerHeldConstructionModelSourcesV1(
        module_base, true, campaign,
        {request.expected_snapshot_revision});
    if (held.status !=
            PlayerHeldConstructionModelStatusV1::sources_available ||
        held.failure != PlayerHeldConstructionModelFailureV1::none ||
        held.player_character_id != before.played_character_id ||
        held.date_raw != before.date_raw ||
        held.snapshot_revision != before.snapshot_revision) {
      return Failed(PlayerWorldBuildingFailureV1::held_source);
    }
    std::int32_t stock_gui_actor_id = -1;
    if (!Read(campaign, module_base, kGuiPlayerCharacterIdRva,
              stock_gui_actor_id) ||
        stock_gui_actor_id != before.played_character_id) {
      return Failed(PlayerWorldBuildingFailureV1::player_actor_binding);
    }
    result.directly_held_barony_provinces =
        held.directly_held_barony_provinces;
    auto sample_holding_order = result.directly_held_barony_provinces;
    if (request.preferred_held_province_id > 0) {
      const auto found = std::find_if(
          sample_holding_order.begin(),
          sample_holding_order.end(),
          [&request](const auto &row) {
            return row.province_id == request.preferred_held_province_id;
          });
      if (found == sample_holding_order.end()) {
        return Failed(PlayerWorldBuildingFailureV1::held_source);
      }
      std::rotate(sample_holding_order.begin(), found,
                  found + 1);
    }
    std::vector<std::pair<std::int32_t, std::uintptr_t>> definitions;
    PlayerWorldBuildingFailureV1 registry_failure =
        PlayerWorldBuildingFailureV1::registry_source;
    if (!ReadWorldDefinitions(campaign, module_base, definitions,
                              result.definition_source_count,
                              registry_failure,
                              result.definition_identity_diagnostic)) {
      return Failed(registry_failure,
                    result.definition_identity_diagnostic);
    }
    result.active_constructions.reserve(
        result.directly_held_barony_provinces.size());
    result.completed_buildings_observed = true;
    for (const auto &holding : result.directly_held_barony_provinces) {
      std::int32_t slot_count = 0;
      std::uintptr_t province = 0;
      std::uintptr_t active_definition = 0;
      if (!ReadProvinceSlots(campaign, module_base, holding.province_id,
                             slot_count, province) ||
          !Read(campaign, province,
                kProvinceSlotsOffset + kProvinceActiveBuildingOffset,
                active_definition)) {
        return Failed(PlayerWorldBuildingFailureV1::construction_state);
      }
      if (result.completed_buildings_observed) {
        std::uintptr_t built_slots = 0;
        if (!Read(campaign, province,
                  kProvinceSlotsOffset + kProvinceBuiltSlotsDataOffset,
                  built_slots) || (slot_count > 0 && built_slots == 0)) {
          result.completed_buildings_observed = false;
        } else {
          for (std::int32_t slot = 0; slot < slot_count; ++slot) {
            std::uintptr_t built_definition = 0;
            if (!Read(campaign, built_slots,
                      static_cast<std::size_t>(slot) * kProvinceBuiltSlotStride,
                      built_definition)) {
              result.completed_buildings_observed = false;
              break;
            }
            if (built_definition == 0) continue;
            const auto built_match = std::find_if(
                definitions.begin(), definitions.end(),
                [built_definition](const auto &definition) {
                  return definition.second == built_definition;
                });
            if (built_match == definitions.end()) {
              result.completed_buildings_observed = false;
              break;
            }
            result.completed_buildings.push_back({
                holding.barony_title_id, holding.province_id,
                built_match->first, slot});
          }
        }
        if (!result.completed_buildings_observed) {
          result.completed_buildings.clear();
        }
      }
      PlayerWorldActiveConstructionV1 state{};
      state.barony_title_id = holding.barony_title_id;
      state.province_id = holding.province_id;
      if (active_definition != 0) {
        const auto match = std::find_if(
            definitions.begin(), definitions.end(),
            [active_definition](const auto &definition) {
              return definition.second == active_definition;
            });
        if (match == definitions.end() ||
            !Read(campaign, province,
                  kProvinceSlotsOffset + kProvinceActiveSlotOffset,
                  state.slot_index) ||
            !Read(campaign, province,
                  kProvinceSlotsOffset + kProvinceActiveInitiatorOffset,
                  state.initiator_character_id) ||
            state.slot_index < 0 || state.slot_index >= slot_count ||
            state.initiator_character_id <= 0) {
          return Failed(PlayerWorldBuildingFailureV1::construction_state);
        }
        state.active = true;
        state.building_type_id = match->first;
      }
      result.active_constructions.push_back(state);
    }
    if (access.final_legality != nullptr &&
        request.max_native_checks > 0 &&
        request.max_legal_samples > 0) {
      if (access.native_cost != nullptr) {
        if (!ReadPlayedCharacterGold(campaign, module_base,
                                     before.played_character_id,
                                     result.player_gold_raw)) {
          return Failed(PlayerWorldBuildingFailureV1::player_gold_source);
        }
        result.player_gold_observed = true;
      }
      struct ScanDefinition final {
        std::int32_t building_type_id;
        std::uintptr_t definition;
        int authored_income_hundredths;
      };
      std::vector<ScanDefinition> positive_definitions;
      std::vector<ScanDefinition> remaining_definitions;
      positive_definitions.reserve(kAuthoredBuildingIncomeHundredthsV1.size());
      remaining_definitions.reserve(definitions.size());
      bool all_definition_keys_classified = true;
      for (const auto &[building_type_id, definition] : definitions) {
        std::string key;
        if (!ReadBuildingKey(campaign, definition, key)) {
          all_definition_keys_classified = false;
          remaining_definitions.push_back({building_type_id, definition, 0});
          continue;
        }
        const int income = AuthoredIncomeHundredths(key);
        (income > 0 ? positive_definitions : remaining_definitions)
            .push_back({building_type_id, definition, income});
      }
      std::stable_sort(positive_definitions.begin(),
                       positive_definitions.end(),
                       [](const auto &a, const auto &b) {
                         return a.authored_income_hundredths >
                                b.authored_income_hundredths;
                       });
      PlayerWorldBuildingFailureV1 scan_failure =
          PlayerWorldBuildingFailureV1::none;
      const auto scan = [&](const std::vector<ScanDefinition> &ordered) {
        // Definition first distributes each valued option across every held
        // barony before the bounded scan spends checks on unvalued types.
        for (const auto &row : ordered) {
          for (const auto &holding : sample_holding_order) {
            std::int32_t slot_count = 0;
            std::uintptr_t province = 0;
            if (!ReadProvinceSlots(campaign, module_base,
                                   holding.province_id,
                                   slot_count, province)) {
              scan_failure = PlayerWorldBuildingFailureV1::province_slot_source;
              return false;
            }
            for (std::int32_t slot = 0; slot < slot_count; ++slot) {
              if (result.final_legality_checks >= request.max_native_checks ||
                  static_cast<std::int32_t>(result.legal_samples.size()) >=
                      request.max_legal_samples) {
                result.checks_truncated = true;
                return false;
              }
              bool allowed = false;
              if (!access.final_legality(
                      access.final_legality_context,
                      before.played_character_id, holding.province_id,
                      row.definition, slot, allowed)) {
                scan_failure = PlayerWorldBuildingFailureV1::
                    native_final_legality;
                return false;
              }
              ++result.final_legality_checks;
              if (!allowed) continue;
              PlayerWorldBuildingLegalSampleV1 sample{
                  holding.barony_title_id, holding.province_id,
                  row.building_type_id, slot};
              if (!ReadBuildingKey(campaign, row.definition,
                                   sample.building_key)) {
                scan_failure = PlayerWorldBuildingFailureV1::definition_key;
                return false;
              }
              if (access.native_cost != nullptr) {
                if (!access.native_cost(
                        access.native_cost_context,
                        before.played_character_id, holding.province_id,
                        province, row.building_type_id, row.definition, slot,
                        sample.cost_raw_native)) {
                  scan_failure = PlayerWorldBuildingFailureV1::native_cost;
                  return false;
                }
                const auto &raw = sample.cost_raw_native;
                sample.cost_raw_slots = {
                    raw[0], raw[1], raw[2], raw[4],
                    raw[5], raw[6], raw[8], raw[9]};
                sample.native_cost_observed = true;
                ++result.native_cost_checks;
              }
              result.legal_samples.push_back(sample);
            }
          }
        }
        return true;
      };
      const bool positive_scan_complete = scan(positive_definitions);
      if (scan_failure != PlayerWorldBuildingFailureV1::none) {
        return Failed(scan_failure);
      }
      result.positive_income_coverage_complete =
          all_definition_keys_classified && positive_scan_complete;
      if (positive_scan_complete) {
        scan(remaining_definitions);
        if (scan_failure != PlayerWorldBuildingFailureV1::none) {
          return Failed(scan_failure);
        }
      }
      result.native_final_legality_evaluated =
          result.final_legality_checks > 0;
      result.native_cost_evaluated =
          result.native_cost_checks > 0;
    }
    game::CampaignRootFrameV1 after{};
    if (!campaign.capture_frame(campaign.context, after) ||
        after != before) {
      return Failed(PlayerWorldBuildingFailureV1::frame_changed);
    }
    result.source_available = true;
    result.snapshot_revision = before.snapshot_revision;
    result.date_raw = before.date_raw;
    result.player_character_id = before.played_character_id;
    // Costs must come from the exact stock player row/provider; no action is
    // permitted merely because native final-legality returned true.
    result.cost_ready = false;
    return result;
  } catch (...) {
    return Failed(PlayerWorldBuildingFailureV1::registry_source);
  }
}

} // namespace xar::ck3_11906
