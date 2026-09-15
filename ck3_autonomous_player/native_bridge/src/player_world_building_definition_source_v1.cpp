#include "player_world_building_definition_source_v1.hpp"

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <unordered_set>
#include <utility>
#include <vector>

namespace xar::ck3_11906 {
namespace {

constexpr std::uintptr_t kWorldBuildingRegistrySlotRva = 0x57BFFD0;
constexpr std::uintptr_t kBuildingTypePrimaryVtableRva = 0x44046C0;
constexpr std::uintptr_t kGameStateSlotRva = 0x570E068;
constexpr std::uintptr_t kGuiPlayerCharacterIdRva = 0x4FE7EE0;
constexpr std::size_t kGameDataOffset = 0xA0;
constexpr std::size_t kProvinceArrayOffset = 0x140;
constexpr std::size_t kProvinceCountOffset = 0x14C;
constexpr std::size_t kProvinceIdentityOffset = 0x10;
constexpr std::size_t kProvinceSlotsOffset = 0x620;
constexpr std::size_t kProvinceSlotCountOffset = 0x24;
constexpr std::size_t kRegistryDataOffset = 0x68;
constexpr std::size_t kRegistryCapacityOffset = 0x70;
constexpr std::size_t kRegistryCountOffset = 0x74;
constexpr std::size_t kBuildingTypeIdentityOffset = 0x10;
constexpr std::int32_t kMaxWorldDefinitions = 16'384;
constexpr std::int32_t kMaxProvinceSlots = 64;
constexpr std::int32_t kMaxProvinceCount = 1'000'000;

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

bool ReadWorldDefinitions(const CampaignRootAccessV1 &access,
                          std::uintptr_t module,
                          std::vector<std::pair<std::int32_t,
                                                std::uintptr_t>> &out,
                          std::int32_t &count,
                          PlayerWorldBuildingFailureV1 &failure) {
  failure = PlayerWorldBuildingFailureV1::registry_source;
  std::uintptr_t registry = 0;
  std::uintptr_t data = 0;
  std::int32_t capacity = 0;
  count = 0;
  if (!Read(access, module, kWorldBuildingRegistrySlotRva, registry) ||
      registry == 0 || !Read(access, registry, kRegistryDataOffset, data) ||
      !Read(access, registry, kRegistryCapacityOffset, capacity) ||
      !Read(access, registry, kRegistryCountOffset, count) ||
      capacity < 0 || count < 0 || count > capacity ||
      count > kMaxWorldDefinitions || (count > 0 && data == 0)) {
    return false;
  }
  out.reserve(static_cast<std::size_t>(count));
  std::unordered_set<std::int32_t> seen_ids;
  seen_ids.reserve(static_cast<std::size_t>(count));
  failure = PlayerWorldBuildingFailureV1::definition_identity;
  for (std::int32_t index = 0; index < count; ++index) {
    std::uintptr_t definition = 0;
    std::uintptr_t vtable = 0;
    std::int32_t building_type_id = -1;
    if (!Read(access, data,
              static_cast<std::size_t>(index) * sizeof(definition),
              definition) || definition == 0 ||
        !Read(access, definition, 0, vtable) ||
        vtable != module + kBuildingTypePrimaryVtableRva ||
        !Read(access, definition, kBuildingTypeIdentityOffset,
              building_type_id) || building_type_id < 0 ||
        !seen_ids.insert(building_type_id).second) {
      return false;
    }
    out.emplace_back(building_type_id, definition);
  }
  failure = PlayerWorldBuildingFailureV1::none;
  return true;
}

bool ReadProvinceSlots(const CampaignRootAccessV1 &access,
                       std::uintptr_t module, std::int32_t province_id,
                       std::int32_t &slot_count) noexcept {
  std::uintptr_t game_state = 0;
  std::uintptr_t game_data = 0;
  std::uintptr_t provinces = 0;
  std::uintptr_t province = 0;
  std::int32_t province_count = 0;
  std::int32_t observed_id = -1;
  slot_count = 0;
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
         slot_count >= 0 && slot_count <= kMaxProvinceSlots;
}

PlayerWorldBuildingSourceResultV1 Failed(
    PlayerWorldBuildingFailureV1 failure) noexcept {
  PlayerWorldBuildingSourceResultV1 result{};
  result.failure = failure;
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
                              registry_failure)) {
      return Failed(registry_failure);
    }
    if (access.final_legality != nullptr &&
        request.max_native_checks > 0 &&
        request.max_legal_samples > 0) {
      bool stop = false;
      for (const auto &holding : sample_holding_order) {
        std::int32_t slot_count = 0;
        if (!ReadProvinceSlots(campaign, module_base, holding.province_id,
                               slot_count)) {
          return Failed(PlayerWorldBuildingFailureV1::province_slot_source);
        }
        for (const auto &[building_type_id, definition] : definitions) {
          for (std::int32_t slot = 0; slot < slot_count; ++slot) {
            if (result.final_legality_checks >= request.max_native_checks ||
                static_cast<std::int32_t>(result.legal_samples.size()) >=
                    request.max_legal_samples) {
              result.checks_truncated = true;
              stop = true;
              break;
            }
            bool allowed = false;
            if (!access.final_legality(
                    access.final_legality_context,
                    before.played_character_id, holding.province_id,
                    definition, slot, allowed)) {
              return Failed(PlayerWorldBuildingFailureV1::
                                native_final_legality);
            }
            ++result.final_legality_checks;
            if (allowed) {
              result.legal_samples.push_back(
                  {holding.barony_title_id, holding.province_id,
                   building_type_id, slot});
            }
          }
          if (stop) break;
        }
        if (stop) break;
      }
      result.native_final_legality_evaluated =
          result.final_legality_checks > 0;
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
